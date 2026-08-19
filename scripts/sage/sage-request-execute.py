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

from request_execution import ProposalError, load_proposal, next_operator_boundary, request_sha256, validate_operator_result, validate_routine_git_lifecycle_receipt  # noqa: E402


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


def write_fixture_package(
    path: Path,
    manifest: dict[str, object],
    payload: bytes,
    source_path: str = "fixture.txt",
) -> None:
    """Write one deterministic ZIP fixture."""

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sage-proposal.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr(f"payload/{source_path}", payload)


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

        from workflow import (  # noqa: PLC0415
            AtomicFileWriter,
            CommandRunner,
            CommandSpec,
            JsonlEventLogger,
            PrimitiveCatalog,
            WorkflowCommandError,
            WorkflowError,
        )
        from workflows.request_execution import (  # noqa: PLC0415
            candidate_from_mapping,
            capture_python_safety_baseline,
            load_state,
            safety_action,
            validate_python_payloads,
        )

        fixture_repo = root / "repository"
        sage_dir = fixture_repo / "scripts" / "sage"
        sage_dir.mkdir(parents=True)
        installed_guardrail = (
            Path(__file__).resolve().parent / "sage-python-static-guardrail.py"
        )
        (sage_dir / "sage-python-static-guardrail.py").write_bytes(
            installed_guardrail.read_bytes()
        )
        state = root / "prewrite-state"
        logger = JsonlEventLogger(
            state / "events.jsonl",
            "sage.request-execution.prewrite-runtime-name-self-test",
        )
        runner = CommandRunner(logger, allowed_roots=(fixture_repo, state))
        writer = AtomicFileWriter((state,))

        valid_python = b"def run():\n    return 'ok'\n"
        valid_manifest = fixture_manifest(request, valid_python)
        valid_manifest["source_files"][0]["path"] = "fixture.py"
        valid_zip = root / "valid-python.zip"
        write_fixture_package(
            valid_zip, valid_manifest, valid_python, source_path="fixture.py"
        )
        valid_bundle = load_proposal(valid_zip, request)

        class FixtureContext:
            pass

        candidate_context = FixtureContext()
        candidate_context.repo = Path(__file__).resolve().parents[2]
        candidate_context.bundle = bundle
        candidate_context.catalog = PrimitiveCatalog.load(
            candidate_context.repo / "sage-workflow-primitives.json"
        )

        registered = candidate_from_mapping(
            candidate_context,
            manifest["candidates"][0],
        )
        if registered.component_id != "validation.plan":
            raise RuntimeError("registered primitive candidate binding changed")

        unknown = dict(manifest["candidates"][0])
        unknown["component_id"] = "fixture.unknown-primitive"
        try:
            candidate_from_mapping(candidate_context, unknown)
        except WorkflowError as error:
            if "Unknown workflow primitives" not in str(error):
                raise RuntimeError(
                    f"unexpected unknown-primitive rejection: {error}"
                ) from error
        else:
            raise RuntimeError("unknown ordinary primitive unexpectedly passed")

        planning_sha = digest(b"staged-domain-planning-source\\n")
        staged_capabilities = (
            "artifact.promote-without-rebuild",
            "environment.binding",
            "execution.qualified-executor",
        )
        for index, capability_id in enumerate(staged_capabilities, 1):
            staged = {
                "candidate_id": f"CAND-STAGED-{index:03d}",
                "capability_ids": [capability_id],
                "component_id": f"staged-domain-capability:{capability_id}",
                "version": (
                    "SAGE-WORKFLOW-CAPABILITY-BASELINE-FIXTURE@"
                    + planning_sha[:12]
                ),
                "source_path": "fixture.txt",
                "maturity": "staged-implementation",
                "selection_factors": dict(
                    manifest["candidates"][0]["selection_factors"]
                ),
                "evidence_references": [
                    f"approved-domain-gap:{capability_id}",
                    f"planning-source-sha256:{planning_sha}",
                    (
                        "proposed-baseline:markdown/standards/"
                        "sage-capability-intelligence-workflow-capability-"
                        f"baseline-v1.0.json#{capability_id}"
                    ),
                ],
                "rationale": "Fixture staged-domain candidate.",
            }
            bound = candidate_from_mapping(candidate_context, staged)
            if (
                bound.component_id
                != f"staged-domain-capability:{capability_id}"
                or bound.version != staged["version"]
            ):
                raise RuntimeError(
                    f"staged-domain candidate binding changed: {capability_id}"
                )

            malformed = dict(staged)
            malformed["capability_ids"] = ["different.capability"]
            try:
                candidate_from_mapping(candidate_context, malformed)
            except WorkflowError as error:
                if "single declared capability" not in str(error):
                    raise RuntimeError(
                        f"unexpected staged identity rejection: {error}"
                    ) from error
            else:
                raise RuntimeError(
                    "mismatched staged-domain capability unexpectedly passed"
                )

            malformed = dict(staged)
            malformed["evidence_references"] = [
                item
                for item in staged["evidence_references"]
                if not item.startswith("approved-domain-gap:")
            ]
            try:
                candidate_from_mapping(candidate_context, malformed)
            except WorkflowError as error:
                if "Architect-approved domain-gap evidence" not in str(error):
                    raise RuntimeError(
                        f"unexpected staged approval rejection: {error}"
                    ) from error
            else:
                raise RuntimeError(
                    "staged candidate without approval evidence unexpectedly passed"
                )

        valid_context = FixtureContext()
        valid_context.repo = fixture_repo
        valid_context.state_dir = state
        valid_context.bundle = valid_bundle
        valid_context.writer = writer
        valid_context.runner = runner
        valid_context.transaction = None
        valid_context.baseline_safety = {"fixture.py": ()}
        if validate_python_payloads(valid_context) != ("fixture.py",):
            raise RuntimeError("valid Python payload was not pre-write validated")
        if (fixture_repo / "fixture.py").exists():
            raise RuntimeError("valid pre-write validation mutated repository content")

        invalid_python = b"def run():\n    raise WorkflowError('missing import')\n"
        invalid_manifest = fixture_manifest(request, invalid_python)
        invalid_manifest["source_files"][0]["path"] = "fixture.py"
        invalid_zip = root / "invalid-python.zip"
        write_fixture_package(
            invalid_zip, invalid_manifest, invalid_python, source_path="fixture.py"
        )
        invalid_bundle = load_proposal(invalid_zip, request)
        invalid_context = FixtureContext()
        invalid_context.repo = fixture_repo
        invalid_context.state_dir = state
        invalid_context.bundle = invalid_bundle
        invalid_context.writer = writer
        invalid_context.runner = runner
        invalid_context.transaction = None
        invalid_context.baseline_safety = {"fixture.py": ()}
        try:
            validate_python_payloads(invalid_context)
        except WorkflowCommandError as error:
            if "Validate Python payload globals: fixture.py" not in str(error):
                raise RuntimeError(
                    f"unexpected pre-write validation wrapper: {error}"
                ) from error
        else:
            raise RuntimeError("undefined WorkflowError payload unexpectedly passed")
        if invalid_context.transaction is not None:
            raise RuntimeError("repository transaction was created before rejection")
        if (fixture_repo / "fixture.py").exists():
            raise RuntimeError("invalid pre-write validation mutated repository content")

        invalid_candidate = state / "prewrite-python-payloads" / "fixture.py"
        diagnostic = runner.run(
            CommandSpec(
                primitive_id="command.run",
                label="Inspect expected undefined-global diagnostic",
                argv=(
                    "python3",
                    "scripts/sage/sage-python-static-guardrail.py",
                    str(invalid_candidate),
                ),
                cwd=fixture_repo,
                timeout_seconds=120,
                expected_codes=(1,),
            ),
            step_id="prewrite-python-static-diagnostic",
        )
        combined = diagnostic.stdout + diagnostic.stderr
        if "undefined global reference WorkflowError" not in combined:
            raise RuntimeError(
                "expected undefined WorkflowError diagnostic was not preserved"
            )

        prewrite_safety_cases = (
            (
                "mixed-git-authority",
                b"from workflow import GitRepository\nVALUE = 1\n",
                "MIXED-GIT-AUTHORITY",
            ),
            (
                "git-mutation-api",
                (
                    b"class Holder:\n"
                    b"    def fetch(self):\n"
                    b"        return None\n"
                    b"repository = Holder()\n"
                    b"repository.fetch()\n"
                ),
                "GIT-MUTATION-API",
            ),
            (
                "github-mutation",
                (
                    b"from pathlib import Path\n"
                    b"from workflow import CommandSpec\n"
                    b"SPEC = CommandSpec(\n"
                    b"    primitive_id='command.run',\n"
                    b"    label='x',\n"
                    b"    argv=('gh', 'pr', 'view', '1'),\n"
                    b"    cwd=Path('.'),\n"
                    b")\n"
                ),
                "GITHUB-MUTATION",
            ),
        )
        for label, payload, expected_code in prewrite_safety_cases:
            source_path = f"fixture-{label}.py"
            manifest = fixture_manifest(request, payload)
            manifest["source_files"][0]["path"] = source_path
            package = root / f"{label}.zip"
            write_fixture_package(
                package,
                manifest,
                payload,
                source_path=source_path,
            )
            bundle = load_proposal(package, request)
            prewrite_context = FixtureContext()
            prewrite_context.repo = fixture_repo
            prewrite_context.state_dir = state
            prewrite_context.bundle = bundle
            prewrite_context.writer = writer
            prewrite_context.runner = runner
            prewrite_context.transaction = None
            prewrite_context.baseline_safety = {source_path: ()}
            try:
                validate_python_payloads(prewrite_context)
            except WorkflowError as error:
                if expected_code not in str(error):
                    raise RuntimeError(
                        f"unexpected {label} pre-write safety rejection: {error}"
                    ) from error
            else:
                raise RuntimeError(
                    f"{label} payload unexpectedly passed pre-write safety"
                )
            if prewrite_context.transaction is not None:
                raise RuntimeError(
                    f"{label} created a repository transaction before rejection"
                )
            if (fixture_repo / source_path).exists():
                raise RuntimeError(
                    f"{label} mutated repository content before rejection"
                )

        safety_path = fixture_repo / "fixture.py"
        safety_path.write_text(
            "import subprocess\nVALUE = 'baseline'\n",
            encoding="utf-8",
        )
        capture_python_safety_baseline(valid_context)

        safety_path.write_text(
            "import subprocess\nVALUE = 'changed safely'\n",
            encoding="utf-8",
        )
        if safety_action(valid_context)["status"] != "pass":
            raise RuntimeError(
                "unchanged pre-existing safety finding was not treated as baseline"
            )

        safety_path.write_text(
            "import subprocess\n"
            "subprocess.run(['git', 'push', 'origin', 'main'])\n",
            encoding="utf-8",
        )
        try:
            safety_action(valid_context)
        except WorkflowError as error:
            if "GIT-MUTATION" not in str(error):
                raise RuntimeError(
                    f"unexpected introduced-safety rejection: {error}"
                ) from error
        else:
            raise RuntimeError("new Git mutation unexpectedly passed baseline safety")

        valid_context.baseline_safety = {"fixture.py": ()}
        safety_path.write_text("import subprocess\n", encoding="utf-8")
        try:
            safety_action(valid_context)
        except WorkflowError as error:
            if "DIRECT-SUBPROCESS" not in str(error):
                raise RuntimeError(
                    f"unexpected new-file safety rejection: {error}"
                ) from error
        else:
            raise RuntimeError("new direct-subprocess helper unexpectedly passed")
        safety_path.unlink()

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
        if observed["complete_output_sha256"] != digest(b"") or observed["result_sha256"] != digest(b""):
            raise RuntimeError("operator-result output digest mismatch")
        routine_proposal = {
            "schema_version": "1.2",
            "proposal_id": "SAGE-GIT-20260806-002",
            "boundary": "routine-git-lifecycle",
            "repository": {"branch": "feature/fixture", "head": "0" * 40},
            "command": {"sha256": "b" * 64},
            "operator_contract": {
                "execution_mode": "operator-executed",
                "approval_required": True,
                "pasted_output_required": False,
                "repository_receipt_required": True,
                "next_boundary_blocked_until_verified": True,
            },
        }
        routine_state_contract = {
            "repository_branch": "feature/fixture",
            "base_head": "0" * 40,
            "base_main_head": "1" * 40,
            "declared_paths": ["fixture.txt"],
            "operator_plan": {"commit_message": "Fixture", "push_remote": "origin"},
        }
        routine_receipt = {
            "schema_version": "1.0",
            "record_type": "sage-routine-git-lifecycle-receipt",
            "status": "pass",
            "proposal_id": "SAGE-GIT-20260806-002",
            "command_sha256": "b" * 64,
            "branch": "feature/fixture",
            "pre_head": "0" * 40,
            "base_main_head": "1" * 40,
            "commit": "2" * 40,
            "remote": "origin",
            "remote_branch_head": "2" * 40,
            "declared_paths": ["fixture.txt"],
            "event_log": "/tmp/routine-events.jsonl",
        }
        receipt_evidence = validate_routine_git_lifecycle_receipt(
            routine_receipt,
            routine_proposal,
            routine_state_contract,
            receipt_sha256="c" * 64,
        )
        if receipt_evidence["source_kind"] != "routine-controller-receipt" or receipt_evidence["result_commit"] != "2" * 40:
            raise RuntimeError("routine-controller receipt normalization failed")
        legacy_routine_proposal = {
            "schema_version": "1.0",
            "proposal_id": "SAGE-GIT-20260806-002",
            "boundary": "routine-git-lifecycle",
            "repository": {"branch": "feature/fixture", "head": "0" * 40},
            "command": {"sha256": "b" * 64},
            "operator_contract": {
                "execution_mode": "operator-executed",
                "approval_required": True,
                "pasted_output_required": True,
                "next_boundary_blocked_until_verified": True,
            },
        }
        legacy_receipt_evidence = validate_routine_git_lifecycle_receipt(
            routine_receipt,
            legacy_routine_proposal,
            routine_state_contract,
            receipt_sha256="c" * 64,
        )
        if legacy_receipt_evidence["source_kind"] != "routine-controller-receipt":
            raise RuntimeError("already-open legacy routine receipt compatibility failed")
        if [next_operator_boundary(item) for item in ("routine-git-lifecycle", "stage", "commit", "push")] != [None, "commit", "push", None]:
            raise RuntimeError("operator continuation boundary sequence mismatch")

        legacy_state = {
            "schema_version": "1.0",
            "record_type": "sage-request-execution-state",
            "request": request,
            "request_sha256": hashlib.sha256(
                request.encode("utf-8")
            ).hexdigest(),
            "proposal_package": str(positive),
            "proposal_package_sha256": hashlib.sha256(
                positive.read_bytes()
            ).hexdigest(),
            "repository_branch": "feature/fixture",
            "base_head": "0" * 40,
            "declared_paths": ["fixture.txt"],
            "authority_receipt": "authority.json",
            "component_manifest": "components.json",
            "capability_gap_decision": "gap.json",
            "validation": [],
            "operator_plan": {
                "commit_message": "Fixture request execution",
                "push_remote": "origin",
            },
            "current_boundary": "stage",
            "current_proposal": "operator-git-proposal.json",
            "history": [],
        }
        legacy_path = root / "legacy-stage-state.json"
        legacy_path.write_text(
            json.dumps(legacy_state, indent=2) + "\n",
            encoding="utf-8",
        )
        loaded_legacy = load_state(legacy_path)
        if "base_main_head" in loaded_legacy:
            raise RuntimeError(
                "legacy stage state unexpectedly gained main authority"
            )

        routine_state = dict(legacy_state)
        routine_state["current_boundary"] = "routine-git-lifecycle"
        routine_path = root / "routine-state-missing-main.json"
        routine_path.write_text(
            json.dumps(routine_state, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            load_state(routine_path)
        except WorkflowError as error:
            if "state fields are invalid" not in str(error):
                raise RuntimeError(
                    f"unexpected routine state rejection: {error}"
                ) from error
        else:
            raise RuntimeError(
                "routine lifecycle state without base_main_head passed"
            )

        routine_state["base_main_head"] = "1" * 40
        routine_path.write_text(
            json.dumps(routine_state, indent=2) + "\n",
            encoding="utf-8",
        )
        loaded_routine = load_state(routine_path)
        if loaded_routine.get("base_main_head") != "1" * 40:
            raise RuntimeError(
                "routine lifecycle main authority was not preserved"
            )
    print("PASS exact literal-request binding")
    print("PASS checksum-bound source payload")
    print("PASS Git SHA-1 and SHA-256 object-ID validation")
    print("PASS unsafe validation target rejection")
    print("PASS new-low-level-primitive fail-closed gate")
    print("PASS registered and staged-domain candidate binding separation")
    print("PASS all three Action-002 staged-domain capabilities bind without primitive registration")
    print("PASS malformed staged-domain identities and approval evidence fail closed")
    print("PASS Python payload undefined-global rejection before repository write")
    print("PASS valid Python payload pre-write validation without repository mutation")
    print("PASS introduced Git and GitHub safety findings rejected before repository mutation")
    print("PASS unchanged proposal-bound safety findings remain baseline-only")
    print("PASS newly introduced and new-file unsafe findings fail closed")
    print("PASS repository-receipt routine lifecycle continuation and legacy pasted stage/commit/push compatibility")
    print("Kalaxy3 SAGE request execution self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    """Parse the repository request-execution CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request")
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--continue-state", type=Path)
    parser.add_argument("--operator-result", type=Path)
    parser.add_argument("--routine-receipt", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the self-test or exact governed request execution."""

    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    legacy_continuing = args.operator_result is not None
    routine_continuing = args.routine_receipt is not None
    continuing = args.continue_state is not None or legacy_continuing or routine_continuing
    starting = bool(args.request) or args.proposal is not None
    if continuing and starting:
        raise ProposalError("start and continue arguments are mutually exclusive")
    if continuing:
        if args.continue_state is None or legacy_continuing == routine_continuing:
            raise ProposalError(
                "--continue-state requires exactly one of --operator-result or --routine-receipt"
            )
        if routine_continuing:
            from workflows.request_execution import continue_request_from_routine_receipt  # noqa: PLC0415
            result = continue_request_from_routine_receipt(
                repo, args.continue_state, args.routine_receipt
            )
        else:
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
    if proposal.get("boundary") == "routine-git-lifecycle":
        print("That one approval performs the bounded Git lifecycle and consumes its repository-owned receipt to complete request verification, metrics, and evidence closeout.")
    else:
        print("Stop after that one operator command and paste its complete output.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, ProposalError, RuntimeError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE request execution: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
