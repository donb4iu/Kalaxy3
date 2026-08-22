#!/usr/bin/env python3
"""Govern one improvement-action transition to the existing operator Git continuation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from request_execution import request_sha256
from workflows.request_execution import load_state
from workflow import (
    AtomicFileTransaction,
    AtomicFileWriter,
    AuthorityAssertion,
    AuthorityReconciler,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    GitInspector,
    ImprovementActionClient,
    JsonlEventLogger,
    OperatorGitProposal,
    PrimitiveCatalog,
    SageDiscovery,
    Step,
    ValidationCommand,
    ValidationPlan,
    Workflow,
    WorkflowError,
)
from workflows.request_planning import derive_component_plan

WORKFLOW_ID = "sage.improvement-action-transition"
WORKFLOW_VERSION = "1.1.0"
REGISTRY_PATH = "sage-improvement-actions.json"
RECOVERY_DECISION_TYPE = "sage-recovery-next-boundary"
SUCCESSOR_BOUNDARY_NAME = "successor-improvement-action-boundary.json"
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "sage.discovery",
    "git.inspect",
    "authority.reconcile",
    "component.select",
    "capability.gap",
    "sage.action-lifecycle",
    "file.atomic-preserve-mode",
    "validation.plan",
    "operator.git-proposal",
    "evidence.closeout",
    "workflow.composition",
)
SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


@dataclass
class TransitionContext:
    """State for one governed improvement-action lifecycle mutation."""

    repo: Path
    request: str
    action_id: str
    operation: str
    to_status: str | None
    replacement_path: Path | None
    expected_contract_sha256: str | None
    actor: str
    reason: str
    evidence_references: tuple[str, ...]
    commit_message: str
    push_remote: str
    state_dir: Path
    catalog: PrimitiveCatalog
    logger: JsonlEventLogger
    runner: CommandRunner
    inspector: GitInspector
    writer: AtomicFileWriter
    discovery: Any = None
    git_snapshot: Any = None
    authority_path: Path | None = None
    component_path: Path | None = None
    gap_path: Path | None = None
    proposal_path: Path | None = None
    state_path: Path | None = None
    provenance_path: Path | None = None
    validation: list[dict[str, Any]] = field(default_factory=list)
    transition_status: str | None = None
    lifecycle_event: dict[str, Any] | None = None


def stable_json(value: Mapping[str, Any]) -> str:
    """Return repository-style deterministic JSON text."""

    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for one file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_local(
    context: TransitionContext,
    name: str,
    value: Mapping[str, Any],
) -> Path:
    """Write one local state receipt through the atomic file primitive."""

    path = context.state_dir / name
    context.writer.write_text(path, stable_json(value), new_mode=0o600)
    return path


def build_successor_action_boundary(
    decision: Mapping[str, Any],
    source_reference: str,
) -> dict[str, Any]:
    """Translate accepted-control recurrence into an Architect lifecycle boundary."""

    if decision.get("record_type") != RECOVERY_DECISION_TYPE:
        raise WorkflowError("successor recovery decision type is invalid")
    control = decision.get("owning_control")
    if not isinstance(control, Mapping):
        raise WorkflowError("successor recovery owning control is missing")
    if decision.get("disposition") != "successor-action":
        raise WorkflowError("recovery decision does not require successor action")
    if decision.get("classification") != "recurrence":
        raise WorkflowError("successor action requires a recurrence")
    if control.get("status") != "accepted" or control.get("accepted_control_failure") is not True:
        raise WorkflowError("successor action requires failure of an accepted control")
    if not decision.get("previous_failure_references"):
        raise WorkflowError("successor action requires previous failure evidence")
    return {
        "schema_version": "1.0",
        "record_type": "sage-improvement-action-successor-boundary",
        "status": "architect-decision-required",
        "decision_authority": "architect",
        "requested_outcome": "register-successor-capability-gap/improvement-action",
        "source_recovery_decision": source_reference,
        "recovery_identity": dict(decision.get("recovery_identity", {})),
        "owning_component": decision.get("owning_component"),
        "owning_control": dict(control),
        "reason": decision.get("reason"),
        "required_evidence": list(decision.get("required_evidence", [])),
        "mutation_authority": "sage.action-lifecycle",
        "next_boundary": "architect-decision",
    }


def emit_successor_action_boundary(
    repo: Path,
    recovery_decision_path: Path,
    output: Path | None = None,
) -> Mapping[str, Any]:
    """Persist one lifecycle-owned successor Architect boundary without repo mutation."""

    resolved_repo = repo.expanduser().resolve()
    source = recovery_decision_path.expanduser().resolve()
    decision = json.loads(source.read_text(encoding="utf-8"))
    boundary = build_successor_action_boundary(decision, str(source))
    destination = (output or source.parent / SUCCESSOR_BOUNDARY_NAME).expanduser().resolve()
    catalog = PrimitiveCatalog.load(resolved_repo / "sage-workflow-primitives.json")
    catalog.require(("file.atomic-preserve-mode",))
    writer = AtomicFileWriter((destination.parent,))
    writer.write_text(destination, stable_json(boundary), new_mode=0o600)
    return {
        "status": "architect-decision-required",
        "boundary": str(destination),
        "decision": boundary,
        "repository_mutation": False,
    }


def build_context(
    *,
    repo: Path,
    request: str,
    action_id: str,
    operation: str,
    to_status: str | None,
    replacement_path: Path | None,
    expected_contract_sha256: str | None,
    actor: str,
    reason: str,
    evidence_references: tuple[str, ...],
    commit_message: str,
    push_remote: str,
) -> TransitionContext:
    """Build the primitive-backed least-authority workflow context."""

    if operation not in {"transition", "amendment"}:
        raise WorkflowError(f"Unsupported action lifecycle operation: {operation}")
    if operation == "transition" and not to_status:
        raise WorkflowError("Transition operation requires to_status")
    if operation == "amendment":
        if replacement_path is None or not expected_contract_sha256:
            raise WorkflowError(
                "Amendment operation requires replacement path and expected contract digest"
            )

    resolved = repo.expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = (
        Path("~/.local/state/kalaxy3/sage-action-transition").expanduser()
        / stamp
    )
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(resolved / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(resolved, state_dir),
        base_environment={
            name: ""
            for name in SECRET_ENVIRONMENT_NAMES
        },
    )
    inspector = GitInspector(resolved, runner)
    writer = AtomicFileWriter((resolved, state_dir))
    return TransitionContext(
        resolved,
        request,
        action_id,
        operation,
        to_status,
        replacement_path,
        expected_contract_sha256,
        actor,
        reason,
        evidence_references,
        commit_message,
        push_remote,
        state_dir,
        catalog,
        logger,
        runner,
        inspector,
        writer,
    )


def discovery_action(context: TransitionContext) -> Mapping[str, Any]:
    """Preserve literal discovery and current evidence retrieval."""

    context.discovery = SageDiscovery(
        context.repo,
        context.runner,
    ).literal(context.request)
    retrieval = context.runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Retrieve evidence for improvement-action lifecycle mutation",
            argv=("make", "sage-evidence-retrieve"),
            cwd=context.repo,
            environment={"SAGE_REQUEST": context.request},
            timeout_seconds=600,
        ),
        step_id="transition-evidence-retrieval",
    )
    return {
        "request": context.request,
        "contexts": list(context.discovery.contexts),
        "authorities": list(context.discovery.authorities),
        "retrieval_sha256": retrieval.output_sha256,
    }


def git_action(context: TransitionContext) -> Mapping[str, Any]:
    """Require a clean synchronized non-main feature branch."""

    context.inspector.require_clean()
    branch = context.inspector.branch()
    if not branch or branch == "main":
        raise WorkflowError(
            "Improvement-action lifecycle mutations require an active non-main branch"
        )
    context.inspector.require_upstream_equal()
    context.git_snapshot = context.inspector.snapshot()
    return context.git_snapshot.as_dict()


def authority_action(context: TransitionContext) -> Mapping[str, Any]:
    """Reconcile the material authority required for registry mutation."""

    if context.discovery is None or context.git_snapshot is None:
        raise WorkflowError(
            "Discovery and Git authority must precede reconciliation"
        )
    policy_path = context.repo / "sage-operating-contract-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    required = policy["authority_policy"]["required_authority_types"]
    captured = datetime.now().astimezone().isoformat(timespec="seconds")
    request_digest = hashlib.sha256(
        context.request.encode("utf-8")
    ).hexdigest()
    discovery_digest = hashlib.sha256(
        context.discovery.stdout.encode("utf-8")
    ).hexdigest()
    common = {
        "captured_at": captured,
        "freshness": "current",
        "confidence": "high",
        "applicability": "material",
    }
    assertions = (
        AuthorityAssertion(
            "ASSERT-001",
            "operator-intent",
            "operator-request",
            "literal-request",
            subject="operator intent",
            statement=context.request,
            measurement_type="declared",
            evidence_sha256=request_digest,
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-002",
            "git",
            "git",
            f"HEAD:{context.git_snapshot.head}",
            subject="repository state",
            statement=(
                f"Branch {context.git_snapshot.branch} is clean and "
                f"locally synchronized at {context.git_snapshot.head}."
            ),
            measurement_type="measured",
            evidence_sha256=hashlib.sha256(
                context.git_snapshot.head.encode("utf-8")
            ).hexdigest(),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-003",
            "github",
            "repository-policy",
            "sage-operating-contract-policy.json#operator_mutation_policy",
            subject="remote mutation authority",
            statement=(
                "Git and GitHub mutation remain operator-executed one "
                "boundary at a time."
            ),
            measurement_type="declared",
            evidence_sha256=sha256_file(policy_path),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-004",
            "repository-policy",
            "repository",
            "sage-continuous-improvement-policy.json",
            subject="improvement-action lifecycle policy",
            statement=(
                "Improvement-action status changes use the canonical "
                "append-only dry-run-first lifecycle."
            ),
            measurement_type="declared",
            evidence_sha256=sha256_file(
                context.repo / "sage-continuous-improvement-policy.json"
            ),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-005",
            "sage",
            "repository",
            "sage-change-authority.json",
            subject="SAGE discovery authority",
            statement=(
                "The literal transition request was classified through "
                "current repository SAGE discovery."
            ),
            measurement_type="measured",
            evidence_sha256=discovery_digest,
            **common,
        ),
    )
    receipt = AuthorityReconciler(required).reconcile(
        receipt_id=(
            "SAGE-AUTH-"
            + datetime.now().strftime("%Y%m%d")
            + "-ACT"
        ),
        request=context.request,
        repository=context.git_snapshot.as_dict(),
        assertions=assertions,
        evidence_references=context.evidence_references,
        captured_at=captured,
    )
    if receipt.reconciliation["disposition"] != "complete":
        raise WorkflowError(receipt.reconciliation["summary"])
    context.authority_path = write_local(
        context,
        "authority-reconciliation.json",
        receipt.to_dict(),
    )
    return receipt.to_dict()


def component_action(context: TransitionContext) -> Mapping[str, Any]:
    """Derive lifecycle-mutation component semantics from the live repository registry."""

    if context.authority_path is None:
        raise WorkflowError("Authority reconciliation receipt is missing")
    plan = derive_component_plan(
        repo=context.repo,
        catalog=context.catalog,
        request=context.request,
        authority_reference=str(context.authority_path),
        required_primitives=PRIMITIVES_USED,
    )
    if plan.gap_receipt is not None:
        context.gap_path = write_local(
            context,
            "capability-gap.json",
            plan.gap_receipt,
        )
        raise WorkflowError(
            "Existing registered primitives cannot satisfy the action lifecycle workflow"
        )
    context.component_path = write_local(
        context,
        "component-selection.json",
        plan.selection_manifest,
    )
    context.gap_path = write_local(
        context,
        "capability-gap-decision.json",
        {
            "schema_version": "1.0",
            "record_type": "sage-capability-gap-decision",
            "request": context.request,
            "authority_receipt": str(context.authority_path),
            "component_manifest": str(context.component_path),
            "new_primitive_required": False,
            "composition_can_close_gap": True,
            "decision": (
                "Reuse the selected repository primitives; no new low-level "
                "primitive is authorized."
            ),
        },
    )
    return plan.selection_manifest


def lifecycle_action(context: TransitionContext) -> Mapping[str, Any]:
    """Run canonical dry-run then explicit apply for one lifecycle mutation."""

    client = ImprovementActionClient(
        context.inspector,
        context.runner,
    )
    if context.operation == "transition":
        if context.to_status is None:
            raise WorkflowError("Transition target status is missing")
        record = client.transition(
            action_id=context.action_id,
            to_status=context.to_status,
            actor=context.actor,
            reason=context.reason,
            evidence_references=context.evidence_references,
            apply=True,
        )
    else:
        if (
            context.replacement_path is None
            or context.expected_contract_sha256 is None
        ):
            raise WorkflowError("Amendment contract inputs are missing")
        record = client.amend(
            action_id=context.action_id,
            replacement_path=context.replacement_path,
            expected_contract_sha256=context.expected_contract_sha256,
            actor=context.actor,
            reason=context.reason,
            evidence_references=context.evidence_references,
            apply=True,
        )
    context.inspector.require_exact_paths((REGISTRY_PATH,))
    context.transition_status = str(record["current_status"])
    history = record.get("history")
    if not isinstance(history, list) or not history:
        raise WorkflowError("Action lifecycle result has no history")
    event = history[-1]
    if not isinstance(event, dict):
        raise WorkflowError("Action lifecycle result event is invalid")
    context.lifecycle_event = event
    return record


def validation_action(
    context: TransitionContext,
) -> tuple[Any, ...]:
    """Validate the mutated action registry and reusable workflow controls."""

    commands = (
        ValidationCommand(
            "Validate improvement-action registry and policy",
            ("make", "sage-improvement-policy-check"),
            600,
        ),
        ValidationCommand(
            "Validate improvement-action lifecycle and learning controls",
            ("make", "sage-learning-self-test"),
            600,
        ),
        ValidationCommand(
            "Validate reusable workflow composition controls",
            ("make", "sage-workflow-guardrail"),
            600,
        ),
        ValidationCommand(
            "Validate root operating-contract controls",
            ("make", "sage-operating-contract-check"),
            600,
        ),
    )
    results = ValidationPlan(
        context.repo,
        context.runner,
        commands,
    ).run()
    context.inspector.run_read_only(
        ("diff", "--check"),
        label="Validate action-registry diff whitespace",
    )
    context.inspector.require_exact_paths((REGISTRY_PATH,))
    context.validation = [
        {
            "label": command.label,
            "reference": "validation.plan",
            "status": "pass",
            "sha256": result.output_sha256,
        }
        for command, result in zip(commands, results)
    ]
    return results


def proposal_id(context: TransitionContext) -> str:
    """Build one deterministic valid proposal suffix."""

    digest = hashlib.sha256(
        f"{context.action_id}:{context.operation}:{context.to_status or context.expected_contract_sha256}".encode("utf-8")
    ).hexdigest()
    suffix = int(digest[:8], 16) % 1000
    return (
        "SAGE-GIT-"
        + datetime.now().strftime("%Y%m%d")
        + f"-{suffix:03d}"
    )


def proposal_action(context: TransitionContext) -> Mapping[str, Any]:
    """Emit exactly one operator Git stage boundary."""

    if context.authority_path is None or context.component_path is None:
        raise WorkflowError(
            "Lifecycle authority/component receipts are missing"
        )
    payload = OperatorGitProposal.build(
        proposal_id=proposal_id(context),
        controller="sage-improvement-action-lifecycle",
        repository=context.inspector.snapshot(),
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="stage",
        change_scope=(REGISTRY_PATH,),
        validation=context.validation,
        command_argv=("git", "add", "--", REGISTRY_PATH),
        expected_result=(
            "Exactly sage-improvement-actions.json becomes staged on the "
            "active feature branch."
        ),
        risk=(
            "Only the canonical improvement-action registry is staged; no "
            "commit, push, GitHub, credential, or deployment mutation occurs."
        ),
        rollback=(
            "Do not execute the proposal, or restore the registry through a "
            "separately governed recovery after operator review."
        ),
        post_command_verification=(
            "git branch --show-current",
            "git status --porcelain=v1 --untracked-files=all",
        ),
    )
    context.proposal_path = (
        context.state_dir / "operator-git-proposal.json"
    )
    OperatorGitProposal.write(
        context.proposal_path,
        payload,
        context.writer,
    )
    return payload


def continuation_state_action(
    context: TransitionContext,
    proposal: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Write state compatible with the proven stage/commit/push continuation."""

    if (
        context.authority_path is None
        or context.component_path is None
        or context.gap_path is None
        or context.proposal_path is None
        or context.git_snapshot is None
    ):
        raise WorkflowError(
            "Lifecycle continuation receipts are incomplete"
        )
    provenance = {
        "schema_version": "1.0",
        "record_type": "sage-improvement-action-lifecycle-provenance",
        "workflow_version": WORKFLOW_VERSION,
        "request": context.request,
        "request_sha256": request_sha256(context.request),
        "action_id": context.action_id,
        "operation": context.operation,
        "to_status": context.to_status,
        "expected_contract_sha256": context.expected_contract_sha256,
        "actor": context.actor,
        "reason": context.reason,
        "evidence_references": list(context.evidence_references),
        "resulting_status": context.transition_status,
        "lifecycle_event": context.lifecycle_event,
    }
    context.provenance_path = write_local(
        context,
        "lifecycle-provenance.json",
        provenance,
    )
    state = {
        "schema_version": "1.0",
        "record_type": "sage-request-execution-state",
        "request": context.request,
        "request_sha256": request_sha256(context.request),
        "proposal_package": str(context.provenance_path),
        "proposal_package_sha256": sha256_file(
            context.provenance_path
        ),
        "repository_branch": context.git_snapshot.branch,
        "base_head": context.git_snapshot.head,
        "declared_paths": [REGISTRY_PATH],
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "capability_gap_decision": str(context.gap_path),
        "validation": list(context.validation),
        "operator_plan": {
            "commit_message": context.commit_message,
            "push_remote": context.push_remote,
        },
        "current_boundary": str(proposal["boundary"]),
        "current_proposal": str(context.proposal_path),
        "history": [],
    }
    context.state_path = write_local(
        context,
        "request-execution-state.json",
        state,
    )
    load_state(context.state_path)
    return state


