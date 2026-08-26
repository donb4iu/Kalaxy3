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
from workflow.diagnosis import FailureDiagnoser, classify_post_retrieval_continuation, require_post_retrieval_boundary  # noqa: E402
from workflow.recovery import (  # noqa: E402
    bind_successor_operator_boundary,
    build_accepted_control_failure_assertion,
    build_recovery_identity,
    decide_next_boundary,
)


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



def _recovery_identity_self_test() -> None:
    """Prove stable failure identity preserves separate repository authority."""

    request = "Action-002 immutable promotion"
    failure = (
        "Feature branch HEAD 4192551f1df150d06d8ad62235746bc5f29eaa18 "
        "is not based on current remote main cf514c41400ed546c9781db0f5834ea5d16a14fa"
    )
    first = build_recovery_identity(
        request=request,
        component_id="sage.request-execution",
        failure_text=failure,
        repository_authority={"branch": "feature/fixture", "head": "4" * 40},
    )
    second = build_recovery_identity(
        request=request,
        component_id="sage.request-execution",
        failure_text=failure,
        repository_authority={"branch": "feature/fixture", "head": "5" * 40},
    )
    if first["identity_sha256"] != second["identity_sha256"]:
        raise RuntimeError("recovery identity changed with repository authority")
    if first["repository_authority_sha256"] == second["repository_authority_sha256"]:
        raise RuntimeError("repository authority evidence was flattened into identity")


def _recovery_boundary_self_test() -> None:
    """Prove new change, duplicate loop, repair, and successor dispositions."""

    identity = build_recovery_identity(
        request="Action-002 immutable promotion",
        component_id="sage.request-execution",
        failure_text="fixture ancestry failure",
        repository_authority={"branch": "feature/fixture", "head": "4" * 40},
    )
    post = classify_post_retrieval_continuation(
        retrieval_performed=True,
        attempted_action_authorized=True,
        governing_changes={
            "authority": False, "scope": False, "required_capability": False,
            "safety_requirements": False, "repository_owned_composition": True,
            "approval_or_mutation_boundaries": False,
        },
        recovery_identity=identity,
    )
    if post.get("recovery_identity_sha256") != identity["identity_sha256"]:
        raise RuntimeError("post-retrieval decision lost recovery identity")
    evidence = {"repository_owned_composition_sha256": "a" * 64}
    first = decide_next_boundary(
        identity=identity, post_retrieval=post, governing_evidence=evidence,
        previous=(), consumed_fingerprints=set(),
        owning_component="sage.request-execution",
        control_action_id="SAGE-ACTION-20260810-001",
        control_action_status="accepted", accepted_control_failure=None,
    )
    if first["next_boundary"] != "planning":
        raise RuntimeError("new governing change did not route to planning")
    _assert_recovery_recurrence(identity, post, evidence, first)


def _assert_recovery_recurrence(
    identity: dict[str, object],
    post: dict[str, object],
    evidence: dict[str, str],
    first: dict[str, object],
) -> None:
    """Prove recurrence alone cannot manufacture accepted-control failure."""

    prior = [{**first, "_path": "/tmp/first-recovery.json"}]
    duplicate = decide_next_boundary(
        identity=identity,
        post_retrieval=post,
        governing_evidence=evidence,
        previous=prior,
        consumed_fingerprints=set(),
        owning_component="sage.request-execution",
        control_action_id="SAGE-ACTION-20260810-001",
        control_action_status="accepted",
        accepted_control_failure=None,
    )
    if duplicate["next_boundary"] != "await-existing-reentry":
        raise RuntimeError("duplicate planning re-entry was not blocked")

    consumed = {str(first["governing_condition_fingerprint"])}
    repeated = decide_next_boundary(
        identity=identity,
        post_retrieval=post,
        governing_evidence=evidence,
        previous=prior,
        consumed_fingerprints=consumed,
        owning_component="sage.request-execution",
        control_action_id="SAGE-ACTION-20260810-001",
        control_action_status="accepted",
        accepted_control_failure=None,
    )
    if repeated["disposition"] != "repair":
        raise RuntimeError("consumed recurrence falsely became accepted-control failure")
    if repeated["next_boundary"] != "implementation-local":
        raise RuntimeError("consumed recurrence escaped implementation-local repair")

    assertion = build_accepted_control_failure_assertion(
        control_action_id="SAGE-ACTION-20260810-001",
        violated_obligation=(
            "fixture: accepted recovery control violated its promised "
            "post-retrieval routing behavior"
        ),
        evidence_references=("fixture:accepted-control-contract-violation",),
    )
    successor = decide_next_boundary(
        identity=identity,
        post_retrieval=post,
        governing_evidence=evidence,
        previous=prior,
        consumed_fingerprints=consumed,
        owning_component="sage.request-execution",
        control_action_id="SAGE-ACTION-20260810-001",
        control_action_status="accepted",
        accepted_control_failure=assertion,
    )
    if successor["disposition"] != "successor-action":
        raise RuntimeError("explicit accepted-control violation did not escalate")
    if successor["next_boundary"] != "architect-decision":
        raise RuntimeError("explicit accepted-control violation lost Architect boundary")
    successor = bind_successor_operator_boundary(
        successor, Path("/tmp/recovery-next-boundary.json")
    )
    command = successor.get("operator_boundary", {}).get("command", "")
    if "sage-improvement-action-transition.py --recovery-decision" not in command:
        raise RuntimeError("successor escalation bypassed action lifecycle")


