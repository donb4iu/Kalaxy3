#!/usr/bin/env python3
"""Test the Kalaxy3 centralized-logging runtime validator."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parent.parent
VALIDATOR: Final = ROOT / "scripts/validate-centralized-logging-runtime.py"


def load_validator() -> ModuleType:
    """Load the runtime validator as a Python module."""
    spec = importlib.util.spec_from_file_location(
        "kalaxy3_logging_runtime_validator",
        VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_actionable_failure(module: ModuleType) -> None:
    """Require every standard failure section."""
    message = module.actionable_failure(
        attempted="Attempt",
        detected="State",
        why="Reason",
        intended="Inference",
        confirm="Authority",
        allowed=("Inspect",),
        prohibited=("Bypass",),
        recovery="make target",
        integrity="Preserve evidence",
        gap="Record gap",
    )
    missing = [
        item
        for item in module.REQUIRED_SECTIONS
        if item not in message
    ]
    if missing:
        raise RuntimeError(f"Missing failure sections: {missing}")


def test_expected_releases(module: ModuleType) -> None:
    """Validate centralized-logging chart-lock extraction."""
    lock: dict[str, Any] = {
        "charts": {
            "logging_loki": {
                "release": "loki",
                "version": "18.5.4",
            },
            "logging_collector": {
                "release": "fluent-bit-collector",
                "version": "1.0.9",
            },
            "other": {
                "release": "grafana",
                "version": "1.2.3",
            },
        }
    }
    observed = module.expected_releases(lock)
    expected = {
        "loki": "18.5.4",
        "fluent-bit-collector": "1.0.9",
    }
    if observed != expected:
        raise RuntimeError(
            f"Release extraction mismatch: {observed!r}"
        )


def test_node_label_selection(module: ModuleType) -> None:
    """Validate all-node Loki label selection."""
    nodes = {"arm64-01", "amd64-01"}
    values = {
        "host": {"arm64-01"},
        "node_name": {"arm64-01", "amd64-01"},
    }
    observed = module.select_node_label(
        ("host", "node_name"),
        values,
        nodes,
    )
    if observed != "node_name":
        raise RuntimeError(f"Unexpected node label: {observed!r}")
    missing = module.select_node_label(
        ("host",),
        values,
        nodes,
    )
    if missing is not None:
        raise RuntimeError("Incomplete node coverage was accepted")


def test_vault_tolerant_inventory(
    module: ModuleType,
) -> None:
    """Parse actual inventory without decrypting unrelated secrets."""
    payload = module.load_mapping(module.INVENTORY_PATH)
    active = payload.get("deploy_centralized_logging")
    if active is not True:
        raise RuntimeError(
            f"Unexpected centralized-logging activation gate: {active!r}"
        )


def main() -> int:
    """Run focused runtime-validator regression tests."""
    module = load_validator()
    test_actionable_failure(module)
    test_expected_releases(module)
    test_node_label_selection(module)
    test_vault_tolerant_inventory(module)
    if "centralized_logging.runtime_requires_active_gate" not in module.ACTIONABLE_FAILURE_IDS:
        raise RuntimeError("Runtime failure id is not registered")
    print("PASS vault-tolerant inventory metadata")
    print("Kalaxy3 centralized logging runtime self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
