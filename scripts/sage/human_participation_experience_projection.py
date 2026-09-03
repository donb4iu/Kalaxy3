"""Experience + innovation projection using canonical SAGE retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from human_participation_canonical_experience import (
    retrieve_profile,
    supported_candidates,
    weak_candidates,
)


def source_availability(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Project canonical repository source availability."""
    return [
        {
            "source_type": item["source_type"],
            "source_path": item["path"],
            "availability": "available",
            "records_loaded": item["records_loaded"],
        }
        for item in payload.get("sources", [])
    ]


def project_profile(
    repo: Path,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Project one canonical experience profile."""
    bundle = retrieve_profile(repo, profile)
    payload = bundle["canonical_payload"]
    candidates = supported_candidates(bundle)

    return {
        "area": profile["area"],
        "question": profile["question"],
        "assessment_context": profile["assessment_context"],
        "retrieval_request": payload["request"],
        "retrieval_algorithm": payload["algorithm_version"],
        "retrieval_basis_sha256": payload["retrieval_basis_sha256"],
        "retrieval_basis_preserved": bundle[
            "retrieval_basis_preserved"
        ],
        "policy_sha256": payload["policy_sha256"],
        "source_availability": source_availability(payload),
        "retrieval_status": (
            "canonical_experience_candidates_found"
            if candidates else "no_supported_experience_candidate"
        ),
        "experience_claim": "not_inferred_from_retrieval_score",
        "experience_candidates": candidates,
        "reviewed_weak_candidates": weak_candidates(bundle),
        "reconsideration_summary": bundle["reconsideration_summary"],
        "llm_relevance_hypothesis": profile.get(
            "llm_relevance_hypothesis"
        ),
    }


def local_source_visibility() -> list[dict[str, Any]]:
    """Expose bounded executor-local experience availability."""
    root = Path.home() / ".local/state/kalaxy3"
    checks = {
        "objective_episode": root / "sage-objective-execution",
        "causal_observation": (
            root / "sage-objective-execution"
            / "path-critic-observations"
        ),
        "runtime_receipts": root / "sage-e2e-zero-trust",
    }
    return [
        {
            "source_type": source_type,
            "availability": (
                "available_local_only"
                if path.exists()
                else "unavailable_on_this_executor"
            ),
            "source_path": str(path),
            "canonical_repository_retrieval": False,
        }
        for source_type, path in checks.items()
    ]


def build_inventory(
    repo: Path,
    seed: dict[str, Any],
) -> dict[str, Any]:
    """Build 'what are you prepared to help with?'."""
    return {
        "projection_type": "experience_inventory",
        "epistemic_rule": (
            "Canonical retrieval surfaces governed experience; "
            "retrieval score is not competence or transferability."
        ),
        "areas": [
            project_profile(repo, profile)
            for profile in seed["experience_inventory_queries"]
        ],
        "supplemental_experience_sources": local_source_visibility(),
    }


def build_intent_projection(
    repo: Path,
    seed: dict[str, Any],
) -> dict[str, Any]:
    """Build intent-relative experience plus LLM innovation."""
    return {
        "projection_type": "intent_relative_experience_and_innovation",
        "architect_intent": seed["architect_intent"],
        "stakeholder_concerns": seed["stakeholder_concerns"],
        "relevant_experience": [
            project_profile(repo, profile)
            for profile in seed["intent_experience_queries"]
        ],
        "llm_innovations": seed["llm_innovations"],
        "unresolved_questions": seed["unresolved_questions"],
        "human_decisions": seed["human_decisions"],
        "tactical_options": seed["tactical_options"],
        "authority_contract": {
            "experience": "SAGE retrieves and preserves provenance",
            "innovation": "LLM proposes beyond experience",
            "decision": "Architect selects objectives and trade-offs",
        },
        "supplemental_experience_sources": local_source_visibility(),
    }


def validate_seed(seed: dict[str, Any]) -> list[str]:
    """Validate canonical retrieval, authority, and innovation boundaries."""
    errors: list[str] = []
    profiles = (
        seed.get("experience_inventory_queries", [])
        + seed.get("intent_experience_queries", [])
    )
    for profile in profiles:
        if not profile.get("retrieval_request"):
            errors.append(
                f"{profile.get('area', '?')} lacks retrieval_request"
            )
        if "terms" in profile:
            errors.append(
                f"{profile.get('area', '?')} retains obsolete terms field"
            )
        if profile.get("assessment_context") not in {
            "experience_inventory",
            "intent_transfer",
        }:
            errors.append(
                f"{profile.get('area', '?')} lacks assessment_context"
            )
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
    """Reject product priority scores while allowing retrieval scores."""
    errors: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            here = f"{path}.{key}" if path else key
            if key.lower() in {
                "priority_score",
                "overall_score",
                "rank_score",
            }:
                errors.append(f"opaque score forbidden at {here}")
            errors.extend(forbid_opaque_scores(child, here))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(
                forbid_opaque_scores(child, f"{path}[{index}]")
            )
    return errors
