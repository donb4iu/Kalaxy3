#!/usr/bin/env python3
"""Verify a signed SAGE prior-art inquiry without asserting retrieval completeness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

SCHEMA = "sage-semantic-inquiry-attestation-v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
REVISION = re.compile(r"[0-9a-f]{40}\Z")


class InquiryError(ValueError):
    """Indicate missing or untrusted inquiry provenance."""


def canonical(value: Mapping[str, Any]) -> bytes:
    """Encode exactly the same deterministic UTF-8 bytes for signing.

    Args:
        value: JSON inquiry receipt to be independently attested.
    """
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def require_text(value: Any, name: str) -> str:
    """Accept bounded, nonempty textual evidence identifiers.

    Args:
        value: Untrusted field.
        name: Field name for diagnostics.
    """
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 2048:
        raise InquiryError(f"Missing or oversized {name}")
    return value.strip()


def validate_record(value: Any) -> dict[str, Any]:
    """Validate an inquiry's scope without evaluating result relevance.

    Args:
        value: Decoded independent-retrieval-controller receipt.
    """
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise InquiryError("Invalid inquiry attestation schema")
    for key in ("objective", "milestone", "proposal_sha256", "collection_revision",
                "search_scope", "retriever", "attester_role"):
        require_text(value.get(key), key)
    if value["attester_role"] != "semantic-retrieval-controller":
        raise InquiryError("Unexpected evidence attester role")
    if not SHA256.fullmatch(value["proposal_sha256"]):
        raise InquiryError("Invalid proposal digest")
    if not REVISION.fullmatch(value["collection_revision"]):
        raise InquiryError("Invalid collection Git revision")
    entries = value.get("inquiries")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 20:
        raise InquiryError("At least one bounded inquiry is required")
    for entry in entries:
        if not isinstance(entry, dict):
            raise InquiryError("Invalid inquiry entry")
        require_text(entry.get("question"), "inquiry question")
        results = entry.get("returned")
        if not isinstance(results, list) or len(results) > 100:
            raise InquiryError("Invalid returned result list")
        if any(not isinstance(ref, str) or not ref.strip() for ref in results):
            raise InquiryError("Invalid source reference")
    return value


def verify_signature(receipt: Path, signature: Path, key: Path) -> None:
    """Check a raw RSA SHA-256 signature using trusted-base public key bytes.

    Args:
        receipt: Canonical signed JSON file.
        signature: Binary signature file.
        key: Independently provisioned trusted public key.
    """
    if not key.is_file() or not signature.is_file():
        raise InquiryError("Trusted public key or signature is absent")
    result = subprocess.run(
        ["openssl", "dgst", "-sha256", "-verify", str(key),
         "-signature", str(signature), str(receipt)],
        capture_output=True, check=False, timeout=15,
    )
    if result.returncode:
        raise InquiryError("Inquiry signature invalid under trusted authority")


def verify_inquiry(receipt: Path, signature: Path, trusted_key: Path,
                   objective: str, milestone: str, proposal: Path,
                   revision: str) -> dict[str, Any]:
    """Check cryptographic integrity and exact proposal/collection bindings.

    Args:
        receipt: Semantic inquiry receipt.
        signature: Signature produced by separately controlled retriever.
        trusted_key: Public key admitted in trusted Git base, never PR head.
        objective: Required objective identifier.
        milestone: Required milestone identifier.
        proposal: Exact bytes of iterated milestone proposal.
        revision: Semantic collection Git revision independently expected by caller.
    """
    data = receipt.read_bytes()
    if len(data) > 131072:
        raise InquiryError("Inquiry receipt too large")
    try:
        value = validate_record(json.loads(data))
    except (ValueError, UnicodeDecodeError) as exc:
        raise InquiryError(f"Invalid inquiry record: {exc}") from exc
    if data != canonical(value):
        raise InquiryError("Inquiry receipt must be canonical JSON")
    if value["objective"] != objective or value["milestone"] != milestone:
        raise InquiryError("Inquiry scope differs from proposed milestone")
    if value["collection_revision"] != revision:
        raise InquiryError("Inquiry refers to different semantic collection revision")
    if hashlib.sha256(proposal.read_bytes()).hexdigest() != value["proposal_sha256"]:
        raise InquiryError("Proposed approach changed since inquiry")
    verify_signature(receipt, signature, trusted_key)
    return {"status": "attested_inquiry_recorded", "sha256": hashlib.sha256(data).hexdigest(),
            "collection_revision": revision, "objective": objective,
            "milestone": milestone, "inquiry_count": len(value["inquiries"]),
            "result_count": sum(len(item["returned"]) for item in value["inquiries"]),
            "guarantee": "signature_and_scope_only; not_retrieval_completeness_or_relevance",
            "authority": "does_not_authorize_implementation_or_pr_merge"}


def main() -> None:
    """Run the independent inquiry gate in a trusted CI execution context."""
    cli = argparse.ArgumentParser(description=__doc__)
    for name in ("receipt", "signature", "trusted-key", "proposal", "output"):
        cli.add_argument(f"--{name}", type=Path, required=True)
    for name in ("objective", "milestone", "collection-revision"):
        cli.add_argument(f"--{name}", required=True)
    args = cli.parse_args()
    result = verify_inquiry(args.receipt, args.signature, args.trusted_key,
                            args.objective, args.milestone, args.proposal,
                            args.collection_revision)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("STATUS=PRIOR_ART_INQUIRY_ATTESTATION_VERIFIED")
    print("SEMANTIC_RELEVANCE=NOT_ASSERTED; PR_PROMOTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
