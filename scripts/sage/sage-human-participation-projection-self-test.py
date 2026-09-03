#!/usr/bin/env python3
"""Self-test for SAGE human-participation projection semantics."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from human_participation_projection import project, validate_projection


def write_fixture(root: Path) -> tuple[Path, Path]:
    """Write a minimal audit and Architect-intent fixture."""
    audit = {
        "coverage": [
            {
                "concept": "stakeholder_concerns",
                "status": "documented_context",
            },
            {
                "concept": "strategic_objectives",
                "status": "structured_explicit",
            },
        ],
        "coverage_disposition": {
            "reuse": ["strategic_objectives"],
            "normalize_or_project": ["stakeholder_concerns"],
            "candidate_gap": [],
        },
        "epic_catalog_projection": [{"category": "legacy-evidence"}],
        "runtime_evidence_inventory": {"state_root_available": False},
    }
    audit_path = root / "audit.json"
    epic_path = root / "epic.md"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    epic_path.write_text("Architect intent", encoding="utf-8")
    return audit_path, epic_path


def main() -> int:
    """Exercise positive and negative contract behavior."""
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        audit, epic = write_fixture(root)
        value = project(audit, epic, "fixture-commit")
        assert not validate_projection(value)
        assert value["epistemic_context"]["candidate_first_class_gaps"] == []
        assert value["provenance_issues"]
        option = value["questions"][
            "where_should_we_spend_next_unit_of_effort"
        ][1]
        assert option["disposition"] == "not_yet_justified"
        value["priority_score"] = 99
        errors = validate_projection(value)
        assert any("opaque score forbidden" in item for item in errors)
    print("SAGE human participation projection self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
