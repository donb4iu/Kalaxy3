#!/usr/bin/env python3
"""Generate generic Human Participation experience graph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_participation_experience_graph import build_graph


def main() -> int:
    """Generate graph JSON and browser payload."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--browser-output", required=True, type=Path)
    args = parser.parse_args()

    graph = build_graph(args.repo.resolve())
    serialized = json.dumps(
        graph,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    args.output.write_text(serialized + "\n", encoding="utf-8")
    args.browser_output.write_text(
        "window.KALAXY3_EXPERIENCE_GRAPH = "
        + serialized
        + ";\n",
        encoding="utf-8",
    )
    print("SAGE Human Participation generic experience graph: GENERATED")
    print(f"Entities: {len(graph['entities'])}")
    print(f"Relationships: {len(graph['relationships'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
