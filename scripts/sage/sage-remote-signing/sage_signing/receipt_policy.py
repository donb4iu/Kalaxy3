"""Bound signing authority to the existing SAGE PR #61 audit receipt contract."""

import json
import re
from typing import Any

SCHEMA = "sage-pr-audit-receipt-v1"
FIELDS = frozenset({
    "schema", "objective", "disposition", "signer_role", "reviewed_head",
    "merge_base", "scope_sha256", "audit_evidence", "bypass_reason",
    "original_query",
})
OBJECTIVE = re.compile(r"^(?:#[1-9][0-9]*|SAGE-[A-Za-z0-9-]+)$")
REVISION = re.compile(r"^[0-9a-f]{40,64}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def validate_evidence(value: Any) -> bool:
    """Recognize a PR #61 evidence reference.

    Args:
        value: Untrusted evidence entry.
    """
    return (isinstance(value, dict) and set(value) == {"path", "sha256"}
            and isinstance(value["path"], str) and bool(value["path"])
            and isinstance(value["sha256"], str)
            and bool(DIGEST.fullmatch(value["sha256"])))


def check_receipt(data: bytes, role: str) -> dict[str, Any]:
    """Reject noncanonical receipts or dispositions outside signer authority.

    Args:
        data: Candidate canonical PR #61 JSON bytes.
        role: Isolated controller identity, architect or auditor.
    """
    if role not in {"architect", "auditor"} or len(data) > 65536:
        raise PermissionError("Invalid configured signing authority")
    try:
        payload = json.loads(data)
    except (ValueError, UnicodeError) as error:
        raise ValueError("Malformed PR audit receipt") from error
    if not isinstance(payload, dict) or set(payload) != FIELDS:
        raise ValueError("Unexpected receipt fields")
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"))
               + "\n").encode("utf-8")
    if encoded != data or payload["schema"] != SCHEMA:
        raise ValueError("Noncanonical or incompatible PR #61 receipt")
    expected = "auditor" if payload["disposition"] == "executed" else "architect"
    if payload["disposition"] not in {"executed", "bypassed", "not_applicable"}:
        raise PermissionError("Unsupported audit disposition")
    if payload["signer_role"] != role or role != expected:
        raise PermissionError("Disposition requires a different signer")
    if not OBJECTIVE.fullmatch(str(payload["objective"])):
        raise ValueError("Invalid objective")
    if any(not REVISION.fullmatch(str(payload[field]))
           for field in ("reviewed_head", "merge_base")):
        raise ValueError("Invalid committed source revision")
    if not DIGEST.fullmatch(str(payload["scope_sha256"])):
        raise ValueError("Invalid source scope digest")
    if role == "auditor" and not validate_evidence(payload["audit_evidence"]):
        raise ValueError("Auditor must bind committed evidence")
    if role == "architect" and len(str(payload["bypass_reason"] or "").strip()) < 12:
        raise ValueError("Architect requires substantive justification")
    if payload["original_query"] is not None and not validate_evidence(
        payload["original_query"]
    ):
        raise ValueError("Malformed original query evidence")
    return payload
