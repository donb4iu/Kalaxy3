#!/usr/bin/env python3
"""Plan source-only SAGE content into an executor-compatible proposal."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from request_execution import ProposalError, load_proposal
from request_planning import derive_applicable_contexts, load_source_bundle, reconcile_semantic_contexts, resolve_planning_authority, write_proposal_package, write_source_package
from workflow import PrimitiveCatalog, WorkflowError
from workflows.request_planning import derive_component_plan, plan_request



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
        payload = b"fixture\n"
        from request_execution import ProposedFile, sha256_bytes
        bundle = write_source_package(
            source,
            semantic_request,
            repository={"branch": "feature/fixture", "head": "0" * 40},
            source_files=(ProposedFile("fixture.txt", sha256_bytes(payload), 0o644, payload),),
            evidence_references=["fixture:request-planning"],
            validation_commands=[{"label": "Fixture validation", "argv": ["make", "sage-index-check"], "timeout_seconds": 60}],
            operator_plan={"commit_message": "Fixture planned request", "push_remote": "origin"},
        )
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

        semantic_payload = b"semantic-fixture\n"
        semantic_relative = "scripts/sage/request_planning.py"
        implementation = derive_applicable_contexts(repo, (semantic_relative,))
        extras = tuple(item for item in ("helm-platform", "observability") if item not in implementation)
        reconciled = reconcile_semantic_contexts(repo, tuple((*implementation, *extras)), (semantic_relative,))
        applicable = tuple(reconciled["applicable_contexts"])
        dispositions = list(reconciled["context_dispositions"])
        understanding = {
            "schema_version": "1.0",
            "record_type": "sage-semantic-understanding",
            "action": {"action_id": "SAGE-ACTION-FIXTURE", "status": "accepted"},
            "literal_request": semantic_request,
            "contribution": {"proposed_paths": [semantic_relative]},
            "interpretation": {
                "implementation_scope": [semantic_relative],
                "inferred_contexts": list(dict.fromkeys((*applicable, *extras))),
                "applicable_contexts": list(applicable),
                "implementation_contexts": list(implementation),
                "context_dispositions": dispositions,
            },
            "assertions": {"meaning": "architect-confirmation-required"},
        }
        understanding_path = temp_root / "semantic-understanding.json"
        understanding_path.write_text(json.dumps(understanding, indent=4) + "\n", encoding="utf-8")
        confirmation = {
            "schema_version": "1.0",
            "record_type": "sage-semantic-confirmation",
            "action_id": "SAGE-ACTION-FIXTURE",
            "actor_role": "architect",
            "semantic_understanding_sha256": sha256_bytes(understanding_path.read_bytes()),
            "meaning": "architect-confirmed",
        }
        confirmation_path = temp_root / "semantic-confirmation.json"
        confirmation_path.write_text(json.dumps(confirmation, indent=4) + "\n", encoding="utf-8")
        semantic_source = temp_root / "semantic-source.zip"
        semantic_bundle = write_source_package(
            semantic_source,
            semantic_request,
            repository={"branch": "feature/fixture", "head": "0" * 40},
            source_files=(ProposedFile(semantic_relative, sha256_bytes(semantic_payload), 0o644, semantic_payload),),
            evidence_references=["fixture:semantic-authority"],
            validation_commands=[{"label": "Fixture validation", "argv": ["make", "sage-index-check"], "timeout_seconds": 60}],
            operator_plan={"commit_message": "Fixture semantic planned request", "push_remote": "origin"},
            semantic_understanding_path=understanding_path,
            semantic_confirmation_path=confirmation_path,
        )
        if semantic_bundle.manifest.get("schema_version") != "1.2" or semantic_bundle.semantic_authority is None:
            raise RuntimeError("split semantic planning source did not preserve confirmed authority")
        class DiscoveryFixture:
            contexts = tuple(dict.fromkeys((*applicable, *extras)))
            authorities = ("infrastructure/k3s-homelab/helm-chart-lock.json",)
        resolved = resolve_planning_authority(repo, semantic_bundle, DiscoveryFixture())
        if tuple(resolved["contexts"]) != implementation:
            raise RuntimeError("semantic planning mutation authority re-expanded raw discovery contexts")
        if tuple(resolved["applicable_contexts"]) != applicable:
            raise RuntimeError("semantic applicability was collapsed back to mutation scope")
        if not all(item in applicable for item in extras):
            raise RuntimeError("request-relevant contexts were silently discarded because no source path changed")
        if any(str(path).startswith("infrastructure/k3s-homelab/") for path in resolved["authoritative_files"]):
            raise RuntimeError("semantic planning mutation authority leaked infrastructure authorities")

        historical_understanding = json.loads(json.dumps(understanding))
        historical_understanding["interpretation"].pop("implementation_contexts", None)
        historical_understanding["interpretation"]["applicable_contexts"] = list(implementation)
        historical_understanding["interpretation"]["context_dispositions"] = [
            {"context_id": item, "disposition": "applicable"}
            for item in implementation
        ]
        historical_understanding_path = temp_root / "semantic-understanding-v1.1.json"
        historical_understanding_path.write_text(json.dumps(historical_understanding, indent=4) + "\n", encoding="utf-8")
        historical_confirmation = dict(confirmation)
        historical_confirmation["semantic_understanding_sha256"] = sha256_bytes(historical_understanding_path.read_bytes())
        historical_confirmation_path = temp_root / "semantic-confirmation-v1.1.json"
        historical_confirmation_path.write_text(json.dumps(historical_confirmation, indent=4) + "\n", encoding="utf-8")
        historical_source = temp_root / "semantic-source-v1.1.zip"
        historical_bundle = write_source_package(
            historical_source,
            semantic_request,
            repository={"branch": "feature/fixture", "head": "0" * 40},
            source_files=(ProposedFile(semantic_relative, sha256_bytes(semantic_payload), 0o644, semantic_payload),),
            evidence_references=["fixture:historical-semantic-authority"],
            validation_commands=[{"label": "Fixture validation", "argv": ["make", "sage-index-check"], "timeout_seconds": 60}],
            operator_plan={"commit_message": "Fixture historical semantic request", "push_remote": "origin"},
            semantic_understanding_path=historical_understanding_path,
            semantic_confirmation_path=historical_confirmation_path,
        )
        if historical_bundle.manifest.get("schema_version") != "1.1":
            raise RuntimeError("historical semantic source did not retain v1.1 contract")
        class HistoricalDiscoveryFixture:
            contexts = implementation
            authorities = ()
        historical_resolved = resolve_planning_authority(repo, historical_bundle, HistoricalDiscoveryFixture())
        if tuple(historical_resolved["contexts"]) != implementation:
            raise RuntimeError("historical v1.1 semantic source changed combined-context authority")
        try:
            resolve_planning_authority(repo, historical_bundle, DiscoveryFixture())
        except ProposalError as error:
            if "return to semantic confirmation" not in str(error):
                raise RuntimeError(f"unexpected historical semantic re-entry failure: {error}") from error
        else:
            raise RuntimeError("historical v1.1 source silently accepted contexts absent from its confirmation")
        class ChangedDiscoveryFixture:
            contexts = tuple(dict.fromkeys((*DiscoveryFixture.contexts, "storage")))
            authorities = DiscoveryFixture.authorities
        try:
            resolve_planning_authority(repo, semantic_bundle, ChangedDiscoveryFixture())
        except ProposalError as error:
            if "return to semantic confirmation" not in str(error):
                raise RuntimeError(f"unexpected semantic re-entry failure: {error}") from error
        else:
            raise RuntimeError("new post-confirmation context did not fail closed")

    print("PASS repository-derived required capabilities")
    print("PASS repository-derived candidates and selection factors")
    print(
        "PASS semantic-vocabulary replay without external candidate semantics"
    )
    print("PASS unsupported capability produces capability.gap receipt")
    print("PASS repository-owned source package to existing proposal interface")
    print("PASS semantic applicability remains distinct from source-mutation authority")
    print("PASS request-relevant contexts are preserved without leaking unrelated mutation authority")
    print("PASS historical v1.1 semantic planning sources remain readable without rewrite")
    print("PASS historical v1.1 sources still fail closed on newly discovered contexts")
    print("PASS new post-confirmation contexts return to semantic confirmation")
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
