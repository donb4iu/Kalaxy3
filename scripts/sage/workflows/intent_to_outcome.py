
"""Repository-owned SAGE intent-to-outcome orchestration front door."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from workflow import AtomicFileWriter, PrimitiveCatalog, WorkflowError
from workflows.checkpoint_promotion import continue_promotion, start_promotion
from workflows.request_execution import (
    continue_request,
    continue_request_from_routine_receipt,
    execute_request,
)
from workflows.request_planning import plan_request
from workflows.semantic_bootstrap import begin_bootstrap, continue_bootstrap

WORKFLOW_ID = "sage.intent-to-outcome"
WORKFLOW_VERSION = "0.1.0"
PRIMITIVES_USED = (
    "catalog.registry",
    "file.atomic-preserve-mode",
    "workflow.composition",
)
STATE_ROOT = Path("~/.local/state/kalaxy3/sage-intent-to-outcome").expanduser()


def _stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def _request_digest(request: str) -> str:
    return hashlib.sha256(request.encode("utf-8")).hexdigest()


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
    return value


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
        "contribution": str(contribution.expanduser().resolve()),
        "status": "architect-confirmation-required",
        "semantic_state": str(semantic["state"]),
        "request_execution_state": None,
        "runtime_receipt": None,
        "promotion_state": None,
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
    semantic = continue_bootstrap(
        resolved,
        Path(str(state["semantic_state"])),
        confirmation,
        actor,
        None,
        dispositions.expanduser().resolve(),
    )
    proposal_path = (
        Path("~/Downloads").expanduser()
        / ("sage-request-proposal-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip")
    )
    planned = plan_request(
        resolved,
        str(state["request"]),
        Path(str(semantic["planning_source"])),
        proposal_path,
    )
    execution = execute_request(
        resolved,
        str(state["request"]),
        Path(str(planned["proposal"])),
    )
    state["status"] = "request-operator-review-required"
    state["planning_source"] = str(semantic["planning_source"])
    state["planning_proposal"] = str(planned["proposal"])
    state["request_execution_state"] = str(execution["state"])
    state["history"].append(
        {
            "stage": "semantic-plan-execute",
            "planning_source": str(semantic["planning_source"]),
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


def adopt_request_execution(
    repo: Path,
    request: str,
    request_state: Path,
) -> Mapping[str, Any]:
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
    directory = _new_state_directory()
    state_path = directory / "intent-to-outcome-state.json"
    state = {
        "schema_version": "1.0",
        "record_type": "sage-intent-to-outcome-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "request": request,
        "request_sha256": _request_digest(request),
        "action_id": None,
        "contribution": None,
        "status": (
            "source-git-complete"
            if child.get("current_boundary") == "complete"
            else "request-operator-review-required"
        ),
        "semantic_state": None,
        "request_execution_state": str(request_state),
        "runtime_receipt": None,
        "promotion_state": None,
        "history": [
            {
                "stage": "one-time-bootstrap-adoption",
                "request_execution_state": str(request_state),
            }
        ],
    }
    _persist(state_path, state)
    return {"status": state["status"], "state": str(state_path)}


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
    if routine_receipt is not None:
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
    state["history"].append(
        {
            "stage": "request-continuation",
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
        "metrics_monitor_configured",
        "unauthenticated_access_denied",
        "authorized_mfa_access_verified",
        "privileged_surfaces_not_published",
    )
    failed = [name for name in required if checks.get(name) is not True]
    if failed:
        raise WorkflowError("runtime receipt is incomplete: " + ", ".join(failed))


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
    state["history"].append(
        {
            "stage": "runtime-acceptance",
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
