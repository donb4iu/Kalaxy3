
"""Repository-owned SAGE intent-to-outcome orchestration front door."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from workflow import AtomicFileWriter, PrimitiveCatalog, WorkflowError, load_improvement_action
from workflow.recovery import (
    governing_composition_digest,
    RECOVERY_CONSUMPTION_NAME,
    build_consumption_record,
    latest_matching_reentry,
    load_consumed_fingerprints,
)
from workflows.checkpoint_promotion import continue_promotion, start_promotion
from workflows.objective_execution import objective_execution_route_summary
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
from request_execution import load_proposal
from semantic_understanding import load_engineering_contribution
from sage_evidence_retrieval import (
    load_json as load_retrieval_json,
    reconsideration_summary,
    requires_contribution_refresh,
    retrieve as retrieve_evidence,
    validate_result as validate_retrieval_result,
    write_result as write_retrieval_result,
)

WORKFLOW_ID = "sage.intent-to-outcome"
WORKFLOW_VERSION = "0.4.4"
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
    "promotion-complete",
})
INFLIGHT_CANDIDATE_STATUSES = frozenset({
    "architect-confirmation-required",
    "planning-source-ready",
    "authority-review-required",
    "objective-path-decision-required",
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


def _parent_reentry_objective(action: Mapping[str, Any]) -> str | None:
    """Extract an explicitly named parent delivery re-entry objective from accepted intent."""

    action_id = str(action.get("action_id", ""))
    for criterion in action.get("acceptance_criteria", []):
        text = str(criterion)
        lowered = text.lower()
        if "parent delivery re-entry point" not in lowered:
            continue
        candidates = re.findall(r"SAGE-ACTION-\d{8}-\d{3}", text)
        for candidate in candidates:
            if candidate != action_id:
                return candidate
    return None


def _route_obligations(action: Mapping[str, Any]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    desired = action.get("desired_outcome")
    if isinstance(desired, str) and desired.strip():
        obligations.append({
            "obligation_id": "PO-OUTCOME-001",
            "kind": "outcome",
            "status": "remaining",
            "description": desired.strip(),
            "source": "accepted-action.desired_outcome",
        })
    for index, value in enumerate(action.get("acceptance_criteria", []), 1):
        obligations.append({
            "obligation_id": f"PO-AC-{index:03d}",
            "kind": "requirement",
            "status": "remaining",
            "description": str(value),
            "source": f"accepted-action.acceptance_criteria[{index - 1}]",
        })
    for index, value in enumerate(action.get("measurement_plan", []), 1):
        obligations.append({
            "obligation_id": f"PO-MEASURE-{index:03d}",
            "kind": "measurement",
            "status": "remaining",
            "description": str(value),
            "source": f"accepted-action.measurement_plan[{index - 1}]",
        })
    return obligations


def _route_alternatives(contribution_manifest: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    values = [] if contribution_manifest is None else list(contribution_manifest.get("alternatives", []))
    if not any("do nothing" in str(item).lower() or "do-nothing" in str(item).lower() for item in values):
        values.append("Do nothing: retain the current objective lifecycle without objective-route composition.")
    return [
        {
            "alternative_id": f"ALT-{index:03d}",
            "description": str(value),
            "risk": "unassessed",
            "reversibility": "unassessed",
            "expected_value": "unassessed",
            "time_to_evidence": "unassessed",
            "disposition": "pending-architect-or-planning-evaluation",
        }
        for index, value in enumerate(values, 1)
    ]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.expanduser().resolve().read_bytes()).hexdigest()




def implementation_local_source_scope_relation(
    prior_manifest: Mapping[str, Any],
    corrected_manifest: Mapping[str, Any],
) -> str:
    """
    Validate an implementation-local source set against the
    previously approved source envelope.

    The successor may narrow to a mode-compatible subset.
    Expansion or a mode change is material and fails closed.
    """

    def shape(
        manifest: Mapping[str, Any],
        label: str,
    ) -> tuple[tuple[str, str], ...]:
        values = manifest.get("source_files")
        if not isinstance(values, list):
            raise WorkflowError(
                f"{label} proposal source_files are invalid"
            )

        result: list[tuple[str, str]] = []

        for item in values:
            if not isinstance(item, Mapping):
                raise WorkflowError(
                    f"{label} proposal source file is invalid"
                )

            path = str(
                item.get("path", "")
            )
            mode = str(
                item.get("mode", "")
            )

            if not path or not mode:
                raise WorkflowError(
                    f"{label} proposal source file is incomplete"
                )

            result.append(
                (path, mode)
            )

        if len(result) != len(
            {path for path, _ in result}
        ):
            raise WorkflowError(
                f"{label} proposal source_files contain duplicates"
            )

        return tuple(result)

    prior_shape = shape(
        prior_manifest,
        "prior",
    )
    corrected_shape = shape(
        corrected_manifest,
        "corrected",
    )

    if not corrected_shape:
        raise WorkflowError(
            "implementation-local proposal has no source files"
        )

    prior_modes = dict(
        prior_shape
    )

    invalid = [
        f"{path}:{mode}"
        for path, mode in corrected_shape
        if (
            path not in prior_modes
            or prior_modes[path] != mode
        )
    ]

    if invalid:
        raise WorkflowError(
            "implementation-local proposal expanded the "
            "approved source-file envelope or changed modes: "
            + ", ".join(invalid)
        )

    if (
        len(corrected_shape) == len(prior_shape)
        and dict(corrected_shape) == dict(prior_shape)
    ):
        return "exact"

    return "subset"


def implementation_local_repository_rebind(
    prior_repository: Mapping[str, Any],
    corrected_repository: Mapping[str, Any],
) -> dict[str, Any]:
    """
    Validate repository provenance for a successor candidate.

    A new synchronized non-main feature branch is execution
    provenance, not a change to Architect-owned objective authority.
    """

    if (
        not isinstance(prior_repository, Mapping)
        or not isinstance(corrected_repository, Mapping)
    ):
        raise WorkflowError(
            "implementation-local proposal repository provenance "
            "is invalid"
        )

    prior_branch = str(
        prior_repository.get("branch", "")
    ).strip()
    corrected_branch = str(
        corrected_repository.get("branch", "")
    ).strip()

    prior_head = str(
        prior_repository.get("head", "")
    ).strip()
    corrected_head = str(
        corrected_repository.get("head", "")
    ).strip()

    if not prior_branch or not corrected_branch:
        raise WorkflowError(
            "implementation-local repository branch provenance "
            "is incomplete"
        )

    if corrected_branch == "main":
        raise WorkflowError(
            "implementation-local successor cannot bind to main"
        )

    for label, value in (
        ("prior", prior_head),
        ("corrected", corrected_head),
    ):
        if re.fullmatch(
            r"[0-9a-f]{40}",
            value,
        ) is None:
            raise WorkflowError(
                f"{label} implementation-local repository "
                "HEAD provenance is invalid"
            )

    return {
        "prior_branch": prior_branch,
        "corrected_branch": corrected_branch,
        "prior_head": prior_head,
        "corrected_head": corrected_head,
        "branch_rebound": (
            prior_branch != corrected_branch
        ),
    }


def _implementation_local_inherited_objective_decision(
    state_path: Path,
    state: Mapping[str, Any],
    prior_proposal_path: Path,
    corrected_proposal_path: Path,
    contribution_path: Path,
) -> Path:
    """Project one existing Architect path approval onto a verified local correction."""

    raw_decision_path = os.environ.get(
        "SAGE_OBJECTIVE_PATH_DECISION", ""
    ).strip()
    if not raw_decision_path:
        raise WorkflowError(
            "implementation-local continuation requires the existing "
            "SAGE_OBJECTIVE_PATH_DECISION approval source"
        )

    decision_source = Path(raw_decision_path).expanduser().resolve()
    try:
        decision = json.loads(
            decision_source.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(
            "existing objective-path decision is unreadable: "
            f"{decision_source}: {error}"
        ) from error
    if not isinstance(decision, dict):
        raise WorkflowError(
            "existing objective-path decision must be a JSON object"
        )

    request = str(state.get("request", ""))
    if not request:
        raise WorkflowError(
            "implementation-local continuation lost literal request"
        )
    if decision.get("request_sha256") != _request_digest(request):
        raise WorkflowError(
            "existing objective-path decision belongs to another request"
        )

    objective_id = str(
        state.get("objective_id")
        or state.get("action_id")
        or ""
    )
    if not objective_id:
        raise WorkflowError(
            "implementation-local continuation has no active objective id"
        )
    if decision.get("active_objective_id") != objective_id:
        raise WorkflowError(
            "existing objective-path decision belongs to another objective"
        )

    disposition = decision.get("architect_disposition")
    if (
        not isinstance(disposition, Mapping)
        or disposition.get("status") != "approved"
        or str(disposition.get("authority", "")).strip().lower()
        != "architect"
        or disposition.get("basis")
        != "operator-supplied-to-governed-execution"
    ):
        raise WorkflowError(
            "existing objective-path decision is not an Architect-approved "
            "governed execution decision"
        )

    prior = prior_proposal_path.expanduser().resolve()
    corrected = corrected_proposal_path.expanduser().resolve()
    if decision.get("proposal_sha256") != _file_sha256(prior):
        raise WorkflowError(
            "existing Architect decision no longer matches the prior "
            "approved proposal"
        )

    prior_bundle = load_proposal(prior, request)
    corrected_bundle = load_proposal(corrected, request)

    # Component/path selection is immutable across this implementation-local
    # correction. Only implementation bytes and their repository HEAD may move.
    immutable_manifest_fields = (
        "capabilities",
        "candidates",
        "new_primitive_required",
        "generated_paths",
        "reconcile_evidence_index",
        "validation_commands",
        "operator_plan",
    )
    changed = [
        field
        for field in immutable_manifest_fields
        if corrected_bundle.manifest.get(field)
        != prior_bundle.manifest.get(field)
    ]
    if changed:
        raise WorkflowError(
            "implementation-local proposal changed the approved component/path "
            "decision surface: "
            + ", ".join(changed)
        )

    prior_repository = prior_bundle.manifest.get(
        "repository"
    )
    corrected_repository = corrected_bundle.manifest.get(
        "repository"
    )

    repository_rebind = implementation_local_repository_rebind(
        prior_repository,
        corrected_repository,
    )

    scope_relation = implementation_local_source_scope_relation(
        prior_bundle.manifest,
        corrected_bundle.manifest,
    )

    reuse_marker = (
        "implementation-local-plan-reuse:"
        + str(prior_bundle.package_path)
    )
    evidence = corrected_bundle.manifest.get("evidence_references")
    if (
        not isinstance(evidence, list)
        or reuse_marker not in evidence
    ):
        raise WorkflowError(
            "corrected proposal lacks repository-owned prior-plan reuse lineage"
        )

    # Bind the corrected proposal payload to the exact implementation-local
    # engineering contribution supplied to this iteration.
    contribution = load_engineering_contribution(
        contribution_path.expanduser().resolve()
    )
    expected_payload = tuple(
        (item.path, item.sha256, f"{item.mode:04o}")
        for item in contribution.source_files
    )
    observed_payload = tuple(
        (
            str(item.get("path", "")),
            str(item.get("sha256", "")),
            str(item.get("mode", "")),
        )
        for item in corrected_bundle.manifest.get("source_files", [])
        if isinstance(item, Mapping)
    )
    if observed_payload != expected_payload:
        raise WorkflowError(
            "corrected proposal payload does not exactly match the "
            "implementation-local contribution"
        )

    corrected_sha = _file_sha256(corrected)
    inherited = json.loads(json.dumps(decision))
    inherited["proposal_sha256"] = corrected_sha

    iteration_number = int(state.get("current_iteration", 0) or 0)
    destination = (
        state_path.expanduser().resolve().parent
        / f"objective-path-decision-iteration-{iteration_number:03d}.json"
    )
    if destination.exists():
        existing = json.loads(
            destination.read_text(encoding="utf-8")
        )
        if existing != inherited:
            raise WorkflowError(
                "implementation-local inherited decision already exists with "
                "different content"
            )
    else:
        _persist(destination, inherited)

    state.setdefault("history", []).append(
        {
            "stage": "implementation-local-objective-path-approval-inherited",
            "iteration": iteration_number,
            "architect_decision_source": str(decision_source),
            "architect_decision_source_sha256": _file_sha256(
                decision_source
            ),
            "prior_planning_proposal": str(prior),
            "prior_planning_proposal_sha256": _file_sha256(prior),
            "corrected_planning_proposal": str(corrected),
            "corrected_planning_proposal_sha256": corrected_sha,
            "source_scope_relation": scope_relation,
            "prior_repository_branch": repository_rebind["prior_branch"],
            "corrected_repository_branch": repository_rebind["corrected_branch"],
            "repository_branch_rebound": repository_rebind["branch_rebound"],
            "material_decision_surface_changed": False,
            "approval_reused": True,
        }
    )
    return destination


def _evidence_route_state(state: Mapping[str, Any]) -> dict[str, Any]:
    value = state.get("evidence_reconsideration")
    if not isinstance(value, Mapping):
        return {
            "status": "not-triggered",
            "candidate_count": 0,
            "assessed_count": 0,
            "assessment_coverage": 1.0,
            "alternative_set_change_count": 0,
            "augmentation_count": 0,
            "additional_acceptance_criteria_count": 0,
            "requires_revalidation_count": 0,
            "reconsideration_trigger_count": 0,
        }
    summary = value.get("summary")
    if isinstance(summary, Mapping):
        return {"status": str(value.get("status", "finalized")), **dict(summary)}
    count = int(value.get("candidate_count", 0) or 0)
    return {
        "status": str(value.get("status", "pending")),
        "candidate_count": count,
        "assessed_count": 0,
        "assessment_coverage": 0.0 if count else 1.0,
        "alternative_set_change_count": 0,
        "augmentation_count": 0,
        "additional_acceptance_criteria_count": 0,
        "requires_revalidation_count": 0,
        "reconsideration_trigger_count": 0,
    }


def _generation_route_state(state: Mapping[str, Any]) -> dict[str, Any]:
    generations = [
        dict(item)
        for item in state.get("implementation_generations", [])
        if isinstance(item, Mapping)
    ]
    return {
        "generation_count": len(generations),
        "current_generation": generations[-1] if generations else None,
        "history": generations,
    }


def _promotion_source_branch(state: Mapping[str, Any]) -> str:
    semantic_state = state.get("semantic_state")
    if isinstance(semantic_state, str) and semantic_state:
        path = Path(semantic_state).expanduser().resolve()
        try:
            child = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise WorkflowError(f"semantic state is unreadable for promotion source resolution: {error}") from error
        repository = child.get("repository")
        if isinstance(repository, Mapping):
            branch = repository.get("branch")
            if isinstance(branch, str) and branch and branch != "main":
                return branch
    raise WorkflowError(
        "promotion source branch is not preserved in governed semantic lineage"
    )


def build_objective_route(
    action: Mapping[str, Any],
    state: Mapping[str, Any],
    contribution_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a conservative machine-readable route without claiming unearned assurance."""

    current = _current_iteration(state)
    evidence = []
    for field in (
        "semantic_state",
        "planning_source",
        "planning_proposal",
        "request_execution_state",
        "runtime_receipt",
        "promotion_state",
    ):
        value = state.get(field)
        if isinstance(value, str) and value:
            evidence.append({"kind": field, "reference": value})
    findings = [str(item) for item in current.get("unresolved_findings", [])]
    deferred_debt = [
        item for item in state.get("deferred_debt", []) if isinstance(item, Mapping)
    ]
    runtime_mapped = bool(state.get("runtime_receipt"))
    delivery_applicability = state.get("delivery_applicability")
    if not isinstance(delivery_applicability, Mapping):
        delivery_applicability = {}
    evidence_route = _evidence_route_state(state)
    generation_route = _generation_route_state(state)
    source_validated = current.get("validation_state") in {
        "source-validations-passed",
        "runtime-verified",
    }
    return {
        "schema_version": "1.0",
        "record_type": "sage-objective-route",
        "objective_id": state.get("objective_id") or state.get("action_id") or state.get("request_sha256"),
        "parent_objective_id": _parent_reentry_objective(action),
        "status": "active",
        "remaining_obligations": _route_obligations(action),
        "current_evidence": evidence,
        "dependencies": [
            "accepted-action authority",
            "confirmed semantic/planning lineage when present",
            "repository-owned request/Git/runtime/promotion compositions",
            "contextual evidence reconsideration before semantic commitment when retrieval finds relevant prior experience",
        ],
        "alternatives": _route_alternatives(contribution_manifest),
        "selected_candidate": {
            "iteration": current.get("iteration"),
            "candidate_head": current.get("candidate_head"),
            "status": current.get("status"),
            "selection_status": "current-governed-candidate-not-objective-completion",
        },
        "next_governed_boundary": current.get("next_boundary"),
        "reentry_point": {
            "objective_id": _parent_reentry_objective(action),
            "boundary": current.get("next_boundary"),
        },
        "limitations": [
            {
                "description": item,
                "disposition": "block-dependent-activity-until-dispositioned",
                "risk": "unassessed",
                "detectability": "observed-by-current-validation",
                "reversibility": "unassessed",
                "recovery_cost": "unassessed",
                "reconsideration_trigger": "before dependent objective work or promotion",
            }
            for item in findings
        ],
        "deferred_debt": deferred_debt,
        "evidence_reconsideration": evidence_route,
        "implementation_generation_lineage": generation_route,
        "assurance": {
            "source_validation_evidence": source_validated,
            "runtime_evidence_mapped": runtime_mapped,
            "bdd_requirement_coverage": "unassessed",
            "uncovered_or_weak_obligations": [
                item["obligation_id"] for item in _route_obligations(action)
            ],
        },
        "integration_state": {
            "canonical_integration_eligibility": "unassessed",
            "capability_validation": current.get("validation_state"),
            "runtime_promotion_eligibility": bool(current.get("promotion_eligible")),
            "runtime_applicability": (
                delivery_applicability.get(
                    "runtime_validation",
                    {},
                ).get("applicability")
                if isinstance(
                    delivery_applicability.get("runtime_validation"),
                    Mapping,
                )
                else "required-unless-dispositioned"
            ),
            "promotion_applicability": (
                delivery_applicability.get(
                    "promotion",
                    {},
                ).get("applicability")
                if isinstance(
                    delivery_applicability.get("promotion"),
                    Mapping,
                )
                else "required-unless-dispositioned"
            ),
            "objective_completion": state.get("status") == "promotion-complete",
        },
        "objective_execution": objective_execution_route_summary(state),
        "delivery_applicability": delivery_applicability,
        "guardrail_collaboration_feedback": {
            "status": "measurement-contract-present-values-may-be-unavailable",
            "activations": None,
            "prevented_defects": None,
            "false_positives": None,
            "break_glass_uses": None,
            "manual_corrections": None,
            "unplanned_recovery_steps": None,
            "operator_boundaries": None,
            "interpretation_burden": None,
            "evidence_retrieval_candidates": evidence_route["candidate_count"],
            "evidence_assessment_coverage": evidence_route["assessment_coverage"],
            "prior_capability_alternative_changes": evidence_route["alternative_set_change_count"],
            "evidence_revalidation_needs": evidence_route["requires_revalidation_count"],
            "reconsideration_triggers": evidence_route["reconsideration_trigger_count"],
        },
    }



