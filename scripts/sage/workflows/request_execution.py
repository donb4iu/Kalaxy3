#!/usr/bin/env python3
"""Repository-owned SAGE request-to-operator execution composition."""

from __future__ import annotations

from collections import Counter

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from request_execution import ProposalBundle, load_proposal, next_operator_boundary, validate_operator_result, validate_routine_git_lifecycle_receipt
from workflow import (
    AtomicFileTransaction,
    AtomicFileWriter,
    AuthorityAssertion,
    AuthorityReconciler,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    ComponentCandidate,
    ComponentSelector,
    FailureDiagnoser,
    GitInspector,
    GitSafetyGuardrail,
    JsonlEventLogger,
    OperatorGitProposal,
    OutcomeMetrics,
    PrimitiveCatalog,
    RequiredCapability,
    SageDiscovery,
    ValidationCommand,
    ValidationPlan,
    WorkflowError,
)
from workflow.diagnosis import classify_post_retrieval_continuation
from workflow.recovery import (
    RECOVERY_CONSUMPTION_NAME,
    RECOVERY_DECISION_NAME,
    bind_successor_operator_boundary,
    build_consumption_record,
    build_recovery_identity,
    decide_next_boundary,
    digest_value,
    governing_composition_digest,
    load_consumed_fingerprints,
    load_recovery_decisions,
)
from workflows.operating_contract import build_post_operator_workflow, build_pre_mutation_workflow

PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "sage.discovery",
    "git.inspect",
    "authority.reconcile",
    "component.select",
    "capability.gap",
    "file.atomic-preserve-mode",
    "validation.plan",
    "git.safety-guardrail",
    "failure.diagnose",
    "operator.git-proposal",
    "metrics.outcome",
    "evidence.closeout",
    "workflow.composition",
)
WORKFLOW_ID = "sage.request-execution"
SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


@dataclass
class ExecutionContext:
    """Mutable state for one governed request execution."""

    repo: Path
    request: str
    bundle: ProposalBundle
    state_dir: Path
    catalog: PrimitiveCatalog
    logger: JsonlEventLogger
    runner: CommandRunner
    inspector: GitInspector
    writer: AtomicFileWriter
    discovery: Any = None
    git_snapshot: Any = None
    remote_main_head: str | None = None
    authority_path: Path | None = None
    component_path: Path | None = None
    gap_path: Path | None = None
    proposal_path: Path | None = None
    transaction: AtomicFileTransaction | None = None
    baseline_safety: dict[str, tuple[tuple[str, str, str], ...]] | None = None
    context_baseline_validation: dict[str, Any] | None = None
    validation: list[dict[str, Any]] = field(default_factory=list)


def sha256_file(path: Path) -> str:
    """Return one repository file digest."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Mapping[str, Any]) -> str:
    """Return deterministic repository-style JSON."""

    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def write_state(context: ExecutionContext, name: str, value: Mapping[str, Any]) -> Path:
    """Write one local state receipt through the atomic file primitive."""

    path = context.state_dir / name
    context.writer.write_text(path, stable_json(value), new_mode=0o600)
    return path


def _request_execution_recovery_state_root(source: Path) -> Path:
    """Resolve the shared local-state root for a request-execution recovery."""

    for parent in source.parents:
        if parent.name == "sage-request-execution":
            return parent.parent
    raise WorkflowError("recovery decision is outside SAGE request-execution state")


def _request_execution_recovery_runtime(
    repo: Path,
    state_dir: Path,
) -> tuple[CommandRunner, Path]:
    """Build the registered command runtime for request-execution recovery."""

    required = ("command.run", "file.atomic-preserve-mode")
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(required)
    event_log = state_dir / "recovery-consumption-events.jsonl"
    logger = JsonlEventLogger(
        event_log,
        WORKFLOW_ID + ".recovery",
        primitive_versions=catalog.versions_for(required),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    return runner, event_log


def consume_recovery_decision(
    repo: Path,
    recovery_decision_path: Path,
    output: Path | None = None,
) -> Mapping[str, Any]:
    """Consume one implementation-local recovery owned by request execution."""

    resolved_repo = repo.expanduser().resolve()
    source = recovery_decision_path.expanduser().resolve()
    decision = json.loads(source.read_text(encoding="utf-8"))
    if decision.get("record_type") != "sage-recovery-next-boundary":
        raise WorkflowError("request-execution recovery decision type is invalid")
    if decision.get("owning_component") != WORKFLOW_ID:
        raise WorkflowError("request-execution recovery owner is invalid")
    if (
        decision.get("disposition") != "repair"
        or decision.get("next_boundary") != "implementation-local"
    ):
        raise WorkflowError("request-execution recovery is not implementation-local repair")
    identity = decision.get("recovery_identity", {})
    identity_sha = str(identity.get("identity_sha256", ""))
    fingerprint = str(decision.get("governing_condition_fingerprint", ""))
    if not identity_sha or not fingerprint:
        raise WorkflowError("request-execution recovery identity is invalid")

    state_root = _request_execution_recovery_state_root(source)
    already_consumed = fingerprint in load_consumed_fingerprints(
        state_root,
        identity_sha,
    )

    runner, event_log = _request_execution_recovery_runtime(
        resolved_repo,
        source.parent,
    )
    result = runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Validate request-execution implementation-local recovery",
            argv=("make", "sage-request-execute-self-test"),
            cwd=resolved_repo,
            timeout_seconds=600,
        ),
        step_id="request-execution-implementation-local-recovery-validation",
    )
    if already_consumed:
        return {
            "status": "already-consumed",
            "consumption": None,
            "validation_output_sha256": result.output_sha256,
            "source_recovery_decision": str(source),
            "repository_mutation": False,
        }

    destination = (
        output or source.parent / RECOVERY_CONSUMPTION_NAME
    ).expanduser().resolve()
    if destination.exists():
        raise WorkflowError(f"recovery consumption already exists: {destination}")
    record = build_consumption_record(
        decision,
        consumed_boundary="implementation-local",
        consumer_reference=str(event_log.resolve()),
    )
    AtomicFileWriter((source.parent, destination.parent)).write_text(
        destination,
        stable_json(record),
        new_mode=0o600,
    )
    return {
        "status": "consumed",
        "consumption": str(destination),
        "validation_output_sha256": result.output_sha256,
        "source_recovery_decision": str(source),
        "repository_mutation": False,
    }


def build_context(repo: Path, request: str, proposal: Path) -> ExecutionContext:
    """Resolve proposal, primitives, and local execution state."""

    bundle = load_proposal(proposal, request)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = Path("~/.local/state/kalaxy3/sage-request-execution").expanduser() / stamp
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir, bundle.package_path.parent),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    inspector = GitInspector(repo, runner)
    writer = AtomicFileWriter((repo, state_dir))
    return ExecutionContext(repo, request, bundle, state_dir, catalog, logger, runner, inspector, writer)



def context_policy_validation(
    context: ExecutionContext,
    *,
    field: str,
    changed: bool = False,
) -> dict[str, Any]:
    """Run repository-owned context validation without trusting proposal-authored commands."""

    if field not in {"baseline", "required"}:
        raise WorkflowError(f"unsupported context validation phase: {field}")
    argv: list[str] = [
        "python3",
        "scripts/sage/sage-change-preflight.py",
    ]
    if changed:
        argv.append("--changed")
    else:
        for relative in context.bundle.declared_paths:
            argv.extend(("--path", relative))
    argv.append(
        "--run-baseline-validation"
        if field == "baseline"
        else "--run-required-validation"
    )
    result = context.runner.run(
        CommandSpec(
            primitive_id="validation.plan",
            label=f"Run context-derived {field} validation",
            argv=tuple(argv),
            cwd=context.repo,
            timeout_seconds=3600,
        ),
        step_id=f"context-{field}-validation",
    )
    return {
        "label": f"Context-derived {field} validation",
        "reference": "sage-change-authority.json",
        "status": "pass",
        "sha256": result.output_sha256,
    }



def discovery_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Preserve literal discovery and current evidence retrieval."""

    context.discovery = SageDiscovery(context.repo, context.runner).literal(context.request)
    result = context.runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Retrieve evidence for literal SAGE request",
            argv=("make", "sage-evidence-retrieve"),
            cwd=context.repo,
            environment={"SAGE_REQUEST": context.request},
            timeout_seconds=600,
        ),
        step_id="literal-evidence-retrieval",
    )
    context.writer.write_text(
        context.state_dir / "evidence-retrieval.txt",
        result.stdout,
        new_mode=0o600,
    )
    return {
        "request": context.request,
        "contexts": list(context.discovery.contexts),
        "authorities": list(context.discovery.authorities),
        "retrieval_output_sha256": result.output_sha256,
    }


