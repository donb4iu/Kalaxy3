#!/usr/bin/env python3
"""Advise on objective/milestone evidence continuity without granting authority."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_ISSUE = re.compile(r"(?<![A-Za-z0-9])#([0-9]+)\b")
_FIELD = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?([\w -]+?):?(?:\*\*)?\s*:\s*(.*?)\s*$")
_HEADING = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
_SECTIONS = {
    "paths": "declared change paths",
    "evidence": "acceptance evidence",
    "unknowns": "known uncertainties",
    "next": "next bounded work",
}


@dataclass(frozen=True)
class Finding:
    """Record an advisory-only, source-limited observation."""

    code: str
    message: str


def labeled_field(body: str, name: str) -> str:
    """Read a single declared field without interpreting surrounding prose.

    Args:
        body: PR Markdown body.
        name: Case-insensitive expected field name.
    """
    for line in body.splitlines():
        match = _FIELD.match(line.replace("`", ""))
        if match and match.group(1).strip().lower() == name.lower():
            return match.group(2).strip()
    return ""


def section_items(body: str, section_name: str) -> list[str]:
    """Read bullet items in a named Markdown section, excluding commentary.

    Args:
        body: PR Markdown body.
        section_name: Exact section title.
    """
    depth: int | None = None
    items: list[str] = []
    for line in body.splitlines():
        match = _HEADING.match(line)
        if match and match.group(2).strip().lower() == section_name:
            depth = len(match.group(1))
            continue
        if match and depth is not None and len(match.group(1)) <= depth:
            break
        if depth is None:
            continue
        bullet = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if bullet:
            value = bullet.group(1).strip().strip("`")
            if value and not value.startswith("<!--"):
                items.append(value[:500])
    return items


def issue_number(value: str) -> int | None:
    """Extract a single unambiguous issue reference from a declared field.

    Args:
        value: Issue field content.
    """
    found = {int(item) for item in _ISSUE.findall(value)}
    return next(iter(found)) if len(found) == 1 else None


def declared_context(body: str) -> dict[str, Any]:
    """Extract PR continuity claims without accepting them as truth.

    Args:
        body: PR Markdown text.
    """
    return {
        "contract": labeled_field(body, "Context contract"),
        "parent_objective": issue_number(labeled_field(body, "Parent objective")),
        "milestone_issue": issue_number(labeled_field(body, "Milestone issue")),
        "contribution": labeled_field(body, "Objective contribution"),
        "paths": section_items(body, _SECTIONS["paths"]),
        "evidence": section_items(body, _SECTIONS["evidence"]),
        "unknowns": section_items(body, _SECTIONS["unknowns"]),
        "next": section_items(body, _SECTIONS["next"]),
    }


def evaluate(
    context: Mapping[str, Any], changed_paths: Sequence[str] | None
) -> list[Finding]:
    """Evaluate declared continuity and observed paths without making a gate.

    Args:
        context: Unverified PR-authored metadata.
        changed_paths: GitHub-reported changed paths or None when unavailable.
    """
    findings: list[Finding] = []
    if context["contract"] != "v1":
        return [Finding("CONTRACT_NOT_DECLARED", "No v1 handoff declaration.")]
    for field, code in (
        ("parent_objective", "PARENT_UNDECLARED"),
        ("milestone_issue", "MILESTONE_UNDECLARED"),
        ("contribution", "CONTRIBUTION_UNDECLARED"),
        ("paths", "SCOPE_UNDECLARED"),
        ("evidence", "EVIDENCE_UNDECLARED"),
        ("unknowns", "UNCERTAINTY_UNDECLARED"),
        ("next", "CONTINUATION_UNDECLARED"),
    ):
        if not context[field]:
            findings.append(Finding(code, f"Missing {field} declaration."))
    if context["parent_objective"] == context["milestone_issue"] and context["parent_objective"]:
        findings.append(Finding("PARENT_AS_MILESTONE", "Milestone equals parent objective."))
    if changed_paths is None:
        findings.append(Finding("CHANGED_FILES_UNKNOWN", "Changed files were not verified."))
    elif context["paths"]:
        outside = sorted(path for path in set(changed_paths) if not any(
            fnmatch.fnmatchcase(path, pattern) for pattern in context["paths"]
        ))
        if outside:
            names = ", ".join(outside[:8])
            findings.append(Finding("OUTSIDE_DECLARED_PATHS", f"Undeclared paths: {names}; total={len(outside)}."))
    return findings


def github_changed_paths(
    api: str, repo: str, pr_number: int, token: str
) -> tuple[list[str] | None, bool]:
    """Fetch up to 500 PR changed-file names using read-only GitHub REST.

    Args:
        api: REST API base URL.
        repo: GitHub owner/repository.
        pr_number: Pull request number.
        token: Token with pull-requests read permission.
    """
    paths: list[str] = []
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "sage-pr-continuity-v1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        for page in range(1, 6):
            url = f"{api.rstrip('/')}/repos/{repo}/pulls/{pr_number}/files?per_page=100&page={page}"
            with urlopen(Request(url, headers=headers), timeout=12) as response:
                records = json.load(response)
            if not isinstance(records, list):
                return None, False
            paths.extend(item["filename"] for item in records if isinstance(item, dict) and isinstance(item.get("filename"), str))
            if len(records) < 100:
                return sorted(set(paths)), True
        return sorted(set(paths)), False
    except (HTTPError, URLError, OSError, ValueError, KeyError, TimeoutError):
        return None, False


def build_manifest(
    event: Mapping[str, Any], paths: Sequence[str] | None,
    complete: bool
) -> dict[str, Any]:
    """Create a reproducible candidate handoff from GitHub event evidence.

    Args:
        event: GitHub pull_request webhook payload.
        paths: Observed changed paths or None.
        complete: Whether all changed files were retrieved.
    """
    pr = event["pull_request"]
    context = declared_context(pr.get("body") or "")
    findings = evaluate(context, paths if complete else None)
    result: dict[str, Any] = {
        "schema": "sage-pr-context-continuity-v1",
        "status": "unverified_pr_claims_not_architect_acceptance",
        "pr_number": pr["number"],
        "base_revision": pr["base"]["sha"],
        "head_revision": pr["head"]["sha"],
        "declared": context,
        "observed_changed_paths": sorted(set(paths)) if paths is not None else None,
        "changed_paths_complete": complete,
        "advisories": [asdict(finding) for finding in findings],
        "evidence_independently_qualified": False,
        "context_completeness_verified": False,
    }
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["manifest_sha256"] = hashlib.sha256(encoded).hexdigest()
    return result


def report(manifest: Mapping[str, Any], summary: str) -> None:
    """Show advisory findings and write a non-authoritative CI step summary.

    Args:
        manifest: Generated candidate continuity manifest.
        summary: GitHub Actions summary path, when defined.
    """
    findings = manifest["advisories"]
    lines = ["### SAGE PR context continuity (advisory only)", "",
             "Claims and file paths are unverified context, not acceptance.", "",
             f"Manifest SHA-256: `{manifest['manifest_sha256']}`", ""]
    for finding in findings:
        msg = f"{finding['code']}: {finding['message']}"
        print("ADVISORY " + msg)
        safe = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print("::warning title=PR context continuity::" + safe)
        lines.append(f"- `{finding['code']}` — {json.dumps(finding['message'])}")
    if not findings:
        lines.append("No declared-continuity concerns observed; no acceptance inferred.")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as stream:
                stream.write("\n".join(lines) + "\n")
        except OSError:
            print("ADVISORY summary unavailable")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the nonblocking audit against a GitHub PR event.

    Args:
        argv: CLI arguments, defaulting to process arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", default=os.getenv("GITHUB_EVENT_PATH", ""))
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    try:
        event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        pr = event["pull_request"]
        repo = event["repository"]["full_name"]
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            raise ValueError("Invalid repository")
        paths, complete = github_changed_paths(
            os.getenv("GITHUB_API_URL", "https://api.github.com"), repo,
            int(pr["number"]), os.getenv("GITHUB_TOKEN", ""),
        )
        manifest = build_manifest(event, paths, complete)
        if args.out:
            Path(args.out).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        report(manifest, os.getenv("GITHUB_STEP_SUMMARY", ""))
        print(f"PR context continuity: {len(manifest['advisories'])} advisory(s); no enforcement")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ADVISORY continuity unavailable: {type(error).__name__}; no enforcement")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
