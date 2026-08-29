#!/usr/bin/env python3
"""Start or continue repository-owned checkpoint promotion."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from checkpoint_promotion import PromotionError
from workflow import WorkflowError
from workflows.checkpoint_promotion import (
    continue_promotion,
    self_test,
    start_promotion,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--source-branch")
    parser.add_argument("--expected-head")
    parser.add_argument("--target-branch", default="main")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--continue-state", type=Path)
    parser.add_argument("--operator-result", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.continue_state or args.operator_result:
        if not args.continue_state or not args.operator_result:
            raise WorkflowError(
                "--continue-state and --operator-result are required together"
            )
        result = continue_promotion(
            repo=args.repo,
            state_path=args.continue_state,
            operator_result_path=args.operator_result,
        )
    else:
        required = (
            args.request,
            args.source_branch,
            args.expected_head,
            args.title,
            args.body,
        )
        if not all(required):
            raise WorkflowError(
                "--request, --source-branch, --expected-head, --title, and --body "
                "are required"
            )
        result = start_promotion(
            repo=args.repo,
            request=args.request,
            source_branch=args.source_branch,
            expected_head=args.expected_head,
            target_branch=args.target_branch,
            title=args.title,
            body=args.body,
        )
    print("Kalaxy3 SAGE checkpoint promotion: PASS")
    print(json.dumps(result, indent=2))
    if result.get("status") == "operator-review-required":
        proposal = result.get("proposal")
        print("Next operator boundary:")
        if isinstance(proposal, dict) and isinstance(proposal.get("command"), dict):
            command = proposal["command"].get("display")
            print(f"  {command}")
            print("Stop after that one operator command and paste its complete output.")
        elif isinstance(proposal, dict) and isinstance(proposal.get("browser"), dict):
            browser = proposal["browser"]
            print(f"  Browser action: {browser.get('action')}")
            print(f"  Open: {browser.get('url')}")
            print("Complete only that browser-reviewed boundary, then continue with its bound operator result.")
        else:
            raise WorkflowError("operator-review-required result lacks a command or browser proposal")
    else:
        print("Checkpoint promotion lifecycle: COMPLETE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        PromotionError,
        WorkflowError,
    ) as error:
        print("Kalaxy3 SAGE checkpoint promotion: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
