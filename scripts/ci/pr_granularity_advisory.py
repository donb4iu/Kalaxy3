#!/usr/bin/env python3
"""Report PR scope concerns without changing GitHub state."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ISSUE_REF = re.compile(r"(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#(\d+)\b")
_CLOSING_REF = re.compile(
    r"\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)\s+"
    r"(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#(\d+)\b",
    re.IGNORECASE,
)
_SECTION = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
_DOD_TITLE = re.compile(r"^(?:definition of done|do[d])\b", re.IGNORECASE)
_CRITERIA = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:acceptance criteria|definition of done)\b"
    r"|^\s*(?:[-*]\s*)?\[[ xX]\]\s+\S"
    r"|^\s*(?:[-*]\s*)?AC\s*\d+\b",
)
_PARENT = re.compile(
    r"\b(?:parent\s+(?:objective|issue)|umbrella|epic|"
    r"master\s+(?:issue|objective))\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    """Represent a non-blocking scope or evidence warning."""

    code: str
    message: str


def milestone_issues(body: str) -> list[int]:
    """Extract distinct issue numbers declared in milestone issue fields.

    Args:
        body: Markdown text of the pull request.
    """
    found: set[int] = set()
    for original in body.splitlines():
        line = original.replace("**", "").replace("`", "").strip()
        line = re.sub(r"^[-*]\s+", "", line)
        match = re.match(r"^milestone\s+issues?\s*:\s*(.*)$", line, re.I)
        if match is None:
            match = re.match(r"^milestone\s*:\s*(.*)$", line, re.I)
        if match:
            found.update(int(value) for value in _ISSUE_REF.findall(match[1]))
    return sorted(found)


def closing_issues(body: str) -> list[int]:
    """Extract GitHub closing-keyword issue references from PR text.

    Args:
        body: Markdown text of the pull request.
    """
    return sorted({int(value) for value in _CLOSING_REF.findall(body)})


def dod_section(body: str) -> str:
    """Return the Markdown Definition of Done section, if present.

    Args:
        body: Linked issue description.
    """
    lines: list[str] = []
    depth: int | None = None
    for line in body.splitlines():
        heading = _SECTION.match(line)
        if heading and _DOD_TITLE.search(heading[2]):
            depth = len(heading[1])
            continue
        if depth is not None and heading and len(heading[1]) <= depth:
            break
        if depth is not None:
            lines.append(line)
    return "\n".join(lines)


def dod_domain_count(body: str) -> int:
    """Estimate independently named DoD domains, not individual checkboxes.

    Args:
        body: Linked issue description.
    """
    section = dod_section(body)
    headings = re.findall(r"(?m)^\s*#{2,6}\s+(.+?)\s*$", section)
    if headings:
        return len({item.strip().casefold() for item in headings})
    numbered = re.findall(
        r"(?m)^\s*(?:\d+[.)]|DoD\s*\d+\s*[-.:])\s+(.+?)\s*$",
        section,
        re.IGNORECASE,
    )
    if numbered:
        return len({item.strip().casefold() for item in numbered})
    explicit = re.findall(
        r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?DoD\s*domain\s*(\d+)\b",
        body,
    )
    return len(set(explicit))


def has_acceptance_criteria(body: str) -> bool:
    """Indicate whether issue text exposes identifiable acceptance checks.

    Args:
        body: Linked issue description.
    """
    return bool(_CRITERIA.search(body))


def parent_signals(issue: Mapping[str, Any]) -> bool:
    """Detect explicit parent/epic signals in title or labels.

    Args:
        issue: GitHub issue fields, including title and labels.
    """
    title = str(issue.get("title") or "")
    labels = issue.get("labels") or []
    names = [
        item if isinstance(item, str) else str(item.get("name") or "")
        for item in labels if isinstance(item, (str, dict))
    ]
    return bool(_PARENT.search(" ".join([title, *names])))


def inspect_issue(
    number: int, issue: Mapping[str, Any] | None
) -> list[Finding]:
    """Return scope concerns about one declared milestone issue.

    Args:
        number: Declared milestone issue number.
        issue: Issue record or None when authoritative readback fails.
    """
    if issue is None:
        return [Finding("ISSUE_UNVERIFIED", f"Issue #{number} unavailable.")]
    result: list[Finding] = []
    if parent_signals(issue):
        result.append(
            Finding(
                "PARENT_OBJECTIVE", f"Issue #{number} has parent indicators."
            )
        )
    body = str(issue.get("body") or "")
    domains = dod_domain_count(body)
    if domains >= 3:
        result.append(
            Finding(
                "MULTI_DOMAIN_DOD",
                f"Issue #{number} has {domains} DoD domains.",
            )
        )
    if not has_acceptance_criteria(body):
        result.append(
            Finding(
                "MISSING_ACCEPTANCE",
                f"Issue #{number} lacks acceptance criteria.",
            )
        )
    return result


def evaluate(
    pr_body: str, issues: Mapping[int, Mapping[str, Any] | None]
) -> list[Finding]:
    """Evaluate deterministic advisory concerns using supplied issue evidence.

    Args:
        pr_body: Markdown body of a pull request.
        issues: Issue number to GitHub issue object or None if unavailable.
    """
    declared = milestone_issues(pr_body)
    findings: list[Finding] = []
    if not declared:
        findings.append(
            Finding("MISSING_MILESTONE", "Declare one milestone issue.")
        )
    if len(declared) > 1:
        findings.append(
            Finding("MULTIPLE_MILESTONES", f"Milestone issues: {declared}.")
        )
    outside = sorted(set(closing_issues(pr_body)) - set(declared))
    if declared and outside:
        findings.append(
            Finding("OUTSIDE_MILESTONE", f"Outside milestone: {outside}.")
        )
    for number in declared:
        findings.extend(inspect_issue(number, issues.get(number)))
    return findings


def fetch_issue(
    repository: str, number: int, token: str, api_url: str
) -> Mapping[str, Any] | None:
    """Read an issue without changing its GitHub state.

    Args:
        repository: Owner/repository name.
        number: Issue number to inspect.
        token: Read-only GitHub Actions token.
        api_url: GitHub REST API root.
    """
    url = f"{api_url.rstrip('/')}/repos/{repository}/issues/{number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "kalaxy3-pr-granularity-v1",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=12) as response:
            result = json.load(response)
        if isinstance(result, dict) and "pull_request" not in result:
            return result
        return None
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return None


def report(findings: Sequence[Finding], summary_path: str) -> None:
    """Print advisory warnings and append them to GitHub step summary.

    Args:
        findings: Non-blocking diagnostics.
        summary_path: Optional GitHub step-summary path.
    """
    lines = [
        "### PR Granularity Advisory",
        "",
        "Non-blocking; Architect acceptance is unchanged.",
        "",
    ]
    if not findings:
        lines.append("No concerns detected by the granularity heuristic.")
    for finding in findings:
        message = f"{finding.code}: {finding.message}"
        print(f"ADVISORY {message}")
        safe = (
            message.replace("%", "%25")
            .replace("\r", "%0D")
            .replace("\n", "%0A")
        )
        print(f"::warning title=PR granularity advisory::{safe}")
        lines.append(f"- **{finding.code}** — {finding.message}")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as output:
                output.write("\n".join(lines) + "\n")
        except OSError as exc:
            print(f"ADVISORY summary unavailable: {exc}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Run read-only analysis from a GitHub pull-request event JSON.

    Args:
        argv: Optional command-line arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event-path", default=os.getenv("GITHUB_EVENT_PATH", "")
    )
    parser.add_argument(
        "--repository", default=os.getenv("GITHUB_REPOSITORY", "")
    )
    args = parser.parse_args(argv)
    try:
        event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        body = event["pull_request"].get("body") or ""
        repository = args.repository or event["repository"]["full_name"]
        if not _REPOSITORY.fullmatch(repository):
            raise ValueError("invalid repository identity")
        numbers = milestone_issues(body)
        token = os.getenv("GITHUB_TOKEN", "")
        api_url = os.getenv("GITHUB_API_URL", "https://api.github.com")
        issues = {
            n: fetch_issue(repository, n, token, api_url)
            for n in numbers[:20]
        }
        findings = evaluate(body, issues)
        if len(numbers) > 20:
            findings.append(
                Finding(
                    "LOOKUP_LIMIT", "Only 20 milestone issues were inspected."
                )
            )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        findings = [
            Finding(
                "EVALUATION_UNAVAILABLE",
                f"PR evidence unavailable: {type(exc).__name__}.",
            )
        ]
    report(findings, os.getenv("GITHUB_STEP_SUMMARY", ""))
    print(
        f"PR granularity advisory: {len(findings)} concern(s); no enforcement."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
