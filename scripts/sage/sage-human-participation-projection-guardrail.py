#!/usr/bin/env python3
"""Guardrail for the persisted human-participation projection example."""

from __future__ import annotations

import json
from pathlib import Path

from human_participation_projection import validate_projection


def main() -> int:
    """Validate the checked-in example against the projection contract."""
    path = Path("sage-human-participation-projection-example.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_projection(value)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 2
    context = value["epistemic_context"]
    assert context["context_only_concepts"]
    questions = value["questions"]
    assert questions["where_do_you_need_me"][0]["authority"] == "Architect"
    print("PASS explicit epistemic identity and provenance")
    print("PASS three stakeholder-value questions")
    print("PASS Architect decision boundary")
    print("PASS context-only concepts remain visible")
    print("PASS opaque aggregate scoring forbidden")
    print("Kalaxy3 SAGE human-participation projection guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
