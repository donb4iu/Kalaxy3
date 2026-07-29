#!/usr/bin/env python3
"""Manage SAGE change-candidate lifecycle transitions safely."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any, Final, Sequence

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
CANDIDATE_REGISTRY_PATH: Final = (
    ROOT / "sage-change-candidate-registry.json"
)
LIFECYCLE_REGISTRY_PATH: Final = (
    ROOT / "sage-change-candidate-lifecycle-registry.json"
)
SHA_LENGTH: Final = 40


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def require_nonempty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from error


def parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{label} must be an ISO date") from error


def validate_policy(policy: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(policy, dict):
        return ["continuous-improvement policy must be an object"]

    lifecycle = policy.get("candidate_lifecycle_policy")
    if not isinstance(lifecycle, dict):
        return ["candidate_lifecycle_policy must be an object"]

    statuses = policy.get("candidate_statuses")
    if lifecycle.get("statuses") != statuses:
        failures.append(
            "candidate lifecycle statuses must match candidate_statuses"
        )

    transitions = lifecycle.get("allowed_transitions")
    if not isinstance(transitions, dict):
        failures.append("allowed_transitions must be an object")
    elif set(transitions) != set(statuses or []):
        failures.append(
            "allowed_transitions must cover every candidate status"
        )
    else:
        valid = set(statuses)
        for source, targets in transitions.items():
            if (
                not isinstance(targets, list)
                or len(targets) != len(set(targets))
                or not set(targets).issubset(valid)
            ):
                failures.append(
                    f"allowed transitions invalid for {source}"
                )

    required_activation = lifecycle.get(
        "required_activation_conditions"
    )
    expected_activation = [
        "deployment-gate-open",
        "pre-deployment-prediction-recorded",
        "revalidation-current",
        "candidate-branch-checked-out",
        "feature-branch-synchronized",
        "validation-reference-present",
        "expected-head-matches",
    ]
    if required_activation != expected_activation:
        failures.append("activation conditions changed")

    for key in (
        "history_append_only",
        "candidate_status_must_match_lifecycle",
        "dry_run_default",
        "apply_requires_explicit_flag",
        "rollback_on_write_failure",
    ):
        if lifecycle.get(key) is not True:
            failures.append(
                f"candidate_lifecycle_policy.{key} must be true"
            )

    if lifecycle.get("staged_term") != "staged implementation":
        failures.append(
            "candidate lifecycle staged term changed"
        )
    return failures


def candidate_by_id(
    registry: dict[str, Any],
    change_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in registry.get("candidates", [])
        if isinstance(item, dict)
        and item.get("change_id") == change_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"candidate {change_id} must appear exactly once"
        )
    return matches[0]


def lifecycle_by_id(
    registry: dict[str, Any],
    change_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in registry.get("lifecycles", [])
        if isinstance(item, dict)
        and item.get("change_id") == change_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"lifecycle {change_id} must appear exactly once"
        )
    return matches[0]


def validate_candidate_registry(registry: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(registry, dict):
        return ["candidate registry must be an object"]
    if registry.get("schema_version") != "1.0":
        failures.append("candidate registry schema_version must be 1.0")
    if registry.get("registry_type") != "change-candidates":
        failures.append(
            "candidate registry_type must be change-candidates"
        )
    candidates = registry.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        failures.append("candidate registry must be non-empty")
        return failures

    identifiers = [
        item.get("change_id")
        for item in candidates
        if isinstance(item, dict)
    ]
    if len(identifiers) != len(set(identifiers)):
        failures.append("candidate identifiers must be unique")
    return failures


def validate_lifecycle_registry(
    registry: Any,
    candidate_registry: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(registry, dict):
        return ["lifecycle registry must be an object"]
    if registry.get("schema_version") != "1.0":
        failures.append("lifecycle schema_version must be 1.0")
    if registry.get(
        "registry_type"
    ) != "change-candidate-lifecycle":
        failures.append(
            "lifecycle registry_type must be "
            "change-candidate-lifecycle"
        )

    lifecycles = registry.get("lifecycles")
    if not isinstance(lifecycles, list) or not lifecycles:
        failures.append("lifecycle registry must be non-empty")
        return failures

    identifiers = [
        item.get("change_id")
        for item in lifecycles
        if isinstance(item, dict)
    ]
    if len(identifiers) != len(set(identifiers)):
        failures.append("lifecycle identifiers must be unique")

    statuses = set(policy["candidate_statuses"])
    allowed = policy["candidate_lifecycle_policy"][
        "allowed_transitions"
    ]

    for item in lifecycles:
        if not isinstance(item, dict):
            failures.append("lifecycle entry must be an object")
            continue

        required = {
            "change_id",
            "current_status",
            "branch",
            "baseline_commit",
            "deployment_gate_required",
            "revalidation_required",
            "history",
        }
        if set(item) != required:
            failures.append(
                "lifecycle entry fields must match the contract"
            )

        change_id = str(item.get("change_id", ""))
        try:
            candidate = candidate_by_id(
                candidate_registry,
                change_id,
            )
        except ValueError as error:
            failures.append(str(error))
            continue

        if item.get("current_status") not in statuses:
            failures.append(
                f"{change_id}: lifecycle current_status invalid"
            )
        if candidate.get("status") != item.get("current_status"):
            failures.append(
                f"{change_id}: candidate and lifecycle status differ"
            )
        if candidate.get("branch") != item.get("branch"):
            failures.append(
                f"{change_id}: candidate and lifecycle branch differ"
            )
        if candidate.get("baseline_commit") != item.get(
            "baseline_commit"
        ):
            failures.append(
                f"{change_id}: candidate and lifecycle baseline differ"
            )
        if item.get("deployment_gate_required") is not True:
            failures.append(
                f"{change_id}: deployment gate must be required"
            )
        if item.get("revalidation_required") is not True:
            failures.append(
                f"{change_id}: revalidation must be required"
            )

        history = item.get("history")
        if not isinstance(history, list) or not history:
            failures.append(
                f"{change_id}: lifecycle history must be non-empty"
            )
            continue

        previous_status: str | None = None
        previous_time: datetime | None = None

        for index, event in enumerate(history, start=1):
            if not isinstance(event, dict):
                failures.append(
                    f"{change_id}: history event must be an object"
                )
                continue

            event_required = {
                "sequence",
                "from_status",
                "to_status",
                "transition_type",
                "recorded_at",
                "actor",
                "reason",
                "validation_references",
                "candidate_commit",
            }
            if set(event) != event_required:
                failures.append(
                    f"{change_id}: event fields must match contract"
                )

            if event.get("sequence") != index:
                failures.append(
                    f"{change_id}: history sequence must be contiguous"
                )

            from_status = event.get("from_status")
            to_status = event.get("to_status")
            event_type = event.get("transition_type")

            if index == 1:
                if from_status is not None:
                    failures.append(
                        f"{change_id}: initial from_status must be null"
                    )
                if event_type != "initial-registration":
                    failures.append(
                        f"{change_id}: first event must be initial-registration"
                    )
            else:
                if from_status != previous_status:
                    failures.append(
                        f"{change_id}: event chain is not contiguous"
                    )
                if event_type != "status-transition":
                    failures.append(
                        f"{change_id}: later events must be status-transition"
                    )
                if (
                    from_status not in allowed
                    or to_status not in allowed[from_status]
                ):
                    failures.append(
                        f"{change_id}: transition "
                        f"{from_status} -> {to_status} is not allowed"
                    )

            if to_status not in statuses:
                failures.append(
                    f"{change_id}: event to_status invalid"
                )

            for key in ("actor", "reason"):
                try:
                    require_nonempty_string(
                        event.get(key),
                        f"{change_id} event {key}",
                    )
                except ValueError as error:
                    failures.append(str(error))

            references = event.get("validation_references")
            if (
                not isinstance(references, list)
                or not references
                or len(references) != len(set(references))
                or not all(
                    isinstance(value, str) and value
                    for value in references
                )
            ):
                failures.append(
                    f"{change_id}: validation references invalid"
                )

            commit = event.get("candidate_commit")
            if (
                not isinstance(commit, str)
                or len(commit) != SHA_LENGTH
                or any(
                    character not in "0123456789abcdef"
                    for character in commit
                )
            ):
                failures.append(
                    f"{change_id}: candidate_commit invalid"
                )

            try:
                recorded_at = parse_timestamp(
                    str(event.get("recorded_at", "")),
                    f"{change_id} recorded_at",
                )
                if (
                    previous_time is not None
                    and recorded_at < previous_time
                ):
                    failures.append(
                        f"{change_id}: history timestamps regress"
                    )
                previous_time = recorded_at
            except ValueError as error:
                failures.append(str(error))

            previous_status = str(to_status)

        if previous_status != item.get("current_status"):
            failures.append(
                f"{change_id}: final event does not match current_status"
            )

    return failures


def activation_failures(
    candidate: dict[str, Any],
    *,
    current_branch: str,
    head: str,
    remote_head: str,
    expected_head: str,
    validation_references: Sequence[str],
    today: date,
) -> list[str]:
    failures: list[str] = []

    if candidate.get("deployment_gate", {}).get(
        "status"
    ) != "open":
        failures.append("deployment gate is closed")

    predictions = candidate.get("predictions", [])
    has_predeployment = any(
        isinstance(item, dict)
        and item.get("stage") == "pre-deployment"
        for item in predictions
    )
    if not has_predeployment:
        failures.append(
            "pre-deployment prediction is missing"
        )

    valid_until = candidate.get(
        "revalidation", {}
    ).get("valid_until")
    try:
        if parse_date(
            str(valid_until),
            "revalidation.valid_until",
        ) < today:
            failures.append("candidate revalidation has expired")
    except ValueError as error:
        failures.append(str(error))

    if current_branch != candidate.get("branch"):
        failures.append(
            "candidate branch is not checked out"
        )
    if head != remote_head:
        failures.append(
            "feature branch is not synchronized"
        )
    if expected_head != head:
        failures.append(
            "expected HEAD does not match current HEAD"
        )
    if not validation_references:
        failures.append(
            "at least one validation reference is required"
        )
    return failures


def plan_transition(
    candidate_registry: dict[str, Any],
    lifecycle_registry: dict[str, Any],
    policy: dict[str, Any],
    *,
    change_id: str,
    to_status: str,
    actor: str,
    reason: str,
    validation_references: Sequence[str],
    recorded_at: str,
    candidate_commit: str,
    current_branch: str,
    remote_head: str,
    expected_head: str,
    today: date,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    candidate = candidate_by_id(
        candidate_registry,
        change_id,
    )
    lifecycle = lifecycle_by_id(
        lifecycle_registry,
        change_id,
    )

    from_status = str(candidate["status"])
    if lifecycle.get("current_status") != from_status:
        raise ValueError(
            "candidate and lifecycle status differ"
        )

    allowed = policy["candidate_lifecycle_policy"][
        "allowed_transitions"
    ]
    if (
        from_status not in allowed
        or to_status not in allowed[from_status]
    ):
        raise ValueError(
            f"transition {from_status} -> {to_status} is not allowed"
        )

    require_nonempty_string(actor, "actor")
    require_nonempty_string(reason, "reason")
    if (
        not validation_references
        or len(validation_references)
        != len(set(validation_references))
        or not all(
            isinstance(value, str) and value
            for value in validation_references
        )
    ):
        raise ValueError(
            "validation references must be unique and non-empty"
        )

    parse_timestamp(recorded_at, "recorded_at")

    if to_status == "active":
        failures = activation_failures(
            candidate,
            current_branch=current_branch,
            head=candidate_commit,
            remote_head=remote_head,
            expected_head=expected_head,
            validation_references=validation_references,
            today=today,
        )
        if failures:
            raise ValueError(
                "activation blocked: " + "; ".join(failures)
            )

    updated_candidates = copy.deepcopy(candidate_registry)
    updated_lifecycles = copy.deepcopy(lifecycle_registry)

    updated_candidate = candidate_by_id(
        updated_candidates,
        change_id,
    )
    updated_lifecycle = lifecycle_by_id(
        updated_lifecycles,
        change_id,
    )

    updated_candidate["status"] = to_status
    event = {
        "sequence": len(updated_lifecycle["history"]) + 1,
        "from_status": from_status,
        "to_status": to_status,
        "transition_type": "status-transition",
        "recorded_at": recorded_at,
        "actor": actor,
        "reason": reason,
        "validation_references": list(validation_references),
        "candidate_commit": candidate_commit,
    }
    updated_lifecycle["current_status"] = to_status
    updated_lifecycle["history"].append(event)

    validation_failures = []
    validation_failures.extend(
        validate_candidate_registry(updated_candidates)
    )
    validation_failures.extend(
        validate_lifecycle_registry(
            updated_lifecycles,
            updated_candidates,
            policy,
        )
    )
    if validation_failures:
        raise ValueError(
            "planned transition is invalid: "
            + "; ".join(validation_failures)
        )

    return updated_candidates, updated_lifecycles, event


def write_registry_pair(
    candidates: dict[str, Any],
    lifecycles: dict[str, Any],
) -> None:
    original_candidates = CANDIDATE_REGISTRY_PATH.read_text(
        encoding="utf-8"
    )
    original_lifecycles = LIFECYCLE_REGISTRY_PATH.read_text(
        encoding="utf-8"
    )

    candidate_text = json.dumps(candidates, indent=4) + "\n"
    lifecycle_text = json.dumps(lifecycles, indent=4) + "\n"

    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-sage-lifecycle-",
        dir=ROOT,
    ) as temp_dir:
        candidate_temp = Path(temp_dir) / "candidates.json"
        lifecycle_temp = Path(temp_dir) / "lifecycles.json"
        candidate_temp.write_text(
            candidate_text,
            encoding="utf-8",
        )
        lifecycle_temp.write_text(
            lifecycle_text,
            encoding="utf-8",
        )

        try:
            os.replace(
                candidate_temp,
                CANDIDATE_REGISTRY_PATH,
            )
            os.replace(
                lifecycle_temp,
                LIFECYCLE_REGISTRY_PATH,
            )
        except OSError:
            CANDIDATE_REGISTRY_PATH.write_text(
                original_candidates,
                encoding="utf-8",
            )
            LIFECYCLE_REGISTRY_PATH.write_text(
                original_lifecycles,
                encoding="utf-8",
            )
            raise


def representative_policy() -> dict[str, Any]:
    statuses = [
        "discovery-needed",
        "sized",
        "decision-ready",
        "sequenced",
        "staged-implementation",
        "active",
        "validated",
        "closed",
        "superseded",
    ]
    return {
        "candidate_statuses": statuses,
        "candidate_lifecycle_policy": {
            "statuses": statuses,
            "allowed_transitions": {
                "discovery-needed": ["sized", "superseded"],
                "sized": [
                    "discovery-needed",
                    "decision-ready",
                    "superseded",
                ],
                "decision-ready": [
                    "sized",
                    "sequenced",
                    "superseded",
                ],
                "sequenced": [
                    "decision-ready",
                    "staged-implementation",
                    "superseded",
                ],
                "staged-implementation": [
                    "sequenced",
                    "active",
                    "superseded",
                ],
                "active": [
                    "staged-implementation",
                    "validated",
                ],
                "validated": [
                    "staged-implementation",
                    "closed",
                ],
                "closed": [],
                "superseded": [],
            },
            "required_activation_conditions": [
                "deployment-gate-open",
                "pre-deployment-prediction-recorded",
                "revalidation-current",
                "candidate-branch-checked-out",
                "feature-branch-synchronized",
                "validation-reference-present",
                "expected-head-matches",
            ],
            "history_append_only": True,
            "candidate_status_must_match_lifecycle": True,
            "dry_run_default": True,
            "apply_requires_explicit_flag": True,
            "rollback_on_write_failure": True,
            "staged_term": "staged implementation",
        },
    }


def representative_candidate_registry() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_type": "change-candidates",
        "candidates": [
            {
                "change_id": "SAGE-CHANGE-20260728-001",
                "status": "staged-implementation",
                "branch": "feature/sage-continuous-improvement",
                "baseline_commit": "0" * 40,
                "deployment_gate": {
                    "status": "closed",
                    "reason": "Staged implementation.",
                },
                "predictions": [
                    {
                        "stage": "discovery",
                        "version": 1,
                    }
                ],
                "revalidation": {
                    "valid_until": "2999-12-31",
                    "triggers": ["origin/main advances"],
                },
            }
        ],
    }


def representative_lifecycle_registry() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_type": "change-candidate-lifecycle",
        "lifecycles": [
            {
                "change_id": "SAGE-CHANGE-20260728-001",
                "current_status": "staged-implementation",
                "branch": "feature/sage-continuous-improvement",
                "baseline_commit": "0" * 40,
                "deployment_gate_required": True,
                "revalidation_required": True,
                "history": [
                    {
                        "sequence": 1,
                        "from_status": None,
                        "to_status": "staged-implementation",
                        "transition_type": "initial-registration",
                        "recorded_at": "2026-07-28T22:00:00-05:00",
                        "actor": "repository-workflow",
                        "reason": "Initial staged implementation.",
                        "validation_references": [
                            "commit:" + ("1" * 40)
                        ],
                        "candidate_commit": "1" * 40,
                    }
                ],
            }
        ],
    }


def run_self_tests() -> list[str]:
    failures: list[str] = []
    policy = representative_policy()
    candidates = representative_candidate_registry()
    lifecycles = representative_lifecycle_registry()

    failures.extend(validate_policy(policy))
    failures.extend(validate_candidate_registry(candidates))
    failures.extend(
        validate_lifecycle_registry(
            lifecycles,
            candidates,
            policy,
        )
    )

    original_candidates = copy.deepcopy(candidates)
    original_lifecycles = copy.deepcopy(lifecycles)

    try:
        plan_transition(
            candidates,
            lifecycles,
            policy,
            change_id="SAGE-CHANGE-20260728-001",
            to_status="active",
            actor="self-test",
            reason="Closed gate must block activation.",
            validation_references=["self-test"],
            recorded_at="2026-07-28T22:10:00-05:00",
            candidate_commit="2" * 40,
            current_branch=(
                "feature/sage-continuous-improvement"
            ),
            remote_head="2" * 40,
            expected_head="2" * 40,
            today=date(2026, 7, 28),
        )
        failures.append("closed gate activation was accepted")
    except ValueError as error:
        if "deployment gate is closed" not in str(error):
            failures.append(
                "closed gate failure reason changed"
            )

    active_candidates = copy.deepcopy(candidates)
    active_candidate = active_candidates["candidates"][0]
    active_candidate["deployment_gate"]["status"] = "open"
    active_candidate["predictions"].append(
        {
            "stage": "pre-deployment",
            "version": 1,
        }
    )

    try:
        planned_candidates, planned_lifecycles, event = (
            plan_transition(
                active_candidates,
                lifecycles,
                policy,
                change_id="SAGE-CHANGE-20260728-001",
                to_status="active",
                actor="self-test",
                reason="All activation controls passed.",
                validation_references=[
                    "self-test:guardrails-pass"
                ],
                recorded_at="2026-07-28T22:10:00-05:00",
                candidate_commit="2" * 40,
                current_branch=(
                    "feature/sage-continuous-improvement"
                ),
                remote_head="2" * 40,
                expected_head="2" * 40,
                today=date(2026, 7, 28),
            )
        )
        if planned_candidates["candidates"][0]["status"] != "active":
            failures.append("planned candidate status changed")
        if planned_lifecycles["lifecycles"][0][
            "current_status"
        ] != "active":
            failures.append("planned lifecycle status changed")
        if event["sequence"] != 2:
            failures.append("planned event sequence changed")
    except ValueError as error:
        failures.append(
            f"valid activation plan failed: {error}"
        )

    if candidates != original_candidates:
        failures.append("dry-run planning mutated candidates")
    if lifecycles != original_lifecycles:
        failures.append("dry-run planning mutated lifecycles")

    try:
        plan_transition(
            candidates,
            lifecycles,
            policy,
            change_id="SAGE-CHANGE-20260728-001",
            to_status="closed",
            actor="self-test",
            reason="Invalid transition.",
            validation_references=["self-test"],
            recorded_at="2026-07-28T22:10:00-05:00",
            candidate_commit="2" * 40,
            current_branch=(
                "feature/sage-continuous-improvement"
            ),
            remote_head="2" * 40,
            expected_head="2" * 40,
            today=date(2026, 7, 28),
        )
        failures.append("invalid transition was accepted")
    except ValueError:
        pass

    mismatched = copy.deepcopy(lifecycles)
    mismatched["lifecycles"][0]["current_status"] = "active"
    if not validate_lifecycle_registry(
        mismatched,
        candidates,
        policy,
    ):
        failures.append("status mismatch negative test failed")

    sequence_gap = copy.deepcopy(lifecycles)
    sequence_gap["lifecycles"][0]["history"][0][
        "sequence"
    ] = 2
    if not validate_lifecycle_registry(
        sequence_gap,
        candidates,
        policy,
    ):
        failures.append("sequence-gap negative test failed")
    return failures


def render_status(
    candidate: dict[str, Any],
    lifecycle: dict[str, Any],
) -> None:
    print("Kalaxy3 SAGE candidate lifecycle: PASS")
    print(f"Change ID: {candidate['change_id']}")
    print(f"Status: {candidate['status']}")
    print(f"Branch: {candidate['branch']}")
    print(
        "Deployment gate: "
        f"{candidate['deployment_gate']['status']}"
    )
    print(
        "Revalidation valid until: "
        f"{candidate['revalidation']['valid_until']}"
    )
    print(
        "Lifecycle events: "
        f"{len(lifecycle['history'])}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage SAGE candidate lifecycle transitions"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--change-id")
    parser.add_argument("--to-status")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument(
        "--validation-reference",
        action="append",
        default=[],
    )
    parser.add_argument("--recorded-at")
    parser.add_argument("--expected-head")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        failures = run_self_tests()
        if failures:
            print(
                "Kalaxy3 SAGE candidate lifecycle self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS canonical candidate lifecycle policy")
        print("PASS append-only contiguous transition history")
        print("PASS dry-run transition planning")
        print("PASS closed deployment gate blocks activation")
        print("PASS pre-deployment prediction required")
        print("PASS branch, remote, and expected HEAD checks")
        print("PASS lifecycle mutation negative tests")
        print(
            "Kalaxy3 SAGE candidate lifecycle self-test: PASS"
        )
        return 0

    try:
        policy = load_json(POLICY_PATH)
        candidates = load_json(CANDIDATE_REGISTRY_PATH)
        lifecycles = load_json(LIFECYCLE_REGISTRY_PATH)

        failures = []
        failures.extend(validate_policy(policy))
        failures.extend(validate_candidate_registry(candidates))
        failures.extend(
            validate_lifecycle_registry(
                lifecycles,
                candidates,
                policy,
            )
        )
        if failures:
            raise ValueError("; ".join(failures))

        if not args.change_id:
            raise ValueError("--change-id is required")

        candidate = candidate_by_id(
            candidates,
            args.change_id,
        )
        lifecycle = lifecycle_by_id(
            lifecycles,
            args.change_id,
        )

        if args.status:
            render_status(candidate, lifecycle)
            return 0

        if not args.to_status:
            raise ValueError(
                "use --status or provide --to-status"
            )

        head = git_output("rev-parse", "HEAD")
        branch = git_output("branch", "--show-current")
        remote_head = git_output(
            "rev-parse",
            f"origin/{candidate['branch']}",
        )
        recorded_at = (
            args.recorded_at
            or datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
        )
        expected_head = args.expected_head or ""

        planned_candidates, planned_lifecycles, event = (
            plan_transition(
                candidates,
                lifecycles,
                policy,
                change_id=args.change_id,
                to_status=args.to_status,
                actor=args.actor or "",
                reason=args.reason or "",
                validation_references=(
                    args.validation_reference
                ),
                recorded_at=recorded_at,
                candidate_commit=head,
                current_branch=branch,
                remote_head=remote_head,
                expected_head=expected_head,
                today=date.today(),
            )
        )

        print(
            json.dumps(
                {
                    "mode": "apply" if args.apply else "dry-run",
                    "event": event,
                },
                indent=4,
            )
        )

        if not args.apply:
            print(
                "DRY RUN: no candidate or lifecycle files changed"
            )
            return 0

        if git_output("status", "--porcelain"):
            raise ValueError(
                "working tree must be clean before --apply"
            )

        write_registry_pair(
            planned_candidates,
            planned_lifecycles,
        )
        print(
            "APPLIED candidate and lifecycle registry transition"
        )
        return 0
    except (
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        TypeError,
    ) as error:
        print(
            "Kalaxy3 SAGE candidate lifecycle: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
