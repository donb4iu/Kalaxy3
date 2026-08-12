#!/usr/bin/env python3
"""Plan source-only SAGE content into an executor-compatible proposal."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from request_execution import ProposalError, load_proposal, request_sha256
from request_planning import load_source_bundle, write_proposal_package
from workflow import PrimitiveCatalog, WorkflowError
from workflows.request_planning import derive_component_plan, plan_request


def _fixture_source(path: Path, request: str, payload: bytes) -> None:
    manifest = {
        "schema_version": "1.0",
        "request_sha256": request_sha256(request),
        "repository": {
            "branch": "feature/fixture",
            "head": "0" * 40,
        },
        "source_files": [
            {
                "path": "fixture.txt",
                "sha256": hashlib.sha256(payload).hexdigest(),
                "mode": "0644",
            }
        ],
        "generated_paths": [],
        "reconcile_evidence_index": False,
        "evidence_references": ["fixture:request-planning"],
        "validation_commands": [
            {
                "label": "Fixture validation",
                "argv": ["make", "sage-index-check"],
                "timeout_seconds": 60,
            }
        ],
        "operator_plan": {
            "commit_message": "Fixture planned request",
            "push_remote": "origin",
        },
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "sage-source.json",
            json.dumps(manifest, indent=2) + "\n",
        )
        archive.writestr("payload/fixture.txt", payload)


def self_test(repo: Path) -> int:
    """Exercise derivation, gap handling, and proposal publication."""

    semantic_request = (
        "Replay the semantic-vocabulary request planning case using existing "
        "repository workflow primitives."
    )
    catalog = PrimitiveCatalog.load(
        repo / "sage-workflow-primitives.json"
    )
    positive = derive_component_plan(
        repo=repo,
        catalog=catalog,
        request=semantic_request,
        authority_reference="fixture:authority",
    )
    if positive.gap_receipt is not None:
        raise RuntimeError(
            "existing request-execution primitives produced a capability gap"
        )
    if (
        not positive.capabilities
        or len(positive.capabilities) != len(positive.candidates)
    ):
        raise RuntimeError(
            "positive planning capability/candidate coverage mismatch"
        )

    reduced = dict(catalog.primitives)
    reduced.pop("component.select", None)
    negative_catalog = PrimitiveCatalog(
        framework_version=catalog.framework_version,
        primitives=reduced,
    )
    negative = derive_component_plan(
        repo=repo,
        catalog=negative_catalog,
        request="Require an unsupported component-selection capability.",
        authority_reference="fixture:authority",
    )
    if negative.gap_receipt is None:
        raise RuntimeError(
            "unsupported capability did not produce a gap receipt"
        )
    if (
        negative.gap_receipt["gap"]["new_primitive_required"]
        is not True
    ):
        raise RuntimeError(
            "negative capability-gap receipt is malformed"
        )

    with tempfile.TemporaryDirectory(
        prefix="sage-request-plan-"
    ) as raw:
        temp_root = Path(raw)
        source = temp_root / "source.zip"
        _fixture_source(source, semantic_request, b"fixture\n")
        bundle = load_source_bundle(source, semantic_request)
        if bundle.declared_paths != ("fixture.txt",):
            raise RuntimeError("planning source scope mismatch")
        proposal = temp_root / "proposal.zip"
        planned = write_proposal_package(
            proposal,
            bundle,
            capabilities=positive.capabilities,
            candidates=positive.candidates,
            evidence_references=[
                "fixture:authority",
                "fixture:selection",
            ],
            request=semantic_request,
        )
        load_proposal(planned.package_path, semantic_request)

    print("PASS repository-derived required capabilities")
    print("PASS repository-derived candidates and selection factors")
    print(
        "PASS semantic-vocabulary replay without external candidate semantics"
    )
    print("PASS unsupported capability produces capability.gap receipt")
    print("PASS source-only package to existing proposal interface")
    print("Kalaxy3 SAGE request planning self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    if args.self_test:
        return self_test(repo)
    if not args.request or args.source is None:
        raise ProposalError("--request and --source are required")
    output = args.output
    if output is None:
        from datetime import datetime

        output = Path("~/Downloads").expanduser() / (
            "sage-request-proposal-"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".zip"
        )
    result = plan_request(
        repo,
        args.request,
        args.source,
        output.expanduser().resolve(),
    )
    print("Kalaxy3 SAGE request planning: PASS")
    print(f"Proposal: {result['proposal']}")
    print(f"Resolved authority: {result['authority']}")
    print(f"Component manifest: {result['component_manifest']}")
    print(f"Closeout: {result['closeout']}")
    print(f"State directory: {result['state_dir']}")
    print(
        "Next: execute the proposal through make sage-request-execute."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        TypeError,
        ProposalError,
        WorkflowError,
        RuntimeError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
    ) as error:
        print(
            "Kalaxy3 SAGE request planning: FAIL CLOSED",
            file=sys.stderr,
        )
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
