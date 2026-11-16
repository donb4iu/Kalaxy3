"""Integration tests for read-only Git source discovery and graph comparison."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sage_context_discovery import (
    build_input, exact_revision, git_content_hits, graph_candidate_paths,
    graph_discrepancies,
    inventory, query_terms, rank_sources, sensitive_path, write_outputs,
)
from sage_context_graph_read import require_loopback, receipt_projection


class ContextDiscoveryTests(unittest.TestCase):
    """Ensure candidate discovery preserves scope, provenance and authority."""

    def setUp(self) -> None:
        """Create an isolated Git repository with main and feature history."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "SAGE Test")
        self.git("config", "user.email", "sage@example.invalid")
        self.add("docs/observability.md", "Monitoring and recovery obligations\n")
        self.add("docs/alternative.md", "Historical graph decision, rejected\n")
        self.add("secrets/private.key", "NOT_FOR_PACKET\n")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.main = exact_revision(self.repo, "HEAD")
        self.git("switch", "-qc", "feature/context")
        self.add("docs/context.md", "Context assembly sources and risk\n")
        self.git("add", ".")
        self.git("commit", "-qm", "feature")
        self.feature = exact_revision(self.repo, "HEAD")

    def git(self, *args: str) -> None:
        """Run local Git commands within the synthetic checkout.

        Args:
            *args: Git arguments.
        """
        subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def add(self, path: str, content: str) -> None:
        """Write a synthetic fixture file.

        Args:
            path: Repo-relative fixture path.
            content: Synthetic text.
        """
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def context(self, graph: dict[str, Any] | None = None
                ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Build the real Git-discovery test input.

        Args:
            graph: Optional native-shaped graph candidate response.
        """
        return build_input(self.repo, self.feature, self.main, "SAGE-TEST",
                           "Context assembly monitoring recovery", "critic", graph)

    def test_exact_revision_separates_main_and_feature(self) -> None:
        """Two committed revisions stay separate in context metadata."""
        self.assertNotEqual(self.main, self.feature)
        request, _ = self.context()
        self.assertEqual(request["main_revision"], self.main)
        self.assertEqual(request["feature_revision"], self.feature)

    def test_git_inventory_preserves_all_sources(self) -> None:
        """Independent Git source enumeration is not restricted to graph hits."""
        tree = inventory(self.repo, self.feature)
        self.assertEqual(len(tree), 4)
        self.assertIn("docs/alternative.md", tree)
        self.assertIn("secrets/private.key", tree)

    def test_committed_content_discovers_unmapped_source(self) -> None:
        """A source absent from graph results remains discoverable by content."""
        hits = git_content_hits(self.repo, self.feature, ["monitoring"])
        self.assertIn("docs/observability.md", hits)
        candidates = rank_sources(inventory(self.repo, self.feature),
                                  "Monitoring recovery", hits)
        self.assertIn("docs/observability.md", candidates)

    def test_graph_only_source_preserved_as_candidate(self) -> None:
        """Graph-only proposals are considered without being authenticated."""
        graph = {"projection_id": self.feature + ":candidate", "qualification": "candidate_only",
                 "sources": [{"path": "docs/alternative.md"}]}
        request, _ = self.context(graph)
        record = next(row for row in request["sources"]
                      if row["title"] == "docs/alternative.md")
        self.assertIn("graph", record["discovery_lanes"])
        self.assertEqual(record["epistemic_state"], "not_evaluated")
        self.assertEqual(record["relevance"], "uncertain")

    def test_graph_wrong_digest_is_visible(self) -> None:
        """Matching counts cannot hide graph/Git identity disagreement."""
        request, _ = self.context()
        candidate = next(row for row in request["sources"]
                         if row["title"] == "docs/context.md")
        graph = {"sources": [{"path": "docs/context.md",
                              "git_oid": candidate["git_oid"],
                              "content_sha256": "0" * 64}]}
        mismatches = graph_discrepancies(graph, request["sources"])
        self.assertIn({"path": "docs/context.md", "reason": "sha256_mismatch"},
                      mismatches)

    def test_graph_revision_mismatch_fails(self) -> None:
        """A graph for a different feature commit cannot silently mix evidence."""
        with self.assertRaises(ValueError):
            graph_candidate_paths({"projection_id": self.main + ":candidate",
                                   "qualification": "candidate_only"}, self.feature)

    def test_graph_qualified_claim_fails(self) -> None:
        """Graph response cannot promote a candidate source's epistemic state."""
        with self.assertRaises(ValueError):
            graph_candidate_paths({"projection_id": self.feature + ":candidate",
                                   "qualification": "accepted"}, self.feature)

    def test_missing_graph_must_be_reported(self) -> None:
        """Graph lane absence and outside-graph findings remain explicit."""
        request, counts = self.context()
        self.assertEqual(request["search_scope"]["neo4j_candidate"], "not_searched")
        self.assertTrue(counts["independent_candidates_not_in_graph_result"])

    def test_sensitive_source_not_selected(self) -> None:
        """Paths that suggest secrets cannot be included in permitted candidates."""
        self.assertTrue(sensitive_path("secrets/private.key"))
        self.assertFalse(sensitive_path("docs/observability.md"))

    def test_output_is_only_outside_git(self) -> None:
        """The collector must not create artifacts in the inspected checkout."""
        request, counts = self.context()
        with self.assertRaises(ValueError):
            write_outputs(self.repo / "evidence", request, counts,
                          self.repo, self.feature, self.main)
        out = Path(self.temp.name) / "out"
        write_outputs(out, request, counts, self.repo, self.feature, self.main)
        self.assertTrue((out / "context-manifest.json").is_file())
        self.assertNotIn("NOT_FOR_PACKET", (out / "context-packet.md").read_text())

    def test_output_determinism(self) -> None:
        """Two runs over identical pinned sources produce identical source inputs."""
        self.assertEqual(self.context(), self.context())

    def test_content_search_cues_are_bounded(self) -> None:
        """Lexical cue extraction does not imply verified semantic relevance."""
        self.assertLessEqual(len(query_terms("Context assembly observability")), 12)

    def test_receipt_requires_matching_commit(self) -> None:
        """A native receipt's graph identity must match the exact feature SHA."""
        receipt = Path(self.temp.name) / "receipt.json"
        receipt.write_text(json.dumps({"feature_revision": self.feature,
                                       "projection_id": self.feature + ":projection"}))
        self.assertEqual(receipt_projection(receipt, self.feature),
                         self.feature + ":projection")
        with self.assertRaises(ValueError):
            receipt_projection(receipt, self.main)

    def test_read_only_endpoint_must_be_loopback(self) -> None:
        """The native reader refuses a nonlocal or credential-bearing Bolt URI."""
        require_loopback("bolt+ssc://127.0.0.1:17687")
        for uri in ("bolt://192.168.2.28:7687", "neo4j://127.0.0.1:7687",
                    "bolt://user:secret@localhost:7687"):
            with self.assertRaises(ValueError):
                require_loopback(uri)


if __name__ == "__main__":
    unittest.main()
