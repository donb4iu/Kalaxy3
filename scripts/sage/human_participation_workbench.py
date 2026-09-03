"""Read-only Human Participation Workbench state projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EPISTEMIC_LEGEND = [
    {
        "id": "evidence",
        "label": "Evidence",
        "meaning": "Persisted source material with provenance.",
    },
    {
        "id": "sage-derived",
        "label": "SAGE-derived",
        "meaning": "Deterministic projection or validation from governed inputs.",
    },
    {
        "id": "llm-derived",
        "label": "LLM-derived",
        "meaning": (
            "Semantic interpretation grounded in cited evidence; "
            "not promoted to demonstrated fact."
        ),
    },
    {
        "id": "llm-proposed",
        "label": "LLM-proposed",
        "meaning": (
            "A new possibility that may extend beyond prior SAGE experience."
        ),
    },
    {
        "id": "architect",
        "label": "Architect",
        "meaning": "Human authority for objectives, trade-offs, and action.",
    },
]


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def unique_strings(values: list[str]) -> list[str]:
    """Return stable unique non-empty strings."""
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def collect_unknowns(
    synthesis: dict[str, Any],
    intent: dict[str, Any],
) -> list[str]:
    """Collect visible uncertainty without inventing resolution."""
    values = list(intent.get("unresolved_questions", []))
    for item in synthesis.get("intent_applicability", []):
        values.extend(item.get("unknowns", []))
    return unique_strings(values)


def evidence_gaps(intent: dict[str, Any]) -> list[dict[str, Any]]:
    """Project local evidence availability as explicit gaps."""
    output: list[dict[str, Any]] = []
    for item in intent.get("supplemental_experience_sources", []):
        output.append({
            "source_type": item.get("source_type", ""),
            "availability": item.get("availability", "unknown"),
            "canonical_repository_retrieval": item.get(
                "canonical_repository_retrieval",
                False,
            ),
        })
    return output


def build_state(
    synthesis: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any]:
    """Build the stable stakeholder-facing read-only state."""
    objective = dict(synthesis["architect_intent"])
    objective["display_epistemic_class"] = "architect"

    themes = []
    for item in synthesis["experience_themes"]:
        projected = dict(item)
        projected["display_epistemic_class"] = "llm-derived"
        themes.append(projected)

    applicability = []
    for item in synthesis["intent_applicability"]:
        projected = dict(item)
        projected["display_epistemic_class"] = "llm-derived"
        applicability.append(projected)

    innovations = []
    for item in synthesis["innovation_beyond_experience"]:
        projected = dict(item)
        projected["display_epistemic_class"] = "llm-proposed"
        innovations.append(projected)

    decisions = []
    for item in intent.get("human_decisions", []):
        projected = dict(item)
        projected["display_epistemic_class"] = "architect"
        decisions.append(projected)

    return {
        "schema_version": "1.0",
        "product": "Kalaxy3 Human Participation Workbench",
        "interaction_mode": "read_only",
        "maturity": "stakeholder_ui_proof",
        "product_questions": [
            "What can SAGE help me with?",
            "Given this objective, what matters?",
            "Where is my judgment valuable?",
        ],
        "objective": objective,
        "experience_themes": themes,
        "intent_applicability": applicability,
        "innovation_beyond_experience": innovations,
        "architect_decisions": decisions,
        "unknowns": collect_unknowns(synthesis, intent),
        "evidence_availability": evidence_gaps(intent),
        "epistemic_legend": EPISTEMIC_LEGEND,
        "provenance": {
            "semantic_projection_type": synthesis["projection_type"],
            "semantic_corpus_sha256": synthesis["corpus_sha256"],
            "semantic_truth_validated_by_sage": synthesis[
                "validation"
            ]["semantic_truth_validated_by_sage"],
            "evidence_citations_resolved": synthesis[
                "validation"
            ]["evidence_citations_resolved"],
            "architect_authority": synthesis["architect_authority"],
        },
    }


def forbidden_score_paths(
    value: Any,
    path: str = "",
) -> list[str]:
    """Reject opaque stakeholder-ranking scores."""
    forbidden = {"priority_score", "overall_score", "rank_score"}
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else key
            if key.lower() in forbidden:
                errors.append(here)
            errors.extend(forbidden_score_paths(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(
                forbidden_score_paths(child, f"{path}[{index}]")
            )
    return errors


def validate_state(state: dict[str, Any]) -> list[str]:
    """Validate product and epistemic boundaries."""
    errors: list[str] = []
    if state.get("interaction_mode") != "read_only":
        errors.append("interaction_mode must remain read_only")
    if state.get("objective", {}).get("authority") != "Architect":
        errors.append("objective authority must remain Architect")
    if len(state.get("experience_themes", [])) < 3:
        errors.append("at least three experience themes are required")
    if not state.get("intent_applicability"):
        errors.append("intent applicability must be visible")
    if not state.get("architect_decisions"):
        errors.append("Architect decisions must be visible")
    if not state.get("unknowns"):
        errors.append("unknowns must be visible")

    for item in state.get("experience_themes", []):
        if item.get("epistemic_status") != "llm_derived":
            errors.append("experience theme must remain llm_derived")
        if not item.get("evidence"):
            errors.append("experience theme must expose evidence")

    for item in state.get("intent_applicability", []):
        if item.get("epistemic_status") != "llm_derived":
            errors.append("applicability must remain llm_derived")
        if item.get("transfer_decision") != (
            "requires_architect_judgment"
        ):
            errors.append("experience transfer must remain Architect-owned")
        if not item.get("evidence"):
            errors.append("applicability must expose evidence")

    for item in state.get("innovation_beyond_experience", []):
        if item.get("epistemic_status") != "llm_proposed":
            errors.append("innovation must remain llm_proposed")
        if item.get("decision_authority") != "Architect":
            errors.append("innovation authority must remain Architect")

    labels = {
        item.get("label")
        for item in state.get("epistemic_legend", [])
    }
    required = {
        "Evidence",
        "SAGE-derived",
        "LLM-derived",
        "LLM-proposed",
        "Architect",
    }
    if not required.issubset(labels):
        errors.append("epistemic legend is incomplete")

    for path in forbidden_score_paths(state):
        errors.append(f"opaque aggregate score forbidden at {path}")
    return errors
