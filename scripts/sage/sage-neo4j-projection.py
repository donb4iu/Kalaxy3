#!/usr/bin/env python3
"""Build/read a local Neo4j candidate from the governed SAGE Git revision."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sage_neo4j_inventory import prepare
from sage_neo4j_lifecycle import ensure_lossless, projection_id, receipt_path
from sage_neo4j_projection import build_projection, concept_evidence


def arguments() -> argparse.Namespace:
    """Parse explicit non-promoting CLI operations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--uri', default='bolt://127.0.0.1:7687')
    parser.add_argument('--user', default='neo4j')
    parser.add_argument('--concept', default='storage')
    parser.add_argument('--require-integration', action='store_true')
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict[str, Any]:
    """Construct and check candidate graph while withholding promotion authority.

    Args:
        args: Parsed operator arguments.
    """
    root = args.repo.resolve()
    config = args.config or root / 'sage-semantic-concepts.json'
    payload = prepare(root, config)
    expected = {row['path'] for row in payload['sources']}
    ensure_lossless(payload['sources'], expected)
    receipt: dict[str, Any] = {
        'source_revision': payload['revision'],
        'source_count': len(payload['sources']),
        'concept_count': len(payload['concepts']),
        'candidate_links': len(payload['candidate_edges']),
        'projection_id': projection_id(payload),
        'canonical_mutation': False, 'promotion': False,
        'qualification': 'candidate_only', 'all_mandatory_dod_passed': False,
    }
    if args.require_integration:
        if not args.uri.startswith(('bolt://127.0.0.1:', 'bolt://localhost:')):
            raise PermissionError('local-only Neo4j required for this implementation test')
        password = os.environ.get('SAGE_NEO4J_PASSWORD')
        if not password:
            raise PermissionError('SAGE_NEO4J_PASSWORD not set')
        from neo4j import GraphDatabase  # type: ignore[import-not-found]
        with GraphDatabase.driver(args.uri, auth=(args.user, password)) as driver:
            driver.verify_connectivity()
            with driver.session() as session:
                receipt['neo4j'] = build_projection(session, payload)
                receipt['sample_readback'] = concept_evidence(
                    session, receipt['projection_id'], args.concept)
    else:
        receipt['neo4j'] = 'not_run_requires_local_integration'
    receipt['receipt'] = str(receipt_path(args.out, receipt))
    return receipt


def main() -> int:
    """Emit fail-closed operational status and an evidence receipt."""
    args = arguments()
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 10 if not args.require_integration else 0


if __name__ == '__main__':
    raise SystemExit(main())
