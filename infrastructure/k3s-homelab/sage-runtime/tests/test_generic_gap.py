"""Regression tests for bounded evidence fallback on general architecture requests."""

from __future__ import annotations

import unittest

from service.architect import (
    generic_evidence_fallback,
    validate_architect_answer,
)
from service.roles import RoleError


class ArchitectureFallbackTests(unittest.TestCase):
    """Verify context-grounded fallback without invented implementation facts."""

    def test_broad_architecture_question_returns_cited_gap(self) -> None:
        """Use exact source excerpts for the cross-domain Python app request."""
        question = "Deploy a Python application using Kubernetes and Ansible"
        sources = [
            {"path": "infrastructure/k3s-homelab/playbooks/platform.yml",
             "excerpt": "- name: Configure the Kubernetes cluster with Ansible playbooks\n",
             "sha256": "abc"},
            {"path": "infrastructure/k3s-homelab/README.md",
             "excerpt": "Kubernetes is deployed with K3s on the Intel nodes.\n",
             "sha256": "def"},
        ]
        evidence = {"retrieved_sources": sources}
        answer = generic_evidence_fallback(evidence, question)
        self.assertEqual(answer["answer_mode"], "evidence-gap")
        self.assertIn("cannot verify a complete implementation plan", answer["answer"])
        self.assertGreaterEqual(len(answer["supporting_quotes"]), 1)
        validate_architect_answer(answer, evidence, question, internal_gap=True)

    def test_fallback_rejects_unrelated_material(self) -> None:
        """Unrelated governance text must not become evidence for a deployment."""
        evidence = {"retrieved_sources": [
            {"path": "SAGE.md", "excerpt": "Be responsible in all decisions and be honest.",
             "sha256": "abc"},
        ]}
        with self.assertRaises(RoleError):
            generic_evidence_fallback(evidence, "Deploy Python on Kubernetes")

    def test_unverified_quote_stays_blocked(self) -> None:
        """The fallback bypasses relevance, not source-integrity validation."""
        evidence = {"retrieved_sources": [
            {"path": "infrastructure/k3s-homelab/playbooks/platform.yml",
             "excerpt": "- name: Configure Kubernetes with Ansible playbooks\n",
             "sha256": "abc"},
        ]}
        result = generic_evidence_fallback(evidence, "Kubernetes Ansible")
        result["supporting_quotes"][0]["quote"] = "A fake external architecture requirement"
        with self.assertRaises(RoleError):
            validate_architect_answer(result, evidence, "Kubernetes Ansible",
                                      internal_gap=True)


if __name__ == "__main__":
    unittest.main()
