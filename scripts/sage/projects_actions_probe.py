"""Read-only GitHub Projects permission probe for GitHub Actions."""
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

QUERY = "query { viewer { login projectsV2(first: 10) { nodes { number title url } } } }"


def inspect(token: str) -> dict[str, Any]:
    """Probe user Projects visibility using a fixed read-only query.

    Args:
        token: Ephemeral Actions GitHub token, not written to output.
    """
    if not token or "\n" in token or "\r" in token:
        return {"status": "unavailable", "reason": "no_valid_token"}
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "Kalaxy3-SAGE-projects-probe/1"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = json.load(response)
    except HTTPError as exc:
        return {"status": "unavailable", "reason": "http_error",
                "http_status": exc.code}
    except (URLError, TimeoutError, ValueError):
        return {"status": "unavailable", "reason": "network_or_response_error"}
    if not isinstance(body, dict) or body.get("errors"):
        return {"status": "unavailable", "reason": "graphql_denied_or_invalid"}
    viewer = (body.get("data") or {}).get("viewer")
    if not isinstance(viewer, dict):
        return {"status": "unavailable", "reason": "no_viewer"}
    projects = (viewer.get("projectsV2") or {}).get("nodes")
    if not isinstance(projects, list):
        return {"status": "unavailable", "reason": "no_projects_data"}
    return {"status": "accessible", "viewer": viewer.get("login"),
            "projects": [{"number": p.get("number"), "title": p.get("title"),
                          "url": p.get("url")} for p in projects if isinstance(p, dict)]}


def main() -> int:
    """Write sanitized proof output without leaking the token."""
    result = inspect(os.environ.get("GITHUB_TOKEN", ""))
    path = os.environ.get("GITHUB_OUTPUT_JSON", "projects-probe-result.json")
    with open(path, "w", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print(f"PROJECTS_PROBE_STATUS={result['status']}")
    print(f"PROJECTS_PROBE_REASON={result.get('reason', 'none')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
