#!/usr/bin/env python3
"""Inspect or propose/update one SAGE Project work item using trusted credentials."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from workflow.projects_credentials import ProjectsCredentialError, resolve_projects_token
from workflow.projects_inspect import ProjectsInspectionError, inspect_issue_work_item
from workflow.projects_operational import ProjectsOperationError, update_operational_status


def parse_arguments() -> argparse.Namespace:
    """Parse the bounded, participant-independent Project operation request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-source", choices=("actions-secret", "vault-file"), required=True)
    parser.add_argument("--owner", default="donb4iu")
    parser.add_argument("--project-number", type=int, default=15)
    parser.add_argument("--repository", default="donb4iu/Kalaxy3")
    parser.add_argument("--issue-number", type=int, default=44)
    parser.add_argument("--action", choices=("read", "propose-status", "apply-status"), default="read")
    parser.add_argument("--new-status", choices=("Todo", "In Progress", "Blocked"))
    parser.add_argument("--expected-issue-sha256")
    parser.add_argument("--expected-status-updated-at")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def execute(args: argparse.Namespace, environment: dict[str, str]) -> dict[str, Any]:
    """Execute an exact operation and return nonsecret, attributable evidence.

    Args:
        args: Parsed, bounded operation request.
        environment: Trusted executor's environment, never LLM-supplied.
    """
    token = resolve_projects_token(args.credential_source, environment)
    if args.action == "read":
        item = inspect_issue_work_item(token, args.owner, args.project_number,
                                      args.repository, args.issue_number)
        return {"record_type": "sage-projects-live-readback", "live": True,
                "source": args.credential_source, "work_item": item,
                "issue_body_sha256": hashlib.sha256(
                    item["body"].encode("utf-8")
                ).hexdigest(), "architect_approval": "not_implied"}
    if not all((args.new_status, args.expected_issue_sha256,
                args.expected_status_updated_at)):
        raise ProjectsOperationError("Update requires status and exact prior evidence")
    apply = args.action == "apply-status"
    if apply and environment.get("SAGE_PROJECTS_APPLY_AUTHORIZED") != "true":
        raise ProjectsOperationError("Trusted runtime did not authorize status application")
    actor = (environment.get("GITHUB_ACTOR") if args.credential_source == "actions-secret"
             else environment.get("SAGE_EXECUTOR_ID")) or ""
    receipt = update_operational_status(
        token, owner=args.owner, project_number=args.project_number,
        repository=args.repository, issue_number=args.issue_number,
        new_status=args.new_status, expected_issue_digest=args.expected_issue_sha256,
        expected_status_timestamp=args.expected_status_updated_at,
        actor=actor, apply=apply,
    )
    return {"record_type": "sage-projects-operational-status", "source": args.credential_source,
            "receipt": receipt, "approval_authority": "none"}


def main() -> int:
    """Produce one file-backed receipt, with no credentials in stdout or artifacts."""
    args = parse_arguments()
    try:
        evidence = execute(args, dict(os.environ))
    except (ProjectsCredentialError, ProjectsInspectionError, ProjectsOperationError) as exc:
        print(f"SAGE_PROJECTS_RESULT=FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(f"SAGE_PROJECTS_RESULT={'READBACK_VERIFIED' if args.action == 'read' else 'STATUS_EVALUATED'}")
    print(f"SAGE_PROJECTS_EVIDENCE={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
