#!/usr/bin/env python3
"""Thin reusable composition for evidence navigation and template work."""

from __future__ import annotations

from typing import Callable, Mapping

from workflow import PrimitiveCatalog, Step, Workflow

PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "git.inspect",
    "sage.discovery",
    "file.atomic-preserve-mode",
    "validation.plan",
    "failure.diagnose",
    "operator.git-proposal",
    "evidence.closeout",
    "workflow.composition",
)

SEQUENCE = (
    ("discover-authorities-and-lessons", "sage.discovery"),
    ("inspect-repository-state", "git.inspect"),
    ("apply-declared-content-transaction", "file.atomic-preserve-mode"),
    ("validate-rendered-and-governance-paths", "validation.plan"),
    ("diagnose-unexpected-failure", "failure.diagnose"),
    ("propose-operator-git-boundary", "operator.git-proposal"),
    ("write-closeout-evidence", "evidence.closeout"),
)


def build_workflow(
    *,
    workflow_id: str,
    logger: object,
    catalog: PrimitiveCatalog,
    actions: Mapping[str, Callable[[], object]],
) -> Workflow:
    """Build the registered evidence-navigation workflow composition."""
    expected = {step_id for step_id, _ in SEQUENCE}
    missing = sorted(expected - set(actions))
    extra = sorted(set(actions) - expected)
    if missing or extra:
        raise ValueError(
            f"Evidence-navigation actions mismatch: missing={missing}, extra={extra}"
        )
    steps = tuple(
        Step(step_id, primitive_id, actions[step_id])
        for step_id, primitive_id in SEQUENCE
    )
    return Workflow(
        workflow_id=workflow_id,
        logger=logger,
        catalog=catalog,
        steps=steps,
    )
