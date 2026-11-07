#!/usr/bin/env python3
"""Publish one governed SAGE objective-episode record to its Project issue."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "donb4iu/Kalaxy3"
API_ROOT = f"https://api.github.com/repos/{REPOSITORY}"
SHA_PATTERN = re.compile(r"^[a-f0-9]{40}$")
REF_PATTERN = re.compile(r"^refs/heads/(main|qualification/[a-z0-9-]+)$")
RUN_PATTERN = re.compile(r"^[1-9][0-9]{0,18}$")
OBJECTIVE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 /#._:()\-]{2,159}$")
ALLOWED_RESULTS = {"success", "failure", "transport-exercise"}


class EpisodeError(RuntimeError):
    """Report a bounded episode-visibility or authority failure."""


def now_utc() -> str:
    """Return an offset-aware UTC time for an event."""
    return datetime.now(timezone.utc).isoformat()


def required_environment(env: Mapping[str, str]) -> dict[str, str]:
    """Validate source and actor attribution from GitHub Actions.

    Args:
        env: Actual GitHub Actions environment mapping.
    """
    required = ("GITHUB_REPOSITORY", "GITHUB_ACTIONS", "GITHUB_RUN_ID",
                "GITHUB_SHA", "GITHUB_REF", "GITHUB_ACTOR",
                "SAGE_PROJECT_NUMBER", "SAGE_ISSUE_NUMBER", "SAGE_OBJECTIVE",
                "SAGE_RESPONSIBLE", "SAGE_ACCOUNTABLE", "SAGE_AUTHORITY")
    if any(not env.get(name) for name in required):
        raise EpisodeError("ACTIONS_PROVENANCE_MISSING")
    if env["GITHUB_REPOSITORY"] != REPOSITORY or env["GITHUB_ACTIONS"] != "true":
        raise EpisodeError("UNTRUSTED_REPOSITORY_OR_RUNTIME")
    if not RUN_PATTERN.fullmatch(env["GITHUB_RUN_ID"]):
        raise EpisodeError("INVALID_ACTIONS_RUN_ID")
    if not SHA_PATTERN.fullmatch(env["GITHUB_SHA"]):
        raise EpisodeError("INVALID_ACTIONS_SOURCE_SHA")
    if not REF_PATTERN.fullmatch(env["GITHUB_REF"]):
        raise EpisodeError("UNAUTHORIZED_GIT_REFERENCE")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}(?:\[bot\])?", env["GITHUB_ACTOR"]):
        raise EpisodeError("INVALID_ACTIONS_ACTOR")
    if (not RUN_PATTERN.fullmatch(env["SAGE_PROJECT_NUMBER"])
            or not RUN_PATTERN.fullmatch(env["SAGE_ISSUE_NUMBER"])
            or any(not OBJECTIVE_PATTERN.fullmatch(env[key]) for key in (
                "SAGE_OBJECTIVE", "SAGE_RESPONSIBLE", "SAGE_ACCOUNTABLE",
                "SAGE_AUTHORITY"))):
        raise EpisodeError("INVALID_PROJECT_EPISODE_CONTRACT")
    attempt = env.get("GITHUB_RUN_ATTEMPT", "1")
    if not RUN_PATTERN.fullmatch(attempt):
        raise EpisodeError("INVALID_RUN_ATTEMPT")
    return {name.lower(): env[name] for name in required}


def validate_receipt(path: Path, env: Mapping[str, str]) -> dict[str, str]:
    """Validate a live, main-branch AC5 receipt without trusting its contents.

    Args:
        path: Artifact path produced by the readback job.
        env: Trusted Actions runtime identity.
    """
    if env["GITHUB_REF"] != "refs/heads/main":
        raise EpisodeError("LIVE_RECEIPT_NOT_MAIN_BRANCH")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EpisodeError("LIVE_RECEIPT_UNAVAILABLE") from exc
    expected = {"repository": REPOSITORY,
                "issue_number": int(env["SAGE_ISSUE_NUMBER"]),
                "project_number": int(env["SAGE_PROJECT_NUMBER"]),
                "project_owner": "donb4iu",
                "source_sha": env["GITHUB_SHA"],
                "run_id": env["GITHUB_RUN_ID"]}
    if not isinstance(data, dict):
        raise EpisodeError("LIVE_RECEIPT_IDENTITY_MISMATCH")
    if any(data.get(k) != v for k, v in expected.items()):
        raise EpisodeError("LIVE_RECEIPT_IDENTITY_MISMATCH")
    for name in ("project_id", "item_id", "issue_id", "issue_body_sha256",
                 "status_updated_at", "retrieved_at_utc"):
        if not isinstance(data.get(name), str) or not data[name]:
            raise EpisodeError("LIVE_RECEIPT_PROVENANCE_INCOMPLETE")
    if not re.fullmatch(r"[a-f0-9]{64}", data["issue_body_sha256"]):
        raise EpisodeError("LIVE_RECEIPT_CONTRACT_HASH_INVALID")
    for name in ("project_id", "item_id", "issue_id"):
        if not re.fullmatch(r"[A-Za-z0-9_-]{5,120}", data[name]):
            raise EpisodeError("LIVE_RECEIPT_NODE_ID_INVALID")
    return {"receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "project_id": data["project_id"], "item_id": data["item_id"],
            "issue_id": data["issue_id"], "status_updated_at": data["status_updated_at"],
            "issue_body_sha256": data["issue_body_sha256"]}


def construct_event(
    phase: str, outcome: str, env: Mapping[str, str],
    evidence: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build an authority-scoped event for one configured Project issue.

    Args:
        phase: Begin or finish lifecycle boundary.
        outcome: Success, failure, or transport exercise.
        env: Validated GitHub Actions identity.
        evidence: Nonsecret evidence from the verified AC5 receipt.
    """
    if phase not in {"begin", "finish"} or outcome not in ALLOWED_RESULTS:
        raise EpisodeError("INVALID_EPISODE_TRANSITION")
    branch = env["GITHUB_REF"].removeprefix("refs/heads/")
    attempt = env.get("GITHUB_RUN_ATTEMPT", "1")
    if outcome == "transport-exercise" and not branch.startswith("qualification/"):
        raise EpisodeError("TRANSPORT_EXERCISE_NOT_ON_QUALIFICATION_BRANCH")
    if phase == "finish" and outcome == "success" and not evidence:
        raise EpisodeError("SUCCESS_REQUIRES_LIVE_RECEIPT")
    status = "running" if phase == "begin" else (
        "observed" if outcome == "success" else
        "transport_exercised" if outcome == "transport-exercise" else "blocked")
    return {
        "schema": "sage-objective-episode/v1", "repository": REPOSITORY,
        "project_number": int(env["SAGE_PROJECT_NUMBER"]),
        "issue_number": int(env["SAGE_ISSUE_NUMBER"]),
        "objective": env["SAGE_OBJECTIVE"],
        "episode_id": f"{env['GITHUB_RUN_ID']}-{attempt}",
        "phase": phase, "status": status,
        "role_responsible": env["SAGE_RESPONSIBLE"],
        "role_accountable": env["SAGE_ACCOUNTABLE"],
        "authority": env["SAGE_AUTHORITY"],
        "promotion_authority": "none", "actor": env["GITHUB_ACTOR"],
        "source_sha": env["GITHUB_SHA"], "branch": branch,
        "run_url": f"https://github.com/{REPOSITORY}/actions/runs/{env['GITHUB_RUN_ID']}",
        "recorded_at_utc": now_utc(), "evidence": dict(evidence or {}),
        "next_action": (
            "Execute and independently verify the bounded read-back" if phase == "begin"
            else "Independent receipt audit; Architect decision remains separate"
            if outcome == "success" else "Review qualification transport evidence only"
            if outcome == "transport-exercise" else "Inspect the failed episode; do not promote"),
    }


