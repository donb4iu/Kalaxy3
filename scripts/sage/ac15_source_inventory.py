"""Produce a non-secret source inventory for SAGE issue #44 / AC15.

This is a static discovery aid, NOT proof of runtime credential isolation.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any


def _record(path: Path, root: Path, line: int, category: str) -> dict[str, Any]:
    """Create one source-location record without copying credential values.

    Args:
        path: Examined file.
        root: Repository root.
        line: Approximate evidence line.
        category: Source-level risk category.
    """
    return {"file": path.relative_to(root).as_posix(), "line": line,
            "category": category}


def _is_attribute(node: ast.AST, module: str, member: str) -> bool:
    """Recognize a direct module attribute in a parsed Python expression.

    Args:
        node: Expression to examine.
        module: Expected module identifier.
        member: Expected attribute.
    """
    return (isinstance(node, ast.Attribute) and node.attr == member
            and isinstance(node.value, ast.Name) and node.value.id == module)


def scan_python(path: Path, root: Path) -> list[dict[str, Any]]:
    """Inventory relevant ambient-environment, process, and HTTP interfaces.

    Args:
        path: Python source file.
        root: Repository root for relative evidence paths.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeError) as exc:
        return [_record(path, root, getattr(exc, "lineno", 1) or 1,
                        "unparseable-source")]
    records: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        category = ""
        if _is_attribute(node, "os", "environ"):
            category = "ambient-environment-reference"
        elif isinstance(node, ast.Call):
            call = node.func
            if _is_attribute(call, "subprocess", "run") or _is_attribute(
                call, "subprocess", "Popen"
            ):
                category = "subprocess-execution"
            elif (isinstance(call, ast.Name) and call.id == "urlopen") or (
                _is_attribute(call, "requests", "request")
            ):
                category = "http-transport"
        if category:
            records.append(_record(path, root, node.lineno, category))
    return records


def scan_actions(path: Path, root: Path) -> list[dict[str, Any]]:
    """Identify Actions YAML permission grants without reading secret values.

    Args:
        path: GitHub Actions workflow YAML file.
        root: Repository root for relative evidence paths.
    """
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        write_grant = r"^\s*(contents|issues|pull-requests|projects):\s*write\s*(#.*)?$"
        if re.match(write_grant, line):
            records.append(_record(path, root, line_no, "actions-write-permission"))
        if re.search(r"\$\{\{\s*secrets\.", line):
            records.append(_record(path, root, line_no, "actions-secret-reference"))
    return records


def build_inventory(root: Path) -> dict[str, Any]:
    """Build a deterministic, source-only inventory of access surfaces.

    Args:
        root: Path containing the Kalaxy3 repository source.
    """
    records: list[dict[str, Any]] = []
    for path in sorted((root / "scripts/sage").rglob("*.py")):
        records.extend(scan_python(path, root))
    for path in sorted((root / ".github/workflows").glob("*.yml")):
        records.extend(scan_actions(path, root))
    records.sort(key=lambda item: (item["file"], item["line"], item["category"]))
    categories = sorted(set(item["category"] for item in records))
    return {
        "schema_version": "1.0",
        "record_type": "sage-ac15-source-surface-inventory",
        "scope": "repository-source-only",
        "runtime_isolation_verified": False,
        "live_github_permission_denial_verified": False,
        "non_exhaustive": True,
        "counts": {key: sum(item["category"] == key for item in records)
                   for key in categories},
        "findings": records,
    }


def main() -> int:
    """Print a non-secret inventory; never load tokens or contact GitHub."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_inventory(args.repo.resolve()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
