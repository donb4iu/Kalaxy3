"""Trusted operator-approved bounded routine Git lifecycle controller."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from workflow import (
    AtomicFileWriter,
    CommandRunner,
    GitInspector,
    GitRepository,
    JsonlEventLogger,
    PrimitiveCatalog,
    WorkflowError,
)

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "git.inspect",
    "git.repository",
    "file.atomic-preserve-mode",
)


def _load_object(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise WorkflowError(f"{label} must be a JSON object")
    return value


def _command_sha256(argv: tuple[str, ...]) -> str:
    payload = json.dumps(
        list(argv),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), indent=4, sort_keys=False) + "\n"


def _expected_argv(state_path: Path, proposal_path: Path) -> tuple[str, ...]:
    return (
        "python3",
        "scripts/sage/sage-routine-git-lifecycle.py",
        "--state",
        str(state_path),
        "--proposal",
        str(proposal_path),
        "--apply",
    )


def _validate_authorization(
    state: Mapping[str, Any],
    proposal: Mapping[str, Any],
    *,
    state_path: Path,
    proposal_path: Path,
) -> dict[str, Any]:
    if state.get("record_type") != "sage-request-execution-state":
        raise WorkflowError("routine Git lifecycle state record type is invalid")
    if state.get("current_boundary") != "routine-git-lifecycle":
        raise WorkflowError("routine Git lifecycle is not the active request boundary")
    current_proposal = Path(str(state.get("current_proposal", ""))).expanduser().resolve()
    if current_proposal != proposal_path:
        raise WorkflowError("active request proposal path does not match controller proposal")
    if proposal.get("boundary") != "routine-git-lifecycle":
        raise WorkflowError("operator proposal is not a routine Git lifecycle boundary")
    proposal_schema = proposal.get("schema_version")
    contract = proposal.get("operator_contract")
    if not isinstance(contract, dict):
        raise WorkflowError("routine Git lifecycle operator contract is invalid")
    if proposal_schema == "1.2":
        if (
            contract.get("approval_required") is not True
            or contract.get("pasted_output_required") is not False
            or contract.get("repository_receipt_required") is not True
            or contract.get("next_boundary_blocked_until_verified") is not True
        ):
            raise WorkflowError("routine Git lifecycle repository-receipt operator contract drifted")
    elif proposal_schema == "1.0":
        if (
            contract.get("approval_required") is not True
            or contract.get("pasted_output_required") is not True
            or contract.get("repository_receipt_required") not in {None, False}
            or contract.get("next_boundary_blocked_until_verified") is not True
        ):
            raise WorkflowError("already-open legacy routine proposal contract drifted")
    else:
        raise WorkflowError("routine Git lifecycle requires schema 1.2 or an already-open legacy schema 1.0 proposal")
    if proposal.get("controller") != "sage-request-execution":
        raise WorkflowError("routine Git lifecycle controller ownership drifted")

    repository = proposal.get("repository")
    if not isinstance(repository, dict):
        raise WorkflowError("routine Git lifecycle repository authority is missing")
    branch = str(state.get("repository_branch", ""))
    expected_head = str(state.get("base_head", ""))
    base_main_head = str(state.get("base_main_head", ""))
    if not branch or branch == "main":
        raise WorkflowError("routine Git lifecycle requires a non-main feature branch")
    if repository.get("branch") != branch or repository.get("head") != expected_head:
        raise WorkflowError("operator proposal repository authority does not match request state")
    if not _SHA40.fullmatch(expected_head) or not _SHA40.fullmatch(base_main_head):
        raise WorkflowError("routine Git lifecycle requires exact SHA-1 authorities")

    declared = tuple(str(item) for item in state.get("declared_paths", ()))
    if not declared or list(declared) != proposal.get("change_scope"):
        raise WorkflowError("routine Git lifecycle declared path scope does not match active proposal")

    plan = state.get("operator_plan")
    if not isinstance(plan, dict):
        raise WorkflowError("routine Git lifecycle operator plan is missing")
    remote = str(plan.get("push_remote", ""))
    message = str(plan.get("commit_message", ""))
    if remote != "origin":
        raise WorkflowError("routine Git lifecycle is limited to the origin remote")
    if not message or "\n" in message or "\r" in message:
        raise WorkflowError("routine Git lifecycle commit message is invalid")

    validations = state.get("validation")
    if not isinstance(validations, list) or not validations:
        raise WorkflowError("routine Git lifecycle validation receipts are missing")
    if validations != proposal.get("validation"):
        raise WorkflowError("routine Git lifecycle proposal validation receipts drifted")
    if any(not isinstance(item, dict) or item.get("status") != "pass" for item in validations):
        raise WorkflowError("routine Git lifecycle requires pass-only validation receipts")

    command = proposal.get("command")
    if not isinstance(command, dict):
        raise WorkflowError("routine Git lifecycle proposal command is missing")
    argv = _expected_argv(state_path, proposal_path)
    if tuple(str(item) for item in command.get("argv", ())) != argv:
        raise WorkflowError("routine Git lifecycle proposal command drifted")
    if command.get("sha256") != _command_sha256(argv):
        raise WorkflowError("routine Git lifecycle proposal command digest drifted")
    if command.get("executed_by_helper") is not False:
        raise WorkflowError("routine Git lifecycle approval must remain operator executed")

    if state.get("authority_receipt") != proposal.get("authority_receipt"):
        raise WorkflowError("routine Git lifecycle authority receipt drifted")
    if state.get("component_manifest") != proposal.get("component_manifest"):
        raise WorkflowError("routine Git lifecycle component manifest drifted")

    return {
        "branch": branch,
        "expected_head": expected_head,
        "base_main_head": base_main_head,
        "declared_paths": declared,
        "commit_message": message,
        "remote": remote,
        "command_sha256": str(command["sha256"]),
        "proposal_id": str(proposal.get("proposal_id", "")),
    }


def run_controller(
    repo: Path,
    state_path: Path,
    proposal_path: Path,
    *,
    apply: bool,
) -> Mapping[str, Any]:
    """Execute one checksum-bound operator-approved stage/commit/push lifecycle."""

    if not apply:
        raise WorkflowError("routine Git lifecycle requires explicit --apply operator approval")

    repo = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    proposal_path = proposal_path.expanduser().resolve()
    if not (repo / ".git").exists():
        raise WorkflowError(f"Git repository not found: {repo}")
    if not state_path.is_file() or not proposal_path.is_file():
        raise WorkflowError("routine Git lifecycle state/proposal is missing")

    state = _load_object(state_path, "request execution state")
    proposal = _load_object(proposal_path, "operator proposal")
    authorization = _validate_authorization(
        state,
        proposal,
        state_path=state_path,
        proposal_path=proposal_path,
    )

    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    event_log = state_path.parent / "routine-git-lifecycle-events.jsonl"
    logger = JsonlEventLogger(
        event_log,
        "sage.routine-git-lifecycle",
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_path.parent),
        base_environment={name: "" for name in _SECRET_ENVIRONMENT_NAMES},
    )
    inspector = GitInspector(repo, runner)

    branch = str(authorization["branch"])
    expected_head = str(authorization["expected_head"])
    base_main_head = str(authorization["base_main_head"])
    declared = tuple(str(item) for item in authorization["declared_paths"])
    remote = str(authorization["remote"])

    inspector.require_branch(branch)
    inspector.require_head(expected_head)
    inspector.require_exact_paths(declared)
    if inspector.staged_paths():
        raise WorkflowError("routine Git lifecycle requires an unstaged declared change set")
    upstream = inspector.upstream_head()
    if upstream != expected_head:
        raise WorkflowError(
            f"routine Git lifecycle upstream authority mismatch: expected={expected_head}, observed={upstream}"
        )
    if inspector.remote_head(remote, branch) != expected_head:
        raise WorkflowError("routine Git lifecycle remote feature branch drifted")
    live_main = inspector.remote_head(remote, "main")
    if live_main != base_main_head:
        raise WorkflowError(
            f"routine Git lifecycle remote main authority changed: expected={base_main_head}, observed={live_main}"
        )

    repository = GitRepository(repo, runner, remote=remote)
    commit = repository.commit_and_push(
        branch=branch,
        exact_paths=declared,
        message=str(authorization["commit_message"]),
        apply=True,
    )

    inspector.require_branch(branch)
    inspector.require_clean()
    inspector.require_head(commit)
    inspector.require_upstream_equal()
    remote_branch = inspector.remote_head(remote, branch)
    if remote_branch != commit:
        raise WorkflowError("routine Git lifecycle remote branch does not contain the resulting commit")
    history = inspector.run_read_only(
        ("rev-list", "--parents", f"{expected_head}..{commit}"),
        label="Verify routine Git lifecycle single-commit topology",
    )
    rows = [line.split() for line in history.stdout.splitlines() if line]
    if rows != [[commit, expected_head]]:
        raise WorkflowError(
            f"routine Git lifecycle did not create exactly one commit from the approved HEAD: {rows}"
        )
    changed = inspector.diff_paths(expected_head, commit)
    if changed != set(declared):
        raise WorkflowError(
            f"routine Git lifecycle committed path scope mismatch: expected={sorted(declared)}, observed={sorted(changed)}"
        )

    receipt = {
        "schema_version": "1.0",
        "record_type": "sage-routine-git-lifecycle-receipt",
        "status": "pass",
        "proposal_id": authorization["proposal_id"],
        "command_sha256": authorization["command_sha256"],
        "branch": branch,
        "pre_head": expected_head,
        "base_main_head": base_main_head,
        "commit": commit,
        "remote": remote,
        "remote_branch_head": remote_branch,
        "declared_paths": list(declared),
        "event_log": str(event_log),
    }
    receipt_path = state_path.parent / "routine-git-lifecycle-receipt.json"
    writer = AtomicFileWriter((state_path.parent,))
    writer.write_text(receipt_path, _stable_json(receipt), new_mode=0o600)
    return {
        **receipt,
        "receipt": str(receipt_path),
        "receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
    }
