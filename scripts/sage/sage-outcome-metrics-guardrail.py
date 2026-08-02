#!/usr/bin/env python3
"""Fail-closed runtime guardrail for semantic outcome measurement."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import OutcomeMetrics  # noqa: E402

ARTIFACT_ROOT = ROOT / "markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001"
BASELINE = ARTIFACT_ROOT / "outcome-metrics-baseline.json"
GAP = ARTIFACT_ROOT / "capability-gap-outcome-metrics.json"
MANIFEST = ARTIFACT_ROOT / "component-selection-outcome-metrics.json"


def runtime_failures() -> list[str]:
    failures: list[str] = []
    raw = {field: None for field in __import__("workflow.metrics", fromlist=["RAW_FIELDS"]).RAW_FIELDS}
    raw.update({"workflows_completed": 4, "first_pass_completions": 3, "semantic_validations": 5, "semantic_false_passes": 1, "commands_executed": 8, "manual_corrections": 2, "operator_interventions": 1, "authority_checks": 4, "authority_failures": 1, "components_selected": 4, "components_reused": 3, "known_failures_encountered": 2, "known_failures_recurred": 1, "mutation_opportunities": 2, "failures_detected_pre_mutation": 2})
    report = OutcomeMetrics.build_report(report_id="SAGE-METRICS-20260801-999", captured_at="2026-08-01T22:40:00-05:00", period={"started_at":"2026-08-01T22:00:00-05:00","completed_at":"2026-08-01T22:40:00-05:00"}, workflow_class="fixture", raw_metrics=raw, provenance=({"source_type":"runtime","reference":"fixture","measurement_type":"measured","captured_at":"2026-08-01T22:40:00-05:00"},), limitations=("fixture",))
    if report["derived_metrics"]["first_pass_completion_rate"] != 0.75 or report["derived_metrics"]["manual_correction_rate"] != 0.2:
        failures.append("transparent rate derivation failed")
    if report["composite_score_enabled"] is not False or report["raw_metrics"]["workflows_started"] is not None:
        failures.append("null or composite-score contract failed")
    baseline = {**report, "report_id":"SAGE-METRICS-20260801-998", "derived_metrics":{**report["derived_metrics"], "first_pass_completion_rate":0.5}}
    trend = OutcomeMetrics.trend(metric="first_pass_completion_rate", current_report=report, baseline_report=baseline, direction="higher-is-better", comparability_basis="same fixture class")
    if trend["result"] != "improved":
        failures.append("direction-aware trend failed")
    try:
        OutcomeMetrics.trend(metric="first_pass_completion_rate", current_report=report, baseline_report={**baseline,"workflow_class":"other"}, direction="higher-is-better", comparability_basis="invalid")
    except ValueError:
        pass
    else:
        failures.append("incomparable workflow classes were accepted")
    try:
        OutcomeMetrics.derive({**raw, "first_pass_completions":5})
    except ValueError:
        pass
    else:
        failures.append("invalid subset numerator was accepted")
    return failures


def repository_failures() -> list[str]:
    failures: list[str] = []
    registry = json.loads((ROOT / "sage-workflow-primitives.json").read_text(encoding="utf-8"))
    entries = {item.get("primitive_id"): item for item in registry.get("primitives", []) if isinstance(item, dict)}
    entry = entries.get("metrics.outcome", {})
    if entry.get("version") != "1.0.0" or entry.get("capability_gap_receipt") != str(GAP.relative_to(ROOT)):
        failures.append("metrics.outcome registry contract failed")
    for path in (BASELINE, GAP, MANIFEST):
        if not path.is_file(): failures.append(f"missing outcome artifact: {path}")
    if BASELINE.is_file():
        value=json.loads(BASELINE.read_text(encoding="utf-8"))
        rebuilt=OutcomeMetrics.build_report(report_id=value["report_id"], captured_at=value["captured_at"], period=value["period"], workflow_class=value["workflow_class"], raw_metrics=value["raw_metrics"], provenance=value["provenance"], limitations=value["limitations"], trends=value["trends"])
        if rebuilt != value: failures.append("baseline report does not match primitive semantics")
        if value.get("composite_score_enabled") is not False: failures.append("baseline enabled composite score")
    if GAP.is_file() and json.loads(GAP.read_text(encoding="utf-8")).get("approval",{}).get("status") != "approved": failures.append("outcome gap is not approved")
    if MANIFEST.is_file():
        value=json.loads(MANIFEST.read_text(encoding="utf-8"))
        if value.get("approval",{}).get("status") != "approved" or value.get("composite_score_enabled") is not False: failures.append("outcome component manifest contract failed")
    policy=json.loads((ROOT / "sage-operating-contract-policy.json").read_text(encoding="utf-8"))
    activation=policy.get("activation_policy",{})
    if "semantic-outcome-measurement" not in activation.get("completed_phases",[]): failures.append("Phase 4 completion marker is missing")
    if activation.get("current_state") != "staged-implementation" or activation.get("deployment_authorized") is not False: failures.append("Phase 4 must remain staged and non-deploying")
    return failures


def main() -> int:
    failures=[*runtime_failures(),*repository_failures()]
    if failures:
        print("Kalaxy3 SAGE outcome metrics guardrail: FAIL CLOSED")
        for failure in failures: print(f"  - {failure}")
        return 1
    print("PASS explicit raw metrics and null preservation")
    print("PASS transparent derived rates and invalid-subset rejection")
    print("PASS comparable workflow-class trends and direction semantics")
    print("PASS baseline, registry, policy, manifest, and approved-gap integration")
    print("Kalaxy3 SAGE outcome metrics guardrail: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
