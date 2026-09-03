#!/usr/bin/env python3
"""Build or validate Human Participation semantic synthesis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from human_participation_semantic_synthesis import (
    build_corpus,
    build_synthesis,
    load_object,
    validate_proposal,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    corpus = sub.add_parser("corpus")
    corpus.add_argument("--repo", type=Path, default=Path.cwd())
    corpus.add_argument("--inventory", required=True, type=Path)
    corpus.add_argument("--intent", required=True, type=Path)
    corpus.add_argument("--output", required=True, type=Path)

    validate = sub.add_parser("validate")
    validate.add_argument("--corpus", required=True, type=Path)
    validate.add_argument("--intent", required=True, type=Path)
    validate.add_argument("--proposal", required=True, type=Path)

    project = sub.add_parser("project")
    project.add_argument("--corpus", required=True, type=Path)
    project.add_argument("--intent", required=True, type=Path)
    project.add_argument("--proposal", required=True, type=Path)
    project.add_argument("--output", required=True, type=Path)

    return parser.parse_args()


def write_json(path: Path, value: dict) -> None:
    """Write deterministic JSON."""
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    """Execute selected semantic-synthesis operation."""
    args = parse_args()

    if args.command == "corpus":
        value = build_corpus(
            args.repo.resolve(),
            args.inventory,
            args.intent,
        )
        write_json(args.output, value)
        print("SAGE semantic experience corpus: GENERATED")
        return 0

    corpus = load_object(args.corpus)
    intent = load_object(args.intent)
    proposal = load_object(args.proposal)

    if args.command == "validate":
        errors = validate_proposal(proposal, corpus, intent)
        if errors:
            print("\n".join(f"FAIL: {item}" for item in errors))
            return 2
        print("SAGE semantic synthesis proposal: VALID")
        return 0

    value = build_synthesis(proposal, corpus, intent)
    write_json(args.output, value)
    print("SAGE semantic experience synthesis: GENERATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
