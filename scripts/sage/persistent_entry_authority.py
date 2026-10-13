#!/usr/bin/env python3
"""Enforce persistent-agent admission authority before SAGE role invocation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


class AdmissionError(ValueError):
    """Reject a caller whose requested action exceeds its authority."""


FUNCTIONAL_FIELDS = frozenset({
    "schema_version", "objective_id", "functional_goal", "current_maturity",
    "verified_progress", "outstanding_functional_work", "success_evidence",
    "constraints", "evidence_refs", "parent_objective_id",
})
CONTROL_FIELDS = frozenset({
    "command", "argv", "shell_command", "git_command", "git_push",
    "primitive", "workflow", "workflow_state", "source_patch", "role_prompt",
    "role_assignment", "conversation_history", "reasoning_trace",
})


def canonical(value: dict[str, Any]) -> bytes:
    """Encode an object deterministically for content binding.

    Args:
        value: JSON object to encode.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha256(value: dict[str, Any]) -> str:
    """Return the SHA-256 digest of a JSON object.

    Args:
        value: JSON object to hash.
    """
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_functional(value: dict[str, Any]) -> None:
    """Require a strictly functional handoff from a persistent agent.

    Args:
        value: Untrusted functional input.
    """
    if set(value) != FUNCTIONAL_FIELDS or set(value) & CONTROL_FIELDS:
        raise AdmissionError("persistent input contains unauthorized fields")
    if value.get("schema_version") != "1.0":
        raise AdmissionError("unsupported functional handoff")
    for key in ("objective_id", "functional_goal", "current_maturity",
                "outstanding_functional_work"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise AdmissionError(f"invalid {key}")
    for key in ("verified_progress", "success_evidence", "constraints",
                "evidence_refs"):
        if not isinstance(value[key], list) or any(
            not isinstance(x, str) or not x.strip() for x in value[key]
        ):
            raise AdmissionError(f"invalid {key}")
    if value["parent_objective_id"] is not None and not isinstance(
        value["parent_objective_id"], str
    ):
        raise AdmissionError("invalid parent_objective_id")


def validate_exception(request: dict[str, Any], grant: dict[str, Any]) -> None:
    """Validate exact exception scope against external approval evidence.

    Args:
        request: Persistent-agent repair request.
        grant: Approval verified by an independent trusted SAGE caller.
    """
    required = {"schema_version", "grant_id", "architect_identity",
                "objective_id", "request_sha256", "scope", "valid"}
    if set(grant) != required or grant["schema_version"] != "1.0":
        raise AdmissionError("invalid break-glass grant contract")
    if grant["valid"] is not True or not grant["architect_identity"]:
        raise AdmissionError("break-glass not authorized")
    if grant["request_sha256"] != sha256(request):
        raise AdmissionError("grant does not bind exact request")
    if grant["objective_id"] != request.get("objective_id"):
        raise AdmissionError("objective authority mismatch")
    if grant["scope"] != request.get("repair_scope"):
        raise AdmissionError("repair exceeds granted scope")
    if not isinstance(grant["scope"], str) or not grant["scope"].strip():
        raise AdmissionError("missing repair scope")


def admit(payload: dict[str, Any], trusted_grant: dict[str, Any] | None = None) -> str:
    """Authorize a single functional handoff or bounded break-glass action.

    Args:
        payload: Untrusted persistent-agent request envelope.
        trusted_grant: Independently verified grant, never caller-supplied.
    """
    if set(payload) != {"caller", "mode", "request"}:
        raise AdmissionError("invalid admission envelope")
    if payload["caller"] != "persistent-llm":
        raise AdmissionError("unsupported caller for this boundary")
    request = payload["request"]
    if not isinstance(request, dict):
        raise AdmissionError("request must be an object")
    if payload["mode"] == "functional":
        if trusted_grant is not None:
            raise AdmissionError("unexpected authority in functional mode")
        validate_functional(request)
        return "functional-handoff-only"
    if payload["mode"] == "break-glass":
        if trusted_grant is None:
            raise AdmissionError("independent Architect authorization required")
        if set(request) != {"objective_id", "repair_scope", "defect", "evidence_refs"}:
            raise AdmissionError("break-glass request exceeds contract")
        if not isinstance(request["evidence_refs"], list):
            raise AdmissionError("invalid evidence references")
        validate_exception(request, trusted_grant)
        return "bounded-repair-proposal-only"
    raise AdmissionError("unknown admission mode")


def main() -> int:
    """Validate a functional input; never grant execution authority from a CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.envelope.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise AdmissionError("envelope must be an object")
        result = admit(payload)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"FAIL CLOSED: {error}\n")
    print(f"PASS {result}; request_sha256={sha256(payload['request'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