def git_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Require proposal-bound feature authority and observe current remote main."""

    repository = context.bundle.manifest["repository"]
    context.inspector.require_clean()
    context.inspector.require_branch(str(repository["branch"]))
    context.inspector.require_head(str(repository["head"]))
    context.git_snapshot = context.inspector.snapshot()
    context.remote_main_head = context.inspector.remote_head("origin", "main")
    return {
        **context.git_snapshot.as_dict(),
        "remote_main_head": context.remote_main_head,
    }


def authority_assertions(context: ExecutionContext, captured: str) -> tuple[AuthorityAssertion, ...]:
    """Build SAGE-owned authority assertions; never trust package assertions."""

    common = {
        "captured_at": captured,
        "freshness": "current",
        "confidence": "high",
        "applicability": "material",
    }
    policy = context.repo / "sage-operating-contract-policy.json"
    standard = context.repo / "markdown/standards/kalaxy3-sage-operating-contract.md"
    request_digest = hashlib.sha256(context.request.encode("utf-8")).hexdigest()
    discovery_digest = hashlib.sha256(context.discovery.stdout.encode("utf-8")).hexdigest()
    return (
        AuthorityAssertion("ASSERT-001", "operator-intent", "operator-request", "literal-request", subject="operator intent", statement=context.request, measurement_type="declared", evidence_sha256=request_digest, **common),
        AuthorityAssertion("ASSERT-002", "git", "git", f"HEAD:{context.git_snapshot.head}", subject="repository state", statement=f"Branch {context.git_snapshot.branch} is clean at {context.git_snapshot.head}.", measurement_type="measured", evidence_sha256=hashlib.sha256(context.git_snapshot.head.encode()).hexdigest(), **common),
        AuthorityAssertion("ASSERT-003", "github", "repository-policy", "sage-operating-contract-policy.json#helper_policy", subject="GitHub mutation boundary", statement="SAGE request execution may not mutate GitHub; an operator boundary is required.", measurement_type="declared", evidence_sha256=sha256_file(policy), **common),
        AuthorityAssertion("ASSERT-004", "repository-policy", "repository", "markdown/standards/kalaxy3-sage-operating-contract.md", subject="repository mutation policy", statement="Repository content may be changed atomically and validated before one operator-executed Git proposal.", measurement_type="declared", evidence_sha256=sha256_file(standard), **common),
        AuthorityAssertion("ASSERT-005", "sage", "repository", "sage-change-authority.json", subject="SAGE discovery authority", statement="The literal request was classified through current repository SAGE discovery and its authoritative files were readable.", measurement_type="measured", evidence_sha256=discovery_digest, **common),
        AuthorityAssertion(
            "ASSERT-006",
            "git",
            "git",
            f"origin/main:{context.remote_main_head}",
            subject="remote main authority",
            statement=(
                f"Live origin/main is {context.remote_main_head}; it is frozen "
                "as observed authority evidence and is not an ancestry "
                "requirement unless an applicable authority explicitly says so."
            ),
            measurement_type="measured",
            evidence_sha256=hashlib.sha256(
                str(context.remote_main_head).encode()
            ).hexdigest(),
            **common,
        ),
    )



OBJECTIVE_PATH_DECISION_ENV = "SAGE_OBJECTIVE_PATH_DECISION"
OBJECTIVE_PATH_CLASSIFICATIONS = frozenset({
    "direct-objective-value",
    "necessary-blocker-material-risk",
    "deferrable-sage-internal-improvement",
})


def _objective_path_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"objective path decision {field} must be non-empty")
    return value.strip()


def _validate_objective_path_decision(
    value: Mapping[str, Any],
    *,
    request: str,
    proposal_path: Path,
) -> dict[str, Any]:
    required = {
        "schema_version",
        "record_type",
        "active_objective_id",
        "request_sha256",
        "proposal_sha256",
        "who",
        "what",
        "why",
        "when",
        "where",
        "how",
        "classification",
        "deferral_consequence",
        "next_value_milestone",
        "architect_disposition",
    }
    if set(value) != required:
        missing = sorted(required - set(value))
        extra = sorted(set(value) - required)
        raise WorkflowError(
            "objective path decision fields mismatch: "
            f"missing={missing}, extra={extra}"
        )
    if value.get("schema_version") != "1.0":
        raise WorkflowError("objective path decision schema_version must be 1.0")
    if value.get("record_type") != "sage-objective-path-decision":
        raise WorkflowError("objective path decision record_type is invalid")

    request_sha = hashlib.sha256(request.encode("utf-8")).hexdigest()
    if value.get("request_sha256") != request_sha:
        raise WorkflowError(
            "objective path decision is not bound to the exact literal request"
        )
    proposal_sha = sha256_file(proposal_path.expanduser().resolve())
    if value.get("proposal_sha256") != proposal_sha:
        raise WorkflowError(
            "objective path decision is not bound to the exact proposal package"
        )

    for field in (
        "active_objective_id",
        "who",
        "what",
        "why",
        "when",
        "where",
        "how",
        "deferral_consequence",
        "next_value_milestone",
    ):
        _objective_path_text(value.get(field), field)

    classification = value.get("classification")
    if classification not in OBJECTIVE_PATH_CLASSIFICATIONS:
        raise WorkflowError("objective path decision classification is invalid")
    if classification == "deferrable-sage-internal-improvement":
        raise WorkflowError(
            "deferrable SAGE/internal improvement cannot authorize mutation"
        )

    disposition = value.get("architect_disposition")
    if not isinstance(disposition, Mapping):
        raise WorkflowError(
            "objective path decision architect_disposition must be an object"
        )
    if set(disposition) != {"status", "authority", "basis", "rationale"}:
        raise WorkflowError(
            "objective path decision architect_disposition fields are invalid"
        )
    if disposition.get("status") != "approved":
        raise WorkflowError("objective path decision lacks Architect approval")
    if str(disposition.get("authority", "")).strip().lower() != "architect":
        raise WorkflowError("objective path decision authority must be Architect")
    if disposition.get("basis") != "operator-supplied-to-governed-execution":
        raise WorkflowError("objective path decision approval basis is invalid")
    _objective_path_text(
        disposition.get("rationale"),
        "architect_disposition.rationale",
    )
    return json.loads(json.dumps(value))


def _objective_path_decision_action(
    context: ExecutionContext,
    policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    gate = policy.get("objective_path_decision_policy")
    if not isinstance(gate, Mapping) or gate.get("enabled") is not True:
        raise WorkflowError("objective path decision policy is missing or disabled")
    if gate.get("decision_authority") != "architect":
        raise WorkflowError("objective path decision policy lost Architect authority")
    if gate.get("environment_variable") != OBJECTIVE_PATH_DECISION_ENV:
        raise WorkflowError("objective path decision environment binding drifted")

    raw_path = os.environ.get(OBJECTIVE_PATH_DECISION_ENV, "").strip()
    if not raw_path:
        raise WorkflowError(
            f"{OBJECTIVE_PATH_DECISION_ENV} is required before request mutation"
        )
    source = Path(raw_path).expanduser().resolve()
    if not source.is_file():
        raise WorkflowError(f"objective path decision file is missing: {source}")

    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(
            f"objective path decision is not valid JSON: {source}"
        ) from error
    if not isinstance(raw, Mapping):
        raise WorkflowError("objective path decision must be a JSON object")

    decision = _validate_objective_path_decision(
        raw,
        request=context.request,
        proposal_path=context.bundle.package_path,
    )
    receipt = {
        **decision,
        "decision_source": str(source),
        "decision_source_sha256": sha256_file(source),
        "enforcement": {
            "status": "accepted-for-mutation",
            "gate": "request-execution-authority",
            "deferrable_internal_work_blocked": True,
        },
    }
    write_state(context, "objective-path-decision.json", receipt)
    return receipt



def authority_action(context: ExecutionContext) -> Mapping[str, Any]:
    # Reconcile federated authority only after objective-path authority is proven.
    policy = json.loads(
        (context.repo / "sage-operating-contract-policy.json").read_text(
            encoding="utf-8"
        )
    )
    objective_path_decision = _objective_path_decision_action(context, policy)
    required = policy["authority_policy"]["required_authority_types"]
    captured = datetime.now().astimezone().isoformat(timespec="seconds")
    receipt = AuthorityReconciler(required).reconcile(
        receipt_id=f"SAGE-AUTH-{datetime.now().strftime('%Y%m%d')}-801",
        request=context.request,
        repository=context.git_snapshot.as_dict(),
        assertions=authority_assertions(context, captured),
        evidence_references=tuple(context.bundle.manifest["evidence_references"]),
        captured_at=captured,
    )
    if receipt.reconciliation["disposition"] != "complete":
        raise WorkflowError(receipt.reconciliation["summary"])
    context.authority_path = write_state(
        context,
        "authority-reconciliation.json",
        receipt.to_dict(),
    )
    result = receipt.to_dict()
    result["objective_path_decision"] = dict(objective_path_decision)
    return result



def candidate_from_mapping(context: ExecutionContext, item: Mapping[str, Any]) -> ComponentCandidate:
    """Bind an untrusted candidate to registered or staged-domain authority."""

    component_id = str(item["component_id"])
    capability_ids = tuple(str(value) for value in item["capability_ids"])
    version = str(item["version"])
    maturity = str(item["maturity"])
    source_path = str(item["source_path"])
    evidence_references = tuple(
        str(value) for value in item["evidence_references"]
    )
    staged_prefix = "staged-domain-capability:"

    if component_id.startswith(staged_prefix):
        capability_id = component_id.removeprefix(staged_prefix)
        if not capability_id or capability_ids != (capability_id,):
            raise WorkflowError(
                f"Staged domain candidate {component_id} must bind exactly its "
                "single declared capability"
            )
        if maturity != "staged-implementation":
            raise WorkflowError(
                f"Staged domain candidate {component_id} has invalid maturity: "
                f"{maturity}"
            )
        approved_reference = f"approved-domain-gap:{capability_id}"
        if approved_reference not in evidence_references:
            raise WorkflowError(
                f"Staged domain candidate {component_id} lacks Architect-approved "
                "domain-gap evidence"
            )
        planning_references = tuple(
            value.removeprefix("planning-source-sha256:")
            for value in evidence_references
            if value.startswith("planning-source-sha256:")
        )
        if (
            len(planning_references) != 1
            or re.fullmatch(r"[0-9a-f]{64}", planning_references[0]) is None
        ):
            raise WorkflowError(
                f"Staged domain candidate {component_id} lacks one valid "
                "planning-source SHA-256 provenance reference"
            )
        source_sha = planning_references[0]
        if not version.endswith("@" + source_sha[:12]):
            raise WorkflowError(
                f"Staged domain candidate {component_id} version is not bound "
                "to its planning-source digest"
            )
        baseline_references = tuple(
            value
            for value in evidence_references
            if value.startswith("proposed-baseline:")
            and value.endswith("#" + capability_id)
        )
        if len(baseline_references) != 1:
            raise WorkflowError(
                f"Staged domain candidate {component_id} lacks one matching "
                "proposed-baseline provenance reference"
            )
        proposal_source_paths = {
            source.path for source in context.bundle.source_files
        }
        if (
            source_path not in proposal_source_paths
            and not (context.repo / source_path).is_file()
        ):
            raise WorkflowError(
                f"Staged domain candidate source is absent from both the "
                f"checksum-bound proposal and repository: {source_path}"
            )
        expected = version
    else:
        context.catalog.require((component_id,))
        expected = context.catalog.versions_for((component_id,))[component_id]
        if version != expected:
            raise WorkflowError(
                f"Candidate {component_id} version mismatch: expected {expected}"
            )
        if not (context.repo / source_path).is_file():
            raise WorkflowError(f"Candidate source does not exist: {source_path}")

    return ComponentCandidate(
        str(item["candidate_id"]),
        capability_ids,
        component_id,
        expected,
        source_path,
        maturity,
        dict(item["selection_factors"]),
        evidence_references,
        str(item["rationale"]),
    )


def selection_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Select registered primitives and governed staged-domain candidates."""

    capabilities = tuple(
        RequiredCapability(str(item["capability_id"]), str(item["description"]), bool(item["required"]))
        for item in context.bundle.manifest["capabilities"]
    )
    candidates = tuple(
        candidate_from_mapping(context, item)
        for item in context.bundle.manifest["candidates"]
    )
    payload = ComponentSelector().build_manifest(
        manifest_id=f"SAGE-COMP-{datetime.now().strftime('%Y%m%d')}-801",
        request=context.request,
        authority_receipt=str(context.authority_path),
        capabilities=capabilities,
        candidates=candidates,
        approval={"status": "review-required", "reviewed_by": None, "reviewed_at": None, "rationale": "Operator review occurs at the generated Git proposal."},
    )
    ComponentSelector.require_complete(payload)
    context.component_path = write_state(context, "component-selection.json", payload)
    return payload


