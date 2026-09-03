"""Read-only SAGE human-participation projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
CONTEXT_ONLY = "documented_context"


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def coverage_map(audit: dict[str, Any]) -> dict[str, str]:
    """Map audited concepts to observed support status."""
    rows = audit.get("coverage", [])
    return {
        str(row["concept"]): str(row["status"])
        for row in rows
        if isinstance(row, dict)
        and "concept" in row
        and "status" in row
    }


def source_ref(path: Path, kind: str) -> dict[str, str]:
    """Build a local repository source reference."""
    return {
        "source_type": kind,
        "source_ref": str(path),
        "availability": "available" if path.exists() else "unavailable",
    }


def attention_items(
    audit: dict[str, Any],
    audit_path: Path,
) -> list[dict[str, Any]]:
    """Project material attention items without ranking them."""
    disposition = audit.get("coverage_disposition", {})
    normalize = list(disposition.get("normalize_or_project", []))
    gaps = list(disposition.get("candidate_gap", []))
    return [
        {
            "statement": (
                "Human-participation concepts remain context-only and must be "
                "normalized or projected before presentation can treat them as "
                "structured state."
            ),
            "epistemic_status": "derived",
            "concepts": normalize,
            "source_refs": [source_ref(audit_path, "audit_result")],
        },
        {
            "statement": (
                "The bounded audit found no concept wholly absent from the "
                "scanned authority."
            ),
            "epistemic_status": "derived",
            "scope_limit": "bounded scanned authority only",
            "concepts": gaps,
            "source_refs": [source_ref(audit_path, "audit_result")],
        },
    ]


def human_decisions(
    audit_path: Path,
    epic_path: Path,
) -> list[dict[str, Any]]:
    """Project the explicit Architect review boundary."""
    return [
        {
            "decision": (
                "Decide whether context-only concepts can be normalized "
                "deterministically or require minimal first-class representation."
            ),
            "authority": "Architect",
            "status": "decision_required",
            "epistemic_status": "documented",
            "source_refs": [
                source_ref(audit_path, "audit_result"),
                source_ref(epic_path, "architect_intent"),
            ],
        }
    ]


def tactical_options(
    audit: dict[str, Any],
    audit_path: Path,
    epic_path: Path,
) -> list[dict[str, Any]]:
    """Project bounded tactical options without an opaque score."""
    context = list(
        audit.get("coverage_disposition", {}).get(
            "normalize_or_project", []
        )
    )
    refs = [
        source_ref(audit_path, "audit_result"),
        source_ref(epic_path, "architect_intent"),
    ]
    return [
        {
            "candidate": "build_read_only_projection",
            "disposition": "current_80_20_path",
            "epistemic_status": "documented",
            "strategic_reach": [
                "stakeholder comprehension",
                "decision quality",
                "tactical attention allocation",
            ],
            "uncertainty_reduced": context,
            "information_gain": (
                "Tests whether existing semantics can support a useful human "
                "experience before UI investment."
            ),
            "source_refs": refs,
        },
        {
            "candidate": "add_first_class_schema_for_all_context_only_concepts",
            "disposition": "not_yet_justified",
            "epistemic_status": "derived",
            "reason": (
                "The audit found contextual support and no wholly absent "
                "concept; normalization must fail before broader schema work "
                "is justified."
            ),
            "source_refs": [source_ref(audit_path, "audit_result")],
        },
        {
            "candidate": "start_ui_implementation",
            "disposition": "deferred",
            "epistemic_status": "documented",
            "reason": (
                "The Architect epic requires the read/introspection contract "
                "to be proven before UI implementation."
            ),
            "source_refs": [source_ref(epic_path, "architect_intent")],
        },
    ]


def provenance_issues(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose provenance anomalies rather than normalizing them away."""
    records = audit.get("epic_catalog_projection", [])
    if not records:
        return []
    return [
        {
            "issue": "architect_intent_catalog_classification_requires_review",
            "epistemic_status": "observed",
            "detail": records,
        }
    ]


def project(
    audit_path: Path,
    epic_path: Path,
    source_commit: str,
) -> dict[str, Any]:
    """Build the human-participation projection."""
    audit = load_json(audit_path)
    coverage = coverage_map(audit)
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_type": "human-participation-attention",
        "source_commit": source_commit,
        "source_objective": "human-participation-introspection-contract-audit",
        "questions": {
            "what_should_i_care_about": attention_items(
                audit, audit_path
            ),
            "where_do_you_need_me": human_decisions(
                audit_path, epic_path
            ),
            "where_should_we_spend_next_unit_of_effort": tactical_options(
                audit, audit_path, epic_path
            ),
        },
        "epistemic_context": {
            "coverage": coverage,
            "context_only_concepts": sorted(
                key
                for key, value in coverage.items()
                if value == CONTEXT_ONLY
            ),
            "candidate_first_class_gaps": list(
                audit.get("coverage_disposition", {}).get(
                    "candidate_gap", []
                )
            ),
        },
        "provenance_issues": provenance_issues(audit),
        "runtime_evidence_inventory": audit.get(
            "runtime_evidence_inventory", {}
        ),
    }


def validate_projection(value: dict[str, Any]) -> list[str]:
    """Return projection contract violations."""
    errors: list[str] = []
    questions = value.get("questions", {})
    required = {
        "what_should_i_care_about",
        "where_do_you_need_me",
        "where_should_we_spend_next_unit_of_effort",
    }
    if set(questions) != required:
        errors.append("projection must expose exactly three stakeholder questions")
    errors.extend(_validate_items(questions))
    errors.extend(_validate_no_opaque_score(value))
    return errors


def _validate_items(questions: dict[str, Any]) -> list[str]:
    """Validate provenance and epistemic identity on projected items."""
    errors: list[str] = []
    for name, items in questions.items():
        if not isinstance(items, list) or not items:
            errors.append(f"{name} must contain at least one item")
            continue
        for index, item in enumerate(items):
            if "epistemic_status" not in item:
                errors.append(f"{name}[{index}] lacks epistemic_status")
            refs = item.get("source_refs", [])
            if not refs:
                errors.append(f"{name}[{index}] lacks source_refs")
    return errors


def _validate_no_opaque_score(value: Any, prefix: str = "") -> list[str]:
    """Reject scalar priority/ranking scores anywhere in the projection."""
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key.lower() in {"priority_score", "rank_score", "overall_score"}:
                errors.append(f"opaque score forbidden at {path}")
            errors.extend(_validate_no_opaque_score(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(
                _validate_no_opaque_score(child, f"{prefix}[{index}]")
            )
    return errors
