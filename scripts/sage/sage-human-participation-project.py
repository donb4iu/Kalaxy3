#!/usr/bin/env python3
"""CLI for the SAGE human-participation read projection."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from human_participation_projection import project, validate_projection


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--epic", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def git_head() -> str:
    """Return the exact source commit used for projection."""
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main() -> int:
    """Generate and optionally persist a read-only projection."""
    args = parse_args()
    value = project(args.audit, args.epic, git_head())
    errors = validate_projection(value)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 2
    rendered = json.dumps(value, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"SAGE human participation projection: {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
