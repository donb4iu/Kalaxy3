#!/usr/bin/env python3
"""Validate rendered Kalaxy3 Grafana operations ServiceMonitors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

EXPECTED_FAMILIES = {"longhorn": 1, "kubecost": 2}


def require(condition: bool, message: str) -> None:
    """Raise a validation error when a condition is false."""
    if not condition:
        raise ValueError(message)


def load_documents(path: Path) -> list[dict[str, Any]]:
    """Load YAML documents from a rendered manifest."""
    values = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    return [item for item in values if isinstance(item, dict)]


def validate_metadata(document: Mapping[str, Any]) -> str:
    """Validate ServiceMonitor metadata and return its family."""
    metadata = document.get("metadata", {})
    labels = metadata.get("labels", {})
    require(metadata.get("namespace") == "observability", "Wrong namespace")
    require(
        labels.get("release") == "kube-prometheus-stack",
        "Release label missing",
    )
    require(
        labels.get("kalaxy3.io/component") == "grafana-operations",
        "Component label missing",
    )
    family = labels.get("kalaxy3.io/telemetry-family")
    require(family in EXPECTED_FAMILIES, f"Unexpected family: {family}")
    return str(family)


def validate_spec(document: Mapping[str, Any]) -> None:
    """Validate ServiceMonitor selector and endpoint structure."""
    spec = document.get("spec", {})
    namespaces = spec.get("namespaceSelector", {}).get("matchNames", [])
    selector = spec.get("selector", {}).get("matchLabels", {})
    endpoints = spec.get("endpoints", [])
    require(len(namespaces) == 1, "Exactly one target namespace required")
    require(isinstance(selector, dict) and selector, "Selector missing")
    require(len(endpoints) == 1, "Exactly one endpoint required")
    endpoint = endpoints[0]
    require(endpoint.get("path") == "/metrics", "Metrics path mismatch")
    require(endpoint.get("scheme") in ("http", "https"), "Scheme mismatch")
    require(endpoint.get("interval") == "30s", "Interval mismatch")
    require(bool(endpoint.get("port")), "Named port missing")


def validate(path: Path) -> None:
    """Validate all rendered ServiceMonitor documents."""
    documents = load_documents(path)
    require(
        len(documents) == 3,
        f"Expected 3 documents, found {len(documents)}",
    )
    counts = {name: 0 for name in EXPECTED_FAMILIES}
    names: set[str] = set()
    for document in documents:
        require(
            document.get("apiVersion") == "monitoring.coreos.com/v1",
            "Unexpected apiVersion",
        )
        require(document.get("kind") == "ServiceMonitor", "Unexpected kind")
        name = str(document.get("metadata", {}).get("name", ""))
        require(name and name not in names, f"Duplicate or empty name: {name}")
        names.add(name)
        family = validate_metadata(document)
        counts[family] += 1
        validate_spec(document)
    require(counts == EXPECTED_FAMILIES, f"Family counts mismatch: {counts}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run command-line validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    validate(args.manifest)
    print("PASS Grafana operations ServiceMonitor structure")
    print("PASS one Longhorn and two Kubecost monitors")
    print("Kalaxy3 Grafana operations YAML validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
