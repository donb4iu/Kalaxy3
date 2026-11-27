"""Real Git/OpenSSL interoperability tests against the captured PR #61 verifier."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

from pr61_remote_issue import issue_remote, trusted_module


def command(arguments: Sequence[str], cwd: Path | None = None) -> bytes:
    """Execute isolated Git or OpenSSL test fixtures.

    Args:
        arguments: Command argument vector.
        cwd: Optional disposable Git checkout.
    """
    return subprocess.run(
        list(arguments), cwd=cwd, capture_output=True, check=True
    ).stdout


class PR61RemoteIssueTests(unittest.TestCase):
    """Require a real verifier, signed receipt, and Git source scope."""

    def setUp(self) -> None:
        """Create disposable Git history with both independently signed roles."""
        source = os.environ.get("SAGE_PR61_SOURCE")
        if not source or not Path(source).is_file():
            raise RuntimeError("SAGE_PR61_SOURCE must name actual trusted verifier")
        self.temp = tempfile.TemporaryDirectory(prefix="sage-pr61-contract-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        command(["git", "init", "-q", "-b", "main", str(self.repo)])
        command(["git", "config", "user.name", "Fixture Auditor"], self.repo)
        command(["git", "config", "user.email", "test@example.invalid"], self.repo)
        verifier = self.repo / "scripts/ci/sage_audit_receipt.py"
        verifier.parent.mkdir(parents=True)
        shutil.copyfile(source, verifier)
        self.keys: dict[str, Path] = {}
        self.create_keys()
        self.commit("verifier + public trust anchors")
        command(["git", "checkout", "-q", "-b", "feature"], self.repo)
        file = self.repo / "src/feature.py"
        file.parent.mkdir()
        file.write_text("implemented = True\n")
        audit = self.repo / "evidence/auditor.json"
        audit.parent.mkdir()
        audit.write_text('{"independent_review":"qualified"}\n')
        self.commit("implementation and evaluated evidence")

    def create_keys(self) -> None:
        """Generate distinct RSA-3072 test identities with public Git anchors."""
        keys = self.repo / ".github/sage/authorized-signers"
        keys.mkdir(parents=True)
        for role in ("architect", "auditor"):
            private = Path(self.temp.name) / f"{role}-private.pem"
            public = keys / f"{role}.pem"
            command(["openssl", "genpkey", "-algorithm", "RSA", "-pkeyopt",
                     "rsa_keygen_bits:3072", "-out", str(private)])
            command(["openssl", "pkey", "-in", str(private), "-pubout",
                     "-out", str(public)])
            self.keys[role] = private

    def commit(self, message: str) -> None:
        """Advance disposable evidence history.

        Args:
            message: Git commit subject.
        """
        command(["git", "add", "-A"], self.repo)
        command(["git", "commit", "-qm", message], self.repo)

    def options(self, disposition: str) -> argparse.Namespace:
        """Create bounded remote signing request for existing PR semantics.

        Args:
            disposition: PR #61 disposition.
        """
        return argparse.Namespace(
            repo=self.repo, base="main", objective="#50",
            disposition=disposition, audit_path="evidence/auditor.json",
            reason="Architect reviewed and explicitly accepts the bypass",
            original_query_ref="", sign_url="https://sign.example.invalid",
            purpose="SAGE independent PR audit authorization",
        )

    def fake_remote_sign(self, file: Path, purpose: str,
                         url: str, *, role: str) -> Path:
        """Emulate remote OpenBao return using actual OpenSSL RSA-3072 bytes.

        Args:
            file: Canonical exact receipt bytes.
            purpose: Human-visible reason for the operation.
            url: Fake HTTPS Access origin.
            role: Controller used for the signature.
        """
        payload = file.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        sig = subprocess.run(["openssl", "dgst", "-sha256", "-sign",
                              str(self.keys[role])], input=payload,
                             capture_output=True, check=True).stdout
        output = file.with_suffix(".remote.json")
        output.write_text(json.dumps({
            "sha256": digest, "signer_role": role,
            "signature_algorithm": "pkcs1v15", "hash_algorithm": "sha2-256",
            "signature_b64": base64.b64encode(sig).decode(),
        }))
        return output

    def issue(self, disposition: str, signing_role: str) -> str:
        """Run the real adapter with fake transport and true RSA signatures.

        Args:
            disposition: Governed receipt disposition.
            signing_role: Controller signing identity to use.
        """
        def fake(file: Path, purpose: str, url: str) -> Path:
            """Return an independently generated signature for the chosen role.

            Args:
                file: Canonical receipt file.
                purpose: Human-visible signing request purpose.
                url: Endpoint fixture.
            """
            return self.fake_remote_sign(file, purpose, url, role=signing_role)
        with patch("pr61_remote_issue.sign_receipt", side_effect=fake):
            return issue_remote(self.options(disposition))

    def verify(self, digest: str) -> subprocess.CompletedProcess[bytes]:
        """Run trusted PR #61 verifier against committed receipt and evidence.

        Args:
            digest: Receipt ID committed in the final trailer.
        """
        self.commit_receipt(digest)
        head = command(["git", "rev-parse", "HEAD"], self.repo).decode().strip()
        return subprocess.run([
            "python3", "scripts/ci/sage_audit_receipt.py", "verify",
            "--repo", ".", "--base", "main", "--head", head,
            "--trusted-keys", ".github/sage/authorized-signers",
        ], cwd=self.repo, capture_output=True, check=False)

    def commit_receipt(self, digest: str) -> None:
        """Commit only generated receipt files and the exact PR #61 trailer.

        Args:
            digest: Verified canonical SHA-256.
        """
        command(["git", "add", ".sage/audit-receipts"], self.repo)
        command(["git", "commit", "-qm", "SAGE audit closeout", "-m",
                 f"SAGE-Audit-Receipt-SHA256: {digest}"], self.repo)

    def test_auditor_executed_reaches_real_verifier(self) -> None:
        """Independent auditor signing an executed disposition passes PR #61."""
        digest = self.issue("executed", "auditor")
        result = self.verify(digest)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_architect_bypass_reaches_real_verifier(self) -> None:
        """Architect bypass signature with reason passes the real verifier."""
        digest = self.issue("bypassed", "architect")
        result = self.verify(digest)
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_wrong_controller_fails_before_files(self) -> None:
        """Auditor cannot sign the Architect's bypass, even in a test repo."""
        with self.assertRaisesRegex(Exception, "signature"):
            self.issue("bypassed", "auditor")
        self.assertFalse((self.repo / ".sage/audit-receipts").exists())

    def test_code_mutation_invalidates_real_verifier(self) -> None:
        """PR #61 rejects a changed implementation after signing."""
        digest = self.issue("executed", "auditor")
        self.commit_receipt(digest)
        changed = self.repo / "src/other.py"
        changed.write_text("changed = True\n")
        self.commit("late unaudited implementation")
        head = command(["git", "rev-parse", "HEAD"], self.repo).decode().strip()
        result = subprocess.run([
            "python3", "scripts/ci/sage_audit_receipt.py", "verify",
            "--repo", ".", "--base", "main", "--head", head,
            "--trusted-keys", ".github/sage/authorized-signers",
        ], cwd=self.repo, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)

    def test_trusted_verifier_hash_guard(self) -> None:
        """Refuse to execute changed verifier code from unreviewed Git."""
        with tempfile.TemporaryDirectory() as scratch:
            trusted_module(self.repo, "main", Path(scratch))
        file = self.repo / "scripts/ci/sage_audit_receipt.py"
        file.write_text(file.read_text() + "\n# not trusted\n")
        self.commit("modify verifier in untrusted PR")
        with tempfile.TemporaryDirectory() as scratch:
            with self.assertRaisesRegex(RuntimeError, "changed"):
                trusted_module(self.repo, "HEAD", Path(scratch))


if __name__ == "__main__":
    unittest.main()
