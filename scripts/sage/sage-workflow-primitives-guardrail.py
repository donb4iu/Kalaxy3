#!/usr/bin/env python3
"""Fail-closed guardrail for reusable SAGE workflow engineering."""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts/sage"
PACKAGE = SAGE_DIR / "workflow"
WRAPPERS = SAGE_DIR / "workflows"
REGISTRY = ROOT / "sage-workflow-primitives.json"
SCHEMA = (
    ROOT
    / "markdown/standards/"
    "sage-workflow-primitives-schema-v1.0.json"
)
STANDARD = (
    ROOT
    / "markdown/standards/"
    "kalaxy3-sage-workflow-primitives-process.md"
)
OPERATOR_ROUTINE_SCHEMA = (
    ROOT
    / "markdown/standards/"
    "sage-operator-git-proposal-schema-v1.2.json"
)
OPERATOR_BROWSER_SCHEMA = (
    ROOT
    / "markdown/standards/"
    "sage-operator-git-proposal-schema-v1.1.json"
)
STATIC_GUARD = SAGE_DIR / "sage-python-static-guardrail.py"
SAFETY_CLI = SAGE_DIR / "sage-git-safety-guardrail.py"
GAP_ROOT = ROOT / "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001"
sys.path.insert(0, str(SAGE_DIR))

from workflow import FRAMEWORK_VERSION, AuthorityReconciler, ComponentSelector, FailureDiagnoser, GitSafetyGuardrail, MakefileDocument, OutcomeMetrics  # noqa: E402

