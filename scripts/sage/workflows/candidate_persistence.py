#!/usr/bin/env python3
"""Authorize exact dirty-candidate persistence before clean-HEAD semantics."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from workflow import (
    AtomicFileWriter,
    CommandRunner,
    CommandSpec,
    GitInspector,
    JsonlEventLogger,
    OperatorGitProposal,
    PrimitiveCatalog,
    WorkflowError,
)

WORKFLOW_ID = "sage.candidate-persistence"
STATE_ROOT = Path(
    "~/.local/state/kalaxy3/sage-candidate-persistence"
).expanduser()
PRIMITIVES = (
    "logging.events",
    "command.run",
    "git.inspect",
    "file.atomic-preserve-mode",
    "operator.git-proposal",
)


def _json(value: Mapping[str, Any]) -> str:
    """Render persisted JSON."""
    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def _runtime(
    repo: Path,
    state_dir: Path,
) -> tuple[AtomicFileWriter, CommandRunner, GitInspector]:
    """Build repository-owned validation primitives."""
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(PRIMITIVES),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir),
        base_environment={},
    )
    writer = AtomicFileWriter((state_dir, STATE_ROOT))
    return writer, runner, GitInspector(repo, runner)


def _paths(repo: Path, values: Sequence[str]) -> tuple[str, ...]:
    """Validate exact repository-relative candidate paths."""
    result: set[str] = set()
    for raw in values:
        value = Path(raw)
        relative = value.as_posix().lstrip("./")
        target = repo / relative
        if (
            value.is_absolute()
            or ".." in value.parts
            or not relative
            or not target.is_file()
            or target.is_symlink()
        ):
            raise WorkflowError(f"invalid candidate path: {raw}")
        result.add(relative)
    if not result or len(result) != len(values):
        raise WorkflowError("candidate paths must be non-empty and unique")
    return tuple(sorted(result))


def _message(value: str) -> str:
    """Validate one bounded commit message."""
    result = value.strip()
    if not result or "\n" in result or "\r" in result or len(result) > 120:
        raise WorkflowError("candidate persistence commit message is invalid")
    return result


def _validate(repo: Path, runner: CommandRunner) -> list[dict[str, Any]]:
    """Run the bounded validation set."""
    commands = (
        (
            "Objective execution self-test",
            ("python3", "scripts/sage/sage-objective-execution.py", "--self-test"),
        ),
        (
            "Objective execution guardrail",
            ("python3", "scripts/sage/sage-objective-execution-guardrail.py"),
        ),
        (
            "Request execution guardrail",
            ("python3", "scripts/sage/sage-request-execution-guardrail.py"),
        ),
        (
            "Intent-to-outcome guardrail",
            ("python3", "scripts/sage/sage-intent-to-outcome-guardrail.py"),
        ),
        (
            "Branch lifecycle self-test",
            (
                "python3",
                "scripts/sage/sage-workflow-primitives-branch-lifecycle.py",
                "--self-test",
            ),
        ),
        (
            "Branch lifecycle guardrail",
            (
                "python3",
                "scripts/sage/"
                "sage-workflow-primitives-branch-lifecycle-guardrail.py",
            ),
        ),
    )
    receipts: list[dict[str, Any]] = []
    for index, (label, argv) in enumerate(commands, 1):
        result = runner.run(
            CommandSpec(
                "command.run",
                label,
                argv,
                repo,
                timeout_seconds=900,
            ),
            step_id=f"candidate-validation-{index:02d}",
        )
        receipts.append(
            {
                "label": label,
                "reference": "command.run",
                "status": "pass",
                "sha256": result.output_sha256,
            }
        )
    return receipts


def _authority(
    inspector: GitInspector,
    snapshot: Any,
    declared: tuple[str, ...],
) -> tuple[str, str]:
    """Require synchronized feature authority around exact dirty scope."""
    if not snapshot.branch or snapshot.branch == "main":
        raise WorkflowError("candidate persistence requires a feature branch")
    inspector.require_exact_paths(declared)
    if inspector.staged_paths():
        raise WorkflowError("candidate persistence requires unstaged changes")
    if snapshot.upstream_head != snapshot.head:
        raise WorkflowError("candidate persistence upstream HEAD drifted")
    remote_branch = inspector.remote_head("origin", snapshot.branch)
    if remote_branch != snapshot.head:
        raise WorkflowError("candidate persistence remote branch drifted")
    remote_main = inspector.remote_head("origin", "main")
    if not remote_main:
        raise WorkflowError("candidate persistence remote main is unavailable")
    return remote_branch, remote_main


def _write_support(
    writer: AtomicFileWriter,
    state_dir: Path,
    snapshot: Any,
    remote_branch: str,
    remote_main: str,
    declared: tuple[str, ...],
) -> tuple[Path, Path]:
    """Persist authority and component evidence."""
    authority = state_dir / "candidate-persistence-authority.json"
    components = state_dir / "candidate-persistence-components.json"
    writer.write_text(
        authority,
        _json(
            {
                "schema_version": "1.0",
                "record_type": "sage-candidate-persistence-authority",
                "status": "pass",
                "branch": snapshot.branch,
                "head": snapshot.head,
                "upstream_head": snapshot.upstream_head,
                "remote_branch_head": remote_branch,
                "remote_main_head": remote_main,
                "declared_paths": list(declared),
            }
        ),
        new_mode=0o600,
    )
    writer.write_text(
        components,
        _json(
            {
                "schema_version": "1.0",
                "record_type": "sage-candidate-persistence-components",
                "component_id": WORKFLOW_ID,
                "mutation_owner": "sage.routine-git-lifecycle",
                "direct_git_mutation": False,
            }
        ),
        new_mode=0o600,
    )
    return authority, components


def start(
    repo: Path,
    values: Sequence[str],
    commit_message: str,
) -> Mapping[str, Any]:
    """Create one exact routine-Git persistence authorization."""
    resolved = repo.expanduser().resolve()
    declared = _paths(resolved, values)
    message = _message(commit_message)
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    state_dir = STATE_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir.mkdir()
    writer, runner, inspector = _runtime(resolved, state_dir)
    snapshot = inspector.snapshot()
    remote_branch, remote_main = _authority(inspector, snapshot, declared)
    validation = _validate(resolved, runner)
    authority, components = _write_support(
        writer,
        state_dir,
        snapshot,
        remote_branch,
        remote_main,
        declared,
    )
    state_path = state_dir / "candidate-persistence-state.json"
    proposal_path = state_dir / "operator-git-proposal.json"
    proposal = OperatorGitProposal.build(
        proposal_id=f"SAGE-GIT-{datetime.now().strftime('%Y%m%d')}-851",
        controller=WORKFLOW_ID,
        repository=snapshot,
        authority_receipt=str(authority),
        component_manifest=str(components),
        boundary="routine-git-lifecycle",
        change_scope=declared,
        validation=validation,
        command_argv=(
            "python3",
            "scripts/sage/sage-routine-git-lifecycle.py",
            "--state",
            str(state_path),
            "--proposal",
            str(proposal_path),
            "--apply",
        ),
        expected_result=(
            "Create and push exactly one commit containing the declared candidate."
        ),
        risk=(
            "Exact-scope feature-branch stage/commit/push only; no merge, "
            "rebase, reset, force push, branch deletion, or deployment."
        ),
        rollback="Do not execute; rollback requires separate governance.",
        post_command_verification=(
            "git status --porcelain=v1 --untracked-files=all",
            "git rev-parse HEAD",
            "git rev-parse @{upstream}",
        ),
    )
    OperatorGitProposal.write(proposal_path, proposal, writer)
    state = {
        "schema_version": "1.0",
        "record_type": "sage-candidate-persistence-state",
        "current_boundary": "routine-git-lifecycle",
        "current_proposal": str(proposal_path),
        "repository_branch": snapshot.branch,
        "base_head": snapshot.head,
        "base_main_head": remote_main,
        "declared_paths": list(declared),
        "operator_plan": {
            "commit_message": message,
            "push_remote": "origin",
        },
        "validation": validation,
        "authority_receipt": str(authority),
        "component_manifest": str(components),
    }
    writer.write_text(state_path, _json(state), new_mode=0o600)
    return {
        "status": "operator-approval-required",
        "state": str(state_path),
        "proposal": str(proposal_path),
        "proposal_sha256": hashlib.sha256(
            proposal_path.read_bytes()
        ).hexdigest(),
        "next_boundary": proposal["command"]["display"],
    }


def verify(repo: Path, state_path: Path, receipt_path: Path) -> Mapping[str, Any]:
    """Verify one candidate-persistence routine-Git receipt."""
    state = json.loads(state_path.resolve().read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.resolve().read_text(encoding="utf-8"))
    if state.get("record_type") != "sage-candidate-persistence-state":
        raise WorkflowError("candidate persistence state type is invalid")
    if (
        receipt.get("record_type") != "sage-routine-git-lifecycle-receipt"
        or receipt.get("status") != "pass"
        or receipt.get("declared_paths") != state.get("declared_paths")
    ):
        raise WorkflowError("candidate persistence receipt is invalid")
    _, _, inspector = _runtime(repo.resolve(), state_path.resolve().parent)
    commit = str(receipt["commit"])
    branch = str(state["repository_branch"])
    inspector.require_branch(branch)
    inspector.require_clean()
    inspector.require_head(commit)
    inspector.require_upstream_equal()
    if inspector.remote_head("origin", branch) != commit:
        raise WorkflowError("candidate persistence remote verification failed")
    return {"status": "verified", "commit": commit}


def self_test() -> None:
    """Exercise bounded input validation."""
    if _message("candidate persistence") != "candidate persistence":
        raise RuntimeError("candidate persistence message validation failed")
