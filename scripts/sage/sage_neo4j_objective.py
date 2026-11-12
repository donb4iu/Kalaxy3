#!/usr/bin/env python3
"""Read bounded, objective-scoped candidate evidence from a Neo4j projection."""

from __future__ import annotations

import re
from typing import Any

from sage_neo4j_inventory import cue_match

MAX_PAGE_SIZE = 100
FUNCTION_WORDS = {'a', 'an', 'and', 'as', 'at', 'be', 'by', 'for', 'from',
                  'in', 'into', 'is', 'of', 'on', 'or', 'the', 'to', 'using', 'with'}


def page_bounds(offset: int, limit: int) -> None:
    """Reject invalid pagination without deciding relevance.

    Args:
        offset: Zero-based result offset.
        limit: Maximum source records in one page.
    """
    if offset < 0 or not 1 <= limit <= MAX_PAGE_SIZE:
        raise ValueError('INVALID_EVIDENCE_PAGE_BOUNDS')



def substantive_words(text: str) -> set[str]:
    """Normalize terms for transparent lexical candidate discovery.

    Args:
        text: Objective wording or an existing governed concept alias.
    """
    return {word for word in re.findall(r'[a-z0-9]+', text.lower())
            if len(word) >= 3 and word not in FUNCTION_WORDS}


