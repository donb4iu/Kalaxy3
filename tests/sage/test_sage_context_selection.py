"""Behavior tests for bounded context selection and separate omission challenge."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sage_context_critique import challenge, validate_probes
from sage_context_discovery import exact_revision, inventory
from sage_context_selection import (excerpt_permissions, load_review, render,
                                    review_labels, run, safe_excerpt, select)


class ContextSelectionTests(unittest.TestCase):
    """Use real disposable Git history; do not require Neo4j or a network."""

    def setUp(self) -> None:
        """Create independently named alternative, selected and secret sources."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.write(
            "docs/context.md",
            "Context assembly and evidence discovery\nApproved summary\n"
        )
        self.write("docs/rejected.md", "Historical RabbitMQ alternative was rejected\n")
        self.write("docs/oversight.md", "Independent audit for recovery obligations\n")
        self.write("docs/creds.md", "context evidence\nsecret=NEVER_EXPORT_ME\n")
        self.write("secrets/private.key", "BEGIN PRIVATE KEY\nNOT_FOR_PACKET\n")
        self.git("add", ".")
        self.git("commit", "-qm", "initial")
        self.main = exact_revision(self.repo, "HEAD")
        self.git("switch", "-qc", "feature/context")
        self.write("docs/feature.md", "Context assembly new feature evidence\n")
        self.git("add", ".")
        self.git("commit", "-qm", "feature")
        self.feature = exact_revision(self.repo, "HEAD")
        self.tree = inventory(self.repo, self.feature)

    def git(self, *args: str) -> None:
        """Run Git commands on the synthetic repository.

        Args:
            *args: Git arguments without a shell.
        """
        subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def write(self, name: str, content: str) -> None:
        """Write a test-only source before committing it.

        Args:
            name: Repo-relative path.
            content: Source contents.
        """
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def review(self) -> dict[str, Any]:
        """Provide externally claimed relevance and separate omission probes."""
        return {"reviewer": "external_assessor_unverified",
                "probe_origin": "fixture_critic_separate_from_nomination",
                "probes": ["RabbitMQ", "recovery obligations"],
                "judgments": [
                    {"path": "docs/rejected.md", "relevance": "relevant",
                     "perspective": "historical",
                     "rationale": "Previously rejected alternative matters now"},
                    {"path": "docs/context.md", "relevance": "relevant",
                     "perspective": "supporting",
                     "rationale": "Direct objective description evidence"}],
                "excerpts": []}

    def call(self, review: dict[str, Any] | None = None
             ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Run the actual selection code with optional reviewer evidence.

        Args:
            review: External evidence labels and probe phrases, if present.
        """
        return select(self.repo, self.feature, self.main, "#54",
                      "Context assembly evidence discovery", "critic",
                      self.review() if review is None else review)

    def test_outside_selection_critic_finds_historical_alternative(self) -> None:
        """Critic probes nominate a source omitted by the initial selection."""
        manifest, report = self.call()
        self.assertIn("docs/rejected.md", report["outside_nomination_visible_paths"])
        record = next(row for row in manifest["sources"]
                      if row["path"] == "docs/rejected.md")
        self.assertFalse(record["candidate_discovered"])
        self.assertEqual(record["perspective"], "historical")

    def test_critic_does_not_certify_semantic_truth(self) -> None:
        """Even labeled historical sources remain unverified judgments."""
        manifest, report = self.call()
        self.assertFalse(report["semantically_validated"])
        self.assertFalse(manifest["independent_relevance_verified"])
        self.assertFalse(manifest["context_completeness_verified"])
        self.assertEqual(manifest["architect_acceptance"], "not_evaluated")

    def test_absent_review_records_unknowns(self) -> None:
        """Missing judgments cannot silently become relevant or accepted."""
        blank = {"judgments": [], "excerpts": [], "probes": []}
        manifest, report = self.call(blank)
        self.assertEqual(report["outside_nomination_total"], 0)
        self.assertTrue(all(row["relevance"] == "not_evaluated"
                            for row in manifest["sources"]))

    def sha(self, path: str) -> str:
        """Compute a pinned test fixture digest.

        Args:
            path: Exact Git-tree path.
        """
        data = subprocess.check_output(["git", "-C", str(self.repo), "cat-file",
                                        "blob", self.tree[path]["git_oid"]])
        return hashlib.sha256(data).hexdigest()

    def test_authorized_excerpt_is_bounded_and_pinned(self) -> None:
        """Only explicitly allowed relevant exact-Git source text is copied."""
        review = self.review()
        review["excerpts"] = [{"path": "docs/context.md", "authorized": True,
                               "git_oid": self.tree["docs/context.md"]["git_oid"],
                               "content_sha256": self.sha("docs/context.md")}]
        manifest, _ = self.call(review)
        excerpt = next(row["excerpt"] for row in manifest["sources"]
                       if row["path"] == "docs/context.md")
        self.assertEqual(excerpt["status"], "explicitly_authorized_bounded_excerpt")
        self.assertIn("Context assembly", excerpt["text"])
        self.assertEqual(excerpt["lines"], [1, 2])

    def test_wrong_digest_or_revision_refuses_excerpt(self) -> None:
        """Authorization for a different source object cannot authorize bytes."""
        review = self.review()
        review["excerpts"] = [{"path": "docs/context.md", "authorized": True,
                               "git_oid": "0" * 40,
                               "content_sha256": self.sha("docs/context.md")}]
        with self.assertRaises(ValueError):
            self.call(review)

    def test_wrong_sha256_refuses_excerpt(self) -> None:
        """An authorized path and object still require the correct digest."""
        review = self.review()
        review["excerpts"] = [{"path": "docs/context.md", "authorized": True,
                               "git_oid": self.tree["docs/context.md"]["git_oid"],
                               "content_sha256": "0" * 64}]
        with self.assertRaises(ValueError):
            self.call(review)

    def test_sensitive_source_path_refuses_even_with_authorization(self) -> None:
        """A signed candidate label cannot defeat sensitive-path protection."""
        review = self.review()
        review["excerpts"] = [{"path": "secrets/private.key", "authorized": True,
                               "git_oid": self.tree["secrets/private.key"]["git_oid"],
                               "content_sha256": self.sha("secrets/private.key")}]
        with self.assertRaises(ValueError):
            self.call(review)

    def test_sensitive_content_is_omitted_even_when_path_approved(self) -> None:
        """An ordinary document with secret-like assignments stays private."""
        review = self.review()
        review["judgments"].append({"path": "docs/creds.md", "relevance": "relevant",
                                    "perspective": "context",
                                    "rationale": "Synthetic sensitive content fixture"})
        review["excerpts"] = [{"path": "docs/creds.md", "authorized": True,
                               "git_oid": self.tree["docs/creds.md"]["git_oid"],
                               "content_sha256": self.sha("docs/creds.md")}]
        manifest, _ = self.call(review)
        excerpt = next(row["excerpt"] for row in manifest["sources"]
                       if row["path"] == "docs/creds.md")
        self.assertEqual(excerpt["status"], "omitted_sensitive_pattern")
        self.assertNotIn("NEVER_EXPORT_ME", render(manifest))

    def test_probe_path_does_not_inflate_source_selection(self) -> None:
        """Unjudged probe sources remain critic findings, not accepted content."""
        review = self.review()
        review["judgments"] = []
        manifest, report = self.call(review)
        self.assertIn("docs/rejected.md", report["outside_nomination_visible_paths"])
        selected = [row["path"] for row in manifest["sources"]]
        self.assertNotIn("docs/rejected.md", selected)

    def test_duplicate_review_labels_fail_closed(self) -> None:
        """Duplicate paths cannot silently override opposing assessments."""
        review = self.review()
        review["judgments"].append(review["judgments"][0])
        with self.assertRaises(ValueError):
            self.call(review)

    def test_unknown_review_source_fails_closed(self) -> None:
        """Labels from a different source revision cannot be treated as found."""
        review = self.review()
        review["judgments"][0]["path"] = "docs/nonexistent.md"
        with self.assertRaises(ValueError):
            self.call(review)

    def test_independent_probe_bounds(self) -> None:
        """Malicious or overly broad probe strings are refused."""
        for probes in (["a"], ["A" * 100], ["context; rm -rf /"], ["hello"] * 13):
            with self.assertRaises(ValueError):
                validate_probes(probes)

    def test_source_order_and_repeat_are_deterministic(self) -> None:
        """Same pinned source and reviewer file gives identical manifest IDs."""
        a, b = self.call()[0], self.call()[0]
        self.assertEqual(a, b)
        self.assertEqual(a["manifest_id"], b["manifest_id"])

    def test_output_never_enters_inspected_repo(self) -> None:
        """Review artifacts cannot be generated inside the source checkout."""
        with self.assertRaises(ValueError):
            run(self.repo, self.feature, self.main, "#54", "Context assembly",
                "critic", self.review(), self.repo / "output")

    def test_real_local_artifacts_are_revision_labeled(self) -> None:
        """Non-mutating local execution writes inspectable bounded artifacts."""
        out = Path(self.tmp.name) / "output"
        manifest = run(self.repo, self.feature, self.main, "#54",
                       "Context assembly evidence discovery", "critic",
                       self.review(), out)
        self.assertEqual(json.loads((out / "selection-manifest.json").read_text()),
                         manifest)
        self.assertEqual(manifest["main_revision"], self.main)
        self.assertEqual(manifest["feature_revision"], self.feature)
        self.assertTrue((out / "omission-challenge.json").exists())

    def test_review_input_does_not_claim_independence(self) -> None:
        """The presence of reviewer labels does not authenticate their origin."""
        manifest, _ = self.call()
        self.assertEqual(manifest["reviewer_claim"], "external_assessor_unverified")
        self.assertFalse(manifest["independent_relevance_verified"])

    def test_json_packet_escapes_untrusted_backtick(self) -> None:
        """Untrusted source text cannot close the rendered Markdown fence."""
        review = self.review()
        review["judgments"][1]["rationale"] = "Do not follow ``` markdown injections"
        result, _ = self.call(review)
        text = render(result)
        self.assertNotIn("``` markdown injections", text)
        self.assertIn("\\u0060", text)

    def test_missing_and_restricted_scope_remain_visible(self) -> None:
        """Out-of-scope external systems cannot be marked searched implicitly."""
        manifest, critique = self.call()
        self.assertEqual(
            manifest["other_authoritative_source_families"], "not_searched"
        )
        self.assertFalse(critique["omission_completeness_verified"])


if __name__ == "__main__":
    unittest.main()
