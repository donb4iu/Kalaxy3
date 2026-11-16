"""Read the pinned Issue #50 candidate projection without creating or modifying it.

Only a loopback Bolt endpoint is accepted. Credentials come from the runtime
process environment and are never saved in output artifacts.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def git_bytes(repo: Path, *args: str) -> bytes:
    """Read an exact Git object or revision without changing repository state.

    Args:
        repo: Existing Issue #50 feature checkout.
        *args: Git read arguments.
    """
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True).stdout


def verify_candidate_module(repo: Path, revision: str) -> Path:
    """Require native read-only code to match the pinned committed source.

    Args:
        repo: Issue #50 feature checkout.
        revision: Exact expected feature commit.
    """
    observed = git_bytes(repo, "rev-parse", "HEAD").decode().strip()
    if observed != revision:
        raise ValueError("Issue #50 checkout HEAD is not the expected revision")
    folder = repo / "scripts" / "sage"
    for name in ("sage_neo4j_objective.py", "sage_neo4j_inventory.py"):
        committed = git_bytes(repo, "show", f"HEAD:scripts/sage/{name}")
        if committed != (folder / name).read_bytes():
            raise ValueError("Pinned candidate reader was locally modified")
    return folder


def require_loopback(uri: str) -> None:
    """Reject expansion of candidate access beyond the existing local boundary.

    Args:
        uri: Bolt URI for an already authorized loopback tunnel.
    """
    parsed = urlparse(uri)
    if parsed.scheme not in {"bolt", "bolt+ssc", "bolt+s"} or (
        parsed.hostname not in {"localhost", "127.0.0.1"}
    ) or parsed.username or parsed.password:
        raise ValueError("Only credential-free loopback Bolt URI is supported")


def receipt_projection(receipt: Path, revision: str) -> str:
    """Read an existing native receipt without copying its operational fields.

    Args:
        receipt: Native Issue #50 live receipt JSON.
        revision: Expected feature commit.
    """
    document = json.loads(receipt.read_text(encoding="utf-8"))
    if document.get("feature_revision") != revision:
        raise ValueError("Native receipt feature revision disagrees with checkout")
    projection = document.get("projection_id")
    if not isinstance(projection, str) or not projection.startswith(revision + ":"):
        raise ValueError("Native receipt lacks a pinned candidate projection ID")
    return projection


def read_candidate(repo: Path, revision: str, uri: str,
                   projection: str, objective: str) -> dict[str, Any]:
    """Call the existing native objective_evidence function in read-only mode.

    Args:
        repo: Exact-revision Issue #50 checkout.
        revision: Full feature commit.
        uri: Already-authorized loopback Bolt endpoint.
        projection: Exact candidate graph identity.
        objective: Architect-owned query string.
    """
    require_loopback(uri)
    folder = verify_candidate_module(repo, revision)
    password = os.environ.get("SAGE_NEO4J_PASSWORD")
    if not password:
        raise ValueError("SAGE_NEO4J_PASSWORD must already be set")
    sys.path.insert(0, str(folder))
    native = importlib.import_module("sage_neo4j_objective")
    from neo4j import GraphDatabase, READ_ACCESS  # type: ignore[import-not-found]

    with GraphDatabase.driver(uri, auth=("neo4j", password)) as driver:
        with driver.session(default_access_mode=READ_ACCESS) as session:
            return native.objective_evidence(session, projection, objective, limit=100)


def main() -> int:
    """Capture a single bounded native read response outside the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-repo", type=Path, required=True)
    parser.add_argument("--candidate-revision", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--uri", required=True)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.resolve().is_relative_to(args.candidate_repo.resolve()):
        raise ValueError("Refusing output inside Issue #50 checkout")
    projection = receipt_projection(args.receipt, args.candidate_revision)
    result = read_candidate(args.candidate_repo, args.candidate_revision,
                            args.uri, projection, args.objective)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("GRAPH_CAPTURE=EXISTING_CANDIDATE_READ_ONLY")
    print("GRAPH_RESPONSE=" + str(args.out))
    print("GRAPH_PAGE_INCOMPLETE=" + str(result.get("next_offset") is not None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
