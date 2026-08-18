#!/usr/bin/env python3
"""Audit SAGE workflow capability completeness against a governed comparison baseline."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "markdown/standards/sage-capability-intelligence-workflow-capability-baseline-v1.0.json"
CAPABILITY_INTELLIGENCE = ROOT / "sage-capability-intelligence.json"
MAKEFILE = ROOT / "Makefile"

ALLOWED = {
    "implemented",
    "partial",
    "required-gap",
    "deferred-gap",
    "intentionally-prohibited",
    "not-applicable",
}
REQUIRED_FAMILIES = {
    "scm-lifecycle",
    "workflow-state",
    "triggers-events",
    "orchestration",
    "artifacts-promotion",
    "environment-authority",
    "execution-portability",
    "evidence-observability-recovery",
}
REQUIRED_FRAMEWORKS = {"github-actions", "jenkins", "argo-workflows", "tekton"}


def main() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if baseline.get("schema_version") != "1.0" or baseline.get("record_type") != "sage-workflow-capability-completeness-baseline":
        raise RuntimeError("workflow capability baseline version/type drifted")
    policy = baseline.get("comparison_policy", {})
    if policy.get("external_frameworks_are_discovery_sources_not_authority") is not True:
        raise RuntimeError("external framework comparison was promoted to authority")
    if policy.get("class_level_remediation_required") is not True or policy.get("silent_unclassified_allowed") is not False:
        raise RuntimeError("class-level remediation / fail-closed classification policy drifted")

    families = baseline.get("families")
    if not isinstance(families, list):
        raise RuntimeError("workflow capability families must be a list")
    family_ids = {item.get("family_id") for item in families if isinstance(item, dict)}
    missing_families = sorted(REQUIRED_FAMILIES - family_ids)
    if missing_families:
        raise RuntimeError(f"workflow capability families missing: {missing_families}")

    seen: set[str] = set()
    required_gaps: list[str] = []
    deferred_gaps: list[str] = []
    for family in families:
        for capability in family.get("capabilities", []):
            capability_id = capability.get("capability_id")
            disposition = capability.get("disposition")
            if not isinstance(capability_id, str) or not capability_id or capability_id in seen:
                raise RuntimeError(f"invalid or duplicate capability id: {capability_id}")
            seen.add(capability_id)
            if disposition not in ALLOWED:
                raise RuntimeError(f"{capability_id}: unsupported disposition {disposition!r}")
            presence = capability.get("framework_presence")
            if not isinstance(presence, dict) or set(presence) != REQUIRED_FRAMEWORKS:
                raise RuntimeError(f"{capability_id}: framework comparison coverage is incomplete")
            implementation = capability.get("implementation")
            if not isinstance(implementation, list):
                raise RuntimeError(f"{capability_id}: implementation must be a list")
            if disposition == "implemented":
                if not implementation:
                    raise RuntimeError(f"{capability_id}: implemented capability lacks repository mapping")
                for relative in implementation:
                    path = ROOT / relative
                    if not path.exists():
                        raise RuntimeError(f"{capability_id}: mapped implementation is missing: {relative}")
            if disposition == "required-gap":
                required_gaps.append(capability_id)
            if disposition == "deferred-gap":
                deferred_gaps.append(capability_id)

    intelligence = CAPABILITY_INTELLIGENCE.read_text(encoding="utf-8")
    required_blockers = (
        "bootstrap requires the capability it is intended to create",
        "required live state exists only through undocumented manual mutation",
    )
    missing_blockers = [item for item in required_blockers if item not in intelligence]
    if missing_blockers:
        raise RuntimeError(f"capability-intelligence bootstrap blocking rules missing: {missing_blockers}")

    makefile = MAKEFILE.read_text(encoding="utf-8")
    for marker in (
        "sage-capability-intelligence-workflow-audit",
        "sage-branch-lifecycle-self-test",
        "sage-branch-lifecycle-guardrail",
    ):
        if marker not in makefile:
            raise RuntimeError(f"root Make integration missing: {marker}")

    print(f"PASS {len(seen)} workflow capabilities classified across {len(family_ids)} families")
    print(f"PASS required gaps are explicit: {', '.join(sorted(required_gaps))}")
    print(f"PASS deferred gaps are explicit: {', '.join(sorted(deferred_gaps))}")
    print("PASS external workflow frameworks remain comparison inputs, not SAGE authority")
    print("PASS branch bootstrap is implemented as a governed operator-proposal composition")
    print("Kalaxy3 SAGE workflow capability completeness audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
