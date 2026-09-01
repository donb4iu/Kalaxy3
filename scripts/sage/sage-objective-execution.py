
#!/usr/bin/env python3
"""Operate the bounded SAGE objective-execution unit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError  # noqa: E402
from workflows.objective_execution import (  # noqa: E402
    create_closeout_plan,
    record_critic_observation,
    run_closeout_objective,
    self_test,
)


def parse_args() -> argparse.Namespace:
    """Parse objective-execution arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    plan = sub.add_parser("plan-closeout")
    plan.add_argument("--lifecycle-state", type=Path, required=True)
    plan.add_argument("--baseline-round-trips", type=int, default=6)

    run = sub.add_parser("run-closeout")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--approved-plan-sha256", required=True)

    run.add_argument(
        "--planning-critic-observation",
        type=Path,
        required=True,
    )
    critic = sub.add_parser("record-critic")
    critic.add_argument("--request", type=Path, required=True)
    critic.add_argument("--observation", type=Path, required=True)

    recover = sub.add_parser("recover")
    recover.add_argument("--recovery-decision", type=Path, required=True)
    recover.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    """Run one objective-execution operation."""
    args = parse_args()
    if args.self_test:
        self_test()
        from workflows.objective_execution import (
            objective_recovery_contract_self_test,
        )

        objective_recovery_contract_self_test(args.repo)
        print("PASS objective correction and true-replan semantics")
        print("PASS objective execution reuses shared self-directing recovery")
        print("PASS objective approval is plan-atomic, not step-atomic")
        print("PASS LLM path critic remains advisory")
        print("PASS planning critic challenges implementation before Architect approval")
        print("PASS active closeout delegates Git mechanics and records semantic lineage")
        print("Kalaxy3 SAGE objective execution self-test: PASS")
        return 0
    if args.command == "plan-closeout":
        result = create_closeout_plan(
            args.repo,
            args.lifecycle_state,
            baseline_round_trips=args.baseline_round_trips,
        )
    elif args.command == "run-closeout":
        result = run_closeout_objective(
            args.repo,
            args.plan,
            args.approved_plan_sha256,
            args.planning_critic_observation,
        )
    elif args.command == "record-critic":
        result = record_critic_observation(args.request, args.observation)
    elif args.command == "recover":
        from workflows.objective_execution import (
            consume_objective_recovery_decision,
        )

        result = consume_objective_recovery_decision(
            args.repo,
            args.recovery_decision,
            args.output,
        )
    else:
        raise WorkflowError("one objective-execution command is required")
    print("Kalaxy3 SAGE objective execution: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError) as error:
        print("Kalaxy3 SAGE objective execution: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
