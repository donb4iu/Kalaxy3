#!/usr/bin/env python3
"""Projection versioning, lifecycle state and fail-closed governance for SAGE."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable


def stable_digest(value: Any) -> str:
    """Compute a reproducible SHA-256 checksum for JSON-compatible records.

    Args:
        value: JSON-compatible value.
    """
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def projection_id(payload: dict[str, Any]) -> str:
    """Bind one projection identity to source revision and full inputs.

    Args:
        payload: Prepared projection candidate.
    """
    revision, checksum = payload['revision'], payload['fingerprint']
    if len(revision) != 40 or len(checksum) != 64:
        raise ValueError('invalid source revision or input checksum')
    return f'{revision}:{checksum[:20]}'


def evaluate_presence(concept: str, edges: list[dict[str, Any]],
                      qualified_scope: bool) -> str:
    """Distinguish candidate matches from qualified evidence presence.

    Args:
        concept: Semantic concept identifier.
        edges: Linked candidate and established relationships.
        qualified_scope: Whether the source universe and mappings were qualified.
    """
    if any(edge['concept'] == concept and edge['state'] == 'established'
           for edge in edges):
        return 'evidence_found'
    if not qualified_scope:
        return 'not_evaluated'
    if any(edge['concept'] == concept for edge in edges):
        return 'not_evaluated'
    return 'none_found_in_qualified_scope'


def ensure_lossless(sources: list[dict[str, Any]],
                    expected_paths: set[str]) -> None:
    """Reject missing or altered source universe, independent of semantics.

    Args:
        sources: Actual indexed source nodes.
        expected_paths: Independently enumerated Git-tree paths.
    """
    paths = [item['path'] for item in sources]
    if set(paths) != expected_paths or len(paths) != len(expected_paths):
        raise ValueError('SOURCE_UNIVERSE_LOSS_OR_DUPLICATION')
    if any(not item.get('identity') or not item.get('git_oid') for item in sources):
        raise ValueError('SOURCE_PROVENANCE_MISSING')


def ensure_reverse_links(edges: list[dict[str, Any]],
                         source_to_concepts: dict[str, set[str]],
                         concept_to_sources: dict[str, set[str]]) -> None:
    """Check both exact directions against independently expected relationships.

    Args:
        edges: Expected source-concept links.
        source_to_concepts: Observed reverse retrieval.
        concept_to_sources: Observed forward retrieval.
    """
    for edge in edges:
        source, concept = edge['source_id'], edge['concept']
        if (concept not in source_to_concepts.get(source, set()) or
                source not in concept_to_sources.get(concept, set())):
            raise ValueError('LOSSY_BIDIRECTIONAL_RETRIEVAL')


def verify_patch(patch: dict[str, Any],
                 before: dict[str, Any], after: dict[str, Any]) -> None:
    """Validate a bounded revisioned patch without granting semantic authority.

    Args:
        patch: Governed patch record and list of authorized changed paths.
        before: Pinned evidence universe before the model correction.
        after: Pinned evidence universe after the model correction.
    """
    for field in ('gap_id', 'rationale', 'governed_source_ref'):
        if not isinstance(patch.get(field), str) or not patch[field].strip():
            raise ValueError(f'break-glass patch omits {field}')
    allowed = set(patch.get('allowed_changed_paths', []))
    if not allowed or not all(isinstance(path, str) for path in allowed):
        raise ValueError('break-glass patch requires explicit changed paths')
    old = {row['path']: row for row in before['sources']}
    new = {row['path']: row for row in after['sources']}
    if old.keys() != new.keys():
        raise ValueError('BREAK_GLASS_SOURCE_UNIVERSE_LOSS')
    changed = {path for path in old if
               old[path]['content_sha256'] != new[path]['content_sha256']}
    if not changed or not changed <= allowed:
        raise ValueError('BREAK_GLASS_UNAUTHORIZED_SOURCE_MUTATION')
    if before['fingerprint'] == after['fingerprint']:
        raise ValueError('break-glass patch made no projection change')


def activation_gate(receipt: dict[str, Any], expected_id: str,
                    qualified: dict[str, Any],
                    authority_verifier: Callable[[dict[str, Any]], bool]) -> None:
    """Only a trusted, externally enforced SAGE verifier may grant activation.

    Args:
        receipt: Verifier-controlled authoritative promotion receipt.
        expected_id: Version-qualified projection identifier.
        qualified: Independent acceptance evidence.
        authority_verifier: Existing SAGE authority check, not an LLM predicate.
    """
    if not authority_verifier(receipt):
        raise PermissionError('EXTERNAL_PROMOTION_AUTHORITY_REQUIRED')
    if receipt.get('projection_id') != expected_id:
        raise PermissionError('PROMOTION_REVISION_MISMATCH')
    if qualified.get('all_mandatory_dod_passed') is not True:
        raise PermissionError('UNQUALIFIED_SEMANTIC_PROJECTION')
    if qualified.get('projection_id') != expected_id:
        raise PermissionError('QUALIFICATION_VERSION_MISMATCH')


def receipt_path(output: Path, payload: dict[str, Any]) -> Path:
    """Write a metadata-only, non-authoritative evidence receipt.

    Args:
        output: Isolated operator evidence folder.
        payload: Non-secret receipt contents.
    """
    output.mkdir(parents=True, exist_ok=True)
    path = output / 'projection-receipt.json'
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', 'utf-8')
    path.chmod(0o600)
    return path
