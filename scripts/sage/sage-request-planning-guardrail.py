#!/usr/bin/env python3
"""Enforce repository-owned SAGE request planning ahead of execution."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts/sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import GitSafetyGuardrail

WORKFLOW_PATH = "scripts/sage/workflows/request_planning.py"
DOMAIN_PATH = "scripts/sage/request_planning.py"
CLI_PATH = "scripts/sage/sage-request-plan.py"
GUARDRAIL_PATH = "scripts/sage/sage-request-planning-guardrail.py"
PROCESS_PATH = (
    "markdown/standards/kalaxy3-sage-request-planning-process.md"
)
SCHEMA_PATH = (
    "markdown/standards/"
    "sage-request-planning-source-schema-v1.0.json"
)
EXECUTION_PROCESS_PATH = (
    "markdown/standards/kalaxy3-sage-request-execution-process.md"
)
REQUIRED_PATHS = {
    WORKFLOW_PATH,
    DOMAIN_PATH,
    CLI_PATH,
    GUARDRAIL_PATH,
    PROCESS_PATH,
    SCHEMA_PATH,
}
REQUIRED_TERMS = {
    "request planning",
    "request planner",
    "planning composition",
    "sage request plan",
}
PROCESS_MARKERS = (
    "source-only package",
    "literal request",
    "repository authority",
    "workflow-primitives",
    "component.select",
    "capability.gap",
    "external callers",
    "request execution",
    "no Git mutation",
    "no GitHub mutation",
    "no deployment mutation",
)
WORKFLOW_MARKERS = (
    "EXECUTION_PRIMITIVES",
    "derive_component_plan",
    "ComponentSelector",
    "CapabilityGapRecorder",
    "SageDiscovery",
    "GitInspector",
    "write_proposal_package",
    "CloseoutWriter",
    "external_candidate_semantics",
)


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path}: expected JSON object")
    return value


def authority_failures() -> list[str]:
    payload = load_object(ROOT / "sage-change-authority.json")
    contexts = {
        item.get("id"): item
        for item in payload.get("contexts", [])
        if isinstance(item, dict)
    }
    failures: list[str] = []
    workflow = contexts.get("workflow-primitives")
    if not isinstance(workflow, dict):
        return ["workflow-primitives authority context is missing"]
    missing_terms = sorted(
        REQUIRED_TERMS - set(workflow.get("match_terms", []))
    )
    if missing_terms:
        failures.append(
            "workflow-primitives request-planning match terms missing "
            f"{missing_terms}"
        )
    for context_id in ("repository-governance", "workflow-primitives"):
        context = contexts.get(context_id)
        if not isinstance(context, dict):
            failures.append(
                f"{context_id} authority context is missing"
            )
            continue
        missing = sorted(
            REQUIRED_PATHS
            - set(context.get("authoritative_files", []))
        )
        if missing:
            failures.append(
                f"{context_id} request-planning authorities missing "
                f"{missing}"
            )
    return failures


def makefile_failures() -> list[str]:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    markers = (
        "sage-request-plan:",
        "sage-request-plan-self-test:",
        "sage-request-planning-guardrail:",
        (
            'SAGE_REQUEST="<request>" SAGE_SOURCE="<source.zip>" '
            "make sage-request-plan"
        ),
        (
            'scripts/sage/sage-request-plan.py --request "$$SAGE_REQUEST" '
            '--source "$$SAGE_SOURCE"'
        ),
    )
    failures = [
        f"Makefile request-planning marker missing: {item}"
        for item in markers
        if item not in text
    ]
    self_headers = [
        line
        for line in text.splitlines()
        if line.startswith("sage-self-test:")
    ]
    if (
        len(self_headers) != 1
        or "sage-request-plan-self-test" not in self_headers[0]
    ):
        failures.append(
            "sage-self-test lacks request-planning self-test"
        )
    normalized = " ".join(text.split())
    if "sage-request-planning-guardrail" not in normalized.partition(
        "sage-guardrails:"
    )[2]:
        failures.append(
            "sage-guardrails lacks request-planning guardrail"
        )
    return failures


def source_failures() -> list[str]:
    workflow = (ROOT / WORKFLOW_PATH).read_text(encoding="utf-8")
    failures = [
        f"request-planning workflow marker missing: {item}"
        for item in WORKFLOW_MARKERS
        if item not in workflow
    ]
    if "subprocess" in workflow:
        failures.append(
            "request-planning workflow imports or references subprocess"
        )
    paths = tuple(
        ROOT / item
        for item in (
            WORKFLOW_PATH,
            DOMAIN_PATH,
            CLI_PATH,
            GUARDRAIL_PATH,
        )
    )
    failures.extend(
        violation.render()
        for violation in GitSafetyGuardrail.scan_paths(paths)
    )
    return failures


def schema_failures() -> list[str]:
    schema = load_object(ROOT / SCHEMA_PATH)
    required = {
        "schema_version",
        "request_sha256",
        "repository",
        "source_files",
        "generated_paths",
        "reconcile_evidence_index",
        "evidence_references",
        "validation_commands",
        "operator_plan",
    }
    failures = []
    if schema.get("$id") != SCHEMA_PATH:
        failures.append(
            "request-planning source schema identifier mismatch"
        )
    if set(schema.get("required", [])) != required:
        failures.append(
            "request-planning source schema required fields mismatch"
        )
    return failures


def process_failures() -> list[str]:
    text = " ".join(
        (ROOT / PROCESS_PATH).read_text(encoding="utf-8").split()
    ).casefold()
    failures = [
        f"request-planning process marker missing: {item}"
        for item in PROCESS_MARKERS
        if item.casefold() not in text
    ]
    execution = " ".join(
        (ROOT / EXECUTION_PROCESS_PATH)
        .read_text(encoding="utf-8")
        .split()
    ).casefold()
    if (
        "sage-request-plan".casefold() not in execution
        or "caller-authored capabilities and candidates".casefold()
        not in execution
    ):
        failures.append(
            "request-execution process does not require "
            "canonical request planning"
        )
    return failures


def runtime_self_test() -> list[str]:
    path = ROOT / CLI_PATH
    spec = importlib.util.spec_from_file_location(
        "sage_request_plan_guardrail",
        path,
    )
    if spec is None or spec.loader is None:
        return ["request-planning CLI cannot be loaded"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        result = module.self_test(ROOT)
    except Exception as error:
        return [
            f"request-planning runtime self-test failed: {error}"
        ]
    return (
        []
        if result == 0
        else [f"request-planning self-test returned {result}"]
    )


def validate() -> list[str]:
    failures = [
        f"request-planning authority file missing: {item}"
        for item in REQUIRED_PATHS
        if not (ROOT / item).is_file()
    ]
    if failures:
        return failures
    failures.extend(authority_failures())
    failures.extend(makefile_failures())
    failures.extend(source_failures())
    failures.extend(schema_failures())
    failures.extend(process_failures())
    failures.extend(runtime_self_test())
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print(
            "Kalaxy3 SAGE request planning guardrail: FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS literal request and source-only planning interface")
    print("PASS repository-derived capabilities and candidates")
    print("PASS component.select and capability.gap ownership")
    print("PASS existing request-execution proposal interface")
    print("PASS no external candidate-selection semantics")
    print("Kalaxy3 SAGE request planning guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(
            "Kalaxy3 SAGE request planning guardrail: FAIL CLOSED"
        )
        print(f"  - {error}")
        raise SystemExit(2)
