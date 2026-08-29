#!/usr/bin/env python3
"""Run one governed SAGE improvement-action lifecycle transition."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError
from workflows.improvement_action_transition import (
    consume_recovery_decision,
    self_test,
    start_transition,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--action-id")
    parser.add_argument("--to-status")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument(
        "--evidence-reference",
        action="append",
        default=[],
    )
    parser.add_argument("--commit-message")
    parser.add_argument("--push-remote", default="origin")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--recovery-decision", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def required(value: str | None, label: str) -> str:
    """Require one non-empty CLI value."""

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value.strip()


def run_recovery_boundary(args: argparse.Namespace) -> int:
    """Continue one lifecycle-owned recovery decision."""

    result = consume_recovery_decision(
        repo=args.repo,
        recovery_decision_path=args.recovery_decision,
        output=args.output,
    )
    status = result.get("status")
    if status == "architect-decision-required":
        print("Kalaxy3 SAGE improvement-action successor boundary: PASS")
        print(json.dumps(result, indent=2))
        print("Next Architect boundary:")
        print("  Review and authorize the emitted successor capability-gap/action boundary.")
        print("Repository mutation: none")
        return 0
    if status == "consumed":
        print("Kalaxy3 SAGE implementation-local recovery: PASS")
        print(json.dumps(result, indent=2))
        print("Next governed boundary:")
        print("  Retry the exact failed lifecycle request without changing its wording.")
        print("Repository mutation: none")
        return 0
    raise WorkflowError(f"unsupported recovery continuation status: {status}")


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.recovery_decision is not None:
        return run_recovery_boundary(args)
    request = required(args.request, "--request")
    action_id = required(args.action_id, "--action-id")
    to_status = required(args.to_status, "--to-status")
    actor = required(args.actor, "--actor")
    reason = required(args.reason, "--reason")
    commit_message = required(
        args.commit_message,
        "--commit-message",
    )
    references = tuple(
        item.strip()
        for item in args.evidence_reference
        if isinstance(item, str) and item.strip()
    )
    if not references:
        raise ValueError(
            "at least one --evidence-reference is required"
        )
    result = start_transition(
        repo=args.repo,
        request=request,
        action_id=action_id,
        to_status=to_status,
        actor=actor,
        reason=reason,
        evidence_references=references,
        commit_message=commit_message,
        push_remote=required(args.push_remote, "--push-remote"),
    )
    print(
        "Kalaxy3 SAGE improvement-action transition: PASS"
    )
    print(json.dumps(result, indent=2))
    print("Next operator boundary:")
    proposal = json.loads(
        Path(str(result["proposal"])).read_text(
            encoding="utf-8"
        )
    )
    print(f"  {proposal['command']['display']}")
    print(
        "Stop after that one operator command and paste its complete output."
    )
    print(
        "Then bind the result to the emitted state and resume through "
        "make sage-request-continue."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
        WorkflowError,
        RuntimeError,
    ) as error:
        print(
            "Kalaxy3 SAGE improvement-action transition: FAIL CLOSED",
            file=sys.stderr,
        )
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
