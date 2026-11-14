#!/usr/bin/env python3
"""Prepare and verify blinded, revision-pinned SAGE semantic review cases."""

from __future__ import annotations

import random
from typing import Any

from sage_neo4j_benchmark import (LABELS_SCHEMA, candidate_pairs, evaluate,
                                  stable_hash)

REVIEW_SCHEMA = 'sage-neo4j-blinded-review-v1'


def pair_indices(snapshot: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return the complete independent source/concept pair dimensions.

    Args:
        snapshot: Complete, revision-pinned semantic source inventory.
    """
    paths = sorted(source['path'] for source in snapshot['sources'])
    concepts = sorted(concept['name'] for concept in snapshot['concepts'])
    if len(set(paths)) != len(paths) or len(set(concepts)) != len(concepts):
        raise ValueError('DUPLICATE_REVIEW_DIMENSIONS')
    return paths, concepts


def sample_non_candidates(snapshot: dict[str, Any], predicted: set[tuple[str, str]],
                          count: int, rng: random.Random) -> list[tuple[str, str]]:
    """Select non-nominated pairs without trusting candidate recall.

    Args:
        snapshot: Exact source and concept dimensions.
        predicted: Matcher-nominated pairs, used for sampling only.
        count: Number of independent negative-stratum cases requested.
        rng: Deterministic sampling generator.
    """
    paths, concepts = pair_indices(snapshot)
    total = len(paths) * len(concepts)
    if not total or not count:
        return []
    if total <= 250_000:
        pool = [(path, concept) for path in paths for concept in concepts
                if (path, concept) not in predicted]
        return rng.sample(pool, min(count, len(pool)))
    chosen: set[tuple[str, str]] = set()
    target = min(count, total - len(predicted))
    for _ in range(max(1000, target * 200)):
        index = rng.randrange(total)
        pair = (paths[index // len(concepts)], concepts[index % len(concepts)])
        if pair not in predicted:
            chosen.add(pair)
        if len(chosen) == target:
            break
    if len(chosen) != target:
        raise ValueError('INCOMPLETE_NONCANDIDATE_SAMPLE')
    return sorted(chosen)


def select_pairs(snapshot: dict[str, Any], size: int, seed: int) -> list[tuple[str, str]]:
    """Select nominated and missed-candidate strata without labeling truth.

    Args:
        snapshot: Read-only projection snapshot with model available.
        size: Maximum total independent review pairs.
        seed: Explicit deterministic sampling seed.
    """
    if size < 2 or size > 10000:
        raise ValueError('REVIEW_SAMPLE_SIZE_OUT_OF_RANGE')
    predicted = candidate_pairs(snapshot)
    paths, concepts = pair_indices(snapshot)
    total = len(paths) * len(concepts)
    rng = random.Random(int(snapshot['fingerprint'][:16], 16) ^ seed)
    candidate_target = min(len(predicted), (min(size, total) + 1) // 2)
    selected = rng.sample(sorted(predicted), candidate_target)
    non_candidates = sample_non_candidates(snapshot, predicted,
                                           min(size, total) - candidate_target, rng)
    selected += non_candidates
    if len(selected) < min(size, total):
        remaining = sorted(predicted - set(selected))
        selected += rng.sample(remaining, min(min(size, total) - len(selected),
                                               len(remaining)))
    rng.shuffle(selected)
    return selected


def build_review(snapshot: dict[str, Any], size: int = 48,
                 seed: int = 50) -> dict[str, Any]:
    """Build an annotation-neutral review packet with no predicted outcomes.

    Args:
        snapshot: Revision-pinned complete inventory and candidate edges.
        size: Maximum total reviewed source/concept pairs.
        seed: Deterministic explicit sampling seed.
    """
    if snapshot['model_state'] not in {'available', 'evidence_derived_candidate'}:
        return {'status': 'not_evaluated', 'reason': 'CONCEPT_MODEL_ABSENT',
                'revision': snapshot['revision'],
                'source_count': len(snapshot['sources'])}
    pairs = select_pairs(snapshot, size, seed)
    sources = {source['path']: source for source in snapshot['sources']}
    cases = [{'path': path, 'concept': concept,
              'content_sha256': sources[path]['content_sha256'],
              'git_oid': sources[path]['git_oid']} for path, concept in pairs]
    return {'schema': REVIEW_SCHEMA, 'status': 'ready_for_independent_annotation',
            'revision': snapshot['revision'],
            'projection_fingerprint': snapshot['fingerprint'],
            'selection_seed': seed, 'requested_pairs': size,
            'sampled_pair_count': len(cases),
            'source_count': len(snapshot['sources']),
            'concept_count': len(snapshot['concepts']),
            'possible_pair_count': len(snapshot['sources']) * len(snapshot['concepts']),
            'review_cases': cases,
            'predictions_exposed': False, 'source_bodies_exported': False,
            'qualification': 'review_sample_only_not_corpus_wide'}


def label_template(review: dict[str, Any]) -> dict[str, Any]:
    """Prepare unfilled judgments without inventing human assessments.

    Args:
        review: Revision-locked blinded review packet.
    """
    if review.get('status') != 'ready_for_independent_annotation':
        raise ValueError('REVIEW_NOT_READY')
    return {'schema': LABELS_SCHEMA, 'revision': review['revision'],
            'projection_fingerprint': review['projection_fingerprint'],
            'review_packet_digest': stable_hash(review),
            'annotator': '', 'annotation_reference': '',
            'judgments': [{'path': case['path'], 'concept': case['concept'],
                           'verdict': None, 'basis': ''}
                          for case in review['review_cases']]}


def score_review(snapshot: dict[str, Any], review: dict[str, Any],
                 labels: dict[str, Any]) -> dict[str, Any]:
    """Require every selected judgment before invoking existing metrics.

    Args:
        snapshot: Reproduced committed projection candidate snapshot.
        review: Previously issued blinded review packet.
        labels: Filled, independently authored judgments.
    """
    if review.get('schema') != REVIEW_SCHEMA:
        raise ValueError('INVALID_REVIEW_SCHEMA')
    if (review['revision'] != snapshot['revision'] or
            review['projection_fingerprint'] != snapshot['fingerprint']):
        raise ValueError('STALE_REVIEW_SNAPSHOT')
    regenerated = build_review(snapshot, review['requested_pairs'],
                               review['selection_seed'])
    if stable_hash(regenerated) != stable_hash(review):
        raise ValueError('REVIEW_PACKET_TAMPERED')
    if labels.get('review_packet_digest') != stable_hash(review):
        raise ValueError('REVIEW_PACKET_BINDING_MISMATCH')
    expected = [(item['path'], item['concept']) for item in review['review_cases']]
    supplied = [(item.get('path'), item.get('concept'))
                for item in labels.get('judgments', [])]
    if len(expected) != len(set(expected)) or set(expected) != set(supplied):
        raise ValueError('INCOMPLETE_OR_ALTERED_REVIEW_SET')
    if len(supplied) != len(set(supplied)):
        raise ValueError('DUPLICATE_REVIEW_JUDGMENT')
    result = evaluate(snapshot, labels)
    result['review_packet_digest'] = stable_hash(review)
    result['sampled_pair_count'] = len(expected)
    result['sample_is_population_representative'] = False
    result['independent_label_verification'] = 'not_evaluated'
    return result