def action_map(context: TransitionContext) -> dict[str, Any]:
    """Return the shared lifecycle-mutation composition actions."""

    results: dict[str, Any] = {}

    def propose() -> Mapping[str, Any]:
        payload = proposal_action(context)
        results["proposal"] = payload
        return payload

    def state() -> Mapping[str, Any]:
        proposal = results.get("proposal")
        if not isinstance(proposal, Mapping):
            raise WorkflowError(
                "Operator proposal must precede continuation state"
            )
        return continuation_state_action(context, proposal)

    return {
        "discover": lambda: discovery_action(context),
        "inspect": lambda: git_action(context),
        "authority": lambda: authority_action(context),
        "components": lambda: component_action(context),
        "lifecycle": lambda: lifecycle_action(context),
        "validation": lambda: validation_action(context),
        "proposal": propose,
        "continuation": state,
    }


def workflow_for(context: TransitionContext) -> Workflow:
    """Build the shared registered action-lifecycle workflow."""

    actions = action_map(context)
    return Workflow(
        workflow_id=WORKFLOW_ID,
        logger=context.logger,
        catalog=context.catalog,
        steps=(
            Step("discover", "sage.discovery", actions["discover"]),
            Step("inspect", "git.inspect", actions["inspect"]),
            Step(
                "authority",
                "authority.reconcile",
                actions["authority"],
            ),
            Step(
                "components",
                "component.select",
                actions["components"],
            ),
            Step(
                "lifecycle",
                "sage.action-lifecycle",
                actions["lifecycle"],
            ),
            Step(
                "validation",
                "validation.plan",
                actions["validation"],
            ),
            Step(
                "proposal",
                "operator.git-proposal",
                actions["proposal"],
            ),
            Step(
                "continuation",
                "file.atomic-preserve-mode",
                actions["continuation"],
            ),
        ),
    )


