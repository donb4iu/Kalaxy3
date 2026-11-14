#!/usr/bin/env python3
"""Construct non-authoritative Neo4j candidate models from Git evidence."""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from sage_neo4j_inventory import (bounded_committed_text, candidate_edges,
                                  digest, fingerprint, git_output,
                                  source_records, tree_entries)
from sage_neo4j_lifecycle import ensure_lossless

IDENTIFIER_KEYS = ('capability_id', 'component_id', 'policy_id', 'workflow_id',
                   'objective_id', 'context_id', 'record_type')
GENERIC_TITLES = {'introduction', 'overview', 'contents', 'summary', 'readme',
                  'references', 'installation', 'testing', 'status', 'appendix',
                  'sage', 'kalaxy3', 'architecture', 'evidence', 'index',
                  'concepts', 'policy', 'workflow', 'examples'}
LINK_RE = re.compile(r'\]\(([^)]+)\)')
HEADING_RE = re.compile(r'^#\s+(.+?)\s*$', re.MULTILINE)


def commit_id(repo: Path, ref: str) -> str:
    """Resolve an explicit Git ref to a pinned commit.

    Args:
        repo: Local source checkout.
        ref: Exact baseline or candidate ref to resolve.
    """
    return git_output(repo, 'rev-parse', '--verify', ref + '^{commit}').decode().strip()


def safe_label(value: str) -> str | None:
    """Normalize an explicit repository label without inferring a capability.

    Args:
        value: Human-readable source heading or declared identifier.
    """
    clean = re.sub(r'[`*_\[\]#]', '', value).strip()
    clean = re.sub(r'\s+', ' ', clean).split(' | ', 1)[0].strip(' -:')
    if not 4 <= len(clean) <= 100 or clean.lower() in GENERIC_TITLES:
        return None
    if not re.search(r'[a-zA-Z]{3}', clean) or clean.startswith(('http:', 'https:')):
        return None
    return clean


def anchor_labels(source: dict[str, Any], text: str | None) -> list[tuple[str, str]]:
    """Extract explicit headings, JSON identities, and Helm task names.

    Args:
        source: Immutable tracked source provenance.
        text: Bounded committed text; None for opaque sources.
    """
    path = source['path']
    if (not text or any(part in path.lower().split('/') for part in
                        ('fixtures', 'tests', 'examples', 'testdata')) or
            Path(path).name.startswith(('test_', 'index.'))):
        return []
    labels: list[tuple[str, str]] = []
    if path.endswith('.md'):
        heading = HEADING_RE.search(text[:12000])
        if heading:
            labels.append((heading.group(1), 'markdown_heading'))
    if path.endswith('.json'):
        try:
            record = json.loads(text)
        except (ValueError, UnicodeDecodeError):
            record = None
        if isinstance(record, dict):
            for key in IDENTIFIER_KEYS:
                if isinstance(record.get(key), str):
                    labels.append((record[key], 'json_' + key))
    if path.startswith('infrastructure/k3s-homelab/playbooks/tasks/'):
        labels.append((Path(path).stem.replace('-', ' '), 'playbook_task_name'))
    return [(normalized, kind) for label, kind in labels
            if (normalized := safe_label(label)) is not None]


def slug(label: str) -> str:
    """Construct a stable provisional concept key from an attested label.

    Args:
        label: Provenance-backed literal heading or identifier.
    """
    return re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-')