def matching_concepts(objective: str,
                      concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nominate lexical entry points without confidence gates or semantic claims.

    Args:
        objective: Architect-owned objective wording.
        concepts: Projection-scoped semantic vocabulary metadata.
    """
    if not objective or not objective.strip():
        raise ValueError('OBJECTIVE_REQUIRED')
    terms = substantive_words(objective)
    matches: list[dict[str, Any]] = []
    for concept in concepts:
        aliases = list(dict.fromkeys(
            [concept['name'], *(concept.get('aliases') or [])]))
        exact = sorted({alias for alias in aliases if alias and (
            cue_match(objective, alias) or cue_match(alias, objective.strip()))})
        alias_words = set().union(*(substantive_words(alias) for alias in aliases))
        overlapping = sorted(alias_words & terms)
        if exact or overlapping:
            matches.append({'name': concept['name'], 'uid': concept['uid'],
                            'matched_aliases': exact, 'matched_terms': overlapping,
                            'relation': ('explicit_phrase_candidate' if exact
                                         else 'lexical_overlap_candidate')})
    return sorted(matches, key=lambda row: (
        not bool(row['matched_aliases']), -len(row['matched_terms']), row['name']))


def caller_concepts(
    names: list[str], concepts: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    """Resolve optional caller-proposed concept entry points as untrusted hints.

    Args:
        names: Exact concept names nominated by an Architect or LLM.
        concepts: Scoped graph concept metadata, not an authority grant.
    """
    existing = {item['name']: item for item in concepts}
    resolved = [{'uid': existing[name]['uid'], 'name': name,
                 'relation': 'caller_proposed_candidate'}
                for name in sorted(set(names)) if name in existing]
    unknown = sorted(set(names) - existing.keys())
    return resolved, unknown



def ensure_candidate_projection(session: Any, identifier: str) -> None:
    """Distinguish a missing graph from a valid empty concept result.

    Args:
        session: Read-only local Neo4j session.
        identifier: Exact candidate projection identity.
    """
    record = session.run("MATCH (p:SageProjection {id:$id}) "
                         "RETURN p.state AS state", id=identifier).single()
    if record is None or record['state'] != 'candidate':
        raise ValueError('CANDIDATE_PROJECTION_NOT_AVAILABLE')


def projection_concepts(session: Any, identifier: str) -> list[dict[str, Any]]:
    """Read only concept metadata in a pinned, candidate graph.

    Args:
        session: Read-only local Neo4j session.
        identifier: Exact projection identity.
    """
    result = session.run('''MATCH (p:SageProjection {id:$id})
       WHERE p.state='candidate'
       MATCH (c:SageConcept)-[:IN_PROJECTION]->(p)
       RETURN c.uid AS uid, c.name AS name, c.aliases AS aliases
       ORDER BY name''', id=identifier)
    return [dict(row) for row in result]


def adjacent_concepts(session: Any, identifier: str,
                      matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand a single explicit vocabulary relationship hop, without inference.

    Args:
        session: Read-only local Neo4j session.
        identifier: Exact projection identity.
        matches: Explicit lexical entry-point concepts.
    """
    if not matches:
        return []
    result = session.run('''MATCH (p:SageProjection {id:$id})
       MATCH (a:SageConcept)-[:IN_PROJECTION]->(p)
       WHERE a.uid IN $uids
       MATCH (a)-[:RELATED_CONCEPT]-(b:SageConcept)-[:IN_PROJECTION]->(p)
       RETURN DISTINCT b.uid AS uid, b.name AS name ORDER BY name''',
                         id=identifier, uids=[row['uid'] for row in matches])
    return [{'uid': row['uid'], 'name': row['name'],
             'relation': 'explicit_related_concept'} for row in result
            if row['uid'] not in {match['uid'] for match in matches}]


def source_page(session: Any, identifier: str, uids: list[str],
                offset: int, limit: int) -> tuple[int, list[dict[str, Any]]]:
    """Fetch one page of source-concept candidate links with exact provenance.

    Args:
        session: Read-only Neo4j session.
        identifier: Exact projection identity.
        uids: Exact selected concept identities.
        offset: Source-page offset.
        limit: Maximum sources in the page.
    """
    if not uids:
        return 0, []
    scoped = '''MATCH (p:SageProjection {id:$id})
       MATCH (c:SageConcept)-[:IN_PROJECTION]->(p)
       WHERE c.uid IN $uids
       MATCH (s:SageSource)-[r:CANDIDATE_CONCEPT]->(c)
       MATCH (s)-[:IN_PROJECTION]->(p)'''
    total = session.run(scoped + ' RETURN count(DISTINCT s) AS total',
                        id=identifier, uids=uids).single()['total']
    result = session.run(scoped + ''' WITH s, collect(DISTINCT c.name) AS concepts
       RETURN s.uid AS uid, s.path AS path, s.git_oid AS git_oid,
              s.content_sha256 AS content_sha256,
              s.content_state AS content_state,
              s.mapping_state AS mapping_state, concepts
       ORDER BY path, uid SKIP $offset LIMIT $limit''',
                         id=identifier, uids=uids, offset=offset, limit=limit)
    return total, [dict(row) for row in result]


def literal_links(session: Any, identifier: str,
                  sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Read one hop of literal source references for the current source page.

    Args:
        session: Read-only local Neo4j session.
        identifier: Exact projection identity.
        sources: Source records in the returned page.
    """
    if not sources:
        return []
    result = session.run('''MATCH (p:SageProjection {id:$id})
       MATCH (s:SageSource)-[:IN_PROJECTION]->(p)
       WHERE s.uid IN $uids
       MATCH (s)-[link:REFERENCES_SOURCE]-(other:SageSource)-[:IN_PROJECTION]->(p)
       RETURN DISTINCT startNode(link).uid AS from_uid,
              endNode(link).uid AS to_uid, other.uid AS related_uid,
              other.path AS related_path,
              other.git_oid AS related_git_oid,
              other.content_sha256 AS related_content_sha256,
              link.semantic_authority AS semantic_authority
       ORDER BY from_uid, to_uid''',
                         id=identifier, uids=[source['uid'] for source in sources])
    return [dict(row) for row in result]


def governance_sources(session: Any, identifier: str) -> list[dict[str, Any]]:
    """Fetch existing root instruction pointers independent of objective wording.

    Args:
        session: Read-only Neo4j session.
        identifier: Version-pinned candidate projection identity.
    """
    result = session.run('''MATCH (p:SageProjection {id:$id})
       WHERE p.state='candidate'
       MATCH (s:SageSource)-[r:ROOT_GOVERNANCE_POINTER]->(p)
       RETURN s.uid AS uid, s.path AS path, s.git_oid AS git_oid,
              s.content_sha256 AS content_sha256,
              r.attestation AS attestation,
              r.applicability AS applicability,
              r.semantic_qualification AS semantic_qualification
       ORDER BY path''', id=identifier)
    return [dict(row) for row in result]


def evidence_sections(session: Any, identifier: str, uids: list[str],
                      offset: int, limit: int) -> tuple[int, list[dict[str, Any]]]:
    """Page source-attested context headings without loading source bodies.

    Args:
        session: Read-only Neo4j session.
        identifier: Exact candidate projection identity.
        uids: Candidate and root-governance source identities.
        offset: Section-page offset independent of source pagination.
        limit: Section-page bound, not a relevance threshold.
    """
    if not uids:
        return 0, []
    scoped = '''MATCH (p:SageProjection {id:$id})
       WHERE p.state='candidate'
       MATCH (s:SageSource)-[:IN_PROJECTION]->(p)
       WHERE s.uid IN $uids
       MATCH (e:SageEvidenceSection)-[:SECTION_OF]->(s)
       MATCH (e)-[:IN_PROJECTION]->(p)'''
    params = {'id': identifier, 'uids': uids}
    total = session.run(scoped + ' RETURN count(e) AS total',
                        **params).single()['total']
    rows = session.run(scoped + ''' RETURN e.uid AS uid, s.path AS source_path,
       s.git_oid AS git_oid, s.content_sha256 AS source_sha256,
       e.heading AS heading, e.kind AS kind, e.start_line AS start_line,
       e.end_line AS end_line, e.section_sha256 AS section_sha256,
       e.attestation AS attestation,
       e.semantic_qualification AS semantic_qualification
       ORDER BY source_path, start_line, uid SKIP $offset LIMIT $limit''',
                       **params, offset=offset, limit=limit)
    return total, [dict(row) for row in rows]


def context_readback(session: Any, identifier: str,
                     sources: list[dict[str, Any]],
                     offset: int, limit: int) -> dict[str, Any]:
    """Collect attested root and related-source context with independent paging.

    Args:
        session: Read-only Neo4j session.
        identifier: Exact projection identity.
        sources: Already-paged lexical candidate sources.
        offset: Context section page offset.
        limit: Context section page size.
    """
    roots = governance_sources(session, identifier)
    links = literal_links(session, identifier, sources)
    uids = sorted(set([row['uid'] for row in sources] +
                      [row['uid'] for row in roots] +
                      [row['related_uid'] for row in links
                       if row.get('related_uid')]))
    total, sections = evidence_sections(session, identifier, uids, offset, limit)
    return {'governance_source_pointers': roots,
            'governance_scope': 'kalaxy3_implementation_source_pointer_only',
            'context_sections': sections, 'total_context_sections': total,
            'section_offset': offset, 'section_limit': limit,
            'next_section_offset': (offset + limit if offset + limit < total
                                    else None), 'literal_source_links': links}


def objective_evidence(session: Any, identifier: str, objective: str,
                       offset: int = 0, limit: int = 30,
                       proposed_concepts: list[str] | None = None,
                       section_offset: int = 0,
                       section_limit: int = 30) -> dict[str, Any]:
    """Return a paginated candidate subgraph, not an objective judgment.

    Args:
        session: Read-only local Neo4j session.
        identifier: Pinned candidate projection identity.
        objective: Architect-owned wording, used only for alias matching.
        offset: Zero-based source-page offset.
        limit: Bounded number of source records per page.
        proposed_concepts: Optional external candidate concept names.
        section_offset: Independent context-section page offset.
        section_limit: Maximum context-section pointers per page.
    """
    page_bounds(offset, limit)
    page_bounds(section_offset, section_limit)
    ensure_candidate_projection(session, identifier)
    concepts = projection_concepts(session, identifier)
    matches = matching_concepts(objective, concepts)
    proposed, unknown = caller_concepts(proposed_concepts or [], concepts)
    related = adjacent_concepts(session, identifier, matches + proposed)
    selected = sorted({row['uid'] for row in matches + proposed + related})
    total, sources = source_page(session, identifier, selected, offset, limit)
    context = context_readback(session, identifier, sources,
                               section_offset, section_limit)
    return {'projection_id': identifier, 'objective': objective,
            'match_method': 'lexical_alias_and_overlap_candidates',
            'matched_concepts': matches, 'caller_proposed_concepts': proposed,
            'unknown_proposed_concepts': unknown, 'related_concepts': related,
            **context, 'sources': sources,
            'total_candidate_sources': total,
            'offset': offset, 'limit': limit,
            'next_offset': offset + limit if offset + limit < total else None,
            'broader_inventory_available': True,
            'matching_status': 'candidate_concepts_found' if selected
            else 'no_explicit_alias_match',
            'evidence_presence': 'not_evaluated',
            'qualification': 'candidate_only'}


def inventory_page(session: Any, identifier: str, offset: int = 0,
                   limit: int = 30, unmapped_only: bool = False) -> dict[str, Any]:
    """Expose all or unmapped source evidence independent of concept candidates.

    Args:
        session: Read-only local Neo4j session.
        identifier: Pinned candidate projection identity.
        offset: Zero-based source-page offset.
        limit: Maximum returned source records.
        unmapped_only: Return only sources without candidate concept links.
    """
    page_bounds(offset, limit)
    ensure_candidate_projection(session, identifier)
    scoped = '''MATCH (p:SageProjection {id:$id})
       MATCH (s:SageSource)-[:IN_PROJECTION]->(p)
       WHERE NOT $unmapped OR NOT EXISTS {
         MATCH (s)-[:CANDIDATE_CONCEPT]->(c:SageConcept)-[:IN_PROJECTION]->(p)
       }'''
    args = {'id': identifier, 'unmapped': unmapped_only}
    total = session.run(scoped + ' RETURN count(s) AS total', **args).single()['total']
    result = session.run(scoped + ''' RETURN s.uid AS uid, s.path AS path,
       s.git_oid AS git_oid, s.content_sha256 AS content_sha256,
       s.content_state AS content_state, s.mapping_state AS mapping_state
       ORDER BY path, uid SKIP $offset LIMIT $limit''',
                         **args, offset=offset, limit=limit)
    return {'projection_id': identifier, 'sources': [dict(row) for row in result],
            'total_sources': total, 'unmapped_only': unmapped_only,
            'offset': offset, 'limit': limit,
            'next_offset': offset + limit if offset + limit < total else None,
            'evidence_presence': 'not_evaluated',
            'qualification': 'candidate_only'}
