#!/usr/bin/env python3
"""Provenance-preserving projection of immutable legacy evidence into current SAGE semantics."""

from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any, Mapping, Sequence

ALLOWED_CLASSIFICATIONS = {
    "directly-supported",
    "safely-derivable",
    "unknown",
    "requires-current-revalidation",
    "requires-Architect-disposition",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

class LegacyEvidenceError(ValueError):
    pass

def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LegacyEvidenceError(f"{label} must be a non-empty string")
    return value.strip()

def _safe_relative_path(value: object, label: str) -> str:
    text = _string(value, label)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts:
        raise LegacyEvidenceError(f"{label} must be a safe repository-relative path")
    return text

def _source(value: Mapping[str, Any], source_bytes: bytes) -> dict[str, Any]:
    required = {"repository","repository_url","path","commit","historical_time_context"}
    optional = {"expected_content_sha256"}
    if set(value) - (required | optional) or not required.issubset(value):
        raise LegacyEvidenceError("legacy source descriptor fields are invalid")
    commit = _string(value.get("commit"), "source.commit")
    if not COMMIT_RE.fullmatch(commit):
        raise LegacyEvidenceError("source.commit must be a full 40-character Git SHA-1")
    observed_sha = sha256_bytes(source_bytes)
    expected = value.get("expected_content_sha256")
    if expected is not None:
        expected_text = _string(expected, "source.expected_content_sha256")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_text):
            raise LegacyEvidenceError("source.expected_content_sha256 must be SHA-256")
        if expected_text != observed_sha:
            raise LegacyEvidenceError("legacy source content digest mismatch")
    return {
        "repository": _string(value.get("repository"), "source.repository"),
        "repository_url": _string(value.get("repository_url"), "source.repository_url"),
        "path": _safe_relative_path(value.get("path"), "source.path"),
        "commit": commit,
        "content_sha256": observed_sha,
        "historical_time_context": _string(value.get("historical_time_context"), "source.historical_time_context"),
    }

def _claims(values: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)) or not values:
        raise LegacyEvidenceError("claims must contain at least one claim")
    result, seen = [], set()
    for index, item in enumerate(values):
        if not isinstance(item, Mapping):
            raise LegacyEvidenceError(f"claims[{index}] must be an object")
        required = {"claim_id","statement","classification","rationale"}
        optional = {"source_basis"}
        if set(item) - (required | optional) or not required.issubset(item):
            raise LegacyEvidenceError(f"claims[{index}] fields are invalid")
        claim_id = _string(item.get("claim_id"), f"claims[{index}].claim_id")
        if claim_id in seen:
            raise LegacyEvidenceError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        classification = _string(item.get("classification"), f"claims[{index}].classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise LegacyEvidenceError(f"claims[{index}].classification is not allowed")
        basis = item.get("source_basis", [])
        if not isinstance(basis, list) or not all(isinstance(entry, str) and entry.strip() for entry in basis):
            raise LegacyEvidenceError(f"claims[{index}].source_basis must contain strings")
        if classification in {"directly-supported", "safely-derivable"} and not basis:
            raise LegacyEvidenceError(f"claims[{index}] requires source_basis for {classification}")
        result.append({
            "claim_id": claim_id,
            "statement": _string(item.get("statement"), f"claims[{index}].statement"),
            "classification": classification,
            "source_basis": list(basis),
            "rationale": _string(item.get("rationale"), f"claims[{index}].rationale"),
        })
    return result

def build_projection(*, projection_id, source_descriptor, source_bytes, claims, projected_by):
    before = sha256_bytes(source_bytes)
    source = _source(source_descriptor, source_bytes)
    participant = _string(projected_by.get("participant_class"), "projected_by.participant_class")
    if participant not in {"human","llm","deterministic-orchestrator"}:
        raise LegacyEvidenceError("projected_by.participant_class is invalid")
    identity = _string(projected_by.get("identity"), "projected_by.identity")
    record = {
        "schema_version": "1.0",
        "record_type": "sage-legacy-evidence-projection",
        "projection_id": _string(projection_id, "projection_id"),
        "source": source,
        "projection": {
            "projected_by": {"participant_class": participant, "identity": identity},
            "claims": _claims(claims),
        },
        "authority": {
            "historical_source_is_immutable": True,
            "projection_is_current_authority": False,
            "projection_may_upgrade_confidence": False,
            "projection_may_establish_current_applicability": False,
            "projection_may_claim_current_success": False,
            "projection_may_claim_current_security_posture": False,
            "projection_may_claim_current_validation": False,
            "material_ambiguity_requires_architect_disposition": True,
        },
        "publication": {
            "legacy_label_required": True,
            "surface_source_repository_path_commit": True,
            "surface_current_revalidation_status": True,
        },
    }
    if sha256_bytes(source_bytes) != before:
        raise LegacyEvidenceError("legacy source bytes changed during projection")
    return record

def write_projection(path: Path, record: Mapping[str, Any]) -> str:
    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise LegacyEvidenceError(f"projection output already exists: {destination}")
    payload = (json.dumps(record, indent=2) + "\n").encode()
    destination.write_bytes(payload)
    return sha256_bytes(payload)
