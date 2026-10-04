#!/usr/bin/env python3
"""Generate the first governed SAGE engineering candidate through a fresh role."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import WorkflowError
from workflows.fresh_candidate_generation import (
    generate_first_candidate,
    run_contract_self_test,
)


def parse_args() -> argparse.Namespace:
    """Parse first-candidate generation arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action-id")
    parser.add_argument("--request")
    parser.add_argument("--readiness", type=Path)
    parser.add_argument("--strawman", type=Path)
    parser.add_argument("--strawman-provenance", type=Path)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run self-test or create a fresh-role-authored first candidate."""
    args = parse_args()
    if args.self_test:
        run_contract_self_test()
        print("Kalaxy3 SAGE first-candidate generation self-test: PASS")
        return 0
    if not args.action_id or not args.request or args.readiness is None:
        raise WorkflowError("--action-id, --request, and --readiness are required")
    result = generate_first_candidate(
        args.repo,
        args.action_id,
        args.request,
        readiness=args.readiness,
        strawman=args.strawman,
        strawman_provenance=args.strawman_provenance,
    )
    if result.get("status") == "capability-blocked":
        print("Kalaxy3 SAGE first-candidate generation: FAIL CLOSED", file=sys.stderr)
        print(json.dumps(result, indent=2, sort_keys=False), file=sys.stderr)
        return 2
    print("Kalaxy3 SAGE first-candidate generation: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, WorkflowError, RuntimeError) as error:
        print("Kalaxy3 SAGE first-candidate generation: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
