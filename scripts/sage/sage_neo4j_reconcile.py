#!/usr/bin/env python3
"""Read-only source-revision reconciliation for the SAGE Neo4j query projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import (candidate_edges, concept_records, git_output,
                                  source_records)


def committed_model(repo: Path, revision: str) -> list[dict[str, Any]]:
    """Load SAGE's governed concept configuration at an exact Git revision.

    Args:
        repo: Repository containing canonical SAGE vocabulary.
        revision: Full, resolved commit identifier.
    """
    data = git_output(repo, 'show', f'{revision}:sage-semantic-concepts.json')
    return concept_records(json.loads(data.decode('utf-8')))


def revision_inventory(repo: Path, revision: str) -> dict[str, Any]:
    """Read a committed source universe and candidate edges without mutation.

    Args:
        repo: Valid Git repository checkout.
        revision: Exact committed source revision.
    """
    resolved = git_output(repo, 'rev-parse', '--verify', revision + '^{commit}')
    canonical = resolved.decode().strip()
    sources = source_records(repo, canonical)
    concepts = committed_model(repo, canonical)
    return {'revision': canonical, 'sources': sources, 'concepts': concepts,
            'candidate_edges': candidate_edges(sources, concepts)}


def compare_sources(before: list[dict[str, Any]],
                    after: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Classify all path changes while retaining revision-specific identities.

    Args:
        before: Complete source records from the previous revision.
        after: Complete source records from the candidate revision.
    """
    old = {row['path']: row for row in before}
    new = {row['path']: row for row in after}
    if len(old) != len(before) or len(new) != len(after):
        raise ValueError('RECONCILIATION_DUPLICATE_SOURCE_PATH')
    changed = sorted(path for path in old.keys() & new.keys()
                     if old[path]['content_sha256'] != new[path]['content_sha256']
                     or old[path]['mode'] != new[path]['mode'])
    return {'added': sorted(new.keys() - old.keys()),
            'removed': sorted(old.keys() - new.keys()),
            'modified': changed,
            'unchanged': sorted(old.keys() & new.keys() - set(changed))}


def candidate_pairs(universe: dict[str, Any]) -> set[tuple[str, str]]:
    """Return comparable non-authoritative candidate links using source paths.

    Args:
        universe: Revision-specific inventory with candidate edges.
    """
    paths = {row['identity']: row['path'] for row in universe['sources']}
    return {(paths[edge['source_id']], edge['concept'])
            for edge in universe['candidate_edges']}


def reconcile(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Produce version-bound delta evidence without changing the active index.

    Args:
        before: Complete predecessor source and concept inventory.
        after: Complete candidate source and concept inventory.
    """
    changes = compare_sources(before['sources'], after['sources'])
    old_edges = candidate_pairs(before)
    new_edges = candidate_pairs(after)
    identity = hashlib.sha256(json.dumps({
        'before': before['revision'], 'after': after['revision'],
        'changes': changes, 'added_candidates': sorted(new_edges - old_edges),
        'removed_candidates': sorted(old_edges - new_edges),
    }, sort_keys=True).encode()).hexdigest()
    return {'record_type': 'sage-neo4j-source-reconciliation',
            'previous_revision': before['revision'],
            'candidate_revision': after['revision'],
            'before_count': len(before['sources']),
            'after_count': len(after['sources']),
            'source_changes': changes,
            'new_candidate_links': sorted(new_edges - old_edges),
            'removed_candidate_links': sorted(old_edges - new_edges),
            'digest': identity,
            'semantic_relationships_established': 0,
            'active_projection_mutated': False,
            'promotion_authorized': False}
