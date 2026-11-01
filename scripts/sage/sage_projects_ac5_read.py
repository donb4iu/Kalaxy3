#!/usr/bin/env python3
"""Qualify a read-only GitHub Project #15 read from the protected Actions job."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from workflow.projects_inspect import ProjectsInspectionError, inspect_issue_work_item


class Ac5ReadbackError(RuntimeError):
    """Report a missing trusted runtime or an incomplete work contract."""


def create_receipt(environment: Mapping[str, str]) -> dict[str, Any]:
    """Inspect Project #15 and create a nonsecret, source-attributed receipt.

    Args:
        environment: Trusted GitHub Actions execution environment.
    """
    if (environment.get("GITHUB_ACTIONS") != "true"
            or environment.get("GITHUB_REF") != "refs/heads/main"
            or environment.get("GITHUB_REPOSITORY") != "donb4iu/Kalaxy3"):
        raise Ac5ReadbackError("Trusted main-branch Actions runtime required")
    if not environment.get("GITHUB_ACTOR") or not environment.get("GITHUB_RUN_ID"):
        raise Ac5ReadbackError("GitHub run and actor attribution required")
    token = environment.get("SAGE_PROJECTS_CREDENTIAL", "")
    if not token:
        raise Ac5ReadbackError("Governed Projects credential unavailable")
    item = inspect_issue_work_item(token, "donb4iu", 15, "donb4iu/Kalaxy3", 44)
    if "Architect-approved Project/RACI Definition of Done" not in item["body"]:
        raise Ac5ReadbackError("Approved Project/RACI DoD absent from live issue")
    if not item.get("status_updated_at") or not item.get("item_id"):
        raise Ac5ReadbackError("Project status or item identity unverified")
    return {
        "record_type": "sage-issue44-ac5-readonly-candidate",
        "repository": item["repository"],
        "issue_number": item["issue_number"],
        "project_number": item["project_number"],
        "item_id": item["item_id"],
        "issue_id": item["issue_id"],
        "issue_body_sha256": hashlib.sha256(item["body"].encode()).hexdigest(),
        "issue_updated_at": item["issue_updated_at"],
        "status": item["status"],
        "status_updated_at": item["status_updated_at"],
        "assignees": item["assignees"],
        "not_retrieved": item["not_retrieved"],
        "source_sha": environment.get("GITHUB_SHA", ""),
        "run_id": environment["GITHUB_RUN_ID"],
        "actor": environment["GITHUB_ACTOR"],
        "ac5_disposition": "live_read_candidate_independent_review_required",
        "architect_approval": "not_implied",
        "ac15_full_qualification": "outstanding",
    }


def main() -> int:
    """Write a local JSON receipt with no bearer token or issue body."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        evidence = create_receipt(os.environ)
    except (Ac5ReadbackError, ProjectsInspectionError) as exc:
        print(f"AC5_RESULT=BLOCKED: {exc}")
        return 2
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print("AC5_RESULT=LIVE_READBACK_CANDIDATE_REQUIRES_INDEPENDENT_AUDIT")
    print(f"AC5_RECEIPT={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
