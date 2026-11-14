#!/usr/bin/env python3
"""Regression tests for bounded independent objective retrieval measurement."""

from __future__ import annotations

import copy
import unittest
from collections.abc import Iterator
from typing import Any
from unittest.mock import patch

from sage_neo4j_objective_measure import (SCHEMA, evaluate_cases, gather_objective,
                                          measure_dimension, projection_inventory,
                                          validate_labels)


INVENTORY = {'projection_id': 'graph-50', 'revision': 'a' * 40,
             'fingerprint': 'f' * 64,
             'source_paths': ['AGENTS.md', 'foo.md', 'bar.md'],
             'claim_ids': ['global.rules', 'bar.decision']}


def fixture_labels() -> dict[str, Any]:
    """Create synthetic independent labels without claiming real reviewer authority."""
    return {'schema': SCHEMA, 'projection_id': 'graph-50',
            'revision': 'a' * 40, 'fingerprint': 'f' * 64,
            'annotator': 'fixture-annotator',
            'annotation_reference': 'fixture-only-no-independent-review',
            'cases': [{'id': 'objective.one', 'objective': 'Explore requirements',
                       'source_judgments': [
                           {'path': 'AGENTS.md', 'verdict': 'relevant', 'basis': 'fixture'},
                           {'path': 'foo.md', 'verdict': 'irrelevant', 'basis': 'fixture'},
                           {'path': 'bar.md', 'verdict': 'uncertain', 'basis': 'fixture'}],
                       'claim_judgments': [
                           {'claim_id': 'global.rules', 'verdict': 'relevant',
                            'basis': 'fixture'},
                           {'claim_id': 'bar.decision', 'verdict': 'irrelevant',
                            'basis': 'fixture'}]}]}


def fake_observed(objective: str) -> dict[str, set[str]]:
    """Return a deliberately mixed candidate/context result.

    Args:
        objective: Synthetic objective used by the fake retrieval.
    """
    return {'candidate_sources': {'foo.md'},
            'context_sources': {'AGENTS.md'}, 'claims': {'global.rules'}}