def _live_accepted_control_attribution_self_test() -> None:
    """Replay the live Action-001 d173/b869 attribution contradiction."""

    expected_identity = (
        "d173954d83b3ca52666a4380ea3b7ace129c8a5c57182390a3b3a4e31c9eb16e"
    )
    expected_fingerprint = (
        "b869f5985a1d5d31b309c481779b2e9a341e6dbe912356cc8d8115a5aeba6ec2"
    )
    identity = {
        "request_sha256": (
            "8b45d3ebe51aa680cee343b7ab0d3f4b136bb141535b58e0d670efacf76f4f40"
        ),
        "component_id": "sage.request-execution",
        "failure_signature": (
            "8b1f07cb73f85f9db4507881fe4d9475bbc0bdccfffc244d5a29d28b8753b418"
        ),
        "repository_authority": {
            "branch": "feature/sage-action-20260815-002-immutable-artifact-promotion",
            "head": "c1bea2c03ad1aa38b9aa4a57af39cdba71611211",
        },
        "repository_authority_sha256": (
            "0ff9377865fdd1b2c17230f4db3eef5ca06527f58293cee316b2f4b226228e71"
        ),
        "identity_sha256": expected_identity,
    }
    post = {
        "governing_conditions": {
            "authority": False,
            "scope": False,
            "required_capability": False,
            "safety_requirements": False,
            "repository_owned_composition": False,
            "approval_or_mutation_boundaries": False,
        },
        "disposition": "implementation-local-retry",
        "required_reentry_boundary": "implementation-local",
    }
    evidence = {
        "authority_contract_sha256": (
            "1e052c26358ac39414a56ea60114b5d336a58c99ab46a73d29445fb8c72cb651"
        ),
        "scope_sha256": (
            "07c05d1a24f4eb4eb0f9ce4b0e03ccb6cf7134f8dbee0ca773ea7db8ed0dfec2"
        ),
        "required_capability_sha256": (
            "a6c8d7d894e347e42c3956da4a14342f6a53434be39b1e367006098e31615c8e"
        ),
        "safety_requirements_sha256": (
            "cd3ce1d1aa1da2dc0ff2887a902aef33f2057e89ef804f45d8aebfbdb5bfad97"
        ),
        "repository_owned_composition_sha256": (
            "2f23579d02b20db50e1204fb17ec631f71213f98e0ff2b1be8e5f85f128eae5f"
        ),
        "approval_or_mutation_boundaries_sha256": (
            "a2e48c34194eba4155d072e5c9ead05d1b886c2a05cf7e57007d98a11df0e7d4"
        ),
        "observed_remote_main": "cf514c41400ed546c9781db0f5834ea5d16a14fa",
    }
    prior = [{
        "governing_condition_fingerprint": expected_fingerprint,
        "disposition": "governance-reentry",
        "_path": "/fixture/previous-recovery.json",
    }]
    decision = decide_next_boundary(
        identity=identity,
        post_retrieval=post,
        governing_evidence=evidence,
        previous=prior,
        consumed_fingerprints={expected_fingerprint},
        owning_component="sage.request-execution",
        control_action_id="SAGE-ACTION-20260810-001",
        control_action_status="accepted",
        accepted_control_failure=None,
    )
    if decision.get("recovery_identity", {}).get("identity_sha256") != expected_identity:
        raise RuntimeError("live attribution regression lost d173 recovery identity")
    if decision.get("governing_condition_fingerprint") != expected_fingerprint:
        raise RuntimeError("live attribution regression lost b869 governing fingerprint")
    if decision.get("disposition") != "repair":
        raise RuntimeError("live unchanged whitespace recurrence falsely escalated")
    if decision.get("next_boundary") != "implementation-local":
        raise RuntimeError("live unchanged whitespace recurrence left implementation-local")
    control = decision.get("owning_control", {})
    if control.get("accepted_control_failure") is not False:
        raise RuntimeError("live recurrence manufactured accepted-control failure")
    if control.get("accepted_control_failure_assertion") is not None:
        raise RuntimeError("live recurrence manufactured control-failure evidence")


