"""Reusable LLM architecture-evaluation contract for Architect approval."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from workflow import WorkflowError

POLICY_PATH = Path(
    "markdown/standards/sage-architecture-approval-evaluation-policy-v1.0.json"
)
RECOMMENDATIONS = {
    "retain",
    "approve-with-conditions",
    "revise",
    "defer",
    "reject",
}
MATERIALITY = {"material", "considered-not-material", "unknown"}
EPISTEMIC_STATES = {
    "demonstrated",
    "derived",
    "hypothesized",
    "unknown",
    "contradicted",
}


def _require_text(value: Any, label: str) -> str:
    """Return non-empty text or fail closed."""
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"architecture evaluation requires {label}")
    return value.strip()


def _require_list(value: Any, label: str) -> list[Any]:
    """Return a list or fail closed."""
    if not isinstance(value, list):
        raise WorkflowError(f"architecture evaluation requires {label} list")
    return value


def load_policy(repo: Path) -> Mapping[str, Any]:
    """Load repository-owned architecture-evaluation guidance."""
    path = repo.expanduser().resolve() / POLICY_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(
            f"architecture evaluation policy unreadable: {error}"
        ) from error
    if not isinstance(value, Mapping):
        raise WorkflowError("architecture evaluation policy must be an object")
    principles = value.get("principles")
    if not isinstance(principles, Mapping):
        raise WorkflowError("architecture evaluation policy principles missing")
    required_true = (
        "independent_evaluation_before_material_approval",
        "framework_guided_not_framework_bound",
        "broad_solution_space_required",
        "current_sage_capability_is_not_solution_boundary",
        "additional_fit_for_purpose_lenses_allowed",
        "checklist_completion_is_not_fitness_evidence",
        "opaque_aggregate_score_prohibited",
        "implementation_micromanagement_is_not_the_goal",
        "explicit_unknowns_and_limits_required",
    )
    if any(principles.get(name) is not True for name in required_true):
        raise WorkflowError("architecture evaluation policy weakened")
    return value


def service_contract(repo: Path | None = None) -> Mapping[str, Any]:
    """Return the reusable, framework-guided evaluation service surface."""
    resolved = repo or Path(__file__).resolve().parents[2]
    policy = load_policy(resolved)
    return {
        "record_type": "sage-llm-architecture-evaluation-service",
        "policy": str(POLICY_PATH),
        "framework_guided_not_bound": True,
        "framework_seeds": policy["framework_seeds"],
        "service_area_seeds": policy["service_area_seeds"],
        "desired_evaluation_effects": policy["desired_evaluation_effects"],
        "additional_lenses_allowed": True,
        "checklist_completion_required": False,
        "opaque_aggregate_score_allowed": False,
        "approval_authority": "Architect",
        "evaluator_authority": "advisory",
    }


def evaluation_sha256(value: Mapping[str, Any]) -> str:
    """Return stable content identity for one evaluation payload."""
    payload = json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_lenses(value: Any) -> None:
    """Validate chosen lenses without constraining the LLM to a fixed list."""
    lenses = _require_list(value, "lenses_considered")
    if not lenses:
        raise WorkflowError(
            "architecture evaluation requires at least one considered lens"
        )
    for item in lenses:
        if not isinstance(item, Mapping):
            raise WorkflowError("architecture evaluation lens must be an object")
        _require_text(item.get("lens"), "lens name")
        if item.get("materiality") not in MATERIALITY:
            raise WorkflowError(
                "architecture evaluation lens materiality is invalid"
            )
        _require_text(item.get("rationale"), "lens rationale")


def _validate_findings(value: Any, empty_rationale: Any) -> None:
    """Validate findings while allowing an evidenced no-finding result."""
    findings = _require_list(value, "material_findings")
    if not findings:
        _require_text(empty_rationale, "no_material_findings_rationale")
        return
    for item in findings:
        if not isinstance(item, Mapping):
            raise WorkflowError(
                "architecture evaluation finding must be an object"
            )
        _require_text(item.get("service_area"), "finding service_area")
        _require_text(item.get("finding"), "finding")
        if item.get("epistemic_status") not in EPISTEMIC_STATES:
            raise WorkflowError(
                "architecture evaluation epistemic_status is invalid"
            )
        _require_text(
            item.get("expected_decision_impact"),
            "finding expected_decision_impact",
        )
        indicators = _require_list(
            item.get("measurable_indicators"),
            "finding measurable_indicators",
        )
        for indicator in indicators:
            _require_text(indicator, "measurable indicator")


def _validate_influence(value: Any) -> None:
    """Validate impact-oriented decision contribution evidence."""
    if not isinstance(value, Mapping):
        raise WorkflowError("architecture evaluation requires decision_influence")
    for name in (
        "risks_exposed",
        "alternatives_widened",
        "assumptions_challenged",
    ):
        _require_list(value.get(name), f"decision_influence.{name}")
    _require_text(
        value.get("information_gain"),
        "decision_influence.information_gain",
    )


def validate_evaluation(
    value: Any,
    *,
    objective_id: str,
    decision_surface_sha256: str,
) -> Mapping[str, Any]:
    """Validate advisory breadth and exact decision-surface binding."""
    if not isinstance(value, Mapping):
        raise WorkflowError("architecture evaluation payload is missing")
    if value.get("schema_version") != "1.0":
        raise WorkflowError("architecture evaluation schema_version must be 1.0")
    if value.get("record_type") != "sage-llm-architecture-approval-evaluation":
        raise WorkflowError("architecture evaluation record_type is invalid")
    if value.get("producer_class") != "llm-architecture-evaluator":
        raise WorkflowError("architecture evaluation producer_class is invalid")
    if value.get("authority") != "advisory":
        raise WorkflowError(
            "architecture evaluation cannot claim approval authority"
        )
    if value.get("objective_id") != objective_id:
        raise WorkflowError("architecture evaluation objective does not match")
    if value.get("decision_surface_sha256") != decision_surface_sha256:
        raise WorkflowError(
            "architecture evaluation does not bind exact decision surface"
        )
    for name in (
        "framework_guided_not_bound",
        "broad_solution_space_evaluated",
        "current_sage_capability_not_solution_boundary",
    ):
        if value.get(name) is not True:
            raise WorkflowError(f"architecture evaluation requires {name}=true")
    _validate_lenses(value.get("lenses_considered"))
    _require_list(value.get("additional_lenses", []), "additional_lenses")
    _require_text(value.get("alternative_assessment"), "alternative_assessment")
    _validate_findings(
        value.get("material_findings"),
        value.get("no_material_findings_rationale"),
    )
    _require_list(value.get("unknowns_and_limits"), "unknowns_and_limits")
    _validate_influence(value.get("decision_influence"))
    if value.get("recommendation") not in RECOMMENDATIONS:
        raise WorkflowError("architecture evaluation recommendation is invalid")
    return value


def self_test() -> None:
    """Exercise broad-lens and authority-negative behavior."""
    base = {
        "schema_version": "1.0",
        "record_type": "sage-llm-architecture-approval-evaluation",
        "producer_class": "llm-architecture-evaluator",
        "authority": "advisory",
        "objective_id": "SAGE-ACTION-FIXTURE",
        "decision_surface_sha256": "a" * 64,
        "framework_guided_not_bound": True,
        "broad_solution_space_evaluated": True,
        "current_sage_capability_not_solution_boundary": True,
        "lenses_considered": [
            {
                "lens": "WAR/reliability",
                "materiality": "material",
                "rationale": "Failure recovery affects the objective.",
            },
            {
                "lens": "CAF/people",
                "materiality": "considered-not-material",
                "rationale": "No material participant change is proposed.",
            },
            {
                "lens": "human-factors-and-usability",
                "materiality": "material",
                "rationale": "Comprehension changes architectural fitness.",
            },
        ],
        "additional_lenses": ["human-factors-and-usability"],
        "alternative_assessment": (
            "Compared retain, simplify, and delegate options."
        ),
        "material_findings": [
            {
                "service_area": "stakeholder-value-and-human-factors",
                "finding": "A hidden collection increases navigation burden.",
                "epistemic_status": "derived",
                "expected_decision_impact": (
                    "Prefer inspectable collection navigation."
                ),
                "measurable_indicators": ["navigation_hops_to_known_item"],
            }
        ],
        "unknowns_and_limits": [
            "No measured unfamiliar-user completion time yet."
        ],
        "decision_influence": {
            "risks_exposed": ["navigation burden"],
            "alternatives_widened": ["searchable master/detail"],
            "assumptions_challenged": [
                "count-only summaries are sufficient"
            ],
            "information_gain": (
                "Made human-factor cost explicit before approval."
            ),
        },
        "recommendation": "revise",
    }
    validate_evaluation(
        base,
        objective_id="SAGE-ACTION-FIXTURE",
        decision_surface_sha256="a" * 64,
    )
    broadened = dict(base)
    broadened["lenses_considered"] = list(base["lenses_considered"]) + [
        {
            "lens": "novel-fit-for-purpose-lens",
            "materiality": "unknown",
            "rationale": (
                "The LLM may introduce a relevant lens not in policy seeds."
            ),
        }
    ]
    validate_evaluation(
        broadened,
        objective_id="SAGE-ACTION-FIXTURE",
        decision_surface_sha256="a" * 64,
    )
    bad = dict(base)
    bad["authority"] = "Architect"
    try:
        validate_evaluation(
            bad,
            objective_id="SAGE-ACTION-FIXTURE",
            decision_surface_sha256="a" * 64,
        )
    except WorkflowError:
        pass
    else:
        raise RuntimeError(
            "architecture evaluator illegally acquired approval authority"
        )
    print("PASS framework seeds do not bound additional LLM lenses")
    print("PASS evaluation is bound to the exact decision surface")
    print("PASS broad solution-space evaluation is explicit")
    print("PASS Architect approval authority cannot transfer to the LLM")
