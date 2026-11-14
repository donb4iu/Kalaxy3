#!/usr/bin/env python3
"""Issue #50 semantic projection contract tests without a live Neo4j server."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

MODULES = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULES))

from sage_neo4j_inventory import (candidate_edges, concept_records, cue_match,
                                  prepare, tree_entries)
from sage_neo4j_lifecycle import (activation_gate, ensure_lossless,
                                  ensure_reverse_links, evaluate_presence,
                                  projection_id, verify_patch)
from sage_neo4j_projection import chunks


class InventoryTests(unittest.TestCase):
    """Validate source enumeration and untrusted semantics."""

    def setUp(self) -> None:
        """Create a real isolated Git repository fixture."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.email',
                        'test@example.invalid'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'config', 'user.name',
                        'Test Fixture'], check=True)
        (self.root / 'longhorn-setup.md').write_text('storage service\n', 'utf-8')
        (self.root / 'unclassified.zz').write_bytes(b'\0binary\0')
        (self.root / 'sage-semantic-concepts.json').write_text(
            json.dumps({'concepts': {'storage': {
                'terms': ['longhorn', 'persistent volume'],
                'related': [], 'dimensions': []}, 'unseen': {
                'terms': ['not present'], 'related': [], 'dimensions': []}}}), 'utf-8')
        self.commit('initial')

    def commit(self, message: str) -> None:
        """Commit fixture changes to construct a governed revision.

        Args:
            message: Revision label.
        """
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.root), 'commit', '-qm', message],
                       check=True)

    def test_full_inventory_and_concept_absence(self) -> None:
        """Never omit binary paths or invent evidence for an empty concept."""
        payload = prepare(self.root, self.root / 'sage-semantic-concepts.json')
        self.assertEqual(len(payload['sources']), 3)
        self.assertIn('unclassified.zz', {s['path'] for s in payload['sources']})
        self.assertEqual(len(payload['concepts']), 2)
        self.assertTrue(any(e['concept'] == 'storage'
                            for e in payload['candidate_edges']))
        self.assertEqual(evaluate_presence('unseen', [], True),
                         'none_found_in_qualified_scope')
        self.assertEqual(evaluate_presence('unseen', [], False), 'not_evaluated')
        self.assertEqual(evaluate_presence('storage', payload['candidate_edges'], True),
                         'not_evaluated')
        self.assertEqual(payload['qualification'], 'candidate_only')

    def test_lossless_source_detects_drop(self) -> None:
        """Prevent denominator cheating through source omission."""
        payload = prepare(self.root, self.root / 'sage-semantic-concepts.json')
        expected = {row['path'] for row in payload['sources']}
        ensure_lossless(payload['sources'], expected)
        with self.assertRaises(ValueError):
            ensure_lossless(payload['sources'][:-1], expected)

    def test_commit_changes_projection_identity(self) -> None:
        """New evidence revisions cannot silently reuse the prior graph."""
        before = prepare(self.root, self.root / 'sage-semantic-concepts.json')
        (self.root / 'longhorn-setup.md').write_text('changed storage\n', 'utf-8')
        self.commit('change')
        after = prepare(self.root, self.root / 'sage-semantic-concepts.json')
        self.assertNotEqual(projection_id(before), projection_id(after))
        self.assertNotEqual(before['sources'][0]['revision'],
                            after['sources'][0]['revision'])

    def test_model_patch_and_unforeseen_gap(self) -> None:
        """Break-glass preserves evidence while extending the concepts."""
        before = prepare(self.root, self.root / 'sage-semantic-concepts.json')
        path = self.root / 'sage-semantic-concepts.json'
        model = json.loads(path.read_text('utf-8'))
        model['concepts']['new-relationship'] = {
            'terms': ['novel relation'], 'related': ['storage'], 'dimensions': []}
        path.write_text(json.dumps(model), 'utf-8')
        self.commit('governed model repair')
        after = prepare(self.root, path)
        verify_patch({'gap_id': 'gap-one', 'rationale': 'New evidence relation',
                      'governed_source_ref': 'fixture:commit',
                      'allowed_changed_paths': ['sage-semantic-concepts.json']},
                     before, after)
        self.assertEqual(len(after['concepts']), 3)

    def test_candidate_cues_do_not_create_authority(self) -> None:
        """Path matching does not establish proven semantic relationships."""
        concepts = concept_records({'concepts': {'storage': {
            'terms': ['longhorn'], 'related': [], 'dimensions': []}}})
        edges = candidate_edges([{'path': 'longhorn.md', 'identity': 'file'}], concepts)
        self.assertEqual(edges[0]['state'], 'candidate_unverified')
        self.assertTrue(cue_match('longhorn-setup.md', 'longhorn'))
        self.assertFalse(cue_match('longhorns.md', 'longhorn'))

    def test_binary_and_git_tree_paths_preserved(self) -> None:
        """Source tree includes binary evidence even when text scan skips it."""
        records = tree_entries(self.root, prepare(
            self.root, self.root / 'sage-semantic-concepts.json')['revision'])
        self.assertEqual(len(records), 3)
        self.assertTrue(all(row['git_oid'] for row in records))


class BoundaryTests(unittest.TestCase):
    """Protect governance and exact retrieval semantics."""

    def test_exact_reverse_links(self) -> None:
        """Verify two directions of the exact same established edge set."""
        edges = [{'source_id': 'f1', 'concept': 'storage'}]
        ensure_reverse_links(edges, {'f1': {'storage'}}, {'storage': {'f1'}})
        with self.assertRaises(ValueError):
            ensure_reverse_links(edges, {'f1': set()}, {'storage': {'f1'}})

    def test_activation_rejects_unverified_or_unqualified(self) -> None:
        """Never use a candidate or forged receipt to promote a projection."""
        qualified: dict[str, Any] = {'projection_id': 'p1',
                                     'all_mandatory_dod_passed': True}
        with self.assertRaises(PermissionError):
            activation_gate({}, 'p1', qualified, lambda _receipt: False)
        with self.assertRaises(PermissionError):
            activation_gate({'verified_by_existing_sage_authority': True,
                             'projection_id': 'p1'}, 'p1', {
                                 'projection_id': 'p1',
                                 'all_mandatory_dod_passed': False}, lambda _receipt: True)

    def test_graph_batches(self) -> None:
        """Bound transaction sizes and preserve ordering."""
        rows = [{'n': index} for index in range(305)]
        parts = list(chunks(rows))
        self.assertEqual([len(batch) for batch in parts], [150, 150, 5])
        self.assertEqual([record for batch in parts for record in batch], rows)


if __name__ == '__main__':
    unittest.main(verbosity=2)
