"""Assert published MkDocs pages display provenance-backed source dates.

A source template which is not published as HTML is not a published content page.
All other absent outputs and any rendered output missing its correct date fail closed.
"""
from __future__ import annotations
import json
import re
from pathlib import Path

MANIFEST = Path('.mkdocs-work/page-freshness-manifest.json')
SITE = Path('.mkdocs-work/site')
NONPUBLIC_TEMPLATES = {
    'templates/sage-evidence-generation-request.md',
    'templates/sage-evidence-record-template.md',
}


def verify(manifest: dict, site: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    excluded: list[str] = []
    checked = 0
    for record in manifest['pages']:
        rel = Path(record['staged'])
        expected = record['git_content_date'] or 'Not established'
        html_candidates = ([site / 'index.html'] if rel.as_posix() == 'index.md'
                           else [site / rel.with_suffix('') / 'index.html',
                                 site / rel.with_suffix('.html')])
        html_file = next((candidate for candidate in html_candidates if candidate.is_file()), None)
        if html_file is None:
            if rel.as_posix() in NONPUBLIC_TEMPLATES:
                excluded.append(rel.as_posix())
            else:
                errors.append(f'Missing published HTML for {rel}')
            continue
        rendered = html_file.read_text(encoding='utf-8')
        correct_date = re.search(r'Last content updated:</strong>\s*' + re.escape(expected), rendered)
        if not correct_date:
            errors.append(f'Incorrect or absent content date: {rel}')
        checked += 1
    if errors:
        raise SystemExit('RENDERED_PAGE_FRESHNESS=FAIL: ' + repr(errors[:20]) + f' (total {len(errors)})')
    if checked == 0:
        raise SystemExit('RENDERED_PAGE_FRESHNESS=FAIL: No published pages verified')
    print(f'RENDERED_PAGE_FRESHNESS=PASS; PUBLISHED_PAGES_VERIFIED={checked}; NONPUBLIC_TEMPLATES={len(excluded)}')
    for item in excluded:
        print(f'NONPUBLIC_SOURCE_TEMPLATE={item}')
    return checked, excluded


if __name__ == '__main__':
    verify(json.loads(MANIFEST.read_text(encoding='utf-8')), SITE)
