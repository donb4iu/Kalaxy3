"""Thin workflow composition over registered reusable primitives."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable

from .catalog import PrimitiveCatalog
from .logging import JsonlEventLogger


@dataclass(frozen=True)
class Step:
    """One named composition step."""

    step_id: str
    primitive_id: str
    action: Callable[[], object]


class Workflow:
    """Execute ordered registered steps with shared lifecycle events."""

    def __init__(
        self,
        *,
        workflow_id: str,
        logger: JsonlEventLogger,
        catalog: PrimitiveCatalog,
        steps: Iterable[Step],
    ) -> None:
        self.workflow_id = workflow_id
        self.logger = logger
        self.catalog = catalog
        self.steps = tuple(steps)
        if not self.steps:
            raise ValueError("Workflow must contain at least one step")
        self.catalog.require(
            (
                "workflow.composition",
                *(step.primitive_id for step in self.steps),
            )
        )

    def run(self) -> tuple[object, ...]:
        results: list[object] = []
        self.logger.emit(
            event="workflow-start",
            status="running",
            primitive_id="workflow.composition",
        )
        started = time.monotonic()
        try:
            for step in self.steps:
                self.logger.emit(
                    event="step-start",
                    status="running",
                    primitive_id=step.primitive_id,
                    step_id=step.step_id,
                )
                step_started = time.monotonic()
                try:
                    result = step.action()
                except Exception:
                    self.logger.emit(
                        event="step-finish",
                        status="fail",
                        primitive_id=step.primitive_id,
                        step_id=step.step_id,
                        fields={
                            "duration_ms": int(
                                (time.monotonic() - step_started)
                                * 1000
                            )
                        },
                    )
                    raise
                results.append(result)
                self.logger.emit(
                    event="step-finish",
                    status="pass",
                    primitive_id=step.primitive_id,
                    step_id=step.step_id,
                    fields={
                        "duration_ms": int(
                            (time.monotonic() - step_started)
                            * 1000
                        )
                    },
                )
        except Exception:
            self.logger.emit(
                event="workflow-finish",
                status="fail",
                primitive_id="workflow.composition",
                fields={
                    "duration_ms": int(
                        (time.monotonic() - started) * 1000
                    )
                },
            )
            raise

        self.logger.emit(
            event="workflow-finish",
            status="pass",
            primitive_id="workflow.composition",
            fields={
                "duration_ms": int(
                    (time.monotonic() - started) * 1000
                )
            },
        )
        return tuple(results)
