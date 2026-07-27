#!/usr/bin/env python3
"""Verify every inventory host supports noninteractive Ansible authentication."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ansible = ROOT / ".venv/bin/ansible"
    result = subprocess.run(
        [
            str(ansible),
            "all",
            "--module-name",
            "ansible.builtin.ping",
            "--one-line",
            "--forks",
            "1",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        print(
            "Kalaxy3 SSH authentication preflight: FAIL CLOSED\n"
            "At least one inventory host did not accept noninteractive "
            "authentication. Use the repository bootstrap workflow one host "
            "at a time, then rerun this gate."
        )
        return 1

    inventory = subprocess.run(
        [
            str(ROOT / ".venv/bin/ansible-inventory"),
            "-i",
            str(ROOT / "inventory/hosts.yml"),
            "--list",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    hostvars = json.loads(inventory.stdout).get(
        "_meta", {}
    ).get("hostvars", {})

    print(
        f"PASS noninteractive Ansible authentication for "
        f"{len(hostvars)} inventory hosts"
    )
    print("Kalaxy3 SSH authentication preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