def gap_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Record that existing composition closes the request execution gap."""

    payload = {
        "schema_version": "1.0",
        "record_type": "sage-capability-gap-decision",
        "request": context.request,
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "new_primitive_required": False,
        "composition_can_close_gap": True,
        "decision": "Reuse selected registered primitives and governed checksum-bound staged-domain candidates; no new low-level primitive is authorized.",
        "approval": {"status": "review-required", "reviewed_by": None, "reviewed_at": None},
    }
    context.gap_path = write_state(context, "capability-gap-decision.json", payload)
    return payload


def reconcile_index(context: ExecutionContext) -> None:
    """Run only the repository-owned evidence index reconciliation path."""

    if context.bundle.manifest["reconcile_evidence_index"] is not True:
        return
    context.runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Reconcile generated SAGE evidence indexes",
            argv=("python3", "scripts/sage/sage-index.py", "reconcile"),
            cwd=context.repo,
            timeout_seconds=600,
        ),
        step_id="evidence-index-reconcile",
    )



def validate_python_payloads(context: ExecutionContext) -> tuple[str, ...]:
    """Reject invalid or newly unsafe Python payloads before repository mutation."""

    if context.baseline_safety is None:
        raise WorkflowError(
            "Python safety baseline was not captured before pre-write validation"
        )

    validated: list[str] = []
    root = context.state_dir / "prewrite-python-payloads"
    for item in context.bundle.source_files:
        if Path(item.path).suffix != ".py":
            continue
        candidate = root / item.path
        context.writer.write_bytes(candidate, item.payload, new_mode=item.mode)
        context.runner.run(
            CommandSpec(
                primitive_id="command.run",
                label=f"Validate Python payload globals: {item.path}",
                argv=(
                    "python3",
                    "scripts/sage/sage-python-static-guardrail.py",
                    str(candidate),
                ),
                cwd=context.repo,
                timeout_seconds=120,
            ),
            step_id="prewrite-python-static-validation",
        )
        baseline = context.baseline_safety.get(item.path)
        if baseline is None:
            raise WorkflowError(
                f"Python safety baseline missing for {item.path}"
            )
        introduced = introduced_safety_violations(candidate, baseline)
        if introduced:
            raise WorkflowError(
                "; ".join(item.render() for item in introduced)
            )
        validated.append(item.path)
    return tuple(validated)



def safety_fingerprint(
    source: str,
    violation: Any,
) -> tuple[str, str, str]:
    """Identify one safety finding without coupling identity to line movement."""

    lines = source.splitlines()
    statement = (
        lines[violation.line - 1].strip()
        if 0 < violation.line <= len(lines)
        else ""
    )
    return (str(violation.code), str(violation.message), statement)


def safety_fingerprints(
    source: str,
    *,
    path: Path,
) -> tuple[tuple[str, str, str], ...]:
    """Return deterministic whole-source safety fingerprints."""

    return tuple(
        safety_fingerprint(source, violation)
        for violation in GitSafetyGuardrail.scan_source(source, path=path)
    )


def capture_python_safety_baseline(
    context: ExecutionContext,
) -> Mapping[str, tuple[tuple[str, str, str], ...]]:
    """Capture proposal-bound baseline findings before repository writes."""

    baseline: dict[str, tuple[tuple[str, str, str], ...]] = {}
    for item in context.bundle.source_files:
        if Path(item.path).suffix != ".py":
            continue
        path = context.repo / item.path
        baseline[item.path] = (
            safety_fingerprints(path.read_text(encoding="utf-8"), path=path)
            if path.is_file()
            else ()
        )
    context.baseline_safety = baseline
    return baseline


def introduced_safety_violations(
    path: Path,
    baseline: tuple[tuple[str, str, str], ...],
) -> tuple[Any, ...]:
    """Return only findings not present in the proposal-bound baseline."""

    source = path.read_text(encoding="utf-8")
    remaining = Counter(baseline)
    introduced: list[Any] = []
    for violation in GitSafetyGuardrail.scan_source(source, path=path):
        fingerprint = safety_fingerprint(source, violation)
        if remaining[fingerprint] > 0:
            remaining[fingerprint] -= 1
        else:
            introduced.append(violation)
    return tuple(introduced)


def mutation_action(context: ExecutionContext) -> Mapping[str, str]:
    """Apply the checksum-bound proposal atomically within its exact scope."""

    capture_python_safety_baseline(context)
    validate_python_payloads(context)
    context.context_baseline_validation = context_policy_validation(
        context,
        field="baseline",
    )
    paths = tuple(context.repo / relative for relative in context.bundle.declared_paths)
    context.transaction = AtomicFileTransaction(context.writer, paths)
    digests: dict[str, str] = {}
    for item in context.bundle.source_files:
        digest = context.transaction.write_bytes(context.repo / item.path, item.payload, new_mode=item.mode)
        if digest != item.sha256:
            raise WorkflowError(f"Written payload digest mismatch: {item.path}")
        digests[item.path] = digest
    reconcile_index(context)
    for relative in context.bundle.generated_paths:
        path = context.repo / relative
        if not path.is_file():
            raise WorkflowError(f"Declared generated path is missing: {relative}")
        digests[relative] = sha256_file(path)
    context.inspector.require_exact_paths(context.bundle.declared_paths)
    return digests


def proposal_validation_commands(context: ExecutionContext) -> tuple[ValidationCommand, ...]:
    """Build the shell-free proposal validation plan already constrained by the parser."""

    return tuple(
        ValidationCommand(
            str(item["label"]),
            tuple(str(value) for value in item["argv"]),
            float(item["timeout_seconds"]),
        )
        for item in context.bundle.manifest["validation_commands"]
    )


def validation_action(context: ExecutionContext) -> tuple[Any, ...]:
    """Execute repository-required context validation plus proposal-supplied checks."""

    changed = SageDiscovery(context.repo, context.runner).changed()
    context_required = context_policy_validation(
        context,
        field="required",
        changed=True,
    )
    commands = proposal_validation_commands(context)
    results = ValidationPlan(context.repo, context.runner, commands).run()
    context.inspector.run_read_only(("diff", "--check"), label="Validate repository diff whitespace")
    context.inspector.require_exact_paths(context.bundle.declared_paths)
    context.validation = []
    if context.context_baseline_validation is not None:
        context.validation.append(dict(context.context_baseline_validation))
    context.validation.append(context_required)
    context.validation.extend(
        {
            "label": command.label,
            "reference": "proposal-supplemental-validation",
            "status": "pass",
            "sha256": result.output_sha256,
        }
        for command, result in zip(commands, results)
    )
    context.validation.append({
        "label": "Changed-path SAGE discovery",
        "reference": "sage.discovery",
        "status": "pass",
        "sha256": hashlib.sha256(changed.stdout.encode("utf-8")).hexdigest(),
    })
    return results


def safety_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Reject safety findings introduced beyond the proposal-bound baseline."""

    if context.baseline_safety is None:
        raise WorkflowError("Python safety baseline was not captured before mutation")

    introduced: list[Any] = []
    observed: dict[str, dict[str, int]] = {}
    paths: list[str] = []
    for item in context.bundle.source_files:
        if Path(item.path).suffix != ".py":
            continue
        path = context.repo / item.path
        baseline = context.baseline_safety.get(item.path)
        if baseline is None:
            raise WorkflowError(f"Python safety baseline missing for {item.path}")
        current = GitSafetyGuardrail.scan_source(
            path.read_text(encoding="utf-8"),
            path=path,
        )
        new_findings = introduced_safety_violations(path, baseline)
        introduced.extend(new_findings)
        observed[item.path] = {
            "baseline_findings": len(baseline),
            "candidate_findings": len(current),
            "introduced_findings": len(new_findings),
        }
        paths.append(str(path))

    if introduced:
        raise WorkflowError("; ".join(item.render() for item in introduced))
    return {"status": "pass", "paths": paths, "findings": observed}


