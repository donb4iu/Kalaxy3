#!/usr/bin/env python3
"""Test the reusable Kalaxy3 SAGE actionable-failure framework."""

from __future__ import annotations

import copy
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
MODULE_PATH: Final = ROOT / "scripts/sage/sage_actionable_failure.py"
CATALOG_PATH: Final = ROOT / "sage-actionable-failures.json"
REQUIRED_SECTIONS: Final = (
    "SAGE ACTION BLOCKED",
    "Attempted action",
    "Detected state",
    "Why this is invalid",
    "Likely intended outcome",
    "Confirm the correct approach",
    "Allowed actions",
    "Prohibited actions",
    "Canonical recovery",
    "SAGE integrity requirements",
    "Repository gap",
)


def load_module() -> ModuleType:
    """Load the shared actionable-failure module."""
    spec = importlib.util.spec_from_file_location(
        "kalaxy3_sage_actionable_failure",
        MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_sections(message: str) -> None:
    """Require the complete rendered failure contract."""
    missing = [item for item in REQUIRED_SECTIONS if item not in message]
    if missing:
        raise RuntimeError(f"Rendered failure is missing: {missing}")


def test_real_catalog(module: ModuleType) -> None:
    """Render both original incident failures from the real catalog."""
    catalog = module.load_catalog(CATALOG_PATH)
    module.validate_catalog(catalog)
    values = {
        "centralized_logging.unmanaged_controller_interpreter": {
            "ansible_playbook_python": "/usr/local/bin/python"
        },
        "centralized_logging.render_validator_after_activation": {
            "deploy_centralized_logging": "true"
        },
    }
    for failure_id, variables in values.items():
        failure = module.catalog_failure(
            catalog, failure_id, variables
        )
        require_sections(module.render_failure(failure))


def test_missing_variable(module: ModuleType) -> None:
    """Reject rendering when detected-state variables are absent."""
    catalog = module.load_catalog(CATALOG_PATH)
    try:
        module.catalog_failure(
            catalog,
            "centralized_logging.unmanaged_controller_interpreter",
            {},
        )
    except module.ActionableFailureError:
        return
    raise RuntimeError("Missing template variable was accepted")


def test_negative_catalog_mutation(module: ModuleType) -> None:
    """Reject a catalog entry with missing recovery authority."""
    catalog: dict[str, Any] = module.load_catalog(CATALOG_PATH)
    mutation = copy.deepcopy(catalog)
    entry = next(iter(mutation["failures"].values()))
    del entry["prohibited_actions"]
    try:
        module.validate_catalog(mutation)
    except module.ActionableFailureError:
        return
    raise RuntimeError("Invalid catalog mutation was accepted")


def test_validator_runtime_failure(module: ModuleType) -> None:
    """Exercise the generic validator-runtime failure model."""
    failure = module.validator_runtime_failure(
        validator_id="sage.self_test",
        attempted_action="Validate the SAGE failure framework.",
        command=(sys.executable, "-c", "raise RuntimeError('boom')"),
        exit_code=1,
        error_summary="RuntimeError: boom",
        working_directory=".",
        recovery_command=(
            "python3 scripts/sage/sage-actionable-failure-self-test.py"
        ),
        authoritative_paths=(
            "scripts/sage/sage-actionable-failure-self-test.py",
        ),
        integrity_requirements=(
            "Preserve the traceback as regression evidence.",
        ),
    )
    message = module.render_failure(failure)
    require_sections(message)
    for marker in (
        "RuntimeError: boom",
        "Do not treat py_compile as sufficient",
        "validator-bootstrap or dependency gap",
    ):
        if marker not in message:
            raise RuntimeError(
                f"Validator runtime failure is missing {marker!r}"
            )


def test_validator_runner_entry_path() -> None:
    """Exercise the actual subprocess failure and rendering path."""
    command = (
        sys.executable,
        str(ROOT / "scripts/sage/sage-validator-runner.py"),
        "--validator-id",
        "sage.dynamic_import_regression",
        "--attempted-action",
        "Exercise a validator runtime path.",
        "--working-directory",
        ".",
        "--recovery-command",
        "python3 scripts/sage/sage-actionable-failure-self-test.py",
        "--authoritative-path",
        "scripts/sage/sage-actionable-failure-self-test.py",
        "--",
        sys.executable,
        "-c",
        "raise RuntimeError('simulated dataclass bootstrap failure')",
    )
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 2:
        raise RuntimeError(
            f"Validator runner returned {result.returncode}, expected 2"
        )
    require_sections(result.stderr)
    for marker in (
        "simulated dataclass bootstrap failure",
        "SAGE ACTION BLOCKED",
        "Do not report a pass",
    ):
        if marker not in result.stderr:
            raise RuntimeError(
                f"Validator runner output is missing {marker!r}"
            )

def main() -> int:
    """Run reusable actionable-failure regression tests."""
    module = load_module()
    test_real_catalog(module)
    test_missing_variable(module)
    test_negative_catalog_mutation(module)
    test_validator_runtime_failure(module)
    test_validator_runner_entry_path()
    print("PASS reusable actionable-failure renderer")
    print("PASS original incident regression cases")
    print("PASS actionable-failure negative mutation tests")
    print("PASS validator bootstrap/runtime failure regression")
    print("Kalaxy3 SAGE actionable failure self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
