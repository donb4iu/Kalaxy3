"""Fresh SAGE-context LLM workflow management over existing intent-to-outcome boundaries."""

from __future__ import annotations

import hashlib
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping

from llm_role_invocation import (
    RoleInvocationError,
    build_invocation,
    invoke_ollama_json,
    new_state_dir,
    persist_json,
)
from semantic_understanding import load_engineering_contribution
from workflows.intent_to_outcome import (
    begin_candidate_iteration,
    objective_route_snapshot,
)


ROLE = "llm-workflow-manager"
REENTRY_BOUNDARIES = (
    "implementation-local",
    "planning",
    "semantic-confirmation",
    "authority",
)
DECISIONS = (*REENTRY_BOUNDARIES, "architect-clarification-required")

SYSTEM_INSTRUCTION = """\
You are the SAGE llm-workflow-manager specialized role.
You are advisory. You do not hold Architect authority and you do not execute commands.

Use only the supplied SAGE invocation envelope and your general engineering knowledge.
Do not assume or reconstruct prior Architect or role conversations.

Your job is to decide the EARLIEST existing SAGE intent-to-outcome re-entry boundary
required by the supplied trigger and authoritative context.

Available execution boundaries:
- implementation-local: objective meaning, authority, confirmed implementation envelope,
  safety/trust boundaries, and material risk are unchanged; only mechanical/source
  correction inside already-approved scope is needed.
- planning: confirmed semantic meaning and authority remain valid, but capability/path
  selection must be recomputed.
- semantic-confirmation: objective meaning, scope, trust boundary, requirements,
  constraints, intended outcome, or other Architect-owned semantic condition changed.
- authority: governing authority changed, is missing, or cannot be established.
- architect-clarification-required: supplied context is insufficient to reliably
  understand the Architect's intent. Do not authorize repository spelunking merely
  because intent is vague.

Do not expand the Definition of Done because an adjacent defect, experiment, or
interesting observation exists. A discovered condition changes the active path only
when it deterministically affects achieving/proving the current objective or the
Architect explicitly changed/delegated the objective. Otherwise preserve it as an
observation and continue the objective.

Prefer deterministic SAGE capability when the correct action is already established.
Use semantic judgment only for the boundary decision requested here.

Return exactly one JSON object and no prose:
{
  "schema_version": "1.0",
  "record_type": "sage-llm-workflow-manager-decision",
  "producer_class": "llm-workflow-manager",
  "authority": "advisory",
  "objective_id": "<exact supplied objective_id>",
  "decision": "<one allowed decision>",
  "objective_effect": "deterministic|possible|none|unknown",
  "material_change": true|false,
  "reasoning_summary": "<concise decision rationale, not chain-of-thought>",
  "architect_question": null or "<single concise clarification question>",
  "observations_not_path_changing": ["..."]
}

Consistency:
- architect-clarification-required requires objective_effect="unknown",
  material_change=false, and a non-empty architect_question.
- implementation-local requires material_change=false.
- semantic-confirmation or authority requires material_change=true.
- other decisions require architect_question=null.
"""


class WorkflowManagerError(RuntimeError):
    """Fail-closed workflow-manager error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _contribution_context(path: Path) -> dict[str, Any]:
    contribution = load_engineering_contribution(path.expanduser().resolve())
    return {
        "package_sha256": contribution.package_sha256,
        "manifest": dict(contribution.manifest),
        "source_files": [
            {
                "path": item.path,
                "sha256": item.sha256,
                "mode": format(item.mode, "04o"),
            }
            for item in contribution.source_files
        ],
    }


def build_context(
    repo: Path,
    state_path: Path,
    contribution: Path,
    *,
    trigger: str,
    parent_checkpoint: str,
    affected_obligations: list[str] | None = None,
    approved_gap_set: Path | None = None,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Construct SAGE-owned context for one fresh workflow decision."""
    route = dict(objective_route_snapshot(repo, state_path))
    objective_id = str(route.get("objective_id", "")).strip()
    if not objective_id:
        raise WorkflowManagerError("objective route has no objective_id")
    if not trigger.strip():
        raise WorkflowManagerError("workflow-manager trigger is required")
    request = {
        "trigger": trigger.strip(),
        "parent_checkpoint": parent_checkpoint.strip(),
        "affected_obligations": list(affected_obligations or []),
        "approved_gap_set": (
            {
                "sha256": _sha256(approved_gap_set.expanduser().resolve()),
            }
            if approved_gap_set is not None
            else None
        ),
        "allowed_decisions": list(DECISIONS),
    }
    context = {
        "objective_route": route,
        "engineering_contribution": _contribution_context(contribution),
        "governance": {
            "dod_expansion_by_discovery_allowed": False,
            "observations_create_automatic_work": False,
            "architect_intent_ambiguity_requires_clarification": True,
            "delegated_discovery_requires_architect_or_clear_execution_need": True,
            "deterministic_sage_semantics_preferred_when_sufficient": True,
        },
    }
    return objective_id, request, context


