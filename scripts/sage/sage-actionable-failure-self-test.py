#!/usr/bin/env python3
"""Validate the Kalaxy3 actionable SAGE failure contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
STANDARD: Final = (
    ROOT
    / "markdown/standards/"
    "kalaxy3-sage-actionable-failure-contract.md"
)
PLAYBOOK: Final = (
    ROOT
    / "infrastructure/k3s-homelab/playbooks/"
    "validate-centralized-logging.yml"
)
REQUIRED_SECTIONS: Final = (
    "SAGE ACTION BLOCKED",
    "Attempted action",
    "Detected state",
    "Why this is invalid",
    "Likely intended outcome",
    "Confirm the correct approach",
    "Allowed actions",
    "Prohibited actions",
    "Canonical recovery",
    "SAGE integrity requirements",
    "Repository gap",
)


def require_markers(text: str, source: str) -> None:
    """Require every actionable-failure section in the supplied text."""
    missing = [marker for marker in REQUIRED_SECTIONS if marker not in text]
    if missing:
        raise RuntimeError(
            f"{source}: missing failure sections: {', '.join(missing)}"
        )


def validate_standard() -> None:
    """Validate the authoritative Markdown contract."""
    text = STANDARD.read_text(encoding="utf-8")
    require_markers(text, str(STANDARD))
    for marker in (
        "MUST NOT depend on remembered conversations",
        "frequent cohesive validated commits",
        "systemic repository gap",
    ):
        if marker not in text:
            raise RuntimeError(f"{STANDARD}: missing marker {marker!r}")
    print("PASS actionable failure standard")


def validate_playbook() -> None:
    """Validate actionable interpreter and lifecycle failures."""
    text = PLAYBOOK.read_text(encoding="utf-8")
    messages = re.findall(
        r"fail_msg:\s*[>|]-?\s*\n(?P<body>(?:\s{10,}.*\n)+)",
        text,
    )
    actionable = [
        message
        for message in messages
        if "SAGE ACTION BLOCKED" in message
    ]
    if len(actionable) < 2:
        raise RuntimeError(
            f"{PLAYBOOK}: expected two actionable failure messages"
        )
    for index, message in enumerate(actionable, start=1):
        require_markers(message, f"{PLAYBOOK} failure {index}")
    for marker in (
        "make centralized-logging-render",
        "make centralized-logging-runtime-validate",
        "Do not bypass this assertion",
        "make sage-preflight",
    ):
        if marker not in text:
            raise RuntimeError(f"{PLAYBOOK}: missing marker {marker!r}")
    print("PASS centralized logging actionable failures")


def main() -> int:
    """Run actionable-failure contract regression checks."""
    validate_standard()
    validate_playbook()
    print("Kalaxy3 SAGE actionable failure self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
