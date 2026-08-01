#!/usr/bin/env python3
"""Test centralized-logging validator contracts in source-only CI."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

HOMELAB_ROOT: Final = Path(__file__).resolve().parent.parent
REPO_ROOT: Final = HOMELAB_ROOT.parents[1]
VALIDATOR: Final = (
    HOMELAB_ROOT
    / "scripts/validate-centralized-logging-runtime.py"
)

sys.path.insert(0, str(REPO_ROOT / "scripts/sage"))


def load_validator() -> ModuleType:
    """Import the runtime validator without operator-only dependencies."""
    if "yaml" in sys.modules:
        raise RuntimeError(
            "Source-only test started with unexpected PyYAML state"
        )
    spec = importlib.util.spec_from_file_location(
        "kalaxy3_logging_runtime_source_contract",
        VALIDATOR,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load validator: {VALIDATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if "yaml" in sys.modules:
        raise RuntimeError(
            "Runtime-validator import eagerly loaded PyYAML"
        )
    return module


def test_expected_releases(module: ModuleType) -> None:
    """Validate chart-lock interpretation without a live cluster."""
    lock: dict[str, Any] = {
        "charts": {
            "loki": {
                "release": "loki",
                "version": "18.5.4",
            },
            "collector": {
                "release": "fluent-bit-collector",
                "version": "1.0.9",
            },
        }
    }
    expected = {
        "loki": "18.5.4",
        "fluent-bit-collector": "1.0.9",
    }
    observed = module.expected_releases(lock)
    if observed != expected:
        raise RuntimeError(f"Unexpected release mapping: {observed}")


def test_node_label_selection(module: ModuleType) -> None:
    """Validate the repository's actual all-node label-selection API."""
    function = getattr(module, "select_node_label", None)
    if not callable(function):
        raise RuntimeError("Runtime validator select_node_label is missing")

    import inspect

    parameters = tuple(inspect.signature(function).parameters)
    expected_parameters = ("candidates", "values", "nodes")
    if parameters != expected_parameters:
        raise RuntimeError(
            "Unexpected select_node_label signature: "
            f"{parameters}; expected {expected_parameters}"
        )

    nodes = {"arm64-01", "amd64-01"}
    candidates = ("node_name", "node")
    values = {
        "filename": {"/var/log/a", "/var/log/b"},
        "node": {"arm64-01", "amd64-01"},
    }
    observed = function(candidates, values, nodes)
    if observed != "node":
        raise RuntimeError(
            f"Complete node label was not selected: {observed!r}"
        )

    incomplete = function(
        candidates,
        {"node": {"arm64-01"}},
        nodes,
    )
    if incomplete is not None:
        raise RuntimeError("Incomplete node coverage was accepted")



def test_lazy_metadata_contract() -> None:
    """Require metadata helpers to remain importable without PyYAML."""
    from sage_yaml_metadata import require_plain_bool

    if require_plain_bool({"enabled": True}, "enabled") is not True:
        raise RuntimeError("Plain boolean metadata was not preserved")
    if "yaml" in sys.modules:
        raise RuntimeError(
            "Non-parsing metadata contract loaded PyYAML"
        )


def test_runtime_entry_points(module: ModuleType) -> None:
    """Require the live validator entry points to remain present."""
    required = {
        "main",
        "validate_runtime",
        "validate_loki_data",
        "require_active_gate",
        "load_mapping",
    }
    missing = sorted(
        name for name in required
        if not callable(getattr(module, name, None))
    )
    if missing:
        raise RuntimeError(
            f"Runtime validator entry points missing: {missing}"
        )


def main() -> int:
    """Run source-only validator contract tests."""
    module = load_validator()
    test_expected_releases(module)
    test_node_label_selection(module)
    test_lazy_metadata_contract()
    test_runtime_entry_points(module)
    print("PASS runtime validator source-only import without PyYAML")
    print("PASS locked-release interpretation")
    print("PASS dynamic all-node label selection")
    print("PASS live runtime entry-point contract")
    print(
        "Kalaxy3 centralized logging source-only self-test: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