def marker(run_id: str) -> str:
    """Return a stable run-specific marker for one Project-linked comment.

    Args:
        run_id: Trusted GitHub Actions run identifier.
    """
    return f"<!-- sage-objective-episode:v1:{run_id} -->"


def render_comment(event: Mapping[str, Any]) -> str:
    """Render a compact operator-facing issue-linked episode record.

    Args:
        event: Deterministically validated episode event.
    """
    evidence = event["evidence"]
    pointer = (f"Receipt SHA-256 `{evidence['receipt_sha256']}`; "
               f"Project item `{evidence['item_id']}`" if evidence else
               "Receipt not yet available; no AC5 completion claim")
    transitions = (f"Started: {event['began_at_utc']}; "
                   f"{event['status']}: {event['recorded_at_utc']}"
                   if event.get("began_at_utc") else
                   f"Started: {event['recorded_at_utc']}")
    return "\n".join([
        marker(event["episode_id"]), "### SAGE objective episode",
        f"**Project:** #{event['project_number']} · **Issue:** #{event['issue_number']} "
        f"· **Episode:** `{event['episode_id']}`",
        f"**Objective:** {event['objective']}",
        f"**Status:** `{event['status']}` · **Phase:** `{event['phase']}`",
        f"**Transitions:** {transitions}",
        f"**RACI:** Responsible: {event['role_responsible']}; "
        f"Accountable: {event['role_accountable']}",
        f"**Authority:** {event['authority']} · Promotion: **not authorized**",
        f"**Source:** `{event['source_sha']}` on `{event['branch']}`",
        f"**Actor:** `{event['actor']}` · **Recorded:** {event['recorded_at_utc']}",
        f"**Evidence:** {pointer}",
        f"**Next:** {event['next_action']}",
        f"**Actions:** {event['run_url']}",
        "", "_This is execution visibility, not an Architect approval or Project status mutation._",
        "",
    ])


