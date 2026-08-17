"""Governed operator-proposal branch lifecycle composition for SAGE."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from workflow import (
    AtomicFileWriter,
    CommandRunner,
    GitInspector,
    JsonlEventLogger,
    OperatorGitProposal,
    PrimitiveCatalog,
    WorkflowError,
)

WORKFLOW_ID = "sage.branch-lifecycle"
WORKFLOW_VERSION = "0.1.0"
STATE_ROOT = Path("~/.local/state/kalaxy3/sage-branch-lifecycle").expanduser()
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "git.inspect",
    "file.atomic-preserve-mode",
    "operator.git-proposal",
)
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


def _stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), indent=4, sort_keys=False) + "\n"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _proposal_id(branch: str, phase: str) -> str:
    seed = int(hashlib.sha256(f"{branch}:{phase}".encode("utf-8")).hexdigest()[:8], 16) % 1000
    return f"SAGE-GIT-{datetime.now().strftime('%Y%m%d')}-{seed:03d}"


def _new_state_dir() -> Path:
    path = STATE_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path.mkdir(parents=True, exist_ok=False)
    return path


def _runtime(repo: Path, state_dir: Path):
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir),
        base_environment={name: "" for name in _SECRET_ENVIRONMENT_NAMES},
    )
    writer = AtomicFileWriter((state_dir,))
    return catalog, logger, writer, GitInspector(repo, runner)


def _remote_branch_exists(inspector: GitInspector, remote: str, branch: str) -> bool:
    reference = f"refs/heads/{branch}"
    result = inspector.run_read_only(
        ("ls-remote", "--heads", remote, reference),
        label=f"Check remote branch {remote}/{branch}",
    )
    lines = [line for line in result.stdout.splitlines() if line]
    if len(lines) > 1:
        raise WorkflowError(f"remote branch identity is ambiguous: {remote}/{branch}")
    return bool(lines)


def _local_branch_exists(inspector: GitInspector, branch: str) -> bool:
    result = inspector.run_read_only(
        ("rev-parse", branch),
        label=f"Check local branch {branch}",
        expected_codes=(0, 128),
    )
    return result.returncode == 0


def _write_common_receipts(
    writer: AtomicFileWriter,
    state_dir: Path,
    *,
    request: str,
    expected_main: str,
    branch: str,
    repository: Mapping[str, Any],
) -> tuple[Path, Path, list[dict[str, Any]]]:
    authority = {
        "schema_version": "1.0",
        "record_type": "sage-branch-lifecycle-authority",
        "request": request,
        "architect_authority": True,
        "frozen_main": expected_main,
        "target_branch": branch,
        "repository": dict(repository),
        "mutation_gate": {
            "status": "review-ready",
            "operator_approval_required": True,
            "autonomous_mutation_allowed": False,
        },
    }
    authority_path = state_dir / "authority-reconciliation.json"
    writer.write_text(authority_path, _stable_json(authority), new_mode=0o600)
    component = {
        "schema_version": "1.0",
        "record_type": "sage-branch-lifecycle-component-selection",
        "required_capabilities": [
            "read-only Git authority",
            "one-boundary operator proposal",
            "post-operator verification",
        ],
        "selected_components": [
            "git.inspect",
            "operator.git-proposal",
            "file.atomic-preserve-mode",
        ],
        "new_low_level_primitive_required": False,
    }
    component_path = state_dir / "component-selection.json"
    writer.write_text(component_path, _stable_json(component), new_mode=0o600)
    validation = [
        {
            "label": "Frozen origin/main authority",
            "reference": "git.inspect",
            "status": "pass",
            "sha256": _sha256_text(expected_main),
        },
        {
            "label": "Governed branch lifecycle component reuse",
            "reference": "component-selection.json",
            "status": "pass",
            "sha256": hashlib.sha256(component_path.read_bytes()).hexdigest(),
        },
    ]
    return authority_path, component_path, validation


def _write_proposal(
    writer: AtomicFileWriter,
    path: Path,
    *,
    snapshot,
    authority_path: Path,
    component_path: Path,
    validation: list[dict[str, Any]],
    boundary: str,
    branch: str,
    argv: tuple[str, ...],
    expected_result: str,
    risk: str,
    rollback: str,
) -> Mapping[str, Any]:
    proposal = OperatorGitProposal.build(
        proposal_id=_proposal_id(branch, boundary),
        controller=WORKFLOW_ID,
        repository=snapshot,
        authority_receipt=str(authority_path),
        component_manifest=str(component_path),
        boundary=boundary,
        change_scope=(f"refs/heads/{branch}",),
        validation=validation,
        command_argv=argv,
        expected_result=expected_result,
        risk=risk,
        rollback=rollback,
        post_command_verification=(
            "git branch --show-current",
            "git status --porcelain=v1 --untracked-files=all",
            "git rev-parse HEAD",
            "git rev-parse @{upstream}",
        ),
    )
    OperatorGitProposal.write(path, proposal, writer)
    return proposal


def start_branch_bootstrap(
    repo: Path,
    *,
    request: str,
    branch: str,
    expected_main: str,
) -> Mapping[str, Any]:
    """Freeze exact main authority and emit one create-branch operator proposal."""
    repo = repo.expanduser().resolve()
    if not request.strip():
        raise WorkflowError("branch bootstrap requires the literal governed request")
    if not _BRANCH.fullmatch(branch) or branch == "main" or ".." in branch:
        raise WorkflowError("branch bootstrap target branch is invalid")
    if not _SHA40.fullmatch(expected_main):
        raise WorkflowError("branch bootstrap requires an exact 40-character main SHA")

    state_dir = _new_state_dir()
    _, _, writer, inspector = _runtime(repo, state_dir)
    inspector.require_clean()
    inspector.require_upstream_equal()

    local_main = inspector.head("origin/main")
    live_main = inspector.remote_head("origin", "main")
    if local_main != expected_main or live_main != expected_main:
        raise WorkflowError(
            "branch bootstrap frozen main authority drifted: "
            f"expected={expected_main}, local_origin_main={local_main}, live_origin_main={live_main}"
        )
    if _local_branch_exists(inspector, branch):
        raise WorkflowError(f"branch bootstrap target already exists locally: {branch}")
    if _remote_branch_exists(inspector, "origin", branch):
        raise WorkflowError(f"branch bootstrap target already exists remotely: {branch}")

    snapshot = inspector.snapshot()
    authority_path, component_path, validation = _write_common_receipts(
        writer,
        state_dir,
        request=request,
        expected_main=expected_main,
        branch=branch,
        repository=snapshot.as_dict(),
    )
    proposal_path = state_dir / "operator-git-proposal-create-branch.json"
    proposal = _write_proposal(
        writer,
        proposal_path,
        snapshot=snapshot,
        authority_path=authority_path,
        component_path=component_path,
        validation=validation,
        boundary="create-branch",
        branch=branch,
        argv=("git", "switch", "-c", branch, expected_main),
        expected_result="Create and switch to exactly the approved feature branch at the frozen origin/main commit; no repository content changes.",
        risk="Mutates only the local branch reference and active branch; no commit, push, merge, deployment, or GitHub mutation.",
        rollback="Do not execute the proposal; after execution a branch deletion requires a separately governed boundary.",
    )
    state = {
        "schema_version": "1.0",
        "record_type": "sage-branch-lifecycle-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "request": request,
        "target_branch": branch,
        "expected_main": expected_main,
        "phase": "create-branch",
        "status": "operator-review-required",
        "authority_receipt": str(authority_path),
        "component_manifest": str(component_path),
        "current_proposal": str(proposal_path),
        "history": [],
    }
    state_path = state_dir / "branch-lifecycle-state.json"
    writer.write_text(state_path, _stable_json(state), new_mode=0o600)
    return {
        "status": state["status"],
        "state": str(state_path),
        "proposal_path": str(proposal_path),
        "proposal": proposal,
    }


def _load_result(path: Path, proposal: Mapping[str, Any]) -> Mapping[str, Any]:
    result = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise WorkflowError("operator result must be a JSON object")
    if result.get("proposal_id") != proposal.get("proposal_id"):
        raise WorkflowError("operator result proposal_id does not match active proposal")
    command = proposal.get("command")
    if not isinstance(command, dict) or result.get("command_sha256") != command.get("sha256"):
        raise WorkflowError("operator result command digest does not match active proposal")
    if result.get("returncode") != 0 or result.get("pasted_output_received") is not True:
        raise WorkflowError("operator result must record successful execution and complete pasted output")
    return result


def continue_branch_bootstrap(
    repo: Path,
    state_path: Path,
    operator_result: Path,
) -> Mapping[str, Any]:
    """Verify one operator boundary and emit the next or complete the lifecycle."""
    repo = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("record_type") != "sage-branch-lifecycle-state":
        raise WorkflowError("branch lifecycle state type is invalid")
    if state.get("status") != "operator-review-required":
        raise WorkflowError("branch lifecycle is not awaiting an operator result")
    state_dir = state_path.parent
    _, _, writer, inspector = _runtime(repo, state_dir)
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    result = _load_result(operator_result, proposal)

    branch = str(state["target_branch"])
    expected_main = str(state["expected_main"])
    inspector.require_clean()
    inspector.require_branch(branch)
    inspector.require_head(expected_main)
    if inspector.head("origin/main") != expected_main or inspector.remote_head("origin", "main") != expected_main:
        raise WorkflowError("branch lifecycle main authority changed during operator boundary verification")

    phase = str(state["phase"])
    state["history"].append(
        {
            "phase": phase,
            "proposal_id": proposal["proposal_id"],
            "command_sha256": proposal["command"]["sha256"],
            "result_sha256": hashlib.sha256(
                operator_result.expanduser().resolve().read_bytes()
            ).hexdigest(),
        }
    )

    if phase == "create-branch":
        if inspector.upstream_head() is not None:
            raise WorkflowError("new feature branch unexpectedly has an upstream before governed push")
        authority_path = Path(str(state["authority_receipt"]))
        component_path = Path(str(state["component_manifest"]))
        validation = [
            {
                "label": "Create-branch post-operator verification",
                "reference": "git.inspect",
                "status": "pass",
                "sha256": _sha256_text(f"{branch}:{expected_main}"),
            }
        ]
        next_path = state_dir / "operator-git-proposal-push.json"
        next_proposal = _write_proposal(
            writer,
            next_path,
            snapshot=inspector.snapshot(),
            authority_path=authority_path,
            component_path=component_path,
            validation=validation,
            boundary="push",
            branch=branch,
            argv=("git", "push", "-u", "origin", branch),
            expected_result="Publish exactly the approved feature branch at the frozen main commit and establish its upstream.",
            risk="Mutates only the declared remote feature branch; no repository content, merge, deployment, or other GitHub mutation.",
            rollback="Do not execute the proposal; after execution remote branch deletion requires a separately governed boundary.",
        )
        state["phase"] = "push"
        state["current_proposal"] = str(next_path)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {
            "status": state["status"],
            "verified_boundary": "create-branch",
            "state": str(state_path),
            "proposal_path": str(next_path),
            "proposal": next_proposal,
        }

    if phase == "push":
        inspector.require_upstream_equal()
        remote_branch = inspector.remote_head("origin", branch)
        if remote_branch != expected_main:
            raise WorkflowError(
                f"branch lifecycle remote branch mismatch: expected={expected_main}, observed={remote_branch}"
            )
        receipt = {
            "schema_version": "1.0",
            "record_type": "sage-branch-lifecycle-receipt",
            "status": "pass",
            "target_branch": branch,
            "frozen_main": expected_main,
            "head": inspector.head(),
            "upstream_head": inspector.upstream_head(),
            "remote_head": remote_branch,
            "operator_boundaries": list(state["history"]),
            "architect_intervention": {
                "classification": "platform-immaturity-bootstrap",
                "reason": "Existing SAGE could propose branch mutation but lacked a root branch-lifecycle composition; this receipt bootstraps the class-level remediation without fabricating historical governance.",
                "temporary": True,
            },
        }
        receipt_path = state_dir / "branch-lifecycle-receipt.json"
        writer.write_text(receipt_path, _stable_json(receipt), new_mode=0o600)
        state["status"] = "complete"
        state["phase"] = "complete"
        state["current_proposal"] = None
        state["receipt"] = str(receipt_path)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {
            "status": "complete",
            "verified_boundary": "push",
            "state": str(state_path),
            "receipt": str(receipt_path),
            "proposal": None,
        }

    raise WorkflowError(f"unsupported branch lifecycle phase: {phase}")