def objective_route_snapshot(repo: Path, state_path: Path) -> Mapping[str, Any]:
    """Render the current objective route, including legacy states, without mutation."""

    state = _load_parent(state_path)
    action: Mapping[str, Any] = {
        "action_id": state.get("action_id"),
        "desired_outcome": "",
        "acceptance_criteria": [],
        "measurement_plan": [],
    }
    if state.get("action_id"):
        action = load_improvement_action(repo.expanduser().resolve(), str(state["action_id"]))
    contribution_manifest = None
    contribution_path = state.get("contribution")
    if isinstance(contribution_path, str) and contribution_path:
        path = Path(contribution_path).expanduser().resolve()
        if path.is_file():
            contribution_manifest = load_engineering_contribution(path).manifest
    return build_objective_route(action, state, contribution_manifest)


def _refresh_objective_route(repo: Path, state: dict[str, Any]) -> None:
    action: Mapping[str, Any] = {
        "action_id": state.get("action_id"),
        "desired_outcome": "",
        "acceptance_criteria": [],
        "measurement_plan": [],
    }
    if state.get("action_id"):
        action = load_improvement_action(repo.expanduser().resolve(), str(state["action_id"]))
    contribution_manifest = None
    contribution_path = state.get("contribution")
    if isinstance(contribution_path, str) and contribution_path:
        path = Path(contribution_path).expanduser().resolve()
        if path.is_file():
            contribution_manifest = load_engineering_contribution(path).manifest
    state["objective_route"] = build_objective_route(action, state, contribution_manifest)



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
    if "implementation_generations" not in state:
        state["implementation_generations"] = []
    if "evidence_reconsideration" not in state:
        state["evidence_reconsideration"] = None
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


