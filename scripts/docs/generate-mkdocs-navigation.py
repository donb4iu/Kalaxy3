#!/usr/bin/env python3
"""Generate policy-driven MkDocs navigation for staged Kalaxy3 Markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from navigation_support import (
    NavigationBuilder,
    NavigationError,
    NavigationPolicy,
    nav_leaf_paths,
)

DEFAULT_WORK_DIR = ".mkdocs-work"
DEFAULT_POLICY = "mkdocs-navigation-policy.json"


def parse_args() -> argparse.Namespace:
    """Parse generator options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", default=DEFAULT_WORK_DIR)
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def load_base_config(repo: Path) -> dict[str, Any]:
    """Load the repository MkDocs configuration."""
    path = repo / "mkdocs.yml"
    if not path.is_file():
        raise NavigationError(f"MkDocs configuration is missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise NavigationError("MkDocs configuration must be a mapping")
    return data


def generated_config(
    base: dict[str, Any],
    nav: list[Any],
    hidden: list[str],
) -> dict[str, Any]:
    """Return a work-directory-relative generated configuration."""
    result = dict(base)
    result["docs_dir"] = "source"
    result["site_dir"] = "site"
    result["nav"] = nav
    exclusions = ["/evidence-artifacts/"]
    exclusions.extend(f"/{path}" for path in hidden)
    result["not_in_nav"] = "\n".join(exclusions) + "\n"
    theme = dict(result.get("theme") or {})
    features = list(theme.get("features") or [])
    if "navigation.indexes" not in features:
        features.append("navigation.indexes")
    theme["features"] = features
    result["theme"] = theme
    return result


def write_outputs(repo: Path, work_dir: str, policy_path: str) -> dict[str, Any]:
    """Write generated config and machine-readable navigation manifest."""
    work = repo / work_dir
    source = work / "source"
    policy = NavigationPolicy.load(repo / policy_path)
    builder = NavigationBuilder.create(source, policy)
    nav = builder.build()
    leaves = nav_leaf_paths(nav)
    if len(leaves) != len(set(leaves)):
        raise NavigationError("Generated navigation has duplicate leaf paths")
    hidden = builder.hidden_paths()
    config = generated_config(load_base_config(repo), nav, hidden)
    config_path = work / "mkdocs.generated.yml"
    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0",
        "generator": "scripts/docs/generate-mkdocs-navigation.py",
        **policy.as_manifest(),
        "config_path": str(config_path.relative_to(repo)),
        "primary_leaf_count": len(leaves),
        "primary_leaf_paths": leaves,
        "excluded_evidence_record_count": len(builder.excluded),
        "excluded_evidence_record_paths": sorted(builder.excluded),
        "hidden_markdown_count": len(hidden),
        "hidden_markdown_paths": hidden,
    }
    manifest_path = work / "navigation-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def write_fixture_policy(path: Path) -> None:
    """Write a minimal policy fixture for the self-test."""
    payload = {
        "schema_version": "1.0",
        "policy_id": "fixture",
        "site_root_label": "Kalaxy3",
        "landing_page": "index.md",
        "excluded_top_level_names": ["index.md", "evidence-artifacts", "templates"],
        "label_policy": {
            "front_matter_key": "nav_title",
            "fallback_order": ["first-h1", "humanized-filename"],
            "maximum_length": 80,
        },
        "evidence": {
            "root_directory": "evidence",
            "root_label": "Evidence",
            "index_page": "evidence/index.md",
            "catalog_path": "evidence/catalog.json",
            "repository_source_prefix": "markdown/",
            "hide_catalog_records": True,
            "hide_generated_group_children": ["sections", "status", "subjects"],
            "curated_pages": [
                {"label": "Current records", "path": "evidence/current.md"},
                {"label": "Historical records", "path": "evidence/legacy.md"},
                {"label": "Migration report", "path": "evidence/migration-report.md"},
                {"label": "Browse by section", "path": "evidence/sections/index.md"},
                {"label": "Browse by status", "path": "evidence/status/index.md"},
                {"label": "Browse by subject", "path": "evidence/subjects/index.md"},
            ],
        },
        "material": {
            "primary_navigation_classes": ["md-nav", "md-nav--primary"],
            "secondary_navigation_classes": ["md-nav", "md-nav--secondary"],
            "leaf_link_class": "md-nav__link",
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_fixture_source(source: Path) -> None:
    """Write staged-source pages for the generator self-test."""
    for group in ("sections", "status", "subjects"):
        (source / "evidence" / group).mkdir(parents=True, exist_ok=True)
    (source / "operations").mkdir(parents=True)
    (source / "index.md").write_text("# Kalaxy3\n", encoding="utf-8")
    pages = (
        "index.md",
        "current.md",
        "legacy.md",
        "migration-report.md",
        "sections/index.md",
        "status/index.md",
        "subjects/index.md",
    )
    for item in pages:
        path = source / "evidence" / item
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {item}\n", encoding="utf-8")
    (source / "operations/record.md").write_text(
        "---\nnav_title: Concise record\n---\n# Long formal title\n",
        encoding="utf-8",
    )


def write_fixture_catalog(source: Path) -> None:
    """Write one cataloged evidence record for the self-test."""
    catalog = {
        "records": [
            {
                "evidence_id": "SAGE-K3-TEST-20260802-001",
                "source_path": "markdown/operations/record.md",
                "record_class": "sage-current",
                "title": "Long formal title",
                "nav_title": "Concise record",
                "metadata_source": "front-matter",
                "migration_status": "current",
            }
        ]
    }
    (source / "evidence/catalog.json").write_text(
        json.dumps(catalog),
        encoding="utf-8",
    )


def self_test() -> int:
    """Exercise policy-driven exclusions and curated Evidence navigation."""
    with TemporaryDirectory() as directory:
        repo = Path(directory)
        source = repo / ".mkdocs-work/source"
        write_fixture_source(source)
        write_fixture_catalog(source)
        policy_path = repo / DEFAULT_POLICY
        write_fixture_policy(policy_path)
        policy = NavigationPolicy.load(policy_path)
        builder = NavigationBuilder.create(source, policy)
        navigation = builder.build()
        leaves = nav_leaf_paths(navigation)
        if "operations/record.md" in leaves:
            raise NavigationError("Cataloged evidence was not excluded")
        evidence_entry = next(
            item["Evidence"]
            for item in navigation
            if isinstance(item, dict) and "Evidence" in item
        )
        if evidence_entry[0] != "evidence/index.md":
            raise NavigationError("Evidence section index is not first")
        if len(policy.curated_evidence_pages) != 6:
            raise NavigationError("Curated Evidence child count differs")
        if len(evidence_entry) != 7:
            raise NavigationError("Evidence primary-page count differs")
    print("PASS policy-driven catalog exclusion")
    print("PASS Evidence section-index contract")
    print("PASS curated Evidence pages are data, not code constants")
    print("Kalaxy3 MkDocs navigation generator self-test: PASS")
    return 0


def main() -> int:
    """Generate the staged MkDocs configuration and manifest."""
    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    manifest = write_outputs(repo, args.work_dir, args.policy)
    print("Kalaxy3 MkDocs navigation generation: PASS")
    print(f"Primary navigation pages: {manifest['primary_leaf_count']}")
    print(
        "Cataloged evidence records hidden from primary navigation: "
        f"{manifest['excluded_evidence_record_count']}"
    )
    print(
        "Curated Evidence navigation pages: "
        f"{len(manifest['curated_evidence'])}"
    )
    print(f"Generated config: {manifest['config_path']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NavigationError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Kalaxy3 MkDocs navigation generation: FAIL\n{error}", file=sys.stderr)
        raise SystemExit(2)
