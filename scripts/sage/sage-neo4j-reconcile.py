#!/usr/bin/env python3
"""Read-only source lifecycle delta receipt for two governed Git revisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage_neo4j_reconcile import reconcile, revision_inventory


def main() -> int:
    """Emit an exact, non-authoritative reconciliation record to an output path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--before', required=True)
    parser.add_argument('--after', default='HEAD')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    before = revision_inventory(args.repo, args.before)
    after = revision_inventory(args.repo, args.after)
    receipt = reconcile(before, after)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + '\n', 'utf-8')
    args.out.chmod(0o600)
    print('RECONCILIATION=READ_ONLY')
    print('ADDED=' + str(len(receipt['source_changes']['added'])))
    print('MODIFIED=' + str(len(receipt['source_changes']['modified'])))
    print('REMOVED=' + str(len(receipt['source_changes']['removed'])))
    print('CANDIDATE_COMPARISON=' + receipt['candidate_comparison_state'])
    print('PROJECTION_PROMOTION=NONE')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
