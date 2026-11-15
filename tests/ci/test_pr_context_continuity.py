"""Regression coverage for the non-blocking objective/PR continuity handoff."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch
from typing import Any

from scripts.ci.pr_context_continuity import (
    build_manifest,
    declared_context,
    evaluate,
    github_changed_paths,
    section_items,
)


BODY = """Context contract: v1
Parent objective: #90
Milestone issue: #91
Objective contribution: Publish the deterministic source manifest

## Declared change paths
- `scripts/sage/*`
- `tests/sage/*`

## Acceptance evidence
- Test run: 12 source identity regressions passed (candidate claim)

## Known uncertainties
- External evidence unavailable in this slice

## Next bounded work
- Read-only semantic retrieval adapter remains separate
"""


class ContinuityTests(unittest.TestCase):
    """Test declaration semantics independent of live GitHub or K3s."""

    def fixture(self, body: str = BODY) -> dict[str, Any]:
        """Construct a minimal pinned GitHub event.

        Args:
            body: Pull request Markdown body.
        """
        return {
            "pull_request": {"number": 92, "body": body,
                             "base": {"sha": "a" * 40},
                             "head": {"sha": "b" * 40}},
            "repository": {"full_name": "donb4iu/Kalaxy3"},
        }

    def codes(self, body: str, paths: list[str] | None) -> set[str]:
        """Return advisory codes from a PR body and changed paths.

        Args:
            body: PR body.
            paths: Observed changed paths or None.
        """
        return {f.code for f in evaluate(declared_context(body), paths)}

    def test_bounded_pr_has_no_warning(self) -> None:
        """A declared PR with matching source/test files remains advisory-clean."""
        self.assertEqual(self.codes(BODY, ["scripts/sage/one.py", "tests/sage/test_one.py"]), set())

    def test_undeclared_paths_warn(self) -> None:
        """Changing a second subsystem is observable as a scope concern."""
        self.assertIn("OUTSIDE_DECLARED_PATHS", self.codes(BODY, ["scripts/sage/one.py", "infrastructure/k3s/neo4j.yaml"]))

    def test_missing_files_are_unknown_not_clean(self) -> None:
        """No API results never count as a verified in-scope change list."""
        self.assertIn("CHANGED_FILES_UNKNOWN", self.codes(BODY, None))

    def test_no_contract_is_observable_not_blocking(self) -> None:
        """Legacy PRs produce a single nonblocking adoption diagnostic."""
        self.assertEqual(self.codes("Milestone issue: #91", []), {"CONTRACT_NOT_DECLARED"})

    def test_parent_not_a_milestone(self) -> None:
        """Parent objective used as a milestone warns without rejecting the PR."""
        self.assertIn("PARENT_AS_MILESTONE", self.codes(BODY.replace("#91", "#90"), []))

    def test_missing_evidence_is_not_a_pass(self) -> None:
        """Acceptance evidence must be traceable in the declared PR handoff."""
        body = BODY.replace("- Test run: 12 source identity regressions passed (candidate claim)", "")
        self.assertIn("EVIDENCE_UNDECLARED", self.codes(body, []))

    def test_unknowns_are_explicit(self) -> None:
        """The context boundary must preserve known uncertainty."""
        self.assertIn("UNCERTAINTY_UNDECLARED", self.codes(BODY.replace("- External evidence unavailable in this slice", ""), []))

    def test_next_milestone_is_explicit(self) -> None:
        """Missing continuation context is visible to subsequent agents."""
        self.assertIn("CONTINUATION_UNDECLARED", self.codes(BODY.replace("- Read-only semantic retrieval adapter remains separate", ""), []))

    def test_scope_paths_are_not_embedded_in_source_text(self) -> None:
        """Scope declarations only come from the intended Markdown section."""
        self.assertEqual(section_items("## Acceptance evidence\n- `foo.py`", "declared change paths"), [])

    def test_manifest_pins_base_head_and_limits_authority(self) -> None:
        """The resulting manifest preserves revisions without promoting claims."""
        manifest = build_manifest(self.fixture(), ["scripts/sage/one.py"], True)
        self.assertEqual(manifest["base_revision"], "a" * 40)
        self.assertEqual(manifest["head_revision"], "b" * 40)
        self.assertFalse(manifest["context_completeness_verified"])
        self.assertFalse(manifest["evidence_independently_qualified"])

    def test_changed_path_order_does_not_change_hash(self) -> None:
        """Reordering GitHub file observations cannot change source identity."""
        paths = ["tests/sage/test_one.py", "scripts/sage/one.py"]
        first = build_manifest(self.fixture(), sorted(paths), True)
        second = build_manifest(self.fixture(), list(reversed(paths)), True)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])

    def test_incomplete_changed_file_list_stays_unknown(self) -> None:
        """Paginated/truncated API output cannot establish scope equivalence."""
        manifest = build_manifest(self.fixture(), ["scripts/sage/one.py"], False)
        self.assertIn("CHANGED_FILES_UNKNOWN", [x["code"] for x in manifest["advisories"]])

    def test_metadata_is_not_acceptance(self) -> None:
        """Writing an acceptance-evidence claim never authenticates it."""
        manifest = build_manifest(self.fixture(), [], True)
        self.assertEqual(manifest["status"], "unverified_pr_claims_not_architect_acceptance")


    def test_read_only_file_list_is_enumerated(self) -> None:
        """A successful REST list provides observed paths, not semantic proof."""
        body = b'[{"filename": "scripts/sage/x.py"}]'
        with patch("scripts.ci.pr_context_continuity.urlopen", return_value=io.BytesIO(body)):
            paths, complete = github_changed_paths(
                "https://api.github.com", "donb4iu/Kalaxy3", 92, ""
            )
        self.assertEqual(paths, ["scripts/sage/x.py"])
        self.assertTrue(complete)

    def test_inaccessible_api_does_not_prove_scope(self) -> None:
        """A failed REST read cannot silently turn into a clean scope check."""
        with patch("scripts.ci.pr_context_continuity.urlopen", side_effect=OSError("unavailable")):
            paths, complete = github_changed_paths(
                "https://api.github.com", "donb4iu/Kalaxy3", 92, ""
            )
        self.assertIsNone(paths)
        self.assertFalse(complete)

    def test_no_external_effects_from_evaluation(self) -> None:
        """Pure evaluation never needs repository, network, or files."""
        self.assertEqual(self.codes(BODY, []), set())


if __name__ == "__main__":
    unittest.main()
