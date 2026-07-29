#!/usr/bin/env python3
"""Validate SAGE candidate lifecycle authority and state."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
CANDIDATE_PATH: Final = ROOT / "sage-change-candidate-registry.json"
LIFECYCLE_PATH: Final = (
    ROOT / "sage-change-candidate-lifecycle-registry.json"
)
SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-change-candidate-lifecycle-schema-v1.0.json"
)
TOOL_PATH: Final = ROOT / "scripts/sage/sage-candidate-lifecycle.py"
FOUNDATION_ID: Final = "SAGE-CHANGE-20260728-001"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "sage_candidate_lifecycle",
        TOOL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load lifecycle tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_schema(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["lifecycle schema must be an object"]
    if payload.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append("lifecycle schema draft changed")
    if payload.get("additionalProperties") is not False:
        failures.append(
            "lifecycle schema must fail unknown properties"
        )
    required = payload.get("required", [])
    properties = payload.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            "lifecycle schema required fields must equal properties"
        )
    if "transition" not in payload.get("$defs", {}):
        failures.append("lifecycle transition contract missing")
    return failures


def validate_foundation(
    candidates: dict[str, Any],
    lifecycles: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    candidate_matches = [
        item
        for item in candidates.get("candidates", [])
        if isinstance(item, dict)
        and item.get("change_id") == FOUNDATION_ID
    ]
    lifecycle_matches = [
        item
        for item in lifecycles.get("lifecycles", [])
        if isinstance(item, dict)
        and item.get("change_id") == FOUNDATION_ID
    ]

    if len(candidate_matches) != 1:
        failures.append(
            "foundational candidate must appear exactly once"
        )
        return failures
    if len(lifecycle_matches) != 1:
        failures.append(
            "foundational lifecycle must appear exactly once"
        )
        return failures

    candidate = candidate_matches[0]
    lifecycle = lifecycle_matches[0]

    if candidate.get("status") != "staged-implementation":
        failures.append(
            "foundational candidate must remain staged"
        )
    if lifecycle.get(
        "current_status"
    ) != "staged-implementation":
        failures.append(
            "foundational lifecycle must remain staged"
        )
    if candidate.get(
        "deployment_gate", {}
    ).get("status") != "closed":
        failures.append(
            "foundational deployment gate must remain closed"
        )
    if len(lifecycle.get("history", [])) != 1:
        failures.append(
            "foundational lifecycle must begin with one event"
        )
    else:
        event = lifecycle["history"][0]
        if event.get("transition_type") != "initial-registration":
            failures.append(
                "foundational first event must be initial-registration"
            )
        if event.get("candidate_commit") != (
            "fbeedfbe827e967bac9530522d44b814bc9b6bd4"
        ):
            failures.append(
                "foundational registration commit changed"
            )
    return failures


def mutation_tests(
    tool: Any,
    policy: dict[str, Any],
    candidates: dict[str, Any],
    lifecycles: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    status_mismatch = copy.deepcopy(lifecycles)
    status_mismatch["lifecycles"][0][
        "current_status"
    ] = "active"
    if not tool.validate_lifecycle_registry(
        status_mismatch,
        candidates,
        policy,
    ):
        failures.append(
            "status-mismatch negative test was accepted"
        )

    sequence_gap = copy.deepcopy(lifecycles)
    sequence_gap["lifecycles"][0]["history"][0][
        "sequence"
    ] = 2
    if not tool.validate_lifecycle_registry(
        sequence_gap,
        candidates,
        policy,
    ):
        failures.append(
            "sequence-gap negative test was accepted"
        )

    duplicate = copy.deepcopy(lifecycles)
    duplicate["lifecycles"].append(
        copy.deepcopy(duplicate["lifecycles"][0])
    )
    if not tool.validate_lifecycle_registry(
        duplicate,
        candidates,
        policy,
    ):
        failures.append(
            "duplicate lifecycle negative test was accepted"
        )

    no_validation = copy.deepcopy(lifecycles)
    no_validation["lifecycles"][0]["history"][0][
        "validation_references"
    ] = []
    if not tool.validate_lifecycle_registry(
        no_validation,
        candidates,
        policy,
    ):
        failures.append(
            "missing validation reference was accepted"
        )

    weakened = copy.deepcopy(schema)
    weakened["additionalProperties"] = True
    if not validate_schema(weakened):
        failures.append(
            "weakened lifecycle schema was accepted"
        )

    altered_policy = copy.deepcopy(policy)
    altered_policy["candidate_lifecycle_policy"][
        "dry_run_default"
    ] = False
    if not tool.validate_policy(altered_policy):
        failures.append(
            "non-dry-run lifecycle policy was accepted"
        )
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        tool = load_tool()
        policy = load_json(POLICY_PATH)
        candidates = load_json(CANDIDATE_PATH)
        lifecycles = load_json(LIFECYCLE_PATH)
        schema = load_json(SCHEMA_PATH)

        failures.extend(tool.validate_policy(policy))
        failures.extend(
            tool.validate_candidate_registry(candidates)
        )
        failures.extend(
            tool.validate_lifecycle_registry(
                lifecycles,
                candidates,
                policy,
            )
        )
        failures.extend(validate_schema(schema))
        failures.extend(
            validate_foundation(candidates, lifecycles)
        )
        failures.extend(
            mutation_tests(
                tool,
                policy,
                candidates,
                lifecycles,
                schema,
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
            "Kalaxy3 SAGE candidate lifecycle guardrail: "
            "FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical candidate lifecycle policy")
    print("PASS candidate and lifecycle status consistency")
    print("PASS append-only contiguous lifecycle history")
    print("PASS foundational staged implementation")
    print("PASS closed deployment gate preserved")
    print("PASS activation prerequisites fail closed")
    print("PASS lifecycle policy mutation negative tests")
    print(
        "Kalaxy3 SAGE candidate lifecycle guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
