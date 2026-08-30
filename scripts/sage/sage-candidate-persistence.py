#!/usr/bin/env python3
"""Authorize or verify bounded pre-semantic candidate persistence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from workflow import WorkflowError
from workflows.candidate_persistence import self_test, start, verify


def args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    begin = sub.add_parser("start")
    begin.add_argument("--path", action="append", required=True)
    begin.add_argument("--commit-message", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--state", type=Path, required=True)
    check.add_argument("--receipt", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    """Run one candidate-persistence operation."""
    parsed = args()
    if parsed.self_test:
        self_test()
        print("Kalaxy3 SAGE candidate persistence self-test: PASS")
        return 0
    if parsed.command == "start":
        result = start(parsed.repo, parsed.path, parsed.commit_message)
    elif parsed.command == "verify":
        result = verify(parsed.repo, parsed.state, parsed.receipt)
    else:
        raise WorkflowError("candidate persistence command is required")
    print("Kalaxy3 SAGE candidate persistence: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except WorkflowError as error:
        print("Kalaxy3 SAGE candidate persistence: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
