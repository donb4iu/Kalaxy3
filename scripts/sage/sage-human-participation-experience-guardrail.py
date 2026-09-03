#!/usr/bin/env python3
"""Guardrail canonical experience + innovation projections."""

from __future__ import annotations

import json
from pathlib import Path

from human_participation_experience_projection import forbid_opaque_scores


def load(path: str) -> dict:
    """Load one projection."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def find_area(payload: dict, area: str) -> dict:
    """Find one projected experience area."""
    return next(item for item in payload["areas"] if item["area"] == area)


def require_candidate(area: dict) -> None:
    """Require one governed non-weak experience candidate."""
    assert area["retrieval_status"] == "canonical_experience_candidates_found"
    assert area["retrieval_basis_preserved"] is True
    assert area["experience_candidates"]
    for wrapper in area["experience_candidates"]:
        result = wrapper["canonical_result"]
        assert wrapper["experience_relationship"] in {
            "direct",
            "analogous",
            "contradictory",
        }
        assert wrapper["score_semantics"] == (
            "retrieval_relevance_not_applicability"
        )
        assert result["source_path"]
        assert result["applicable_facts"]
        assert "experience_relationship" not in result


def main() -> int:
    """Validate regressions, provenance, and authority."""
    inventory = load(
        "sage-human-participation-experience-inventory-example.json"
    )
    intent = load("sage-human-participation-intent-projection-example.json")

    artifact = find_area(inventory, "artifact_identity_and_promotion")
    zero_trust = find_area(inventory, "zero_trust_runtime")
    require_candidate(artifact)
    require_candidate(zero_trust)

    artifact_ids = {
        item["canonical_result"]["identifier"]
        for item in artifact["experience_candidates"]
    }
    assert "SAGE-ACTION-20260815-002" in artifact_ids

    for area in intent["relevant_experience"]:
        assert area["retrieval_basis_preserved"] is True
        for wrapper in area["experience_candidates"]:
            result = wrapper["canonical_result"]
            assert result["applicability"] == "requires-revalidation"
            assert result["disposition"] == "requires-revalidation"

    assert intent["architect_intent"]["authority"] == "Architect"
    for proposal in intent["llm_innovations"]:
        assert proposal["epistemic_status"] == "llm_proposed"
    for option in intent["tactical_options"]:
        assert option["epistemic_status"] == "llm_proposed"
    for decision in intent["human_decisions"]:
        assert decision["authority"] == "Architect"
    assert not forbid_opaque_scores([inventory, intent])

    print("PASS canonical retrieval immutable basis preserved")
    print("PASS prior artifact-promotion retrieval miss corrected")
    print("PASS prior zero-trust retrieval miss corrected")
    print("PASS relationship metadata wraps rather than rewrites evidence")
    print("PASS intent transfer remains requires-revalidation")
    print("PASS LLM innovation remains distinct from experience")
    print("PASS Architect retains consequential authority")
    print("Kalaxy3 canonical experience projection guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
