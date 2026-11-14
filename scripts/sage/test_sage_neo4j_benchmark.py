#!/usr/bin/env python3
"""Independent-label measurement regressions over real Git fixtures."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sage_neo4j_benchmark import (LABELS_SCHEMA, assess, build_snapshot,
                                  evaluate, stable_hash)


class BenchmarkTests(unittest.TestCase):
    """Enforce denominators, independent provenance, and false-negative honesty."""

    def setUp(self) -> None:
        """Create versioned positive, negative and uncertain source examples."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Independent Fixture')
        (self.repo / 'a.md').write_text('longhorn provides durable volumes\n', 'utf-8')
        (self.repo / 'b.md').write_text('longhorn shape wallpaper\n', 'utf-8')
        (self.repo / 'c.md').write_text('Stateful records survive pod restarts\n', 'utf-8')
        (self.repo / 'd.md').write_text('unrelated example\n', 'utf-8')
        (self.repo / 'sage-semantic-concepts.json').write_text(json.dumps({
            'concepts': {'storage': {'terms': ['longhorn'], 'related': [],
                                     'dimensions': []},
                         'unused': {'terms': ['nevermentioned'], 'related': [],
                                    'dimensions': []}}}), encoding='utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'benchmark fixture')
        self.snapshot = build_snapshot(self.repo)

    def git(self, *args: str) -> str:
        """Run fixture Git command.

        Args:
            args: Arguments passed to Git within test repository.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True).strip()

    def labels(self) -> dict:
        """Return externally authored style judgments independent of predictions."""
        judgments = [
            {'path': 'a.md', 'concept': 'storage', 'verdict': 'relevant',
             'basis': 'Documents durable data volume'},
            {'path': 'b.md', 'concept': 'storage', 'verdict': 'irrelevant',
             'basis': 'Only decorative wallpaper'},
            {'path': 'c.md', 'concept': 'storage', 'verdict': 'relevant',
             'basis': 'Describes persistent storage without cue'},
            {'path': 'd.md', 'concept': 'storage', 'verdict': 'irrelevant',
             'basis': 'Does not address storage'},
            {'path': 'd.md', 'concept': 'unused', 'verdict': 'uncertain',
             'basis': 'Independent annotator unresolved'},
        ]
        return {'schema': LABELS_SCHEMA,
                'revision': self.snapshot['revision'],
                'projection_fingerprint': self.snapshot['fingerprint'],
                'annotator': 'external-reviewer-placeholder',
                'annotation_reference': 'fixture:review-1',
                'judgments': judgments}

    def test_metrics_preserve_misses_false_positives_and_unknown(self) -> None:
        """Measure only labeled pairs; do not count uncertain as negatives."""
        result = evaluate(self.snapshot, self.labels())
        self.assertEqual((result['true_positive'], result['false_positive'],
                          result['false_negative'], result['true_negative']), (1, 1, 1, 1))
        self.assertEqual(result['labeled_precision'], 0.5)
        self.assertEqual(result['labeled_recall'], 0.5)
        self.assertEqual(result['uncertain_labeled_pairs'], 1)
        self.assertEqual(result['labeled_pair_count'], 5)
        self.assertEqual(result['possible_pair_count'], 10)
        self.assertEqual(result['annotation_independence_verified'], False)
        self.assertEqual(result['paraphrase_query_recall'], 'not_evaluated')
        self.assertEqual(result['architect_acceptance'], 'not_evaluated')

    def test_zero_denominator_returns_null(self) -> None:
        """No labeled pairs cannot report perfect precision or recall."""
        labels = self.labels()
        labels['judgments'] = []
        result = evaluate(self.snapshot, labels)
        self.assertIsNone(result['labeled_precision'])
        self.assertIsNone(result['labeled_recall'])
        self.assertEqual(result['unlabeled_candidate_count'], 2)

    def test_stale_or_rewritten_labels_fail_closed(self) -> None:
        """Reject labels produced against a different candidate snapshot."""
        labels = self.labels()
        labels['projection_fingerprint'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'STALE_LABEL_SCOPE'):
            evaluate(self.snapshot, labels)

    def test_duplicate_unknown_and_unjustified_labels_fail(self) -> None:
        """Reject silent denominator and evidence-scope manipulation."""
        labels = self.labels()
        labels['judgments'].append(dict(labels['judgments'][0]))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            evaluate(self.snapshot, labels)
        labels = self.labels()
        labels['judgments'][0]['path'] = 'not-in-git.md'
        with self.assertRaisesRegex(ValueError, 'UNKNOWN_SOURCE'):
            evaluate(self.snapshot, labels)
        labels = self.labels()
        labels['judgments'][0]['basis'] = ''
        with self.assertRaisesRegex(ValueError, 'BASIS_REQUIRED'):
            evaluate(self.snapshot, labels)

    def test_missing_label_provenance_fails_closed(self) -> None:
        """A metric must refer to accountable independent judgments."""
        labels = self.labels()
        labels['annotation_reference'] = ''
        with self.assertRaisesRegex(ValueError, 'PROVENANCE_REQUIRED'):
            evaluate(self.snapshot, labels)

    def test_cannot_score_labels_when_model_missing(self) -> None:
        """A missing model cannot silently make external labels irrelevant."""
        labels = self.labels()
        (self.repo / 'sage-semantic-concepts.json').unlink()
        self.git('add', '-A')
        self.git('commit', '-qm', 'remove concept model')
        with self.assertRaisesRegex(ValueError, 'CANNOT_SCORE_LABELS'):
            assess(self.repo, labels)

    def test_missing_model_keeps_full_inventory_and_unknown_state(self) -> None:
        """Missing concept model must not fabricate absence or a zero score."""
        (self.repo / 'sage-semantic-concepts.json').unlink()
        self.git('add', '-A')
        self.git('commit', '-qm', 'model unavailable')
        report = assess(self.repo)
        self.assertEqual(report['status'], 'not_evaluated')
        self.assertEqual(report['reason'], 'CONCEPT_MODEL_ABSENT')
        self.assertEqual(report['source_count'], 4)
        self.assertTrue(report['source_inventory_preserved'])

    def test_no_labels_marks_not_evaluated(self) -> None:
        """Candidate coverage is not independent validation."""
        report = assess(self.repo)
        self.assertEqual(report['reason'], 'INDEPENDENT_LABELS_ABSENT')
        self.assertEqual(report['candidate_count'], 2)

    def test_dirty_worktree_does_not_change_committed_model(self) -> None:
        """Governed revision remains sole source for scoring inputs."""
        before = build_snapshot(self.repo)
        (self.repo / 'sage-semantic-concepts.json').write_text('bad data', 'utf-8')
        after = build_snapshot(self.repo)
        self.assertEqual(stable_hash(before), stable_hash(after))

    def test_malformed_committed_model_fails_closed(self) -> None:
        """Malformed model is distinct from a genuinely missing model."""
        (self.repo / 'sage-semantic-concepts.json').write_text('{broken', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'bad model')
        with self.assertRaises(json.JSONDecodeError):
            assess(self.repo)


if __name__ == '__main__':
    unittest.main(verbosity=2)
