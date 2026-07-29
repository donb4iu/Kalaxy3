#!/usr/bin/env python3
"""Promote a validated MkDocs site into a repository publication directory."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final

REQUIRED_FILES: Final[tuple[str, ...]] = (
    "index.html",
    "rpi4.png",
    "search/search_index.json",
)
FORBIDDEN_PATHS: Final[tuple[str, ...]] = (
    "daux_libraries",
    "daux_search_index.js",
    "themes/daux",
)
MINIMUM_HTML_FILES: Final[int] = 100


class PromotionError(RuntimeError):
    """Raised when publication promotion cannot be completed safely."""


def repository_root(argument: str | None) -> Path:
    """Resolve the Git repository root."""
    start = Path(argument).expanduser().resolve() if argument else Path.cwd()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        check=True,
        text=True,
        capture_output=True,
    )
    return Path(result.stdout.strip()).resolve()


def resolve_inside_repo(repo: Path, value: str, label: str) -> Path:
    """Resolve one path and require it to remain inside the repository."""
    raw = Path(value).expanduser()
    resolved = raw.resolve() if raw.is_absolute() else (repo / raw).resolve()
    if resolved == repo or repo not in resolved.parents:
        raise PromotionError(f"{label} must be inside the repository: {resolved}")
    return resolved


def sha256(path: Path) -> str:
    """Return the SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    """Return a deterministic file digest inventory and reject symlinks."""
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise PromotionError(f"Symbolic links are not allowed: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256(path)
    return result


def validate_source(source: Path) -> dict[str, str]:
    """Validate the staged MkDocs source before promotion."""
    if not source.is_dir():
        raise PromotionError(f"MkDocs site directory is missing: {source}")

    for relative in REQUIRED_FILES:
        if not (source / relative).is_file():
            raise PromotionError(f"Required MkDocs output is missing: {relative}")

    present_forbidden = [
        relative
        for relative in FORBIDDEN_PATHS
        if (source / relative).exists()
    ]
    if present_forbidden:
        raise PromotionError(
            "Daux output found in staged MkDocs site: "
            + ", ".join(present_forbidden)
        )

    html_count = sum(1 for path in source.rglob("*.html") if path.is_file())
    if html_count < MINIMUM_HTML_FILES:
        raise PromotionError(
            f"Expected at least {MINIMUM_HTML_FILES} HTML files, found {html_count}"
        )

    files = inventory(source)
    if not files:
        raise PromotionError("MkDocs site inventory is empty")
    return files


def promote(source: Path, destination: Path) -> tuple[int, int]:
    """Replace destination with an exact, verified copy of source."""
    source_inventory = validate_source(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.mkdocs-promote-",
            dir=destination.parent,
        )
    )
    backup = destination.parent / (
        f".{destination.name}.mkdocs-backup-{os.getpid()}"
    )

    try:
        shutil.copytree(source, temporary, dirs_exist_ok=True)
        copied_inventory = inventory(temporary)
        if copied_inventory != source_inventory:
            raise PromotionError(
                "Temporary publication copy differs from the MkDocs site"
            )

        if backup.exists():
            shutil.rmtree(backup)

        if destination.exists():
            destination.rename(backup)

        try:
            temporary.rename(destination)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination)
            if backup.exists():
                backup.rename(destination)
            raise

        published_inventory = inventory(destination)
        if published_inventory != source_inventory:
            if destination.exists():
                shutil.rmtree(destination)
            if backup.exists():
                backup.rename(destination)
            raise PromotionError(
                "Published directory differs from the validated MkDocs site"
            )

        if backup.exists():
            shutil.rmtree(backup)

        html_count = sum(
            1 for relative in published_inventory if relative.endswith(".html")
        )
        return len(published_inventory), html_count
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if backup.exists() and not destination.exists():
            backup.rename(destination)


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Promote validated MkDocs output for publication"
    )
    parser.add_argument("--repo")
    parser.add_argument("--source", default=".mkdocs-work/site")
    parser.add_argument("--destination", default="docs")
    return parser.parse_args()


def main() -> int:
    """Run publication promotion."""
    args = parse_args()
    try:
        repo = repository_root(args.repo)
        source = resolve_inside_repo(repo, args.source, "source")
        destination = resolve_inside_repo(
            repo,
            args.destination,
            "destination",
        )
        if source == destination:
            raise PromotionError("Source and destination must differ")
        if destination in source.parents or source in destination.parents:
            raise PromotionError(
                "Source and destination must not contain one another"
            )

        file_count, html_count = promote(source, destination)
        print("Kalaxy3 MkDocs publication promotion: PASS")
        print(f"Source:          {source}")
        print(f"Destination:     {destination}")
        print(f"Published files: {file_count}")
        print(f"HTML files:      {html_count}")
        return 0
    except (
        OSError,
        PromotionError,
        subprocess.CalledProcessError,
    ) as error:
        print(
            f"Kalaxy3 MkDocs publication promotion: FAIL\n{error}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
