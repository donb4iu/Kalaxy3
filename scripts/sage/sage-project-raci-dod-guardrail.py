#!/usr/bin/env python3
"""Validate the Project/RACI completion contract and receipt structure.

This is a structural gate. Independent auditors must verify cited Git/GitHub
records; a structurally valid receipt is never itself an approval.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
STANDARD = "markdown/standards/kalaxy3-sage-project-raci-definition-of-done.md"
FORM = ".github/ISSUE_TEMPLATE/engineering-work.yml"
TARGET = "sage-project-raci-dod-guardrail"

QUESTIONS = (
    "Project contract retrieved",
    "RACI understood and applied",
    "Independent execution within scope",
    "SAGE guardrail compliance",
    "Durable handoff/reconstruction",
)

def required_text(value: Any, label: str, errors: list[str]) -> None:
    """Require nonempty text, appending a field-specific error.

    Args:
        value: Candidate text.
        label: Field label used in diagnostics.
        errors: Mutable diagnostics collection.
    """
    if not isinstance(value, str) or not value.strip():
        errors.append(f"missing or empty: {label}")


def required_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    """Require a mapping or return an empty mapping with a diagnostic.

    Args:
        value: Candidate mapping.
        label: Field label used in diagnostics.
        errors: Mutable diagnostics collection.

    Returns:
        Validated mapping or an empty fallback.
    """
    if not isinstance(value, dict):
        errors.append(f"missing or invalid object: {label}")
        return {}
    return value


def required_references(value: Any, label: str, errors: list[str]) -> None:
    """Require at least one nonblank external evidence reference.

    Args:
        value: Candidate list of references.
        label: Field label used in diagnostics.
        errors: Mutable diagnostics collection.
    """
    if not isinstance(value, list) or not value:
        errors.append(f"missing evidence references: {label}")
    elif any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"invalid evidence reference: {label}")


def check_contract(receipt: Mapping[str, Any], errors: list[str]) -> None:
    """Validate the authoritative Project and participant RACI evidence.

    Args:
        receipt: Candidate completion evidence.
        errors: Mutable diagnostics collection.
    """
    project = required_mapping(receipt.get("project_contract"), "project_contract", errors)
    raci = required_mapping(receipt.get("raci"), "raci", errors)
    for key in ("issue_url", "revision", "retrieval_evidence"):
        required_text(project.get(key), f"project_contract.{key}", errors)
    for key in ("participant", "role", "assignment_ref", "authority_ref"):
        required_text(raci.get(key), f"raci.{key}", errors)
    required_references(raci.get("boundary_evidence"), "raci.boundary_evidence", errors)


def check_execution(receipt: Mapping[str, Any], errors: list[str]) -> None:
    """Validate execution and guardrail evidence; never infer a PASS.

    Args:
        receipt: Candidate completion evidence.
        errors: Mutable diagnostics collection.
    """
    execution = required_mapping(receipt.get("execution"), "execution", errors)
    guards = required_mapping(receipt.get("guardrails"), "guardrails", errors)
    required_references(execution.get("work_refs"), "execution.work_refs", errors)
    required_text(execution.get("scope_evidence"), "execution.scope_evidence", errors)
    required_references(guards.get("results"), "guardrails.results", errors)
    if guards.get("status") != "passed":
        errors.append("guardrails.status must be passed with actual evidence")
    if not isinstance(execution.get("deviations"), list):
        errors.append("execution.deviations must record even an empty list")


def check_continuation(receipt: Mapping[str, Any], errors: list[str]) -> None:
    """Validate durable handoff and independent audit evidence.

    Args:
        receipt: Candidate completion evidence.
        errors: Mutable diagnostics collection.
    """
    handoff = required_mapping(receipt.get("continuation"), "continuation", errors)
    audit = required_mapping(receipt.get("independent_audit"), "independent_audit", errors)
    required_references(handoff.get("persisted_refs"), "continuation.persisted_refs", errors)
    required_text(handoff.get("next_action"), "continuation.next_action", errors)
    if not isinstance(handoff.get("open_obligations"), list):
        errors.append("continuation.open_obligations must be a list")
    for key in ("auditor", "audit_evidence"):
        required_text(audit.get(key), f"independent_audit.{key}", errors)
    if audit.get("verdict") != "verified":
        errors.append("independent_audit.verdict must be verified")


def check_overrides(receipt: Mapping[str, Any], errors: list[str]) -> None:
    """Reject overrides without an attributable Architect decision.

    Args:
        receipt: Candidate completion evidence.
        errors: Mutable diagnostics collection.
    """
    overrides = receipt.get("architect_overrides")
    if not isinstance(overrides, list):
        errors.append("architect_overrides must be a list, even when empty")
        return
    for index, item in enumerate(overrides):
        record = required_mapping(item, f"architect_overrides[{index}]", errors)
        for key in ("architect", "decision_ref", "scope", "rationale"):
            required_text(record.get(key), f"architect_overrides[{index}].{key}", errors)


def validate_receipt(receipt: Mapping[str, Any]) -> list[str]:
    """Return structural deficiencies in a participant closeout receipt.

    Args:
        receipt: Parsed JSON receipt object.

    Returns:
        List of diagnostics, empty when structurally complete.
    """
    errors: list[str] = []
    check_contract(receipt, errors)
    check_execution(receipt, errors)
    check_continuation(receipt, errors)
    check_overrides(receipt, errors)
    return errors


def validate_publication(root: Path = ROOT) -> list[str]:
    """Check that the canonical DoD is published at participant entry points.

    Args:
        root: Repository root containing contract and entry points.

    Returns:
        List of missing publication or contract requirements.
    """
    errors: list[str] = []
    for relative in (STANDARD, FORM, "AGENTS.md", "SAGE.md", "Makefile"):
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        if relative != STANDARD and STANDARD not in content:
            errors.append(f"missing canonical DoD link in {relative}")
    if errors:
        return errors
    standard = (root / STANDARD).read_text(encoding="utf-8")
    form = (root / FORM).read_text(encoding="utf-8")
    makefile = (root / "Makefile").read_text(encoding="utf-8")
    for question in QUESTIONS:
        if question not in standard:
            errors.append(f"missing audit question: {question}")
    for label in ("Project contract retrieved", "RACI applied", "SAGE guardrails", "Durable handoff"):
        if label not in form:
            errors.append(f"missing issue-form DoD: {label}")
    if f"{TARGET}:" not in makefile or TARGET not in makefile.split("sage-stage-guardrails:", 1)[-1]:
        errors.append("missing SAGE stage guardrail integration")
    return errors


def sample_receipt() -> dict[str, Any]:
    """Create a synthetic, never-authoritative receipt for negative tests.

    Returns:
        A structurally populated synthetic receipt.
    """
    return {
        "project_contract": {"issue_url": "https://example.invalid/issues/44",
                             "revision": "synthetic", "retrieval_evidence": "fixture"},
        "raci": {"participant": "fixture", "role": "Responsible",
                 "assignment_ref": "fixture", "authority_ref": "fixture",
                 "boundary_evidence": ["fixture"]},
        "execution": {"work_refs": ["fixture"], "scope_evidence": "fixture",
                      "deviations": []},
        "guardrails": {"status": "passed", "results": ["fixture"]},
        "continuation": {"persisted_refs": ["fixture"], "next_action": "fixture",
                         "open_obligations": []},
        "independent_audit": {"auditor": "fixture", "audit_evidence": "fixture",
                              "verdict": "verified"},
        "architect_overrides": [],
    }


def self_test() -> None:
    """Exercise independent missing-evidence and authority negative cases."""
    import copy

    candidate = sample_receipt()
    assert not validate_receipt(candidate)
    scenarios = (
        ("project_contract", "retrieval_evidence", ""),
        ("raci", "assignment_ref", ""),
        ("raci", "boundary_evidence", []),
        ("execution", "work_refs", []),
        ("guardrails", "status", "failed"),
        ("continuation", "persisted_refs", []),
        ("independent_audit", "verdict", "allow"),
    )
    for section, field, invalid in scenarios:
        defective = copy.deepcopy(candidate)
        defective[section][field] = invalid
        assert validate_receipt(defective), f"accepted missing: {section}.{field}"
    defective = copy.deepcopy(candidate)
    defective["architect_overrides"] = [{"architect": "agent"}]
    assert validate_receipt(defective), "accepted unapproved override"
    assert not validate_publication(), "repository DoD publication incomplete"
    print("SAGE Project/RACI DoD structural self-test: PASS")


def main() -> int:
    """Validate published DoD and optional closeout evidence.

    Returns:
        Process status: zero for valid structure; one for failures.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    errors = validate_publication()
    if args.receipt:
        try:
            payload = json.loads(args.receipt.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                errors.append("closeout receipt must be a JSON object")
            else:
                errors.extend(validate_receipt(payload))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"cannot read closeout receipt: {exc}")
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("SAGE Project/RACI DoD publication and structure: PASS")
    if args.receipt:
        print("CLOSEOUT=STRUCTURAL_ONLY_NOT_INDEPENDENTLY_VERIFIED")
    print("NOTE: External evidence and auditor identity require independent verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
