"""Contract tests for observable SAGE Project/RACI objective episodes."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from sage_episode_visibility import (
    EpisodeError,
    construct_event,
    find_comment,
    marker,
    publish,
    render_comment,
    required_environment,
    validate_receipt,
)


class EpisodeVisibilityTests(unittest.TestCase):
    """Assert RACI attribution, readback lineage, and mutation boundaries."""

    def setUp(self) -> None:
        """Initialize a synthetic GitHub Actions run without credentials."""
        self.env = {
            "GITHUB_REPOSITORY": "donb4iu/Kalaxy3",
            "GITHUB_ACTIONS": "true",
            "GITHUB_RUN_ID": "41792799940",
            "GITHUB_SHA": "a" * 40,
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_ACTOR": "donb4iu",
            "SAGE_PROJECT_NUMBER": "15", "SAGE_ISSUE_NUMBER": "44",
            "SAGE_OBJECTIVE": "Issue #44 - governed Project and RACI readback",
            "SAGE_RESPONSIBLE": "GitHub Actions readback operator",
            "SAGE_ACCOUNTABLE": "Architect",
            "SAGE_AUTHORITY": "read-only Project inspection",
        }

    def receipt(self) -> dict[str, Any]:
        """Provide a synthetic, source-pinned Project readback fixture."""
        return {
            "repository": "donb4iu/Kalaxy3", "project_number": 15,
            "issue_number": 44, "project_owner": "donb4iu",
            "project_id": "PVT_kwHOAE2wDM4Bom6J",
            "item_id": "PVTI_lAHOAE2wDM4Bom6JzhDeePU",
            "issue_id": "I_kwDOSla5x88AAAABZ46quA",
            "source_sha": self.env["GITHUB_SHA"],
            "run_id": self.env["GITHUB_RUN_ID"],
            "issue_body_sha256": "1fbe56311ae9ffa3fefac39322d4bbc6af0e8ff83017341b13737db5130e40bb",
            "retrieved_at_utc": "2026-11-06T22:00:00+00:00",
            "status_updated_at": "2026-11-01T00:00:00Z",
        }

    def test_validated_runtime_and_attribution(self) -> None:
        """Keep the genuine actor, run, source, and authority boundary."""
        required_environment(self.env)
        event = construct_event("begin", "failure", self.env)
        body = render_comment(event)
        self.assertIn("Accountable: Architect", body)
        self.assertIn("Promotion: **not authorized**", body)
        self.assertIn("[#15](https://github.com/users/donb4iu/projects/15)", body)
        self.assertIn("[#44](https://github.com/donb4iu/Kalaxy3/issues/44)", body)
        self.assertIn("**Publication:** issue-comment create/update", body)
        self.assertEqual(
            event["visibility_authority"],
            "issue-comment create/update via job-scoped GITHUB_TOKEN",
        )
        self.assertIn(self.env["GITHUB_SHA"], body)
        self.assertIn(marker(self.env["GITHUB_RUN_ID"] + "-1"), body)

    def test_untrusted_branch_fails_closed(self) -> None:
        """Deny unqualified branches despite their GitHub Actions provenance."""
        self.env["GITHUB_REF"] = "refs/heads/feature/untrusted"
        with self.assertRaises(EpisodeError):
            required_environment(self.env)

    def test_rerun_attempt_is_distinct_episode(self) -> None:
        """Treat each GitHub Actions attempt as a separately visible episode."""
        self.env["GITHUB_RUN_ATTEMPT"] = "2"
        event = construct_event("begin", "failure", self.env)
        self.assertEqual(event["episode_id"], "41792799940-2")

    def test_nonproject_issue_contract_fails_closed(self) -> None:
        """Reject missing or invalid Project/issue identity."""
        self.env["SAGE_ISSUE_NUMBER"] = "0"
        with self.assertRaises(EpisodeError):
            required_environment(self.env)

    def test_github_actions_bot_is_an_attributable_actor(self) -> None:
        """Support workflows initiated by GitHub automation, not only humans."""
        self.env["GITHUB_ACTOR"] = "github-actions[bot]"
        required_environment(self.env)

    def test_invalid_actor_or_sha_fails_closed(self) -> None:
        """Reject forged or syntactically invalid attribution."""
        self.env["GITHUB_SHA"] = "not-a-sha"
        with self.assertRaises(EpisodeError):
            required_environment(self.env)

    def test_success_requires_verified_live_receipt(self) -> None:
        """Never report success from a green run without evidence."""
        with self.assertRaises(EpisodeError):
            construct_event("finish", "success", self.env)

    def test_qualification_cannot_claim_ac5_success(self) -> None:
        """Keep qualification transport observations separate from AC5."""
        self.env["GITHUB_REF"] = "refs/heads/qualification/sage-episode-visibility-x"
        event = construct_event("finish", "transport-exercise", self.env)
        self.assertEqual(event["status"], "transport_exercised")
        self.assertNotIn("Receipt SHA-256", render_comment(event))
        self.assertIn("**Publication:** issue-comment create/update", render_comment(event))

    def test_receipt_pins_run_and_source(self) -> None:
        """Bind Project evidence to the exact GitHub Actions run."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            path.write_text(json.dumps(self.receipt()), encoding="utf-8")
            evidence = validate_receipt(path, self.env)
        self.assertEqual(evidence["item_id"], self.receipt()["item_id"])
        self.assertRegex(evidence["receipt_sha256"], r"^[0-9a-f]{64}$")

    def test_drifted_source_or_issue_fails_closed(self) -> None:
        """Reject receipts from another run or issue."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            payload = self.receipt()
            payload["source_sha"] = "b" * 40
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(EpisodeError):
                validate_receipt(path, self.env)

    @patch("sage_episode_visibility.api_json")
    def test_begin_creates_one_comment(self, api: Any) -> None:
        """Create a Project-linked record only when no prior episode exists."""
        api.side_effect = [[], {"id": 123}]
        event = construct_event("begin", "failure", self.env)
        self.assertEqual(publish("fixture-token", event), 123)
        self.assertEqual(api.call_args_list[-1].args[1], "POST")
        self.assertEqual(api.call_args_list[-1].args[2], "/issues/44/comments")

    @patch("sage_episode_visibility.api_json")
    def test_finish_updates_only_existing_episode(self, api: Any) -> None:
        """Update the existing run's record instead of adding noise."""
        api.side_effect = [[{"id": 123, "body": marker(self.env["GITHUB_RUN_ID"] + "-1"),
                             "user": {"login": "github-actions[bot]"},
                             "created_at": "2026-11-06T00:00:00Z"}],
                           {"id": 123}]
        event = construct_event("finish", "failure", self.env)
        self.assertEqual(publish("fixture-token", event), 123)
        self.assertEqual(api.call_args_list[-1].args[1], "PATCH")
        self.assertEqual(api.call_args_list[-1].args[2], "/issues/comments/123")
        self.assertIn("Started: 2026-11-06T00:00:00Z", api.call_args_list[-1].args[4]["body"])

    @patch("sage_episode_visibility.api_json", return_value=[])
    def test_finish_without_start_fails_closed(self, api: Any) -> None:
        """Never fabricate a successful terminal record without opening."""
        with self.assertRaises(EpisodeError):
            publish("fixture-token", construct_event("finish", "failure", self.env))

    @patch("sage_episode_visibility.api_json")
    def test_duplicate_episode_fails_closed(self, api: Any) -> None:
        """Reject duplicate run markers rather than update an ambiguous issue."""
        found = {"id": 11, "body": marker(self.env["GITHUB_RUN_ID"] + "-1"),
                 "user": {"login": "github-actions[bot]"}}
        api.return_value = [found, {**found, "id": 12}]
        with self.assertRaises(EpisodeError):
            find_comment("fixture-token", self.env["GITHUB_RUN_ID"] + "-1", 44)


if __name__ == "__main__":
    unittest.main()
