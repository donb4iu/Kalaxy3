#!/usr/bin/env python3
"""Build Git-main and feature evidence-derived Neo4j review-ready candidates."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from sage_neo4j_evidence_bootstrap import bootstrap
from sage_neo4j_review import build_review, label_template


def write_private(path: Path, value: dict[str, Any]) -> None:
    """Save evidence metadata to a new protected file, never overwrite.

    Args:
        path: New file beneath a caller-controlled output directory.
        value: Revision-pinned JSON data with no raw source bodies.
    """
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    handle = os.open(path, flags, 0o600)
    with os.fdopen(handle, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """Summarize distinct main and WIP evidence without approval assertions.

    Args:
        payload: Independently inventoried Git-main and feature projections.
    """
    main, feature = payload['main'], payload['feature']
    return {'record_type': 'sage-evidence-derived-semantic-bootstrap',
            'main_revision': main['revision'],
            'feature_revision': feature['revision'],
            'merge_base_revision': payload['three_way']['merge_base_revision'],
            'main_source_count': len(main['sources']),
            'feature_source_count': len(feature['sources']),
            'main_candidate_concepts': len(main['concepts']),
            'feature_candidate_concepts': len(feature['concepts']),
            'feature_candidate_links': len(feature['candidate_edges']),
            'main_explicit_document_links': len(main['explicit_source_links']),
            'feature_explicit_document_links': len(feature['explicit_source_links']),
            'three_way': payload['three_way'],
            'main_projection_fingerprint': main['fingerprint'],
            'feature_projection_fingerprint': feature['fingerprint'],
            'relationship_authority': 'candidate_only',
            'runtime_state': 'not_evaluated',
            'semantic_recall': 'not_evaluated',
            'model_coverage_qualified': False,
            'architect_acceptance': 'not_evaluated',
            'neo4j_activation': 'not_authorized'}


def generate(repo: Path, main_ref: str, feature_ref: str,
             output: Path, size: int = 48) -> dict[str, Any]:
    """Materialize a new evidence-first review and Neo4j projection candidate.

    Args:
        repo: Local Git checkout, read only.
        main_ref: Explicit fetched production ref.
        feature_ref: Explicit feature ref or HEAD.
        output: New destination for private artifacts.
        size: Maximum blinded source-concept review cases.
    """
    if output.exists() or output.is_symlink():
        raise ValueError('OUTPUT_EXISTS_REFUSE_OVERWRITE')
    payload = bootstrap(repo, main_ref, feature_ref)
    output.mkdir(parents=True, mode=0o700)
    result = summarize(payload)
    write_private(output / 'bootstrap-receipt.json', result)
    for label in ('main', 'feature'):
        write_private(output / f'{label}-projection-candidate.json', payload[label])
    review = build_review(payload['feature'], size)
    write_private(output / 'review-packet.json', review)
    if review['status'] == 'ready_for_independent_annotation':
        write_private(output / 'labels-template.json', label_template(review))
    result['review_status'] = review['status']
    return result


def main() -> int:
    """Read explicit source refs and emit candidate artifacts without Git writes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--main-ref', required=True)
    parser.add_argument('--feature-ref', default='HEAD')
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--review-size', type=int, default=48)
    args = parser.parse_args()
    result = generate(args.repo, args.main_ref, args.feature_ref,
                      args.out_dir, args.review_size)
    print('MAIN_REVISION=' + result['main_revision'])
    print('FEATURE_REVISION=' + result['feature_revision'])
    print('REVIEW_READINESS=' + result['review_status'])
    print('SEMANTIC_AUTHORITY=CANDIDATE_ONLY')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
