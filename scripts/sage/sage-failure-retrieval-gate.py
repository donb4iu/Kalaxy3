#!/usr/bin/env python3
"""Retrieve repository experience after failure and before retry guidance."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from sage_evidence_retrieval import (
    RetrievalError,
    load_json,
    retrieve,
    validate_result,
)

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "sage-evidence-retrieval-policy.json"
STATE_ENV = "SAGE_FAILURE_RETRIEVAL_STATE_DIR"


def bounded(value: str, limit: int = 2000) -> str:
    """Return bounded diagnostic text."""
    compact = value.strip()
    return compact if len(compact) <= limit else compact[-limit:]


def build_request(
    failure: str,
    validator_id: str,
    error_summary: str,
) -> str:
    """Build the literal failure-recovery request."""
    return " ".join(
        (
            f"Unexpected failure while attempting: {failure}.",
            f"Validator or workflow: {validator_id}.",
            f"Observed error: {bounded(error_summary)}.",
            (
                "Before another corrective attempt, retrieve repository "
                "evidence, lessons, actionable failures, decisions, "
                "validation records, and canonical recovery explaining how "
                "to succeed. Prefer authoritative production structures and "
                "structured interfaces over inferred fixtures or formatted "
                "command output."
            ),
        )
    )


def state_directory() -> Path:
    """Return the local non-repository receipt directory."""
    configured = os.environ.get(STATE_ENV)
    if configured:
        return Path(configured).expanduser()
    return (
        Path.home()
        / ".local"
        / "state"
        / "kalaxy3"
        / "sage-failure-retrieval"
    )


def default_path(request: str) -> Path:
    """Return a timestamped stable receipt path."""
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(request.encode("utf-8")).hexdigest()[:12]
    return state_directory() / f"{timestamp}-{digest}.json"


def build_receipt(
    *,
    repo: Path,
    policy_path: Path,
    failure: str,
    validator_id: str,
    error_summary: str,
    limit: int,
) -> dict[str, Any]:
    """Run retrieval and return a local receipt."""
    request = build_request(
        failure,
        validator_id,
        error_summary,
    )
    result = retrieve(
        repo=repo,
        policy_path=policy_path,
        request=request,
        limit=limit,
    )
    validate_result(result, load_json(policy_path))
    return {
        "schema_version": "1.0",
        "receipt_type": "failure-triggered-retrieval",
        "captured_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "validator_id": validator_id,
        "failure": bounded(failure, 1000),
        "error_summary_sha256": hashlib.sha256(
            error_summary.encode("utf-8")
        ).hexdigest(),
        "retrieval_completed": True,
        "matches_found": bool(result["results"]),
        "retrieval_request": request,
        "retry_policy": (
            "Review this receipt and repository authority before another "
            "corrective mutation. A second failure in the same class "
            "requires a lesson or improvement action."
        ),
        "retrieval_result": result,
    }


def write_receipt(path: Path, payload: dict[str, Any]) -> None:
    """Write one receipt atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def render_summary(path: Path, receipt: dict[str, Any]) -> str:
    """Render a concise operator-facing summary."""
    results = receipt["retrieval_result"]["results"]
    lines = [
        "Failure-triggered SAGE retrieval: COMPLETE",
        f"Receipt: {path}",
        f"Matches: {len(results)}",
    ]
    for item in results[:5]:
        lines.append(
            f"  {item['rank']}. {item['identifier']} "
            f"[{item['source_type']}] {item['title']}"
        )
    if not results:
        lines.append(
            "  No match found. Classify the failure as new and inspect "
            "repository authority before retrying."
        )
    return "\n".join(lines)


def self_test() -> int:
    """Exercise the production dotted-key failure container shape."""
    with tempfile.TemporaryDirectory(
        prefix="sage-failure-retrieval-test-"
    ) as raw:
        repo = Path(raw)
        policy = load_json(POLICY_PATH)
        fixtures = {
            "sage-evidence-retrieval-policy.json": policy,
            "markdown/evidence/catalog.json": {
                "records": [
                    {
                        "evidence_id": "SAGE-K3-TEST-001",
                        "title": "Runtime parser recovery evidence",
                        "subjects": [
                            "runtime",
                            "validation",
                            "guardrail",
                        ],
                        "summary": (
                            "Inspect the authoritative production structure "
                            "before repairing a failed parser."
                        ),
                        "status": "validated",
                    }
                ]
            },
            "sage-lessons.json": {
                "lessons": [
                    {
                        "lesson_id": "SAGE-LESSON-TEST-001",
                        "title": "Retrieve experience before retry",
                        "match_terms": [
                            "failure",
                            "runtime",
                            "parser",
                            "retry",
                        ],
                        "status": "accepted",
                    }
                ]
            },
            "sage-actionable-failures.json": {
                "schema_version": "1.0",
                "failures": {
                    "centralized_logging.runtime_requires_active_gate": {
                        "attempted_action": "Validate logging runtime",
                        "why_invalid": (
                            "Runtime validation requires activation."
                        ),
                        "likely_intended_outcome": (
                            "Validate deployed logging health."
                        ),
                        "canonical_recovery": [],
                    }
                },
            },
            "sage-improvement-actions.json": {"actions": []},
            "sage-post-session-review-registry.json": {"reviews": []},
        }
        for relative, payload in fixtures.items():
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )

        receipt = build_receipt(
            repo=repo,
            policy_path=(
                repo / "sage-evidence-retrieval-policy.json"
            ),
            failure="Runtime parser failure before retry",
            validator_id="fixture.validator",
            error_summary="fixture failure",
            limit=10,
        )
        failure_source = next(
            item
            for item in receipt["retrieval_result"]["sources"]
            if item["source_type"] == "failure"
        )
        if failure_source["records_loaded"] != 1:
            raise RuntimeError(
                "Dotted-key failure container was not loaded"
            )
        identifiers = {
            item["identifier"]
            for item in receipt["retrieval_result"]["results"]
        }
        if (
            "centralized_logging.runtime_requires_active_gate"
            not in identifiers
        ):
            raise RuntimeError(
                "Dotted-key failure record was not retrieved"
            )

        destination = repo / "receipt.json"
        write_receipt(destination, receipt)
        if not json.loads(
            destination.read_text(encoding="utf-8")
        ).get("retrieval_completed"):
            raise RuntimeError("Receipt round-trip failed")

    print("SAGE failure-triggered retrieval self-test: PASS")
    return 0


def parser() -> argparse.ArgumentParser:
    """Build the command interface."""
    cli = argparse.ArgumentParser()
    cli.add_argument("--failure")
    cli.add_argument("--validator-id", default="manual")
    cli.add_argument("--error-summary", default="")
    cli.add_argument("--limit", type=int, default=10)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--self-test", action="store_true")
    return cli


def main() -> int:
    """Run failure-triggered retrieval."""
    arguments = parser().parse_args()
    if arguments.self_test:
        return self_test()
    if not arguments.failure:
        raise RetrievalError("--failure is required")

    request = build_request(
        arguments.failure,
        arguments.validator_id,
        arguments.error_summary,
    )
    destination = arguments.output or default_path(request)
    receipt = build_receipt(
        repo=ROOT,
        policy_path=POLICY_PATH,
        failure=arguments.failure,
        validator_id=arguments.validator_id,
        error_summary=arguments.error_summary,
        limit=arguments.limit,
    )
    write_receipt(destination, receipt)
    print(render_summary(destination, receipt))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        json.JSONDecodeError,
        OSError,
        RetrievalError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"Failure-triggered SAGE retrieval: FAIL CLOSED: {error}",
            file=sys.stderr,
        )
        raise SystemExit(2)
