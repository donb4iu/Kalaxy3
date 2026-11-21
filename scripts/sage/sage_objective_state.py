"""Evidence-bound objective-state evaluation for bounded SAGE work proposals."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

OBJECTIVE = "#50"
GRAPH_REVISION = "5e15f72d95827e026637cf4161048b7afbc8072e"
PINNED_CAPABILITY = "source_metadata_identity"
UNKNOWN_OBLIGATIONS = frozenset({
    "concept_obligation_coverage", "semantic_relationship_fidelity",
    "tri_state_evidence_presence", "bidirectional_semantic_retrieval",
    "independent_relevance_quality", "governed_rebuild",
    "lifecycle_promotion_recovery", "bounded_model_repair",
})
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceError(ValueError):
    """Indicate a missing, malformed, or unverified evidence boundary."""


def read_object(path: Path) -> dict[str, Any]:
    """Read a JSON object from a known local file.

    Args:
        path: Existing local file path.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise EvidenceError(f"Expected JSON object: {path}")
    return data


def sha256_file(path: Path) -> str:
    """Return SHA-256 of exact artifact bytes.

    Args:
        path: Existing local file path.
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receipt(receipt_path: Path, manifest_path: Path) -> dict[str, Any]:
    """Bind #55 native receipt to the earlier local episode and exact scope.

    Args:
        receipt_path: Native read-only Issue #55 summary.
        manifest_path: Earlier episode's digest-bearing manifest.
    """
    receipt = read_object(receipt_path)
    manifest = read_object(manifest_path)
    expected = manifest.get("issue55_receipt_sha256")
    if not isinstance(expected, str) or not HEX64.fullmatch(expected):
        raise EvidenceError("Prior episode lacks a valid receipt digest")
    if sha256_file(receipt_path) != expected:
        raise EvidenceError("Native #55 receipt bytes differ from prior episode")
    if manifest.get("graph_revision") != GRAPH_REVISION:
        raise EvidenceError("Episode's #55 graph revision differs")
    expected_flags = {
        "graph_revision": GRAPH_REVISION, "graph_page_incomplete": False,
        "semantic_relevance_qualified": False, "complete_context_claim": False,
    }
    if any(receipt.get(key) != value for key, value in expected_flags.items()):
        raise EvidenceError("Native #55 receipt has unexpected scope or flags")
    audit = receipt.get("full_graph_inventory_reconciliation")
    if not isinstance(audit, dict):
        raise EvidenceError("Native #55 full inventory check is missing")
    if audit.get("git_blob_count") != 1388 or audit.get("graph_inventory_count") != 1388:
        raise EvidenceError("Native #55 source counts differ")
    if audit.get("exact_source_identity_and_digest_equivalence") is not True:
        raise EvidenceError("Native #55 source equivalence is not established")
    mismatches = ("missing_graph_paths", "non_git_graph_paths",
                  "git_oid_disagreements", "sha256_disagreements")
    if any(audit.get(key) != [] for key in mismatches):
        raise EvidenceError("Native #55 source mismatch/unknown exists")
    return {"capability": PINNED_CAPABILITY, "state": "validated",
            "source_revision": GRAPH_REVISION, "receipt_sha256": expected,
            "evidence_id": "ST-ISS55-RECEIPT", "source_count": 1388,
            "scope": "source_identity_and_digest_only",
            "semantic_coverage_state": "unknown",
            "acceptance_authority": "none_conferred_by_this_checker"}


def git_output(repo: Path, *arguments: str) -> bytes:
    """Execute a non-mutating Git inspection command.

    Args:
        repo: Local Git checkout.
        arguments: Explicit read-only Git arguments.
    """
    result = subprocess.run(["git", "-C", str(repo), *arguments],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            check=False, timeout=40)
    if result.returncode:
        raise EvidenceError("Required Git revision unavailable or unreadable")
    return result.stdout


def tracked_blobs(repo: Path, revision: str) -> dict[bytes, bytes]:
    """Enumerate Git blob path-to-OID identities at an exact commit.

    Args:
        repo: Local repository with the required object.
        revision: Full 40-digit Git commit ID.
    """
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        raise EvidenceError("A complete Git commit SHA-1 is required")
    commit = git_output(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if commit.decode("ascii").strip() != revision:
        raise EvidenceError("Git revision is not an exact commit identity")
    entries = git_output(repo, "ls-tree", "-r", "-z", revision).split(b"\0")
    mapping: dict[bytes, bytes] = {}
    for entry in entries:
        if not entry:
            continue
        identity, separator, path = entry.partition(b"\t")
        fields = identity.split(b" ")
        if not separator or len(fields) != 3:
            raise EvidenceError("Malformed Git inventory record")
        if fields[1] == b"blob":
            mapping[path] = fields[2]
    return mapping


def changed_scope(repo: Path, old_revision: str,
                  new_revision: str) -> dict[str, Any]:
    """Measure tracked source identity changes without mutating Git.

    Args:
        repo: Git checkout containing both revisions.
        old_revision: Previously validated exact source revision.
        new_revision: Proposed revision needing fresh validation.
    """
    before = tracked_blobs(repo, old_revision)
    after = tracked_blobs(repo, new_revision)
    changes = {path for path in before.keys() | after.keys()
               if before.get(path) != after.get(path)}
    return {"changed_blob_identities": len(changes),
            "old_source_count": len(before), "new_source_count": len(after),
            "changed_path_sample": [p.decode("utf-8", errors="replace")
                                    for p in sorted(changes)[:12]]}


def decision(status: str, capability: str, reason: str,
             evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a deterministic, non-authorizing action disposition.

    Args:
        status: Candidate/blocked/unverified status.
        capability: Targeted capability identifier.
        reason: Exact boundary or evidence deficiency.
        evidence: Optional verified diagnostic details.
    """
    return {"status": status, "capability": capability, "reason": reason,
            "evidence": dict(evidence or {}), "architect_authorization": False,
            "effect": "no_execution_or_approval"}


