#!/usr/bin/env python3
"""Generate canonical experience inventory and intent projection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_participation_experience_projection import (
    build_intent_projection,
    build_inventory,
    forbid_opaque_scores,
    validate_seed,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--inventory-output", required=True, type=Path)
    parser.add_argument("--intent-output", required=True, type=Path)
    return parser.parse_args()


def load_json(path: Path) -> dict:
    """Load one JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: dict) -> None:
    """Write deterministic JSON."""
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Generate both read-only projections."""
    args = parse_args()
    repo = args.repo.resolve()
    seed = load_json(args.seed)
    errors = validate_seed(seed)
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors))
        return 2

    inventory = build_inventory(repo, seed)
    intent = build_intent_projection(repo, seed)
    errors = forbid_opaque_scores([inventory, intent])
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors))
        return 2

    write_json(args.inventory_output, inventory)
    write_json(args.intent_output, intent)
    print("SAGE canonical experience + intent projection: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
