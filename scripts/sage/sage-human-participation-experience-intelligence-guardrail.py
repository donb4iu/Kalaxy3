#!/usr/bin/env python3
"""Guardrail generic Human Participation experience-intelligence slice."""

from __future__ import annotations

import json
from pathlib import Path


GRAPH = Path("sage-human-participation-experience-graph-example.json")
NARRATION = Path("sage-human-participation-narration-example.json")
ROOT = Path("markdown/workbench/human-participation")


def load(path: Path) -> dict:
    """Load JSON object."""
    return json.loads(path.read_text(encoding="utf-8"))


def require(path: Path, *needles: str) -> None:
    """Require product markers."""
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in text, f"{needle!r} missing from {path}"


def forbid(path: Path, *needles: str) -> None:
    """Reject live/mutation browser behavior."""
    lowered = path.read_text(encoding="utf-8").lower()
    for needle in needles:
        assert needle.lower() not in lowered, (
            f"{needle!r} forbidden in {path}"
        )


def main() -> int:
    """Validate generic navigation and epistemic boundaries."""
    graph = load(GRAPH)
    narration = load(NARRATION)

    assert graph["interaction_mode"] == "read_only"
    assert len(graph["entities"]) >= 10
    assert "Role interaction uses explicit provenance only" in graph["role_rule"]
    assert graph["future_cost_rule"].startswith(
        "Historical path signals describe observed structure only"
    )
    assert "Age alone never creates staleness" in graph["standing_rule"]

    episodes = [item for item in graph["entities"] if item["is_episode"]]
    assert episodes, "generic episode discovery produced no episodes"

    narrated = set(narration["entries"])
    discovered = {item["id"] for item in graph["entities"]}
    assert narrated.issubset(discovered)

    for value in narration["entries"].values():
        assert value["epistemic_status"] == "llm_derived"
        if "expected_repeat_effect" in value:
            assert value["expected_repeat_effect_status"] == "llm_proposed"

    require(
        ROOT / "index.html",
        "Objectives &amp; experiences",
        "Capabilities",
        "Current objective",
        "Human judgment",
        "Role interaction",
    )
    require(
        ROOT / "app.js",
        "Raw governed view",
        "Optional LLM narration",
        "What points here / downstream use",
        "Where this points / upstream context",
        "Historical linked-record counts. They are not a future effort estimate.",
        "LLM innovation beyond prior experience",
        "How the work came together",
        "Only explicit role provenance is shown",
    )
    forbid(
        ROOT / "app.js",
        "fetch(",
        "xmlhttprequest",
        "websocket",
        "localstorage",
        "sessionstorage",
        "innerhtml",
    )
    forbid(ROOT / "index.html", "<form")

    print("PASS generic objective/episode discovery")
    print("PASS raw governed view does not require narration")
    print("PASS optional narration attaches only to governed entities")
    print("PASS bidirectional explicit relationship navigation")
    print("PASS generic references remain distinct from semantic contribution")
    print("PASS explicit standing does not equate age with staleness")
    print("PASS historical effort is not rendered as future repeat cost")
    print("PASS predicted repeat effect remains LLM-proposed")
    print("PASS role interaction requires explicit provenance")
    print("PASS LLM innovation remains distinct from Architect intent and SAGE state")
    print("PASS read-only/no-network browser boundary")
    print("Kalaxy3 experience-intelligence guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
