#!/usr/bin/env python3
"""Project explicit, source-attested relationship claims without qualifying them."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import bounded_committed_text, digest

REGISTRY = 'sage-neo4j-relationship-claims.json'
GLOBAL_SCOPE = 'kalaxy3_implementation'
SOURCE_SCOPE = 'source_to_source'
RELATION_KINDS = frozenset({
    'applicable_to', 'decision_about', 'alternative_considered',
    'alternative_rejected', 'supersedes', 'depends_on',
    'supports', 'contradicts',
})
MAX_CLAIMS = 512
MAX_QUOTE_LINES = 5
CLAIM_ID = re.compile(r'^[a-z][a-z0-9._-]{3,80}$')


def validate_shape(claim: dict[str, Any], paths: set[str]) -> None:
    """Enforce bounded, explicit claim endpoints and a closed relation vocabulary.

    Args:
        claim: One untrusted JSON relationship declaration.
        paths: Complete set of pinned Git source paths.
    """
    required = {'id', 'kind', 'scope', 'subject_path', 'object_path',
                'evidence_path', 'start_line', 'quote'}
    if set(claim) != required or not isinstance(claim['id'], str):
        raise ValueError('INVALID_RELATIONSHIP_CLAIM_SHAPE')
    if (not CLAIM_ID.fullmatch(claim['id']) or
            not isinstance(claim['kind'], str) or
            claim['kind'] not in RELATION_KINDS):
        raise ValueError('INVALID_RELATIONSHIP_CLAIM_TYPE')
    if (not isinstance(claim['subject_path'], str) or
            not isinstance(claim['evidence_path'], str) or
            claim['subject_path'] not in paths or
            claim['evidence_path'] not in paths):
        raise ValueError('RELATIONSHIP_CLAIM_SOURCE_MISSING')
    if claim['kind'] == 'applicable_to':
        if claim['scope'] != GLOBAL_SCOPE or claim['object_path'] is not None:
            raise ValueError('INVALID_GLOBAL_APPLICABILITY_SCOPE')
    elif (claim['scope'] != SOURCE_SCOPE or
          not isinstance(claim['object_path'], str) or
          claim['object_path'] not in paths):
        raise ValueError('INVALID_SOURCE_RELATIONSHIP_SCOPE')
    if type(claim['start_line']) is not int or claim['start_line'] < 1:
        raise ValueError('INVALID_RELATIONSHIP_EVIDENCE_LINE')
    if not isinstance(claim['quote'], str) or not claim['quote'].strip():
        raise ValueError('RELATIONSHIP_EVIDENCE_QUOTE_REQUIRED')
    if not 1 <= len(claim['quote'].splitlines()) <= MAX_QUOTE_LINES:
        raise ValueError('RELATIONSHIP_EVIDENCE_SPAN_TOO_LARGE')


def validate_quote(repo: Path, source: dict[str, Any],
                   claim: dict[str, Any]) -> None:
    """Require an exact quote from Git-committed source lines, not worktree text.

    Args:
        repo: Repository containing the pinned Git objects.
        source: Exact evidence-path entry in the revision-qualified inventory.
        claim: Relationship declaration with a literal quote and start line.
    """
    body = bounded_committed_text(repo, source)
    if body is None:
        raise ValueError('RELATIONSHIP_EVIDENCE_NOT_BOUNDED_TEXT')
    lines = body.splitlines()
    quote = claim['quote'].splitlines()
    start = claim['start_line'] - 1
    if lines[start:start + len(quote)] != quote:
        raise ValueError('RELATIONSHIP_EVIDENCE_QUOTE_MISMATCH')


def pinned_claims(repo: Path, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Load optional claim registry from Git and bind every claim to source bytes.

    Args:
        repo: Git repository containing the source revision.
        sources: Lossless Git inventory for exactly one revision.
    """
    by_path = {row['path']: row for row in sources}
    registry = by_path.get(REGISTRY)
    if registry is None:
        return []
    text = bounded_committed_text(repo, registry)
    if text is None:
        raise ValueError('RELATIONSHIP_REGISTRY_NOT_READABLE')
    try:
        document = json.loads(text)
    except (UnicodeError, ValueError) as exc:
        raise ValueError('RELATIONSHIP_REGISTRY_INVALID_JSON') from exc
    if not isinstance(document, dict) or set(document) != {'version', 'claims'}:
        raise ValueError('RELATIONSHIP_REGISTRY_INVALID_SHAPE')
    rows = document['claims']
    if type(document['version']) is not int or document['version'] != 1:
        raise ValueError('RELATIONSHIP_REGISTRY_UNSUPPORTED_VERSION')
    if not isinstance(rows, list) or len(rows) > MAX_CLAIMS:
        raise ValueError('RELATIONSHIP_REGISTRY_INVALID_COUNT')
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('INVALID_RELATIONSHIP_CLAIM_SHAPE')
        validate_shape(row, set(by_path))
        if row['id'] in seen:
            raise ValueError('DUPLICATE_RELATIONSHIP_CLAIM_ID')
        seen.add(row['id'])
        evidence = by_path[row['evidence_path']]
        validate_quote(repo, evidence, row)
        output.append({**{key: row[key] for key in row if key != 'quote'},
                       'identity': digest((registry['revision'] + '\0' + row['id']).encode()),
                       'subject_id': by_path[row['subject_path']]['identity'],
                       'object_id': (by_path[row['object_path']]['identity']
                                     if row['object_path'] is not None else None),
                       'evidence_id': evidence['identity'],
                       'evidence_sha256': evidence['content_sha256'],
                       'quote_sha256': digest(row['quote'].encode('utf-8')),
                       'attestation': 'registered_type_exact_committed_quote',
                       'semantic_qualification': 'not_evaluated'})
    return sorted(output, key=lambda item: item['id'])
