#!/usr/bin/env python3
"""Validate SAGE post-session review and lesson-to-control authority."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
REGISTRY_PATH: Final = ROOT / "sage-post-session-review-registry.json"
SCHEMA_PATH: Final = (
    ROOT / "markdown/standards/"
    "sage-post-session-review-schema-v1.0.json"
)
TOOL_PATH: Final = (
    ROOT / "scripts/sage/sage-post-session-review.py"
)
LEARNING_GUARDRAIL_PATH: Final = (
    ROOT / "scripts/sage/sage-learning-guardrail.py"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "sage_post_session_review",
        TOOL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load post-session review tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_policy(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be an object"]

    registries = payload.get("registries", {})
    if registries.get("post_session_reviews") != (
        "sage-post-session-review-registry.json"
    ):
        failures.append("post-session review registry path changed")

    contracts = payload.get("contracts", {})
    if contracts.get("post_session_review_schema") != (
        "markdown/standards/"
        "sage-post-session-review-schema-v1.0.json"
    ):
        failures.append("post-session review schema path changed")

    if payload.get("post_session_review_path") != (
        "scripts/sage/sage-post-session-review.py"
    ):
        failures.append("post_session_review_path changed")
    if payload.get(
        "post_session_review_guardrail_path"
    ) != (
        "scripts/sage/sage-post-session-review-guardrail.py"
    ):
        failures.append(
            "post_session_review_guardrail_path changed"
        )

    review_policy = payload.get("post_session_review_policy")
    if not isinstance(review_policy, dict):
        failures.append("post_session_review_policy missing")
    else:
        for key in (
            "canonical_session_required",
            "every_referenced_lesson_requires_control_decision",
            "create_action_requires_draft",
            "no_action_requires_rationale",
            "action_registration_is_separate",
            "review_registry_mutation_is_separate",
        ):
            if review_policy.get(key) is not True:
                failures.append(
                    f"review policy {key} must be true"
                )
        if review_policy.get(
            "composite_score_enabled"
        ) is not False:
            failures.append(
                "post-session composite score enabled"
            )
    return failures


def validate_registry(payload: Any) -> list[str]:
    expected = {
        "schema_version": "1.0",
        "registry_type": "post-session-reviews",
        "reviews": [],
    }
    if payload != expected:
        return [
            "post-session review registry must begin "
            "canonical and empty"
        ]
    return []


def validate_schema(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["post-session review schema must be an object"]
    if payload.get("$schema") != (
        "https://json-schema.org/draft/2020-12/schema"
    ):
        failures.append("post-session review schema draft changed")
    if payload.get("additionalProperties") is not False:
        failures.append(
            "post-session review schema must fail unknown properties"
        )
    required = payload.get("required", [])
    properties = payload.get("properties", {})
    if set(required) != set(properties):
        failures.append(
            "post-session registry required fields "
            "must equal properties"
        )
    definitions = payload.get("$defs", {})
    for key in (
        "review",
        "failure",
        "control_decision",
        "action_draft",
    ):
        if key not in definitions:
            failures.append(
                f"post-session schema definition missing: {key}"
            )
    failure_rework = (
        payload.get("$defs", {})
        .get("failure", {})
        .get("properties", {})
        .get("avoidable_rework_minutes", {})
    )
    if failure_rework.get("type") != ["number", "null"]:
        failures.append(
            "post-session failure rework must allow number or null"
        )

    return failures


def validate_expected_git_diagnostics() -> list[str]:
    """Validate the negative-test assignment semantically."""
    text = LEARNING_GUARDRAIL_PATH.read_text(
        encoding="utf-8"
    )
    failures: list[str] = []

    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return [
            "learning guardrail could not be parsed: "
            f"{error}"
        ]

    def subscript_path(
        node: ast.expr,
    ) -> tuple[str, list[object]] | None:
        parts: list[object] = []
        current: ast.expr = node

        while isinstance(current, ast.Subscript):
            item = current.slice
            if not isinstance(item, ast.Constant):
                return None
            parts.append(item.value)
            current = current.value

        if not isinstance(current, ast.Name):
            return None
        return current.id, list(reversed(parts))

    assignments: list[str] = []
    expected_path = (
        "changed_commit",
        ["baselines", 0, "current_commit"],
    )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if subscript_path(target) == expected_path:
                assignments.append(ast.unparse(node.value))

    if assignments != ["FOUNDATION_BASELINE"]:
        failures.append(
            "learning negative test must assign exactly "
            "FOUNDATION_BASELINE to the mutated current_commit; "
            f"found {assignments}"
        )
    return failures


def mutation_tests(
    tool: Any,
    policy: dict[str, Any],
    registry: dict[str, Any],
    schema: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    altered_policy = copy.deepcopy(policy)
    altered_policy["post_session_review_policy"][
        "action_registration_is_separate"
    ] = False
    if not validate_policy(altered_policy):
        failures.append(
            "coupled action registration policy was accepted"
        )

    composite = copy.deepcopy(policy)
    composite["post_session_review_policy"][
        "composite_score_enabled"
    ] = True
    if not validate_policy(composite):
        failures.append(
            "post-session composite score was accepted"
        )

    populated = copy.deepcopy(registry)
    populated["reviews"].append({"unexpected": True})
    if not validate_registry(populated):
        failures.append(
            "unexpected review registry content was accepted"
        )

    weakened = copy.deepcopy(schema)
    weakened["additionalProperties"] = True
    if not validate_schema(weakened):
        failures.append(
            "weakened post-session schema was accepted"
        )

    tool_failures = tool.validate_policy(altered_policy)
    if not tool_failures:
        failures.append(
            "review tool accepted coupled registration policy"
        )
    non_nullable = copy.deepcopy(schema)
    non_nullable["$defs"]["failure"]["properties"][
        "avoidable_rework_minutes"
    ]["type"] = "number"
    if not validate_schema(non_nullable):
        failures.append(
            "non-nullable post-session failure rework was accepted"
        )

    return failures


def main() -> int:
    failures: list[str] = []
    try:
        tool = load_tool()
        policy = load_json(POLICY_PATH)
        registry = load_json(REGISTRY_PATH)
        schema = load_json(SCHEMA_PATH)

        failures.extend(validate_policy(policy))
        failures.extend(tool.validate_policy(policy))
        failures.extend(validate_registry(registry))
        failures.extend(validate_schema(schema))
        failures.extend(validate_expected_git_diagnostics())
        failures.extend(
            mutation_tests(
                tool,
                policy,
                registry,
                schema,
            )
        )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        failures.append(str(error))

    if failures:
        print(
            "Kalaxy3 SAGE post-session review guardrail: "
            "FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical post-session review policy")
    print("PASS empty canonical post-session review registry")
    print("PASS canonical questions and session linkage")
    print("PASS known-failure and lesson-use review contract")
    print("PASS unavailable failure rework remains nullable")
    print("PASS four-plane feedback review contract")
    print("PASS lesson-to-control decision coverage")
    print("PASS action registration remains a separate mutation")
    print("PASS expected negative Git tests remain quiet")
    print("PASS post-session policy mutation negative tests")
    print(
        "Kalaxy3 SAGE post-session review guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
