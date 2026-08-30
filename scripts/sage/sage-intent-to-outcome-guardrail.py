
#!/usr/bin/env python3
"""Guard the SAGE intent-to-outcome composition against parallel orchestration."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "scripts/sage/workflows/intent_to_outcome.py"
CLI = ROOT / "scripts/sage/sage-intent-to-outcome.py"
STANDARD = ROOT / "markdown/standards/kalaxy3-sage-intent-to-outcome-process.md"
MAKEFILE = ROOT / "Makefile"


def main() -> int:
    failures: list[str] = []
    for path in (WRAPPER, CLI, STANDARD, MAKEFILE):
        if not path.is_file():
            failures.append(
                f"missing intent-to-outcome artifact: {path.relative_to(ROOT)}"
            )
    if failures:
        print("Kalaxy3 SAGE intent-to-outcome guardrail: FAIL CLOSED")
        for item in failures:
            print(f"  - {item}")
        return 1

    wrapper = WRAPPER.read_text(encoding="utf-8")
    tree = ast.parse(wrapper, filename=str(WRAPPER))
    for marker in (
        "from workflow import",
        "PRIMITIVES_USED",
        "begin_bootstrap",
        "continue_bootstrap",
        "plan_request",
        "execute_request",
        "continue_request_from_routine_receipt",
        "start_promotion",
        "continue_promotion",
        "validate_runtime_receipt",
        "begin_candidate_iteration",
        "continue_planned_request",
        "objective-path-decision-required",
        "candidate_iteration_entry_mode",
        "reuse_confirmed_intent",
        "reuse_component_plan",
        "checkpoint-non-promotable",
        "superseded-in-progress",
        "invalidated_downstream_state",
        "_semantic_planning_source",
        "validate_reusable_plan_lineage",
        "proposal_package",
        "iterative objective adoption requires --planning-source",
        "reconcile_completed_request_child",
        "reconciled_from_completed_child",
        "completed request child",
        "reconcile_completed_semantic_child",
        "reconciled_from_completed_semantic_child",
        "planning-source-ready",
        "approved_gap_set",
        "build_objective_route",
        "objective_route_snapshot",
        "reconcile_stale_parent_completed_request_child",
        "validate_reusable_plan_lineage",
        "stale-parent completed-child reconciliation requires planning-source-ready parent",
        "sage-objective-route",
        "remaining_obligations",
        "parent_objective_id",
        "canonical_integration_eligibility",
        "bdd_requirement_coverage",
        "guardrail_collaboration_feedback",
        "_current_recovery_composition_sha256",
        "governing_composition_digest",
        "repository_owned_composition_sha256=current_composition",
        "evidence-reconsideration-required",
        "reconsider_intent",
        "retrieve_evidence",
        "validate_retrieval_result",
        "requires_contribution_refresh",
        "additional_acceptance_criteria",
        "implementation_generation_lineage",
        "_promotion_source_branch",
    ):
        if marker not in wrapper:
            failures.append(f"front door missing existing-component marker: {marker}")

    if 'semantic["planning_source"]' in wrapper:
        failures.append("front door directly assumes one semantic-bootstrap result key")
    if 'result.get("planning_source") or result.get("source")' not in wrapper:
        failures.append("front door lacks semantic-bootstrap planning-source compatibility resolution")

    cli = CLI.read_text(encoding="utf-8")
    for marker in (
        "stale consumed recovery decisions do not block changed recovery composition",
        "current consumed recovery decisions still block duplicate governance re-entry",
    ):
        if marker not in cli:
            failures.append(f"intent recovery-composition regression missing: {marker}")
    if '"--planning-source"' not in cli:
        failures.append("adopt-iteration CLI does not accept historical planning-source lineage")
    if 'sub.add_parser("continue-planned")' not in cli or "continue_planned_request" not in cli:
        failures.append("intent-to-outcome CLI lacks exact-proposal objective-path continuation")
    if 'sub.add_parser("route")' not in cli or "objective_route_snapshot" not in cli:
        failures.append("intent-to-outcome CLI lacks read-only objective route inspection")
    if 'sub.add_parser("reconsider")' not in cli or "reconsider_intent" not in cli:
        failures.append("intent-to-outcome CLI lacks evidence-reconsideration continuation")
    if '"--completed-child-state"' not in cli or '"--planning-source"' not in cli:
        failures.append("continue-request lacks explicit stale-parent completed-child reconciliation inputs")
    if "intent state is not awaiting request continuation" not in wrapper:
        failures.append("ordinary continue-request status gate was weakened")
    if '"planning_source": inherited_source' not in wrapper or '"planning_proposal": inherited_proposal' not in wrapper:
        failures.append("adopt-iteration does not persist validated planning lineage")
    if "candidate iteration requires a durable prior candidate checkpoint" in wrapper:
        failures.append("front door still requires checkpoint before same-class accumulation")
    if 'source_branch="feature/sage-e2e-zero-trust-viability"' in wrapper:
        failures.append("front door promotion still hard-codes one historical source branch")

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for function_name in ("confirm_intent", "begin_candidate_iteration"):
        node = functions.get(function_name)
        if node is None:
            failures.append(f"missing front-door function: {function_name}")
            continue
        calls = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        if "execute_request" in calls:
            failures.append(
                f"{function_name} executes request mutation before an exact-proposal Architect boundary"
            )
    continuation_node = functions.get("continue_planned_request")
    continuation_calls = set() if continuation_node is None else {
        child.func.id
        for child in ast.walk(continuation_node)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    if "execute_request" not in continuation_calls:
        failures.append("planned-request continuation does not reuse request execution")

    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    if {"subprocess", "shlex"} & imports:
        failures.append("front door imports forbidden execution modules")

    for forbidden in (
        "GitRepository(",
        'argv=("git"',
        'argv=("gh"',
        'argv=("kubectl"',
        'argv=("helm"',
        'argv=("ansible-playbook"',
    ):
        if forbidden in wrapper:
            failures.append(f"front door contains direct mutation machinery: {forbidden}")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    for marker in (
        "sage-intent-to-outcome:",
        "sage-intent-to-outcome-reconsider:",
        "sage-intent-to-outcome-confirm:",
        "sage-intent-to-outcome-adopt-request:",
        "sage-intent-to-outcome-adopt-iteration:",
        "sage-intent-to-outcome-iterate:",
        "sage-intent-to-outcome-continue-planned:",
        "sage-intent-to-outcome-continue-routine:",
        "sage-intent-to-outcome-record-runtime:",
        "sage-intent-to-outcome-promote:",
        "sage-intent-to-outcome-continue-promotion:",
        "sage-intent-to-outcome-self-test",
        "sage-intent-to-outcome-guardrail",
    ):
        if marker not in makefile:
            failures.append(f"Makefile missing intent-to-outcome marker: {marker}")

    standard = STANDARD.read_text(encoding="utf-8")
    for marker in (
        "one-time bootstrap seam",
        "existing SAGE child workflows",
        "does not create a parallel orchestration system",
        "runtime evidence",
        "checkpoint promotion",
        "candidate iteration",
        "Candidate union and serial validation",
        "Authoritative shared-responsibility role contract",
        "Intent-first innovation boundary",
        "Current SAGE capabilities constrain the governed transition path",
        "non-promotable",
        "implementation-local",
        "earliest affected boundary",
        "preserve the prior confirmed planning source",
        "different subset of already-authorized paths",
        "already self-closed",
        "must not replay",
        "completed semantic child",
        "persist the planning source before planning",
        "planning failure",
        "approved domain-capability gap set",
        "Objective-first route",
        "value-preserving integration",
        "BDD-style assurance",
        "active technical debt",
        "parent delivery re-entry",
        "read-only route",
        "completed-child reconciliation",
        "refreshed planning lineage",
        "current recovery composition",
        "historical consumed recovery decision",
        "Evidence reconsideration before semantic commitment",
        "consideration obligation, not a selection preference",
        "Implementation-generation lineage",
        "historically justified",
        "repository-lineage milestone",
        "objective-path decision",
        "exact planning proposal",
    ):
        if marker not in standard:
            failures.append(f"intent-to-outcome standard missing: {marker}")

    if failures:
        print("Kalaxy3 SAGE intent-to-outcome guardrail: FAIL CLOSED")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("PASS existing semantic, planning, execution, Git, and promotion compositions are reused")
    print("PASS front door contains no direct Git, GitHub, deployment, or credential mutation path")
    print("PASS one-time bootstrap adoption path is explicit")
    print("PASS adopted iterative objectives preserve and validate planning source/proposal lineage")
    print("PASS already-completed self-closing request children reconcile without replaying Git")
    print("PASS already-completed semantic children reconcile without replay and parent planning lineage persists before planning")
    print("PASS candidate iteration preserves non-promotable checkpoints and earliest-boundary re-entry")
    print("PASS same-class corrections accumulate before promotion and intent-first role separation is explicit")
    print("PASS objective-first route is a read-only extension of the existing front door, not a parallel orchestrator")
    print("PASS stale-parent completed-child reconciliation preserves exact child, receipt, and refreshed planning lineage without replay")
    print("PASS route exposes parent re-entry, limitations, BDD assurance status, integration separation, and collaboration feedback without manufacturing evidence")
    print("PASS exact planning proposal is persisted before Architect objective-path approval and request mutation")
    print("PASS evidence reconsideration is an in-loop boundary and material augmentation requires a refreshed contribution")
    print("PASS implementation generations preserve historical justification and promotion source is lineage-derived")
    print("Kalaxy3 SAGE intent-to-outcome guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