def write_closeout(
    context: TransitionContext,
    *,
    status: str,
    details: Mapping[str, Any],
) -> Path:
    """Write lifecycle closeout evidence with primitive provenance."""

    return CloseoutWriter(
        destination_directory=context.state_dir,
        primitive_registry=(
            context.repo / "sage-workflow-primitives.json"
        ),
        event_log=context.state_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID,
        status=status,
        used_primitives=PRIMITIVES_USED,
        details=details,
    )


def _closeout_details(context: TransitionContext) -> dict[str, Any]:
    """Return shared closeout facts for one lifecycle mutation."""

    return {
        "action_id": context.action_id,
        "operation": context.operation,
        "to_status": context.to_status,
        "expected_contract_sha256": context.expected_contract_sha256,
        "resulting_status": context.transition_status,
        "registry_path": REGISTRY_PATH,
        "proposal": str(context.proposal_path),
        "continuation_state": str(context.state_path),
        "git_mutation": False,
        "github_mutation": False,
        "deployment_mutation": False,
        "next_continuation": "make sage-request-continue",
    }


def run_lifecycle(context: TransitionContext) -> Mapping[str, Any]:
    """Apply one governed lifecycle mutation and stop at the stage boundary."""

    transaction = AtomicFileTransaction(
        context.writer,
        (context.repo / REGISTRY_PATH,),
    )
    try:
        with transaction:
            workflow_for(context).run()
            if context.proposal_path is None or context.state_path is None:
                raise WorkflowError(
                    "Lifecycle workflow completed without operator continuation"
                )
            transaction.commit()
    except Exception as error:
        details = _closeout_details(context)
        details.update(
            {
                "error": f"{type(error).__name__}: {error}",
                "repository_registry_rollback": True,
            }
        )
        write_closeout(context, status="failed-rolled-back", details=details)
        raise

    closeout = write_closeout(
        context,
        status="operator-review-required",
        details=_closeout_details(context),
    )
    return {
        "status": "operator-review-required",
        "action_id": context.action_id,
        "operation": context.operation,
        "to_status": context.to_status,
        "resulting_status": context.transition_status,
        "proposal": str(context.proposal_path),
        "state": str(context.state_path),
        "closeout": str(closeout),
        "event_log": str(context.state_dir / "events.jsonl"),
    }


