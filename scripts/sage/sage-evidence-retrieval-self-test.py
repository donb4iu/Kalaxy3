#!/usr/bin/env python3
"""Source-only tests for deterministic SAGE evidence retrieval."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import sage_evidence_retrieval as retrieval_module

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
            "failures": {
                "FAIL-001": {
                    "title": "Grafana operator runtime dependency missing",
                    "tags": ["grafana", "runtime", "guardrail"],
                    "status": "closed",
                }
            }
        },
    )
    write_json(repo / "sage-improvement-actions.json", {"actions": []})
    write_json(
        repo / "sage-post-session-review-registry.json",
        {"reviews": []},
    )
    return repo / "sage-evidence-retrieval-policy.json"


def positive_test(repo: Path, policy_path: Path) -> None:
    """Require relevant evidence and keyed failures to rank first."""
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

    failure_source = next(
        source
        for source in first["sources"]
        if source["source_type"] == "failure"
    )
    if failure_source["records_loaded"] != 1:
        raise AssertionError("keyed failure registry was not loaded")

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


def no_overlap_test(repo: Path, policy_path: Path) -> None:
    """Require bonuses alone to be unable to create relevance."""
    payload = retrieve(
        repo=repo,
        policy_path=policy_path,
        request="Rotate internal TLS certificates",
        limit=10,
    )
    if payload["results"]:
        raise AssertionError(
            "source or status bonuses admitted unrelated records"
        )


def production_failure_registry_test() -> None:
    """Exercise the actual dotted-key actionable-failure registry."""
    root = Path(__file__).resolve().parents[2]
    payload = retrieval_module.load_json(
        root / "sage-actionable-failures.json"
    )
    failures = payload.get("failures")
    if not isinstance(failures, dict):
        raise AssertionError(
            "production actionable failures must be a mapping"
        )

    records = retrieval_module.extract_records(
        payload,
        "failure",
    )
    identifiers = {
        retrieval_module.identifier(
            record,
            "failure",
            index,
        )
        for index, record in enumerate(records, start=1)
    }
    required = {
        "centralized_logging.render_validator_after_activation",
        "centralized_logging.runtime_requires_active_gate",
        "centralized_logging.unmanaged_controller_interpreter",
    }
    if not required.issubset(identifiers):
        raise AssertionError(
            f"production failure identifiers missing: {identifiers}"
        )
    if len(records) != len(failures):
        raise AssertionError(
            "production failure count does not match mapping"
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
        no_overlap_test(repo, policy_path)

    production_failure_registry_test()
    print("SAGE evidence retrieval self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
