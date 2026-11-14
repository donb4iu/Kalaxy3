"""Structural tests for unrestricted, source-complete semantic navigation."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any

from sage_neo4j_evidence_bootstrap import derive_concepts, snapshot
from sage_neo4j_inventory import source_records


class SemanticCorpusTests(unittest.TestCase):
    """Verify every source remains graph-reachable without a subject verdict."""

    def setUp(self) -> None:
        """Create a disposable, committed Git source universe."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Corpus Fixture')
        (self.repo / 'SAGE.md').write_text('# SAGE\n', encoding='utf-8')
        (self.repo / 'opaque.bin').write_bytes(b'\0\xff')
        (self.repo / 'unrelated.txt').write_text('unknown topic', encoding='utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'baseline')
        self.revision = self.git('rev-parse', 'HEAD')

    def git(self, *args: str) -> str:
        """Run Git in the disposable fixture only.

        Args:
            args: Git CLI arguments.
        """
        return subprocess.check_output(
            ['git', '-C', str(self.repo), *args], text=True
        ).strip()

    def view(self) -> dict[str, Any]:
        """Prepare a single-revision SAGE semantic snapshot."""
        sources = source_records(self.repo, self.revision)
        concepts = derive_concepts(self.repo, sources, 'pinned_revision')
        return snapshot(self.repo, self.revision, concepts, sources)

    def test_all_sources_have_a_corpus_concept_link(self) -> None:
        """Link every source, even opaque and semantically ambiguous evidence."""
        view = self.view()
        identities = {source['identity'] for source in view['sources']}
        members = [edge for edge in view['candidate_edges']
                   if edge['concept'] == 'full-repository-corpus']
        self.assertEqual({edge['source_id'] for edge in members}, identities)
        self.assertEqual(len(members), len(identities))
        self.assertTrue(all(edge['match_surfaces'] ==
                            ['git_corpus_membership'] for edge in members))
        root = next(concept for concept in view['concepts']
                    if concept['name'] == 'full-repository-corpus')
        self.assertEqual(root['origin_scope'], 'pinned_revision')
        self.assertFalse(view['candidate_seed_cap_reached'])
        self.assertIsNone(view['candidate_seed_limit'])

    def test_no_180_concept_cutoff(self) -> None:
        """Preserve every source-attested concept regardless of original seed cap."""
        for number in range(190):
            path = self.repo / f'subject_{number:03d}.md'
            path.write_text(f'# Distinct Subject {number:03d}\n', 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'many subjects')
        revision = self.git('rev-parse', 'HEAD')
        sources = source_records(self.repo, revision)
        concepts = derive_concepts(self.repo, sources, 'pinned_revision')
        self.assertGreaterEqual(len(concepts), 190)
        self.assertIn('distinct-subject-189',
                      {concept['name'] for concept in concepts})


class QueryResult:
    """Mock one Neo4j response without introducing a real graph server."""

    def __init__(self, entries: list[dict[str, Any]]) -> None:
        """Store test rows.

        Args:
            entries: Materialized result records.
        """
        self.entries = entries

    def __iter__(self) -> Any:
        """Yield the supplied graph rows."""
        return iter(self.entries)

    def single(self) -> dict[str, Any] | None:
        """Get the first record, if any."""
        return self.entries[0] if self.entries else None


class QuerySession:
    """Reject any Cypher that filters candidate usefulness."""

    def run(self, query: str, **kwargs: Any) -> QueryResult:
        """Return fixture metadata after inspecting the traversal.

        Args:
            query: Cypher statement under evaluation.
            kwargs: Query parameters.
        """
        if 'RETURN p.state AS state' in query:
            return QueryResult([{'state': 'candidate'}])
        self.assert_valid(query, kwargs)
        return QueryResult([{'nodes': [{'uid': 'p:s', 'path': 'x'}],
                             'relationships': [{'type': 'CANDIDATE_CONCEPT',
                                                'metadata': {'state': 'trial'}}]}])

    @staticmethod
    def assert_valid(query: str, kwargs: dict[str, Any]) -> None:
        """Check undirected paths and direct metadata exposure.

        Args:
            query: Generated graph walk Cypher.
            kwargs: Parameter bindings.
        """
        assert 'CLAIM_EVIDENCE*1..2]-(other)' in query
        assert 'metadata:properties(r)' in query
        assert 'semantic_qualification=' not in query
        assert kwargs['anchor'] == 'p:s'


class WalkTests(unittest.TestCase):
    """Check that traversal exposes both edge directions and source metadata."""

    def test_bidirectional_walk_preserves_relationship_metadata(self) -> None:
        """Do not use state or inferred relevance to suppress any path."""
        from sage_neo4j_objective import semantic_walk

        result = semantic_walk(QuerySession(), 'p', 'p:s', depth=2)
        self.assertEqual(len(result['paths']), 1)
        self.assertEqual(result['paths'][0]['relationships'][0]['metadata'],
                         {'state': 'trial'})
        self.assertEqual(result['interpretation'],
                         'unfiltered_graph_navigation_only')

    def test_corpus_membership_does_not_hide_unclassified_sources(self) -> None:
        """Preserve the distinction between corpus membership and topic mapping."""
        from sage_neo4j_objective import inventory_page
        from test_sage_neo4j_objective import FakeSession

        session = FakeSession()
        result = inventory_page(session, 'p', unmapped_only=True)
        queries = [query for query, _ in session.calls]
        self.assertEqual(result['total_sources'], 1)
        self.assertTrue(any("c.name <> 'full-repository-corpus'" in query
                            for query in queries))

    def test_walk_validates_only_mechanical_bounds(self) -> None:
        """Validate transport limits without assessing evidence relevance."""
        from sage_neo4j_objective import semantic_walk

        with self.assertRaisesRegex(ValueError, 'INVALID_GRAPH_WALK_DEPTH'):
            semantic_walk(None, 'p', 'p:s', depth=4)
        with self.assertRaisesRegex(ValueError, 'INVALID_GRAPH_WALK_ANCHOR'):
            semantic_walk(None, 'p', 'other:s')


if __name__ == '__main__':
    unittest.main()
