#!/usr/bin/env python3
"""Compare repository Helm locks with releases already installed in Kalaxy3."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def enabled_variables() -> dict[str, bool]:
    text = (
        ROOT / "inventory/group_vars/all/main.yml"
    ).read_text(encoding="utf-8")
    return {
        name: raw.lower() == "true"
        for name, raw in re.findall(
            r"(?m)^([A-Za-z_][A-Za-z0-9_]*):\s*(true|false)\s*$",
            text,
            flags=re.IGNORECASE,
        )
    }


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Permit locked releases that are not installed yet.",
    )
    return parser.parse_args()


def main() -> int:
    options = arguments()
    lock = json.loads(
        (ROOT / "helm-chart-lock.json").read_text(encoding="utf-8")
    )
    flags = enabled_variables()

    result = subprocess.run(
        [
            str(ROOT / "scripts/helm"),
            "list",
            "--all-namespaces",
            "--output",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    releases = {
        item["name"]: item
        for item in json.loads(result.stdout)
    }

    failures: list[str] = []
    checked = 0
    missing = 0

    for key, item in lock.get("charts", {}).items():
        enabled_variable = str(item.get("enabled_variable", ""))
        enabled = (
            enabled_variable == "always"
            or flags.get(enabled_variable, False)
        )
        if not enabled:
            print(f"SKIP {key}: release is not enabled")
            continue

        expected_version = str(item.get("version", ""))
        release_name = str(item.get("release", ""))
        expected_namespace = str(item.get("namespace", ""))
        release = releases.get(release_name)

        if release is None:
            missing += 1
            if options.allow_missing:
                print(
                    f"NEW  {key}: {release_name} is not installed; "
                    "the pinned version may be installed"
                )
                continue
            failures.append(
                f"{key}: release {release_name!r} is not installed"
            )
            continue

        checked += 1
        chart_string = str(release.get("chart", ""))
        expected_suffix = f"-{expected_version}"
        if not chart_string.endswith(expected_suffix):
            failures.append(
                f"{key}: expected chart version {expected_version}, "
                f"found {chart_string}"
            )

        namespace = str(release.get("namespace", ""))
        if namespace != expected_namespace:
            failures.append(
                f"{key}: expected namespace {expected_namespace}, "
                f"found {namespace}"
            )

        status = str(release.get("status", ""))
        if status != "deployed":
            failures.append(
                f"{key}: installed release status is {status!r}, "
                "not 'deployed'"
            )

        if (
            chart_string.endswith(expected_suffix)
            and namespace == expected_namespace
            and status == "deployed"
        ):
            print(
                f"PASS {key}: {chart_string} in {namespace}"
            )

    if failures:
        print("\nKalaxy3 Helm lock reconciliation: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(
        f"\nPASS {checked} installed locked releases; "
        f"{missing} permitted new releases"
    )
    print("Kalaxy3 Helm lock reconciliation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
