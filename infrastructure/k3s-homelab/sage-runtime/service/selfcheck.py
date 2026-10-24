"""Verify real cluster dependencies before claiming a reachable SAGE runtime."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from .context import clone_repository, compile_context, read_versioned
from .evidence import build_langchain_searcher, select_evidence


def graph_smoke() -> str:
    """Execute real LangGraph transitions against disposable SQLite state."""
    from .workflow import build_graph
    from langgraph.checkpoint.sqlite import SqliteSaver

    common = {"objective_id": "SELF-CHECK", "revision": "fixture",
              "source_sha256": {"SAGE.md": "source-digest"},
              "acceptance_criteria": ["Restore correctly"],
              "evidence": {"manifest": {"revision": "fixture"},
                           "manifest_sha256": "fixture-manifest",
                           "retrieved_sources": [{"path": "SAGE.md",
                                                  "sha256": "source-digest"}]}}
    calls: list[str] = []

    def role(name: str, envelope: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic contributions for runtime orchestration proof.

        Args:
            name: Simulated RACI role.
            envelope: Objective-scoped invocation context.
        """
        calls.append(name)
        if name == "engineering":
            return {"proposal": "Restore accepted context", "evidence_paths": ["SAGE.md"]}
        if calls.count("engineering") == 1:
            return {"verdict": "correct", "findings": [{
                "source_path": "SAGE.md", "source_sha256": "source-digest",
                "criterion": "Restore correctly", "invariant": "missing checkpoint"}]}
        return {"verdict": "allow", "findings": []}

    state = {"objective_id": "SELF-CHECK", "revision": "fixture",
             "context": common, "question": "Recover context", "attempts": 0}
    with SqliteSaver.from_conn_string(":memory:") as saver:
        workflow = build_graph(role).compile(checkpointer=saver)
        result = workflow.invoke(state, {"configurable": {"thread_id": "self-check"}})
    if result.get("attempts") != 2 or result.get("outcome") != "advisory-awaiting-governed-acceptance":
        raise RuntimeError("LangGraph correction routing did not complete")
    return "pass"


def run() -> dict[str, str]:
    """Check Git restoration, Ollama availability and LangGraph storage."""
    from tempfile import TemporaryDirectory
    from langgraph.checkpoint.sqlite import SqliteSaver

    with TemporaryDirectory(prefix="sage-health-") as root:
        repo = Path(root) / "git"
        revision = clone_repository(os.environ["SAGE_REPO_URL"], repo)
        registry = json.loads(read_versioned(repo, revision, "sage-improvement-actions.json"))
        eligible = sorted(
            action["action_id"] for action in registry.get("actions", [])
            if action.get("current_status") in {"accepted", "implemented", "validated"}
            and any(h.get("to_status") == "accepted"
                    for h in action.get("history", []))
        )
        if not eligible:
            raise RuntimeError("Git has no accepted SAGE action")
        record = compile_context(repo, revision, eligible[0])
        short_records = [{"path": path,
                          "sha256": __import__("hashlib").sha256(
                              read_versioned(repo, revision, path)).hexdigest(),
                          "content": read_versioned(repo, revision, path).decode()}
                         for path in ("AGENTS.md", "SAGE.md")]
        semantic_search = build_langchain_searcher(
            short_records, os.environ["SAGE_OLLAMA_URL"],
            os.environ["SAGE_OLLAMA_EMBED_MODEL"])
        matches = select_evidence(short_records, record["objective"], semantic_search)
        if not matches:
            raise RuntimeError("LangChain retrieval did not return Git-bound evidence")
    db_path = os.environ["SAGE_CHECKPOINT_DB"]
    with SqliteSaver.from_conn_string(db_path) as saver:
        saver.setup()
    endpoint = os.environ["SAGE_OLLAMA_URL"].rstrip("/") + "/api/tags"
    with urllib.request.urlopen(endpoint, timeout=20) as response:
        tags = json.load(response)
    models = {item.get("name") for item in tags.get("models", [])}
    expected = os.environ["SAGE_OLLAMA_MODEL"]
    embedding_model = os.environ["SAGE_OLLAMA_EMBED_MODEL"]
    if (not ({expected, expected + ":latest"} & models)
            or not ({embedding_model, embedding_model + ":latest"} & models)):
        raise RuntimeError("configured inference or embedding model is unavailable")
    return {"git_checkpoint": record["revision"],
            "ollama_model": expected, "embedding_model": embedding_model,
            "langgraph_storage": "available",
            "bounded_graph_correction": graph_smoke(),
            "langchain_git_retrieval": "pass"}


def main() -> None:
    """Report verified infrastructure dependencies without leaking secrets."""
    print(json.dumps(run(), sort_keys=True))


if __name__ == "__main__":
    main()
