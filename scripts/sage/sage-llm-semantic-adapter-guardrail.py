#!/usr/bin/env python3
# Fail closed if SAGE makes an LLM serialize canonical SAGE control records.

import argparse
import ast
import json
from pathlib import Path

FORBIDDEN_MODEL_FIELDS = {
    "schema_version",
    "record_type",
    "producer_class",
    "authority",
    "objective_id",
    "decision",
    "objective_effect",
    "material_change",
    "request_sha256",
    "proposal_sha256",
    "receipt",
}

EXPECTED_ROLE_FIELDS = {
    "intent",
    "rationale",
    "clarification_question",
    "observations",
}

EXPECTED_MAPPING = {
    "bounded-correction": "implementation-local",
    "replan": "planning",
    "meaning-change": "semantic-confirmation",
    "authority-problem": "authority",
    "need-clarification": "architect-clarification-required",
}


def _literal_assignment(tree, name):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError(f"missing assignment {name}")


def validate(root):
    failures=[]
    policy_path=root / "sage-llm-semantic-adapter-policy.json"
    standard_path=root / "markdown/standards/kalaxy3-sage-llm-semantic-adapter-sop.md"
    manager_path=root / "scripts/sage/workflows/llm_workflow_manager.py"
    makefile_path=root / "Makefile"

    for path in (policy_path, standard_path, manager_path, makefile_path):
        if not path.exists():
            failures.append(f"missing semantic-adapter SOP artifact: {path.relative_to(root)}")
    if failures:
        return failures

    policy=json.loads(policy_path.read_text(encoding="utf-8"))
    if policy.get("policy_id") != "SAGE-LLM-SEMANTIC-ADAPTER-SOP-001":
        failures.append("semantic-adapter policy identity changed")
    if policy.get("scope") != "all SAGE LLM and inference roles":
        failures.append("semantic-adapter SOP is not system-wide")

    source=manager_path.read_text(encoding="utf-8")
    tree=ast.parse(source)
    try:
        response_format=_literal_assignment(tree, "ROLE_RESPONSE_FORMAT")
        mapping=_literal_assignment(tree, "SEMANTIC_INTENT_MAP")
    except Exception as exc:
        failures.append(str(exc))
        return failures

    properties=set(response_format.get("properties", {}))
    required=set(response_format.get("required", []))
    if properties != EXPECTED_ROLE_FIELDS or required != EXPECTED_ROLE_FIELDS:
        failures.append("workflow-manager model-facing schema is not the minimal role semantic contract")
    leaked=properties & FORBIDDEN_MODEL_FIELDS
    if leaked:
        failures.append("model-facing schema leaks SAGE control fields: "+repr(sorted(leaked)))
    if mapping != EXPECTED_MAPPING:
        failures.append("workflow-manager semantic-to-SAGE mapping changed")

    for marker in (
        "def _canonicalize_semantic_response(",
        "response_format=ROLE_RESPONSE_FORMAT",
        "return validate_decision(canonical, objective_id=objective_id)",
        "_self_test_semantic_adapter()",
    ):
        if marker not in source:
            failures.append("workflow-manager semantic adapter marker missing: "+marker)

    canonical_source=source[
        source.index("def _canonicalize_semantic_response("):
        source.index("def _invoke_fresh_manager(")
    ]
    for marker in (
        '"schema_version": "1.0"',
        '"record_type": "sage-llm-workflow-manager-decision"',
        '"authority": "advisory"',
        '"objective_id": objective_id',
        '"material_change": decision in {"semantic-confirmation", "authority"}',
    ):
        if marker not in canonical_source:
            failures.append("SAGE-owned canonicalization marker missing: "+marker)

    standard=standard_path.read_text(encoding="utf-8")
    for marker in (
        "LLMs propose meaning. SAGE converts meaning into canonical control records.",
        "SAGE may translate representation but may not silently repair meaning.",
        "This SOP applies to all current and future SAGE LLM/inference roles.",
    ):
        if marker not in standard:
            failures.append("normative SOP marker missing: "+marker)

    makefile=makefile_path.read_text(encoding="utf-8")
    if "sage-stage-guardrails: sage-llm-semantic-adapter-guardrail" not in makefile:
        failures.append("semantic-adapter guardrail is not bound into sage-stage-guardrails")
    if "sage-llm-semantic-adapter-guardrail:" not in makefile:
        failures.append("semantic-adapter guardrail Makefile target missing")

    return failures


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args=parser.parse_args()
    failures=validate(args.root.expanduser().resolve())
    if failures:
        print("Kalaxy3 SAGE LLM semantic-adapter SOP guardrail: FAIL CLOSED")
        for failure in failures:
            print("  - "+failure)
        return 1
    print("PASS model-facing contract contains role semantics only")
    print("PASS SAGE owns canonical control-record construction")
    print("PASS deterministic semantic mapping and invariant derivation")
    print("PASS canonical validator remains post-conversion authority")
    print("PASS semantic-adapter SOP is bound into stage guardrails")
    print("Kalaxy3 SAGE LLM semantic-adapter SOP guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