def validate_decision(
    decision: Mapping[str, Any],
    *,
    objective_id: str,
) -> dict[str, Any]:
    """Validate one advisory workflow-manager decision."""
    required = {
        "schema_version",
        "record_type",
        "producer_class",
        "authority",
        "objective_id",
        "decision",
        "objective_effect",
        "material_change",
        "reasoning_summary",
        "architect_question",
        "observations_not_path_changing",
    }
    if set(decision) != required:
        raise WorkflowManagerError("workflow-manager decision fields are invalid")
    if decision.get("schema_version") != "1.0":
        raise WorkflowManagerError("workflow-manager schema_version is invalid")
    if decision.get("record_type") != "sage-llm-workflow-manager-decision":
        raise WorkflowManagerError("workflow-manager record_type is invalid")
    if decision.get("producer_class") != ROLE:
        raise WorkflowManagerError("workflow-manager producer_class is invalid")
    if decision.get("authority") != "advisory":
        raise WorkflowManagerError("workflow-manager authority must be advisory")
    if decision.get("objective_id") != objective_id:
        raise WorkflowManagerError("workflow-manager objective_id changed")
    selected = decision.get("decision")
    if selected not in DECISIONS:
        raise WorkflowManagerError("workflow-manager decision is unsupported")
    if decision.get("objective_effect") not in {
        "deterministic",
        "possible",
        "none",
        "unknown",
    }:
        raise WorkflowManagerError("workflow-manager objective_effect is invalid")
    if not isinstance(decision.get("material_change"), bool):
        raise WorkflowManagerError("workflow-manager material_change must be boolean")
    if not isinstance(decision.get("reasoning_summary"), str) or not decision[
        "reasoning_summary"
    ].strip():
        raise WorkflowManagerError("workflow-manager reasoning_summary is required")
    observations = decision.get("observations_not_path_changing")
    if not isinstance(observations, list) or not all(
        isinstance(item, str) and item.strip() for item in observations
    ):
        raise WorkflowManagerError(
            "workflow-manager observations_not_path_changing is invalid"
        )
    question = decision.get("architect_question")
    if selected == "architect-clarification-required":
        if decision.get("objective_effect") != "unknown":
            raise WorkflowManagerError(
                "architect clarification requires unknown objective effect"
            )
        if decision.get("material_change") is not False:
            raise WorkflowManagerError(
                "architect clarification may not assert a material change"
            )
        if not isinstance(question, str) or not question.strip():
            raise WorkflowManagerError(
                "architect clarification requires one question"
            )
    else:
        if question is not None:
            raise WorkflowManagerError(
                "non-clarification workflow decision may not ask Architect question"
            )
    if selected == "implementation-local" and decision.get("material_change"):
        raise WorkflowManagerError(
            "implementation-local decision may not assert material change"
        )
    if selected in {"semantic-confirmation", "authority"} and not decision.get(
        "material_change"
    ):
        raise WorkflowManagerError(
            f"{selected} decision requires material_change=true"
        )
    return dict(decision)


def manage_candidate_iteration(
    repo: Path,
    state_path: Path,
    contribution: Path,
    *,
    trigger: str,
    parent_checkpoint: str,
    endpoint: str,
    model: str,
    affected_obligations: list[str] | None = None,
    approved_gap_set: Path | None = None,
) -> Mapping[str, Any]:
    """Let a fresh SAGE-context role choose the existing governed re-entry boundary."""
    objective_id, request, context = build_context(
        repo,
        state_path,
        contribution,
        trigger=trigger,
        parent_checkpoint=parent_checkpoint,
        affected_obligations=affected_obligations,
        approved_gap_set=approved_gap_set,
    )
    envelope = build_invocation(
        role=ROLE,
        objective_id=objective_id,
        request=request,
        context=context,
    )
    state_dir = new_state_dir("workflow-manager")
    persist_json(state_dir / "workflow-manager-invocation.json", envelope)
    raw_decision, receipt = invoke_ollama_json(
        envelope=envelope,
        system_instruction=SYSTEM_INSTRUCTION,
        endpoint=endpoint,
        model=model,
    )
    decision = validate_decision(raw_decision, objective_id=objective_id)
    persist_json(state_dir / "workflow-manager-decision.json", decision)
    persist_json(state_dir / "workflow-manager-invocation-receipt.json", receipt)

    if decision["decision"] == "architect-clarification-required":
        return {
            "status": "architect-clarification-required",
            "objective_id": objective_id,
            "architect_question": decision["architect_question"],
            "workflow_manager_decision": str(
                state_dir / "workflow-manager-decision.json"
            ),
            "repository_mutation": False,
            "next_boundary": "architect-intent",
        }

    result = begin_candidate_iteration(
        repo,
        state_path,
        contribution,
        trigger=trigger,
        reentry_boundary=str(decision["decision"]),
        parent_checkpoint=parent_checkpoint,
        affected_obligations=affected_obligations,
        approved_gap_set=approved_gap_set,
    )
    return {
        "status": result.get("status"),
        "objective_id": objective_id,
        "selected_reentry_boundary": decision["decision"],
        "workflow_manager_decision": str(
            state_dir / "workflow-manager-decision.json"
        ),
        "workflow_manager_receipt": str(
            state_dir / "workflow-manager-invocation-receipt.json"
        ),
        "sage_result": dict(result),
    }


