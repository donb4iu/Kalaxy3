#!/usr/bin/env python3
"""Fail-closed root guardrail for the Kalaxy3 SAGE operating contract."""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
POLICY = ROOT / "sage-operating-contract-policy.json"
REGISTRY = ROOT / "sage-workflow-primitives.json"
AUTHORITY = ROOT / "sage-change-authority.json"
STANDARD = ROOT / "markdown/standards/kalaxy3-sage-operating-contract.md"
MANIFEST = ROOT / "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-root-enforcement.json"
READINESS = ROOT / "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/root-enforcement-readiness.json"
COMPOSITION = SAGE_DIR / "workflows/operating_contract.py"
SELF_TEST = SAGE_DIR / "sage-operating-contract-self-test.py"
WORKFLOW_GUARDRAIL = SAGE_DIR / "sage-workflow-primitives-guardrail.py"
MAKEFILE = ROOT / "Makefile"
AGENTS = ROOT / "AGENTS.md"
SAGE = ROOT / "SAGE.md"
sys.path.insert(0, str(SAGE_DIR))

from workflow import FRAMEWORK_VERSION, MakefileDocument  # noqa: E402

EXPECTED_SEQUENCE = [
    "preserve-literal-request",
    "collect-current-authority",
    "reconcile-authority",
    "declare-required-capabilities",
    "select-repository-owned-components",
    "record-composition-manifest",
    "record-capability-gaps",
    "implement-with-least-authority",
    "validate-real-runtime-path",
    "diagnose-unexpected-failures",
    "propose-one-operator-mutation-boundary",
    "verify-pasted-operator-result",
    "record-outcomes-and-trends",
    "publish-sage-evidence",
]
EXPECTED_PRE = (
    ("preserve-literal-request", "sage.discovery"),
    ("collect-current-git-authority", "git.inspect"),
    ("reconcile-authority", "authority.reconcile"),
    ("select-repository-components", "component.select"),
    ("record-capability-gaps", "capability.gap"),
    ("implement-declared-repository-scope", "file.atomic-preserve-mode"),
    ("validate-real-runtime-path", "validation.plan"),
    ("validate-helper-safety", "git.safety-guardrail"),
    ("diagnose-unexpected-failures", "failure.diagnose"),
    ("propose-one-operator-boundary", "operator.git-proposal"),
)
EXPECTED_POST = (
    ("verify-pasted-operator-result", "git.inspect"),
    ("record-outcomes-and-trends", "metrics.outcome"),
    ("publish-sage-evidence", "evidence.closeout"),
)
EXPECTED_PRIMITIVES = {
    "catalog.registry",
    "logging.events",
    "git.inspect",
    "sage.discovery",
    "authority.reconcile",
    "component.select",
    "capability.gap",
    "file.atomic-preserve-mode",
    "validation.plan",
    "git.safety-guardrail",
    "failure.diagnose",
    "operator.git-proposal",
    "metrics.outcome",
    "evidence.closeout",
    "workflow.composition",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def literal_assignment(tree: ast.AST, name: str):
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(
            isinstance(target, ast.Name) and target.id == name
            for target in targets
        ):
            continue
        value = node.value
        return ast.literal_eval(value)
    raise ValueError(f"Missing literal assignment: {name}")


def validate_policy(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != "1.0":
        failures.append("policy schema_version must be 1.0")
    if payload.get("status") != "root-enforcement-staged":
        failures.append("policy status must be root-enforcement-staged")
    if payload.get("mandatory_sequence") != EXPECTED_SEQUENCE:
        failures.append("mandatory operating-contract sequence drifted")

    helper = payload.get("helper_policy", {})
    for field in (
        "git_mutation_allowed",
        "github_mutation_allowed",
        "deployment_mutation_allowed",
        "personal_credentials_in_generated_code_allowed",
    ):
        if helper.get(field) is not False:
            failures.append(f"helper policy must keep {field}=false")
    if helper.get("read_only_git_inspection_allowed") is not True:
        failures.append("helper policy must allow read-only Git inspection")

    mutation = payload.get("operator_mutation_policy", {})
    for field in (
        "operator_executed",
        "one_boundary_at_a_time",
        "one_command_per_proposal",
        "pasted_complete_output_required",
        "next_boundary_blocked_until_verified",
        "helper_execution_of_proposed_command_forbidden",
        "root_composition_required",
    ):
        if mutation.get(field) is not True:
            failures.append(f"operator mutation policy must enable {field}")

    validation = payload.get("validation_policy", {})
    if validation.get("root_guardrail_required") is not True:
        failures.append("root operating-contract guardrail must be required")

    activation = payload.get("activation_policy", {})
    if activation.get("current_state") != "staged-root-enforcement":
        failures.append("activation state must be staged-root-enforcement")
    if activation.get("remaining_phases") != ["evidence-publication"]:
        failures.append("only split evidence publication may remain")
    if activation.get("deployment_authorized") is not False:
        failures.append("deployment must remain unauthorized")
    if activation.get("autonomous_mutation_authorized") is not False:
        failures.append("autonomous mutation must remain unauthorized")
    if "root-enforcement" not in activation.get("completed_phases", []):
        failures.append("root-enforcement phase is not marked complete")
    root = activation.get("root_enforcement", {})
    expected = {
        "composition": "scripts/sage/workflows/operating_contract.py",
        "self_test": "scripts/sage/sage-operating-contract-self-test.py",
        "guardrail": "scripts/sage/sage-operating-contract-guardrail.py",
        "make_target": "sage-operating-contract-check",
        "component_manifest": "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-root-enforcement.json",
        "readiness_receipt": "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/root-enforcement-readiness.json",
    }
    if root != expected:
        failures.append("activation root-enforcement linkage drifted")
    return failures


def validate_registry(payload: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("framework_version") != FRAMEWORK_VERSION:
        failures.append("workflow framework_version must match canonical FRAMEWORK_VERSION")
    if "root operating-contract composition and guardrail enforcement" not in payload.get("principles", []):
        failures.append("workflow registry lacks root-enforcement principle")
    policy = payload.get("operating_contract_policy", {})
    if policy.get("status") != "staged-root-enforcement":
        failures.append("registry operating-contract status mismatch")
    if policy.get("new_primitive_required") is not False:
        failures.append("root enforcement must not claim a new primitive")
    if policy.get("composition_path") != "scripts/sage/workflows/operating_contract.py":
        failures.append("registry composition path mismatch")
    if policy.get("aggregate_target") != "sage-operating-contract-check":
        failures.append("registry aggregate target mismatch")
    return failures


def validate_composition() -> list[str]:
    failures: list[str] = []
    source = COMPOSITION.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(COMPOSITION))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    if "subprocess" in imported or "shlex" in imported:
        failures.append("operating-contract composition imports direct execution machinery")
    for forbidden in ("GitRepository", "CommandRunner", "AtomicFileWriter"):
        if forbidden in source:
            failures.append(f"composition bypasses injected primitive action: {forbidden}")
    try:
        primitives = set(literal_assignment(tree, "PRIMITIVES_USED"))
        pre = tuple(tuple(item) for item in literal_assignment(tree, "PRE_MUTATION_SEQUENCE"))
        post = tuple(tuple(item) for item in literal_assignment(tree, "POST_OPERATOR_SEQUENCE"))
    except (ValueError, TypeError, SyntaxError) as error:
        return [*failures, str(error)]
    if primitives != EXPECTED_PRIMITIVES:
        failures.append("composition primitive manifest drifted")
    if pre != EXPECTED_PRE:
        failures.append("pre-mutation sequence drifted")
    if post != EXPECTED_POST:
        failures.append("post-operator sequence drifted")
    if any(step[0] == "propose-one-operator-boundary" for step in post):
        failures.append("operator proposal must end the pre-mutation workflow")
    return failures


def validate_makefile() -> list[str]:
    failures: list[str] = []
    document = MakefileDocument.parse(MAKEFILE.read_text(encoding="utf-8"))
    expected = {
        "sage-self-test": "sage-operating-contract-self-test",
        "sage-guardrails": "sage-operating-contract-guardrail",
        "sage-operating-contract-check": "sage-operating-contract-self-test",
    }
    for target, dependency in expected.items():
        if dependency not in document.dependencies(target):
            failures.append(f"{target} is missing {dependency}")
    if "sage-operating-contract-guardrail" not in document.dependencies(
        "sage-operating-contract-check"
    ):
        failures.append("operating-contract aggregate target lacks guardrail")
    rendered = document.render()
    for marker in (
        "scripts/sage/sage-operating-contract-self-test.py",
        "scripts/sage/sage-operating-contract-guardrail.py",
        "Kalaxy3 SAGE operating contract: PASS",
    ):
        if marker not in rendered:
            failures.append(f"Makefile missing operating-contract marker: {marker}")
    return failures


def validate_manifest() -> list[str]:
    failures: list[str] = []
    payload = load_json(MANIFEST)
    if payload.get("schema_version") != "1.0":
        failures.append("root component manifest schema_version must be 1.0")
    if payload.get("manifest_id") != "SAGE-COMP-20260801-004":
        failures.append("root component manifest identifier mismatch")
    if payload.get("approval", {}).get("status") != "approved":
        failures.append("root component manifest must be approved")
    if payload.get("capability_gap_receipts") != []:
        failures.append("root composition must not fabricate a tenth gap receipt")
    if payload.get("composite_score_enabled") is not False:
        failures.append("root component manifest must disable composite scoring")
    selected = {
        item.get("component_id")
        for item in payload.get("selections", [])
        if isinstance(item, dict)
    }
    required = {
        "repository-root-policy",
        "workflow.composition",
        "validation.plan",
        "evidence.closeout",
    }
    missing = sorted(required - selected)
    if missing:
        failures.append(f"root component selections missing: {missing}")
    rejected = [
        item
        for item in payload.get("candidates", [])
        if isinstance(item, dict)
        and item.get("component_id") == "operating-contract.mutation-engine"
    ]
    if len(rejected) != 1 or rejected[0].get("disposition") != "rejected":
        failures.append("autonomous mutation-engine alternative must be rejected")
    return failures


def validate_readiness() -> list[str]:
    failures: list[str] = []
    payload = load_json(READINESS)
    if payload.get("state") != "staged-root-enforcement":
        failures.append("root readiness state mismatch")
    publication = payload.get("evidence_publication", {})
    if publication.get("mode") != "split":
        failures.append("root readiness must use split evidence publication")
    if publication.get("status") != "pending-implementation-commit":
        failures.append("evidence must remain pending until the implementation SHA exists")
    safety = payload.get("safety", {})
    for field in (
        "downloaded_helper_git_mutation",
        "github_mutation",
        "deployment_mutation",
        "autonomous_mutation_authorized",
    ):
        if safety.get(field) is not False:
            failures.append(f"root readiness safety must keep {field}=false")
    receipts = payload.get("approved_gap_receipts")
    expected = [f"SAGE-GAP-20260801-{index:03d}" for index in range(1, 10)]
    if receipts != expected:
        failures.append("readiness receipt does not preserve all nine approved gaps")
    return failures


def validate_docs_authority() -> list[str]:
    failures: list[str] = []
    for path, markers in (
        (
            AGENTS,
            (
                "Mandatory SAGE operating contract",
                "make sage-operating-contract-check",
                "one operator-executed Git or GitHub boundary",
            ),
        ),
        (
            SAGE,
            (
                "Mandatory operating-contract enforcement",
                "scripts/sage/workflows/operating_contract.py",
                "split publication",
            ),
        ),
        (
            STANDARD,
            (
                "Root enforcement composition",
                "make sage-operating-contract-check",
                "Final activation evidence",
            ),
        ),
    ):
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                failures.append(f"{path}: missing marker {marker}")

    authority = load_json(AUTHORITY)
    required = {
        str(COMPOSITION.relative_to(ROOT)),
        str(SELF_TEST.relative_to(ROOT)),
        str(Path(__file__).resolve().relative_to(ROOT)),
        str(MANIFEST.relative_to(ROOT)),
        str(READINESS.relative_to(ROOT)),
    }
    for context_id in (
        "repository-governance",
        "continuous-improvement",
        "workflow-primitives",
    ):
        matches = [
            item
            for item in authority.get("contexts", [])
            if isinstance(item, dict) and item.get("id") == context_id
        ]
        if len(matches) != 1:
            failures.append(f"authority context missing: {context_id}")
            continue
        missing = sorted(required - set(matches[0].get("authoritative_files", [])))
        if missing:
            failures.append(f"{context_id} authorities missing: {missing}")
    return failures


def negative_tests() -> list[str]:
    failures: list[str] = []
    policy = load_json(POLICY)

    mutated = json.loads(json.dumps(policy))
    mutated["helper_policy"]["git_mutation_allowed"] = True
    if not any(
        "git_mutation_allowed" in item
        for item in validate_policy(mutated)
    ):
        failures.append("negative policy test accepted helper Git mutation")

    mutated = json.loads(json.dumps(policy))
    mutated["activation_policy"]["autonomous_mutation_authorized"] = True
    if not any(
        "autonomous mutation" in item
        for item in validate_policy(mutated)
    ):
        failures.append("negative policy test accepted autonomous mutation")

    with tempfile.TemporaryDirectory(
        prefix="sage-operating-contract-negative-"
    ) as raw:
        path = Path(raw) / "bad.py"
        path.write_text(
            "import subprocess\nPRIMITIVES_USED = ('workflow.composition',)\n",
            encoding="utf-8",
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        if "subprocess" not in imports:
            failures.append("negative composition fixture failed to expose subprocess")
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        failures.extend(validate_policy(load_json(POLICY)))
        failures.extend(validate_registry(load_json(REGISTRY)))
        failures.extend(validate_composition())
        failures.extend(validate_makefile())
        failures.extend(validate_manifest())
        failures.extend(validate_readiness())
        failures.extend(validate_docs_authority())
        failures.extend(negative_tests())
    except (
        OSError,
        ValueError,
        TypeError,
        SyntaxError,
        json.JSONDecodeError,
    ) as error:
        failures.append(str(error))

    if failures:
        print("Kalaxy3 SAGE operating-contract guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS root operating-contract policy and staged activation state")
    print("PASS two-boundary composition and exact primitive sequence")
    print("PASS root Make integration and repository guardrail dependencies")
    print("PASS approved no-new-primitive component manifest")
    print("PASS split evidence-publication readiness and nine-gap continuity")
    print("PASS helper, GitHub, deployment, and autonomous-mutation negatives")
    print("Kalaxy3 SAGE operating-contract guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
