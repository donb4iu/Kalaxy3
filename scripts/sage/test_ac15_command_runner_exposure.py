"""Evidence tests for pre-existing SAGE command-runner credential exposure."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from workflow import CommandRunner, CommandSpec, JsonlEventLogger


class CommandRunnerExposureTests(unittest.TestCase):
    """Prove current environment behavior without using actual credentials."""

    def test_parent_environment_is_inherited(self) -> None:
        """Show that an arbitrary ambient secret reaches a child process."""
        with tempfile.TemporaryDirectory() as location:
            path = Path(location)
            runner = CommandRunner(
                JsonlEventLogger(path / "events.jsonl", "test"),
                allowed_roots=(path,),
            )
            spec = CommandSpec(
                primitive_id="command.run", label="fixture",
                argv=("fixture-no-execution",), cwd=path,
            )
            fake_result: Any = SimpleNamespace(
                stdout="", stderr="", returncode=0,
            )
            with patch.dict("os.environ", {"SAGE_TEST_SYNTHETIC_SECRET": "not-real"}):
                with patch(
                    "workflow.runner.subprocess.run", return_value=fake_result
                ) as run:
                    runner.run(spec)
            child_environment = run.call_args.kwargs["env"]
            self.assertEqual(
                child_environment["SAGE_TEST_SYNTHETIC_SECRET"], "not-real"
            )

    def test_command_environment_may_override_base(self) -> None:
        """Demonstrate that command-specific values override runner settings."""
        with tempfile.TemporaryDirectory() as location:
            path = Path(location)
            runner = CommandRunner(
                JsonlEventLogger(path / "events.jsonl", "test"),
                allowed_roots=(path,),
                base_environment={"SAGE_TEST_ONLY": "runner"},
            )
            spec = CommandSpec(
                primitive_id="command.run", label="fixture",
                argv=("fixture-no-execution",), cwd=path,
                environment={"SAGE_TEST_ONLY": "command"},
            )
            fake_result: Any = SimpleNamespace(
                stdout="", stderr="", returncode=0,
            )
            with patch(
                "workflow.runner.subprocess.run", return_value=fake_result
            ) as run:
                runner.run(spec)
            self.assertEqual(run.call_args.kwargs["env"]["SAGE_TEST_ONLY"], "command")


if __name__ == "__main__":
    unittest.main()
