#!/usr/bin/env python3
"""Validate and render the Kalaxy3 SAGE end-to-end thin slice."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
MODEL = "sage-thin-slice.json"
VIEW = "markdown/architecture/kalaxy3-sage-thin-slice.md"
METRICS = "markdown/architecture/kalaxy3-sage-thin-slice-metrics.json"


def load(root: Path) -> dict[str, Any]:
    return json.loads((root / MODEL).read_text(encoding="utf-8"))


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> list[str]:
    return [f"{label} missing {field}" for field in fields if field not in value]


def _validate_selected(value: Mapping[str, Any]) -> list[str]:
    failures = _require_fields(
        value,
        ("capability_id", "selection_authority_id", "selection_rationale", "evidence_refs"),
        "selected_case",
    )
    if value.get("selection_authority_id") != "operator-intent":
        failures.append("selected case must preserve operator decision authority")
    if not value.get("evidence_refs"):
        failures.append("selected case requires evidence")
    return failures


def _validate_alternatives(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    identifiers = [item.get("case_id") for item in items]
    if len(identifiers) != len(set(identifiers)):
        failures.append("alternative case IDs must be unique")
    dispositions = {item.get("disposition") for item in items}
    if "rejected" not in dispositions:
        failures.append("at least one rejected alternative is required")
    if "do-nothing" not in identifiers:
        failures.append("do-nothing alternative is required")
    for item in items:
        failures.extend(_require_fields(item, ("case_id", "title", "disposition", "rationale"), "alternative"))
    return failures


def _validate_trace(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    expected = list(range(1, len(items) + 1))
    if [item.get("sequence") for item in items] != expected:
        failures.append("end-to-end trace sequence must be contiguous")
    for item in items:
        failures.extend(_require_fields(
            item,
            ("sequence", "stage_id", "title", "source_statement", "sage_contribution", "human_contribution", "evidence_refs"),
            "trace stage",
        ))
        if not item.get("evidence_refs"):
            failures.append(f"{item.get('stage_id')}: source-backed stage requires evidence")
        if not item.get("human_contribution"):
            failures.append(f"{item.get('stage_id')}: human contribution is required")
    return failures


def _validate_measures(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    identifiers = [item.get("measure_id") for item in items]
    if len(identifiers) != len(set(identifiers)):
        failures.append("measure IDs must be unique")
    for item in items:
        failures.extend(_require_fields(
            item,
            ("measure_id", "description", "target", "actual", "unit", "status", "measurement_type", "evidence_refs"),
            "measure",
        ))
        unavailable = item.get("measurement_type") == "unavailable"
        if unavailable and item.get("actual") is not None:
            failures.append(f"{item.get('measure_id')}: unavailable actual must be null")
        if not unavailable and not item.get("evidence_refs"):
            failures.append(f"{item.get('measure_id')}: measured outcome requires evidence")
        if item.get("status") == "not-measured" and not unavailable:
            failures.append(f"{item.get('measure_id')}: not-measured must be unavailable")
    return failures


def _validate_participation(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = {"reader", "operator", "domain-expert", "engineer", "reviewer"}
    observed = {item.get("participant") for item in items}
    if not required <= observed:
        failures.append(f"participation paths missing {sorted(required - observed)}")
    for item in items:
        failures.extend(_require_fields(item, ("participant", "entry_action", "authority"), "participation path"))
    return failures


def validate(value: Mapping[str, Any]) -> list[str]:
    failures = _require_fields(
        value,
        ("schema_version", "thin_slice_id", "title", "status", "audience", "introduction", "case_question", "selected_case", "alternatives", "end_to_end_trace", "measures", "participation_paths", "future_capability"),
        "thin slice",
    )
    if value.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")
    if value.get("thin_slice_id") != "kalaxy3.centralized-logging":
        failures.append("unexpected thin_slice_id")
    failures.extend(_validate_selected(value.get("selected_case", {})))
    failures.extend(_validate_alternatives(value.get("alternatives", [])))
    failures.extend(_validate_trace(value.get("end_to_end_trace", [])))
    failures.extend(_validate_measures(value.get("measures", [])))
    failures.extend(_validate_participation(value.get("participation_paths", [])))
    return failures


def metrics(value: Mapping[str, Any]) -> dict[str, Any]:
    measures = value["measures"]
    return {
        "schema_version": "1.0",
        "snapshot_type": "sage-thin-slice",
        "thin_slice_id": value["thin_slice_id"],
        "status": value["status"],
        "trace_stage_count": len(value["end_to_end_trace"]),
        "alternative_count": len(value["alternatives"]),
        "participation_path_count": len(value["participation_paths"]),
        "measures_met": sum(item["status"] == "met" for item in measures),
        "measures_not_measured": sum(item["status"] == "not-measured" for item in measures),
        "measures": measures,
        "maturity_claim": None,
    }


def _render_alternatives(value: Mapping[str, Any]) -> list[str]:
    lines = ["## Alternatives considered", "", "| Case | Disposition | Rationale |", "|---|---|---|"]
    for item in value["alternatives"]:
        lines.append(f"| `{item['case_id']}` | {item['disposition']} | {item['rationale']} |")
    return lines


def _render_trace(value: Mapping[str, Any]) -> list[str]:
    lines = ["## End-to-end trace", ""]
    for item in value["end_to_end_trace"]:
        lines.extend([
            f"### {item['sequence']}. {item['title']}", "",
            f"**What happened:** {item['source_statement']}", "",
            f"**SAGE contribution:** {item['sage_contribution']}", "",
            f"**Human contribution:** {item['human_contribution']}", "",
            "**Evidence:** " + ", ".join(f"`{ref}`" for ref in item["evidence_refs"]), "",
        ])
    return lines


def _render_measures(value: Mapping[str, Any]) -> list[str]:
    lines = ["## Measured outcomes and open measurements", "", "| Measure | Target | Actual | Status | Evidence |", "|---|---:|---:|---|---|"]
    for item in value["measures"]:
        actual = "unknown" if item["actual"] is None else str(item["actual"])
        refs = ", ".join(f"`{ref}`" for ref in item["evidence_refs"]) or "not yet available"
        lines.append(f"| `{item['measure_id']}` | {item['target']} {item['unit']} | {actual} | {item['status']} | {refs} |")
    return lines


def _render_participation(value: Mapping[str, Any]) -> list[str]:
    lines = ["## How to participate", ""]
    for item in value["participation_paths"]:
        lines.extend([
            f"### {item['participant']}", "",
            item["entry_action"], "",
            f"**Authority boundary:** {item['authority']}", "",
        ])
    return lines


def render(value: Mapping[str, Any]) -> str:
    selected = value["selected_case"]
    lines = [
        "# Kalaxy3 SAGE End-to-End Thin Slice", "",
        f"**Case:** {value['title']}", "",
        "## What SAGE is", "", value["introduction"], "",
        "## The question", "", value["case_question"], "",
        "## Why this case", "", selected["selection_rationale"], "",
        f"Decision authority: `{selected['selection_authority_id']}`", "",
        "Core evidence: " + ", ".join(f"`{ref}`" for ref in selected["evidence_refs"]), "",
    ]
    lines.extend(_render_alternatives(value))
    lines.extend([""] + _render_trace(value))
    lines.extend(_render_measures(value))
    lines.extend([""] + _render_participation(value))
    lines.extend(["## Reusable future capability", ""])
    lines.extend(f"- {item}" for item in value["future_capability"])
    lines.extend(["", "SAGE remains a federated decision partner. Repository, operator, runtime, and domain authorities retain their scoped authority.", ""])
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    normalized = content.rstrip() + "\n"
    if check:
        return path.is_file() and path.read_text(encoding="utf-8") == normalized
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    return True


def self_test(value: Mapping[str, Any]) -> list[str]:
    failures = validate(value)
    cases: list[tuple[dict[str, Any], str]] = []
    no_human = copy.deepcopy(value)
    no_human["end_to_end_trace"][0]["human_contribution"] = ""
    cases.append((no_human, "human contribution"))
    no_baseline = copy.deepcopy(value)
    no_baseline["alternatives"] = [item for item in no_baseline["alternatives"] if item["case_id"] != "do-nothing"]
    cases.append((no_baseline, "do-nothing alternative"))
    fabricated = copy.deepcopy(value)
    fabricated["measures"][-1]["actual"] = 0
    cases.append((fabricated, "unavailable actual must be null"))
    no_evidence = copy.deepcopy(value)
    no_evidence["end_to_end_trace"][0]["evidence_refs"] = []
    cases.append((no_evidence, "requires evidence"))
    wrong_authority = copy.deepcopy(value)
    wrong_authority["selected_case"]["selection_authority_id"] = "sage-inference"
    cases.append((wrong_authority, "operator decision authority"))
    for candidate, expected in cases:
        observed = validate(candidate)
        if not any(expected in item for item in observed):
            failures.append(f"negative test missing {expected}: {observed}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "render", "metrics", "self-test"))
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = load(args.repo)
    failures = validate(value)
    if failures:
        print("SAGE thin slice: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    if args.command == "check":
        print("SAGE thin-slice model: PASS")
        return 0
    if args.command == "render":
        if not write_or_check(args.repo / VIEW, render(value), args.check):
            print("Rendered thin-slice view differs")
            return 1
        print("SAGE thin-slice render: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    if args.command == "metrics":
        content = json.dumps(metrics(value), indent=2, ensure_ascii=False)
        if not write_or_check(args.repo / METRICS, content, args.check):
            print("Thin-slice metrics snapshot differs")
            return 1
        print("SAGE thin-slice metrics: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    failures = self_test(value)
    if failures:
        print("SAGE thin-slice self-test: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS selected real case and alternatives")
    print("PASS source, SAGE, and human-contribution separation")
    print("PASS measured outcomes and explicit unknowns")
    print("PASS participation and reusable-capability paths")
    print("PASS authority, evidence, and do-nothing negative tests")
    print("SAGE thin-slice self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
