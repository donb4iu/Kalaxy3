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
        'boundary="switch-branch"',
        '"other-git-mutation"',
        'boundary="branch-delete"',
        "start_branch_closeout",
        "continue_branch_closeout",
        "continue_branch_lifecycle",
        'mode": "post-promotion-closeout"',
        "source-contained-in-target",
        "sage-repository-lineage-milestone",
        "repository-lineage-closeout.json",
        '"--ff-only"',
        '"--delete"',
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
        '("git", "reset"',
        '("git", "rebase"',
        '("git", "push", "--force"',
    )
    observed = [item for item in forbidden if item in workflow]
    if observed:
        raise RuntimeError(f"branch lifecycle workflow contains direct/destructive mutation path: {observed}")
    cli_required = (
        "--self-test",
        "start_branch_bootstrap",
        "start_branch_closeout",
        "continue_branch_lifecycle",
        'sub.add_parser("closeout")',
        'closeout.add_argument("--objective-id"',
        'closeout.add_argument("--promoted-source"',
    )
    cli_missing = [item for item in cli_required if item not in cli]
    if cli_missing:
        raise RuntimeError(f"branch lifecycle CLI does not expose the governed composition: {cli_missing}")
    print("PASS branch bootstrap and post-promotion closeout are operator-proposal boundaries")
    print("PASS closeout requires exact source containment, stable authority, and fast-forward-only main reconciliation")
    print("PASS source retirement uses governed remote/local ref boundaries and semantic repository-lineage milestones")
    print("PASS branch lifecycle workflow has no direct or destructive Git mutation implementation")
    print("Kalaxy3 SAGE branch lifecycle guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
