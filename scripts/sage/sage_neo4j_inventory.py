#!/usr/bin/env python3
"""Lossless Git-tree inventory and source-derived semantic candidates for SAGE."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

MAX_MATCH_BYTES = 750_000
TEXT_SUFFIXES = {'.md', '.json', '.yaml', '.yml', '.py', '.toml', '.txt'}


def digest(data: bytes) -> str:
    """Return SHA-256 hex for evidence bytes.

    Args:
        data: Immutable source or normalized metadata bytes.
    """
    return hashlib.sha256(data).hexdigest()


def git_output(repo: Path, *args: str) -> bytes:
    """Read from Git without modifying its checkout.

    Args:
        repo: Valid Git checkout root.
        args: Arguments following the git executable.
    """
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def committed_head(repo: Path) -> str:
    """Return exact checked-out Git commit.

    Args:
        repo: Repository root.
    """
    return git_output(repo, 'rev-parse', 'HEAD').decode().strip()


def tree_entries(repo: Path, revision: str) -> list[dict[str, str]]:
    """Enumerate every blob/symlink in a pinned Git revision without filtering.

    Args:
        repo: Repository root.
        revision: Fully resolved commit identifier.
    """
    raw = git_output(repo, 'ls-tree', '-rz', '--full-tree', revision)
    entries: list[dict[str, str]] = []
    for item in raw.split(b'\0'):
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        mode, kind, oid = metadata.decode('ascii').split(' ')
        entries.append({'path': name.decode('utf-8', 'surrogateescape'),
                        'mode': mode, 'kind': kind, 'git_oid': oid})
    if len({item['path'] for item in entries}) != len(entries):
        raise ValueError('duplicate Git source path')
    return entries


def source_records(repo: Path, revision: str) -> list[dict[str, Any]]:
    """Inventory every Git-tree object and hash every blob's exact bytes.

    Args:
        repo: Repository root.
        revision: Exact source revision.
    """
    records: list[dict[str, Any]] = []
    for entry in tree_entries(repo, revision):
        if entry['kind'] != 'blob':
            raise ValueError('UNSUPPORTED_TRACKED_GIT_OBJECT_FAIL_CLOSED')
        size = int(git_output(repo, 'cat-file', '-s', entry['git_oid']))
        if size > 150_000_000:
            raise ValueError('OVERSIZED_SOURCE_REQUIRES_STREAMING_HASH')
        raw = git_output(repo, 'cat-file', 'blob', entry['git_oid'])
        if len(raw) != size:
            raise ValueError('GIT_BLOB_BYTE_COUNT_MISMATCH')
        text_eligible = (len(raw) <= MAX_MATCH_BYTES and b'\0' not in raw and
                         Path(entry['path']).suffix.lower() in TEXT_SUFFIXES)
        records.append({**entry, 'revision': revision,
                        'identity': digest((revision + '\0' + entry['path']).encode()),
                        'content_sha256': digest(raw),
                        'content_state': 'bounded_text' if text_eligible else 'uninspected',
                        'mapping_state': 'not_evaluated'})
    return records


def concept_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Load existing SAGE vocabulary without promoting candidate semantics.

    Args:
        config: Existing sage-semantic-concepts.json document.
    """
    definitions = config.get('concepts')
    if not isinstance(definitions, dict) or not definitions:
        raise ValueError('SAGE concept definitions missing')
    results: list[dict[str, Any]] = []
    for name, details in sorted(definitions.items()):
        if not isinstance(details, dict):
            raise ValueError(f'invalid concept definition: {name}')
        aliases = list(dict.fromkeys([name, *details.get('terms', [])]))
        results.append({'name': name, 'aliases': aliases,
                        'related': details.get('related', []),
                        'dimensions': details.get('dimensions', [])})
    return results


def cue_match(label: str, cue: str) -> bool:
    """Test conservative whole-phrase lexical cues; not a semantic assertion.

    Args:
        label: Source path or content excerpt.
        cue: Existing concept alias.
    """
    expression = r'(?<![a-z0-9])' + re.escape(cue.lower()) + r'(?![a-z0-9])'
    return bool(re.search(expression, label.lower()))


def bounded_committed_text(repo: Path, source: dict[str, Any]) -> str | None:
    """Read eligible Git text for matching without persisting its body.

    Args:
        repo: Governed Git repository root.
        source: Revision-pinned, independently inventoried source record.
    """
    if source.get('content_state') != 'bounded_text':
        return None
    if source.get('mode') == '120000':
        return None
    raw = git_output(repo, 'cat-file', 'blob', source['git_oid'])
    if len(raw) > MAX_MATCH_BYTES or b'\0' in raw:
        raise ValueError('CONTENT_MATCH_SCOPE_DRIFT')
    if digest(raw) != source['content_sha256']:
        raise ValueError('SOURCE_CONTENT_DIGEST_MISMATCH')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return None


def candidate_edges(sources: list[dict[str, Any]],
                    concepts: list[dict[str, Any]],
                    repo: Path | None = None) -> list[dict[str, Any]]:
    """Nominate path/content lexical candidates without asserting relevance.

    Args:
        sources: Complete immutable source inventory.
        concepts: Governed, unmodified concept vocabulary.
        repo: Optional Git source for bounded content candidate scanning.
    """
    edges: list[dict[str, Any]] = []
    for source in sources:
        if source['path'] == 'sage-semantic-concepts.json':
            continue  # Vocabulary definitions cannot self-certify source relevance.
        content = bounded_committed_text(repo, source) if repo else None
        for concept in concepts:
            path_aliases = [alias for alias in concept['aliases']
                            if cue_match(source['path'], alias)]
            text_aliases = [alias for alias in concept['aliases']
                            if content is not None and cue_match(content, alias)]
            if path_aliases or text_aliases:
                edges.append({'source_id': source['identity'],
                              'concept': concept['name'],
                              'state': 'candidate_unverified',
                              'matched_aliases': sorted(set(path_aliases + text_aliases)),
                              'match_surfaces': [name for name, found in
                                                 [('path', path_aliases),
                                                  ('content', text_aliases)] if found]})
    return edges


def fingerprint(sources: list[dict[str, Any]],
                concepts: list[dict[str, Any]],
                edges: list[dict[str, Any]]) -> str:
    """Bind a projection to its exact source and concept inputs.

    Args:
        sources: Git source inventory.
        concepts: Semantic vocabulary snapshot.
        edges: Explicit candidate edge records.
    """
    payload = {'projection_schema': 'attested_context_v1',
               'sources': sources, 'concepts': concepts, 'edges': edges}
    return digest(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode())


def prepare(repo: Path, config_path: Path) -> dict[str, Any]:
    """Produce a reproducible, non-authoritative projection candidate.

    Args:
        repo: Repository root.
        config_path: Existing semantic concepts JSON.
    """
    head = committed_head(repo)
    config = json.loads(config_path.read_text(encoding='utf-8'))
    sources = source_records(repo, head)
    concepts = concept_records(config)
    edges = candidate_edges(sources, concepts, repo=repo)
    from sage_neo4j_context import root_governance_sources, source_sections
    sections = source_sections(repo, sources)
    governance = root_governance_sources(sources)
    return {'source_sections': sections, 'root_governance_sources': governance,
            'revision': head, 'sources': sources, 'concepts': concepts,
            'candidate_edges': edges, 'fingerprint': fingerprint(sources, concepts, edges),
            'qualification': 'candidate_only', 'evidence_maturity_assessed': False}
