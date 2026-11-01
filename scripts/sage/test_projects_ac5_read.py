"""Negative and positive tests for Project #15 read-only receipt construction."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from sage_projects_ac5_read import Ac5ReadbackError, create_receipt


class Ac5ReadbackTests(unittest.TestCase):
    """Ensure runtime authority and actual contract evidence are mandatory."""

    def setUp(self) -> None:
        """Provide a synthetic protected workflow environment."""
        self.env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_REPOSITORY": "donb4iu/Kalaxy3",
            "SAGE_PROJECTS_CREDENTIAL": "fixture-not-real",
            "GITHUB_SHA": "a" * 40,
            "GITHUB_RUN_ID": "123",
            "GITHUB_ACTOR": "donb4iu",
        }
        self.item = {
            "repository": "donb4iu/Kalaxy3", "issue_number": 44,
            "project_number": 15, "item_id": "PVTI_123", "issue_id": "I_123",
            "body": "## Architect-approved Project/RACI Definition of Done",
            "issue_updated_at": "2026-11-01T00:00:00Z",
            "status": "In Progress", "status_updated_at": "2026-11-01T00:00:00Z",
            "assignees": [], "not_retrieved": ["issue_activity"],
        }

    @patch("sage_projects_ac5_read.inspect_issue_work_item")
    def test_receipt_excludes_token_and_body(self, read: object) -> None:
        """Verify source identification without persisting secrets or issue body."""
        read.return_value = self.item
        receipt = create_receipt(self.env)
        self.assertEqual(receipt["project_number"], 15)
        self.assertEqual(receipt["status"], "In Progress")
        self.assertNotIn("fixture-not-real", str(receipt))
        self.assertNotIn(self.item["body"], str(receipt))
        self.assertEqual(receipt["architect_approval"], "not_implied")

    @patch("sage_projects_ac5_read.inspect_issue_work_item")
    def test_requires_main(self, read: object) -> None:
        """Reject an environment invocation on a feature branch."""
        self.env["GITHUB_REF"] = "refs/heads/feature/unreviewed"
        with self.assertRaises(Ac5ReadbackError):
            create_receipt(self.env)
        read.assert_not_called()

    @patch("sage_projects_ac5_read.inspect_issue_work_item")
    def test_requires_approved_dod(self, read: object) -> None:
        """Reject live issues that omit the Architect-approved DoD."""
        self.item["body"] = "## Objective"
        read.return_value = self.item
        with self.assertRaises(Ac5ReadbackError):
            create_receipt(self.env)

    @patch("sage_projects_ac5_read.inspect_issue_work_item")
    def test_requires_status_timestamp(self, read: object) -> None:
        """Reject missing Project status provenance."""
        self.item["status_updated_at"] = None
        read.return_value = self.item
        with self.assertRaises(Ac5ReadbackError):
            create_receipt(self.env)


if __name__ == "__main__":
    unittest.main()
