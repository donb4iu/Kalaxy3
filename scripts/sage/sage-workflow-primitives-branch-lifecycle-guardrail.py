#!/usr/bin/env python3
"""Guardrail for the SAGE branch-lifecycle composition."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "scripts/sage/workflows/branch_lifecycle.py"
CLI = ROOT / "scripts/sage/sage-workflow-primitives-branch-lifecycle.py"


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    required = (
        "GitInspector",
        "OperatorGitProposal",
        'boundary="create-branch"',
        'boundary="push"',
        "expected_main",
        "remote_head",
        "require_clean",
        "require_upstream_equal",
        "architect_intervention",
    )
    missing = [item for item in required if item not in workflow]
    if missing:
        raise RuntimeError(f"branch lifecycle contract markers missing: {missing}")
    forbidden = (
        "GitRepository",
        "subprocess.",
        "os.system",
        "git checkout",
        "git switch -c",
        "git push -u",
    )
    observed = [item for item in forbidden if item in workflow]
    if observed:
        raise RuntimeError(f"branch lifecycle workflow contains direct mutation path: {observed}")
    if "--self-test" not in cli or "start_branch_bootstrap" not in cli or "continue_branch_bootstrap" not in cli:
        raise RuntimeError("branch lifecycle CLI does not expose the governed composition")
    print("PASS branch creation and push are operator-proposal boundaries")
    print("PASS branch lifecycle workflow has no direct Git mutation implementation")
    print("PASS exact frozen-main and post-operator verification markers")
    print("Kalaxy3 SAGE branch lifecycle guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
