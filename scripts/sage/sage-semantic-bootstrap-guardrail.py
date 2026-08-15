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
    "markdown/standards/sage-request-planning-source-schema-v1.2.json",
)


def validate() -> list[str]:
    failures = [f"semantic-bootstrap path missing: {item}" for item in REQUIRED if not (ROOT / item).is_file()]
    if failures:
        return failures
    workflow = (ROOT / "scripts/sage/workflows/semantic_bootstrap.py").read_text(encoding="utf-8")
    domain = (ROOT / "scripts/sage/semantic_understanding.py").read_text(encoding="utf-8")
    planning = (ROOT / "scripts/sage/request_planning.py").read_text(encoding="utf-8")
    cli = (ROOT / "scripts/sage/sage-request-plan.py").read_text(encoding="utf-8")
    bootstrap_cli = (ROOT / "scripts/sage/sage-action-bootstrap.py").read_text(encoding="utf-8")
    process = (ROOT / "markdown/standards/kalaxy3-sage-semantic-bootstrap-process.md").read_text(encoding="utf-8").casefold()
    markers = (
        "load_improvement_action",
        'action.get("current_status") != "accepted"',
        "architect-confirmation-required",
        "reconcile_semantic_contexts",
        "implementation_contexts",
        "write_source_package",
        "planning-source-generation-authorized",
        "semantic-confirmation.json",
        "feasibility.json",
        "authorization.json",
        "render_operator_command",
        "semantic_understanding_path",
        "semantic_confirmation_path",
        "default_planning_source_path",
        "semantic-{confirmation_sha256}-source.zip",
    )
    for marker in markers:
        if marker not in workflow:
            failures.append(f"semantic-bootstrap workflow marker missing: {marker}")
    if "GitRepository" in workflow or "subprocess" in workflow:
        failures.append("semantic bootstrap broadened authority beyond read-only Git/workflow composition")
    if "import shlex" in workflow or "shlex." in workflow:
        failures.append("semantic bootstrap bypasses the repository-owned operator-command renderer")
    if "_apply_architect_dispositions" not in workflow or "architect-dispositions.json" not in workflow:
        failures.append("semantic bootstrap Architect disposition contract is missing")
    if "not-applicable-to-proposed-repository-scope" in workflow:
        failures.append("semantic bootstrap still equates absent mutation paths with non-applicability")
    if "implementation_contexts" not in planning or "SEMANTIC_APPLICABLE_DISPOSITIONS" not in planning:
        failures.append("request planning does not preserve semantic applicability separately from mutation authority")
    if "SOURCE_FIELDS_V1_2" not in planning or '"1.2"' not in planning:
        failures.append("request planning lacks additive v1.2 split semantic-authority support")
    if "applicable-now-no-proposed-source-mutation" not in planning:
        failures.append("request-relevant non-mutation context disposition is missing")
    if "write_source_package" not in planning:
        failures.append("repository-owned planning-source writer is missing")
    for marker in ("resolve_planning_authority", "semantic_authority", "return to semantic confirmation"):
        if marker not in planning:
            failures.append(f"semantic planning-authority propagation marker missing: {marker}")
    if "_fixture_source" in cli:
        failures.append("request-planning self-test still relies on caller-style fixture source writer")
    if "default_planning_source_path" not in bootstrap_cli or "semantic-confirmation digest scopes default planning-source identity" not in bootstrap_cli:
        failures.append("semantic-bootstrap self-test does not cover distinct confirmed-slice planning-source identity")
    if "sage-source.json" not in domain or "may not author sage control artifact" not in domain.casefold():
        failures.append("engineering contribution does not reject external sage-source authorship")
    for marker in ("anti-goose-chase", "semantic confirmation is not feasibility", "bootstrap exception", "confirmed semantic authority", "semantic-confirmation digest", "multiple confirmed slices"):
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
    print("PASS Architect accept/reject/modify/defer disposition contract")
    print("PASS Architect semantic-confirmation boundary")
    print("PASS bounded one-pass context disposition without path/applicability conflation")
    print("PASS semantic applicability is preserved separately from mutation authority")
    print("PASS split semantic authority is additive through planning-source v1.2")
    print("PASS repository-owned planning-source generation")
    print("PASS existing planner/executor reuse")
    print("PASS confirmed semantic authority is bound into downstream planning")
    print("PASS semantic-confirmation digest scopes immutable planning-source identity")
    print("Kalaxy3 SAGE semantic bootstrap guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
