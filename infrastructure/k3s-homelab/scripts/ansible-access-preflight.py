#!/usr/bin/env python3
"""Verify SSH authentication and privilege escalation as separate controls."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory_host_count() -> int:
    result = subprocess.run(
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
    payload = json.loads(result.stdout)
    hostvars = payload.get("_meta", {}).get("hostvars", {})
    if not isinstance(hostvars, dict) or not hostvars:
        raise RuntimeError("Effective inventory contains no hosts")
    return len(hostvars)


def run_ansible(arguments: list[str], label: str) -> bool:
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/ansible"),
            "all",
            "--one-line",
            "--forks",
            "1",
            *arguments,
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
        print(f"Kalaxy3 {label}: FAIL CLOSED")
        return False

    print(f"PASS {label} for {inventory_host_count()} inventory hosts")
    return True


def verify_ssh() -> bool:
    return run_ansible(
        [
            "--extra-vars",
            json.dumps({"ansible_become": False}),
            "--module-name",
            "ansible.builtin.ping",
        ],
        "noninteractive SSH authentication",
    )


def verify_privilege() -> bool:
    return run_ansible(
        [
            "--become",
            "--extra-vars",
            json.dumps({"ansible_become": True}),
            "--module-name",
            "ansible.builtin.command",
            "--args",
            "id -u",
        ],
        "noninteractive Ansible privilege escalation",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=("ssh", "privilege", "all"),
        default="all",
    )
    args = parser.parse_args()

    if args.scope in ("ssh", "all") and not verify_ssh():
        print(
            "At least one inventory host did not accept noninteractive "
            "SSH authentication."
        )
        return 1

    if args.scope in ("privilege", "all") and not verify_privilege():
        print(
            "At least one inventory host did not permit noninteractive "
            "privilege escalation."
        )
        return 1

    print(f"Kalaxy3 Ansible access preflight ({args.scope}): PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
