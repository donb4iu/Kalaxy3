#!/usr/bin/env python3
"""Manage SAGE improvement-action lifecycle records safely."""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Sequence

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
REGISTRY_PATH: Final = ROOT / "sage-improvement-actions.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def parse_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            "recorded_at must be an ISO-8601 timestamp"
        ) from error


def validate_policy(policy: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(policy, dict):
        return ["policy must be an object"]

    lifecycle = policy.get(
        "improvement_action_lifecycle_policy"
    )
    if not isinstance(lifecycle, dict):
        return [
            "improvement_action_lifecycle_policy "
            "must be an object"
        ]

    if lifecycle.get("statuses") != policy.get(
        "improvement_action_statuses"
    ):
        failures.append(
            "action lifecycle statuses must match policy"
        )

    statuses = set(lifecycle.get("statuses", []))
    transitions = lifecycle.get("allowed_transitions")
    if not isinstance(transitions, dict):
        failures.append("action allowed_transitions missing")
    elif set(transitions) != statuses:
        failures.append(
            "action transitions must cover every status"
        )
    else:
        for source, targets in transitions.items():
            if (
                not isinstance(targets, list)
                or len(targets) != len(set(targets))
                or not set(targets).issubset(statuses)
            ):
                failures.append(
                    f"invalid action transitions for {source}"
                )

    expected_terminal = ["closed", "rejected"]
    if lifecycle.get("terminal_statuses") != expected_terminal:
        failures.append("action terminal statuses changed")

    for key in (
        "history_append_only",
        "dry_run_default",
        "apply_requires_explicit_flag",
        "atomic_write_required",
        "direct_status_edits_forbidden",
        "registration_requires_source",
    ):
        if lifecycle.get(key) is not True:
            failures.append(
                f"improvement_action_lifecycle_policy.{key} "
                "must be true"
            )

    if lifecycle.get("initial_status") != "identified":
        failures.append("action initial status changed")
    return failures


def validate_registry(
    registry: Any,
    policy: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(registry, dict):
        return ["action registry must be an object"]
    if registry.get("schema_version") != "1.0":
        failures.append(
            "action registry schema_version must be 1.0"
        )
    if registry.get("registry_type") != "improvement-actions":
        failures.append(
            "action registry_type must be improvement-actions"
        )

    actions = registry.get("actions")
    if not isinstance(actions, list):
        failures.append("actions must be a list")
        return failures

    statuses = set(policy["improvement_action_statuses"])
    allowed = policy[
        "improvement_action_lifecycle_policy"
    ]["allowed_transitions"]
    identifiers: list[str] = []

    for item in actions:
        if not isinstance(item, dict):
            failures.append("action entry must be an object")
            continue

        required = {
            "action_id",
            "title",
            "source_lessons",
            "source_sessions",
            "current_status",
            "owner",
            "priority",
            "target_control_type",
            "desired_outcome",
            "acceptance_criteria",
            "measurement_plan",
            "history",
        }
        if set(item) != required:
            failures.append(
                "action fields must match the contract"
            )

        action_id = str(item.get("action_id", ""))
        identifiers.append(action_id)

        for key in (
            "title",
            "owner",
            "desired_outcome",
        ):
            try:
                require_string(item.get(key), f"{action_id} {key}")
            except ValueError as error:
                failures.append(str(error))

        lessons = item.get("source_lessons")
        sessions = item.get("source_sessions")
        if not isinstance(lessons, list):
            failures.append(
                f"{action_id}: source_lessons must be a list"
            )
            lessons = []
        if not isinstance(sessions, list):
            failures.append(
                f"{action_id}: source_sessions must be a list"
            )
            sessions = []
        if not lessons and not sessions:
            failures.append(
                f"{action_id}: at least one source is required"
            )
        for label, values in (
            ("source_lessons", lessons),
            ("source_sessions", sessions),
        ):
            if (
                len(values) != len(set(values))
                or not all(
                    isinstance(value, str) and value
                    for value in values
                )
            ):
                failures.append(
                    f"{action_id}: {label} invalid"
                )

        status = item.get("current_status")
        if status not in statuses:
            failures.append(
                f"{action_id}: current_status invalid"
            )

        if item.get("priority") not in (
            "low",
            "medium",
            "high",
            "critical",
        ):
            failures.append(f"{action_id}: priority invalid")

        if item.get("target_control_type") not in (
            "manual",
            "template",
            "preflight",
            "guardrail",
            "runbook",
            "automation",
            "no-action",
        ):
            failures.append(
                f"{action_id}: target_control_type invalid"
            )

        for key in (
            "acceptance_criteria",
            "measurement_plan",
        ):
            values = item.get(key)
            if (
                not isinstance(values, list)
                or not values
                or not all(
                    isinstance(value, str) and value
                    for value in values
                )
            ):
                failures.append(
                    f"{action_id}: {key} must be non-empty"
                )

        history = item.get("history")
        if not isinstance(history, list) or not history:
            failures.append(
                f"{action_id}: history must be non-empty"
            )
            continue

        previous_status: str | None = None
        previous_time: datetime | None = None
        for index, event in enumerate(history, start=1):
            if not isinstance(event, dict):
                failures.append(
                    f"{action_id}: history event invalid"
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
                "evidence_references",
            }
            if set(event) != event_required:
                failures.append(
                    f"{action_id}: event fields invalid"
                )
            if event.get("sequence") != index:
                failures.append(
                    f"{action_id}: event sequence not contiguous"
                )

            source = event.get("from_status")
            target = event.get("to_status")
            event_type = event.get("transition_type")
            if index == 1:
                if source is not None:
                    failures.append(
                        f"{action_id}: initial source must be null"
                    )
                if target != "identified":
                    failures.append(
                        f"{action_id}: initial status must be identified"
                    )
                if event_type != "initial-registration":
                    failures.append(
                        f"{action_id}: initial event type invalid"
                    )
            else:
                if source != previous_status:
                    failures.append(
                        f"{action_id}: event chain not contiguous"
                    )
                if event_type != "status-transition":
                    failures.append(
                        f"{action_id}: transition event type invalid"
                    )
                if (
                    source not in allowed
                    or target not in allowed[source]
                ):
                    failures.append(
                        f"{action_id}: transition "
                        f"{source} -> {target} not allowed"
                    )

            for key in ("actor", "reason"):
                try:
                    require_string(
                        event.get(key),
                        f"{action_id} event {key}",
                    )
                except ValueError as error:
                    failures.append(str(error))

            references = event.get("evidence_references")
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
                    f"{action_id}: evidence references invalid"
                )

            try:
                parsed = datetime.fromisoformat(
                    str(event.get("recorded_at", "")).replace(
                        "Z",
                        "+00:00",
                    )
                )
                if (
                    previous_time is not None
                    and parsed < previous_time
                ):
                    failures.append(
                        f"{action_id}: timestamps regress"
                    )
                previous_time = parsed
            except ValueError:
                failures.append(
                    f"{action_id}: recorded_at invalid"
                )

            previous_status = str(target)

        if previous_status != status:
            failures.append(
                f"{action_id}: final event and status differ"
            )

    if len(identifiers) != len(set(identifiers)):
        failures.append("action identifiers must be unique")
    return failures


def action_by_id(
    registry: dict[str, Any],
    action_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in registry.get("actions", [])
        if isinstance(item, dict)
        and item.get("action_id") == action_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"action {action_id} must appear exactly once"
        )
    return matches[0]


def plan_registration(
    registry: dict[str, Any],
    policy: dict[str, Any],
    draft: dict[str, Any],
    *,
    recorded_at: str,
    actor: str,
    reason: str,
    evidence_references: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = {
        "action_id",
        "title",
        "source_lessons",
        "source_sessions",
        "owner",
        "priority",
        "target_control_type",
        "desired_outcome",
        "acceptance_criteria",
        "measurement_plan",
    }
    if set(draft) != required:
        raise ValueError("registration draft fields invalid")
    if any(
        item.get("action_id") == draft["action_id"]
        for item in registry["actions"]
        if isinstance(item, dict)
    ):
        raise ValueError("action_id already exists")

    require_string(actor, "actor")
    require_string(reason, "reason")
    parse_timestamp(recorded_at)
    if (
        not evidence_references
        or len(evidence_references)
        != len(set(evidence_references))
        or not all(
            isinstance(value, str) and value
            for value in evidence_references
        )
    ):
        raise ValueError("evidence references invalid")

    updated = copy.deepcopy(registry)
    action = copy.deepcopy(draft)
    action["current_status"] = "identified"
    action["history"] = [
        {
            "sequence": 1,
            "from_status": None,
            "to_status": "identified",
            "transition_type": "initial-registration",
            "recorded_at": recorded_at,
            "actor": actor,
            "reason": reason,
            "evidence_references": list(
                evidence_references
            ),
        }
    ]
    ordered = {
        key: action[key]
        for key in (
            "action_id",
            "title",
            "source_lessons",
            "source_sessions",
            "current_status",
            "owner",
            "priority",
            "target_control_type",
            "desired_outcome",
            "acceptance_criteria",
            "measurement_plan",
            "history",
        )
    }
    updated["actions"].append(ordered)

    failures = validate_registry(updated, policy)
    if failures:
        raise ValueError(
            "planned registration invalid: "
            + "; ".join(failures)
        )
    return updated, ordered


def plan_transition(
    registry: dict[str, Any],
    policy: dict[str, Any],
    *,
    action_id: str,
    to_status: str,
    recorded_at: str,
    actor: str,
    reason: str,
    evidence_references: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    action = action_by_id(registry, action_id)
    source = str(action["current_status"])
    allowed = policy[
        "improvement_action_lifecycle_policy"
    ]["allowed_transitions"]
    if (
        source not in allowed
        or to_status not in allowed[source]
    ):
        raise ValueError(
            f"transition {source} -> {to_status} is not allowed"
        )

    require_string(actor, "actor")
    require_string(reason, "reason")
    parse_timestamp(recorded_at)
    if (
        not evidence_references
        or len(evidence_references)
        != len(set(evidence_references))
        or not all(
            isinstance(value, str) and value
            for value in evidence_references
        )
    ):
        raise ValueError("evidence references invalid")

    updated = copy.deepcopy(registry)
    changed = action_by_id(updated, action_id)
    event = {
        "sequence": len(changed["history"]) + 1,
        "from_status": source,
        "to_status": to_status,
        "transition_type": "status-transition",
        "recorded_at": recorded_at,
        "actor": actor,
        "reason": reason,
        "evidence_references": list(evidence_references),
    }
    changed["current_status"] = to_status
    changed["history"].append(event)

    failures = validate_registry(updated, policy)
    if failures:
        raise ValueError(
            "planned transition invalid: "
            + "; ".join(failures)
        )
    return updated, event


def atomic_write(registry: dict[str, Any]) -> None:
    original = REGISTRY_PATH.read_text(encoding="utf-8")
    text = json.dumps(registry, indent=4) + "\n"

    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-sage-actions-",
        dir=ROOT,
    ) as temp_dir:
        temp_path = Path(temp_dir) / "actions.json"
        temp_path.write_text(text, encoding="utf-8")
        try:
            os.replace(temp_path, REGISTRY_PATH)
        except OSError:
            REGISTRY_PATH.write_text(
                original,
                encoding="utf-8",
            )
            raise


def representative_policy() -> dict[str, Any]:
    statuses = [
        "identified",
        "accepted",
        "implemented",
        "validated",
        "measured",
        "closed",
        "rejected",
    ]
    return {
        "improvement_action_statuses": statuses,
        "improvement_action_lifecycle_policy": {
            "statuses": statuses,
            "allowed_transitions": {
                "identified": ["accepted", "rejected"],
                "accepted": ["implemented", "rejected"],
                "implemented": ["accepted", "validated"],
                "validated": ["implemented", "measured"],
                "measured": ["validated", "closed"],
                "closed": [],
                "rejected": [],
            },
            "initial_status": "identified",
            "terminal_statuses": ["closed", "rejected"],
            "history_append_only": True,
            "dry_run_default": True,
            "apply_requires_explicit_flag": True,
            "atomic_write_required": True,
            "direct_status_edits_forbidden": True,
            "registration_requires_source": True,
        },
    }


def representative_draft() -> dict[str, Any]:
    return {
        "action_id": "SAGE-ACTION-20260728-001",
        "title": "Require downloadable implementation scripts",
        "source_lessons": [
            "SAGE-LESSON-20260728-001",
        ],
        "source_sessions": [],
        "owner": "repository-workflow",
        "priority": "high",
        "target_control_type": "template",
        "desired_outcome": (
            "Prevent interactive heredoc failures."
        ),
        "acceptance_criteria": [
            "Large terminal payloads are delivered as scripts.",
        ],
        "measurement_plan": [
            "Measure heredoc failure recurrence.",
        ],
    }


def run_self_tests() -> list[str]:
    failures: list[str] = []
    policy = representative_policy()
    registry = {
        "schema_version": "1.0",
        "registry_type": "improvement-actions",
        "actions": [],
    }

    failures.extend(validate_policy(policy))
    failures.extend(validate_registry(registry, policy))

    original = copy.deepcopy(registry)
    try:
        registered, action = plan_registration(
            registry,
            policy,
            representative_draft(),
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Register an evidence-backed action.",
            evidence_references=[
                "SAGE-LESSON-20260728-001",
            ],
        )
        if action["current_status"] != "identified":
            failures.append("initial action status changed")

        accepted, event = plan_transition(
            registered,
            policy,
            action_id=action["action_id"],
            to_status="accepted",
            recorded_at="2026-07-28T23:01:00-05:00",
            actor="self-test",
            reason="Accept the improvement action.",
            evidence_references=["self-test:accepted"],
        )
        if event["sequence"] != 2:
            failures.append("action transition sequence changed")
        if accepted["actions"][0][
            "current_status"
        ] != "accepted":
            failures.append("accepted action status changed")
    except ValueError as error:
        failures.append(f"valid action lifecycle failed: {error}")

    if registry != original:
        failures.append("dry-run planning mutated registry")

    no_source = representative_draft()
    no_source["source_lessons"] = []
    try:
        plan_registration(
            registry,
            policy,
            no_source,
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Invalid source-free action.",
            evidence_references=["self-test"],
        )
        failures.append("source-free action was accepted")
    except ValueError:
        pass

    try:
        registered, _ = plan_registration(
            registry,
            policy,
            representative_draft(),
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Register action.",
            evidence_references=["self-test"],
        )
        plan_transition(
            registered,
            policy,
            action_id="SAGE-ACTION-20260728-001",
            to_status="closed",
            recorded_at="2026-07-28T23:01:00-05:00",
            actor="self-test",
            reason="Invalid jump.",
            evidence_references=["self-test"],
        )
        failures.append("invalid action transition accepted")
    except ValueError:
        pass

    altered = copy.deepcopy(policy)
    altered["improvement_action_lifecycle_policy"][
        "dry_run_default"
    ] = False
    if not validate_policy(altered):
        failures.append("non-dry-run action policy accepted")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage SAGE improvement actions"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--register-file", type=Path)
    parser.add_argument("--action-id")
    parser.add_argument("--to-status")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument(
        "--evidence-reference",
        action="append",
        default=[],
    )
    parser.add_argument("--recorded-at")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        failures = run_self_tests()
        if failures:
            print(
                "Kalaxy3 SAGE improvement-action self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS canonical improvement-action lifecycle")
        print("PASS evidence-backed registration")
        print("PASS append-only contiguous action history")
        print("PASS dry-run registration and transition planning")
        print("PASS explicit apply required for mutation")
        print("PASS invalid transitions fail closed")
        print(
            "Kalaxy3 SAGE improvement-action self-test: PASS"
        )
        return 0

    try:
        policy = load_json(POLICY_PATH)
        registry = load_json(REGISTRY_PATH)
        failures = validate_policy(policy)
        failures.extend(validate_registry(registry, policy))
        if failures:
            raise ValueError("; ".join(failures))

        if args.status:
            print("Kalaxy3 SAGE improvement actions: PASS")
            print(f"Actions: {len(registry['actions'])}")
            for action in registry["actions"]:
                print(
                    f"  - {action['action_id']}: "
                    f"{action['current_status']} — "
                    f"{action['title']}"
                )
            return 0

        recorded_at = (
            args.recorded_at
            or datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
        )

        if args.register_file is not None:
            draft = load_json(args.register_file)
            planned, event = plan_registration(
                registry,
                policy,
                draft,
                recorded_at=recorded_at,
                actor=args.actor or "",
                reason=args.reason or "",
                evidence_references=(
                    args.evidence_reference
                ),
            )
        else:
            if not args.action_id or not args.to_status:
                raise ValueError(
                    "use --status, --register-file, "
                    "or provide --action-id and --to-status"
                )
            planned, event = plan_transition(
                registry,
                policy,
                action_id=args.action_id,
                to_status=args.to_status,
                recorded_at=recorded_at,
                actor=args.actor or "",
                reason=args.reason or "",
                evidence_references=(
                    args.evidence_reference
                ),
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
            print("DRY RUN: action registry unchanged")
            return 0

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if status:
            raise ValueError(
                "working tree must be clean before --apply"
            )

        atomic_write(planned)
        print("APPLIED improvement-action registry mutation")
        return 0
    except (
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        TypeError,
    ) as error:
        print(
            "Kalaxy3 SAGE improvement actions: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
