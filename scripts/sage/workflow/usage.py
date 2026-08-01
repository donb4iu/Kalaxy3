"""Summarize primitive execution evidence from structured JSONL logs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .model import WorkflowError


class UsageAnalyzer:
    """Aggregate workflow and primitive outcomes by version."""

    @staticmethod
    def summarize(paths: Iterable[Path]) -> dict[str, Any]:
        workflows: set[str] = set()
        successes: Counter[str] = Counter()
        failures: Counter[str] = Counter()
        event_count = 0

        for path in sorted(set(paths)):
            if not path.is_file():
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as error:
                    raise WorkflowError(
                        f"{path}:{line_number}: invalid JSONL"
                    ) from error
                if not isinstance(event, dict):
                    raise WorkflowError(
                        f"{path}:{line_number}: event must be an object"
                    )
                event_count += 1
                workflow_id = event.get("workflow_id")
                if isinstance(workflow_id, str):
                    workflows.add(workflow_id)

                primitive_id = event.get("primitive_id")
                primitive_version = event.get("primitive_version")
                status = event.get("status")
                if not isinstance(primitive_id, str):
                    continue
                version = (
                    primitive_version
                    if isinstance(primitive_version, str)
                    else "unversioned"
                )
                key = f"{primitive_id}@{version}"
                if status == "pass":
                    successes[key] += 1
                elif status in {"fail", "timeout"}:
                    failures[key] += 1

        return {
            "schema_version": "1.0",
            "workflow_count": len(workflows),
            "event_count": event_count,
            "successful_events_by_primitive_version": dict(
                sorted(successes.items())
            ),
            "failed_events_by_primitive_version": dict(
                sorted(failures.items())
            ),
        }
