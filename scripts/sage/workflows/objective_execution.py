
"""Objective-sized execution and path-critique support for SAGE."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from workflow import (
    AtomicFileWriter,
    CommandRunner,
    CommandSpec,
    JsonlEventLogger,
    PrimitiveCatalog,
    WorkflowError,
)
from workflows.branch_lifecycle import continue_branch_lifecycle

WORKFLOW_ID = "sage.objective-execution"
WORKFLOW_VERSION = "0.1.0"
STATE_ROOT = Path("~/.local/state/kalaxy3/sage-objective-execution").expanduser()
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "file.atomic-preserve-mode",
)
MATERIAL_FIELDS = (
    "objective_meaning_changed",
    "authority_changed",
    "scope_expanded",
    "constraints_changed",
    "risk_envelope_changed",
    "intended_outcome_changed",
)
CRITIC_DIMENSIONS = (
    "objective-equivalent-efficiency",
    "operator-boundaries",
    "component-reuse",
    "mutation-evidence-cost",
    "recovery-burden",
    "architecture-technology-fitness",
)
RECOMMENDATIONS = (
    "retain",
    "blue-green-migration",
    "parallel-canary-adoption",
    "selective-adoption",
    "replacement",
    "deferral",
)
SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


def _stable_json(value: Mapping[str, Any]) -> str:
    """Serialize one mapping for persisted objective evidence."""
    return json.dumps(dict(value), indent=4, sort_keys=False) + "\n"


def _load_json(path: Path, label: str) -> dict[str, Any]:
    """Load one JSON object or fail closed."""
    resolved = path.expanduser().resolve()
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"{label} is unreadable: {resolved}: {error}") from error
    if not isinstance(value, dict):
        raise WorkflowError(f"{label} must be a JSON object")
    return value


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    return hashlib.sha256(path.expanduser().resolve().read_bytes()).hexdigest()


def _new_state_dir() -> Path:
    """Create one objective-execution evidence directory."""
    path = STATE_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path.mkdir(parents=True, exist_ok=False)
    return path


def _runtime(repo: Path, state_dir: Path) -> tuple[AtomicFileWriter, CommandRunner]:
    """Build governed persistence and command primitives."""
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
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    return AtomicFileWriter((state_dir, STATE_ROOT)), runner


def classify_change(observation: Mapping[str, Any]) -> str:
    """Classify an execution deviation as correction or true replan."""
    if any(observation.get(name) is True for name in MATERIAL_FIELDS):
        return "true-replan"
    return "implementation-local-correction"


def _material_triggers() -> list[str]:
    """Return explicit Architect-intervention triggers."""
    return [
        "objective meaning changes",
        "governing authority changes or becomes unverifiable",
        "scope expands outside the approved envelope",
        "constraints or nondelegable safety/trust boundaries change",
        "material risk exceeds the approved risk envelope",
        "intended outcome changes",
        "delegated adapter digest changes after objective approval",
    ]


def _planned_work() -> list[dict[str, Any]]:
    """Return the bounded conditional branch-closeout path."""
    return [
        {
            "step_id": "switch-main",
            "condition": "always",
            "dependencies": ["promoted source contained in authoritative main"],
            "expected_evidence": ["post-switch repository verification"],
            "recovery": "resume from persisted result without replay",
        },
        {
            "step_id": "fast-forward-main",
            "condition": "when local main differs from authoritative main",
            "dependencies": ["switch-main"],
            "expected_evidence": ["exact fast-forward verification"],
            "recovery": "stop without history rewrite on authority divergence",
        },
        {
            "step_id": "delete-remote",
            "condition": "after main reconciliation",
            "dependencies": ["switch-main"],
            "expected_evidence": ["remote source absence"],
            "recovery": "retain local source until remote retirement is verified",
        },
        {
            "step_id": "delete-local",
            "condition": "after remote retirement",
            "dependencies": ["delete-remote"],
            "expected_evidence": ["repository-lineage closeout milestone"],
            "recovery": "fail closed if local source identity changed",
        },
    ]


def _validate_lifecycle(state: Mapping[str, Any]) -> None:
    """Validate the narrow post-promotion closeout surface."""
    if state.get("record_type") != "sage-branch-lifecycle-state":
        raise WorkflowError("objective execution requires branch-lifecycle state")
    if state.get("mode") != "post-promotion-closeout":
        raise WorkflowError("objective execution slice supports closeout only")
    if state.get("status") not in {"operator-review-required", "complete"}:
        raise WorkflowError("branch closeout is not at a deterministic boundary")


def _build_plan(
    lifecycle: Path,
    state: Mapping[str, Any],
    adapter_sha256: str,
    baseline_round_trips: int,
) -> dict[str, Any]:
    """Build the immutable objective decision surface before mutation."""
    return {
        "schema_version": "1.0",
        "record_type": "sage-objective-execution-plan",
        "objective_id": state.get("objective_id"),
        "approval": {
            "authority": "Architect",
            "status": "required",
            "atomicity": "material-objective-path",
        },
        "delegated_adapter": {
            "workflow_id": "sage.branch-lifecycle",
            "sha256": adapter_sha256,
        },
        "lifecycle_state": str(lifecycle),
        "approved_path": _planned_work(),
        "components": ["sage.intent-to-outcome", "sage.branch-lifecycle"],
        "material_intervention_triggers": _material_triggers(),
        "correction_policy": "automatic-inside-approved-envelope",
        "replan_policy": "interrupt-on-material-decision-surface-change",
        "baseline_round_trips": baseline_round_trips,
        "routine_followup_target": 0,
        "path_critic": {
            "producer_class": "llm-path-critic",
            "dimensions": list(CRITIC_DIMENSIONS),
            "dynamic_invocation": False,
            "autonomous_migration": False,
        },
    }


def create_closeout_plan(
    repo: Path,
    lifecycle_state: Path,
    baseline_round_trips: int = 6,
) -> Mapping[str, Any]:
    """Persist one cohesive closeout plan before any objective mutation."""
    resolved = repo.expanduser().resolve()
    lifecycle = lifecycle_state.expanduser().resolve()
    state = _load_json(lifecycle, "branch lifecycle state")
    _validate_lifecycle(state)
    state_dir = _new_state_dir()
    writer, _ = _runtime(resolved, state_dir)
    adapter = resolved / "scripts/sage/workflows/branch_lifecycle.py"
    plan = _build_plan(
        lifecycle,
        state,
        _sha256(adapter),
        baseline_round_trips,
    )
    plan_path = state_dir / "objective-execution-plan.json"
    writer.write_text(plan_path, _stable_json(plan), new_mode=0o600)
    return {
        "status": "objective-plan-ready",
        "plan": str(plan_path),
        "plan_sha256": _sha256(plan_path),
        "next_boundary": "architect-objective-path-approval",
    }


def objective_execution_route_summary(state: Mapping[str, Any]) -> dict[str, Any]:
    """Expose objective-execution semantics on the existing objective route."""
    return {
        "approval_atomicity": "material-objective-path",
        "routine_step_approval_atomicity": False,
        "correction_semantics": "implementation-local-within-approved-envelope",
        "replan_semantics": "material-decision-surface-change",
        "plan": state.get("objective_execution_plan"),
        "episode": state.get("objective_execution_episode"),
    }


def _validate_adapter(repo: Path, plan: Mapping[str, Any]) -> None:
    """Fail closed if delegated Git semantics changed after plan creation."""
    adapter = repo / "scripts/sage/workflows/branch_lifecycle.py"
    expected = plan.get("delegated_adapter", {}).get("sha256")
    if expected != _sha256(adapter):
        raise WorkflowError("branch-lifecycle adapter changed after plan creation")


def _write_approval(
    writer: AtomicFileWriter,
    plan_path: Path,
    approved_sha256: str,
) -> Path:
    """Persist the explicit Architect approval consumed by execution."""
    observed = _sha256(plan_path)
    if approved_sha256 != observed:
        raise WorkflowError("Architect-approved plan digest does not match exact plan")
    approval = {
        "schema_version": "1.0",
        "record_type": "sage-objective-execution-approval",
        "authority": "Architect",
        "status": "approved",
        "atomicity": "material-objective-path",
        "plan": str(plan_path),
        "plan_sha256": observed,
        "approved_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path = plan_path.parent / "objective-execution-approval.json"
    writer.write_text(path, _stable_json(approval), new_mode=0o600)
    return path


def _validate_proposal(state: Mapping[str, Any], proposal: Mapping[str, Any]) -> None:
    """Validate one generated Git step against the approved closeout envelope."""
    phases = {"switch-main", "fast-forward-main", "delete-remote", "delete-local"}
    boundaries = {"switch-branch", "other-git-mutation", "push", "branch-delete"}
    if state.get("phase") not in phases:
        raise WorkflowError("branch phase is outside the approved objective path")
    if proposal.get("controller") != "sage.branch-lifecycle":
        raise WorkflowError("proposal controller is not the delegated adapter")
    if proposal.get("boundary") not in boundaries:
        raise WorkflowError("proposal boundary exceeds the approved objective path")
    command = proposal.get("command")
    if not isinstance(command, Mapping) or command.get("command_count") != 1:
        raise WorkflowError("objective executor requires one deterministic command")
    if command.get("contains_secret") is not False:
        raise WorkflowError("objective executor rejects secret-bearing proposals")
    _validate_scope(state, proposal)


def _validate_scope(state: Mapping[str, Any], proposal: Mapping[str, Any]) -> None:
    """Restrict mutation to main and the exact promoted source branch."""
    source = str(state.get("target_branch", ""))
    allowed = {"refs/heads/main", f"refs/heads/{source}"}
    scope = proposal.get("change_scope")
    if not isinstance(scope, list) or not scope:
        raise WorkflowError("proposal has no bounded change scope")
    if not set(map(str, scope)).issubset(allowed):
        raise WorkflowError("proposal change scope exceeds objective authority")


def _execution_state(plan: Path, digest: str, approval: Path) -> dict[str, Any]:
    """Create resumable actual-path evidence before command execution."""
    return {
        "schema_version": "1.0",
        "record_type": "sage-objective-execution-state",
        "plan": str(plan),
        "plan_sha256": digest,
        "approval": str(approval),
        "approval_sha256": _sha256(approval),
        "status": "executing",
        "actual_path": [],
        "local_corrections": [],
        "true_replans": [],
        "architect_interventions": [],
    }


def _load_execution(
    writer: AtomicFileWriter,
    plan: Path,
    approval: Path,
) -> tuple[Path, dict[str, Any]]:
    """Load or initialize crash-resumable objective execution state."""
    path = plan.parent / "objective-execution-state.json"
    digest = _sha256(plan)
    if path.is_file():
        value = _load_json(path, "objective execution state")
        if value.get("plan_sha256") != digest:
            raise WorkflowError("execution state belongs to a different plan")
        return path, value
    value = _execution_state(plan, digest, approval)
    writer.write_text(path, _stable_json(value), new_mode=0o600)
    return path, value


def _captured_output(result: Any) -> str:
    """Return all command output available from the command runner."""
    return (
        str(getattr(result, "stdout", "") or "")
        + str(getattr(result, "stderr", "") or "")
    )


def _execute_step(
    repo: Path,
    writer: AtomicFileWriter,
    runner: CommandRunner,
    proposal: Mapping[str, Any],
    execution: Mapping[str, Any],
    result_path: Path,
) -> None:
    """Execute exactly one delegated proposal and persist complete output."""
    command = proposal["command"]
    result = runner.run(
        CommandSpec(
            "command.run",
            f"Objective execution: {proposal.get('boundary')}",
            tuple(str(item) for item in command["argv"]),
            repo,
        )
    )
    evidence = {
        "schema_version": "1.0",
        "proposal_id": proposal["proposal_id"],
        "command_sha256": command["sha256"],
        "returncode": int(result.returncode),
        "execution_mode": "objective-executor",
        "complete_output_captured": True,
        "complete_output": _captured_output(result),
        "objective_execution_plan": execution["plan"],
        "objective_execution_plan_sha256": execution["plan_sha256"],
        "objective_execution_approval": execution["approval"],
        "objective_execution_approval_sha256": execution["approval_sha256"],
    }
    writer.write_text(result_path, _stable_json(evidence), new_mode=0o600)


def _pending_result(
    execution: Mapping[str, Any],
    proposal_id: str,
) -> Path | None:
    """Return an executed-but-unverified result after interruption."""
    for item in reversed(execution.get("actual_path", [])):
        if item.get("proposal_id") != proposal_id:
            continue
        if item.get("status") == "command-executed":
            return Path(str(item["result"])).expanduser().resolve()
    return None


def _append_step(
    execution: dict[str, Any],
    lifecycle: Mapping[str, Any],
    proposal: Mapping[str, Any],
    result_path: Path,
) -> None:
    """Append one delegated command to the actual objective path."""
    execution["actual_path"].append({
        "phase": lifecycle.get("phase"),
        "boundary": proposal.get("boundary"),
        "proposal_id": proposal.get("proposal_id"),
        "command_sha256": proposal.get("command", {}).get("sha256"),
        "result": str(result_path),
        "status": "command-executed",
    })


def _mark_verified(execution: dict[str, Any], proposal_id: str) -> None:
    """Mark one delegated step as post-command verified."""
    for item in reversed(execution["actual_path"]):
        if item.get("proposal_id") == proposal_id:
            item["status"] = "verified"
            return
    raise WorkflowError("verified proposal is missing from actual path")


def _ensure_result(
    repo: Path,
    writer: AtomicFileWriter,
    runner: CommandRunner,
    lifecycle: Mapping[str, Any],
    proposal: Mapping[str, Any],
    execution: dict[str, Any],
) -> Path:
    """Reuse crash evidence or execute the next deterministic proposal."""
    proposal_id = str(proposal["proposal_id"])
    existing = _pending_result(execution, proposal_id)
    if existing is not None:
        return existing
    state_dir = Path(str(execution["plan"])).expanduser().resolve().parent
    result_path = state_dir / f"result-{proposal_id}.json"
    _execute_step(repo, writer, runner, proposal, execution, result_path)
    _append_step(execution, lifecycle, proposal, result_path)
    return result_path


def _episode(
    plan: Mapping[str, Any],
    execution: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one comparable objective episode after successful closeout."""
    baseline = int(plan.get("baseline_round_trips", 0) or 0)
    steps = len(execution.get("actual_path", []))
    return {
        "schema_version": "1.0",
        "record_type": "sage-objective-episode",
        "objective_id": plan.get("objective_id"),
        "planned_path": plan.get("approved_path"),
        "counterfactual_path": {
            "kind": "legacy-step-wise-operator-boundaries",
            "observed_round_trips": baseline,
        },
        "actual_path": execution.get("actual_path", []),
        "local_corrections": execution.get("local_corrections", []),
        "true_replans": execution.get("true_replans", []),
        "architect_interventions": execution.get("architect_interventions", []),
        "component_use": plan.get("components"),
        "evidence_cost": {"internal_verified_steps": steps},
        "outcome": "complete",
        "path_efficiency_metrics": {
            "baseline_round_trips": baseline,
            "actual_objective_approvals": 1,
            "routine_followup_interventions": 0,
            "avoided_round_trips": max(0, baseline - 1),
        },
        "repository_lineage": lifecycle.get("repository_lineage_post"),
        "improvement_observations": [],
    }