def no_failure_action() -> Mapping[str, str]:
    """Record that failure diagnosis is not required on the successful path."""

    return {"status": "not-required", "reason": "No unexpected failure occurred before the operator boundary."}


def proposal_action(context: ExecutionContext) -> Mapping[str, Any]:
    """Produce one exact-scope routine Git lifecycle proposal when authority permits."""

    snapshot = context.inspector.snapshot()
    plan = context.bundle.manifest["operator_plan"]
    branch = snapshot.branch
    if context.remote_main_head is None:
        raise WorkflowError("routine Git lifecycle main authority is missing")
    if snapshot.upstream_head is None:
        raise WorkflowError(
            "routine Git lifecycle requires an existing synchronized feature-branch upstream"
        )
    if snapshot.upstream_head != snapshot.head:
        raise WorkflowError(
            "routine Git lifecycle requires local HEAD to equal the feature-branch upstream"
        )
    if context.inspector.remote_head(str(plan["push_remote"]), branch) != snapshot.head:
        raise WorkflowError("routine Git lifecycle remote feature branch authority drifted")
    if context.inspector.remote_head(str(plan["push_remote"]), "main") != context.remote_main_head:
        raise WorkflowError("routine Git lifecycle remote main authority changed during validation")

    context.proposal_path = context.state_dir / "operator-git-proposal.json"
    state_path = context.state_dir / "request-execution-state.json"
    payload = OperatorGitProposal.build(
        proposal_id=f"SAGE-GIT-{datetime.now().strftime('%Y%m%d')}-801",
        controller="sage-request-execution",
        repository=snapshot,
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="routine-git-lifecycle",
        change_scope=context.bundle.declared_paths,
        validation=context.validation,
        command_argv=(
            "python3",
            "scripts/sage/sage-routine-git-lifecycle.py",
            "--state",
            str(state_path),
            "--proposal",
            str(context.proposal_path),
            "--apply",
        ),
        expected_result="One explicitly approved repository-owned controller stages exactly the declared paths, creates exactly one commit, pushes the feature branch, and records a deterministic receipt.",
        risk="The approved command performs bounded Git stage/commit/push mutation on the declared feature branch only; GitHub, credential, deployment, branch-management, merge, rebase, reset, and ref-deletion mutation remain prohibited.",
        rollback="Do not execute the proposal; after execution any commit or remote rollback requires a separately governed operator boundary.",
        post_command_verification=(
            "git branch --show-current",
            "git status --porcelain=v1 --untracked-files=all",
            "git rev-parse HEAD",
            "git rev-parse @{upstream}",
        ),
    )
    OperatorGitProposal.write(context.proposal_path, payload, context.writer)
    return payload


def action_map(context: ExecutionContext) -> dict[str, Any]:
    """Bind exact request-execution actions to the mandatory operating contract."""

    return {
        "preserve-literal-request": lambda: discovery_action(context),
        "collect-current-git-authority": lambda: git_action(context),
        "reconcile-authority": lambda: authority_action(context),
        "select-repository-components": lambda: selection_action(context),
        "record-capability-gaps": lambda: gap_action(context),
        "implement-declared-repository-scope": lambda: mutation_action(context),
        "validate-real-runtime-path": lambda: validation_action(context),
        "validate-helper-safety": lambda: safety_action(context),
        "diagnose-unexpected-failures": no_failure_action,
        "propose-one-operator-boundary": lambda: proposal_action(context),
    }


def write_closeout(context: ExecutionContext, status: str, details: Mapping[str, Any]) -> Path:
    """Write local primitive-version closeout evidence."""

    writer = CloseoutWriter(
        destination_directory=context.state_dir,
        primitive_registry=context.repo / "sage-workflow-primitives.json",
        event_log=context.state_dir / "events.jsonl",
    )
    return writer.write(
        workflow_id=WORKFLOW_ID,
        status=status,
        used_primitives=PRIMITIVES_USED,
        details=details,
    )


def recover_repository_after_failure(
    context: ExecutionContext,
) -> Mapping[str, Any]:
    """Rollback only an opened repository transaction and independently verify it."""
    if context.transaction is None:
        return {
            "transaction_started": False,
            "rollback_attempted": False,
            "rollback_verified": False,
            "verification_error": None,
        }

    try:
        context.transaction.rollback()
    except Exception as error:
        return {
            "transaction_started": True,
            "rollback_attempted": True,
            "rollback_verified": False,
            "verification_error": f"{type(error).__name__}: {error}",
        }

    repository = context.bundle.manifest["repository"]
    try:
        context.inspector.require_clean()
        context.inspector.require_branch(str(repository["branch"]))
        context.inspector.require_head(str(repository["head"]))
    except Exception as error:
        return {
            "transaction_started": True,
            "rollback_attempted": True,
            "rollback_verified": False,
            "verification_error": f"{type(error).__name__}: {error}",
        }

    return {
        "transaction_started": True,
        "rollback_attempted": True,
        "rollback_verified": True,
        "verification_error": None,
    }


