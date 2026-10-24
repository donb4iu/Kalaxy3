"""Cross-source Git evidence scenarios for Ansible and GitHub credentials."""

from __future__ import annotations

import hashlib
import unittest
from dataclasses import dataclass
from typing import Any

from service.architect import extractive_fallback, validate_architect_answer
from service.evidence import prioritize_records, select_evidence
from service.roles import RoleError


@dataclass
class Document:
    """Minimal LangChain-compatible document for offline testing."""

    page_content: str
    metadata: dict[str, Any]


def record(path: str, content: str) -> dict[str, str]:
    """Build a source with immutable provenance.

    Args:
        path: Git repository path.
        content: Exact committed document content.
    """
    return {"path": path, "content": content,
            "sha256": hashlib.sha256(content.encode()).hexdigest()}


class CrossSourceTests(unittest.TestCase):
    """Ensure accurate partial answers do not invent credential linkage."""

    def setUp(self) -> None:
        """Build independent Ansible and GitHub Actions records."""
        self.question = "How does Ansible manage GitHub credentials via Vault?"
        self.ansible = record("infrastructure/k3s-homelab/playbooks/platform.yml",
                              "- name: Install applications using Ansible and Helm\n")
        self.workflow = record(".github/workflows/kalaxy3_build_publish.yml",
                               "    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}\n"
                               "    API_TOKEN_GITHUB: ${{ secrets.API_TOKEN_GITHUB }}\n")
        self.policy = record("markdown/standards/kalaxy3-sage-operating-contract.md",
                             "RACI needs objective evidence and validated results.\n")

    def test_workflow_is_retrieved_before_generic_policy(self) -> None:
        """Keep GitHub Actions credential sources even if vector search prefers policy."""
        records = prioritize_records([self.ansible, self.workflow, self.policy],
                                     self.question)
        search = lambda _query, _k: [Document(self.policy["content"], {
            "path": self.policy["path"], "sha256": self.policy["sha256"]})]
        found = select_evidence(records, self.question, search)
        self.assertIn(self.workflow["path"], [x["path"] for x in found])
        self.assertIn(self.ansible["path"], [x["path"] for x in found])

    def test_cross_source_question_reports_a_gap(self) -> None:
        """Do not infer Ansible-to-GitHub credentials from unrelated committed facts."""
        evidence = {"retrieved_sources": [
            {"path": x["path"], "excerpt": x["content"]}
            for x in (self.ansible, self.workflow)]}
        answer = extractive_fallback(evidence, self.question)
        self.assertEqual(answer["answer_mode"], "evidence-gap")
        self.assertIn("do not establish", answer["answer"])
        validate_architect_answer(answer, evidence, self.question, internal_gap=True)
        with self.assertRaisesRegex(RoleError, "no direct source quote"):
            validate_architect_answer(answer, evidence, self.question)

    def test_github_token_quote_does_not_authorize_vault_claim(self) -> None:
        """An Ansible GitHub token mention alone is not proof of Vault storage."""
        source = record("infrastructure/k3s-homelab/playbooks/site.yml",
                        "github_token: Provided by an injected runtime variable")
        evidence = {"retrieved_sources": [{"path": source["path"],
                                            "excerpt": source["content"]}]}
        answer = {"answer": "Ansible Vault stores the GitHub token.",
                  "evidence_paths": [source["path"]],
                  "supporting_quotes": [{"path": source["path"],
                                         "quote": source["content"]}],
                  "uncertainties": []}
        with self.assertRaisesRegex(RoleError, "no direct source quote"):
            validate_architect_answer(answer, evidence, self.question)

    def test_fabricated_github_vault_claim_is_still_rejected(self) -> None:
        """Model output cannot label a claim as an internal evidence-gap fallback."""
        evidence = {"retrieved_sources": [{
            "path": self.ansible["path"], "excerpt": self.ansible["content"]}]}
        answer = {"answer": "Ansible Vault stores the GitHub token.",
                  "evidence_paths": [self.ansible["path"]],
                  "supporting_quotes": [{"path": self.ansible["path"],
                                         "quote": self.ansible["content"].strip()}],
                  "uncertainties": [], "answer_mode": "evidence-gap"}
        with self.assertRaises(RoleError):
            validate_architect_answer(answer, evidence, self.question)


if __name__ == "__main__":
    unittest.main()
