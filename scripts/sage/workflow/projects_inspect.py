"""Read-only GitHub Projects discovery with fixed GraphQL queries.

This module does not create, update or delete GitHub resources.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .github_inspect import (
    PROJECT_DETAIL_QUERY as _PROJECT_QUERY,
    PROJECT_OWNER_QUERY as _OWNER_QUERY,
    PROJECT_VIEWER_QUERY as _VIEWER_QUERY,
    post_project_read_graphql,
)
from .model import WorkflowError

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ProjectsInspectionError(RuntimeError):
    """Report bounded, non-secret errors from Projects discovery."""


def _validate_login(login: str) -> str:
    """Validate a GitHub owner login.

    Args:
        login: GitHub user login.
    """
    if not _NAME.fullmatch(login):
        raise ProjectsInspectionError("Invalid GitHub owner login")
    return login


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    """Validate a mapping returned by GitHub.

    Args:
        value: Response object.
        label: Error context.
    """
    if not isinstance(value, dict):
        raise ProjectsInspectionError(f"Missing or invalid {label}")
    return value


def _post_graphql(query: str, variables: Mapping[str, object], token: str) -> dict[str, Any]:
    """Read Project evidence through the trusted, fixed-query GitHub adapter.

    Args:
        query: Fixed approved Project query.
        variables: Variables for the approved query.
        token: Read-capable credential held by the trusted caller.
    """
    try:
        return post_project_read_graphql(query, variables, token)
    except WorkflowError as exc:
        raise ProjectsInspectionError(str(exc)) from None


def discover_projects(token: str, owner: str | None = None) -> dict[str, Any]:
    """Discover viewer-owned or specified user-owned Projects without mutation.

    Args:
        token: API credential from a separate protected secret source.
        owner: Optional explicit GitHub user login.
    """
    if owner is None:
        data = _post_graphql(_VIEWER_QUERY, {}, token)
        node = _require_mapping(data.get("viewer"), "viewer")
    else:
        data = _post_graphql(_OWNER_QUERY, {"login": _validate_login(owner)}, token)
        node = _require_mapping(data.get("user"), "user")
    projects = _require_mapping(node.get("projectsV2"), "projectsV2")
    page = _require_mapping(projects.get("pageInfo"), "projects pageInfo")
    if page.get("hasNextPage") is not False:
        raise ProjectsInspectionError("Project listing truncated; cannot establish baseline")
    items = projects.get("nodes")
    if not isinstance(items, list):
        raise ProjectsInspectionError("Invalid project listing")
    return {"owner": node.get("login"), "projects": items, "complete": True}


def inspect_project(token: str, owner: str, number: int) -> dict[str, Any]:
    """Inspect a user-owned Project's fields and first 100 items.

    Args:
        token: API credential from a separate protected secret source.
        owner: GitHub user login.
        number: Project number.
    """
    if type(number) is not int or number < 1:
        raise ProjectsInspectionError("Invalid project number")
    data = _post_graphql(_PROJECT_QUERY, {
        "login": _validate_login(owner), "number": number,
    }, token)
    user = _require_mapping(data.get("user"), "project owner")
    if user.get("login") != owner:
        raise ProjectsInspectionError("Project owner identity mismatch")
    project = _require_mapping(user.get("projectV2"), "project")
    if type(project.get("number")) is not int or project["number"] != number:
        raise ProjectsInspectionError("Project number identity mismatch")
    if not isinstance(project.get("id"), str) or not project["id"]:
        raise ProjectsInspectionError("Project identity is missing")
    for name in ("fields", "items"):
        connection = _require_mapping(project.get(name), name)
        page = _require_mapping(connection.get("pageInfo"), f"{name} pagination")
        if page.get("hasNextPage") is not False:
            raise ProjectsInspectionError(f"{name} truncated; no baseline claim")
        if not isinstance(connection.get("nodes"), list):
            raise ProjectsInspectionError(f"Invalid {name} nodes")
    return {"owner": owner, "project": dict(project), "complete": True}


def _validate_issue_url(url: object, repository: str, number: int) -> None:
    """Require an exact canonical GitHub Issue identity without HTTP access.

    Args:
        url: URL returned in the Project issue response.
        repository: Expected full repository name.
        number: Expected issue number.
    """
    if url != f"https://github.com/{repository}/issues/{number}":
        raise ProjectsInspectionError("Issue canonical URL identity mismatch")


def _normalize_issue_item(
    item: Mapping[str, Any], issue: Mapping[str, Any], repository: str,
    issue_number: int, project_number: int,
) -> dict[str, Any]:
    """Validate one Project item before reporting a work-contract snapshot.

    Args:
        item: Verified item matching an issue number.
        issue: Issue object embedded in the Project item.
        repository: Expected full repository identity.
        issue_number: Expected issue number.
        project_number: Project from which the item was retrieved.
    """
    repo = _require_mapping(issue.get("repository"), "issue repository")
    if repo.get("nameWithOwner") != repository:
        raise ProjectsInspectionError("Issue repository identity mismatch")
    if type(issue.get("number")) is not int or issue["number"] != issue_number:
        raise ProjectsInspectionError("Issue number identity mismatch")
    if not isinstance(issue.get("id"), str) or not issue["id"]:
        raise ProjectsInspectionError("Issue immutable identity is missing")
    _validate_issue_url(issue.get("url"), repository, issue_number)
    if not isinstance(issue.get("body"), str) or not issue["body"].strip():
        raise ProjectsInspectionError("Issue work contract is missing")
    assignees = _require_mapping(issue.get("assignees"), "assignees")
    page = _require_mapping(assignees.get("pageInfo"), "assignee pagination")
    if page.get("hasNextPage") is not False:
        raise ProjectsInspectionError("Issue assignees may be truncated")
    people = assignees.get("nodes")
    if not isinstance(people, list) or any(
        not isinstance(person, dict) or not isinstance(person.get("login"), str)
        for person in people
    ):
        raise ProjectsInspectionError("Invalid issue assignees")
    field = item.get("fieldValueByName")
    if not isinstance(field, dict) or not isinstance(field.get("name"), str):
        raise ProjectsInspectionError("Project Status is missing or unknown")
    if not isinstance(field.get("updatedAt"), str) or not field["updatedAt"]:
        raise ProjectsInspectionError("Project Status timestamp is unknown")
    return {
        "repository": repository, "issue_number": issue_number,
        "project_number": project_number, "item_id": item.get("id"),
        "issue_id": issue.get("id"), "title": issue.get("title"),
        "body": issue["body"], "issue_state": issue.get("state"),
        "issue_updated_at": issue.get("updatedAt"),
        "status": field["name"], "status_updated_at": field["updatedAt"],
        "assignees": [person["login"] for person in people],
        "project_listing_complete": True, "architect_intent_authorized": "unverified",
        "not_retrieved": ["issue_activity", "authority_provenance",
                          "dependency_relationships"],
    }


def inspect_issue_work_item(
    token: str, owner: str, project_number: int,
    repository: str, issue_number: int,
) -> dict[str, Any]:
    """Retrieve one attributable issue snapshot, never approval or authority.

    Args:
        token: Credential from a separately isolated read-only caller.
        owner: Project owner.
        project_number: Project number.
        repository: Expected owner/repository.
        issue_number: Required issue number.
    """
    parts = repository.split("/")
    if len(parts) != 2 or any(not _NAME.fullmatch(p) for p in parts):
        raise ProjectsInspectionError("Invalid repository identity")
    if type(issue_number) is not int or issue_number <= 0:
        raise ProjectsInspectionError("Invalid issue number")
    snapshot = inspect_project(token, owner, project_number)
    project = _require_mapping(snapshot["project"], "project")
    items = _require_mapping(project["items"], "items")["nodes"]
    matches: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for item in items:
        entry = _require_mapping(item, "project item")
        issue = entry.get("content")
        if entry.get("type") != "ISSUE" or not isinstance(issue, dict):
            continue
        if issue.get("number") == issue_number:
            matches.append((entry, issue))
    if len(matches) != 1:
        raise ProjectsInspectionError("Issue absent or ambiguous in Project")
    item, issue = matches[0]
    return _normalize_issue_item(
        item, issue, repository, issue_number, project_number
    )
