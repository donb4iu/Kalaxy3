"""Evidence-bound task/objective functional narration without invented success."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _sha(data: bytes) -> str:
    """Return a stable content digest."""
    return hashlib.sha256(data).hexdigest()


def evidence_item(path: Path) -> dict[str, Any]:
    """Bind a local evidence file to its bytes, without asserting its truth."""
    data = path.read_bytes()
    return {"path": str(path), "sha256": _sha(data)}


def summarize(
    request: str,
    result: Mapping[str, Any],
    evidence: Mapping[str, Any],
    *,
    referee: Mapping[str, Any] | None = None,
    execution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Separate task evidence from objective progress and incomplete participation."""
    fresh = result.get("fresh_role", {})
    fresh = fresh if isinstance(fresh, Mapping) else {}
    checked_referee = referee is not None and referee.get("decision", {}).get("verdict") == "allow"
    status = str(result.get("status", "unknown"))
    execution_status = (execution or {}).get("status")
    execution_receipt_present = execution is not None
    task = {
        "request_sha256": _sha(request.encode("utf-8")),
        "fresh_invoked": fresh.get("invoked") is True,
        "referee_participation": "evidenced-allow" if checked_referee else (
            "evidenced-reject" if referee else "not-demonstrated"
        ),
        "admission_status": status,
        "execution_status": execution_status or "not-demonstrated",
        "evidence": dict(evidence),
    }
    objective = {
        "functional_outcome_verified": False,
        "functional_progress": "execution-receipt-requires-independent-qualification" if execution_receipt_present else "not-yet-proven",
        "blocker": result.get("blocker", {}),
        "next_boundary": result.get("next_boundary", "unknown"),
        "remaining": [
            "A SAGE-governed execution receipt is required before claiming functional delivery"
        ],
        "unproven_participants": [
            name for name in ("Responsible", "Reviewer", "task Narrator", "objective Narrator",
                              "Path/Architecture Critic", "participation telemetry", "Evidence Observatory")
            if not (execution or {}).get("participation", {}).get(name)
        ],
    }
    return {"schema_version": "1.0", "task": task, "objective": objective,
            "authority": "deterministic-projection-of-supplied-receipts"}


def write_report(
    request: str, receipt_path: Path, destination: Path, *,
    referee_path: Path | None = None, execution_path: Path | None = None,
) -> dict[str, Any]:
    """Persist independently reproducible narration from evidence files."""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    paths = {"front_door": evidence_item(receipt_path)}
    referee = None
    execution = None
    if referee_path and referee_path.is_file():
        referee = json.loads(referee_path.read_text(encoding="utf-8"))
        paths["referee"] = evidence_item(referee_path)
    if execution_path and execution_path.is_file():
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        paths["execution"] = evidence_item(execution_path)
    result = summarize(request, receipt, paths, referee=referee, execution=execution)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