def _new_intent_state(
    *,
    action_id: str,
    request: str,
    contribution: Path,
    status: str,
    semantic_state: str | None,
    iteration_status: str,
    next_boundary: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.1",
        "record_type": "sage-intent-to-outcome-state",
        "workflow_id": WORKFLOW_ID,
        "workflow_version": WORKFLOW_VERSION,
        "request": request,
        "request_sha256": _request_digest(request),
        "action_id": action_id,
        "objective_id": action_id,
        "initial_contribution": str(contribution.expanduser().resolve()),
        "contribution": str(contribution.expanduser().resolve()),
        "status": status,
        "semantic_state": semantic_state,
        "request_execution_state": None,
        "runtime_receipt": None,
        "promotion_state": None,
        "evidence_reconsideration": None,
        "implementation_generations": [],
        "current_iteration": 1,
        "iterations": [
            _iteration_record(
                1,
                parent_checkpoint=None,
                candidate_head=None,
                trigger="initial governed objective candidate",
                affected_obligations=[],
                status=iteration_status,
                next_boundary=next_boundary,
            )
        ],
        "promotion_eligible": False,
        "history": [],
    }


def begin_intent(
    repo: Path,
    action_id: str,
    request: str,
    contribution: Path,
) -> Mapping[str, Any]:
    """Start with intent-first contribution, then require contextual evidence reconsideration."""
    resolved = repo.expanduser().resolve()
    PrimitiveCatalog.load(resolved / "sage-workflow-primitives.json").require(
        PRIMITIVES_USED
    )
    contribution_path = contribution.expanduser().resolve()
    initial = load_engineering_contribution(contribution_path)
    action = load_improvement_action(resolved, action_id)
    if action.get("current_status") != "accepted":
        raise WorkflowError(f"{action_id} must be accepted before intent-to-outcome start")

    directory = _new_state_directory()
    state_path = directory / "intent-to-outcome-state.json"
    policy_path = resolved / "sage-evidence-retrieval-policy.json"
    retrieval = retrieve_evidence(
        repo=resolved,
        policy_path=policy_path,
        request=request,
    )
    retrieval_path = directory / "evidence-retrieval.json"
    write_retrieval_result(retrieval_path, retrieval)

    if retrieval.get("results"):
        state = _new_intent_state(
            action_id=action_id,
            request=request,
            contribution=contribution_path,
            status="evidence-reconsideration-required",
            semantic_state=None,
            iteration_status="evidence-reconsideration",
            next_boundary="evidence-reconsideration",
        )
        state["evidence_reconsideration"] = {
            "status": "pending",
            "retrieval": str(retrieval_path),
            "retrieval_sha256": _file_sha256(retrieval_path),
            "retrieval_basis_sha256": retrieval.get("retrieval_basis_sha256"),
            "candidate_count": len(retrieval["results"]),
            "assessment": None,
            "assessment_sha256": None,
            "summary": None,
        }
        state["history"].append({
            "stage": "evidence-retrieval",
            "iteration": 1,
            "initial_contribution_sha256": initial.package_sha256,
            "retrieval": str(retrieval_path),
            "retrieval_basis_sha256": retrieval.get("retrieval_basis_sha256"),
            "candidate_count": len(retrieval["results"]),
        })
        _refresh_objective_route(resolved, state)
        _persist(state_path, state)
        return {
            "status": state["status"],
            "state": str(state_path),
            "evidence_retrieval": str(retrieval_path),
            "retrieval_basis_sha256": retrieval.get("retrieval_basis_sha256"),
            "candidate_count": len(retrieval["results"]),
            "next_boundary": "LLM must finalize every candidate applicability/value assessment and refresh the contribution when evidence materially changes it.",
        }

    semantic = begin_bootstrap(
        resolved, action_id, request, contribution_path
    )
    state = _new_intent_state(
        action_id=action_id,
        request=request,
        contribution=contribution_path,
        status="architect-confirmation-required",
        semantic_state=str(semantic["state"]),
        iteration_status="semantic-confirmation",
        next_boundary="semantic-confirmation",
    )
    state["evidence_reconsideration"] = {
        "status": "not-triggered",
        "retrieval": str(retrieval_path),
        "retrieval_sha256": _file_sha256(retrieval_path),
        "retrieval_basis_sha256": retrieval.get("retrieval_basis_sha256"),
        "candidate_count": 0,
        "assessment": None,
        "assessment_sha256": None,
        "summary": reconsideration_summary(retrieval),
    }
    state["history"].append({
        "stage": "evidence-retrieval-no-relevant-candidates",
        "iteration": 1,
        "retrieval": str(retrieval_path),
    })
    _refresh_objective_route(resolved, state)
    _persist(state_path, state)
    return {
        "status": state["status"],
        "state": str(state_path),
        "semantic_understanding": semantic["semantic_understanding"],
        "semantic_understanding_sha256": semantic["semantic_understanding_sha256"],
        "architect_dispositions": semantic["architect_dispositions"],
        "confirmation_command": semantic["confirmation_command"],
    }