def derive_concepts(repo: Path, sources: list[dict[str, Any]],
                    scope: str) -> list[dict[str, Any]]:
    """Generate deterministic provisional concepts from actual Git anchors.

    Args:
        repo: Git repository containing the pinned source objects.
        sources: Complete source inventory for one commit.
        scope: Baseline or feature source provenance label.
    """
    candidates: dict[str, dict[str, Any]] = {}
    preferred = sorted(sources, key=lambda row: (
        0 if row['path'].startswith('markdown/standards/') else
        1 if row['path'].startswith('infrastructure/k3s-homelab/playbooks/tasks/') else
        2 if row['path'].startswith('sage-') and row['path'].endswith('.json') else
        3, row['path']))
    for source in preferred:
        if not (source['path'].endswith(('.md', '.json')) or
                source['path'].startswith('infrastructure/k3s-homelab/playbooks/tasks/')):
            continue
        text = bounded_committed_text(repo, source)
        for label, kind in anchor_labels(source, text):
            name = slug(label)
            if not name:
                continue
            origin = {'path': source['path'], 'sha256': source['content_sha256'],
                      'revision': source['revision'], 'kind': kind, 'scope': scope}
            if name in candidates:
                candidates[name]['origin_refs'].append(origin)
                continue
            candidates[name] = {'name': name, 'aliases': [label, name],
                                'related': [], 'dimensions': ['candidate_anchor'],
                                'origin_paths': [source['path']],
                                'origin_refs': [origin], 'origin_scope': scope,
                                'semantic_authority': 'unverified_candidate'}
    return [candidates[key] for key in sorted(candidates)]


