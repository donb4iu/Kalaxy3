"""SAGE-owned bounded correction request derived from existing execution evidence.

This is candidate evidence, never authorization for execution or a substitute for
canonical action registration or qualified contribution admission.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def digest(data: Any) -> str:
    """Return a reproducible hash of evidence, without trusting model digests."""
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def prepare_correction(
    request: str,
    decision: dict[str, Any] | None,
    referee: dict[str, Any] | None,
    status: str,
) -> dict[str, Any]:
    """Preserve source facts for a fresh engineering attempt after nonacceptance."""
    if not request.strip():
        raise ValueError("functional request is required")
    verdict = (referee or {}).get("decision", {}).get("verdict")
    if status == "accepted" and verdict == "allow":
        raise ValueError("accepted contribution must not be escalated")
    return {
        "record_type": "sage-bounded-engineering-correction-request",
        "schema_version": "1.0",
        "functional_request": request,
        "request_sha256": hashlib.sha256(request.encode()).hexdigest(),
        "fresh_decision": decision,
        "fresh_decision_sha256": digest(decision),
        "referee": referee,
        "referee_sha256": digest(referee),
        "status": "candidate-engineering-evidence-only",
        "reason": status,
        "authority": {
            "execution_authorized": False,
            "action_accepted": False,
            "contribution_qualified": False,
        },
        "required_continuation": (
            "Produce source-backed engineering contribution using authoritative "
            "Kalaxy3 contracts; require independent new Referee and Reviewer "
            "qualification and canonical action registration before execution."
        ),
    }
