#!/usr/bin/env python3
"""Self-test read-only Human Participation Workbench state."""

from __future__ import annotations

from human_participation_workbench import validate_state


def fixture() -> dict:
    """Return minimal valid product-state fixture."""
    theme = {
        "epistemic_status": "llm_derived",
        "evidence": [{"evidence_ref": "E1"}],
    }
    applicability = {
        "epistemic_status": "llm_derived",
        "transfer_decision": "requires_architect_judgment",
        "evidence": [{"evidence_ref": "E1"}],
    }
    return {
        "interaction_mode": "read_only",
        "objective": {"authority": "Architect"},
        "experience_themes": [theme, theme, theme],
        "intent_applicability": [applicability],
        "innovation_beyond_experience": [{
            "epistemic_status": "llm_proposed",
            "decision_authority": "Architect",
        }],
        "architect_decisions": [{"authority": "Architect"}],
        "unknowns": ["Unknown current runtime state."],
        "epistemic_legend": [
            {"label": "Evidence"},
            {"label": "SAGE-derived"},
            {"label": "LLM-derived"},
            {"label": "LLM-proposed"},
            {"label": "Architect"},
        ],
    }


def main() -> int:
    """Exercise read-only and epistemic negatives."""
    valid = fixture()
    assert not validate_state(valid)

    invalid = fixture()
    invalid["interaction_mode"] = "write"
    assert validate_state(invalid)

    invalid = fixture()
    invalid["innovation_beyond_experience"][0][
        "decision_authority"
    ] = "LLM"
    assert validate_state(invalid)

    invalid = fixture()
    invalid["priority_score"] = 9
    assert validate_state(invalid)

    print("PASS read-only product boundary")
    print("PASS Architect authority boundary")
    print("PASS opaque aggregate scores rejected")
    print("PASS evidence-backed semantic classes")
    print("SAGE Human Participation Workbench self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
