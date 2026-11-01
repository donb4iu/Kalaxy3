"""Contract tests for multi-user SAGE Projects credentials and operations."""
from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.github_inspect import post_project_status_update_graphql
from workflow.model import WorkflowError
from workflow.projects_credentials import ProjectsCredentialError, resolve_projects_token
from workflow.projects_operational import ProjectsOperationError, update_operational_status


class CredentialResolutionTests(unittest.TestCase):
    """Require independently supplied secret sources, not LLM credential prompts."""

    def test_actions_environment_secret(self) -> None:
        """Accept the Actions credential only inside its declared runtime."""
        context = {"GITHUB_ACTIONS": "true", "SAGE_PROJECTS_CREDENTIAL": "fixture-only"}
        self.assertEqual(resolve_projects_token("actions-secret", context), "fixture-only")
        with self.assertRaisesRegex(ProjectsCredentialError, "Actions runtime"):
            resolve_projects_token("actions-secret", {"SAGE_PROJECTS_CREDENTIAL": "x"})

    def test_vault_protected_file(self) -> None:
        """Load a private Vault projection without putting token bytes in Git."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            path.write_text("fixture-only\n", encoding="utf-8")
            path.chmod(0o600)
            self.assertEqual(resolve_projects_token("vault-file", {
                "SAGE_PROJECTS_VAULT_FILE": str(path)
            }), "fixture-only")
            path.chmod(0o644)
            with self.assertRaisesRegex(ProjectsCredentialError, "private"):
                resolve_projects_token("vault-file", {
                    "SAGE_PROJECTS_VAULT_FILE": str(path)
                })

    def test_rejects_symlink(self) -> None:
        """Reject a symlink to prevent a confused-deputy secret read."""
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / "token"
            original.write_text("fixture-only", encoding="utf-8")
            original.chmod(0o600)
            alias = Path(directory) / "alias"
            alias.symlink_to(original)
            with self.assertRaisesRegex(ProjectsCredentialError, "symlink"):
                resolve_projects_token("vault-file", {"SAGE_PROJECTS_VAULT_FILE": str(alias)})

    def test_rejects_unapproved_source(self) -> None:
        """Never accept plaintext Git, inline token, or arbitrary sources."""
        with self.assertRaisesRegex(ProjectsCredentialError, "Unapproved"):
            resolve_projects_token("git-plaintext", {})


class OperationalStatusTests(unittest.TestCase):
    """Constrain mutation to checked operational status, not Architect intent."""

    def setUp(self) -> None:
        """Create a precise issue snapshot and existing Status field option."""
        import hashlib

        self.body = "## Objective\nProtected intent"
        self.digest = hashlib.sha256(self.body.encode("utf-8")).hexdigest()
        self.item = {"body": self.body, "status": "Todo", "status_updated_at": "t1",
                     "item_id": "IT44"}
        self.project = {"project": {"id": "P15", "fields": {"nodes": [
            {"id": "F1", "name": "Status", "options": [
                {"id": "O1", "name": "In Progress"},
                {"id": "O2", "name": "Done"},
            ]}]}}}
        self.arguments = {"owner": "donb4iu", "project_number": 15,
                          "repository": "donb4iu/Kalaxy3", "issue_number": 44,
                          "new_status": "In Progress", "expected_issue_digest": self.digest,
                          "expected_status_timestamp": "t1", "actor": "sage-runner"}

    @patch("workflow.projects_operational.post_project_status_update_graphql")
    @patch("workflow.projects_operational.inspect_project")
    @patch("workflow.projects_operational.inspect_issue_work_item")
    def test_proposal_does_not_mutate(self, read: object, project: object,
                                      write: object) -> None:
        """Default to a non-approval proposal, even with a write-capable token."""
        read.return_value = self.item
        project.return_value = self.project
        receipt = update_operational_status("synthetic", **self.arguments)
        self.assertFalse(receipt["applied"])
        self.assertEqual(receipt["architect_approval"], "not_implied")
        write.assert_not_called()

    @patch("workflow.projects_operational.post_project_status_update_graphql")
    @patch("workflow.projects_operational.inspect_project")
    @patch("workflow.projects_operational.inspect_issue_work_item")
    def test_explicit_status_update(self, read: object, project: object,
                                    write: object) -> None:
        """Allow only the exact existing operational Status field and item."""
        read.return_value = self.item
        project.return_value = self.project
        receipt = update_operational_status("synthetic", **self.arguments, apply=True)
        self.assertTrue(receipt["applied"])
        write.assert_called_once_with("synthetic", "P15", "IT44", "F1", "O1")

    @patch("workflow.projects_operational.inspect_project")
    @patch("workflow.projects_operational.inspect_issue_work_item")
    def test_rejects_approval_and_stale_contract(self, read: object,
                                                  project: object) -> None:
        """Block approval-like status and stale Architect intent at runtime."""
        read.return_value = self.item
        project.return_value = self.project
        with self.assertRaisesRegex(ProjectsOperationError, "allowlist"):
            update_operational_status("synthetic", **{**self.arguments,
                                                        "new_status": "Done"}, apply=True)
        with self.assertRaisesRegex(ProjectsOperationError, "Stale"):
            update_operational_status("synthetic", **{**self.arguments,
                                           "expected_issue_digest": "0" * 64}, apply=True)
        with self.assertRaisesRegex(ProjectsOperationError, "Stale"):
            update_operational_status("synthetic", **{**self.arguments,
                                         "expected_status_timestamp": "t0"}, apply=True)

    @patch("workflow.github_inspect.urlopen")
    def test_fixed_mutation_and_verified_response(self, open_url: object) -> None:
        """Transport sends only a fixed Project Status mutation with bounded IDs."""
        open_url.return_value = io.BytesIO(
            b'{"data":{"updateProjectV2ItemFieldValue":{"projectV2Item":{"id":"IT44"}}}}'
        )
        post_project_status_update_graphql("synthetic", "P15", "IT44", "F1", "O1")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        import json
        payload = json.loads(request.data)
        self.assertIn("updateProjectV2ItemFieldValue", payload["query"])
        self.assertEqual(payload["variables"]["item"], "IT44")
        self.assertNotIn("synthetic", request.data.decode("utf-8"))

    @patch("workflow.github_inspect.urlopen")
    def test_rejects_unconfirmed_mutation(self, open_url: object) -> None:
        """Do not report a write without GitHub confirming exact item ID."""
        open_url.return_value = io.BytesIO(
            b'{"data":{"updateProjectV2ItemFieldValue":{"projectV2Item":{"id":"WRONG"}}}}'
        )
        with self.assertRaisesRegex(WorkflowError, "confirm"):
            post_project_status_update_graphql("synthetic", "P15", "IT44", "F1", "O1")


if __name__ == "__main__":
    unittest.main()
