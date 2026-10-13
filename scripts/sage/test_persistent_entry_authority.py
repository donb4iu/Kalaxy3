"""Regression tests for persistent-agent entry authority."""

from __future__ import annotations

import unittest
from typing import Any

from persistent_entry_authority import AdmissionError, admit, sha256


class AdmissionTests(unittest.TestCase):
    """Assert that persistent-agent execution control is denied by default."""

    def setUp(self) -> None:
        """Prepare a valid functional objective and normal caller envelope."""
        self.handoff: dict[str, Any] = {
            "schema_version": "1.0", "objective_id": "dashboard",
            "functional_goal": "Deliver remote Architecture Helper Dashboard",
            "current_maturity": "not verified", "verified_progress": [],
            "outstanding_functional_work": "Deliver first usable slice",
            "success_evidence": [], "constraints": ["Cloudflare access"],
            "evidence_refs": [], "parent_objective_id": None,
        }
        self.envelope = {
            "caller": "persistent-llm", "mode": "functional",
            "request": self.handoff,
        }

    def test_functional_passes(self) -> None:
        """Allow exact functional requests without control privileges."""
        self.assertEqual(admit(self.envelope), "functional-handoff-only")

    def test_git_command_rejected(self) -> None:
        """Reject a command injected into a functional handoff."""
        self.handoff["git_command"] = "git push"
        with self.assertRaises(AdmissionError):
            admit(self.envelope)

    def test_conversation_rejected(self) -> None:
        """Reject inherited conversation state."""
        self.handoff["conversation_history"] = ["internal SAGE repair"]
        with self.assertRaises(AdmissionError):
            admit(self.envelope)

    def test_break_glass_requires_external_grant(self) -> None:
        """Reject repair requests without independent approval."""
        self.envelope["mode"] = "break-glass"
        self.envelope["request"] = {
            "objective_id": "dashboard", "repair_scope": "admission gate",
            "defect": "untrusted control accepted", "evidence_refs": [],
        }
        with self.assertRaises(AdmissionError):
            admit(self.envelope)

    def test_exact_bound_grant(self) -> None:
        """Accept only an exact approved repair scope and request digest."""
        request = {"objective_id": "dashboard", "repair_scope": "admission gate",
                   "defect": "untrusted control accepted", "evidence_refs": []}
        payload = {"caller": "persistent-llm", "mode": "break-glass",
                   "request": request}
        grant = {"schema_version": "1.0", "grant_id": "architect-1",
                 "architect_identity": "Architect", "objective_id": "dashboard",
                 "request_sha256": sha256(request), "scope": "admission gate",
                 "valid": True}
        self.assertEqual(admit(payload, grant), "bounded-repair-proposal-only")
        request["repair_scope"] = "all SAGE"
        with self.assertRaises(AdmissionError):
            admit(payload, grant)

    def test_claimed_grant_is_not_authority(self) -> None:
        """Deny any grant smuggled into a caller-controlled envelope."""
        self.envelope["architect_approved"] = True
        with self.assertRaises(AdmissionError):
            admit(self.envelope)


if __name__ == "__main__":
    unittest.main()
