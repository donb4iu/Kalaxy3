#!/usr/bin/env python3
"""Validate promoted MkDocs publication output against the staged site."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
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


class ValidationError(RuntimeError):
    """Raised when publication output does not match the staged site."""


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
        raise ValidationError(f"{label} must be inside the repository: {resolved}")
    return resolved


def sha256(path: Path) -> str:
    """Return the SHA-256 digest for one file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, str]:
    """Return a deterministic digest inventory and reject symlinks."""
    if not root.is_dir():
        raise ValidationError(f"Directory is missing: {root}")

    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValidationError(f"Symbolic links are not allowed: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256(path)
    return result


def validate_structure(root: Path) -> tuple[int, int]:
    """Validate required MkDocs structures and reject Daux output."""
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            raise ValidationError(f"Required publication file is missing: {relative}")

    present_forbidden = [
        relative
        for relative in FORBIDDEN_PATHS
        if (root / relative).exists()
    ]
    if present_forbidden:
        raise ValidationError(
            "Daux output found in MkDocs publication: "
            + ", ".join(present_forbidden)
        )

    html_count = sum(1 for path in root.rglob("*.html") if path.is_file())
    if html_count < MINIMUM_HTML_FILES:
        raise ValidationError(
            f"Expected at least {MINIMUM_HTML_FILES} HTML files, found {html_count}"
        )

    file_count = sum(1 for path in root.rglob("*") if path.is_file())
    return file_count, html_count


def parse_args() -> argparse.Namespace:
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Validate promoted MkDocs publication output"
    )
    parser.add_argument("--repo")
    parser.add_argument("--source", default=".mkdocs-work/site")
    parser.add_argument("--destination", default="docs")
    return parser.parse_args()


def main() -> int:
    """Run publication validation."""
    args = parse_args()
    try:
        repo = repository_root(args.repo)
        source = resolve_inside_repo(repo, args.source, "source")
        destination = resolve_inside_repo(
            repo,
            args.destination,
            "destination",
        )

        source_files, source_html = validate_structure(source)
        destination_files, destination_html = validate_structure(destination)

        source_inventory = inventory(source)
        destination_inventory = inventory(destination)

        if source_inventory != destination_inventory:
            source_only = sorted(
                set(source_inventory) - set(destination_inventory)
            )
            destination_only = sorted(
                set(destination_inventory) - set(source_inventory)
            )
            changed = sorted(
                relative
                for relative in set(source_inventory) & set(destination_inventory)
                if source_inventory[relative] != destination_inventory[relative]
            )
            raise ValidationError(
                "Published output differs from staged MkDocs site; "
                f"source_only={source_only[:10]}, "
                f"destination_only={destination_only[:10]}, "
                f"changed={changed[:10]}"
            )

        print("Kalaxy3 MkDocs publication validation: PASS")
        print(f"Source files:      {source_files}")
        print(f"Published files:   {destination_files}")
        print(f"Source HTML:       {source_html}")
        print(f"Published HTML:    {destination_html}")
        print(f"Publication root:  {destination}")
        return 0
    except (
        OSError,
        ValidationError,
        subprocess.CalledProcessError,
    ) as error:
        print(
            f"Kalaxy3 MkDocs publication validation: FAIL\n{error}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
