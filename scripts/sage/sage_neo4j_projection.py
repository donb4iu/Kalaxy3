#!/usr/bin/env python3
"""Version-scoped Neo4j semantic projection; never a canonical SAGE store."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from sage_neo4j_lifecycle import projection_id

SCHEMA = (
    'CREATE CONSTRAINT sage_proj_id IF NOT EXISTS FOR (p:SageProjection) REQUIRE p.id IS UNIQUE',
    'CREATE CONSTRAINT sage_concept_id IF NOT EXISTS FOR (c:SageConcept) REQUIRE c.uid IS UNIQUE',
    'CREATE CONSTRAINT sage_source_id IF NOT EXISTS FOR (s:SageSource) REQUIRE s.uid IS UNIQUE',
    ('CREATE CONSTRAINT sage_section_id IF NOT EXISTS '
     'FOR (e:SageEvidenceSection) REQUIRE e.uid IS UNIQUE'),
    ('CREATE CONSTRAINT sage_claim_id IF NOT EXISTS '
     'FOR (c:SageRelationClaim) REQUIRE c.uid IS UNIQUE'),
)


def chunks(items: list[dict[str, Any]], size: int = 150) -> Iterator[list[dict[str, Any]]]:
    """Divide query rows into bounded transactions.

    Args:
        items: Query record list.
        size: Maximum rows per batch.
    """
    for start in range(0, len(items), size):
        yield items[start:start + size]


def create_schema(session: Any) -> None:
    """Establish stable Neo4j uniqueness constraints.

    Args:
        session: Authenticated Neo4j database session.
    """
    for statement in SCHEMA:
        session.run(statement).consume()


def write_header(tx: Any, identifier: str, payload: dict[str, Any]) -> None:
    """Create a candidate projection only, without activating it.

    Args:
        tx: Neo4j transaction.
        identifier: Version-scoped projection ID.
        payload: Prepared source inventory and semantic model.
    """
    tx.run('''MERGE (p:SageProjection {id:$id})
       ON CREATE SET p.revision=$rev, p.fingerprint=$hash,
                     p.state='candidate', p.created_at=datetime()
       WITH p WHERE p.revision=$rev AND p.fingerprint=$hash AND p.state='candidate'
       RETURN p.id AS id''', id=identifier, rev=payload['revision'],
           hash=payload['fingerprint']).single(strict=True)


def write_sources(tx: Any, identifier: str, rows: list[dict[str, Any]]) -> None:
    """Persist Git source metadata, never raw source content.

    Args:
        tx: Neo4j transaction.
        identifier: Projection identity.
        rows: Source metadata for one version.
    """
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       MERGE (s:SageSource {uid:row.uid})
       SET s.path=row.path, s.git_oid=row.git_oid,
           s.content_sha256=row.content_sha256,
           s.content_state=row.content_state,
           s.mapping_state=row.mapping_state
       MERGE (s)-[:IN_PROJECTION]->(p)''', projection=identifier, rows=rows).consume()


def write_concepts(tx: Any, identifier: str, rows: list[dict[str, Any]]) -> None:
    """Write scoped concepts, including concepts with no related evidence.

    Args:
        tx: Neo4j transaction.
        identifier: Projection identity.
        rows: Concept metadata, including aliases.
    """
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       MERGE (c:SageConcept {uid:row.uid})
       SET c.name=row.name, c.aliases=row.aliases,
           c.dimensions=row.dimensions,
           c.origin_scope=row.origin_scope,
           c.origin_paths=row.origin_paths,
           c.origin_refs_json=row.origin_refs_json
       MERGE (c)-[:IN_PROJECTION]->(p)''', projection=identifier, rows=rows).consume()


def write_edges(tx: Any, rows: list[dict[str, Any]]) -> None:
    """Persist explicitly untrusted semantic candidate edges.

    Args:
        tx: Neo4j transaction.
        rows: Candidate source-concept relationship records.
    """
    tx.run('''UNWIND $rows AS row
       MATCH (s:SageSource {uid:row.source_uid})
       MATCH (c:SageConcept {uid:row.concept_uid})
       MERGE (s)-[r:CANDIDATE_CONCEPT]->(c)
       SET r.match_state='candidate_unverified', r.matched_aliases=row.aliases,
           r.match_surfaces=row.surfaces''',
           rows=rows).consume()


def write_source_references(tx: Any, rows: list[dict[str, Any]]) -> None:
    """Project verified literal Git-document links, never runtime dependencies.

    Args:
        tx: Neo4j write transaction.
        rows: Revision-scoped source-to-source link metadata.
    """
    tx.run("""UNWIND $rows AS row
       MATCH (a:SageSource {uid:row.from_uid})
       MATCH (b:SageSource {uid:row.to_uid})
       MERGE (a)-[r:REFERENCES_SOURCE]->(b)
       SET r.reference_class='literal_markdown_link',
           r.semantic_authority='source_reference_only' """, rows=rows).consume()


def write_related(tx: Any, rows: list[dict[str, Any]]) -> None:
    """Record vocabulary-defined related-concept relationships.

    Args:
        tx: Neo4j transaction.
        rows: Source-target concept edges from existing semantic vocabulary.
    """
    tx.run('''UNWIND $rows AS row
       MATCH (left:SageConcept {uid:row.from_uid})
       MATCH (right:SageConcept {uid:row.to_uid})
       MERGE (left)-[:RELATED_CONCEPT]->(right)''', rows=rows).consume()


def write_sections(tx: Any, identifier: str, rows: list[dict[str, Any]]) -> None:
    """Project literal context-section pointers, not qualified decisions.

    Args:
        tx: Neo4j write transaction.
        identifier: Exact candidate projection identity.
        rows: Revision-bound heading metadata and source pointers.
    """
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       MATCH (s:SageSource {uid:row.source_uid})-[:IN_PROJECTION]->(p)
       MERGE (e:SageEvidenceSection {uid:row.uid})
       SET e.heading=row.heading, e.kind=row.kind,
           e.start_line=row.start_line, e.end_line=row.end_line,
           e.section_sha256=row.section_sha256,
           e.source_sha256=row.source_sha256,
           e.attestation='literal_markdown_heading',
           e.semantic_qualification='not_evaluated'
       MERGE (e)-[:SECTION_OF]->(s)
       MERGE (e)-[:IN_PROJECTION]->(p)''', projection=identifier,
           rows=rows).consume()


def write_governance_pointers(tx: Any, identifier: str,
                              rows: list[dict[str, Any]]) -> None:
    """Link attested root instruction sources, without inventing obligations.

    Args:
        tx: Neo4j write transaction.
        identifier: Exact pinned candidate projection identity.
        rows: Repository-root source pointers with Git provenance.
    """
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       MATCH (s:SageSource {uid:row.source_uid})-[:IN_PROJECTION]->(p)
       MERGE (s)-[r:ROOT_GOVERNANCE_POINTER]->(p)
       SET r.attestation='repository_root_instruction_location',
           r.applicability='repository_implementation_context_pointer',
           r.semantic_qualification='not_evaluated'
       ''',
           projection=identifier, rows=rows).consume()


def write_relation_claims(tx: Any, identifier: str,
                          rows: list[dict[str, Any]]) -> None:
    """Write attested but unqualified relationship declarations.

    Args:
        tx: Neo4j write transaction.
        identifier: Exact candidate projection identity.
        rows: Claim metadata and verified Git source pointers.
    """
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       MATCH (s:SageSource {uid:row.subject_uid})-[:IN_PROJECTION]->(p)
       MATCH (e:SageSource {uid:row.evidence_uid})-[:IN_PROJECTION]->(p)
       MERGE (c:SageRelationClaim {uid:row.uid})
       SET c.claim_id=row.id, c.kind=row.kind, c.scope=row.scope,
           c.start_line=row.start_line, c.evidence_sha256=row.evidence_sha256,
           c.quote_sha256=row.quote_sha256,
           c.attestation='registered_type_exact_committed_quote',
           c.semantic_qualification='not_evaluated'
       MERGE (c)-[:IN_PROJECTION]->(p)
       MERGE (c)-[:CLAIM_SUBJECT]->(s)
       MERGE (c)-[:CLAIM_EVIDENCE]->(e)''',
           projection=identifier, rows=rows).consume()
    tx.run('''MATCH (p:SageProjection {id:$projection})
       WHERE p.state='candidate'
       UNWIND $rows AS row
       WITH p, row WHERE row.object_uid IS NOT NULL
       MATCH (c:SageRelationClaim {uid:row.uid})-[:IN_PROJECTION]->(p)
       MATCH (o:SageSource {uid:row.object_uid})-[:IN_PROJECTION]->(p)
       MERGE (c)-[:CLAIM_OBJECT]->(o)''',
           projection=identifier, rows=rows).consume()


def prepared_claim_rows(identifier: str,
                        payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Map pinned source identities into a distinct candidate graph namespace.

    Args:
        identifier: Candidate projection identity.
        payload: Revision-bound relationship claims and source records.
    """
    return [{'uid': identifier + ':claim:' + row['identity'],
             'subject_uid': identifier + ':' + row['subject_id'],
             'object_uid': (identifier + ':' + row['object_id']
                            if row['object_id'] else None),
             'evidence_uid': identifier + ':' + row['evidence_id'], **row}
            for row in payload.get('relationship_claims', [])]


