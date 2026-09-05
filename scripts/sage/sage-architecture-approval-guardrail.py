#!/usr/bin/env python3
"""Guard broad LLM architecture evaluation before material approval."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from architecture_approval import service_contract

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / (
    "markdown/standards/"
    "sage-architecture-approval-evaluation-policy-v1.0.json"
)
PROCESS = ROOT / (
    "markdown/standards/"
    "kalaxy3-sage-architecture-approval-evaluation-process.md"
)
SCHEMA = ROOT / (
    "markdown/standards/"
    "sage-architecture-approval-evaluation-schema-v1.0.json"
)
OBJECTIVE = ROOT / "scripts/sage/workflows/objective_execution.py"
MAKEFILE = ROOT / "Makefile"


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    """Load one machine-readable architecture contract."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _check_policy(
    policy: Mapping[str, Any],
    failures: list[str],
) -> None:
    """Validate authority and evaluation breadth from policy."""
    authority = policy.get("authority")
    if not isinstance(authority, Mapping):
        failures.append("policy authority contract is missing")
    else:
        if authority.get("architecture_approval") != "Architect":
            failures.append(
                "Architect is not the architecture approval authority"
            )
        if authority.get("architecture_evaluation") != "LLM advisory":
            failures.append(
                "LLM architecture evaluation is not advisory"
            )
        delegated = authority.get("implementation")
        if not isinstance(delegated, str) or "delegated" not in delegated:
            failures.append(
                "implementation is not explicitly delegated"
            )

    principles = policy.get("principles")
    if not isinstance(principles, Mapping):
        failures.append("policy principles are missing")
        return

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
    for name in required_true:
        if principles.get(name) is not True:
            failures.append(
                f"architecture policy weakened: {name}"
            )


def _check_service(failures: list[str]) -> None:
    """Validate reusable evaluation service semantics."""
    contract = service_contract(ROOT)

    exact = {
        "framework_guided_not_bound": True,
        "additional_lenses_allowed": True,
        "checklist_completion_required": False,
        "opaque_aggregate_score_allowed": False,
        "approval_authority": "Architect",
        "evaluator_authority": "advisory",
    }
    for name, expected in exact.items():
        actual = contract.get(name)
        if actual != expected:
            failures.append(
                f"architecture service {name}={actual!r}, "
                f"expected {expected!r}"
            )

    framework_seeds = contract.get("framework_seeds")
    if not isinstance(framework_seeds, Mapping):
        failures.append(
            "architecture service framework seeds are missing"
        )
        return

    if "war" not in framework_seeds:
        failures.append(
            "WAR does not seed the evaluation aperture"
        )
    if "caf" not in framework_seeds:
        failures.append(
            "CAF does not seed the evaluation aperture"
        )


def _check_schema(
    schema: Mapping[str, Any],
    failures: list[str],
) -> None:
    """Validate the persisted evaluation payload contract."""
    required = schema.get("required")
    if not isinstance(required, list):
        failures.append(
            "architecture evaluation schema required fields are missing"
        )
        return

    expected = {
        "authority",
        "objective_id",
        "decision_surface_sha256",
        "framework_guided_not_bound",
        "broad_solution_space_evaluated",
        "current_sage_capability_not_solution_boundary",
        "lenses_considered",
        "alternative_assessment",
        "material_findings",
        "unknowns_and_limits",
        "decision_influence",
        "recommendation",
    }
    missing = expected - set(required)
    if missing:
        failures.append(
            "architecture evaluation schema omits: "
            + ", ".join(sorted(missing))
        )


def _check_documentation(failures: list[str]) -> None:
    """Require explanatory documentation without executing its prose."""
    if not PROCESS.is_file():
        failures.append(
            "architecture evaluation process documentation is missing"
        )
        return

    text = PROCESS.read_text(encoding="utf-8")
    if not text.strip():
        failures.append(
            "architecture evaluation process documentation is empty"
        )


def _check_enforcement(failures: list[str]) -> None:
    """Validate the first concrete material-approval consumer."""
    objective = OBJECTIVE.read_text(encoding="utf-8")
    makefile = MAKEFILE.read_text(encoding="utf-8")

    markers = (
        "architecture_evaluation_service",
        "architecture_evaluation_required",
        "architecture_evaluation",
        "architecture_evaluation_sha256",
        "validate_architecture_evaluation",
    )
    for marker in markers:
        if marker not in objective:
            failures.append(
                f"material objective approval does not bind {marker}"
            )

    if "sage-architecture-approval-self-test" not in makefile:
        failures.append(
            "global self-test omits architecture evaluation"
        )
    if "sage-architecture-approval-guardrail" not in makefile:
        failures.append(
            "global guardrails omit architecture evaluation"
        )


def main() -> int:
    """Validate structured semantics, not prose formatting."""
    failures: list[str] = []

    policy = _load_json(
        POLICY,
        "architecture approval policy",
    )
    schema = _load_json(
        SCHEMA,
        "architecture approval schema",
    )

    _check_policy(policy, failures)
    _check_service(failures)
    _check_schema(schema, failures)
    _check_documentation(failures)
    _check_enforcement(failures)

    if failures:
        print(
            "Kalaxy3 SAGE architecture approval guardrail: "
            "FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        "PASS Architect approval authority comes from "
        "machine-readable policy"
    )
    print(
        "PASS LLM architecture evaluation remains advisory"
    )
    print(
        "PASS WAR and CAF seed but do not bound the evaluation aperture"
    )
    print(
        "PASS additional fit-for-purpose lenses remain available to the LLM"
    )
    print(
        "PASS current SAGE capability does not bound the solution space"
    )
    print(
        "PASS evaluation impact is distinct from checklist completion"
    )
    print(
        "PASS implementation remains delegated after Architect approval"
    )
    print(
        "PASS exact evaluation is content-bound into material approval"
    )
    print(
        "PASS explanatory prose is documentation, not an executable contract"
    )
    print(
        "Kalaxy3 SAGE architecture approval guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
