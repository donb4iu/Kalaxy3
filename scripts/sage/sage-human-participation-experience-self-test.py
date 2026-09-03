#!/usr/bin/env python3
"""Self-test canonical experience relationship and seed semantics."""

from __future__ import annotations

from copy import deepcopy

from human_participation_canonical_experience import (
    apply_finalization,
    finalization,
    relationship,
)
from human_participation_experience_projection import (
    forbid_opaque_scores,
    validate_seed,
)
from sage_evidence_retrieval import retrieval_basis_sha256


def result_fixture() -> dict:
    """Return one canonical-result-shaped fixture."""
    return {
        "rank": 1,
        "source_type": "evidence",
        "identifier": "E1",
        "title": "Artifact promotion",
        "source_path": "catalog.json",
        "record_path": "",
        "status": "validated",
        "score": 10,
        "matched_terms": ["artifact", "promotion"],
        "matched_groups": [],
        "reasons": ["fixture"],
        "confidence": {
            "value": "not-recorded",
            "source_field": "",
            "basis": "not-recorded",
        },
        "applicable_facts": [{
            "source_field": "summary",
            "value": "artifact promotion",
            "matched_terms": ["artifact", "promotion"],
        }],
        "source_section": {
            "record_field": "summary",
            "navigation_section": "",
            "source_document": "",
        },
        "recency": {
            "value": "",
            "source_field": "",
            "basis": "not-recorded",
        },
        "disposition": "pending",
        "disposition_rationale": "",
        "applicability": "pending",
        "value_effect": "pending",
        "alternative_effect": "pending",
        "augmentations": [],
        "additional_acceptance_criteria": [],
        "reconsideration_trigger": "",
    }


def main() -> int:
    """Prove wrapper and seed migration boundaries."""
    profile = {
        "direct_terms": ["artifact", "promotion", "digest"],
        "analogous_terms": ["provenance", "executor"],
        "direct_min_hits": 2,
    }
    item = result_fixture()
    relation = relationship(item, profile)
    assert relation["experience_relationship"] == "direct"

    payload = {
        "schema_version": "1.1",
        "algorithm_version": "fixture",
        "request": "fixture",
        "policy_sha256": "fixture",
        "sources": [],
        "results": [item],
    }
    payload["retrieval_basis_sha256"] = retrieval_basis_sha256(payload)
    before = payload["retrieval_basis_sha256"]

    finalized = deepcopy(payload)
    apply_finalization(
        finalized["results"][0],
        finalization("direct", "experience_inventory"),
    )
    assert retrieval_basis_sha256(finalized) == before
    assert "experience_relationship" not in finalized["results"][0]

    valid_seed = {
        "experience_inventory_queries": [{
            "area": "x",
            "retrieval_request": "retrieve x",
            "assessment_context": "experience_inventory",
        }],
        "intent_experience_queries": [],
        "llm_innovations": [{"epistemic_status": "llm_proposed"}],
        "tactical_options": [{"epistemic_status": "llm_proposed"}],
        "human_decisions": [{"authority": "Architect"}],
    }
    assert not validate_seed(valid_seed)

    old_seed = deepcopy(valid_seed)
    profile = old_seed["experience_inventory_queries"][0]
    profile.pop("retrieval_request")
    profile["terms"] = ["x"]
    assert validate_seed(old_seed)

    assert not forbid_opaque_scores({"retrieval_score": 42})
    assert forbid_opaque_scores({"priority_score": 42})

    print("PASS relationship metadata stays outside canonical result")
    print("PASS finalization preserves immutable retrieval basis")
    print("PASS obsolete projection-local seed format is rejected")
    print("PASS canonical retrieval seed is required")
    print("SAGE canonical experience relationship self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
