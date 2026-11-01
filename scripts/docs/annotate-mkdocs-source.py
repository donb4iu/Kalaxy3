#!/usr/bin/env python3
"""Annotate staged source and generated projections with Git provenance."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from page_freshness import annotate_staged_pages


def main(argv: Sequence[str] | None = None) -> int:
    """Apply Git provenance labels to all staged pages.

    Args:
        argv: Optional command-line arguments for testing.

    Returns:
        Zero on successful annotation.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--work-dir", default=".mkdocs-work")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    source = repo / args.work_dir / "source"
    annotate_staged_pages(repo, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
