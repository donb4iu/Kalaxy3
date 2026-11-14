#!/usr/bin/env python3
"""New Issue #50 evidence-attested context and baseline retrieval contracts."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterator

from sage_neo4j_context import (heading_kind, root_governance_sources,
                                source_sections)
from sage_neo4j_inventory import prepare, source_records
from sage_neo4j_objective import objective_evidence
from sage_neo4j_projection import build_projection


class GitContextFixture(unittest.TestCase):
    """Capture a genuinely committed miniature SAGE evidence corpus."""

    def setUp(self) -> None:
        """Initialize independent source, governance and opaque evidence."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(['git', '-C', str(self.repo), 'init', '-q'], check=True)
        self.git('config', 'user.email', 'context@example.invalid')
        self.git('config', 'user.name', 'Source Context Fixture')
        (self.repo / 'AGENTS.md').write_text(
            '# Repository Instructions\n## Requirements\nFollow repo process.\n', 'utf-8')
        (self.repo / 'architecture.md').write_text(
            '# Architecture Decision: Longhorn\n## Context\nBefore.\n'
            '## Alternatives Considered\nOption A.\n## Decision\nChoice B.\n'
            '## Consequences\nAfter.\n', 'utf-8')
        (self.repo / 'opaque.bin').write_bytes(b'\x00secret')
        (self.repo / 'sage-semantic-concepts.json').write_text(json.dumps({
            'concepts': {'longhorn': {'terms': ['Longhorn'], 'related': [],
                                     'dimensions': []}}}), 'utf-8')
        self.git('add', '-A')
        self.git('commit', '-qm', 'pinned governed evidence')
        self.revision = self.git('rev-parse', 'HEAD')

    def git(self, *args: str) -> str:
        """Run Git only inside the disposable test repository.

        Args:
            args: Arguments to pass to Git.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True).strip()

    def test_attested_sections_are_not_verdicts(self) -> None:
        """Expose literal headings and bytes, not accepted historical choices."""
        sources = source_records(self.repo, self.revision)
        result = source_sections(self.repo, sources)
        kinds = [row['kind'] for row in result if row['source_path'] == 'architecture.md']
        self.assertEqual(kinds, ['context_section', 'alternatives_section',
                                 'decision_section', 'consequences_section'])
        self.assertTrue(all(row['revision'] == self.revision for row in result))
        self.assertTrue(all(row['semantic_qualification'] == 'not_evaluated'
                            for row in result))
        self.assertTrue(all(len(row['section_sha256']) == 64 for row in result))
        self.assertNotIn('Choice B.', json.dumps(result))

    def test_uncommitted_edits_cannot_rewrite_history(self) -> None:
        """Prove Git object provenance excludes uncommitted history rewrites."""
        sources = source_records(self.repo, self.revision)
        first = source_sections(self.repo, sources)
        (self.repo / 'architecture.md').write_text('# Different Decision\n', 'utf-8')
        self.assertEqual(first, source_sections(self.repo, sources))

    def test_governance_pointer_is_a_path_not_a_claim(self) -> None:
        """Include real root authority pointers without inferred applicability."""
        sources = source_records(self.repo, self.revision)
        roots = root_governance_sources(sources)
        self.assertEqual([row['source_path'] for row in roots], ['AGENTS.md'])
        self.assertEqual(roots[0]['semantic_qualification'], 'not_evaluated')
        self.assertEqual(roots[0]['revision'], self.revision)
        self.assertEqual(heading_kind('Alternatives Considered'),
                         'alternatives_section')
        self.assertIsNone(heading_kind('Approved'))

    def test_new_graph_edges_are_scoped_and_counted(self) -> None:
        """Root pointers and literal sections must appear in count verification."""
        payload = prepare(self.repo, self.repo / 'sage-semantic-concepts.json')
        session = WriteSession(payload)
        result = build_projection(session, payload)
        self.assertEqual(result['observed']['source_sections'], 5)
        self.assertEqual(result['observed']['root_governance_sources'], 1)
        self.assertTrue(any('MERGE (e)-[:SECTION_OF]->(s)' in query
                            for query in session.queries))
        self.assertTrue(any('ROOT_GOVERNANCE_POINTER' in query
                            for query in session.queries))
        self.assertTrue(any("p.state='candidate'" in query
                            for query in session.queries))


    def test_prepare_preserves_complete_source_universe(self) -> None:
        """Prepared graph includes opaque files and exact section provenance."""
        payload = prepare(self.repo, self.repo / 'sage-semantic-concepts.json')
        self.assertEqual(len(payload['sources']), 4)
        self.assertEqual(len(payload['source_sections']), 5)
        self.assertEqual(len(payload['root_governance_sources']), 1)
        self.assertEqual(payload['qualification'], 'candidate_only')


class Result:
    """Minimal read-only Neo4j response used for context-specific tests."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Remember exact query results.

        Args:
            rows: Neo4j-compatible result records.
        """
        self.rows = rows

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate stored result records."""
        return iter(self.rows)

    def single(self, **_options: Any) -> dict[str, Any] | None:
        """Return the first record or the absence state."""
        return self.rows[0] if self.rows else None


