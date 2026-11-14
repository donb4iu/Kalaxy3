#!/usr/bin/env python3
"""Regression tests for revision-pinned, content-aware candidates."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sage_neo4j_inventory import candidate_edges, prepare
from sage_neo4j_reconcile import reconcile, revision_inventory


class ContentCandidateTests(unittest.TestCase):
    """Exercise actual Git revisions without trusting candidate matches."""

    def setUp(self) -> None:
        """Construct a committed corpus with separate content and path evidence."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Content Fixture')
        self.model = self.repo / 'sage-semantic-concepts.json'
        self.model.write_text(json.dumps({'concepts': {
            'networking': {'terms': ['private LAN access'],
                           'related': [], 'dimensions': []},
            'unused': {'terms': ['unseen phrase'],
                       'related': [], 'dimensions': []}}}), 'utf-8')
        (self.repo / 'docs.md').write_text(
            'Private LAN access is a requirement.\n', 'utf-8')
        (self.repo / 'opaque.dat').write_bytes(b'\x00private LAN access\x00')
        self.git('add', '-A')
        self.git('commit', '-qm', 'original')
        self.before = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args: str) -> str:
        """Execute fixture Git operation and capture its standard output.

        Args:
            args: Git CLI arguments following -C and repository path.
        """
        return subprocess.check_output(
            ['git', '-C', str(self.repo), *args], text=True)

    def test_content_only_match_remains_unverified(self) -> None:
        """Content cues nominate a source while preserving evidence status."""
        projection = prepare(self.repo, self.model)
        matches = [edge for edge in projection['candidate_edges']
                   if edge['concept'] == 'networking']
        self.assertEqual(len(matches), 1)
        self.assertNotIn('sage-semantic-concepts.json',
                         [row['path'] for row in projection['sources']
                          if row['identity'] == matches[0]['source_id']])
        self.assertEqual(matches[0]['match_surfaces'], ['content'])
        self.assertEqual(matches[0]['state'], 'candidate_unverified')
        self.assertEqual(projection['qualification'], 'candidate_only')
        self.assertEqual(len(projection['sources']), 3)
        self.assertTrue(all('Private LAN access is a requirement' not in
                            json.dumps(row) for row in projection['sources']))

    def test_no_binary_matching_or_missing_evidence_claim(self) -> None:
        """Binary sources remain counted and empty concepts remain empty."""
        projection = prepare(self.repo, self.model)
        self.assertFalse(any(edge['concept'] == 'unused'
                             for edge in projection['candidate_edges']))
        self.assertFalse(any(edge['concept'] == 'networking' and
                             edge['source_id'] == source['identity']
                             for source in projection['sources']
                             if source['path'] == 'opaque.dat'
                             for edge in projection['candidate_edges']))
        self.assertTrue(any(row['path'] == 'opaque.dat'
                            for row in projection['sources']))

    def test_reconcile_deleted_content_candidates(self) -> None:
        """Removing source content removes its candidate without losing source."""
        (self.repo / 'docs.md').write_text('No recognized cue.\n', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'remove content evidence')
        result = reconcile(revision_inventory(self.repo, self.before),
                           revision_inventory(self.repo, 'HEAD'))
        self.assertEqual(result['source_changes']['modified'], ['docs.md'])
        self.assertEqual(result['removed_candidate_links'],
                         [('docs.md', 'networking')])
        self.assertEqual(result['candidate_comparison_state'], 'evaluated')
        self.assertEqual(result['semantic_relationships_established'], 0)

    def test_content_scan_optional_and_existing_path_behavior(self) -> None:
        """Legacy two-argument calls remain strictly path-based candidates."""
        snapshot = prepare(self.repo, self.model)
        path_only = candidate_edges(snapshot['sources'], snapshot['concepts'])
        self.assertEqual(path_only, [])
        self.assertTrue(snapshot['candidate_edges'])

    def test_committed_snapshot_ignores_dirty_worktree(self) -> None:
        """Uncommitted changes must never influence source-bound matching."""
        before = prepare(self.repo, self.model)
        (self.repo / 'docs.md').write_text('No matching content now.\n', 'utf-8')
        after = prepare(self.repo, self.model)
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
