#!/usr/bin/env python3
# Repository-owned active SAGE session recorder.

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
REGISTRY_PATH: Final = ROOT / "sage-active-session-registry.json"

SESSION_ID_RE: Final = re.compile(
    r"^SAGE-SESSION-[0-9]{8}-[0-9]{3}$"
)
CHANGE_ID_RE: Final = re.compile(
    r"^SAGE-CHANGE-[0-9]{8}-[0-9]{3}$"
)
LESSON_ID_RE: Final = re.compile(
    r"^SAGE-LESSON-[0-9]{8}-[0-9]{3}$"
)
SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")

COMMAND_CLASSES: Final = [
    "discovery",
    "implementation",
    "repository-mutation",
    "validation",
    "evidence",
    "commit",
    "push",
    "recovery",
]
NOTE_TYPES: Final = [
    "baseline",
    "observation",
    "decision",
    "limitation",
    "evidence-gap",
]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(
        timespec="seconds"
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=4)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
        handle.flush()
        os.fsync(handle.fileno())


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def validate_registry(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["active-session registry must be an object"]
    if payload.get("schema_version") != "1.0":
        failures.append("registry schema_version must be 1.0")
    if payload.get("registry_type") != "active-sessions":
        failures.append("registry_type must be active-sessions")
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        return failures + ["sessions must be a list"]

    seen: set[str] = set()
    expected_fields = {
        "schema_version",
        "session_id",
        "change_id",
        "status",
        "branch",
        "baseline_commit",
        "started_at",
        "measurement_boundary",
        "prediction_versions",
        "runtime_ledger",
        "command_storage_policy",
        "deployment_gate",
    }
    for index, session in enumerate(sessions):
        prefix = f"sessions[{index}]"
        if not isinstance(session, dict):
            failures.append(f"{prefix} must be an object")
            continue
        if set(session) != expected_fields:
            failures.append(f"{prefix} fields changed")

        session_id = session.get("session_id")
        if (
            not isinstance(session_id, str)
            or not SESSION_ID_RE.fullmatch(session_id)
        ):
            failures.append(f"{prefix}.session_id is invalid")
        elif session_id in seen:
            failures.append(f"duplicate active session_id {session_id}")
        else:
            seen.add(session_id)

        change_id = session.get("change_id")
        if (
            not isinstance(change_id, str)
            or not CHANGE_ID_RE.fullmatch(change_id)
        ):
            failures.append(f"{prefix}.change_id is invalid")
        if session.get("status") != "active":
            failures.append(f"{prefix}.status must be active")
        branch = session.get("branch")
        if (
            not isinstance(branch, str)
            or not branch.startswith(("feature/", "staged/"))
        ):
            failures.append(f"{prefix}.branch is invalid")
        baseline = session.get("baseline_commit")
        if (
            not isinstance(baseline, str)
            or not SHA_RE.fullmatch(baseline)
        ):
            failures.append(f"{prefix}.baseline_commit is invalid")

        boundary = session.get("measurement_boundary")
        if not isinstance(boundary, dict) or set(boundary) != {
            "included_from",
            "excluded_prior_commands",
            "reason",
        }:
            failures.append(
                f"{prefix}.measurement_boundary is invalid"
            )

        versions = session.get("prediction_versions")
        if (
            not isinstance(versions, list)
            or not versions
            or any(
                not isinstance(value, int) or value < 1
                for value in versions
            )
            or len(versions) != len(set(versions))
        ):
            failures.append(
                f"{prefix}.prediction_versions is invalid"
            )

        expected_runtime = (
            f".sage/active-sessions/{session_id}/events.jsonl"
        )
        if session.get("runtime_ledger") != expected_runtime:
            failures.append(f"{prefix}.runtime_ledger is invalid")
        if (
            session.get("command_storage_policy")
            != "label-and-digest-only"
        ):
            failures.append(
                f"{prefix}.command_storage_policy changed"
            )
        if session.get("deployment_gate") != "closed":
            failures.append(
                f"{prefix}.deployment_gate must remain closed"
            )
    return failures


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    payload = load_json(path)
    failures = validate_registry(payload)
    if failures:
        raise ValueError("; ".join(failures))
    return payload


def find_session(
    registry: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    matches = [
        session
        for session in registry["sessions"]
        if session["session_id"] == session_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected one active session {session_id}, "
            f"found {len(matches)}"
        )
    return matches[0]


def event_path(session: dict[str, Any]) -> Path:
    return ROOT / session["runtime_ledger"]


def digest_command(command: list[str]) -> str:
    canonical = json.dumps(
        command,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def lesson_ids(values: list[str]) -> list[str]:
    unique = sorted(set(values))
    for value in unique:
        if not LESSON_ID_RE.fullmatch(value):
            raise ValueError(f"invalid lesson ID: {value}")
    return unique


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(
                f"event line {number} must be an object"
            )
        if "command" in payload or "command_text" in payload:
            raise ValueError(
                f"raw command data prohibited at line {number}"
            )
        events.append(payload)
    return events


def summarize(
    session: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    commands = [
        event
        for event in events
        if event.get("event_type") == "command"
    ]
    notes = [
        event
        for event in events
        if event.get("event_type") == "note"
    ]
    phases: dict[str, list[dict[str, Any]]] = {}
    for event in commands:
        phases.setdefault(str(event["phase"]), []).append(event)

    rework = [
        event.get("avoidable_rework_minutes")
        for event in commands
    ]
    rework_total: float | None
    if any(value is None for value in rework):
        rework_total = None
    else:
        rework_total = round(
            sum(float(value) for value in rework),
            3,
        )

    applicable = {
        lesson
        for event in commands
        for lesson in event.get("applicable_lesson_ids", [])
    }
    used = {
        lesson
        for event in commands
        for lesson in event.get("used_lesson_ids", [])
    }

    return {
        "session_id": session["session_id"],
        "change_id": session["change_id"],
        "status": session["status"],
        "started_at": session["started_at"],
        "commands_executed": len(commands),
        "commands_failed": sum(
            1 for event in commands if event["exit_code"] != 0
        ),
        "commands_retried": sum(
            1 for event in commands if event["retry"]
        ),
        "manual_corrections": sum(
            1 for event in commands if event["manual_correction"]
        ),
        "phases_total": len(phases),
        "phases_first_pass": sum(
            1
            for values in phases.values()
            if values
            and all(item["exit_code"] == 0 for item in values)
        ),
        "mutation_opportunities": sum(
            1
            for event in commands
            if event["mutation_opportunity"]
        ),
        "failures_detected_pre_mutation": sum(
            1
            for event in commands
            if event["failure_detected_pre_mutation"]
        ),
        "known_failures_encountered": sum(
            1
            for event in commands
            if event["known_failure_encountered"]
        ),
        "known_failures_recurred": sum(
            1
            for event in commands
            if event["known_failure_recurred"]
        ),
        "applicable_lessons": len(applicable),
        "applicable_lessons_used": len(used),
        "avoidable_rework_minutes": rework_total,
        "prompt_to_validated_change_minutes": None,
        "command_runtime_seconds": round(
            sum(
                float(event["duration_seconds"])
                for event in commands
            ),
            3,
        ),
        "notes_recorded": len(notes),
        "runtime_ledger": session["runtime_ledger"],
    }


def handle_start(args: argparse.Namespace) -> int:
    if not SESSION_ID_RE.fullmatch(args.session_id):
        raise ValueError("session_id is invalid")
    if not CHANGE_ID_RE.fullmatch(args.change_id):
        raise ValueError("change_id is invalid")
    if not SHA_RE.fullmatch(args.baseline_commit):
        raise ValueError("baseline_commit is invalid")
    if not args.branch.startswith(("feature/", "staged/")):
        raise ValueError("branch must use feature/ or staged/")
    if git_output("branch", "--show-current") != args.branch:
        raise ValueError("requested branch is not checked out")

    boundary = load_json(args.measurement_boundary_file)
    if not isinstance(boundary, dict) or set(boundary) != {
        "included_from",
        "excluded_prior_commands",
        "reason",
    }:
        raise ValueError("measurement boundary is invalid")

    registry = load_registry(args.registry)
    if any(
        item["session_id"] == args.session_id
        for item in registry["sessions"]
    ):
        raise ValueError("active session already exists")

    session = {
        "schema_version": "1.0",
        "session_id": args.session_id,
        "change_id": args.change_id,
        "status": "active",
        "branch": args.branch,
        "baseline_commit": args.baseline_commit,
        "started_at": args.started_at,
        "measurement_boundary": boundary,
        "prediction_versions": sorted(
            set(args.prediction_version)
        ),
        "runtime_ledger": (
            f".sage/active-sessions/{args.session_id}/"
            "events.jsonl"
        ),
        "command_storage_policy": "label-and-digest-only",
        "deployment_gate": "closed",
    }
    candidate = {
        **registry,
        "sessions": [*registry["sessions"], session],
    }
    failures = validate_registry(candidate)
    if failures:
        raise ValueError("; ".join(failures))

    if not args.apply:
        print(json.dumps(session, indent=2))
        print("DRY RUN: pass --apply to register the session")
        return 0

    ledger = ROOT / session["runtime_ledger"]
    if ledger.exists():
        raise ValueError("runtime ledger already exists")
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.touch()
    atomic_write_json(args.registry, candidate)
    print(f"REGISTERED active session {args.session_id}")
    return 0


def handle_run(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    session = find_session(registry, args.session_id)
    if git_output("branch", "--show-current") != session["branch"]:
        raise ValueError("active-session branch is not checked out")

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise ValueError("a command is required after --")

    if args.manual_correction and not args.manual_correction_reason:
        raise ValueError(
            "manual correction requires a reason"
        )
    if (
        not args.manual_correction
        and args.manual_correction_reason is not None
    ):
        raise ValueError(
            "manual correction reason requires the correction flag"
        )
    if (
        args.avoidable_rework_minutes is not None
        and (
            not math.isfinite(args.avoidable_rework_minutes)
            or args.avoidable_rework_minutes < 0
        )
    ):
        raise ValueError(
            "avoidable rework must be finite and non-negative"
        )

    applicable = lesson_ids(args.applicable_lesson)
    used = lesson_ids(args.used_lesson)
    if not set(used).issubset(set(applicable)):
        raise ValueError(
            "used lessons must be a subset of applicable lessons"
        )

    event_id = str(uuid.uuid4())
    started_at = now_iso()
    started_clock = time.monotonic()
    print(
        f"ACTIVE SESSION START event_id={event_id} "
        f"phase={args.phase} class={args.command_class}"
    )
    process = subprocess.Popen(command, cwd=ROOT)
    exit_code = process.wait()
    completed_at = now_iso()
    duration = round(time.monotonic() - started_clock, 3)

    event = {
        "event_id": event_id,
        "event_type": "command",
        "session_id": session["session_id"],
        "change_id": session["change_id"],
        "phase": args.phase,
        "command_class": args.command_class,
        "label": args.label,
        "command_digest": digest_command(command),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "retry": args.retry,
        "manual_correction": args.manual_correction,
        "manual_correction_reason": (
            args.manual_correction_reason
            if args.manual_correction
            else None
        ),
        "mutation_opportunity": args.mutation_opportunity,
        "failure_detected_pre_mutation": (
            args.failure_detected_pre_mutation
        ),
        "known_failure_encountered": (
            args.known_failure_encountered
        ),
        "known_failure_recurred": (
            args.known_failure_recurred
        ),
        "applicable_lesson_ids": applicable,
        "used_lesson_ids": used,
        "avoidable_rework_minutes": (
            args.avoidable_rework_minutes
        ),
    }
    append_jsonl(event_path(session), event)
    print(
        f"ACTIVE SESSION END event_id={event_id} "
        f"exit_code={exit_code} duration_seconds={duration}"
    )
    return exit_code


def handle_note(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    session = find_session(registry, args.session_id)
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "note",
        "session_id": session["session_id"],
        "change_id": session["change_id"],
        "phase": args.phase,
        "note_type": args.note_type,
        "recorded_at": now_iso(),
        "text": args.text,
    }
    append_jsonl(event_path(session), event)
    print(f"RECORDED active-session note {event['event_id']}")
    return 0


def handle_status(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    session = find_session(registry, args.session_id)
    print(
        json.dumps(
            summarize(session, read_events(event_path(session))),
            indent=2,
        )
    )
    return 0


def self_test() -> list[str]:
    failures: list[str] = []
    session_id = "SAGE-SESSION-20260729-999"
    session = {
        "schema_version": "1.0",
        "session_id": session_id,
        "change_id": "SAGE-CHANGE-20260729-999",
        "status": "active",
        "branch": "feature/self-test",
        "baseline_commit": "a" * 40,
        "started_at": "2026-07-29T21:00:00-05:00",
        "measurement_boundary": {
            "included_from": "self-test",
            "excluded_prior_commands": [],
            "reason": "self-test",
        },
        "prediction_versions": [1],
        "runtime_ledger": (
            f".sage/active-sessions/{session_id}/events.jsonl"
        ),
        "command_storage_policy": "label-and-digest-only",
        "deployment_gate": "closed",
    }
    registry = {
        "schema_version": "1.0",
        "registry_type": "active-sessions",
        "sessions": [session],
    }
    if validate_registry(registry):
        failures.append("representative active session failed")

    duplicate = json.loads(json.dumps(registry))
    duplicate["sessions"].append(
        json.loads(json.dumps(session))
    )
    if not validate_registry(duplicate):
        failures.append("duplicate session was accepted")

    digest = digest_command(["python3", "-c", "print('ok')"])
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        failures.append("command digest changed")

    with tempfile.TemporaryDirectory(
        prefix="sage-active-session-self-test-"
    ) as temporary:
        ledger = Path(temporary) / "events.jsonl"
        event = {
            "event_id": "event-1",
            "event_type": "command",
            "session_id": session_id,
            "change_id": session["change_id"],
            "phase": "validation",
            "command_class": "validation",
            "label": "self-test",
            "command_digest": digest,
            "started_at": session["started_at"],
            "completed_at": session["started_at"],
            "duration_seconds": 0.0,
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
        append_jsonl(ledger, event)
        summary = summarize(session, read_events(ledger))
        if summary["commands_executed"] != 1:
            failures.append("command count changed")
        if summary["avoidable_rework_minutes"] is not None:
            failures.append("unknown rework did not remain null")
        if summary["known_failures_encountered"] != 0:
            failures.append("known-failure encounter count changed")
        if summary["known_failures_recurred"] != 0:
            failures.append("known-failure recurrence count changed")

        unsafe = dict(event)
        unsafe["command_text"] = "secret"
        append_jsonl(ledger, unsafe)
        try:
            read_events(ledger)
        except ValueError:
            pass
        else:
            failures.append("raw command text was accepted")

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record active Kalaxy3 SAGE session metrics"
    )
    parser.add_argument("--self-test", action="store_true")
    subparsers = parser.add_subparsers(dest="subcommand")

    start = subparsers.add_parser("start")
    start.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    start.add_argument("--session-id", required=True)
    start.add_argument("--change-id", required=True)
    start.add_argument("--branch", required=True)
    start.add_argument("--baseline-commit", required=True)
    start.add_argument("--started-at", required=True)
    start.add_argument(
        "--measurement-boundary-file",
        type=Path,
        required=True,
    )
    start.add_argument(
        "--prediction-version",
        type=int,
        action="append",
        required=True,
    )
    start.add_argument("--apply", action="store_true")
    start.set_defaults(function=handle_start)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
    )
    run_parser.add_argument("--session-id", required=True)
    run_parser.add_argument("--phase", required=True)
    run_parser.add_argument(
        "--command-class",
        required=True,
        choices=COMMAND_CLASSES,
    )
    run_parser.add_argument("--label", required=True)
    run_parser.add_argument("--retry", action="store_true")
    run_parser.add_argument(
        "--manual-correction",
        action="store_true",
    )
    run_parser.add_argument("--manual-correction-reason")
    run_parser.add_argument(
        "--mutation-opportunity",
        action="store_true",
    )
    run_parser.add_argument(
        "--failure-detected-pre-mutation",
        action="store_true",
    )
    run_parser.add_argument(
        "--known-failure-encountered",
        action="store_true",
    )
    run_parser.add_argument(
        "--known-failure-recurred",
        action="store_true",
    )
    run_parser.add_argument(
        "--applicable-lesson",
        action="append",
        default=[],
    )
    run_parser.add_argument(
        "--used-lesson",
        action="append",
        default=[],
    )
    run_parser.add_argument(
        "--avoidable-rework-minutes",
        type=float,
        default=None,
    )
    run_parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
    )
    run_parser.set_defaults(function=handle_run)

    note = subparsers.add_parser("note")
    note.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
    )
    note.add_argument("--session-id", required=True)
    note.add_argument("--phase", required=True)
    note.add_argument(
        "--note-type",
        required=True,
        choices=NOTE_TYPES,
    )
    note.add_argument("--text", required=True)
    note.set_defaults(function=handle_note)

    status = subparsers.add_parser("status")
    status.add_argument(
        "--registry",
        type=Path,
        default=REGISTRY_PATH,
    )
    status.add_argument("--session-id", required=True)
    status.set_defaults(function=handle_status)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        failures = self_test()
        if failures:
            print("Kalaxy3 SAGE active-session self-test: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS canonical active-session registry contract")
        print("PASS duplicate session rejection")
        print("PASS label-and-digest-only command storage")
        print("PASS unknown measurements remain null")
        print("PASS known-failure metrics are preserved")
        print("PASS unsafe raw command data is rejected")
        print("Kalaxy3 SAGE active-session self-test: PASS")
        return 0
    if args.subcommand is None:
        raise SystemExit("A subcommand or --self-test is required")
    return int(args.function(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as error:
        print(f"Kalaxy3 SAGE active session: FAIL: {error}")
        raise SystemExit(1)
