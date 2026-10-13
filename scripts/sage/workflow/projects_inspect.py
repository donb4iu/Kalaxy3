"""Read-only GitHub Projects discovery with fixed GraphQL queries.

This module does not create, update or delete GitHub resources.
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_GRAPHQL_URL = "https://api.github.com/graphql"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_MAX_BYTES = 2 * 1024 * 1024
_VIEWER_QUERY = """query { viewer { login projectsV2(first: 30) {
 nodes { id number title closed url } pageInfo { hasNextPage } } } }"""
_OWNER_QUERY = """query($login:String!) { user(login:$login) {
 login projectsV2(first:30) { nodes { id number title closed url }
 pageInfo { hasNextPage } } } }"""
_PROJECT_QUERY = """query($login:String!, $number:Int!) { user(login:$login) {
 projectV2(number:$number) { id number title closed url
 fields(first:50) { nodes { ... on ProjectV2FieldCommon { id name dataType }
 ... on ProjectV2SingleSelectField { id name options { id name } }
 ... on ProjectV2IterationField { id name configuration { duration } } }
 pageInfo { hasNextPage } }
 items(first:100) { nodes { id type content { ... on Issue { id number title url state }
 ... on PullRequest { id number title url state } } }
 pageInfo { hasNextPage } } } } }"""


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
    """Execute one fixed read-only GraphQL query.

    Args:
        query: One of the three module-owned query strings.
        variables: Exact query variables.
        token: API bearer credential, never logged or returned.
    """
    if query not in (_VIEWER_QUERY, _OWNER_QUERY, _PROJECT_QUERY):
        raise ProjectsInspectionError("Unapproved GraphQL query")
    if not token or any(c in token for c in "\r\n"):
        raise ProjectsInspectionError("Authorized GitHub API token required")
    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = Request(_GRAPHQL_URL, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Kalaxy3-SAGE-projects.inspect/0.1",
    })
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(_MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ProjectsInspectionError("GitHub Projects API request failed") from None
    if len(raw) > _MAX_BYTES:
        raise ProjectsInspectionError("GitHub Projects response too large")
    try:
        document = _require_mapping(json.loads(raw), "GraphQL response")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ProjectsInspectionError("Invalid GitHub GraphQL response") from None
    if document.get("errors"):
        raise ProjectsInspectionError("GitHub Projects GraphQL returned errors")
    return dict(_require_mapping(document.get("data"), "GraphQL data"))


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
    project = _require_mapping(user.get("projectV2"), "project")
    for name in ("fields", "items"):
        connection = _require_mapping(project.get(name), name)
        page = _require_mapping(connection.get("pageInfo"), f"{name} pagination")
        if page.get("hasNextPage") is not False:
            raise ProjectsInspectionError(f"{name} truncated; no baseline claim")
        if not isinstance(connection.get("nodes"), list):
            raise ProjectsInspectionError(f"Invalid {name} nodes")
    return {"owner": owner, "project": dict(project), "complete": True}
