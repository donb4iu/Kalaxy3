"""Bind approved LangGraph work to the existing governed request executor."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


class HandoffError(RuntimeError):
    """Fail an unverified execution handoff without changing authority."""


def git(repo: Path, *args: str) -> str:
    """Read Git state without shell interpolation.

    Args:
        repo: Isolated execution checkout.
        *args: Exact Git argument tokens.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        capture_output=True, text=True, timeout=40,
    )
    return result.stdout.strip()


def prepare_workspace(root: Path, url: str, submission: dict[str, str]) -> Path:
    """Reconstruct an isolated feature branch from the configured Git origin.

    Args:
        root: Persistent runtime workspaces directory.
        url: Administrator-controlled Git read-only remote.
        submission: Bound feature branch and expected commit.
    """
    branch = submission.get("branch", "")
    if not re.fullmatch(r"feature/[A-Za-z0-9._/-]+", branch) or ".." in branch:
        raise HandoffError("invalid feature-branch identity")
    identity = hashlib.sha256(f"{url}\0{branch}".encode()).hexdigest()[:20]
    target = root / identity
    if not target.exists():
        root.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--single-branch", "--branch", branch,
             "--", url, str(target)], check=True,
            capture_output=True, text=True, timeout=120,
        )
    if git(target, "remote", "get-url", "origin") != url:
        raise HandoffError("execution checkout origin does not match configuration")
    if git(target, "branch", "--show-current") != branch:
        raise HandoffError("execution checkout branch changed")
    if git(target, "status", "--porcelain=v1", "--untracked-files=all"):
        raise HandoffError("execution checkout is not clean")
    if git(target, "rev-parse", "HEAD") != submission.get("head"):
        raise HandoffError("execution checkout commit differs from qualified proposal")
    return target


def verify_handoff(context: dict[str, Any], submission: dict[str, str],
                   repo: Path, proposals: Path) -> Path:
    """Require exact accepted action, Git ancestry and content-addressed package.

    Args:
        context: Shared authoritative Git context.
        submission: Bound, non-model-supplied execution identity.
        repo: Verified isolated execution checkout.
        proposals: Content-addressed artifact directory.
    """
    action = context.get("action", {})
    if action.get("action_id") != context.get("objective_id"):
        raise HandoffError("objective identity does not match accepted Git action")
    if action.get("current_status") not in {"accepted", "implemented", "validated"}:
        raise HandoffError("Git action has no currently effective authority")
    if not any(entry.get("to_status") == "accepted" for entry in action.get("history", [])):
        raise HandoffError("no recorded accepted-action transition")
    if context.get("objective") != action.get("desired_outcome"):
        raise HandoffError("request differs from accepted Git objective")
    if submission.get("revision") != context.get("revision"):
        raise HandoffError("context revision differs from proposed authority")
    if git(repo, "rev-parse", "HEAD") != submission.get("head"):
        raise HandoffError("Git HEAD does not match execution submission")
    digest = submission.get("package_id", "")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise HandoffError("invalid content-addressed proposal identity")
    package = proposals / f"{digest}.zip"
    if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest() != digest:
        raise HandoffError("proposal archive missing or modified")
    return package


def invoke_executor(repo: Path, request: str, proposal: Path,
                    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
                    ) -> dict[str, Any]:
    """Execute the repository-owned request adapter, preserving its Git boundary.

    Args:
        repo: Clean feature checkout containing the existing SAGE implementation.
        request: Exact accepted Architect objective.
        proposal: Verified immutable source proposal.
        runner: Injected subprocess runner for testing.
    """
    script = repo / "scripts/sage/sage-request-execute.py"
    if not script.is_file():
        raise HandoffError("repository request-execution adapter missing")
    argv = [sys.executable, str(script), "--repo", str(repo),
            "--request", request, "--proposal", str(proposal)]
    result = runner(argv, capture_output=True, text=True, timeout=3600,
                    cwd=str(repo), env=os.environ.copy(), check=False)
    if result.returncode != 0:
        raise HandoffError("request executor failed: " + result.stderr[-1200:])
    if "Kalaxy3 SAGE request execution: PASS" not in result.stdout:
        raise HandoffError("request executor did not produce verified boundary")
    if "Operator proposal:" not in result.stdout or "Continuation state:" not in result.stdout:
        raise HandoffError("missing continuation state or governed Git proposal")
    details = {}
    for line in result.stdout.splitlines():
        for label, field in (("Operator proposal:", "proposal_path"),
                             ("Continuation state:", "state_path")):
            if line.startswith(label):
                details[field] = line[len(label):].strip()
    if not all(Path(path).is_file() for path in details.values()):
        raise HandoffError("execution receipt references missing state files")
    return {"status": "governed-git-boundary-pending", **details,
            "proposal_sha256": hashlib.sha256(proposal.read_bytes()).hexdigest()}


def execute_qualified(state: dict[str, Any], *, repo: Path, proposals: Path,
                      executor: Callable[[Path, str, Path], dict[str, Any]] = invoke_executor
                      ) -> dict[str, Any]:
    """Hand a qualified objective to the existing request-execution adapter.

    Args:
        state: LangGraph checkpointed context, role findings and proposal identity.
        repo: Verified isolated feature checkout.
        proposals: Immutable content-addressed submission store.
        executor: Guarded execution adapter, replaceable for fixture tests.
    """
    if state.get("referee_disposition") not in {"allow", "unsupported-objection-recused"}:
        raise HandoffError("Referee correction remains unresolved")
    submission = state.get("execution_submission")
    if not isinstance(submission, dict):
        raise HandoffError("no qualified executable contribution was supplied")
    context = state["context"]
    package = verify_handoff(context, submission, repo, proposals)
    result = executor(repo, context["objective"], package)
    if result.get("status") not in {"governed-git-boundary-pending", "already-realized"}:
        raise HandoffError("existing adapter did not verify the execution boundary")
    return {"execution_receipt": result, "outcome": result["status"]}
