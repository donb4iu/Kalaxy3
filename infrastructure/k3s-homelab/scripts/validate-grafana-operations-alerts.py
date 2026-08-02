#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

EXPECTED: Mapping[str, Mapping[str, str]] = {
    "FluentBitCoverageDegraded": {
        "expr": (
            'sum(up{job="fluent-bit-collector"}) < 7 '
            'or absent(up{job="fluent-bit-collector"})'
        ),
        "for": "10m",
        "severity": "warning",
        "component": "logging",
    },
    "LonghornStorageUtilizationHigh": {
        "expr": (
            "100 * sum(longhorn_node_storage_usage_bytes) "
            "/ sum(longhorn_node_storage_capacity_bytes) > 80"
        ),
        "for": "15m",
        "severity": "warning",
        "component": "storage",
    },
}

LABEL_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def require(condition: bool, message: str) -> None:
    "Raise when validation fails."
    if not condition:
        raise ValueError(message)


def load_manifest(path: Path) -> dict[str, Any]:
    "Load one PrometheusRule manifest."
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(isinstance(payload, dict), "Manifest object required")
    return payload


def rules_by_name(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    "Return alert rules indexed by name."
    groups = payload.get("spec", {}).get("groups", [])
    require(len(groups) == 1, "Expected one rule group")
    group = groups[0]
    require(
        group.get("name") == "kalaxy3-grafana-operations.rules",
        "Rule group name mismatch",
    )
    require(group.get("interval") == "30s", "Interval mismatch")
    rules = group.get("rules", [])
    require(len(rules) == 2, "Expected two rules")
    return {str(item.get("alert")): dict(item) for item in rules}


def validate_metadata(payload: Mapping[str, Any]) -> None:
    "Validate resource identity and selection labels."
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


def validate_rule(
    name: str,
    rule: Mapping[str, Any],
    expected: Mapping[str, str],
) -> None:
    "Validate one alert rule."
    require(rule.get("expr") == expected["expr"], f"Expression: {name}")
    require(rule.get("for") == expected["for"], f"Duration: {name}")
    labels = rule.get("labels", {})
    annotations = rule.get("annotations", {})
    invalid_labels = sorted(
        str(key)
        for key in labels
        if not LABEL_NAME_PATTERN.fullmatch(str(key))
    )
    require(not invalid_labels, f"Invalid label names: {invalid_labels}")
    require(
        labels.get("severity") == expected["severity"],
        f"Severity: {name}",
    )
    require(
        labels.get("component") == expected["component"],
        f"Component: {name}",
    )
    require(bool(annotations.get("summary")), f"Summary: {name}")
    require(bool(annotations.get("description")), f"Description: {name}")


def validate(payload: Mapping[str, Any]) -> None:
    "Validate the complete PrometheusRule."
    validate_metadata(payload)
    rules = rules_by_name(payload)
    require(set(rules) == set(EXPECTED), "Alert-name set mismatch")

    for name, expected in EXPECTED.items():
        validate_rule(name, rules[name], expected)


def expect_failure(payload: Mapping[str, Any], label: str) -> None:
    "Require one mutated fixture to fail."
    try:
        validate(payload)
    except ValueError:
        return
    raise ValueError(f"Negative test passed: {label}")


def self_test(payload: Mapping[str, Any]) -> None:
    "Run focused mutation tests."
    validate(payload)

    renamed = copy.deepcopy(payload)
    renamed["spec"]["groups"][0]["rules"][0]["alert"] = "WrongName"
    expect_failure(renamed, "name")

    severity = copy.deepcopy(payload)
    severity["spec"]["groups"][0]["rules"][0]["labels"]["severity"] = "info"
    expect_failure(severity, "severity")

    expression = copy.deepcopy(payload)
    expression["spec"]["groups"][0]["rules"][1]["expr"] = "vector(0)"
    expect_failure(expression, "expression")


def main(arguments: Sequence[str] | None = None) -> int:
    "Run command-line validation."
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(arguments)
    payload = load_manifest(args.manifest)

    if args.self_test:
        self_test(payload)
        print("PASS PrometheusRule mutation negative tests")
    else:
        validate(payload)

    print("PASS PrometheusRule identity and selection labels")
    print("PASS two alert expressions, durations, and severities")
    print("Kalaxy3 Grafana operations alert validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        raise SystemExit(2)