def failure_closeout_status(recovery: Mapping[str, Any]) -> str:
    """Classify failure closeout without inferring rollback from control flow."""
    if recovery.get("transaction_started") is not True:
        return "failed-pre-mutation"
    if recovery.get("rollback_verified") is True:
        return "failed-rolled-back"
    return "failed-rollback-unverified"



def _recovery_policy(context: ExecutionContext) -> dict[str, Any]:
    """Load the repository-owned fail-closed recovery policy."""

    policy_path = context.repo / "sage-recovery-policy.json"
    recovery = json.loads(policy_path.read_text(encoding="utf-8"))
    if (
        not isinstance(recovery, dict)
        or recovery.get("schema_version") != "1.0"
        or recovery.get("policy_id") != "kalaxy3-sage-recovery"
    ):
        raise WorkflowError("SAGE recovery policy is invalid")
    return recovery


def _action_status(context: ExecutionContext, action_id: str) -> str | None:
    """Return the current lifecycle status for one improvement action."""

    registry = json.loads(
        (context.repo / "sage-improvement-actions.json").read_text(encoding="utf-8")
    )
    for action in registry.get("actions", []):
        if isinstance(action, dict) and action.get("action_id") == action_id:
            status = action.get("current_status")
            return str(status) if status is not None else None
    return None


def _governing_evidence(context: ExecutionContext) -> dict[str, Any]:
    """Build stable evidence for all post-retrieval governing conditions."""

    policy_path = context.repo / "sage-operating-contract-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    recovery = _recovery_policy(context)
    paths = recovery.get("governing_composition_paths", [])
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise WorkflowError("recovery governing composition paths are invalid")
    return {
        "authority_contract_sha256": digest_value(
            {
                "branch": context.bundle.manifest["repository"]["branch"],
                "policy": policy.get("authority_policy", {}),
            }
        ),
        "scope_sha256": digest_value(list(context.bundle.declared_paths)),
        "required_capability_sha256": digest_value(
            context.bundle.manifest.get("capabilities", [])
        ),
        "safety_requirements_sha256": digest_value(policy.get("helper_policy", {})),
        "repository_owned_composition_sha256": governing_composition_digest(
            context.repo, paths
        ),
        "approval_or_mutation_boundaries_sha256": digest_value(
            {
                "operator_plan": context.bundle.manifest.get("operator_plan", {}),
                "policy": policy.get("operator_mutation_policy", {}),
            }
        ),
        "observed_remote_main": context.remote_main_head,
    }


def _governing_changes(
    identity: Mapping[str, Any],
    evidence: Mapping[str, Any],
    previous: list[Mapping[str, Any]],
) -> dict[str, bool]:
    """Compare current governing evidence with the prior matching failure."""

    if not previous:
        return {
            "authority": False,
            "scope": False,
            "required_capability": False,
            "safety_requirements": False,
            "repository_owned_composition": False,
            "approval_or_mutation_boundaries": False,
        }
    prior = previous[-1]
    prior_evidence = prior.get("governing_evidence", {})
    return {
        "authority": (
            evidence.get("authority_contract_sha256")
            != prior_evidence.get("authority_contract_sha256")
        ),
        "scope": evidence.get("scope_sha256") != prior_evidence.get("scope_sha256"),
        "required_capability": (
            evidence.get("required_capability_sha256")
            != prior_evidence.get("required_capability_sha256")
        ),
        "safety_requirements": (
            evidence.get("safety_requirements_sha256")
            != prior_evidence.get("safety_requirements_sha256")
        ),
        "repository_owned_composition": (
            evidence.get("repository_owned_composition_sha256")
            != prior_evidence.get("repository_owned_composition_sha256")
        ),
        "approval_or_mutation_boundaries": (
            evidence.get("approval_or_mutation_boundaries_sha256")
            != prior_evidence.get("approval_or_mutation_boundaries_sha256")
        ),
    }


def _recovery_authority(context: ExecutionContext) -> dict[str, str]:
    """Return stable feature-branch authority for recovery identity."""

    repository = context.bundle.manifest["repository"]
    return {
        "branch": str(repository["branch"]),
        "head": str(repository["head"]),
    }


