#!/usr/bin/env python3
"""Govern one identified improvement-action contract amendment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from workflow import WorkflowError
from workflows.improvement_action_transition import self_test, start_amendment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--amend-file", type=Path)
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument("--evidence-reference", action="append", default=[])
    parser.add_argument("--commit-message")
    parser.add_argument("--push-remote", default="origin")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def required(value: str | None, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value.strip()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    request = required(args.request, "--request")
    if args.amend_file is None:
        raise ValueError("--amend-file is required")
    expected = required(
        args.expected_contract_sha256,
        "--expected-contract-sha256",
    )
    actor = required(args.actor, "--actor")
    reason = required(args.reason, "--reason")
    commit_message = required(args.commit_message, "--commit-message")
    references = tuple(
        item.strip()
        for item in args.evidence_reference
        if isinstance(item, str) and item.strip()
    )
    if not references:
        raise ValueError("at least one --evidence-reference is required")
    result = start_amendment(
        repo=args.repo,
        request=request,
        replacement_path=args.amend_file,
        expected_contract_sha256=expected,
        actor=actor,
        reason=reason,
        evidence_references=references,
        commit_message=commit_message,
        push_remote=required(args.push_remote, "--push-remote"),
    )
    print("Kalaxy3 SAGE improvement-action amendment: PASS")
    print(json.dumps(result, indent=2))
    print("Next operator boundary:")
    proposal = json.loads(
        Path(str(result["proposal"])).read_text(encoding="utf-8")
    )
    print(f"  {proposal['command']['display']}")
    print("Stop after that one operator command and paste its complete output.")
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
            "Kalaxy3 SAGE improvement-action amendment: FAIL CLOSED",
            file=sys.stderr,
        )
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