def evaluate(proposal: Mapping[str, Any], state: Mapping[str, Any],
             repo: Path) -> dict[str, Any]:
    """Reject redundant metadata work and distinguish unknown obligations.

    Args:
        proposal: Untrusted LLM/operator candidate action.
        state: Locally verified, bounded source-accounting observation.
        repo: Git checkout for exact revision-delta inspection.
    """
    capability = proposal.get("capability")
    action = proposal.get("action")
    revision = proposal.get("target_revision")
    if proposal.get("objective") != OBJECTIVE:
        return decision("blocked", str(capability), "Objective ID mismatch")
    if not isinstance(revision, str) or not HEX40.fullmatch(revision):
        return decision("blocked", str(capability), "Missing exact target revision")
    if capability in UNKNOWN_OBLIGATIONS:
        if action != "validate":
            return decision("blocked", capability, "Unknown state cannot authorize implementation")
        if revision != state["source_revision"]:
            try:
                tracked_blobs(repo, revision)
            except (EvidenceError, OSError, subprocess.TimeoutExpired) as exc:
                return decision("unverified", capability, str(exc))
        return decision("candidate", capability,
                        "Unverified obligation: bounded validation candidate, not approved")
    if capability != PINNED_CAPABILITY:
        return decision("blocked", str(capability), "Capability absent from bounded contract")
    if action not in ("validate", "revalidate"):
        return decision("blocked", capability, "Validated capability cannot be implicitly reopened")
    if revision == state["source_revision"]:
        return decision("blocked_repeat", capability,
                        "Already validated at this exact source revision", state)
    try:
        delta = changed_scope(repo, state["source_revision"], revision)
    except (EvidenceError, OSError, subprocess.TimeoutExpired) as exc:
        return decision("unverified", capability, str(exc))
    if delta["changed_blob_identities"] == 0:
        return decision("blocked_repeat", capability,
                        "New commit has identical tracked source blob identities", delta)
    return decision("candidate_new_scope", capability,
                    "Verified source-universe change; new revision requires distinct validation",
                    delta)


def evaluate_all(proposals: list[Any], state: Mapping[str, Any],
                 repo: Path) -> dict[str, Any]:
    """Evaluate a bounded candidate action batch, preserving every outcome.

    Args:
        proposals: At most twenty untrusted action candidates.
        state: Verified source-accounting record.
        repo: Local read-only Git source.
    """
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 20:
        raise EvidenceError("Expected between one and twenty proposals")
    if any(not isinstance(item, dict) for item in proposals):
        raise EvidenceError("All proposals must be JSON objects")
    decisions = [evaluate(item, state, repo) for item in proposals]
    return {"schema": "sage-objective-state-gate-v1", "objective": OBJECTIVE,
            "verified_state": dict(state), "proposals": decisions,
            "no_execution": True, "no_new_approval_gate": True,
            "architect_acceptance": "not_evaluated"}
