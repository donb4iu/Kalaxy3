"""Negative and positive checks for the least-authority Projects inspector."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from workflow.projects_inspect import (
    ProjectsInspectionError,
    _OWNER_QUERY,
    _VIEWER_QUERY,
    _post_graphql,
    discover_projects,
    inspect_project,
)


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
        query.return_value = {"user": {"projectV2": {
            "id": "P1", "fields": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            "items": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        }}}
        self.assertTrue(inspect_project("x", "owner", 1)["complete"])

    def test_bad_owner_and_number(self) -> None:
        """Reject unexpected owner syntax and invalid project identity."""
        with self.assertRaises(ProjectsInspectionError):
            discover_projects("x", "owner/name")
        with self.assertRaises(ProjectsInspectionError):
            inspect_project("x", "owner", 0)


if __name__ == "__main__":
    unittest.main()