def _idempotent_recovery_consumption_self_test() -> None:
    """Prove identical implementation-local recovery consumption is idempotent."""

    import workflows.request_execution as request_execution_workflow  # noqa: PLC0415

    class _Result:
        output_sha256 = "9" * 64

    class _Runner:
        def __init__(self) -> None:
            self.calls = 0

        def run(self, *_args, **_kwargs):
            self.calls += 1
            return _Result()

    with tempfile.TemporaryDirectory(
        prefix="sage-request-execute-idempotent-recovery-"
    ) as raw:
        root = Path(raw)
        state_root = root / "sage-request-execution"
        run_dir = state_root / "fixture-run"
        run_dir.mkdir(parents=True)
        identity_sha = "1" * 64
        fingerprint = "2" * 64
        decision_path = run_dir / "recovery-next-boundary.json"
        decision_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "record_type": "sage-recovery-next-boundary",
                    "owning_component": "sage.request-execution",
                    "disposition": "repair",
                    "next_boundary": "implementation-local",
                    "recovery_identity": {"identity_sha256": identity_sha},
                    "governing_condition_fingerprint": fingerprint,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        runner = _Runner()
        original_runtime = request_execution_workflow._request_execution_recovery_runtime
        request_execution_workflow._request_execution_recovery_runtime = (
            lambda _repo, _state_dir: (runner, run_dir / "recovery-consumption-events.jsonl")
        )
        try:
            first = request_execution_workflow.consume_recovery_decision(
                root,
                decision_path,
            )
            receipt = run_dir / "recovery-governing-change-consumption.json"
            if first.get("status") != "consumed" or not receipt.is_file():
                raise RuntimeError("first recovery consumption did not persist one receipt")
            first_receipt = receipt.read_bytes()

            second = request_execution_workflow.consume_recovery_decision(
                root,
                decision_path,
            )
            if second.get("status") != "already-consumed":
                raise RuntimeError("second identical recovery consumption was not idempotent")
            if second.get("consumption") is not None:
                raise RuntimeError("idempotent recovery reported a duplicate consumption receipt")
            if receipt.read_bytes() != first_receipt:
                raise RuntimeError("idempotent recovery rewrote the first consumption receipt")
            receipts = list(root.rglob("recovery-governing-change-consumption.json"))
            if receipts != [receipt]:
                raise RuntimeError("idempotent recovery created a second consumption receipt")
            if runner.calls != 2:
                raise RuntimeError("idempotent recovery did not revalidate on recurrence")
            if second.get("repository_mutation") is not False:
                raise RuntimeError("idempotent recovery claimed repository mutation")
        finally:
            request_execution_workflow._request_execution_recovery_runtime = original_runtime


