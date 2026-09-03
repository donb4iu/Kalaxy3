#!/usr/bin/env python3
"""Generate experience inventory and intent-relative projections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_participation_experience_projection import (
    build_intent_projection,
    build_inventory,
    forbid_opaque_scores,
    load_object,
    validate_seed,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--inventory-output", required=True, type=Path)
    parser.add_argument("--intent-output", required=True, type=Path)
    return parser.parse_args()


def write_json(path: Path, value: dict) -> None:
    """Write deterministic formatted JSON."""
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Generate both read-only projections."""
    args = parse_args()
    seed = load_object(args.seed)
    catalog = load_object(args.catalog)
    errors = validate_seed(seed)
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors))
        return 2
    inventory = build_inventory(seed, catalog)
    intent = build_intent_projection(seed, catalog)
    errors = forbid_opaque_scores([inventory, intent])
    if errors:
        print("\n".join(f"FAIL: {item}" for item in errors))
        return 2
    write_json(args.inventory_output, inventory)
    write_json(args.intent_output, intent)
    print("SAGE experience inventory + intent projection: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
