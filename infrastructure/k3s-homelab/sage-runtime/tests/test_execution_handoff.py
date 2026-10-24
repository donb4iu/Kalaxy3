"""Test real Git boundary binding and fail-closed SAGE execution handoff."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from service.handoff import HandoffError, execute_qualified, prepare_workspace


def git(repo: Path, *args: str) -> str:
    """Run an isolated Git fixture operation.

    Args:
        repo: Fixture repository path.
        *args: Explicit Git argument tokens.
    """
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def fixture(root: Path) -> tuple[Path, Path, dict[str, Any], dict[str, str]]:
    """Make an isolated Git remote with a feature branch and a proposal artifact.

    Args:
        root: Disposable test directory.
    """
    origin = root / "origin"
    origin.mkdir()
    git(origin, "init", "-q")
    git(origin, "config", "user.email", "fixture@example.com")
    git(origin, "config", "user.name", "Fixture")
    (origin / "README.md").write_text("qualified source\n", encoding="utf-8")
    git(origin, "add", ".")
    git(origin, "commit", "-qm", "baseline")
    git(origin, "switch", "-q", "-c", "feature/accepted")
    head = git(origin, "rev-parse", "HEAD")
    proposal_root = root / "proposals"
    proposal_root.mkdir()
    data = b"qualified-test-proposal"
    package_id = hashlib.sha256(data).hexdigest()
    (proposal_root / f"{package_id}.zip").write_bytes(data)
    context = {"objective_id": "SAGE-ACTION-1", "revision": head,
               "objective": "Resume Architecture Helper",
               "action": {"action_id": "SAGE-ACTION-1",
                          "current_status": "accepted",
                          "desired_outcome": "Resume Architecture Helper",
                          "history": [{"to_status": "accepted"}]}}
    submission = {"revision": head, "head": head,
                  "branch": "feature/accepted", "package_id": package_id}
    return origin, proposal_root, context, submission


class ExecutionHandoffTests(unittest.TestCase):
    """Verify objective binding and exactly one delegated execution boundary."""

    def test_qualified_execution_delegates_existing_adapter(self) -> None:
        """Invoke a governed adapter only with an accepted and verified proposal."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin, proposals, context, submission = fixture(root)
            workspace = prepare_workspace(root / "cache", str(origin), submission)
            received: list[str] = []

            def execute(repo: Path, objective: str, package: Path) -> dict[str, Any]:
                """Simulate the existing request executor's verified Git boundary."""
                received.append(objective)
                return {"status": "governed-git-boundary-pending",
                        "proposal_path": str(package)}

            state = {"context": context, "execution_submission": submission,
                     "referee_disposition": "allow"}
            result = execute_qualified(state, repo=workspace, proposals=proposals,
                                       executor=execute)
            self.assertEqual(result["outcome"], "governed-git-boundary-pending")
            self.assertEqual(received, [context["objective"]])
            self.assertTrue(workspace.exists())

    def test_rejects_changed_proposal_and_missing_authority(self) -> None:
        """Neither model output nor an artifact digest can manufacture authority."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin, proposals, context, submission = fixture(root)
            workspace = prepare_workspace(root / "cache", str(origin), submission)
            state = {"context": context, "execution_submission": submission,
                     "referee_disposition": "allow"}
            with self.assertRaisesRegex(HandoffError, "no qualified"):
                execute_qualified({"context": context, "referee_disposition": "allow"},
                                  repo=workspace, proposals=proposals)
            rejected = {**context, "action": {**context["action"],
                                               "current_status": "candidate"}}
            with self.assertRaisesRegex(HandoffError, "effective authority"):
                execute_qualified({**state, "context": rejected},
                                  repo=workspace, proposals=proposals)
            (proposals / f'{submission["package_id"]}.zip').write_bytes(b"modified")
            with self.assertRaisesRegex(HandoffError, "modified"):
                execute_qualified(state, repo=workspace, proposals=proposals)

    def test_rejects_worktree_mutation_or_wrong_branch(self) -> None:
        """Reject independently modified execution workspaces before applying work."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin, _, _, submission = fixture(root)
            workspace = prepare_workspace(root / "cache", str(origin), submission)
            (workspace / "README.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(HandoffError, "not clean"):
                prepare_workspace(root / "cache", str(origin), submission)
            git(workspace, "restore", "README.md")
            with self.assertRaisesRegex(HandoffError, "feature-branch"):
                prepare_workspace(root / "second", str(origin),
                                  {**submission, "branch": "main"})


    def test_existing_cli_contract_and_receipt_paths(self) -> None:
        """Require the repository executor CLI to emit an actionable Git boundary."""
        from service.handoff import invoke_executor

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            script = repo / "scripts/sage/sage-request-execute.py"
            script.parent.mkdir(parents=True)
            script.write_text("# existing SAGE request execution\n", encoding="utf-8")
            artifact = root / "proposal.zip"
            artifact.write_bytes(b"qualified content")
            state = root / "request-state.json"
            proposal = root / "operator-proposal.json"
            state.write_text("{}", encoding="utf-8")
            proposal.write_text("{}", encoding="utf-8")

            def run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
                """Validate original request and immutable artifact CLI arguments."""
                self.assertEqual(argv[-4:], ["--request", "Original objective",
                                              "--proposal", str(artifact)])
                output = ("Kalaxy3 SAGE request execution: PASS\n"
                          f"Operator proposal: {proposal}\n"
                          f"Continuation state: {state}\n")
                return subprocess.CompletedProcess(argv, 0, output, "")

            result = invoke_executor(repo, "Original objective", artifact, runner=run)
            self.assertEqual(result["status"], "governed-git-boundary-pending")
            self.assertEqual(result["state_path"], str(state))


if __name__ == "__main__":
    unittest.main()
