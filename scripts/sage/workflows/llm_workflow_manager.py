"""Fresh SAGE-context workflow judgment over existing intent-to-outcome boundaries."""

from __future__ import annotations

import hashlib
import json
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping

from llm_role_invocation import (
    RoleInvocationError,
    build_invocation,
    invoke_ollama_json,
    new_state_dir,
    resolve_ollama_runtime,
    stable_json,
)
from semantic_understanding import load_engineering_contribution
from workflow import AtomicFileWriter
from workflows.intent_to_outcome import (
    begin_candidate_iteration,
    objective_route_snapshot,
)

PRIMITIVES_USED = ("file.atomic-preserve-mode",)

ROLE = "llm-workflow-manager"
REENTRY_BOUNDARIES = (
    "implementation-local",
    "planning",
    "semantic-confirmation",
    "authority",
)
DECISIONS = (*REENTRY_BOUNDARIES, "architect-clarification-required")
RUNTIME_BOUNDARY = "workflow-manager-runtime-qualification"

REGRESSION_LITERAL_REQUEST = (
    "Operationalize SAGE so the persistent Architect-facing LLM participates only "
    "through published SAGE request/continuation interfaces. Below that boundary, "
    "semantic workflow decisions must use fresh LLM invocations whose context is "
    "constructed and owned by SAGE, with no inherited Architect-chat or prior "
    "role-chat context. SAGE retains authoritative state, authority, deterministic "
    "execution, recovery, evidence, and handoffs; deterministic SAGE semantics "
    "should replace LLM judgment wherever sufficient. Reuse the existing "
    "workflow-manager/isolation candidate work and accepted architecture/DoD "
    "evidence where fit rather than rebuilding it. The first 80/20 proof is one "
    "real objective driven through this boundary end-to-end. If required machinery "
    "or inference capability is missing, report that as the governed blocking "
    "boundary rather than having the persistent LLM implement around SAGE."
)

SYSTEM_INSTRUCTION = 'You are the SAGE llm-workflow-manager specialized advisory role.\n\nReason only about the supplied objective state and trigger. Do not emit SAGE control\nrecords, repository mechanics, authority metadata, provenance metadata, lifecycle\ntokens, receipts, schema versions, record types, objective identifiers, or derived\ninvariant fields. SAGE owns all of those.\n\nReturn only the smallest role-level semantic judgment needed for SAGE to continue:\n{\n  "intent": "bounded-correction|replan|meaning-change|authority-problem|need-clarification",\n  "rationale": "<concise explanation, not chain-of-thought>",\n  "clarification_question": null or "<one concise question>",\n  "observations": ["<optional non-path-changing observation>"]\n}\n\nSemantic meanings:\n- bounded-correction: objective meaning/authority are unchanged; only bounded implementation repair is needed.\n- replan: objective meaning/authority are unchanged; SAGE should recompute capability/path selection.\n- meaning-change: objective meaning, scope, trust boundary, requirements, constraints, or intended outcome materially changed.\n- authority-problem: governing authority changed, is missing, or cannot be established.\n- need-clarification: the supplied context is insufficient to understand Architect intent reliably.\n\nRules:\n- need-clarification requires one non-empty clarification_question.\n- all other intents require clarification_question=null.\n- observations do not create work and do not expand Definition of Done.\n- do not translate your answer into SAGE internal boundary names. SAGE performs that translation deterministically.\n'


class WorkflowManagerError(RuntimeError):
    """Fail-closed workflow-manager contract error."""


