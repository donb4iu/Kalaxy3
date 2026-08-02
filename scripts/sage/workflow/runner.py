"""Central command execution with timeouts and structured evidence."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Mapping

from .logging import JsonlEventLogger, digest_parts, redact_text
from .model import CommandResult, CommandSpec, WorkflowCommandError


class CommandRunner:
    """Execute argv-only commands through one observable fail-closed path."""

    def __init__(
        self,
        logger: JsonlEventLogger,
        *,
        allowed_roots: Iterable[Path],
        base_environment: Mapping[str, str] | None = None,
    ) -> None:
        self.logger = logger
        self.allowed_roots = tuple(
            path.expanduser().resolve()
            for path in allowed_roots
        )
        if not self.allowed_roots:
            raise ValueError("allowed_roots must not be empty")
        self.base_environment = {
            "PAGER": "cat",
            "GIT_PAGER": "cat",
            "LESS": "FRX",
            **dict(base_environment or {}),
        }

    def _require_allowed_cwd(self, cwd: Path) -> Path:
        resolved = cwd.expanduser().resolve()
        for root in self.allowed_roots:
            try:
                resolved.relative_to(root)
                return resolved
            except ValueError:
                continue
        raise WorkflowCommandError(
            f"Command cwd is outside allowed roots: {resolved}"
        )

    def run(
        self,
        spec: CommandSpec,
        *,
        step_id: str | None = None,
    ) -> CommandResult:
        """Run one command without shell expansion or raw-command logging."""

        cwd = self._require_allowed_cwd(spec.cwd)
        command_digest = digest_parts(spec.argv)
        print(f"+ [{spec.primitive_id}] {spec.label}", flush=True)

        self.logger.emit(
            event="command-start",
            status="running",
            primitive_id=spec.primitive_id,
            step_id=step_id,
            fields={
                "command_label": spec.label,
                "command_digest": command_digest,
                "cwd": str(cwd),
                "timeout_seconds": spec.timeout_seconds,
            },
        )

        environment = dict(os.environ)
        environment.update(self.base_environment)
        environment.update(dict(spec.environment))

        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(spec.argv),
                cwd=cwd,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                timeout=spec.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            duration_ms = int((time.monotonic() - started) * 1000)
            self.logger.emit(
                event="command-finish",
                status="timeout",
                primitive_id=spec.primitive_id,
                step_id=step_id,
                fields={
                    "command_label": spec.label,
                    "command_digest": command_digest,
                    "duration_ms": duration_ms,
                },
            )
            raise WorkflowCommandError(
                f"Command timed out: {spec.label}"
            ) from error

        duration_ms = int((time.monotonic() - started) * 1000)
        stdout = redact_text(
            completed.stdout,
            spec.sensitive_values,
        )
        stderr = redact_text(
            completed.stderr,
            spec.sensitive_values,
        )
        if stdout:
            print(stdout, end="")
        if stderr:
            print(stderr, end="", file=sys.stderr)

        output_sha256 = hashlib.sha256(
            (stdout + "\x00" + stderr).encode("utf-8")
        ).hexdigest()
        status = (
            "pass"
            if completed.returncode in spec.expected_codes
            else "fail"
        )
        self.logger.emit(
            event="command-finish",
            status=status,
            primitive_id=spec.primitive_id,
            step_id=step_id,
            fields={
                "command_label": spec.label,
                "command_digest": command_digest,
                "duration_ms": duration_ms,
                "returncode": completed.returncode,
                "output_sha256": output_sha256,
            },
        )

        if completed.returncode not in spec.expected_codes:
            raise WorkflowCommandError(
                f"Command failed ({completed.returncode}): "
                f"{spec.label}"
            )

        return CommandResult(
            returncode=completed.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            output_sha256=output_sha256,
        )
