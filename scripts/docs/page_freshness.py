"""Expose original Git-content dates in staged MkDocs pages, never build timestamps."""
from __future__ import annotations
import datetime as dt
import json
import subprocess
from pathlib import Path

LABEL = '<p class="sage-content-updated"><strong>Last content updated:</strong> '


def git_date(repo: Path, original: Path) -> str | None:
    relative = original.relative_to(repo).as_posix()
    result = subprocess.run(
        ['git', '-C', str(repo), 'log', '-1', '--follow', '--format=%cs', '--', relative],
        text=True, capture_output=True, check=True,
    )
    value = result.stdout.strip()
    if not value:
        return None
    dt.date.fromisoformat(value)
    return value


def annotate_staged_pages(repo: Path, staged_source: Path) -> dict:
    mapping = []
    missing = []
    for staged in sorted(staged_source.rglob('*.md')):
        relative = staged.relative_to(staged_source)
        original = repo / 'markdown' / relative
        if relative.as_posix() == 'index.md':
            original = repo / 'markdown' / '_index.md'
        if not original.is_file():
            raise RuntimeError(f'Staged page has no canonical source: {relative}')
        date = git_date(repo, original)
        if date is None:
            # Missing history must be explicit, never converted to a current timestamp.
            display = 'Not established'
            missing.append(original.relative_to(repo).as_posix())
        else:
            display = date
        body = staged.read_text(encoding='utf-8')
        if 'class="sage-content-updated"' in body:
            raise RuntimeError(f'Duplicate freshness annotation: {relative}')
        staged.write_text(body.rstrip() + '\n\n---\n\n' + LABEL + display + '</p>\n', encoding='utf-8')
        mapping.append({'staged': relative.as_posix(), 'source': original.relative_to(repo).as_posix(), 'git_content_date': date})
    manifest = {'schema_version': '1', 'date_semantics': 'last Git content commit of canonical Markdown source; not build or observation date', 'pages': mapping, 'missing_git_history': missing}
    path = staged_source.parent / 'page-freshness-manifest.json'
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'PAGE_FRESHNESS_STAGED={len(mapping)}; DATES_PROVEN={len(mapping)-len(missing)}; MISSING_HISTORY={len(missing)}')
    return manifest
