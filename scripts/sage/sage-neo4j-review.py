#!/usr/bin/env python3
"""Emit blinded SAGE evidence review packets or score separately completed labels."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sage_neo4j_benchmark import build_snapshot
from sage_neo4j_review import build_review, label_template, score_review


def write_receipt(path: Path, record: dict[str, Any]) -> None:
    """Write a local-only, permission-restricted JSON document.

    Args:
        path: Owned local file outside the Git checkout.
        record: JSON-compatible read-only output.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ValueError('REFUSE_OVERWRITE_REVIEW_EVIDENCE')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2, sort_keys=True)
        handle.write('\n')


def main() -> int:
    """Bind every review and assessment to the current committed Git head."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--size', type=int, default=48)
    parser.add_argument('--seed', type=int, default=50)
    parser.add_argument('--review-packet', type=Path)
    parser.add_argument('--labels', type=Path)
    args = parser.parse_args()
    snapshot = build_snapshot(args.repo)
    if bool(args.review_packet) != bool(args.labels):
        parser.error('--review-packet and --labels must be supplied together')
    if args.labels:
        review = json.loads(args.review_packet.read_text('utf-8'))
        labels = json.loads(args.labels.read_text('utf-8'))
        receipt = score_review(snapshot, review, labels)
        write_receipt(args.out_dir / 'semantic-review-score.json', receipt)
    else:
        review = build_review(snapshot, args.size, args.seed)
        write_receipt(args.out_dir / 'review-packet.json', review)
        receipt = {'status': review['status'], 'revision': snapshot['revision'],
                   'source_count': len(snapshot['sources']),
                   'projection_fingerprint': snapshot['fingerprint'],
                   'label_independence': 'not_evaluated',
                   'architect_acceptance': 'not_evaluated'}
        if review['status'] == 'ready_for_independent_annotation':
            write_receipt(args.out_dir / 'labels-template.json',
                          label_template(review))
        write_receipt(args.out_dir / 'review-readiness.json', receipt)
    print('SEMANTIC_REVIEW=' + receipt['status'])
    print('ARCHITECT_ACCEPTANCE=NOT_ASSERTED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