def api_json(
    token: str, method: str, path: str, issue_number: int,
    payload: dict | None = None,
) -> Any:
    """Call one allowlisted GitHub issue-comment endpoint.

    Args:
        token: Job-scoped GITHUB_TOKEN, never a Projects credential.
        method: GET, POST, or PATCH.
        path: Verified REST API path inside the issue-comment namespace.
        issue_number: Governed Project-linked issue.
        payload: Optional JSON body.
    """
    list_path = rf"/issues/{issue_number}/comments(?:\?per_page=100&page=[1-9][0-9]?)?"
    allowed_list = re.fullmatch(list_path, path)
    allowed_edit = re.fullmatch(r"/issues/comments/[1-9][0-9]*", path)
    if not allowed_list and not allowed_edit:
        raise EpisodeError("UNAPPROVED_API_PATH")
    if method not in {"GET", "POST", "PATCH"}:
        raise EpisodeError("UNAPPROVED_API_METHOD")
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(API_ROOT + path, data=body, method=method, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "sage-episode-visibility/1",
        "Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(1_000_001)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise EpisodeError("GITHUB_ISSUE_VISIBILITY_TRANSPORT_FAILED") from exc
    if len(raw) > 1_000_000:
        raise EpisodeError("GITHUB_ISSUE_RESPONSE_TOO_LARGE")
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise EpisodeError("GITHUB_ISSUE_RESPONSE_INVALID") from exc


def find_comment(
    token: str, run_id: str, issue_number: int,
) -> dict[str, Any] | None:
    """Locate a unique Actions-owned episode comment across bounded pages.

    Args:
        token: Scoped GitHub issue-write token.
        run_id: Exact episode identifier.
        issue_number: Governed Project-linked issue.
    """
    matches: list[dict[str, Any]] = []
    for page in range(1, 11):
        comments = api_json(
            token, "GET", f"/issues/{issue_number}/comments?per_page=100&page={page}",
            issue_number,
        )
        if not isinstance(comments, list):
            raise EpisodeError("GITHUB_ISSUE_COMMENTS_INVALID")
        for item in comments:
            owner = item.get("user", {}) if isinstance(item, dict) else {}
            if (isinstance(owner, dict) and owner.get("login") == "github-actions[bot]"
                    and marker(run_id) in str(item.get("body", ""))):
                matches.append(item)
        if len(comments) < 100:
            break
    else:
        raise EpisodeError("GITHUB_ISSUE_COMMENT_SEARCH_TRUNCATED")
    if len(matches) > 1:
        raise EpisodeError("AMBIGUOUS_EPISODE_COMMENT")
    return matches[0] if matches else None


def publish(token: str, event: dict[str, Any]) -> int:
    """Create on begin and update on finish one visible Project-linked record.

    Args:
        token: Scoped GitHub Actions GITHUB_TOKEN.
        event: Validated event to publish.
    """
    issue_number = event["issue_number"]
    existing = find_comment(token, event["episode_id"], issue_number)
    if event["phase"] == "finish" and existing is not None:
        began = existing.get("created_at")
        if not isinstance(began, str) or not began:
            raise EpisodeError("EPISODE_START_TIMESTAMP_MISSING")
        event["began_at_utc"] = began
    body = render_comment(event)
    if event["phase"] == "begin" and existing is not None:
        raise EpisodeError("EPISODE_ALREADY_STARTED")
    if event["phase"] == "finish" and existing is None:
        raise EpisodeError("EPISODE_BEGIN_NOT_OBSERVED")
    method = "POST" if existing is None else "PATCH"
    path = (f"/issues/{issue_number}/comments" if existing is None
            else f"/issues/comments/{existing['id']}")
    response = api_json(token, method, path, issue_number, {"body": body})
    if not isinstance(response, dict) or not isinstance(response.get("id"), int):
        raise EpisodeError("EPISODE_COMMENT_NOT_ACKNOWLEDGED")
    return response["id"]


def main() -> int:
    """Emit visible, attributable boundaries without a Projects write token."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("begin", "finish"))
    parser.add_argument("--result", choices=sorted(ALLOWED_RESULTS), default="failure")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        env = os.environ
        required_environment(env)
        evidence = validate_receipt(args.receipt, env) if (
            args.phase == "finish" and args.result == "success" and args.receipt) else None
        event = construct_event(args.phase, args.result, env, evidence)
        token = env.get("GITHUB_TOKEN", "")
        if not token or env.get("SAGE_PROJECTS_CREDENTIAL"):
            raise EpisodeError("VISIBILITY_TOKEN_BOUNDARY_INVALID")
        comment_id = publish(token, event)
        args.output.write_text(json.dumps(event, indent=2, sort_keys=True) + "\n")
        summary = env.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as handle:
                handle.write(render_comment(event))
        print(f"EPISODE_VISIBILITY=PASS phase={args.phase} comment_id={comment_id}")
        return 0
    except EpisodeError as exc:
        print(f"EPISODE_VISIBILITY=BLOCKED code={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