def build_projection(session: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Rebuild a version-scoped candidate without altering any active pointer.

    Args:
        session: Connected Neo4j session.
        payload: Immutable Git snapshot and untrusted candidate mapping.
    """
    identifier = projection_id(payload)
    sources = [{**row, 'uid': identifier + ':' + row['identity']}
               for row in payload['sources']]
    concepts = [{**row, 'uid': identifier + ':' + row['name'],
                 'origin_refs_json': json.dumps(row.get('origin_refs', []),
                                                sort_keys=True)}
                for row in payload['concepts']]
    edges = [{'source_uid': identifier + ':' + edge['source_id'],
              'concept_uid': identifier + ':' + edge['concept'],
              'aliases': edge['matched_aliases'],
              'surfaces': edge.get('match_surfaces', ['path'])}
             for edge in payload['candidate_edges']]
    related = [{'from_uid': identifier + ':' + row['name'],
                'to_uid': identifier + ':' + name}
               for row in payload['concepts'] for name in row['related']]
    sections = [{'uid': identifier + ':section:' + row['identity'],
                 'source_uid': identifier + ':' + row['source_id'], **row}
                for row in payload.get('source_sections', [])]
    governance = [{'source_uid': identifier + ':' + row['source_id']}
                  for row in payload.get('root_governance_sources', [])]
    claims = prepared_claim_rows(identifier, payload)
    references = [{'from_uid': identifier + ':' + row['from_id'],
                   'to_uid': identifier + ':' + row['to_id']}
                  for row in payload.get('explicit_source_links', [])]
    create_schema(session)
    session.execute_write(write_header, identifier, payload)
    for batch in chunks(sources):
        session.execute_write(write_sources, identifier, batch)
    for batch in chunks(concepts):
        session.execute_write(write_concepts, identifier, batch)
    for batch in chunks(edges):
        session.execute_write(write_edges, batch)
    for batch in chunks(related):
        session.execute_write(write_related, batch)
    for batch in chunks(references):
        session.execute_write(write_source_references, batch)
    for batch in chunks(sections):
        session.execute_write(write_sections, identifier, batch)
    for batch in chunks(governance):
        session.execute_write(write_governance_pointers, identifier, batch)
    for batch in chunks(claims):
        session.execute_write(write_relation_claims, identifier, batch)
    return verify_counts(session, identifier, payload)


def verify_counts(session: Any, identifier: str,
                  payload: dict[str, Any]) -> dict[str, Any]:
    """Verify exact node/edge inventory counts after writing a candidate.

    Args:
        session: Neo4j session.
        identifier: Candidate projection identity.
        payload: Independently prepared reference inventory.
    """
    queries = {
        'sources': ('MATCH (s:SageSource)-[:IN_PROJECTION]->'
                    '(p:SageProjection {id:$id}) RETURN count(s) AS count'),
        'concepts': ('MATCH (c:SageConcept)-[:IN_PROJECTION]->'
                     '(p:SageProjection {id:$id}) RETURN count(c) AS count'),
        'candidate_edges': 'MATCH (s:SageSource)-[:CANDIDATE_CONCEPT]->(c:SageConcept) '
                           'WHERE s.uid STARTS WITH $prefix AND '
                           'c.uid STARTS WITH $prefix RETURN count(*) AS count',
        'source_links': 'MATCH (a:SageSource)-[:REFERENCES_SOURCE]->(b:SageSource) '
                        'WHERE a.uid STARTS WITH $prefix AND '
                        'b.uid STARTS WITH $prefix RETURN count(*) AS count',
    }
    observed = {key: session.run(query, id=identifier, prefix=identifier + ':').single()['count']
                for key, query in queries.items()}
    expected = {key: len(payload['candidate_edges'] if key == 'candidate_edges'
                         else payload.get('explicit_source_links', []) if
                         key == 'source_links' else payload[key]) for key in queries}
    if payload.get('root_governance_sources'):
        query = ('MATCH (s:SageSource)-[:ROOT_GOVERNANCE_POINTER]->'
                 '(p:SageProjection {id:$id}) RETURN count(s) AS count')
        observed['root_governance_sources'] = session.run(
            query, id=identifier).single()['count']
        expected['root_governance_sources'] = len(payload['root_governance_sources'])
    if payload.get('source_sections'):
        query = ('MATCH (e:SageEvidenceSection)-[:IN_PROJECTION]->'
                 '(p:SageProjection {id:$id}) RETURN count(e) AS count')
        observed['source_sections'] = session.run(query, id=identifier).single()['count']
        expected['source_sections'] = len(payload['source_sections'])
    if payload.get('relationship_claims'):
        query = ('MATCH (c:SageRelationClaim)-[:IN_PROJECTION]->'
                 '(p:SageProjection {id:$id}) RETURN count(c) AS count')
        observed['relationship_claims'] = session.run(
            query, id=identifier).single()['count']
        expected['relationship_claims'] = len(payload['relationship_claims'])
    if observed != expected:
        raise ValueError(f'NEO4J_PROJECTION_COUNT_MISMATCH: {observed} != {expected}')
    return {'projection_id': identifier, 'observed': observed,
            'expected': expected, 'qualification': 'candidate_only'}


def concept_evidence(session: Any, identifier: str, name: str) -> dict[str, Any]:
    """Return candidates and explicit unknown state, not evidence maturity.

    Args:
        session: Neo4j read session.
        identifier: Scoped projection version.
        name: Existing semantic concept.
    """
    uid = identifier + ':' + name
    rows = session.run('''MATCH (c:SageConcept {uid:$uid})
       OPTIONAL MATCH (s:SageSource)-[:CANDIDATE_CONCEPT]->(c)
       RETURN c.name AS concept, collect(s.path) AS candidate_paths''', uid=uid)
    record = rows.single()
    if record is None or record['concept'] is None:
        raise KeyError(f'UNKNOWN_CONCEPT:{name}')
    return {'concept': name, 'candidate_sources': sorted(x for x in
            record['candidate_paths'] if x is not None),
            'evidence_presence': 'not_evaluated', 'qualification': 'candidate_only'}


def write_json(path: str, payload: dict[str, Any]) -> None:
    """Write safe, metadata-only JSON receipt to an isolated output path.

    Args:
        path: Output file path.
        payload: Versioned projection receipt.
    """
    with open(path, 'w', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write('\n')