def start_transition(
    *,
    repo: Path,
    request: str,
    action_id: str,
    to_status: str,
    actor: str,
    reason: str,
    evidence_references: tuple[str, ...],
    commit_message: str,
    push_remote: str = "origin",
) -> Mapping[str, Any]:
    """Build and run one canonical improvement-action status transition."""

    context = build_context(
        repo=repo,
        request=request,
        action_id=action_id,
        operation="transition",
        to_status=to_status,
        replacement_path=None,
        expected_contract_sha256=None,
        actor=actor,
        reason=reason,
        evidence_references=evidence_references,
        commit_message=commit_message,
        push_remote=push_remote,
    )
    return run_lifecycle(context)


def start_amendment(
    *,
    repo: Path,
    request: str,
    replacement_path: Path,
    expected_contract_sha256: str,
    actor: str,
    reason: str,
    evidence_references: tuple[str, ...],
    commit_message: str,
    push_remote: str = "origin",
) -> Mapping[str, Any]:
    """Build and run one identified action-contract amendment."""

    resolved_replacement = replacement_path.expanduser().resolve()
    replacement = json.loads(resolved_replacement.read_text(encoding="utf-8"))
    action_id = replacement.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        raise WorkflowError("Amendment replacement action_id is missing")
    context = build_context(
        repo=repo,
        request=request,
        action_id=action_id,
        operation="amendment",
        to_status=None,
        replacement_path=resolved_replacement,
        expected_contract_sha256=expected_contract_sha256,
        actor=actor,
        reason=reason,
        evidence_references=evidence_references,
        commit_message=commit_message,
        push_remote=push_remote,
    )
    return run_lifecycle(context)

