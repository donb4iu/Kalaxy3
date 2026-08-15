#!/usr/bin/env python3
"""Fail-closed runtime guardrail for SAGE decision and diagnosis primitives."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    AuthorityAssertion,
    AuthorityReconciler,
    CapabilityGapRecorder,
    ComponentCandidate,
    ComponentSelector,
    FailureDiagnoser,
    RequiredCapability,
)

ARTIFACT_ROOT = ROOT / "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001"
EXPECTED = {
    "authority.reconcile": ARTIFACT_ROOT / "capability-gap-authority-reconcile.json",
    "component.select": ARTIFACT_ROOT / "capability-gap-component-select.json",
    "capability.gap": ARTIFACT_ROOT / "capability-gap-capability-gap.json",
    "failure.diagnose": ARTIFACT_ROOT / "capability-gap-failure-diagnose.json",
}


def runtime_tests() -> list[str]:
    failures: list[str] = []
    repository = {"path": ".", "branch": "feature/test", "head": "a" * 40, "upstream_head": "a" * 40, "working_tree_clean": True}
    assertions = [
        AuthorityAssertion("AUTH-001", "git", "repository", "HEAD", "2026-08-01T22:00:00-05:00", "current", "git.head", "a" * 40, "measured", "high", "material", None),
        AuthorityAssertion("AUTH-002", "repository-policy", "repository", "policy", "2026-08-01T22:00:00-05:00", "current", "policy.state", "staged", "declared", "high", "material", None),
    ]
    receipt = AuthorityReconciler(("git", "repository-policy")).reconcile(receipt_id="SAGE-AUTH-20260801-999", request="test", repository=repository, assertions=assertions, evidence_references=("fixture",), captured_at="2026-08-01T22:00:00-05:00")
    if receipt.reconciliation["disposition"] != "complete" or receipt.mutation_gate["status"] != "review-ready":
        failures.append("complete authority did not become review-ready")
    conflict = AuthorityReconciler(("git",)).reconcile(receipt_id="SAGE-AUTH-20260801-998", request="test", repository=repository, assertions=(*assertions[:1], AuthorityAssertion("AUTH-003", "git", "repository", "other", "2026-08-01T22:00:00-05:00", "current", "git.head", "b" * 40, "measured", "high", "material", None)), evidence_references=("fixture",), captured_at="2026-08-01T22:00:00-05:00")
    if conflict.mutation_gate["status"] != "blocked":
        failures.append("conflicting authority did not block mutation")

    selector = ComponentSelector()
    capability = RequiredCapability("CAP-999", "test capability")
    good = ComponentCandidate("CANDIDATE-999", ("CAP-999",), "component.good", "1.0.0", "good.py", "pilot", {"applicability":"direct","authority_compatibility":"compatible","mutation_scope_fit":"least-authority","published_interface_verified":True,"successful_production_executions":None,"failed_production_executions":None,"open_recurrence":"no","runtime_test_coverage":"positive-and-negative"}, ("fixture",), "direct least-authority fit")
    bad = ComponentCandidate("CANDIDATE-998", ("CAP-999",), "component.bad", "1.0.0", "bad.py", "pilot", {"applicability":"partial","authority_compatibility":"compatible","mutation_scope_fit":"broader-than-required","published_interface_verified":True,"successful_production_executions":10,"failed_production_executions":0,"open_recurrence":"no","runtime_test_coverage":"positive-and-negative"}, ("fixture",), "broader path")
    manifest = selector.build_manifest(manifest_id="SAGE-COMP-20260801-999", request="test", authority_receipt="fixture", capabilities=(capability,), candidates=(bad, good), approval={"status":"approved","reviewed_by":"operator","reviewed_at":"2026-08-01T22:00:00-05:00","rationale":"fixture"}, created_at="2026-08-01T22:00:00-05:00")
    if manifest["selections"][0]["component_id"] != "component.good" or manifest["composite_score_enabled"] is not False:
        failures.append("component selection did not choose explicit least-authority candidate")
    try:
        selector.require_complete({**manifest, "capability_gap_receipts": ["CAP-999"]})
    except ValueError:
        pass
    else:
        failures.append("unresolved component gap did not fail closed")

    gap = CapabilityGapRecorder.create(gap_id="SAGE-GAP-20260801-999", request="test", authority_receipt="fixture", component_manifest="fixture", required_capability="test", candidates_considered=({"component_id":"old","version":"1.0.0","source_path":"old.py","insufficiency":"missing contract","composition_can_close_gap":False},), missing_interface_or_behavior="new contract", why_configuration_is_insufficient="configuration cannot add interface", why_composition_is_insufficient="composition cannot add interface", proposed_primitive={"primitive_id":"new.primitive","responsibility":"test","side_effects":"none","idempotency":"deterministic","logging":"caller","failure_mode":"fail closed","runtime_tests":["positive","negative"],"initial_maturity":"pilot"}, approval={"status":"approved","reviewed_by":"operator","reviewed_at":"2026-08-01T22:00:00-05:00","rationale":"fixture"}, evidence_references=("fixture",), created_at="2026-08-01T22:00:00-05:00")
    CapabilityGapRecorder.assert_implementation_allowed(gap)
    domain_gap = CapabilityGapRecorder.create_domain(
        gap_id="SAGE-GAP-20260815-DOMAIN",
        request="test",
        authority_receipt="fixture",
        component_manifest="fixture",
        required_capability="DOMAIN-SECRET-MANAGEMENT",
        candidates_considered=({
            "component_id":"workflow.fixture",
            "version":"1.0.0",
            "source_path":"fixture.py",
            "insufficiency":"workflow primitive does not provide reusable secrets management",
            "composition_can_close_gap":False,
        },),
        missing_interface_or_behavior="Reusable secrets management with credentials outside Git and observable command/evidence surfaces.",
        why_configuration_is_insufficient="A controller-local token file plus rendered Kubernetes Secret does not establish the reusable capability.",
        why_composition_is_insufficient="Existing workflow primitives can govern selection but do not supply the domain capability.",
        approval={"status":"review-required","reviewed_by":None,"reviewed_at":None,"rationale":"domain selection required"},
        evidence_references=("fixture:architect-planning-obligation",),
        created_at="2026-08-15T01:00:00-05:00",
    )
    CapabilityGapRecorder.assert_domain_selection_required(domain_gap)
    if domain_gap["gap"]["new_primitive_required"] is not False or domain_gap["proposed_primitive"] is not None:
        failures.append("domain capability gap incorrectly authorized a new primitive")
    try:
        CapabilityGapRecorder.assert_implementation_allowed(domain_gap)
    except ValueError:
        pass
    else:
        failures.append("domain capability gap was accepted as primitive implementation authority")
    try:
        CapabilityGapRecorder.assert_implementation_allowed({**gap, "approval": {"status":"review-required"}})
    except PermissionError:
        pass
    else:
        failures.append("unapproved capability gap did not fail closed")

    base = dict(diagnosis_id="SAGE-DIAG-20260801-999", failure_id="FAIL-999", attempted_action="test", what_failed="fixture", direct_evidence=({"source":"fixture","captured_at":"2026-08-01T22:00:00-05:00","observation":"failed","artifact":"fixture","sha256":None},), actual_path={"component_id":"bad","component_version":"1.0.0","source_path":"bad.py","description":"bad path"}, expected_path={"component_id":"good","component_version":"1.0.0","source_path":"good.py","description":"good path"}, why_actual_path_differed="selection bypass", ownership="composition", mutation_effect={"mutation_opportunity":True,"mutation_performed":False,"detected_pre_mutation":True,"mutation_scope":"none"}, lesson_use={"retrieval_performed":True,"applicable_lesson_ids":[],"surfaced_lesson_ids":[],"used_lesson_ids":[],"nonuse_reason":None}, previous_failure_references=(), avoidable_rework_minutes=None, correction={"disposition":"update-composition","reusable_correction":"enforce selected component","target_control_type":"guardrail","primitive_version_bump_required":False,"regression_test_required":True,"action_reference":None,"no_action_rationale":None}, evidence_references=("fixture",), recorded_at="2026-08-01T22:00:00-05:00")
    diagnosis = FailureDiagnoser.diagnose(**base)
    if diagnosis["classification"] != "new" or diagnosis["divergence"]["selection_failure"] is not True:
        failures.append("failure diagnosis semantics are incorrect")
    try:
        FailureDiagnoser.diagnose(**{**base, "previous_failure_references": ("FAIL-001",), "correction": {**base["correction"], "regression_test_required": False}})
    except ValueError:
        pass
    else:
        failures.append("recurring failure without control did not fail closed")
    return failures


def repository_contract_tests() -> list[str]:
    failures: list[str] = []
    registry = json.loads((ROOT / "sage-workflow-primitives.json").read_text(encoding="utf-8"))
    if registry.get("framework_version") != "0.4.0":
        failures.append("framework_version must be 0.4.0")
    entries = {item.get("primitive_id"): item for item in registry.get("primitives", []) if isinstance(item, dict)}
    for primitive_id, path in EXPECTED.items():
        entry = entries.get(primitive_id, {})
        if entry.get("version") != "1.0.0":
            failures.append(f"{primitive_id} must be version 1.0.0")
        if entry.get("capability_gap_receipt") != str(path.relative_to(ROOT)):
            failures.append(f"{primitive_id} capability-gap linkage mismatch")
        if not path.is_file():
            failures.append(f"missing capability-gap receipt: {path}")
        else:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if receipt.get("approval", {}).get("status") != "approved":
                failures.append(f"unapproved capability-gap receipt: {path}")
    manifest = ARTIFACT_ROOT / "component-selection-decision-primitives.json"
    if not manifest.is_file():
        failures.append("Phase 3 component-selection manifest is missing")
    else:
        value = json.loads(manifest.read_text(encoding="utf-8"))
        if value.get("approval", {}).get("status") != "approved" or value.get("composite_score_enabled") is not False:
            failures.append("Phase 3 component-selection manifest contract failed")
    policy = json.loads((ROOT / "sage-operating-contract-policy.json").read_text(encoding="utf-8"))
    activation = policy.get("activation_policy", {})
    if "decision-and-diagnosis-primitives" not in activation.get("completed_phases", []):
        failures.append("Phase 3 completion marker is missing")
    if activation.get("current_state") != "staged-implementation" or activation.get("deployment_authorized") is not False:
        failures.append("Phase 3 must remain staged and non-deploying")
    return failures


def main() -> int:
    failures = [*runtime_tests(), *repository_contract_tests()]
    if failures:
        print("Kalaxy3 SAGE decision primitives guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS federated authority reconciliation and conflict blocking")
    print("PASS explicit component ranking and composition manifests")
    print("PASS capability-gap proof and operator approval gate")
    print("PASS complete failure diagnosis and recurrence control")
    print("PASS Phase 3 registry, authority, policy, manifest, and receipt integration")
    print("Kalaxy3 SAGE decision primitives guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
