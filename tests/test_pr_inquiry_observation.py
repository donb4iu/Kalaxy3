"""Tests for trusted-base SAGE PR inquiry reporting and optional enforcement."""

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
SOURCE = ROOT / "scripts/ci/pr_inquiry_observation.py"
SPEC = importlib.util.spec_from_file_location("pr_inquiry_observation", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def invoke(*args: str) -> str:
    """Run a Git or OpenSSL operation for a disposable fixture.

    Args:
        args: Exact executable and arguments.
    """
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()


def new_fixture(root: Path, thread: bool = False) -> dict[str, Path]:
    """Build an isolated PR checkout and matching GitHub event.

    Args:
        root: Writable temporary test directory.
        thread: Whether to include a candidate work-thread record.
    """
    candidate = root / "candidate"
    candidate.mkdir()
    invoke("git", "-C", str(candidate), "init", "-q")
    invoke("git", "-C", str(candidate), "config", "user.email", "test@example.invalid")
    invoke("git", "-C", str(candidate), "config", "user.name", "Test")
    (candidate / "README.md").write_text("Test checkout\n")
    if thread:
        path = candidate / "docs/sage/pr-work/pr-62.json"
        path.parent.mkdir(parents=True)
        example = json.loads((ROOT / "examples/pr62-work-thread.json").read_text())
        example["pr_number"] = 62
        path.write_text(json.dumps(example))
    invoke("git", "-C", str(candidate), "add", ".")
    invoke("git", "-C", str(candidate), "commit", "-qm", "test")
    sha = invoke("git", "-C", str(candidate), "rev-parse", "HEAD")
    event = root / "event.json"
    event.write_text(json.dumps({"pull_request": {"number": 62,
        "title": "Protect PR admission", "head": {"sha": sha}}}))
    return {"candidate": candidate, "event_path": event,
            "trusted": ROOT, "output": root / "out"}


def write_signed_inquiry(files: dict[str, Path]) -> None:
    """Supply a real signature and separate trusted-base test key.

    Args:
        files: Isolated paths for the test checkout and trusted base.
    """
    trusted = files["output"].parent / "trusted"
    import shutil
    shutil.copytree(ROOT / "scripts", trusted / "scripts")
    keys = trusted / ".github/sage/authorized-signers"
    keys.mkdir(parents=True)
    private = trusted / "private.pem"
    public = keys / "semantic-retrieval-controller.pem"
    invoke("openssl", "genrsa", "-out", str(private), "2048")
    invoke("openssl", "pkey", "-in", str(private), "-pubout", "-out", str(public))
    rev = trusted / ".github/sage/semantic-collection-revision.txt"
    rev.write_text("3" * 40 + "\n")
    folder = files["candidate"] / "docs/sage/pr-inquiry/pr-62"
    folder.mkdir(parents=True)
    proposal = folder / "proposal.md"
    proposal.write_text("Reuse Actions for signing-controller build.\n")
    record: dict[str, Any] = {
        "schema": "sage-semantic-inquiry-attestation-v1",
        "objective": "#62", "milestone": "proposed — issue link not verified",
        "proposal_sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        "collection_revision": "3" * 40,
        "search_scope": "Kalaxy3 repository", "retriever": "trusted-semantic-test",
        "attester_role": "semantic-retrieval-controller",
        "inquiries": [{"question": "What image build exists?", "returned": []}],
    }
    receipt = folder / "receipt.json"
    payload = (json.dumps(record, sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False) + "\n")
    receipt.write_bytes(payload.encode("utf-8"))
    invoke("openssl", "dgst", "-sha256", "-sign", str(private),
           "-out", str(folder / "signature.bin"), str(receipt))
    invoke("git", "-C", str(files["candidate"]), "add", ".")
    invoke("git", "-C", str(files["candidate"]), "commit", "-qm", "attest")
    event = json.loads(files["event_path"].read_text())
    event["pull_request"]["head"]["sha"] = invoke(
        "git", "-C", str(files["candidate"]), "rev-parse", "HEAD")
    files["event_path"].write_text(json.dumps(event))
    files["trusted"] = trusted


class ObservationTests(unittest.TestCase):
    """Prove missing, attested and manipulated evidence stays distinct."""

    def test_missing_thread_does_not_invent_prior_art(self) -> None:
        """Display unknown information without treating it as no prior art."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder))
            result = MODULE.render(**files)
            self.assertEqual(result["thread"], "missing")
            self.assertEqual(result["inquiry"], "missing")
            html = (files["output"] / "dashboard.html").read_text()
            self.assertIn("No inquiry record supplied", html)
            self.assertNotIn("prior art does not exist", html)

    def test_candidate_thread_never_qualifies_itself(self) -> None:
        """Do not turn model-authored assertions into provenance."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder), thread=True)
            result = MODULE.render(**files)
            self.assertEqual(result["thread"], "candidate_unverified")
            self.assertEqual(result["qualification"], "not_granted")
            self.assertIn("GitHub Actions", (files["output"] / "dashboard.html").read_text())

    def test_enforcement_fails_closed_without_attestation(self) -> None:
        """Require a verified inquiry when the trusted workflow opts in."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder), thread=True)
            with self.assertRaises(MODULE.ObservationError):
                MODULE.render(**files, enforce=True)

    def test_signed_zero_result_inquiry_is_attested(self) -> None:
        """Accept an authentic inquiry that found nothing without completeness claims."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder), thread=True)
            write_signed_inquiry(files)
            result = MODULE.render(**files, enforce=True)
            self.assertEqual(result["inquiry"], "attested_provenance_only")
            projection = json.loads((files["output"] / "work.json").read_text())
            self.assertEqual(projection["inquiry_attestation"]["result_count"], 0)

    def test_wrong_head_is_rejected(self) -> None:
        """Reject data from a different PR revision."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder))
            event = json.loads(files["event_path"].read_text())
            event["pull_request"]["head"]["sha"] = "0" * 40
            files["event_path"].write_text(json.dumps(event))
            with self.assertRaises(MODULE.ObservationError):
                MODULE.render(**files)

    def test_candidate_symlink_cannot_escape_checkout(self) -> None:
        """Prevent PR-supplied paths from pointing outside their checkout."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder))
            docs = files["candidate"] / "docs"
            docs.mkdir()
            (docs / "sage").symlink_to(Path(folder), target_is_directory=True)
            with self.assertRaises(MODULE.ObservationError):
                MODULE.render(**files)

    def test_wrong_signature_fails_required_mode(self) -> None:
        """Reject self-certified or altered inquiry evidence."""
        with tempfile.TemporaryDirectory() as folder:
            files = new_fixture(Path(folder), thread=True)
            write_signed_inquiry(files)
            receipt = files["candidate"] / "docs/sage/pr-inquiry/pr-62/receipt.json"
            receipt.write_text(receipt.read_text().replace("What image build exists?", "Other?"))
            with self.assertRaises(MODULE.ObservationError):
                MODULE.render(**files, enforce=True)


if __name__ == "__main__":
    unittest.main()
