#!/usr/bin/env python3
"""Validate SAGE continuous-improvement policy, schemas, and registries."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
CANDIDATE_SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-change-candidate-schema-v1.0.json"
)
SESSION_SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-session-improvement-schema-v1.0.json"
)
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
REQUIRED_SIZING_DIMENSIONS: Final = [
    "implementation_effort",
    "elapsed_duration",
    "technical_uncertainty",
    "operational_risk",
    "blast_radius",
    "validation_burden",
    "cost_exposure",
    "dependency_complexity",
]
CHANGE_ID_RE: Final = re.compile(
    r"^SAGE-CHANGE-[0-9]{8}-[0-9]{3}$"
)
SESSION_ID_RE: Final = re.compile(
    r"^SAGE-SESSION-[0-9]{8}-[0-9]{3}$"
)
SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")

FOUNDATION_CHANGE_ID: Final = "SAGE-CHANGE-20260728-001"
FOUNDATION_REQUEST: Final = (
    "agreed, make it so, but remember frequent pushes "
    "to a feature branch is good practice"
)
FOUNDATION_BASELINE_SHA: Final = (
    "20c06b2c1c6d3a5af5cc392d95f6743bd4ab8d82"
)


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

    contracts = payload.get("contracts")
    if not isinstance(contracts, dict):
        failures.append("contracts must be an object")
    else:
        if contracts.get("status") != "implemented":
            failures.append(
                "contract status must be implemented"
            )
        for key, expected in (
            (
                "change_candidate_schema",
                CANDIDATE_SCHEMA_PATH,
            ),
            (
                "session_improvement_schema",
                SESSION_SCHEMA_PATH,
            ),
        ):
            relative = contracts.get(key)
            if not isinstance(relative, str):
                failures.append(f"contract path missing: {key}")
            elif ROOT / relative != expected:
                failures.append(
                    f"contract path mismatch: {key}"
                )
            elif not expected.is_file():
                failures.append(
                    f"contract file missing: {expected}"
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


def validate_registry_header(
    payload: Any,
    *,
    registry_type: str,
    collection: str,
) -> list[str]:
    """Validate fields shared by all registries."""
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
    if not isinstance(payload.get(collection), list):
        failures.append(
            f"{registry_type} {collection} must be a list"
        )
    return failures


def validate_empty_registry(
    payload: Any,
    *,
    registry_type: str,
    collection: str,
) -> list[str]:
    """Validate a registry that has not yet been populated."""
    failures = validate_registry_header(
        payload,
        registry_type=registry_type,
        collection=collection,
    )
    if isinstance(payload, dict) and payload.get(collection) != []:
        failures.append(
            f"{registry_type} registry must remain empty"
        )
    return failures


def validate_candidate_registry(
    payload: Any,
    policy: dict[str, Any],
) -> list[str]:
    """Validate the canonical change-candidate registry."""
    failures = validate_registry_header(
        payload,
        registry_type="change-candidates",
        collection="candidates",
    )
    if not isinstance(payload, dict):
        return failures

    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return failures
    if not candidates:
        failures.append(
            "change-candidates registry must include "
            "the foundational candidate"
        )
        return failures

    identifiers = [
        str(item.get("change_id", ""))
        for item in candidates
        if isinstance(item, dict)
    ]
    if len(identifiers) != len(set(identifiers)):
        failures.append(
            "change-candidate identifiers must be unique"
        )

    for candidate in candidates:
        failures.extend(
            validate_candidate_instance(candidate, policy)
        )

    foundation = [
        item
        for item in candidates
        if isinstance(item, dict)
        and item.get("change_id") == FOUNDATION_CHANGE_ID
    ]
    if len(foundation) != 1:
        failures.append(
            "foundational change candidate must appear exactly once"
        )
        return failures

    item = foundation[0]
    if item.get("request") != FOUNDATION_REQUEST:
        failures.append(
            "foundational candidate request must remain literal"
        )
    if item.get("baseline_commit") != FOUNDATION_BASELINE_SHA:
        failures.append(
            "foundational candidate baseline commit changed"
        )
    if item.get("branch") != (
        "feature/sage-continuous-improvement"
    ):
        failures.append(
            "foundational candidate branch changed"
        )
    if item.get("status") != "staged-implementation":
        failures.append(
            "foundational candidate must remain staged "
            "until explicit lifecycle advancement"
        )
    if item.get("deployment_gate", {}).get(
        "status"
    ) != "closed":
        failures.append(
            "foundational candidate deployment gate must be closed"
        )

    predictions = item.get("predictions", [])
    discovery_v1 = [
        prediction
        for prediction in predictions
        if isinstance(prediction, dict)
        and prediction.get("stage") == "discovery"
        and prediction.get("version") == 1
    ]
    if len(discovery_v1) != 1:
        failures.append(
            "foundational discovery prediction v1 "
            "must appear exactly once"
        )
    return failures

def validate_candidate_schema(
    schema: Any,
    policy: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(schema, dict):
        return ["candidate schema must be an object"]

    if schema.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append(
            "candidate schema must use draft 2020-12"
        )
    if schema.get("type") != "object":
        failures.append("candidate schema type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(
            "candidate schema must fail unknown properties"
        )

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            "candidate required fields must equal top-level properties"
        )

    if properties.get("status", {}).get("enum") != policy.get(
        "candidate_statuses"
    ):
        failures.append(
            "candidate status enum must match policy"
        )

    defs = schema.get("$defs", {})
    prediction = defs.get("prediction", {})
    if prediction.get("properties", {}).get(
        "stage", {}
    ).get("enum") != policy.get("prediction_stages"):
        failures.append(
            "candidate prediction stages must match policy"
        )

    sizing = defs.get("sizing", {})
    sizing_properties = sizing.get("properties", {})
    if sizing_properties.get("overall", {}).get(
        "enum"
    ) != list(policy.get("tshirt_sizes", {})):
        failures.append(
            "candidate size enum must match policy"
        )
    dimensions = sizing_properties.get(
        "dimensions", {}
    ).get("required")
    if dimensions != policy.get("required_sizing_dimensions"):
        failures.append(
            "candidate sizing dimensions must match policy"
        )
    if sizing_properties.get("confidence", {}).get(
        "properties", {}
    ).get("rating", {}).get("enum") != list(
        policy.get("confidence_ratings", {})
    ):
        failures.append(
            "candidate confidence enum must match policy"
        )
    return failures


def validate_session_schema(
    schema: Any,
    policy: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(schema, dict):
        return ["session schema must be an object"]

    if schema.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append(
            "session schema must use draft 2020-12"
        )
    if schema.get("type") != "object":
        failures.append("session schema type must be object")
    if schema.get("additionalProperties") is not False:
        failures.append(
            "session schema must fail unknown properties"
        )

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            "session required fields must equal top-level properties"
        )

    feedback = properties.get("feedback_planes", {})
    if feedback.get("required") != policy.get(
        "required_feedback_planes"
    ):
        failures.append(
            "session feedback planes must match policy"
        )

    evaluation = schema.get("$defs", {}).get(
        "prediction_evaluation", {}
    )
    evaluation_properties = evaluation.get("properties", {})
    if evaluation_properties.get(
        "prediction_stage", {}
    ).get("enum") != policy.get("prediction_stages"):
        failures.append(
            "session prediction stages must match policy"
        )
    if evaluation_properties.get(
        "error_classifications", {}
    ).get("items", {}).get("enum") != policy.get(
        "prediction_error_classifications"
    ):
        failures.append(
            "prediction error classes must match policy"
        )
    return failures


def validate_candidate_instance(
    item: Any,
    policy: dict[str, Any],
) -> list[str]:
    """Validate one change-candidate instance."""
    failures: list[str] = []
    if not isinstance(item, dict):
        return ["candidate instance must be an object"]

    required_fields = {
        "schema_version",
        "change_id",
        "title",
        "request",
        "status",
        "branch",
        "baseline_commit",
        "contexts",
        "dependencies",
        "predictions",
        "sizing",
        "expected_value",
        "cost",
        "observability",
        "implementation_outline",
        "validation_plan",
        "deployment_gate",
        "revalidation",
    }
    if set(item) != required_fields:
        failures.append(
            "candidate top-level fields must match the schema"
        )

    if item.get("schema_version") != "1.0":
        failures.append("candidate schema_version invalid")
    if not CHANGE_ID_RE.fullmatch(
        str(item.get("change_id", ""))
    ):
        failures.append("candidate change_id invalid")
    if not isinstance(item.get("title"), str) or not item.get(
        "title"
    ):
        failures.append("candidate title required")
    if not isinstance(item.get("request"), str) or not item.get(
        "request"
    ):
        failures.append("candidate request required")
    if item.get("status") not in policy["candidate_statuses"]:
        failures.append("candidate status invalid")

    branch = str(item.get("branch", ""))
    if not any(
        branch.startswith(prefix)
        for prefix in policy["branch_policy"][
            "allowed_candidate_branch_prefixes"
        ]
    ):
        failures.append("candidate branch prefix invalid")
    if not SHA_RE.fullmatch(
        str(item.get("baseline_commit", ""))
    ):
        failures.append("candidate baseline_commit invalid")

    contexts = item.get("contexts")
    if (
        not isinstance(contexts, list)
        or not contexts
        or len(contexts) != len(set(contexts))
        or not all(
            isinstance(value, str) and value
            for value in contexts
        )
    ):
        failures.append("candidate contexts invalid")

    dependencies = item.get("dependencies")
    if not isinstance(dependencies, list):
        failures.append("candidate dependencies invalid")
    elif (
        len(dependencies) != len(set(dependencies))
        or not all(
            CHANGE_ID_RE.fullmatch(str(value))
            for value in dependencies
        )
    ):
        failures.append("candidate dependencies invalid")

    predictions = item.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        failures.append("candidate predictions required")
    else:
        prediction_keys = {
            "stage",
            "version",
            "recorded_at",
            "estimate",
            "range",
            "confidence",
            "confidence_basis",
            "assumptions",
            "known_unknowns",
            "failure_conditions",
        }
        versions: set[tuple[str, int]] = set()
        stages: set[str] = set()

        for prediction in predictions:
            if not isinstance(prediction, dict):
                failures.append(
                    "candidate prediction must be an object"
                )
                continue
            if set(prediction) != prediction_keys:
                failures.append(
                    "candidate prediction fields invalid"
                )

            stage = prediction.get("stage")
            version = prediction.get("version")
            if stage not in policy["prediction_stages"]:
                failures.append(
                    "candidate prediction stage invalid"
                )
            else:
                stages.add(str(stage))

            if (
                not isinstance(version, int)
                or isinstance(version, bool)
                or version < 1
            ):
                failures.append(
                    "candidate prediction version invalid"
                )
            elif isinstance(stage, str):
                key = (stage, version)
                if key in versions:
                    failures.append(
                        "candidate prediction versions "
                        "must be unique per stage"
                    )
                versions.add(key)

            if not isinstance(
                prediction.get("recorded_at"), str
            ) or not prediction.get("recorded_at"):
                failures.append(
                    "candidate prediction recorded_at required"
                )
            for key in ("estimate", "range"):
                value = prediction.get(key)
                if not isinstance(value, dict) or not value:
                    failures.append(
                        f"candidate prediction {key} invalid"
                    )
            if prediction.get("confidence") not in policy[
                "confidence_ratings"
            ]:
                failures.append(
                    "candidate prediction confidence invalid"
                )
            basis = prediction.get("confidence_basis")
            if (
                not isinstance(basis, list)
                or not basis
                or not all(
                    isinstance(value, str) and value
                    for value in basis
                )
            ):
                failures.append(
                    "candidate prediction confidence basis invalid"
                )
            for key in (
                "assumptions",
                "known_unknowns",
                "failure_conditions",
            ):
                value = prediction.get(key)
                if not isinstance(value, list) or not all(
                    isinstance(entry, str)
                    for entry in value
                ):
                    failures.append(
                        f"candidate prediction {key} invalid"
                    )

        if "discovery" not in stages:
            failures.append(
                "candidate requires a discovery prediction"
            )

    sizing = item.get("sizing")
    if not isinstance(sizing, dict):
        failures.append("candidate sizing invalid")
    else:
        if set(sizing) != {
            "overall",
            "dimensions",
            "confidence",
        }:
            failures.append(
                "candidate sizing fields invalid"
            )
        if sizing.get("overall") not in policy["tshirt_sizes"]:
            failures.append("candidate overall size invalid")

        dimensions = sizing.get("dimensions")
        if not isinstance(dimensions, dict):
            failures.append(
                "candidate sizing dimensions invalid"
            )
        elif list(dimensions) != policy[
            "required_sizing_dimensions"
        ]:
            failures.append(
                "candidate sizing dimensions invalid"
            )
        elif not all(
            value in policy["tshirt_sizes"]
            for value in dimensions.values()
        ):
            failures.append(
                "candidate sizing dimension value invalid"
            )

        confidence = sizing.get("confidence")
        if not isinstance(confidence, dict):
            failures.append(
                "candidate sizing confidence invalid"
            )
        elif set(confidence) != {"rating", "basis"}:
            failures.append(
                "candidate sizing confidence fields invalid"
            )
        else:
            if confidence.get("rating") not in policy[
                "confidence_ratings"
            ]:
                failures.append(
                    "candidate sizing confidence invalid"
                )
            basis = confidence.get("basis")
            if (
                not isinstance(basis, list)
                or not basis
                or not all(
                    isinstance(value, str) and value
                    for value in basis
                )
            ):
                failures.append(
                    "candidate sizing confidence basis invalid"
                )

    expected_value = item.get("expected_value")
    expected_levels = {
        "none",
        "low",
        "medium",
        "high",
        "very-high",
    }
    if not isinstance(expected_value, dict):
        failures.append("candidate expected_value invalid")
    elif list(expected_value) != policy[
        "required_feedback_planes"
    ]:
        failures.append(
            "candidate expected_value planes invalid"
        )
    elif not all(
        value in expected_levels
        for value in expected_value.values()
    ):
        failures.append(
            "candidate expected_value rating invalid"
        )

    cost = item.get("cost")
    required_cost = {
        "baseline_references",
        "one_time_change_cost",
        "recurring_run_rate_delta",
        "unit_economics",
        "avoidable_rework_cost",
        "measurement_provenance",
        "confidence",
    }
    if not isinstance(cost, dict) or set(cost) != required_cost:
        failures.append("candidate cost fields invalid")
    else:
        if not isinstance(
            cost.get("baseline_references"), list
        ):
            failures.append(
                "candidate cost baseline references invalid"
            )
        for key in (
            "one_time_change_cost",
            "recurring_run_rate_delta",
            "unit_economics",
            "avoidable_rework_cost",
        ):
            if not isinstance(cost.get(key), dict):
                failures.append(
                    f"candidate cost {key} invalid"
                )
        provenance = cost.get("measurement_provenance")
        if (
            not isinstance(provenance, list)
            or not provenance
            or not all(
                isinstance(value, str) and value
                for value in provenance
            )
        ):
            failures.append(
                "candidate cost measurement provenance invalid"
            )
        if cost.get("confidence") not in policy[
            "confidence_ratings"
        ]:
            failures.append(
                "candidate cost confidence invalid"
            )

    observability = item.get("observability")
    required_observability = {
        "baseline_references",
        "signals",
        "observation_windows",
    }
    if (
        not isinstance(observability, dict)
        or set(observability) != required_observability
    ):
        failures.append(
            "candidate observability fields invalid"
        )
    else:
        if not isinstance(
            observability.get("baseline_references"), list
        ):
            failures.append(
                "candidate observability baseline references invalid"
            )
        signals = observability.get("signals")
        if (
            not isinstance(signals, list)
            or not signals
            or not all(
                isinstance(value, str) and value
                for value in signals
            )
        ):
            failures.append(
                "candidate observability signals invalid"
            )
        windows = observability.get("observation_windows")
        if (
            not isinstance(windows, list)
            or not windows
            or len(windows) != len(set(windows))
            or not all(
                value
                in policy["required_observability_windows"]
                for value in windows
            )
        ):
            failures.append(
                "candidate observability windows invalid"
            )

    for key in (
        "implementation_outline",
        "validation_plan",
    ):
        value = item.get(key)
        if (
            not isinstance(value, list)
            or not value
            or not all(
                isinstance(entry, str) and entry
                for entry in value
            )
        ):
            failures.append(f"candidate {key} invalid")

    gate = item.get("deployment_gate")
    if not isinstance(gate, dict):
        failures.append("candidate deployment gate invalid")
    elif set(gate) != {"status", "reason"}:
        failures.append(
            "candidate deployment gate fields invalid"
        )
    else:
        if gate.get("status") not in ("closed", "open"):
            failures.append(
                "candidate deployment gate invalid"
            )
        if not isinstance(gate.get("reason"), str) or not gate.get(
            "reason"
        ):
            failures.append(
                "candidate deployment gate reason required"
            )
        if item.get("status") == "active" and gate.get(
            "status"
        ) != "open":
            failures.append(
                "active candidate requires open deployment gate"
            )
        if item.get("status") == "staged-implementation" and gate.get(
            "status"
        ) != "closed":
            failures.append(
                "staged implementation requires closed deployment gate"
            )

    revalidation = item.get("revalidation")
    if not isinstance(revalidation, dict):
        failures.append("candidate revalidation invalid")
    elif set(revalidation) != {"valid_until", "triggers"}:
        failures.append(
            "candidate revalidation fields invalid"
        )
    else:
        if not isinstance(
            revalidation.get("valid_until"), str
        ) or not revalidation.get("valid_until"):
            failures.append(
                "candidate revalidation date required"
            )
        triggers = revalidation.get("triggers")
        if (
            not isinstance(triggers, list)
            or not triggers
            or not all(
                isinstance(value, str) and value
                for value in triggers
            )
        ):
            failures.append(
                "candidate revalidation triggers invalid"
            )

    return failures

def validate_session_instance(
    item: Any,
    policy: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not isinstance(item, dict):
        return ["session instance must be an object"]

    if not SESSION_ID_RE.fullmatch(
        str(item.get("session_id", ""))
    ):
        failures.append("session_id invalid")
    if not CHANGE_ID_RE.fullmatch(
        str(item.get("change_id", ""))
    ):
        failures.append("session change_id invalid")
    if not SHA_RE.fullmatch(
        str(item.get("implementation_commit", ""))
    ):
        failures.append("session implementation_commit invalid")
    if not item.get("evidence_ids"):
        failures.append("session evidence_ids required")

    feedback = item.get("feedback_planes", {})
    if list(feedback) != policy["required_feedback_planes"]:
        failures.append("session feedback planes invalid")

    for evaluation in item.get(
        "prediction_evaluations", []
    ):
        if evaluation.get("prediction_stage") not in policy[
            "prediction_stages"
        ]:
            failures.append(
                "session prediction stage invalid"
            )
        for classification in evaluation.get(
            "error_classifications", []
        ):
            if classification not in policy[
                "prediction_error_classifications"
            ]:
                failures.append(
                    "session prediction error class invalid"
                )
    return failures


def representative_candidate() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "change_id": "SAGE-CHANGE-20260728-001",
        "title": "Continuous-improvement foundation",
        "request": "Create the SAGE continuous-improvement foundation.",
        "status": "staged-implementation",
        "branch": "feature/sage-continuous-improvement",
        "baseline_commit": "0" * 40,
        "contexts": [
            "repository-governance",
            "evidence",
            "continuous-improvement",
        ],
        "dependencies": [],
        "predictions": [
            {
                "stage": "discovery",
                "version": 1,
                "recorded_at": "2026-07-28T21:20:00-05:00",
                "estimate": {"active_hours": 48},
                "range": {
                    "active_hours_min": 32,
                    "active_hours_max": 80,
                },
                "confidence": "medium",
                "confidence_basis": ["Existing SAGE patterns exist."],
                "assumptions": [],
                "known_unknowns": [],
                "failure_conditions": [],
            }
        ],
        "sizing": {
            "overall": "L",
            "dimensions": {
                "implementation_effort": "L",
                "elapsed_duration": "M",
                "technical_uncertainty": "L",
                "operational_risk": "S",
                "blast_radius": "M",
                "validation_burden": "L",
                "cost_exposure": "S",
                "dependency_complexity": "L",
            },
            "confidence": {
                "rating": "medium",
                "basis": ["The governance surface is known."],
            },
        },
        "expected_value": {
            "delivery": "high",
            "operations": "high",
            "economics": "high",
            "learning": "very-high",
        },
        "cost": {
            "baseline_references": [],
            "one_time_change_cost": {},
            "recurring_run_rate_delta": {},
            "unit_economics": {},
            "avoidable_rework_cost": {},
            "measurement_provenance": ["initial estimate"],
            "confidence": "medium",
        },
        "observability": {
            "baseline_references": [],
            "signals": ["guardrail pass rate"],
            "observation_windows": ["baseline", "trend"],
        },
        "implementation_outline": ["Build the staged foundation."],
        "validation_plan": ["Run SAGE guardrails."],
        "deployment_gate": {
            "status": "closed",
            "reason": "Staged implementation.",
        },
        "revalidation": {
            "valid_until": "2026-08-27",
            "triggers": ["origin/main advances"],
        },
    }


def representative_session() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "session_id": "SAGE-SESSION-20260728-001",
        "change_id": "SAGE-CHANGE-20260728-001",
        "candidate_prediction_versions": [
            {"stage": "discovery", "version": 1}
        ],
        "implementation_commit": "0" * 40,
        "evidence_ids": ["SAGE-K3-OBS-20260728-003"],
        "started_at": "2026-07-28T21:20:00-05:00",
        "completed_at": "2026-07-28T22:00:00-05:00",
        "feedback_planes": {
            key: {
                "measurements": [],
                "summary": "Initial controlled measurement.",
            }
            for key in REQUIRED_PLANES
        },
        "prediction_evaluations": [
            {
                "prediction_stage": "discovery",
                "prediction_version": 1,
                "subject": "active engineering hours",
                "predicted": {"min": 32, "max": 80},
                "actual": {"hours": 48},
                "result": "in-range",
                "confidence": "medium",
                "error_classifications": [],
                "explanation": "The actual was inside the range.",
            }
        ],
        "cost_comparison": {
            "before": {},
            "after": {},
            "delta": {},
            "one_time_change_cost": {},
            "avoidable_rework_cost": {},
            "unit_economics": {},
            "provenance": ["session measurement"],
        },
        "observability_comparison": {
            "before": {},
            "after": {},
            "delta": {},
            "observation_windows": ["baseline", "trend"],
            "provenance": ["session measurement"],
        },
        "lessons": [],
        "improvement_actions": [],
        "outcome": {
            "hypothesis_result": "supported",
            "summary": "The staged foundation behaved as expected.",
        },
    }


def mutation_tests(
    policy: dict[str, Any],
    candidate_schema: dict[str, Any],
    session_schema: dict[str, Any],
    candidate_registry: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    policy_cases: list[
        tuple[str, dict[str, Any]]
    ] = []
    overwrite = copy.deepcopy(policy)
    overwrite["prediction_policy"][
        "overwrite_previous_predictions"
    ] = True
    policy_cases.append(
        ("prediction overwrite enabled", overwrite)
    )
    no_push = copy.deepcopy(policy)
    no_push["branch_policy"][
        "push_after_each_cohesive_commit"
    ] = False
    policy_cases.append(("frequent push disabled", no_push))
    composite = copy.deepcopy(policy)
    composite["metric_policy"][
        "allow_composite_score_before_baseline"
    ] = True
    policy_cases.append(
        ("premature composite score enabled", composite)
    )
    missing_plane = copy.deepcopy(policy)
    missing_plane["required_feedback_planes"].remove(
        "learning"
    )
    policy_cases.append(
        ("learning plane removed", missing_plane)
    )

    for label, candidate in policy_cases:
        if not validate_policy(candidate):
            failures.append(
                f"negative test accepted {label}"
            )

    candidate_cases: list[
        tuple[str, dict[str, Any]]
    ] = []
    invalid_status = representative_candidate()
    invalid_status["status"] = "unknown"
    candidate_cases.append(
        ("invalid candidate status", invalid_status)
    )
    missing_dimension = representative_candidate()
    del missing_dimension["sizing"]["dimensions"][
        "dependency_complexity"
    ]
    candidate_cases.append(
        ("missing sizing dimension", missing_dimension)
    )
    active_closed = representative_candidate()
    active_closed["status"] = "active"
    candidate_cases.append(
        ("active candidate with closed gate", active_closed)
    )
    duplicate_prediction = representative_candidate()
    duplicate_prediction["predictions"].append(
        copy.deepcopy(
            duplicate_prediction["predictions"][0]
        )
    )
    candidate_cases.append(
        ("duplicate prediction version", duplicate_prediction)
    )

    for label, candidate in candidate_cases:
        if not validate_candidate_instance(
            candidate, policy
        ):
            failures.append(
                f"candidate negative test accepted {label}"
            )

    registry_cases: list[
        tuple[str, dict[str, Any]]
    ] = []
    empty_registry = copy.deepcopy(candidate_registry)
    empty_registry["candidates"] = []
    registry_cases.append(
        ("empty candidate registry", empty_registry)
    )

    duplicate_id = copy.deepcopy(candidate_registry)
    duplicate_id["candidates"].append(
        copy.deepcopy(duplicate_id["candidates"][0])
    )
    registry_cases.append(
        ("duplicate candidate identifier", duplicate_id)
    )

    altered_request = copy.deepcopy(candidate_registry)
    altered_request["candidates"][0]["request"] = (
        "altered requester language"
    )
    registry_cases.append(
        ("altered foundational request", altered_request)
    )

    opened_staged_gate = copy.deepcopy(candidate_registry)
    opened_staged_gate["candidates"][0][
        "deployment_gate"
    ]["status"] = "open"
    registry_cases.append(
        ("opened staged deployment gate", opened_staged_gate)
    )

    for label, registry in registry_cases:
        if not validate_candidate_registry(
            registry, policy
        ):
            failures.append(
                f"candidate registry negative test accepted {label}"
            )

    session_cases: list[
        tuple[str, dict[str, Any]]
    ] = []
    missing_feedback = representative_session()
    del missing_feedback["feedback_planes"]["learning"]
    session_cases.append(
        ("missing learning feedback", missing_feedback)
    )
    bad_class = representative_session()
    bad_class["prediction_evaluations"][0][
        "error_classifications"
    ] = ["unknown-error"]
    session_cases.append(
        ("unknown prediction error class", bad_class)
    )
    no_evidence = representative_session()
    no_evidence["evidence_ids"] = []
    session_cases.append(
        ("session without evidence", no_evidence)
    )

    for label, session in session_cases:
        if not validate_session_instance(
            session, policy
        ):
            failures.append(
                f"session negative test accepted {label}"
            )

    weakened_candidate_schema = copy.deepcopy(
        candidate_schema
    )
    weakened_candidate_schema["additionalProperties"] = True
    if not validate_candidate_schema(
        weakened_candidate_schema, policy
    ):
        failures.append(
            "candidate schema weakening was accepted"
        )

    weakened_session_schema = copy.deepcopy(
        session_schema
    )
    weakened_session_schema["additionalProperties"] = True
    if not validate_session_schema(
        weakened_session_schema, policy
    ):
        failures.append(
            "session schema weakening was accepted"
        )
    return failures

def main() -> int:
    failures: list[str] = []
    try:
        policy = load_json(POLICY_PATH)
        candidate_schema = load_json(
            CANDIDATE_SCHEMA_PATH
        )
        session_schema = load_json(SESSION_SCHEMA_PATH)
        candidate_registry = load_json(
            REGISTRIES["change_candidates"][0]
        )

        failures.extend(validate_policy(policy))
        failures.extend(
            validate_candidate_schema(
                candidate_schema, policy
            )
        )
        failures.extend(
            validate_session_schema(
                session_schema, policy
            )
        )
        failures.extend(
            validate_candidate_registry(
                candidate_registry, policy
            )
        )

        for key in (
            "lessons",
            "improvement_actions",
        ):
            (
                path,
                registry_type,
                collection,
            ) = REGISTRIES[key]
            failures.extend(
                validate_empty_registry(
                    load_json(path),
                    registry_type=registry_type,
                    collection=collection,
                )
            )

        failures.extend(
            validate_candidate_instance(
                representative_candidate(), policy
            )
        )
        failures.extend(
            validate_session_instance(
                representative_session(), policy
            )
        )
        failures.extend(
            mutation_tests(
                policy,
                candidate_schema,
                session_schema,
                candidate_registry,
            )
        )
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
    print("PASS candidate and session schema contracts")
    print("PASS representative candidate and session records")
    print("PASS foundational change candidate registry")
    print("PASS discovery prediction v1 remains immutable")
    print("PASS multidimensional sizing and confidence policy")
    print("PASS cost, observability, and process-metric policy")
    print("PASS frequent cohesive feature-branch push policy")
    print(
        "PASS empty canonical lesson and action registries"
    )
    print(
        "PASS continuous-improvement mutation negative tests"
    )
    print(
        "Kalaxy3 SAGE continuous-improvement guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
