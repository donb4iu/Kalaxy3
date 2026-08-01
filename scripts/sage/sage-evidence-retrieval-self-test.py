#!/usr/bin/env python3
"""Source-only tests for deterministic SAGE evidence retrieval."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from sage_evidence_retrieval import (
    RetrievalError,
    load_json,
    retrieve,
    validate_result,
)


def write_json(path: Path, payload: object) -> None:
    """Write one fixture JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def fixture_policy() -> dict[str, object]:
    """Load the production policy for fixture semantics."""
    return load_json(
        Path(__file__).resolve().parents[2]
        / "sage-evidence-retrieval-policy.json"
    )


def build_fixture(repo: Path) -> Path:
    """Build deterministic positive and negative fixtures."""
    write_json(
        repo / "sage-evidence-retrieval-policy.json",
        fixture_policy(),
    )
    write_json(
        repo / "markdown/evidence/catalog.json",
        {
            "records": [
                {
                    "evidence_id": "OBS-001",
                    "title": "Grafana Loki datasource runtime validation",
                    "subjects": ["grafana", "logging", "validation"],
                    "status": "validated",
                    "summary": (
                        "ConfigMap existence is insufficient; verify the "
                        "Grafana API loaded the datasource."
                    ),
                    "record_path": "markdown/operations/logging.md",
                },
                {
                    "evidence_id": "DOC-001",
                    "title": "Documentation navigation",
                    "subjects": ["mkdocs"],
                    "status": "validated",
                },
            ]
        },
    )
    write_json(
        repo / "sage-lessons.json",
        {
            "lessons": [
                {
                    "lesson_id": "LESSON-001",
                    "title": "Use live runtime validation",
                    "tags": ["runtime", "validation"],
                    "status": "accepted",
                }
            ]
        },
    )
    write_json(
        repo / "sage-actionable-failures.json",
        {
            "failures": [
                {
                    "failure_id": "FAIL-001",
                    "title": "Operator runtime dependency missing",
                    "tags": ["grafana", "runtime", "guardrail"],
                    "status": "closed",
                }
            ]
        },
    )
    write_json(repo / "sage-improvement-actions.json", {"actions": []})
    write_json(
        repo / "sage-post-session-review-registry.json",
        {"reviews": []},
    )
    return repo / "sage-evidence-retrieval-policy.json"


def positive_test(repo: Path, policy_path: Path) -> None:
    """Require relevant evidence and failures to rank first."""
    request = (
        "Add a Grafana dashboard for Prometheus metrics and logging health"
    )
    first = retrieve(
        repo=repo,
        policy_path=policy_path,
        request=request,
        limit=10,
    )
    second = retrieve(
        repo=repo,
        policy_path=policy_path,
        request=request,
        limit=10,
    )
    if first != second:
        raise AssertionError("retrieval output is not deterministic")

    identifiers = [
        result["identifier"]
        for result in first["results"]
    ]
    if identifiers[:2] != ["OBS-001", "FAIL-001"]:
        raise AssertionError(
            f"unexpected positive ranking: {identifiers}"
        )
    validate_result(first, load_json(policy_path))


def disposition_test(repo: Path, policy_path: Path) -> None:
    """Require rationale for finalized dispositions."""
    payload = retrieve(
        repo=repo,
        policy_path=policy_path,
        request="Grafana runtime validation",
        limit=2,
    )
    payload["results"][0]["disposition"] = "applied"
    try:
        validate_result(
            payload,
            load_json(policy_path),
            require_final=True,
        )
    except RetrievalError:
        pass
    else:
        raise AssertionError("missing rationale was accepted")

    for result in payload["results"]:
        result["disposition"] = "applied"
        result["disposition_rationale"] = "Used by implementation plan."
    validate_result(
        payload,
        load_json(policy_path),
        require_final=True,
    )


def negative_test(repo: Path, policy_path: Path) -> None:
    """Require an unrelated request to favor documentation."""
    payload = retrieve(
        repo=repo,
        policy_path=policy_path,
        request="Update MkDocs documentation navigation",
        limit=3,
    )
    identifiers = [
        result["identifier"]
        for result in payload["results"]
    ]
    if identifiers and identifiers[0] != "DOC-001":
        raise AssertionError(
            f"negative request ranking was unexpected: {identifiers}"
        )


def main() -> int:
    """Run all tests without site packages or network access."""
    with tempfile.TemporaryDirectory(
        prefix="sage-evidence-retrieval-test-"
    ) as directory:
        repo = Path(directory)
        policy_path = build_fixture(repo)
        positive_test(repo, policy_path)
        disposition_test(repo, policy_path)
        negative_test(repo, policy_path)

    print("SAGE evidence retrieval self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
