
#!/usr/bin/env python3
"""Operate the repository-owned SAGE intent-to-outcome front door."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError  # noqa: E402
from workflows.intent_to_outcome import (  # noqa: E402
    adopt_iteration,
    adopt_request_execution,
    begin_candidate_iteration,
    begin_intent,
    begin_intent_promotion,
    confirm_intent,
    continue_intent_promotion,
    continue_intent_request,
    record_runtime,
    validate_runtime_receipt,
)


def self_test() -> int:
    good = {
        "schema_version": "1.0",
        "record_type": "sage-e2e-zero-trust-runtime-receipt",
        "status": "pass",
        "checks": {
            "workload_ready": True,
            "origin_through_traefik_ready": True,
            "tunnel_ready": True,
            "metrics_monitor_configured": True,
            "unauthenticated_access_denied": True,
            "authorized_mfa_access_verified": True,
            "privileged_surfaces_not_published": True,
        },
    }
    validate_runtime_receipt(good)
    bad = json.loads(json.dumps(good))
    bad["checks"]["authorized_mfa_access_verified"] = False
    try:
        validate_runtime_receipt(bad)
    except WorkflowError:
        pass
    else:
        raise RuntimeError("missing MFA runtime proof was accepted")
    print("PASS runtime acceptance requires MFA and negative-access proof")
    print("PASS intent-to-outcome front door self-test")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start")
    start.add_argument("--request", required=True)
    start.add_argument("--action-id", required=True)
    start.add_argument("--contribution", type=Path, required=True)

    confirm = sub.add_parser("confirm")
    confirm.add_argument("--state", type=Path, required=True)
    confirm.add_argument("--confirmation", required=True)
    confirm.add_argument("--dispositions", type=Path, required=True)
    confirm.add_argument("--actor", required=True)

    adopt = sub.add_parser("adopt-request")
    adopt.add_argument("--request", required=True)
    adopt.add_argument("--request-state", type=Path, required=True)

    adopt_iteration_parser = sub.add_parser("adopt-iteration")
    adopt_iteration_parser.add_argument("--request", required=True)
    adopt_iteration_parser.add_argument("--request-state", type=Path, required=True)
    adopt_iteration_parser.add_argument("--action-id")
    adopt_iteration_parser.add_argument("--candidate-head")
    adopt_iteration_parser.add_argument("--unresolved-finding", action="append", default=[])

    iterate = sub.add_parser("iterate")
    iterate.add_argument("--state", type=Path, required=True)
    iterate.add_argument("--contribution", type=Path, required=True)
    iterate.add_argument("--trigger", required=True)
    iterate.add_argument(
        "--reentry-boundary",
        choices=("implementation-local", "planning", "semantic-confirmation", "authority"),
        required=True,
    )
    iterate.add_argument("--parent-checkpoint", required=True)
    iterate.add_argument("--affected-obligation", action="append", default=[])

    continuation = sub.add_parser("continue-request")
    continuation.add_argument("--state", type=Path, required=True)
    continuation.add_argument("--operator-result", type=Path)
    continuation.add_argument("--routine-receipt", type=Path)

    runtime = sub.add_parser("record-runtime")
    runtime.add_argument("--state", type=Path, required=True)
    runtime.add_argument("--runtime-receipt", type=Path, required=True)

    promote = sub.add_parser("promote")
    promote.add_argument("--state", type=Path, required=True)
    promote.add_argument("--expected-head", required=True)
    promote.add_argument("--title", required=True)
    promote.add_argument("--body", required=True)

    promotion = sub.add_parser("continue-promotion")
    promotion.add_argument("--state", type=Path, required=True)
    promotion.add_argument("--operator-result", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.command == "start":
        result = begin_intent(args.repo, args.action_id, args.request, args.contribution)
    elif args.command == "confirm":
        result = confirm_intent(
            args.repo, args.state, args.confirmation, args.dispositions, args.actor
        )
    elif args.command == "adopt-request":
        result = adopt_request_execution(args.repo, args.request, args.request_state)
    elif args.command == "adopt-iteration":
        result = adopt_iteration(
            args.repo,
            args.request,
            args.request_state,
            action_id=args.action_id,
            candidate_head=args.candidate_head,
            unresolved_findings=args.unresolved_finding,
        )
    elif args.command == "iterate":
        result = begin_candidate_iteration(
            args.repo,
            args.state,
            args.contribution,
            trigger=args.trigger,
            reentry_boundary=args.reentry_boundary,
            parent_checkpoint=args.parent_checkpoint,
            affected_obligations=args.affected_obligation,
        )
    elif args.command == "continue-request":
        result = continue_intent_request(
            args.repo,
            args.state,
            operator_result=args.operator_result,
            routine_receipt=args.routine_receipt,
        )
    elif args.command == "record-runtime":
        result = record_runtime(args.state, args.runtime_receipt)
    elif args.command == "promote":
        result = begin_intent_promotion(
            args.repo, args.state, args.expected_head, args.title, args.body
        )
    elif args.command == "continue-promotion":
        result = continue_intent_promotion(
            args.repo, args.state, args.operator_result
        )
    else:
        raise WorkflowError("one intent-to-outcome command is required")
    print("Kalaxy3 SAGE intent-to-outcome: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE intent-to-outcome: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
