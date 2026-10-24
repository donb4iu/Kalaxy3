"""Durable bounded engineering/Referee collaboration; no ungoverned mutations."""

from __future__ import annotations

import json
from typing import Any, Callable, TypedDict

from .roles import classify_referee, validated_engineering, validate_citations


class ExecutionState(TypedDict, total=False):
    """LangGraph state for a single admitted objective and question."""

    objective_id: str
    revision: str
    question: str
    context: dict[str, Any]
    engineering: dict[str, Any]
    referee: dict[str, Any]
    attempts: int
    referee_disposition: str
    outcome: str
    execution_submission: dict[str, str]
    execution_receipt: dict[str, Any]


def validate_shared_context(context: dict[str, Any]) -> None:
    """Prevent role invocation unless the Git-bound retrieved context exists.

    Args:
        context: Shared objective checkpoint and source-bound semantic evidence.
    """
    evidence = context.get("evidence", {})
    manifest = evidence.get("manifest", {})
    if (manifest.get("revision") != context.get("revision")
            or not evidence.get("manifest_sha256")
            or not evidence.get("retrieved_sources")
            or not context.get("acceptance_criteria")):
        raise ValueError("mandatory shared Git context is missing")


def build_graph(invoke: Callable[[str, dict[str, Any]], dict[str, Any]],
                execute: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> Any:
    """Build reusable LangGraph nodes and deterministic transition rules.

    Args:
        invoke: Explicit role adapter callable (role name, role envelope).
        execute: Existing governed execution adapter for qualified packages.
    """
    from langgraph.graph import END, START, StateGraph

    def engineer(state: ExecutionState) -> dict[str, Any]:
        """Invoke Engineering using common, pinned context and Referee feedback."""
        envelope = {"context": state["context"], "question": state["question"],
                    "referee_feedback": state.get("referee", {}),
                    "role": "engineering"}
        validate_shared_context(state["context"])
        reply = validated_engineering(invoke("engineering", envelope))
        validate_citations(reply, state["context"])
        return {"engineering": reply, "attempts": state.get("attempts", 0) + 1}

    def referee(state: ExecutionState) -> dict[str, Any]:
        """Independently assess engineering; never self-authorize execution."""
        envelope = {"context": state["context"], "question": state["question"],
                    "engineering": state["engineering"], "role": "referee"}
        validate_shared_context(state["context"])
        reply = invoke("referee", envelope)
        status = classify_referee(reply, state["context"]["source_sha256"],
                                  state["context"]["acceptance_criteria"])
        return {"referee": reply, "referee_disposition": status}

    def route(state: ExecutionState) -> str:
        """Correct at most once, then advance to a guarded terminal result."""
        if state["referee_disposition"] == "correction-proposed":
            return "engineer" if state["attempts"] < 2 else "finish"
        return "execute" if execute is not None else "finish"

    def execute_bound(state: ExecutionState) -> dict[str, Any]:
        """Hand qualified work to the existing SAGE execution adapter."""
        if execute is None:
            raise ValueError("governed execution adapter missing")
        return execute(dict(state))

    def finish(state: ExecutionState) -> dict[str, Any]:
        """Report a qualified advisory or explicit unresolved blocker."""
        outcome = ("needs-governed-correction"
                   if state["referee_disposition"] == "correction-proposed"
                   else "advisory-awaiting-governed-acceptance")
        return {"outcome": outcome}

    graph = StateGraph(ExecutionState)
    graph.add_node("engineer", engineer)
    graph.add_node("referee", referee)
    graph.add_node("finish", finish)
    graph.add_node("execute", execute_bound)
    graph.add_edge(START, "engineer")
    graph.add_edge("engineer", "referee")
    graph.add_conditional_edges("referee", route, {"engineer": "engineer",
                                                   "finish": "finish", "execute": "execute"})
    graph.add_edge("execute", END)
    graph.add_edge("finish", END)
    return graph


def stable_digest(value: dict[str, Any]) -> str:
    """Compute deterministic JSON digest for execution identity.

    Args:
        value: Execution request fields.
    """
    import hashlib

    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(body).hexdigest()
