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

def quality_fields_test(
    repo: Path,
    policy_path: Path,
) -> None:
    """Require exact facts and explicit metadata provenance."""
    catalog_path = repo / "markdown/evidence/catalog.json"
    catalog = load_json(catalog_path)
    record = next(
        item
        for item in catalog["records"]
        if item["evidence_id"] == "OBS-001"
    )
    record.update(
        {
            "confidence": "high",
            "valid_as_of": "2026-07-31",
            "completed_at": "2026-07-31T20:00:00-05:00",
            "nav_section": "operations",
            "source_path": "markdown/operations/fixture.md",
        }
    )
    write_json(catalog_path, catalog)

    evidence_payload = retrieve(
        repo=repo,
        policy_path=policy_path,
        request="Grafana logging runtime validation",
        limit=10,
    )
    evidence_identifiers = [
        item["identifier"]
        for item in evidence_payload["results"]
    ]
    if "OBS-001" not in evidence_identifiers:
        raise AssertionError(
            "Evidence fixture was excluded unexpectedly: "
            f"{evidence_identifiers}"
        )
    result = next(
        item
        for item in evidence_payload["results"]
        if item["identifier"] == "OBS-001"
    )
    if result["confidence"] != {
        "value": "high",
        "source_field": "confidence",
        "basis": "explicit-source-field",
    }:
        raise AssertionError(
            f"explicit confidence was not preserved: "
            f"{result['confidence']}"
        )
    if result["recency"] != {
        "value": "2026-07-31",
        "source_field": "valid_as_of",
        "basis": "explicit-source-field",
    }:
        raise AssertionError(
            f"explicit recency was not preserved: "
            f"{result['recency']}"
        )
    if (
        result["source_section"]["navigation_section"]
        != "operations"
    ):
        raise AssertionError(
            "navigation source section was not preserved"
        )
    if not result["applicable_facts"]:
        raise AssertionError("exact applicable facts are missing")
    for fact in result["applicable_facts"]:
        if fact["value"] not in retrieval_module.scalar_text(
            record
        ):
            raise AssertionError(
                f"fact is not an exact source value: {fact}"
            )
        if not fact["matched_terms"]:
            raise AssertionError(
                f"fact has no request overlap: {fact}"
            )
    validate_result(
        evidence_payload,
        load_json(policy_path),
    )

    lesson_payload = retrieve(
        repo=repo,
        policy_path=policy_path,
        request="Use live runtime validation lesson",
        limit=10,
    )
    lesson_identifiers = [
        item["identifier"]
        for item in lesson_payload["results"]
    ]
    if "LESSON-001" not in lesson_identifiers:
        raise AssertionError(
            "Lesson fixture did not satisfy its domain-valid request: "
            f"{lesson_identifiers}"
        )
    lesson = next(
        item
        for item in lesson_payload["results"]
        if item["identifier"] == "LESSON-001"
    )
    if lesson["confidence"]["basis"] != "not-recorded":
        raise AssertionError(
            "missing lesson confidence was inferred"
        )
    if lesson["recency"]["basis"] != "not-recorded":
        raise AssertionError(
            "missing lesson recency was inferred"
        )
    validate_result(
        lesson_payload,
        load_json(policy_path),
    )


def recency_tie_break_test() -> None:
    """Require explicit recency only after equal relevance."""
    with tempfile.TemporaryDirectory(
        prefix="sage-retrieval-recency-test-"
    ) as directory:
        repo = Path(directory)
        policy = fixture_policy()
        policy["sources"] = [
            {
                "path": "markdown/evidence/catalog.json",
                "source_type": "evidence",
            }
        ]
        write_json(
            repo / "sage-evidence-retrieval-policy.json",
            policy,
        )
        common = {
            "title": "Grafana runtime validation",
            "summary": "Grafana runtime validation evidence.",
            "status": "validated",
            "confidence": "high",
            "nav_section": "operations",
        }
        write_json(
            repo / "markdown/evidence/catalog.json",
            {
                "records": [
                    {
                        **common,
                        "evidence_id": "OLDER",
                        "valid_as_of": "2026-07-01",
                    },
                    {
                        **common,
                        "evidence_id": "NEWER",
                        "valid_as_of": "2026-08-01",
                    },
                ]
            },
        )
        payload = retrieve(
            repo=repo,
            policy_path=(
                repo / "sage-evidence-retrieval-policy.json"
            ),
            request="Grafana runtime validation",
            limit=2,
        )
        identifiers = [
            item["identifier"]
            for item in payload["results"]
        ]
        if identifiers != ["NEWER", "OLDER"]:
            raise AssertionError(
                f"explicit recency tie-break failed: {identifiers}"
            )


def production_schema_quality_test() -> None:
    """Require the repository schema to enforce quality fields."""
    root = Path(__file__).resolve().parents[2]
    schema = load_json(
        root
        / "markdown/standards/"
        / "sage-evidence-retrieval-result-schema-v1.0.json"
    )
    item_schema = (
        schema["properties"]["results"]["items"]
    )
    required = set(item_schema["required"])
    expected = {
        "confidence",
        "applicable_facts",
        "source_section",
        "recency",
    }
    if not expected.issubset(required):
        raise AssertionError(
            f"schema quality fields missing: {required}"
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
        quality_fields_test(repo, policy_path)

    recency_tie_break_test()
    production_failure_registry_test()
    production_schema_quality_test()
    print("SAGE evidence retrieval self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
