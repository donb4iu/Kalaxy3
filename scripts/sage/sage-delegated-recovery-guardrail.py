#!/usr/bin/env python3
"""Guard delegated implementation-local recovery approval semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from workflow.recovery import (
    build_accepted_control_failure_assertion,
    decide_next_boundary,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "sage-recovery-policy.json"
OBJECTIVE = ROOT / "scripts/sage/workflows/objective_execution.py"


def _decision(
    *,
    previous: Iterable[Mapping[str, Any]] = (),
    consumed: set[str] | None = None,
    governing_change: bool = False,
    accepted_failure: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic recovery decision fixture.

    Args:
        previous: Prior matching recovery decisions.
        consumed: Previously consumed governing fingerprints.
        governing_change: Whether authority changed after retrieval.
        accepted_failure: Optional accepted-control failure assertion.

    Returns:
        Recovery next-boundary decision.
    """
    return decide_next_boundary(
        identity={"identity_sha256": "a" * 64},
        post_retrieval={
            "disposition": (
                "governance-reentry" if governing_change else "implementation-local-retry"
            ),
            "required_reentry_boundary": "planning",
            "governing_conditions": {"authority": governing_change},
        },
        governing_evidence={"authority_changed": governing_change},
        previous=previous,
        consumed_fingerprints=consumed or set(),
        owning_component="sage.objective-execution",
        control_action_id="SAGE-ACTION-FIXTURE" if accepted_failure else None,
        control_action_status="accepted" if accepted_failure else None,
        accepted_control_failure=accepted_failure,
        progress_evidence=progress,
    )


def _policy_failures() -> list[str]:
    """Return delegated-recovery policy contract failures.

    Returns:
        Human-readable failures.
    """
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    behavior = policy.get("behavior", {})
    required = (
        "implementation_local_recovery_reuses_existing_approval",
        "recurrence_alone_does_not_require_architect_reentry",
        "architect_attention_requires_material_decision_surface_change",
        "implementation_local_recovery_requires_progress_evidence",
        "non_converging_recovery_must_exit_local_loop",
    )
    failures = [key for key in required if behavior.get(key) is not True]
    paths = policy.get("governing_composition_paths", [])
    if "scripts/sage/workflows/objective_execution.py" not in paths:
        failures.append("objective execution missing from governing composition")
    return failures


def _behavior_failures() -> list[str]:
    """Return deterministic delegated-recovery behavior failures.

    Returns:
        Human-readable failures.
    """
    failures: list[str] = []
    initial = _decision()
    if initial.get("architect_attention_required") is not False:
        failures.append("new local repair requests Architect attention")
    if initial.get("metrics", {}).get("avoided_architect_recovery_round_trips") != 1:
        failures.append("local repair does not measure avoided Architect round trip")
    fingerprint = str(initial.get("governing_condition_fingerprint", ""))
    progressed = _decision(
        previous=(initial,),
        consumed={fingerprint},
        progress={"verified_objective_steps": [{"proposal_id": "P-001"}]},
    )
    if progressed.get("next_boundary") != "implementation-local":
        failures.append("progressing recurrence escaped implementation-local recovery")
    if progressed.get("architect_attention_required") is not False:
        failures.append("progressing recurrence requests Architect attention")
    governance_first = _decision(governing_change=True)
    governance_fp = str(
        governance_first.get("governing_condition_fingerprint", "")
    )
    post_governance = _decision(
        previous=(governance_first,),
        consumed={governance_fp},
        governing_change=True,
    )
    if post_governance.get("next_boundary") != "implementation-local":
        failures.append(
            "consumed governance re-entry falsely counted as failed local repair"
        )
    if post_governance.get("metrics", {}).get("non_convergence_detected") is True:
        failures.append(
            "governance re-entry consumption falsely triggered non-convergence"
        )
    stalled = _decision(previous=(initial,), consumed={fingerprint})
    if stalled.get("next_boundary") != "architect-decision":
        failures.append("non-converging recurrence did not exit local recovery")
    if stalled.get("architect_attention_required") is not True:
        failures.append("non-converging recurrence did not surface Architect boundary")
    if stalled.get("metrics", {}).get("non_convergence_detected") is not True:
        failures.append("non-convergence is not measurable")
    if _decision(governing_change=True).get("architect_attention_required") is not True:
        failures.append("material governing change does not request Architect attention")
    return failures


def _accepted_control_failure() -> Mapping[str, Any]:
    """Return one explicit accepted-control failure fixture.

    Returns:
        Machine-readable accepted-control failure assertion.
    """
    return build_accepted_control_failure_assertion(
        control_action_id="SAGE-ACTION-FIXTURE",
        violated_obligation="fixture accepted control obligation failed",
        evidence_references=("evidence:fixture",),
    )


def main() -> int:
    """Validate delegated recovery authority and observability.

    Returns:
        Process exit status.
    """
    failures = _policy_failures() + _behavior_failures()
    initial = _decision()
    escalation = _decision(
        previous=(initial,),
        accepted_failure=_accepted_control_failure(),
    )
    if escalation.get("architect_attention_required") is not True:
        failures.append("accepted-control failure does not request Architect attention")
    objective = OBJECTIVE.read_text(encoding="utf-8")
    for marker in (
        "architect_approval_reused",
        "recovery_attempt_approval_atomicity",
        "existing-material-objective-path",
        "avoided_architect_recovery_round_trips",
        "_objective_recovery_progress",
        "verified_objective_steps",
        'item.get("status") != "verified"',
        "progress_evidence=",
        "architecture_evaluation_required",
    ):
        if marker not in objective:
            failures.append(f"objective execution missing marker: {marker}")
    if failures:
        print("Kalaxy3 SAGE delegated recovery guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS implementation-local recovery reuses existing objective approval")
    print("PASS progressing recurrence remains implementation-local")
    print("PASS consumed governance re-entry is distinct from consumed local repair")
    print("PASS non-converging recurrence exits the local recovery loop")
    print("PASS material governing change preserves Architect attention boundary")
    print("PASS accepted-control failure preserves successor Architect boundary")
    print("PASS delegated recovery exposes avoided Architect round-trip metrics")
    print("Kalaxy3 SAGE delegated recovery guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
