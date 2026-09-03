#!/usr/bin/env python3
"""Generate Human Participation Workbench state and browser payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_participation_workbench import (
    build_state,
    load_object,
    validate_state,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthesis", required=True, type=Path)
    parser.add_argument("--intent", required=True, type=Path)
    parser.add_argument("--state-output", required=True, type=Path)
    parser.add_argument("--browser-output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """Generate validated read-only workbench state."""
    args = parse_args()
    synthesis = load_object(args.synthesis)
    intent = load_object(args.intent)
    state = build_state(synthesis, intent)
    errors = validate_state(state)
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors))
        return 2

    serialized = json.dumps(
        state,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    args.state_output.write_text(serialized + "\n", encoding="utf-8")
    args.browser_output.write_text(
        "window.KALAXY3_WORKBENCH_STATE = "
        + serialized
        + ";\n",
        encoding="utf-8",
    )
    print("SAGE Human Participation Workbench state: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
