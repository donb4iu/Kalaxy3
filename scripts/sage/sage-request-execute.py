#!/usr/bin/env python3
"""Execute a literal SAGE request through a checksum-bound proposal package."""

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

from request_execution import ProposalError, load_proposal, next_operator_boundary, request_sha256, validate_operator_result  # noqa: E402


def digest(payload: bytes) -> str:
    """Return one fixture digest."""

    return hashlib.sha256(payload).hexdigest()


def fixture_manifest(request: str, payload: bytes) -> dict[str, object]:
    """Return one valid source-only request proposal fixture."""

    factors = {
        "applicability": "direct",
        "authority_compatibility": "compatible",
        "mutation_scope_fit": "least-authority",
        "published_interface_verified": True,
        "successful_production_executions": None,
        "failed_production_executions": None,
        "open_recurrence": "unknown",
        "runtime_test_coverage": "positive-and-negative",
    }
    return {
        "schema_version": "1.0",
        "request_sha256": request_sha256(request),
        "repository": {"branch": "feature/fixture", "head": "0" * 40},
        "source_files": [{"path": "fixture.txt", "sha256": digest(payload), "mode": "0644"}],
        "generated_paths": [],
        "reconcile_evidence_index": False,
        "evidence_references": ["fixture:evidence"],
        "capabilities": [{"capability_id": "CAP-001", "description": "Exercise a validated composition.", "required": True}],
        "candidates": [{
            "candidate_id": "CAND-001",
            "capability_ids": ["CAP-001"],
            "component_id": "validation.plan",
            "version": "1.0.0",
            "source_path": "scripts/sage/workflow/validation.py",
            "maturity": "pilot",
            "selection_factors": factors,
            "evidence_references": ["fixture:evidence"],
            "rationale": "Fixture candidate.",
        }],
        "new_primitive_required": False,
        "validation_commands": [{"label": "Fixture validation", "argv": ["make", "sage-index-check"], "timeout_seconds": 60}],
        "operator_plan": {"commit_message": "Fixture request execution", "push_remote": "origin"},
    }


