"""Adapter for repository-owned improvement-action allocation and lifecycle."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

from .git import GitRepository
from .model import CommandSpec, WorkflowError
from .runner import CommandRunner


class ImprovementActionClient:
    """Use canonical action tools rather than reimplementing lifecycle rules."""

    def __init__(
        self,
        repository: GitRepository,
        runner: CommandRunner,
        *,
        registry: str = "sage-improvement-actions.json",
        allocator: str = "scripts/sage/sage-action-id.py",
        tool: str = "scripts/sage/sage-improvement-actions.py",
    ) -> None:
        self.repository = repository
        self.runner = runner
        self.registry = registry
        self.allocator = allocator
        self.tool = tool

    def _registry_payload(self) -> Mapping[str, Any]:
        payload = json.loads(
            (self.repository.root / self.registry).read_text(
                encoding="utf-8"
            )
        )
        if not isinstance(payload, dict):
            raise WorkflowError(
                "Improvement-action registry must be an object"
            )
        return payload

    def _record(self, action_id: str) -> Mapping[str, Any]:
        matches = [
            item
            for item in self._registry_payload().get("actions", [])
            if isinstance(item, dict)
            and item.get("action_id") == action_id
        ]
        if len(matches) != 1:
            raise WorkflowError(
                f"Expected one action {action_id}, found {len(matches)}"
            )
        return matches[0]

    def allocate_id(self, *, date_token: str | None = None) -> str:
        """Allocate through the canonical read-only action-ID CLI."""

        self.repository.require_clean()
        command = [
            "python3",
            self.allocator,
            "--registry",
            self.registry,
            "--format",
            "plain",
        ]
        if date_token is not None:
            command.extend(["--date", date_token])
        result = self.runner.run(
            CommandSpec(
                primitive_id="sage.action-lifecycle",
                label="Allocate canonical improvement-action ID",
                argv=tuple(command),
                cwd=self.repository.root,
            )
        )
        action_id = result.stdout.strip().splitlines()[-1]
        if not action_id.startswith("SAGE-ACTION-"):
            raise WorkflowError(
                f"Canonical allocator returned invalid ID: {action_id}"
            )
        existing = {
            str(item.get("action_id", ""))
            for item in self._registry_payload().get("actions", [])
            if isinstance(item, dict)
        }
        if action_id in existing:
            raise WorkflowError(
                f"Canonical allocator returned existing ID: {action_id}"
            )
        return action_id

    def register(
        self,
        *,
        draft_path: Path,
        actor: str,
        reason: str,
        evidence_references: Iterable[str],
        apply: bool,
    ) -> Mapping[str, Any]:
        """Dry-run, then optionally apply, canonical action registration."""

        self.repository.require_clean()
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        action_id = draft.get("action_id")
        if not isinstance(action_id, str):
            raise WorkflowError("Action draft action_id is missing")

        recorded_at = (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        )
        command = [
            "python3",
            self.tool,
            "--register-file",
            str(draft_path),
            "--actor",
            actor,
            "--reason",
            reason,
        ]
        for reference in evidence_references:
            command.extend(["--evidence-reference", reference])
        command.extend(["--recorded-at", recorded_at])

        self.runner.run(
            CommandSpec(
                primitive_id="sage.action-lifecycle",
                label=f"Plan action registration {action_id}",
                argv=tuple(command),
                cwd=self.repository.root,
            )
        )
        self.repository.require_clean()
        if not apply:
            return {"action_id": action_id, "current_status": "planned"}

        self.runner.run(
            CommandSpec(
                primitive_id="sage.action-lifecycle",
                label=f"Apply action registration {action_id}",
                argv=tuple((*command, "--apply")),
                cwd=self.repository.root,
            )
        )
        self.repository.require_exact_paths({self.registry})
        record = self._record(action_id)
        if record.get("current_status") != "identified":
            raise WorkflowError(
                f"{action_id}: expected identified after registration"
            )
        return record

    def transition(
        self,
        *,
        action_id: str,
        to_status: str,
        actor: str,
        reason: str,
        evidence_references: Iterable[str],
        apply: bool,
    ) -> Mapping[str, Any]:
        """Dry-run, then optionally apply, one canonical transition."""

        self.repository.require_clean()
        recorded_at = (
            datetime.now()
            .astimezone()
            .isoformat(timespec="seconds")
        )
        command = [
            "python3",
            self.tool,
            "--action-id",
            action_id,
            "--to-status",
            to_status,
            "--actor",
            actor,
            "--reason",
            reason,
        ]
        for reference in evidence_references:
            command.extend(["--evidence-reference", reference])
        command.extend(["--recorded-at", recorded_at])

        self.runner.run(
            CommandSpec(
                primitive_id="sage.action-lifecycle",
                label=f"Plan action transition to {to_status}",
                argv=tuple(command),
                cwd=self.repository.root,
            )
        )
        self.repository.require_clean()
        if not apply:
            return self._record(action_id)

        self.runner.run(
            CommandSpec(
                primitive_id="sage.action-lifecycle",
                label=f"Apply action transition to {to_status}",
                argv=tuple((*command, "--apply")),
                cwd=self.repository.root,
            )
        )
        self.repository.require_exact_paths({self.registry})
        record = self._record(action_id)
        if record.get("current_status") != to_status:
            raise WorkflowError(
                f"{action_id}: expected status {to_status}"
            )
        return record