def reconsider_intent(
    repo: Path,
    state_path: Path,
    evidence_reconsideration: Path,
    contribution: Path,
) -> Mapping[str, Any]:
    """Bind finalized LLM evidence assessment and enter semantic confirmation."""
    resolved = repo.expanduser().resolve()
    state = _load_parent(state_path)
    if state.get("status") != "evidence-reconsideration-required":
        raise WorkflowError("intent state is not awaiting evidence reconsideration")
    gate = state.get("evidence_reconsideration")
    if not isinstance(gate, Mapping):
        raise WorkflowError("intent state lacks evidence-reconsideration lineage")
    raw_path = Path(str(gate.get("retrieval", ""))).expanduser().resolve()
    if not raw_path.is_file() or _file_sha256(raw_path) != gate.get("retrieval_sha256"):
        raise WorkflowError("stored evidence retrieval changed before reconsideration")
    raw = load_retrieval_json(raw_path)
    if raw.get("schema_version") != "1.1":
        raise WorkflowError("intent evidence reconsideration requires retrieval result schema v1.1")

    assessment_path = evidence_reconsideration.expanduser().resolve()
    assessed = load_retrieval_json(assessment_path)
    if assessed.get("schema_version") != "1.1":
        raise WorkflowError("finalized evidence reconsideration requires retrieval result schema v1.1")
    policy = load_retrieval_json(resolved / "sage-evidence-retrieval-policy.json")
    validate_retrieval_result(assessed, policy, require_final=True)
    if assessed.get("request") != state.get("request"):
        raise WorkflowError("evidence reconsideration does not match the literal request")
    if assessed.get("retrieval_basis_sha256") != raw.get("retrieval_basis_sha256"):
        raise WorkflowError("evidence reconsideration does not match the stored retrieval basis")

    initial = load_engineering_contribution(
        Path(str(state["initial_contribution"])).expanduser().resolve()
    )
    refreshed = load_engineering_contribution(contribution.expanduser().resolve())
    if requires_contribution_refresh(assessed) and refreshed.package_sha256 == initial.package_sha256:
        raise WorkflowError(
            "material evidence reconsideration requires a refreshed engineering contribution"
        )

    semantic = begin_bootstrap(
        resolved,
        str(state["action_id"]),
        str(state["request"]),
        refreshed.package_path,
        assessment_path,
    )
    summary = reconsideration_summary(assessed)
    state["contribution"] = str(refreshed.package_path)
    state["semantic_state"] = str(semantic["state"])
    state["status"] = "architect-confirmation-required"
    state["evidence_reconsideration"] = {
        **dict(gate),
        "status": "finalized",
        "assessment": str(assessment_path),
        "assessment_sha256": _file_sha256(assessment_path),
        "summary": summary,
    }
    iteration = _current_iteration(state)
    iteration["status"] = "semantic-confirmation"
    iteration["next_boundary"] = "semantic-confirmation"
    state["history"].append({
        "stage": "evidence-reconsideration-complete",
        "iteration": state["current_iteration"],
        "retrieval_basis_sha256": assessed.get("retrieval_basis_sha256"),
        "assessment": str(assessment_path),
        "assessment_sha256": state["evidence_reconsideration"]["assessment_sha256"],
        "initial_contribution_sha256": initial.package_sha256,
        "refreshed_contribution_sha256": refreshed.package_sha256,
        "material_refresh_required": requires_contribution_refresh(assessed),
        "summary": summary,
    })
    _refresh_objective_route(resolved, state)
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "semantic_understanding": semantic["semantic_understanding"],
        "semantic_understanding_sha256": semantic["semantic_understanding_sha256"],
        "architect_dispositions": semantic["architect_dispositions"],
        "confirmation_command": semantic["confirmation_command"],
        "evidence_reconsideration_summary": summary,
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
    _refresh_objective_route(resolved, state)
    _persist(state_path.expanduser().resolve(), state)
    planned = plan_request(
        resolved,
        str(state["request"]),
        Path(semantic_source),
        proposal_path,
    )
    return _pause_for_objective_path_decision(
        resolved,
        state_path,
        state,
        planning_source=semantic_source,
        planned=planned,
        history_stage="semantic-plan-ready-for-objective-path-decision",
    )


