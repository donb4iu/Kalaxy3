#!/usr/bin/env python3
"""Extract deterministic SAGE repository and process baselines."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]

REGISTRIES: Final = {
    "change_candidates": (
        ROOT / "sage-change-candidate-registry.json",
        "candidates",
    ),
    "lessons": (
        ROOT / "sage-lessons.json",
        "lessons",
    ),
    "improvement_actions": (
        ROOT / "sage-improvement-actions.json",
        "actions",
    ),
    "sessions": (
        ROOT / "sage-session-improvement-registry.json",
        "sessions",
    ),
    "feedback_baselines": (
        ROOT / "sage-feedback-baseline-registry.json",
        "baselines",
    ),
    "candidate_lifecycles": (
        ROOT / "sage-change-candidate-lifecycle-registry.json",
        "lifecycles",
    ),
}

RAW_METRICS: Final = [
    "commands_executed",
    "commands_failed",
    "commands_retried",
    "manual_corrections",
    "phases_total",
    "phases_first_pass",
    "known_failures_encountered",
    "known_failures_recurred",
    "mutation_opportunities",
    "failures_detected_pre_mutation",
    "applicable_lessons",
    "applicable_lessons_used",
    "avoidable_rework_minutes",
    "prompt_to_validated_change_minutes",
]

DERIVED_METRICS: Final = [
    "first_pass_phase_success_rate",
    "known_failure_recurrence_rate",
    "pre_mutation_detection_rate",
    "applicable_lesson_usage_rate",
]


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def repository_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json_at_commit(
    path: Path,
    commit: str,
) -> Any | None:
    try:
        payload = git_output(
            "show",
            f"{commit}:{repository_relative(path)}",
        )
    except subprocess.CalledProcessError:
        return None
    return json.loads(payload)


def registry_count(
    path: Path,
    collection: str,
    commit: str,
) -> int:
    payload = load_json_at_commit(path, commit)
    if payload is None:
        return 0
    values = payload.get(collection)
    if not isinstance(values, list):
        raise ValueError(
            f"{path.name}:{collection} must be a list"
        )
    return len(values)


def git_metrics(
    baseline_commit: str,
    current_commit: str,
) -> dict[str, int]:
    ancestor = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            baseline_commit,
            current_commit,
        ],
        cwd=ROOT,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError(
            "baseline_commit must be an ancestor "
            "of current_commit"
        )

    commit_count = int(
        git_output(
            "rev-list",
            "--count",
            f"{baseline_commit}..{current_commit}",
        )
    )
    numstat = git_output(
        "diff",
        "--numstat",
        f"{baseline_commit}...{current_commit}",
    )

    files_changed = 0
    insertions = 0
    deletions = 0
    binary_files = 0

    for line in numstat.splitlines():
        if not line:
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            raise ValueError(
                f"unexpected git numstat line: {line}"
            )
        added, removed, _ = parts
        files_changed += 1
        if added == "-" or removed == "-":
            binary_files += 1
            continue
        insertions += int(added)
        deletions += int(removed)

    return {
        "commits_in_range": commit_count,
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
        "binary_files": binary_files,
    }


def registry_metrics(
    current_commit: str,
) -> dict[str, int]:
    return {
        key: registry_count(
            path,
            collection,
            current_commit,
        )
        for key, (path, collection) in REGISTRIES.items()
    }


def session_process_metrics(
    session_count: int,
) -> dict[str, Any]:
    if session_count == 0:
        return {
            "status": "unavailable-no-session-records",
            "raw": {
                key: None
                for key in RAW_METRICS
            },
            "derived": {
                key: None
                for key in DERIVED_METRICS
            },
        }
    raise ValueError(
        "baseline extraction for populated session registries "
        "requires explicit aggregation implementation"
    )


def prediction_reference(
    change_id: str,
    current_commit: str,
) -> dict[str, Any]:
    payload = load_json_at_commit(
        REGISTRIES["change_candidates"][0],
        current_commit,
    )
    if payload is None:
        return {
            "status": "unavailable",
            "reason": (
                "The change-candidate registry did not exist at "
                f"commit {current_commit}."
            ),
        }
    candidates = payload["candidates"]
    matches = [
        item
        for item in candidates
        if isinstance(item, dict)
        and item.get("change_id") == change_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"candidate {change_id} must appear exactly once"
        )

    discovery = [
        item
        for item in matches[0].get("predictions", [])
        if isinstance(item, dict)
        and item.get("stage") == "discovery"
    ]
    if not discovery:
        raise ValueError(
            "candidate discovery prediction is missing"
        )
    selected = sorted(
        discovery,
        key=lambda item: int(item.get("version", 0)),
    )[-1]
    return {
        "stage": selected["stage"],
        "version": selected["version"],
        "confidence": selected["confidence"],
        "estimate": selected["estimate"],
        "range": selected["range"],
    }


def extract_baseline(
    *,
    baseline_id: str,
    change_id: str,
    captured_at: str,
    branch: str,
    baseline_commit: str,
    current_commit: str,
) -> dict[str, Any]:
    datetime.fromisoformat(
        captured_at.replace("Z", "+00:00")
    )

    metrics = registry_metrics(current_commit)
    process = session_process_metrics(
        metrics["sessions"]
    )

    return {
        "baseline_id": baseline_id,
        "change_id": change_id,
        "captured_at": captured_at,
        "branch": branch,
        "baseline_commit": baseline_commit,
        "current_commit": current_commit,
        "git_metrics": git_metrics(
            baseline_commit,
            current_commit,
        ),
        "registry_metrics": metrics,
        "process_metrics": process,
        "prediction_reference": prediction_reference(
            change_id,
            current_commit,
        ),
        "measurement_quality": {
            "git": "measured",
            "registries": "measured",
            "process": (
                "unavailable"
                if process["status"]
                == "unavailable-no-session-records"
                else "measured"
            ),
            "overall_confidence": "medium",
        },
        "provenance": [
            {
                "source_type": "git",
                "reference": (
                    f"git:{baseline_commit}...{current_commit}"
                ),
                "measurement_type": "measured",
                "captured_at": captured_at,
            },
            {
                "source_type": "registry",
                "reference": (
                    "sage-change-candidate-registry.json"
                ),
                "measurement_type": "measured",
                "captured_at": captured_at,
            },
            {
                "source_type": "registry",
                "reference": (
                    "sage-session-improvement-registry.json"
                ),
                "measurement_type": (
                    "unavailable"
                    if metrics["sessions"] == 0
                    else "measured"
                ),
                "captured_at": captured_at,
            },
        ],
        "limitations": [
            (
                "No canonical session records exist yet, so "
                "delivery and learning process metrics are null."
            ),
            (
                "Git metrics describe repository change volume, "
                "not engineering quality or business value."
            ),
            (
                "This baseline is not sufficient for a composite "
                "maturity or quality score."
            ),
        ],
        "composite_score_enabled": False,
    }


def normalize_for_check(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(payload))
    normalized["captured_at"] = "<captured-at>"
    for item in normalized["provenance"]:
        item["captured_at"] = "<captured-at>"
    return normalized


def run_self_tests() -> list[str]:
    failures: list[str] = []

    sample = (
        "10\t2\talpha.py\n"
        "-\t-\timage.png\n"
        "3\t4\tbeta.py\n"
    )
    files_changed = 0
    insertions = 0
    deletions = 0
    binary_files = 0
    for line in sample.splitlines():
        added, removed, _ = line.split("\t", 2)
        files_changed += 1
        if added == "-" or removed == "-":
            binary_files += 1
        else:
            insertions += int(added)
            deletions += int(removed)

    if (
        files_changed,
        insertions,
        deletions,
        binary_files,
    ) != (3, 13, 6, 1):
        failures.append("numstat parsing changed")

    process = session_process_metrics(0)
    if process["status"] != (
        "unavailable-no-session-records"
    ):
        failures.append("empty session status changed")
    if any(
        value is not None
        for value in process["raw"].values()
    ):
        failures.append("unavailable raw metrics must be null")
    if any(
        value is not None
        for value in process["derived"].values()
    ):
        failures.append(
            "unavailable derived metrics must be null"
        )

    try:
        session_process_metrics(1)
        failures.append(
            "unimplemented populated-session aggregation "
            "was accepted"
        )
    except ValueError:
        pass

    if normalize_for_check(
        {
            "captured_at": "2026-07-28T23:00:00-05:00",
            "provenance": [
                {
                    "captured_at": (
                        "2026-07-28T23:00:00-05:00"
                    )
                }
            ],
        }
    ) != {
        "captured_at": "<captured-at>",
        "provenance": [
            {"captured_at": "<captured-at>"}
        ],
    }:
        failures.append("baseline normalization changed")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract a SAGE continuous-improvement baseline"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--baseline-id")
    parser.add_argument("--change-id")
    parser.add_argument("--captured-at")
    parser.add_argument("--branch")
    parser.add_argument("--baseline-commit")
    parser.add_argument("--current-commit")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        failures = run_self_tests()
        if failures:
            print(
                "Kalaxy3 SAGE baseline extraction self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS Git numstat baseline parsing")
        print("PASS registry-count extraction contract")
        print("PASS unavailable session metrics remain null")
        print("PASS populated-session aggregation fails closed")
        print("PASS baseline check normalization")
        print(
            "Kalaxy3 SAGE baseline extraction self-test: PASS"
        )
        return 0

    required = {
        "baseline_id": args.baseline_id,
        "change_id": args.change_id,
        "captured_at": args.captured_at,
        "branch": args.branch,
        "baseline_commit": args.baseline_commit,
        "current_commit": args.current_commit,
    }
    missing = [
        key
        for key, value in required.items()
        if not value
    ]
    if missing:
        print(
            "Kalaxy3 SAGE baseline extraction: FAIL CLOSED"
        )
        print(f"  - missing arguments: {missing}")
        return 1

    try:
        record = extract_baseline(**required)
        registry = {
            "schema_version": "1.0",
            "registry_type": (
                "continuous-improvement-baselines"
            ),
            "baselines": [record],
        }

        if args.check is not None:
            existing = load_json(args.check)
            if normalize_for_check(existing["baselines"][0]) != (
                normalize_for_check(record)
            ):
                raise ValueError(
                    "baseline registry differs from "
                    "deterministic extraction"
                )
            print(
                "PASS baseline registry matches "
                "deterministic extraction"
            )
            return 0

        if args.output is None:
            print(json.dumps(registry, indent=4))
            return 0

        args.output.write_text(
            json.dumps(registry, indent=4) + "\n",
            encoding="utf-8",
        )
        print(f"WROTE {args.output}")
        return 0
    except (
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        TypeError,
    ) as error:
        print(
            "Kalaxy3 SAGE baseline extraction: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
