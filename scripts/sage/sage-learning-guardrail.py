#!/usr/bin/env python3
"""Validate SAGE improvement actions and baseline extraction."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
ACTION_REGISTRY_PATH: Final = ROOT / "sage-improvement-actions.json"
BASELINE_REGISTRY_PATH: Final = (
    ROOT / "sage-continuous-improvement-baseline-registry.json"
)
ACTION_SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-improvement-action-schema-v1.1.json"
)
BASELINE_SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-continuous-improvement-baseline-schema-v1.0.json"
)
ACTION_TOOL_PATH: Final = (
    ROOT / "scripts/sage/sage-improvement-actions.py"
)
BASELINE_TOOL_PATH: Final = (
    ROOT / "scripts/sage/sage-baseline-extract.py"
)
FOUNDATION_ID: Final = "SAGE-CHANGE-20260728-001"
FOUNDATION_BASELINE: Final = (
    "20c06b2c1c6d3a5af5cc392d95f6743bd4ab8d82"
)
FOUNDATION_CURRENT: Final = (
    "55a375c849afa4d59254447b3022a57738df7700"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_policy(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be an object"]

    registries = payload.get("registries", {})
    if registries.get("improvement_baselines") != (
        "sage-continuous-improvement-baseline-registry.json"
    ):
        failures.append(
            "improvement baseline registry path changed"
        )

    contracts = payload.get("contracts", {})
    expected_contracts = {
        "improvement_action_schema": (
            "markdown/standards/"
            "sage-improvement-action-schema-v1.1.json"
        ),
        "continuous_improvement_baseline_schema": (
            "markdown/standards/"
            "sage-continuous-improvement-"
            "baseline-schema-v1.0.json"
        ),
    }
    for key, expected in expected_contracts.items():
        if contracts.get(key) != expected:
            failures.append(f"{key} path changed")

    if payload.get("improvement_action_path") != (
        "scripts/sage/sage-improvement-actions.py"
    ):
        failures.append("improvement_action_path changed")
    if payload.get("baseline_extract_path") != (
        "scripts/sage/sage-baseline-extract.py"
    ):
        failures.append("baseline_extract_path changed")
    if payload.get("learning_guardrail_path") != (
        "scripts/sage/sage-learning-guardrail.py"
    ):
        failures.append("learning_guardrail_path changed")

    lifecycle = payload.get(
        "improvement_action_lifecycle_policy"
    )
    if not isinstance(lifecycle, dict):
        failures.append(
            "improvement action lifecycle policy missing"
        )
    else:
        for key in (
            "history_append_only",
            "dry_run_default",
            "apply_requires_explicit_flag",
            "atomic_write_required",
            "direct_status_edits_forbidden",
            "registration_requires_source",
            "contract_amendment_requires_expected_sha256",
            "contract_amendment_preserves_prior_values",
            "contract_amendment_status_unchanged",
        ):
            if lifecycle.get(key) is not True:
                failures.append(
                    f"action lifecycle {key} must be true"
                )
        if lifecycle.get(
            "contract_amendment_allowed_statuses"
        ) != ["identified"]:
            failures.append(
                "action contract amendments must be identified-only"
            )

    baseline_policy = payload.get(
        "baseline_extraction_policy"
    )
    expected_baseline = {
        "git_metrics_measured": True,
        "registry_metrics_measured": True,
        "session_metrics_null_when_unavailable": True,
        "populated_session_aggregation_fail_closed": True,
        "prediction_reference_required": True,
        "provenance_required": True,
        "composite_score_enabled": False,
        "baseline_commit": FOUNDATION_BASELINE,
        "current_commit": FOUNDATION_CURRENT,
    }
    if baseline_policy != expected_baseline:
        failures.append("baseline extraction policy changed")
    return failures


def validate_schema(
    payload: Any,
    label: str,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return [f"{label} schema must be an object"]
    if payload.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append(f"{label} schema draft changed")
    if payload.get("additionalProperties") is not False:
        failures.append(
            f"{label} schema must fail unknown properties"
        )
    required = payload.get("required", [])
    properties = payload.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            f"{label} required fields must equal properties"
        )
    return failures


def validate_baseline(
    payload: Any,
    baseline_tool: Any,
) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["baseline registry must be an object"]
    if payload.get("schema_version") != "1.0":
        failures.append(
            "baseline registry schema_version must be 1.0"
        )
    if payload.get("registry_type") != (
        "continuous-improvement-baselines"
    ):
        failures.append("baseline registry_type changed")

    baselines = payload.get("baselines")
    if not isinstance(baselines, list) or len(baselines) != 1:
        failures.append(
            "baseline registry must contain one foundation baseline"
        )
        return failures

    record = baselines[0]
    if record.get("change_id") != FOUNDATION_ID:
        failures.append("baseline change_id changed")
    if record.get("baseline_commit") != FOUNDATION_BASELINE:
        failures.append("foundation baseline commit changed")
    if record.get("current_commit") != FOUNDATION_CURRENT:
        failures.append("foundation current commit changed")
    if record.get("composite_score_enabled") is not False:
        failures.append("composite baseline score enabled")

    process = record.get("process_metrics", {})
    if process.get("status") != (
        "unavailable-no-session-records"
    ):
        failures.append(
            "foundation process status must be unavailable"
        )
    if any(
        value is not None
        for value in process.get("raw", {}).values()
    ):
        failures.append(
            "unavailable raw process metrics must be null"
        )
    if any(
        value is not None
        for value in process.get("derived", {}).values()
    ):
        failures.append(
            "unavailable derived process metrics must be null"
        )

    try:
        expected = baseline_tool.extract_baseline(
            baseline_id=record["baseline_id"],
            change_id=record["change_id"],
            captured_at=record["captured_at"],
            branch=record["branch"],
            baseline_commit=record["baseline_commit"],
            current_commit=record["current_commit"],
        )
        if baseline_tool.normalize_for_check(expected) != (
            baseline_tool.normalize_for_check(record)
        ):
            failures.append(
                "baseline differs from deterministic extraction"
            )
    except (
        OSError,
        ValueError,
        TypeError,
    ) as error:
        failures.append(str(error))
    return failures


def mutation_tests(
    action_tool: Any,
    baseline_tool: Any,
    policy: dict[str, Any],
    action_registry: dict[str, Any],
    baseline_registry: dict[str, Any],
    action_schema: dict[str, Any],
    baseline_schema: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    altered_policy = copy.deepcopy(policy)
    altered_policy[
        "improvement_action_lifecycle_policy"
    ]["dry_run_default"] = False
    if not validate_policy(altered_policy):
        failures.append(
            "non-dry-run action policy was accepted"
        )

    broad_amendment = copy.deepcopy(policy)
    broad_amendment[
        "improvement_action_lifecycle_policy"
    ]["contract_amendment_allowed_statuses"] = [
        "identified",
        "accepted",
    ]
    if not validate_policy(broad_amendment):
        failures.append(
            "post-acceptance action amendment policy was accepted"
        )

    composite = copy.deepcopy(policy)
    composite["baseline_extraction_policy"][
        "composite_score_enabled"
    ] = True
    if not validate_policy(composite):
        failures.append(
            "composite baseline policy was accepted"
        )

    unexpected_action = copy.deepcopy(action_registry)
    unexpected_action["actions"].append(
        {"current_status": "closed"}
    )
    if not action_tool.validate_registry(
        unexpected_action,
        policy,
    ):
        failures.append(
            "malformed action was accepted"
        )

    changed_commit = copy.deepcopy(baseline_registry)
    changed_commit["baselines"][0][
        "current_commit"
    ] = FOUNDATION_BASELINE
    if not validate_baseline(
        changed_commit,
        baseline_tool,
    ):
        failures.append(
            "changed baseline commit was accepted"
        )

    nonnull_process = copy.deepcopy(baseline_registry)
    nonnull_process["baselines"][0]["process_metrics"][
        "raw"
    ]["commands_executed"] = 1
    if not validate_baseline(
        nonnull_process,
        baseline_tool,
    ):
        failures.append(
            "non-null unavailable process metric was accepted"
        )

    weakened_action = copy.deepcopy(action_schema)
    weakened_action["additionalProperties"] = True
    if not validate_schema(
        weakened_action,
        "action",
    ):
        failures.append(
            "weakened action schema was accepted"
        )

    weakened_baseline = copy.deepcopy(baseline_schema)
    weakened_baseline["additionalProperties"] = True
    if not validate_schema(
        weakened_baseline,
        "baseline",
    ):
        failures.append(
            "weakened baseline schema was accepted"
        )
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        action_tool = load_module(
            "sage_improvement_actions",
            ACTION_TOOL_PATH,
        )
        baseline_tool = load_module(
            "sage_baseline_extract",
            BASELINE_TOOL_PATH,
        )

        policy = load_json(POLICY_PATH)
        action_registry = load_json(ACTION_REGISTRY_PATH)
        baseline_registry = load_json(
            BASELINE_REGISTRY_PATH
        )
        action_schema = load_json(ACTION_SCHEMA_PATH)
        baseline_schema = load_json(BASELINE_SCHEMA_PATH)

        failures.extend(validate_policy(policy))
        failures.extend(
            action_tool.validate_policy(policy)
        )
        failures.extend(
            action_tool.validate_registry(
                action_registry,
                policy,
            )
        )
        failures.extend(
            validate_schema(
                action_schema,
                "action",
            )
        )
        failures.extend(
            validate_schema(
                baseline_schema,
                "baseline",
            )
        )
        failures.extend(
            validate_baseline(
                baseline_registry,
                baseline_tool,
            )
        )
        failures.extend(
            mutation_tests(
                action_tool,
                baseline_tool,
                policy,
                action_registry,
                baseline_registry,
                action_schema,
                baseline_schema,
            )
        )
    except (
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
    ) as error:
        failures.append(str(error))

    if failures:
        print(
            "Kalaxy3 SAGE learning guardrail: FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical improvement-action lifecycle policy")
    print("PASS evidence-backed action registry")
    print("PASS append-only dry-run action and amendment tooling")
    print("PASS identified-only action contract amendment policy")
    print("PASS deterministic repository baseline extraction")
    print("PASS unavailable process metrics remain null")
    print("PASS prediction and provenance references preserved")
    print("PASS composite baseline scoring remains closed")
    print("PASS learning-policy mutation negative tests")
    print("Kalaxy3 SAGE learning guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
