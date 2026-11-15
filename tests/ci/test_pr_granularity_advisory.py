"""Regression coverage for Kalaxy3's non-blocking PR granularity advisory."""

from __future__ import annotations

import unittest
from typing import Any

from scripts.ci.pr_granularity_advisory import (
    closing_issues,
    dod_domain_count,
    evaluate,
    milestone_issues,
)


class GranularityAdvisoryTests(unittest.TestCase):
    """Verify deterministic advisory behavior without GitHub mutation."""

    def setUp(self) -> None:
        """Create a small, independently acceptable milestone issue."""
        self.issue: dict[str, Any] = {
            "title": "Implement bounded ingestion check",
            "body": "## Acceptance criteria\n- [ ] Regression tests pass.",
            "labels": [],
        }

    def codes(
        self, body: str, issues: dict[int, Any] | None = None
    ) -> set[str]:
        """Return finding codes for a PR and supplied issue evidence.

        Args:
            body: Pull-request body to evaluate.
            issues: Mock issue records; defaults to a valid #45.
        """
        records = {45: self.issue} if issues is None else issues
        return {finding.code for finding in evaluate(body, records)}

    def test_valid_milestone(self) -> None:
        """A bounded, documented milestone produces no warnings."""
        self.assertEqual(self.codes("Milestone issue: #45\nCloses #45"), set())

    def test_missing_milestone(self) -> None:
        """An undeclared milestone is a warning, not a failure."""
        self.assertIn("MISSING_MILESTONE", self.codes("Refs #45"))

    def test_multiple_milestones(self) -> None:
        """Two milestone issues are identified as suspicious."""
        codes = self.codes(
            "Milestone issues: #45, #46", {45: self.issue, 46: self.issue}
        )
        self.assertIn("MULTIPLE_MILESTONES", codes)

    def test_outside_milestone_closure(self) -> None:
        """Closing an issue other than the milestone generates an advisory."""
        self.assertIn(
            "OUTSIDE_MILESTONE", self.codes("Milestone issue: #45\nFixes #46")
        )

    def test_same_milestone_closure(self) -> None:
        """Closing the declared milestone does not indicate scope drift."""
        self.assertNotIn(
            "OUTSIDE_MILESTONE",
            self.codes("Milestone issue: #45\nResolves #45"),
        )

    def test_parent_title(self) -> None:
        """Explicit parent-objective titles are recognized."""
        issue = {**self.issue, "title": "Parent objective: evidence index"}
        self.assertIn(
            "PARENT_OBJECTIVE", self.codes("Milestone issue: #45", {45: issue})
        )

    def test_epic_label(self) -> None:
        """Parent/epic GitHub labels are recognized."""
        issue = {**self.issue, "labels": [{"name": "epic"}]}
        self.assertIn(
            "PARENT_OBJECTIVE", self.codes("Milestone issue: #45", {45: issue})
        )

    def test_nine_dod_domains(self) -> None:
        """Nine separately headed DoD domains trigger an advisory."""
        body = "## Definition of Done\n" + "\n".join(
            f"### Domain {number}\n- [ ] Complete." for number in range(1, 10)
        )
        self.assertEqual(dod_domain_count(body), 9)
        issue = {**self.issue, "body": body}
        self.assertIn(
            "MULTI_DOMAIN_DOD", self.codes("Milestone issue: #45", {45: issue})
        )

    def test_missing_acceptance(self) -> None:
        """An issue without recognizable acceptance checks is flagged."""
        issue = {**self.issue, "body": "Design a system."}
        self.assertIn(
            "MISSING_ACCEPTANCE",
            self.codes("Milestone issue: #45", {45: issue}),
        )

    def test_checkbox_acceptance(self) -> None:
        """A checked or unchecked acceptance item is recognizable."""
        issue = {**self.issue, "body": "- [ ] Evidence attached."}
        self.assertNotIn(
            "MISSING_ACCEPTANCE",
            self.codes("Milestone issue: #45", {45: issue}),
        )

    def test_unavailable_issue_is_unknown(self) -> None:
        """A missing API result never becomes a fabricated verification."""
        codes = self.codes("Milestone issue: #45", {45: None})
        self.assertIn("ISSUE_UNVERIFIED", codes)
        self.assertNotIn("MISSING_ACCEPTANCE", codes)

    def test_markdown_milestone_field(self) -> None:
        """Markdown milestone fields and distinct references are supported."""
        self.assertEqual(milestone_issues("- **Milestone issue:** #45"), [45])
        self.assertEqual(closing_issues("Closes #45; fixes #45"), [45])


if __name__ == "__main__":
    unittest.main()
