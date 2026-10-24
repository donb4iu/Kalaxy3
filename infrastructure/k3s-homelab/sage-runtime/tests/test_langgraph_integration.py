"""Run against installed official LangGraph/checkpoint packages in the cluster."""

from __future__ import annotations

import unittest
from typing import Any


class LangGraphReferenceTests(unittest.TestCase):
    """End-to-end graph transitions when the reference runtime is installed."""

    def test_bounded_correction_through_checkpoint(self) -> None:
        """Use real StateGraph and SqliteSaver to verify automatic correction."""
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            from service.workflow import build_graph
        except ImportError as exc:
            self.skipTest(f"LangGraph runtime unavailable: {exc}")
        called: list[str] = []

        def role(name: str, envelope: dict[str, Any]) -> dict[str, Any]:
            """Act as isolated Engineering or Referee for a graph test.

            Args:
                name: Role invoked by LangGraph.
                envelope: Git-source-bound role context.
            """
            called.append(name)
            if name == "engineering":
                return {"proposal": "Use documented Ansible Vault workflow",
                        "evidence_paths": ["infrastructure/README.md"]}
            if called.count("referee") == 1:
                return {"verdict": "correct", "findings": [
                    {"source_path": "infrastructure/README.md", "source_sha256": "a",
                     "criterion": "Reuse existing infrastructure",
                     "invariant": "Must not add HashiCorp Vault"}]}
            return {"verdict": "allow", "findings": []}

        context = {"revision": "testsha", "objective_id": "OBJ-1",
                   "acceptance_criteria": ["Reuse existing infrastructure"],
                   "source_sha256": {"infrastructure/README.md": "a"},
                   "evidence": {"manifest": {"revision": "testsha"},
                                "manifest_sha256": "digest",
                                "retrieved_sources": [{"path": "infrastructure/README.md",
                                                       "sha256": "a"}]}}
        initial = {"objective_id": "OBJ-1", "revision": "testsha", "context": context,
                   "question": "Deploy with existing secrets", "attempts": 0}
        with SqliteSaver.from_conn_string(":memory:") as saver:
            graph = build_graph(role).compile(checkpointer=saver)
            conf = {"configurable": {"thread_id": "OBJ-1"}}
            result = graph.invoke(initial, conf)
            self.assertEqual(result["attempts"], 2)
            self.assertEqual(called, ["engineering", "referee", "engineering", "referee"])
            self.assertTrue(graph.get_state(conf).values["outcome"])


if __name__ == "__main__":
    unittest.main()
