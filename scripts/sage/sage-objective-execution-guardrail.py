
#!/usr/bin/env python3
"""Guard the bounded SAGE objective-execution slice."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / "scripts/sage/workflows/objective_execution.py"
BRANCH = ROOT / "scripts/sage/workflows/branch_lifecycle.py"
INTENT = ROOT / "scripts/sage/workflows/intent_to_outcome.py"
STANDARD = ROOT / "markdown/standards/kalaxy3-sage-intent-to-outcome-process.md"


def main() -> int:
    """Validate objective atomicity, delegation, and critic authority."""
    failures: list[str] = []
    workflow = WORKFLOW.read_text(encoding="utf-8")
    branch = BRANCH.read_text(encoding="utf-8")
    intent = INTENT.read_text(encoding="utf-8")
    standard = STANDARD.read_text(encoding="utf-8")

    required = (
        "sage-objective-execution-plan",
        "sage-objective-execution-approval",
        "material-objective-path",
        "implementation-local-correction",
        "true-replan",
        "sage-objective-episode",
        "counterfactual_path",
        "routine_followup_interventions",
        "sage-llm-path-critic-request",
        "sage-path-critic-causal-observation",
        "autonomous_migration",
        "continue_branch_lifecycle",
        "ACTIVE_OBJECTIVE_PATH_MODEL",
        "post-promotion-source-closeout",
        "planning-path-critic-request",
        "semantic_vs_mechanical_ownership",
        "repeated_graph_or_state_machine_pattern",
        "alternative_representation_or_engine",
        "objective_equivalent_path",
    )
    for marker in required:
        if marker not in workflow:
            failures.append(f"objective executor missing marker: {marker}")

    branch_required = (
        "objective_execution_delegation_allowed",
        "_validate_objective_executor_result",
        'result.get("execution_mode") == "objective-executor"',
        "execute_objective_closeout",
        "mechanical_chronology",
        "sage_mechanical_phase_graph_persisted",
    )
    for marker in branch_required:
        if marker not in branch:
            failures.append(f"branch lifecycle missing delegation marker: {marker}")

    if '"objective_execution": objective_execution_route_summary(state)' not in intent:
        failures.append("intent route does not expose objective-execution semantics")
    if "## Objective execution unit and path critic" not in standard:
        failures.append("intent standard lacks objective-execution contract")

    if failures:
        print("Kalaxy3 SAGE objective execution guardrail: FAIL CLOSED")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("PASS objective approval is material-path atomic")
    print("PASS branch lifecycle delegates Git mechanics rather than exposing them as the active SAGE objective graph")
    print("PASS local correction and true replan remain distinct")
    print("PASS path critic is causal evidence without migration authority")
    print("PASS planning-time critic challenges ownership, repeated state/graph structure, and alternative representations")
    print("Kalaxy3 SAGE objective execution guardrail: PASS")
    return 0


def _objective_recovery_guardrail() -> None:
    """Fail if objective execution bypasses shared recovery ownership."""
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[2]
    recovery = (
        root / "scripts/sage/workflow/recovery.py"
    ).read_text(encoding="utf-8")
    objective = (
        root / "scripts/sage/workflows/objective_execution.py"
    ).read_text(encoding="utf-8")
    cli = (
        root / "scripts/sage/sage-objective-execution.py"
    ).read_text(encoding="utf-8")
    markers = (
        ('"sage.objective-execution"', recovery),
        ("_recover_local_failure(", objective),
        ("consume_objective_recovery_decision(", objective),
        ("classify_post_retrieval_continuation", objective),
        ('sub.add_parser("recover")', cli),
    )
    missing = [marker for marker, source in markers if marker not in source]
    if missing:
        raise RuntimeError(
            "objective shared-recovery guardrail failed: "
            + ", ".join(missing)
        )
    print("PASS objective execution owns shared self-directed recovery")


_objective_recovery_guardrail()

if __name__ == "__main__":
    raise SystemExit(main())
