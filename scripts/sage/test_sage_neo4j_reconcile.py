#!/usr/bin/env python3
"""Validate governed revision delta accounting for SAGE Issue #50."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sage_neo4j_reconcile import (candidate_pairs, compare_sources,
                                  reconcile, revision_inventory)


class SourceLifecycleTests(unittest.TestCase):
    """Test exact source lineage across feature-branch revisions."""

    def setUp(self) -> None:
        """Create a minimal committed corpus and associated concept vocabulary."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        (self.repo / 'longhorn.md').write_text('a', encoding='utf-8')
        (self.repo / 'obsolete.md').write_text('b', encoding='utf-8')
        (self.repo / 'sage-semantic-concepts.json').write_text(json.dumps({
            'concepts': {'storage': {'terms': ['longhorn'], 'related': [],
                                     'dimensions': []}}}), 'utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'before')
        self.before = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args: str) -> str:
        """Run an isolated Git command.

        Args:
            args: Git subcommand and parameters.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args]).decode()

    def mutate(self) -> None:
        """Add, remove, and modify evidence within a new Git commit."""
        (self.repo / 'longhorn.md').write_text('changed', encoding='utf-8')
        (self.repo / 'new.md').write_text('new', encoding='utf-8')
        (self.repo / 'obsolete.md').unlink()
        self.git('add', '-A')
        self.git('commit', '-qm', 'after')

    def test_full_revision_delta(self) -> None:
        """Keep complete, disjoint add/change/remove/unchanged path sets."""
        self.mutate()
        old = revision_inventory(self.repo, self.before)
        new = revision_inventory(self.repo, 'HEAD')
        result = reconcile(old, new)
        self.assertEqual(result['source_changes']['added'], ['new.md'])
        self.assertEqual(result['source_changes']['removed'], ['obsolete.md'])
        self.assertEqual(result['source_changes']['modified'], ['longhorn.md'])
        self.assertEqual(len(result['source_changes']['unchanged']), 1)
        self.assertEqual(result['semantic_relationships_established'], 0)
        self.assertFalse(result['active_projection_mutated'])

    def test_candidate_links_preserved_by_path(self) -> None:
        """A content change does not falsely invent a new semantic relationship."""
        old = revision_inventory(self.repo, self.before)
        self.mutate()
        new = revision_inventory(self.repo, 'HEAD')
        self.assertEqual(candidate_pairs(old), candidate_pairs(new))
        self.assertEqual(reconcile(old, new)['new_candidate_links'], [])

    def test_duplicate_path_fails(self) -> None:
        """Fail closed on duplicated paths that could corrupt coverage counts."""
        source = [{'path': 'a', 'content_sha256': 'h', 'mode': '100644'}]
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            compare_sources(source + source, source)

    def test_dirty_worktree_does_not_change_committed_inventory(self) -> None:
        """Uncommitted evidence must not contaminate a governed snapshot."""
        before = revision_inventory(self.repo, self.before)
        (self.repo / 'longhorn.md').write_text('dirty', encoding='utf-8')
        after = revision_inventory(self.repo, self.before)
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main(verbosity=2)
