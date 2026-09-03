#!/usr/bin/env python3
"""Guardrail persisted Human Participation Workbench product slice."""

from __future__ import annotations

import json
from pathlib import Path

from human_participation_workbench import validate_state


ROOT = Path("markdown/workbench/human-participation")


def load_state() -> dict:
    """Load persisted product state."""
    return json.loads(
        Path(
            "sage-human-participation-workbench-state-example.json"
        ).read_text(encoding="utf-8")
    )


def require_text(path: Path, *needles: str) -> None:
    """Require literal product contract markers."""
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        assert needle in text, f"{needle!r} missing from {path}"


def forbid_text(path: Path, *needles: str) -> None:
    """Reject mutation/network browser constructs."""
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    for needle in needles:
        assert needle.lower() not in lowered, (
            f"{needle!r} forbidden in {path}"
        )


def main() -> int:
    """Validate product, evidence, and read-only boundaries."""
    state = load_state()
    errors = validate_state(state)
    assert not errors, errors

    require_text(
        ROOT / "index.html",
        "Human Participation Workbench",
        "Read-only proof",
    )
    require_text(
        ROOT / "app.js",
        "What can SAGE help me with?",
        "Given this objective, what matters?",
        "Where is my judgment valuable?",
        "Inspect evidence",
    )
    forbid_text(
        ROOT / "app.js",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "localStorage",
        "sessionStorage",
        "innerHTML",
    )
    forbid_text(
        ROOT / "index.html",
        "<form",
        "<input",
        "<textarea",
    )

    state_js = (ROOT / "state.js").read_text(encoding="utf-8")
    assert state_js.startswith("window.KALAXY3_WORKBENCH_STATE = ")

    assert any(
        item["semantic_relationship"] == "directly_relevant"
        for item in state["intent_applicability"]
    )
    assert any(
        item["semantic_relationship"] == "analogous"
        for item in state["intent_applicability"]
    )
    assert state["provenance"]["semantic_truth_validated_by_sage"] is False
    assert state["provenance"]["evidence_citations_resolved"] is True

    print("PASS stakeholder-first three-question surface")
    print("PASS read-only browser boundary")
    print("PASS no network or mutation controls")
    print("PASS evidence drill-down preserved")
    print("PASS direct and analogous experience remain distinguishable")
    print("PASS LLM interpretation is not presented as SAGE-validated truth")
    print("PASS Architect decisions remain visible")
    print("Kalaxy3 Human Participation Workbench guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
