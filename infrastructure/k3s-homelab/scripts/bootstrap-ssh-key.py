#!/usr/bin/env python3
"""Install the controller's SSH public key on one verified inventory host."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN_HOSTS = ROOT / "inventory/ssh_known_hosts"


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument(
        "--identity",
        help="Optional public-key path passed to ssh-copy-id with -i.",
    )
    return parser.parse_args()


def inventory_host(name: str) -> tuple[str, str]:
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/ansible-inventory"),
            "-i",
            str(ROOT / "inventory/hosts.yml"),
            "--host",
            name,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    variables = json.loads(result.stdout)
    if not variables:
        raise RuntimeError(f"Unknown inventory host: {name}")

    address = str(variables.get("ansible_host", "")).strip()
    user = str(variables.get("ansible_user", "")).strip()
    if not address or not user:
        raise RuntimeError(
            f"Inventory host {name} must define ansible_host and ansible_user"
        )
    return address, user


def ssh_options() -> list[str]:
    return [
        "-o",
        f"UserKnownHostsFile={KNOWN_HOSTS}",
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-o",
        "StrictHostKeyChecking=yes",
    ]


def main() -> int:
    options = arguments()
    command = shutil.which("ssh-copy-id")
    if command is None:
        raise RuntimeError(
            "ssh-copy-id is not installed on this controller"
        )

    address, user = inventory_host(options.host)
    destination = f"{user}@{address}"

    copy_command = [command, *ssh_options()]
    if options.identity:
        copy_command.extend(["-i", options.identity])
    copy_command.append(destination)

    print(
        f"Installing the controller public key for {options.host} "
        f"({destination})."
    )
    print(
        "The remote account password may be requested. "
        "No password is written to the repository."
    )
    subprocess.run(copy_command, cwd=ROOT, check=True)

    verify = subprocess.run(
        [
            "ssh",
            *ssh_options(),
            "-o",
            "BatchMode=yes",
            destination,
            "true",
        ],
        cwd=ROOT,
        check=False,
    )
    if verify.returncode != 0:
        raise RuntimeError(
            f"Noninteractive SSH verification failed for {options.host}"
        )

    print(
        f"PASS noninteractive SSH authentication for {options.host}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SSH key bootstrap failed: {error}")
        raise SystemExit(1)