def _sha256(path: Path) -> str:
    """Return a file SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_parent_request(state_path: Path, objective_id: str) -> str:
    """Load and verify the literal request preserved by SAGE parent state."""
    path = state_path.expanduser().resolve()
    state = json.loads(path.read_text(encoding="utf-8"))
    request = state.get("request")
    if not isinstance(request, str) or not request.strip():
        raise WorkflowManagerError("intent state lacks a literal request")
    expected = state.get("request_sha256")
    observed = hashlib.sha256(request.encode("utf-8")).hexdigest()
    if isinstance(expected, str) and expected and expected != observed:
        raise WorkflowManagerError("intent state literal request digest changed")
    state_objective = state.get("objective_id") or state.get("action_id") or expected
    if state_objective and str(state_objective) != objective_id:
        raise WorkflowManagerError("intent state objective identity changed")
    return request


def _contribution_context(path: Path) -> dict[str, Any]:
    """Render validated engineering-contribution provenance as SAGE context."""
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
    if not trigger.strip() or not parent_checkpoint.strip():
        raise WorkflowManagerError(
            "workflow-manager trigger and parent checkpoint are required"
        )
    literal_request = _load_parent_request(state_path, objective_id)
    request = _decision_request(
        trigger, parent_checkpoint, affected_obligations, approved_gap_set
    )
    context = _decision_context(route, literal_request, contribution)
    return objective_id, request, context


def _decision_request(
    trigger: str,
    parent_checkpoint: str,
    affected_obligations: list[str] | None,
    approved_gap_set: Path | None,
) -> dict[str, Any]:
    """Build the bounded workflow judgment request."""
    gap = None
    if approved_gap_set is not None:
        gap = {"sha256": _sha256(approved_gap_set.expanduser().resolve())}
    return {
        "trigger": trigger.strip(),
        "parent_checkpoint": parent_checkpoint.strip(),
        "affected_obligations": list(affected_obligations or []),
        "approved_gap_set": gap,
        "allowed_decisions": list(DECISIONS),
    }


def _decision_context(
    route: Mapping[str, Any],
    literal_request: str,
    contribution: Path,
) -> dict[str, Any]:
    """Build explicit SAGE-owned context with no inherited chat."""
    return {
        "literal_request": literal_request,
        "objective_route": dict(route),
        "engineering_contribution": _contribution_context(contribution),
        "governance": {
            "dod_expansion_by_discovery_allowed": False,
            "observations_create_automatic_work": False,
            "architect_intent_ambiguity_requires_clarification": True,
            "delegated_execution_fact_discovery_only_when_objective_requires": True,
            "deterministic_sage_semantics_preferred_when_sufficient": True,
        },
    }


def validate_decision(
    decision: Mapping[str, Any],
    *,
    objective_id: str,
) -> dict[str, Any]:
    """Validate one advisory workflow-manager decision."""
    required = {
        "schema_version", "record_type", "producer_class", "authority",
        "objective_id", "decision", "objective_effect", "material_change",
        "reasoning_summary", "architect_question", "observations_not_path_changing",
    }
    if set(decision) != required:
        raise WorkflowManagerError("workflow-manager decision fields are invalid")
    _validate_decision_identity(decision, objective_id)
    _validate_decision_shape(decision)
    return dict(decision)


def _validate_decision_identity(
    decision: Mapping[str, Any],
    objective_id: str,
) -> None:
    """Validate immutable role, authority, and objective identity."""
    checks = (
        (decision.get("schema_version") == "1.0", "schema_version is invalid"),
        (
            decision.get("record_type") == "sage-llm-workflow-manager-decision",
            "record_type is invalid",
        ),
        (decision.get("producer_class") == ROLE, "producer_class is invalid"),
        (decision.get("authority") == "advisory", "authority must be advisory"),
        (decision.get("objective_id") == objective_id, "objective_id changed"),
        (decision.get("decision") in DECISIONS, "decision is unsupported"),
    )
    for valid, message in checks:
        if not valid:
            raise WorkflowManagerError(f"workflow-manager {message}")


def _validate_decision_shape(decision: Mapping[str, Any]) -> None:
    """Validate decision consistency without granting new authority."""
    valid_effects = {"deterministic", "possible", "none", "unknown"}
    if decision.get("objective_effect") not in valid_effects:
        raise WorkflowManagerError("workflow-manager objective_effect is invalid")
    if not isinstance(decision.get("material_change"), bool):
        raise WorkflowManagerError("workflow-manager material_change must be boolean")
    reason = decision.get("reasoning_summary")
    if not isinstance(reason, str) or not reason.strip():
        raise WorkflowManagerError("workflow-manager reasoning_summary is required")
    observations = decision.get("observations_not_path_changing")
    valid_observations = isinstance(observations, list) and all(
        isinstance(item, str) and item.strip() for item in observations
    )
    if not valid_observations:
        raise WorkflowManagerError(
            "workflow-manager observations_not_path_changing is invalid"
        )
    _validate_decision_boundary(decision)


def _validate_decision_boundary(decision: Mapping[str, Any]) -> None:
    """Validate boundary-specific Architect and material-change semantics."""
    selected = decision.get("decision")
    question = decision.get("architect_question")
    if selected == "architect-clarification-required":
        if (
            decision.get("objective_effect") != "unknown"
            or decision.get("material_change") is not False
        ):
            raise WorkflowManagerError("architect clarification consistency is invalid")
        if not isinstance(question, str) or not question.strip():
            raise WorkflowManagerError("architect clarification requires one question")
        return
    if question is not None:
        raise WorkflowManagerError(
            "non-clarification decision may not ask Architect question"
        )
    if selected == "implementation-local" and decision.get("material_change"):
        raise WorkflowManagerError(
            "implementation-local decision may not assert material change"
        )
    if (
        selected in {"semantic-confirmation", "authority"}
        and not decision.get("material_change")
    ):
        raise WorkflowManagerError(f"{selected} decision requires material_change=true")


def _runtime_blocker(objective_id: str, reason: str) -> dict[str, Any]:
    """Render missing fresh-role inference as a governed non-mutation blocker."""
    return {
        "status": "capability-blocked",
        "objective_id": objective_id,
        "blocker_class": "fresh-role-inference-runtime",
        "reason": reason,
        "repository_mutation": False,
        "next_boundary": RUNTIME_BOUNDARY,
    }



ROLE_RESPONSE_FORMAT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "bounded-correction",
                "replan",
                "meaning-change",
                "authority-problem",
                "need-clarification",
            ],
        },
        "rationale": {"type": "string"},
        "clarification_question": {"type": ["string", "null"]},
        "observations": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "intent",
        "rationale",
        "clarification_question",
        "observations",
    ],
}

SEMANTIC_INTENT_MAP = {
    "bounded-correction": "implementation-local",
    "replan": "planning",
    "meaning-change": "semantic-confirmation",
    "authority-problem": "authority",
    "need-clarification": "architect-clarification-required",
}


def _canonicalize_semantic_response(raw, *, objective_id):
    # Convert role-level meaning into one canonical SAGE decision record.
    if not isinstance(raw, dict):
        raise WorkflowManagerError("workflow-manager semantic response must be an object")
    required = {
        "intent",
        "rationale",
        "clarification_question",
        "observations",
    }
    if set(raw) != required:
        raise WorkflowManagerError("workflow-manager semantic response fields are invalid")

    intent = raw.get("intent")
    if intent not in SEMANTIC_INTENT_MAP:
        raise WorkflowManagerError("workflow-manager semantic intent is unsupported")

    rationale = raw.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise WorkflowManagerError("workflow-manager semantic rationale is required")

    observations = raw.get("observations")
    if not isinstance(observations, list) or not all(
        isinstance(item, str) and item.strip() for item in observations
    ):
        raise WorkflowManagerError("workflow-manager semantic observations are invalid")

    question = raw.get("clarification_question")
    if intent == "need-clarification":
        if not isinstance(question, str) or not question.strip():
            raise WorkflowManagerError(
                "workflow-manager clarification intent requires one question"
            )
    elif question is not None:
        raise WorkflowManagerError(
            "workflow-manager non-clarification semantic intent may not ask a question"
        )

    decision = SEMANTIC_INTENT_MAP[intent]
    canonical = {
        "schema_version": "1.0",
        "record_type": "sage-llm-workflow-manager-decision",
        "producer_class": ROLE,
        "authority": "advisory",
        "objective_id": objective_id,
        "decision": decision,
        "objective_effect": (
            "unknown" if decision == "architect-clarification-required" else "deterministic"
        ),
        "material_change": decision in {"semantic-confirmation", "authority"},
        "reasoning_summary": rationale.strip(),
        "architect_question": (
            question.strip()
            if decision == "architect-clarification-required"
            else None
        ),
        "observations_not_path_changing": list(observations),
    }
    return validate_decision(canonical, objective_id=objective_id)


def _invoke_fresh_manager(
    envelope: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    # Invoke the fresh role, then let SAGE canonicalize its semantic result.
    try:
        endpoint, model = resolve_ollama_runtime()
        semantic, receipt = invoke_ollama_json(
            envelope=envelope,
            system_instruction=SYSTEM_INSTRUCTION,
            endpoint=endpoint,
            model=model,
            response_format=ROLE_RESPONSE_FORMAT,
        )
        decision = _canonicalize_semantic_response(
            semantic,
            objective_id=str(envelope.get("objective_id", "")).strip(),
        )
    except (RoleInvocationError, WorkflowManagerError) as error:
        return None, None, str(error)
    return decision, receipt, None



def _execute_decision(
    decision: Mapping[str, Any],
    runner: Callable[..., Mapping[str, Any]],
    repo: Path,
    state_path: Path,
    contribution: Path,
    request: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Delegate the selected boundary unchanged to existing SAGE execution."""
    return runner(
        repo,
        state_path,
        contribution,
        trigger=str(request["trigger"]),
        reentry_boundary=str(decision["decision"]),
        parent_checkpoint=str(request["parent_checkpoint"]),
        affected_obligations=list(request["affected_obligations"]),
        approved_gap_set=None,
    )