def self_test(repo: Path) -> None:
    """Prove fresh context, bounded decision validation, and no inherited chat."""
    observed: list[dict[str, Any]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length))
            observed.append(body)
            envelope = json.loads(body["messages"][1]["content"])
            decision = {
                "schema_version": "1.0",
                "record_type": "sage-llm-workflow-manager-decision",
                "producer_class": ROLE,
                "authority": "advisory",
                "objective_id": envelope["objective_id"],
                "decision": "planning",
                "objective_effect": "deterministic",
                "material_change": False,
                "reasoning_summary": (
                    "Semantic meaning is preserved but path selection must be recomputed."
                ),
                "architect_question": None,
                "observations_not_path_changing": [
                    "Routine Git chronology remains execution provenance."
                ],
            }
            response = {
                "model": "fixture-model",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(decision),
                    "thinking": "private fixture thinking",
                },
                "done": True,
            }
            raw = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: object) -> None:
            return

    # Validate decision contract without constructing a full intent fixture.
    validated = validate_decision(
        {
            "schema_version": "1.0",
            "record_type": "sage-llm-workflow-manager-decision",
            "producer_class": ROLE,
            "authority": "advisory",
            "objective_id": "SAGE-ACTION-FIXTURE",
            "decision": "implementation-local",
            "objective_effect": "deterministic",
            "material_change": False,
            "reasoning_summary": "Same objective and authority; mechanical correction only.",
            "architect_question": None,
            "observations_not_path_changing": ["Unrelated documentation change."],
        },
        objective_id="SAGE-ACTION-FIXTURE",
    )
    if validated["decision"] != "implementation-local":
        raise RuntimeError("workflow-manager validation changed decision")

    clarification = validate_decision(
        {
            "schema_version": "1.0",
            "record_type": "sage-llm-workflow-manager-decision",
            "producer_class": ROLE,
            "authority": "advisory",
            "objective_id": "SAGE-ACTION-FIXTURE",
            "decision": "architect-clarification-required",
            "objective_effect": "unknown",
            "material_change": False,
            "reasoning_summary": "The target of the Architect's statement is ambiguous.",
            "architect_question": "Which UI example set do you mean?",
            "observations_not_path_changing": [],
        },
        objective_id="SAGE-ACTION-FIXTURE",
    )
    if clarification["architect_question"] is None:
        raise RuntimeError("workflow-manager clarification lost Architect question")

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        envelope = build_invocation(
            role=ROLE,
            objective_id="SAGE-ACTION-FIXTURE",
            request={"allowed_decisions": list(DECISIONS)},
            context={"objective_route": {"objective_id": "SAGE-ACTION-FIXTURE"}},
        )
        result, receipt = invoke_ollama_json(
            envelope=envelope,
            system_instruction=SYSTEM_INSTRUCTION,
            endpoint=f"http://127.0.0.1:{server.server_port}",
            model="fixture-model",
        )
        validate_decision(result, objective_id="SAGE-ACTION-FIXTURE")
        if len(observed) != 1:
            raise RuntimeError("expected one fresh provider call")
        messages = observed[0].get("messages")
        if not isinstance(messages, list) or len(messages) != 2:
            raise RuntimeError("workflow manager received inherited chat history")
        if [item.get("role") for item in messages] != ["system", "user"]:
            raise RuntimeError("workflow manager messages are not fresh")
        sent = json.loads(messages[1]["content"])
        policy = sent["context_policy"]
        if policy["architect_chat_history_included"]:
            raise RuntimeError("Architect chat leaked into workflow-manager invocation")
        if policy["role_chat_history_included"]:
            raise RuntimeError("role chat leaked into workflow-manager invocation")
        if receipt["architect_chat_history_included"]:
            raise RuntimeError("receipt incorrectly reports Architect chat")
        rendered = json.dumps(receipt)
        if "private fixture thinking" in rendered:
            raise RuntimeError("provider thinking leaked into SAGE receipt")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    print("PASS workflow manager uses one fresh SAGE-context provider call")
    print("PASS workflow manager chooses only existing SAGE re-entry boundaries")
    print("PASS vague Architect intent can return architect-clarification-required")
    print("PASS Architect/role chat history is absent below the intent boundary")
    print("PASS provider thinking is not persisted as SAGE evidence")
