#!/usr/bin/env python3
"""Validate and render the Kalaxy3 SAGE capability-intelligence model."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
MODEL = "sage-capability-intelligence.json"
VIEW = "markdown/architecture/kalaxy3-sage-capability-intelligence.md"
METRICS = "markdown/architecture/kalaxy3-sage-capability-intelligence-metrics.json"

def load(root: Path) -> dict[str, Any]:
    return json.loads((root / MODEL).read_text(encoding="utf-8"))

def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def contains_key(value: Any, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(contains_key(item, key) for item in value)
    return False

def validate(value: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    if value.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")
    policy = value.get("policy", {})
    federation = value.get("federation", {})
    picture = value.get("picture", {})
    decisions = value.get("decision_cycle", {})

    if contains_key(picture, "overall_score") or contains_key(picture, "composite_score"):
        failures.append("opaque overall/composite capability score is forbidden")
    dimensions = policy.get("dimensions", [])
    if not dimensions or len(dimensions) != len(set(dimensions)):
        failures.append("policy dimensions must be unique and non-empty")
    if policy.get("composite_score_enabled") is not False:
        failures.append("composite scoring must remain disabled")
    if len(policy.get("war_pillars", [])) != 6:
        failures.append("exactly six WAR pillars are required")
    if len(policy.get("caf_perspectives", [])) != 6:
        failures.append("exactly six CAF perspectives are required")
    if policy.get("maximum_current_autonomy", 99) > 2:
        failures.append("SAGE autonomy may not exceed level 2")

    authority_items = federation.get("authorities", [])
    authority_ids = [item.get("authority_id") for item in authority_items]
    if len(authority_ids) != len(set(authority_ids)):
        failures.append("authority IDs must be unique")
    for item in authority_items:
        for field in ("authority_id", "scope", "precedence_within_scope",
                      "freshness_policy", "limitations"):
            if field not in item:
                failures.append(f"authority {item.get('authority_id')} missing {field}")
        if item.get("silent_override_allowed") is not False:
            failures.append(f"authority {item.get('authority_id')} permits silent override")
    if federation.get("sage_role") != "partner":
        failures.append("SAGE must remain a decision partner")
    if federation.get("silent_conflict_resolution_allowed") is not False:
        failures.append("silent conflict resolution must be forbidden")

    outcomes = {item.get("outcome_id") for item in picture.get("mission_outcomes", [])}
    capabilities = picture.get("capabilities", [])
    capability_ids = [item.get("capability_id") for item in capabilities]
    capability_set = set(capability_ids)
    if len(capability_ids) != len(capability_set):
        failures.append("capability IDs must be unique")
    graph: dict[str, list[str]] = {}
    statuses = set(policy.get("dimension_statuses", []))
    war = set(policy.get("war_pillars", []))
    caf = set(policy.get("caf_perspectives", []))

    for item in capabilities:
        cid = item.get("capability_id")
        graph[cid] = list(item.get("dependencies", []))
        missing = set(graph[cid]) - capability_set
        if missing:
            failures.append(f"{cid}: unknown dependencies {sorted(missing)}")
        missing_outcomes = set(item.get("mission_outcome_ids", [])) - outcomes
        if missing_outcomes:
            failures.append(f"{cid}: unknown outcomes {sorted(missing_outcomes)}")
        target = item.get("target_dimensions", {})
        current = item.get("current_dimensions", {})
        if set(target) != set(dimensions):
            failures.append(f"{cid}: target dimensions differ from policy")
        if set(current) != set(dimensions):
            failures.append(f"{cid}: current dimensions differ from policy")
        for name in dimensions:
            target_score = target.get(name)
            state = current.get(name, {})
            status = state.get("status")
            score = state.get("score")
            if not isinstance(target_score, int) or not 0 <= target_score <= 100:
                failures.append(f"{cid}/{name}: target score invalid")
            if status not in statuses:
                failures.append(f"{cid}/{name}: status invalid")
            if status in {"unknown", "not-applicable"}:
                if score is not None:
                    failures.append(f"{cid}/{name}: unknown score must be null")
            elif not isinstance(score, int) or not 0 <= score <= 100:
                failures.append(f"{cid}/{name}: current score invalid")
            for field in ("confidence", "rationale", "evidence_refs"):
                if field not in state:
                    failures.append(f"{cid}/{name}: missing {field}")
        if set(item.get("war", {})) != war:
            failures.append(f"{cid}: WAR lens incomplete")
        if set(item.get("caf", {})) != caf:
            failures.append(f"{cid}: CAF lens incomplete")
        for assertion in item.get("assertions", []):
            for field in ("assertion_type", "authority_id", "observed_at",
                          "confidence", "statement", "evidence_refs"):
                if field not in assertion:
                    failures.append(f"{cid}: assertion missing {field}")
            if assertion.get("authority_id") not in authority_ids:
                failures.append(f"{cid}: assertion authority unknown")

    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            failures.append(f"capability dependency cycle includes {node}")
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)

    if not set(picture.get("capability_floor", [])) <= capability_set:
        failures.append("capability floor contains unknown IDs")
    for conflict in picture.get("conflicts", []):
        if conflict.get("capability_id") not in capability_set:
            failures.append("conflict references unknown capability")
        if set(conflict.get("authority_ids", [])) - set(authority_ids):
            failures.append("conflict references unknown authority")

    branches = decisions.get("branches", [])
    branch_ids = [item.get("branch_id") for item in branches]
    if len(branch_ids) != len(set(branch_ids)):
        failures.append("branch IDs must be unique")
    if "branch.do-nothing" not in branch_ids:
        failures.append("do-nothing baseline is required")
    selected_id = decisions.get("selected_branch_id")
    if selected_id not in branch_ids:
        failures.append("selected branch is missing")
    for item in branches:
        prediction = item.get("prediction")
        if not isinstance(prediction, dict):
            failures.append(f"{item.get('branch_id')}: prediction missing")
            continue
        if item.get("prediction_digest") != digest(prediction):
            failures.append(f"{item.get('branch_id')}: prediction digest mismatch")
        for field in ("version", "stage", "recorded_at", "confidence",
                      "confidence_basis", "assumptions", "known_unknowns",
                      "failure_conditions", "impact", "effort", "cost",
                      "risk", "reversibility", "expected_value",
                      "time_to_useful_evidence"):
            if field not in prediction:
                failures.append(f"{item.get('branch_id')}: prediction missing {field}")
        for estimate in prediction.get("effort", []) + prediction.get("cost", []):
            for field in ("subject", "estimate", "range", "unit", "size", "confidence"):
                if field not in estimate:
                    failures.append(f"{item.get('branch_id')}: estimate missing {field}")
        if set(item.get("consulted_authority_ids", [])) - set(authority_ids):
            failures.append(f"{item.get('branch_id')}: consulted authority unknown")
        if item.get("decision_authority_id") not in authority_ids:
            failures.append(f"{item.get('branch_id')}: decision authority unknown")
        outcome = item.get("actual_outcome")
        if outcome is not None:
            predicted_units = {
                estimate["subject"]: estimate["unit"]
                for estimate in prediction.get("effort", [])
            }
            for actual in outcome.get("actual_effort", []):
                subject = actual.get("subject")
                if subject not in predicted_units:
                    failures.append(f"{item.get('branch_id')}: unpredicted actual subject")
                elif actual.get("unit") != predicted_units[subject]:
                    failures.append(f"{item.get('branch_id')}: actual unit differs")

    return failures

def summary(capability: Mapping[str, Any]) -> dict[str, Any]:
    known = [
        (name, state["score"], capability["target_dimensions"][name])
        for name, state in capability["current_dimensions"].items()
        if state["score"] is not None
    ]
    lowest = sorted(known, key=lambda row: (row[1], row[0]))[:3]
    return {
        "known": len(known),
        "unknown": len(capability["current_dimensions"]) - len(known),
        "at_target": sum(score >= target for _, score, target in known),
        "lowest": [
            {"dimension": name, "score": score, "target": target, "gap": target - score}
            for name, score, target in lowest
        ],
        "blockers": len(capability.get("blocking_findings", [])),
    }

def metrics(value: Mapping[str, Any]) -> dict[str, Any]:
    picture = value["picture"]
    capabilities = {
        item["capability_id"]: summary(item)
        for item in picture["capabilities"]
    }
    return {
        "schema_version": "1.0",
        "snapshot_type": "sage-capability-intelligence",
        "captured_at": picture["captured_at"],
        "target_id": picture["preferred_target"]["target_id"],
        "capability_count": len(capabilities),
        "floor_count": len(picture["capability_floor"]),
        "unknown_dimension_count": sum(item["unknown"] for item in capabilities.values()),
        "blocking_finding_count": sum(item["blockers"] for item in capabilities.values()),
        "conflict_count": len(picture["conflicts"]),
        "capabilities": capabilities,
        "decision_cycle": {
            "selected_branch_id": value["decision_cycle"]["selected_branch_id"],
            "actual_outcome_recorded": value["decision_cycle"]["actual_outcome_recorded"],
            "calibration_status": value["decision_cycle"]["calibration_status"],
        },
        "composite_score_enabled": False,
    }

def render(value: Mapping[str, Any]) -> str:
    picture = value["picture"]
    decisions = value["decision_cycle"]
    lines = [
        "# Kalaxy3 SAGE Capability Intelligence",
        "",
        f"- Preferred target: `{picture['preferred_target']['target_id']}`",
        f"- Target status: `{picture['preferred_target']['status']}`",
        f"- Target confidence: `{picture['preferred_target']['confidence']}`",
        f"- Captured: `{picture['captured_at']}`",
        "",
        "## Mission",
        "",
        value["policy"]["mission"],
        "",
        "## Mission outcomes",
        "",
    ]
    for outcome in picture["mission_outcomes"]:
        lines.append(f"- `{outcome['outcome_id']}` — {outcome['title']}")
    lines.extend([
        "",
        "## Capability target and current status",
        "",
        "No opaque overall score is used. Unknowns, blockers, confidence, and the lowest known gaps remain visible.",
        "",
        "| Capability | Criticality | Lifecycle | At target | Unknown | Blockers | Lowest known gaps |",
        "|---|---|---|---:|---:|---:|---|",
    ])
    for item in picture["capabilities"]:
        state = summary(item)
        low = ", ".join(
            f"{entry['dimension']}:{entry['score']}/{entry['target']}"
            for entry in state["lowest"]
        )
        lines.append(
            f"| `{item['capability_id']}` | {item['criticality']} | {item['lifecycle']} | "
            f"{state['at_target']}/{state['known']} | {state['unknown']} | "
            f"{state['blockers']} | {low or 'none'} |"
        )
    for item in picture["capabilities"]:
        lines.extend([
            "",
            f"### {item['title']}",
            "",
            f"- ID: `{item['capability_id']}`",
            f"- Implementation: {item['current_implementation']}",
            f"- Rebuild-forward: `{item['rebuild_forward_status']}`",
            "",
            "| Dimension | Status | Current | Target | Confidence | Gap |",
            "|---|---|---:|---:|---|---:|",
        ])
        for name, state in item["current_dimensions"].items():
            target = item["target_dimensions"][name]
            score = state["score"]
            score_text = "unknown" if score is None else str(score)
            gap = "unknown" if score is None else str(target - score)
            lines.append(
                f"| `{name}` | {state['status']} | {score_text} | {target} | "
                f"{state['confidence']} | {gap} |"
            )
        lines.extend(["", "**Assertions**", ""])
        for assertion in item["assertions"]:
            lines.append(
                f"- `{assertion['authority_id']}` ({assertion['assertion_type']}, "
                f"{assertion['confidence']}, {assertion['observed_at']}): "
                f"{assertion['statement']}"
            )
        lines.append("")
        lines.append("- WAR: " + ", ".join(f"{key}={state}" for key, state in item["war"].items()))
        lines.append("- CAF: " + ", ".join(f"{key}={state}" for key, state in item["caf"].items()))
    lines.extend(["", "## Visible authority conflicts", ""])
    for conflict in picture["conflicts"]:
        lines.append(
            f"- `{conflict['conflict_id']}` ({conflict['status']}): {conflict['summary']}"
        )
    lines.extend([
        "",
        "## Alternative branches",
        "",
        "| Branch | Status | Confidence | Risk | Reversibility | Expected value |",
        "|---|---|---|---|---|---|",
    ])
    for item in decisions["branches"]:
        prediction = item["prediction"]
        lines.append(
            f"| `{item['branch_id']}` | {item['status']} | {prediction['confidence']} | "
            f"{prediction['risk']} | {prediction['reversibility']} | "
            f"{prediction['expected_value']} |"
        )
    lines.extend([
        "",
        f"Selected branch: `{decisions['selected_branch_id']}`",
        f"Actual outcome recorded: `{decisions['actual_outcome_recorded']}`",
        f"Calibration status: `{decisions['calibration_status']}`",
        "",
        "## Federated authority",
        "",
        "| Authority | Scope | Precedence |",
        "|---|---|---:|",
    ])
    for authority in value["federation"]["authorities"]:
        lines.append(
            f"| `{authority['authority_id']}` | {authority['scope']} | "
            f"{authority['precedence_within_scope']} |"
        )
    lines.extend([
        "",
        f"Current SAGE autonomy: `{value['policy']['maximum_current_autonomy']}` "
        "(render, propose, rank; mutation remains approval-gated).",
        "",
    ])
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
    if failures:
        return ["production model invalid"] + failures
    cases: list[tuple[dict[str, Any], str]] = []
    duplicate = copy.deepcopy(value)
    duplicate["picture"]["capabilities"][1]["capability_id"] = duplicate["picture"]["capabilities"][0]["capability_id"]
    cases.append((duplicate, "capability IDs must be unique"))
    opaque = copy.deepcopy(value)
    opaque["picture"]["overall_score"] = 73
    cases.append((opaque, "opaque overall/composite"))
    authority = copy.deepcopy(value)
    authority["picture"]["capabilities"][0]["assertions"][0]["authority_id"] = "missing"
    cases.append((authority, "assertion authority unknown"))
    prediction = copy.deepcopy(value)
    prediction["decision_cycle"]["branches"][0]["prediction"]["confidence"] = "high"
    cases.append((prediction, "prediction digest mismatch"))
    unknown = copy.deepcopy(value)
    state = unknown["picture"]["capabilities"][0]["current_dimensions"]["security-assurance"]
    state["status"] = "unknown"
    state["score"] = 50
    cases.append((unknown, "unknown score must be null"))
    no_baseline = copy.deepcopy(value)
    no_baseline["decision_cycle"]["branches"] = [
        item for item in no_baseline["decision_cycle"]["branches"]
        if item["branch_id"] != "branch.do-nothing"
    ]
    cases.append((no_baseline, "do-nothing baseline is required"))
    cycle = copy.deepcopy(value)
    first = cycle["picture"]["capabilities"][0]["capability_id"]
    second = cycle["picture"]["capabilities"][1]["capability_id"]
    cycle["picture"]["capabilities"][0]["dependencies"] = [second]
    cycle["picture"]["capabilities"][1]["dependencies"] = [first]
    cases.append((cycle, "dependency cycle"))
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
        print("SAGE capability intelligence: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    if args.command == "check":
        print("SAGE capability intelligence model: PASS")
        return 0
    if args.command == "render":
        if not write_or_check(args.repo / VIEW, render(value), args.check):
            print("Rendered capability view differs")
            return 1
        print("SAGE capability intelligence render: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    if args.command == "metrics":
        content = json.dumps(metrics(value), indent=2, ensure_ascii=False)
        if not write_or_check(args.repo / METRICS, content, args.check):
            print("Capability metrics snapshot differs")
            return 1
        print("SAGE capability intelligence metrics: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    failures = self_test(value)
    if failures:
        print("SAGE capability intelligence self-test: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS production model")
    print("PASS multidimensional target/current contract")
    print("PASS WAR and CAF lens completeness")
    print("PASS federated authority and conflict contract")
    print("PASS immutable scalar-neutral branch predictions")
    print("PASS dependency, unknown, do-nothing, and opaque-score negative tests")
    print("SAGE capability intelligence self-test: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