def _repair_recurrence_self_test() -> None:
    """Prove unchanged recurrence stays at repair without governance re-entry."""

    identity = build_recovery_identity(
        request="Action-002 immutable promotion",
        component_id="sage.request-execution",
        failure_text=(
            "ancestry failure at "
            "4192551f1df150d06d8ad62235746bc5f29eaa18"
        ),
        repository_authority={"branch": "feature/fixture", "head": "4" * 40},
    )
    post = classify_post_retrieval_continuation(
        retrieval_performed=True,
        attempted_action_authorized=True,
        governing_changes={
            "authority": False, "scope": False, "required_capability": False,
            "safety_requirements": False, "repository_owned_composition": False,
            "approval_or_mutation_boundaries": False,
        },
        recovery_identity=identity,
    )
    evidence = {"repository_owned_composition_sha256": "a" * 64}
    first = decide_next_boundary(
        identity=identity, post_retrieval=post, governing_evidence=evidence,
        previous=(), consumed_fingerprints=set(),
        owning_component="sage.request-execution", control_action_id=None,
        control_action_status=None, accepted_control_failure=None,
    )
    bound = bind_successor_operator_boundary(
        first, Path("/tmp/request-execution-recovery-next-boundary.json")
    )
    command = bound.get("operator_boundary", {}).get("command", "")
    if "sage-request-execute.py --recovery-decision" not in command:
        raise RuntimeError(
            "implementation-local repair bypassed request-execution recovery consumer"
        )
    prior = [{**first, "_path": "/tmp/first-repair.json"}]
    second = decide_next_boundary(
        identity=identity, post_retrieval=post, governing_evidence=evidence,
        previous=prior, consumed_fingerprints=set(),
        owning_component="sage.request-execution", control_action_id=None,
        control_action_status=None, accepted_control_failure=None,
    )
    if second["classification"] != "recurrence":
        raise RuntimeError("second live failure was not classified as recurrence")
    if second["disposition"] != "repair":
        raise RuntimeError("unchanged recurrence did not stay at repair")


def _diagnosis_recovery_self_test() -> None:
    """Prove failure diagnosis consumes the same recovery contract."""

    identity = build_recovery_identity(
        request="fixture request", component_id="sage.request-execution",
        failure_text="fixture failure",
        repository_authority={"branch": "feature/fixture", "head": "4" * 40},
    )
    post = classify_post_retrieval_continuation(
        retrieval_performed=True, attempted_action_authorized=True,
        governing_changes={name: False for name in (
            "authority", "scope", "required_capability", "safety_requirements",
            "repository_owned_composition", "approval_or_mutation_boundaries",
        )}, recovery_identity=identity,
    )
    decision = decide_next_boundary(
        identity=identity, post_retrieval=post, governing_evidence={"fixture": "a"},
        previous=(), consumed_fingerprints=set(),
        owning_component="sage.request-execution", control_action_id=None,
        control_action_status=None, accepted_control_failure=None,
    )
    component = {"component_id": "fixture", "component_version": "1.0",
                 "source_path": "fixture.py", "description": "fixture"}
    diagnosis = FailureDiagnoser.diagnose(
        diagnosis_id="SAGE-DIAG-FIXTURE", failure_id="fixture",
        attempted_action="fixture", what_failed="fixture failure",
        direct_evidence=({"kind": "fixture", "value": "failure"},),
        actual_path=component, expected_path=component,
        why_actual_path_differed="fixture", ownership="composition",
        mutation_effect={}, lesson_use={"retrieval_performed": True},
        previous_failure_references=(), avoidable_rework_minutes=None,
        correction={"disposition": "update-composition",
                    "reusable_correction": "fixture",
                    "regression_test_required": True},
        evidence_references=("fixture",), recovery_decision=decision,
    )
    if diagnosis.get("recovery", {}).get("identity_sha256") != identity["identity_sha256"]:
        raise RuntimeError("failure diagnosis lost shared recovery identity")


class _AncestrySnapshot:
    """Minimal synchronized feature snapshot for ancestry regression."""

    branch = "feature/fixture"
    head = "0" * 40
    upstream_head = "0" * 40
    working_tree_status = "clean"

    def as_dict(self) -> dict[str, object]:
        """Return the fields consumed by request execution."""

        return {
            "branch": self.branch,
            "head": self.head,
            "upstream_head": self.upstream_head,
            "working_tree_status": self.working_tree_status,
        }


class _NonAncestorInspector:
    """Fail if request execution tries to elevate main ancestry to authority."""

    def require_clean(self) -> None:
        """Accept the clean regression fixture."""

    def require_branch(self, expected: str) -> None:
        """Verify proposal-bound branch authority."""

        if expected != "feature/fixture":
            raise RuntimeError("fixture branch binding changed")

    def require_head(self, expected: str) -> None:
        """Verify proposal-bound HEAD authority."""

        if expected != "0" * 40:
            raise RuntimeError("fixture HEAD binding changed")

    def snapshot(self) -> _AncestrySnapshot:
        """Return the synchronized feature snapshot."""

        return _AncestrySnapshot()

    def remote_head(self, remote: str, branch: str) -> str:
        """Return an intentionally non-ancestor main authority."""

        if (remote, branch) != ("origin", "main"):
            raise RuntimeError("unexpected remote authority lookup")
        return "1" * 40

    def is_ancestor(self, _ancestor: str, _descendant: str) -> bool:
        """Prove the execution path never asks this question."""

        raise RuntimeError("request execution must not require current-main ancestry")


