#!/usr/bin/env python3
"""Enforce repository-owned SAGE request execution composition."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts/sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    CommandRunner,
    GitInspector,
    GitSafetyGuardrail,
    JsonlEventLogger,
)

WORKFLOW_PATH = "scripts/sage/workflows/request_execution.py"
DOMAIN_PATH = "scripts/sage/request_execution.py"
CLI_PATH = "scripts/sage/sage-request-execute.py"
GUARDRAIL_PATH = "scripts/sage/sage-request-execution-guardrail.py"
ROUTINE_CONTROLLER_PATH = "scripts/sage/workflows/routine_git_lifecycle.py"
ROUTINE_CLI_PATH = "scripts/sage/sage-routine-git-lifecycle.py"
ROUTINE_OPERATOR_SCHEMA_PATH = "markdown/standards/sage-operator-git-proposal-schema-v1.2.json"
PROCESS_PATH = "markdown/standards/kalaxy3-sage-request-execution-process.md"
SCHEMA_PATH = "markdown/standards/sage-request-execution-proposal-schema-v1.0.json"
REQUIRED_PATHS = {
    WORKFLOW_PATH,
    DOMAIN_PATH,
    CLI_PATH,
    GUARDRAIL_PATH,
    PROCESS_PATH,
    SCHEMA_PATH,
    ROUTINE_CONTROLLER_PATH,
    ROUTINE_CLI_PATH,
    ROUTINE_OPERATOR_SCHEMA_PATH,
}
SHA256_PATTERN = r"^[0-9a-f]{64}$"
GIT_OBJECT_ID_PATTERN = r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
REQUIRED_TERMS = {
    "request execution",
    "request executor",
    "request-to-operator proposal",
    "proposal package",
    "sage request execute",
}
WORKFLOW_MARKERS = (
    "build_pre_mutation_workflow",
    "build_post_operator_workflow",
    "AtomicFileTransaction",
    "validate_python_payloads",
    "sage-python-static-guardrail.py",
    "AuthorityReconciler",
    "ComponentSelector",
    "SageDiscovery(context.repo, context.runner).changed()",
    "capture_python_safety_baseline(context)",
    "introduced_safety_violations",
    "GitSafetyGuardrail.scan_source",
    "OperatorGitProposal.build",
    "OutcomeMetrics.build_report",
    "verify_operator_result_action",
    "outcome_metrics_action",
    "evidence_closeout_action",
    "continue_request",
    "routine-git-lifecycle",
    "validate_routine_git_lifecycle_receipt",
    "continue_request_from_routine_receipt",
    "boundary_result_sha256",
    "base_main_head",
    'argv=("python3", "scripts/sage/sage-index.py", "reconcile")',
    'argv=("python3", "-S", "scripts/sage/sage-failure-retrieval-gate.py"',
    "recover_repository_after_failure",
    "failure_closeout_status",
    "failed-pre-mutation",
    "failed-rollback-unverified",
    "rollback_verified",
)
PROCESS_MARKERS = (
    "untrusted proposal",
    "literal request",
    "authority reconciliation",
    "component selection",
    "capability gap",
    "atomic",
    "rollback",
    "operator proposal",
    "post-operator",
    "metrics.outcome",
    "evidence.closeout",
    "one-approval",
    "routine Git lifecycle",
    "repository-owned controller receipt",
    "caller-authored",
    "stage → commit → push",
    "no Git",
    "no GitHub",
    "no deployment",
    "proposal-bound baseline",
    "newly introduced safety findings",
    "new Python files",
    "rollback is not inferred",
)


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path}: expected a JSON object")
    return value


def authority_failures(authority: dict[str, Any]) -> list[str]:
    """Require request execution to be classified and authoritative."""

    contexts = {
        item.get("id"): item
        for item in authority.get("contexts", [])
        if isinstance(item, dict)
    }
    failures: list[str] = []
    workflow = contexts.get("workflow-primitives")
    if not isinstance(workflow, dict):
        return ["workflow-primitives authority context is missing"]
    missing_terms = sorted(REQUIRED_TERMS - set(workflow.get("match_terms", [])))
    if missing_terms:
        failures.append(f"workflow-primitives match terms missing {missing_terms}")
    for context_id in ("repository-governance", "workflow-primitives"):
        context = contexts.get(context_id)
        if not isinstance(context, dict):
            failures.append(f"{context_id} authority context is missing")
            continue
        missing = sorted(REQUIRED_PATHS - set(context.get("authoritative_files", [])))
        if missing:
            failures.append(f"{context_id} request-execution authorities missing {missing}")
    return failures


def makefile_failures(text: str) -> list[str]:
    """Require the canonical request execution Make entry points."""

    failures: list[str] = []
    markers = (
        "sage-request-execute:",
        "sage-request-continue:",
        "sage-request-execute-self-test:",
        "sage-request-execution-guardrail:",
        'SAGE_REQUEST="<request>" SAGE_PROPOSAL="<proposal.zip>" make sage-request-execute',
        'SAGE_STATE="<state.json>" SAGE_OPERATOR_RESULT="<result.json>" make sage-request-continue',
        'SAGE_STATE="<state.json>" SAGE_ROUTINE_RECEIPT="<receipt.json>" make sage-request-continue-routine',
        'scripts/sage/sage-request-execute.py --request "$$SAGE_REQUEST" --proposal "$$SAGE_PROPOSAL"',
        'scripts/sage/sage-request-execute.py --continue-state "$$SAGE_STATE" --operator-result "$$SAGE_OPERATOR_RESULT"',
        'scripts/sage/sage-request-execute.py --continue-state "$$SAGE_STATE" --routine-receipt "$$SAGE_ROUTINE_RECEIPT"',
    )
    for marker in markers:
        if marker not in text:
            failures.append(f"Makefile request-execution marker missing: {marker}")
    self_headers = [line for line in text.splitlines() if line.startswith("sage-self-test:")]
    if len(self_headers) != 1 or "sage-request-execute-self-test" not in self_headers[0]:
        failures.append("sage-self-test lacks request-execution self-test")
    guardrail_text = " ".join(text.split())
    if "sage-request-execution-guardrail" not in guardrail_text.partition("sage-guardrails:")[2]:
        failures.append("sage-guardrails lacks request-execution guardrail")
    return failures


def source_failures() -> list[str]:
    """Require registered primitives, exact sequence, and helper safety."""

    failures: list[str] = []
    workflow = (ROOT / WORKFLOW_PATH).read_text(encoding="utf-8")
    routine_cli = (ROOT / ROUTINE_CLI_PATH).read_text(encoding="utf-8")
    for marker in WORKFLOW_MARKERS:
        if marker not in workflow:
            failures.append(f"request-execution workflow marker missing: {marker}")
    if "subprocess" in workflow:
        failures.append("request-execution workflow imports or references subprocess")
    if "SAGE request execution failed and rolled back:" in workflow:
        failures.append("request execution still infers rollback success in failure text")
    if '"repository_content_restored": True' in workflow:
        failures.append("request execution still hard-codes repository restoration")
    if "continue_request_from_routine_receipt" not in routine_cli:
        failures.append("routine Git CLI does not consume its repository-owned receipt")
    if "operator-result" in routine_cli or "pasted_output_received" in routine_cli:
        failures.append("routine Git CLI still depends on caller-authored pasted operator results")
    routine_controller = (ROOT / "scripts/sage/workflows/routine_git_lifecycle.py").read_text(encoding="utf-8")
    request_domain = (ROOT / "scripts/sage/request_execution.py").read_text(encoding="utf-8")
    legacy_marker = "already-open legacy schema 1.0 proposal"
    if legacy_marker not in routine_controller or legacy_marker not in request_domain:
        failures.append("bounded already-open routine activation compatibility is missing")
    paths = tuple(ROOT / path for path in (WORKFLOW_PATH, DOMAIN_PATH, CLI_PATH, GUARDRAIL_PATH, ROUTINE_CONTROLLER_PATH, ROUTINE_CLI_PATH))
    violations = GitSafetyGuardrail.scan_paths(paths)
    failures.extend(item.render() for item in violations)
    return failures


def schema_failures(schema: dict[str, Any]) -> list[str]:
    """Require the proposal schema to bind request, scope, and validation."""

    failures: list[str] = []
    if schema.get("$id") != SCHEMA_PATH:
        failures.append("request-execution proposal schema identifier mismatch")
    required = set(schema.get("required", []))
    expected = {
        "schema_version", "request_sha256", "repository", "source_files",
        "generated_paths", "reconcile_evidence_index", "evidence_references",
        "capabilities", "candidates", "new_primitive_required", "validation_commands",
        "operator_plan",
    }
    if required != expected:
        failures.append("request-execution proposal schema required fields mismatch")
    properties = schema.get("properties", {})
    request = properties.get("request_sha256", {}).get("pattern")
    repository = properties.get("repository", {}).get("properties", {})
    head = repository.get("head", {}).get("pattern")
    source = properties.get("source_files", {}).get("items", {})
    source_props = source.get("properties", {})
    source_digest = source_props.get("sha256", {}).get("pattern")
    if request != SHA256_PATTERN or source_digest != SHA256_PATTERN:
        failures.append("SHA-256 proposal fields must remain 64 hex")
    if head != GIT_OBJECT_ID_PATTERN:
        failures.append("repository.head Git object-ID schema mismatch")
    return failures



def routine_operator_schema_failures(schema: dict[str, Any]) -> list[str]:
    """Require the routine command proposal to use repository-owned receipt binding."""

    failures: list[str] = []
    expected_id = "https://kalaxy3.local/sage-operator-git-proposal-schema-v1.2.json"
    if schema.get("$id") != expected_id:
        failures.append("routine operator proposal schema id mismatch")
    properties = schema.get("properties", {})
    if properties.get("schema_version", {}).get("const") != "1.2":
        failures.append("routine operator proposal schema_version must be 1.2")
    if properties.get("boundary", {}).get("const") != "routine-git-lifecycle":
        failures.append("routine operator proposal schema must be routine-git-lifecycle only")
    operator = schema.get("$defs", {}).get("operator", {})
    operator_properties = operator.get("properties", {}) if isinstance(operator, dict) else {}
    if operator_properties.get("pasted_output_required", {}).get("const") is not False:
        failures.append("routine operator proposal must not require pasted output")
    if operator_properties.get("repository_receipt_required", {}).get("const") is not True:
        failures.append("routine operator proposal must require repository receipt")
    return failures

def git_head_contract_failures(schema: dict[str, Any]) -> list[str]:
    """Require the live Git HEAD to satisfy the proposal head schema."""
    properties = schema.get("properties", {})
    repository = properties.get("repository", {}).get("properties", {})
    pattern = repository.get("head", {}).get("pattern")
    with tempfile.TemporaryDirectory(prefix="sage-request-head-") as raw:
        state = Path(raw)
        logger = JsonlEventLogger(
            state / "events.jsonl",
            "sage.request-execution.head-contract",
        )
        runner = CommandRunner(logger, allowed_roots=(ROOT, state))
        head = GitInspector(ROOT, runner).head()
    if not isinstance(pattern, str) or re.fullmatch(pattern, head) is None:
        return [f"live Git HEAD does not satisfy proposal schema: {head}"]
    return []


def process_failures(text: str) -> list[str]:
    """Require the human-readable boundary and responsibility contract."""

    normalized = " ".join(text.split())
    return [
        f"request-execution process marker missing: {marker}"
        for marker in PROCESS_MARKERS
        if marker not in normalized
    ]


def runtime_self_test() -> list[str]:
    """Execute the installed proposal parser's positive and negative paths."""

    path = ROOT / CLI_PATH
    spec = importlib.util.spec_from_file_location("sage_request_execute_guardrail", path)
    if spec is None or spec.loader is None:
        return ["request-execution CLI cannot be loaded"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        result = module.self_test()
    except Exception as error:
        return [f"request-execution runtime self-test failed: {error}"]
    return [] if result == 0 else [f"request-execution self-test returned {result}"]


def validate() -> list[str]:
    """Run the complete repository request-execution guardrail."""

    failures: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            failures.append(f"request-execution authority file missing: {relative}")
    if failures:
        return failures
    failures.extend(authority_failures(load_object(ROOT / "sage-change-authority.json")))
    failures.extend(makefile_failures((ROOT / "Makefile").read_text(encoding="utf-8")))
    failures.extend(source_failures())
    schema = load_object(ROOT / SCHEMA_PATH)
    failures.extend(schema_failures(schema))
    failures.extend(git_head_contract_failures(schema))
    failures.extend(routine_operator_schema_failures(load_object(ROOT / ROUTINE_OPERATOR_SCHEMA_PATH)))
    failures.extend(process_failures((ROOT / PROCESS_PATH).read_text(encoding="utf-8")))
    failures.extend(runtime_self_test())
    return failures


def main() -> int:
    """Fail closed on any request execution integration defect."""

    failures = validate()
    if failures:
        print("Kalaxy3 SAGE request execution guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS request-to-operator operating-contract composition")
    print("PASS untrusted checksum-bound proposal package")
    print("PASS exact authority, component, gap, validation, and safety boundaries")
    print("PASS atomic rollback and one operator Git proposal")
    print("PASS one-approval routine Git lifecycle self-closes from repository-owned receipt with legacy stage/commit/push fallback")
    print("PASS Python payload runtime-name validation precedes repository writes")
    print("PASS mandatory post-operator verification, metrics, closeout, and deterministic continuation")
    print("PASS Make, authority, process, schema, and negative-test integration")
    print("Kalaxy3 SAGE request execution guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE request execution guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
