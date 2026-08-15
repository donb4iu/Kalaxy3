#!/usr/bin/env python3
"""Repository-owned planning composition ahead of SAGE request execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from request_planning import load_source_bundle, resolve_planning_authority, write_proposal_package
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
WORKFLOW_VERSION = "1.0.0"
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


def derive_component_plan(
    *,
    repo: Path,
    catalog: PrimitiveCatalog,
    request: str,
    authority_reference: str,
    required_primitives: tuple[str, ...] = EXECUTION_PRIMITIVES,
) -> DerivedPlan:
    """Derive capabilities and candidates only from repository-owned contracts."""

    primitive_ids = tuple(dict.fromkeys(required_primitives))
    capabilities = tuple(
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
    gaps = list(manifest.get("capability_gap_receipts", []))
    gap_receipt = None
    if gaps:
        missing_capability = str(gaps[0])
        primitive_by_capability = {
            _capability_id(primitive_id): primitive_id
            for primitive_id in primitive_ids
        }
        missing_primitive = primitive_by_capability[missing_capability]
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
        ComponentSelector.require_complete(manifest)

    return DerivedPlan(
        [item.to_dict() for item in capabilities],
        [_candidate_payload(item) for item in candidates],
        manifest,
        gap_receipt,
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
) -> dict[str, Any]:
    """Plan one source-only package into the existing execution interface."""

    source = load_source_bundle(source_path, request)
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
        plan = derive_component_plan(
            repo=repo,
            catalog=catalog,
            request=request,
            authority_reference=str(authority_reference),
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
            raise WorkflowError(
                "request planning found an unresolved capability gap: "
                f"{gap_path}"
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
