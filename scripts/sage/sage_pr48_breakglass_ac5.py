#!/usr/bin/env python3
"""Emit branch-only live Project evidence under an authorized Actions environment."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request

from workflow import github_inspect
from workflow.projects_inspect import inspect_issue_work_item

HEAD = "1dc228c7226a5233d58c30d1c64228cce067f5a4"
ISSUE_HASH = "1fbe56311ae9ffa3fefac39322d4bbc6af0e8ff83017341b13737db5130e40bb"
REPO = "donb4iu/Kalaxy3"


def inspect() -> dict[str, Any]:
    """Perform exactly one reviewed Project #15 read with a protected secret."""
    token = os.environ.get("SAGE_PROJECTS_CREDENTIAL", "")
    if not token:
        raise RuntimeError("PROTECTED_PROJECT_CREDENTIAL_UNAVAILABLE")
    original = github_inspect.urlopen
    calls = 0

    def guarded_open(request: Request, timeout: float = 20.0) -> Any:
        """Deny every query except the fixed Project #15 read."""
        nonlocal calls
        if request.full_url != "https://api.github.com/graphql":
            raise RuntimeError("UNAPPROVED_NETWORK_DESTINATION")
        payload = json.loads(request.data.decode("utf-8"))
        if (request.get_method() != "POST"
                or payload.get("query") != github_inspect.PROJECT_DETAIL_QUERY
                or payload.get("variables") != {"login": "donb4iu", "number": 15}):
            raise RuntimeError("UNAPPROVED_GRAPHQL_OPERATION")
        calls += 1
        return original(request, timeout=timeout)

    github_inspect.urlopen = guarded_open
    try:
        item = inspect_issue_work_item(token, "donb4iu", 15, REPO, 44)
    finally:
        github_inspect.urlopen = original
    if calls != 1:
        raise RuntimeError("UNEXPECTED_QUERY_COUNT")
    return item


def receipt(item: dict[str, Any]) -> dict[str, Any]:
    """Validate issue identity and build a nonsecret branch-only receipt."""
    body = item.get("body", "")
    if not isinstance(body, str):
        raise RuntimeError("ISSUE_BODY_MISSING")
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if (digest != ISSUE_HASH
            or "Architect-approved Project/RACI Definition of Done" not in body):
        raise RuntimeError("ISSUE_CONTRACT_DRIFT")
    expected = ("repository", "project_id", "project_url", "project_owner",
                "item_id", "issue_id", "issue_updated_at", "status",
                "status_updated_at", "assignees", "not_retrieved")
    if (item.get("repository") != REPO or item.get("project_number") != 15
            or item.get("issue_number") != 44
            or item.get("project_owner") != "donb4iu"
            or item.get("project_url") != "https://github.com/users/donb4iu/projects/15"):
        raise RuntimeError("PROJECT_IDENTITY_MISMATCH")
    if any(item.get(key) is None or item[key] == "" for key in expected):
        raise RuntimeError("REQUIRED_PROVENANCE_MISSING")
    timestamp = datetime.fromisoformat(item["status_updated_at"].replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise RuntimeError("STATUS_TIMESTAMP_UNQUALIFIED")
    record = {key: item[key] for key in expected}
    record.update({"record_type": "issue44-pr48-branch-actions-readback",
                   "issue_number": 44, "project_number": 15,
                   "issue_body_sha256": digest, "reviewed_pr_head": HEAD,
                   "qualification_commit": os.environ["GITHUB_SHA"],
                   "actions_run_id": os.environ["GITHUB_RUN_ID"],
                   "actions_actor": os.environ["GITHUB_ACTOR"],
                   "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                   "ac5_status": "branch_live_read_observed_production_unverified",
                   "ac15_status": "full_boundary_qualification_outstanding",
                   "github_mutation_by_reader": "none",
                   "project_mutation": "none",
                   "architect_promotion": "none"})
    return record


def main() -> int:
    """Fail closed and write only nonsecret evidence to Actions artifact path."""
    out = Path(os.environ["RUNNER_TEMP"]) / "sage-pr48-ac5-branch.json"
    try:
        if (os.environ.get("GITHUB_ACTIONS") != "true"
                or os.environ.get("GITHUB_REPOSITORY") != REPO
                or os.environ.get("GITHUB_REF") != "refs/heads/qualification/sage-pr48-ac5-20261104t062305z"):
            raise RuntimeError("UNTRUSTED_BRANCH_ACTIONS_RUNTIME")
        evidence = receipt(inspect())
        out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print("RESULT=PR48_BRANCH_AC5_LIVE_READ_OBSERVED_NO_PROMOTION")
        return 0
    except Exception as exc:
        # Never serialize exception details or secret-bearing transport objects.
        allowed = {"PROTECTED_PROJECT_CREDENTIAL_UNAVAILABLE", "ISSUE_CONTRACT_DRIFT",
                   "UNTRUSTED_BRANCH_ACTIONS_RUNTIME", "PROJECT_IDENTITY_MISMATCH",
                   "REQUIRED_PROVENANCE_MISSING", "STATUS_TIMESTAMP_UNQUALIFIED",
                   "ISSUE_BODY_MISSING", "UNAPPROVED_NETWORK_DESTINATION",
                   "UNAPPROVED_GRAPHQL_OPERATION", "UNEXPECTED_QUERY_COUNT"}
        code = str(exc) if str(exc) in allowed else "LIVE_READBACK_FAILED_REDACTED"
        out.write_text(json.dumps({"record_type": "issue44-pr48-branch-actions-failure",
                                   "reason": code, "reviewed_pr_head": HEAD,
                                   "architect_promotion": "none"}) + "\n")
        print("RESULT=PR48_BRANCH_AC5_BLOCKED_" + code)
        return 2


if __name__ == "__main__":
    sys.exit(main())
