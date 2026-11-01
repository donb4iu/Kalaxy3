"""Negative and positive checks for the least-authority Projects inspector."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import patch

from workflow.github_inspect import post_project_read_graphql
from workflow.model import WorkflowError
from workflow.projects_inspect import (
    ProjectsInspectionError,
    _OWNER_QUERY,
    _VIEWER_QUERY,
    _post_graphql,
    discover_projects,
    inspect_project,
    inspect_issue_work_item,
)


class TrustedProjectsTransportTests(unittest.TestCase):
    """Verify the existing trusted GitHub adapter only issues fixed reads."""

    @patch("workflow.github_inspect.urlopen")
    def test_fixed_query_posts_without_exposing_token(self, open_url: object) -> None:
        """Use a bounded read query and keep credentials out of results."""
        open_url.return_value = io.BytesIO(b'{"data":{"viewer":{"login":"test"}}}')
        result = post_project_read_graphql(_VIEWER_QUERY, {}, "synthetic-token")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data)["query"], _VIEWER_QUERY)
        self.assertEqual(result, {"viewer": {"login": "test"}})
        self.assertNotIn("synthetic-token", str(result))

    @patch("workflow.github_inspect.urlopen")
    def test_transport_rejects_mutation_before_network(self, open_url: object) -> None:
        """An arbitrary GraphQL mutation never reaches the network."""
        with self.assertRaisesRegex(WorkflowError, "Unapproved"):
            post_project_read_graphql("mutation { deleteIssue(input:{}) { id } }", {}, "x")
        open_url.assert_not_called()

    @patch("workflow.github_inspect.urlopen")
    def test_graphql_errors_fail_closed(self, open_url: object) -> None:
        """GraphQL errors cannot be mistaken for accepted Project evidence."""
        open_url.return_value = io.BytesIO(b'{"errors":[{"message":"denied"}]}')
        with self.assertRaisesRegex(WorkflowError, "returned errors"):
            post_project_read_graphql(_VIEWER_QUERY, {}, "synthetic-token")

    @patch("workflow.github_inspect.urlopen")
    def test_transport_error_does_not_expose_token(self, open_url: object) -> None:
        """A network failure produces no bearer token in the exception."""
        open_url.side_effect = OSError("unavailable")
        with self.assertRaises(WorkflowError) as caught:
            post_project_read_graphql(_VIEWER_QUERY, {}, "synthetic-token")
        self.assertNotIn("synthetic-token", str(caught.exception))


class ProjectsInspectorTests(unittest.TestCase):
    """Ensure only approved discovery, complete evidence and no mutation."""

    def test_rejects_unapproved_query(self) -> None:
        """Forbid arbitrary GraphQL supplied by an LLM."""
        with self.assertRaises(ProjectsInspectionError):
            _post_graphql("mutation { deleteProjectV2(input:{}) { clientMutationId } }", {}, "x")

    def test_rejects_missing_credential(self) -> None:
        """Reject requests without a credential."""
        with self.assertRaises(ProjectsInspectionError):
            _post_graphql(_VIEWER_QUERY, {}, "")

    @patch("workflow.projects_inspect._post_graphql")
    def test_viewer_discovery(self, query: object) -> None:
        """Accept complete viewer-owned listing."""
        query.return_value = {"viewer": {"login": "owner", "projectsV2": {
            "nodes": [{"id": "P1", "number": 1}],
            "pageInfo": {"hasNextPage": False},
        }}}
        self.assertEqual(discover_projects("x")["projects"][0]["id"], "P1")

    @patch("workflow.projects_inspect._post_graphql")
    def test_owner_query(self, query: object) -> None:
        """Use an explicitly scoped owner lookup."""
        query.return_value = {"user": {"login": "owner", "projectsV2": {
            "nodes": [], "pageInfo": {"hasNextPage": False},
        }}}
        self.assertTrue(discover_projects("x", "owner")["complete"])
        self.assertEqual(query.call_args.args[0], _OWNER_QUERY)

    @patch("workflow.projects_inspect._post_graphql")
    def test_truncation_fails_closed(self, query: object) -> None:
        """Never report partial discovery as a complete inventory."""
        query.return_value = {"viewer": {"login": "owner", "projectsV2": {
            "nodes": [], "pageInfo": {"hasNextPage": True},
        }}}
        with self.assertRaises(ProjectsInspectionError):
            discover_projects("x")

    @patch("workflow.projects_inspect._post_graphql")
    def test_project_details(self, query: object) -> None:
        """Accept only project records with complete fields and items."""
        query.return_value = {"user": {"login": "owner", "projectV2": {
            "id": "P1", "number": 1, "fields": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            "items": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        }}}
        self.assertTrue(inspect_project("x", "owner", 1)["complete"])

    @patch("workflow.projects_inspect._post_graphql")
    def test_rejects_wrong_project_identity(self, query: object) -> None:
        """Never report a different Project as the requested Project."""
        query.return_value = {"user": {"login": "owner", "projectV2": {
            "id": "P2", "number": 2,
            "fields": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            "items": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        }}}
        with self.assertRaisesRegex(ProjectsInspectionError, "Project number"):
            inspect_project("fixture", "owner", 1)

    @patch("workflow.projects_inspect._post_graphql")
    def test_rejects_wrong_project_owner(self, query: object) -> None:
        """Never claim owner authority for a different GitHub account."""
        query.return_value = {"user": {"login": "other", "projectV2": {}}}
        with self.assertRaisesRegex(ProjectsInspectionError, "owner identity"):
            inspect_project("fixture", "owner", 1)

    def test_bad_owner_and_number(self) -> None:
        """Reject unexpected owner syntax and invalid project identity."""
        with self.assertRaises(ProjectsInspectionError):
            discover_projects("x", "owner/name")
        with self.assertRaises(ProjectsInspectionError):
            inspect_project("x", "owner", 0)


class ProjectWorkItemTests(unittest.TestCase):
    """Verify Project issue discovery without intent or status fabrication."""

    def setUp(self) -> None:
        """Build a complete isolated GraphQL response for issue #44."""
        self.issue = {
            "id": "I44", "number": 44, "title": "Delegation",
            "url": "https://github.com/donb4iu/Kalaxy3/issues/44",
            "body": "## Objective\nDeliver issue-bound integration",
            "state": "OPEN", "updatedAt": "2026-10-28T00:00:00Z",
            "repository": {"nameWithOwner": "donb4iu/Kalaxy3"},
            "assignees": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        }
        self.item = {
            "id": "PVTI44", "type": "ISSUE",
            "fieldValueByName": {"name": "In Progress",
                                 "updatedAt": "2026-10-28T00:00:00Z"},
            "content": self.issue,
        }
        self.project = {
            "id": "P15", "number": 15, "items": {"nodes": [self.item],
            "pageInfo": {"hasNextPage": False}},
            "fields": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        }

    def inspect(self) -> dict[str, object]:
        """Inspect the isolated fixture through the public function."""
        with patch(
            "workflow.projects_inspect._post_graphql",
            return_value={"user": {"login": "donb4iu", "projectV2": self.project}},
        ):
            return inspect_issue_work_item(
                "read-only-fixture", "donb4iu", 15, "donb4iu/Kalaxy3", 44
            )

    def test_exposes_contract_and_actual_status(self) -> None:
        """Report the issue contract and status without claiming authority."""
        result = self.inspect()
        self.assertEqual(result["status"], "In Progress")
        self.assertIn("2026", result["status_updated_at"])
        self.assertIn("Objective", result["body"])
        self.assertEqual(result["assignees"], [])
        self.assertEqual(result["architect_intent_authorized"], "unverified")
        self.assertIn("authority_provenance", result["not_retrieved"])

    def test_rejects_other_repository(self) -> None:
        """Never substitute same-number issue from an unrelated repository."""
        self.issue["repository"]["nameWithOwner"] = "other/repo"
        with self.assertRaisesRegex(ProjectsInspectionError, "repository"):
            self.inspect()

    def test_rejects_missing_status(self) -> None:
        """Unknown status cannot be interpreted as selected work."""
        self.item["fieldValueByName"] = None
        with self.assertRaisesRegex(ProjectsInspectionError, "Status"):
            self.inspect()

    def test_rejects_missing_status_timestamp(self) -> None:
        """Reject status data without provenance of its update time."""
        del self.item["fieldValueByName"]["updatedAt"]
        with self.assertRaisesRegex(ProjectsInspectionError, "timestamp"):
            self.inspect()

    def test_rejects_truncated_assignees(self) -> None:
        """Never claim complete assignment evidence from a partial list."""
        self.issue["assignees"]["pageInfo"]["hasNextPage"] = True
        with self.assertRaisesRegex(ProjectsInspectionError, "truncated"):
            self.inspect()

    def test_rejects_duplicate_issue(self) -> None:
        """A duplicate item is ambiguous even if both have the same number."""
        self.project["items"]["nodes"].append(self.item.copy())
        with self.assertRaisesRegex(ProjectsInspectionError, "ambiguous"):
            self.inspect()

    def test_rejects_issue_url_substitution(self) -> None:
        """Reject a work item pointing to an unrelated canonical Issue URL."""
        self.issue["url"] = "https://github.com/other/repo/issues/44"
        with self.assertRaisesRegex(ProjectsInspectionError, "canonical URL"):
            self.inspect()

    def test_rejects_issue_url_query_or_fragment(self) -> None:
        """Reject an ambiguous or redirected Issue identity URL."""
        self.issue["url"] += "?redirect=true"
        with self.assertRaisesRegex(ProjectsInspectionError, "canonical URL"):
            self.inspect()

    def test_rejects_missing_immutable_issue_identity(self) -> None:
        """Require the GitHub issue node identifier alongside its number."""
        self.issue["id"] = None
        with self.assertRaisesRegex(ProjectsInspectionError, "immutable"):
            self.inspect()

    def test_rejects_missing_contract(self) -> None:
        """An empty issue body is not an executable work contract."""
        self.issue["body"] = ""
        with self.assertRaisesRegex(ProjectsInspectionError, "contract"):
            self.inspect()

    def test_rejects_truncated_project(self) -> None:
        """Do not treat incomplete Project pagination as complete work."""
        self.project["items"]["pageInfo"]["hasNextPage"] = True
        with self.assertRaisesRegex(ProjectsInspectionError, "truncated"):
            self.inspect()

    def test_rejects_invalid_issue_number(self) -> None:
        """Issue identity is a positive integer, never an LLM claim."""
        with self.assertRaises(ProjectsInspectionError):
            inspect_issue_work_item(
                "fixture", "donb4iu", 15, "donb4iu/Kalaxy3", True
            )

    def test_rejects_cross_origin_query(self) -> None:
        """A malicious GraphQL mutation is never a permitted query."""
        with self.assertRaises(ProjectsInspectionError):
            _post_graphql(
                "mutation { updateIssue(input:{}) { clientMutationId } }",
                {}, "fixture",
            )


if __name__ == "__main__":
    unittest.main()
