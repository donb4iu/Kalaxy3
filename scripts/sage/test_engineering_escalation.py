"""Regression checks for the functional-to-engineering correction boundary."""
import unittest
from sage_engineering_escalation import prepare_correction


class EscalationTests(unittest.TestCase):
    def test_rejected_candidate_preserves_evidence(self):
        request = prepare_correction("Deliver dashboard", {"decision": "plan"},
                                     {"decision": {"verdict": "reject"}}, "referee-rejected")
        self.assertEqual(request["authority"]["execution_authorized"], False)
        self.assertEqual(request["referee"]["decision"]["verdict"], "reject")

    def test_no_duplicate_accepted_escalation(self):
        with self.assertRaises(ValueError):
            prepare_correction("Task", {}, {"decision": {"verdict": "allow"}}, "accepted")

    def test_digest_is_stable(self):
        a = prepare_correction("Task", {"b": 2, "a": 1}, None, "blocked")
        b = prepare_correction("Task", {"a": 1, "b": 2}, None, "blocked")
        self.assertEqual(a["fresh_decision_sha256"], b["fresh_decision_sha256"])

    def test_empty_functional_request_rejected(self):
        with self.assertRaises(ValueError):
            prepare_correction("  ", None, None, "blocked")
