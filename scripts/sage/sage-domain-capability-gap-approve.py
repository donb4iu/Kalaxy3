#!/usr/bin/env python3
"""Approve a checksum-bound SAGE domain-capability gap set for one exact staged candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import AtomicFileWriter, WorkflowError  # noqa: E402


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _load_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError(f"{label} is unreadable JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise WorkflowError(f"{label} must be a JSON object: {path}")
    return value, payload


def _candidate_binding(gap_set: Mapping[str, Any], candidate_contribution: Path) -> dict[str, str]:
    authority_value = gap_set.get("authority_receipt")
    if not isinstance(authority_value, str) or not authority_value:
        raise WorkflowError("domain capability gap set authority receipt is missing")
    authority_path = Path(authority_value).expanduser().resolve()
    authority, authority_bytes = _load_object(authority_path, "domain capability gap authority receipt")
    semantic = authority.get("semantic_authority")
    if not isinstance(semantic, Mapping):
        raise WorkflowError("domain capability gap authority receipt lacks semantic authority")
    understanding_sha = semantic.get("semantic_understanding_sha256")
    confirmation_sha = semantic.get("semantic_confirmation_sha256")
    if (
        not isinstance(understanding_sha, str)
        or len(understanding_sha) != 64
        or not isinstance(confirmation_sha, str)
        or len(confirmation_sha) != 64
    ):
        raise WorkflowError("domain capability gap semantic authority digests are invalid")
    contribution_path = candidate_contribution.expanduser().resolve()
    if not contribution_path.is_file():
        raise WorkflowError(f"staged candidate contribution is missing: {contribution_path}")
    contribution_sha = _sha256(contribution_path.read_bytes())
    request = gap_set.get("request")
    if not isinstance(request, str) or not request:
        raise WorkflowError("domain capability gap set request is invalid")
    return {
        "request_sha256": _sha256(request.encode("utf-8")),
        "contribution_sha256": contribution_sha,
        "semantic_understanding_sha256": understanding_sha,
        "semantic_confirmation_sha256": confirmation_sha,
        "authority_receipt_sha256": _sha256(authority_bytes),
    }


def _validate_review_gap_set(path: Path) -> tuple[dict[str, Any], list[tuple[dict[str, Any], bytes, Path]]]:
    gap_set, _ = _load_object(path, "domain capability gap set")
    if gap_set.get("schema_version") != "1.0" or gap_set.get("record_type") != "sage-domain-capability-gap-set":
        raise WorkflowError("domain capability gap set version/type is invalid")
    approval = gap_set.get("approval")
    if not isinstance(approval, Mapping) or approval.get("status") != "review-required":
        raise WorkflowError("domain capability gap set is not awaiting review")
    request = gap_set.get("request")
    gaps = gap_set.get("gaps")
    if not isinstance(request, str) or not request or not isinstance(gaps, list) or not gaps:
        raise WorkflowError("domain capability gap set request/gaps are invalid")
    if gap_set.get("gap_count") != len(gaps):
        raise WorkflowError("domain capability gap set count is invalid")
    receipts: list[tuple[dict[str, Any], bytes, Path]] = []
    seen: set[str] = set()
    for index, item in enumerate(gaps, 1):
        if not isinstance(item, Mapping):
            raise WorkflowError(f"domain capability gap set item {index} is invalid")
        capability_id = item.get("required_capability")
        receipt_value = item.get("gap_receipt")
        expected_sha = item.get("gap_receipt_sha256")
        if not isinstance(capability_id, str) or not capability_id or capability_id in seen:
            raise WorkflowError(f"domain capability gap set capability {index} is invalid or duplicated")
        if not isinstance(receipt_value, str) or not receipt_value or not isinstance(expected_sha, str) or len(expected_sha) != 64:
            raise WorkflowError(f"domain capability gap set receipt {index} is incomplete")
        seen.add(capability_id)
        receipt_path = Path(receipt_value).expanduser().resolve()
        receipt, receipt_bytes = _load_object(receipt_path, f"domain capability gap receipt {index}")
        if _sha256(receipt_bytes) != expected_sha:
            raise WorkflowError(f"domain capability gap receipt digest changed: {receipt_path}")
        if receipt.get("schema_version") != "1.1" or receipt.get("gap_kind") != "domain-capability":
            raise WorkflowError(f"domain capability gap receipt {index} version/type is invalid")
        if receipt.get("request") != request or receipt.get("required_capability") != capability_id:
            raise WorkflowError(f"domain capability gap receipt {index} binding is invalid")
        if receipt.get("authority_receipt") != gap_set.get("authority_receipt"):
            raise WorkflowError(f"domain capability gap receipt {index} authority binding is invalid")
        gap = receipt.get("gap")
        receipt_approval = receipt.get("approval")
        if not isinstance(gap, Mapping) or gap.get("new_primitive_required") is not False or gap.get("new_domain_capability_required") is not True or receipt.get("proposed_primitive") is not None:
            raise WorkflowError(f"domain capability gap receipt {index} semantics are invalid")
        if not isinstance(receipt_approval, Mapping) or receipt_approval.get("status") != "review-required":
            raise WorkflowError(f"domain capability gap receipt {index} is not awaiting review")
        receipts.append((receipt, receipt_bytes, receipt_path))
    return gap_set, receipts


def approve_gap_set(
    path: Path,
    *,
    actor: str,
    rationale: str,
    candidate_contribution: Path,
    output: Path,
) -> dict[str, Any]:
    if actor != "architect":
        raise WorkflowError("domain capability gap approval must be exercised by the Architect role")
    if not rationale.strip():
        raise WorkflowError("domain capability gap approval requires a rationale")
    source_path = path.expanduser().resolve()
    destination = output.expanduser().resolve()
    if source_path == destination:
        raise WorkflowError("domain capability gap approval must preserve the original review evidence")
    if destination.exists():
        raise WorkflowError(f"approved domain capability gap set already exists: {destination}")
    gap_set, receipts = _validate_review_gap_set(source_path)
    candidate_binding = _candidate_binding(gap_set, candidate_contribution)
    destination.parent.mkdir(parents=True, exist_ok=True)
    writer = AtomicFileWriter((destination.parent,))
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    approved_items: list[dict[str, Any]] = []
    for index, ((receipt, original_bytes, original_path), item) in enumerate(zip(receipts, gap_set["gaps"], strict=True), 1):
        approved_receipt = json.loads(json.dumps(receipt))
        approved_receipt["approval"] = {
            "status": "approved",
            "reviewed_by": actor,
            "reviewed_at": reviewed_at,
            "rationale": rationale.strip(),
        }
        evidence = list(approved_receipt.get("evidence_references", []))
        evidence.extend(
            (
                f"review-source:{original_path}",
                f"review-source-sha256:{_sha256(original_bytes)}",
                f"candidate-request-sha256:{candidate_binding['request_sha256']}",
                f"candidate-contribution-sha256:{candidate_binding['contribution_sha256']}",
                f"semantic-understanding-sha256:{candidate_binding['semantic_understanding_sha256']}",
                f"semantic-confirmation-sha256:{candidate_binding['semantic_confirmation_sha256']}",
                f"authority-receipt-sha256:{candidate_binding['authority_receipt_sha256']}",
            )
        )
        approved_receipt["evidence_references"] = list(dict.fromkeys(evidence))
        receipt_path = destination.with_name(
            f"{destination.stem}-gap-{index:03d}.json"
        )
        receipt_text = json.dumps(approved_receipt, indent=4, sort_keys=False) + "\n"
        writer.write_text(receipt_path, receipt_text, new_mode=0o600)
        approved_items.append(
            {
                "required_capability": item["required_capability"],
                "gap_receipt": str(receipt_path),
                "gap_receipt_sha256": _sha256(receipt_text.encode("utf-8")),
            }
        )
    approved_set = json.loads(json.dumps(gap_set))
    approved_set["gaps"] = approved_items
    approved_set["gap_count"] = len(approved_items)
    approved_set["approval"] = {
        "status": "approved",
        "reviewed_by": actor,
        "reviewed_at": reviewed_at,
        "rationale": rationale.strip(),
    }
    writer.write_text(
        destination,
        json.dumps(approved_set, indent=4, sort_keys=False) + "\n",
        new_mode=0o600,
    )
    return {
        "status": "approved",
        "approved_gap_set": str(destination),
        "gap_count": len(approved_items),
        "required_capabilities": [item["required_capability"] for item in approved_items],
        "review_source": str(source_path),
        "candidate_binding": candidate_binding,
    }


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-domain-gap-approval-") as raw:
        root = Path(raw)
        authority_path = root / "authority.json"
        authority = {
            "schema_version": "1.0",
            "request": "fixture request",
            "semantic_authority": {
                "semantic_understanding_sha256": "1" * 64,
                "semantic_confirmation_sha256": "2" * 64,
            },
        }
        authority_path.write_text(json.dumps(authority, indent=4) + "\n", encoding="utf-8")
        candidate_path = root / "candidate.zip"
        candidate_path.write_bytes(b"fixture candidate")
        receipt_path = root / "gap.json"
        receipt = {
            "schema_version": "1.1",
            "gap_id": "SAGE-GAP-20260818-DOMAIN-001",
            "request": "fixture request",
            "created_at": "2026-08-18T00:00:00-05:00",
            "authority_receipt": str(authority_path),
            "component_manifest": "fixture-components.json",
            "required_capability": "fixture.capability",
            "gap_kind": "domain-capability",
            "candidates_considered": [{
                "component_id": "fixture",
                "version": "1.0.0",
                "source_path": "fixture.py",
                "insufficiency": "missing domain behavior",
                "composition_can_close_gap": False,
            }],
            "gap": {
                "missing_interface_or_behavior": "fixture behavior",
                "why_configuration_is_insufficient": "fixture",
                "why_composition_is_insufficient": "fixture",
                "new_primitive_required": False,
                "new_domain_capability_required": True,
            },
            "proposed_primitive": None,
            "approval": {
                "status": "review-required",
                "reviewed_by": None,
                "reviewed_at": None,
                "rationale": "fixture review",
            },
            "evidence_references": ["fixture"],
        }
        receipt_bytes = (json.dumps(receipt, indent=4) + "\n").encode("utf-8")
        receipt_path.write_bytes(receipt_bytes)
        gap_set_path = root / "gap-set.json"
        gap_set = {
            "schema_version": "1.0",
            "record_type": "sage-domain-capability-gap-set",
            "request": "fixture request",
            "created_at": "2026-08-18T00:00:00-05:00",
            "authority_receipt": str(authority_path),
            "component_manifest": "fixture-components.json",
            "gap_count": 1,
            "gaps": [{
                "required_capability": "fixture.capability",
                "gap_receipt": str(receipt_path),
                "gap_receipt_sha256": _sha256(receipt_bytes),
            }],
            "approval": {
                "status": "review-required",
                "reviewed_by": None,
                "reviewed_at": None,
                "rationale": "fixture review",
            },
        }
        original_set = (json.dumps(gap_set, indent=4) + "\n").encode("utf-8")
        gap_set_path.write_bytes(original_set)
        output = root / "approved.json"
        result = approve_gap_set(
            gap_set_path,
            actor="architect",
            rationale="Approve one coherent fixture remediation.",
            candidate_contribution=candidate_path,
            output=output,
        )
        if result["required_capabilities"] != ["fixture.capability"]:
            raise RuntimeError("approved capability set changed")
        if result["candidate_binding"]["contribution_sha256"] != _sha256(candidate_path.read_bytes()):
            raise RuntimeError("approved gap set did not bind the exact staged candidate")
        if gap_set_path.read_bytes() != original_set or receipt_path.read_bytes() != receipt_bytes:
            raise RuntimeError("review evidence was rewritten")
        approved, _ = _load_object(output, "approved fixture gap set")
        if approved["approval"]["status"] != "approved":
            raise RuntimeError("approved gap set status was not recorded")
        if "candidate_binding" in approved:
            raise RuntimeError("strict gap-set schema was expanded with unsupported fields")
        copied, _ = _load_object(Path(approved["gaps"][0]["gap_receipt"]), "approved fixture gap receipt")
        if copied["approval"]["status"] != "approved":
            raise RuntimeError("approved gap receipt status was not recorded")
        expected_binding_evidence = {
            f"candidate-request-sha256:{result['candidate_binding']['request_sha256']}",
            f"candidate-contribution-sha256:{result['candidate_binding']['contribution_sha256']}",
            f"semantic-understanding-sha256:{result['candidate_binding']['semantic_understanding_sha256']}",
            f"semantic-confirmation-sha256:{result['candidate_binding']['semantic_confirmation_sha256']}",
            f"authority-receipt-sha256:{result['candidate_binding']['authority_receipt_sha256']}",
        }
        if not expected_binding_evidence.issubset(set(copied.get("evidence_references", []))):
            raise RuntimeError("approved gap receipt lacks exact candidate binding evidence")
        try:
            approve_gap_set(
                gap_set_path,
                actor="operator",
                rationale="bad",
                candidate_contribution=candidate_path,
                output=root / "bad.json",
            )
        except WorkflowError:
            pass
        else:
            raise RuntimeError("non-Architect domain gap approval was accepted")
    print("PASS domain-capability gap review evidence remains immutable")
    print("PASS approved copies preserve exact receipt binding and Architect rationale")
    print("PASS approval binds exact staged contribution and semantic authority")
    print("PASS non-Architect approval fails closed")
    print("Kalaxy3 SAGE domain capability gap approval self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-set", type=Path)
    parser.add_argument("--actor")
    parser.add_argument("--rationale")
    parser.add_argument("--candidate-contribution", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    if (
        args.gap_set is None
        or args.candidate_contribution is None
        or args.output is None
        or not args.actor
        or not args.rationale
    ):
        raise WorkflowError(
            "--gap-set, --actor, --rationale, --candidate-contribution, and --output are required"
        )
    result = approve_gap_set(
        args.gap_set,
        actor=args.actor,
        rationale=args.rationale,
        candidate_contribution=args.candidate_contribution,
        output=args.output,
    )
    print("Kalaxy3 SAGE domain capability gap approval: PASS")
    print(json.dumps(result, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, RuntimeError, WorkflowError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE domain capability gap approval: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
