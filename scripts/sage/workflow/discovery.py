"""Repository-owned SAGE discovery and failure-retrieval primitives."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .model import CommandSpec, WorkflowError
from .runner import CommandRunner


@dataclass(frozen=True)
class PreflightResult:
    """Parsed SAGE preflight result."""

    request: str
    contexts: tuple[str, ...]
    authorities: tuple[str, ...]
    stdout: str


class SageDiscovery:
    """Execute and parse repository-owned SAGE discovery entry points."""

    def __init__(
        self,
        repository_root: Path,
        runner: CommandRunner,
    ) -> None:
        self.repository_root = repository_root.expanduser().resolve()
        self.runner = runner

    @staticmethod
    def parse(request: str, stdout: str) -> PreflightResult:
        contexts: list[str] = []
        authorities: list[str] = []
        mode: str | None = None
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped == "Inferred SAGE contexts:":
                mode = "contexts"
                continue
            if stripped == "Authoritative files:":
                mode = "authorities"
                continue
            if line.startswith("  - "):
                value = line[4:].strip()
                if mode == "contexts":
                    contexts.append(value)
                elif mode == "authorities":
                    authorities.append(value)
                continue
            if not stripped:
                mode = None

        unique_contexts = tuple(dict.fromkeys(contexts))
        unique_authorities = tuple(sorted(set(authorities)))
        if not unique_contexts:
            raise WorkflowError(
                "SAGE preflight returned no inferred contexts"
            )
        if not unique_authorities:
            raise WorkflowError(
                "SAGE preflight returned no authoritative files"
            )
        return PreflightResult(
            request=request,
            contexts=unique_contexts,
            authorities=unique_authorities,
            stdout=stdout,
        )

    def literal(self, request: str) -> PreflightResult:
        result = self.runner.run(
            CommandSpec(
                primitive_id="sage.discovery",
                label="Run literal SAGE preflight",
                argv=("make", "sage-preflight"),
                cwd=self.repository_root,
                environment={"SAGE_REQUEST": request},
            )
        )
        parsed = self.parse(request, result.stdout)
        self.read_authorities(parsed.authorities)
        return parsed

    def changed(self) -> PreflightResult:
        result = self.runner.run(
            CommandSpec(
                primitive_id="sage.discovery",
                label="Run changed-path SAGE preflight",
                argv=(
                    "python3",
                    "scripts/sage/sage-change-preflight.py",
                    "--changed",
                ),
                cwd=self.repository_root,
            )
        )
        parsed = self.parse(
            "<changed-path discovery>",
            result.stdout,
        )
        self.read_authorities(parsed.authorities)
        return parsed

    def failure_retrieval(self, failure: str) -> Path:
        result = self.runner.run(
            CommandSpec(
                primitive_id="sage.failure-retrieval",
                label="Retrieve SAGE experience for failure",
                argv=("make", "sage-failure-retrieval"),
                cwd=self.repository_root,
                environment={"SAGE_FAILURE": failure},
            )
        )
        match = re.search(
            r"^Receipt:\s+(.+)$",
            result.stdout,
            re.MULTILINE,
        )
        if match is None:
            raise WorkflowError(
                "Failure retrieval did not return a receipt"
            )
        receipt = Path(match.group(1).strip()).expanduser()
        if not receipt.is_file():
            raise WorkflowError(
                f"Failure retrieval receipt is missing: {receipt}"
            )
        return receipt

    def read_authorities(
        self,
        authorities: tuple[str, ...] | list[str],
    ) -> None:
        for relative in authorities:
            path = self.repository_root / relative
            if not path.exists():
                raise WorkflowError(
                    f"Authority path is missing: {relative}"
                )
            if path.is_file():
                path.read_bytes()
