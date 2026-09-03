#!/usr/bin/env python3
"""Guardrail persisted experience and intent examples."""

from __future__ import annotations

import json
from pathlib import Path

from human_participation_experience_projection import forbid_opaque_scores


def load(path: str) -> dict:
    """Load a persisted projection."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    """Validate stakeholder and epistemic boundaries."""
    inventory = load(
        "sage-human-participation-experience-inventory-example.json"
    )
    intent = load("sage-human-participation-intent-projection-example.json")
    assert inventory["projection_type"] == "experience_inventory"
    for area in inventory["areas"]:
        assert area["experience_claim"] == "not_inferred_from_retrieval_alone"
    assert intent["architect_intent"]["authority"] == "Architect"
    assert intent["stakeholder_concerns"]
    for proposal in intent["llm_innovations"]:
        assert proposal["epistemic_status"] == "llm_proposed"
    for option in intent["tactical_options"]:
        assert option["epistemic_status"] == "llm_proposed"
    for decision in intent["human_decisions"]:
        assert decision["authority"] == "Architect"
    assert not forbid_opaque_scores([inventory, intent])
    print("PASS experience retrieval does not imply competence")
    print("PASS LLM innovation can extend beyond prior experience")
    print("PASS Architect retains objective/trade-off authority")
    print("PASS stakeholder concerns are intent-centered")
    print("PASS no opaque aggregate priority score")
    print("Kalaxy3 SAGE experience + innovation guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