def _build_recovery_decision(
    context: ExecutionContext,
    text: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build post-retrieval and recurrence-aware next-boundary decisions."""

    recovery = _recovery_policy(context)
    identity = build_recovery_identity(
        request=context.request,
        component_id=WORKFLOW_ID,
        failure_text=text,
        repository_authority=_recovery_authority(context),
    )
    state_root = Path(str(recovery.get("state_root", "~/.local/state/kalaxy3")))
    state_root = state_root.expanduser()
    previous = load_recovery_decisions(state_root, str(identity["identity_sha256"]))
    evidence = _governing_evidence(context)
    changes = _governing_changes(identity, evidence, previous)
    post_retrieval = classify_post_retrieval_continuation(
        retrieval_performed=True,
        attempted_action_authorized=True,
        governing_changes=changes,
        recovery_identity=identity,
    )
    control_id = str(recovery.get("owning_control_action_id", "")) or None
    status = _action_status(context, control_id) if control_id else None
    # Recurrence, consumed re-entry, and accepted control status are context,
    # not proof that the owning control violated its contract.
    accepted_failure = None
    consumed = load_consumed_fingerprints(
        state_root,
        str(identity["identity_sha256"]),
    )
    decision = decide_next_boundary(
        identity=identity,
        post_retrieval=post_retrieval,
        governing_evidence=evidence,
        previous=previous,
        consumed_fingerprints=consumed,
        owning_component=WORKFLOW_ID,
        control_action_id=control_id,
        control_action_status=status,
        accepted_control_failure=accepted_failure,
    )
    return post_retrieval, decision


def _diagnosis_correction(
    context: ExecutionContext,
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Map the shared recovery decision into failure-diagnosis correction."""

    recovery = _recovery_policy(context)
    disposition = str(decision.get("disposition"))
    action_reference = None
    if disposition in {"successor-action", "over-governance-blocked"}:
        action_reference = recovery.get("recovery_control_action_id")
    if disposition == "successor-action":
        correction = "Create the governed successor action emitted by recovery."
        target = "create-control"
    elif disposition == "over-governance-blocked":
        correction = "Consume or resolve the already-emitted recovery boundary."
        target = "no-action"
    else:
        correction = "Repair, regress, and revalidate through the selected boundary."
        target = "update-composition"
    return {
        "disposition": target,
        "reusable_correction": correction,
        "no_action_rationale": (
            "A duplicate governance re-entry is already outstanding."
            if target == "no-action"
            else None
        ),
        "regression_test_required": target != "no-action",
        "action_reference": action_reference,
    }

def _failure_text(
    error: Exception,
    recovery: Mapping[str, Any],
) -> str:
    """Render one stable request-execution failure description."""

    if recovery.get("transaction_started") is not True:
        summary = "repository transaction was not started; rollback was not applicable"
    elif recovery.get("rollback_verified") is True:
        summary = "repository rollback independently verified"
    else:
        summary = "repository rollback was not independently verified"
    return (
        f"SAGE request execution failed: {type(error).__name__}: {error}; "
        f"{summary}"
    )


def _failure_retrieval(
    context: ExecutionContext,
    text: str,
) -> str:
    """Run canonical failure retrieval and return its receipt reference."""

    result = context.runner.run(
        CommandSpec(
            primitive_id="failure.diagnose",
            label="Retrieve SAGE experience after request-execution failure",
            argv=(
                "python3",
                "-S",
                "scripts/sage/sage-failure-retrieval-gate.py",
                "--failure",
                text,
            ),
            cwd=context.repo,
            timeout_seconds=600,
        ),
        step_id="failure-retrieval",
    )
    match = re.search(r"^Receipt:\s+(.+)$", result.stdout, re.MULTILINE)
    return match.group(1).strip() if match else "failure-retrieval-output"


def _failure_paths(
    context: ExecutionContext,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return actual and expected component paths for diagnosis."""

    actual = {
        "component_id": WORKFLOW_ID,
        "component_version": "1.0",
        "source_path": "scripts/sage/workflows/request_execution.py",
        "description": "The reusable request execution composition.",
    }
    expected = {
        "component_id": "workflow.composition",
        "component_version": context.catalog.versions_for(
            ("workflow.composition",)
        )["workflow.composition"],
        "source_path": "scripts/sage/workflows/operating_contract.py",
        "description": "The mandatory SAGE operating-contract sequence.",
    }
    return actual, expected


def _diagnose_failure(
    context: ExecutionContext,
    text: str,
    recovery: Mapping[str, Any],
    receipt: str,
    post_path: Path,
    decision_path: Path,
    decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the canonical failure diagnosis from shared recovery evidence."""
    actual, expected = _failure_paths(context)
    diagnosis_id = f"SAGE-DIAG-{datetime.now().strftime('%Y%m%d')}-801"
    return FailureDiagnoser.diagnose(
        diagnosis_id=diagnosis_id,
        failure_id="request-execution",
        attempted_action="Execute the literal request through SAGE request execution.",
        what_failed=text,
        direct_evidence=(
            {"kind": "exception", "value": text},
            {"kind": "recovery-state", "value": stable_json(dict(recovery)).strip()},
            {"kind": "next-boundary", "value": stable_json(dict(decision)).strip()},
        ),
        actual_path=actual,
        expected_path=expected,
        why_actual_path_differed=(
            "The failure interrupted the governed operating-contract path."
        ),
        ownership="composition",
        mutation_effect={
            "repository_content_restored": bool(recovery.get("rollback_verified")),
            "git_mutation": False,
            "github_mutation": False,
            "deployment_mutation": False,
        },
        lesson_use={
            "retrieval_performed": True,
            "applicable_lesson_ids": [],
            "surfaced_lesson_ids": [],
            "used_lesson_ids": [],
        },
        previous_failure_references=decision.get("previous_failure_references", []),
        avoidable_rework_minutes=None,
        correction=_diagnosis_correction(context, decision),
        evidence_references=(
            receipt,
            str(post_path),
            str(decision_path),
            str(context.state_dir / "events.jsonl"),
        ),
        recovery_decision=decision,
    )


def failure_diagnosis(
    context: ExecutionContext,
    error: Exception,
    recovery: Mapping[str, Any],
) -> tuple[Path, Path]:
    """Retrieve experience and emit diagnosis plus one governed next boundary."""

    text = _failure_text(error, recovery)
    receipt = _failure_retrieval(context, text)
    post_retrieval, decision = _build_recovery_decision(context, text)
    decision_path = context.state_dir / RECOVERY_DECISION_NAME
    decision = bind_successor_operator_boundary(decision, decision_path)
    post_path = write_state(
        context,
        "post-retrieval-continuation-decision.json",
        post_retrieval,
    )
    decision_path = write_state(context, RECOVERY_DECISION_NAME, decision)
    diagnosis = _diagnose_failure(
        context,
        text,
        recovery,
        receipt,
        post_path,
        decision_path,
        decision,
    )
    diagnosis_path = write_state(context, "failure-diagnosis.json", diagnosis)
    return diagnosis_path, decision_path

def write_execution_state(
    context: ExecutionContext,
    proposal_payload: Mapping[str, Any],
) -> Path:
    """Persist the post-operator continuation contract for this request."""

    payload = {
        "schema_version": "1.0",
        "record_type": "sage-request-execution-state",
        "request": context.request,
        "request_sha256": hashlib.sha256(context.request.encode("utf-8")).hexdigest(),
        "proposal_package": str(context.bundle.package_path),
        "proposal_package_sha256": sha256_file(context.bundle.package_path),
        "repository_branch": str(context.bundle.manifest["repository"]["branch"]),
        "base_head": str(context.bundle.manifest["repository"]["head"]),
        "base_main_head": str(context.remote_main_head),
        "declared_paths": list(context.bundle.declared_paths),
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "capability_gap_decision": str(context.gap_path),
        "validation": list(context.validation),
        "operator_plan": dict(context.bundle.manifest["operator_plan"]),
        "current_boundary": str(proposal_payload["boundary"]),
        "current_proposal": str(context.proposal_path),
        "history": [],
    }
    return write_state(context, "request-execution-state.json", payload)


def load_state(path: Path) -> dict[str, Any]:
    """Load one immutable-local continuation state object."""

    resolved = path.expanduser().resolve()
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise WorkflowError("request execution state must be an object")
    required = {
        "schema_version",
        "record_type",
        "request",
        "request_sha256",
        "proposal_package",
        "proposal_package_sha256",
        "repository_branch",
        "base_head",
        "base_main_head",
        "declared_paths",
        "authority_receipt",
        "component_manifest",
        "capability_gap_decision",
        "validation",
        "operator_plan",
        "current_boundary",
        "current_proposal",
        "history",
    }
    legacy_required = required - {"base_main_head"}
    boundary = payload.get("current_boundary")
    fields = set(payload)
    if fields != required and not (
        fields == legacy_required and boundary in {"stage", "commit", "push"}
    ):
        raise WorkflowError("request execution state fields are invalid")
    if payload.get("schema_version") != "1.0" or payload.get("record_type") != "sage-request-execution-state":
        raise WorkflowError("request execution state version/type mismatch")
    request = payload.get("request")
    if not isinstance(request, str) or hashlib.sha256(request.encode("utf-8")).hexdigest() != payload.get("request_sha256"):
        raise WorkflowError("request execution state literal-request digest mismatch")
    package = Path(str(payload.get("proposal_package", ""))).expanduser().resolve()
    if not package.is_file() or sha256_file(package) != payload.get("proposal_package_sha256"):
        raise WorkflowError("request execution state proposal-package digest mismatch")
    base_main_head = payload.get("base_main_head")
    if base_main_head is not None and (
        not isinstance(base_main_head, str)
        or re.fullmatch(r"[0-9a-f]{40}", base_main_head) is None
    ):
        raise WorkflowError("request execution state base_main_head is invalid")
    paths = payload.get("declared_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(item, str) and item for item in paths):
        raise WorkflowError("request execution state declared_paths are invalid")
    if not isinstance(payload.get("history"), list):
        raise WorkflowError("request execution state history must be an array")
    plan = payload.get("operator_plan")
    if not isinstance(plan, dict) or set(plan) != {"commit_message", "push_remote"}:
        raise WorkflowError("request execution state operator_plan is invalid")
    return payload


def load_operator_proposal(path: Path) -> dict[str, Any]:
    """Load the active repository-owned operator proposal."""

    payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise WorkflowError("operator proposal must be an object")
    command = payload.get("command")
    if not isinstance(command, dict) or command.get("executed_by_helper") is not False:
        raise WorkflowError("operator proposal command contract is invalid")
    return payload


@dataclass
class ContinuationContext:
    """Mutable state for one post-operator operating-contract boundary."""

    repo: Path
    state_path: Path
    state: dict[str, Any]
    proposal: dict[str, Any]
    result_evidence: dict[str, Any]
    state_dir: Path
    catalog: PrimitiveCatalog
    logger: JsonlEventLogger
    runner: CommandRunner
    inspector: GitInspector
    writer: AtomicFileWriter
    verification: dict[str, Any] = field(default_factory=dict)
    metrics_path: Path | None = None
    evidence_path: Path | None = None
    next_proposal_path: Path | None = None


def _build_continuation_context(
    repo: Path,
    resolved_state: Path,
    state: dict[str, Any],
    proposal: dict[str, Any],
    result_evidence: dict[str, Any],
    evidence_path: Path,
) -> ContinuationContext:
    """Build one post-boundary context from already normalized result evidence."""

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = Path("~/.local/state/kalaxy3/sage-request-execution").expanduser() / ("continue-" + stamp)
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID + ".post-operator",
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, state_dir, resolved_state.parent, evidence_path.parent),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    inspector = GitInspector(repo, runner)
    writer = AtomicFileWriter((state_dir, resolved_state.parent))
    return ContinuationContext(
        repo,
        resolved_state,
        state,
        proposal,
        result_evidence,
        state_dir,
        catalog,
        logger,
        runner,
        inspector,
        writer,
    )


def build_continuation_context(
    repo: Path,
    state_path: Path,
    operator_result_path: Path,
) -> ContinuationContext:
    """Resolve legacy/manual pasted-result continuation evidence."""

    resolved_state = state_path.expanduser().resolve()
    state = load_state(resolved_state)
    if state.get("current_boundary") == "routine-git-lifecycle":
        raise WorkflowError(
            "routine Git lifecycle continuation requires its repository-owned controller receipt"
        )
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = load_operator_proposal(proposal_path)
    result_path = operator_result_path.expanduser().resolve()
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    result_evidence = validate_operator_result(result_payload, proposal)
    return _build_continuation_context(
        repo,
        resolved_state,
        state,
        proposal,
        result_evidence,
        result_path,
    )


def build_routine_receipt_continuation_context(
    repo: Path,
    state_path: Path,
    receipt_path: Path,
) -> ContinuationContext:
    """Resolve a repository-owned routine-controller receipt as first-class evidence."""

    resolved_state = state_path.expanduser().resolve()
    state = load_state(resolved_state)
    if state.get("current_boundary") != "routine-git-lifecycle":
        raise WorkflowError("routine-controller receipt requires the active routine-git-lifecycle boundary")
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = load_operator_proposal(proposal_path)
    resolved_receipt = receipt_path.expanduser().resolve()
    expected_receipt = resolved_state.parent / "routine-git-lifecycle-receipt.json"
    if resolved_receipt != expected_receipt or not resolved_receipt.is_file():
        raise WorkflowError("routine-controller receipt path is not the canonical request-state receipt")
    payload = json.loads(resolved_receipt.read_text(encoding="utf-8"))
    result_evidence = validate_routine_git_lifecycle_receipt(
        payload,
        proposal,
        state,
        receipt_sha256=sha256_file(resolved_receipt),
    )
    expected_event_log = (resolved_state.parent / "routine-git-lifecycle-events.jsonl").resolve()
    if Path(str(result_evidence["event_log"])).expanduser().resolve() != expected_event_log:
        raise WorkflowError("routine-controller receipt event-log path drifted")
    return _build_continuation_context(
        repo,
        resolved_state,
        state,
        proposal,
        result_evidence,
        resolved_receipt,
    )


def verify_operator_result_action(context: ContinuationContext) -> Mapping[str, Any]:
    """Independently verify the state caused by exactly one operator boundary."""

    boundary = str(context.proposal.get("boundary"))
    expected_branch = str(context.state["repository_branch"])
    declared = tuple(str(item) for item in context.state["declared_paths"])
    repository = context.proposal.get("repository")
    if not isinstance(repository, dict):
        raise WorkflowError("operator proposal repository authority is missing")
    expected_head = str(repository.get("head", ""))
    context.inspector.require_branch(expected_branch)
    if boundary == "routine-git-lifecycle":
        context.inspector.require_clean()
        current_head = context.inspector.head()
        if current_head == expected_head:
            raise WorkflowError("routine Git lifecycle did not advance HEAD")
        if (
            context.result_evidence.get("source_kind") != "routine-controller-receipt"
            or context.result_evidence.get("result_commit") != current_head
        ):
            raise WorkflowError("routine-controller receipt does not bind the observed resulting HEAD")
        history = context.inspector.run_read_only(
            ("rev-list", "--parents", f"{expected_head}..{current_head}"),
            label="Verify routine Git lifecycle single-commit topology",
        )
        rows = [line.split() for line in history.stdout.splitlines() if line]
        if rows != [[current_head, expected_head]]:
            raise WorkflowError(
                "routine Git lifecycle did not create exactly one commit from the approved HEAD"
            )
        changed = context.inspector.diff_paths(expected_head, current_head)
        if changed != set(declared):
            raise WorkflowError(
                f"routine Git lifecycle committed path mismatch: expected={sorted(declared)}, observed={sorted(changed)}"
            )
        context.inspector.require_upstream_equal()
        plan = context.state["operator_plan"]
        remote = str(plan["push_remote"])
        if context.inspector.remote_head(remote, expected_branch) != current_head:
            raise WorkflowError("routine Git lifecycle remote feature branch does not equal local HEAD")
        snapshot = context.inspector.snapshot()
    elif boundary == "stage":
        context.inspector.require_head(expected_head)
        context.inspector.require_exact_paths(declared)
        staged = context.inspector.staged_paths()
        if staged != set(declared):
            raise WorkflowError(
                f"Staged-path scope mismatch: expected={sorted(declared)}, observed={sorted(staged)}"
            )
        unstaged_result = context.inspector.run_read_only(
            ("diff", "--name-only"),
            label="Verify no unstaged residue after stage boundary",
        )
        unstaged = {line for line in unstaged_result.stdout.splitlines() if line}
        if unstaged:
            raise WorkflowError(f"stage boundary left unstaged residue: {sorted(unstaged)}")
        snapshot = context.inspector.snapshot()
        if snapshot.working_tree_status != "staged-declared-changes":
            raise WorkflowError("stage boundary did not produce fully staged declared changes")
    elif boundary == "commit":
        context.inspector.require_clean()
        current_head = context.inspector.head()
        if current_head == expected_head:
            raise WorkflowError("commit boundary did not advance HEAD")
        snapshot = context.inspector.snapshot()
    elif boundary == "push":
        context.inspector.require_clean()
        context.inspector.require_head(expected_head)
        context.inspector.require_upstream_equal()
        snapshot = context.inspector.snapshot()
    else:
        raise WorkflowError(f"unsupported request-execution continuation boundary: {boundary}")
    payload = {
        "status": "pass",
        "boundary": boundary,
        "proposal_id": str(context.proposal.get("proposal_id")),
        "command_sha256": str(context.result_evidence["command_sha256"]),
        "boundary_result_sha256": str(context.result_evidence["result_sha256"]),
        "repository": snapshot.as_dict(),
        "declared_paths": list(declared),
    }
    context.verification = payload
    context.writer.write_text(
        context.state_dir / "post-operator-verification.json",
        stable_json(payload),
        new_mode=0o600,
    )
    return payload


def raw_boundary_metrics(boundary: str) -> dict[str, int | float | None]:
    """Return only directly observed boundary-local metrics; unknowns stay null."""

    raw = {
        "workflows_started": 1,
        "workflows_completed": None,
        "first_pass_completions": None,
        "semantic_validations": 1,
        "semantic_false_passes": 0,
        "commands_executed": 1,
        "commands_failed": 0,
        "commands_retried": None,
        "manual_corrections": None,
        "operator_interventions": 1,
        "authority_checks": None,
        "authority_failures": None,
        "component_candidates_considered": None,
        "components_selected": None,
        "components_reused": None,
        "new_components_created": None,
        "component_contract_mismatches": None,
        "direct_execution_violations": 0,
        "known_failures_encountered": None,
        "known_failures_recurred": None,
        "mutation_opportunities": 1,
        "failures_detected_pre_mutation": None,
        "authoritative_repository_git_mutations": 3 if boundary == "routine-git-lifecycle" else 1,
        "disposable_fixture_git_mutations": 0,
        "github_mutations": 0,
        "deployment_mutations": 0,
        "avoidable_rework_minutes": None,
        "prompt_to_validated_change_minutes": None,
    }
    if boundary not in {"routine-git-lifecycle", "stage", "commit", "push"}:
        raise WorkflowError(f"unsupported metrics boundary: {boundary}")
    return raw


def outcome_metrics_action(context: ContinuationContext) -> Mapping[str, Any]:
    """Record boundary-local semantic outcome measurements without fabrication."""

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    boundary = str(context.proposal["boundary"])
    report = OutcomeMetrics.build_report(
        report_id=f"SAGE-METRICS-{datetime.now().strftime('%Y%m%d')}-{boundary.upper()}",
        captured_at=now,
        period={"started_at": str(context.proposal.get("created_at")), "completed_at": now},
        workflow_class="sage-request-execution-operator-boundary",
        raw_metrics=raw_boundary_metrics(boundary),
        provenance=(
            {"kind": "operator-proposal", "reference": str(context.state["current_proposal"])},
            {"kind": "boundary-result-sha256", "reference": str(context.result_evidence["result_sha256"])},
            {"kind": "git-inspect", "reference": "post-operator-verification.json"},
        ),
        limitations=(
            "Only measurements directly observed at this operator boundary are populated; unavailable values remain null.",
        ),
    )
    context.metrics_path = context.state_dir / "outcome-metrics.json"
    context.writer.write_text(context.metrics_path, stable_json(report), new_mode=0o600)
    return report


def evidence_closeout_action(context: ContinuationContext) -> Mapping[str, Any]:
    """Write local post-operator closeout evidence through the registered primitive."""

    if context.metrics_path is None:
        raise WorkflowError("post-operator metrics are missing")
    writer = CloseoutWriter(
        destination_directory=context.state_dir,
        primitive_registry=context.repo / "sage-workflow-primitives.json",
        event_log=context.state_dir / "events.jsonl",
    )
    context.evidence_path = writer.write(
        workflow_id=WORKFLOW_ID + ".post-operator",
        status="verified",
        used_primitives=PRIMITIVES_USED,
        details={
            "proposal": str(context.state["current_proposal"]),
            "boundary": str(context.proposal["boundary"]),
            "verification": str(context.state_dir / "post-operator-verification.json"),
            "metrics": str(context.metrics_path),
            "boundary_result_sha256": str(context.result_evidence["result_sha256"]),
        },
    )
    return {"status": "pass", "closeout": str(context.evidence_path)}


def continuation_action_map(context: ContinuationContext) -> dict[str, Any]:
    """Bind the mandatory post-operator operating-contract actions."""

    return {
        "verify-boundary-result": lambda: verify_operator_result_action(context),
        "record-outcomes-and-trends": lambda: outcome_metrics_action(context),
        "publish-sage-evidence": lambda: evidence_closeout_action(context),
    }


def proposal_suffix(proposal_id: str, boundary: str) -> str:
    """Return a deterministic three-digit suffix for a follow-on proposal."""

    digest = hashlib.sha256(f"{proposal_id}:{boundary}".encode("utf-8")).hexdigest()
    return f"{int(digest[:8], 16) % 1000:03d}"


def continuation_validation(context: ContinuationContext) -> list[dict[str, Any]]:
    """Return pass-only evidence references for the next operator proposal."""

    if context.metrics_path is None:
        raise WorkflowError("continuation metrics receipt is missing")
    verification_path = context.state_dir / "post-operator-verification.json"
    return [
        {
            "label": "Post-operator state verification",
            "reference": "git.inspect",
            "status": "pass",
            "sha256": sha256_file(verification_path),
        },
        {
            "label": "Post-operator outcome metrics",
            "reference": "metrics.outcome",
            "status": "pass",
            "sha256": sha256_file(context.metrics_path),
        },
    ]


def build_next_operator_proposal(context: ContinuationContext) -> Mapping[str, Any] | None:
    """Emit the next deterministic stage/commit/push boundary only after post verification."""

    current = str(context.proposal["boundary"])
    next_boundary = next_operator_boundary(current)
    if next_boundary is None:
        return None
    snapshot = context.inspector.snapshot()
    plan = context.state["operator_plan"]
    branch = str(context.state["repository_branch"])
    if next_boundary == "commit":
        argv = ("git", "commit", "-m", str(plan["commit_message"]))
        expected = "Create exactly one commit from the already verified staged declared paths and leave the working tree clean."
        risk = "The commit mutates local Git history only; exact staged scope was independently verified before this proposal."
        rollback = "Do not execute the proposal, or revert the resulting commit through a separately governed operator boundary."
        verification = ("git branch --show-current", "git status --porcelain=v1 --untracked-files=all")
    elif next_boundary == "push":
        remote = str(plan["push_remote"])
        if snapshot.upstream_head is None:
            argv = ("git", "push", "-u", remote, branch)
        else:
            argv = ("git", "push", remote, branch)
        expected = "Publish the already validated local feature-branch commit and establish or update its upstream reference."
        risk = "This mutates only the declared remote feature branch; no GitHub PR or deployment mutation is included."
        rollback = "Do not execute the proposal; after execution any remote rollback requires a separately governed boundary."
        verification = ("git branch --show-current", "git status --porcelain=v1 --untracked-files=all")
    else:
        raise WorkflowError(f"unsupported next request-execution boundary: {next_boundary}")
    payload = OperatorGitProposal.build(
        proposal_id=f"SAGE-GIT-{datetime.now().strftime('%Y%m%d')}-{proposal_suffix(str(context.proposal['proposal_id']), next_boundary)}",
        controller="sage-request-execution",
        repository=snapshot,
        authority_receipt=str(context.state["authority_receipt"]),
        component_manifest=str(context.state["component_manifest"]),
        boundary=next_boundary,
        change_scope=tuple(str(item) for item in context.state["declared_paths"]),
        validation=continuation_validation(context),
        command_argv=argv,
        expected_result=expected,
        risk=risk,
        rollback=rollback,
        post_command_verification=verification,
    )
    context.next_proposal_path = context.state_dir / f"operator-git-proposal-{next_boundary}.json"
    OperatorGitProposal.write(context.next_proposal_path, payload, context.writer)
    return payload


def update_continuation_state(
    context: ContinuationContext,
    next_proposal: Mapping[str, Any] | None,
) -> None:
    """Advance local request state only after the post-operator workflow succeeds."""

    history = list(context.state["history"])
    history.append(
        {
            "boundary": str(context.proposal["boundary"]),
            "proposal": str(context.state["current_proposal"]),
            "boundary_result_sha256": str(context.result_evidence["result_sha256"]),
            "verification": str(context.state_dir / "post-operator-verification.json"),
            "metrics": str(context.metrics_path),
            "evidence_closeout": str(context.evidence_path),
        }
    )
    context.state["history"] = history
    if next_proposal is None:
        context.state["current_boundary"] = "complete"
        context.state["current_proposal"] = None
    else:
        context.state["current_boundary"] = str(next_proposal["boundary"])
        context.state["current_proposal"] = str(context.next_proposal_path)
    context.writer.write_text(
        context.state_path,
        stable_json(context.state),
        new_mode=0o600,
    )


def _continue_context(context: ContinuationContext) -> Mapping[str, Any]:
    """Run the shared post-boundary verification, metrics, evidence, and state progression."""

    if str(context.state["current_boundary"]) != str(context.proposal.get("boundary")):
        raise WorkflowError("continuation state boundary does not match active operator proposal")
    workflow = build_post_operator_workflow(
        workflow_id=WORKFLOW_ID + ".post-operator",
        logger=context.logger,
        catalog=context.catalog,
        actions=continuation_action_map(context),
    )
    workflow.run()
    next_proposal = build_next_operator_proposal(context)
    update_continuation_state(context, next_proposal)
    return {
        "status": "complete" if next_proposal is None else "operator-review-required",
        "verified_boundary": str(context.proposal["boundary"]),
        "verification": str(context.state_dir / "post-operator-verification.json"),
        "metrics": str(context.metrics_path),
        "evidence_closeout": str(context.evidence_path),
        "state": str(context.state_path),
        "proposal": next_proposal,
        "proposal_path": str(context.next_proposal_path) if context.next_proposal_path else None,
        "event_log": str(context.state_dir / "events.jsonl"),
    }


def continue_request(
    repo: Path,
    state_path: Path,
    operator_result_path: Path,
) -> Mapping[str, Any]:
    """Resume one legacy/manual operator boundary from pasted result evidence."""

    return _continue_context(
        build_continuation_context(
            repo.expanduser().resolve(),
            state_path,
            operator_result_path,
        )
    )


def continue_request_from_routine_receipt(
    repo: Path,
    state_path: Path,
    receipt_path: Path,
) -> Mapping[str, Any]:
    """Resume and close one routine lifecycle from its repository-owned receipt."""

    return _continue_context(
        build_routine_receipt_continuation_context(
            repo.expanduser().resolve(),
            state_path,
            receipt_path,
        )
    )


def execute_request(repo: Path, request: str, proposal: Path) -> Mapping[str, Any]:
    """Execute one literal request to the exact first operator mutation boundary."""

    context = build_context(repo.expanduser().resolve(), request, proposal)
    workflow = build_pre_mutation_workflow(
        workflow_id=WORKFLOW_ID,
        logger=context.logger,
        catalog=context.catalog,
        actions=action_map(context),
    )
    try:
        results = workflow.run()
        if context.transaction is None or context.proposal_path is None:
            raise WorkflowError("request execution completed without transaction or proposal")
        context.transaction.commit()
        proposal_payload = results[-1]
        state = write_execution_state(context, proposal_payload)
        closeout = write_closeout(
            context,
            "operator-review-required",
            {
                "proposal": str(context.proposal_path),
                "state": str(state),
                "declared_paths": list(context.bundle.declared_paths),
            },
        )
    except Exception as error:
        recovery = recover_repository_after_failure(context)
        diagnosis, next_boundary = failure_diagnosis(
            context,
            error,
            recovery,
        )
        closeout = write_closeout(
            context,
            failure_closeout_status(recovery),
            {
                "error": str(error),
                "diagnosis": str(diagnosis),
                "next_boundary": str(next_boundary),
                "recovery": dict(recovery),
            },
        )
        raise WorkflowError(
            f"{error}\nFailure diagnosis: {diagnosis}\n"
            f"Next governed boundary: {next_boundary}\nCloseout: {closeout}"
        ) from error
    return {
        "status": "pass",
        "proposal": proposal_payload,
        "proposal_path": str(context.proposal_path),
        "state": str(state),
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "capability_gap_decision": str(context.gap_path),
        "closeout": str(closeout),
        "event_log": str(context.state_dir / "events.jsonl"),
    }
