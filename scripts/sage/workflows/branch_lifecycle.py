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
WORKFLOW_VERSION = "0.2.0"
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
            "objective_execution_delegation_allowed": True,
            "objective_execution_requires_architect_plan": True,
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
    change_scope: tuple[str, ...] | None = None,
) -> Mapping[str, Any]:
    proposal = OperatorGitProposal.build(
        proposal_id=_proposal_id(branch, boundary),
        controller=WORKFLOW_ID,
        repository=snapshot,
        authority_receipt=str(authority_path),
        component_manifest=str(component_path),
        boundary=boundary,
        change_scope=(change_scope or (f"refs/heads/{branch}",)),
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
        "mode": "bootstrap",
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



def _validate_objective_executor_result(
    result: Mapping[str, Any],
    proposal: Mapping[str, Any],
    state_path: Path | None,
) -> None:
    """Validate objective-level Architect authority for one delegated proposal."""
    if state_path is None:
        raise WorkflowError(
            "objective executor result requires lifecycle state binding"
        )
    plan_path = Path(
        str(result.get("objective_execution_plan", ""))
    ).expanduser().resolve()
    approval_path = Path(
        str(result.get("objective_execution_approval", ""))
    ).expanduser().resolve()
    if not plan_path.is_file() or not approval_path.is_file():
        raise WorkflowError("objective executor authority evidence is missing")
    observed_plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    observed_approval_sha = hashlib.sha256(
        approval_path.read_bytes()
    ).hexdigest()
    if result.get("objective_execution_plan_sha256") != observed_plan_sha:
        raise WorkflowError("objective executor plan digest is invalid")
    if result.get("objective_execution_approval_sha256") != observed_approval_sha:
        raise WorkflowError("objective executor approval digest is invalid")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    lifecycle = json.loads(
        state_path.expanduser().resolve().read_text(encoding="utf-8")
    )
    _validate_objective_bindings(
        plan, approval, lifecycle, plan_path, state_path
    )
    authority_path = Path(
        str(proposal["authority_receipt"])
    ).expanduser().resolve()
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    gate = authority.get("mutation_gate", {})
    if gate.get("objective_execution_delegation_allowed") is not True:
        raise WorkflowError(
            "branch authority does not allow objective execution delegation"
        )
    if gate.get("objective_execution_requires_architect_plan") is not True:
        raise WorkflowError(
            "branch authority does not require objective plan approval"
        )


def _validate_objective_bindings(
    plan: Mapping[str, Any],
    approval: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    plan_path: Path,
    state_path: Path,
) -> None:
    """Validate objective, adapter, lifecycle, and Architect approval binding."""
    if plan.get("record_type") != "sage-objective-execution-plan":
        raise WorkflowError("objective executor plan type is invalid")
    lifecycle_target = Path(
        str(plan.get("lifecycle_state", ""))
    ).expanduser().resolve()
    if lifecycle_target != state_path.expanduser().resolve():
        raise WorkflowError(
            "objective executor plan targets a different lifecycle state"
        )
    if plan.get("objective_id") != lifecycle.get("objective_id"):
        raise WorkflowError(
            "objective executor plan targets a different objective"
        )
    adapter = plan.get("delegated_adapter", {})
    current = hashlib.sha256(Path(__file__).resolve().read_bytes()).hexdigest()
    if adapter.get("workflow_id") != WORKFLOW_ID:
        raise WorkflowError("objective executor plan adapter is invalid")
    if adapter.get("sha256") != current:
        raise WorkflowError("objective executor plan adapter digest is stale")
    if approval.get("record_type") != "sage-objective-execution-approval":
        raise WorkflowError("objective executor approval type is invalid")
    if approval.get("authority") != "Architect":
        raise WorkflowError("objective executor lacks Architect authority")
    if approval.get("status") != "approved":
        raise WorkflowError("objective executor approval is not active")
    if approval.get("atomicity") != "material-objective-path":
        raise WorkflowError("objective executor approval atomicity is invalid")
    approved_plan = Path(
        str(approval.get("plan", ""))
    ).expanduser().resolve()
    if approved_plan != plan_path:
        raise WorkflowError("objective executor approval targets another plan")
    observed_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    if approval.get("plan_sha256") != observed_sha:
        raise WorkflowError(
            "objective executor approval does not bind the exact plan"
        )


def _load_result(
    path: Path,
    proposal: Mapping[str, Any],
    state_path: Path | None = None,
) -> Mapping[str, Any]:
    """Load operator or objective-executor evidence for one exact proposal."""
    result = json.loads(
        path.expanduser().resolve().read_text(encoding="utf-8")
    )
    if not isinstance(result, dict):
        raise WorkflowError("execution result must be a JSON object")
    if result.get("proposal_id") != proposal.get("proposal_id"):
        raise WorkflowError(
            "execution result proposal_id does not match active proposal"
        )
    command = proposal.get("command")
    if not isinstance(command, dict):
        raise WorkflowError("active proposal command is invalid")
    if result.get("command_sha256") != command.get("sha256"):
        raise WorkflowError(
            "execution result command digest does not match active proposal"
        )
    if result.get("returncode") != 0:
        raise WorkflowError(
            "execution result did not record successful execution"
        )
    if result.get("pasted_output_received") is True:
        return result
    if result.get("execution_mode") == "objective-executor":
        if result.get("complete_output_captured") is not True:
            raise WorkflowError(
                "objective executor did not preserve complete output evidence"
            )
        _validate_objective_executor_result(
            result,
            proposal,
            state_path,
        )
        return result
    raise WorkflowError(
        "execution result lacks operator paste or objective authority"
    )

def _write_repository_lineage_milestone(
    writer: AtomicFileWriter,
    path: Path,
    *,
    objective_id: str,
    milestone_type: str,
    source_branch: str,
    source_head: str,
    authoritative_main: str,
    local_main: str,
    source_local_exists: bool,
    source_remote_exists: bool,
    assertions: list[dict[str, Any]],
    evidence_references: list[str],
) -> Path:
    value = {
        "schema_version": "1.0",
        "record_type": "sage-repository-lineage-milestone",
        "objective_id": objective_id,
        "milestone_type": milestone_type,
        "delegation": {
            "capability_class": "source-control",
            "implementation": "git",
            "adapter": WORKFLOW_ID,
            "adapter_version": WORKFLOW_VERSION,
            "chronology_ownership": "delegated-high-resolution-mechanics",
            "sage_ownership": "semantic-milestones-authority-and-reconstruction-evidence",
        },
        "authority": {
            "source_branch": source_branch,
            "source_head": source_head,
            "authoritative_main": authoritative_main,
            "local_main": local_main,
            "source_local_exists": source_local_exists,
            "source_remote_exists": source_remote_exists,
        },
        "assertions": assertions,
        "evidence_references": evidence_references,
        "historical_mechanics": "Consult delegated Git history for per-commit chronology; this milestone preserves the semantic anchors needed to interpret it.",
    }
    writer.write_text(path, _stable_json(value), new_mode=0o600)
    return path


def start_branch_closeout(
    repo: Path,
    *,
    request: str,
    objective_id: str,
    source_branch: str,
    promoted_source: str,
    expected_main: str,
) -> Mapping[str, Any]:
    """Prove promotion containment and emit the first post-promotion closeout proposal."""
    repo = repo.expanduser().resolve()
    if not request.strip() or not objective_id.strip():
        raise WorkflowError("post-promotion closeout requires request and objective identity")
    if not _BRANCH.fullmatch(source_branch) or source_branch == "main" or ".." in source_branch:
        raise WorkflowError("post-promotion closeout source branch is invalid")
    if not _SHA40.fullmatch(promoted_source) or not _SHA40.fullmatch(expected_main):
        raise WorkflowError("post-promotion closeout requires exact source and main SHAs")

    state_dir = _new_state_dir()
    _, _, writer, inspector = _runtime(repo, state_dir)
    inspector.require_clean()
    inspector.require_branch(source_branch)
    inspector.require_head(promoted_source)
    inspector.require_upstream_equal()
    if inspector.upstream_head() != promoted_source:
        raise WorkflowError("source upstream changed before post-promotion closeout")
    if inspector.head("origin/main") != expected_main or inspector.remote_head("origin", "main") != expected_main:
        raise WorkflowError("authoritative main is not stable before post-promotion closeout")
    if inspector.remote_head("origin", source_branch) != promoted_source:
        raise WorkflowError("remote source tip changed after promotion")
    if not inspector.is_ancestor(promoted_source, expected_main):
        raise WorkflowError("promoted source is not contained in authoritative main")
    if not _local_branch_exists(inspector, "main"):
        raise WorkflowError("local main branch is missing")
    local_main = inspector.head("main")
    if not inspector.is_ancestor(local_main, expected_main):
        raise WorkflowError(
            "local main cannot fast-forward to authoritative main without rewriting history"
        )

    snapshot = inspector.snapshot()
    authority_path, component_path, validation = _write_common_receipts(
        writer,
        state_dir,
        request=request,
        expected_main=expected_main,
        branch=source_branch,
        repository=snapshot.as_dict(),
    )
    validation.extend([
        {
            "label": "Promoted source contained in authoritative main",
            "reference": "git.inspect merge-base --is-ancestor",
            "status": "pass",
            "sha256": _sha256_text(f"{promoted_source}:{expected_main}"),
        },
        {
            "label": "Source and main remote tips stable",
            "reference": "git.inspect ls-remote",
            "status": "pass",
            "sha256": _sha256_text(f"{source_branch}:{promoted_source}:{expected_main}"),
        },
    ])
    pre = _write_repository_lineage_milestone(
        writer,
        state_dir / "repository-lineage-pre-closeout.json",
        objective_id=objective_id,
        milestone_type="post-promotion-closeout-ready",
        source_branch=source_branch,
        source_head=promoted_source,
        authoritative_main=expected_main,
        local_main=local_main,
        source_local_exists=True,
        source_remote_exists=True,
        assertions=[
            {"kind": "source-contained-in-target", "verified": True, "source": promoted_source, "target": expected_main},
            {"kind": "local-main-fast-forwardable", "verified": True, "source": local_main, "target": expected_main},
        ],
        evidence_references=[str(authority_path), str(component_path)],
    )
    proposal_path = state_dir / "operator-git-proposal-switch-main.json"
    proposal = _write_proposal(
        writer,
        proposal_path,
        snapshot=snapshot,
        authority_path=authority_path,
        component_path=component_path,
        validation=validation,
        boundary="switch-branch",
        branch=source_branch,
        argv=("git", "switch", "main"),
        expected_result="Switch off the promoted source branch so local main can be reconciled and the source retired safely.",
        risk="Mutates only the active local branch selection; no commit, remote, deployment, or history rewrite.",
        rollback="Do not execute the proposal; remaining closeout steps stay blocked.",
        change_scope=("refs/heads/main", f"refs/heads/{source_branch}"),
    )
    state = {
        "schema_version": "1.0",
        "record_type": "sage-branch-lifecycle-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "mode": "post-promotion-closeout",
        "request": request,
        "objective_id": objective_id,
        "target_branch": source_branch,
        "promoted_source": promoted_source,
        "expected_main": expected_main,
        "local_main_before": local_main,
        "phase": "switch-main",
        "status": "operator-review-required",
        "authority_receipt": str(authority_path),
        "component_manifest": str(component_path),
        "repository_lineage_pre": str(pre),
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


def continue_branch_closeout(
    repo: Path,
    state_path: Path,
    operator_result: Path,
) -> Mapping[str, Any]:
    """Verify one post-promotion closeout boundary and emit the next."""
    repo = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("record_type") != "sage-branch-lifecycle-state" or state.get("mode") != "post-promotion-closeout":
        raise WorkflowError("branch closeout state type or mode is invalid")
    if state.get("status") != "operator-review-required":
        raise WorkflowError("branch closeout is not awaiting an operator result")
    state_dir = state_path.parent
    _, _, writer, inspector = _runtime(repo, state_dir)
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    _load_result(operator_result, proposal, state_path)

    source_branch = str(state["target_branch"])
    promoted_source = str(state["promoted_source"])
    expected_main = str(state["expected_main"])
    phase = str(state["phase"])
    inspector.require_clean()
    if inspector.head("origin/main") != expected_main or inspector.remote_head("origin", "main") != expected_main:
        raise WorkflowError("authoritative main changed during post-promotion closeout")
    if not inspector.is_ancestor(promoted_source, expected_main):
        raise WorkflowError("source containment changed during post-promotion closeout")

    state["history"].append({
        "phase": phase,
        "proposal_id": proposal["proposal_id"],
        "command_sha256": proposal["command"]["sha256"],
        "result_sha256": hashlib.sha256(operator_result.expanduser().resolve().read_bytes()).hexdigest(),
    })
    authority_path = Path(str(state["authority_receipt"]))
    component_path = Path(str(state["component_manifest"]))

    if phase == "switch-main":
        inspector.require_branch("main")
        local_main = inspector.head()
        if local_main != str(state["local_main_before"]):
            raise WorkflowError("local main changed while switching branches")
        if inspector.remote_head("origin", source_branch) != promoted_source:
            raise WorkflowError("remote source changed before local-main reconciliation")
        if local_main == expected_main:
            next_phase = "delete-remote"
            boundary = "push"
            argv = ("git", "push", "origin", "--delete", source_branch)
            expected_result = "Delete exactly the stable promoted remote source branch after proving it is contained in authoritative main."
            change_scope = (f"refs/heads/{source_branch}",)
        else:
            next_phase = "fast-forward-main"
            boundary = "other-git-mutation"
            argv = ("git", "merge", "--ff-only", expected_main)
            expected_result = "Fast-forward local main to the exact authoritative main commit without creating or rewriting history."
            change_scope = ("refs/heads/main",)
        next_path = state_dir / f"operator-git-proposal-{next_phase}.json"
        next_proposal = _write_proposal(
            writer, next_path,
            snapshot=inspector.snapshot(), authority_path=authority_path,
            component_path=component_path,
            validation=[{"label":"Post-switch authority verification","reference":"git.inspect","status":"pass","sha256":_sha256_text(f"{local_main}:{expected_main}:{promoted_source}")}],
            boundary=boundary, branch=source_branch, argv=argv,
            expected_result=expected_result,
            risk="Bounded repository-reference mutation only; force, reset, rebase, and history rewriting are prohibited.",
            rollback="Stop before the next boundary; Git history remains intact and the source is still contained in authoritative main.",
            change_scope=change_scope,
        )
        state["phase"] = next_phase
        state["current_proposal"] = str(next_path)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {"status": state["status"], "verified_boundary":"switch-main", "state":str(state_path), "proposal_path":str(next_path), "proposal":next_proposal}

    if phase == "fast-forward-main":
        inspector.require_branch("main")
        inspector.require_head(expected_main)
        if inspector.remote_head("origin", source_branch) != promoted_source:
            raise WorkflowError("remote source changed before retirement")
        next_path = state_dir / "operator-git-proposal-delete-remote.json"
        next_proposal = _write_proposal(
            writer, next_path,
            snapshot=inspector.snapshot(), authority_path=authority_path,
            component_path=component_path,
            validation=[{"label":"Local main reconciled exactly","reference":"git.inspect","status":"pass","sha256":_sha256_text(expected_main)}],
            boundary="push", branch=source_branch,
            argv=("git", "push", "origin", "--delete", source_branch),
            expected_result="Delete exactly the stable promoted remote source branch after main reconciliation.",
            risk="Deletes only the declared remote source ref; promoted content remains reachable from authoritative main.",
            rollback="Stop before local source deletion; authoritative main already contains the promoted source.",
            change_scope=(f"refs/heads/{source_branch}",),
        )
        state["phase"] = "delete-remote"
        state["current_proposal"] = str(next_path)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {"status":state["status"],"verified_boundary":"fast-forward-main","state":str(state_path),"proposal_path":str(next_path),"proposal":next_proposal}

    if phase == "delete-remote":
        inspector.require_branch("main")
        inspector.require_head(expected_main)
        if _remote_branch_exists(inspector, "origin", source_branch):
            raise WorkflowError("remote promoted source still exists after governed deletion")
        if not _local_branch_exists(inspector, source_branch):
            raise WorkflowError("local source disappeared before its separately governed deletion boundary")
        if inspector.head(source_branch) != promoted_source:
            raise WorkflowError("local source changed before deletion")
        next_path = state_dir / "operator-git-proposal-delete-local.json"
        next_proposal = _write_proposal(
            writer, next_path,
            snapshot=inspector.snapshot(), authority_path=authority_path,
            component_path=component_path,
            validation=[{"label":"Remote source retirement verified","reference":"git.inspect ls-remote","status":"pass","sha256":_sha256_text(f"absent:{source_branch}:{promoted_source}")}],
            boundary="branch-delete", branch=source_branch,
            argv=("git", "branch", "-d", source_branch),
            expected_result="Delete the exact local promoted source branch only after its remote ref is absent and its content remains contained in main.",
            risk="Deletes only the declared local branch ref; promoted content remains reachable from main.",
            rollback="Stop before execution; the local source ref remains available.",
            change_scope=(f"refs/heads/{source_branch}",),
        )
        state["phase"] = "delete-local"
        state["current_proposal"] = str(next_path)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {"status":state["status"],"verified_boundary":"delete-remote","state":str(state_path),"proposal_path":str(next_path),"proposal":next_proposal}

    if phase == "delete-local":
        inspector.require_branch("main")
        inspector.require_head(expected_main)
        inspector.require_upstream_equal()
        if _remote_branch_exists(inspector, "origin", source_branch):
            raise WorkflowError("remote source reappeared during closeout")
        if _local_branch_exists(inspector, source_branch):
            raise WorkflowError("local source still exists after governed deletion")
        post = _write_repository_lineage_milestone(
            writer,
            state_dir / "repository-lineage-closeout.json",
            objective_id=str(state["objective_id"]),
            milestone_type="post-promotion-source-retired",
            source_branch=source_branch,
            source_head=promoted_source,
            authoritative_main=expected_main,
            local_main=expected_main,
            source_local_exists=False,
            source_remote_exists=False,
            assertions=[
                {"kind":"source-contained-in-target","verified":True,"source":promoted_source,"target":expected_main},
                {"kind":"local-main-reconciled","verified":True,"target":expected_main},
                {"kind":"remote-source-retired","verified":True,"branch":source_branch},
                {"kind":"local-source-retired","verified":True,"branch":source_branch},
            ],
            evidence_references=[str(state["repository_lineage_pre"]), str(state["authority_receipt"]), str(state["component_manifest"])],
        )
        receipt = {
            "schema_version":"1.0",
            "record_type":"sage-branch-lifecycle-receipt",
            "status":"pass",
            "mode":"post-promotion-closeout",
            "objective_id":state["objective_id"],
            "source_branch":source_branch,
            "promoted_source":promoted_source,
            "authoritative_main":expected_main,
            "active_branch":"main",
            "head":inspector.head(),
            "upstream_head":inspector.upstream_head(),
            "source_local_exists":False,
            "source_remote_exists":False,
            "repository_lineage_pre":state["repository_lineage_pre"],
            "repository_lineage_post":str(post),
            "repository_lineage_post_sha256":hashlib.sha256(post.read_bytes()).hexdigest(),
            "operator_boundaries":list(state["history"]),
        }
        receipt_path = state_dir / "branch-lifecycle-receipt.json"
        writer.write_text(receipt_path, _stable_json(receipt), new_mode=0o600)
        state["status"]="complete"; state["phase"]="complete"; state["current_proposal"]=None; state["receipt"]=str(receipt_path); state["repository_lineage_post"]=str(post)
        writer.write_text(state_path, _stable_json(state), new_mode=0o600)
        return {"status":"complete","verified_boundary":"delete-local","state":str(state_path),"receipt":str(receipt_path),"repository_lineage":str(post),"proposal":None}

    raise WorkflowError(f"unsupported branch closeout phase: {phase}")


def continue_branch_lifecycle(
    repo: Path,
    state_path: Path,
    operator_result: Path,
) -> Mapping[str, Any]:
    """Dispatch continuation by persisted branch-lifecycle mode."""
    value = json.loads(state_path.expanduser().resolve().read_text(encoding="utf-8"))
    mode = value.get("mode", "bootstrap")
    if mode == "post-promotion-closeout":
        return continue_branch_closeout(repo, state_path, operator_result)
    if mode == "bootstrap":
        return continue_branch_bootstrap(repo, state_path, operator_result)
    raise WorkflowError(f"unsupported branch lifecycle mode: {mode}")


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
    result = _load_result(operator_result, proposal, state_path)

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
