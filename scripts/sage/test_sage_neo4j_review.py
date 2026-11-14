#!/usr/bin/env python3
"""Blinded review protocol regressions over independently committed Git fixtures."""

from __future__ import annotations

import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sage_neo4j_benchmark import build_snapshot
from sage_neo4j_review import (build_review, label_template, score_review,
                               select_pairs)


class ReviewTests(unittest.TestCase):
    """Require complete, blinded and version-pinned independent review scope."""

    def setUp(self) -> None:
        """Create positive, negative and paraphrased source cases in Git."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Review Fixture')
        (self.repo / 'exact.md').write_text('longhorn persistent disk\n', 'utf-8')
        (self.repo / 'false.md').write_text('longhorn wallpaper\n', 'utf-8')
        (self.repo / 'paraphrase.md').write_text(
            'State survives restart across server replacements.\n', 'utf-8')
        (self.repo / 'negative.md').write_text('unrelated subject\n', 'utf-8')
        model = {'concepts': {'storage': {'terms': ['longhorn']},
                              'governance': {'terms': ['authority']}}}
        (self.repo / 'sage-semantic-concepts.json').write_text(
            json.dumps(model), encoding='utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'independent review fixture')
        self.snapshot = build_snapshot(self.repo)

    def git(self, *args: str) -> str:
        """Invoke Git with fixture-local authority and no global writes.

        Args:
            args: Git arguments applied to the temporary repository.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True).strip()

    def labels(self, review: dict[str, Any]) -> dict[str, Any]:
        """Create independent fixture labels for every selected pair.

        Args:
            review: Blinded revision-bound review case set.
        """
        record = label_template(review)
        record['annotator'] = 'independent-fixture-author'
        record['annotation_reference'] = 'fixture:explicit-expert-judgment'
        for item in record['judgments']:
            is_storage = item['concept'] == 'storage'
            relevant = item['path'] in {'exact.md', 'paraphrase.md'}
            item['verdict'] = 'relevant' if is_storage and relevant else 'irrelevant'
            item['basis'] = 'Human fixture author independently assessed source'
        return record

    def test_packet_is_blinded_and_pinned(self) -> None:
        """Matcher outcomes and raw source bodies must not leak to review."""
        review = build_review(self.snapshot, size=10, seed=7)
        serialized = json.dumps(review)
        self.assertEqual(review['status'], 'ready_for_independent_annotation')
        self.assertNotIn('candidate_unverified', serialized)
        self.assertNotIn('match_surfaces', serialized)
        self.assertNotIn('wallpaper', serialized)
        self.assertFalse(review['source_bodies_exported'])
        self.assertEqual(review['sampled_pair_count'], 10)
        self.assertEqual(len({(x['path'], x['concept'])
                              for x in review['review_cases']}), 10)

    def test_deterministic_seed_and_complete_pair_sampling(self) -> None:
        """Repeatable sample includes nominated and unnominated pairs."""
        first = select_pairs(self.snapshot, 10, 17)
        second = select_pairs(self.snapshot, 10, 17)
        self.assertEqual(first, second)
        self.assertIn(('paraphrase.md', 'storage'), first)
        self.assertIn(('false.md', 'storage'), first)
        with self.assertRaisesRegex(ValueError, 'OUT_OF_RANGE'):
            select_pairs(self.snapshot, 1, 0)

    def test_blank_review_cannot_be_scored(self) -> None:
        """Empty judgment fields are not counted as uncertain or negative."""
        review = build_review(self.snapshot, size=10)
        with self.assertRaisesRegex(ValueError, 'PROVENANCE_REQUIRED'):
            score_review(self.snapshot, review, label_template(review))

    def test_fixture_independent_labels_expose_misses(self) -> None:
        """Measured recall cannot conceal an unnamed-storage paraphrase."""
        review = build_review(self.snapshot, size=10)
        report = score_review(self.snapshot, review, self.labels(review))
        self.assertEqual(report['true_positive'], 1)
        self.assertEqual(report['false_positive'], 1)
        self.assertEqual(report['false_negative'], 1)
        self.assertEqual(report['labeled_precision'], .5)
        self.assertEqual(report['labeled_recall'], .5)
        self.assertFalse(report['sample_is_population_representative'])
        self.assertEqual(report['architect_acceptance'], 'not_evaluated')

    def test_no_dropped_cases_or_duplicate_labels(self) -> None:
        """A reviewer cannot omit a difficult case without an explicit failure."""
        review = build_review(self.snapshot, size=10)
        labels = self.labels(review)
        labels['judgments'].pop()
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
            score_review(self.snapshot, review, labels)
        labels = self.labels(review)
        labels['judgments'].append(dict(labels['judgments'][0]))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            score_review(self.snapshot, review, labels)

    def test_replaced_review_packet_does_not_reuse_annotations(self) -> None:
        """Labels remain bound to the exact originally issued review packet."""
        review = build_review(self.snapshot, size=10)
        labels = self.labels(review)
        review['selection_seed'] = 9999
        with self.assertRaisesRegex(ValueError, 'REVIEW_PACKET_TAMPERED'):
            score_review(self.snapshot, review, labels)

    def test_new_revision_fails_closed(self) -> None:
        """Changes to source Git history invalidate previously sampled pairs."""
        review = build_review(self.snapshot, size=10)
        labels = self.labels(review)
        (self.repo / 'new.md').write_text('new authority reference', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'source changed')
        with self.assertRaisesRegex(ValueError, 'STALE_REVIEW_SNAPSHOT'):
            score_review(build_snapshot(self.repo), review, labels)

    def test_cli_writes_local_review_without_scores(self) -> None:
        """CLI generates a blinded case set without modifying the Git tree."""
        output = self.repo / 'out'
        script = Path(__file__).with_name('sage-neo4j-review.py')
        run = subprocess.run([sys.executable, str(script), '--repo',
                              str(self.repo), '--out-dir', str(output)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        packet = json.loads((output / 'review-packet.json').read_text('utf-8'))
        self.assertEqual(packet['status'], 'ready_for_independent_annotation')
        self.assertEqual((output / 'review-packet.json').stat().st_mode & 0o777, 0o600)
        self.assertTrue((output / 'labels-template.json').is_file())
        duplicate = subprocess.run([sys.executable, str(script), '--repo',
                                    str(self.repo), '--out-dir', str(output)],
                                   capture_output=True)
        self.assertNotEqual(duplicate.returncode, 0)

    def test_missing_model_reports_not_evaluated(self) -> None:
        """Preserve revision and inventory without guessing a vocabulary."""
        (self.repo / 'sage-semantic-concepts.json').unlink()
        self.git('add', '-A')
        self.git('commit', '-qm', 'remove model')
        snapshot = build_snapshot(self.repo)
        review = build_review(snapshot)
        self.assertEqual(review['status'], 'not_evaluated')
        self.assertEqual(review['reason'], 'CONCEPT_MODEL_ABSENT')
        self.assertEqual(review['source_count'], 4)
        with self.assertRaisesRegex(ValueError, 'REVIEW_NOT_READY'):
            label_template(review)


if __name__ == '__main__':
    unittest.main(verbosity=2)