def _ancestry_regression_self_test() -> None:
    """Prove synchronized feature authority does not require main ancestry."""

    from types import SimpleNamespace
    from workflows.request_execution import git_action  # noqa: PLC0415

    context = SimpleNamespace(
        bundle=SimpleNamespace(manifest={
            "repository": {"branch": "feature/fixture", "head": "0" * 40}
        }),
        inspector=_NonAncestorInspector(),
        git_snapshot=None,
        remote_main_head=None,
    )
    observed = git_action(context)
    if observed.get("remote_main_head") != "1" * 40:
        raise RuntimeError("live main authority was not captured")

    path = Path(__file__).resolve().parent / "workflows/request_execution.py"
    source = path.read_text(encoding="utf-8")
    if "context.inspector.is_ancestor(" in source:
        raise RuntimeError("request execution still enforces false main ancestry")
    if "remote main authority changed during validation" not in source:
        raise RuntimeError("frozen-main drift protection was not preserved")


def self_test() -> int:
    """Exercise positive and negative proposal-package runtime paths."""

    _recovery_identity_self_test()
    _recovery_boundary_self_test()
    _live_accepted_control_attribution_self_test()
    _idempotent_recovery_consumption_self_test()
    _repair_recurrence_self_test()
    _diagnosis_recovery_self_test()
    _ancestry_regression_self_test()
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

        unchanged = classify_post_retrieval_continuation(
            retrieval_performed=True,
            attempted_action_authorized=True,
            governing_changes={
                "authority": False,
                "scope": False,
                "required_capability": False,
                "safety_requirements": False,
                "repository_owned_composition": False,
                "approval_or_mutation_boundaries": False,
            },
        )
        if unchanged["disposition"] != "implementation-local-retry":
            raise RuntimeError("unchanged post-retrieval conditions did not stay implementation-local")
        require_post_retrieval_boundary(unchanged, "implementation-local")
        try:
            require_post_retrieval_boundary(unchanged, "planning")
        except ValueError:
            pass
        else:
            raise RuntimeError("redundant replanning after unchanged failure did not fail closed")

        composition_changed = classify_post_retrieval_continuation(
            retrieval_performed=True,
            attempted_action_authorized=True,
            governing_changes={
                "authority": False,
                "scope": False,
                "required_capability": False,
                "safety_requirements": False,
                "repository_owned_composition": True,
                "approval_or_mutation_boundaries": False,
            },
        )
        if (
            composition_changed["disposition"] != "governance-reentry"
            or composition_changed["required_reentry_boundary"] != "planning"
        ):
            raise RuntimeError("composition change did not require planning re-entry")
        try:
            require_post_retrieval_boundary(composition_changed, "implementation-local")
        except ValueError:
            pass
        else:
            raise RuntimeError("composition-changing same-request retry did not fail closed")
        require_post_retrieval_boundary(composition_changed, "planning")
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
    print("PASS owner-aware request-execution implementation-local recovery handoff")
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
    parser.add_argument("--recovery-decision", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    """Run the self-test or exact governed request execution."""

    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    if args.recovery_decision is not None:
        if any(
            value is not None
            for value in (
                args.request,
                args.proposal,
                args.continue_state,
                args.operator_result,
                args.routine_receipt,
            )
        ):
            raise ProposalError(
                "--recovery-decision cannot be combined with start or continue arguments"
            )
        from workflows.request_execution import consume_recovery_decision  # noqa: PLC0415
        result = consume_recovery_decision(
            repo,
            args.recovery_decision,
            args.output,
        )
        print("Kalaxy3 SAGE request-execution implementation-local recovery: PASS")
        print(json.dumps(result, indent=2))
        print("Next governed boundary:")
        print("  Retry the exact failed lifecycle request without changing its wording.")
        print("Repository mutation: none")
        return 0
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
