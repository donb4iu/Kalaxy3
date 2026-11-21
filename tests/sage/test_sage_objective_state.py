"""Regression tests for bounded, evidence-backed objective-state decisions."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "sage"))

from sage_objective_state import (EvidenceError, changed_scope, evaluate,
                                  evaluate_all, verify_receipt)


class ObjectiveStateTests(unittest.TestCase):
    """Exercise the #55 trust boundary and repeat-work decision logic."""

    def setUp(self) -> None:
        """Prepare isolated native receipt, manifest and Git repository."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.test")
        self.git("config", "user.name", "Objective State Test")
        self.write_commit("one", "first")
        self.rev1 = self.git("rev-parse", "HEAD").strip()
        self.write_commit("two", "second")
        self.rev2 = self.git("rev-parse", "HEAD").strip()
        self.state = {"source_revision": self.rev1, "source_count": 1388,
                      "capability": "source_metadata_identity", "state": "validated",
                      "scope": "source_identity_and_digest_only"}
        self.receipt_path = self.root / "receipt.json"
        self.manifest_path = self.root / "manifest.json"
        self.write_receipt()

    def git(self, *args: str) -> str:
        """Run Git inside the disposable fixture.

        Args:
            args: Git subcommand arguments.
        """
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              check=True, text=True, capture_output=True).stdout

    def write_commit(self, content: str, message: str) -> None:
        """Commit a tracked file at a new revision.

        Args:
            content: Fixture file content.
            message: Unique commit message.
        """
        (self.repo / "source.txt").write_text(content, encoding="utf-8")
        self.git("add", "source.txt")
        self.git("commit", "-qm", message)

    def write_receipt(self) -> None:
        """Create a hash-linked local test receipt matching the #55 contract."""
        from sage_objective_state import GRAPH_REVISION

        payload: dict[str, Any] = {
            "graph_revision": GRAPH_REVISION, "graph_page_incomplete": False,
            "semantic_relevance_qualified": False, "complete_context_claim": False,
            "full_graph_inventory_reconciliation": {
                "git_blob_count": 1388, "graph_inventory_count": 1388,
                "exact_source_identity_and_digest_equivalence": True,
                "missing_graph_paths": [], "non_git_graph_paths": [],
                "git_oid_disagreements": [], "sha256_disagreements": []}}
        raw = json.dumps(payload).encode("utf-8")
        self.receipt_path.write_bytes(raw)
        manifest = {"graph_revision": GRAPH_REVISION,
                    "issue55_receipt_sha256": hashlib.sha256(raw).hexdigest()}
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def proposal(self, capability: str, action: str,
                 revision: str | None = None) -> dict[str, Any]:
        """Build one untrusted action candidate.

        Args:
            capability: Known or unknown target.
            action: Proposed validation or revalidation.
            revision: Proposed exact Git revision.
        """
        return {"objective": "#50", "capability": capability, "action": action,
                "target_revision": revision or self.rev1}

    def test_native_receipt_verified_and_limited(self) -> None:
        """Bind evidence bytes without inferring semantic correctness."""
        result = verify_receipt(self.receipt_path, self.manifest_path)
        self.assertEqual(result["state"], "validated")
        self.assertEqual(result["semantic_coverage_state"], "unknown")
        self.assertEqual(result["source_count"], 1388)

    def test_receipt_tampering_fails(self) -> None:
        """Reject byte changes even if reported counts remain unchanged."""
        self.receipt_path.write_bytes(self.receipt_path.read_bytes() + b" ")
        with self.assertRaises(EvidenceError):
            verify_receipt(self.receipt_path, self.manifest_path)

    def test_receipt_graph_disagreement_fails(self) -> None:
        """Reject mismatches even with a recomputed matching manifest hash."""
        data = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        data["full_graph_inventory_reconciliation"]["sha256_disagreements"] = ["x"]
        raw = json.dumps(data).encode("utf-8")
        self.receipt_path.write_bytes(raw)
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        manifest["issue55_receipt_sha256"] = hashlib.sha256(raw).hexdigest()
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(EvidenceError):
            verify_receipt(self.receipt_path, self.manifest_path)

    def test_same_revision_repeat_is_blocked(self) -> None:
        """A model cannot re-open completed scoped work by assertion."""
        item = self.proposal("source_metadata_identity", "revalidate")
        self.assertEqual(evaluate(item, self.state, self.repo)["status"],
                         "blocked_repeat")

    def test_unchanged_tree_repeat_is_blocked(self) -> None:
        """Different commit identity alone is not proof of changed sources."""
        self.git("commit", "--allow-empty", "-qm", "empty")
        empty_rev = self.git("rev-parse", "HEAD").strip()
        item = self.proposal("source_metadata_identity", "revalidate", empty_rev)
        self.state["source_revision"] = self.rev2
        self.assertEqual(evaluate(item, self.state, self.repo)["status"],
                         "blocked_repeat")

    def test_new_git_blob_scope_can_be_revalidated(self) -> None:
        """A real source identity delta permits a separate candidate check."""
        item = self.proposal("source_metadata_identity", "revalidate", self.rev2)
        result = evaluate(item, self.state, self.repo)
        self.assertEqual(result["status"], "candidate_new_scope")
        self.assertEqual(result["evidence"]["changed_blob_identities"], 1)
        self.assertFalse(result["architect_authorization"])

    def test_missing_revision_does_not_authorize_repeat(self) -> None:
        """Unknown or unresolvable commit IDs fail as unverified."""
        item = self.proposal("source_metadata_identity", "revalidate", "a" * 40)
        self.assertEqual(evaluate(item, self.state, self.repo)["status"],
                         "unverified")

    def test_unverified_semantic_work_is_candidate_only(self) -> None:
        """Unknown semantic status permits bounded testing, not implementation."""
        item = self.proposal("semantic_relationship_fidelity", "validate")
        self.assertEqual(evaluate(item, self.state, self.repo)["status"], "candidate")
        item["action"] = "implement"
        self.assertEqual(evaluate(item, self.state, self.repo)["status"], "blocked")

    def test_unknown_target_and_wrong_objective_block(self) -> None:
        """Reject candidate objectives outside the bounded contract."""
        item = self.proposal("imagined_capability", "validate")
        self.assertEqual(evaluate(item, self.state, self.repo)["status"], "blocked")
        item["objective"] = "#54"
        self.assertEqual(evaluate(item, self.state, self.repo)["status"], "blocked")

    def test_batch_is_evidence_bound_not_authorization(self) -> None:
        """Preserve per-candidate decisions without implicit acceptance."""
        proposals = [self.proposal("source_metadata_identity", "validate"),
                     self.proposal("tri_state_evidence_presence", "validate")]
        report = evaluate_all(proposals, self.state, self.repo)
        self.assertEqual([r["status"] for r in report["proposals"]],
                         ["blocked_repeat", "candidate"])
        self.assertEqual(report["architect_acceptance"], "not_evaluated")

    def test_git_scope_does_not_modify_repository(self) -> None:
        """Read-only source comparison preserves revision and tree cleanliness."""
        before = self.git("status", "--porcelain")
        self.assertEqual(changed_scope(self.repo, self.rev1, self.rev2)[
            "changed_blob_identities"], 1)
        self.assertEqual(self.git("status", "--porcelain"), before)


    def test_cli_reports_bounded_repeat_and_strict_exit(self) -> None:
        """The CLI blocks the repeated action with a nonzero strict exit."""
        cli = (Path(__file__).resolve().parents[2] / "scripts" / "sage"
               / "sage_objective_state_gate.py")
        proposals = {"schema": "sage-objective-state-proposals-v1",
                     "objective": "#50", "proposals": [
                         self.proposal("source_metadata_identity", "revalidate",
                                       "5e15f72d95827e026637cf4161048b7afbc8072e")]}
        path = self.root / "proposals.json"
        path.write_text(json.dumps(proposals), encoding="utf-8")
        target = self.root / "report.json"
        command = [sys.executable, str(cli), "--receipt", str(self.receipt_path),
                   "--manifest", str(self.manifest_path), "--repo", str(self.repo),
                   "--proposals", str(path), "--output", str(target), "--strict"]
        completed = subprocess.run(command, capture_output=True, text=True,
                                   check=False)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8"))[
            "proposals"][0]["status"], "blocked_repeat")

    def test_cli_refuses_to_overwrite_report(self) -> None:
        """An earlier evidence report cannot be silently overwritten."""
        from sage_objective_state_gate import run
        from argparse import Namespace

        path = self.root / "proposals.json"
        payload = {"schema": "sage-objective-state-proposals-v1",
                   "objective": "#50", "proposals": [
                       self.proposal("tri_state_evidence_presence", "validate")]}
        path.write_text(json.dumps(payload), encoding="utf-8")
        output = self.root / "existing.json"
        output.write_text("{}", encoding="utf-8")
        arguments = Namespace(receipt=self.receipt_path, manifest=self.manifest_path,
                              repo=self.repo, proposals=path, output=output,
                              strict=False)
        with self.assertRaises(EvidenceError):
            run(arguments)

if __name__ == "__main__":
    unittest.main()