REQUIRED_MODULES = {
    "workflow.catalog": "PrimitiveCatalog",
    "workflow.runner": "CommandRunner",
    "workflow.git": "GitRepository",
    "workflow.git_inspect": "GitInspector",
    "workflow.github_inspect": "GitHubInspector",
    "workflow.authority": "AuthorityReconciler",
    "workflow.selection": "ComponentSelector",
    "workflow.gaps": "CapabilityGapRecorder",
    "workflow.diagnosis": "FailureDiagnoser",
    "workflow.metrics": "OutcomeMetrics",
    "workflow.files": "AtomicFileWriter",
    "workflow.proposal": "OperatorGitProposal",
    "workflow.safety": "GitSafetyGuardrail",
    "workflow.discovery": "SageDiscovery",
    "workflow.lifecycle": "ImprovementActionClient",
    "workflow.makefile": "MakefileDocument",
    "workflow.validation": "ValidationPlan",
    "workflow.evidence": "CloseoutWriter",
    "workflow.usage": "UsageAnalyzer",
    "workflow.composition": "Workflow",
}
REQUIRED_PRINCIPLES = {
    "single-responsibility primitives",
    "thin declarative compositions",
    "explicit dry-run and apply",
    "fail-closed repository state",
    "exact mutation scopes",
    "structured label-and-digest logging",
    "secret redaction",
    "bounded command execution",
    "atomic evidence writes",
    "runtime-path integration tests",
    "versioned evolution from failure evidence",
    "candidate Makefile parsing before replacement",
    "least-authority read-only Git inspection",
    "least-authority read-only GitHub inspection",
    "mode-preserving atomic file replacement",
    "operator-executed one-boundary proposals",
    "production helper Git and credential safety",
    "federated authority assertions remain separate from inference",
    "explicit component ranking without opaque composite scores",
    "capability-gap proof before new primitives",
    "failure diagnosis before corrective mutation",
    "versioned composition manifests",
    "semantic raw metrics precede transparent derived rates and comparable trends",
    "root operating-contract composition and guardrail enforcement",
}


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def imports(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(
                alias.name.split(".")[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".")[0])
    return result


def assigned_string_sequence(
    tree: ast.AST,
    name: str,
) -> tuple[str, ...] | None:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets: list[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        else:
            targets = [node.target]
            value = node.value
        if not any(
            isinstance(target, ast.Name) and target.id == name
            for target in targets
        ):
            continue
        if isinstance(value, (ast.Tuple, ast.List)):
            items: list[str] = []
            for item in value.elts:
                if not isinstance(item, ast.Constant) or not isinstance(
                    item.value,
                    str,
                ):
                    return None
                items.append(item.value)
            return tuple(items)
    return None


def load_registry() -> dict[str, Any]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("primitive registry must be an object")
    return payload


def validate_registry(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != "1.0":
        failures.append("registry schema_version must be 1.0")
    if payload.get("framework_version") != FRAMEWORK_VERSION:
        failures.append("registry framework_version must match canonical FRAMEWORK_VERSION")
    if payload.get("status") != "pilot":
        failures.append("new framework must begin at pilot maturity")

    principles = set(payload.get("principles", []))
    missing_principles = sorted(REQUIRED_PRINCIPLES - principles)
    if missing_principles:
        failures.append(
            f"registry principles missing: {missing_principles}"
        )

    entries = payload.get("primitives")
    if not isinstance(entries, list):
        return [*failures, "registry primitives must be an array"]

    identifiers: set[str] = set()
    modules: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("primitive entry must be an object")
            continue
        primitive_id = entry.get("primitive_id")
        if not isinstance(primitive_id, str):
            failures.append("primitive_id must be a string")
            continue
        if primitive_id in identifiers:
            failures.append(
                f"duplicate primitive_id: {primitive_id}"
            )
        identifiers.add(primitive_id)
        for field in (
            "version",
            "module",
            "symbol",
            "side_effects",
            "idempotency",
            "logging",
            "failure_mode",
            "tests",
            "maturity",
        ):
            if field not in entry:
                failures.append(
                    f"{primitive_id}: missing {field}"
                )
        if entry.get("maturity") != "pilot":
            failures.append(
                f"{primitive_id}: unearned non-pilot maturity"
            )
        module = entry.get("module")
        symbol = entry.get("symbol")
        if isinstance(module, str) and isinstance(symbol, str):
            modules[module] = symbol

    for module, symbol in REQUIRED_MODULES.items():
        if modules.get(module) != symbol:
            failures.append(
                f"registry missing {module}.{symbol}"
            )

    operator_entry = next(
        (
            item
            for item in entries
            if isinstance(item, dict)
            and item.get("primitive_id") == "operator.git-proposal"
        ),
        None,
    )
    if not isinstance(operator_entry, dict) or operator_entry.get("version") != "1.3.0":
        failures.append("operator.git-proposal version must be 1.3.0")

    safety_entry = next(
        (
            item
            for item in entries
            if isinstance(item, dict)
            and item.get("primitive_id") == "git.safety-guardrail"
        ),
        None,
    )
    if not isinstance(safety_entry, dict) or safety_entry.get("version") != "1.3.0":
        failures.append("git.safety-guardrail version must be 1.3.0")

    for policy in (
        "composition_policy",
        "logging_policy",
        "mutation_policy",
        "evolution_policy",
        "usage_policy",
        "required_metrics",
        "operating_contract_policy",
    ):
        if policy not in payload:
            failures.append(f"registry missing {policy}")

    mutation = payload.get("mutation_policy", {})
    for field in (
        "explicit_apply_required",
        "dry_run_first",
        "clean_tree_required",
        "remote_sync_required",
        "exact_path_scope_required",
        "atomic_file_write_required",
        "candidate_makefile_parse_required",
        "downloaded_helper_git_mutation_forbidden",
        "operator_one_boundary_required",
        "preserve_existing_file_mode_required",
        "personal_credentials_in_generated_code_forbidden",
        "production_git_repository_primitive_restricted",
    ):
        if mutation.get(field) is not True:
            failures.append(
                f"mutation policy must enable {field}"
            )

    evolution = payload.get("evolution_policy", {})
    for field in (
        "failure_updates_primitive_and_regression_test",
        "primitive_version_bump_required_for_behavior_change",
        "wrapper_only_root_cause_patch_forbidden",
        "execution_evidence_records_primitive_versions",
    ):
        if evolution.get(field) is not True:
            failures.append(
                f"evolution policy must enable {field}"
            )
    return failures


def validate_sources() -> list[str]:
    failures: list[str] = []
    python_paths = sorted(PACKAGE.glob("*.py"))
    if len(python_paths) < 12:
        failures.append("workflow package is incomplete")

    static_module = load_module(
        "sage_python_static_guardrail",
        STATIC_GUARD,
    )
    for path in python_paths:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            failures.append(f"{path}: {error}")
            continue

        unresolved = static_module.undefined_globals(
            source,
            filename=str(path),
        )
        if unresolved:
            failures.append(
                f"{path}: unresolved globals {list(unresolved)}"
            )

        if path.name != "runner.py" and "subprocess" in imports(tree):
            failures.append(
                f"{path}: subprocess is allowed only in runner.py"
            )
        if path.name == "proposal.py":
            http_imports = sorted(
                item
                for item in imports(tree)
                if item == "urllib"
                or item.startswith("urllib.")
                or item == "http"
                or item.startswith("http.")
            )
            if http_imports:
                failures.append(
                    f"{path}: browser proposal must not import HTTP libraries {http_imports}"
                )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if (
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    failures.append(
                        f"{path}: shell=True is forbidden"
                    )

    contracts = {
        "runner.py": (
            "timeout=spec.timeout_seconds",
            "command_digest",
            "output_sha256",
            "sensitive_values",
        ),
        "logging.py": (
            "O_APPEND",
            "os.fsync",
            "primitive_version",
            "redact_text",
        ),
        "git.py": (
            "apply: bool",
            "require_clean",
            "require_synced",
            "require_exact_paths",
            "commit_and_push",
        ),
        "git_inspect.py": (
            "_FIXED_READ_ONLY",
            "is_read_only_git_arguments",
            "git.inspect",
            "require_upstream_equal",
            "require_exact_paths",
            "rstrip(\"\\n\")",
        ),
        "files.py": (
            "os.replace",
            "os.fsync",
            "stat.S_IMODE",
            "AtomicFileTransaction",
        ),
        "proposal.py": (
            "command_count",
            "executed_by_helper",
            "contains_secret",
            "OperatorGitProposal",
            "build_browser",
            "browser-review",
            "github-browser",
            "mutation_performed_by_helper",
            "routine-git-lifecycle",
            "sage-routine-git-lifecycle.py",
            "repository_receipt_required",
            'routine_receipt = boundary == "routine-git-lifecycle"',
        ),
        "safety.py": (
            "GIT-MUTATION",
            "GITHUB-MUTATION",
            "CREDENTIAL-INHERITANCE",
            "DEPLOYMENT-MUTATION",
            "_TRUSTED_ROUTINE_GIT_CONTROLLER_SUFFIX",
            "_TRUSTED_ROUTINE_GIT_MUTATORS",
            "_is_trusted_routine_git_controller",
            "is_read_only_git_arguments(argv[1:])",
        ),
        "lifecycle.py": (
            "sage-action-id.py",
            "allocate_id",
            "register",
            "transition",
        ),
        "makefile.py": (
            "add_dependency",
            "_target_range",
            "prerequisite continuation",
        ),
        "evidence.py": (
            "os.replace",
            "os.fsync",
            "used_primitives",
        ),
        "usage.py": (
            "successful_events_by_primitive_version",
            "failed_events_by_primitive_version",
        ),
        "metrics.py": (
            "RAW_FIELDS",
            "DERIVED_FIELDS",
            "composite_score_enabled",
            "workflow_class",
            "comparability_basis",
        ),
    }
    for name, markers in contracts.items():
        source = (PACKAGE / name).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                failures.append(
                    f"{name}: missing contract marker {marker}"
                )
    if not SAFETY_CLI.is_file():
        failures.append("Git safety CLI is missing")
    else:
        safety_source = SAFETY_CLI.read_text(encoding="utf-8")
        for marker in ("--self-test", "GitSafetyGuardrail", "FAIL CLOSED"):
            if marker not in safety_source:
                failures.append(f"Git safety CLI missing marker {marker}")
    return failures


def wrapper_failures(
    path: Path,
    payload: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [f"{path}: {error}"]

    static_module = load_module(
        "sage_python_static_guardrail",
        STATIC_GUARD,
    )
    unresolved = static_module.undefined_globals(
        source,
        filename=str(path),
    )
    if unresolved:
        failures.append(
            f"{path}: unresolved globals {list(unresolved)}"
        )

    policy = payload["composition_policy"]
    forbidden_imports = set(
        policy.get("forbidden_direct_imports", [])
    )
    direct = sorted(forbidden_imports & imports(tree))
    if direct:
        failures.append(
            f"{path}: forbidden direct imports {direct}"
        )
    if path.name == "checkpoint_promotion.py":
        http_imports = sorted(
            item
            for item in imports(tree)
            if item == "urllib"
            or item.startswith("urllib.")
            or item == "http"
            or item.startswith("http.")
        )
        if http_imports:
            failures.append(
                f"{path}: browser checkpoint promotion must not import HTTP libraries {http_imports}"
            )

    forbidden_definitions = set(
        policy.get("forbidden_helper_definitions", [])
    )
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    duplicate = sorted(forbidden_definitions & defined)
    if duplicate:
        failures.append(
            f"{path}: reimplements primitive helpers {duplicate}"
        )

    manifest = assigned_string_sequence(
        tree,
        policy["required_manifest_constant"],
    )
    if not manifest:
        failures.append(
            f"{path}: PRIMITIVES_USED manifest is missing"
        )
    else:
        registered = {
            item["primitive_id"]
            for item in payload["primitives"]
        }
        unknown = sorted(set(manifest) - registered)
        if unknown:
            failures.append(
                f"{path}: unknown primitives {unknown}"
            )

    if "from workflow import" not in source:
        failures.append(
            f"{path}: does not import repository workflow primitives"
        )
    return failures



def validate_framework_version_authority() -> list[str]:
    failures: list[str] = []
    payload = load_registry()
    if payload.get("framework_version") != FRAMEWORK_VERSION:
        failures.append(
            "registry framework_version does not match canonical FRAMEWORK_VERSION"
        )
    current_consumers = (
        ROOT / "scripts/sage/sage-workflow-primitives-guardrail.py",
        ROOT / "scripts/sage/sage-operating-contract-guardrail.py",
    )
    version_literal = re.compile(
        r"framework_version[^\n]*[=!]=?[^\n]*[\"\']\d+\.\d+\.\d+[\"\']"
    )
    for path in current_consumers:
        source = path.read_text(encoding="utf-8")
        if "FRAMEWORK_VERSION" not in source:
            failures.append(
                f"{path.relative_to(ROOT)} does not consume canonical FRAMEWORK_VERSION"
            )
        if version_literal.search(source):
            failures.append(
                f"{path.relative_to(ROOT)} hard-codes a current framework version"
            )
    return failures


def validate_wrappers(payload: dict[str, Any]) -> list[str]:
    wrappers = sorted(WRAPPERS.glob("*.py"))
    if not wrappers:
        return ["no workflow compositions were found"]
    failures: list[str] = []
    for path in wrappers:
        failures.extend(wrapper_failures(path, payload))
    return failures


def validate_makefile() -> list[str]:
    failures: list[str] = []
    document = MakefileDocument.parse(
        (ROOT / "Makefile").read_text(encoding="utf-8")
    )
    for target, dependency in (
        ("sage-self-test", "sage-workflow-self-test"),
        ("sage-guardrails", "sage-workflow-guardrail"),
        ("sage-self-test", "sage-operating-contract-self-test"),
        ("sage-guardrails", "sage-operating-contract-guardrail"),
    ):
        if dependency not in document.dependencies(target):
            failures.append(
                f"Make target {target} does not depend on {dependency}"
            )
    rendered = document.render()
    for marker in (
        "sage-workflow-self-test:",
        "sage-workflow-guardrail:",
        "scripts/sage/sage-workflow-primitives-self-test.py",
        "scripts/sage/sage-workflow-primitives-guardrail.py",
        "scripts/sage/sage-operating-contract-self-test.py",
        "scripts/sage/sage-operating-contract-guardrail.py",
        "sage-operating-contract-check:",
    ):
        if marker not in rendered:
            failures.append(
                f"Makefile missing workflow marker: {marker}"
            )
    return failures


def validate_docs_and_authority() -> list[str]:
    failures: list[str] = []
    if not STANDARD.is_file():
        failures.append("workflow primitive standard is missing")
    else:
        text = STANDARD.read_text(encoding="utf-8")
        for marker in (
            "thin compositions",
            "shell=True",
            "explicit `apply=True`",
            "wrapper-only",
            "primitive reuse ratio",
            "candidate Makefile",
            "git.inspect",
            "github.inspect",
            "file.atomic-preserve-mode",
            "operator.git-proposal",
            "browser-review",
            "git.safety-guardrail",
            "routine Git lifecycle",
            "metrics.outcome",
            "Root operating-contract composition",
        ):
            if marker not in text:
                failures.append(
                    f"workflow standard missing marker: {marker}"
                )
    if not SCHEMA.is_file():
        failures.append("workflow primitive schema is missing")
    else:
        json.loads(SCHEMA.read_text(encoding="utf-8"))
    github_source = (ROOT / "scripts/sage/workflow/github_inspect.py").read_text(encoding="utf-8")
    for marker in (
        "GitHubCheckRunSnapshot",
        "/check-runs",
        '"filter": "latest"',
        "check_suite_id",
        "require_successful_check",
        "require_successful_checks",
        "required: bool = True",
        "successful required check-suite identity is ambiguous",
    ):
        if marker not in github_source:
            failures.append(f"github.inspect missing check-run marker: {marker}")
    registry = load_registry()
    github_items = [item for item in registry.get("primitives", []) if isinstance(item, dict) and item.get("primitive_id") == "github.inspect"]
    if len(github_items) != 1 or github_items[0].get("version") != "1.4.0":
        failures.append("github.inspect registry version must be 1.4.0")
    if not OPERATOR_ROUTINE_SCHEMA.is_file():
        failures.append("routine-receipt operator proposal schema is missing")
    else:
        routine_schema = json.loads(OPERATOR_ROUTINE_SCHEMA.read_text(encoding="utf-8"))
        if routine_schema.get("$id") != "https://kalaxy3.local/sage-operator-git-proposal-schema-v1.2.json":
            failures.append("routine-receipt operator proposal schema id mismatch")
    if not OPERATOR_BROWSER_SCHEMA.is_file():
        failures.append("browser-backed operator proposal schema is missing")
    else:
        browser_schema = json.loads(
            OPERATOR_BROWSER_SCHEMA.read_text(encoding="utf-8")
        )
        if browser_schema.get("$id") != (
            "https://kalaxy3.local/"
            "sage-operator-git-proposal-schema-v1.1.json"
        ):
            failures.append("browser-backed operator proposal schema id mismatch")

    authority = json.loads(
        (ROOT / "sage-change-authority.json").read_text(
            encoding="utf-8"
        )
    )
    contexts = [
        item
        for item in authority.get("contexts", [])
        if isinstance(item, dict)
        and item.get("id") == "workflow-primitives"
    ]
    if len(contexts) != 1:
        failures.append(
            "workflow-primitives authority context is missing"
        )
    else:
        required = {
            "sage-workflow-primitives.json",
            "scripts/sage/workflow/",
            "scripts/sage/workflows/",
            "scripts/sage/workflows/routine_git_lifecycle.py",
            "scripts/sage/sage-routine-git-lifecycle.py",
            "scripts/sage/sage-workflow-primitives-self-test.py",
            "scripts/sage/sage-workflow-primitives-guardrail.py",
            "scripts/sage/sage-workflow-usage.py",
            "scripts/sage/sage-git-safety-guardrail.py",
            "scripts/sage/workflow/git_inspect.py",
            "scripts/sage/workflow/github_inspect.py",
            "scripts/sage/workflow/files.py",
            "scripts/sage/workflow/proposal.py",
            "scripts/sage/workflow/safety.py",
            "scripts/sage/workflow/authority.py",
            "scripts/sage/workflow/selection.py",
            "scripts/sage/workflow/gaps.py",
            "scripts/sage/workflow/diagnosis.py",
            "scripts/sage/sage-decision-primitives-guardrail.py",
            "scripts/sage/sage-outcome-metrics-guardrail.py",
            "scripts/sage/workflow/metrics.py",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-outcome-metrics.json",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-outcome-metrics.json",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/outcome-metrics-baseline.json",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/",
            "markdown/standards/kalaxy3-sage-workflow-primitives-process.md",
            "markdown/standards/sage-workflow-primitives-schema-v1.0.json",
            "markdown/standards/sage-operator-git-proposal-schema-v1.1.json",
            "markdown/standards/sage-operator-git-proposal-schema-v1.2.json",
            "scripts/sage/workflows/operating_contract.py",
            "scripts/sage/sage-operating-contract-self-test.py",
            "scripts/sage/sage-operating-contract-guardrail.py",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-root-enforcement.json",
            "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/root-enforcement-readiness.json",
        }
        observed = set(
            contexts[0].get("authoritative_files", [])
        )
        missing = sorted(required - observed)
        if missing:
            failures.append(
                f"workflow-primitives authorities missing: {missing}"
            )
    return failures



def validate_gap_receipts(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    manifest_path = GAP_ROOT / "component-selection-approved.json"
    if not manifest_path.is_file():
        failures.append("approved Phase 2 component-selection manifest is missing")
        return failures
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0":
        failures.append("Phase 2 component manifest schema_version must be 1.0")
    if manifest.get("approval", {}).get("status") != "approved":
        failures.append("Phase 2 component manifest must be approved")
    if manifest.get("composite_score_enabled") is not False:
        failures.append("Phase 2 component manifest must not enable a composite score")


    phase3_manifest_path = GAP_ROOT / "component-selection-decision-primitives.json"
    if not phase3_manifest_path.is_file():
        failures.append("approved Phase 3 component-selection manifest is missing")
    else:
        phase3_manifest = json.loads(phase3_manifest_path.read_text(encoding="utf-8"))
        if phase3_manifest.get("approval", {}).get("status") != "approved":
            failures.append("Phase 3 component manifest must be approved")
        if phase3_manifest.get("composite_score_enabled") is not False:
            failures.append("Phase 3 component manifest must not enable a composite score")

    phase4_manifest_path = GAP_ROOT / "component-selection-outcome-metrics.json"
    if not phase4_manifest_path.is_file():
        failures.append("approved Phase 4 component-selection manifest is missing")
    else:
        phase4_manifest = json.loads(phase4_manifest_path.read_text(encoding="utf-8"))
        if phase4_manifest.get("approval", {}).get("status") != "approved":
            failures.append("Phase 4 component manifest must be approved")
        if phase4_manifest.get("composite_score_enabled") is not False:
            failures.append("Phase 4 component manifest must not enable a composite score")
    phase5_manifest_path = GAP_ROOT / "component-selection-root-enforcement.json"
    if not phase5_manifest_path.is_file():
        failures.append("approved root-enforcement component-selection manifest is missing")
    else:
        phase5_manifest = json.loads(phase5_manifest_path.read_text(encoding="utf-8"))
        if phase5_manifest.get("approval", {}).get("status") != "approved":
            failures.append("root-enforcement component manifest must be approved")
        if phase5_manifest.get("capability_gap_receipts") != []:
            failures.append("root-enforcement composition must not invent a tenth gap")
        if phase5_manifest.get("composite_score_enabled") is not False:
            failures.append("root-enforcement component manifest must not enable a composite score")
    baseline_path = GAP_ROOT / "outcome-metrics-baseline.json"
    if not baseline_path.is_file():
        failures.append("Phase 4 outcome baseline is missing")
    else:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        try:
            rebuilt = OutcomeMetrics.build_report(report_id=baseline["report_id"], captured_at=baseline["captured_at"], period=baseline["period"], workflow_class=baseline["workflow_class"], raw_metrics=baseline["raw_metrics"], provenance=baseline["provenance"], limitations=baseline["limitations"], trends=baseline["trends"])
            if rebuilt != baseline:
                failures.append("Phase 4 outcome baseline does not match primitive semantics")
        except (KeyError, TypeError, ValueError) as error:
            failures.append(f"Phase 4 outcome baseline invalid: {error}")

    expected = {
        "git.inspect": GAP_ROOT / "capability-gap-git-inspect.json",
        "github.inspect": GAP_ROOT / "capability-gap-github-inspect.json",
        "file.atomic-preserve-mode": GAP_ROOT / "capability-gap-atomic-file.json",
        "operator.git-proposal": GAP_ROOT / "capability-gap-operator-proposal.json",
        "git.safety-guardrail": GAP_ROOT / "capability-gap-git-safety.json",
        "authority.reconcile": GAP_ROOT / "capability-gap-authority-reconcile.json",
        "component.select": GAP_ROOT / "capability-gap-component-select.json",
        "capability.gap": GAP_ROOT / "capability-gap-capability-gap.json",
        "failure.diagnose": GAP_ROOT / "capability-gap-failure-diagnose.json",
        "metrics.outcome": GAP_ROOT / "capability-gap-outcome-metrics.json",
    }
    registry_entries = {
        item.get("primitive_id"): item
        for item in payload.get("primitives", [])
        if isinstance(item, dict)
    }
    for primitive_id, path in expected.items():
        if not path.is_file():
            failures.append(f"capability-gap receipt missing: {path}")
            continue
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt.get("schema_version") != "1.0":
            failures.append(f"{path}: schema_version must be 1.0")
        if receipt.get("approval", {}).get("status") != "approved":
            failures.append(f"{path}: approval must be approved")
        proposed = receipt.get("proposed_primitive", {})
        if proposed.get("primitive_id") != primitive_id:
            failures.append(f"{path}: proposed primitive mismatch")
        entry = registry_entries.get(primitive_id, {})
        if entry.get("capability_gap_receipt") != str(path.relative_to(ROOT)):
            failures.append(f"{primitive_id}: registry gap receipt linkage mismatch")
    return failures


def git_safety_contract_tests(root: Path) -> list[str]:
    """Exercise canonical read-only Git parity and nearby fail-closed variants."""
    failures: list[str] = []
    read_only = (
        ("git", "branch", "--show-current"),
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        ("git", "diff", "--name-only"),
        ("git", "diff", "--cached", "--name-only"),
        ("git", "diff", "--check"),
        ("git", "diff", "--cached", "--check"),
        ("git", "ls-files", "--others", "--exclude-standard"),
        ("git", "rev-parse", "origin/main"),
        ("git", "ls-remote", "--heads", "origin", "refs/heads/feature/example"),
        ("git", "merge-base", "--is-ancestor", "main", "feature/example"),
        ("git", "rev-list", "--parents", "main..feature/example"),
        ("git", "diff", "--name-only", "main...feature/example"),
    )
    rejected = (
        ("git", "rev-parse", "--verify"),
        ("git", "ls-remote", "origin", "refs/heads/feature/example"),
        ("git", "ls-remote", "--heads", "origin", "refs/heads/../main"),
        ("git", "merge-base", "main", "feature/example"),
        ("git", "rev-list", "main..feature/example"),
        ("git", "diff", "--name-only", "main..feature/example"),
        ("git", "fetch", "origin", "main"),
        ("git", "push", "origin", "main"),
    )
    template = (
        "from workflow import CommandSpec\n"
        "CommandSpec(primitive_id='command.run', label='x', "
        "argv={argv!r}, cwd=ROOT)\n"
    )
    for index, argv in enumerate(read_only):
        source = template.format(argv=argv)
        path = root / f"read-only-{index}.py"
        violations = GitSafetyGuardrail.scan_source(source, path=path)
        if any(item.code == "GIT-MUTATION" for item in violations):
            failures.append(f"canonical read-only Git command rejected: {argv!r}")
    for index, argv in enumerate(rejected):
        source = template.format(argv=argv)
        path = root / f"rejected-{index}.py"
        violations = GitSafetyGuardrail.scan_source(source, path=path)
        if not any(item.code == "GIT-MUTATION" for item in violations):
            failures.append(f"unsafe or unapproved Git command accepted: {argv!r}")
    return failures


def negative_tests(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="sage-workflow-guardrail-negative-"
    ) as raw:
        root = Path(raw)
        bad = root / "bad.py"
        bad.write_text(
            """import subprocess
PRIMITIVES_USED = ("command.run",)
def run():
    subprocess.run(["git", "status"])
""",
            encoding="utf-8",
        )
        observed = wrapper_failures(bad, payload)
        if not any(
            "forbidden direct imports" in item
            for item in observed
        ):
            failures.append(
                "negative test accepted direct subprocess import"
            )
        if not any(
            "reimplements primitive helpers" in item
            for item in observed
        ):
            failures.append(
                "negative test accepted duplicate run helper"
            )

        fixture = """guardrails: alpha \
            beta
	@echo guardrails
"""
        document = MakefileDocument.parse(fixture)
        document.add_dependency("guardrails", "workflow")
        if "workflow" not in document.dependencies("guardrails"):
            failures.append(
                "negative Make continuation regression failed"
            )
        failures.extend(git_safety_contract_tests(root))
        mutating = root / "mutating-helper.py"
        mutating.write_text(
            "import subprocess\nsubprocess.run(['git', 'push', 'origin', 'main'])\n",
            encoding="utf-8",
        )
        violations = GitSafetyGuardrail.scan_paths((mutating,))
        if not any(item.code == "GIT-MUTATION" for item in violations):
            failures.append("negative test accepted production Git mutation")
        direct_github = root / "direct-github-api.py"
        direct_github.write_text(
            "from urllib.request import urlopen\n"
            + "urlopen('https://api."
            + "github.com/repos/example/repo/pulls')\n",
            encoding="utf-8",
        )
        violations = GitSafetyGuardrail.scan_paths((direct_github,))
        if not any(item.code == "GITHUB-DIRECT-API" for item in violations):
            failures.append("negative test accepted direct GitHub API use")
        credential = root / "credential-helper.py"
        credential.write_text(
            "import os\ntoken = os.environ.get('GH_TOKEN')\n",
            encoding="utf-8",
        )
        violations = GitSafetyGuardrail.scan_paths((credential,))
        if not any(item.code == "CREDENTIAL-INHERITANCE" for item in violations):
            failures.append("negative test accepted credential inheritance")
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        payload = load_registry()
        failures.extend(validate_registry(payload))
        failures.extend(validate_sources())
        failures.extend(validate_framework_version_authority())
        failures.extend(validate_wrappers(payload))
        failures.extend(validate_makefile())
        failures.extend(validate_docs_and_authority())
        failures.extend(validate_gap_receipts(payload))
        failures.extend(negative_tests(payload))
    except (
        ImportError,
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        SyntaxError,
        TypeError,
        ValueError,
    ) as error:
        failures.append(str(error))

    if failures:
        print("Kalaxy3 SAGE workflow primitives guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS versioned primitive registry and pilot maturity")
    print("PASS centralized command, Git, discovery, lifecycle, Make, and evidence paths")
    print("PASS least-authority Git and GitHub inspection, atomic writes, operator proposals, and helper safety")
    print("PASS authority reconciliation, component selection, capability gaps, and failure diagnosis")
    print("PASS semantic outcome metrics, null preservation, and comparable trends")
    print("PASS root operating-contract composition and guardrail integration")
    print("PASS structured versioned logging, redaction, and fsync")
    print("PASS explicit mutation, synchronization, exact scope, and candidate parsing")
    print("PASS thin compositions without direct subprocess or duplicated helpers")
    print("PASS execution-usage evidence and primitive-version provenance")
    print("PASS workflow authority, Make, documentation, and negative tests")
    print("Kalaxy3 SAGE workflow primitives guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
