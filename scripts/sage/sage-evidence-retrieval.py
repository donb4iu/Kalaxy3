#!/usr/bin/env python3
"""CLI for deterministic Kalaxy3 SAGE evidence retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sage_evidence_retrieval import (
    RetrievalError,
    load_json,
    retrieve,
    validate_result,
    write_result,
)


def parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    cli = argparse.ArgumentParser(
        description="Retrieve repository-owned SAGE engineering experience"
    )
    cli.add_argument("--repo", type=Path, default=Path.cwd())
    cli.add_argument(
        "--policy",
        type=Path,
        default=Path("sage-evidence-retrieval-policy.json"),
    )
    commands = cli.add_subparsers(dest="command", required=True)

    retrieve_command = commands.add_parser("retrieve")
    retrieve_command.add_argument("--request", required=True)
    retrieve_command.add_argument("--limit", type=int)
    retrieve_command.add_argument("--output", type=Path)

    validate_command = commands.add_parser("validate")
    validate_command.add_argument("--input", type=Path, required=True)
    validate_command.add_argument("--require-final", action="store_true")
    return cli


def main() -> int:
    """Run retrieval or result validation."""
    arguments = parser().parse_args()
    repo = arguments.repo.resolve()
    policy_path = arguments.policy
    if not policy_path.is_absolute():
        policy_path = repo / policy_path

    if arguments.command == "retrieve":
        result = retrieve(
            repo=repo,
            policy_path=policy_path,
            request=arguments.request,
            limit=arguments.limit,
        )
        validate_result(result, load_json(policy_path))
        if arguments.output:
            write_result(arguments.output, result)
        else:
            print(json.dumps(result, indent=2))
        return 0

    payload = load_json(arguments.input)
    validate_result(
        payload,
        load_json(policy_path),
        require_final=arguments.require_final,
    )
    print("SAGE evidence retrieval result: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RetrievalError, json.JSONDecodeError) as error:
        print(f"SAGE evidence retrieval: FAIL: {error}", file=sys.stderr)
        raise SystemExit(2)