class ReadContextSession:
    """Model only the new attested-context queries and no-match boundaries."""

    def __init__(self, has_roots: bool = True) -> None:
        """Set whether the committed projection has a root instruction.

        Args:
            has_roots: Whether provenance-backed governance pointers exist.
        """
        self.has_roots = has_roots
        self.queries: list[str] = []

    def run(self, query: str, **params: Any) -> Result:
        """Answer only explicitly allowed Cypher read paths.

        Args:
            query: Parameterized Neo4j query.
            params: Exact projection and page-scoped input parameters.
        """
        self.queries.append(query)
        if 'RETURN p.state AS state' in query:
            return Result([{'state': 'candidate'}])
        if 'RETURN c.uid AS uid, c.name AS name' in query:
            return Result([])
        if 'ROOT_GOVERNANCE_POINTER' in query:
            return Result([{'uid': 'p:agent', 'path': 'AGENTS.md',
                            'semantic_qualification': 'not_evaluated'}]
                          if self.has_roots else [])
        if 'SageRelationClaim' in query:
            return (Result([{'total': 0}]) if 'count(DISTINCT c)' in query
                    else Result([]))
        if 'SageEvidenceSection' in query:
            if 'count(e)' in query:
                return Result([{'total': 2}])
            sections = [{'uid': f'p:sec-{i}', 'source_path': 'AGENTS.md',
                         'kind': 'obligations_section',
                         'semantic_qualification': 'not_evaluated'}
                        for i in (1, 2)]
            return Result(sections[params['offset']:][:params['limit']])
        raise AssertionError(f'Unexpected query: {query}')


class ContextRetrievalTests(unittest.TestCase):
    """Protect independent governance context from lexical mapping failures."""

    def test_unmatched_objective_still_retrieves_root_context(self) -> None:
        """No matched concept must not erase repository-root source pointers."""
        session = ReadContextSession()
        result = objective_evidence(session, 'p', 'Novel engineering objective',
                                    section_limit=1)
        self.assertEqual(result['matching_status'], 'no_explicit_alias_match')
        self.assertEqual([row['path'] for row in result['governance_source_pointers']],
                         ['AGENTS.md'])
        self.assertEqual(len(result['context_sections']), 1)
        self.assertEqual(result['next_section_offset'], 1)
        self.assertEqual(result['evidence_presence'], 'not_evaluated')
        self.assertTrue(result['broader_inventory_available'])
        self.assertFalse(any('MERGE ' in query or ' SET ' in query
                             for query in session.queries))

    def test_absent_baseline_cannot_become_evidence_absence(self) -> None:
        """Missing root pointers must not fabricate qualified no-evidence."""
        result = objective_evidence(ReadContextSession(False), 'p',
                                    'Novel engineering objective')
        self.assertEqual(result['governance_source_pointers'], [])
        self.assertEqual(result['context_sections'], [])
        self.assertEqual(result['evidence_presence'], 'not_evaluated')
        self.assertIsNone(result['next_section_offset'])