def _pause_for_objective_path_decision(
    repo: Path,
    state_path: Path,
    state: dict[str, Any],
    *,
    planning_source: str,
    planned: Mapping[str, Any],
    history_stage: str,
) -> Mapping[str, Any]:
    """Persist the exact proposal before the Architect authorizes request mutation."""

    proposal = Path(str(planned["proposal"])).expanduser().resolve()
    if not proposal.is_file():
        raise WorkflowError(f"planned request proposal is missing: {proposal}")
    proposal_sha256 = hashlib.sha256(proposal.read_bytes()).hexdigest()
    state["planning_source"] = planning_source
    state["planning_proposal"] = str(proposal)
    state["request_execution_state"] = None
    state["status"] = "objective-path-decision-required"
    iteration = _current_iteration(state)
    iteration["status"] = "objective-path-decision"
    iteration["next_boundary"] = "objective-path-decision"
    state["history"].append({
        "stage": history_stage,
        "iteration": state["current_iteration"],
        "planning_source": planning_source,
        "planning_proposal": str(proposal),
        "planning_proposal_sha256": proposal_sha256,
    })
    _refresh_objective_route(repo, state)
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "planning_proposal": str(proposal),
        "planning_proposal_sha256": proposal_sha256,
        "next_boundary": "objective-path-decision",
    }


