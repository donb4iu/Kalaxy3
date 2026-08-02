#!/usr/bin/env python3
"""Validate policy-driven Kalaxy3 MkDocs navigation and evidence reachability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

from navigation_support import (
    NavigationError,
    NavigationPolicy,
    evidence_index_pages,
    linked_site_urls,
    normalized_primary_hrefs,
    parse_links,
    primary_evidence_pages,
    source_url,
)

SAGE_ROOT = Path(__file__).resolve().parents[1] / "sage"
if str(SAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(SAGE_ROOT))

from workflow.evidence_records import EvidenceCatalog  # noqa: E402
from workflow.markdown import require_inside  # noqa: E402

DEFAULT_POLICY = "mkdocs-navigation-policy.json"


def parse_args() -> argparse.Namespace:
    """Parse validation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--site", default=".mkdocs-work/site")
    parser.add_argument("--manifest", default=".mkdocs-work/navigation-manifest.json")
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--report")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    """Load one generated navigation manifest."""
    if not path.is_file():
        raise NavigationError(f"Navigation manifest is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise NavigationError("Navigation manifest must be a JSON object")
    return payload


def validate_primary(
    site: Path,
    manifest: Mapping[str, Any],
    policy: NavigationPolicy,
) -> list[dict[str, str]]:
    """Validate primary labels, count, and evidence exclusions."""
    links = parse_links(site / "index.html", policy, primary_only=True)
    if not links:
        raise NavigationError("Primary MkDocs navigation could not be parsed")
    expected = manifest.get("primary_leaf_count")
    if len(links) != expected:
        raise NavigationError(
            f"Expected {expected} primary links; got {len(links)}"
        )
    hrefs = normalized_primary_hrefs(links)
    excluded = manifest.get("excluded_evidence_record_paths")
    if not isinstance(excluded, list):
        raise NavigationError("Manifest evidence exclusions are missing")
    exposed = sorted({source_url(path) for path in excluded}.intersection(hrefs))
    if exposed:
        raise NavigationError(
            "Cataloged evidence remains in primary navigation: "
            + ", ".join(exposed[:10])
        )
    if any("evidence-artifacts/" in href for href in hrefs):
        raise NavigationError("Raw evidence artifacts remain in primary navigation")
    labels_by_href: dict[str, list[str]] = {}
    for link, href in zip(links, normalized_primary_hrefs(links)):
        labels_by_href.setdefault(href, []).append(link["label"])
    for item in primary_evidence_pages(policy):
        href = source_url(item.path)
        actual = labels_by_href.get(href, [])
        if item.label not in actual:
            raise NavigationError(
                f"Evidence navigation mismatch: "
                f"{item.label} -> {href}; rendered labels: {actual}"
            )
    labels = [link["label"] for link in links]
    long_labels = [
        label for label in labels if len(label) > policy.maximum_label_length
    ]
    if long_labels:
        raise NavigationError(
            "Primary labels exceed policy maximum: "
            + "; ".join(long_labels[:5])
        )
    return links


def record_html(site: Path, source_path: str) -> Path:
    """Return generated HTML path for one evidence source record."""
    return site / source_url(source_path) / "index.html"


def validate_records(
    catalog: EvidenceCatalog,
    site: Path,
    policy: NavigationPolicy,
) -> int:
    """Validate publication and index reachability for all evidence records."""
    missing_html = [
        item.source_path
        for item in catalog.records
        if not record_html(site, item.source_path).is_file()
    ]
    if missing_html:
        raise NavigationError(
            "Evidence record HTML is missing: " + ", ".join(missing_html[:10])
        )
    linked = linked_site_urls(site, evidence_index_pages(site, policy), policy)
    missing_links = [
        item.source_path
        for item in catalog.records
        if source_url(item.source_path) not in linked
    ]
    if missing_links:
        raise NavigationError(
            "Evidence record is not linked from indexes: "
            + ", ".join(missing_links[:10])
        )
    return len(linked)


def validate(
    repo: Path,
    site: Path,
    manifest_path: Path,
    policy: NavigationPolicy,
) -> dict[str, Any]:
    """Validate the complete rendered navigation contract."""
    manifest = load_manifest(manifest_path)
    artifact_root = site / "evidence-artifacts"
    if not artifact_root.is_dir():
        raise NavigationError("Published evidence artifacts were removed")
    artifact_count = sum(1 for path in artifact_root.rglob("*") if path.is_file())
    if artifact_count == 0:
        raise NavigationError("Published evidence-artifact directory is empty")
    links = validate_primary(site, manifest, policy)
    catalog = EvidenceCatalog.load(repo / "markdown/evidence/catalog.json")
    indexed_link_count = validate_records(catalog, site, policy)
    return {
        "schema_version": "1.0",
        "policy_path": str(policy.path.relative_to(repo)),
        "primary_navigation_links": len(links),
        "cataloged_evidence_records": len(catalog.records),
        "cataloged_evidence_in_primary_navigation": 0,
        "curated_evidence_navigation_pages": len(
            primary_evidence_pages(policy)
        ),
        "evidence_index_resolved_links": indexed_link_count,
        "published_artifact_files": artifact_count,
        "maximum_primary_label_length": max(len(item["label"]) for item in links),
        "status": "pass",
    }


def write_report(path: Path | None, report: Mapping[str, Any]) -> None:
    """Write an optional JSON validation report."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fixture_policy(path: Path) -> NavigationPolicy:
    """Write and load a minimal Material parser policy fixture."""
    payload = {
        "schema_version": "1.0",
        "policy_id": "fixture",
        "site_root_label": "Kalaxy3",
        "landing_page": "index.md",
        "excluded_top_level_names": ["index.md"],
        "label_policy": {
            "front_matter_key": "nav_title",
            "fallback_order": ["first-h1"],
            "maximum_length": 80,
        },
        "evidence": {
            "root_directory": "evidence",
            "root_label": "Evidence",
            "index_page": "evidence/index.md",
            "catalog_path": "evidence/catalog.json",
            "repository_source_prefix": "markdown/",
            "hide_catalog_records": True,
            "hide_generated_group_children": ["sections"],
            "curated_pages": [
                {
                    "label": "Current records",
                    "path": "evidence/current.md",
                }
            ],
        },
        "material": {
            "primary_navigation_classes": ["md-nav", "md-nav--primary"],
            "secondary_navigation_classes": ["md-nav", "md-nav--secondary"],
            "leaf_link_class": "md-nav__link",
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return NavigationPolicy.load(path)


def self_test() -> int:
    """Exercise dual-path mapping and Material navigation parsing."""
    repository_url = source_url("markdown/operations/example.md")
    staged_url = source_url("operations/example.md")
    if repository_url != "operations/example/" or staged_url != repository_url:
        raise NavigationError("Evidence source URL namespace mapping")
    for invalid in (
        "../operations/example.md",
        "/operations/example.md",
        "operations/example.txt",
        "operations\\example.md",
    ):
        try:
            source_url(invalid)
        except NavigationError:
            continue
        raise NavigationError(f"Unsafe source path was accepted: {invalid}")
    html = (
        '<nav class="md-nav md-nav--primary">'
        '<input class="md-nav__toggle" type="checkbox">'
        '<a class="md-nav__button md-logo" href=".">'
        '<img src="rpi4.png" alt="logo"></a>'
        '<a class="md-nav__link" href="evidence/"><span>Evidence</span></a>'
        '<a class="md-nav__link" href="evidence/current/">'
        '<span>Current records</span></a>'
        '<nav class="md-nav md-nav--secondary">'
        '<a class="md-nav__link" href="#details">Details</a></nav>'
        '<a class="md-nav__link" href="operations/runbook/">'
        '<span>Runbook</span></a></nav>'
    )
    with TemporaryDirectory() as directory:
        root = Path(directory)
        policy = fixture_policy(root / "policy.json")
        page = root / "index.html"
        page.write_text(html, encoding="utf-8")
        links = parse_links(page, policy, primary_only=True)
        labels = [item["label"] for item in links]
        if labels != ["Evidence", "Current records", "Runbook"]:
            raise NavigationError(f"Material primary parser differs: {labels}")
        manifest = {
            "primary_leaf_count": 3,
            "excluded_evidence_record_paths": [],
        }
        validate_primary(root, manifest, policy)
    print("PASS repository and staged source URL mapping")
    print("PASS unsafe source-path rejection")
    print("PASS policy-driven Material primary-navigation parsing")
    print("PASS section-index URL-and-label validation")
    print("Kalaxy3 MkDocs navigation validator self-test: PASS")
    return 0


def main() -> int:
    """Run rendered navigation validation."""
    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    site = require_inside(repo, Path(args.site))
    manifest = require_inside(repo, Path(args.manifest))
    policy = NavigationPolicy.load(require_inside(repo, Path(args.policy)))
    report_path = require_inside(repo, Path(args.report)) if args.report else None
    report = validate(repo, site, manifest, policy)
    write_report(report_path, report)
    print("Kalaxy3 MkDocs navigation validation: PASS")
    print(f"Primary navigation links: {report['primary_navigation_links']}")
    print(f"Cataloged evidence records: {report['cataloged_evidence_records']}")
    print("Cataloged evidence records in primary navigation: 0")
    print(
        "Curated Evidence navigation pages: "
        f"{report['curated_evidence_navigation_pages']}"
    )
    print(f"Published artifact files: {report['published_artifact_files']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NavigationError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Kalaxy3 MkDocs navigation validation: FAIL\n{error}", file=sys.stderr)
        raise SystemExit(2)
