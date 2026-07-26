#!/usr/bin/env python3
"""Validate the repository-created Kalaxy3 controller environment."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def run_command(arguments: List[str]) -> str:
    """Run a command and return standard output.

    Args:
        arguments: Command and arguments.

    Returns:
        Captured standard output.
    """
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def required_ansible_core() -> str:
    """Return the exact required ansible-core version."""
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    match = re.search(r"(?m)^ansible-core==([^\s]+)$", text)
    if match is None:
        raise RuntimeError("requirements.txt must pin ansible-core exactly")
    return match.group(1)


def required_collections() -> Dict[str, str]:
    """Return exact collection requirements."""
    text = (ROOT / "requirements.yml").read_text(encoding="utf-8")
    pairs = re.findall(
        r"- name:\s*(\S+)\s*\n\s*version:\s*[\"']?([^\"'\s]+)",
        text,
    )
    if not pairs:
        raise RuntimeError("No exact collection requirements found")
    return dict(pairs)


def installed_collections() -> Dict[str, str]:
    """Return installed collection versions."""
    galaxy = ROOT / ".venv/bin/ansible-galaxy"
    payload = json.loads(
        run_command([str(galaxy), "collection", "list", "--format", "json"])
    )
    installed: Dict[str, str] = {}
    for collections in payload.values():
        for name, metadata in collections.items():
            installed[name] = str(metadata["version"])
    return installed


def validate_python() -> None:
    """Validate the virtual-environment Python version."""
    expected = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    actual = ".".join(str(value) for value in sys.version_info[:3])
    if actual != expected:
        raise RuntimeError(
            f"Python mismatch: expected {expected}, found {actual}"
        )
    print(f"PASS Python {actual}")


def validate_ansible() -> None:
    """Validate ansible-core and collection versions."""
    ansible = ROOT / ".venv/bin/ansible"
    output = run_command([str(ansible), "--version"])
    match = re.search(r"ansible \[core ([^\]]+)\]", output)
    if match is None:
        raise RuntimeError("Unable to determine ansible-core version")

    expected_core = required_ansible_core()
    actual_core = match.group(1)
    if actual_core != expected_core:
        raise RuntimeError(
            f"ansible-core mismatch: expected {expected_core}, found {actual_core}"
        )
    print(f"PASS ansible-core {actual_core}")

    installed = installed_collections()
    for name, expected in required_collections().items():
        actual = installed.get(name)
        if actual != expected:
            raise RuntimeError(
                f"{name} mismatch: expected {expected}, found {actual}"
            )
        print(f"PASS {name} {actual}")


def main() -> int:
    """Run all controller checks."""
    expected_venv = (ROOT / ".venv").resolve()
    active_venv = Path(sys.prefix).resolve()

    if active_venv != expected_venv:
        raise RuntimeError(
            "Preflight must run from the repository .venv: "
            f"expected {expected_venv}, found {active_venv}"
        )
    validate_python()
    validate_ansible()
    print("Kalaxy3 controller preflight: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
