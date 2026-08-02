#!/usr/bin/env python3
"""Fail-closed guardrail for reusable SAGE workflow engineering."""

from __future__ import annotations

import ast
import importlib.util
import json
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
STATIC_GUARD = SAGE_DIR / "sage-python-static-guardrail.py"
sys.path.insert(0, str(SAGE_DIR))

from workflow import MakefileDocument  # noqa: E402

REQUIRED_MODULES = {
    "workflow.catalog": "PrimitiveCatalog",
    "workflow.runner": "CommandRunner",
    "workflow.git": "GitRepository",
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
    if payload.get("framework_version") != "0.2.0":
        failures.append("registry framework_version must be 0.2.0")
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

    for policy in (
        "composition_policy",
        "logging_policy",
        "mutation_policy",
        "evolution_policy",
        "usage_policy",
        "required_metrics",
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
    }
    for name, markers in contracts.items():
        source = (PACKAGE / name).read_text(encoding="utf-8")
        for marker in markers:
            if marker not in source:
                failures.append(
                    f"{name}: missing contract marker {marker}"
                )
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
        ):
            if marker not in text:
                failures.append(
                    f"workflow standard missing marker: {marker}"
                )
    if not SCHEMA.is_file():
        failures.append("workflow primitive schema is missing")
    else:
        json.loads(SCHEMA.read_text(encoding="utf-8"))

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
            "scripts/sage/sage-workflow-primitives-self-test.py",
            "scripts/sage/sage-workflow-primitives-guardrail.py",
            "scripts/sage/sage-workflow-usage.py",
            "markdown/standards/kalaxy3-sage-workflow-primitives-process.md",
            "markdown/standards/sage-workflow-primitives-schema-v1.0.json",
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
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        payload = load_registry()
        failures.extend(validate_registry(payload))
        failures.extend(validate_sources())
        failures.extend(validate_wrappers(payload))
        failures.extend(validate_makefile())
        failures.extend(validate_docs_and_authority())
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
    print("PASS structured versioned logging, redaction, and fsync")
    print("PASS explicit mutation, synchronization, exact scope, and candidate parsing")
    print("PASS thin compositions without direct subprocess or duplicated helpers")
    print("PASS execution-usage evidence and primitive-version provenance")
    print("PASS workflow authority, Make, documentation, and negative tests")
    print("Kalaxy3 SAGE workflow primitives guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
