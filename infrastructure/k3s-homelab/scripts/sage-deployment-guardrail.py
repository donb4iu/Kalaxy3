#!/usr/bin/env python3
"""Fail closed unless enabled Helm operations are fully repository-locked."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def enabled_variables() -> dict[str, bool]:
    text = (
        ROOT / "inventory/group_vars/all/main.yml"
    ).read_text(encoding="utf-8")
    values: dict[str, bool] = {}
    for name, raw in re.findall(
        r"(?m)^([A-Za-z_][A-Za-z0-9_]*):\s*(true|false)\s*$",
        text,
        flags=re.IGNORECASE,
    ):
        values[name] = raw.lower() == "true"
    return values


def exact_version(value: str) -> bool:
    return (
        value not in {"", "UNRESOLVED", "latest", "stable"}
        and re.fullmatch(
            r"[0-9]+(?:\.[0-9]+)+(?:[-+][0-9A-Za-z.-]+)?",
            value,
        )
        is not None
    )


def task_blocks(text: str) -> list[str]:
    starts = [
        match.start()
        for match in re.finditer(r"(?m)^\s*-\s+name:", text)
    ]
    if not starts:
        return []
    starts.append(len(text))
    return [
        text[starts[index] : starts[index + 1]]
        for index in range(len(starts) - 1)
    ]


def helm_operation(block: str) -> bool:
    command_operation = (
        "{{ helm_binary }}" in block
        and re.search(r"(?m)^\s*(?:cmd:\s*)?.*\bupgrade\b", block)
        is not None
        and "--install" in block
    )
    module_operation = "kubernetes.core.helm:" in block
    return command_operation or module_operation


def lock_key(block: str) -> str | None:
    matches = set(
        re.findall(
            r"helm_chart_lock\.charts\.([A-Za-z0-9_]+)\.version",
            block,
        )
    )
    if len(matches) == 1:
        return next(iter(matches))
    return None


def approved_repositories() -> dict[str, str]:
    payload = json.loads(
        (ROOT / "helm-repositories.json").read_text(encoding="utf-8")
    )
    repositories = payload.get("repositories", [])
    return {
        str(item["name"]): str(item["url"])
        for item in repositories
        if isinstance(item, dict)
    }


def playbook_operations() -> tuple[dict[str, str], list[str]]:
    operations: dict[str, str] = {}
    failures: list[str] = []

    for path in sorted((ROOT / "playbooks").rglob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for block in task_blocks(text):
            if not helm_operation(block):
                continue

            heading = block.splitlines()[0].strip()
            key = lock_key(block)
            if key is None:
                failures.append(
                    f"{path.relative_to(ROOT)}: {heading} must reference "
                    "exactly one helm_chart_lock chart version"
                )
                continue

            if key in operations:
                failures.append(
                    f"Helm lock key {key!r} is used by more than one "
                    "installation task"
                )
            operations[key] = block

    return operations, failures


def main() -> int:
    lock = json.loads(
        (ROOT / "helm-chart-lock.json").read_text(encoding="utf-8")
    )
    charts = lock.get("charts", {})
    flags = enabled_variables()
    repositories = approved_repositories()
    operations, failures = playbook_operations()

    if lock.get("schema_version") != "1.0":
        failures.append("helm-chart-lock.json schema_version must be 1.0")

    if not repositories:
        failures.append("No approved Helm repositories are registered")

    for key, item in charts.items():
        if not isinstance(item, dict):
            failures.append(f"{key}: lock entry is not an object")
            continue

        enabled_variable = str(item.get("enabled_variable", ""))
        if enabled_variable == "always":
            enabled = True
        elif enabled_variable not in flags:
            failures.append(
                f"{key}: enabled variable {enabled_variable!r} "
                "does not exist in group variables"
            )
            enabled = False
        else:
            enabled = flags[enabled_variable]

        version = str(item.get("version", ""))
        if enabled and not exact_version(version):
            failures.append(
                f"{key}: enabled release {item.get('release')} has "
                f"unresolved chart version {version!r}"
            )

        chart = str(item.get("chart", ""))
        if not chart.startswith("oci://"):
            prefix = chart.split("/", 1)[0]
            if prefix not in repositories:
                failures.append(
                    f"{key}: chart repository prefix {prefix!r} "
                    "is not approved"
                )

        block = operations.get(key)
        if block is None:
            if enabled:
                failures.append(
                    f"{key}: enabled chart has no repository-locked "
                    "installation task"
                )
            continue

        expected_values = {
            "release": str(item.get("release", "")),
            "chart": chart,
            "namespace": str(item.get("namespace", "")),
        }
        for label, value in expected_values.items():
            if value and value not in block:
                failures.append(
                    f"{key}: installation task does not contain locked "
                    f"{label} value {value!r}"
                )

        if 'environment: "{{ helm_environment }}"' not in block:
            failures.append(
                f"{key}: installation task lacks isolated Helm environment"
            )

        if "kubernetes.core.helm:" in block:
            pattern = re.compile(
                r"chart_version:\s*[\"']?\{\{\s*"
                + re.escape(
                    f"helm_chart_lock.charts.{key}.version"
                )
                + r"\s*\}\}[\"']?"
            )
            if pattern.search(block) is None:
                failures.append(
                    f"{key}: Helm module chart_version is not lock-derived"
                )
        else:
            if "--version" not in block:
                failures.append(
                    f"{key}: Helm command lacks --version"
                )

    unknown = sorted(set(operations) - set(charts))
    for key in unknown:
        failures.append(
            f"Playbook references missing Helm chart lock key {key!r}"
        )

    if failures:
        print("Kalaxy3 SAGE deployment guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    enabled_count = sum(
        1
        for item in charts.values()
        if item.get("enabled_variable") == "always"
        or flags.get(str(item.get("enabled_variable", "")), False)
    )
    print(
        f"PASS {enabled_count} enabled Helm releases have exact chart pins"
    )
    print("PASS every Helm installation task is represented in the lock")
    print("PASS release, chart, namespace, and repository mappings")
    print("Kalaxy3 SAGE deployment guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
