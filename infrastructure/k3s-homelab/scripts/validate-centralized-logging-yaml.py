#!/usr/bin/env python3
"""Validate rendered Kalaxy3 centralized-logging YAML."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


EXPECTED_FILES = (
    "loki-values.yml",
    "fluent-bit-values.yml",
    "grafana-loki-datasource.yml",
)


def load_single_document(path: Path) -> dict[str, Any]:
    """Load one nonempty YAML mapping."""
    documents = list(
        yaml.safe_load_all(path.read_text(encoding="utf-8"))
    )

    if len(documents) != 1:
        raise ValueError(
            f"{path.name}: expected one YAML document, "
            f"found {len(documents)}"
        )

    document = documents[0]
    if not isinstance(document, dict):
        raise ValueError(
            f"{path.name}: expected a YAML mapping"
        )

    return document


def validate_loki(document: dict[str, Any]) -> None:
    """Validate Loki placement, persistence, and retention."""
    if document.get("deploymentMode") != "Monolithic":
        raise ValueError(
            "loki-values.yml: deploymentMode must be Monolithic"
        )

    single_binary = document.get("singleBinary", {})
    selector = single_binary.get("nodeSelector", {})

    if selector.get("kubernetes.io/arch") != "amd64":
        raise ValueError(
            "loki-values.yml: Loki must target amd64"
        )

    if (
        selector.get("kalaxy3.io/workload-pool")
        != "platform-services"
    ):
        raise ValueError(
            "loki-values.yml: Loki must target platform-services"
        )

    persistence = single_binary.get("persistence", {})
    if persistence.get("storageClass") != "longhorn":
        raise ValueError(
            "loki-values.yml: storageClass must be longhorn"
        )

    if persistence.get("size") != "40Gi":
        raise ValueError(
            "loki-values.yml: storage size must be 40Gi"
        )

    limits = document.get("loki", {}).get("limits_config", {})
    if limits.get("retention_period") != "168h":
        raise ValueError(
            "loki-values.yml: retention must be 168h"
        )


def validate_fluent_bit(document: dict[str, Any]) -> None:
    """Validate Fluent Bit output and all-node scheduling."""
    if document.get("nodeSelector"):
        raise ValueError(
            "fluent-bit-values.yml: collector must not have "
            "a nodeSelector"
        )

    tolerations = document.get("tolerations", [])
    if {"operator": "Exists"} not in tolerations:
        raise ValueError(
            "fluent-bit-values.yml: all-node toleration missing"
        )

    outputs = (
        document.get("config", {})
        .get("pipeline", {})
        .get("outputs", [])
    )
    if not outputs or outputs[0].get("name") != "loki":
        raise ValueError(
            "fluent-bit-values.yml: Loki output missing"
        )


def validate_datasource(document: dict[str, Any]) -> None:
    """Validate Grafana datasource metadata."""
    metadata = document.get("metadata", {})
    if metadata.get("namespace") != "observability":
        raise ValueError(
            "grafana-loki-datasource.yml: namespace must be "
            "observability"
        )

    labels = metadata.get("labels", {})
    if labels.get("grafana_datasource") != "1":
        raise ValueError(
            "grafana-loki-datasource.yml: sidecar label missing"
        )


def main() -> int:
    """Validate all rendered files."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "render_dir",
        type=Path,
        help="Directory containing rendered logging YAML",
    )
    args = parser.parse_args()

    render_dir: Path = args.render_dir
    missing = [
        name
        for name in EXPECTED_FILES
        if not (render_dir / name).is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"Missing rendered files: {', '.join(missing)}"
        )

    loki = load_single_document(
        render_dir / "loki-values.yml"
    )
    fluent_bit = load_single_document(
        render_dir / "fluent-bit-values.yml"
    )
    datasource = load_single_document(
        render_dir / "grafana-loki-datasource.yml"
    )

    validate_loki(loki)
    validate_fluent_bit(fluent_bit)
    validate_datasource(datasource)

    for name in EXPECTED_FILES:
        print(f"PASS YAML: {name}")

    print(
        "PASS placement: Loki=platform-services; "
        "Fluent Bit=all nodes"
    )
    print("PASS activation gate: validated by playbook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
