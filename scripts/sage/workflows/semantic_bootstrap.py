#!/usr/bin/env python3
"""Accepted-action semantic understanding and repository planning-source bootstrap."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from request_planning import derive_applicable_contexts, write_source_package
from semantic_understanding import action_record_sha256, load_engineering_contribution, sha256_file
from workflow import (
    AtomicFileWriter,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    GitInspector,
    JsonlEventLogger,
    PrimitiveCatalog,
    SageDiscovery,
    Step,
    Workflow,
    WorkflowError,
    load_improvement_action,
    render_operator_command,
)

WORKFLOW_ID = "sage.semantic-bootstrap"
WORKFLOW_VERSION = "0.3.0"
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "sage.discovery",
    "git.inspect",
    "file.atomic-preserve-mode",
    "evidence.closeout",
    "workflow.composition",
    "sage.action-lifecycle",
)
SECRET_ENVIRONMENT_NAMES = ("GH_TOKEN", "GITHUB_TOKEN", "GITHUB_PAT", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "KUBECONFIG")
DEFAULT_VALIDATIONS = ("sage-guardrails", "sage-index-check", "sage-operating-contract-check")


def _write_json(writer: AtomicFileWriter, path: Path, value: Mapping[str, Any]) -> Path:
    writer.write_text(path, json.dumps(value, indent=4, sort_keys=False) + "\n", new_mode=0o600)
    return path


def _preflight_once(repo: Path, runner: CommandRunner, request: str):
    result = runner.run(CommandSpec(
        primitive_id="sage.discovery",
        label="Run one bounded semantic-bootstrap preflight",
        argv=("python3", "scripts/sage/sage-change-preflight.py", "--request", request),
        cwd=repo,
        environment={"SAGE_REQUEST": request},
    ))
    return SageDiscovery.parse(request, result.stdout)


def _context_dispositions(inferred: tuple[str, ...], applicable: tuple[str, ...]) -> list[dict[str, str]]:
    result = []
    all_ids = tuple(dict.fromkeys((*inferred, *applicable)))
    for context_id in all_ids:
        if context_id in applicable and context_id in inferred:
            disposition = "applicable"
        elif context_id in applicable:
            disposition = "applicable-by-proposed-path-or-dependency"
        else:
            disposition = "not-applicable-to-proposed-repository-scope"
        result.append({"context_id": context_id, "disposition": disposition})
    return result


NEGOTIATION_DISPOSITIONS = {"accept", "reject", "modify", "defer"}


def _negotiation_proposals(contribution: Any) -> list[dict[str, Any]]:
    proposals = [{
        "proposal_id": "implementation-scope",
        "target": "implementation_scope",
        "source": "engineering-contribution.files",
        "provenance": {"package_sha256": contribution.package_sha256},
        "value": list(contribution.paths),
        "prior_disposition": None,
    }]
    for field in ("assumptions", "alternatives"):
        for index, value in enumerate(contribution.manifest[field]):
            proposals.append({
                "proposal_id": f"{field[:-1]}-{index + 1:03d}",
                "target": field,
                "source": f"engineering-contribution.{field}[{index}]",
                "provenance": {"package_sha256": contribution.package_sha256},
                "value": str(value),
                "prior_disposition": None,
            })
    return proposals


def _disposition_template(proposals: list[dict[str, Any]], digest: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "record_type": "sage-architect-intent-dispositions",
        "semantic_understanding_sha256": digest,
        "actor_role": "architect",
        "dispositions": [
            {"proposal_id": item["proposal_id"], "disposition": None, "rationale": "", "modified_value": None, "new_basis": ""}
            for item in proposals
        ],
    }


def _apply_architect_dispositions(understanding: Mapping[str, Any], decisions: Mapping[str, Any], digest: str) -> dict[str, Any]:
    if decisions.get("record_type") != "sage-architect-intent-dispositions" or decisions.get("actor_role") != "architect":
        raise WorkflowError("Architect dispositions version/type/actor is invalid")
    if decisions.get("schema_version") != "1.0" or decisions.get("semantic_understanding_sha256") != digest:
        raise WorkflowError("Architect dispositions are not bound to the interpreted intent")
    proposals_raw = understanding.get("negotiation", {}).get("proposals")
    if not isinstance(proposals_raw, list) or not proposals_raw:
        raise WorkflowError("semantic understanding has no material proposals")
    proposals = {str(item["proposal_id"]): item for item in proposals_raw}
    raw = decisions.get("dispositions")
    if not isinstance(raw, list):
        raise WorkflowError("Architect dispositions must be a list")
    ids = [str(item.get("proposal_id")) for item in raw if isinstance(item, Mapping)]
    if len(ids) != len(raw) or len(set(ids)) != len(ids) or set(ids) != set(proposals):
        raise WorkflowError("every material proposal requires exactly one Architect disposition")

    normalized = []
    confirmed_scope = None
    for item in raw:
        proposal = proposals[str(item["proposal_id"])]
        disposition = item.get("disposition")
        if disposition not in NEGOTIATION_DISPOSITIONS:
            raise WorkflowError(f"{proposal['proposal_id']}: invalid Architect disposition")
        rationale = item.get("rationale", "")
        if not isinstance(rationale, str) or (disposition != "accept" and not rationale.strip()):
            raise WorkflowError(f"{proposal['proposal_id']}: non-accept disposition requires rationale")
        new_basis = item.get("new_basis", "")
        if proposal.get("prior_disposition") is not None and (not isinstance(new_basis, str) or not new_basis.strip()):
            raise WorkflowError(f"{proposal['proposal_id']}: resurfaced proposal requires materially new basis")
        modified = item.get("modified_value")
        if disposition != "modify" and modified is not None:
            raise WorkflowError(f"{proposal['proposal_id']}: modified_value is allowed only for modify")
        effective = modified if disposition == "modify" else proposal["value"]
        authoritative = disposition in {"accept", "modify"}
        if proposal["target"] == "implementation_scope" and authoritative:
            if not isinstance(effective, list) or not effective or not all(isinstance(path, str) and path for path in effective):
                raise WorkflowError("confirmed implementation scope must be a non-empty path list")
            confirmed_scope = list(dict.fromkeys(effective))
        normalized.append({
            "proposal_id": proposal["proposal_id"],
            "target": proposal["target"],
            "source": proposal["source"],
            "provenance": proposal["provenance"],
            "prior_disposition": proposal.get("prior_disposition"),
            "disposition": disposition,
            "rationale": rationale.strip(),
            "new_basis": new_basis.strip() if isinstance(new_basis, str) and new_basis.strip() else None,
            "authority_effect": "authoritative-in-confirmed-intent" if authoritative else "evidence-only",
            "effective_value": effective if authoritative else None,
        })
    if confirmed_scope is None:
        raise WorkflowError("semantic confirmation cannot proceed without an authoritative implementation scope")
    result = json.loads(json.dumps(understanding))
    result["interpretation"]["implementation_scope"] = confirmed_scope
    result["negotiation"] = {
        "status": "architect-dispositioned",
        "proposals": proposals_raw,
        "dispositions": normalized,
        "non_authoritative_proposals": [item["proposal_id"] for item in normalized if item["authority_effect"] == "evidence-only"],
    }
    if isinstance(result.get("assertions"), dict):
        result["assertions"]["meaning"] = "architect-confirmed"
    return result


def _request_commit_subject(request: str) -> str:
    first = " ".join(request.strip().splitlines()[0].split()) if request.strip() else ""
    prefix = "Implement the next coherent slice of SAGE-ACTION-20260813-001: "
    first = first[len(prefix):] if first.startswith(prefix) else first
    return (first.rstrip(".") or "Implement governed SAGE request")[:120]
def _runtime(repo: Path, state_dir: Path):
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(state_dir / "events.jsonl", WORKFLOW_ID, primitive_versions=catalog.versions_for(PRIMITIVES_USED))
    runner = CommandRunner(logger, allowed_roots=(repo, state_dir, Path("~/Downloads").expanduser()), base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES})
    writer = AtomicFileWriter((state_dir, Path("~/Downloads").expanduser()))
    return catalog, logger, runner, writer, GitInspector(repo, runner)


def begin_bootstrap(repo: Path, action_id: str, request: str, contribution_path: Path) -> Mapping[str, Any]:
    repo = repo.expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = Path("~/.local/state/kalaxy3/sage-semantic-bootstrap").expanduser() / stamp
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog, logger, runner, writer, inspector = _runtime(repo, state_dir)
    state: dict[str, Any] = {}

    def action_contract() -> Mapping[str, Any]:
        action = load_improvement_action(repo, action_id)
        if action.get("current_status") != "accepted":
            raise WorkflowError(f"{action_id} must be accepted before semantic bootstrap")
        state["action"] = action
        return {"action_id": action_id, "status": "accepted", "record_sha256": action_record_sha256(action)}

    def git_authority() -> Mapping[str, Any]:
        inspector.require_clean()
        head = inspector.require_upstream_equal()
        branch = inspector.branch()
        if branch == "main":
            raise WorkflowError("semantic bootstrap requires a synchronized non-main feature branch")
        state["branch"] = branch
        state["head"] = head
        return inspector.snapshot().as_dict()

    def contribution_action() -> Mapping[str, Any]:
        contribution = load_engineering_contribution(contribution_path)
        state["contribution"] = contribution
        return {
            "package": str(contribution.package_path),
            "package_sha256": contribution.package_sha256,
            "paths": list(contribution.paths),
        }

    def discovery_action() -> Mapping[str, Any]:
        preflight = _preflight_once(repo, runner, request)
        contribution = state["contribution"]
        applicable = derive_applicable_contexts(repo, contribution.paths)
        state["preflight"] = preflight
        state["applicable"] = applicable
        return {
            "inferred_contexts": list(preflight.contexts),
            "applicable_contexts": list(applicable),
            "context_dispositions": _context_dispositions(preflight.contexts, applicable),
        }

    def interpretation_action() -> Mapping[str, Any]:
        action = state["action"]
        contribution = state["contribution"]
        preflight = state["preflight"]
        applicable = state["applicable"]
        understanding = {
            "schema_version": "1.0",
            "record_type": "sage-semantic-understanding",
            "action": {
                "action_id": action_id,
                "status": "accepted",
                "record_sha256": action_record_sha256(action),
                "desired_outcome": action.get("desired_outcome"),
            },
            "literal_request": request,
            "contribution": {
                "package": str(contribution.package_path),
                "package_sha256": contribution.package_sha256,
                "contributor": dict(contribution.manifest["contributor"]),
                "summary": contribution.manifest["summary"],
                "rationale": contribution.manifest["rationale"],
                "assumptions": list(contribution.manifest["assumptions"]),
                "alternatives": list(contribution.manifest["alternatives"]),
                "proposed_paths": list(contribution.paths),
            },
            "interpretation": {
                "implementation_scope": list(contribution.paths),
                "inferred_contexts": list(preflight.contexts),
                "applicable_contexts": list(applicable),
                "context_dispositions": _context_dispositions(preflight.contexts, applicable),
                "goose_chase_policy": "one-preflight-pass; unrelated inferred contexts are dispositioned rather than recursively expanded",
            },
            "negotiation": {
                "status": "architect-disposition-required",
                "proposals": _negotiation_proposals(contribution),
            },
            "assertions": {
                "meaning": "architect-confirmation-required",
                "feasibility": "not-yet-established",
                "authorization": "accepted-action-does-not-yet-authorize-source-generation",
            },
        }
        understanding_path = _write_json(writer, state_dir / "semantic-understanding.json", understanding)
        state["understanding_path"] = understanding_path
        state["understanding_sha"] = sha256_file(understanding_path)
        state["dispositions_path"] = _write_json(
            writer,
            state_dir / "architect-dispositions.json",
            _disposition_template(understanding["negotiation"]["proposals"], state["understanding_sha"]),
        )
        return {
            "semantic_understanding": str(understanding_path),
            "sha256": state["understanding_sha"],
            "architect_dispositions": str(state["dispositions_path"]),
        }

    Workflow(
        workflow_id=WORKFLOW_ID,
        logger=logger,
        catalog=catalog,
        steps=(
            Step("read-accepted-action", "sage.action-lifecycle", action_contract),
            Step("collect-current-git-authority", "git.inspect", git_authority),
            Step("load-engineering-contribution", "workflow.composition", contribution_action),
            Step("interpret-applicable-contexts", "sage.discovery", discovery_action),
            Step("record-semantic-understanding", "file.atomic-preserve-mode", interpretation_action),
        ),
    ).run()

    action = state["action"]
    contribution = state["contribution"]
    applicable = state["applicable"]
    understanding_path = state["understanding_path"]
    understanding_sha = state["understanding_sha"]
    persisted = {
        "schema_version": "1.0",
        "record_type": "sage-semantic-bootstrap-state",
        "action_id": action_id,
        "action_record_sha256": action_record_sha256(action),
        "request": request,
        "repository": {"branch": state["branch"], "head": state["head"]},
        "contribution": str(contribution.package_path),
        "contribution_sha256": contribution.package_sha256,
        "semantic_understanding": str(understanding_path),
        "semantic_understanding_sha256": understanding_sha,
        "applicable_contexts": list(applicable),
        "architect_dispositions": str(state["dispositions_path"]),
        "status": "architect-confirmation-required",
    }
    state_path = _write_json(writer, state_dir / "state.json", persisted)
    CloseoutWriter(
        destination_directory=state_dir,
        primitive_registry=repo / "sage-workflow-primitives.json",
        event_log=state_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID,
        status="architect-confirmation-required",
        used_primitives=PRIMITIVES_USED,
        details={"state": str(state_path), "semantic_understanding": str(understanding_path), "architect_dispositions": str(state["dispositions_path"])},
    )
    confirmation_command = render_operator_command(
        (
            "python3",
            "scripts/sage/sage-action-bootstrap.py",
            "--continue-state", str(state_path),
            "--confirm-understanding-sha256", understanding_sha,
            "--actor", "architect",
            "--dispositions", str(state["dispositions_path"]),
        )
    )
    return {
        "status": persisted["status"],
        "state": str(state_path),
        "semantic_understanding": str(understanding_path),
        "semantic_understanding_sha256": understanding_sha,
        "architect_dispositions": str(state["dispositions_path"]),
        "confirmation_command": confirmation_command,
    }



def default_planning_source_path(action_id: str, confirmation_sha256: str) -> Path:
    """Return the immutable default planning-source path for one confirmed semantic slice."""

    if not action_id or "/" in action_id or "\\" in action_id:
        raise WorkflowError("semantic bootstrap action ID is invalid for planning-source identity")
    if (
        len(confirmation_sha256) != 64
        or confirmation_sha256 != confirmation_sha256.lower()
        or any(character not in "0123456789abcdef" for character in confirmation_sha256)
    ):
        raise WorkflowError("semantic confirmation digest is invalid for planning-source identity")
    return Path("~/Downloads").expanduser() / f"sage-action-{action_id}-semantic-{confirmation_sha256}-source.zip"

def continue_bootstrap(repo: Path, state_path: Path, confirmation_sha256: str, actor: str, output: Path | None = None, dispositions_path: Path | None = None) -> Mapping[str, Any]:
    if actor != "architect":
        raise WorkflowError("semantic confirmation must be exercised by the Architect role")
    repo = repo.expanduser().resolve()
    state_path = state_path.expanduser().resolve()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") != "architect-confirmation-required":
        raise WorkflowError("semantic bootstrap state is not awaiting Architect confirmation")
    if confirmation_sha256 != state.get("semantic_understanding_sha256"):
        raise WorkflowError("Architect confirmation digest does not match interpreted intent")
    state_dir = state_path.parent
    _, logger, _, writer, inspector = _runtime(repo, state_dir)
    inspector.require_clean()
    inspector.require_branch(str(state["repository"]["branch"]))
    inspector.require_head(str(state["repository"]["head"]))
    inspector.require_upstream_equal()
    action = load_improvement_action(repo, str(state["action_id"]))
    if action.get("current_status") != "accepted" or action_record_sha256(action) != state.get("action_record_sha256"):
        raise WorkflowError("accepted action changed after semantic interpretation")
    contribution_path = Path(str(state["contribution"])).expanduser().resolve()
    if sha256_file(contribution_path) != state.get("contribution_sha256"):
        raise WorkflowError("engineering contribution changed after semantic interpretation")
    contribution = load_engineering_contribution(contribution_path)
    confirmed_understanding_path = Path(str(state["semantic_understanding"])).expanduser().resolve()
    confirmed_understanding_sha256 = confirmation_sha256
    if state.get("architect_dispositions"):
        if dispositions_path is None:
            raise WorkflowError("Architect dispositions are required before semantic confirmation")
        understanding = json.loads(confirmed_understanding_path.read_text(encoding="utf-8"))
        decisions_path = dispositions_path.expanduser().resolve()
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
        confirmed = _apply_architect_dispositions(understanding, decisions, confirmation_sha256)
        confirmed_understanding_path = _write_json(writer, state_dir / "semantic-understanding-confirmed.json", confirmed)
        confirmed_understanding_sha256 = sha256_file(confirmed_understanding_path)
        state["architect_dispositions_evidence"] = str(decisions_path)
        state["architect_dispositions_sha256"] = sha256_file(decisions_path)
        state["confirmed_semantic_understanding"] = str(confirmed_understanding_path)
        state["confirmed_semantic_understanding_sha256"] = confirmed_understanding_sha256
    output = (output or default_planning_source_path(str(state["action_id"]), confirmed_understanding_sha256)).expanduser().resolve()
    validations = [{"label": f"Run {target}", "argv": ["make", target], "timeout_seconds": 3600} for target in DEFAULT_VALIDATIONS]
    confirmation = {
        "schema_version": "1.0",
        "record_type": "sage-semantic-confirmation",
        "action_id": str(state["action_id"]),
        "actor_role": actor,
        "semantic_understanding_sha256": confirmed_understanding_sha256,
        "interpreted_understanding_sha256": confirmation_sha256,
        "architect_dispositions_sha256": state.get("architect_dispositions_sha256"),
        "meaning": "architect-confirmed",
        "recorded_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    confirmation_path = _write_json(writer, state_dir / "semantic-confirmation.json", confirmation)
    feasibility = {
        "schema_version": "1.0",
        "record_type": "sage-semantic-bootstrap-feasibility",
        "action_id": str(state["action_id"]),
        "status": "sufficient-for-planning-source",
        "observed": {
            "repository_clean": True,
            "branch": inspector.branch(),
            "head": inspector.head(),
            "upstream_equal": True,
            "accepted_action_unchanged": True,
            "engineering_contribution_unchanged": True,
        },
        "limitations": [
            "Runtime behavior is not proven until the planned source is applied and deterministic validations pass.",
            "Outcome feasibility and external-framework review remain downstream acceptance obligations.",
        ],
    }
    feasibility_path = _write_json(writer, state_dir / "feasibility.json", feasibility)
    authorization = {
        "schema_version": "1.0",
        "record_type": "sage-semantic-bootstrap-authorization",
        "action_id": str(state["action_id"]),
        "status": "planning-source-generation-authorized",
        "basis": ["accepted improvement action", "Architect semantic confirmation", "sufficient planning-source feasibility"],
        "repository_mutation_authorized": False,
        "downstream_authority": "sage-request-execute",
    }
    authorization_path = _write_json(writer, state_dir / "authorization.json", authorization)
    evidence = [
        f"action:{state['action_id']}",
        f"action-record-sha256:{state['action_record_sha256']}",
        f"engineering-contribution-sha256:{state['contribution_sha256']}",
        f"semantic-understanding-sha256:{confirmed_understanding_sha256}",
        f"semantic-confirmation-sha256:{sha256_file(confirmation_path)}",
        f"feasibility-sha256:{sha256_file(feasibility_path)}",
        f"authorization-sha256:{sha256_file(authorization_path)}",
        "authority:sage-change-authority.json",
        "bootstrap-exception:one-time-legacy-source-format-generated-by-repository-owned-code",
    ]
    confirmed = json.loads(confirmed_understanding_path.read_text(encoding="utf-8"))
    confirmed_scope = tuple(str(item) for item in confirmed["interpretation"]["implementation_scope"])
    source_by_path = {item.path: item for item in contribution.source_files}
    if set(confirmed_scope) - set(source_by_path):
        raise WorkflowError("confirmed implementation scope references files absent from the engineering contribution")
    confirmed_source_files = tuple(source_by_path[path] for path in confirmed_scope)
    source = write_source_package(
        output,
        str(state["request"]),
        repository={"branch": inspector.branch(), "head": inspector.head()},
        source_files=confirmed_source_files,
        evidence_references=evidence,
        validation_commands=validations,
        operator_plan={"commit_message": _request_commit_subject(str(state["request"])), "push_remote": "origin"},
        semantic_understanding_path=confirmed_understanding_path,
        semantic_confirmation_path=confirmation_path,
    )
    state["status"] = "planning-source-ready"
    state["semantic_confirmation"] = str(confirmation_path)
    state["feasibility"] = str(feasibility_path)
    state["authorization"] = str(authorization_path)
    state["planning_source"] = str(source.package_path)
    _write_json(writer, state_path, state)
    CloseoutWriter(
        destination_directory=state_dir,
        primitive_registry=repo / "sage-workflow-primitives.json",
        event_log=state_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID,
        status="planning-source-ready",
        used_primitives=PRIMITIVES_USED,
        details={
            "state": str(state_path),
            "semantic_understanding": str(state["semantic_understanding"]),
            "semantic_confirmation": str(confirmation_path),
            "feasibility": str(feasibility_path),
            "authorization": str(authorization_path),
            "planning_source": str(source.package_path),
        },
    )
    next_command = render_operator_command(
        (
            "env",
            f"SAGE_REQUEST={state['request']}",
            f"SAGE_SOURCE={source.package_path}",
            "make",
            "sage-request-plan",
        )
    )
    return {
        "status": state["status"],
        "source": str(source.package_path),
        "state": str(state_path),
        "next_command": next_command,
    }
