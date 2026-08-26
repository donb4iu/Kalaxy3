
"""Repository-owned SAGE intent-to-outcome orchestration front door."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from workflow import AtomicFileWriter, PrimitiveCatalog, WorkflowError
from workflow.recovery import (
    RECOVERY_CONSUMPTION_NAME,
    build_consumption_record,
    governing_composition_digest,
    latest_matching_reentry,
    load_consumed_fingerprints,
)
from workflows.checkpoint_promotion import continue_promotion, start_promotion
from workflows.request_execution import (
    continue_request,
    continue_request_from_routine_receipt,
    execute_request,
)
from workflows.request_planning import (
    plan_request,
    reuse_component_plan,
    validate_reusable_plan_lineage,
)
from workflows.semantic_bootstrap import begin_bootstrap, continue_bootstrap, reuse_confirmed_intent

WORKFLOW_ID = "sage.intent-to-outcome"
WORKFLOW_VERSION = "0.2.6"
PRIMITIVES_USED = (
    "catalog.registry",
    "file.atomic-preserve-mode",
    "workflow.composition",
)
STATE_ROOT = Path("~/.local/state/kalaxy3/sage-intent-to-outcome").expanduser()
RECOVERY_STATE_ROOT = Path("~/.local/state/kalaxy3").expanduser()


def _stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def _request_digest(request: str) -> str:
    return hashlib.sha256(request.encode("utf-8")).hexdigest()


def _semantic_planning_source(result: Mapping[str, Any]) -> str:
    """Resolve the semantic-bootstrap planning-source interface across compatible versions."""

    value = result.get("planning_source") or result.get("source")
    if not isinstance(value, str) or not value:
        raise WorkflowError("semantic bootstrap did not return a planning source")
    return value


REENTRY_BOUNDARIES = {
    "implementation-local",
    "planning",
    "semantic-confirmation",
    "authority",
}

DURABLE_CANDIDATE_STATUSES = frozenset({
    "source-git-complete",
    "runtime-verified",
})
INFLIGHT_CANDIDATE_STATUSES = frozenset({
    "architect-confirmation-required",
    "planning-source-ready",
    "authority-review-required",
})


def candidate_iteration_entry_mode(status: str) -> str:
    """Classify durable iteration versus safe pre-mutation supersession."""
    if status in DURABLE_CANDIDATE_STATUSES:
        return "durable-checkpoint"
    if status in INFLIGHT_CANDIDATE_STATUSES:
        return "inflight-supersession"
    raise WorkflowError(
        "candidate iteration requires either a durable checkpoint or an "
        "unfinished pre-mutation candidate that can be safely superseded"
    )



def _iteration_record(
    number: int,
    *,
    parent_checkpoint: str | None,
    candidate_head: str | None,
    trigger: str,
    affected_obligations: list[str],
    status: str,
    unresolved_findings: list[str] | None = None,
    next_boundary: str | None = None,
) -> dict[str, Any]:
    return {
        "iteration": number,
        "parent_checkpoint": parent_checkpoint,
        "candidate_head": candidate_head,
        "trigger": trigger,
        "affected_obligations": list(dict.fromkeys(affected_obligations)),
        "validation_state": "pending",
        "status": status,
        "unresolved_findings": list(dict.fromkeys(unresolved_findings or [])),
        "learning": [],
        "invalidated_downstream_state": [],
        "next_boundary": next_boundary,
        "promotion_eligible": False,
    }


def _ensure_iteration_contract(state: dict[str, Any]) -> dict[str, Any]:
    if "iterations" not in state:
        state["objective_id"] = state.get("action_id") or state.get("request_sha256")
        state["current_iteration"] = 1
        state["iterations"] = [
            _iteration_record(
                1,
                parent_checkpoint=None,
                candidate_head=None,
                trigger="legacy intent-to-outcome state adopted into iterative contract",
                affected_obligations=[],
                status="legacy-adopted",
                next_boundary=None,
            )
        ]
        state["promotion_eligible"] = False
    return state


def _current_iteration(state: Mapping[str, Any]) -> dict[str, Any]:
    number = int(state.get("current_iteration", 0))
    for item in state.get("iterations", []):
        if isinstance(item, dict) and item.get("iteration") == number:
            return item
    raise WorkflowError("intent state current iteration is missing")


def _new_state_directory() -> Path:
    destination = STATE_ROOT / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination.mkdir(parents=True, exist_ok=False)
    return destination


def _persist(path: Path, state: Mapping[str, Any]) -> None:
    AtomicFileWriter((path.parent,)).write_text(
        path,
        _stable_json(state),
        new_mode=0o600,
    )


def _load_parent(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    value = json.loads(resolved.read_text(encoding="utf-8"))
    if value.get("record_type") != "sage-intent-to-outcome-state":
        raise WorkflowError("intent-to-outcome state type is invalid")
    request = str(value.get("request", ""))
    if not request or value.get("request_sha256") != _request_digest(request):
        raise WorkflowError("intent-to-outcome request binding is invalid")
    return _ensure_iteration_contract(value)


def reconcile_completed_semantic_child(
    parent: Mapping[str, Any],
    semantic_state_path: Path,
    confirmation: str,
    dispositions: Path,
    actor: str,
) -> Mapping[str, Any]:
    """Validate and reuse one already-completed semantic child without replay."""

    if actor != "architect":
        raise WorkflowError("semantic confirmation must be exercised by the Architect role")
    child_path = semantic_state_path.expanduser().resolve()
    try:
        child = json.loads(child_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"completed semantic child state is unreadable: {child_path}: {error}") from error
    if child.get("record_type") != "sage-semantic-bootstrap-state":
        raise WorkflowError("completed semantic child state type is invalid")
    if child.get("status") != "planning-source-ready":
        raise WorkflowError("semantic child is not already planning-source-ready")
    if child.get("request") != parent.get("request") or child.get("action_id") != parent.get("action_id"):
        raise WorkflowError("completed semantic child does not match parent request/action lineage")
    parent_contribution = parent.get("contribution")
    if not isinstance(parent_contribution, str) or not parent_contribution:
        raise WorkflowError("intent parent contribution lineage is missing")
    if Path(str(child.get("contribution", ""))).expanduser().resolve() != Path(parent_contribution).expanduser().resolve():
        raise WorkflowError("completed semantic child does not match parent contribution lineage")
    if confirmation != child.get("semantic_understanding_sha256"):
        raise WorkflowError("completed semantic child confirmation digest does not match the parent confirmation")
    decisions_path = dispositions.expanduser().resolve()
    expected_decisions_sha = child.get("architect_dispositions_sha256")
    if not isinstance(expected_decisions_sha, str) or not expected_decisions_sha:
        raise WorkflowError("completed semantic child does not preserve Architect disposition evidence")
    try:
        observed_decisions_sha = hashlib.sha256(decisions_path.read_bytes()).hexdigest()
    except OSError as error:
        raise WorkflowError(f"Architect dispositions are unreadable: {decisions_path}: {error}") from error
    if observed_decisions_sha != expected_decisions_sha:
        raise WorkflowError("Architect disposition evidence changed after semantic confirmation")
    planning_source = child.get("planning_source")
    if not isinstance(planning_source, str) or not planning_source:
        raise WorkflowError("completed semantic child does not preserve a planning source")
    planning_path = Path(planning_source).expanduser().resolve()
    if not planning_path.is_file():
        raise WorkflowError(f"completed semantic planning source is missing: {planning_path}")
    return {
        "status": "planning-source-ready",
        "planning_source": str(planning_path),
        "source": str(planning_path),
        "state": str(child_path),
        "reconciled_from_completed_semantic_child": True,
    }


def begin_intent(
    repo: Path,
    action_id: str,
    request: str,
    contribution: Path,
) -> Mapping[str, Any]:
    resolved = repo.expanduser().resolve()
    PrimitiveCatalog.load(resolved / "sage-workflow-primitives.json").require(
        PRIMITIVES_USED
    )
    semantic = begin_bootstrap(
        resolved,
        action_id,
        request,
        contribution.expanduser().resolve(),
    )
    directory = _new_state_directory()
    state_path = directory / "intent-to-outcome-state.json"
    state = {
        "schema_version": "1.0",
        "record_type": "sage-intent-to-outcome-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "request": request,
        "request_sha256": _request_digest(request),
        "action_id": action_id,
        "objective_id": action_id,
        "contribution": str(contribution.expanduser().resolve()),
        "status": "architect-confirmation-required",
        "semantic_state": str(semantic["state"]),
        "request_execution_state": None,
        "runtime_receipt": None,
        "promotion_state": None,
        "current_iteration": 1,
        "iterations": [
            _iteration_record(
                1,
                parent_checkpoint=None,
                candidate_head=None,
                trigger="initial governed objective candidate",
                affected_obligations=[],
                status="semantic-confirmation",
                next_boundary="semantic-confirmation",
            )
        ],
        "promotion_eligible": False,
        "history": [],
    }
    _persist(state_path, state)
    return {
        "status": state["status"],
        "state": str(state_path),
        "semantic_understanding": semantic["semantic_understanding"],
        "semantic_understanding_sha256": semantic["semantic_understanding_sha256"],
        "architect_dispositions": semantic["architect_dispositions"],
        "confirmation_command": semantic["confirmation_command"],
    }


def confirm_intent(
    repo: Path,
    state_path: Path,
    confirmation: str,
    dispositions: Path,
    actor: str,
) -> Mapping[str, Any]:
    resolved = repo.expanduser().resolve()
    state = _load_parent(state_path)
    if state.get("status") != "architect-confirmation-required":
        raise WorkflowError("intent state is not awaiting Architect confirmation")
    semantic_state_path = Path(str(state["semantic_state"]))
    child_state = json.loads(semantic_state_path.expanduser().resolve().read_text(encoding="utf-8"))
    if child_state.get("status") == "planning-source-ready":
        semantic = reconcile_completed_semantic_child(
            state,
            semantic_state_path,
            confirmation,
            dispositions,
            actor,
        )
    else:
        semantic = continue_bootstrap(
            resolved,
            semantic_state_path,
            confirmation,
            actor,
            None,
            dispositions.expanduser().resolve(),
        )
    proposal_path = (
        Path("~/Downloads").expanduser()
        / ("sage-request-proposal-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip")
    )
    semantic_source = _semantic_planning_source(semantic)
    state["planning_source"] = semantic_source
    state["status"] = "planning-source-ready"
    iteration = _current_iteration(state)
    iteration["status"] = "planning"
    iteration["next_boundary"] = "planning"
    state["history"].append(
        {
            "stage": "semantic-confirmation-complete",
            "iteration": state["current_iteration"],
            "planning_source": semantic_source,
            "reconciled_from_completed_semantic_child": bool(
                semantic.get("reconciled_from_completed_semantic_child")
            ),
        }
    )
    _persist(state_path.expanduser().resolve(), state)
    planned = plan_request(
        resolved,
        str(state["request"]),
        Path(semantic_source),
        proposal_path,
    )
    execution = execute_request(
        resolved,
        str(state["request"]),
        Path(str(planned["proposal"])),
    )
    state["status"] = "request-operator-review-required"
    state["planning_source"] = semantic_source
    state["planning_proposal"] = str(planned["proposal"])
    state["request_execution_state"] = str(execution["state"])
    iteration = _current_iteration(state)
    iteration["status"] = "request-execution"
    iteration["next_boundary"] = "operator-review"
    state["history"].append(
        {
            "stage": "semantic-plan-execute",
            "iteration": state["current_iteration"],
            "planning_source": semantic_source,
            "planning_proposal": str(planned["proposal"]),
            "request_execution_state": str(execution["state"]),
        }
    )
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "request_execution": execution,
    }


def adopt_iteration(
    repo: Path,
    request: str,
    request_state: Path,
    *,
    action_id: str | None = None,
    candidate_head: str | None = None,
    planning_source: Path | None = None,
    unresolved_findings: list[str] | None = None,
) -> Mapping[str, Any]:
    """Adopt an existing request execution as iteration 1 without claiming promotion."""

    resolved = repo.expanduser().resolve()
    PrimitiveCatalog.load(resolved / "sage-workflow-primitives.json").require(
        PRIMITIVES_USED
    )
    request_state = request_state.expanduser().resolve()
    child = json.loads(request_state.read_text(encoding="utf-8"))
    if child.get("record_type") != "sage-request-execution-state":
        raise WorkflowError("adopted request state type is invalid")
    if child.get("request_sha256") != _request_digest(request):
        raise WorkflowError("adopted request state does not match literal request")
    inherited_source: str | None = None
    inherited_proposal: str | None = None
    proposal_value = child.get("proposal_package")
    if planning_source is not None:
        if not isinstance(proposal_value, str) or not proposal_value:
            raise WorkflowError("adopted request state has no planning proposal lineage")
        proposal_path = Path(proposal_value).expanduser().resolve()
        if not proposal_path.is_file():
            raise WorkflowError(f"adopted planning proposal is missing: {proposal_path}")
        expected_proposal_sha = child.get("proposal_package_sha256")
        observed_proposal_sha = hashlib.sha256(proposal_path.read_bytes()).hexdigest()
        if expected_proposal_sha != observed_proposal_sha:
            raise WorkflowError("adopted planning proposal digest no longer matches request state")
        lineage = validate_reusable_plan_lineage(
            request,
            planning_source.expanduser().resolve(),
            proposal_path,
        )
        inherited_source = lineage["planning_source"]
        inherited_proposal = lineage["planning_proposal"]
    elif action_id is not None:
        raise WorkflowError(
            "iterative objective adoption requires --planning-source so confirmed planning lineage is preserved"
        )
    directory = _new_state_directory()
    state_path = directory / "intent-to-outcome-state.json"
    complete = child.get("current_boundary") == "complete"
    findings = list(dict.fromkeys(unresolved_findings or []))
    state = {
        "schema_version": "1.1",
        "record_type": "sage-intent-to-outcome-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "request": request,
        "request_sha256": _request_digest(request),
        "action_id": action_id,
        "objective_id": action_id or _request_digest(request),
        "contribution": None,
        "status": "source-git-complete" if complete else "request-operator-review-required",
        "semantic_state": None,
        "planning_source": inherited_source,
        "planning_proposal": inherited_proposal,
        "request_execution_state": str(request_state),
        "runtime_receipt": None,
        "promotion_state": None,
        "current_iteration": 1,
        "iterations": [
            _iteration_record(
                1,
                parent_checkpoint=None,
                candidate_head=candidate_head,
                trigger="one-time bootstrap adoption of pre-front-door candidate",
                affected_obligations=[],
                status="checkpoint-non-promotable" if complete else "request-execution",
                unresolved_findings=findings,
                next_boundary="candidate-iteration" if complete else "operator-review",
            )
        ],
        "promotion_eligible": False,
        "history": [
            {
                "stage": "one-time-bootstrap-adoption",
                "iteration": 1,
                "request_execution_state": str(request_state),
                "planning_source": inherited_source,
                "planning_proposal": inherited_proposal,
                "candidate_head": candidate_head,
                "unresolved_findings": findings,
            }
        ],
    }
    _persist(state_path, state)
    return {"status": state["status"], "state": str(state_path)}


def adopt_request_execution(
    repo: Path,
    request: str,
    request_state: Path,
) -> Mapping[str, Any]:
    """Compatibility wrapper for the original one-time bootstrap seam."""

    return adopt_iteration(repo, request, request_state)



def _current_recovery_composition_sha256(repo: Path) -> str:
    """Return the current policy-declared recovery-composition digest."""

    resolved = repo.expanduser().resolve()
    policy_path = resolved / "sage-recovery-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if (
        not isinstance(policy, dict)
        or policy.get("schema_version") != "1.0"
        or policy.get("policy_id") != "kalaxy3-sage-recovery"
    ):
        raise WorkflowError("SAGE recovery policy is invalid")
    paths = policy.get("governing_composition_paths")
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise WorkflowError("recovery governing composition paths are invalid")
    return governing_composition_digest(resolved, paths)


def _consume_recovery_reentry(
    repo: Path,
    state_path: Path,
    state: Mapping[str, Any],
    reentry_boundary: str,
) -> str | None:
    """Consume one current-composition recovery re-entry exactly once."""

    if reentry_boundary == "implementation-local":
        return None
    current_composition = _current_recovery_composition_sha256(repo)
    match = latest_matching_reentry(
        RECOVERY_STATE_ROOT,
        str(state["request_sha256"]),
        reentry_boundary,
        repository_owned_composition_sha256=current_composition,
    )
    if match is None:
        return None
    _, decision = match
    identity = decision.get("recovery_identity", {})
    identity_sha = str(identity.get("identity_sha256", ""))
    fingerprint = str(decision.get("governing_condition_fingerprint", ""))
    if not identity_sha or not fingerprint:
        raise WorkflowError("recovery re-entry decision identity is invalid")
    consumed = load_consumed_fingerprints(RECOVERY_STATE_ROOT, identity_sha)
    if fingerprint in consumed:
        raise WorkflowError(
            "repeated governance re-entry blocked for consumed recovery fingerprint"
        )
    destination = (
        state_path.expanduser().resolve().parent
        / "recovery-consumptions"
        / fingerprint
        / RECOVERY_CONSUMPTION_NAME
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    record = build_consumption_record(
        decision,
        consumed_boundary=reentry_boundary,
        consumer_reference=str(state_path.expanduser().resolve()),
    )
    _persist(destination, record)
    return str(destination)


def begin_candidate_iteration(
    repo: Path,
    state_path: Path,
    contribution: Path,
    *,
    trigger: str,
    reentry_boundary: str,
    parent_checkpoint: str,
    affected_obligations: list[str] | None = None,
    approved_gap_set: Path | None = None,
) -> Mapping[str, Any]:
    """Begin the next candidate under the same objective at the earliest affected boundary."""

    if reentry_boundary not in REENTRY_BOUNDARIES:
        raise WorkflowError(f"unsupported iteration re-entry boundary: {reentry_boundary}")
    if not trigger.strip() or not parent_checkpoint.strip():
        raise WorkflowError("candidate iteration requires trigger and parent checkpoint")
    resolved = repo.expanduser().resolve()
    state = _load_parent(state_path)
    entry_mode = candidate_iteration_entry_mode(str(state.get("status", "")))
    recovery_consumption = _consume_recovery_reentry(
        resolved,
        state_path,
        state,
        reentry_boundary,
    )
    prior = _current_iteration(state)
    prior["promotion_eligible"] = False
    findings = prior.setdefault("unresolved_findings", [])
    if trigger.strip() not in findings:
        findings.append(trigger.strip())
    if entry_mode == "durable-checkpoint":
        prior["status"] = "checkpoint-non-promotable"
    else:
        prior["status"] = "superseded-in-progress"
        prior["next_boundary"] = "candidate-iteration"
        prior.setdefault("learning", []).append({
            "kind": "candidate-union",
            "observation": (
                "Validation exposed another related correction before the "
                "candidate reached a durable checkpoint; the successor "
                "accumulates the unfinished candidate rather than requiring "
                "separate promotion."
            ),
        })
    number = int(state["current_iteration"]) + 1
    iteration = _iteration_record(
        number,
        parent_checkpoint=parent_checkpoint.strip(),
        candidate_head=None,
        trigger=trigger.strip(),
        affected_obligations=affected_obligations or [],
        status="starting",
        next_boundary=reentry_boundary,
    )
    state["iterations"].append(iteration)
    state["current_iteration"] = number
    iteration["entry_mode"] = entry_mode
    if recovery_consumption is not None:
        iteration["recovery_consumption"] = recovery_consumption
    state["promotion_eligible"] = False
    state["runtime_receipt"] = None
    state["promotion_state"] = None
    state["contribution"] = str(contribution.expanduser().resolve())

    if reentry_boundary == "authority":
        iteration["status"] = "authority-review-required"
        iteration["invalidated_downstream_state"] = [
            "semantic-confirmation",
            "planning",
            "request-execution",
            "runtime",
            "promotion",
        ]
        state["status"] = "authority-review-required"
        state["history"].append({
            "stage": "candidate-iteration-start",
            "iteration": number,
            "reentry_boundary": reentry_boundary,
            "trigger": trigger.strip(),
        })
        _persist(state_path.expanduser().resolve(), state)
        return {"status": state["status"], "state": str(state_path.expanduser().resolve())}

    if reentry_boundary == "semantic-confirmation":
        if not state.get("action_id"):
            raise WorkflowError("semantic re-entry requires an objective action_id")
        iteration["invalidated_downstream_state"] = [
            "semantic-confirmation",
            "planning",
            "request-execution",
            "runtime",
            "promotion",
        ]
        semantic = begin_bootstrap(
            resolved,
            str(state["action_id"]),
            str(state["request"]),
            contribution.expanduser().resolve(),
        )
        state["semantic_state"] = str(semantic["state"])
        state["status"] = "architect-confirmation-required"
        iteration["status"] = "semantic-confirmation"
        iteration["next_boundary"] = "semantic-confirmation"
        state["history"].append({
            "stage": "candidate-iteration-start",
            "iteration": number,
            "reentry_boundary": reentry_boundary,
            "trigger": trigger.strip(),
        })
        _persist(state_path.expanduser().resolve(), state)
        return {
            "status": state["status"],
            "state": str(state_path.expanduser().resolve()),
            "semantic_understanding": semantic["semantic_understanding"],
            "semantic_understanding_sha256": semantic["semantic_understanding_sha256"],
            "architect_dispositions": semantic["architect_dispositions"],
            "confirmation_command": semantic["confirmation_command"],
        }

    if not state.get("planning_source"):
        raise WorkflowError(
            f"{reentry_boundary} re-entry requires a prior confirmed planning source"
        )
    reused = reuse_confirmed_intent(
        resolved,
        str(state["request"]),
        Path(str(state["planning_source"])),
        contribution.expanduser().resolve(),
    )
    new_source = Path(str(reused["planning_source"]))
    proposal_path = (
        Path("~/Downloads").expanduser()
        / ("sage-request-proposal-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip")
    )
    if reentry_boundary == "implementation-local":
        if not state.get("planning_proposal"):
            raise WorkflowError("implementation-local re-entry requires a prior planning proposal")
        iteration["invalidated_downstream_state"] = ["request-execution", "runtime", "promotion"]
        planned = reuse_component_plan(
            resolved,
            str(state["request"]),
            new_source,
            Path(str(state["planning_proposal"])),
            proposal_path,
        )
    else:
        iteration["invalidated_downstream_state"] = ["planning", "request-execution", "runtime", "promotion"]
        planned = plan_request(
            resolved,
            str(state["request"]),
            new_source,
            proposal_path,
            approved_gap_set=approved_gap_set,
        )
    execution = execute_request(
        resolved,
        str(state["request"]),
        Path(str(planned["proposal"])),
    )
    state["planning_source"] = str(new_source)
    state["planning_proposal"] = str(planned["proposal"])
    state["request_execution_state"] = str(execution["state"])
    state["status"] = "request-operator-review-required"
    iteration["status"] = "request-execution"
    iteration["next_boundary"] = "operator-review"
    state["history"].append({
        "stage": "candidate-iteration-start",
        "iteration": number,
        "reentry_boundary": reentry_boundary,
        "trigger": trigger.strip(),
        "planning_source": str(new_source),
        "planning_proposal": str(planned["proposal"]),
        "request_execution_state": str(execution["state"]),
        "approved_gap_set": (
            str(approved_gap_set.expanduser().resolve())
            if approved_gap_set is not None
            else None
        ),
    })
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "iteration": number,
        "request_execution": execution,
    }



def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"{label} is not readable JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise WorkflowError(f"{label} must be a JSON object: {path}")
    return value


def reconcile_completed_request_child(
    parent: Mapping[str, Any],
    child_state_path: Path,
    *,
    routine_receipt: Path | None = None,
) -> Mapping[str, Any]:
    """Validate and reconcile a child request execution that already self-closed.

    The routine Git controller may consume its own receipt and move request execution
    to ``complete`` before the parent intent-to-outcome workflow is resumed.  Parent
    continuation must treat that completed child state as evidence, not replay the
    already-consumed mutation boundary.
    """

    child_state_path = child_state_path.expanduser().resolve()
    child = _load_json_object(child_state_path, "completed request child state")
    if child.get("record_type") != "sage-request-execution-state":
        raise WorkflowError("completed request child state type is invalid")
    if child.get("request_sha256") != parent.get("request_sha256"):
        raise WorkflowError("completed request child does not match parent literal request")
    if child.get("current_boundary") != "complete":
        raise WorkflowError("request child is not already complete")
    if child.get("current_proposal") is not None:
        raise WorkflowError("completed request child still carries an active proposal")

    history = child.get("history")
    if not isinstance(history, list) or not history:
        raise WorkflowError("completed request child has no boundary history")
    completed = [
        item
        for item in history
        if isinstance(item, dict)
        and item.get("boundary") == "routine-git-lifecycle"
        and isinstance(item.get("boundary_result_sha256"), str)
        and item.get("boundary_result_sha256")
    ]
    if not completed:
        raise WorkflowError("completed request child lacks routine Git lifecycle evidence")
    event = completed[-1]

    canonical_receipt = (child_state_path.parent / "routine-git-lifecycle-receipt.json").resolve()
    supplied_receipt = routine_receipt.expanduser().resolve() if routine_receipt is not None else canonical_receipt
    if supplied_receipt != canonical_receipt:
        raise WorkflowError("routine receipt does not match the completed child canonical receipt")
    if not canonical_receipt.is_file():
        raise WorkflowError(f"completed child routine receipt is missing: {canonical_receipt}")
    receipt_sha256 = hashlib.sha256(canonical_receipt.read_bytes()).hexdigest()
    if event.get("boundary_result_sha256") != receipt_sha256:
        raise WorkflowError("completed child routine receipt digest does not match child history")
    _load_json_object(canonical_receipt, "completed child routine receipt")

    evidence: dict[str, str] = {}
    for field, label in (
        ("verification", "post-operator verification"),
        ("metrics", "outcome metrics"),
        ("evidence_closeout", "evidence closeout"),
    ):
        raw = event.get(field)
        if not isinstance(raw, str) or not raw:
            raise WorkflowError(f"completed request child lacks {field} evidence")
        evidence_path = Path(raw).expanduser().resolve()
        _load_json_object(evidence_path, label)
        evidence[field] = str(evidence_path)

    return {
        "status": "complete",
        "verified_boundary": "routine-git-lifecycle",
        "reconciled_from_completed_child": True,
        "routine_receipt": str(canonical_receipt),
        "routine_receipt_sha256": receipt_sha256,
        **evidence,
    }

def continue_intent_request(
    repo: Path,
    state_path: Path,
    *,
    operator_result: Path | None = None,
    routine_receipt: Path | None = None,
) -> Mapping[str, Any]:
    if (operator_result is None) == (routine_receipt is None):
        raise WorkflowError("provide exactly one operator result or routine receipt")
    state = _load_parent(state_path)
    if state.get("status") != "request-operator-review-required":
        raise WorkflowError("intent state is not awaiting request continuation")
    child_state = Path(str(state["request_execution_state"]))
    child_snapshot = _load_json_object(child_state.expanduser().resolve(), "request child state")
    if child_snapshot.get("current_boundary") == "complete":
        if routine_receipt is None:
            raise WorkflowError(
                "completed self-closing request child requires its canonical routine receipt for parent reconciliation"
            )
        result = reconcile_completed_request_child(
            state,
            child_state,
            routine_receipt=routine_receipt,
        )
    elif routine_receipt is not None:
        result = continue_request_from_routine_receipt(
            repo.expanduser().resolve(),
            child_state,
            routine_receipt.expanduser().resolve(),
        )
    else:
        result = continue_request(
            repo.expanduser().resolve(),
            child_state,
            operator_result.expanduser().resolve(),  # type: ignore[union-attr]
        )
    state["status"] = (
        "source-git-complete"
        if result["status"] == "complete"
        else "request-operator-review-required"
    )
    iteration = _current_iteration(state)
    if result["status"] == "complete":
        iteration["status"] = "checkpoint-non-promotable"
        iteration["validation_state"] = "source-validations-passed"
        iteration["next_boundary"] = "runtime-validation"
        iteration["promotion_eligible"] = False
    state["history"].append(
        {
            "stage": "request-continuation",
            "iteration": state["current_iteration"],
            "verified_boundary": result.get("verified_boundary"),
            "status": result["status"],
            "reconciled_from_completed_child": bool(
                result.get("reconciled_from_completed_child", False)
            ),
        }
    )
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "child": result,
    }


def validate_runtime_receipt(value: Mapping[str, Any]) -> None:
    if value.get("schema_version") != "1.0":
        raise WorkflowError("runtime receipt schema_version must be 1.0")
    if value.get("record_type") != "sage-e2e-zero-trust-runtime-receipt":
        raise WorkflowError("runtime receipt record_type is invalid")
    if value.get("status") != "pass":
        raise WorkflowError("runtime receipt is not passing")
    checks = value.get("checks")
    if not isinstance(checks, Mapping):
        raise WorkflowError("runtime receipt checks are missing")
    required = (
        "workload_ready",
        "origin_through_traefik_ready",
        "tunnel_ready",
        "connector_node_ha",
        "metrics_monitor_configured",
        "unauthenticated_access_denied",
        "authorized_mfa_access_verified",
        "privileged_surfaces_not_published",
    )
    failed = [name for name in required if checks.get(name) is not True]
    if failed:
        raise WorkflowError("runtime receipt is incomplete: " + ", ".join(failed))
    vignette = value.get("value_vignette")
    if not isinstance(vignette, Mapping):
        raise WorkflowError("runtime receipt SAGE value vignette is missing")
    required_vignette = (
        "architect_observation",
        "sage_finding",
        "prevented_action",
        "bounded_correction",
        "value_demonstrated",
    )
    for name in required_vignette:
        item = vignette.get(name)
        if not isinstance(item, str) or not item.strip():
            raise WorkflowError(
                f"runtime receipt SAGE value vignette is missing {name}"
            )


def record_runtime(
    state_path: Path,
    runtime_receipt: Path,
) -> Mapping[str, Any]:
    state = _load_parent(state_path)
    if state.get("status") != "source-git-complete":
        raise WorkflowError("source Git lifecycle must complete before runtime acceptance")
    receipt_path = runtime_receipt.expanduser().resolve()
    value = json.loads(receipt_path.read_text(encoding="utf-8"))
    validate_runtime_receipt(value)
    state["runtime_receipt"] = str(receipt_path)
    state["runtime_receipt_sha256"] = hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    state["status"] = "runtime-verified"
    iteration = _current_iteration(state)
    iteration["validation_state"] = "runtime-verified"
    iteration["status"] = "validated-candidate"
    iteration["next_boundary"] = "promotion"
    iteration["promotion_eligible"] = not bool(iteration.get("unresolved_findings"))
    state["promotion_eligible"] = iteration["promotion_eligible"]
    state["history"].append(
        {
            "stage": "runtime-acceptance",
            "iteration": state["current_iteration"],
            "receipt": str(receipt_path),
            "sha256": state["runtime_receipt_sha256"],
        }
    )
    _persist(state_path.expanduser().resolve(), state)
    return {"status": state["status"], "state": str(state_path.expanduser().resolve())}


def begin_intent_promotion(
    repo: Path,
    state_path: Path,
    expected_head: str,
    title: str,
    body: str,
) -> Mapping[str, Any]:
    state = _load_parent(state_path)
    if state.get("status") != "runtime-verified":
        raise WorkflowError("runtime outcome must be verified before promotion")
    iteration = _current_iteration(state)
    if state.get("promotion_eligible") is not True or iteration.get("unresolved_findings"):
        raise WorkflowError("current candidate remains non-promotable while unresolved findings exist")
    result = start_promotion(
        repo=repo.expanduser().resolve(),
        request=str(state["request"]),
        source_branch="feature/sage-e2e-zero-trust-viability",
        expected_head=expected_head,
        target_branch="main",
        title=title,
        body=body,
    )
    state["promotion_state"] = str(result["state"])
    state["status"] = "promotion-operator-review-required"
    state["history"].append(
        {"stage": "promotion-start", "promotion_state": str(result["state"])}
    )
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "child": result,
    }


def continue_intent_promotion(
    repo: Path,
    state_path: Path,
    operator_result: Path,
) -> Mapping[str, Any]:
    state = _load_parent(state_path)
    if state.get("status") != "promotion-operator-review-required":
        raise WorkflowError("intent state is not awaiting promotion continuation")
    result = continue_promotion(
        repo=repo.expanduser().resolve(),
        state_path=Path(str(state["promotion_state"])),
        operator_result_path=operator_result.expanduser().resolve(),
    )
    state["status"] = (
        "promotion-complete"
        if result["status"] == "complete"
        else "promotion-operator-review-required"
    )
    state["history"].append(
        {
            "stage": "promotion-continuation",
            "verified_boundary": result.get("verified_boundary"),
            "status": result["status"],
        }
    )
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "child": result,
    }
