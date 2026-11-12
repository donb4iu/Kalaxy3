#!/usr/bin/env python3
"""Read-only local Neo4j objective retrieval benchmark using external labels."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sage_neo4j_objective_measure import (evaluate_cases, gather_objective,
                                          projection_inventory)


def arguments() -> argparse.Namespace:
    """Require explicit local graph, external labels and private output receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--projection-id', required=True)
    parser.add_argument('--labels', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--uri', default='bolt://127.0.0.1:7687')
    parser.add_argument('--user', default='neo4j')
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Score labels from a loopback-only candidate graph, never modifying it.

    Args:
        args: Explicit CLI arguments.
    """
    if not args.uri.startswith(('bolt://127.0.0.1:', 'bolt://localhost:')):
        raise PermissionError('LOCAL_NEO4J_ONLY')
    if args.labels.stat().st_size > 1_048_576:
        raise ValueError('OBJECTIVE_LABEL_DOCUMENT_TOO_LARGE')
    password = os.environ.get('SAGE_NEO4J_PASSWORD')
    if not password:
        raise PermissionError('SAGE_NEO4J_PASSWORD_REQUIRED')
    labels = json.loads(args.labels.read_text(encoding='utf-8'))
    from neo4j import GraphDatabase, READ_ACCESS  # type: ignore[import-not-found]
    with GraphDatabase.driver(args.uri, auth=(args.user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(default_access_mode=READ_ACCESS) as session:
            inventory = projection_inventory(session, args.projection_id)
            result = evaluate_cases(labels, inventory, lambda objective:
                                    gather_objective(session, args.projection_id,
                                                     objective))
    return result


def main() -> int:
    """Write an operator-local measurement receipt without declaring success."""
    args = arguments()
    receipt = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    output = args.out
    with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600),
                   'w', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print('OBJECTIVE_RETRIEVAL_BENCHMARK=MEASUREMENT_ONLY')
    print('LABELED_OBJECTIVE_CASES=' + str(len(receipt['cases'])))
    print('OBJECTIVE_ACCEPTANCE=NOT_ASSERTED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
