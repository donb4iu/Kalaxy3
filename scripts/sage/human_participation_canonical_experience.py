"""Canonical SAGE experience retrieval adapter for human participation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import re

from sage_evidence_retrieval import (
    load_json,
    reconsideration_summary,
    retrieve,
    retrieval_basis_sha256,
    validate_result,
)

POLICY = Path("sage-evidence-retrieval-policy.json")
CONTRADICTORY_STATES = {
    "contradicted",
    "invalidated",
    "rejected",
    "superseded",
}


def normalized(value: Any) -> str:
    """Normalize scalar evidence text for bounded relationship checks."""
    text = str(value).lower()
    return " ".join(re.findall(r"[a-z0-9]+", text))


def result_text(result: dict[str, Any]) -> str:
    """Build bounded relationship text from canonical result fields."""
    facts = " ".join(
        str(item.get("value", ""))
        for item in result.get("applicable_facts", [])
    )
    values = [
        result.get("identifier", ""),
        result.get("title", ""),
        result.get("source_path", ""),
        result.get("status", ""),
        " ".join(result.get("matched_terms", [])),
        facts,
    ]
    return normalized(" ".join(str(value) for value in values))


def hit_terms(
    result: dict[str, Any],
    terms: list[str],
) -> list[str]:
    """Return profile terms evidenced in canonical result content."""
    haystack = result_text(result)
    return sorted(
        term
        for term in terms
        if normalized(term) and normalized(term) in haystack
    )


def relationship(
    result: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Classify relationship without mutating canonical retrieval data."""
    direct = hit_terms(result, list(profile.get("direct_terms", [])))
    analogous = hit_terms(
        result,
        list(profile.get("analogous_terms", [])),
    )
    status = str(result.get("status", "")).lower()

    if status in CONTRADICTORY_STATES:
        name = "contradictory"
    elif len(direct) >= int(profile.get("direct_min_hits", 2)):
        name = "direct"
    elif direct or len(analogous) >= 2:
        name = "analogous"
    else:
        name = "weakly_related"

    return {
        "experience_relationship": name,
        "direct_term_hits": direct,
        "analogous_term_hits": analogous,
        "relationship_basis": "bounded_canonical_result_evidence",
    }


def finalization(
    relation: str,
    assessment_context: str,
) -> dict[str, Any]:
    """Return canonical reconsideration-field values only."""
    if relation == "weakly_related":
        return {
            "disposition": "reviewed-not-applicable",
            "disposition_rationale": (
                "Reviewed canonical retrieval result is too weakly related "
                "to support this bounded experience projection."
            ),
            "applicability": "contextually-relevant-not-applicable",
            "value_effect": "no-material-effect",
            "alternative_effect": "none",
            "reconsideration_trigger": (
                "Reconsider if stronger relationship evidence or more "
                "specific stakeholder context becomes available."
            ),
        }

    if assessment_context == "experience_inventory":
        applicability = (
            "applicable" if relation == "direct"
            else "partially-applicable"
        )
        return {
            "disposition": "applied",
            "disposition_rationale": (
                "Applied only to the bounded claim that SAGE has accumulated "
                "experience in this area; transferability is not implied."
            ),
            "applicability": applicability,
            "value_effect": "no-material-effect",
            "alternative_effect": "none",
            "reconsideration_trigger": "",
        }

    return {
        "disposition": "requires-revalidation",
        "disposition_rationale": (
            "Retrieved experience may relate to the current intent, but "
            "relationship evidence cannot establish transferability."
        ),
        "applicability": "requires-revalidation",
        "value_effect": "requires-revalidation",
        "alternative_effect": "none",
        "reconsideration_trigger": (
            "Reassess against current objective context, constraints, "
            "runtime state, and Architect priorities before transfer."
        ),
    }


def apply_finalization(
    result: dict[str, Any],
    values: dict[str, Any],
) -> None:
    """Mutate only canonical evidence-reconsideration fields."""
    for field, value in values.items():
        result[field] = value
    result["augmentations"] = []
    result["additional_acceptance_criteria"] = []


def retrieve_profile(
    repo: Path,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Retrieve canonically and wrap relationship interpretation."""
    policy = load_json(repo / POLICY)
    original = retrieve(
        repo=repo,
        policy_path=repo / POLICY,
        request=str(profile["retrieval_request"]),
        limit=int(profile.get("limit", 12)),
    )
    original_basis = original["retrieval_basis_sha256"]
    finalized = deepcopy(original)
    wrappers: list[dict[str, Any]] = []
    context = str(profile["assessment_context"])

    for result in finalized["results"]:
        relation = relationship(result, profile)
        apply_finalization(
            result,
            finalization(
                relation["experience_relationship"],
                context,
            ),
        )
        wrappers.append({
            **relation,
            "score_semantics": "retrieval_relevance_not_applicability",
            "canonical_result": result,
        })

    if retrieval_basis_sha256(finalized) != original_basis:
        raise RuntimeError(
            "human-participation adapter changed canonical retrieval basis"
        )
    validate_result(finalized, policy, require_final=True)

    return {
        "canonical_payload": finalized,
        "relationship_results": wrappers,
        "retrieval_basis_preserved": True,
        "reconsideration_summary": reconsideration_summary(finalized),
    }


def supported_candidates(
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return relationship results stronger than weakly related."""
    return [
        item
        for item in bundle["relationship_results"]
        if item["experience_relationship"] != "weakly_related"
    ]


def weak_candidates(
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return reviewed weak relationship results."""
    return [
        item
        for item in bundle["relationship_results"]
        if item["experience_relationship"] == "weakly_related"
    ]
