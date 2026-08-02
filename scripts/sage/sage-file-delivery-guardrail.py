#!/usr/bin/env python3
"""Enforce Kalaxy3's file-based operator execution delivery contract."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]

AGENTS_PATH = ROOT / "AGENTS.md"
LESSONS_PATH = ROOT / "sage-lessons.json"
ACTIONS_PATH = ROOT / "sage-improvement-actions.json"
AUTHORITY_PATH = ROOT / "sage-change-authority.json"
MAKEFILE_PATH = ROOT / "Makefile"

LESSON_ID = "SAGE-LESSON-20260728-001"
ACTION_TITLE = "Enforce file-based Kalaxy3 execution delivery"
EVIDENCE_REFERENCE = (
    "terminal-session:"
    "2026-08-01-file-based-execution-recurrence-001"
)
GUARDRAIL_PATH = "scripts/sage/sage-file-delivery-guardrail.py"

SECTION_MARKER = "## Operator execution delivery contract"
REQUIRED_PHRASES = (
    "downloadable executable helper file",
    "SHA-256 checksum",
    "one short invocation",
    "explicitly requests console commands",
    "known recurrence",
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: expected a JSON object")
    return payload


def validate(
    *,
    agents_text: str,
    lessons: Mapping[str, Any],
    actions: Mapping[str, Any],
    authority: Mapping[str, Any],
    makefile_text: str,
    require_validated: bool,
) -> list[str]:
    failures: list[str] = []

    normalized_agents_text = " ".join(agents_text.split())

    if SECTION_MARKER not in agents_text:
        failures.append("AGENTS.md delivery-contract section is missing")
    for phrase in REQUIRED_PHRASES:
        if phrase not in normalized_agents_text:
            failures.append(
                f"AGENTS.md delivery-contract phrase missing: {phrase}"
            )

    lesson_matches = [
        item
        for item in lessons.get("lessons", [])
        if isinstance(item, dict)
        and item.get("lesson_id") == LESSON_ID
    ]
    if len(lesson_matches) != 1:
        failures.append(
            f"{LESSON_ID}: expected exactly one lesson record"
        )
    else:
        lesson = lesson_matches[0]
        if int(lesson.get("recurrence_count", 0)) < 2:
            failures.append(
                f"{LESSON_ID}: recurrence_count must be at least 2"
            )
        if lesson.get("automation_status") not in {
            "guardrail",
            "automated",
        }:
            failures.append(
                f"{LESSON_ID}: automation_status must be guardrail or automated"
            )
        if EVIDENCE_REFERENCE not in lesson.get(
            "latest_evidence",
            [],
        ):
            failures.append(
                f"{LESSON_ID}: recurrence evidence is missing"
            )

    action_matches = [
        item
        for item in actions.get("actions", [])
        if isinstance(item, dict)
        and item.get("title") == ACTION_TITLE
    ]
    if len(action_matches) != 1:
        failures.append(
            f"{ACTION_TITLE}: expected exactly one action"
        )
    else:
        action = action_matches[0]
        allowed = {
            "identified",
            "accepted",
            "implemented",
            "validated",
            "measured",
            "closed",
        }
        if action.get("current_status") not in allowed:
            failures.append(
                f"{ACTION_TITLE}: invalid current status"
            )
        if require_validated and action.get("current_status") not in {
            "validated",
            "measured",
            "closed",
        }:
            failures.append(
                f"{ACTION_TITLE}: validated status required"
            )
        if LESSON_ID not in action.get("source_lessons", []):
            failures.append(
                f"{ACTION_TITLE}: source lesson is missing"
            )

    governance = [
        item
        for item in authority.get("contexts", [])
        if isinstance(item, dict)
        and item.get("id") == "repository-governance"
    ]
    if len(governance) != 1:
        failures.append(
            "repository-governance context is missing or duplicated"
        )
    elif GUARDRAIL_PATH not in governance[0].get(
        "authoritative_files",
        [],
    ):
        failures.append(
            "file-delivery guardrail is not registered as authority"
        )

    if "sage-file-delivery-guardrail:" not in makefile_text:
        failures.append(
            "Makefile file-delivery target is missing"
        )
    if (
        "python3 scripts/sage/sage-file-delivery-guardrail.py"
        not in makefile_text
    ):
        failures.append(
            "Makefile file-delivery command is missing"
        )

    return failures


def run_self_test() -> list[str]:
    failures: list[str] = []
    fixture_agents = (
        f"{SECTION_MARKER}\n\n"
        + "\n".join(REQUIRED_PHRASES)
        + "\n"
    )
    fixture_lessons = {
        "lessons": [
            {
                "lesson_id": LESSON_ID,
                "recurrence_count": 2,
                "automation_status": "guardrail",
                "latest_evidence": [EVIDENCE_REFERENCE],
            }
        ]
    }
    fixture_actions = {
        "actions": [
            {
                "title": ACTION_TITLE,
                "source_lessons": [LESSON_ID],
                "current_status": "validated",
            }
        ]
    }
    fixture_authority = {
        "contexts": [
            {
                "id": "repository-governance",
                "authoritative_files": [GUARDRAIL_PATH],
            }
        ]
    }
    fixture_make = (
        "sage-self-test:\n"
        "\tpython3 scripts/sage/sage-file-delivery-guardrail.py\n\n"
        "sage-file-delivery-guardrail:\n"
        "\tpython3 scripts/sage/sage-file-delivery-guardrail.py\n"
    )

    failures.extend(
        validate(
            agents_text=fixture_agents,
            lessons=fixture_lessons,
            actions=fixture_actions,
            authority=fixture_authority,
            makefile_text=fixture_make,
            require_validated=True,
        )
    )

    broken_agents = fixture_agents.replace(
        "one short invocation",
        "many console commands",
    )
    negative = validate(
        agents_text=broken_agents,
        lessons=fixture_lessons,
        actions=fixture_actions,
        authority=fixture_authority,
        makefile_text=fixture_make,
        require_validated=True,
    )
    if not any(
        "one short invocation" in item
        for item in negative
    ):
        failures.append(
            "negative test accepted a missing one-line invocation contract"
        )

    with tempfile.TemporaryDirectory(
        prefix="sage-file-delivery-self-test-"
    ) as raw:
        target = Path(raw) / "marker.txt"
        target.write_text("pass\n", encoding="utf-8")
        if target.read_text(encoding="utf-8") != "pass\n":
            failures.append("temporary filesystem self-test failed")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Kalaxy3's file-based operator execution contract"
        )
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )
    parser.add_argument(
        "--require-validated",
        action="store_true",
    )
    args = parser.parse_args()

    if args.self_test:
        failures = run_self_test()
    else:
        failures = validate(
            agents_text=AGENTS_PATH.read_text(encoding="utf-8"),
            lessons=load_json(LESSONS_PATH),
            actions=load_json(ACTIONS_PATH),
            authority=load_json(AUTHORITY_PATH),
            makefile_text=MAKEFILE_PATH.read_text(
                encoding="utf-8"
            ),
            require_validated=args.require_validated,
        )

    if failures:
        print(
            "Kalaxy3 SAGE file-delivery guardrail: FAIL CLOSED",
            file=sys.stderr,
        )
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 2

    if args.self_test:
        print("PASS file-delivery contract positive fixture")
        print("PASS file-delivery contract negative fixture")
        print("PASS validated-action requirement")
    else:
        print("PASS AGENTS.md file-based execution contract")
        print("PASS recurring lesson and evidence linkage")
        print("PASS improvement-action lifecycle linkage")
        print("PASS repository authority and Make integration")
    print("Kalaxy3 SAGE file-delivery guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        print(
            "Kalaxy3 SAGE file-delivery guardrail: "
            f"FAIL CLOSED\n  - {error}",
            file=sys.stderr,
        )
        raise SystemExit(2)