def _critic_request(
    plan: Mapping[str, Any],
    episode_path: Path,
    episode: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the LLM path-critic request without dynamic model invocation."""
    return {
        "schema_version": "1.0",
        "record_type": "sage-llm-path-critic-request",
        "objective_id": plan.get("objective_id"),
        "episode": str(episode_path),
        "episode_sha256": _sha256(episode_path),
        "evaluation_dimensions": list(CRITIC_DIMENSIONS),
        "allowed_recommendations": list(RECOMMENDATIONS),
        "autonomous_migration_allowed": False,
        "episode_metrics": episode.get("path_efficiency_metrics"),
    }


def _finalize(
    writer: AtomicFileWriter,
    state_dir: Path,
    plan: Mapping[str, Any],
    execution: dict[str, Any],
    lifecycle: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Persist the episode and path-critic request."""
    episode = _episode(plan, execution, lifecycle)
    episode_path = state_dir / "objective-episode.json"
    writer.write_text(episode_path, _stable_json(episode), new_mode=0o600)
    critic = _critic_request(plan, episode_path, episode)
    critic_path = state_dir / "path-critic-request.json"
    writer.write_text(critic_path, _stable_json(critic), new_mode=0o600)
    execution["status"] = "complete"
    execution["objective_episode"] = str(episode_path)
    execution["path_critic_request"] = str(critic_path)
    return {
        "status": "complete",
        "objective_episode": str(episode_path),
        "path_critic_request": str(critic_path),
    }


def run_closeout_objective(
    repo: Path,
    plan_path: Path,
    approved_plan_sha256: str,
) -> Mapping[str, Any]:
    """Execute the deterministic closeout suffix under one objective approval."""
    resolved = repo.expanduser().resolve()
    plan_file = plan_path.expanduser().resolve()
    plan = _load_json(plan_file, "objective execution plan")
    if plan.get("record_type") != "sage-objective-execution-plan":
        raise WorkflowError("objective execution plan type is invalid")
    _validate_adapter(resolved, plan)
    writer, runner = _runtime(resolved, plan_file.parent)
    approval = _write_approval(writer, plan_file, approved_plan_sha256)
    execution_path, execution = _load_execution(writer, plan_file, approval)
    return _run_loop(
        resolved, plan, writer, runner, execution_path, execution
    )


def _run_loop(
    repo: Path,
    plan: Mapping[str, Any],
    writer: AtomicFileWriter,
    runner: CommandRunner,
    execution_path: Path,
    execution: dict[str, Any],
) -> Mapping[str, Any]:
    """Run a bounded maximum of four closeout mutations plus finalization."""
    lifecycle_path = Path(str(plan["lifecycle_state"])).expanduser().resolve()
    for _ in range(5):
        lifecycle = _load_json(lifecycle_path, "branch lifecycle state")
        _validate_lifecycle(lifecycle)
        if lifecycle.get("status") == "complete":
            result = _finalize(
                writer, execution_path.parent, plan, execution, lifecycle
            )
            writer.write_text(execution_path, _stable_json(execution), new_mode=0o600)
            return result
        proposal = _load_json(
            Path(str(lifecycle["current_proposal"])),
            "branch lifecycle proposal",
        )
        _validate_proposal(lifecycle, proposal)
        try:
            result_path = _ensure_result(
                repo, writer, runner, lifecycle, proposal, execution
            )
            writer.write_text(
                execution_path,
                _stable_json(execution),
                new_mode=0o600,
            )
            continue_branch_lifecycle(repo, lifecycle_path, result_path)
            _mark_verified(execution, str(proposal["proposal_id"]))
            writer.write_text(
                execution_path,
                _stable_json(execution),
                new_mode=0o600,
            )
        except Exception as error:
            if _recover_local_failure(
                repo,
                plan,
                writer,
                runner,
                execution_path,
                execution,
                error,
            ):
                continue
            raise
    raise WorkflowError("objective closeout exceeded bounded deterministic steps")


def validate_critic_observation(
    request: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> None:
    """Validate one advisory LLM causal observation."""
    if observation.get("record_type") != "sage-path-critic-causal-observation":
        raise WorkflowError("path critic observation type is invalid")
    if observation.get("producer_class") != "llm-path-critic":
        raise WorkflowError("path critic producer class is invalid")
    if observation.get("objective_id") != request.get("objective_id"):
        raise WorkflowError("path critic objective does not match request")
    if observation.get("autonomous_migration") is not False:
        raise WorkflowError("path critic cannot authorize autonomous migration")
    if observation.get("recommendation") not in RECOMMENDATIONS:
        raise WorkflowError("path critic recommendation is unsupported")
    _validate_findings(observation.get("findings"))


def _validate_findings(findings: Any) -> None:
    """Require contextual, quantified, revisitable causal findings."""
    if not isinstance(findings, list) or not findings:
        raise WorkflowError("path critic requires at least one finding")
    for finding in findings:
        if not isinstance(finding, Mapping):
            raise WorkflowError("path critic finding must be an object")
        if finding.get("dimension") not in CRITIC_DIMENSIONS:
            raise WorkflowError("path critic finding dimension is unsupported")
        for name in ("finding_key", "context", "causal_rationale", "expected_benefit"):
            if not isinstance(finding.get(name), str) or not finding[name].strip():
                raise WorkflowError(f"path critic finding requires {name}")
        if not isinstance(finding.get("affected_components"), list):
            raise WorkflowError("path critic finding requires affected components")
        if not isinstance(finding.get("measurable_indicators"), list):
            raise WorkflowError("path critic finding requires measurable indicators")


def record_critic_observation(
    request_path: Path,
    observation_path: Path,
) -> Mapping[str, Any]:
    """Persist one content-addressed revisitable path-critic observation."""
    request = _load_json(request_path, "path critic request")
    observation = _load_json(observation_path, "path critic observation")
    validate_critic_observation(request, observation)
    identity = dict(observation)
    identity["critic_request_sha256"] = _sha256(request_path)
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    root = STATE_ROOT / "path-critic-observations"
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"observation-sha256-{digest}.json"
    if not destination.exists():
        AtomicFileWriter((root,)).write_text(
            destination, _stable_json(identity), new_mode=0o600
        )
    return {"status": "recorded", "observation": str(destination)}


def _material_failure_observation(error: Exception) -> dict[str, bool]:
    """Return a conservative material-boundary observation."""
    text = f"{type(error).__name__}: {error}".lower()
    material_terms = (
        "authority",
        "containment",
        "history rewrite",
        "scope expansion",
        "constraint",
        "risk envelope",
        "different plan",
        "adapter",
        "approval digest",
    )
    material = any(term in text for term in material_terms)
    return {name: material for name in MATERIAL_FIELDS}


def _objective_recovery_authority(
    plan: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, str]:
    """Return stable authority evidence for recovery identity."""
    return {
        "objective_id": str(plan.get("objective_id", "")),
        "plan_sha256": str(execution.get("plan_sha256", "")),
        "approval_sha256": str(execution.get("approval_sha256", "")),
    }


def _recovery_attempt_dir(execution: Mapping[str, Any]) -> Path:
    """Create the next append-only objective recovery directory."""
    state_dir = Path(str(execution["plan"])).expanduser().resolve().parent
    number = len(execution.get("local_corrections", [])) + 1
    path = state_dir / f"recovery-{number:03d}"
    path.mkdir(parents=False, exist_ok=False)
    return path


def _objective_failure_text(error: Exception) -> str:
    """Return stable objective-execution failure text."""
    return (
        f"SAGE objective execution failed: "
        f"{type(error).__name__}: {error}"
    )


def _retrieve_objective_failure(
    repo: Path,
    runner: CommandRunner,
    text: str,
) -> None:
    """Run canonical failure retrieval before recovery classification."""
    runner.run(
        CommandSpec(
            "command.run",
            "Retrieve experience after objective-execution failure",
            (
                "python3",
                "-S",
                "scripts/sage/sage-failure-retrieval-gate.py",
                "--failure",
                text,
            ),
            repo,
            timeout_seconds=600,
        ),
        step_id="objective-execution-failure-retrieval",
    )


def _objective_recovery_context(
    plan: Mapping[str, Any],
    execution: Mapping[str, Any],
    error: Exception,
) -> tuple[str, Mapping[str, Any], list[dict[str, Any]], set[str]]:
    """Build identity plus recurrence context for one local failure."""
    from workflow.recovery import (
        build_recovery_identity,
        load_consumed_fingerprints,
        load_recovery_decisions,
    )

    text = _objective_failure_text(error)
    identity = build_recovery_identity(
        request=str(plan.get("objective_id", "")),
        component_id=WORKFLOW_ID,
        failure_text=text,
        repository_authority=_objective_recovery_authority(
            plan,
            execution,
        ),
    )
    root = STATE_ROOT.expanduser().resolve().parent
    identity_sha = str(identity["identity_sha256"])
    previous = load_recovery_decisions(root, identity_sha)
    consumed = load_consumed_fingerprints(root, identity_sha)
    return text, identity, previous, consumed


def _decide_objective_recovery(
    plan: Mapping[str, Any],
    execution: Mapping[str, Any],
    identity: Mapping[str, Any],
    previous: list[dict[str, Any]],
    consumed: set[str],
) -> Mapping[str, Any]:
    """Return the shared recurrence-aware next-boundary decision."""
    from workflow.diagnosis import classify_post_retrieval_continuation
    from workflow.recovery import decide_next_boundary

    post_retrieval = classify_post_retrieval_continuation(
        retrieval_performed=True,
        attempted_action_authorized=True,
        governing_changes={
            "authority": False,
            "scope": False,
            "required_capability": False,
            "safety_requirements": False,
            "repository_owned_composition": False,
            "approval_or_mutation_boundaries": False,
        },
        recovery_identity=identity,
    )
    evidence = {
        "objective_id": plan.get("objective_id"),
        "plan_sha256": execution.get("plan_sha256"),
        "approval_sha256": execution.get("approval_sha256"),
        "classification": "implementation-local-correction",
    }
    return decide_next_boundary(
        identity=identity,
        post_retrieval=post_retrieval,
        governing_evidence=evidence,
        previous=previous,
        consumed_fingerprints=consumed,
        owning_component=WORKFLOW_ID,
        control_action_id=None,
        control_action_status=None,
        accepted_control_failure=None,
    )


def _persist_objective_recovery_decision(
    writer: AtomicFileWriter,
    execution: Mapping[str, Any],
    decision: Mapping[str, Any],
) -> tuple[Path, Mapping[str, Any]]:
    """Persist one bound objective-owned recovery decision."""
    from workflow.recovery import (
        RECOVERY_DECISION_NAME,
        bind_successor_operator_boundary,
    )

    attempt_dir = _recovery_attempt_dir(execution)
    decision_path = attempt_dir / RECOVERY_DECISION_NAME
    bound = bind_successor_operator_boundary(
        decision,
        decision_path,
    )
    writer.write_text(
        decision_path,
        _stable_json(bound),
        new_mode=0o600,
    )
    return decision_path, bound


def _build_objective_recovery_decision(
    repo: Path,
    plan: Mapping[str, Any],
    writer: AtomicFileWriter,
    runner: CommandRunner,
    execution: Mapping[str, Any],
    error: Exception,
) -> tuple[Path, Mapping[str, Any]]:
    """Build one shared recurrence-aware recovery decision."""
    text, identity, previous, consumed = _objective_recovery_context(
        plan,
        execution,
        error,
    )
    _retrieve_objective_failure(repo, runner, text)
    decision = _decide_objective_recovery(
        plan,
        execution,
        identity,
        previous,
        consumed,
    )
    return _persist_objective_recovery_decision(
        writer,
        execution,
        decision,
    )


def _validate_objective_recovery_decision(
    decision: Mapping[str, Any],
) -> tuple[str, str]:
    """Validate one objective-owned implementation-local recovery."""
    if decision.get("record_type") != "sage-recovery-next-boundary":
        raise WorkflowError("objective recovery decision type is invalid")
    if decision.get("owning_component") != WORKFLOW_ID:
        raise WorkflowError("objective recovery owner is invalid")
    if (
        decision.get("disposition") != "repair"
        or decision.get("next_boundary") != "implementation-local"
    ):
        raise WorkflowError(
            "objective recovery is not implementation-local repair"
        )
    identity = decision.get("recovery_identity", {})
    identity_sha = str(identity.get("identity_sha256", ""))
    fingerprint = str(
        decision.get("governing_condition_fingerprint", "")
    )
    if not identity_sha or not fingerprint:
        raise WorkflowError("objective recovery identity is invalid")
    return identity_sha, fingerprint


def _validate_objective_recovery_runtime(
    repo: Path,
    source: Path,
) -> tuple[AtomicFileWriter, str]:
    """Run owner validation before consuming local recovery."""
    writer, runner = _runtime(repo, source.parent)
    result = runner.run(
        CommandSpec(
            "command.run",
            "Validate objective implementation-local recovery",
            (
                "python3",
                "scripts/sage/sage-objective-execution.py",
                "--self-test",
            ),
            repo,
            timeout_seconds=600,
        ),
        step_id="objective-execution-recovery-validation",
    )
    return writer, result.output_sha256


def _recovery_already_consumed(
    identity_sha: str,
    fingerprint: str,
) -> bool:
    """Return whether the exact governing condition was consumed."""
    from workflow.recovery import load_consumed_fingerprints

    root = STATE_ROOT.expanduser().resolve().parent
    return fingerprint in load_consumed_fingerprints(
        root,
        identity_sha,
    )


def _already_consumed_recovery(
    source: Path,
    validation_sha: str,
) -> Mapping[str, Any]:
    """Return the idempotent recovery-consumption result."""
    return {
        "status": "already-consumed",
        "consumption": None,
        "validation_output_sha256": validation_sha,
        "source_recovery_decision": str(source),
        "repository_mutation": False,
    }


def consume_objective_recovery_decision(
    repo: Path,
    recovery_decision_path: Path,
    output: Path | None = None,
) -> Mapping[str, Any]:
    """Consume one objective-owned implementation-local recovery."""
    from workflow.recovery import (
        RECOVERY_CONSUMPTION_NAME,
        build_consumption_record,
    )

    resolved_repo = repo.expanduser().resolve()
    source = recovery_decision_path.expanduser().resolve()
    decision = _load_json(source, "objective recovery decision")
    identity_sha, fingerprint = _validate_objective_recovery_decision(
        decision
    )
    writer, validation_sha = _validate_objective_recovery_runtime(
        resolved_repo,
        source,
    )
    if _recovery_already_consumed(identity_sha, fingerprint):
        return _already_consumed_recovery(source, validation_sha)

    destination = (
        output or source.parent / RECOVERY_CONSUMPTION_NAME
    ).expanduser().resolve()
    record = build_consumption_record(
        decision,
        consumed_boundary="implementation-local",
        consumer_reference=str(source.parent / "events.jsonl"),
    )
    writer.write_text(
        destination,
        _stable_json(record),
        new_mode=0o600,
    )
    return {
        "status": "consumed",
        "consumption": str(destination),
        "validation_output_sha256": validation_sha,
        "repository_mutation": False,
    }


def _record_true_replan(
    writer: AtomicFileWriter,
    execution_path: Path,
    execution: dict[str, Any],
    error: Exception,
    observation: Mapping[str, Any],
) -> None:
    """Persist a material deviation without auto-continuation."""
    execution["true_replans"].append(
        {
            "classification": "true-replan",
            "error": _objective_failure_text(error),
            "observation": dict(observation),
        }
    )
    execution["status"] = "material-intervention-required"
    writer.write_text(
        execution_path,
        _stable_json(execution),
        new_mode=0o600,
    )


def _record_local_correction(
    writer: AtomicFileWriter,
    execution_path: Path,
    execution: dict[str, Any],
    error: Exception,
    decision_path: Path,
    consumed: Mapping[str, Any],
) -> None:
    """Persist verified implementation-local correction evidence."""
    execution["local_corrections"].append(
        {
            "classification": "implementation-local-correction",
            "error": _objective_failure_text(error),
            "recovery_decision": str(decision_path),
            "recovery_consumption": consumed.get("consumption"),
            "validation_output_sha256": (
                consumed.get("validation_output_sha256")
            ),
        }
    )
    execution["status"] = "executing"
    writer.write_text(
        execution_path,
        _stable_json(execution),
        new_mode=0o600,
    )


def _require_local_recovery_decision(
    writer: AtomicFileWriter,
    execution_path: Path,
    execution: dict[str, Any],
    decision: Mapping[str, Any],
) -> None:
    """Fail closed when shared recovery selects a governed boundary."""
    if (
        decision.get("disposition") == "repair"
        and decision.get("next_boundary") == "implementation-local"
    ):
        return
    execution["status"] = "recovery-boundary-required"
    writer.write_text(
        execution_path,
        _stable_json(execution),
        new_mode=0o600,
    )
    raise WorkflowError(
        "objective recovery requires governed boundary: "
        f"{decision.get('next_boundary')}"
    )


def _recover_local_failure(
    repo: Path,
    plan: Mapping[str, Any],
    writer: AtomicFileWriter,
    runner: CommandRunner,
    execution_path: Path,
    execution: dict[str, Any],
    error: Exception,
) -> bool:
    """Recover one local failure or expose a material boundary."""
    observation = _material_failure_observation(error)
    if classify_change(observation) == "true-replan":
        _record_true_replan(
            writer,
            execution_path,
            execution,
            error,
            observation,
        )
        return False

    decision_path, decision = _build_objective_recovery_decision(
        repo,
        plan,
        writer,
        runner,
        execution,
        error,
    )
    _require_local_recovery_decision(
        writer,
        execution_path,
        execution,
        decision,
    )
    consumed = consume_objective_recovery_decision(
        repo,
        decision_path,
    )
    _record_local_correction(
        writer,
        execution_path,
        execution,
        error,
        decision_path,
        consumed,
    )
    return True

def objective_recovery_contract_self_test(repo: Path) -> None:
    """Verify objective execution is registered with shared recovery."""
    resolved = repo.expanduser().resolve()
    recovery = (
        resolved / "scripts/sage/workflow/recovery.py"
    ).read_text(encoding="utf-8")
    objective = Path(__file__).read_text(encoding="utf-8")
    required = (
        '"sage.objective-execution"',
        "sage-objective-execution.py recover",
    )
    if any(marker not in recovery for marker in required):
        raise RuntimeError("objective shared-recovery registration is missing")
    for marker in (
        "_recover_local_failure(",
        "consume_objective_recovery_decision(",
        "classify_post_retrieval_continuation",
    ):
        if marker not in objective:
            raise RuntimeError(
                f"objective recovery composition is missing {marker}"
            )


def self_test() -> None:
    """Exercise objective atomicity and path-critic authority contracts."""
    if classify_change({"scope_expanded": False}) != "implementation-local-correction":
        raise RuntimeError("local correction classification failed")
    if classify_change({"authority_changed": True}) != "true-replan":
        raise RuntimeError("true replan classification failed")
    route = objective_execution_route_summary({})
    if route["routine_step_approval_atomicity"] is not False:
        raise RuntimeError("routine step approval remained Architect-atomic")
    request = {"objective_id": "SAGE-ACTION-FIXTURE"}
    validate_critic_observation(request, _fixture_observation())


def _fixture_observation() -> dict[str, Any]:
    """Return one valid quantified path-critic fixture."""
    return {
        "record_type": "sage-path-critic-causal-observation",
        "producer_class": "llm-path-critic",
        "objective_id": "SAGE-ACTION-FIXTURE",
        "recommendation": "deferral",
        "autonomous_migration": False,
        "findings": [{
            "dimension": "operator-boundaries",
            "finding_key": "routine-boundary-amplification",
            "context": "ordinary post-promotion branch closeout",
            "causal_rationale": "Equivalent steps caused repeated human round trips.",
            "expected_benefit": "Reduce routine follow-up interventions to zero.",
            "affected_components": ["sage.branch-lifecycle"],
            "measurable_indicators": ["architect_interventions", "verified_steps"],
        }],
    }
