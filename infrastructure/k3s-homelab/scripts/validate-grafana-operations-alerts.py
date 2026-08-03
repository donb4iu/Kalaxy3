#!/usr/bin/env python3
"""Validate Kalaxy3 Grafana operations recording and alert rules."""

from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

EXPECTED_RECORDS: Mapping[str, Mapping[str, str]] = {
    "kalaxy3:fluent_bit_coverage_ratio": {
        "expr": 'sum(up{job="fluent-bit-collector"}) / 7',
        "component": "logging",
        "slo": "fluent-bit-coverage",
        "objective": "1",
    },
    "kalaxy3:loki_workload_ready_ratio": {
        "expr_contains": "kube_statefulset_status_replicas_ready",
        "component": "logging",
        "slo": "loki-workload-availability",
        "objective": "1",
    },
}

EXPECTED_ALERTS: Mapping[str, Mapping[str, str]] = {
    "FluentBitCoverageDegraded": {
        "expr_contains": "kalaxy3:fluent_bit_coverage_ratio < 1",
        "for": "10m",
        "severity": "warning",
        "component": "logging",
        "slo": "fluent-bit-coverage",
        "objective": "1",
    },
    "LokiWorkloadAvailabilityDegraded": {
        "expr_contains": "kalaxy3:loki_workload_ready_ratio < 1",
        "for": "10m",
        "severity": "warning",
        "component": "logging",
        "slo": "loki-workload-availability",
        "objective": "1",
    },
    "LonghornStorageUtilizationHigh": {
        "expr_contains": "longhorn_node_storage_usage_bytes",
        "for": "15m",
        "severity": "warning",
        "component": "storage",
    },
}

LABEL_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def require(condition: bool, message: str) -> None:
    """Raise when validation fails."""
    if not condition:
        raise ValueError(message)


def load_manifest(path: Path) -> dict[str, Any]:
    """Load one PrometheusRule manifest."""
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "Manifest object required")
    return payload


def validate_metadata(payload: Mapping[str, Any]) -> None:
    """Validate resource identity and selection labels."""
    require(
        payload.get("apiVersion") == "monitoring.coreos.com/v1",
        "apiVersion mismatch",
    )
    require(payload.get("kind") == "PrometheusRule", "Kind mismatch")
    metadata = payload.get("metadata", {})
    labels = metadata.get("labels", {})
    require(
        metadata.get("name") == "kalaxy3-grafana-operations-alerts",
        "Name mismatch",
    )
    require(metadata.get("namespace") == "observability", "Namespace mismatch")
    require(
        labels.get("release") == "kube-prometheus-stack",
        "Release label missing",
    )
    require(
        labels.get("kalaxy3.io/component") == "grafana-operations",
        "Component label missing",
    )


def rules(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the single validated rule group."""
    groups = payload.get("spec", {}).get("groups", [])
    require(len(groups) == 1, "Expected one rule group")
    group = groups[0]
    require(
        group.get("name") == "kalaxy3-grafana-operations.rules",
        "Rule group name mismatch",
    )
    require(group.get("interval") == "30s", "Interval mismatch")
    values = group.get("rules", [])
    require(len(values) == 5, "Expected five rules")
    return [dict(item) for item in values]


def validate_labels(
    labels: Mapping[str, Any],
    expected: Mapping[str, str],
    name: str,
) -> None:
    """Validate required rule labels."""
    invalid = sorted(
        str(key)
        for key in labels
        if not LABEL_PATTERN.fullmatch(str(key))
    )
    require(not invalid, f"Invalid labels for {name}: {invalid}")
    for key in ("component", "slo", "objective", "severity"):
        if key in expected:
            require(labels.get(key) == expected[key], f"{key}: {name}")


def validate_record(
    name: str,
    rule: Mapping[str, Any],
    expected: Mapping[str, str],
) -> None:
    """Validate one SLO recording rule."""
    expression = str(rule.get("expr", ""))
    if "expr" in expected:
        require(expression == expected["expr"], f"Expression: {name}")
    if "expr_contains" in expected:
        require(
            expected["expr_contains"] in expression,
            f"Expression fragment: {name}",
        )
    validate_labels(rule.get("labels", {}), expected, name)


def validate_alert(
    name: str,
    rule: Mapping[str, Any],
    expected: Mapping[str, str],
) -> None:
    """Validate one actionable alert."""
    expression = str(rule.get("expr", ""))
    require(
        expected["expr_contains"] in expression,
        f"Expression fragment: {name}",
    )
    require(rule.get("for") == expected["for"], f"Duration: {name}")
    validate_labels(rule.get("labels", {}), expected, name)
    annotations = rule.get("annotations", {})
    require(bool(annotations.get("summary")), f"Summary: {name}")
    require(bool(annotations.get("description")), f"Description: {name}")


def validate(payload: Mapping[str, Any]) -> None:
    """Validate the complete recording and alert contract."""
    validate_metadata(payload)
    values = rules(payload)
    records = {
        str(item.get("record")): item
        for item in values
        if item.get("record")
    }
    alerts = {
        str(item.get("alert")): item
        for item in values
        if item.get("alert")
    }
    require(set(records) == set(EXPECTED_RECORDS), "Recording-rule set")
    require(set(alerts) == set(EXPECTED_ALERTS), "Alert-rule set")
    for name, expected in EXPECTED_RECORDS.items():
        validate_record(name, records[name], expected)
    for name, expected in EXPECTED_ALERTS.items():
        validate_alert(name, alerts[name], expected)


def expect_failure(payload: Mapping[str, Any], label: str) -> None:
    """Require one mutated fixture to fail."""
    try:
        validate(payload)
    except ValueError:
        return
    raise ValueError(f"Negative test passed: {label}")


def self_test(payload: Mapping[str, Any]) -> None:
    """Run focused mutation tests."""
    validate(payload)
    renamed = copy.deepcopy(payload)
    renamed["spec"]["groups"][0]["rules"][0]["record"] = "wrong:record"
    expect_failure(renamed, "record name")
    severity = copy.deepcopy(payload)
    severity["spec"]["groups"][0]["rules"][2]["labels"]["severity"] = "info"
    expect_failure(severity, "alert severity")
    objective = copy.deepcopy(payload)
    del objective["spec"]["groups"][0]["rules"][3]["labels"]["objective"]
    expect_failure(objective, "SLO objective")
    expression = copy.deepcopy(payload)
    expression["spec"]["groups"][0]["rules"][4]["expr"] = "vector(0)"
    expect_failure(expression, "storage expression")


def main(arguments: Sequence[str] | None = None) -> int:
    """Run command-line validation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(arguments)
    payload = load_manifest(args.manifest)
    self_test(payload) if args.self_test else validate(payload)
    if args.self_test:
        print("PASS recording and alert mutation negative tests")
    print("PASS PrometheusRule identity and selection labels")
    print("PASS two SLO recording rules and three actionable alerts")
    print("Kalaxy3 Grafana operations alert validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
