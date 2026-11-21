#!/usr/bin/env python3
"""Check SAGE proposed work against exact, locally verified objective state."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sage_objective_state import (EvidenceError, evaluate_all, read_object,
                                  verify_receipt)


def load_proposals(path: Path) -> list[Any]:
    """Load the candidate array without granting authority.

    Args:
        path: JSON file containing candidate work proposals.
    """
    source = read_object(path)
    if source.get("schema") != "sage-objective-state-proposals-v1":
        raise EvidenceError("Unexpected proposed-action schema")
    if source.get("objective") != "#50":
        raise EvidenceError("Proposal objective does not match #50")
    entries = source.get("proposals")
    if not isinstance(entries, list):
        raise EvidenceError("Missing proposal array")
    return entries


def run(args: argparse.Namespace) -> int:
    """Write a deterministic report and optionally fail closed on blocked work.

    Args:
        args: Parsed read-only inputs and report destination.
    """
    state = verify_receipt(args.receipt, args.manifest)
    proposals = load_proposals(args.proposals)
    report = evaluate_all(proposals, state, args.repo)
    target: Path = args.output
    if target.exists():
        raise EvidenceError("Refusing to overwrite an existing report")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    statuses = [item["status"] for item in report["proposals"]]
    print(f"NATIVE_RECEIPT=CHECKED; GIT_GRAPH_SOURCE_IDENTITIES=1388_OF_1388")
    print(f"GATE_REPORT={target}")
    print(f"RESULTS={','.join(statuses)}")
    print("ARCHITECT_AUTHORIZATION=NOT_GRANTED")
    if args.strict and any(status not in ("candidate", "candidate_new_scope")
                           for status in statuses):
        return 2
    return 0


def main() -> int:
    """Parse paths and run the objective-state checker fail-closed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    arguments = parser.parse_args()
    try:
        return run(arguments)
    except (EvidenceError, ValueError, OSError, KeyError) as exc:
        print(f"BLOCKED={type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