def manage_candidate_iteration(
    repo: Path,
    state_path: Path,
    contribution: Path,
    *,
    trigger: str,
    parent_checkpoint: str,
    affected_obligations: list[str] | None = None,
    approved_gap_set: Path | None = None,
) -> Mapping[str, Any]:
    """Choose one existing re-entry boundary from fresh SAGE-owned context."""
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
    writer = AtomicFileWriter((state_dir,))
    writer.write_text(
        state_dir / "workflow-manager-invocation.json",
        stable_json(envelope),
        new_mode=0o600,
    )
    raw, receipt, blocker = _invoke_fresh_manager(envelope)
    if blocker is not None:
        result = _runtime_blocker(objective_id, blocker)
        writer.write_text(
            state_dir / "workflow-manager-blocker.json",
            stable_json(result),
            new_mode=0o600,
        )
        return result
    decision = validate_decision(raw or {}, objective_id=objective_id)
    writer.write_text(
        state_dir / "workflow-manager-decision.json",
        stable_json(decision),
        new_mode=0o600,
    )
    writer.write_text(
        state_dir / "workflow-manager-invocation-receipt.json",
        stable_json(receipt or {}),
        new_mode=0o600,
    )
    if decision["decision"] == "architect-clarification-required":
        return _clarification_result(objective_id, decision, state_dir)
    result = _execute_governed_boundary(
        repo, state_path, contribution, request, approved_gap_set, decision
    )
    return _managed_result(objective_id, decision, state_dir, result)


