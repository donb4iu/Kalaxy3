"""Reusable validation-plan composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .model import CommandResult, CommandSpec
from .runner import CommandRunner


@dataclass(frozen=True)
class ValidationCommand:
    """One named validation command."""

    label: str
    argv: tuple[str, ...]
    timeout_seconds: float = 600.0


class ValidationPlan:
    """Execute a deterministic ordered validation plan."""

    def __init__(
        self,
        repository_root: Path,
        runner: CommandRunner,
        commands: Iterable[ValidationCommand],
    ) -> None:
        self.repository_root = repository_root.expanduser().resolve()
        self.runner = runner
        self.commands = tuple(commands)
        if not self.commands:
            raise ValueError("Validation plan must not be empty")

    def run(self) -> tuple[CommandResult, ...]:
        results: list[CommandResult] = []
        for command in self.commands:
            results.append(
                self.runner.run(
                    CommandSpec(
                        primitive_id="validation.plan",
                        label=command.label,
                        argv=command.argv,
                        cwd=self.repository_root,
                        timeout_seconds=command.timeout_seconds,
                    )
                )
            )
        return tuple(results)