def _successor_recovery_self_test() -> None:
    """Prove action lifecycle owns accepted-control successor escalation."""

    decision = {
        "record_type": RECOVERY_DECISION_TYPE,
        "classification": "recurrence",
        "disposition": "successor-action",
        "previous_failure_references": ["prior.json"],
        "recovery_identity": {"identity_sha256": "a" * 64},
        "owning_component": "sage.request-execution",
        "owning_control": {"action_id": "SAGE-ACTION-20260810-001",
                           "status": "accepted",
                           "accepted_control_failure": True},
        "reason": "accepted control recurred",
        "required_evidence": ["failure retrieval receipt"],
    }
    boundary = build_successor_action_boundary(decision, "/tmp/recovery.json")
    if boundary.get("status") != "architect-decision-required":
        raise RuntimeError("successor lifecycle boundary did not require Architect")
    if boundary.get("mutation_authority") != "sage.action-lifecycle":
        raise RuntimeError("successor escalation escaped action lifecycle")
    rejected = dict(decision)
    rejected["disposition"] = "repair"
    try:
        build_successor_action_boundary(rejected, "/tmp/recovery.json")
    except WorkflowError:
        return
    raise RuntimeError("non-successor recovery entered action lifecycle escalation")


def self_test() -> int:
    """Exercise least-authority and continuation contracts without mutation."""

    _successor_recovery_self_test()
    for method in (
        "require_clean",
        "require_exact_paths",
        "require_upstream_equal",
    ):
        if not callable(getattr(GitInspector, method, None)):
            raise RuntimeError(
                f"GitInspector lacks lifecycle repository-state method: {method}"
            )
    for mutator in ("commit_and_push", "create_branch", "fetch"):
        if hasattr(GitInspector, mutator):
            raise RuntimeError(
                f"GitInspector unexpectedly exposes mutation method: {mutator}"
            )
    if "git.repository" in PRIMITIVES_USED:
        raise RuntimeError(
            "Restricted git.repository primitive entered production "
            "composition"
        )
    if not callable(getattr(ImprovementActionClient, "amend", None)):
        raise RuntimeError("ImprovementActionClient lacks amendment method")
    required = {
        "git.inspect",
        "sage.action-lifecycle",
        "validation.plan",
        "operator.git-proposal",
        "evidence.closeout",
        "workflow.composition",
    }
    if not required.issubset(PRIMITIVES_USED):
        raise RuntimeError(
            "Transition composition primitive manifest is incomplete"
        )
    if REGISTRY_PATH != "sage-improvement-actions.json":
        raise RuntimeError("Transition mutation scope changed")
    print("PASS GitInspector satisfies lifecycle RepositoryState contract")
    print("PASS GitInspector exposes no lifecycle Git mutation methods")
    print("PASS least-authority Git inspection contract")
    print("PASS canonical improvement-action transition and amendment ownership")
    print("PASS exact single-registry mutation scope")
    print("PASS accepted-control recurrence emits Architect successor boundary")
    print("PASS operator stage boundary with request-execution continuation")
    print(
        "Kalaxy3 SAGE improvement-action transition self-test: PASS"
    )
    return 0
