"""Typed data contracts shared by SAGE workflow primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence


class WorkflowError(RuntimeError):
    """Base fail-closed workflow exception."""


class WorkflowCommandError(WorkflowError):
    """Raised when a command violates its declared execution contract."""


@dataclass(frozen=True)
class CommandSpec:
    """Declarative command execution contract."""

    primitive_id: str
    label: str
    argv: tuple[str, ...]
    cwd: Path
    timeout_seconds: float = 300.0
    expected_codes: tuple[int, ...] = (0,)
    environment: Mapping[str, str] = field(default_factory=dict)
    sensitive_values: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.primitive_id.strip():
            raise ValueError("primitive_id is required")
        if not self.label.strip():
            raise ValueError("label is required")
        if not self.argv:
            raise ValueError("argv must not be empty")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not self.expected_codes:
            raise ValueError("expected_codes must not be empty")


@dataclass(frozen=True)
class CommandResult:
    """Result returned by the command runner."""

    returncode: int
    stdout: str
    stderr: str
    duration_ms: int
    output_sha256: str
