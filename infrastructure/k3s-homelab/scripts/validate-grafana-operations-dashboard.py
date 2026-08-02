#!/usr/bin/env python3
"""Validate the Kalaxy3 Grafana operations dashboard artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

EXPECTED_UID = "kalaxy3-operations"
EXPECTED_TITLE = "Kalaxy3 Operations"
EXPECTED_PANEL_IDS = set(range(1, 21))
EXPECTED_DATASOURCES = {"prometheus", "loki"}
PENDING_FAMILIES = {"longhorn", "kubecost"}


def require(condition: bool, message: str) -> None:
    """Raise a validation error when a condition is false."""
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


def load_manifest(path: Path) -> dict[str, Any]:
    """Load one YAML manifest object."""
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Manifest object required")
    return value


def embedded_dashboard(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Load the dashboard JSON embedded in the ConfigMap."""
    require(manifest.get("apiVersion") == "v1", "Wrong apiVersion")
    require(manifest.get("kind") == "ConfigMap", "Wrong resource kind")
    metadata = manifest.get("metadata", {})
    labels = metadata.get("labels", {})
    require(metadata.get("namespace") == "observability", "Wrong namespace")
    require(labels.get("grafana_dashboard") == "1", "Sidecar label missing")
    require(
        labels.get("kalaxy3.io/component") == "grafana-operations",
        "Component label missing",
    )
    text = manifest.get("data", {}).get("kalaxy3-operations.json")
    require(isinstance(text, str) and text, "Dashboard data missing")
    value = json.loads(text)
    require(isinstance(value, dict), "Embedded dashboard must be an object")
    return value


def query_metric_coverage(panel: Mapping[str, Any]) -> None:
    """Require every declared metric name to occur in its query."""
    query = str(panel.get("query", ""))
    metrics = panel.get("required_metrics", [])
    require(query, "Panel query missing")
    require(isinstance(metrics, list), "Required metrics must be a list")
    for metric in metrics:
        require(str(metric) in query, f"Metric not used by query: {metric}")


def validate_contract(contract: Mapping[str, Any]) -> None:
    """Validate the machine-readable dashboard contract."""
    dashboard = contract.get("dashboard", {})
    require(dashboard.get("uid") == EXPECTED_UID, "Contract UID mismatch")
    require(dashboard.get("title") == EXPECTED_TITLE, "Title mismatch")
    datasources = set(contract.get("datasources", {}).values())
    require(datasources == EXPECTED_DATASOURCES, "Datasource mismatch")
    deployment = contract.get("deployment", {})
    require(
        deployment.get("current_staged_value") is False,
        "Deployment gate must remain false",
    )
    panels = contract.get("panels", [])
    ids = {item.get("id") for item in panels}
    require(ids == EXPECTED_PANEL_IDS, f"Contract panel IDs: {ids}")
    for panel in panels:
        query_metric_coverage(panel)
        if panel.get("family") in PENDING_FAMILIES:
            require(
                panel.get("validation_stage")
                == "syntax-only-before-activation",
                "Pending panel validation stage mismatch",
            )


def dashboard_query_map(
    dashboard: Mapping[str, Any],
) -> dict[int, tuple[str, str]]:
    """Return panel query and datasource values by panel ID."""
    result: dict[int, tuple[str, str]] = {}
    for panel in dashboard.get("panels", []):
        panel_id = panel.get("id")
        if panel_id not in EXPECTED_PANEL_IDS:
            continue
        targets = panel.get("targets", [])
        require(len(targets) == 1, f"One target required: {panel_id}")
        item = targets[0]
        query = str(item.get("expr", ""))
        uid = str(item.get("datasource", {}).get("uid", ""))
        result[int(panel_id)] = (query, uid)
    return result


def validate_dashboard(
    contract: Mapping[str, Any],
    dashboard: Mapping[str, Any],
) -> None:
    """Validate dashboard identity and contract consistency."""
    require(dashboard.get("uid") == EXPECTED_UID, "Dashboard UID mismatch")
    require(dashboard.get("title") == EXPECTED_TITLE, "Title mismatch")
    require(dashboard.get("editable") is False, "Dashboard must be immutable")
    require(dashboard.get("refresh") == "30s", "Refresh mismatch")
    query_map = dashboard_query_map(dashboard)
    require(set(query_map) == EXPECTED_PANEL_IDS, "Panel IDs mismatch")
    for panel in contract.get("panels", []):
        panel_id = int(panel["id"])
        query, uid = query_map[panel_id]
        require(query == panel["query"], f"Query mismatch: {panel_id}")
        require(uid == panel["datasource_uid"], f"UID mismatch: {panel_id}")


def validate(contract_path: Path, manifest_path: Path) -> None:
    """Validate the complete dashboard artifact pair."""
    contract = load_json(contract_path)
    manifest = load_manifest(manifest_path)
    dashboard = embedded_dashboard(manifest)
    validate_contract(contract)
    validate_dashboard(contract, dashboard)


def main(arguments: Sequence[str] | None = None) -> int:
    """Run command-line dashboard validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(arguments)
    validate(args.contract, args.manifest)
    print("PASS dashboard identity and sidecar ConfigMap")
    print("PASS 20 panel queries match the repository contract")
    print("PASS Longhorn and Kubecost remain pre-activation panels")
    print("Kalaxy3 Grafana operations dashboard validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
