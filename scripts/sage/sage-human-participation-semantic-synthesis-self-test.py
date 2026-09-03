#!/usr/bin/env python3
"""Self-test semantic synthesis epistemic boundaries."""

from __future__ import annotations

from copy import deepcopy

from human_participation_semantic_synthesis import validate_proposal


def corpus_fixture() -> dict:
    """Return bounded corpus fixture."""
    return {
        "corpus_sha256": "abc",
        "records": [{
            "evidence_ref": "E1",
            "source_type": "evidence",
            "title": "Evidence one",
            "source_path": "evidence.json",
            "applicable_facts": [{"value": "fact"}],
        }],
    }


def intent_fixture() -> dict:
    """Return intent projection fixture."""
    return {
        "relevant_experience": [{
            "area": "delivery",
            "experience_candidates": [{
                "canonical_result": {"identifier": "E1"}
            }],
            "reviewed_weak_candidates": [],
        }]
    }


def proposal_fixture() -> dict:
    """Return valid LLM proposal fixture."""
    return {
        "producer_class": "llm",
        "corpus_sha256": "abc",
        "semantic_claim_status": "llm_derived_not_fact",
        "experience_themes": [{
            "theme": "delivery",
            "epistemic_status": "llm_derived",
            "why_this_theme": "Repeated delivery evidence is present.",
            "evidence_refs": ["E1"],
            "limits": ["fixture"],
        }],
        "intent_applicability": [{
            "intent_area": "delivery",
            "semantic_relationship": "directly_relevant",
            "epistemic_status": "llm_derived",
            "why": "Evidence directly concerns delivery.",
            "evidence_refs": ["E1"],
            "assumptions": [],
            "unknowns": [],
            "transfer_decision": "requires_architect_judgment",
        }],
        "innovation_beyond_experience": [{
            "proposal": "Novel option",
            "why": "Experience is not a hard boundary.",
            "epistemic_status": "llm_proposed",
            "experience_dependency": "none",
            "decision_authority": "Architect",
        }],
        "architect_authority": (
            "Architect decides objectives, trade-offs, and whether to transfer "
            "experience into action."
        ),
    }


def main() -> int:
    """Exercise citation and authority failures."""
    corpus = corpus_fixture()
    intent = intent_fixture()
    proposal = proposal_fixture()
    assert not validate_proposal(proposal, corpus, intent)

    bad = deepcopy(proposal)
    bad["experience_themes"][0]["evidence_refs"] = ["UNKNOWN"]
    assert validate_proposal(bad, corpus, intent)

    bad = deepcopy(proposal)
    bad["intent_applicability"][0]["epistemic_status"] = "demonstrated"
    assert validate_proposal(bad, corpus, intent)

    bad = deepcopy(proposal)
    bad["innovation_beyond_experience"][0][
        "decision_authority"
    ] = "LLM"
    assert validate_proposal(bad, corpus, intent)

    print("PASS LLM themes require governed evidence citations")
    print("PASS unknown evidence citations are rejected")
    print("PASS semantic judgment cannot promote itself to demonstrated")
    print("PASS innovation may exceed experience but not Architect authority")
    print("SAGE semantic synthesis self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
