#!/usr/bin/env python3
"""Read-only SAGE #50 semantic candidate benchmark and readiness CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sage_neo4j_benchmark import assess


def main() -> int:
    """Measure only externally labeled pairs or record not-evaluated readiness."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--labels', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    labels = json.loads(args.labels.read_text('utf-8')) if args.labels else None
    receipt = assess(args.repo, labels)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n',
                        encoding='utf-8')
    args.out.chmod(0o600)
    print('SEMANTIC_BENCHMARK=' + receipt['status'])
    print('SOURCE_COUNT=' + str(receipt['source_count']))
    print('SEMANTIC_ACCEPTANCE=NOT_ASSERTED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
