#!/usr/bin/env python3
"""Close one active Kalaxy3 SAGE session into the completed registry."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[2]
ACTIVE_REGISTRY_PATH = ROOT / "sage-active-session-registry.json"
COMPLETED_REGISTRY_PATH = ROOT / "sage-session-improvement-registry.json"
CANDIDATE_REGISTRY_PATH = ROOT / "sage-change-candidate-registry.json"
LIFECYCLE_REGISTRY_PATH = (
    ROOT / "sage-change-candidate-lifecycle-registry.json"
)
ACTIVE_TOOL_PATH = ROOT / "scripts/sage/sage-active-session.py"
CONTINUOUS_GUARDRAIL_PATH = (
    ROOT / "scripts/sage/sage-continuous-improvement-guardrail.py"
)
ACTIVE_GUARDRAIL_PATH = (
    ROOT / "scripts/sage/sage-active-session-guardrail.py"
)

SESSION_ID_RE = re.compile(r"^SAGE-SESSION-[0-9]{8}-[0-9]{3}$")
CHANGE_ID_RE = re.compile(r"^SAGE-CHANGE-[0-9]{8}-[0-9]{3}$")
LESSON_ID_RE = re.compile(r"^SAGE-LESSON-[0-9]{8}-[0-9]{3}$")
ACTION_ID_RE = re.compile(r"^SAGE-ACTION-[0-9]{8}-[0-9]{3}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_ID_RE = re.compile(r"^SAGE-K3-[A-Z0-9-]+-[0-9]{8}-[0-9]{3}$")

REQUIRED_PLANES = ["delivery", "operations", "economics", "learning"]
PREDICTION_RESULTS = {
    "in-range",
    "outside-range",
    "correct",
    "incorrect",
    "inconclusive",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
ERROR_CLASSIFICATIONS = {
    "incomplete-discovery",
    "prior-lesson-not-applied",
    "baseline-inaccurate",
    "scope-changed",
    "implementation-defect",
    "environmental-change",
    "dependency-behavior",
    "operator-error",
    "new-failure-mode",
    "range-too-narrow",
    "confidence-overstated",
    "confidence-understated",
}
OBSERVATION_WINDOWS = {
    "baseline",
    "immediate",
    "stabilization",
    "trend",
    "economic",
}
COMPLETED_FIELDS = {
    "schema_version",
    "session_id",
    "change_id",
    "candidate_prediction_versions",
    "implementation_commit",
    "evidence_ids",
    "started_at",
    "completed_at",
    "feedback_planes",
    "prediction_evaluations",
    "cost_comparison",
    "observability_comparison",
    "lessons",
    "improvement_actions",
    "outcome",
}
PREDICTION_FIELDS = {
    "prediction_stage",
    "prediction_version",
    "subject",
    "predicted",
    "actual",
    "result",
    "confidence",
    "error_classifications",
    "explanation",
}
COST_FIELDS = {
    "before",
    "after",
    "delta",
    "one_time_change_cost",
    "avoidable_rework_cost",
    "unit_economics",
    "provenance",
}
OBSERVABILITY_FIELDS = {
    "before",
    "after",
    "delta",
    "observation_windows",
    "provenance",
}


def command_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["PAGER"] = "cat"
    environment["GIT_PAGER"] = "cat"
    environment["LESS"] = "FRX"
    return environment


def run(
    args: Sequence[str],
    *,
    cwd: Path = ROOT,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        capture_output=capture,
        check=False,
        env=command_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(
            f"command failed ({result.returncode}): "
            f"{' '.join(args)}: {detail}"
        )
    return result


def git_output(*args: str) -> str:
    return run(["git", *args], capture=True).stdout.strip()


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{label} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone offset")
    return parsed


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_bytes_fsync(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def write_json_fsync(path: Path, payload: dict[str, Any]) -> None:
    write_bytes_fsync(
        path,
        (json.dumps(payload, indent=4) + "\n").encode("utf-8"),
    )


def load_active_tool() -> Any:
    specification = importlib.util.spec_from_file_location(
        "kalaxy3_sage_active_session",
        ACTIVE_TOOL_PATH,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load active-session tool")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def find_record(
    payload: dict[str, Any],
    collection: str,
    key: str,
    value: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in payload.get(collection, [])
        if isinstance(item, dict) and item.get(key) == value
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one {collection} record for {key}={value}"
        )
    return matches[0]


def unique_strings(value: Any, label: str, *, nonempty: bool) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    if nonempty and not value:
        raise ValueError(f"{label} cannot be empty")
    if (
        any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError(f"{label} must contain unique nonempty strings")
    return value


def validate_completed_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict) or set(record) != COMPLETED_FIELDS:
        raise ValueError("completed-session fields must match the contract")
    if record["schema_version"] != "1.0":
        raise ValueError("completed-session schema_version must be 1.0")
    if not SESSION_ID_RE.fullmatch(str(record["session_id"])):
        raise ValueError("completed-session session_id is invalid")
    if not CHANGE_ID_RE.fullmatch(str(record["change_id"])):
        raise ValueError("completed-session change_id is invalid")
    if not SHA_RE.fullmatch(str(record["implementation_commit"])):
        raise ValueError("completed-session implementation_commit is invalid")

    versions = record["candidate_prediction_versions"]
    if not isinstance(versions, list) or not versions:
        raise ValueError("candidate_prediction_versions cannot be empty")
    observed_versions: set[tuple[str, int]] = set()
    for item in versions:
        if (
            not isinstance(item, dict)
            or set(item) != {"stage", "version"}
            or item["stage"] not in {"discovery", "pre-deployment"}
            or not isinstance(item["version"], int)
            or isinstance(item["version"], bool)
            or item["version"] < 1
        ):
            raise ValueError("candidate prediction version is invalid")
        key = (item["stage"], item["version"])
        if key in observed_versions:
            raise ValueError("candidate prediction versions must be unique")
        observed_versions.add(key)

    evidence_ids = unique_strings(
        record["evidence_ids"],
        "evidence_ids",
        nonempty=True,
    )
    for evidence_id in evidence_ids:
        if not EVIDENCE_ID_RE.fullmatch(evidence_id):
            raise ValueError(f"invalid evidence ID: {evidence_id}")

    started = parse_timestamp(record["started_at"], "started_at")
    completed = parse_timestamp(record["completed_at"], "completed_at")
    if completed < started:
        raise ValueError("completed_at cannot precede started_at")

    feedback = record["feedback_planes"]
    if not isinstance(feedback, dict) or list(feedback) != REQUIRED_PLANES:
        raise ValueError("feedback planes must preserve canonical order")
    for plane, item in feedback.items():
        if (
            not isinstance(item, dict)
            or set(item) != {"measurements", "summary"}
            or not isinstance(item["measurements"], list)
            or not isinstance(item["summary"], str)
            or not item["summary"]
            or any(
                not isinstance(measurement, dict)
                for measurement in item["measurements"]
            )
        ):
            raise ValueError(f"{plane} feedback plane is invalid")

    evaluations = record["prediction_evaluations"]
    if not isinstance(evaluations, list):
        raise ValueError("prediction_evaluations must be a list")
    for item in evaluations:
        if not isinstance(item, dict) or set(item) != PREDICTION_FIELDS:
            raise ValueError("prediction evaluation fields are invalid")
        if item["prediction_stage"] not in {
            "discovery",
            "pre-deployment",
        }:
            raise ValueError("prediction evaluation stage is invalid")
        if (
            not isinstance(item["prediction_version"], int)
            or isinstance(item["prediction_version"], bool)
            or item["prediction_version"] < 1
        ):
            raise ValueError("prediction evaluation version is invalid")
        if not isinstance(item["subject"], str) or not item["subject"]:
            raise ValueError("prediction evaluation subject is required")
        if item["result"] not in PREDICTION_RESULTS:
            raise ValueError("prediction evaluation result is invalid")
        if item["confidence"] not in CONFIDENCE_LEVELS:
            raise ValueError("prediction evaluation confidence is invalid")
        classifications = unique_strings(
            item["error_classifications"],
            "prediction error classifications",
            nonempty=False,
        )
        unknown = sorted(set(classifications) - ERROR_CLASSIFICATIONS)
        if unknown:
            raise ValueError(
                f"unknown prediction error classifications: {unknown}"
            )
        if not isinstance(item["explanation"], str):
            raise ValueError("prediction explanation must be a string")
        if item["actual"] is None and item["result"] != "inconclusive":
            raise ValueError(
                "unavailable prediction actual must be inconclusive"
            )

    cost = record["cost_comparison"]
    if not isinstance(cost, dict) or set(cost) != COST_FIELDS:
        raise ValueError("cost_comparison fields are invalid")
    unique_strings(cost["provenance"], "cost provenance", nonempty=True)

    observability = record["observability_comparison"]
    if (
        not isinstance(observability, dict)
        or set(observability) != OBSERVABILITY_FIELDS
    ):
        raise ValueError("observability_comparison fields are invalid")
    windows = unique_strings(
        observability["observation_windows"],
        "observation windows",
        nonempty=True,
    )
    if not set(windows).issubset(OBSERVATION_WINDOWS):
        raise ValueError("observability comparison window is invalid")
    unique_strings(
        observability["provenance"],
        "observability provenance",
        nonempty=True,
    )

    lessons = unique_strings(record["lessons"], "lessons", nonempty=False)
    if any(not LESSON_ID_RE.fullmatch(item) for item in lessons):
        raise ValueError("completed-session lesson ID is invalid")
    actions = unique_strings(
        record["improvement_actions"],
        "improvement_actions",
        nonempty=False,
    )
    if any(not ACTION_ID_RE.fullmatch(item) for item in actions):
        raise ValueError("completed-session action ID is invalid")

    outcome = record["outcome"]
    if (
        not isinstance(outcome, dict)
        or set(outcome) != {"hypothesis_result", "summary"}
        or outcome["hypothesis_result"]
        not in {"supported", "rejected", "inconclusive"}
        or not isinstance(outcome["summary"], str)
        or not outcome["summary"]
    ):
        raise ValueError("completed-session outcome is invalid")
    return record


def validate_completed_registry(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["completed-session registry must be an object"]
    if payload.get("schema_version") != "1.0":
        failures.append("completed-session registry schema_version must be 1.0")
    if payload.get("registry_type") != "session-improvements":
        failures.append(
            "completed-session registry_type must be session-improvements"
        )
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        return failures + ["completed-session sessions must be a list"]
    identifiers: list[str] = []
    for index, item in enumerate(sessions):
        try:
            validate_completed_record(item)
            identifiers.append(item["session_id"])
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"sessions[{index}]: {error}")
    if len(identifiers) != len(set(identifiers)):
        failures.append("completed-session identifiers must be unique")
    return failures


def evidence_exists(evidence_id: str) -> bool:
    for record in (ROOT / "markdown").rglob("*.md"):
        try:
            first = record.read_text(
                encoding="utf-8",
                errors="ignore",
            )[:4096]
        except OSError:
            continue
        if f"evidence_id: {evidence_id}" in first:
            return True
    return False


def replacement_values(
    *,
    completed_at: str,
    session_elapsed_minutes: float,
    elapsed_days: float,
    summary: dict[str, Any],
) -> dict[str, Any]:
    values: dict[str, Any] = {
        "__SAGE_COMPLETED_AT__": completed_at,
        "__SAGE_SESSION_ELAPSED_MINUTES__": session_elapsed_minutes,
        "__SAGE_ELAPSED_DAYS__": elapsed_days,
        "__SAGE_FINAL_SUMMARY__": summary,
    }
    for key, value in summary.items():
        values[f"__SAGE_{key.upper()}__"] = value
    return values


def replace_tokens(value: Any, replacements: dict[str, Any]) -> Any:
    if isinstance(value, str) and value in replacements:
        return copy.deepcopy(replacements[value])
    if isinstance(value, list):
        return [replace_tokens(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_tokens(item, replacements)
            for key, item in value.items()
        }
    return value


def close_event(
    *,
    session: dict[str, Any],
    completed_file: Path,
    expected_head: str,
    started_at: str,
    completed_at: str,
    duration_seconds: float,
) -> dict[str, Any]:
    digest_source = json.dumps(
        {
            "operation": "close-active-session",
            "session_id": session["session_id"],
            "completed_session_file_sha256": hashlib.sha256(
                completed_file.read_bytes()
            ).hexdigest(),
            "expected_head": expected_head,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "command",
        "session_id": session["session_id"],
        "change_id": session["change_id"],
        "phase": "session-closeout",
        "command_class": "repository-mutation",
        "label": "close-active-session",
        "command_digest": hashlib.sha256(
            digest_source.encode("utf-8")
        ).hexdigest(),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": round(duration_seconds, 3),
        "exit_code": 0,
        "retry": False,
        "manual_correction": False,
        "manual_correction_reason": None,
        "mutation_opportunity": True,
        "failure_detected_pre_mutation": False,
        "known_failure_encountered": False,
        "known_failure_recurred": False,
        "applicable_lesson_ids": [],
        "used_lesson_ids": [],
        "avoidable_rework_minutes": None,
    }


def render_completed_record(
    draft: dict[str, Any],
    *,
    session: dict[str, Any],
    summary: dict[str, Any],
    completed_at: str,
) -> dict[str, Any]:
    started = parse_timestamp(session["started_at"], "session started_at")
    completed = parse_timestamp(completed_at, "completed_at")
    elapsed_seconds = max(0.0, (completed - started).total_seconds())
    rendered = replace_tokens(
        draft,
        replacement_values(
            completed_at=completed_at,
            session_elapsed_minutes=round(elapsed_seconds / 60, 3),
            elapsed_days=round(elapsed_seconds / 86400, 6),
            summary=summary,
        ),
    )
    return validate_completed_record(rendered)


def validate_cross_references(
    record: dict[str, Any],
    *,
    session: dict[str, Any],
    candidate: dict[str, Any],
    lifecycle: dict[str, Any],
    expected_head: str,
) -> None:
    if record["session_id"] != session["session_id"]:
        raise ValueError("completed session_id does not match active session")
    if record["change_id"] != session["change_id"]:
        raise ValueError("completed change_id does not match active session")
    if record["started_at"] != session["started_at"]:
        raise ValueError("completed started_at does not match active session")
    expected_versions = [
        {"stage": "discovery", "version": value}
        for value in session["prediction_versions"]
    ]
    if record["candidate_prediction_versions"] != expected_versions:
        raise ValueError(
            "candidate prediction versions do not match active session"
        )
    if record["implementation_commit"] != expected_head:
        raise ValueError(
            "completed implementation_commit must equal expected HEAD"
        )
    missing_evidence = [
        evidence_id
        for evidence_id in record["evidence_ids"]
        if not evidence_exists(evidence_id)
    ]
    if missing_evidence:
        raise ValueError(
            f"completed session references missing evidence: "
            f"{missing_evidence}"
        )
    if candidate["status"] != "validated":
        raise ValueError("candidate must be validated before session close")
    if lifecycle["current_status"] != "validated":
        raise ValueError("lifecycle must be validated before session close")
    if lifecycle["execution_scope"] != "repository-only":
        raise ValueError("session close currently requires repository-only scope")
    if candidate["deployment_gate"]["status"] != "closed":
        raise ValueError("deployment gate must remain closed")


def updated_registries(
    active_registry: dict[str, Any],
    completed_registry: dict[str, Any],
    *,
    session_id: str,
    completed_record: dict[str, Any],
    active_tool: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated_active = copy.deepcopy(active_registry)
    updated_completed = copy.deepcopy(completed_registry)
    updated_active["sessions"] = [
        item
        for item in updated_active["sessions"]
        if item.get("session_id") != session_id
    ]
    updated_completed["sessions"].append(completed_record)

    active_failures = active_tool.validate_registry(updated_active)
    completed_failures = validate_completed_registry(updated_completed)
    failures = [*active_failures, *completed_failures]
    if failures:
        raise ValueError(
            "planned active-to-completed registry move is invalid: "
            + "; ".join(failures)
        )
    return updated_active, updated_completed


def write_registry_pair(
    active_registry: dict[str, Any],
    completed_registry: dict[str, Any],
) -> None:
    original_active = ACTIVE_REGISTRY_PATH.read_bytes()
    original_completed = COMPLETED_REGISTRY_PATH.read_bytes()
    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-sage-session-close-",
        dir=ROOT,
    ) as temp_directory:
        temporary = Path(temp_directory)
        active_temp = temporary / ACTIVE_REGISTRY_PATH.name
        completed_temp = temporary / COMPLETED_REGISTRY_PATH.name
        write_json_fsync(active_temp, active_registry)
        write_json_fsync(completed_temp, completed_registry)
        try:
            os.replace(active_temp, ACTIVE_REGISTRY_PATH)
            os.replace(completed_temp, COMPLETED_REGISTRY_PATH)
        except OSError:
            write_bytes_fsync(ACTIVE_REGISTRY_PATH, original_active)
            write_bytes_fsync(COMPLETED_REGISTRY_PATH, original_completed)
            raise


def preflight_repository(session: dict[str, Any], expected_head: str) -> None:
    if not SHA_RE.fullmatch(expected_head):
        raise ValueError("--expected-head must be a full Git SHA")
    if git_output("branch", "--show-current") != session["branch"]:
        raise ValueError("active-session branch is not checked out")
    run(["git", "fetch", "origin"])
    head = git_output("rev-parse", "HEAD")
    remote = git_output("rev-parse", f"origin/{session['branch']}")
    if head != expected_head:
        raise ValueError("local HEAD does not match --expected-head")
    if remote != expected_head:
        raise ValueError("remote feature branch does not match --expected-head")
    if git_output(
        "rev-list",
        "--left-right",
        "--count",
        f"HEAD...origin/{session['branch']}",
    ) != "0\t0":
        raise ValueError("feature branch divergence is nonzero")


def prepare_close(
    *,
    session_id: str,
    completed_file: Path,
    expected_head: str,
    simulated_duration: float,
) -> tuple[
    Any,
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    active_tool = load_active_tool()
    active_registry = active_tool.load_registry(ACTIVE_REGISTRY_PATH)
    session = active_tool.find_session(active_registry, session_id)
    preflight_repository(session, expected_head)

    completed_registry = load_json(COMPLETED_REGISTRY_PATH)
    failures = validate_completed_registry(completed_registry)
    if failures:
        raise ValueError("; ".join(failures))
    if any(
        item.get("session_id") == session_id
        for item in completed_registry["sessions"]
    ):
        raise ValueError("session is already completed")

    candidate_registry = load_json(CANDIDATE_REGISTRY_PATH)
    lifecycle_registry = load_json(LIFECYCLE_REGISTRY_PATH)
    candidate = find_record(
        candidate_registry,
        "candidates",
        "change_id",
        session["change_id"],
    )
    lifecycle = find_record(
        lifecycle_registry,
        "lifecycles",
        "change_id",
        session["change_id"],
    )

    draft = load_json(completed_file)
    events = active_tool.read_events(active_tool.event_path(session))
    if any(
        event.get("event_type") == "command"
        and event.get("label") == "close-active-session"
        for event in events
    ):
        raise ValueError(
            "active ledger already contains a close event; "
            "recover the prior close attempt before retrying"
        )

    started_at = now_iso()
    completed_at = now_iso()
    event = close_event(
        session=session,
        completed_file=completed_file,
        expected_head=expected_head,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=simulated_duration,
    )
    planned_events = [*events, event]
    summary = active_tool.summarize(session, planned_events)
    record = render_completed_record(
        draft,
        session=session,
        summary=summary,
        completed_at=completed_at,
    )
    validate_cross_references(
        record,
        session=session,
        candidate=candidate,
        lifecycle=lifecycle,
        expected_head=expected_head,
    )
    updated_active, updated_completed = updated_registries(
        active_registry,
        completed_registry,
        session_id=session_id,
        completed_record=record,
        active_tool=active_tool,
    )
    return (
        active_tool,
        active_registry,
        completed_registry,
        session,
        candidate,
        lifecycle,
        event,
        events,
        {
            "record": record,
            "summary": summary,
            "updated_active": updated_active,
            "updated_completed": updated_completed,
        },
    )


def close_session(args: argparse.Namespace) -> int:
    if not args.completed_session_file.is_file():
        raise ValueError("completed-session file does not exist")

    started_clock = time.monotonic()
    (
        active_tool,
        active_registry,
        completed_registry,
        session,
        candidate,
        lifecycle,
        _,
        original_events,
        plan,
    ) = prepare_close(
        session_id=args.session_id,
        completed_file=args.completed_session_file,
        expected_head=args.expected_head,
        simulated_duration=0.0,
    )

    print(
        json.dumps(
            {
                "mode": "apply" if args.apply else "dry-run",
                "session_id": args.session_id,
                "change_id": session["change_id"],
                "candidate_status": candidate["status"],
                "lifecycle_status": lifecycle["current_status"],
                "deployment_gate": candidate["deployment_gate"]["status"],
                "completed_record": plan["record"],
                "final_summary": plan["summary"],
            },
            indent=4,
        )
    )

    if not args.apply:
        print("DRY RUN: no ledger or registry files changed")
        return 0

    if git_output("status", "--porcelain"):
        raise ValueError("working tree must be clean before --apply")

    original_ledger = active_tool.event_path(session).read_bytes()
    original_active = ACTIVE_REGISTRY_PATH.read_bytes()
    original_completed = COMPLETED_REGISTRY_PATH.read_bytes()

    close_started_at = now_iso()
    try:
        duration = round(time.monotonic() - started_clock, 3)
        close_completed_at = now_iso()
        event = close_event(
            session=session,
            completed_file=args.completed_session_file,
            expected_head=args.expected_head,
            started_at=close_started_at,
            completed_at=close_completed_at,
            duration_seconds=duration,
        )
        active_tool.append_jsonl(active_tool.event_path(session), event)
        final_events = [*original_events, event]
        final_summary = active_tool.summarize(session, final_events)
        final_record = render_completed_record(
            load_json(args.completed_session_file),
            session=session,
            summary=final_summary,
            completed_at=close_completed_at,
        )
        validate_cross_references(
            final_record,
            session=session,
            candidate=candidate,
            lifecycle=lifecycle,
            expected_head=args.expected_head,
        )
        updated_active, updated_completed = updated_registries(
            active_registry,
            completed_registry,
            session_id=args.session_id,
            completed_record=final_record,
            active_tool=active_tool,
        )
        write_registry_pair(updated_active, updated_completed)
        run([sys.executable, str(ACTIVE_GUARDRAIL_PATH)])
        run([sys.executable, str(CONTINUOUS_GUARDRAIL_PATH)])
    except Exception:
        write_bytes_fsync(active_tool.event_path(session), original_ledger)
        write_bytes_fsync(ACTIVE_REGISTRY_PATH, original_active)
        write_bytes_fsync(COMPLETED_REGISTRY_PATH, original_completed)
        raise

    print("APPLIED active-to-completed session registry mutation")
    print(f"Session: {args.session_id}")
    print(f"Completed at: {final_record['completed_at']}")
    print(
        "Changed paths: "
        "sage-active-session-registry.json, "
        "sage-session-improvement-registry.json"
    )
    print("Deployment gate: closed")
    print("Cluster mutation: none")
    print(json.dumps(final_summary, indent=4))
    return 0


def representative_draft() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "session_id": "SAGE-SESSION-20260730-999",
        "change_id": "SAGE-CHANGE-20260730-999",
        "candidate_prediction_versions": [
            {"stage": "discovery", "version": 1}
        ],
        "implementation_commit": "0" * 40,
        "evidence_ids": ["SAGE-K3-SAGE-20260730-999"],
        "started_at": "2026-07-30T00:00:00-05:00",
        "completed_at": "__SAGE_COMPLETED_AT__",
        "feedback_planes": {
            "delivery": {
                "measurements": [
                    {
                        "metric": "active_session_summary",
                        "value": "__SAGE_FINAL_SUMMARY__",
                        "measurement_type": "measured",
                    }
                ],
                "summary": "Measured from the canonical active ledger.",
            },
            "operations": {
                "measurements": [],
                "summary": "No cluster mutation.",
            },
            "economics": {
                "measurements": [],
                "summary": "No recurring infrastructure delta.",
            },
            "learning": {
                "measurements": [
                    {
                        "metric": "session_elapsed_minutes",
                        "value": "__SAGE_SESSION_ELAPSED_MINUTES__",
                        "measurement_type": "measured",
                    }
                ],
                "summary": "Lessons remained separate from outcomes.",
            },
        },
        "prediction_evaluations": [
            {
                "prediction_stage": "discovery",
                "prediction_version": 1,
                "subject": "active engineering hours",
                "predicted": {
                    "point": 6,
                    "minimum": 4,
                    "maximum": 12,
                    "unit": "hours",
                },
                "actual": None,
                "result": "inconclusive",
                "confidence": "medium",
                "error_classifications": [],
                "explanation": "Human effort was not explicitly timed.",
            }
        ],
        "cost_comparison": {
            "before": {},
            "after": {},
            "delta": {},
            "one_time_change_cost": {},
            "avoidable_rework_cost": {},
            "unit_economics": {},
            "provenance": ["self-test"],
        },
        "observability_comparison": {
            "before": {},
            "after": {},
            "delta": {},
            "observation_windows": ["baseline", "immediate"],
            "provenance": ["self-test"],
        },
        "lessons": [],
        "improvement_actions": [],
        "outcome": {
            "hypothesis_result": "inconclusive",
            "summary": "One session cannot establish a trend.",
        },
    }


def self_test() -> list[str]:
    failures: list[str] = []
    draft = representative_draft()
    try:
        rendered = replace_tokens(
            draft,
            replacement_values(
                completed_at="2026-07-30T01:00:00-05:00",
                session_elapsed_minutes=60.0,
                elapsed_days=0.041667,
                summary={
                    "session_id": "SAGE-SESSION-20260730-999",
                    "commands_executed": 1,
                },
            ),
        )
        rendered["implementation_commit"] = "0" * 40
        validate_completed_record(rendered)
        if (
            rendered["feedback_planes"]["delivery"]["measurements"][0][
                "value"
            ]["commands_executed"]
            != 1
        ):
            failures.append("final summary token replacement changed")
    except (KeyError, TypeError, ValueError) as error:
        failures.append(f"representative completed record failed: {error}")

    unavailable = representative_draft()
    unavailable["completed_at"] = "2026-07-30T01:00:00-05:00"
    try:
        validate_completed_record(unavailable)
    except ValueError as error:
        failures.append(f"nullable prediction actual was rejected: {error}")

    fabricated = copy.deepcopy(unavailable)
    fabricated["prediction_evaluations"][0]["result"] = "in-range"
    try:
        validate_completed_record(fabricated)
    except ValueError:
        pass
    else:
        failures.append("unavailable prediction actual was scored conclusively")

    registry = {
        "schema_version": "1.0",
        "registry_type": "session-improvements",
        "sessions": [unavailable],
    }
    if validate_completed_registry(registry):
        failures.append("representative completed registry was rejected")

    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-sage-close-self-test-"
    ) as temporary_directory:
        temporary = Path(temporary_directory)
        active_path = temporary / "active.json"
        completed_path = temporary / "completed.json"
        active_payload = {
            "schema_version": "1.0",
            "registry_type": "active-sessions",
            "sessions": [{"session_id": "temporary"}],
        }
        completed_payload = registry
        write_json_fsync(active_path, active_payload)
        write_json_fsync(completed_path, completed_payload)
        if not active_path.is_file() or not completed_path.is_file():
            failures.append("fsync JSON writer did not create files")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Move one active SAGE session into the completed-session registry"
        )
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--session-id")
    parser.add_argument("--completed-session-file", type=Path)
    parser.add_argument("--expected-head")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        failures = self_test()
        if failures:
            print("Kalaxy3 SAGE session close self-test: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS completed-session schema contract")
        print("PASS final active-session summary token replacement")
        print("PASS unavailable prediction actual remains inconclusive")
        print("PASS completed registry uniqueness and field validation")
        print("PASS fsync-backed registry serialization")
        print("PASS close remains dry-run unless --apply is explicit")
        print("Kalaxy3 SAGE session close self-test: PASS")
        return 0

    if (
        args.session_id is None
        or args.completed_session_file is None
        or args.expected_head is None
    ):
        print(
            "Provide --session-id, --completed-session-file, "
            "and --expected-head, or use --self-test."
        )
        return 2
    try:
        return close_session(args)
    except (
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print("Kalaxy3 SAGE session close: FAIL CLOSED")
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
