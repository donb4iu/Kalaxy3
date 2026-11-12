#!/usr/bin/env python3
"""Score bounded objective retrieval using externally authored relevance judgments."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any

from sage_neo4j_objective import objective_evidence

SCHEMA = 'sage-neo4j-objective-labels-v1'
VERDICTS = frozenset({'relevant', 'irrelevant', 'uncertain'})
PAGE_SIZE = 100
MAX_CASES = 100
MAX_JUDGMENTS = 2000
MAX_PAGES = 250
ID_PATTERN = re.compile(r'^[a-z][a-z0-9._-]{2,79}$')


def canonical_hash(value: Any) -> str:
    """Digest a JSON-safe object deterministically.

    Args:
        value: JSON-compatible object to hash.
    """
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                     ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def projection_inventory(session: Any, identifier: str) -> dict[str, Any]:
    """Read the candidate graph identity and valid source/claim universes.

    Args:
        session: Read-only Neo4j session.
        identifier: Exact candidate projection identity.
    """
    row = session.run('MATCH (p:SageProjection {id:$id}) RETURN p.state AS state, '
                      'p.revision AS revision, p.fingerprint AS fingerprint',
                      id=identifier).single()
    if row is None or row['state'] != 'candidate':
        raise ValueError('OBJECTIVE_BENCHMARK_CANDIDATE_ONLY')
    if not row['revision'] or not row['fingerprint']:
        raise ValueError('OBJECTIVE_BENCHMARK_PROVENANCE_REQUIRED')
    sources = session.run('MATCH (s:SageSource)-[:IN_PROJECTION]->'
                          '(p:SageProjection {id:$id}) RETURN s.path AS value',
                          id=identifier)
    claims = session.run('MATCH (c:SageRelationClaim)-[:IN_PROJECTION]->'
                         '(p:SageProjection {id:$id}) RETURN c.claim_id AS value',
                         id=identifier)
    return {'projection_id': identifier, 'revision': row['revision'],
            'fingerprint': row['fingerprint'],
            'source_paths': [item['value'] for item in sources],
            'claim_ids': [item['value'] for item in claims]}


def validated_universe(inventory: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Reject duplicate or malformed graph identities before scoring.

    Args:
        inventory: Candidate graph metadata and enumerated identifiers.
    """
    sources, claims = inventory['source_paths'], inventory['claim_ids']
    if len(sources) > 100000 or len(claims) > 100000:
        raise ValueError('OBJECTIVE_BENCHMARK_GRAPH_TOO_LARGE')
    if (any(not isinstance(value, str) or not value for value in sources + claims) or
            len(sources) != len(set(sources)) or len(claims) != len(set(claims))):
        raise ValueError('OBJECTIVE_BENCHMARK_DUPLICATE_GRAPH_IDENTITY')
    return set(sources), set(claims)


def validate_judgments(rows: Any, universe: set[str], label: str) -> None:
    """Enforce explicit, independently explained positive/negative labels.

    Args:
        rows: Untrusted judgments for one objective.
        universe: Version-scoped source paths or claim identifiers.
        label: Name of the judgment identifier key.
    """
    if not isinstance(rows, list) or len(rows) > MAX_JUDGMENTS:
        raise ValueError('OBJECTIVE_LABEL_JUDGMENTS_INVALID')
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {label, 'verdict', 'basis'}:
            raise ValueError('OBJECTIVE_LABEL_JUDGMENT_SHAPE')
        value = row[label]
        if (not isinstance(value, str) or value not in universe or
                value in seen or not isinstance(row['verdict'], str) or
                row['verdict'] not in VERDICTS or
                not isinstance(row['basis'], str) or not row['basis'].strip()):
            raise ValueError('OBJECTIVE_LABEL_INVALID_OR_DUPLICATED')
        seen.add(value)


