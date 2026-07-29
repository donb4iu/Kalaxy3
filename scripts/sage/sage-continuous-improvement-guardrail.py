#!/usr/bin/env python3
"""Validate SAGE continuous-improvement policy and registries."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
REGISTRIES: Final = {
    "change_candidates": (
        ROOT / "sage-change-candidate-registry.json",
        "change-candidates",
        "candidates",
    ),
    "lessons": (
        ROOT / "sage-lessons.json",
        "lessons",
        "lessons",
    ),
    "improvement_actions": (
        ROOT / "sage-improvement-actions.json",
        "improvement-actions",
        "actions",
    ),
}
REQUIRED_PLANES: Final = [
    "delivery",
    "operations",
    "economics",
    "learning",
]
REQUIRED_PREDICTION_STAGES: Final = [
    "discovery",
    "pre-deployment",
]
REQUIRED_SIZES: Final = ["XS", "S", "M", "L", "XL"]
REQUIRED_CONFIDENCE: Final = ["high", "medium", "low"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_policy(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be a JSON object"]

    if payload.get("schema_version") != "1.0":
        failures.append("policy schema_version must be 1.0")

    if payload.get("required_feedback_planes") != REQUIRED_PLANES:
        failures.append(
            "required_feedback_planes must preserve canonical order"
        )

    if payload.get("prediction_stages") != REQUIRED_PREDICTION_STAGES:
        failures.append(
            "prediction_stages must preserve canonical order"
        )

    prediction_policy = payload.get("prediction_policy", {})
    if prediction_policy.get(
        "record_before_outcome_is_known"
    ) is not True:
        failures.append(
            "predictions must be recorded before outcomes"
        )
    if prediction_policy.get("preserve_all_versions") is not True:
        failures.append("prediction versions must be preserved")
    if prediction_policy.get(
        "overwrite_previous_predictions"
    ) is not False:
        failures.append(
            "previous predictions must not be overwritten"
        )

    sizes = payload.get("tshirt_sizes", {})
    if list(sizes) != REQUIRED_SIZES:
        failures.append(
            "T-shirt sizes must be XS, S, M, L, XL in order"
        )
    else:
        boundaries = [
            (
                sizes["XS"].get("active_hours_min"),
                sizes["XS"].get("active_hours_max"),
            ),
            (
                sizes["S"].get("active_hours_min"),
                sizes["S"].get("active_hours_max"),
            ),
            (
                sizes["M"].get("active_hours_min"),
                sizes["M"].get("active_hours_max"),
            ),
            (
                sizes["L"].get("active_hours_min"),
                sizes["L"].get("active_hours_max"),
            ),
            (
                sizes["XL"].get("active_hours_min"),
                sizes["XL"].get("active_hours_max"),
            ),
        ]
        if boundaries != [
            (0, 4),
            (4, 12),
            (12, 32),
            (32, 80),
            (80, None),
        ]:
            failures.append(
                "T-shirt active-hour boundaries changed"
            )
        if sizes["XL"].get(
            "requires_decomposition"
        ) is not True:
            failures.append(
                "XL work must require decomposition"
            )

    if list(payload.get("confidence_ratings", {})) != REQUIRED_CONFIDENCE:
        failures.append(
            "confidence ratings must be high, medium, low"
        )

    branch_policy = payload.get("branch_policy", {})
    for key in (
        "small_cohesive_commits",
        "validate_before_commit",
        "push_after_each_cohesive_commit",
        "deployment_requires_explicit_gate",
        "revalidate_before_activation",
    ):
        if branch_policy.get(key) is not True:
            failures.append(
                f"branch_policy.{key} must be true"
            )

    metric_policy = payload.get("metric_policy", {})
    if metric_policy.get(
        "allow_composite_score_before_baseline"
    ) is not False:
        failures.append(
            "composite scoring must remain closed before baseline"
        )

    for label in ("standard_path", "guardrail_path"):
        relative = payload.get(label)
        if not isinstance(relative, str):
            failures.append(f"{label} must be a string")
        elif not (ROOT / relative).is_file():
            failures.append(
                f"{label} does not exist: {relative}"
            )

    registries = payload.get("registries")
    if not isinstance(registries, dict):
        failures.append("registries must be an object")
    else:
        for key in REGISTRIES:
            relative = registries.get(key)
            if not isinstance(relative, str):
                failures.append(
                    f"registry path missing: {key}"
                )
            elif not (ROOT / relative).is_file():
                failures.append(
                    f"registry path does not exist: {relative}"
                )

    return failures


def validate_registry(
    payload: Any,
    *,
    registry_type: str,
    collection: str,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return [f"{registry_type} registry must be an object"]

    expected_keys = [
        "schema_version",
        "registry_type",
        collection,
    ]
    if list(payload) != expected_keys:
        failures.append(
            f"{registry_type} registry keys must be {expected_keys}"
        )
    if payload.get("schema_version") != "1.0":
        failures.append(
            f"{registry_type} schema_version must be 1.0"
        )
    if payload.get("registry_type") != registry_type:
        failures.append(
            f"{registry_type} registry_type mismatch"
        )
    if payload.get(collection) != []:
        failures.append(
            f"{registry_type} registry must begin empty"
        )
    return failures


def mutation_tests(policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases: list[tuple[str, dict[str, Any]]] = []

    overwrite = copy.deepcopy(policy)
    overwrite["prediction_policy"][
        "overwrite_previous_predictions"
    ] = True
    cases.append(("prediction overwrite enabled", overwrite))

    no_push = copy.deepcopy(policy)
    no_push["branch_policy"][
        "push_after_each_cohesive_commit"
    ] = False
    cases.append(("frequent push disabled", no_push))

    composite = copy.deepcopy(policy)
    composite["metric_policy"][
        "allow_composite_score_before_baseline"
    ] = True
    cases.append(
        ("premature composite score enabled", composite)
    )

    missing_plane = copy.deepcopy(policy)
    missing_plane["required_feedback_planes"].remove(
        "learning"
    )
    cases.append(("learning plane removed", missing_plane))

    for label, candidate in cases:
        if not validate_policy(candidate):
            failures.append(
                f"negative test accepted {label}"
            )
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        policy = load_json(POLICY_PATH)
        failures.extend(validate_policy(policy))

        for _, (
            path,
            registry_type,
            collection,
        ) in REGISTRIES.items():
            failures.extend(
                validate_registry(
                    load_json(path),
                    registry_type=registry_type,
                    collection=collection,
                )
            )

        failures.extend(mutation_tests(policy))
    except (OSError, ValueError, TypeError) as error:
        failures.append(str(error))

    if failures:
        print(
            "Kalaxy3 SAGE continuous-improvement "
            "guardrail: FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical continuous-improvement policy")
    print("PASS four-plane feedback contract")
    print("PASS immutable versioned prediction policy")
    print(
        "PASS multidimensional sizing and confidence policy"
    )
    print(
        "PASS cost, observability, and process-metric policy"
    )
    print(
        "PASS frequent cohesive feature-branch push policy"
    )
    print(
        "PASS empty canonical candidate, lesson, "
        "and action registries"
    )
    print(
        "PASS continuous-improvement policy mutation "
        "negative tests"
    )
    print(
        "Kalaxy3 SAGE continuous-improvement guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
