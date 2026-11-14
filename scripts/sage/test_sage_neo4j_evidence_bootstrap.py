#!/usr/bin/env python3
"""Real-Git regressions for production evidence and WIP model discovery."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sage_neo4j_evidence_bootstrap import bootstrap
from sage_neo4j_review import build_review, label_template
from sage_neo4j_benchmark import LABELS_SCHEMA, evaluate
from sage_neo4j_projection import build_projection


class RecordingResponse:
    """Minimal transaction response, not a live Neo4j result."""

    def __init__(self, result: int = 0) -> None:
        """Store a precomputed fixture count.

        Args:
            result: Expected record count.
        """
        self.result = result

    def consume(self) -> None:
        """Simulate Neo4j query completion."""

    def single(self, **_options: Any) -> dict[str, int]:
        """Report the recorded fixture count."""
        return {'count': self.result}


class RecordingSession:
    """Capture parameterized Cypher for adapter contract tests."""

    def __init__(self, expected: dict[str, int]) -> None:
        """Store expected source and relationship populations.

        Args:
            expected: Inventoried counts for all Neo4j record types.
        """
        self.expected = expected
        self.statements: list[str] = []

    def run(self, query: str, **_args: Any) -> RecordingResponse:
        """Emulate only the count interface and capture Cypher text.

        Args:
            query: Neo4j Cypher statement.
            _args: Statement parameters.
        """
        self.statements.append(query)
        if 'RETURN count(' in query:
            key = ('source_links' if 'REFERENCES_SOURCE' in query else
                   'candidate_edges' if 'CANDIDATE_CONCEPT' in query else
                   'concepts' if 'SageConcept' in query else 'sources')
            return RecordingResponse(self.expected[key])
        return RecordingResponse()

    def execute_write(self, callback: Any, *args: Any) -> Any:
        """Invoke the existing graph adapter without a live database.

        Args:
            callback: Existing transaction function.
            args: Arguments supplied to the function.
        """
        return callback(self, *args)


class EvidenceBootstrapTests(unittest.TestCase):
    """Prove that no pre-existing ontology or deployed graph is required."""

    def setUp(self) -> None:
        """Construct divergent main and feature Git history without any vocabulary."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Evidence Fixture')
        docs = self.repo / 'markdown/standards'
        docs.mkdir(parents=True)
        (docs / 'architecture.md').write_text(
            '# Kalaxy3 Evidence Architecture\nThe model preserves evidence.\n'
            '[Runbook](runbook.md)\n', 'utf-8')
        (docs / 'runbook.md').write_text('# Recovery Runbook\nRecover evidence.\n',
                                         'utf-8')
        (self.repo / 'sage-recovery-policy.json').write_text(json.dumps(
            {'policy_id': 'sage-recovery', 'notes': 'candidate only'}), 'utf-8')
        (self.repo / 'opaque.bin').write_bytes(b'\x00opaque\xff')
        self.git('add', '-A')
        self.git('commit', '-qm', 'governed base')
        self.base = self.git('rev-parse', 'HEAD')
        self.git('switch', '-qc', 'feature/issue50')
        (docs / 'feature.md').write_text(
            '# Semantic Projection\nProposed graph read model.\n', 'utf-8')
        (docs / 'runbook.md').write_text('# Recovery Runbook\nEdited branch.\n',
                                         'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'feature proposal')
        self.feature = self.git('rev-parse', 'HEAD')
        self.git('switch', 'main')
        (docs / 'operations.md').write_text(
            '# Observability Operations\nMonitored services.\n', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'main continues independently')
        self.main = self.git('rev-parse', 'HEAD')
        self.git('switch', 'feature/issue50')

    def git(self, *args: str) -> str:
        """Execute Git against the disposable committed fixture.

        Args:
            args: Git arguments following the fixture repository.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True).strip()

    def candidate(self) -> dict[str, Any]:
        """Resolve both independent Git lineages into candidate projections."""
        return bootstrap(self.repo, 'refs/heads/main', 'HEAD')

    def test_main_and_feature_keep_distinct_three_way_evidence(self) -> None:
        """Never misclassify newer main content as branch-deleted evidence."""
        result = self.candidate()
        self.assertEqual(result['main']['revision'], self.main)
        self.assertEqual(result['feature']['revision'], self.feature)
        self.assertEqual(result['three_way']['merge_base_revision'], self.base)
        main_delta = result['three_way']['main_changes']
        branch_delta = result['three_way']['feature_changes']
        self.assertEqual(main_delta['added'], ['markdown/standards/operations.md'])
        self.assertEqual(branch_delta['added'], ['markdown/standards/feature.md'])
        self.assertEqual(branch_delta['removed'], [])
        self.assertEqual(branch_delta['modified'], ['markdown/standards/runbook.md'])

    def test_no_vocabulary_still_generates_reviewable_model(self) -> None:
        """Source-anchored concepts feed existing unbiased review machinery."""
        result = self.candidate()
        main = result['main']
        feature = result['feature']
        self.assertEqual(len(main['sources']), 5)
        self.assertEqual(len(feature['sources']), 5)
        self.assertEqual(feature['model_origin'],
                         'derived_from_governed_git_evidence')
        self.assertEqual(feature['model_state'], 'evidence_derived_candidate')
        self.assertTrue(feature['concepts'])
        self.assertTrue(feature['candidate_edges'])
        self.assertFalse(feature['runtime_implementation_verified'])
        self.assertEqual(feature['semantic_relationships_established'], 0)
        review = build_review(feature, size=10)
        self.assertEqual(review['status'], 'ready_for_independent_annotation')
        self.assertFalse(review['predictions_exposed'])
        self.assertTrue(label_template(review)['judgments'])

    def test_candidate_model_benchmark_never_promotes_results(self) -> None:
        """Existing independent measurement accepts a provisional model only."""
        view = self.candidate()['feature']
        review = build_review(view, size=8)
        labels = label_template(review)
        labels['annotator'] = 'independent-fixture-reviewer'
        labels['annotation_reference'] = 'fixture:manual-judgment'
        for judgment in labels['judgments']:
            judgment['verdict'] = 'uncertain'
            judgment['basis'] = 'Unreviewed semantics fixture'
        self.assertEqual(labels['schema'], LABELS_SCHEMA)
        scored = evaluate(view, labels)
        self.assertEqual(scored['architect_acceptance'], 'not_evaluated')
        self.assertIsNone(scored['labeled_precision'])
        self.assertIsNone(scored['labeled_recall'])

    def test_concept_anchors_keep_origin_commit_and_digests(self) -> None:
        """Every generated concept must trace to immutable source evidence."""
        result = self.candidate()
        concepts = result['feature']['concepts']
        source = {(row['revision'], row['path']): row
                  for view in ('main', 'feature') for row in result[view]['sources']}
        for concept in concepts:
            self.assertEqual(concept['semantic_authority'], 'unverified_candidate')
            self.assertTrue(concept['origin_refs'])
            for origin in concept['origin_refs']:
                reference = source[(origin['revision'], origin['path'])]
                self.assertEqual(reference['content_sha256'], origin['sha256'])

    def test_explicit_links_are_source_references_not_dependencies(self) -> None:
        """Capture actual document links without inferring technical reliance."""
        links = self.candidate()['main']['explicit_source_links']
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['relation'], 'literal_document_link')
        self.assertEqual(links[0]['state'], 'source_reference_only')

    def test_dirty_worktree_cannot_change_derived_evidence(self) -> None:
        """Never allow local draft files to change a pinned model silently."""
        before = self.candidate()
        (self.repo / 'markdown/standards/feature.md').write_text(
            '# Uncommitted Replacement\n', 'utf-8')
        after = self.candidate()
        self.assertEqual(before, after)

    def test_new_main_revision_invalidates_feature_projection(self) -> None:
        """Baseline movement requires a new version-qualified candidate."""
        first = self.candidate()['feature']['fingerprint']
        self.git('switch', 'main')
        (self.repo / 'markdown/standards/operations.md').write_text(
            '# New Monitoring Operations\n', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'production changes')
        self.git('switch', 'feature/issue50')
        second = self.candidate()['feature']['fingerprint']
        self.assertNotEqual(first, second)

    def test_graph_writer_projects_document_links_with_provenance(self) -> None:
        """Existing Neo4j adapter represents explicit, scoped source references."""
        view = self.candidate()['main']
        expected = {'sources': len(view['sources']),
                    'concepts': len(view['concepts']),
                    'candidate_edges': len(view['candidate_edges']),
                    'source_links': len(view['explicit_source_links'])}
        statements: list[str] = []

        session = RecordingSession(expected)
        result = build_projection(session, view)
        self.assertEqual(result['observed']['source_links'], 1)
        self.assertTrue(any('MERGE (a)-[r:REFERENCES_SOURCE]' in text
                            for text in session.statements))
        self.assertTrue(any('c.origin_refs_json=row.origin_refs_json' in text
                            for text in session.statements))

    def test_invalid_main_ref_fails_closed(self) -> None:
        """Never silently use the branch checkout as a production baseline."""
        with self.assertRaises(subprocess.CalledProcessError):
            bootstrap(self.repo, 'refs/heads/unknown-main', 'HEAD')

    def test_cli_writes_private_reviewable_evidence(self) -> None:
        """Produce rev-pinned outputs without introducing Git modifications."""
        script = Path(__file__).with_name('sage-neo4j-evidence-bootstrap.py')
        destination = self.repo / 'review-output'
        status = subprocess.run([
            sys.executable, str(script), '--repo', str(self.repo),
            '--main-ref', 'refs/heads/main', '--out-dir', str(destination)],
            capture_output=True, text=True)
        self.assertEqual(status.returncode, 0, status.stderr)
        receipt = json.loads((destination / 'bootstrap-receipt.json').read_text())
        self.assertEqual(receipt['main_revision'], self.main)
        self.assertEqual(receipt['runtime_state'], 'not_evaluated')
        self.assertEqual(receipt['neo4j_activation'], 'not_authorized')
        self.assertTrue((destination / 'labels-template.json').exists())
        self.assertEqual((destination / 'review-packet.json').stat().st_mode & 0o777,
                         0o600)
        self.assertNotIn('Monitored services.', json.dumps(receipt))
        replay = subprocess.run([
            sys.executable, str(script), '--repo', str(self.repo),
            '--main-ref', 'refs/heads/main', '--out-dir', str(destination)],
            capture_output=True)
        self.assertNotEqual(replay.returncode, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
