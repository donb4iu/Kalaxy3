#!/usr/bin/env python3
"""Guard the first accepted-action semantic-understanding bootstrap composition."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = (
    "scripts/sage/semantic_understanding.py",
    "scripts/sage/workflows/semantic_bootstrap.py",
    "scripts/sage/sage-action-bootstrap.py",
    "markdown/standards/kalaxy3-sage-semantic-bootstrap-process.md",
    "markdown/standards/sage-engineering-contribution-schema-v1.0.json",
    "markdown/standards/sage-semantic-understanding-schema-v1.0.json",
    "markdown/standards/sage-request-planning-source-schema-v1.1.json",
)


def validate() -> list[str]:
    failures = [f"semantic-bootstrap path missing: {item}" for item in REQUIRED if not (ROOT / item).is_file()]
    if failures:
        return failures
    workflow = (ROOT / "scripts/sage/workflows/semantic_bootstrap.py").read_text(encoding="utf-8")
    domain = (ROOT / "scripts/sage/semantic_understanding.py").read_text(encoding="utf-8")
    planning = (ROOT / "scripts/sage/request_planning.py").read_text(encoding="utf-8")
    cli = (ROOT / "scripts/sage/sage-request-plan.py").read_text(encoding="utf-8")
    process = (ROOT / "markdown/standards/kalaxy3-sage-semantic-bootstrap-process.md").read_text(encoding="utf-8").casefold()
    markers = (
        "load_improvement_action",
        'action.get("current_status") != "accepted"',
        "architect-confirmation-required",
        "derive_applicable_contexts",
        "not-applicable-to-proposed-repository-scope",
        "write_source_package",
        "planning-source-generation-authorized",
        "semantic-confirmation.json",
        "feasibility.json",
        "authorization.json",
        "render_operator_command",
        "semantic_understanding_path",
        "semantic_confirmation_path",
    )
    for marker in markers:
        if marker not in workflow:
            failures.append(f"semantic-bootstrap workflow marker missing: {marker}")
    if "GitRepository" in workflow or "subprocess" in workflow:
        failures.append("semantic bootstrap broadened authority beyond read-only Git/workflow composition")
    if "import shlex" in workflow or "shlex." in workflow:
        failures.append("semantic bootstrap bypasses the repository-owned operator-command renderer")
    if "write_source_package" not in planning:
        failures.append("repository-owned planning-source writer is missing")
    for marker in ("resolve_planning_authority", "semantic_authority", "return to semantic confirmation"):
        if marker not in planning:
            failures.append(f"semantic planning-authority propagation marker missing: {marker}")
    if "_fixture_source" in cli:
        failures.append("request-planning self-test still relies on caller-style fixture source writer")
    if "sage-source.json" not in domain or "may not author sage control artifact" not in domain.casefold():
        failures.append("engineering contribution does not reject external sage-source authorship")
    for marker in ("anti-goose-chase", "semantic confirmation is not feasibility", "bootstrap exception", "confirmed semantic authority"):
        if marker not in process:
            failures.append(f"semantic-bootstrap process marker missing: {marker}")
    for path in ("markdown/standards/sage-engineering-contribution-schema-v1.0.json", "markdown/standards/sage-semantic-understanding-schema-v1.0.json"):
        json.loads((ROOT / path).read_text(encoding="utf-8"))
    make = (ROOT / "Makefile").read_text(encoding="utf-8")
    for marker in ("sage-semantic-bootstrap-self-test:", "sage-semantic-bootstrap-guardrail:", "sage-action-bootstrap:", "sage-action-bootstrap-continue:"):
        if marker not in make:
            failures.append(f"Makefile semantic-bootstrap marker missing: {marker}")
    authority = json.loads((ROOT / "sage-change-authority.json").read_text(encoding="utf-8"))
    contexts = {item.get("id"): item for item in authority.get("contexts", []) if isinstance(item, dict)}
    if "semantic-understanding" not in contexts:
        failures.append("semantic-understanding change-authority context is missing")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("Kalaxy3 SAGE semantic bootstrap guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS accepted-action read-only bootstrap authority")
    print("PASS engineering contribution excludes caller-authored SAGE mechanics")
    print("PASS Architect semantic-confirmation boundary")
    print("PASS bounded one-pass context disposition")
    print("PASS repository-owned planning-source generation")
    print("PASS existing planner/executor reuse")
    print("PASS confirmed semantic authority is bound into downstream planning")
    print("Kalaxy3 SAGE semantic bootstrap guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
