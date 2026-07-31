#!/usr/bin/env python3
"""Validate post-session reviews and derive lesson-to-control drafts."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Final, Sequence

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
LESSON_REGISTRY_PATH: Final = ROOT / "sage-lessons.json"
ACTION_REGISTRY_PATH: Final = ROOT / "sage-improvement-actions.json"
SESSION_REGISTRY_PATH: Final = (
    ROOT / "sage-session-improvement-registry.json"
)
ACTION_TOOL_PATH: Final = (
    ROOT / "scripts/sage/sage-improvement-actions.py"
)

REVIEW_ID_RE: Final = re.compile(
    r"^SAGE-REVIEW-[0-9]{8}-[0-9]{3}$"
)
FAILURE_ID_RE: Final = re.compile(r"^FAIL-[0-9]{3}$")
DECISION_ID_RE: Final = re.compile(r"^CONTROL-[0-9]{3}$")
SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_action_tool() -> Any:
    spec = importlib.util.spec_from_file_location(
        "sage_improvement_actions",
        ACTION_TOOL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load improvement-action tool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def require_unique_strings(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) != len(set(value))
        or not all(
            isinstance(item, str) and item
            for item in value
        )
    ):
        raise ValueError(
            f"{label} must be a non-empty unique string list"
        )
    return list(value)


def validate_policy(policy: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(policy, dict):
        return ["policy must be an object"]

    review_policy = policy.get("post_session_review_policy")
    if not isinstance(review_policy, dict):
        return ["post_session_review_policy must be an object"]

    if review_policy.get("required_questions") != policy.get(
        "post_session_questions"
    ):
        failures.append(
            "review required questions must match post_session_questions"
        )
    if review_policy.get(
        "required_feedback_planes"
    ) != policy.get("required_feedback_planes"):
        failures.append(
            "review feedback planes must match policy"
        )
    if review_policy.get("failure_classifications") != [
        "known",
        "new",
    ]:
        failures.append(
            "review failure classifications changed"
        )
    if review_policy.get("control_types") != [
        "manual",
        "template",
        "preflight",
        "guardrail",
        "runbook",
        "automation",
        "no-action",
    ]:
        failures.append("review control types changed")

    for key in (
        "canonical_session_required",
        "every_referenced_lesson_requires_control_decision",
        "create_action_requires_draft",
        "no_action_requires_rationale",
        "action_registration_is_separate",
        "review_registry_mutation_is_separate",
    ):
        if review_policy.get(key) is not True:
            failures.append(
                f"post_session_review_policy.{key} must be true"
            )

    if review_policy.get("composite_score_enabled") is not False:
        failures.append(
            "post-session composite scoring must remain closed"
        )
    return failures


def lesson_ids(registry: dict[str, Any]) -> set[str]:
    lessons = registry.get("lessons")
    if not isinstance(lessons, list):
        raise ValueError("lesson registry lessons must be a list")
    return {
        str(item.get("lesson_id"))
        for item in lessons
        if isinstance(item, dict)
    }


def session_by_id(
    registry: dict[str, Any],
    session_id: str,
) -> dict[str, Any]:
    sessions = registry.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("session registry sessions must be a list")
    matches = [
        item
        for item in sessions
        if isinstance(item, dict)
        and item.get("session_id") == session_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"session {session_id} must appear exactly once"
        )
    return matches[0]


def validate_review(
    review: Any,
    *,
    policy: dict[str, Any],
    lessons: dict[str, Any],
    actions: dict[str, Any],
    sessions: dict[str, Any],
    action_tool: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    drafts: list[dict[str, Any]] = []

    if not isinstance(review, dict):
        return ["review must be an object"], drafts

    required = {
        "review_id",
        "session_id",
        "change_id",
        "recorded_at",
        "reviewer",
        "implementation_commit",
        "evidence_references",
        "questions",
        "failures",
        "feedback_planes",
        "control_decisions",
        "summary",
        "composite_score_enabled",
    }
    if set(review) != required:
        failures.append(
            "review top-level fields must match the contract"
        )

    if not REVIEW_ID_RE.fullmatch(
        str(review.get("review_id", ""))
    ):
        failures.append("review_id invalid")
    for key in (
        "recorded_at",
        "reviewer",
        "summary",
    ):
        try:
            require_string(review.get(key), key)
        except ValueError as error:
            failures.append(str(error))

    if not SHA_RE.fullmatch(
        str(review.get("implementation_commit", ""))
    ):
        failures.append("implementation_commit invalid")

    try:
        require_unique_strings(
            review.get("evidence_references"),
            "evidence_references",
        )
    except ValueError as error:
        failures.append(str(error))

    try:
        session = session_by_id(
            sessions,
            str(review.get("session_id", "")),
        )
        if session.get("change_id") != review.get("change_id"):
            failures.append(
                "review change_id does not match session"
            )
        if session.get(
            "implementation_commit"
        ) != review.get("implementation_commit"):
            failures.append(
                "review implementation_commit does not match session"
            )
    except ValueError as error:
        failures.append(str(error))

    expected_questions = policy[
        "post_session_review_policy"
    ]["required_questions"]
    questions = review.get("questions")
    if not isinstance(questions, list):
        failures.append("questions must be a list")
    else:
        actual_questions = [
            item.get("question")
            for item in questions
            if isinstance(item, dict)
        ]
        if actual_questions != expected_questions:
            failures.append(
                "review questions must preserve canonical order and text"
            )
        for index, item in enumerate(questions):
            if (
                not isinstance(item, dict)
                or set(item) != {"question", "answer"}
                or not isinstance(item.get("answer"), str)
                or not item.get("answer")
            ):
                failures.append(
                    f"review question {index + 1} is incomplete"
                )

    known_lessons = lesson_ids(lessons)
    failure_items = review.get("failures")
    failure_identifiers: list[str] = []
    referenced_lessons: list[str] = []

    if not isinstance(failure_items, list):
        failures.append("failures must be a list")
        failure_items = []

    for item in failure_items:
        if not isinstance(item, dict):
            failures.append("failure entry must be an object")
            continue

        required_failure = {
            "failure_id",
            "summary",
            "classification",
            "lesson_ids",
            "lesson_surfaced",
            "lesson_used",
            "recurred",
            "detected_pre_mutation",
            "avoidable_rework_minutes",
            "root_cause",
            "prevention_opportunity",
        }
        if set(item) != required_failure:
            failures.append("failure fields invalid")

        failure_id = str(item.get("failure_id", ""))
        failure_identifiers.append(failure_id)
        if not FAILURE_ID_RE.fullmatch(failure_id):
            failures.append(f"{failure_id}: failure_id invalid")

        for key in (
            "summary",
            "root_cause",
            "prevention_opportunity",
        ):
            try:
                require_string(
                    item.get(key),
                    f"{failure_id} {key}",
                )
            except ValueError as error:
                failures.append(str(error))

        classification = item.get("classification")
        if classification not in ("known", "new"):
            failures.append(
                f"{failure_id}: classification invalid"
            )

        ids = item.get("lesson_ids")
        if not isinstance(ids, list):
            failures.append(
                f"{failure_id}: lesson_ids must be a list"
            )
            ids = []
        elif (
            len(ids) != len(set(ids))
            or not all(
                isinstance(value, str) and value
                for value in ids
            )
        ):
            failures.append(
                f"{failure_id}: lesson_ids invalid"
            )

        unknown = sorted(set(ids) - known_lessons)
        if unknown:
            failures.append(
                f"{failure_id}: unknown lessons {unknown}"
            )
        referenced_lessons.extend(ids)

        if classification == "known" and not ids:
            failures.append(
                f"{failure_id}: known failure requires a lesson"
            )
        if item.get("lesson_used") is True and item.get(
            "lesson_surfaced"
        ) is not True:
            failures.append(
                f"{failure_id}: used lesson was not surfaced"
            )
        if item.get("recurred") is True and classification != "known":
            failures.append(
                f"{failure_id}: only known failures can recur"
            )

        for key in (
            "lesson_surfaced",
            "lesson_used",
            "recurred",
            "detected_pre_mutation",
        ):
            if not isinstance(item.get(key), bool):
                failures.append(
                    f"{failure_id}: {key} must be boolean"
                )

        minutes = item.get("avoidable_rework_minutes")
        if minutes is not None and (
            not isinstance(minutes, (int, float))
            or isinstance(minutes, bool)
            or minutes < 0
        ):
            failures.append(
                f"{failure_id}: avoidable_rework_minutes invalid"
            )

    if len(failure_identifiers) != len(
        set(failure_identifiers)
    ):
        failures.append("failure identifiers must be unique")

    feedback = review.get("feedback_planes")
    expected_planes = policy[
        "post_session_review_policy"
    ]["required_feedback_planes"]
    if not isinstance(feedback, dict):
        failures.append("feedback_planes must be an object")
    elif list(feedback) != expected_planes:
        failures.append(
            "feedback planes must preserve canonical order"
        )
    else:
        for plane, item in feedback.items():
            if (
                not isinstance(item, dict)
                or set(item) != {
                    "summary",
                    "evidence_references",
                }
            ):
                failures.append(
                    f"{plane} feedback fields invalid"
                )
                continue
            try:
                require_string(
                    item.get("summary"),
                    f"{plane} feedback summary",
                )
                require_unique_strings(
                    item.get("evidence_references"),
                    f"{plane} feedback evidence",
                )
            except ValueError as error:
                failures.append(str(error))

    decisions = review.get("control_decisions")
    decision_identifiers: list[str] = []
    decision_lesson_coverage: list[str] = []

    if not isinstance(decisions, list):
        failures.append("control_decisions must be a list")
        decisions = []

    for item in decisions:
        if not isinstance(item, dict):
            failures.append(
                "control decision must be an object"
            )
            continue

        required_decision = {
            "decision_id",
            "source_lessons",
            "source_failures",
            "disposition",
            "target_control_type",
            "rationale",
            "action_draft",
        }
        if set(item) != required_decision:
            failures.append("control decision fields invalid")

        decision_id = str(item.get("decision_id", ""))
        decision_identifiers.append(decision_id)
        if not DECISION_ID_RE.fullmatch(decision_id):
            failures.append(
                f"{decision_id}: decision_id invalid"
            )

        source_lessons = item.get("source_lessons")
        try:
            source_lessons = require_unique_strings(
                source_lessons,
                f"{decision_id} source_lessons",
            )
        except ValueError as error:
            failures.append(str(error))
            source_lessons = []

        unknown = sorted(
            set(source_lessons) - known_lessons
        )
        if unknown:
            failures.append(
                f"{decision_id}: unknown lessons {unknown}"
            )
        decision_lesson_coverage.extend(source_lessons)

        source_failures = item.get("source_failures")
        if not isinstance(source_failures, list):
            failures.append(
                f"{decision_id}: source_failures must be a list"
            )
            source_failures = []
        elif (
            len(source_failures)
            != len(set(source_failures))
            or not all(
                isinstance(value, str) and value
                for value in source_failures
            )
        ):
            failures.append(
                f"{decision_id}: source_failures invalid"
            )
        unknown_failures = sorted(
            set(source_failures)
            - set(failure_identifiers)
        )
        if unknown_failures:
            failures.append(
                f"{decision_id}: unknown failures "
                f"{unknown_failures}"
            )

        disposition = item.get("disposition")
        control_type = item.get("target_control_type")
        try:
            require_string(
                item.get("rationale"),
                f"{decision_id} rationale",
            )
        except ValueError as error:
            failures.append(str(error))

        draft = item.get("action_draft")
        if disposition == "no-action":
            if control_type != "no-action":
                failures.append(
                    f"{decision_id}: no-action control type required"
                )
            if draft is not None:
                failures.append(
                    f"{decision_id}: no-action cannot contain a draft"
                )
        elif disposition == "create-action":
            if control_type == "no-action":
                failures.append(
                    f"{decision_id}: create-action control type invalid"
                )
            if not isinstance(draft, dict):
                failures.append(
                    f"{decision_id}: action draft required"
                )
            else:
                if draft.get(
                    "target_control_type"
                ) != control_type:
                    failures.append(
                        f"{decision_id}: action draft control type differs"
                    )
                if set(
                    draft.get("source_lessons", [])
                ) != set(source_lessons):
                    failures.append(
                        f"{decision_id}: action draft lesson sources differ"
                    )
                if review.get("session_id") not in draft.get(
                    "source_sessions", []
                ):
                    failures.append(
                        f"{decision_id}: review session missing from draft"
                    )
                try:
                    action_tool.plan_registration(
                        actions,
                        policy,
                        draft,
                        recorded_at=str(
                            review.get("recorded_at", "")
                        ),
                        actor=str(
                            review.get("reviewer", "")
                        ),
                        reason=str(
                            item.get("rationale", "")
                        ),
                        evidence_references=list(
                            review.get(
                                "evidence_references",
                                [],
                            )
                        ),
                    )
                    drafts.append(copy.deepcopy(draft))
                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ) as error:
                    failures.append(
                        f"{decision_id}: action draft invalid: "
                        f"{error}"
                    )
        else:
            failures.append(
                f"{decision_id}: disposition invalid"
            )

    if len(decision_identifiers) != len(
        set(decision_identifiers)
    ):
        failures.append(
            "control decision identifiers must be unique"
        )

    for lesson_id in sorted(set(referenced_lessons)):
        count = decision_lesson_coverage.count(lesson_id)
        if count != 1:
            failures.append(
                f"{lesson_id}: referenced lesson requires "
                "exactly one control decision"
            )

    if review.get("composite_score_enabled") is not False:
        failures.append(
            "post-session composite score must remain disabled"
        )
    return failures, drafts


def representative_sessions() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "registry_type": "session-improvements",
        "sessions": [
            {
                "session_id": "SAGE-SESSION-20260728-001",
                "change_id": "SAGE-CHANGE-20260728-001",
                "implementation_commit": "1" * 40,
            }
        ],
    }


def representative_review(
    required_questions: Sequence[str],
) -> dict[str, Any]:
    session_id = "SAGE-SESSION-20260728-001"
    return {
        "review_id": "SAGE-REVIEW-20260728-001",
        "session_id": session_id,
        "change_id": "SAGE-CHANGE-20260728-001",
        "recorded_at": "2026-07-28T23:50:00-05:00",
        "reviewer": "repository-workflow",
        "implementation_commit": "1" * 40,
        "evidence_references": [
            "terminal-session:continuous-improvement-001",
        ],
        "questions": [
            {
                "question": question,
                "answer": "Reviewed with canonical evidence.",
            }
            for question in required_questions
        ],
        "failures": [
            {
                "failure_id": "FAIL-001",
                "summary": (
                    "A large interactive heredoc required recovery."
                ),
                "classification": "known",
                "lesson_ids": [
                    "SAGE-LESSON-20260728-001",
                ],
                "lesson_surfaced": True,
                "lesson_used": True,
                "recurred": True,
                "detected_pre_mutation": False,
                "avoidable_rework_minutes": 20,
                "root_cause": (
                    "A large payload was pasted into an interactive shell."
                ),
                "prevention_opportunity": (
                    "Require downloadable implementation scripts."
                ),
            }
        ],
        "feedback_planes": {
            plane: {
                "summary": (
                    f"{plane} feedback reviewed without "
                    "a composite score."
                ),
                "evidence_references": [
                    "terminal-session:continuous-improvement-001",
                ],
            }
            for plane in [
                "delivery",
                "operations",
                "economics",
                "learning",
            ]
        },
        "control_decisions": [
            {
                "decision_id": "CONTROL-001",
                "source_lessons": [
                    "SAGE-LESSON-20260728-001",
                ],
                "source_failures": ["FAIL-001"],
                "disposition": "create-action",
                "target_control_type": "template",
                "rationale": (
                    "Convert the proven recovery pattern into "
                    "a standard delivery control."
                ),
                "action_draft": {
                    "action_id": "SAGE-ACTION-20260728-001",
                    "title": (
                        "Require downloadable implementation scripts"
                    ),
                    "source_lessons": [
                        "SAGE-LESSON-20260728-001",
                    ],
                    "source_sessions": [session_id],
                    "owner": "repository-workflow",
                    "priority": "high",
                    "target_control_type": "template",
                    "desired_outcome": (
                        "Prevent interactive heredoc failures."
                    ),
                    "acceptance_criteria": [
                        (
                            "Large generated terminal payloads are "
                            "delivered as downloadable scripts."
                        ),
                    ],
                    "measurement_plan": [
                        (
                            "Track recurrence of interactive "
                            "heredoc failures."
                        ),
                    ],
                },
            },
            {
                "decision_id": "CONTROL-002",
                "source_lessons": [
                    "SAGE-LESSON-20260728-005",
                ],
                "source_failures": [],
                "disposition": "no-action",
                "target_control_type": "no-action",
                "rationale": (
                    "Existing preflight and branch checks already "
                    "implement the lesson."
                ),
                "action_draft": None,
            },
        ],
        "summary": (
            "The review converts evidence into an explicit "
            "control decision without mutating registries."
        ),
        "composite_score_enabled": False,
    }


def run_self_tests(
    policy: dict[str, Any],
    lessons: dict[str, Any],
    actions: dict[str, Any],
    action_tool: Any,
) -> list[str]:
    failures: list[str] = []
    sessions = representative_sessions()
    review = representative_review(
        policy["post_session_review_policy"][
            "required_questions"
        ]
    )

    valid_failures, drafts = validate_review(
        review,
        policy=policy,
        lessons=lessons,
        actions=actions,
        sessions=sessions,
        action_tool=action_tool,
    )
    failures.extend(valid_failures)
    if len(drafts) != 1:
        failures.append(
            "representative review must derive one action draft"
        )

    cases: list[tuple[str, dict[str, Any]]] = []

    missing_question = copy.deepcopy(review)
    missing_question["questions"].pop()
    cases.append(("missing canonical question", missing_question))

    no_decision = copy.deepcopy(review)
    no_decision["control_decisions"] = [
        no_decision["control_decisions"][1]
    ]
    cases.append(("lesson without control decision", no_decision))

    duplicate_coverage = copy.deepcopy(review)
    duplicate_coverage["control_decisions"][1][
        "source_lessons"
    ] = ["SAGE-LESSON-20260728-001"]
    cases.append(
        ("duplicate lesson control coverage", duplicate_coverage)
    )

    no_action_draft = copy.deepcopy(review)
    no_action_draft["control_decisions"][1][
        "action_draft"
    ] = copy.deepcopy(
        review["control_decisions"][0]["action_draft"]
    )
    cases.append(
        ("no-action with action draft", no_action_draft)
    )

    missing_draft = copy.deepcopy(review)
    missing_draft["control_decisions"][0][
        "action_draft"
    ] = None
    cases.append(
        ("create-action without draft", missing_draft)
    )

    unknown_lesson = copy.deepcopy(review)
    unknown_lesson["failures"][0]["lesson_ids"] = [
        "SAGE-LESSON-20990101-999",
    ]
    unknown_lesson["control_decisions"][0][
        "source_lessons"
    ] = ["SAGE-LESSON-20990101-999"]
    unknown_lesson["control_decisions"][0][
        "action_draft"
    ]["source_lessons"] = [
        "SAGE-LESSON-20990101-999",
    ]
    cases.append(("unknown lesson", unknown_lesson))

    used_not_surfaced = copy.deepcopy(review)
    used_not_surfaced["failures"][0][
        "lesson_surfaced"
    ] = False
    cases.append(
        ("used lesson not surfaced", used_not_surfaced)
    )

    composite = copy.deepcopy(review)
    composite["composite_score_enabled"] = True
    cases.append(("composite score enabled", composite))

    for label, candidate in cases:
        case_failures, _ = validate_review(
            candidate,
            policy=policy,
            lessons=lessons,
            actions=actions,
            sessions=sessions,
            action_tool=action_tool,
        )
        if not case_failures:
            failures.append(
                f"negative test accepted {label}"
            )
    nullable_rework = representative_review(
        policy["post_session_review_policy"]["required_questions"]
    )
    nullable_rework["failures"][0][
        "avoidable_rework_minutes"
    ] = None
    nullable_failures, _ = validate_review(
        nullable_rework,
        policy=policy,
        lessons=lessons,
        actions=actions,
        sessions=representative_sessions(),
        action_tool=action_tool,
    )
    if nullable_failures:
        failures.append(
            "unavailable failure rework was rejected: "
            + "; ".join(nullable_failures)
        )

    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a post-session review and derive "
            "lesson-to-control action drafts"
        )
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--review-output", type=Path)
    parser.add_argument("--action-drafts-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        policy = load_json(POLICY_PATH)
        lessons = load_json(LESSON_REGISTRY_PATH)
        actions = load_json(ACTION_REGISTRY_PATH)
        sessions = load_json(SESSION_REGISTRY_PATH)
        action_tool = load_action_tool()

        policy_failures = validate_policy(policy)
        if policy_failures:
            raise ValueError("; ".join(policy_failures))

        if args.self_test:
            failures = run_self_tests(
                policy,
                lessons,
                actions,
                action_tool,
            )
            if failures:
                print(
                    "Kalaxy3 SAGE post-session review "
                    "self-test: FAIL"
                )
                for failure in failures:
                    print(f"  - {failure}")
                return 1
            print("PASS canonical post-session questions")
            print("PASS canonical session linkage")
            print("PASS known-failure and lesson-use review")
            print("PASS unavailable failure rework remains null")
            print("PASS four-plane feedback review")
            print("PASS lesson-to-control decision coverage")
            print("PASS action drafts validated without mutation")
            print("PASS no-action decisions require rationale")
            print("PASS post-session review mutation negative tests")
            print(
                "Kalaxy3 SAGE post-session review "
                "self-test: PASS"
            )
            return 0

        if args.input is None:
            print(
                "Provide --input or use --self-test."
            )
            return 2

        review = load_json(args.input)
        failures, drafts = validate_review(
            review,
            policy=policy,
            lessons=lessons,
            actions=actions,
            sessions=sessions,
            action_tool=action_tool,
        )
        if failures:
            print(
                "Kalaxy3 SAGE post-session review: "
                "FAIL CLOSED"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1

        print("Kalaxy3 SAGE post-session review: PASS")
        print(f"Review: {review['review_id']}")
        print(f"Session: {review['session_id']}")
        print(f"Action drafts: {len(drafts)}")
        print(
            "Registry mutations: none; review and action "
            "registration remain separate"
        )

        if args.review_output is not None:
            args.review_output.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "registry_type": "post-session-reviews",
                        "reviews": [review],
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"WROTE {args.review_output}")

        if args.action_drafts_output is not None:
            args.action_drafts_output.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "source_review_id": review["review_id"],
                        "action_drafts": drafts,
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )
            print(f"WROTE {args.action_drafts_output}")
        return 0
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        print(
            "Kalaxy3 SAGE post-session review: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
