#!/usr/bin/env python3
"""Validate that raw evidence artifacts remain published but outside navigation."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path


class NavigationError(RuntimeError):
    """Raised when generated MkDocs navigation violates the site contract."""


class PrimaryNavigationParser(HTMLParser):
    """Collect links and text from the Material primary navigation element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.in_primary = False
        self.primary_depth = 0
        self.hrefs: list[str] = []
        self.text: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())

        if (
            tag == "nav"
            and not self.in_primary
            and {"md-nav", "md-nav--primary"}.issubset(classes)
        ):
            self.in_primary = True
            self.primary_depth = self.depth

        if self.in_primary and tag == "a":
            href = attributes.get("href")
            if href:
                self.hrefs.append(href)

        self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        self.depth -= 1
        if (
            self.in_primary
            and tag == "nav"
            and self.depth == self.primary_depth
        ):
            self.in_primary = False

    def handle_data(self, data: str) -> None:
        if self.in_primary:
            value = re.sub(r"\s+", " ", data).strip()
            if value:
                self.text.append(value)


def repository_root(argument: str | None) -> Path:
    """Resolve the active Git repository root."""
    start = Path(argument).expanduser().resolve() if argument else Path.cwd()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        text=True,
        capture_output=True,
    )
    return Path(result.stdout.strip()).resolve()


def resolve_site(repo: Path, value: str) -> Path:
    """Resolve the generated site and require it inside the repository."""
    raw = Path(value).expanduser()
    site = raw.resolve() if raw.is_absolute() else (repo / raw).resolve()
    if repo not in site.parents:
        raise NavigationError(
            f"Generated site must remain inside the repository: {site}"
        )
    return site


def validate(site: Path) -> tuple[int, int]:
    """Validate navigation exclusion and artifact preservation."""
    index = site / "index.html"
    artifact_root = site / "evidence-artifacts"

    if not index.is_file():
        raise NavigationError(f"Landing page is missing: {index}")
    if not artifact_root.is_dir():
        raise NavigationError(
            f"Evidence artifacts were removed from the published site: {artifact_root}"
        )

    artifact_files = [
        path
        for path in artifact_root.rglob("*")
        if path.is_file()
    ]
    if not artifact_files:
        raise NavigationError("Published evidence-artifact directory is empty")

    parser = PrimaryNavigationParser()
    parser.feed(index.read_text(encoding="utf-8"))

    if not parser.hrefs:
        raise NavigationError("Primary MkDocs navigation could not be parsed")

    artifact_links = [
        href
        for href in parser.hrefs
        if "evidence-artifacts/" in href
    ]
    if artifact_links:
        raise NavigationError(
            "Raw evidence artifacts remain in primary navigation: "
            + ", ".join(artifact_links[:10])
        )

    navigation_text = " ".join(parser.text)
    if "Evidence artifacts" in navigation_text:
        raise NavigationError(
            "The Evidence artifacts section remains in primary navigation"
        )

    for required in ("Infrastructure", "Evidence"):
        if required not in navigation_text:
            raise NavigationError(
                f"Expected primary navigation section is missing: {required}"
            )

    return len(parser.hrefs), len(artifact_files)


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Validate Kalaxy3 MkDocs navigation"
    )
    parser.add_argument("--repo")
    parser.add_argument("--site", default=".mkdocs-work/site")
    return parser.parse_args()


def main() -> int:
    """Run navigation validation."""
    args = parse_args()
    try:
        repo = repository_root(args.repo)
        site = resolve_site(repo, args.site)
        link_count, artifact_count = validate(site)

        print("Kalaxy3 MkDocs navigation validation: PASS")
        print(f"Primary navigation links: {link_count}")
        print(f"Published artifact files: {artifact_count}")
        print("Evidence artifacts in navigation: 0")
        return 0
    except (
        NavigationError,
        OSError,
        subprocess.CalledProcessError,
    ) as error:
        print(
            f"Kalaxy3 MkDocs navigation validation: FAIL\n{error}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
