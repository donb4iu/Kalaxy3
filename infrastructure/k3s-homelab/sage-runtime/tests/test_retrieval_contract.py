"""Deterministic regressions for the LangChain-backed SAGE context contract."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from service.evidence import allowed_path, select_evidence, snapshot
from service.roles import RoleError, validate_citations
from service.workflow import validate_shared_context


@dataclass
class SampleDocument:
    """Minimal test document with LangChain-compatible fields."""

    page_content: str
    metadata: dict[str, Any]


def create_git_fixture(folder: Path) -> tuple[Path, str]:
    """Create an immutable evidence fixture including Ansible Vault prior art.

    Args:
        folder: Temporary test directory.
    """
    root = folder / "kalaxy3"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Tester"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "tester@example.com"], check=True)
    sources = {
        "AGENTS.md": "Objective: reliable execution.\n",
        "SAGE.md": "Only governed evidence authorizes changes.\n",
        "infrastructure/k3s-homelab/playbooks/README.md":
            "Ansible Vault protects Git automation credentials.\n",
        "infrastructure/k3s-homelab/group_vars/secrets.yml":
            "$ANSIBLE_VAULT;1.1;AES256\nmy-secret\n",
    }
    for relative, content in sources.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    return root, sha


class RetrievalTests(unittest.TestCase):
    """Verify that guardrails cannot be bypassed by an LLM invocation."""

    def test_git_evidence_survives_worktree_mutation(self) -> None:
        """Only committed Ansible prior art may enter role context."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, revision = create_git_fixture(Path(tmp))
            records = snapshot(repo, revision)
            source = next(record for record in records if "playbooks/README" in record["path"])
            (repo / source["path"]).write_text("HashiCorp Vault is installed\n")
            self.assertIn("Ansible Vault", source["content"])
            self.assertEqual(snapshot(repo, revision), records)

    def test_secret_content_is_not_indexed(self) -> None:
        """Exclude encrypted vars and credential-like paths from the index."""
        with tempfile.TemporaryDirectory() as tmp:
            repo, revision = create_git_fixture(Path(tmp))
            all_paths = [record["path"] for record in snapshot(repo, revision)]
            self.assertFalse(any("group_vars" in name for name in all_paths))
            self.assertFalse(allowed_path("infrastructure/k3s-homelab/passwords.yml"))

    def test_provenance_validation_rejects_modified_result(self) -> None:
        """A retrieved text modification fails before it reaches any role."""
        record = {"path": "SAGE.md", "content": "A", "sha256": hashlib.sha256(b"A").hexdigest()}
        altered = SampleDocument("Invented fact", {"path": "SAGE.md", "sha256": record["sha256"]})
        with self.assertRaisesRegex(ValueError, "altered committed content"):
            select_evidence([record], "question", lambda query, k: [altered])

    def test_provenance_validation_rejects_unknown_path(self) -> None:
        """A vector match cannot cite a path missing from pinned Git."""
        doc = SampleDocument("A", {"path": "invented.md", "sha256": "x"})
        with self.assertRaisesRegex(ValueError, "unverified source"):
            select_evidence([], "question", lambda query, k: [doc])

    def test_shared_context_is_mandatory(self) -> None:
        """No role proceeds without the pinned retrieval manifest."""
        with self.assertRaisesRegex(ValueError, "mandatory shared Git context"):
            validate_shared_context({"revision": "abc", "acceptance_criteria": ["pass"]})

    def test_engineering_must_cite_retrieved_evidence(self) -> None:
        """Engineering cannot substitute an invented platform assertion."""
        context = {"source_sha256": {"AGENTS.md": "a"}, "evidence": {
            "retrieved_sources": [{"path": "playbooks/README.md", "sha256": "b"}]}}
        with self.assertRaises(RoleError):
            validate_citations({"evidence_paths": ["invented-vault.yml"]}, context)
        validate_citations({"evidence_paths": ["playbooks/README.md"]}, context)


if __name__ == "__main__":
    unittest.main()
