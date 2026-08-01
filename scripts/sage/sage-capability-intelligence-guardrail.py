#!/usr/bin/env python3
"""Protect the SAGE capability-intelligence walking skeleton."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/sage/sage-capability-intelligence.py"

def run(*args: str) -> None:
    result = subprocess.run(
        (sys.executable, str(CLI), *args),
        cwd=ROOT, check=False, capture_output=True, text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise RuntimeError(" ".join(args))

def main() -> int:
    try:
        run("check")
        run("render", "--check")
        run("metrics", "--check")
        run("self-test")
    except (OSError, RuntimeError) as error:
        print(
            "Kalaxy3 SAGE capability-intelligence guardrail: FAIL CLOSED\n"
            f"  - entry point failed: {error}"
        )
        return 1
    print("PASS capability intent, target, and current state")
    print("PASS visible unknowns, gaps, confidence, WAR, and CAF lenses")
    print("PASS federated authorities and conflict preservation")
    print("PASS alternative branch prediction and outcome loop")
    print("PASS rebuild-forward continuity and bounded autonomy")
    print("Kalaxy3 SAGE capability-intelligence guardrail: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
