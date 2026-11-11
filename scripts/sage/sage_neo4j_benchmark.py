#!/usr/bin/env python3
"""Evidence-scoped precision/recall measurement for SAGE Neo4j candidates."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import candidate_edges, committed_head, concept_records
from sage_neo4j_inventory import git_output, source_records, fingerprint

MODEL = 'sage-semantic-concepts.json'
LABELS_SCHEMA = 'sage-neo4j-independent-labels-v1'
VERDICTS = {'relevant', 'irrelevant', 'uncertain'}


def stable_hash(value: Any) -> str:
    """Hash canonical JSON without relying on host serialization order.

    Args:
        value: JSON-compatible data structure.
    """
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def read_committed_model(repo: Path, head: str) -> dict[str, Any] | None:
    """Read the model solely from governed Git history if it exists.

    Args:
        repo: Repository checkout.
        head: Fully resolved committed revision.
    """
    try:
        raw = git_output(repo, 'show', f'{head}:{MODEL}')
    except subprocess.CalledProcessError:
        if subprocess.run(['git', '-C', str(repo), 'cat-file', '-e',
                           f'{head}:{MODEL}'], capture_output=True).returncode == 0:
            raise ValueError('CONCEPT_MODEL_READ_ERROR')
        return None
    model = json.loads(raw)
    if not isinstance(model, dict):
        raise ValueError('INVALID_COMMITTED_CONCEPT_MODEL')
    return model


def build_snapshot(repo: Path) -> dict[str, Any]:
    """Inventory all tracked evidence and prepare untrusted model candidates.

    Args:
        repo: Governed Git repository checkout.
    """
    head = committed_head(repo)
    sources = source_records(repo, head)
    model = read_committed_model(repo, head)
    if model is None:
        return {'revision': head, 'sources': sources, 'concepts': [],
                'candidate_edges': [], 'model_state': 'not_evaluated',
                'fingerprint': stable_hash({'revision': head, 'sources': sources,
                                            'model_state': 'not_evaluated'})}
    concepts = concept_records(model)
    edges = candidate_edges(sources, concepts, repo)
    return {'revision': head, 'sources': sources, 'concepts': concepts,
            'candidate_edges': edges, 'model_state': 'available',
            'fingerprint': fingerprint(sources, concepts, edges)}


def validate_labels(snapshot: dict[str, Any], labels: dict[str, Any]) -> list[dict[str, str]]:
    """Check revision, provenance and every independently labeled pair.

    Args:
        snapshot: Revision-pinned candidate inventory.
        labels: External annotator's label set; not SAGE-generated truth.
    """
    if labels.get('schema') != LABELS_SCHEMA:
        raise ValueError('UNSUPPORTED_LABEL_SCHEMA')
    if (labels.get('revision') != snapshot['revision'] or
            labels.get('projection_fingerprint') != snapshot['fingerprint']):
        raise ValueError('STALE_LABEL_SCOPE')
    if (not isinstance(labels.get('annotator'), str) or
            not labels['annotator'].strip() or
            not isinstance(labels.get('annotation_reference'), str) or
            not labels['annotation_reference'].strip()):
        raise ValueError('LABEL_PROVENANCE_REQUIRED')
    paths = {s['path'] for s in snapshot['sources']}
    concepts = {c['name'] for c in snapshot['concepts']}
    judgments = labels.get('judgments')
    if not isinstance(judgments, list):
        raise ValueError('LABEL_JUDGMENTS_REQUIRED')
    seen: set[tuple[str, str]] = set()
    for item in judgments:
        if not isinstance(item, dict):
            raise ValueError('INVALID_JUDGMENT')
        pair = (item.get('path'), item.get('concept'))
        if pair[0] not in paths or pair[1] not in concepts:
            raise ValueError('LABEL_REFERENCES_UNKNOWN_SOURCE_OR_CONCEPT')
        if pair in seen or item.get('verdict') not in VERDICTS:
            raise ValueError('DUPLICATE_OR_INVALID_LABEL')
        if not isinstance(item.get('basis'), str) or not item['basis'].strip():
            raise ValueError('JUDGMENT_BASIS_REQUIRED')
        seen.add(pair)
    return judgments


def candidate_pairs(snapshot: dict[str, Any]) -> set[tuple[str, str]]:
    """Resolve candidate source identities into versioned source paths.

    Args:
        snapshot: Versioned semantic candidate data.
    """
    lookup = {s['identity']: s['path'] for s in snapshot['sources']}
    result: set[tuple[str, str]] = set()
    for edge in snapshot['candidate_edges']:
        if edge['source_id'] not in lookup:
            raise ValueError('CANDIDATE_SOURCE_NOT_IN_INVENTORY')
        if edge.get('state') != 'candidate_unverified':
            raise ValueError('CANDIDATE_EDGE_STATE_MISMATCH')
        if edge['concept'] not in {c['name'] for c in snapshot['concepts']}:
            raise ValueError('CANDIDATE_CONCEPT_NOT_IN_MODEL')
        pair = (lookup[edge['source_id']], edge['concept'])
        if pair in result:
            raise ValueError('DUPLICATE_CANDIDATE_PAIR')
        result.add(pair)
    return result


def ratio(numerator: int, denominator: int) -> float | None:
    """Return a bounded metric or null for undefined denominators.

    Args:
        numerator: Count of successful cases.
        denominator: Count of eligible cases.
    """
    return numerator / denominator if denominator else None


def evaluate(snapshot: dict[str, Any], labels: dict[str, Any]) -> dict[str, Any]:
    """Measure only labeled-pair performance, with no authority promotion.

    Args:
        snapshot: Committed projection candidate snapshot.
        labels: Independently authored pair judgments, including negatives.
    """
    if snapshot['model_state'] not in {'available', 'evidence_derived_candidate'}:
        raise ValueError('CONCEPT_MODEL_NOT_EVALUATED')
    judgments = validate_labels(snapshot, labels)
    candidates = candidate_pairs(snapshot)
    predicted = {(j['path'], j['concept']) for j in judgments
                 if (j['path'], j['concept']) in candidates}
    positive = {(j['path'], j['concept']) for j in judgments
                if j['verdict'] == 'relevant'}
    negative = {(j['path'], j['concept']) for j in judgments
                if j['verdict'] == 'irrelevant'}
    uncertain = {(j['path'], j['concept']) for j in judgments
                 if j['verdict'] == 'uncertain'}
    tp, fp = predicted & positive, predicted & negative
    fn, tn = positive - predicted, negative - predicted
    labeled_pairs = positive | negative | uncertain
    return {'status': 'measurement_only', 'revision': snapshot['revision'],
            'projection_fingerprint': snapshot['fingerprint'],
            'annotation_reference': labels['annotation_reference'],
            'annotation_digest': stable_hash(labels),
            'annotation_independence_verified': False,
            'architect_acceptance': 'not_evaluated',
            'source_count': len(snapshot['sources']),
            'concept_count': len(snapshot['concepts']),
            'labeled_pair_count': len(labeled_pairs),
            'possible_pair_count': len(snapshot['sources']) * len(snapshot['concepts']),
            'unlabeled_candidate_count': len(candidates - labeled_pairs),
            'uncertain_labeled_pairs': len(uncertain),
            'uncertain_predicted_pairs': len(predicted & uncertain),
            'true_positive': len(tp), 'false_positive': len(fp),
            'false_negative': len(fn), 'true_negative': len(tn),
            'labeled_precision': ratio(len(tp), len(tp) + len(fp)),
            'labeled_recall': ratio(len(tp), len(tp) + len(fn)),
            'missed_labeled_positive_pairs': sorted([list(p) for p in fn]),
            'negative_candidate_pairs': sorted([list(p) for p in fp]),
            'coverage': 'labeled_pairs_only_no_corpus_wide_claim',
            'paraphrase_query_recall': 'not_evaluated',
            'established_edge_retrieval': 'not_evaluated',
            'evidence_maturity': 'not_evaluated'}


def assess(repo: Path, labels: dict[str, Any] | None = None) -> dict[str, Any]:
    """Give explicit readiness when the historical model or labels are absent.

    Args:
        repo: Actual repository checkout.
        labels: Optional independently created label document.
    """
    snapshot = build_snapshot(repo)
    if snapshot['model_state'] not in {'available', 'evidence_derived_candidate'}:
        if labels is not None:
            raise ValueError('CANNOT_SCORE_LABELS_WITHOUT_CONCEPT_MODEL')
        return {'status': 'not_evaluated', 'reason': 'CONCEPT_MODEL_ABSENT',
                'revision': snapshot['revision'], 'source_count': len(snapshot['sources']),
                'projection_fingerprint': snapshot['fingerprint'],
                'source_inventory_preserved': True}
    if labels is None:
        return {'status': 'not_evaluated', 'reason': 'INDEPENDENT_LABELS_ABSENT',
                'revision': snapshot['revision'], 'source_count': len(snapshot['sources']),
                'concept_count': len(snapshot['concepts']),
                'candidate_count': len(snapshot['candidate_edges']),
                'projection_fingerprint': snapshot['fingerprint'],
                'source_inventory_preserved': True}
    return evaluate(snapshot, labels)