def continue_planned_request(
    repo: Path,
    state_path: Path,
) -> Mapping[str, Any]:
    """Execute one persisted exact proposal after Architect objective-path approval."""

    resolved = repo.expanduser().resolve()
    state = _load_parent(state_path)
    if state.get("status") != "objective-path-decision-required":
        raise WorkflowError(
            "intent state is not awaiting objective-path decision"
        )
    proposal_value = state.get("planning_proposal")
    if not isinstance(proposal_value, str) or not proposal_value:
        raise WorkflowError(
            "objective-path continuation has no planning proposal"
        )
    proposal = Path(proposal_value).expanduser().resolve()
    if not proposal.is_file():
        raise WorkflowError(
            f"objective-path planning proposal is missing: {proposal}"
        )
    iteration = _current_iteration(state)
    if (
        iteration.get("status") != "objective-path-decision"
        or iteration.get("next_boundary")
        != "objective-path-decision"
    ):
        raise WorkflowError(
            "objective-path continuation iteration boundary is invalid"
        )

    execution = execute_request(
        resolved,
        str(state["request"]),
        proposal,
    )
    proposal_sha256 = hashlib.sha256(
        proposal.read_bytes()
    ).hexdigest()

    if execution.get("status") == "already-realized":
        candidate_head = execution.get("candidate_head")
        if (
            not isinstance(candidate_head, str)
            or re.fullmatch(r"[0-9a-f]{40}", candidate_head) is None
        ):
            raise WorkflowError(
                "already-realized request execution lost candidate HEAD"
            )
        bundle = load_proposal(
            proposal,
            str(state["request"]),
        )
        if candidate_head != str(
            bundle.manifest["repository"]["head"]
        ):
            raise WorkflowError(
                "already-realized candidate HEAD differs from proposal authority"
            )

        state["request_execution_state"] = None
        state["status"] = "source-git-complete"
        iteration["candidate_head"] = candidate_head
        iteration["status"] = "checkpoint-non-promotable"
        iteration["validation_state"] = "source-validations-passed"
        iteration["next_boundary"] = "runtime-validation"
        iteration["promotion_eligible"] = False
        state["promotion_eligible"] = False
        state["history"].append(
            {
                "stage": (
                    "objective-path-decision-consumed-already-realized"
                ),
                "iteration": state["current_iteration"],
                "planning_proposal": str(proposal),
                "planning_proposal_sha256": proposal_sha256,
                "candidate_head": candidate_head,
                "realization_receipt": execution.get(
                    "realization_receipt"
                ),
                "request_execution_closeout": execution.get(
                    "closeout"
                ),
                "repository_mutation": False,
                "git_mutation": False,
            }
        )
        _refresh_objective_route(resolved, state)
        _persist(state_path.expanduser().resolve(), state)
        return {
            "status": state["status"],
            "state": str(state_path.expanduser().resolve()),
            "request_execution": execution,
            "candidate_head": candidate_head,
        }

    state["request_execution_state"] = str(execution["state"])
    state["status"] = "request-operator-review-required"
    iteration["status"] = "request-execution"
    iteration["next_boundary"] = "operator-review"
    state["history"].append(
        {
            "stage": "objective-path-decision-consumed",
            "iteration": state["current_iteration"],
            "planning_proposal": str(proposal),
            "planning_proposal_sha256": proposal_sha256,
            "request_execution_state": str(execution["state"]),
        }
    )
    _refresh_objective_route(resolved, state)
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
    _refresh_objective_route(resolved, state)
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
    prior_planning_proposal = state.get("planning_proposal")
    entry_mode = candidate_iteration_entry_mode(str(state.get("status", "")))
    if (
        reentry_boundary == "implementation-local"
        and not os.environ.get("SAGE_OBJECTIVE_PATH_DECISION", "").strip()
    ):
        raise WorkflowError(
            "implementation-local re-entry requires the existing "
            "SAGE_OBJECTIVE_PATH_DECISION approval source"
        )
    recovery_consumption = _consume_recovery_reentry(
        resolved,
        state_path,
        state,
        reentry_boundary,
    )
    prior = _current_iteration(state)

    promoted_predecessor = (
        str(state.get("status", ""))
        == "promotion-complete"
    )

    if promoted_predecessor:
        if entry_mode != "durable-checkpoint":
            raise WorkflowError(
                "promoted implementation generation was not "
                "classified as a durable predecessor"
            )

        # Preserve the predecessor iteration exactly as the
        # successfully promoted historical generation.  The new
        # trigger belongs to the successor iteration, not to the
        # already-promoted candidate.
        state.setdefault("history", []).append(
            {
                "stage": "promoted-generation-successor-start",
                "prior_iteration": state.get(
                    "current_iteration"
                ),
                "prior_iteration_status": prior.get(
                    "status"
                ),
                "prior_candidate_head": prior.get(
                    "candidate_head"
                ),
                "prior_promotion_eligible": prior.get(
                    "promotion_eligible"
                ),
                "prior_promotion_state": state.get(
                    "promotion_state"
                ),
                "trigger": trigger.strip(),
                "historical_predecessor_preserved": True,
            }
        )
    else:
        prior["promotion_eligible"] = False

        findings = prior.setdefault(
            "unresolved_findings",
            [],
        )

        if trigger.strip() not in findings:
            findings.append(
                trigger.strip()
            )

        if entry_mode == "durable-checkpoint":
            prior["status"] = (
                "checkpoint-non-promotable"
            )
        else:
            prior["status"] = (
                "superseded-in-progress"
            )
            prior["next_boundary"] = (
                "candidate-iteration"
            )
            prior.setdefault(
                "learning",
                [],
            ).append(
                {
                    "kind": "candidate-union",
                    "observation": (
                        "Validation exposed another related "
                        "correction before the candidate reached "
                        "a durable checkpoint; the successor "
                        "accumulates the unfinished candidate "
                        "rather than requiring separate promotion."
                    ),
                }
            )

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
    state["delivery_applicability"] = None
    state["contribution"] = str(contribution.expanduser().resolve())

    resolved = repo.expanduser().resolve()
    _refresh_objective_route(resolved, state)
    _persist(state_path.expanduser().resolve(), state)
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
        _refresh_objective_route(resolved, state)
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
        _refresh_objective_route(resolved, state)
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
    state["history"].append({
        "stage": "candidate-iteration-plan-ready",
        "iteration": number,
        "reentry_boundary": reentry_boundary,
        "trigger": trigger.strip(),
        "approved_gap_set": (
            str(approved_gap_set.expanduser().resolve())
            if approved_gap_set is not None
            else None
        ),
    })

    if reentry_boundary == "implementation-local":
        if not isinstance(prior_planning_proposal, str) or not prior_planning_proposal:
            raise WorkflowError(
                "implementation-local re-entry lost the prior approved proposal"
            )
        corrected_proposal = Path(str(planned["proposal"])).expanduser().resolve()
        validate_reusable_plan_lineage(
            str(state["request"]),
            new_source,
            corrected_proposal,
        )
        inherited_decision = _implementation_local_inherited_objective_decision(
            state_path,
            state,
            Path(prior_planning_proposal),
            corrected_proposal,
            contribution,
        )
        _pause_for_objective_path_decision(
            resolved,
            state_path,
            state,
            planning_source=str(new_source),
            planned=planned,
            history_stage=(
                "candidate-iteration-ready-for-objective-path-decision"
            ),
        )
        prior_environment = os.environ.get(
            "SAGE_OBJECTIVE_PATH_DECISION"
        )
        os.environ["SAGE_OBJECTIVE_PATH_DECISION"] = str(
            inherited_decision
        )
        try:
            return continue_planned_request(
                resolved,
                state_path,
            )
        finally:
            if prior_environment is None:
                os.environ.pop(
                    "SAGE_OBJECTIVE_PATH_DECISION",
                    None,
                )
            else:
                os.environ[
                    "SAGE_OBJECTIVE_PATH_DECISION"
                ] = prior_environment

    return _pause_for_objective_path_decision(
        resolved,
        state_path,
        state,
        planning_source=str(new_source),
        planned=planned,
        history_stage="candidate-iteration-ready-for-objective-path-decision",
    )



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
    receipt = _load_json_object(canonical_receipt, "completed child routine receipt")
    candidate_head = receipt.get("commit")
    if not isinstance(candidate_head, str) or not candidate_head:
        raise WorkflowError("completed child routine receipt has no candidate commit")

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
        "candidate_head": candidate_head,
        **evidence,
    }



