"""Least-authority read-only GitHub pull-request and check-run inspection for Kalaxy3 SAGE."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .model import WorkflowError

_API_ROOT = "https://api." + "github.com"
_API_VERSION = "2026-03-10"
_ACCEPT = "application/vnd.github+json"
_USER_AGENT = "Kalaxy3-SAGE-github.inspect/1.4.0"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class GitHubPullRequestSnapshot:
    repository: str
    number: int
    state: str
    draft: bool
    base_branch: str
    base_sha: str
    head_repository: str
    head_branch: str
    head_sha: str
    merged: bool
    merged_at: str | None
    merge_commit_sha: str | None
    mergeable: bool | None
    mergeable_state: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "number": self.number,
            "state": self.state,
            "draft": self.draft,
            "base_branch": self.base_branch,
            "base_sha": self.base_sha,
            "head_repository": self.head_repository,
            "head_branch": self.head_branch,
            "head_sha": self.head_sha,
            "merged": self.merged,
            "merged_at": self.merged_at,
            "merge_commit_sha": self.merge_commit_sha,
            "mergeable": self.mergeable,
            "mergeable_state": self.mergeable_state,
        }


@dataclass(frozen=True)
class GitHubCheckRunSnapshot:
    repository: str
    check_run_id: int
    check_suite_id: int
    name: str
    head_sha: str
    status: str
    conclusion: str | None
    app_slug: str
    details_url: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "check_run_id": self.check_run_id,
            "check_suite_id": self.check_suite_id,
            "name": self.name,
            "head_sha": self.head_sha,
            "status": self.status,
            "conclusion": self.conclusion,
            "app_slug": self.app_slug,
            "details_url": self.details_url,
        }


class GitHubInspector:
    """Read GitHub PR state through fixed GET-only public REST endpoints."""

    def __init__(self, owner: str, repository: str, *, timeout_seconds: float = 20.0) -> None:
        if not _NAME.fullmatch(owner):
            raise WorkflowError(f"Invalid GitHub owner: {owner!r}")
        if not _NAME.fullmatch(repository):
            raise WorkflowError(f"Invalid GitHub repository: {repository!r}")
        if timeout_seconds <= 0 or timeout_seconds > 120:
            raise WorkflowError("github.inspect timeout must be between 0 and 120 seconds")
        self.owner = owner
        self.repository = repository
        self.timeout_seconds = timeout_seconds

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repository}"

    @staticmethod
    def _validate_branch(value: str, label: str) -> str:
        if not _BRANCH.fullmatch(value) or ".." in value:
            raise WorkflowError(f"Invalid GitHub {label}: {value!r}")
        return value

    @staticmethod
    def _validate_sha(value: object, label: str) -> str:
        if not isinstance(value, str) or not _SHA.fullmatch(value):
            raise WorkflowError(f"Invalid GitHub {label}")
        return value

    def _request_json(self, path: str, query: Mapping[str, str] | None = None) -> Any:
        pulls = f"/repos/{self.owner}/{self.repository}/pulls"
        checks_prefix = f"/repos/{self.owner}/{self.repository}/commits/"
        approved_checks = path.startswith(checks_prefix) and path.endswith("/check-runs")
        if not path.startswith(pulls) and not approved_checks:
            raise WorkflowError("github.inspect rejected an unapproved endpoint")
        suffix = f"?{urlencode(dict(query))}" if query else ""
        request = Request(
            _API_ROOT + path + suffix,
            headers={
                "Accept": _ACCEPT,
                "X-GitHub-Api-Version": _API_VERSION,
                "User-Agent": _USER_AGENT,
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = response.read(_MAX_RESPONSE_BYTES + 1)
        except HTTPError as error:
            raise WorkflowError(f"github.inspect GitHub REST request failed with HTTP {error.code}") from error
        except (URLError, TimeoutError, OSError) as error:
            raise WorkflowError("github.inspect GitHub REST transport failed") from error
        if len(data) > _MAX_RESPONSE_BYTES:
            raise WorkflowError("github.inspect GitHub REST response exceeded size limit")
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WorkflowError("github.inspect received invalid GitHub JSON") from error

    @staticmethod
    def _mapping(value: object, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise WorkflowError(f"github.inspect missing or invalid {label}")
        return value

    @staticmethod
    def _string(value: object, label: str, *, nullable: bool = False) -> str | None:
        if value is None and nullable:
            return None
        if not isinstance(value, str) or not value:
            raise WorkflowError(f"github.inspect missing or invalid {label}")
        return value

    @staticmethod
    def _bool(value: object, label: str, *, nullable: bool = False) -> bool | None:
        if value is None and nullable:
            return None
        if not isinstance(value, bool):
            raise WorkflowError(f"github.inspect missing or invalid {label}")
        return value

    def _snapshot(self, payload: object, expected_number: int) -> GitHubPullRequestSnapshot:
        data = self._mapping(payload, "pull-request response")
        number = data.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number != expected_number or number <= 0:
            raise WorkflowError("github.inspect pull-request number mismatch")
        state = self._string(data.get("state"), "state")
        if state not in {"open", "closed"}:
            raise WorkflowError(f"github.inspect unsupported pull-request state: {state!r}")
        draft = self._bool(data.get("draft"), "draft")
        merged = self._bool(data.get("merged"), "merged")
        base = self._mapping(data.get("base"), "base")
        head = self._mapping(data.get("head"), "head")
        base_repo = self._mapping(base.get("repo"), "base.repo")
        head_repo = self._mapping(head.get("repo"), "head.repo")
        base_full_name = self._string(base_repo.get("full_name"), "base.repo.full_name")
        if base_full_name.lower() != self.full_name.lower():
            raise WorkflowError(f"github.inspect base repository mismatch: expected={self.full_name}, observed={base_full_name}")
        head_full_name = self._string(head_repo.get("full_name"), "head.repo.full_name")
        base_branch = self._validate_branch(str(self._string(base.get("ref"), "base.ref")), "base branch")
        head_branch = self._validate_branch(str(self._string(head.get("ref"), "head.ref")), "head branch")
        base_sha = self._validate_sha(base.get("sha"), "base SHA")
        head_sha = self._validate_sha(head.get("sha"), "head SHA")
        merged_at = self._string(data.get("merged_at"), "merged_at", nullable=True)
        merge_commit_raw = data.get("merge_commit_sha")
        merge_commit_sha = None if merge_commit_raw is None else self._validate_sha(merge_commit_raw, "merge commit SHA")
        mergeable = self._bool(data.get("mergeable"), "mergeable", nullable=True)
        mergeable_state = self._string(data.get("mergeable_state"), "mergeable_state", nullable=True)
        if merged is True:
            if state != "closed" or merged_at is None:
                raise WorkflowError("github.inspect merged state is incomplete")
        elif merged_at is not None:
            raise WorkflowError("github.inspect unmerged pull request has merged_at")
        return GitHubPullRequestSnapshot(
            repository=self.full_name,
            number=number,
            state=str(state),
            draft=bool(draft),
            base_branch=base_branch,
            base_sha=base_sha,
            head_repository=str(head_full_name),
            head_branch=head_branch,
            head_sha=head_sha,
            merged=bool(merged),
            merged_at=merged_at,
            merge_commit_sha=merge_commit_sha,
            mergeable=mergeable,
            mergeable_state=mergeable_state,
        )

    def get_pull_request(self, number: int) -> GitHubPullRequestSnapshot:
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise WorkflowError("github.inspect pull-request number must be a positive integer")
        return self._snapshot(self._request_json(f"/repos/{self.owner}/{self.repository}/pulls/{number}"), number)

    def require_pull_request(
        self,
        number: int,
        *,
        base_branch: str,
        head_branch: str,
        head_sha: str,
        merged: bool | None = None,
        require_mergeable: bool = False,
    ) -> GitHubPullRequestSnapshot:
        expected_base = self._validate_branch(base_branch, "expected base branch")
        expected_head = self._validate_branch(head_branch, "expected head branch")
        expected_sha = self._validate_sha(head_sha, "expected head SHA")
        snapshot = self.get_pull_request(number)
        if snapshot.base_branch != expected_base:
            raise WorkflowError(f"github.inspect base branch mismatch: expected={expected_base}, observed={snapshot.base_branch}")
        if snapshot.head_branch != expected_head:
            raise WorkflowError(f"github.inspect head branch mismatch: expected={expected_head}, observed={snapshot.head_branch}")
        if snapshot.head_sha != expected_sha:
            raise WorkflowError(f"github.inspect head SHA mismatch: expected={expected_sha}, observed={snapshot.head_sha}")
        if merged is not None and snapshot.merged is not merged:
            raise WorkflowError(f"github.inspect merged-state mismatch: expected={merged}, observed={snapshot.merged}")
        if require_mergeable and snapshot.mergeable is not True:
            raise WorkflowError(f"github.inspect mergeability is not affirmatively true: {snapshot.mergeable!r}")
        return snapshot

    def find_pull_request(self, *, base_branch: str, head_branch: str, head_sha: str, required: bool = True) -> GitHubPullRequestSnapshot | None:
        expected_base = self._validate_branch(base_branch, "expected base branch")
        expected_head = self._validate_branch(head_branch, "expected head branch")
        expected_sha = self._validate_sha(head_sha, "expected head SHA")
        payload = self._request_json(
            f"/repos/{self.owner}/{self.repository}/pulls",
            {"state": "all", "base": expected_base, "head": f"{self.owner}:{expected_head}", "per_page": "100"},
        )
        if not isinstance(payload, list):
            raise WorkflowError("github.inspect list response is not an array")
        if len(payload) >= 100:
            raise WorkflowError("github.inspect pull-request lookup may be truncated; identity is unverifiable")
        matches: list[int] = []
        for raw in payload:
            item = self._mapping(raw, "pull-request list item")
            number = item.get("number")
            base = self._mapping(item.get("base"), "list base")
            head = self._mapping(item.get("head"), "list head")
            if isinstance(number, int) and number > 0 and base.get("ref") == expected_base and head.get("ref") == expected_head and head.get("sha") == expected_sha:
                matches.append(number)
        if not matches:
            if required:
                raise WorkflowError("github.inspect found no matching pull request")
            return None
        if len(matches) != 1:
            raise WorkflowError(f"github.inspect pull-request identity is ambiguous: {matches}")
        return self.require_pull_request(matches[0], base_branch=expected_base, head_branch=expected_head, head_sha=expected_sha)

    def _check_snapshot(self, payload: object, *, expected_sha: str) -> GitHubCheckRunSnapshot:
        data = self._mapping(payload, "check-run response")
        check_run_id = data.get("id")
        if not isinstance(check_run_id, int) or isinstance(check_run_id, bool) or check_run_id <= 0:
            raise WorkflowError("github.inspect check-run id must be a positive integer")
        name = self._string(data.get("name"), "check-run name")
        head_sha = self._validate_sha(data.get("head_sha"), "check-run head SHA")
        if head_sha != expected_sha:
            raise WorkflowError(f"github.inspect check-run head SHA mismatch: expected={expected_sha}, observed={head_sha}")
        status = self._string(data.get("status"), "check-run status")
        if status not in {"queued", "in_progress", "requested", "waiting", "pending", "completed"}:
            raise WorkflowError(f"github.inspect unsupported check-run status: {status!r}")
        conclusion = self._string(data.get("conclusion"), "check-run conclusion", nullable=True)
        if conclusion is not None and conclusion not in {"action_required", "cancelled", "failure", "neutral", "skipped", "stale", "success", "timed_out"}:
            raise WorkflowError(f"github.inspect unsupported check-run conclusion: {conclusion!r}")
        check_suite = self._mapping(data.get("check_suite"), "check-run check_suite")
        check_suite_id = check_suite.get("id")
        if (
            not isinstance(check_suite_id, int)
            or isinstance(check_suite_id, bool)
            or check_suite_id <= 0
        ):
            raise WorkflowError("github.inspect check-suite id must be a positive integer")
        app = self._mapping(data.get("app"), "check-run app")
        app_slug = self._string(app.get("slug"), "check-run app.slug")
        details_url = self._string(data.get("details_url"), "check-run details_url", nullable=True)
        return GitHubCheckRunSnapshot(
            repository=self.full_name,
            check_run_id=check_run_id,
            check_suite_id=check_suite_id,
            name=str(name),
            head_sha=head_sha,
            status=str(status),
            conclusion=conclusion,
            app_slug=str(app_slug),
            details_url=details_url,
        )

    def list_check_runs(self, *, head_sha: str, check_name: str) -> tuple[GitHubCheckRunSnapshot, ...]:
        expected_sha = self._validate_sha(head_sha, "expected check-run head SHA")
        expected_name = self._string(check_name, "expected check-run name")
        payload = self._request_json(
            f"/repos/{self.owner}/{self.repository}/commits/{expected_sha}/check-runs",
            {"check_name": str(expected_name), "filter": "latest", "per_page": "100"},
        )
        data = self._mapping(payload, "check-run list response")
        total = data.get("total_count")
        raw_runs = data.get("check_runs")
        if not isinstance(total, int) or isinstance(total, bool) or total < 0:
            raise WorkflowError("github.inspect check-run total_count is invalid")
        if not isinstance(raw_runs, list):
            raise WorkflowError("github.inspect check-run list is not an array")
        if total != len(raw_runs) or total >= 100:
            raise WorkflowError("github.inspect check-run lookup may be truncated or inconsistent")
        return tuple(self._check_snapshot(item, expected_sha=expected_sha) for item in raw_runs)

    def require_successful_check(
        self,
        *,
        head_sha: str,
        check_name: str,
        app_slug: str = "github-actions",
    ) -> GitHubCheckRunSnapshot:
        expected_app = self._string(app_slug, "expected check-run app slug")
        runs = tuple(
            item
            for item in self.list_check_runs(head_sha=head_sha, check_name=check_name)
            if item.name == check_name and item.app_slug == expected_app
        )
        if not runs:
            raise WorkflowError(f"github.inspect found no required check run: {check_name}")
        if len(runs) != 1:
            raise WorkflowError(f"github.inspect required check-run identity is ambiguous: {check_name}")
        run = runs[0]
        if run.status != "completed" or run.conclusion != "success":
            raise WorkflowError(
                "github.inspect required check is not successful: "
                f"name={check_name!r}, status={run.status!r}, conclusion={run.conclusion!r}"
            )
        return run

    def require_successful_checks(
        self,
        *,
        head_sha: str,
        required: tuple[tuple[str, str], ...],
    ) -> tuple[GitHubCheckRunSnapshot, ...]:
        if not required:
            raise WorkflowError("github.inspect required-check set must not be empty")
        expected_sha = self._validate_sha(head_sha, "expected check-run head SHA")
        required_runs: list[tuple[tuple[str, str], tuple[GitHubCheckRunSnapshot, ...]]] = []
        for check_name, app_slug in required:
            expected_name = str(self._string(check_name, "expected check-run name"))
            expected_app = str(self._string(app_slug, "expected check-run app slug"))
            runs = tuple(
                item
                for item in self.list_check_runs(
                    head_sha=expected_sha,
                    check_name=expected_name,
                )
                if item.name == expected_name and item.app_slug == expected_app
            )
            if not runs:
                raise WorkflowError(
                    f"github.inspect found no required check run: {expected_name}"
                )
            required_runs.append(((expected_name, expected_app), runs))

        common_suites = {
            item.check_suite_id for item in required_runs[0][1]
        }
        for _, runs in required_runs[1:]:
            common_suites &= {item.check_suite_id for item in runs}
        if not common_suites:
            raise WorkflowError(
                "github.inspect found no coherent check suite containing the complete required-check set"
            )

        successful: list[tuple[int, tuple[GitHubCheckRunSnapshot, ...]]] = []
        for suite_id in sorted(common_suites):
            selected: list[GitHubCheckRunSnapshot] = []
            for _, runs in required_runs:
                suite_runs = tuple(
                    item for item in runs if item.check_suite_id == suite_id
                )
                if len(suite_runs) != 1:
                    selected = []
                    break
                run = suite_runs[0]
                if run.status != "completed" or run.conclusion != "success":
                    selected = []
                    break
                selected.append(run)
            if selected:
                successful.append((suite_id, tuple(selected)))

        if not successful:
            raise WorkflowError(
                "github.inspect found no single successful required check suite for exact source SHA"
            )
        if len(successful) != 1:
            identities = [suite_id for suite_id, _ in successful]
            raise WorkflowError(
                "github.inspect successful required check-suite identity is ambiguous: "
                f"{identities}"
            )
        return successful[0][1]
