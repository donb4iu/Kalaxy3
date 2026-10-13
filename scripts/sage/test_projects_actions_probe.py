"""Contract tests for a restricted GitHub Projects permission probe."""
import unittest
from unittest.mock import patch
from typing import Any

from projects_actions_probe import QUERY, inspect


class ProjectsProbeTests(unittest.TestCase):
    """Test read-only probe behavior without real network or credentials."""

    def test_missing_token(self) -> None:
        """Fail closed if no token is provided."""
        self.assertEqual(inspect("")["reason"], "no_valid_token")

    def test_fixed_query(self) -> None:
        """Never authorize GraphQL mutations."""
        self.assertNotIn("mutation", QUERY.lower())

    def test_bad_token(self) -> None:
        """Reject injected header separators."""
        self.assertEqual(inspect("x\ny")["status"], "unavailable")

    def test_http_denial(self) -> None:
        """Report HTTP denial without returning a credential."""
        from urllib.error import HTTPError
        with patch("projects_actions_probe.urlopen", side_effect=HTTPError(
                "https://api.github.com/graphql", 403, "Denied", {}, None)):
            result = inspect("fixture-secret")
        self.assertNotIn("fixture-secret", str(result))
        self.assertEqual(result["http_status"], 403)


if __name__ == "__main__":
    unittest.main()
