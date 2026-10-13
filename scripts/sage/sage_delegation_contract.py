"""Bounded functional handoff; source context is evidence, not authority."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class AssignmentError(ValueError):
    """An assignment is incomplete or outside its permitted structure."""


def load_assignment(filename: str, functional_request: str) -> dict[str, Any]:
    """Load a bounded assignment without silently changing the Architect objective."""
    if not filename:
        return {"deliverable": functional_request, "acceptance": [], "constraints": []}
    raw = json.loads(Path(filename).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AssignmentError("assignment must be an object")
    allowed = {"deliverable", "acceptance", "constraints", "evidence_paths"}
    if set(raw) - allowed:
        raise AssignmentError("assignment contains unsupported fields")
    if not isinstance(raw.get("deliverable"), str) or not raw["deliverable"].strip():
        raise AssignmentError("assignment requires a nonempty deliverable")
    for key in ("acceptance", "constraints", "evidence_paths"):
        if not isinstance(raw.get(key, []), list) or not all(
            isinstance(v, str) and v.strip() for v in raw.get(key, [])
        ):
            raise AssignmentError(f"{key} must contain nonempty strings")
    return {"deliverable": raw["deliverable"],
            "acceptance": raw.get("acceptance", []),
            "constraints": raw.get("constraints", []),
            "evidence_paths": raw.get("evidence_paths", [])}


def bounded_role_context(selected: dict[str, Any], max_chars: int = 14000) -> dict[str, Any]:
    """Transmit a bounded projection of SAGE-selected evidence into the role envelope."""
    result: dict[str, Any] = {"contexts": selected.get("contexts", []),
        "source_classes": selected.get("source_classes", {})}
    budget = max_chars - len(json.dumps(result, ensure_ascii=False))
    records: list[Any] = []
    for record in selected.get("repository_files", []):
        size = len(json.dumps(record, ensure_ascii=False))
        if size > budget:
            continue
        records.append(record)
        budget -= size
    result["repository_files"] = records
    retrieval = selected.get("evidence_retrieval", {})
    if len(json.dumps(retrieval, ensure_ascii=False)) <= budget:
        result["evidence_retrieval"] = retrieval
    else:
        result["evidence_retrieval"] = {"omitted": "context-budget; available in SAGE receipt"}
    result["truncated"] = len(records) != len(selected.get("repository_files", []))
    return result


class EvidenceSelectionError(AssignmentError):
    """Required assignment evidence cannot be faithfully transmitted."""


def required_source_records(repo: Path, assignment: dict[str, Any], max_chars: int = 44000) -> list[dict[str, str]]:
    """Load exact repo-relative requested source files; never follow paths outside checkout."""
    import hashlib
    root = repo.resolve()
    records: list[dict[str, str]] = []
    used = 0
    for raw in assignment.get("evidence_paths", []):
        rel = Path(raw)
        if rel.is_absolute() or ".." in rel.parts:
            raise EvidenceSelectionError(f"unsafe evidence path: {raw}")
        full = (root / rel).resolve()
        if not full.is_relative_to(root) or not full.is_file():
            raise EvidenceSelectionError(f"required evidence missing or outside checkout: {raw}")
        payload = full.read_bytes()
        try:
            content = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceSelectionError(f"required evidence is not UTF-8: {raw}") from exc
        if "\x00" in content:
            raise EvidenceSelectionError(f"required evidence is binary: {raw}")
        record = {"path": rel.as_posix(), "sha256": hashlib.sha256(payload).hexdigest(),
                  "source_class": "assignment-required-source", "content": content}
        size = len(json.dumps(record, ensure_ascii=False))
        if used + size > max_chars:
            raise EvidenceSelectionError(f"required evidence exceeds source context budget: {raw}")
        used += size
        records.append(record)
    return records


def combine_role_context(selected: dict[str, Any], required: list[dict[str, str]], max_chars: int = 64000) -> dict[str, Any]:
    """Keep required evidence ahead of generic selections, deduplicate by path."""
    result = {"contexts": selected.get("contexts", []),
              "source_classes": selected.get("source_classes", {})}
    fixed = {r["path"]: r for r in required}
    spent = len(json.dumps(result, ensure_ascii=False))
    records = []
    for record in required:
        records.append(record)
        spent += len(json.dumps(record, ensure_ascii=False))
    if spent > max_chars:
        raise EvidenceSelectionError("required evidence exceeds role context budget")
    candidates = selected.get("repository_files", [])
    for record in candidates:
        if record.get("path") in fixed:
            continue
        size = len(json.dumps(record, ensure_ascii=False))
        if spent + size > max_chars:
            continue
        records.append(record)
        spent += size
    result["repository_files"] = records
    result["required_paths"] = list(fixed)
    result["truncated"] = len(records) < len(candidates) + len(required) - sum(r.get("path") in fixed for r in candidates)
    result["evidence_retrieval"] = {"reference": "evidence-retrieval.json", "note": "full retrieval remains in local receipt"}
    return result
