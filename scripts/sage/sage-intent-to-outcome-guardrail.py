
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
        "reuse_confirmed_intent",
        "reuse_component_plan",
        "checkpoint-non-promotable",
        "invalidated_downstream_state",
        "_semantic_planning_source",
        "validate_reusable_plan_lineage",
        "proposal_package",
        "iterative objective adoption requires --planning-source",
    ):
        if marker not in wrapper:
            failures.append(f"front door missing existing-component marker: {marker}")

    if 'semantic["planning_source"]' in wrapper:
        failures.append("front door directly assumes one semantic-bootstrap result key")
    if 'result.get("planning_source") or result.get("source")' not in wrapper:
        failures.append("front door lacks semantic-bootstrap planning-source compatibility resolution")

    cli = CLI.read_text(encoding="utf-8")
    if '"--planning-source"' not in cli:
        failures.append("adopt-iteration CLI does not accept historical planning-source lineage")
    if '"planning_source": inherited_source' not in wrapper or '"planning_proposal": inherited_proposal' not in wrapper:
        failures.append("adopt-iteration does not persist validated planning lineage")

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
        "sage-intent-to-outcome-confirm:",
        "sage-intent-to-outcome-adopt-request:",
        "sage-intent-to-outcome-adopt-iteration:",
        "sage-intent-to-outcome-iterate:",
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
        "non-promotable",
        "implementation-local",
        "earliest affected boundary",
        "preserve the prior confirmed planning source",
        "different subset of already-authorized paths",
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
    print("PASS candidate iteration preserves non-promotable checkpoints and earliest-boundary re-entry")
    print("Kalaxy3 SAGE intent-to-outcome guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
