#!/usr/bin/env python3
"""Fail-closed guardrail for the improvement-action transition composition."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / "scripts/sage/workflows/improvement_action_transition.py"
)
CLI = ROOT / "scripts/sage/sage-improvement-action-transition.py"
AMENDMENT_CLI = ROOT / "scripts/sage/sage-improvement-action-amendment.py"
LIFECYCLE = ROOT / "scripts/sage/workflow/lifecycle.py"
REGISTRY = ROOT / "sage-workflow-primitives.json"
MAKEFILE = ROOT / "Makefile"


def manifest(tree: ast.AST) -> tuple[str, ...]:
    """Read a literal PRIMITIVES_USED tuple."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "PRIMITIVES_USED"
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, (ast.Tuple, ast.List)):
            break
        values = []
        for item in node.value.elts:
            if (
                not isinstance(item, ast.Constant)
                or not isinstance(item.value, str)
            ):
                raise RuntimeError(
                    "PRIMITIVES_USED must be literal strings"
                )
            values.append(item.value)
        return tuple(values)
    raise RuntimeError("PRIMITIVES_USED manifest is missing")


def main() -> int:
    failures: list[str] = []
    workflow_source = WORKFLOW.read_text(encoding="utf-8")
    lifecycle_source = LIFECYCLE.read_text(encoding="utf-8")
    cli_source = CLI.read_text(encoding="utf-8")
    amendment_cli_source = AMENDMENT_CLI.read_text(encoding="utf-8")
    make_source = MAKEFILE.read_text(encoding="utf-8")
    tree = ast.parse(workflow_source, filename=str(WORKFLOW))
    primitives = set(manifest(tree))

    if "git.repository" in primitives:
        failures.append(
            "restricted git.repository entered production transition "
            "composition"
        )
    for primitive in (
        "git.inspect",
        "sage.action-lifecycle",
        "validation.plan",
        "operator.git-proposal",
        "evidence.closeout",
        "workflow.composition",
    ):
        if primitive not in primitives:
            failures.append(
                f"transition composition missing {primitive}"
            )
    if "GitRepository" in workflow_source:
        failures.append(
            "transition workflow imports or names GitRepository"
        )
    if (
        "subprocess" in workflow_source
        or "shlex" in workflow_source
    ):
        failures.append(
            "transition workflow bypasses repository command primitives"
        )
    if "ImprovementActionClient(\n        context.inspector," not in workflow_source:
        failures.append(
            "transition workflow does not supply GitInspector to the "
            "canonical lifecycle client"
        )
    for prohibited in (
        ".commit_and_push(",
        ".create_branch(",
        ".fetch(",
    ):
        if prohibited in lifecycle_source:
            failures.append(
                "sage.action-lifecycle unexpectedly owns Git mutation: "
                + prohibited
            )
    for required_call in (
        "self.repository.require_clean()",
        "self.repository.require_exact_paths",
    ):
        if required_call not in lifecycle_source:
            failures.append(
                "sage.action-lifecycle least-authority call surface "
                f"missing {required_call}"
            )
    for marker in (
        "sage-improvement-action-transition:",
        "sage-improvement-action-transition-self-test:",
        "sage-improvement-action-transition-guardrail:",
        "sage-improvement-action-amendment:",
    ):
        if marker not in make_source:
            failures.append(f"Makefile missing {marker}")
    if (
        "from workflows.improvement_action_transition import"
        not in cli_source
    ):
        failures.append(
            "CLI does not consume tracked transition workflow"
        )
    if "from workflows.improvement_action_transition import" not in amendment_cli_source:
        failures.append(
            "amendment CLI does not consume tracked shared lifecycle workflow"
        )
    if "start_amendment" not in amendment_cli_source:
        failures.append("amendment CLI does not call shared amendment entry point")
    for marker in (
        "build_successor_action_boundary",
        "emit_successor_action_boundary",
        "sage-improvement-action-successor-boundary",
        "architect-decision-required",
    ):
        if marker not in workflow_source:
            failures.append(f"successor lifecycle marker missing: {marker}")
    if "--recovery-decision" not in cli_source:
        failures.append("transition CLI cannot consume recovery successor boundary")
    for marker in (
        "failure_recovery_action(context, error)",
        "classify_post_retrieval_continuation",
        "RECOVERY_DECISION_NAME",
        "recovery_control_action_id",
        "Next governed boundary:",
    ):
        if marker not in workflow_source:
            failures.append(
                "fail-closed lifecycle recovery integration missing: " + marker
            )
    workflows_dir = ROOT / "scripts/sage/workflows"
    parallel = [
        path.name
        for path in workflows_dir.glob("*improvement_action*amend*.py")
        if path.name != "improvement_action_transition.py"
    ]
    if parallel:
        failures.append(
            "parallel improvement-action amendment workflow detected: "
            + ", ".join(sorted(parallel))
        )
    if "make sage-request-continue" not in workflow_source:
        failures.append(
            "transition workflow does not delegate Git continuation"
        )
    if "sage-improvement-actions.json" not in workflow_source:
        failures.append(
            "transition workflow exact registry scope is missing"
        )

    if failures:
        print(
            "Kalaxy3 SAGE improvement-action transition guardrail: FAIL"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS existing lifecycle client reused through GitInspector call surface")
    print("PASS no production git.repository or direct subprocess path")
    print(
        "PASS canonical lifecycle/validation/operator-boundary composition"
    )
    print(
        "PASS exact action-registry mutation and request continuation"
    )
    print("PASS Make and CLI integration")
    print("PASS accepted-control recurrence is owned by action lifecycle")
    print("PASS lifecycle failures emit one recovery next-boundary contract")
    print(
        "Kalaxy3 SAGE improvement-action transition guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