def write_fixture_package(path: Path, manifest: dict[str, object], payload: bytes) -> None:
    """Write one deterministic ZIP fixture."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sage-proposal.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("payload/fixture.txt", payload)


def expect_rejected(path: Path, request: str, fragment: str) -> None:
    """Require one invalid package to fail closed."""

    try:
        load_proposal(path, request)
    except ProposalError as error:
        if fragment not in str(error):
            raise RuntimeError(f"unexpected rejection: {error}") from error
        return
    raise RuntimeError(f"invalid proposal unexpectedly passed: {fragment}")


def self_test() -> int:
    """Exercise positive and negative proposal-package runtime paths."""

    request = "exercise SAGE request execution"
    payload = b"fixture\n"
    with tempfile.TemporaryDirectory(prefix="sage-request-execute-") as raw:
        root = Path(raw)
        positive = root / "positive.zip"
        manifest = fixture_manifest(request, payload)
        write_fixture_package(positive, manifest, payload)
        bundle = load_proposal(positive, request)
        if bundle.declared_paths != ("fixture.txt",):
            raise RuntimeError("positive proposal scope mismatch")
        sha256_repo = root / "sha256-repo.zip"
        sha256_manifest = fixture_manifest(request, payload)
        sha256_manifest["repository"] = {
            "branch": "feature/fixture", "head": "0" * 64,
        }
        write_fixture_package(sha256_repo, sha256_manifest, payload)
        load_proposal(sha256_repo, request)
        invalid_head = root / "invalid-head.zip"
        bad = fixture_manifest(request, payload)
        bad["repository"] = {
            "branch": "feature/fixture", "head": "0" * 39,
        }
        write_fixture_package(invalid_head, bad, payload)
        expect_rejected(invalid_head, request, "Git object id")
        expect_rejected(positive, request + " changed", "exact literal request")
        unsafe = root / "unsafe.zip"
        bad = fixture_manifest(request, payload)
        bad["validation_commands"] = [{"label": "bad", "argv": ["make", "sage-evidence-publish"], "timeout_seconds": 60}]
        write_fixture_package(unsafe, bad, payload)
        expect_rejected(unsafe, request, "forbidden")
        primitive = root / "primitive.zip"
        bad = fixture_manifest(request, payload)
        bad["new_primitive_required"] = True
        write_fixture_package(primitive, bad, payload)
        expect_rejected(primitive, request, "cannot authorize a new low-level primitive")

        operator_proposal = {
            "proposal_id": "SAGE-GIT-20260806-001",
            "command": {"sha256": "a" * 64},
        }
        operator_result = {
            "schema_version": "1.0",
            "proposal_id": "SAGE-GIT-20260806-001",
            "command_sha256": "a" * 64,
            "returncode": 0,
            "pasted_output_received": True,
            "complete_output": "",
        }
        observed = validate_operator_result(operator_result, operator_proposal)
        if observed["complete_output_sha256"] != digest(b""):
            raise RuntimeError("operator-result output digest mismatch")
        if [next_operator_boundary(item) for item in ("stage", "commit", "push")] != ["commit", "push", None]:
            raise RuntimeError("operator continuation boundary sequence mismatch")
    print("PASS exact literal-request binding")
    print("PASS checksum-bound source payload")
    print("PASS Git SHA-1 and SHA-256 object-ID validation")
    print("PASS unsafe validation target rejection")
    print("PASS new-low-level-primitive fail-closed gate")
    print("PASS pasted operator-result binding and stage-commit-push continuation")
    print("Kalaxy3 SAGE request execution self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse the repository request-execution CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--continue-state", type=Path)
    parser.add_argument("--operator-result", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the self-test or exact governed request execution."""

    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    continuing = args.continue_state is not None or args.operator_result is not None
    starting = bool(args.request) or args.proposal is not None
    if continuing and starting:
        raise ProposalError("start and continue arguments are mutually exclusive")
    if continuing:
        if args.continue_state is None or args.operator_result is None:
            raise ProposalError("--continue-state and --operator-result are both required")
        from workflows.request_execution import continue_request  # noqa: PLC0415
        result = continue_request(repo, args.continue_state, args.operator_result)
        print("Kalaxy3 SAGE request continuation: PASS")
        print(f"Verified boundary: {result['verified_boundary']}")
        print(f"Verification: {result['verification']}")
        print(f"Metrics: {result['metrics']}")
        print(f"Evidence closeout: {result['evidence_closeout']}")
        print(f"State: {result['state']}")
        print(f"Event log: {result['event_log']}")
        proposal = result["proposal"]
        if proposal is None:
            print("Repository Git lifecycle: COMPLETE")
            print("No next operator mutation boundary.")
        else:
            print(f"Operator proposal: {result['proposal_path']}")
            print("Next operator boundary:")
            print(proposal["command"]["display"])
            print("Stop after that one operator command and paste its complete output.")
        return 0
    if not args.request or args.proposal is None:
        raise ProposalError("--request and --proposal are required")
    from workflows.request_execution import execute_request  # noqa: PLC0415
    result = execute_request(repo, args.request, args.proposal)
    proposal = result["proposal"]
    print("Kalaxy3 SAGE request execution: PASS")
    print(f"Authority receipt: {result['authority_receipt']}")
    print(f"Component manifest: {result['component_manifest']}")
    print(f"Capability-gap decision: {result['capability_gap_decision']}")
    print(f"Operator proposal: {result['proposal_path']}")
    print(f"Continuation state: {result['state']}")
    print(f"Closeout: {result['closeout']}")
    print(f"Event log: {result['event_log']}")
    print("Next operator boundary:")
    print(proposal["command"]["display"])
    print("Stop after that one operator command and paste its complete output.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, ProposalError, RuntimeError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE request execution: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
