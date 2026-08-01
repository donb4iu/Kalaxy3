#!/usr/bin/env python3
"""Audit Kalaxy3 validator coverage by the actionable-failure framework."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
REGISTRY: Final = ROOT / "sage-actionable-failure-registry.json"
FRAMEWORK_PATHS: Final = {
    "scripts/sage/sage_actionable_failure.py",
    "scripts/sage/sage-actionable-failure-audit.py",
    "scripts/sage/sage-actionable-failure-guardrail.py",
    "scripts/sage/sage-actionable-failure-self-test.py",
    "scripts/sage/sage-validator-runner.py",
}
CANDIDATE_SUFFIXES: Final = {".py", ".yml", ".yaml", ".sh"}
PATTERNS: Final = (
    re.compile(r"\bansible\.builtin\.(?:assert|fail)\b"),
    re.compile(r"\bfail_msg\s*:"),
    re.compile(r"\braise\s+(?:RuntimeError|ValueError|SystemExit)\b"),
    re.compile(r"\bsys\.exit\s*\("),
    re.compile(r"\bexit\s+[1-9]\b"),
)


def tracked_files() -> list[Path]:
    """Return tracked repository files that can contain validators."""
    output = subprocess.run(
        ("git", "ls-files"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    files: list[Path] = []
    for relative in output.splitlines():
        path = ROOT / relative
        if path.name == "Makefile" or path.suffix in CANDIDATE_SUFFIXES:
            files.append(path)
    return files


def is_candidate(path: Path) -> bool:
    """Return whether one tracked file contains failure-like behavior."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    return any(pattern.search(text) for pattern in PATTERNS)


def registered_paths() -> dict[str, str]:
    """Return registered validator paths and migration states."""
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    validators = payload.get("validators", [])
    if not isinstance(validators, list):
        raise RuntimeError("Actionable-failure registry is invalid")
    return {
        str(item["path"]): str(item["status"])
        for item in validators
        if isinstance(item, dict)
    }


def build_report() -> dict[str, Any]:
    """Build the current actionable-failure coverage report."""
    candidates = sorted(
        str(path.relative_to(ROOT))
        for path in tracked_files()
        if is_candidate(path)
        and str(path.relative_to(ROOT)) not in FRAMEWORK_PATHS
    )
    registry = registered_paths()
    migrated = sorted(
        path for path, status in registry.items() if status == "migrated"
    )
    planned = sorted(
        path for path, status in registry.items() if status == "planned"
    )
    return {
        "candidate_count": len(candidates),
        "registered_count": len(registry),
        "migrated_count": len(migrated),
        "planned_count": len(planned),
        "unregistered_candidates": [
            path for path in candidates if path not in registry
        ],
        "migrated": migrated,
        "planned": planned,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse audit output options."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def print_summary(report: dict[str, Any]) -> None:
    """Print a concise human-readable coverage summary."""
    print("Kalaxy3 actionable-failure coverage audit")
    for key in (
        "candidate_count",
        "registered_count",
        "migrated_count",
        "planned_count",
    ):
        print(f"{key}: {report[key]}")
    unregistered = report["unregistered_candidates"]
    print(f"unregistered_count: {len(unregistered)}")
    if unregistered:
        print("Unregistered validator candidates:")
        for path in unregistered[:30]:
            print(f"  - {path}")
        if len(unregistered) > 30:
            print(f"  - ... {len(unregistered) - 30} more")


def main() -> int:
    """Audit actionable-failure adoption without hiding gaps."""
    arguments = parse_arguments()
    report = build_report()
    if arguments.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_summary(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
