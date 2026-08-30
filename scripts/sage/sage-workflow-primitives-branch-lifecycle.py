#!/usr/bin/env python3
"""Operate the governed SAGE branch-lifecycle composition."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import GitAuthoritySnapshot, OperatorGitProposal, WorkflowError  # noqa: E402
from workflows.branch_lifecycle import (  # noqa: E402
    continue_branch_lifecycle,
    start_branch_bootstrap,
    start_branch_closeout,
)


def self_test() -> int:
    snapshot = GitAuthoritySnapshot(
        path="/tmp/repo",
        branch="feature/old",
        head="a" * 40,
        upstream_head="a" * 40,
        working_tree_status="clean",
        changed_paths=(),
    )
    common = dict(
        controller="sage.branch-lifecycle",
        repository=snapshot,
        authority_receipt="/tmp/authority.json",
        component_manifest="/tmp/component.json",
        validation=(
            {
                "label": "fixture",
                "reference": "fixture",
                "status": "pass",
                "sha256": "0" * 64,
            },
        ),
        expected_result="fixture",
        risk="fixture",
        rollback="fixture",
        post_command_verification=("git branch --show-current",),
        created_at="2026-08-16T00:00:00-05:00",
    )
    cases = (
        ("SAGE-GIT-20260816-001", "create-branch", ("git", "switch", "-c", "feature/new", "a" * 40), ("refs/heads/feature/new",)),
        ("SAGE-GIT-20260816-002", "push", ("git", "push", "-u", "origin", "feature/new"), ("refs/heads/feature/new",)),
        ("SAGE-GIT-20260816-003", "switch-branch", ("git", "switch", "main"), ("refs/heads/main",)),
        ("SAGE-GIT-20260816-004", "other-git-mutation", ("git", "merge", "--ff-only", "b" * 40), ("refs/heads/main",)),
        ("SAGE-GIT-20260816-005", "push", ("git", "push", "origin", "--delete", "feature/old"), ("refs/heads/feature/old",)),
        ("SAGE-GIT-20260816-006", "branch-delete", ("git", "branch", "-d", "feature/old"), ("refs/heads/feature/old",)),
    )
    for proposal_id, boundary, argv, change_scope in cases:
        proposal = OperatorGitProposal.build(
            proposal_id=proposal_id,
            boundary=boundary,
            change_scope=change_scope,
            command_argv=argv,
            **common,
        )
        if proposal["boundary"] != boundary or proposal["command"]["command_count"] != 1:
            raise RuntimeError(f"{boundary} proposal contract failed")
    print("PASS bootstrap and post-promotion closeout remain separate one-command operator boundaries")
    print("PASS fast-forward, remote retirement, and local retirement use existing operator proposal boundaries")
    print("PASS branch lifecycle reuses git.inspect and operator.git-proposal without direct mutation")
    print("Kalaxy3 SAGE branch lifecycle self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start")
    start.add_argument("--request", required=True)
    start.add_argument("--branch", required=True)
    start.add_argument("--expected-main", required=True)

    closeout = sub.add_parser("closeout")
    closeout.add_argument("--request", required=True)
    closeout.add_argument("--objective-id", required=True)
    closeout.add_argument("--source-branch", required=True)
    closeout.add_argument("--promoted-source", required=True)
    closeout.add_argument("--expected-main", required=True)

    cont = sub.add_parser("continue")
    cont.add_argument("--state", type=Path, required=True)
    cont.add_argument("--operator-result", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if args.command == "start":
        result = start_branch_bootstrap(
            args.repo,
            request=args.request,
            branch=args.branch,
            expected_main=args.expected_main,
        )
    elif args.command == "closeout":
        result = start_branch_closeout(
            args.repo,
            request=args.request,
            objective_id=args.objective_id,
            source_branch=args.source_branch,
            promoted_source=args.promoted_source,
            expected_main=args.expected_main,
        )
    elif args.command == "continue":
        result = continue_branch_lifecycle(args.repo, args.state, args.operator_result)
    else:
        raise WorkflowError("one branch-lifecycle command is required")
    print("Kalaxy3 SAGE branch lifecycle: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE branch lifecycle: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
