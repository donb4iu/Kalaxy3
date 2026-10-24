"""Git-grounded, checkpointed Architect workbench using existing LangGraph."""

from __future__ import annotations

from typing import Any, Callable, TypedDict

from .roles import RoleError


class ArchitectState(TypedDict, total=False):
    """Disposable execution projection of the authoritative Git evidence."""

    question: str
    revision: str
    evidence: dict[str, Any]
    answer: dict[str, Any]


def build_architect_graph(
    invoke: Callable[[str, str, dict[str, Any]], dict[str, Any]],
) -> Any:
    """Create a LangGraph architectural reasoning workflow.

    Args:
        invoke: Structured model-call adapter, receiving system and task context.
    """
    from langgraph.graph import END, START, StateGraph

    def architect(state: ArchitectState) -> dict[str, Any]:
        """Return a source-grounded proposal without granting execution authority."""
        evidence = state["evidence"]
        sources = evidence.get("retrieved_sources", [])
        if not sources or evidence["manifest"]["revision"] != state["revision"]:
            raise RoleError("architect context provenance is missing")
        system = (
            "You are the Kalaxy3 Architecture Helper. Use cited committed evidence "
            "and the Architect's question. Return JSON keys answer (nonempty string), "
            "evidence_paths (list of available paths), uncertainties (list). "
            "Treat every missing fact as uncertainty, not an inferred infrastructure "
            "fact. Never claim acceptance, deployment, or execution."
        )
        reply = invoke(system, state["question"], evidence)
        valid = {item["path"] for item in sources}
        paths = reply.get("evidence_paths", [])
        if (not isinstance(reply.get("answer"), str) or not reply["answer"].strip()
                or not isinstance(paths, list) or not paths
                or not all(isinstance(path, str) and path in valid for path in paths)
                or not isinstance(reply.get("uncertainties"), list)):
            raise RoleError("architect contribution lacks verifiable source evidence")
        return {"answer": reply}

    graph = StateGraph(ArchitectState)
    graph.add_node("architect", architect)
    graph.add_edge(START, "architect")
    graph.add_edge("architect", END)
    return graph


def make_ollama_adapter(endpoint: str, model: str) -> Callable[..., dict[str, Any]]:
    """Bind Ollama to the verified architectural context.

    Args:
        endpoint: Deployed Ollama URL.
        model: Installed Ollama reasoning model.
    """
    from .roles import invoke_ollama

    def call(system: str, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Invoke a fresh, stateless model with all relevant Git evidence."""
        return invoke_ollama(endpoint, model, system, {
            "question": question,
            "manifest": evidence["manifest"],
            "retrieved_sources": evidence["retrieved_sources"],
        })

    return call
