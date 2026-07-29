#!/usr/bin/env python3
"""Validate SAGE cost and observability feedback authority."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
REGISTRY_PATH: Final = ROOT / "sage-feedback-baseline-registry.json"
SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-feedback-comparison-schema-v1.0.json"
)
COMPARE_PATH: Final = ROOT / "scripts/sage/sage-feedback-compare.py"

EXPECTED_POLICY: Final = {
    "baseline_window": "baseline",
    "after_windows": [
        "immediate",
        "stabilization",
        "trend",
        "economic",
    ],
    "require_matching_currency": True,
    "require_matching_unit_economic_metrics": True,
    "require_matching_observability_metrics": True,
    "require_matching_units": True,
    "require_matching_directions": True,
    "require_provenance": True,
    "preserve_measurement_types": True,
    "percentage_change_when_baseline_zero": None,
    "composite_score_enabled": False,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_policy(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be an object"]

    if payload.get("feedback_compare_path") != (
        "scripts/sage/sage-feedback-compare.py"
    ):
        failures.append("feedback_compare_path changed")
    elif not COMPARE_PATH.is_file():
        failures.append("feedback comparison script missing")

    if payload.get("feedback_guardrail_path") != (
        "scripts/sage/sage-feedback-guardrail.py"
    ):
        failures.append("feedback_guardrail_path changed")

    registries = payload.get("registries", {})
    if registries.get("feedback_baselines") != (
        "sage-feedback-baseline-registry.json"
    ):
        failures.append("feedback baseline registry path changed")

    contracts = payload.get("contracts", {})
    if contracts.get("feedback_comparison_schema") != (
        "markdown/standards/"
        "sage-feedback-comparison-schema-v1.0.json"
    ):
        failures.append("feedback comparison schema path changed")

    if payload.get("feedback_comparison_policy") != EXPECTED_POLICY:
        failures.append("feedback_comparison_policy changed")
    return failures


def validate_registry(payload: Any) -> list[str]:
    expected = {
        "schema_version": "1.0",
        "registry_type": "feedback-baselines",
        "baselines": [],
    }
    if payload != expected:
        return [
            "feedback baseline registry must begin canonical and empty"
        ]
    return []


def validate_schema(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["feedback schema must be an object"]
    if payload.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append("feedback schema draft changed")
    if payload.get("additionalProperties") is not False:
        failures.append(
            "feedback schema must fail unknown properties"
        )
    required = payload.get("required", [])
    properties = payload.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            "feedback schema required fields must equal properties"
        )
    if "cost_comparison" not in properties:
        failures.append("cost comparison contract missing")
    if "observability_comparison" not in properties:
        failures.append("observability comparison contract missing")
    if "provenance" not in properties:
        failures.append("feedback provenance contract missing")
    return failures


def mutation_tests(
    policy: dict[str, Any],
    registry: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    policy_cases: list[tuple[str, dict[str, Any]]] = []
    no_currency = copy.deepcopy(policy)
    no_currency["feedback_comparison_policy"][
        "require_matching_currency"
    ] = False
    policy_cases.append(("currency matching disabled", no_currency))

    no_provenance = copy.deepcopy(policy)
    no_provenance["feedback_comparison_policy"][
        "require_provenance"
    ] = False
    policy_cases.append(("provenance disabled", no_provenance))

    composite = copy.deepcopy(policy)
    composite["feedback_comparison_policy"][
        "composite_score_enabled"
    ] = True
    policy_cases.append(("composite enabled", composite))

    for label, candidate in policy_cases:
        if not validate_policy(candidate):
            failures.append(
                f"policy negative test accepted {label}"
            )

    populated = copy.deepcopy(registry)
    populated["baselines"].append({"unexpected": True})
    if not validate_registry(populated):
        failures.append(
            "registry negative test accepted unexpected baseline"
        )

    weakened = copy.deepcopy(schema)
    weakened["additionalProperties"] = True
    if not validate_schema(weakened):
        failures.append(
            "schema negative test accepted unknown properties"
        )
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        policy = load_json(POLICY_PATH)
        registry = load_json(REGISTRY_PATH)
        schema = load_json(SCHEMA_PATH)

        failures.extend(validate_policy(policy))
        failures.extend(validate_registry(registry))
        failures.extend(validate_schema(schema))
        failures.extend(
            mutation_tests(policy, registry, schema)
        )
    except (OSError, ValueError, TypeError) as error:
        failures.append(str(error))

    if failures:
        print("Kalaxy3 SAGE feedback guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical feedback comparison policy")
    print("PASS empty feedback baseline registry")
    print("PASS cost and observability comparison schema")
    print("PASS matching currency, units, metrics, and directions")
    print("PASS provenance and measurement-type preservation")
    print("PASS zero-baseline and composite-score policies")
    print("PASS feedback policy mutation negative tests")
    print("Kalaxy3 SAGE feedback guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
