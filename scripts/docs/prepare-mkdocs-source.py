#!/usr/bin/env python3
"""Prepare canonical Kalaxy3 Markdown for a staged MkDocs build."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from pathlib import Path
from typing import Final

DEFAULT_WORK_DIR: Final[str] = ".mkdocs-work"
LINK_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?P<prefix>\[[^\]]*\]\()"
    r"(?P<target>[^)\s]+\.md(?:[?#][^)]*)?)"
    r"(?P<suffix>\))"
)


def parse_args() -> argparse.Namespace:
    """Parse repository and work-directory arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Kalaxy3 repository root.",
    )
    parser.add_argument(
        "--work-dir",
        default=DEFAULT_WORK_DIR,
        help="Repository-relative MkDocs work directory.",
    )
    return parser.parse_args()


def remove_noise(source_dir: Path) -> None:
    """Remove machine-local and Daux-only files from staged source."""
    for path in source_dir.rglob(".DS_Store"):
        path.unlink()

    config_path = source_dir / "config.json"
    if config_path.exists():
        config_path.unlink()


def create_landing_page(source_dir: Path) -> None:
    """Rename the Daux landing page only in the staged source tree."""
    daux_index = source_dir / "_index.md"
    mkdocs_index = source_dir / "index.md"

    if not daux_index.is_file():
        raise FileNotFoundError(f"Missing landing page: {daux_index}")
    if mkdocs_index.exists():
        raise FileExistsError(f"Unexpected landing page: {mkdocs_index}")

    daux_index.rename(mkdocs_index)


def normalize_segment(segment: str) -> str:
    """Normalize one path segment for Daux-to-MkDocs compatibility."""
    normalized = segment.lower().replace("_", "-")
    if normalized.endswith(".md"):
        stem = normalized[:-3]
        stem = re.sub(r"^\d+[-]*", "", stem)
        return f"{stem}.md"
    return normalized


def normalize_path(path: Path) -> str:
    """Normalize case, separators, and Daux navigation-number prefixes."""
    return "/".join(
        normalize_segment(segment)
        for segment in path.parts
    )


def build_path_index(source_dir: Path) -> dict[str, list[Path]]:
    """Index staged Markdown paths by compatibility-normalized key."""
    index: dict[str, list[Path]] = {}

    for path in source_dir.rglob("*.md"):
        relative = path.relative_to(source_dir)
        index.setdefault(normalize_path(relative), []).append(path)

    return index


def split_target(target: str) -> tuple[str, str]:
    """Split a Markdown path from its query or fragment suffix."""
    positions = [
        position
        for marker in ("?", "#")
        if (position := target.find(marker)) >= 0
    ]

    if not positions:
        return target, ""

    position = min(positions)
    return target[:position], target[position:]


def find_candidate(
    source_dir: Path,
    document: Path,
    target_path: str,
    path_index: dict[str, list[Path]],
) -> Path | None:
    """Resolve a missing Daux-style link to one staged Markdown file."""
    candidates = (
        (document.parent / target_path).resolve(),
        (source_dir / target_path).resolve(),
    )

    for candidate in candidates:
        if candidate.is_file() and source_dir in candidate.parents:
            return candidate

    for candidate in candidates:
        try:
            relative = candidate.relative_to(source_dir)
        except ValueError:
            continue

        matches = path_index.get(normalize_path(relative), [])
        if len(matches) == 1:
            return matches[0]

    return None


def rewrite_document_links(
    source_dir: Path,
    document: Path,
    path_index: dict[str, list[Path]],
) -> tuple[int, list[str]]:
    """Rewrite resolvable compatibility links in one staged document."""
    original = document.read_text(encoding="utf-8")
    rewrite_count = 0
    unresolved: list[str] = []

    def replace(match: re.Match[str]) -> str:
        nonlocal rewrite_count

        target = match.group("target")
        target_path, suffix = split_target(target)
        candidate = find_candidate(
            source_dir,
            document,
            target_path,
            path_index,
        )

        if candidate is None:
            unresolved.append(
                f"{document.relative_to(source_dir)} -> {target}"
            )
            return match.group(0)

        direct = (document.parent / target_path).resolve()
        if direct == candidate.resolve():
            return match.group(0)

        relative = os.path.relpath(candidate, document.parent)
        rewrite_count += 1
        return (
            f"{match.group('prefix')}"
            f"{Path(relative).as_posix()}{suffix}"
            f"{match.group('suffix')}"
        )

    updated = LINK_PATTERN.sub(replace, original)
    if updated != original:
        document.write_text(updated, encoding="utf-8")

    return rewrite_count, unresolved


def rewrite_links(source_dir: Path) -> tuple[int, list[str]]:
    """Rewrite resolvable Daux-style Markdown links in staged copies."""
    path_index = build_path_index(source_dir)
    total_rewrites = 0
    unresolved: list[str] = []

    for document in sorted(source_dir.rglob("*.md")):
        rewrite_count, document_unresolved = rewrite_document_links(
            source_dir,
            document,
            path_index,
        )
        total_rewrites += rewrite_count
        unresolved.extend(document_unresolved)

    return total_rewrites, unresolved


def prepare_source(repo: Path, work_dir_name: str) -> tuple[int, int, int]:
    """Copy, normalize, and validate the staged MkDocs source tree."""
    source = repo / "markdown"
    work_dir = repo / work_dir_name
    staged_source = work_dir / "source"

    if not source.is_dir():
        raise FileNotFoundError(f"Missing source: {source}")

    if work_dir.exists():
        shutil.rmtree(work_dir)

    staged_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, staged_source)
    remove_noise(staged_source)
    create_landing_page(staged_source)

    rewrites, unresolved = rewrite_links(staged_source)
    if unresolved:
        detail = "\n".join(unresolved)
        raise RuntimeError(f"Unresolved Markdown links:\n{detail}")

    markdown_count = sum(1 for _ in staged_source.rglob("*.md"))
    total_files = sum(
        1 for path in staged_source.rglob("*") if path.is_file()
    )
    return markdown_count, total_files, rewrites


def main() -> int:
    """Prepare and report the staged MkDocs source tree."""
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    markdown_count, total_files, rewrites = prepare_source(
        repo,
        args.work_dir,
    )

    print("Kalaxy3 MkDocs source preparation: PASS")
    print(f"Markdown files: {markdown_count}")
    print(f"Total staged files: {total_files}")
    print(f"Compatibility link rewrites: {rewrites}")
    print(f"Staged source: {repo / args.work_dir / 'source'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
