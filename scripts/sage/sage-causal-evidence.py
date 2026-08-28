#!/usr/bin/env python3
"""Operate the SAGE causal evidence MVP without acquiring decision authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from causal_evidence import (
    CausalEvidenceError,
    CausalEvidenceStore,
    self_test,
)

DEFAULT_ROOT = Path("~/.local/state/kalaxy3/sage-causal-evidence").expanduser()


def _json_object(raw: str) -> dict[str, object]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("value must decode to a JSON object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record immutable causal evidence facts and derive SAGE objective views."
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--self-test", action="store_true")

    sub = parser.add_subparsers(dest="command")

    record = sub.add_parser("record")
    record.add_argument("--objective-id", required=True)
    record.add_argument("--fact-type", required=True)
    record.add_argument("--producer-class", required=True)
    record.add_argument("--producer-identity", required=True)
    record.add_argument("--authority-reference", required=True)
    record.add_argument("--authority-receipt", type=Path)
    record.add_argument("--depends-on", action="append", default=[])
    record.add_argument("--evidence-reference", action="append", default=[])
    record.add_argument("--evidence-file", action="append", type=Path, default=[])
    record.add_argument("--attributes-json", type=_json_object, default={})

    project = sub.add_parser("project")
    project.add_argument("--objective-id", required=True)
    project.add_argument("--require-type", action="append", required=True)
    project.add_argument("--as-of")

    lineage = sub.add_parser("lineage")
    lineage.add_argument("--fact-id", required=True)

    sub.add_parser("verify")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0

    store = CausalEvidenceStore(args.root)
    if args.command == "record":
        fact = store.record(
            objective_id=args.objective_id,
            fact_type=args.fact_type,
            producer={
                "participant_class": args.producer_class,
                "identity": args.producer_identity,
            },
            authority_reference=args.authority_reference,
            authority_receipt=args.authority_receipt,
            dependencies=tuple(args.depends_on),
            evidence_references=tuple(args.evidence_reference),
            evidence_paths=tuple(args.evidence_file),
            attributes=args.attributes_json,
        )
        print(json.dumps(fact.payload, indent=2))
        return 0

    if args.command == "project":
        print(
            json.dumps(
                store.project(
                    objective_id=args.objective_id,
                    required_fact_types=tuple(args.require_type),
                    as_of=args.as_of,
                ),
                indent=2,
            )
        )
        return 0

    if args.command == "lineage":
        print(json.dumps(store.lineage(args.fact_id), indent=2))
        return 0

    if args.command == "verify":
        print(json.dumps(store.verify(), indent=2))
        return 0

    raise CausalEvidenceError("select a command or use --self-test")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CausalEvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Kalaxy3 SAGE causal evidence: FAIL CLOSED\n  - {error}")
        raise SystemExit(2)