def reconcile_stale_parent_completed_request_child(
    repo: Path,
    state_path: Path,
    child_state_path: Path,
    planning_source: Path,
    routine_receipt: Path,
) -> Mapping[str, Any]:
    # Bounded recovery for a completed request child whose parent persistence
    # was interrupted before request lineage was recorded.
    resolved = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    child_state_path = child_state_path.expanduser().resolve()
    planning_source = planning_source.expanduser().resolve()
    routine_receipt = routine_receipt.expanduser().resolve()

    state = _load_parent(state_path)
    if state.get("status") != "planning-source-ready":
        raise WorkflowError(
            "stale-parent completed-child reconciliation requires planning-source-ready parent"
        )
    if state.get("request_execution_state") is not None:
        raise WorkflowError(
            "stale-parent completed-child reconciliation refuses an existing request child pointer"
        )
    if state.get("planning_proposal") is not None:
        raise WorkflowError(
            "stale-parent completed-child reconciliation refuses an existing planning proposal"
        )

    iteration = _current_iteration(state)
    if (
        iteration.get("status") != "planning"
        or iteration.get("validation_state") != "pending"
        or iteration.get("next_boundary") != "planning"
    ):
        raise WorkflowError(
            "stale-parent completed-child reconciliation requires untouched planning iteration"
        )

    child = _load_json_object(child_state_path, "completed request child state")
    if child.get("record_type") != "sage-request-execution-state":
        raise WorkflowError("completed request child state type is invalid")
    if child.get("request_sha256") != state.get("request_sha256"):
        raise WorkflowError("completed request child does not match parent literal request")

    proposal_value = child.get("proposal_package")
    proposal_sha256 = child.get("proposal_package_sha256")
    if not isinstance(proposal_value, str) or not proposal_value:
        raise WorkflowError("completed request child has no planning proposal lineage")
    if not isinstance(proposal_sha256, str) or not proposal_sha256:
        raise WorkflowError("completed request child has no planning proposal digest")
    proposal_path = Path(proposal_value).expanduser().resolve()
    if not proposal_path.is_file():
        raise WorkflowError(f"completed child planning proposal is missing: {proposal_path}")
    observed_proposal_sha256 = hashlib.sha256(proposal_path.read_bytes()).hexdigest()
    if observed_proposal_sha256 != proposal_sha256:
        raise WorkflowError(
            "completed child planning proposal digest no longer matches request state"
        )

    request = state.get("request")
    if not isinstance(request, str) or not request:
        raise WorkflowError("intent parent literal request is missing")
    lineage = validate_reusable_plan_lineage(request, planning_source, proposal_path)

    result = reconcile_completed_request_child(
        state,
        child_state_path,
        routine_receipt=routine_receipt,
    )

    candidate_head = result.get("candidate_head")
    if not isinstance(candidate_head, str) or not candidate_head:
        raise WorkflowError("completed child reconciliation did not preserve the candidate commit")

    prior_planning_source = state.get("planning_source")
    state["planning_source"] = lineage["planning_source"]
    state["planning_proposal"] = lineage["planning_proposal"]
    state["request_execution_state"] = str(child_state_path)
    state["status"] = "source-git-complete"

    iteration["candidate_head"] = candidate_head
    iteration["status"] = "checkpoint-non-promotable"
    iteration["validation_state"] = "source-validations-passed"
    iteration["next_boundary"] = "runtime-validation"
    iteration["promotion_eligible"] = False

    state["history"].append(
        {
            "stage": "completed-request-child-reconciliation",
            "iteration": state["current_iteration"],
            "request_execution_state": str(child_state_path),
            "prior_planning_source": prior_planning_source,
            "planning_source": lineage["planning_source"],
            "planning_proposal": lineage["planning_proposal"],
            "candidate_head": candidate_head,
            "verified_boundary": result.get("verified_boundary"),
            "reconciled_from_completed_child": True,
            "routine_receipt_sha256": result.get("routine_receipt_sha256"),
        }
    )
    _refresh_objective_route(resolved, state)
    _persist(state_path, state)
    return {
        "status": state["status"],
        "state": str(state_path),
        "child": result,
        "planning_source": lineage["planning_source"],
        "planning_proposal": lineage["planning_proposal"],
        "candidate_head": candidate_head,
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
        if result.get("reconciled_from_completed_child") is True:
            candidate_head = result.get("candidate_head")
            if not isinstance(candidate_head, str) or not candidate_head:
                raise WorkflowError("completed child reconciliation did not preserve the candidate commit")
            iteration["candidate_head"] = candidate_head
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
    _refresh_objective_route(repo.expanduser().resolve(), state)
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "child": result,
    }




def _runtime_not_applicable_promotion_ready(
    state: Mapping[str, Any],
    iteration: Mapping[str, Any],
) -> bool:
    disposition = state.get("delivery_applicability")
    if not isinstance(disposition, Mapping):
        return False

    runtime = disposition.get("runtime_validation")
    promotion = disposition.get("promotion")
    if not isinstance(runtime, Mapping) or not isinstance(promotion, Mapping):
        return False

    return (
        runtime.get("applicability") == "not-applicable-to-bounded-slice"
        and runtime.get("status") == "not-evaluated"
        and str(runtime.get("actor", "")).strip().lower() == "architect"
        and promotion.get("applicability") == "applicable"
        and promotion.get("status") == "pending"
        and str(promotion.get("actor", "")).strip().lower() == "architect"
        and state.get("runtime_receipt") is None
        and iteration.get("validation_state") == "source-validations-passed"
        and not bool(iteration.get("unresolved_findings"))
    )


