#!/usr/bin/env python3
"""Thin two-boundary composition for the Kalaxy3 SAGE operating contract."""

from __future__ import annotations

from typing import Callable, Mapping

from workflow import PrimitiveCatalog, Step, Workflow

PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "git.inspect",
    "sage.discovery",
    "authority.reconcile",
    "component.select",
    "capability.gap",
    "file.atomic-preserve-mode",
    "validation.plan",
    "git.safety-guardrail",
    "failure.diagnose",
    "operator.git-proposal",
    "metrics.outcome",
    "evidence.closeout",
    "workflow.composition",
)

PRE_MUTATION_SEQUENCE = (
    ("preserve-literal-request", "sage.discovery"),
    ("collect-current-git-authority", "git.inspect"),
    ("reconcile-authority", "authority.reconcile"),
    ("select-repository-components", "component.select"),
    ("record-capability-gaps", "capability.gap"),
    ("implement-declared-repository-scope", "file.atomic-preserve-mode"),
    ("validate-real-runtime-path", "validation.plan"),
    ("validate-helper-safety", "git.safety-guardrail"),
    ("diagnose-unexpected-failures", "failure.diagnose"),
    ("propose-one-operator-boundary", "operator.git-proposal"),
)

POST_OPERATOR_SEQUENCE = (
    ("verify-pasted-operator-result", "git.inspect"),
    ("record-outcomes-and-trends", "metrics.outcome"),
    ("publish-sage-evidence", "evidence.closeout"),
)


def _steps(
    sequence: tuple[tuple[str, str], ...],
    actions: Mapping[str, Callable[[], object]],
) -> tuple[Step, ...]:
    missing = [step_id for step_id, _ in sequence if step_id not in actions]
    extra = sorted(set(actions) - {step_id for step_id, _ in sequence})
    if missing or extra:
        raise ValueError(
            f"Operating-contract actions mismatch: missing={missing}, extra={extra}"
        )
    return tuple(
        Step(step_id, primitive_id, actions[step_id])
        for step_id, primitive_id in sequence
    )


def build_pre_mutation_workflow(
    *,
    workflow_id: str,
    logger: object,
    catalog: PrimitiveCatalog,
    actions: Mapping[str, Callable[[], object]],
) -> Workflow:
    """Build the repository-content phase ending at one operator proposal."""

    return Workflow(
        workflow_id=workflow_id,
        logger=logger,
        catalog=catalog,
        steps=_steps(PRE_MUTATION_SEQUENCE, actions),
    )


def build_post_operator_workflow(
    *,
    workflow_id: str,
    logger: object,
    catalog: PrimitiveCatalog,
    actions: Mapping[str, Callable[[], object]],
) -> Workflow:
    """Build verification and evidence work after pasted operator output."""

    return Workflow(
        workflow_id=workflow_id,
        logger=logger,
        catalog=catalog,
        steps=_steps(POST_OPERATOR_SEQUENCE, actions),
    )
