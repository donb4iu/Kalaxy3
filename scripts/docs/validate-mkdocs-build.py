#!/usr/bin/env python3
"""Validate the structural output of a staged Kalaxy3 MkDocs build."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

DEFAULT_SITE_DIR: Final[str] = ".mkdocs-work/site"


def parse_args() -> argparse.Namespace:
    """Parse repository and site-directory arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Kalaxy3 repository root; defaults to the current directory.",
    )
    parser.add_argument(
        "--site-dir",
        default=DEFAULT_SITE_DIR,
        help="Repository-relative staged site directory.",
    )
    return parser.parse_args()


def require_file(path: Path, description: str) -> None:
    """Require a non-empty generated file."""
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"Missing or empty {description}: {path}")


def validate_site(site_dir: Path) -> tuple[int, int]:
    """Validate core MkDocs output and reject Daux structures."""
    require_file(site_dir / "index.html", "landing page")
    require_file(site_dir / "search" / "search_index.json", "search index")
    require_file(site_dir / "rpi4.png", "site image")
    html_files = list(site_dir.rglob("*.html"))
    if len(html_files) < 20:
        raise RuntimeError(
            f"Too few generated HTML files: {len(html_files)}"
        )
    forbidden = (
        "daux_libraries",
        "daux_search_index.js",
        "themes/daux",
    )
    present = [item for item in forbidden if (site_dir / item).exists()]
    if present:
        raise RuntimeError(
            f"Daux output found in staged MkDocs site: {present}"
        )
    total_files = sum(
        1 for path in site_dir.rglob("*") if path.is_file()
    )
    return len(html_files), total_files


def main() -> int:
    """Validate and report the staged MkDocs site."""
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    site_dir = repo / args.site_dir
    html_count, total_count = validate_site(site_dir)
    print("Kalaxy3 staged MkDocs build validation: PASS")
    print(f"Generated HTML files: {html_count}")
    print(f"Total generated files: {total_count}")
    print(f"Staged site: {site_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
