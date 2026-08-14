#!/usr/bin/env python3
"""Invoke the repository-owned bounded routine Git lifecycle controller."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError  # noqa: E402
from workflows.request_execution import continue_request_from_routine_receipt  # noqa: E402
from workflows.routine_git_lifecycle import run_controller  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(__file__).resolve().parents[2]
    result = run_controller(
        repo,
        args.state,
        args.proposal,
        apply=args.apply,
    )
    continuation = continue_request_from_routine_receipt(
        repo,
        args.state,
        Path(str(result["receipt"])),
    )
    if continuation.get("status") != "complete" or continuation.get("proposal") is not None:
        raise WorkflowError("routine Git lifecycle receipt did not deterministically close request execution")
    print("Kalaxy3 SAGE routine Git lifecycle: PASS")
    print(f"Commit: {result['commit']}")
    print(f"Remote branch: {result['remote']}/{result['branch']}={result['remote_branch_head']}")
    print(f"Receipt: {result['receipt']}")
    print(f"Receipt SHA-256: {result['receipt_sha256']}")
    print(f"Post-operator verification: {continuation['verification']}")
    print(f"Outcome metrics: {continuation['metrics']}")
    print(f"Evidence closeout: {continuation['evidence_closeout']}")
    print(f"Request state: {continuation['state']}")
    print("Repository Git lifecycle: COMPLETE")
    print("No next operator mutation boundary.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, json.JSONDecodeError, WorkflowError) as error:
        print("Kalaxy3 SAGE routine Git lifecycle: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
