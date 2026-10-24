"""Read authoritative SAGE action and shared context from a pinned Git commit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


class ContextError(ValueError):
    """Indicate that governing context cannot be reconstructed safely."""


def git(repo: Path, *args: str) -> str:
    """Run Git without a shell.

    Args:
        repo: Local disposable Git clone.
        *args: Individual Git arguments.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        text=True, capture_output=True, timeout=45,
    )
    return proc.stdout.strip()


def clone_repository(url: str, destination: Path) -> str:
    """Clone an explicitly configured public repository and pin its commit.

    Args:
        url: Administrator-defined, read-only Git remote.
        destination: Disposable checkout path.
    """
    if destination.exists():
        raise ContextError("repository destination already exists")
    subprocess.run(
        ["git", "clone", "--depth=1", "--single-branch", "--branch=main",
         "--", url, str(destination)],
        check=True, capture_output=True, text=True, timeout=90,
    )
    return git(destination, "rev-parse", "HEAD")


def read_versioned(repo: Path, revision: str, path: str) -> bytes:
    """Read one exact repository object at a committed revision.

    Args:
        repo: Local repository.
        revision: Full pinned Git commit.
        path: Hardcoded repository-relative document path.
    """
    if len(revision) != 40 or not all(c in "0123456789abcdef" for c in revision):
        raise ContextError("invalid pinned commit")
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        capture_output=True, check=True, timeout=30,
    )
    return result.stdout


def accepted_action(registry: dict[str, Any], action_id: str) -> dict[str, Any]:
    """Find one action with an actual governed acceptance transition.

    Args:
        registry: Repository-owned improvement-action registry.
        action_id: Exact requested action identifier.
    """
    matches = [a for a in registry.get("actions", [])
               if a.get("action_id") == action_id]
    if len(matches) != 1:
        raise ContextError("exact accepted action not found in Git")
    action = matches[0]
    history = action.get("history", [])
    if not any(item.get("to_status") == "accepted" for item in history):
        raise ContextError("action lacks a recorded acceptance transition")
    if action.get("current_status") not in {"accepted", "implemented", "validated"}:
        raise ContextError("action is not in an executable accepted status")
    return action


def compile_context(repo: Path, revision: str,
                    action_id: str) -> dict[str, Any]:
    """Compile common, provenance-bound context for every RACI participant.

    Args:
        repo: Disposable clone of authoritative Git.
        revision: Pinned commit SHA.
        action_id: Exact accepted action identifier.
    """
    paths = ["sage-improvement-actions.json", "AGENTS.md", "SAGE.md"]
    contents = {path: read_versioned(repo, revision, path) for path in paths}
    registry = json.loads(contents[paths[0]])
    action = accepted_action(registry, action_id)
    sources = {path: hashlib.sha256(data).hexdigest()
               for path, data in contents.items()}
    return {
        "objective_id": action_id,
        "revision": revision,
        "objective": action["desired_outcome"],
        "acceptance_criteria": action.get("acceptance_criteria", []),
        "action": action,
        "source_sha256": sources,
        "governance": {path: contents[path].decode("utf-8")[:12000]
                       for path in paths[1:]},
        "governance_excerpt_limit": 12000,
    }


def pin_revision(repo: Path, revision: str) -> str:
    """Fetch an explicit historical commit to restore an earlier cognitive point.

    Args:
        repo: Disposable Git clone.
        revision: Exact forty-character SHA-1 commit identifier.
    """
    if len(revision) != 40 or not all(c in "0123456789abcdef" for c in revision):
        raise ContextError("invalid historical revision")
    subprocess.run(
        ["git", "-C", str(repo), "fetch", "--unshallow", "origin", "main"],
        check=True, capture_output=True, text=True, timeout=120,
    )
    if git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}") != revision:
        raise ContextError("historical Git commit is unavailable")
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor",
         revision, "origin/main"],
        check=False, capture_output=True, timeout=30,
    )
    if ancestor.returncode != 0:
        raise ContextError("historical commit is not in governed main lineage")
    return revision
