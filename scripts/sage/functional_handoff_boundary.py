#!/usr/bin/env python3
"""Validate an isolated functional handoff and one-shot translator disposition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Reject an untrusted request or translator output that violates isolation."""


HANDOFF_FIELDS = frozenset({
    "schema_version", "objective_id", "functional_goal", "current_maturity",
    "verified_progress", "outstanding_functional_work", "success_evidence",
    "constraints", "evidence_refs", "parent_objective_id",
})
DISPOSITION_FIELDS = frozenset({
    "schema_version", "handoff_sha256", "disposition", "functional_contribution",
    "sage_capabilities", "validation", "reason", "clarification_question",
    "blocker", "next_functional_step",
})
DENIED = frozenset({
    "git_command", "shell_command", "source_patch", "workflow_state",
    "primitive", "role_prompt", "conversation_history", "reasoning_trace",
})


def canonical(value: dict[str, Any]) -> bytes:
    """Serialize a JSON object canonically for identity verification.

    Args:
        value: JSON object to serialize.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def digest(value: dict[str, Any]) -> str:
    """Calculate content identity for one JSON object.

    Args:
        value: JSON object to hash.
    """
    return hashlib.sha256(canonical(value)).hexdigest()


def require_text(value: dict[str, Any], key: str) -> None:
    """Require a nonempty text value.

    Args:
        value: Parsed JSON object.
        key: Required property name.
    """
    if not isinstance(value.get(key), str) or not value[key].strip():
        raise ContractError(f"{key} must be nonempty text")


def require_text_list(value: dict[str, Any], key: str) -> None:
    """Require a list of strings, including the empty list.

    Args:
        value: Parsed JSON object.
        key: Required property name.
    """
    items = value.get(key)
    if not isinstance(items, list) or any(
        not isinstance(item, str) or not item.strip() for item in items
    ):
        raise ContractError(f"{key} must be a list of nonempty strings")


def validate_handoff(value: dict[str, Any]) -> None:
    """Validate functional-only handoff without SAGE execution instructions.

    Args:
        value: Untrusted persistent-agent handoff.
    """
    if set(value) != HANDOFF_FIELDS or set(value) & DENIED:
        raise ContractError("handoff must have exactly the functional fields")
    if value["schema_version"] != "1.0":
        raise ContractError("unsupported handoff schema")
    for key in ("objective_id", "functional_goal", "current_maturity",
                "outstanding_functional_work"):
        require_text(value, key)
    for key in ("verified_progress", "success_evidence", "constraints",
                "evidence_refs"):
        require_text_list(value, key)
    if value["parent_objective_id"] is not None:
        require_text(value, "parent_objective_id")


def validate_disposition(value: dict[str, Any], handoff: dict[str, Any]) -> None:
    """Validate one isolated translator response against its exact input.

    Args:
        value: Fresh translator result.
        handoff: Validated functional input object.
    """
    if set(value) != DISPOSITION_FIELDS:
        raise ContractError("translator output contains missing or extra fields")
    if value["schema_version"] != "1.0":
        raise ContractError("unsupported disposition schema")
    if value["handoff_sha256"] != digest(handoff):
        raise ContractError("disposition is not bound to the exact handoff")
    if value["disposition"] not in {"executable", "clarify", "blocked"}:
        raise ContractError("unknown translator disposition")
    for key in ("functional_contribution", "reason", "next_functional_step"):
        require_text(value, key)
    for key in ("sage_capabilities", "validation"):
        require_text_list(value, key)
    if value["disposition"] == "clarify":
        require_text(value, "clarification_question")
    elif value["clarification_question"] is not None:
        raise ContractError("unexpected clarification")
    if value["disposition"] == "blocked":
        require_text(value, "blocker")
    elif value["blocker"] is not None:
        raise ContractError("unexpected blocker")


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk.

    Args:
        path: Input JSON file path.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError("top-level JSON value must be an object")
    return value


def main() -> int:
    """Validate a handoff and optionally its one-shot translator disposition."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--disposition", type=Path)
    args = parser.parse_args()
    try:
        handoff = load_json(args.handoff)
        validate_handoff(handoff)
        if args.disposition:
            validate_disposition(load_json(args.disposition), handoff)
    except (ContractError, OSError, ValueError) as error:
        parser.exit(1, f"FAIL CLOSED: {error}\n")
    print(f"PASS functional boundary; handoff_sha256={digest(handoff)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
