#!/usr/bin/env python3
"""Self-test experience plus innovation boundaries."""

from __future__ import annotations

from human_participation_experience_projection import (
    build_intent_projection,
    build_inventory,
    forbid_opaque_scores,
    validate_seed,
)


def fixture_seed() -> dict:
    """Return a valid working seed."""
    return {
        "architect_intent": {"statement": "Improve outcome X"},
        "stakeholder_concerns": ["reliability"],
        "experience_inventory_queries": [{
            "area": "delivery",
            "question": "Delivery experience?",
            "terms": ["artifact", "promotion"],
        }],
        "intent_experience_queries": [{
            "area": "delivery",
            "question": "Relevant delivery experience?",
            "terms": ["artifact"],
        }],
        "llm_innovations": [{
            "proposal": "Try a new path",
            "epistemic_status": "llm_proposed",
        }],
        "unresolved_questions": ["Which path is limiting?"],
        "human_decisions": [{
            "decision": "Choose trade-off",
            "authority": "Architect",
        }],
        "tactical_options": [{
            "candidate": "experiment",
            "epistemic_status": "llm_proposed",
        }],
    }


def main() -> int:
    """Exercise match, no-match, and authority semantics."""
    catalog = {
        "records": [{
            "id": "E1",
            "title": "Artifact promotion validation",
            "summary": "Promotion preserved artifact identity.",
        }]
    }
    seed = fixture_seed()
    assert not validate_seed(seed)
    inventory = build_inventory(seed, catalog)
    area = inventory["areas"][0]
    assert area["retrieval_status"] == (
        "repository_evidence_candidates_found"
    )
    assert area["experience_claim"] == "not_inferred_from_retrieval_alone"
    intent = build_intent_projection(seed, catalog)
    assert intent["llm_innovations"][0]["epistemic_status"] == "llm_proposed"
    assert intent["human_decisions"][0]["authority"] == "Architect"
    assert not forbid_opaque_scores([inventory, intent])
    seed["experience_inventory_queries"][0]["terms"] = ["never-found-term"]
    no_match = build_inventory(seed, catalog)["areas"][0]
    assert no_match["retrieval_status"] == "no_bounded_catalog_match"
    print("SAGE experience + innovation projection self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
