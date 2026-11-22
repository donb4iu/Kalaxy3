"""Offline integration tests for signed SAGE audit receipts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Sequence


SOURCE = Path(__file__).resolve().parents[2] / "scripts/ci"
sys.path.insert(0, str(SOURCE))

from sage_audit_receipt import (  # noqa: E402
    RECEIPTS,
    ReceiptError,
    encode,
    git,
    issue,
    parser,
    revision_scope,
    verify,
)


def run(args: Sequence[str], cwd: Path | None = None) -> None:
    """Run a disposable tool command, raising on errors.

    Args:
        args: Command and arguments.
        cwd: Optional working directory.
    """
    subprocess.run(list(args), cwd=cwd, check=True, capture_output=True)


class ReceiptIntegrationTests(unittest.TestCase):
    """Exercise the receipt protocol against real disposable Git histories."""

    def setUp(self) -> None:
        """Build a repository, audit artifact, and separated role signing keys."""
        self.temp = tempfile.TemporaryDirectory(prefix="sage-pr-audit-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        run(["git", "init", "-q", "-b", "main", str(self.repo)])
        run(["git", "config", "user.name", "SAGE Test"], self.repo)
        run(["git", "config", "user.email", "sage-test@example.invalid"], self.repo)
        self.commit("README.md", "base\n", "baseline")
        run(["git", "checkout", "-q", "-b", "feature"], self.repo)
        self.commit("src/feature.py", "value = 1\n", "implementation")
        self.commit(
            "evidence/audit.json", '{"role":"independent_auditor"}\n',
            "auditor evidence",
        )
        self.trusted = self.root / "trusted"
        self.trusted.mkdir()
        for role in ("auditor", "architect"):
            self.make_key(role)

    def make_key(self, role: str) -> None:
        """Create a non-production RSA key pair for the named test role.

        Args:
            role: Signer role name.
        """
        private = self.root / f"{role}-private.pem"
        public = self.trusted / f"{role}.pem"
        run(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt",
             "rsa_keygen_bits:2048", "-out", str(private)])
        run(["openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public)])

    def commit(self, name: str, content: str, message: str) -> None:
        """Write and commit one fixture file.

        Args:
            name: Repository-relative file path.
            content: File contents.
            message: Commit message.
        """
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        run(["git", "add", name], self.repo)
        run(["git", "commit", "-qm", message], self.repo)

    def issue_args(
        self, disposition: str = "executed", role: str = "auditor"
    ) -> argparse.Namespace:
        """Build CLI issuance arguments for an expected role.

        Args:
            disposition: Audit disposition.
            role: Private signing key identity.
        """
        return parser().parse_args([
            "issue", "--repo", str(self.repo), "--base", "main",
            "--objective", "#50", "--disposition", disposition,
            "--audit-path", "evidence/audit.json", "--reason",
            "Architect consciously accepts this omission",
            "--signing-key", str(self.root / f"{role}-private.pem"),
        ])

    def closeout(self, digest: str) -> None:
        """Commit the exact receipt and signature with the required trailer.

        Args:
            digest: Canonical receipt SHA-256.
        """
        run(["git", "add", f"{RECEIPTS}/{digest}.json",
             f"{RECEIPTS}/{digest}.sig"], self.repo)
        run(["git", "commit", "-qm", "SAGE audit closeout", "-m",
             f"SAGE-Audit-Receipt-SHA256: {digest}"], self.repo)

    def verify_args(self) -> argparse.Namespace:
        """Build verifier arguments for the current feature head."""
        head = git(self.repo, "rev-parse", "HEAD").decode().strip()
        return parser().parse_args([
            "verify", "--repo", str(self.repo), "--base", "main",
            "--head", head, "--trusted-keys", str(self.trusted),
        ])

    def test_executed_audit_verifies(self) -> None:
        """An independently signed executed audit validates end-to-end."""
        digest = issue(self.issue_args())
        self.closeout(digest)
        self.assertEqual(verify(self.verify_args()), digest)

    def test_architect_signed_bypass_verifies(self) -> None:
        """An Architect-signed bypass with a reason is permitted."""
        digest = issue(self.issue_args("bypassed", "architect"))
        self.closeout(digest)
        self.assertEqual(verify(self.verify_args()), digest)

    def test_wrong_key_rejected(self) -> None:
        """An auditor cannot authorize their own bypass."""
        digest = issue(self.issue_args("bypassed", "auditor"))
        self.closeout(digest)
        with self.assertRaisesRegex(ReceiptError, "signature"):
            verify(self.verify_args())

    def test_late_code_edit_invalidates_scope(self) -> None:
        """Changing the code after signature invalidates even a valid receipt."""
        digest = issue(self.issue_args())
        self.closeout(digest)
        self.commit("src/new.py", "different = 2\n", "later code")
        run(["git", "commit", "--amend", "--no-edit", "-m",
             "SAGE-Audit-Receipt-SHA256: " + digest], self.repo)
        with self.assertRaisesRegex(ReceiptError, "scope"):
            verify(self.verify_args())

    def test_receipt_tampering_rejected(self) -> None:
        """Changing receipt bytes causes digest validation to fail."""
        digest = issue(self.issue_args())
        self.closeout(digest)
        file = self.repo / RECEIPTS / f"{digest}.json"
        data = json.loads(file.read_text())
        data["objective"] = "#999"
        file.write_bytes(encode(data))
        run(["git", "add", str(file)], self.repo)
        run(["git", "commit", "--amend", "-q", "--no-edit"], self.repo)
        with self.assertRaisesRegex(ReceiptError, "do not match"):
            verify(self.verify_args())

    def test_missing_trailer_rejected(self) -> None:
        """An unreferenced receipt cannot silently qualify a PR."""
        digest = issue(self.issue_args())
        run(["git", "add", f"{RECEIPTS}/{digest}.json",
             f"{RECEIPTS}/{digest}.sig"], self.repo)
        run(["git", "commit", "-qm", "no trailer"], self.repo)
        with self.assertRaisesRegex(ReceiptError, "trailer"):
            verify(self.verify_args())

    def test_uncommitted_evidence_rejected(self) -> None:
        """Review evidence must already belong to governed Git lineage."""
        (self.repo / "uncommitted.txt").write_text("not governed")
        with self.assertRaisesRegex(ReceiptError, "Commit changes"):
            issue(self.issue_args())

    def test_missing_bypass_reason_rejected(self) -> None:
        """A reasonless bypass cannot be signed into compliance."""
        args = self.issue_args("bypassed", "architect")
        args.reason = "short"
        with self.assertRaisesRegex(ReceiptError, "justification"):
            issue(args)

    def test_untrusted_key_replacement_does_not_count(self) -> None:
        """A PR-local substitute cannot override the trusted signer key."""
        digest = issue(self.issue_args())
        self.closeout(digest)
        other = self.root / "other-trusted"
        other.mkdir()
        key = (self.trusted / "architect.pem").read_bytes()
        (other / "auditor.pem").write_bytes(key)
        with self.assertRaisesRegex(ReceiptError, "signature"):
            args = self.verify_args()
            args.trusted_keys = other
            verify(args)

    def test_scope_ignores_receipt_only_closeout(self) -> None:
        """An audit closeout does not create a self-referential diff hash."""
        before = revision_scope(self.repo, "main", "HEAD")
        digest = issue(self.issue_args())
        self.closeout(digest)
        after = revision_scope(self.repo, "main", "HEAD")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