def record_runtime_applicability_for_promotion(
    repo: Path,
    state_path: Path,
    *,
    reason: str,
    actor: str,
) -> Mapping[str, Any]:
    """Record runtime N/A while retaining governed checkpoint promotion."""

    resolved = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    state = _load_parent(state_path)

    if state.get("status") != "source-git-complete":
        raise WorkflowError(
            "runtime applicability disposition requires source-git-complete"
        )
    if state.get("runtime_receipt") is not None:
        raise WorkflowError(
            "runtime applicability disposition cannot replace runtime evidence"
        )
    if state.get("promotion_state") is not None:
        raise WorkflowError(
            "runtime applicability disposition cannot replace active promotion"
        )
    if state.get("delivery_applicability") is not None:
        raise WorkflowError(
            "runtime applicability disposition has already been recorded"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise WorkflowError(
            "runtime applicability disposition requires an explicit rationale"
        )
    if not isinstance(actor, str) or actor.strip().lower() != "architect":
        raise WorkflowError(
            "runtime applicability disposition requires explicit Architect authority"
        )

    action: Mapping[str, Any] = {
        "action_id": state.get("action_id"),
        "desired_outcome": "",
        "acceptance_criteria": [],
        "measurement_plan": [],
    }
    if state.get("action_id"):
        action = load_improvement_action(
            resolved,
            str(state["action_id"]),
        )

    parent_objective = _parent_reentry_objective(action)
    if not isinstance(parent_objective, str) or not parent_objective:
        raise WorkflowError(
            "runtime applicability disposition requires an explicit parent objective"
        )

    iteration = _current_iteration(state)
    candidate_head = iteration.get("candidate_head")

    if not isinstance(candidate_head, str) or not candidate_head:
        raise WorkflowError(
            "runtime applicability disposition requires a candidate source commit"
        )
    if iteration.get("validation_state") != "source-validations-passed":
        raise WorkflowError(
            "runtime applicability disposition requires passed source validation"
        )
    if iteration.get("unresolved_findings"):
        raise WorkflowError(
            "runtime applicability disposition refuses unresolved findings"
        )

    disposition = {
        "runtime_validation": {
            "applicability": "not-applicable-to-bounded-slice",
            "status": "not-evaluated",
            "reason": reason.strip(),
            "actor": "Architect",
        },
        "promotion": {
            "applicability": "applicable",
            "status": "pending",
            "reason": (
                "Promotion remains required to prove the approved "
                "post-promotion branch-closeout objective path."
            ),
            "actor": "Architect",
        },
        "parent_objective_id": parent_objective,
    }

    state["delivery_applicability"] = disposition
    state["promotion_eligible"] = True
    iteration["status"] = "source-validated-promotion-ready"
    iteration["next_boundary"] = "promotion"
    iteration["promotion_eligible"] = True

    generations = state.setdefault("implementation_generations", [])
    previous = generations[-1] if generations else None
    generations.append(
        {
            "generation": len(generations) + 1,
            "iteration": state["current_iteration"],
            "candidate_head": candidate_head,
            "status": "runtime-not-applicable-promotion-ready",
            "supersedes_generation": (
                previous.get("generation")
                if isinstance(previous, Mapping)
                else None
            ),
            "historical_justification_preserved": True,
            "accepted_action": state.get("action_id"),
            "evidence_reconsideration": (
                dict(state["evidence_reconsideration"])
                if isinstance(
                    state.get("evidence_reconsideration"),
                    Mapping,
                )
                else None
            ),
            "runtime_receipt": None,
            "runtime_receipt_sha256": None,
            "delivery_applicability": disposition,
        }
    )

    state["history"].append(
        {
            "stage": "runtime-applicability-disposition",
            "iteration": state["current_iteration"],
            "candidate_head": candidate_head,
            "parent_objective_id": parent_objective,
            "runtime_applicability": "not-applicable-to-bounded-slice",
            "runtime_success_claimed": False,
            "promotion_applicability": "applicable",
            "promotion_eligible": True,
            "actor": "Architect",
            "reason": reason.strip(),
        }
    )

    if not _runtime_not_applicable_promotion_ready(state, iteration):
        raise WorkflowError(
            "runtime applicability disposition did not produce promotion readiness"
        )

    _refresh_objective_route(resolved, state)
    _persist(state_path, state)

    return {
        "status": state["status"],
        "state": str(state_path),
        "candidate_head": candidate_head,
        "parent_objective_id": parent_objective,
        "next_boundary": "promotion",
        "runtime_applicability": "not-applicable-to-bounded-slice",
        "runtime_success_claimed": False,
        "promotion_applicability": "applicable",
        "promotion_eligible": True,
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
    repo: Path,
    state_path: Path,
    runtime_receipt: Path,
) -> Mapping[str, Any]:
    state = _load_parent(state_path)
    if state.get("status") != "source-git-complete":
        raise WorkflowError("source Git lifecycle must complete before runtime acceptance")
    iteration = _current_iteration(state)
    candidate_head = iteration.get("candidate_head")
    if not isinstance(candidate_head, str) or not candidate_head:
        raise WorkflowError("runtime acceptance requires a candidate source commit")
    receipt_path = runtime_receipt.expanduser().resolve()
    value = json.loads(receipt_path.read_text(encoding="utf-8"))
    validate_runtime_receipt(value)
    state["runtime_receipt"] = str(receipt_path)
    state["runtime_receipt_sha256"] = hashlib.sha256(
        receipt_path.read_bytes()
    ).hexdigest()
    state["status"] = "runtime-verified"
    iteration["validation_state"] = "runtime-verified"
    iteration["status"] = "validated-candidate"
    iteration["next_boundary"] = "promotion"
    iteration["promotion_eligible"] = not bool(iteration.get("unresolved_findings"))
    state["promotion_eligible"] = iteration["promotion_eligible"]
    generations = state.setdefault("implementation_generations", [])
    previous = generations[-1] if generations else None
    generation = {
        "generation": len(generations) + 1,
        "iteration": state["current_iteration"],
        "candidate_head": candidate_head,
        "status": "runtime-verified",
        "supersedes_generation": previous.get("generation") if isinstance(previous, Mapping) else None,
        "historical_justification_preserved": True,
        "accepted_action": state.get("action_id"),
        "evidence_reconsideration": (
            dict(state["evidence_reconsideration"])
            if isinstance(state.get("evidence_reconsideration"), Mapping)
            else None
        ),
        "runtime_receipt": str(receipt_path),
        "runtime_receipt_sha256": state["runtime_receipt_sha256"],
    }
    generations.append(generation)
    state["history"].append(
        {
            "stage": "runtime-acceptance",
            "iteration": state["current_iteration"],
            "receipt": str(receipt_path),
            "sha256": state["runtime_receipt_sha256"],
        }
    )
    _refresh_objective_route(repo.expanduser().resolve(), state)
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
    iteration = _current_iteration(state)

    runtime_verified = state.get("status") == "runtime-verified"
    runtime_not_applicable = (
        state.get("status") == "source-git-complete"
        and _runtime_not_applicable_promotion_ready(
            state,
            iteration,
        )
    )

    if not runtime_verified and not runtime_not_applicable:
        raise WorkflowError(
            "runtime outcome must be verified before promotion unless "
            "explicit Architect applicability records runtime as not "
            "applicable and promotion as applicable"
        )
    if state.get("promotion_eligible") is not True or iteration.get("unresolved_findings"):
        raise WorkflowError("current candidate remains non-promotable while unresolved findings exist")
    result = start_promotion(
        repo=repo.expanduser().resolve(),
        request=str(state["request"]),
        source_branch=_promotion_source_branch(state),
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
    _refresh_objective_route(repo.expanduser().resolve(), state)
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
    if result["status"] == "complete":
        generations = state.setdefault("implementation_generations", [])
        if generations:
            generations[-1]["status"] = "promoted"
            generations[-1]["promotion_state"] = str(state.get("promotion_state"))
    state["history"].append(
        {
            "stage": "promotion-continuation",
            "verified_boundary": result.get("verified_boundary"),
            "status": result["status"],
        }
    )
    _refresh_objective_route(repo.expanduser().resolve(), state)
    _persist(state_path.expanduser().resolve(), state)
    return {
        "status": state["status"],
        "state": str(state_path.expanduser().resolve()),
        "child": result,
    }
