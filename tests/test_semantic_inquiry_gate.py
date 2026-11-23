"""Tests for a protected SAGE semantic-inquiry attestation boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sage_semantic_inquiry_gate", ROOT / "scripts/ci/sage_semantic_inquiry_gate.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
REVISION = "1" * 40


def command(args: list[str]) -> None:
    """Run OpenSSL and fail a test if its command fails.

    Args:
        args: OpenSSL argument sequence.
    """
    subprocess.run(["openssl", *args], check=True, capture_output=True)


def generate_fixture(path: Path) -> dict[str, Path]:
    """Generate a disposable signer and independently signed inquiry.

    Args:
        path: Temporary test directory for ephemeral key material.
    """
    private = path / "private.pem"
    public = path / "public.pem"
    proposal = path / "proposal.txt"
    receipt = path / "receipt.json"
    signature = path / "receipt.sig"
    proposal.write_text("Use existing Buildx multiarch pipeline\n")
    command(["genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048",
             "-out", str(private)])
    command(["pkey", "-in", str(private), "-pubout", "-out", str(public)])
    value: dict[str, Any] = {
        "schema": MODULE.SCHEMA,
        "objective": "#62",
        "milestone": "issue-63",
        "proposal_sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        "collection_revision": REVISION,
        "search_scope": "Kalaxy3 governed semantic collection",
        "retriever": "SAGE approved semantic adapter",
        "attester_role": "semantic-retrieval-controller",
        "inquiries": [{"question": "Existing image build?", "returned": []}],
    }
    receipt.write_bytes(MODULE.canonical(value))
    command(["dgst", "-sha256", "-sign", str(private), "-out", str(signature),
             str(receipt)])
    return {"private": private, "public": public, "proposal": proposal,
            "receipt": receipt, "signature": signature}


class InquiryGateTests(unittest.TestCase):
    """Verify the boundary checks bytes, signers, and iteration scope."""

    def test_signed_record_passes_without_results(self) -> None:
        """A genuine zero-result query satisfies occurrence, not completeness."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            result = self.verify(files)
            self.assertEqual(result["status"], "attested_inquiry_recorded")
            self.assertEqual(result["result_count"], 0)

    def test_tampering_is_rejected(self) -> None:
        """Reject a changed semantic result after signature issuance."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            value = json.loads(files["receipt"].read_text())
            value["inquiries"][0]["returned"] = ["invented ref"]
            files["receipt"].write_bytes(MODULE.canonical(value))
            with self.assertRaises(MODULE.InquiryError):
                self.verify(files)

    def test_revised_proposal_requires_new_receipt(self) -> None:
        """Reject scope changes made after the independent inquiry signature."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            files["proposal"].write_text("Use a new BuildKit cluster\n")
            with self.assertRaises(MODULE.InquiryError):
                self.verify(files)

    def test_wrong_objective_rejected(self) -> None:
        """Do not replay evidence for a different objective."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            with self.assertRaises(MODULE.InquiryError):
                self.verify(files, objective="#99")

    def test_wrong_collection_revision_rejected(self) -> None:
        """Do not silently reuse evidence from an unrelated semantic revision."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            with self.assertRaises(MODULE.InquiryError):
                self.verify(files, revision="2" * 40)

    def test_dashboard_consumes_signed_inquiry(self) -> None:
        """Use signed returned refs, rather than model-authored inquiry claims."""
        with tempfile.TemporaryDirectory() as directory:
            files = generate_fixture(Path(directory))
            project_spec = importlib.util.spec_from_file_location(
                "pr_work_projection",
                ROOT / "scripts/sage/architecture_helper/pr_work_projection.py",
            )
            assert project_spec and project_spec.loader
            projector = importlib.util.module_from_spec(project_spec)
            project_spec.loader.exec_module(projector)
            import argparse
            args = argparse.Namespace(
                receipt=files["receipt"], signature=files["signature"],
                trusted_key=files["public"], proposal=files["proposal"],
                collection_revision=REVISION,
            )
            thread = {"objective": {"id": "#62"}, "milestone": {"id": "issue-63"}}
            attestation, inquiries = projector.load_verified_inquiry(args, thread)
            self.assertEqual(attestation["result_count"], 0)
            self.assertEqual(inquiries[0]["question"], "Existing image build?")
            self.assertEqual(len(inquiries), 1)

    def test_wrong_signer_rejected(self) -> None:
        """A self-made key cannot substitute for an admitted trusted public key."""
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            (parent / "first").mkdir()
            (parent / "other").mkdir()
            files = generate_fixture(parent / "first")
            other = generate_fixture(parent / "other")
            files["public"] = other["public"]
            with self.assertRaises(MODULE.InquiryError):
                self.verify(files)

    def verify(self, files: dict[str, Path], objective: str = "#62",
               revision: str = REVISION) -> dict[str, Any]:
        """Run the exact verification path with one test fixture.

        Args:
            files: Generated fixture paths.
            objective: Expected objective binding.
            revision: Expected trusted semantic revision.
        """
        return MODULE.verify_inquiry(files["receipt"], files["signature"],
                                     files["public"], objective, "issue-63",
                                     files["proposal"], revision)


if __name__ == "__main__":
    unittest.main()
