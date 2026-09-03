#!/usr/bin/env python3
"""Guardrail persisted Human Participation semantic synthesis."""

from __future__ import annotations

import json
from pathlib import Path


def load(path: str) -> dict:
    """Load JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    """Validate persisted product-level semantics."""
    corpus = load("sage-human-participation-semantic-experience-corpus.json")
    proposal = load("sage-human-participation-semantic-synthesis-proposal.json")
    synthesis = load("sage-human-participation-semantic-synthesis-example.json")

    assert corpus["corpus_scope"] == "bounded_governed_experience_snapshot"
    assert corpus["completeness_claim"] == "not_exhaustive"
    assert len(corpus["records"]) >= 5

    assert len(proposal["experience_themes"]) >= 3
    assert all(
        item["epistemic_status"] == "llm_derived"
        for item in proposal["experience_themes"]
    )
    assert all(
        item["evidence_refs"]
        for item in proposal["experience_themes"]
    )

    relationships = {
        item["semantic_relationship"]
        for item in synthesis["intent_applicability"]
    }
    assert "directly_relevant" in relationships
    assert "analogous" in relationships or "weak_or_uncertain" in relationships

    assert synthesis["validation"]["evidence_citations_resolved"] is True
    assert (
        synthesis["validation"]["semantic_truth_validated_by_sage"]
        is False
    )
    assert synthesis["validation"]["epistemic_boundaries_validated"] is True

    assert any(
        item.get("experience_dependency") == "none"
        for item in synthesis["innovation_beyond_experience"]
    )
    assert synthesis["architect_authority"].startswith("Architect decides")

    print("PASS bounded corpus is not mislabeled exhaustive")
    print("PASS experience inventory themes are LLM-derived from evidence")
    print("PASS intent applicability is semantic judgment, not retrieval score")
    print("PASS SAGE validates citations without claiming semantic truth")
    print("PASS innovation remains possible without prior experience")
    print("PASS Architect retains transfer and action authority")
    print("Kalaxy3 semantic synthesis guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
