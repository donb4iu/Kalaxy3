#!/usr/bin/env python3
"""Read-only, version-qualified source reconciliation for SAGE Neo4j."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import (candidate_edges, concept_records, git_output,
                                  source_records)

MODEL_PATH = 'sage-semantic-concepts.json'
MODEL_AVAILABLE = 'available_at_revision'
MODEL_ABSENT = 'not_evaluated_model_absent_at_revision'


def committed_model(repo: Path, revision: str) -> tuple[list[dict[str, Any]], str]:
    """Read a revision's own vocabulary; distinguish absence from invalidity.

    Args:
        repo: Valid source repository.
        revision: Fully resolved source commit identifier.
    """
    listing = git_output(repo, 'ls-tree', '--name-only', revision, '--', MODEL_PATH)
    if not listing.strip():
        return [], MODEL_ABSENT
    if listing.decode('utf-8').strip() != MODEL_PATH:
        raise ValueError('UNEXPECTED_COMMITTED_CONCEPT_MODEL_PATH')
    data = git_output(repo, 'show', f'{revision}:{MODEL_PATH}')
    return concept_records(json.loads(data.decode('utf-8'))), MODEL_AVAILABLE


def revision_inventory(repo: Path, revision: str) -> dict[str, Any]:
    """Inventory all committed sources, keeping unavailable semantics explicit.

    Args:
        repo: Valid Git repository checkout.
        revision: Commit or ref to resolve to an exact revision.
    """
    resolved = git_output(repo, 'rev-parse', '--verify', revision + '^{commit}')
    canonical = resolved.decode().strip()
    sources = source_records(repo, canonical)
    concepts, model_state = committed_model(repo, canonical)
    return {'revision': canonical, 'sources': sources, 'concepts': concepts,
            'model_state': model_state,
            'candidate_edges': candidate_edges(sources, concepts)}


def compare_sources(before: list[dict[str, Any]],
                    after: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Classify every source change including adds, removals, and modifications.

    Args:
        before: Previous committed source records.
        after: Candidate committed source records.
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
            'unchanged': sorted((old.keys() & new.keys()) - set(changed))}


def candidate_pairs(universe: dict[str, Any]) -> set[tuple[str, str]]:
    """Compare only source-derived, non-authoritative candidate identifiers.

    Args:
        universe: Revision-specific complete source and candidate inventory.
    """
    paths = {row['identity']: row['path'] for row in universe['sources']}
    return {(paths[edge['source_id']], edge['concept'])
            for edge in universe['candidate_edges']}


def reconcile(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Report exact source delta without manufacturing semantic comparisons.

    Args:
        before: Exact predecessor inventory and model availability.
        after: Exact successor inventory and model availability.
    """
    changes = compare_sources(before['sources'], after['sources'])
    model_states = {'before': before['model_state'], 'after': after['model_state']}
    evaluated = all(state == MODEL_AVAILABLE for state in model_states.values())
    old_edges = candidate_pairs(before) if evaluated else set()
    new_edges = candidate_pairs(after) if evaluated else set()
    candidate_status = 'evaluated' if evaluated else 'not_evaluated'
    identity = hashlib.sha256(json.dumps({
        'before': before['revision'], 'after': after['revision'],
        'changes': changes, 'model_states': model_states,
        'candidate_status': candidate_status,
        'added_candidates': sorted(new_edges - old_edges),
        'removed_candidates': sorted(old_edges - new_edges),
    }, sort_keys=True).encode()).hexdigest()
    return {'record_type': 'sage-neo4j-source-reconciliation',
            'previous_revision': before['revision'],
            'candidate_revision': after['revision'],
            'before_count': len(before['sources']),
            'after_count': len(after['sources']),
            'source_changes': changes, 'concept_model_states': model_states,
            'candidate_comparison_state': candidate_status,
            'new_candidate_links': sorted(new_edges - old_edges),
            'removed_candidate_links': sorted(old_edges - new_edges),
            'digest': identity,
            'semantic_relationships_established': 0,
            'active_projection_mutated': False,
            'promotion_authorized': False}
