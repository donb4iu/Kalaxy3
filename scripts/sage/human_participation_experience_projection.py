"""Experience-aware, read-only SAGE human-participation projections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MAX_RECORDS = 4


def load_object(path: Path) -> dict[str, Any]:
    """Load a JSON object."""
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def scalar_text(value: Any) -> str:
    """Flatten bounded scalar content for deterministic matching."""
    if isinstance(value, dict):
        return " ".join(scalar_text(child) for child in value.values())
    if isinstance(value, list):
        return " ".join(scalar_text(child) for child in value[:100])
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return ""


def candidate_dicts(value: Any) -> list[dict[str, Any]]:
    """Collect bounded dictionary candidates from a JSON catalog."""
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        text = scalar_text(value)
        if 2 <= len(value) <= 40 and 20 <= len(text) <= 6000:
            found.append(value)
        for child in value.values():
            found.extend(candidate_dicts(child))
    elif isinstance(value, list):
        for child in value[:1000]:
            found.extend(candidate_dicts(child))
    return found


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    """Keep useful provenance fields without copying whole records."""
    preferred = [
        "evidence_id", "id", "title", "subject", "status", "path",
        "source_path", "recorded_at", "date", "summary", "description",
    ]
    compact = {key: record[key] for key in preferred if key in record}
    if compact:
        return compact
    return {key: record[key] for key in sorted(record)[:8]}


def retrieve(
    catalog: dict[str, Any],
    terms: list[str],
) -> list[dict[str, Any]]:
    """Return deterministic keyword-matched evidence candidates."""
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for record in candidate_dicts(catalog):
        text = scalar_text(record).lower()
        score = sum(1 for term in terms if term.lower() in text)
        if not score:
            continue
        compact = compact_record(record)
        identity = json.dumps(compact, sort_keys=True, default=str)
        ranked.append((score, identity, compact))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return unique_matches(ranked)


def unique_matches(
    ranked: list[tuple[int, str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Deduplicate and bound retrieval results."""
    unique: dict[str, dict[str, Any]] = {}
    for score, identity, compact in ranked:
        if identity not in unique:
            unique[identity] = {
                "retrieval_match_count": score,
                "epistemic_status": "retrieved_evidence_candidate",
                "record": compact,
            }
        if len(unique) >= MAX_RECORDS:
            break
    return list(unique.values())


def inventory_area(
    catalog: dict[str, Any],
    query: dict[str, Any],
) -> dict[str, Any]:
    """Project one bounded experience area."""
    matches = retrieve(catalog, list(query["terms"]))
    return {
        "area": query["area"],
        "question": query["question"],
        "retrieval_status": (
            "repository_evidence_candidates_found"
            if matches else "no_bounded_catalog_match"
        ),
        "experience_claim": "not_inferred_from_retrieval_alone",
        "evidence_candidates": matches,
        "llm_relevance_hypothesis": query.get(
            "llm_relevance_hypothesis"
        ),
    }


def build_inventory(
    seed: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Build the experience-inventory entry mode."""
    areas = [
        inventory_area(catalog, query)
        for query in seed["experience_inventory_queries"]
    ]
    return {
        "projection_type": "experience_inventory",
        "epistemic_rule": (
            "Catalog matches are evidence candidates, not proof of competence."
        ),
        "areas": areas,
    }


def build_intent_projection(
    seed: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Build intent-relative experience plus innovation."""
    experience = []
    for query in seed["intent_experience_queries"]:
        item = inventory_area(catalog, query)
        item["applicability"] = "requires_contextual_judgment"
        experience.append(item)
    return {
        "projection_type": "intent_relative_experience_and_innovation",
        "architect_intent": seed["architect_intent"],
        "stakeholder_concerns": seed["stakeholder_concerns"],
        "relevant_experience": experience,
        "llm_innovations": seed["llm_innovations"],
        "unresolved_questions": seed["unresolved_questions"],
        "human_decisions": seed["human_decisions"],
        "tactical_options": seed["tactical_options"],
        "authority_contract": {
            "experience": "SAGE retrieves and preserves provenance",
            "innovation": "LLM proposes beyond experience",
            "decision": "Architect selects objectives and trade-offs",
        },
    }


def validate_seed(seed: dict[str, Any]) -> list[str]:
    """Validate epistemic and authority boundaries in the working seed."""
    errors: list[str] = []
    for item in seed.get("llm_innovations", []):
        if item.get("epistemic_status") != "llm_proposed":
            errors.append("LLM innovations must remain llm_proposed")
    for item in seed.get("tactical_options", []):
        if item.get("epistemic_status") != "llm_proposed":
            errors.append("Tactical options must remain llm_proposed")
    for item in seed.get("human_decisions", []):
        if item.get("authority") != "Architect":
            errors.append("Human decisions must remain Architect-owned")
    return errors


def forbid_opaque_scores(value: Any, path: str = "") -> list[str]:
    """Reject aggregate priority/ranking scores."""
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else key
            if key.lower() in {
                "priority_score", "overall_score", "rank_score"
            }:
                errors.append(f"opaque score forbidden at {here}")
            errors.extend(forbid_opaque_scores(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(forbid_opaque_scores(child, f"{path}[{index}]"))
    return errors
