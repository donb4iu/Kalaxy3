#!/usr/bin/env python3
"""Operate the SAGE causal evidence MVP without acquiring decision authority."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from causal_evidence import (
    CausalEvidenceError,
    CausalEvidenceStore,
    rebuild_cache,
    validate_canonical_repository_snapshot,
    self_test,
)


from workflow import (
    CommandRunner,
    GitInspector,
    JsonlEventLogger,
    PrimitiveCatalog,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = REPO_ROOT / "sage-causal-evidence-authority"
DEFAULT_CACHE_ROOT = Path(
    "~/.local/state/kalaxy3/sage-causal-evidence-cache"
).expanduser()


def _json_object(raw: str) -> dict[str, object]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError("value must decode to a JSON object")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record immutable causal evidence facts and derive SAGE objective views."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            "Explicit non-authoritative causal store root for tests or "
            "sandbox projections. Omit to use the repository-backed "
            "canonical authority store."
        ),
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=DEFAULT_CACHE_ROOT,
        help="Disposable per-machine causal projection/cache root.",
    )
    parser.add_argument("--self-test", action="store_true")

    sub = parser.add_subparsers(dest="command")

    record = sub.add_parser("record")
    record.add_argument("--objective-id", required=True)
    record.add_argument("--fact-type", required=True)
    record.add_argument("--producer-class", required=True)
    record.add_argument("--producer-identity", required=True)
    record.add_argument("--authority-reference", required=True)
    record.add_argument("--authority-receipt", type=Path)
    record.add_argument("--delegated-authority-system")
    record.add_argument("--delegated-immutable-identity")
    record.add_argument("--delegated-verification-semantics")
    record.add_argument("--delegated-retrieval-reference")
    record.add_argument("--depends-on", action="append", default=[])
    record.add_argument("--evidence-reference", action="append", default=[])
    record.add_argument("--evidence-file", action="append", type=Path, default=[])
    record.add_argument("--attributes-json", type=_json_object, default={})

    project = sub.add_parser("project")
    project.add_argument("--objective-id", required=True)
    project.add_argument("--require-type", action="append", required=True)
    project.add_argument("--as-of")

    sub.add_parser("cache-rebuild")

    lineage = sub.add_parser("lineage")
    lineage.add_argument("--fact-id", required=True)

    sub.add_parser("verify")
    return parser.parse_args()



AUTHORITY_STATE_ROOT = Path(
    "~/.local/state/kalaxy3/sage-causal-evidence-authority-check"
).expanduser()

AUTHORITY_PRIMITIVES = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "git.inspect",
)


def _canonical_repository_authority(
    repo: Path,
) -> dict[str, object]:
    """Prove this checkout exactly represents canonical remote main."""

    state_dir = (
        AUTHORITY_STATE_ROOT
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    state_dir.mkdir(parents=True, exist_ok=False)

    catalog = PrimitiveCatalog.load(
        repo / "sage-workflow-primitives.json"
    )
    catalog.require(AUTHORITY_PRIMITIVES)

    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        "sage.causal-evidence.canonical-authority",
        primitive_versions=catalog.versions_for(
            AUTHORITY_PRIMITIVES
        ),
    )

    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir),
        base_environment={},
    )
    inspector = GitInspector(repo, runner)

    return validate_canonical_repository_snapshot(
        branch=inspector.branch(),
        head=inspector.head(),
        local_main_head=inspector.head("origin/main"),
        remote_main_head=inspector.remote_head(
            "origin",
            "main",
        ),
        changed_paths=tuple(
            sorted(inspector.changed_paths())
        ),
    )


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0

    canonical_default = args.root is None
    root = (
        DEFAULT_ROOT
        if canonical_default
        else args.root.expanduser().resolve()
    )

    if canonical_default and args.command in {
        "project",
        "verify",
        "lineage",
        "cache-rebuild",
    }:
        _canonical_repository_authority(REPO_ROOT)

    store = CausalEvidenceStore(root)
    if args.command == "record":
        delegated_values = (
            args.delegated_authority_system,
            args.delegated_immutable_identity,
            args.delegated_verification_semantics,
            args.delegated_retrieval_reference,
        )
        if any(value is not None for value in delegated_values) and not all(
            isinstance(value, str) and value.strip()
            for value in delegated_values
        ):
            raise CausalEvidenceError(
                "delegated authority fields must be supplied together"
            )
        delegated_authority = (
            {
                "authority_system": args.delegated_authority_system,
                "immutable_identity": args.delegated_immutable_identity,
                "verification_semantics": args.delegated_verification_semantics,
                "retrieval_reference": args.delegated_retrieval_reference,
            }
            if all(value is not None for value in delegated_values)
            else None
        )
        fact = store.record(
            objective_id=args.objective_id,
            fact_type=args.fact_type,
            producer={
                "participant_class": args.producer_class,
                "identity": args.producer_identity,
            },
            authority_reference=args.authority_reference,
            authority_receipt=args.authority_receipt,
            delegated_authority=delegated_authority,
            dependencies=tuple(args.depends_on),
            evidence_references=tuple(args.evidence_reference),
            evidence_paths=tuple(args.evidence_file),
            attributes=args.attributes_json,
        )
        result = dict(fact.payload)
        if canonical_default:
            result["repository_authority_status"] = (
                "candidate-until-canonical-main-integration"
            )
        print(json.dumps(result, indent=2))
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

    if args.command == "cache-rebuild":
        print(
            json.dumps(
                rebuild_cache(root, args.cache_root),
                indent=2,
            )
        )
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