def validate_labels(labels: dict[str, Any],
                    inventory: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind external annotations to one exact candidate projection.

    Args:
        labels: Independently authored objective-label document.
        inventory: Read-only exact-version candidate graph inventory.
    """
    required = {'schema', 'projection_id', 'revision', 'fingerprint',
                'annotator', 'annotation_reference', 'cases'}
    if not isinstance(labels, dict) or set(labels) != required:
        raise ValueError('OBJECTIVE_LABEL_DOCUMENT_SHAPE')
    if labels['schema'] != SCHEMA or any(
        labels[key] != inventory[key] for key in ('projection_id', 'revision', 'fingerprint')
    ):
        raise ValueError('OBJECTIVE_LABEL_STALE_PROJECTION')
    if any(not isinstance(labels[key], str) or not labels[key].strip()
           for key in ('annotator', 'annotation_reference')):
        raise ValueError('OBJECTIVE_LABEL_PROVENANCE_REQUIRED')
    cases = labels['cases']
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ValueError('OBJECTIVE_LABEL_CASE_COUNT')
    source_paths, claim_ids = validated_universe(inventory)
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            'id', 'objective', 'source_judgments', 'claim_judgments'
        }:
            raise ValueError('OBJECTIVE_LABEL_CASE_SHAPE')
        if (not isinstance(case['id'], str) or
                not ID_PATTERN.fullmatch(case['id']) or case['id'] in seen or
                not isinstance(case['objective'], str) or not case['objective'].strip() or
                len(case['objective']) > 2000):
            raise ValueError('OBJECTIVE_LABEL_CASE_INVALID')
        seen.add(case['id'])
        validate_judgments(case['source_judgments'], source_paths, 'path')
        validate_judgments(case['claim_judgments'], claim_ids, 'claim_id')
    return cases


def add_page(observed: dict[str, set[str]], page: dict[str, Any]) -> None:
    """Collect candidate and contextual pointers without inferred relevance.

    Args:
        observed: Accumulated objective-level retrieval identities.
        page: A bounded candidate readback page.
    """
    observed['candidate_sources'].update(row['path'] for row in page['sources'])
    observed['context_sources'].update(
        row['path'] for row in page['governance_source_pointers'])
    observed['context_sources'].update(
        row['related_path'] for row in page['literal_source_links'])
    observed['context_sources'].update(
        row['source_path'] for row in page['context_sections'])
    for claim in page['relationship_claims']:
        observed['claims'].add(claim['claim_id'])
        observed['context_sources'].update(
            claim[key] for key in ('subject_path', 'object_path', 'evidence_path')
            if claim.get(key))


def gather_objective(session: Any, projection_id: str,
                     objective: str) -> dict[str, set[str]]:
    """Collect all bounded source, section and claim pages for an objective.

    Args:
        session: Read-only Neo4j session.
        projection_id: Exact candidate projection identity.
        objective: Externally labeled objective wording.
    """
    observed: dict[str, set[str]] = {'candidate_sources': set(),
                                      'context_sources': set(), 'claims': set()}
    offsets = {'offset': 0, 'section_offset': 0, 'claim_offset': 0}
    fields = {'offset': ('next_offset', 'total_candidate_sources'),
              'section_offset': ('next_section_offset', 'total_context_sections'),
              'claim_offset': ('next_claim_offset', 'total_relationship_claims')}
    for _ in range(MAX_PAGES):
        page = objective_evidence(session, projection_id, objective,
                                  limit=PAGE_SIZE, section_limit=PAGE_SIZE,
                                  claim_limit=PAGE_SIZE, **offsets)
        if page.get('projection_id') != projection_id or page.get('qualification') != 'candidate_only':
            raise ValueError('OBJECTIVE_BENCHMARK_UNQUALIFIED_PAGE')
        add_page(observed, page)
        upcoming = {key: page[next_key] if page[next_key] is not None else page[count_key]
                    for key, (next_key, count_key) in fields.items()}
        if all(page[next_key] is None
               for next_key, _ in fields.values()):
            return observed
        if upcoming == offsets:
            raise ValueError('OBJECTIVE_BENCHMARK_PAGE_STALL')
        if any(upcoming[key] < offsets[key] for key in offsets):
            raise ValueError('OBJECTIVE_BENCHMARK_PAGE_REGRESSION')
        offsets = upcoming
    raise ValueError('OBJECTIVE_BENCHMARK_PAGE_BUDGET_EXCEEDED')


def ratio(numerator: int, denominator: int) -> float | None:
    """Return a metric, or None when no eligible labels exist.

    Args:
        numerator: Number of correctly retrieved labeled items.
        denominator: Number of eligible labeled items.
    """
    return numerator / denominator if denominator else None


def measure_dimension(rows: list[dict[str, str]], observed: set[str],
                      key: str) -> dict[str, Any]:
    """Score labeled pairs only; leave unknown relevance uncounted.

    Args:
        rows: Explicit independent relevance judgments.
        observed: Returned graph identifiers for the objective.
        key: Judged identifier field.
    """
    positives = {row[key] for row in rows if row['verdict'] == 'relevant'}
    negatives = {row[key] for row in rows if row['verdict'] == 'irrelevant'}
    uncertain = {row[key] for row in rows if row['verdict'] == 'uncertain'}
    tp, fp = positives & observed, negatives & observed
    fn, tn = positives - observed, negatives - observed
    return {'judged_positive': len(positives), 'judged_negative': len(negatives),
            'judged_uncertain': len(uncertain),
            'true_positive': len(tp), 'false_positive': len(fp),
            'false_negative': len(fn), 'true_negative': len(tn),
            'precision_labeled_only': ratio(len(tp), len(tp) + len(fp)),
            'recall_labeled_only': ratio(len(tp), len(tp) + len(fn)),
            'unjudged_retrieved': len(observed - positives - negatives - uncertain),
            'retrieved_uncertain': len(observed & uncertain),
            'missed_positive': sorted(fn), 'retrieved_negative': sorted(fp)}


def summarize_cases(results: list[dict[str, Any]], dimension: str) -> dict[str, Any]:
    """Aggregate source/claim measurements without a corpus-wide claim.

    Args:
        results: Individually scored, externally labeled objective cases.
        dimension: Either source or claim scoring family.
    """
    metrics = ('true_positive', 'false_positive', 'false_negative', 'true_negative',
               'judged_positive', 'judged_negative', 'judged_uncertain',
               'unjudged_retrieved')
    totals = {key: sum(case[dimension][key] for case in results) for key in metrics}
    totals['micro_precision_labeled_only'] = ratio(
        totals['true_positive'], totals['true_positive'] + totals['false_positive'])
    totals['micro_recall_labeled_only'] = ratio(
        totals['true_positive'], totals['true_positive'] + totals['false_negative'])
    return totals


def evaluate_cases(labels: dict[str, Any], inventory: dict[str, Any],
                   retrieve: Callable[[str], dict[str, set[str]]]) -> dict[str, Any]:
    """Measure independently labeled objectives without changing graph authority.

    Args:
        labels: External annotations fixed to a graph revision.
        inventory: Candidate graph identity, source and claim universes.
        retrieve: Read-only retrieval function for each objective.
    """
    cases = validate_labels(labels, inventory)
    results = []
    source_paths, claim_ids = validated_universe(inventory)
    for case in cases:
        observed = retrieve(case['objective'])
        all_sources = observed['candidate_sources'] | observed['context_sources']
        if not all_sources <= source_paths or not observed['claims'] <= claim_ids:
            raise ValueError('OBJECTIVE_BENCHMARK_CROSS_PROJECTION_RESULT')
        results.append({'id': case['id'],
                        'source': measure_dimension(case['source_judgments'],
                                                    all_sources, 'path'),
                        'claim': measure_dimension(case['claim_judgments'],
                                                   observed['claims'], 'claim_id'),
                        'candidate_source_count': len(observed['candidate_sources']),
                        'context_source_count': len(observed['context_sources']),
                        'union_source_count': len(all_sources)})
    return {'schema': 'sage-neo4j-objective-measurement-v1',
            'status': 'measurement_only',
            'projection_id': inventory['projection_id'],
            'revision': inventory['revision'],
            'fingerprint': inventory['fingerprint'],
            'annotation_reference': labels['annotation_reference'],
            'annotation_digest': canonical_hash(labels),
            'annotation_independence_verified': False,
            'semantic_qualification': 'not_evaluated',
            'architect_acceptance': 'not_evaluated',
            'coverage': 'only_explicitly_labeled_objectives_and_relevance_pairs',
            'cases': results,
            'source_summary': summarize_cases(results, 'source'),
            'claim_summary': summarize_cases(results, 'claim')}
