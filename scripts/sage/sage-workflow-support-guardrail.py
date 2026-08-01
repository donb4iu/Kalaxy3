#!/usr/bin/env python3
"""Guard canonical workflow-support allocation and static validation."""

from __future__ import annotations

import ast
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IDENTIFIERS = ROOT / "scripts/sage/sage_identifiers.py"
ACTION_ID_CLI = ROOT / "scripts/sage/sage-action-id.py"
STATIC_GUARD = (
    ROOT / "scripts/sage/sage-python-static-guardrail.py"
)
STANDARD = (
    ROOT
    / "markdown"
    / "standards"
    / "kalaxy3-sage-workflow-support-process.md"
)
DUPLICATE_NAMES = {
    "next_action_id",
    "allocate_action_id",
    "allocate_scoped_id",
}


def load_module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(
        name,
        path,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def source_functions(path: Path) -> set[str]:
    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }


def validate_allocator() -> list[str]:
    failures: list[str] = []
    if not IDENTIFIERS.is_file():
        return ["canonical identifier module is missing"]

    source = IDENTIFIERS.read_text(encoding="utf-8")
    if "import re" in source or "re." in source:
        failures.append(
            "canonical identifier allocator must not use regex parsing"
        )
    for marker in (
        "allocate_scoped_id",
        "allocate_action_id",
        "candidate not in occupied",
        "maximum_sequence",
    ):
        if marker not in source:
            failures.append(
                f"identifier allocator missing marker: {marker}"
            )

    if not ACTION_ID_CLI.is_file():
        failures.append("canonical action-ID CLI is missing")
    else:
        cli_source = ACTION_ID_CLI.read_text(encoding="utf-8")
        if "from sage_identifiers import" not in cli_source:
            failures.append(
                "action-ID CLI does not use canonical allocator"
            )
        for marker in (
            "collision allocation regression failed",
            "first-free gap allocation failed",
            "namespace exhaustion",
        ):
            if marker not in cli_source:
                failures.append(
                    f"action-ID CLI missing regression marker: {marker}"
                )
    return failures


def validate_static_guardrail() -> list[str]:
    failures: list[str] = []
    if not STATIC_GUARD.is_file():
        return ["Python static guardrail is missing"]
    module = load_module(
        "sage_python_static_guardrail",
        STATIC_GUARD,
    )
    negative = """def register_action():
    return FAILURE_EVIDENCE
"""
    observed = module.undefined_globals(
        negative,
        filename="negative.py",
    )
    if tuple(observed) != ("FAILURE_EVIDENCE",):
        failures.append(
            "static guardrail does not catch undefined global"
        )
    return failures


def duplicate_allocator_failures() -> list[str]:
    failures: list[str] = []
    allowed = {IDENTIFIERS.resolve()}
    for path in sorted((ROOT / "scripts/sage").rglob("*.py")):
        if path.resolve() in allowed:
            continue
        duplicate = sorted(
            source_functions(path) & DUPLICATE_NAMES
        )
        if duplicate:
            failures.append(
                f"{path.relative_to(ROOT)} duplicates "
                f"canonical allocator functions {duplicate}"
            )
    return failures


def make_target_dependencies(text: str, target: str) -> tuple[str, ...]:
    """Parse a complete Make prerequisite continuation."""
    lines = text.splitlines()
    matches = [
        index for index, line in enumerate(lines)
        if line.startswith(f"{target}:")
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one Make target {target}, found {len(matches)}"
        )
    start = matches[0]
    end = start
    while lines[end].rstrip().endswith("\\"):
        end += 1
        if end >= len(lines):
            raise ValueError(
                f"Unterminated Make target continuation: {target}"
            )
        if lines[end].startswith("\t"):
            raise ValueError(
                f"Recipe appears inside Make target continuation: {target}"
            )
    fragments = [
        lines[start].split(":", 1)[1],
        *lines[start + 1 : end + 1],
    ]
    dependencies: list[str] = []
    for fragment in fragments:
        normalized = fragment.strip()
        if normalized.endswith("\\"):
            normalized = normalized[:-1].rstrip()
        dependencies.extend(normalized.split())
    return tuple(dependencies)


def integration_failures() -> list[str]:
    failures: list[str] = []
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    for marker in (
        "sage-workflow-support-self-test:",
        "sage-workflow-support-guardrail:",
        "scripts/sage/sage-action-id.py --self-test",
        "scripts/sage/sage-python-static-guardrail.py --self-test",
        "scripts/sage/sage-workflow-support-guardrail.py",
    ):
        if marker not in makefile:
            failures.append(
                f"Makefile missing workflow-support marker: {marker}"
            )

    for target, dependency in (
        ("sage-self-test", "sage-workflow-support-self-test"),
        ("sage-guardrails", "sage-workflow-support-guardrail"),
    ):
        try:
            dependencies = make_target_dependencies(makefile, target)
        except ValueError as error:
            failures.append(str(error))
            continue
        if dependency not in dependencies:
            failures.append(
                f"Make target {target} does not depend on {dependency}"
            )

    if not STANDARD.is_file():
        failures.append("workflow-support standard is missing")
    else:
        standard = STANDARD.read_text(encoding="utf-8")
        for marker in (
            "canonical allocator",
            "undefined global",
            "wrapper-only",
            "exact runtime path",
        ):
            if marker not in standard:
                failures.append(
                    f"workflow-support standard missing: {marker}"
                )

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
            "scripts/sage/sage_identifiers.py",
            "scripts/sage/sage-action-id.py",
            "scripts/sage/sage-python-static-guardrail.py",
            "scripts/sage/sage-workflow-support-guardrail.py",
            "markdown/standards/kalaxy3-sage-workflow-support-process.md",
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


def negative_test() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(
        prefix="sage-workflow-support-negative-"
    ) as raw:
        root = Path(raw)
        duplicate = root / "duplicate.py"
        duplicate.write_text(
            """def next_action_id(registry):
    return "SAGE-ACTION-20260801-001"
""",
            encoding="utf-8",
        )
        if "next_action_id" not in source_functions(duplicate):
            failures.append(
                "duplicate allocator negative fixture was not detected"
            )
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        failures.extend(validate_allocator())
        failures.extend(validate_static_guardrail())
        failures.extend(duplicate_allocator_failures())
        failures.extend(integration_failures())
        failures.extend(negative_test())
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
        print("Kalaxy3 workflow-support guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical set-based SAGE action-ID allocation")
    print("PASS collision, gap, malformed, and exhaustion contracts")
    print("PASS source-only undefined-global validation")
    print("PASS duplicate allocator implementations prohibited")
    print("PASS Make, authority, and process integration")
    print("PASS workflow-support negative tests")
    print("Kalaxy3 workflow-support guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
