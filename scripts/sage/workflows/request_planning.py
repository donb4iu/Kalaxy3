#!/usr/bin/env python3
"""Repository-owned planning composition ahead of SAGE request execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from request_planning import PlanningSourceBundle, load_source_bundle, resolve_planning_authority, write_proposal_package
from request_execution import load_proposal
from workflow import (
    AtomicFileWriter,
    CapabilityGapRecorder,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    ComponentCandidate,
    ComponentSelector,
    GitInspector,
    JsonlEventLogger,
    PrimitiveCatalog,
    RequiredCapability,
    SageDiscovery,
    Step,
    Workflow,
    WorkflowError,
)
from workflows.request_execution import PRIMITIVES_USED as EXECUTION_PRIMITIVES

WORKFLOW_ID = "sage.request-planning"
WORKFLOW_VERSION = "1.3.0"
SECRET_ENVIRONMENT_NAMES = (
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
    "sage.discovery",
    "git.inspect",
    "component.select",
    "capability.gap",
    "evidence.closeout",
    "workflow.composition",
)


@dataclass(frozen=True)
class DerivedPlan:
    capabilities: list[dict[str, Any]]
    candidates: list[dict[str, Any]]
    selection_manifest: dict[str, Any]
    gap_receipt: dict[str, Any] | None
    domain_gap_receipts: list[dict[str, Any]]


def _capability_id(primitive_id: str) -> str:
    return "CAP-" + "".join(
        character if character.isalnum() else "-"
        for character in primitive_id
    ).strip("-").upper()


def _source_path(entry: Mapping[str, Any]) -> str:
    module = entry.get("module")
    if not isinstance(module, str) or not module:
        raise WorkflowError("registered primitive module is missing")
    return "scripts/sage/" + module.replace(".", "/") + ".py"


def _selection_factors(
    entry: Mapping[str, Any],
    source_exists: bool,
) -> dict[str, Any]:
    tests = entry.get("tests")
    test_count = len(tests) if isinstance(tests, list) else 0
    return {
        "applicability": "direct",
        "authority_compatibility": "compatible",
        "mutation_scope_fit": "least-authority",
        "published_interface_verified": bool(
            source_exists and entry.get("symbol")
        ),
        "successful_production_executions": None,
        "failed_production_executions": None,
        "open_recurrence": "unknown",
        "runtime_test_coverage": (
            "positive-and-negative" if test_count >= 2 else "positive-only"
        ),
    }


def _candidate_payload(candidate: ComponentCandidate) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "capability_ids": list(candidate.capability_ids),
        "component_id": candidate.component_id,
        "version": candidate.version,
        "source_path": candidate.source_path,
        "maturity": candidate.maturity,
        "selection_factors": dict(candidate.selection_factors),
        "evidence_references": list(candidate.evidence_references),
        "rationale": candidate.rationale,
    }


WORKFLOW_CAPABILITY_BASELINE_PATH = (
    "markdown/standards/"
    "sage-capability-intelligence-workflow-capability-baseline-v1.0.json"
)


def _safe_repository_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise WorkflowError(f"{label} must be a non-empty repository-relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts or value.startswith("/"):
        raise WorkflowError(f"{label} must remain repository-relative")
    return value


def _workflow_capability_entries(payload: bytes, label: str) -> tuple[str, dict[str, Mapping[str, Any]]]:
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as error:
        raise WorkflowError(f"{label} is not readable JSON: {error}") from error
    if not isinstance(value, Mapping):
        raise WorkflowError(f"{label} must be a JSON object")
    if value.get("schema_version") != "1.0" or value.get("record_type") != "sage-workflow-capability-completeness-baseline":
        raise WorkflowError(f"{label} workflow capability baseline version/type is invalid")
    baseline_id = value.get("baseline_id")
    if not isinstance(baseline_id, str) or not baseline_id:
        raise WorkflowError(f"{label} workflow capability baseline id is missing")
    families = value.get("families")
    if not isinstance(families, list):
        raise WorkflowError(f"{label} workflow capability families are invalid")
    result: dict[str, Mapping[str, Any]] = {}
    for family in families:
        if not isinstance(family, Mapping):
            raise WorkflowError(f"{label} workflow capability family is invalid")
        capabilities = family.get("capabilities")
        if not isinstance(capabilities, list):
            raise WorkflowError(f"{label} workflow capability family entries are invalid")
        for capability in capabilities:
            if not isinstance(capability, Mapping):
                raise WorkflowError(f"{label} workflow capability entry is invalid")
            capability_id = capability.get("capability_id")
            if not isinstance(capability_id, str) or not capability_id or capability_id in result:
                raise WorkflowError(f"{label} workflow capability id is invalid or duplicated: {capability_id!r}")
            implementation = capability.get("implementation")
            if not isinstance(implementation, list):
                raise WorkflowError(f"{label} {capability_id} implementation mapping is invalid")
            for index, relative in enumerate(implementation):
                _safe_repository_path(relative, f"{label} {capability_id} implementation[{index}]")
            result[capability_id] = capability
    return baseline_id, result


def _source_payload(source: PlanningSourceBundle | None, relative: str) -> bytes | None:
    if source is None:
        return None
    for item in source.source_files:
        if item.path == relative:
            return item.payload
    return None


def _domain_selection_factors(*, interface_verified: bool) -> dict[str, Any]:
    return {
        "applicability": "direct",
        "authority_compatibility": "compatible",
        "mutation_scope_fit": "least-authority",
        "published_interface_verified": interface_verified,
        "successful_production_executions": None,
        "failed_production_executions": None,
        "open_recurrence": "unknown",
        "runtime_test_coverage": "positive-only",
    }


def _effective_source_contribution_sha(source: PlanningSourceBundle) -> str:
    refs = source.manifest.get("evidence_references")
    if not isinstance(refs, list):
        raise WorkflowError("planning source evidence references are invalid")
    local_prefix = "implementation-local-contribution-sha256:"
    initial_prefix = "engineering-contribution-sha256:"
    local = [
        str(item)[len(local_prefix):]
        for item in refs
        if isinstance(item, str) and item.startswith(local_prefix)
    ]
    initial = [
        str(item)[len(initial_prefix):]
        for item in refs
        if isinstance(item, str) and item.startswith(initial_prefix)
    ]
    candidates = local if local else initial
    if not candidates:
        raise WorkflowError("planning source lacks engineering contribution provenance")
    candidate = candidates[-1]
    if len(candidate) != 64 or any(character not in "0123456789abcdef" for character in candidate):
        raise WorkflowError("planning source engineering contribution digest is invalid")
    return candidate


def _approved_domain_gap_capabilities(path: Path | None, request: str, source: PlanningSourceBundle) -> frozenset[str]:
    if path is None:
        return frozenset()
    resolved = path.expanduser().resolve()
    try:
        gap_set = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"approved domain capability gap set is unreadable: {resolved}: {error}") from error
    if not isinstance(gap_set, Mapping) or gap_set.get("record_type") != "sage-domain-capability-gap-set" or gap_set.get("schema_version") != "1.0":
        raise WorkflowError("approved domain capability gap set version/type is invalid")
    if gap_set.get("request") != request:
        raise WorkflowError("approved domain capability gap set does not match the literal request")
    approval = gap_set.get("approval")
    if (
        not isinstance(approval, Mapping)
        or approval.get("status") != "approved"
        or approval.get("reviewed_by") != "architect"
        or not approval.get("reviewed_at")
    ):
        raise WorkflowError("domain capability gap set must be explicitly Architect-approved")
    expected_request_sha = hashlib.sha256(request.encode("utf-8")).hexdigest()
    semantic = source.semantic_authority
    if not isinstance(semantic, Mapping):
        raise WorkflowError("approved staged domain capability requires confirmed semantic authority")
    expected_binding_evidence = {
        f"candidate-request-sha256:{expected_request_sha}",
        f"candidate-contribution-sha256:{_effective_source_contribution_sha(source)}",
        f"semantic-understanding-sha256:{semantic.get('semantic_understanding_sha256')}",
        f"semantic-confirmation-sha256:{semantic.get('semantic_confirmation_sha256')}",
    }
    gaps = gap_set.get("gaps")
    if not isinstance(gaps, list) or not gaps:
        raise WorkflowError("approved domain capability gap set contains no gaps")
    capabilities: list[str] = []
    for index, item in enumerate(gaps):
        if not isinstance(item, Mapping):
            raise WorkflowError(f"approved domain capability gap set item {index} is invalid")
        capability_id = item.get("required_capability")
        receipt_value = item.get("gap_receipt")
        expected_sha = item.get("gap_receipt_sha256")
        if not isinstance(capability_id, str) or not capability_id or not isinstance(receipt_value, str) or not receipt_value or not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise WorkflowError(f"approved domain capability gap set item {index} is incomplete")
        receipt_path = Path(receipt_value).expanduser().resolve()
        try:
            receipt_bytes = receipt_path.read_bytes()
            receipt = json.loads(receipt_bytes)
        except (OSError, json.JSONDecodeError) as error:
            raise WorkflowError(f"approved domain capability gap receipt is unreadable: {receipt_path}: {error}") from error
        if hashlib.sha256(receipt_bytes).hexdigest() != expected_sha:
            raise WorkflowError(f"approved domain capability gap receipt digest changed: {receipt_path}")
        if not isinstance(receipt, Mapping) or receipt.get("schema_version") != "1.1" or receipt.get("gap_kind") != "domain-capability":
            raise WorkflowError(f"approved domain capability gap receipt type is invalid: {receipt_path}")
        if receipt.get("request") != request or receipt.get("required_capability") != capability_id:
            raise WorkflowError(f"approved domain capability gap receipt binding is invalid: {receipt_path}")
        gap = receipt.get("gap")
        receipt_approval = receipt.get("approval")
        if not isinstance(gap, Mapping) or gap.get("new_primitive_required") is not False or gap.get("new_domain_capability_required") is not True or receipt.get("proposed_primitive") is not None:
            raise WorkflowError(f"approved domain capability gap receipt semantics are invalid: {receipt_path}")
        if (
            not isinstance(receipt_approval, Mapping)
            or receipt_approval.get("status") != "approved"
            or receipt_approval.get("reviewed_by") != "architect"
            or not receipt_approval.get("reviewed_at")
        ):
            raise WorkflowError(f"domain capability gap receipt is not Architect-approved: {receipt_path}")
        evidence = receipt.get("evidence_references")
        if not isinstance(evidence, list):
            raise WorkflowError(f"approved domain capability gap receipt evidence is invalid: {receipt_path}")
        evidence_set = {str(value) for value in evidence if isinstance(value, str)}
        if not expected_binding_evidence.issubset(evidence_set):
            raise WorkflowError(
                f"approved domain capability gap receipt candidate binding does not match current planning source: {receipt_path}"
            )
        authority_binding = [
            value for value in evidence_set
            if value.startswith("authority-receipt-sha256:")
        ]
        if len(authority_binding) != 1:
            raise WorkflowError(
                f"approved domain capability gap receipt authority binding is invalid: {receipt_path}"
            )
        capabilities.append(capability_id)
    if len(capabilities) != len(set(capabilities)):
        raise WorkflowError("approved domain capability gap set contains duplicate capabilities")
    return frozenset(capabilities)


def _domain_component_candidates(
    *,
    repo: Path,
    source: PlanningSourceBundle | None,
    domain_capabilities: tuple[RequiredCapability, ...],
    approved_domain_capabilities: frozenset[str],
    start_index: int,
) -> list[ComponentCandidate]:
    if not domain_capabilities:
        return []
    live_path = repo / WORKFLOW_CAPABILITY_BASELINE_PATH
    if not live_path.is_file():
        raise WorkflowError(f"workflow capability baseline is missing: {WORKFLOW_CAPABILITY_BASELINE_PATH}")
    live_id, live_entries = _workflow_capability_entries(
        live_path.read_bytes(),
        "live",
    )
    proposed_payload = _source_payload(source, WORKFLOW_CAPABILITY_BASELINE_PATH)
    proposed_id: str | None = None
    proposed_entries: dict[str, Mapping[str, Any]] = {}
    if proposed_payload is not None:
        proposed_id, proposed_entries = _workflow_capability_entries(
            proposed_payload,
            "proposed",
        )
    source_paths = set(source.declared_paths) if source is not None else set()
    source_sha = (
        hashlib.sha256(source.package_path.read_bytes()).hexdigest()
        if source is not None
        else ""
    )
    candidates: list[ComponentCandidate] = []
    sequence = start_index
    for capability in domain_capabilities:
        capability_id = capability.capability_id
        live = live_entries.get(capability_id)
        if isinstance(live, Mapping) and live.get("disposition") == "implemented":
            implementation = tuple(str(item) for item in live.get("implementation", []))
            if implementation and all((repo / relative).exists() for relative in implementation):
                candidates.append(
                    ComponentCandidate(
                        f"CAND-{sequence:03d}",
                        (capability_id,),
                        f"domain-capability:{capability_id}",
                        live_id,
                        implementation[0],
                        "repository-proven",
                        _domain_selection_factors(interface_verified=True),
                        tuple([
                            f"baseline:{WORKFLOW_CAPABILITY_BASELINE_PATH}#{capability_id}",
                            *(f"implementation:{relative}" for relative in implementation),
                        ]),
                        (
                            "The governed workflow capability baseline marks this domain "
                            "capability implemented and every mapped repository path exists. "
                            "The live candidate therefore satisfies planning without caller-authored semantics."
                        ),
                    )
                )
                sequence += 1
                continue
        proposed = proposed_entries.get(capability_id)
        if capability_id not in approved_domain_capabilities or not isinstance(proposed, Mapping):
            continue
        if proposed.get("disposition") != "implemented":
            continue
        if not isinstance(live, Mapping) or live.get("disposition") not in {"required-gap", "deferred-gap", "partial"}:
            continue
        implementation = tuple(str(item) for item in proposed.get("implementation", []))
        if not implementation:
            raise WorkflowError(f"approved staged domain capability {capability_id} has no implementation mapping")
        missing = [
            relative
            for relative in implementation
            if relative not in source_paths and not (repo / relative).exists()
        ]
        if missing:
            raise WorkflowError(
                f"approved staged domain capability {capability_id} references implementation paths absent from both the checksum-bound source and repository: {missing}"
            )
        candidates.append(
            ComponentCandidate(
                f"CAND-{sequence:03d}",
                (capability_id,),
                f"staged-domain-capability:{capability_id}",
                f"{proposed_id or 'proposed'}@{source_sha[:12]}",
                implementation[0],
                "staged-implementation",
                _domain_selection_factors(interface_verified=True),
                (
                    f"approved-domain-gap:{capability_id}",
                    f"planning-source-sha256:{source_sha}",
                    f"proposed-baseline:{WORKFLOW_CAPABILITY_BASELINE_PATH}#{capability_id}",
                ),
                (
                    "The Architect-approved domain gap authorizes this checksum-bound staged "
                    "implementation candidate. Selection authorizes implementation and validation "
                    "only; it does not claim the domain capability is proven before request-execution "
                    "guardrails succeed and the governed baseline is subsequently validated."
                ),
            )
        )
        sequence += 1
    return candidates


def _gap_receipt(
    *,
    repo: Path,
    catalog: PrimitiveCatalog,
    request: str,
    authority_reference: str,
    manifest_reference: str,
    missing_primitive: str,
) -> dict[str, Any]:
    considered = []
    for primitive_id, entry in sorted(catalog.primitives.items()):
        considered.append(
            {
                "component_id": primitive_id,
                "version": str(entry["version"]),
                "source_path": _source_path(entry),
                "insufficiency": (
                    f"Does not provide the required registered primitive "
                    f"{missing_primitive}."
                ),
                "composition_can_close_gap": False,
            }
        )
    return CapabilityGapRecorder.create(
        gap_id=f"SAGE-GAP-{datetime.now().strftime('%Y%m%d')}-PLANNING",
        request=request,
        authority_receipt=authority_reference,
        component_manifest=manifest_reference,
        required_capability=_capability_id(missing_primitive),
        candidates_considered=considered,
        missing_interface_or_behavior=(
            f"No eligible registered primitive provides {missing_primitive}."
        ),
        why_configuration_is_insufficient=(
            "The required interface is absent from the live primitive "
            "registry; configuration cannot create a published interface."
        ),
        why_composition_is_insufficient=(
            "The mandatory request-execution contract names a primitive "
            "that the registry cannot supply."
        ),
        proposed_primitive={
            "primitive_id": missing_primitive,
            "responsibility": (
                f"Provide the missing {missing_primitive} "
                "request-execution capability."
            ),
            "side_effects": "unknown until separately authorized",
            "idempotency": "must be declared before implementation",
            "logging": "must use structured SAGE workflow logging",
            "failure_mode": "must fail closed",
            "runtime_tests": [
                "positive path",
                "negative fail-closed path",
            ],
            "initial_maturity": "pilot",
        },
        approval={
            "status": "review-required",
            "reviewed_by": None,
            "reviewed_at": None,
            "rationale": (
                "Planner blocks proposal generation until a separately "
                "governed gap is approved and implemented."
            ),
        },
        evidence_references=(
            "sage-workflow-primitives.json",
            "scripts/sage/workflows/request_execution.py",
        ),
    )



def _domain_capabilities(planning_obligations: tuple[Mapping[str, Any], ...]) -> tuple[RequiredCapability, ...]:
    result: list[RequiredCapability] = []
    seen: set[str] = set()
    for item in planning_obligations:
        if item.get("kind") != "capability":
            continue
        capability_id = str(item.get("capability_id", ""))
        description = str(item.get("description", ""))
        if not capability_id or not description:
            raise WorkflowError("domain capability planning obligation is incomplete")
        if capability_id in seen:
            raise WorkflowError(f"duplicate domain planning capability: {capability_id}")
        seen.add(capability_id)
        result.append(
            RequiredCapability(
                capability_id,
                description,
                bool(item.get("required", True)),
            )
        )
    return tuple(result)


def _domain_gap_receipt(
    *,
    catalog: PrimitiveCatalog,
    request: str,
    authority_reference: str,
    manifest_reference: str,
    missing_capability: str,
    planning_obligations: tuple[Mapping[str, Any], ...],
    gap_sequence: int,
) -> dict[str, Any]:
    obligation = next(
        (
            item for item in planning_obligations
            if item.get("kind") == "capability"
            and item.get("capability_id") == missing_capability
        ),
        None,
    )
    if obligation is None:
        raise WorkflowError(
            f"missing domain planning obligation for capability {missing_capability}"
        )
    considered = [
        {
            "component_id": primitive_id,
            "version": str(entry["version"]),
            "source_path": _source_path(entry),
            "insufficiency": (
                "Registered SAGE workflow primitive does not establish the "
                f"domain capability {missing_capability}."
            ),
            "composition_can_close_gap": False,
        }
        for primitive_id, entry in sorted(catalog.primitives.items())
    ]
    receipt = CapabilityGapRecorder.create_domain(
        gap_id=(
            f"SAGE-GAP-{datetime.now().strftime('%Y%m%d')}-DOMAIN-"
            f"{gap_sequence:03d}"
        ),
        request=request,
        authority_receipt=authority_reference,
        component_manifest=manifest_reference,
        required_capability=missing_capability,
        candidates_considered=considered,
        missing_interface_or_behavior=str(obligation["description"]),
        why_configuration_is_insufficient=(
            "No repository-registered candidate currently proves this "
            "Architect-confirmed domain capability."
        ),
        why_composition_is_insufficient=(
            "The selected SAGE workflow primitives can govern the decision but "
            "cannot themselves satisfy the domain capability."
        ),
        approval={
            "status": "review-required",
            "reviewed_by": None,
            "reviewed_at": None,
            "rationale": (
                "Planner stops for governed domain capability selection; this "
                "receipt does not authorize a new SAGE primitive."
            ),
        },
        evidence_references=(
            "sage-workflow-primitives.json",
            f"planning-obligation:{obligation['obligation_id']}",
            str(obligation["source"]),
        ),
    )
    CapabilityGapRecorder.assert_domain_selection_required(receipt)
    return receipt


def derive_component_plan(
    *,
    repo: Path,
    catalog: PrimitiveCatalog,
    request: str,
    authority_reference: str,
    required_primitives: tuple[str, ...] = EXECUTION_PRIMITIVES,
    planning_obligations: tuple[Mapping[str, Any], ...] = (),
    source: PlanningSourceBundle | None = None,
    approved_domain_capabilities: frozenset[str] = frozenset(),
) -> DerivedPlan:
    """Derive capabilities and candidates only from repository-owned contracts."""

    primitive_ids = tuple(dict.fromkeys(required_primitives))
    execution_capabilities = tuple(
        RequiredCapability(
            _capability_id(primitive_id),
            (
                f"Provide the registered {primitive_id} capability "
                "required by SAGE request execution."
            ),
            True,
        )
        for primitive_id in primitive_ids
    )
    domain_capabilities = _domain_capabilities(planning_obligations)
    capabilities = execution_capabilities + domain_capabilities
    candidates: list[ComponentCandidate] = []
    for index, primitive_id in enumerate(primitive_ids, 1):
        entry = catalog.primitives.get(primitive_id)
        if not isinstance(entry, Mapping):
            continue
        source_path = _source_path(entry)
        source_exists = (repo / source_path).is_file()
        evidence = []
        receipt = entry.get("capability_gap_receipt")
        if isinstance(receipt, str) and receipt:
            evidence.append(receipt)
        evidence.append(
            f"registry:sage-workflow-primitives.json#{primitive_id}"
        )
        candidates.append(
            ComponentCandidate(
                f"CAND-{index:03d}",
                (_capability_id(primitive_id),),
                primitive_id,
                str(entry["version"]),
                source_path,
                str(entry["maturity"]),
                _selection_factors(entry, source_exists),
                tuple(evidence),
                (
                    f"The mandatory request-execution contract requires "
                    f"{primitive_id}; the live registry supplies its "
                    "published version and interface."
                ),
            )
        )

    candidates.extend(
        _domain_component_candidates(
            repo=repo,
            source=source,
            domain_capabilities=domain_capabilities,
            approved_domain_capabilities=approved_domain_capabilities,
            start_index=len(candidates) + 1,
        )
    )

    manifest = ComponentSelector().build_manifest(
        manifest_id=(
            f"SAGE-PLAN-COMP-{datetime.now().strftime('%Y%m%d')}-001"
        ),
        request=request,
        authority_receipt=authority_reference,
        capabilities=capabilities,
        candidates=tuple(candidates),
        approval={
            "status": "review-required",
            "reviewed_by": None,
            "reviewed_at": None,
            "rationale": (
                "The executor remains the operator-review boundary."
            ),
        },
    )
    gaps = [str(item) for item in manifest.get("capability_gap_receipts", [])]
    gap_receipt = None
    domain_gap_receipts: list[dict[str, Any]] = []
    if gaps:
        primitive_by_capability = {
            _capability_id(primitive_id): primitive_id
            for primitive_id in primitive_ids
        }
        primitive_gaps = [
            item for item in gaps
            if item in primitive_by_capability
        ]
        if primitive_gaps:
            missing_primitive = primitive_by_capability[primitive_gaps[0]]
            gap_receipt = _gap_receipt(
                repo=repo,
                catalog=catalog,
                request=request,
                authority_reference=authority_reference,
                manifest_reference=(
                    "request-planning-component-selection.json"
                ),
                missing_primitive=missing_primitive,
            )
        else:
            for sequence, missing_capability in enumerate(gaps, 1):
                domain_gap_receipts.append(
                    _domain_gap_receipt(
                        catalog=catalog,
                        request=request,
                        authority_reference=authority_reference,
                        manifest_reference=(
                            "request-planning-component-selection.json"
                        ),
                        missing_capability=missing_capability,
                        planning_obligations=planning_obligations,
                        gap_sequence=sequence,
                    )
                )
    else:
        ComponentSelector.require_complete(manifest)
    return DerivedPlan(
        [item.to_dict() for item in capabilities],
        [_candidate_payload(item) for item in candidates],
        manifest,
        gap_receipt,
        domain_gap_receipts,
    )



def _write_json(
    writer: AtomicFileWriter,
    path: Path,
    value: Mapping[str, Any],
) -> Path:
    writer.write_text(
        path,
        json.dumps(value, indent=4, sort_keys=False) + "\n",
        new_mode=0o600,
    )
    return path


def plan_request(
    repo: Path,
    request: str,
    source_path: Path,
    output: Path,
    *,
    approved_gap_set: Path | None = None,
) -> dict[str, Any]:
    """Plan one source-only package into the existing execution interface."""

    source = load_source_bundle(source_path, request)
    approved_domain_capabilities = _approved_domain_gap_capabilities(
        approved_gap_set,
        request,
        source,
    )
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = (
        Path("~/.local/state/kalaxy3/sage-request-planning").expanduser()
        / stamp
    )
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
        allowed_roots=(
            repo,
            state_dir,
            source.package_path.parent,
            output.parent,
        ),
        base_environment={
            name: ""
            for name in SECRET_ENVIRONMENT_NAMES
        },
    )
    inspector = GitInspector(repo, runner)
    writer = AtomicFileWriter((state_dir, output.parent))

    state: dict[str, Any] = {}

    def discovery_action() -> Mapping[str, Any]:
        discovery = SageDiscovery(repo, runner).literal(request)
        retrieval = runner.run(
            CommandSpec(
                primitive_id="command.run",
                label="Retrieve evidence for planned literal request",
                argv=("make", "sage-evidence-retrieve"),
                cwd=repo,
                environment={"SAGE_REQUEST": request},
                timeout_seconds=600,
            ),
            step_id="planning-evidence-retrieval",
        )
        resolved = resolve_planning_authority(repo, source, discovery)
        authority_reference = _write_json(
            writer,
            state_dir / "resolved-repository-authority.json",
            {
                "schema_version": "1.0",
                "request": request,
                "authority_mode": resolved["authority_mode"],
                "raw_inferred_contexts": list(resolved["raw_inferred_contexts"]),
                "contexts": list(resolved["contexts"]),
                "applicable_contexts": list(resolved.get("applicable_contexts", resolved["contexts"])),
                "authoritative_files": list(resolved["authoritative_files"]),
                "semantic_authority": resolved["semantic_authority"],
                "discovery_sha256": hashlib.sha256(discovery.stdout.encode("utf-8")).hexdigest(),
                "retrieval_sha256": retrieval.output_sha256,
            },
        )
        state["authority_reference"] = authority_reference
        return {
            "request": request,
            "authority_mode": resolved["authority_mode"],
            "raw_inferred_contexts": list(resolved["raw_inferred_contexts"]),
            "contexts": list(resolved["contexts"]),
            "applicable_contexts": list(resolved.get("applicable_contexts", resolved["contexts"])),
            "authority_reference": str(authority_reference),
        }
    def git_action() -> Mapping[str, Any]:
        inspector.require_clean()
        inspector.require_branch(
            str(source.manifest["repository"]["branch"])
        )
        inspector.require_head(
            str(source.manifest["repository"]["head"])
        )
        return inspector.snapshot().as_dict()

    def selection_action() -> Mapping[str, Any]:
        authority_reference = Path(str(state["authority_reference"]))
        semantic = source.semantic_authority or {}
        obligations = tuple(
            item for item in semantic.get("planning_obligations", [])
            if isinstance(item, Mapping)
        )
        plan = derive_component_plan(
            repo=repo,
            catalog=catalog,
            request=request,
            authority_reference=str(authority_reference),
            planning_obligations=obligations,
            source=source,
            approved_domain_capabilities=approved_domain_capabilities,
        )
        component_path = _write_json(
            writer,
            state_dir / "request-planning-component-selection.json",
            plan.selection_manifest,
        )
        state["plan"] = plan
        state["component_path"] = component_path
        return plan.selection_manifest

    def gap_action() -> Mapping[str, Any]:
        plan = state["plan"]
        if plan.gap_receipt is not None:
            gap_path = _write_json(
                writer,
                state_dir / "request-planning-capability-gap.json",
                plan.gap_receipt,
            )
            kind = plan.gap_receipt.get("gap_kind", "workflow-primitive")
            raise WorkflowError(
                f"request planning found an unresolved {kind} capability gap: "
                f"{gap_path}"
            )
        if plan.domain_gap_receipts:
            gap_items: list[dict[str, Any]] = []
            for index, receipt in enumerate(plan.domain_gap_receipts, 1):
                path = _write_json(
                    writer,
                    state_dir / (
                        "request-planning-capability-gap-"
                        f"{index:03d}.json"
                    ),
                    receipt,
                )
                gap_items.append(
                    {
                        "required_capability": receipt["required_capability"],
                        "gap_receipt": str(path),
                        "gap_receipt_sha256": hashlib.sha256(
                            path.read_bytes()
                        ).hexdigest(),
                    }
                )
            gap_set = {
                "schema_version": "1.0",
                "record_type": "sage-domain-capability-gap-set",
                "request": request,
                "created_at": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
                "authority_receipt": str(state["authority_reference"]),
                "component_manifest": str(state["component_path"]),
                "gap_count": len(gap_items),
                "gaps": gap_items,
                "approval": {
                    "status": "review-required",
                    "reviewed_by": None,
                    "reviewed_at": None,
                    "rationale": (
                        "Planner aggregates all unresolved Architect-confirmed "
                        "domain capabilities before stopping so class-level "
                        "remediation can be governed coherently."
                    ),
                },
            }
            gap_set_path = _write_json(
                writer,
                state_dir / "request-planning-capability-gap-set.json",
                gap_set,
            )
            raise WorkflowError(
                "request planning found "
                f"{len(gap_items)} unresolved domain-capability gaps in one "
                f"pass: {gap_set_path}"
            )
        return {
            "new_primitive_required": False,
            "composition_can_close_gap": True,
        }
    Workflow(
        workflow_id=WORKFLOW_ID,
        logger=logger,
        catalog=catalog,
        steps=(
            Step(
                "preserve-literal-request",
                "sage.discovery",
                discovery_action,
            ),
            Step(
                "collect-current-git-authority",
                "git.inspect",
                git_action,
            ),
            Step(
                "derive-request-components",
                "component.select",
                selection_action,
            ),
            Step(
                "record-capability-gaps",
                "capability.gap",
                gap_action,
            ),
        ),
    ).run()

    authority_reference = Path(str(state["authority_reference"]))
    component_path = Path(str(state["component_path"]))
    plan = state["plan"]
    evidence = list(source.manifest["evidence_references"])
    evidence.extend((str(authority_reference), str(component_path)))
    bundle = write_proposal_package(
        output,
        source,
        capabilities=plan.capabilities,
        candidates=plan.candidates,
        evidence_references=evidence,
        request=request,
    )
    closeout = CloseoutWriter(
        destination_directory=state_dir,
        primitive_registry=repo / "sage-workflow-primitives.json",
        event_log=state_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID,
        status="planned",
        used_primitives=PRIMITIVES_USED,
        details={
            "workflow_version": WORKFLOW_VERSION,
            "proposal": str(bundle.package_path),
            "declared_paths": list(bundle.declared_paths),
            "component_manifest": str(component_path),
            "external_candidate_semantics": False,
        },
    )
    return {
        "proposal": bundle.package_path,
        "state_dir": state_dir,
        "authority": authority_reference,
        "component_manifest": component_path,
        "closeout": closeout,
    }


def validate_reusable_plan_lineage(
    request: str,
    source_path: Path,
    proposal_path: Path,
) -> dict[str, str]:
    """Validate that an adopted proposal descends from the supplied confirmed planning source."""

    source = load_source_bundle(source_path.expanduser().resolve(), request)
    if source.semantic_authority is None:
        raise WorkflowError("adopted iterative lineage requires Architect-confirmed semantic authority")
    proposal = load_proposal(proposal_path.expanduser().resolve(), request)
    expected_sources = [
        {"path": item.path, "sha256": item.sha256, "mode": f"{item.mode:04o}"}
        for item in source.source_files
    ]
    checks = (
        ("repository", dict(source.manifest["repository"])),
        ("source_files", expected_sources),
        ("generated_paths", list(source.generated_paths)),
        ("reconcile_evidence_index", bool(source.manifest["reconcile_evidence_index"])),
        ("validation_commands", list(source.manifest["validation_commands"])),
        ("operator_plan", dict(source.manifest["operator_plan"])),
    )
    mismatches = [
        name for name, expected in checks
        if proposal.manifest.get(name) != expected
    ]
    if mismatches:
        raise WorkflowError(
            "adopted planning proposal does not descend from supplied planning source: "
            + ", ".join(mismatches)
        )
    return {
        "planning_source": str(source.package_path),
        "planning_proposal": str(proposal.package_path),
    }


def reuse_component_plan(
    repo: Path,
    request: str,
    source_path: Path,
    prior_proposal_path: Path,
    output: Path,
) -> dict[str, Any]:
    """Reuse a previously selected complete plan for implementation-local refinement."""

    source = load_source_bundle(source_path, request)
    prior = load_proposal(prior_proposal_path.expanduser().resolve(), request)
    manifest = prior.manifest
    if manifest.get("new_primitive_required") is not False:
        raise WorkflowError("implementation-local iteration cannot reuse a primitive-gap proposal")
    capabilities = manifest.get("capabilities")
    candidates = manifest.get("candidates")
    if not isinstance(capabilities, list) or not capabilities:
        raise WorkflowError("prior proposal has no reusable capabilities")
    if not isinstance(candidates, list) or not candidates:
        raise WorkflowError("prior proposal has no reusable candidates")
    evidence = list(manifest.get("evidence_references", []))
    evidence.append(f"implementation-local-plan-reuse:{prior.package_path}")
    bundle = write_proposal_package(
        output,
        source,
        capabilities=[dict(item) for item in capabilities],
        candidates=[dict(item) for item in candidates],
        evidence_references=list(dict.fromkeys(str(item) for item in evidence)),
        request=request,
    )
    return {
        "proposal": bundle.package_path,
        "source": source.package_path,
        "plan_reused": True,
        "evidence_retrieval_performed": False,
        "component_selection_performed": False,
    }
