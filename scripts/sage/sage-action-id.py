#!/usr/bin/env python3
"""Read-only CLI for canonical SAGE improvement-action ID allocation."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from sage_identifiers import (
    IdentifierAllocationError,
    allocate_action_id,
)


def load_registry(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("registry must be a JSON object")
    return payload


def self_test() -> int:
    date_token = "20260801"

    collision = {
        "actions": [
            {"action_id": "SAGE-ACTION-20260801-001"},
            {"action_id": "SAGE-ACTION-20260801-002"},
        ]
    }
    if allocate_action_id(
        collision,
        date_token=date_token,
    ) != "SAGE-ACTION-20260801-003":
        raise RuntimeError("collision allocation regression failed")

    gap = {
        "actions": [
            {"action_id": "SAGE-ACTION-20260801-001"},
            {"action_id": "SAGE-ACTION-20260801-003"},
        ]
    }
    if allocate_action_id(
        gap,
        date_token=date_token,
    ) != "SAGE-ACTION-20260801-002":
        raise RuntimeError("first-free gap allocation failed")

    malformed = {
        "actions": [
            {"action_id": "SAGE-ACTION-20260801-XYZ"},
            {"action_id": "SAGE-ACTION-20260731-001"},
        ]
    }
    if allocate_action_id(
        malformed,
        date_token=date_token,
    ) != "SAGE-ACTION-20260801-001":
        raise RuntimeError("malformed or foreign ID isolation failed")

    try:
        allocate_action_id(
            {"actions": [{"action_id": 7}]},
            date_token=date_token,
        )
    except IdentifierAllocationError:
        pass
    else:
        raise RuntimeError("non-string action ID did not fail closed")

    try:
        allocate_action_id(
            {"actions": "not-a-list"},
            date_token=date_token,
        )
    except IdentifierAllocationError:
        pass
    else:
        raise RuntimeError("invalid action registry did not fail closed")

    exhausted = {
        "actions": [
            {
                "action_id":
                    f"SAGE-ACTION-20260801-{sequence:03d}"
            }
            for sequence in range(1, 1000)
        ]
    }
    try:
        allocate_action_id(
            exhausted,
            date_token=date_token,
        )
    except IdentifierAllocationError:
        pass
    else:
        raise RuntimeError("exhausted namespace did not fail closed")

    with tempfile.TemporaryDirectory(
        prefix="sage-action-id-self-test-"
    ) as raw:
        path = Path(raw) / "registry.json"
        path.write_text(
            json.dumps(collision) + "\n",
            encoding="utf-8",
        )
        if allocate_action_id(
            load_registry(path),
            date_token=date_token,
        ) != "SAGE-ACTION-20260801-003":
            raise RuntimeError("registry file round-trip failed")

    print("PASS collision and first-free allocation")
    print("PASS malformed and foreign identifier isolation")
    print("PASS invalid registry and namespace exhaustion failures")
    print("Kalaxy3 SAGE action-ID allocator self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("sage-improvement-actions.json"),
    )
    parser.add_argument("--date")
    parser.add_argument(
        "--format",
        choices=("plain", "json"),
        default="plain",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    action_id = allocate_action_id(
        load_registry(args.registry),
        date_token=args.date,
    )
    if args.format == "json":
        print(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "action_id": action_id,
                    "registry": str(args.registry),
                    "mutation": False,
                },
                indent=4,
            )
        )
    else:
        print(action_id)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        IdentifierAllocationError,
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        print(
            f"Kalaxy3 SAGE action-ID allocator: FAIL CLOSED\n"
            f"  - {error}"
        )
        raise SystemExit(2)