class WriteResponse:
    """Emulate successful Neo4j writes and exact count verification."""

    def __init__(self, count: int = 0) -> None:
        """Store the observed fixture record count.

        Args:
            count: Independently prepared graph record count.
        """
        self.count = count

    def consume(self) -> None:
        """Accept a successful parameterized graph write."""

    def single(self, **_options: Any) -> dict[str, Any]:
        """Return one count row or an accepted projection header."""
        return {'count': self.count, 'id': 'fixture-projection'}


class WriteSession:
    """Record Neo4j write queries without requiring a running graph server."""

    def __init__(self, payload: dict[str, Any]) -> None:
        """Bind expected cardinalities to the exact prepared Git snapshot.

        Args:
            payload: One committed fixture projection.
        """
        self.expected = {
            'sources': len(payload['sources']),
            'concepts': len(payload['concepts']),
            'candidate_edges': len(payload['candidate_edges']),
            'source_links': len(payload.get('explicit_source_links', [])),
            'sections': len(payload['source_sections']),
            'governance': len(payload['root_governance_sources']),
        }
        self.queries: list[str] = []

    def run(self, query: str, **_params: Any) -> WriteResponse:
        """Return the exact expected count for each distinct typed edge.

        Args:
            query: Neo4j Cypher statement.
            _params: Parameter bindings, which never define authority.
        """
        self.queries.append(query)
        if 'RETURN count(' not in query:
            return WriteResponse()
        if 'ROOT_GOVERNANCE_POINTER' in query:
            return WriteResponse(self.expected['governance'])
        if 'SageEvidenceSection' in query:
            return WriteResponse(self.expected['sections'])
        if 'REFERENCES_SOURCE' in query:
            return WriteResponse(self.expected['source_links'])
        if 'CANDIDATE_CONCEPT' in query:
            return WriteResponse(self.expected['candidate_edges'])
        if 'SageConcept' in query:
            return WriteResponse(self.expected['concepts'])
        return WriteResponse(self.expected['sources'])

    def execute_write(self, callback: Any, *args: Any) -> None:
        """Execute the actual adapter write routine against a recording session.

        Args:
            callback: Repository-owned graph transaction adapter.
            args: Parameters supplied to the adapter.
        """
        callback(self, *args)


class NeighborSession(ReadContextSession):
    """Expose one literal source-reference hop and its section headings."""

    def run(self, query: str, **params: Any) -> Result:
        """Supply source, link, and context rows without creating graph facts.

        Args:
            query: Scoped read-only query.
            params: Projection, source IDs and pagination bindings.
        """
        if 'RETURN c.uid AS uid, c.name AS name' in query:
            return Result([{'uid': 'p:storage', 'name': 'storage',
                            'aliases': ['Longhorn']}])
        if 'RETURN DISTINCT b.uid' in query:
            return Result([])
        if 'RETURN count(DISTINCT s) AS total' in query:
            return Result([{'total': 1}])
        if 'WITH s, collect(DISTINCT c.name)' in query:
            return Result([{'uid': 'p:selected', 'path': 'longhorn.md'}])
        if 'RETURN DISTINCT startNode(link).uid' in query:
            return Result([{'from_uid': 'p:selected', 'to_uid': 'p:neighbor',
                            'related_uid': 'p:neighbor',
                            'related_path': 'decision.md'}])
        if 'SageEvidenceSection' in query:
            assert 'p:neighbor' in params['uids']
            return (Result([{'total': 1}]) if 'count(e)' in query else
                    Result([{'source_path': 'decision.md',
                             'kind': 'alternatives_section'}]))
        return super().run(query, **params)


class RelatedContextTests(unittest.TestCase):
    """Keep bounded source-to-source traversal distinct from semantic verdicts."""

    def test_existing_source_reference_exposes_neighbor_history(self) -> None:
        """A referenced decision's attested alternatives become discoverable."""
        result = objective_evidence(NeighborSession(), 'p', 'Deploy Longhorn')
        self.assertEqual(result['literal_source_links'][0]['related_path'],
                         'decision.md')
        self.assertEqual(result['context_sections'][0]['kind'],
                         'alternatives_section')
        self.assertEqual(result['evidence_presence'], 'not_evaluated')


if __name__ == '__main__':
    unittest.main(verbosity=2)
