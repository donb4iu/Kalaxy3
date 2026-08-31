#!/usr/bin/env python3
"""Guard candidate persistence as authorization, not Git mutation."""

from pathlib import Path


def main() -> int:
    """Validate the bounded composition."""
    repo = Path(__file__).resolve().parents[2]
    workflow = (
        repo / "scripts/sage/workflows/candidate_persistence.py"
    ).read_text(encoding="utf-8")
    controller = (
        repo / "scripts/sage/workflows/routine_git_lifecycle.py"
    ).read_text(encoding="utf-8")
    required = (
        "OperatorGitProposal.build(",
        "inspector.require_exact_paths(",
        "snapshot.upstream_head != snapshot.head",
        "sage-routine-git-lifecycle.py",
    )
    if any(item not in workflow for item in required):
        raise RuntimeError("candidate persistence contract is incomplete")
    prohibited = ("GitRepository(", "subprocess.", "git commit", "git push")
    if any(item in workflow for item in prohibited):
        raise RuntimeError("candidate persistence owns direct Git mutation")
    if (
        "sage-candidate-persistence-state" not in controller
        or "sage.candidate-persistence" not in controller
    ):
        raise RuntimeError("routine controller lacks candidate owner")
    print("PASS candidate persistence only builds authorization")
    print("PASS routine Git controller remains mutation owner")
    print("Kalaxy3 SAGE candidate persistence guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
