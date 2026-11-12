#!/usr/bin/env python3
"""Bounded objective-to-evidence graph retrieval tests without Neo4j server."""

from __future__ import annotations

import unittest
from typing import Any, Iterator

from sage_neo4j_objective import (caller_concepts, inventory_page, matching_concepts,
                                  objective_evidence, page_bounds)


class FakeResult:
    """Support only the read-only result operations used by the query adapter."""

    def __init__(self, values: list[dict[str, Any]]) -> None:
        """Construct a test result from explicit fixture values.

        Args:
            values: Rows returned by a fake read query.
        """
        self.values = values

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate through the fixture rows."""
        return iter(self.values)

    def single(self) -> dict[str, Any] | None:
        """Return the first fixture row, or None for an absent projection."""
        return self.values[0] if self.values else None


class FakeSession:
    """Represent one pinned candidate projection with typed relationships."""

    def __init__(self) -> None:
        """Create scoped concepts, candidate sources and literal links."""
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.concepts = [
            {'uid': 'p:storage', 'name': 'storage',
             'aliases': ['Longhorn', 'persistent volume']},
            {'uid': 'p:observability', 'name': 'observability',
             'aliases': ['logging', 'observability']},
            {'uid': 'p:unseen', 'name': 'unseen', 'aliases': ['never matched']},
        ]
        self.sources = [
            {'uid': 'p:source-1', 'path': 'longhorn.md', 'git_oid': '1' * 40,
             'content_sha256': '2' * 64, 'content_state': 'bounded_text',
             'mapping_state': 'not_evaluated', 'concepts': ['storage']},
            {'uid': 'p:source-2', 'path': 'unmapped.bin', 'git_oid': '3' * 40,
             'content_sha256': '4' * 64, 'content_state': 'uninspected',
             'mapping_state': 'not_evaluated', 'concepts': []},
        ]

    def run(self, query: str, **params: Any) -> FakeResult:
        """Return deterministic fixtures for read-only Cypher operations.

        Args:
            query: Neo4j read query under test.
            params: Query bindings and source-page constraints.
        """
        self.calls.append((query, params))
        if 'RETURN p.state AS state' in query:
            return FakeResult([{'state': 'candidate'}])
        if 'RETURN c.uid AS uid, c.name AS name' in query:
            return FakeResult(self.concepts)
        if 'RETURN DISTINCT b.uid AS uid' in query:
            return FakeResult([{'uid': 'p:observability', 'name': 'observability'}])
        if 'RETURN DISTINCT startNode(link).uid' in query:
            return FakeResult([{'from_uid': 'p:source-1', 'to_uid': 'p:source-2',
                                'related_path': 'unmapped.bin',
                                'semantic_authority': 'source_reference_only'}])
        if 'ROOT_GOVERNANCE_POINTER' in query:
            return FakeResult([])
        if 'SageRelationClaim' in query:
            return (FakeResult([{'total': 0}]) if 'count(DISTINCT c)' in query
                    else FakeResult([]))
        if 'SageEvidenceSection' in query:
            return FakeResult([{'total': 0}]) if 'count(e)' in query else FakeResult([])
        if 'RETURN count(DISTINCT s) AS total' in query:
            return FakeResult([{'total': 1}])
        if 'RETURN count(s) AS total' in query:
            return FakeResult([{'total': 1 if params['unmapped'] else 2}])
        if 'WITH s, collect(DISTINCT c.name)' in query:
            return FakeResult(self.sources[:1][params['offset']:][:params['limit']])
        if 'RETURN s.uid AS uid, s.path AS path' in query:
            rows = self.sources[1:] if params['unmapped'] else self.sources
            return FakeResult(rows[params['offset']:][:params['limit']])
        raise AssertionError(f'Unexpected Cypher query: {query}')


class ObjectiveRetrievalTests(unittest.TestCase):
    """Preserve candidate semantics, exact provenance, and open discovery."""

    def test_alias_matching_without_judgment(self) -> None:
        """Explicit aliases nominate entry points without claiming relevance."""
        concepts = FakeSession().concepts
        matches = matching_concepts('Deploy Longhorn storage', concepts)
        self.assertEqual([row['name'] for row in matches], ['storage'])
        self.assertEqual(matches[0]['relation'], 'explicit_phrase_candidate')
        self.assertEqual(matching_concepts('Deploy chatbot', concepts), [])
        resolved, unknown = caller_concepts(['storage', 'nonexistent'], concepts)
        self.assertEqual(resolved[0]['relation'], 'caller_proposed_candidate')
        self.assertEqual(unknown, ['nonexistent'])

    def test_provenance_and_one_hop(self) -> None:
        """Retrieve selected metadata and one documented reference hop."""
        session = FakeSession()
        result = objective_evidence(session, 'p', 'Monitor Longhorn', limit=1)
        self.assertEqual(result['sources'][0]['content_sha256'], '2' * 64)
        self.assertEqual(result['matched_concepts'][0]['name'], 'storage')
        self.assertEqual(result['related_concepts'][0]['name'], 'observability')
        self.assertEqual(result['literal_source_links'][0]['related_path'],
                         'unmapped.bin')
        self.assertEqual(result['evidence_presence'], 'not_evaluated')
        self.assertEqual(result['qualification'], 'candidate_only')
        self.assertTrue(all(call[1].get('id') == 'p' for call in session.calls))

    def test_no_match_is_unknown_not_no_evidence(self) -> None:
        """An unknown objective must not be treated as qualified source absence."""
        result = objective_evidence(FakeSession(), 'p', 'New chatbot')
        self.assertEqual(result['matching_status'], 'no_explicit_alias_match')
        self.assertEqual(result['total_candidate_sources'], 0)
        self.assertTrue(result['broader_inventory_available'])
        self.assertEqual(result['evidence_presence'], 'not_evaluated')

    def test_llm_seed_cannot_become_authority(self) -> None:
        """Allow candidate LLM concept nomination with explicit provenance."""
        result = objective_evidence(FakeSession(), 'p', 'New chatbot',
                                    proposed_concepts=['storage', 'not-a-concept'])
        self.assertEqual(result['caller_proposed_concepts'][0]['name'], 'storage')
        self.assertEqual(result['unknown_proposed_concepts'], ['not-a-concept'])
        self.assertEqual(result['total_candidate_sources'], 1)
        self.assertEqual(result['evidence_presence'], 'not_evaluated')

    def test_unmapped_and_full_inventory_are_reachable(self) -> None:
        """Expose every source, including those without candidate graph edges."""
        session = FakeSession()
        all_sources = inventory_page(session, 'p', limit=2)
        unmapped = inventory_page(session, 'p', unmapped_only=True)
        self.assertEqual(all_sources['total_sources'], 2)
        self.assertEqual(unmapped['sources'][0]['path'], 'unmapped.bin')
        self.assertEqual(unmapped['total_sources'], 1)
        self.assertEqual(unmapped['qualification'], 'candidate_only')

    def test_paging_and_invalid_bounds(self) -> None:
        """Paging is navigation, not a semantic exclusion threshold."""
        session = FakeSession()
        first = inventory_page(session, 'p', limit=1)
        second = inventory_page(session, 'p', offset=1, limit=1)
        self.assertEqual(first['next_offset'], 1)
        self.assertIsNone(second['next_offset'])
        with self.assertRaises(ValueError):
            page_bounds(-1, 20)
        with self.assertRaises(ValueError):
            page_bounds(0, 101)
        with self.assertRaises(ValueError):
            matching_concepts(' ', session.concepts)

    def test_unavailable_projection_never_masquerades_as_no_matches(self) -> None:
        """Missing candidate graph is not the same as zero semantic evidence."""
        class MissingSession(FakeSession):
            """Return no candidate projection header for identity validation."""

            def run(self, query: str, **params: Any) -> FakeResult:
                """Simulate a missing version-scoped projection.

                Args:
                    query: Read query.
                    params: Bound query arguments.
                """
                if 'RETURN p.state AS state' in query:
                    return FakeResult([])
                return super().run(query, **params)

        with self.assertRaises(ValueError):
            objective_evidence(MissingSession(), 'p', 'Longhorn')

    def test_no_semantic_promotion_or_mutation(self) -> None:
        """Readback must neither write to Neo4j nor invent approval states."""
        session = FakeSession()
        result = objective_evidence(session, 'p', 'Longhorn')
        self.assertFalse(any('CREATE' in query or 'MERGE' in query or
                             ' SET ' in query for query, _ in session.calls))
        self.assertNotIn('approved', str(result))
        self.assertNotIn('evidence_found', str(result))


if __name__ == '__main__':
    unittest.main(verbosity=2)
