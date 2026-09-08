#!/usr/bin/env python3
"""Prove published SAGE lifecycle routes preserve authority prerequisites."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _function_calls(path: Path, function: str) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function:
            return {
                child.func.id
                for child in ast.walk(node)
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
            }
    raise RuntimeError(f"missing lifecycle function: {function}")


def main() -> int:
    failures: list[str] = []
    intent = ROOT / "scripts/sage/workflows/intent_to_outcome.py"
    semantic = (ROOT / "scripts/sage/workflows/semantic_bootstrap.py").read_text(encoding="utf-8")
    planner_cli = (ROOT / "scripts/sage/sage-request-plan.py").read_text(encoding="utf-8")
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    recovery = (ROOT / "scripts/sage/workflow/recovery.py").read_text(encoding="utf-8")
    planning_standard = (ROOT / "markdown/standards/kalaxy3-sage-request-planning-process.md").read_text(encoding="utf-8")

    adopt_calls = _function_calls(intent, "adopt_confirmed_planning_source")
    if "plan_request" not in adopt_calls or "_pause_for_objective_path_decision" not in adopt_calls:
        failures.append("confirmed-source adoption does not plan then pause at objective-path authority")
    if "reuse_confirmed_intent" not in adopt_calls:
        failures.append("confirmed-source adoption cannot rebind stale repository authority without semantic replay")
    if "execute_request" in adopt_calls:
        failures.append("confirmed-source adoption bypasses objective-path authority")

    confirm_calls = _function_calls(intent, "confirm_intent")
    if "plan_request" not in confirm_calls or "_pause_for_objective_path_decision" not in confirm_calls:
        failures.append("normal semantic confirmation does not plan then pause at objective-path authority")
    if "execute_request" in confirm_calls:
        failures.append("normal semantic confirmation executes before objective-path authority")

    continue_calls = _function_calls(intent, "continue_planned_request")
    if "execute_request" not in continue_calls:
        failures.append("objective-path continuation does not own request execution")

    if "sage-intent-to-outcome-adopt-source" not in semantic:
        failures.append("semantic bootstrap does not return to lifecycle owner")
    if '"sage-request-plan"' in semantic[semantic.find("next_command ="):semantic.find("return {", semantic.find("next_command ="))]:
        failures.append("semantic bootstrap still publishes direct request-plan continuation")

    if "Next: execute the proposal through make sage-request-execute." in planner_cli:
        failures.append("request planner still advertises direct execution continuation")
    if "External continuation is owned by sage-intent-to-outcome" not in planner_cli:
        failures.append("request planner does not state lifecycle ownership")

    if "sage-intent-to-outcome-adopt-source:" not in makefile:
        failures.append("Makefile lacks confirmed-source lifecycle adoption target")
    if "Component/debug interfaces: sage-request-plan, sage-request-execute" not in makefile:
        failures.append("Makefile does not distinguish component APIs from lifecycle entrypoints")

    if 'if non_converging:\n        return "successor-action", "architect-decision"' in recovery:
        failures.append("recovery still converts non-convergence alone into successor authority")
    if "accepted_control_failure" not in recovery or "successor-action" not in recovery:
        failures.append("recovery lost evidence-backed accepted-control successor contract")

    if "component compatibility" not in planning_standard.casefold() or "objective-path decision" not in planning_standard.casefold():
        failures.append("request-planning standard does not document lifecycle/authority split")

    if failures:
        print("Kalaxy3 SAGE lifecycle contract self-test: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS semantic bootstrap returns confirmed source to lifecycle owner")
    print("PASS normal and adopted planning routes pause at objective-path authority")
    print("PASS confirmed semantic authority can rebind to current synchronized repository state without semantic replay")
    print("PASS request execution is reachable only from the authority-consuming continuation")
    print("PASS component CLIs do not advertise an authority-bypassing external route")
    print("PASS non-convergence alone cannot manufacture accepted-control successor authority")
    print("Kalaxy3 SAGE lifecycle contract self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