class MeasurementTests(unittest.TestCase):
    """Exercise labels, metrics and authority boundaries."""

    def test_mixed_labels_score_true_and_false_positive(self) -> None:
        """Score only judged identities and distinguish retrieval surfaces."""
        result = evaluate_cases(fixture_labels(), INVENTORY, fake_observed)
        source = result['cases'][0]['source']
        claim = result['cases'][0]['claim']
        self.assertEqual((source['true_positive'], source['false_positive']), (1, 1))
        self.assertEqual((source['precision_labeled_only'], source['recall_labeled_only']),
                         (0.5, 1.0))
        self.assertEqual((claim['true_positive'], claim['false_negative']), (1, 0))
        self.assertEqual(result['semantic_qualification'], 'not_evaluated')
        self.assertFalse(result['annotation_independence_verified'])
        self.assertEqual(result['source_summary']['micro_precision_labeled_only'], 0.5)

    def test_absent_labels_cannot_be_interpreted_as_absent_evidence(self) -> None:
        """Unreviewed returned sources are unknown rather than false positives."""
        labels = fixture_labels()
        labels['cases'][0]['source_judgments'] = []
        result = evaluate_cases(labels, INVENTORY, fake_observed)['cases'][0]['source']
        self.assertIsNone(result['precision_labeled_only'])
        self.assertIsNone(result['recall_labeled_only'])
        self.assertEqual(result['unjudged_retrieved'], 2)

    def test_stale_projection_refused(self) -> None:
        """Labels cannot be replayed after a source or graph revision change."""
        labels = fixture_labels()
        labels['fingerprint'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'STALE_PROJECTION'):
            validate_labels(labels, INVENTORY)

    def test_unhashable_verdict_rejected_cleanly(self) -> None:
        """Malformed external labels must fail closed with a domain error."""
        labels = fixture_labels()
        labels['cases'][0]['source_judgments'][0]['verdict'] = []
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_DUPLICATED'):
            validate_labels(labels, INVENTORY)

    def test_unknown_source_refused(self) -> None:
        """An annotation must identify an actual pinned graph source."""
        labels = fixture_labels()
        labels['cases'][0]['source_judgments'][0]['path'] = 'absent.md'
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_DUPLICATED'):
            validate_labels(labels, INVENTORY)

    def test_unqualified_free_form_verdict_refused(self) -> None:
        """Only explicit relevance verdicts can enter the metric denominator."""
        labels = fixture_labels()
        labels['cases'][0]['claim_judgments'][0]['verdict'] = 'approved'
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_DUPLICATED'):
            validate_labels(labels, INVENTORY)

    def test_duplicate_objective_ids_fail_closed(self) -> None:
        """Duplicating a case cannot weight one objective twice unnoticed."""
        labels = fixture_labels()
        labels['cases'].append(copy.deepcopy(labels['cases'][0]))
        with self.assertRaisesRegex(ValueError, 'CASE_INVALID'):
            validate_labels(labels, INVENTORY)

    def test_duplicate_judgment_fails_closed(self) -> None:
        """Repetition cannot inflate apparent source recall."""
        labels = fixture_labels()
        labels['cases'][0]['source_judgments'].append(
            copy.deepcopy(labels['cases'][0]['source_judgments'][0]))
        with self.assertRaisesRegex(ValueError, 'INVALID_OR_DUPLICATED'):
            validate_labels(labels, INVENTORY)

    def test_foreign_graph_result_refused(self) -> None:
        """A returned claim not present in the graph universe is a hard error."""
        def foreign(_: str) -> dict[str, set[str]]:
            """Return an identity from a different fixture projection."""
            return {'candidate_sources': set(), 'context_sources': set(),
                    'claims': {'outside.graph'}}
        with self.assertRaisesRegex(ValueError, 'CROSS_PROJECTION'):
            evaluate_cases(fixture_labels(), INVENTORY, foreign)

    def test_metric_with_uncertain_only_stays_null(self) -> None:
        """Uncertain labels do not enter precision/recall denominators."""
        score = measure_dimension([{'path': 'bar.md', 'verdict': 'uncertain',
                                    'basis': 'unknown'}], {'bar.md'}, 'path')
        self.assertIsNone(score['precision_labeled_only'])
        self.assertEqual(score['retrieved_uncertain'], 1)

    def test_missing_provenance_fails_closed(self) -> None:
        """A measurement requires an attributed independent annotation source."""
        labels = fixture_labels()
        labels['annotator'] = ''
        with self.assertRaisesRegex(ValueError, 'PROVENANCE_REQUIRED'):
            validate_labels(labels, INVENTORY)


class FakeRecord:
    """Neo4j record fixture exposing mapping and single-result behavior."""

    def __init__(self, values: dict[str, Any]) -> None:
        """Hold literal response values.

        Args:
            values: Fake Neo4j record mapping.
        """
        self.values = values

    def __getitem__(self, name: str) -> Any:
        """Return one fake field.

        Args:
            name: Exact requested record key.
        """
        return self.values[name]


class FakeQuery:
    """Result fixture supporting single-result and iterable query patterns."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Preserve supplied row mappings.

        Args:
            rows: Query result rows.
        """
        self.rows = [FakeRecord(row) for row in rows]

    def single(self) -> FakeRecord | None:
        """Return the only record, if present."""
        return self.rows[0] if self.rows else None

    def __iter__(self) -> Iterator[FakeRecord]:
        """Iterate fake Neo4j records."""
        return iter(self.rows)


class FakeSession:
    """Read-only fixture for graph provenance and universe retrieval."""

    def run(self, query: str, **kwargs: Any) -> FakeQuery:
        """Return deterministic graph data for the queried node family.

        Args:
            query: Read-only Neo4j query.
            kwargs: Query parameters.
        """
        if 'RETURN p.state' in query:
            return FakeQuery([{'state': 'candidate', 'revision': 'a' * 40,
                               'fingerprint': 'f' * 64}])
        if 'SageRelationClaim' in query:
            return FakeQuery([{'value': value} for value in INVENTORY['claim_ids']])
        return FakeQuery([{'value': value} for value in INVENTORY['source_paths']])


