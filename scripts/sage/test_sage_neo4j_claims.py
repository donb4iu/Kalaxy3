#!/usr/bin/env python3
"""Focused Issue #50 registry-bound relationship-claim regression cases."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterator

from sage_neo4j_claims import REGISTRY, pinned_claims
from sage_neo4j_inventory import fingerprint, prepare, source_records
from sage_neo4j_objective import objective_evidence
from sage_neo4j_projection import build_projection


class Fixture(unittest.TestCase):
    """Provide a true Git commit with a typed, quoted relationship registry."""

    def setUp(self) -> None:
        """Create a disposable revision-pinned policy and decision corpus."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(['git', '-C', str(self.repo), 'init', '-q'], check=True)
        self.git('config', 'user.email', 'claims@example.invalid')
        self.git('config', 'user.name', 'Relation Claims Fixture')
        (self.repo / 'AGENTS.md').write_text(
            '# Instructions\nEvery implementation follows review.\n', 'utf-8')
        (self.repo / 'decisions.md').write_text(
            '# Decision record\nRejected option A in favor of option B.\n', 'utf-8')
        (self.repo / 'options.md').write_text('# Option A\nAvailable option.\n', 'utf-8')
        (self.repo / 'sage-semantic-concepts.json').write_text(json.dumps({
            'concepts': {'decision': {'terms': ['Decision'], 'related': [],
                                      'dimensions': []}}}), 'utf-8')
        self.global_claim = {'id': 'global.review.rule', 'kind': 'applicable_to',
                             'scope': 'kalaxy3_implementation',
                             'subject_path': 'AGENTS.md', 'object_path': None,
                             'evidence_path': 'AGENTS.md', 'start_line': 2,
                             'quote': 'Every implementation follows review.'}
        self.historical_claim = {'id': 'decision.option.rejected',
                                 'kind': 'alternative_rejected',
                                 'scope': 'source_to_source',
                                 'subject_path': 'decisions.md',
                                 'object_path': 'options.md',
                                 'evidence_path': 'decisions.md', 'start_line': 2,
                                 'quote': 'Rejected option A in favor of option B.'}
        self.save([self.global_claim, self.historical_claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'committed claim evidence')
        self.revision = self.git('rev-parse', 'HEAD')

    def git(self, *args: str) -> str:
        """Run Git solely inside an ephemeral test repository.

        Args:
            args: Git arguments.
        """
        return subprocess.check_output(['git', '-C', str(self.repo), *args],
                                       text=True).strip()

    def save(self, claims: list[dict[str, Any]]) -> None:
        """Change fixture worktree registry, not the committed source.

        Args:
            claims: Local uncommitted registry rows.
        """
        (self.repo / REGISTRY).write_text(json.dumps({
            'version': 1, 'claims': claims}, indent=2) + '\n', 'utf-8')

    def claims(self) -> list[dict[str, Any]]:
        """Evaluate only the previously committed registry and evidence."""
        return pinned_claims(self.repo, source_records(self.repo, self.revision))

    def test_pinned_evidence_yields_types_without_qualification(self) -> None:
        """Preserve exact quotes by digest while exposing explicit claim types."""
        rows = self.claims()
        self.assertEqual([row['kind'] for row in rows],
                         ['alternative_rejected', 'applicable_to'])
        self.assertTrue(all(row['semantic_qualification'] == 'not_evaluated'
                            for row in rows))
        self.assertTrue(all(len(row['quote_sha256']) == 64 for row in rows))
        self.assertNotIn('Rejected option A', json.dumps(rows))

    def test_uncommitted_registry_edit_does_not_rewrite_knowledge(self) -> None:
        """Both registry and proof bytes must come from the pinned Git tree."""
        expected = self.claims()
        self.save([])
        (self.repo / 'decisions.md').write_text('Option A was chosen.\n', 'utf-8')
        self.assertEqual(self.claims(), expected)

    def test_stale_quote_fails_closed(self) -> None:
        """Incorrect quote cannot be registered as source-attested fact."""
        claim = {**self.historical_claim, 'quote': 'Option A was chosen.'}
        self.save([self.global_claim, claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'invalid quote')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'QUOTE_MISMATCH'):
            self.claims()

    def test_missing_endpoint_fails_closed(self) -> None:
        """Unknown target source cannot enter the typed graph."""
        claim = {**self.historical_claim, 'object_path': 'missing.md'}
        self.save([self.global_claim, claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'invalid endpoint')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'SOURCE_RELATIONSHIP_SCOPE'):
            self.claims()

    def test_invalid_global_scope_fails_closed(self) -> None:
        """Global applicability cannot be claimed through arbitrary scope."""
        claim = {**self.global_claim, 'scope': 'all_systems'}
        self.save([claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'invalid scope')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'GLOBAL_APPLICABILITY_SCOPE'):
            self.claims()

    def test_unknown_relation_kind_fails_closed(self) -> None:
        """A free-form relation label cannot silently become graph authority."""
        claim = {**self.historical_claim, 'kind': 'unreviewed_admin_override'}
        self.save([self.global_claim, claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'invalid kind')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'CLAIM_TYPE'):
            self.claims()

    def test_duplicate_claim_ids_fail_closed(self) -> None:
        """Conflicting declarations with identical IDs must not silently overwrite."""
        self.save([self.global_claim, self.global_claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'duplicate claims')
        self.revision = self.git('rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'DUPLICATE_RELATIONSHIP'):
            self.claims()

    def test_graph_writer_scopes_attested_claims(self) -> None:
        """Writer binds subject, target, proof and candidate projection identity."""
        payload = prepare(self.repo, self.repo / 'sage-semantic-concepts.json')
        self.assertEqual(len(payload['relationship_claims']), 2)
        session = WriteSession(payload)
        verified = build_projection(session, payload)
        self.assertEqual(verified['observed']['relationship_claims'], 2)
        self.assertTrue(any('MERGE (c)-[:CLAIM_EVIDENCE]->(e)' in query
                            for query in session.queries))
        self.assertTrue(any('MERGE (c)-[:CLAIM_OBJECT]->(o)' in query
                            for query in session.queries))
        self.assertTrue(all("p.state='candidate'" in query
                            for query in session.queries
                            if 'SageRelationClaim {uid:row.uid}' in query))

    def test_fingerprint_changes_on_authoritative_claim_edit(self) -> None:
        """Rebuilding after a registry commit yields a new graph identity."""
        current = prepare(self.repo, self.repo / 'sage-semantic-concepts.json')
        self.save([self.global_claim])
        self.git('add', '-A')
        self.git('commit', '-qm', 'change claims')
        updated = prepare(self.repo, self.repo / 'sage-semantic-concepts.json')
        self.assertNotEqual(current['fingerprint'], updated['fingerprint'])
        self.assertEqual(len(updated['relationship_claims']), 1)

    def test_missing_registry_remains_unqualified(self) -> None:
        """Absence of optional claim declarations never means no obligations."""
        self.git('rm', '-q', REGISTRY)
        self.git('commit', '-qm', 'remove optional registry')
        self.revision = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.claims(), [])
        self.assertEqual(prepare(self.repo,
                         self.repo / 'sage-semantic-concepts.json')['qualification'],
                         'candidate_only')


class Record:
    """Represent a minimal Neo4j result set."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Hold rows returned by a candidate-only query.

        Args:
            rows: Read-only result records.
        """
        self.rows = rows

    def __iter__(self) -> Iterator[dict[str, Any]]:
        """Iterate the records."""
        return iter(self.rows)

    def single(self, **_kwargs: Any) -> dict[str, Any] | None:
        """Return the first record for count and projection queries."""
        return self.rows[0] if self.rows else None


class ReadSession:
    """Emulate the version-scoped global applicability read path."""

    def __init__(self) -> None:
        """Capture queries for read-only and bounded claim pagination checks."""
        self.queries: list[str] = []

    def run(self, query: str, **params: Any) -> Record:
        """Answer only source-pointer and claim queries with explicit parameters.

        Args:
            query: Parameterized Neo4j query.
            params: Candidate graph and pagination parameters.
        """
        self.queries.append(query)
        if 'RETURN p.state AS state' in query:
            return Record([{'state': 'candidate'}])
        if 'RETURN c.uid AS uid, c.name AS name' in query:
            return Record([])
        if 'ROOT_GOVERNANCE_POINTER' in query:
            return Record([{'uid': 'p:agents', 'path': 'AGENTS.md'}])
        if 'SageEvidenceSection' in query:
            return Record([{'total': 0}]) if 'count(e)' in query else Record([])
        if 'SageRelationClaim' in query:
            if 'count(DISTINCT c)' in query:
                return Record([{'total': 2}])
            claims = [{'claim_id': str(i), 'kind': 'applicable_to',
                       'scope': 'kalaxy3_implementation',
                       'semantic_qualification': 'not_evaluated'}
                      for i in (1, 2)]
            return Record(claims[params['offset']:][:params['limit']])
        raise AssertionError('Unexpected candidate query: ' + query)


class ReadTests(unittest.TestCase):
    """Protect non-keyword applicability and separate claim pagination."""

    def test_no_concept_match_retains_global_claim(self) -> None:
        """Applicable claim pointers survive a no-match lexical result."""
        session = ReadSession()
        result = objective_evidence(session, 'p', 'Unrecognized objective',
                                    claim_limit=1)
        self.assertEqual(result['matching_status'], 'no_explicit_alias_match')
        self.assertEqual(result['total_relationship_claims'], 2)
        self.assertEqual(result['next_claim_offset'], 1)
        self.assertEqual(result['relationship_claims'][0]['kind'], 'applicable_to')
        self.assertEqual(result['evidence_presence'], 'not_evaluated')
        self.assertTrue(any('c.scope=' in query and 'SageRelationClaim' in query
                            for query in session.queries))
        self.assertFalse(any('MERGE ' in query or ' SET ' in query
                             for query in session.queries))

    def test_claim_queries_remain_projection_and_page_scoped(self) -> None:
        """No relationship query may widen the selected graph or page scope."""
        session = ReadSession()
        objective_evidence(session, 'p', 'Unrecognized objective', claim_limit=1)
        queries = [query for query in session.queries
                   if 'SageRelationClaim' in query]
        self.assertEqual(len(queries), 2)
        self.assertTrue(all('id:$id' in query and 'IN_PROJECTION' in query
                            and 's.uid IN $uids' in query for query in queries))
        self.assertTrue(all('p.state=' in query for query in queries))

    def test_invalid_claim_page_rejected(self) -> None:
        """Claim transport bounds are checked before any graph reads."""
        with self.assertRaisesRegex(ValueError, 'INVALID_EVIDENCE_PAGE_BOUNDS'):
            objective_evidence(ReadSession(), 'p', 'Any', claim_limit=101)


class WriteResponse:
    """Minimal transaction reply with expected result cardinality."""

    def __init__(self, count: int = 0) -> None:
        """Initialize an independently expected count.

        Args:
            count: Number of projected elements.
        """
        self.count = count

    def consume(self) -> None:
        """Accept completed write without side effects."""

    def single(self, **_kwargs: Any) -> dict[str, Any]:
        """Expose either the verified count or a synthetic header."""
        return {'count': self.count, 'id': 'p'}


class WriteSession:
    """Record typed relationship writes without requiring Neo4j server."""

    def __init__(self, payload: dict[str, Any]) -> None:
        """Retain independent candidate-cardinality expectations.

        Args:
            payload: Pinned source projection candidate.
        """
        self.expected = {'sources': len(payload['sources']),
                         'concepts': len(payload['concepts']),
                         'candidate_edges': len(payload['candidate_edges']),
                         'source_links': len(payload.get('explicit_source_links', [])),
                         'source_sections': len(payload['source_sections']),
                         'root_governance_sources': len(payload['root_governance_sources']),
                         'relationship_claims': len(payload['relationship_claims'])}
        self.queries: list[str] = []

    def run(self, query: str, **_kwargs: Any) -> WriteResponse:
        """Return the precomputed count for each projection-scoped record type.

        Args:
            query: Parameterized Cypher query.
            _kwargs: Arguments including pinned projection identity.
        """
        self.queries.append(query)
        if 'RETURN count(' not in query:
            return WriteResponse()
        for label, key in [('SageRelationClaim', 'relationship_claims'),
                           ('ROOT_GOVERNANCE_POINTER', 'root_governance_sources'),
                           ('SageEvidenceSection', 'source_sections'),
                           ('REFERENCES_SOURCE', 'source_links'),
                           ('CANDIDATE_CONCEPT', 'candidate_edges'),
                           ('SageConcept', 'concepts')]:
            if label in query:
                return WriteResponse(self.expected[key])
        return WriteResponse(self.expected['sources'])

    def execute_write(self, callback: Any, *args: Any) -> None:
        """Run unchanged graph writer against a recording test session.

        Args:
            callback: Existing bounded graph writer routine.
            args: Prepared transaction records.
        """
        callback(self, *args)


if __name__ == '__main__':
    unittest.main(verbosity=2)
