#!/usr/bin/env python3
"""Validate the reusable LLM architecture-approval evaluation service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from architecture_approval import self_test, service_contract  # noqa: E402
from workflow import WorkflowError  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--show-contract", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run one architecture-evaluation service operation."""
    args = parse_args()
    if args.self_test:
        self_test()
        service_contract(args.repo)
        print(
            "Kalaxy3 SAGE architecture approval evaluation self-test: PASS"
        )
        return 0
    if args.show_contract:
        print(json.dumps(service_contract(args.repo), indent=2, sort_keys=False))
        return 0
    raise WorkflowError("choose --self-test or --show-contract")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError) as error:
        print(
            "Kalaxy3 SAGE architecture approval evaluation: FAIL CLOSED",
            file=sys.stderr,
        )
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