def merge_concepts(main: list[dict[str, Any]],
                   feature: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve main precedents while marking branch-only concepts provisional.

    Args:
        main: Concepts derived from production repository evidence.
        feature: Concepts derived from feature-branch evidence.
    """
    result = {row['name']: dict(row) for row in main}
    for row in feature:
        if row['name'] not in result:
            result[row['name']] = dict(row)
        else:
            result[row['name']]['origin_scope'] = 'main_and_feature'
            result[row['name']]['origin_paths'] = sorted(set(
                result[row['name']]['origin_paths'] + row['origin_paths']))
            result[row['name']]['origin_refs'] += row['origin_refs']
    return [result[key] for key in sorted(result)]


def tree_delta(before: list[dict[str, str]],
               after: list[dict[str, str]]) -> dict[str, list[str]]:
    """Compare Git object identities without interpreting deployment status.

    Args:
        before: Exact merge-base tree.
        after: Exact main or feature tree.
    """
    previous = {row['path']: (row['git_oid'], row['mode']) for row in before}
    current = {row['path']: (row['git_oid'], row['mode']) for row in after}
    shared = previous.keys() & current.keys()
    modified = sorted(path for path in shared if previous[path] != current[path])
    return {'added': sorted(current.keys() - previous.keys()),
            'removed': sorted(previous.keys() - current.keys()),
            'modified': modified}


def explicit_links(repo: Path, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Record literal local Markdown links, not inferred dependency semantics.

    Args:
        repo: Git repository holding the committed blobs.
        sources: Entire pinned source inventory, including opaque files.
    """
    paths = {row['path']: row for row in sources}
    references: list[dict[str, Any]] = []
    for source in sources:
        if not source['path'].endswith('.md'):
            continue
        text = bounded_committed_text(repo, source)
        if text is None:
            continue
        for match in LINK_RE.finditer(text):
            url = unquote(urlsplit(match.group(1).split()[0]).path)
            if not url or url.startswith(('/', 'https:', 'http:')):
                continue
            target = posixpath.normpath(posixpath.join(
                posixpath.dirname(source['path']), url))
            if target not in paths:
                continue
            references.append({'from_id': source['identity'],
                               'to_id': paths[target]['identity'],
                               'relation': 'literal_document_link',
                               'state': 'source_reference_only'})
    unique = {(item['from_id'], item['to_id']): item for item in references}
    return [unique[key] for key in sorted(unique)]


def corpus_anchor(sources: list[dict[str, Any]],
                  scope: str) -> dict[str, Any] | None:
    """Represent the entire Git source collection as one traversable concept.

    Args:
        sources: All inventoried sources in the selected revision.
        scope: Provenance scope of this revision.
    """
    if not sources:
        return None
    source = next((item for item in sources
                   if item['path'] == 'SAGE.md'), sources[0])
    origin = {'path': source['path'], 'sha256': source['content_sha256'],
              'revision': source['revision'], 'kind': 'git_corpus_anchor',
              'scope': scope}
    return {'name': 'full-repository-corpus',
            'aliases': ['full repository corpus'], 'related': [],
            'dimensions': ['navigation_anchor'],
            'origin_paths': [source['path']], 'origin_refs': [origin],
            'origin_scope': scope,
            'semantic_authority': 'unverified_candidate'}


def corpus_edges(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Connect every recorded source to the corpus without judging its topic.

    Args:
        sources: Complete provenance-preserving Git inventory.
    """
    return [{'source_id': source['identity'],
             'concept': 'full-repository-corpus',
             'state': 'candidate_unverified', 'matched_aliases': [],
             'match_surfaces': ['git_corpus_membership']}
            for source in sources]


def snapshot(repo: Path, revision: str,
             concepts: list[dict[str, Any]],
             sources: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Reuse existing Neo4j inventory and candidate-matcher contracts.

    Args:
        repo: Valid checked-out Git repository.
        revision: Fully resolved main or feature commit.
        concepts: Evidence-derived, never approved, model seed.
        sources: Previously qualified full inventory, if already enumerated.
    """
    sources = sources if sources is not None else source_records(repo, revision)
    ensure_lossless(sources, {row['path'] for row in tree_entries(repo, revision)})
    concepts = list(concepts)
    anchor = corpus_anchor(sources, 'pinned_revision')
    if anchor and not any(row['name'] == anchor['name'] for row in concepts):
        concepts.append(anchor)
    concepts.sort(key=lambda row: row['name'])
    lexical_concepts = [row for row in concepts
                        if row['name'] != 'full-repository-corpus']
    edges = candidate_edges(sources, lexical_concepts, repo=repo)
    edges.extend(corpus_edges(sources))
    links = explicit_links(repo, sources)
    from sage_neo4j_context import root_governance_sources, source_sections
    from sage_neo4j_claims import pinned_claims
    claims = pinned_claims(repo, sources)
    sections = source_sections(repo, sources)
    governance = root_governance_sources(sources)
    return {'revision': revision, 'sources': sources, 'concepts': concepts,
            'source_sections': sections, 'root_governance_sources': governance,
            'relationship_claims': claims,
            'candidate_seed_limit': None,
            'candidate_seed_cap_reached': False,
            'candidate_edges': edges, 'explicit_source_links': links,
            'model_state': 'evidence_derived_candidate' if concepts else 'not_evaluated',
            'model_origin': 'derived_from_governed_git_evidence',
            'qualification': 'candidate_only',
            'semantic_relationships_established': 0,
            'runtime_implementation_verified': False,
            'fingerprint': fingerprint(sources, concepts, edges)}


def bootstrap(repo: Path, main_ref: str, feature_ref: str) -> dict[str, Any]:
    """Build main and branch projections with independent three-way evidence.

    Args:
        repo: Isolated Kalaxy3 Git checkout; never mutated here.
        main_ref: Fetched and governed production branch ref.
        feature_ref: Pinned, unpromoted feature ref.
    """
    main = commit_id(repo, main_ref)
    feature = commit_id(repo, feature_ref)
    base = git_output(repo, 'merge-base', main, feature).decode().strip()
    baseline = source_records(repo, main)
    proposed = source_records(repo, feature)
    main_concepts = derive_concepts(repo, baseline, 'main')
    candidate_concepts = derive_concepts(repo, proposed, 'feature')
    main_view = snapshot(repo, main, main_concepts, baseline)
    feature_view = snapshot(repo, feature, merge_concepts(
        main_concepts, candidate_concepts), proposed)
    common = tree_entries(repo, base)
    feature_view['governed_main_revision'] = main
    feature_view['merge_base_revision'] = base
    feature_view['fingerprint'] = digest(json.dumps({
        'projection': feature_view['fingerprint'], 'main': main, 'base': base,
    }, sort_keys=True).encode())
    return {'main': main_view, 'feature': feature_view,
            'three_way': {'merge_base_revision': base,
                          'main_changes': tree_delta(common, tree_entries(repo, main)),
                          'feature_changes': tree_delta(common, tree_entries(repo, feature))}}