class GraphReadTests(unittest.TestCase):
    """Check revision-bound graph reads and multi-channel paging."""

    def test_graph_identity_readback(self) -> None:
        """Projection headers and both graph identity universes are read only."""
        self.assertEqual(projection_inventory(FakeSession(), 'graph-50'), INVENTORY)

    def test_multi_page_source_claim_and_section(self) -> None:
        """Independent pages cannot truncate global or historical evidence."""
        def fake_query(session: Any, identifier: str, objective: str,
                       **kwargs: Any) -> dict[str, Any]:
            """Emit independent source/claim pages for one synthetic objective."""
            offset = kwargs['offset']
            result = {'projection_id': identifier, 'qualification': 'candidate_only',
                      'sources': [{'path': 'foo.md'}] if offset == 0 else [],
                      'context_sections': [], 'literal_source_links': [],
                      'governance_source_pointers': [{'path': 'AGENTS.md'}],
                      'relationship_claims': ([{'claim_id': 'global.rules',
                          'subject_path': 'AGENTS.md', 'object_path': None,
                          'evidence_path': 'AGENTS.md'}]
                          if kwargs['claim_offset'] == 0 else [
                          {'claim_id': 'bar.decision', 'subject_path': 'bar.md',
                           'object_path': None, 'evidence_path': 'bar.md'}]),
                      'total_candidate_sources': 1, 'total_context_sections': 0,
                      'total_relationship_claims': 2,
                      'next_offset': None, 'next_section_offset': None,
                      'next_claim_offset': (1 if kwargs['claim_offset'] == 0
                                            else None)}
            return result
        with patch('sage_neo4j_objective_measure.PAGE_SIZE', 1), \
             patch('sage_neo4j_objective_measure.objective_evidence', fake_query):
            observed = gather_objective(FakeSession(), 'graph-50', 'Some objective')
        self.assertEqual(observed['claims'], {'global.rules', 'bar.decision'})
        self.assertEqual(observed['context_sources'], {'AGENTS.md', 'bar.md'})

    def test_stalled_page_fails_closed(self) -> None:
        """A broken pagination cursor must not report complete coverage."""
        def fake_query(session: Any, identifier: str, objective: str,
                       **kwargs: Any) -> dict[str, Any]:
            """Return a non-advancing cursor for a purported second page."""
            return {'projection_id': identifier, 'qualification': 'candidate_only',
                    'sources': [], 'context_sections': [], 'literal_source_links': [],
                    'governance_source_pointers': [], 'relationship_claims': [],
                    'total_candidate_sources': 3, 'total_context_sections': 0,
                    'total_relationship_claims': 0, 'next_offset': 0,
                    'next_section_offset': None, 'next_claim_offset': None}
        with patch('sage_neo4j_objective_measure.objective_evidence', fake_query):
            with self.assertRaisesRegex(ValueError, 'PAGE_STALL'):
                gather_objective(FakeSession(), 'graph-50', 'Some objective')

    def test_no_candidate_matching_still_preserves_claim(self) -> None:
        """A no-match objective may still retrieve a universal rule pointer."""
        def fake_query(session: Any, identifier: str, objective: str,
                       **kwargs: Any) -> dict[str, Any]:
            """Return global claim without any lexical source candidate."""
            return {'projection_id': identifier, 'qualification': 'candidate_only',
                    'sources': [], 'context_sections': [], 'literal_source_links': [],
                    'governance_source_pointers': [],
                    'relationship_claims': [{'claim_id': 'global.rules',
                        'subject_path': 'AGENTS.md', 'evidence_path': 'AGENTS.md',
                        'object_path': None}],
                    'total_candidate_sources': 0, 'total_context_sections': 0,
                    'total_relationship_claims': 1,
                    'next_offset': None, 'next_section_offset': None,
                    'next_claim_offset': None}
        with patch('sage_neo4j_objective_measure.objective_evidence', fake_query):
            observed = gather_objective(FakeSession(), 'graph-50', 'Unknown objective')
        self.assertEqual(observed['claims'], {'global.rules'})


if __name__ == '__main__':
    unittest.main()
