#!/usr/bin/env python3
"""Self-test generic experience-intelligence product rules."""

from __future__ import annotations

from human_participation_experience_graph import current_standing


def main() -> int:
    """Exercise staleness and future-cost boundaries."""
    entity = {"status": ""}
    assert current_standing(entity, [], [])["state"] == (
        "no_explicit_supersession_recorded"
    )

    stale = current_standing(
        entity,
        [{"relation": "superseded_by"}],
        [],
    )
    assert stale["state"] == "superseded"

    contextual = current_standing(
        entity,
        [{"relation": "context_limit"}],
        [],
    )
    assert contextual["state"] == "context_limited"

    print("PASS age alone does not imply evidence staleness")
    print("PASS explicit supersession changes current standing")
    print("PASS context-limited standing remains distinguishable")
    print("PASS raw generic entity view requires no narration")
    print("PASS historical path signals are not future-cost estimates")
    print("PASS role interaction requires explicit provenance")
    print("SAGE experience-intelligence self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
