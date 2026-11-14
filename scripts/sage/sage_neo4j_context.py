#!/usr/bin/env python3
"""Extract source-attested context pointers from revision-pinned Git records."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import bounded_committed_text, digest

HEADING = re.compile(r'^(#{2,5})\s+(.+?)\s*$', re.MULTILINE)
CONTEXT_KINDS: dict[str, tuple[str, ...]] = {
    'decision_section': ('decision', 'chosen approach', 'selected option'),
    'alternatives_section': ('alternatives', 'options considered', 'rejected options'),
    'rationale_section': ('rationale', 'reasoning', 'trade-offs', 'tradeoffs'),
    'context_section': ('context', 'background', 'prior art'),
    'assumptions_section': ('assumptions', 'constraints'),
    'outcomes_section': ('outcomes', 'results', 'measurements', 'lessons learned'),
    'obligations_section': ('obligations', 'requirements', 'applicability'),
    'consequences_section': ('consequences', 'implications', 'risks'),
    'operational_context_section': ('security', 'observability', 'monitoring',
                                    'operations', 'cost', 'recovery', 'lifecycle'),
}
ROOT_GOVERNANCE_PATHS = ('AGENTS.md', 'SAGE.md')


def heading_kind(heading: str) -> str | None:
    """Classify a literal heading as a section pointer, never a judgment.

    Args:
        heading: Source-attested Markdown heading, without its hash prefix.
    """
    label = re.sub(r'[^a-z0-9 -]', ' ', heading.lower()).strip()
    label = re.sub(r'\s+', ' ', label)
    for kind, values in CONTEXT_KINDS.items():
        if any(label == value or label.startswith(value + ' ') for value in values):
            return kind
    return None


def markdown_sections(source: dict[str, Any], body: str) -> list[dict[str, Any]]:
    """Capture version-bound section headings, line numbers and exact digests.

    Args:
        source: Immutable Git source identity and content hash.
        body: Independently verified committed Markdown text.
    """
    matches = list(HEADING.finditer(body))
    result: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        heading = match.group(2).strip(' #')
        kind = heading_kind(heading)
        if kind is None and source['path'] not in ROOT_GOVERNANCE_PATHS:
            continue
        if kind is None:
            kind = 'repository_instruction_section'
        boundary = next((later.start() for later in matches[index + 1:]
                         if len(later.group(1)) <= len(match.group(1))), len(body))
        line = body.count('\n', 0, match.start()) + 1
        content = body[match.start():boundary]
        record_key = f"{source['identity']}\0{line}\0{heading}"
        result.append({'identity': digest(record_key.encode()),
                       'source_id': source['identity'], 'source_path': source['path'],
                       'revision': source['revision'], 'heading': heading[:160],
                       'kind': kind, 'start_line': line,
                       'end_line': line + content.count('\n'),
                       'section_sha256': digest(content.encode('utf-8')),
                       'source_sha256': source['content_sha256'],
                       'attestation': 'literal_markdown_heading',
                       'semantic_qualification': 'not_evaluated'})
    return result


def source_sections(repo: Path, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract only structurally explicit context from the pinned Git corpus.

    Args:
        repo: Git repository holding immutable committed blobs.
        sources: Complete inventory of revision-qualified Git sources.
    """
    sections: list[dict[str, Any]] = []
    for source in sources:
        if not source['path'].endswith('.md'):
            continue
        body = bounded_committed_text(repo, source)
        if body is not None:
            sections.extend(markdown_sections(source, body))
    return sorted(sections, key=lambda row: (row['source_path'], row['start_line']))


def root_governance_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identify existing repository-root instructions without interpreting them.

    Args:
        sources: Complete revision-qualified Git source inventory.
    """
    return [{'source_id': row['identity'], 'source_path': row['path'],
             'source_sha256': row['content_sha256'], 'revision': row['revision'],
             'attestation': 'repository_root_instruction_location',
             'applicability': 'repository_implementation_context_pointer',
             'semantic_qualification': 'not_evaluated'}
            for row in sources if row['path'] in ROOT_GOVERNANCE_PATHS]
