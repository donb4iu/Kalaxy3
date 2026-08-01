#!/usr/bin/env python3
"""Summarize reusable workflow execution evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import UsageAnalyzer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-directory",
        type=Path,
        default=(
            Path.home()
            / ".local"
            / "state"
            / "kalaxy3"
            / "sage-workflows"
        ),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paths = tuple(sorted(args.log_directory.glob("*.jsonl")))
    summary = UsageAnalyzer.summarize(paths)
    encoded = json.dumps(summary, indent=4) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
        print(args.output)
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
