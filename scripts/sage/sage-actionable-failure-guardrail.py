#!/usr/bin/env python3
"""Guard the Kalaxy3 actionable-failure framework and catalog."""

from __future__ import annotations

import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Final

from sage_actionable_failure import (
    ActionableFailureError,
    load_catalog,
    parse_entry,
    validate_catalog,
)

ROOT: Final = Path(__file__).resolve().parents[2]
CATALOG: Final = ROOT / "sage-actionable-failures.json"
REGISTRY: Final = ROOT / "sage-actionable-failure-registry.json"
VALID_STATUSES: Final = {"planned", "migrated", "exempt"}


def load_mapping(path: Path) -> dict[str, Any]:
    """Load one required JSON mapping."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ActionableFailureError(f"{path}: expected a mapping")
    return payload


def make_target(command: str) -> str | None:
    """Extract one Make target from a shell-like command."""
    tokens = shlex.split(command)
    try:
        index = tokens.index("make")
    except ValueError:
        return None
    for token in tokens[index + 1:]:
        if "=" not in token and not token.startswith("-"):
            return token
    return None


def target_exists(directory: Path, target: str) -> bool:
    """Return whether a Makefile declares the requested target."""
    makefile = directory / "Makefile"
    if not makefile.is_file():
        return False
    pattern = re.compile(
        rf"^{re.escape(target)}(?:\s+[^:]*)?:",
        re.MULTILINE,
    )
    return pattern.search(makefile.read_text(encoding="utf-8")) is not None


def validate_recovery(
    failure_id: str,
    entry: dict[str, Any],
) -> None:
    """Validate recovery paths and Make targets for one failure."""
    failure = parse_entry(entry)
    for step in failure.canonical_recovery:
        directory = (ROOT / step.working_directory).resolve()
        if not directory.is_dir():
            raise ActionableFailureError(
                f"{failure_id}: recovery directory missing: {directory}"
            )
        for relative in step.required_paths:
            if not (ROOT / relative).exists():
                raise ActionableFailureError(
                    f"{failure_id}: required recovery path missing: "
                    f"{relative}"
                )
        target = make_target(step.command)
        if target and not target_exists(directory, target):
            raise ActionableFailureError(
                f"{failure_id}: Make target does not exist: "
                f"{step.working_directory}:{target}"
            )
    for relative in failure.authoritative_paths:
        if not (ROOT / relative).exists():
            raise ActionableFailureError(
                f"{failure_id}: authoritative path missing: {relative}"
            )


def validate_registry(
    registry: dict[str, Any],
    failures: dict[str, Any],
) -> None:
    """Validate validator registration and migrated integration."""
    validators = registry.get("validators")
    if not isinstance(validators, list) or not validators:
        raise ActionableFailureError("Registry requires validators")
    seen: set[str] = set()
    for item in validators:
        validate_registry_item(item, failures, seen)


def validate_registry_item(
    item: Any,
    failures: dict[str, Any],
    seen: set[str],
) -> None:
    """Validate one registered validator."""
    if not isinstance(item, dict):
        raise ActionableFailureError("Registry item must be a mapping")
    path = item.get("path")
    status = item.get("status")
    failure_ids = item.get("failure_ids")
    if not isinstance(path, str) or not path:
        raise ActionableFailureError("Registry path is required")
    if path in seen:
        raise ActionableFailureError(f"Duplicate registry path: {path}")
    seen.add(path)
    if not (ROOT / path).is_file():
        raise ActionableFailureError(f"Registered validator missing: {path}")
    if status not in VALID_STATUSES:
        raise ActionableFailureError(f"{path}: invalid status {status!r}")
    if not isinstance(failure_ids, list) or not failure_ids:
        raise ActionableFailureError(f"{path}: failure_ids are required")
    for failure_id in failure_ids:
        if failure_id not in failures:
            raise ActionableFailureError(
                f"{path}: unknown failure id {failure_id}"
            )
    if status == "migrated":
        text = (ROOT / path).read_text(encoding="utf-8")
        missing = [value for value in failure_ids if value not in text]
        if missing:
            raise ActionableFailureError(
                f"{path}: migrated ids missing: {', '.join(missing)}"
            )


def require_framework_targets() -> None:
    """Require root self-test, guardrail, and audit entry points."""
    for target in (
        "sage-actionable-failure-self-test",
        "sage-actionable-failure-guardrail",
        "sage-actionable-failure-audit",
    ):
        if not target_exists(ROOT, target):
            raise ActionableFailureError(
                f"Root Make target is missing: {target}"
            )


def main() -> int:
    """Validate the reusable actionable-failure capability."""
    try:
        catalog = load_catalog(CATALOG)
        validate_catalog(catalog)
        failures = catalog["failures"]
        for failure_id, entry in failures.items():
            validate_recovery(failure_id, entry)
        registry = load_mapping(REGISTRY)
        validate_registry(registry, failures)
        require_framework_targets()
    except (
        ActionableFailureError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    print("PASS actionable-failure catalog and recovery authority")
    print("PASS actionable-failure validator registry")
    print("PASS actionable-failure Make entry points")
    print("Kalaxy3 SAGE actionable-failure guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