def _execute_governed_boundary(
    repo: Path,
    state_path: Path,
    contribution: Path,
    request: Mapping[str, Any],
    approved_gap_set: Path | None,
    decision: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Call the existing authoritative candidate-iteration workflow."""
    return begin_candidate_iteration(
        repo,
        state_path,
        contribution,
        trigger=str(request["trigger"]),
        reentry_boundary=str(decision["decision"]),
        parent_checkpoint=str(request["parent_checkpoint"]),
        affected_obligations=list(request["affected_obligations"]),
        approved_gap_set=approved_gap_set,
    )


def _clarification_result(
    objective_id: str,
    decision: Mapping[str, Any],
    state_dir: Path,
) -> dict[str, Any]:
    """Return a non-mutation Architect clarification boundary."""
    return {
        "status": "architect-clarification-required",
        "objective_id": objective_id,
        "architect_question": decision["architect_question"],
        "workflow_manager_decision": str(state_dir / "workflow-manager-decision.json"),
        "repository_mutation": False,
        "next_boundary": "architect-intent",
    }


def _managed_result(
    objective_id: str,
    decision: Mapping[str, Any],
    state_dir: Path,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the delegated SAGE result with advisory decision evidence."""
    return {
        "status": result.get("status"),
        "objective_id": objective_id,
        "selected_reentry_boundary": decision["decision"],
        "workflow_manager_decision": str(state_dir / "workflow-manager-decision.json"),
        "workflow_manager_receipt": str(
            state_dir / "workflow-manager-invocation-receipt.json"
        ),
        "sage_result": dict(result),
    }


def _fixture_decision(objective_id: str, decision: str = "planning") -> dict[str, Any]:
    """Build one deterministic self-test decision."""
    return {
        "schema_version": "1.0",
        "record_type": "sage-llm-workflow-manager-decision",
        "producer_class": ROLE,
        "authority": "advisory",
        "objective_id": objective_id,
        "decision": decision,
        "objective_effect": "deterministic",
        "material_change": False,
        "reasoning_summary": "Existing SAGE planning must recompute the bounded path.",
        "architect_question": None,
        "observations_not_path_changing": [],
    }


def _self_test_decision_contract() -> None:
    """Prove advisory authority and clarification contracts fail closed."""
    validated = validate_decision(
        _fixture_decision("SAGE-ACTION-FIXTURE"),
        objective_id="SAGE-ACTION-FIXTURE",
    )
    if validated["decision"] != "planning":
        raise RuntimeError("workflow-manager validation changed decision")
    elevated = _fixture_decision("SAGE-ACTION-FIXTURE")
    elevated["authority"] = "architect"
    try:
        validate_decision(elevated, objective_id="SAGE-ACTION-FIXTURE")
    except WorkflowManagerError:
        pass
    else:
        raise RuntimeError("workflow manager acquired Architect authority")
    extra = _fixture_decision("SAGE-ACTION-FIXTURE")
    extra["command"] = "git push"
    try:
        validate_decision(extra, objective_id="SAGE-ACTION-FIXTURE")
    except WorkflowManagerError:
        pass
    else:
        raise RuntimeError("workflow manager accepted direct mutation command")


def _self_test_clarification() -> None:
    """Prove genuine intent ambiguity returns to the Architect boundary."""
    decision = _fixture_decision(
        "SAGE-ACTION-FIXTURE", "architect-clarification-required"
    )
    decision["objective_effect"] = "unknown"
    decision["reasoning_summary"] = "The Architect-owned target is ambiguous."
    decision["architect_question"] = "Which target should this objective change?"
    validated = validate_decision(decision, objective_id="SAGE-ACTION-FIXTURE")
    if not validated["architect_question"]:
        raise RuntimeError("workflow-manager clarification lost Architect question")


def _self_test_runtime_blocker() -> None:
    """Prove missing provider configuration becomes a governed blocker."""
    try:
        resolve_ollama_runtime({})
    except RoleInvocationError as error:
        blocker = _runtime_blocker("SAGE-ACTION-FIXTURE", str(error))
    else:
        raise RuntimeError("missing role inference runtime did not fail closed")
    if blocker["repository_mutation"] or blocker["next_boundary"] != RUNTIME_BOUNDARY:
        raise RuntimeError(
            "runtime absence did not preserve the governed blocker boundary"
        )


def _self_test_fresh_invocation() -> None:
    """Prove provider messages contain one SAGE context and no inherited chat."""
    observed: list[dict[str, Any]] = []
    server = _fixture_server(observed)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        envelope = _fixture_envelope()
        result, receipt = invoke_ollama_json(
            envelope=envelope,
            system_instruction=SYSTEM_INSTRUCTION,
            endpoint=f"http://127.0.0.1:{server.server_port}",
            model="fixture-model",
        )
        validate_decision(result, objective_id="SAGE-ACTION-FIXTURE")
        _assert_fresh_wire(observed, receipt)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _fixture_envelope() -> dict[str, Any]:
    """Build the exact original natural-language request regression fixture."""
    return build_invocation(
        role=ROLE,
        objective_id="SAGE-ACTION-FIXTURE",
        request={
            "trigger": (
                "A correction is required to keep the original objective moving."
            )
        },
        context={
            "literal_request": REGRESSION_LITERAL_REQUEST,
            "objective_route": {"objective_id": "SAGE-ACTION-FIXTURE"},
        },
    )


def _self_test_literal_request_state_bridge() -> None:
    """Prove SAGE state preserves the exact literal request into fresh context."""
    digest = hashlib.sha256(REGRESSION_LITERAL_REQUEST.encode("utf-8")).hexdigest()
    state = {
        "request": REGRESSION_LITERAL_REQUEST,
        "request_sha256": digest,
        "objective_id": "SAGE-ACTION-FIXTURE",
    }
    with tempfile.TemporaryDirectory(prefix="sage-role-request-fixture-") as name:
        path = Path(name) / "intent-to-outcome-state.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        loaded = _load_parent_request(path, "SAGE-ACTION-FIXTURE")
    if loaded != REGRESSION_LITERAL_REQUEST:
        raise RuntimeError("literal request changed before fresh role invocation")


def _fixture_server(observed: list[dict[str, Any]]) -> HTTPServer:
    """Create a local provider fixture returning a bounded planning decision."""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            """Capture one provider request and return fixture JSON."""
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length))
            observed.append(body)
            envelope = json.loads(body["messages"][1]["content"])
            response = {
                "model": "fixture-model",
                "message": {
                    "role": "assistant",
                    "content": json.dumps(_fixture_decision(envelope["objective_id"])),
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
            """Suppress fixture HTTP logs."""
            return

    return HTTPServer(("127.0.0.1", 0), Handler)


def _assert_fresh_wire(
    observed: list[dict[str, Any]],
    receipt: Mapping[str, Any],
) -> None:
    """Assert no Architect/prior-role chat or provider thinking crossed the boundary."""
    if len(observed) != 1:
        raise RuntimeError("expected one fresh provider call")
    messages = observed[0].get("messages")
    roles = (
        [item.get("role") for item in messages]
        if isinstance(messages, list)
        else []
    )
    if roles != ["system", "user"]:
        raise RuntimeError("workflow manager received inherited chat history")
    sent = json.loads(messages[1]["content"])
    if sent["context"]["literal_request"] != REGRESSION_LITERAL_REQUEST:
        raise RuntimeError("original literal request was not preserved")
    if "reentry_boundary" in sent["request"]:
        raise RuntimeError("requester supplied SAGE-internal re-entry vocabulary")
    policy = sent["context_policy"]
    if (
        policy["architect_chat_history_included"]
        or policy["role_chat_history_included"]
    ):
        raise RuntimeError(
            "conversation history leaked into workflow-manager invocation"
        )
    if "private fixture thinking" in json.dumps(receipt):
        raise RuntimeError("provider thinking leaked into SAGE receipt")


def _self_test_governed_dispatch() -> None:
    """Prove LLM judgment delegates only to the existing SAGE iteration workflow."""
    observed: dict[str, Any] = {}

    def runner(*args: Any, **kwargs: Any) -> Mapping[str, Any]:
        """Capture the delegated boundary without performing mutation."""
        observed.update(kwargs)
        return {"status": "planning-source-ready"}

    request = {
        "trigger": "Natural-language correction trigger.",
        "parent_checkpoint": "checkpoint-fixture",
        "affected_obligations": [],
    }
    result = _execute_decision(
        _fixture_decision("SAGE-ACTION-FIXTURE"),
        runner,
        Path("/repo"),
        Path("/state"),
        Path("/contribution"),
        request,
    )
    if (
        result.get("status") != "planning-source-ready"
        or observed.get("reentry_boundary") != "planning"
    ):
        raise RuntimeError(
            "workflow-manager did not delegate through existing SAGE planning boundary"
        )



def _self_test_semantic_adapter() -> None:
    # Prove LLM meaning is separate from SAGE record construction.
    raw = {
        "intent": "bounded-correction",
        "rationale": "Only a bounded source repair is required.",
        "clarification_question": None,
        "observations": [],
    }
    decision = _canonicalize_semantic_response(
        raw,
        objective_id="SAGE-ACTION-FIXTURE",
    )
    if decision["decision"] != "implementation-local":
        raise RuntimeError("semantic adapter changed bounded-correction mapping")
    if decision["material_change"]:
        raise RuntimeError("semantic adapter invented material change")
    if decision["authority"] != "advisory":
        raise RuntimeError("semantic adapter elevated model authority")

    model_fields = set(ROLE_RESPONSE_FORMAT["properties"])
    forbidden = {
        "schema_version",
        "record_type",
        "producer_class",
        "authority",
        "objective_id",
        "decision",
        "objective_effect",
        "material_change",
        "request_sha256",
        "proposal_sha256",
        "receipt",
    }
    if model_fields & forbidden:
        raise RuntimeError("model-facing semantic schema leaks SAGE control fields")

    changed = dict(raw)
    changed["intent"] = "meaning-change"
    changed_decision = _canonicalize_semantic_response(
        changed,
        objective_id="SAGE-ACTION-FIXTURE",
    )
    if (
        changed_decision["decision"] != "semantic-confirmation"
        or changed_decision["material_change"] is not True
    ):
        raise RuntimeError("semantic adapter failed deterministic material-change mapping")

    invalid = dict(raw)
    invalid["authority"] = "architect"
    try:
        _canonicalize_semantic_response(
            invalid,
            objective_id="SAGE-ACTION-FIXTURE",
        )
    except WorkflowManagerError:
        pass
    else:
        raise RuntimeError("model-authored SAGE control field was accepted")

    ambiguous = dict(raw)
    ambiguous["intent"] = "need-clarification"
    try:
        _canonicalize_semantic_response(
            ambiguous,
            objective_id="SAGE-ACTION-FIXTURE",
        )
    except WorkflowManagerError:
        pass
    else:
        raise RuntimeError("clarification intent without a question was accepted")


def self_test() -> None:
    """Exercise fresh context, advisory authority, routing, ambiguity, and blockers."""
    _self_test_semantic_adapter()
    _self_test_decision_contract()
    _self_test_clarification()
    _self_test_runtime_blocker()
    _self_test_literal_request_state_bridge()
    _self_test_fresh_invocation()
    _self_test_governed_dispatch()
    print(
        "PASS literal natural-language intent can reach SAGE-selected planning "
        "without caller boundary vocabulary"
    )
    print("PASS Architect and prior-role chat are absent below the published boundary")
    print("PASS workflow manager cannot acquire mutation or Architect authority")
    print("PASS existing deterministic SAGE iteration remains execution authority")
    print("PASS genuine intent ambiguity returns to Architect clarification")
    print("PASS missing inference runtime is a governed non-mutation blocker")
