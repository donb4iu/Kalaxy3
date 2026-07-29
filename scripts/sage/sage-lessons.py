#!/usr/bin/env python3
"""Surface applicable prior SAGE lessons before implementation."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Final, Sequence

ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY: Final = ROOT / "sage-lessons.json"
SURFACE_STATUSES: Final = {
    "accepted",
    "automated",
    "validated",
}
REQUIRED_FIELDS: Final = {
    "lesson_id",
    "title",
    "status",
    "contexts",
    "match_terms",
    "path_prefixes",
    "failure_signature",
    "symptoms",
    "root_cause",
    "known_resolution",
    "preventive_control",
    "preflight_detection",
    "first_evidence",
    "latest_evidence",
    "recurrence_count",
    "automation_status",
}


def normalize(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").split())


def load_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Lesson registry must be a JSON object")
    return payload


def validate_registry(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if payload.get("schema_version") != "1.0":
        failures.append("lesson registry schema_version must be 1.0")
    if payload.get("registry_type") != "lessons":
        failures.append("lesson registry_type must be lessons")

    lessons = payload.get("lessons")
    if not isinstance(lessons, list) or not lessons:
        return failures + ["lessons must be a non-empty list"]

    identifiers: list[str] = []
    for item in lessons:
        if not isinstance(item, dict):
            failures.append("lesson entry must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - set(item))
        extra = sorted(set(item) - REQUIRED_FIELDS)
        if missing:
            failures.append(
                f"{item.get('lesson_id', '<unknown>')}: "
                f"missing fields {missing}"
            )
        if extra:
            failures.append(
                f"{item.get('lesson_id', '<unknown>')}: "
                f"unexpected fields {extra}"
            )

        identifier = str(item.get("lesson_id", ""))
        identifiers.append(identifier)

        for key in (
            "contexts",
            "match_terms",
            "symptoms",
            "known_resolution",
            "preventive_control",
            "preflight_detection",
            "first_evidence",
            "latest_evidence",
        ):
            value = item.get(key)
            if (
                not isinstance(value, list)
                or not value
                or not all(
                    isinstance(entry, str) and entry
                    for entry in value
                )
            ):
                failures.append(
                    f"{identifier}: {key} must be "
                    "a non-empty string list"
                )

        prefixes = item.get("path_prefixes")
        if not isinstance(prefixes, list) or not all(
            isinstance(entry, str)
            for entry in prefixes
        ):
            failures.append(
                f"{identifier}: path_prefixes must be a string list"
            )

        recurrence = item.get("recurrence_count")
        if (
            not isinstance(recurrence, int)
            or isinstance(recurrence, bool)
            or recurrence < 1
        ):
            failures.append(
                f"{identifier}: recurrence_count must be positive"
            )

    if len(identifiers) != len(set(identifiers)):
        failures.append("lesson identifiers must be unique")
    return failures


def changed_paths() -> list[str]:
    commands = (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
    )
    paths: set[str] = set()
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        paths.update(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )
    return sorted(paths)


def infer_lessons(
    payload: dict[str, Any],
    request: str,
    paths: Sequence[str],
) -> list[dict[str, Any]]:
    request_text = normalize(request)
    normalized_paths = [normalize(path) for path in paths]
    selected: list[dict[str, Any]] = []

    for lesson in payload["lessons"]:
        if lesson.get("status") not in SURFACE_STATUSES:
            continue

        terms = [
            normalize(term)
            for term in lesson["match_terms"]
        ]
        prefixes = [
            normalize(prefix)
            for prefix in lesson["path_prefixes"]
        ]

        request_match = any(
            term and term in request_text
            for term in terms
        )
        path_match = any(
            path.startswith(prefix)
            for path in normalized_paths
            for prefix in prefixes
            if prefix
        )
        if request_match or path_match:
            selected.append(lesson)

    return sorted(
        selected,
        key=lambda item: str(item["lesson_id"]),
    )


def render_report(
    request: str,
    paths: Sequence[str],
    lessons: Sequence[dict[str, Any]],
) -> None:
    print("Kalaxy3 SAGE lessons discovery: PASS")
    print(f"Repository: {ROOT}")
    print(
        "Lesson request: "
        f"{request or '<changed-path discovery>'}"
    )

    if paths:
        print("\nLesson paths considered:")
        for path in paths:
            print(f"  - {path}")

    if not lessons:
        print("\nApplicable prior lessons: none")
        return

    print("\nApplicable prior lessons:")
    for lesson in lessons:
        print(
            f"  - {lesson['lesson_id']}: "
            f"{lesson['title']}"
        )
        print(f"    Status: {lesson['status']}")
        print(
            "    Failure signature: "
            f"{lesson['failure_signature']}"
        )
        print("    Preventive controls:")
        for value in lesson["preventive_control"]:
            print(f"      - {value}")
        print("    Preflight detection:")
        for value in lesson["preflight_detection"]:
            print(f"      - {value}")


def run_self_tests(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases = {
        "Use a heredoc to add a large Markdown file": {
            "SAGE-LESSON-20260728-001",
        },
        "Push cohesive changes to a feature branch": {
            "SAGE-LESSON-20260728-005",
        },
        "Run kubectl with /etc/rancher/k3s/k3s.yaml": {
            "SAGE-LESSON-20260728-006",
        },
        "Investigate Loki 429 errors during startup": {
            "SAGE-LESSON-20260728-008",
        },
    }

    for request, expected in cases.items():
        actual = {
            str(item["lesson_id"])
            for item in infer_lessons(payload, request, [])
        }
        missing = sorted(expected - actual)
        if missing:
            failures.append(
                f"{request!r} did not surface {missing}"
            )

    path_cases = {
        "authority JSON": (
            ["sage-change-authority.json"],
            {"SAGE-LESSON-20260728-004"},
        ),
        "SAGE script": (
            ["scripts/sage/example.py"],
            {"SAGE-LESSON-20260728-003"},
        ),
        "logging template": (
            [
                "infrastructure/k3s-homelab/"
                "playbooks/templates/loki-values.yml.j2"
            ],
            {"SAGE-LESSON-20260728-008"},
        ),
    }

    for label, (paths, expected) in path_cases.items():
        actual = {
            str(item["lesson_id"])
            for item in infer_lessons(payload, "", paths)
        }
        missing = sorted(expected - actual)
        if missing:
            failures.append(
                f"{label} did not surface {missing}"
            )
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Surface applicable prior SAGE lessons"
    )
    parser.add_argument("--request", default="")
    parser.add_argument("--changed", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        payload = load_registry(args.registry)
        failures = validate_registry(payload)
    except (OSError, ValueError, TypeError) as error:
        failures = [str(error)]
        payload = {}

    if failures:
        print("Kalaxy3 SAGE lessons discovery: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    if args.self_test:
        failures = run_self_tests(payload)
        if failures:
            print(
                "Kalaxy3 SAGE lessons discovery self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(
            "Kalaxy3 SAGE lessons discovery self-test: PASS"
        )
        return 0

    paths = changed_paths() if args.changed else []
    if not args.request and not paths:
        print("Provide --request TEXT or use --changed.")
        return 2

    lessons = infer_lessons(payload, args.request, paths)
    render_report(args.request, paths, lessons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
