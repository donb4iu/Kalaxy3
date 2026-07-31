#!/usr/bin/env python3
"""Calculate deterministic SAGE session metrics and prediction scores."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any, Final

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
PREDICTION_FIELDS: Final = {
    "stage",
    "version",
    "subject",
    "unit",
    "confidence",
    "predicted_point",
    "predicted_min",
    "predicted_max",
    "actual",
    "error_classifications",
}
STAGES: Final = {"discovery", "pre-deployment"}
CONFIDENCE_LEVELS: Final = ["high", "medium", "low"]
ERROR_CLASSIFICATIONS: Final = {
    "incomplete-discovery",
    "prior-lesson-not-applied",
    "baseline-inaccurate",
    "scope-changed",
    "implementation-defect",
    "environmental-change",
    "dependency-behavior",
    "operator-error",
    "new-failure-mode",
    "range-too-narrow",
    "confidence-overstated",
    "confidence-understated",
}
CHANGE_ID_RE: Final = re.compile(
    r"^SAGE-CHANGE-[0-9]{8}-[0-9]{3}$"
)
SESSION_ID_RE: Final = re.compile(
    r"^SAGE-SESSION-[0-9]{8}-[0-9]{3}$"
)


def rounded(value: float) -> float:
    """Round derived decimal values consistently."""
    return round(float(value), 6)


def ratio(numerator: int, denominator: int) -> float | None:
    """Return a bounded ratio or null when no denominator exists."""
    if denominator == 0:
        return None
    return rounded(numerator / denominator)


def require_number(
    value: Any,
    *,
    label: str,
    integer: bool = False,
) -> float | int:
    """Validate a non-negative numeric value."""
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    if integer:
        if not isinstance(value, int):
            raise ValueError(f"{label} must be an integer")
        number: float | int = value
    else:
        if not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be numeric")
        number = value
    if not math.isfinite(float(number)):
        raise ValueError(f"{label} must be finite")
    if float(number) < 0:
        raise ValueError(f"{label} must be non-negative")
    return number


def validate_raw_metrics(raw: Any) -> dict[str, float | int | None]:
    """Validate raw session measurements and cross-field invariants."""
    if not isinstance(raw, dict):
        raise ValueError("raw_metrics must be an object")
    if list(raw) != RAW_METRICS:
        raise ValueError(
            "raw_metrics must preserve the canonical field order"
        )

    validated: dict[str, float | int | None] = {}
    nullable_metrics = {
        "avoidable_rework_minutes",
        "prompt_to_validated_change_minutes",
    }
    for key in RAW_METRICS:
        if key in nullable_metrics and raw[key] is None:
            validated[key] = None
            continue
        validated[key] = require_number(
            raw[key],
            label=f"raw_metrics.{key}",
            integer=key not in nullable_metrics,
        )

    invariants = [
        (
            "commands_failed",
            "commands_executed",
            "commands_failed cannot exceed commands_executed",
        ),
        (
            "commands_retried",
            "commands_executed",
            "commands_retried cannot exceed commands_executed",
        ),
        (
            "phases_first_pass",
            "phases_total",
            "phases_first_pass cannot exceed phases_total",
        ),
        (
            "known_failures_recurred",
            "known_failures_encountered",
            (
                "known_failures_recurred cannot exceed "
                "known_failures_encountered"
            ),
        ),
        (
            "failures_detected_pre_mutation",
            "mutation_opportunities",
            (
                "failures_detected_pre_mutation cannot exceed "
                "mutation_opportunities"
            ),
        ),
        (
            "applicable_lessons_used",
            "applicable_lessons",
            (
                "applicable_lessons_used cannot exceed "
                "applicable_lessons"
            ),
        ),
    ]
    for numerator, denominator, message in invariants:
        if int(validated[numerator]) > int(validated[denominator]):
            raise ValueError(message)
    return validated


def derive_metrics(
    raw: dict[str, float | int],
) -> dict[str, float | None]:
    """Derive rate metrics while preserving all raw measurements."""
    return {
        "first_pass_phase_success_rate": ratio(
            int(raw["phases_first_pass"]),
            int(raw["phases_total"]),
        ),
        "known_failure_recurrence_rate": ratio(
            int(raw["known_failures_recurred"]),
            int(raw["known_failures_encountered"]),
        ),
        "pre_mutation_detection_rate": ratio(
            int(raw["failures_detected_pre_mutation"]),
            int(raw["mutation_opportunities"]),
        ),
        "applicable_lesson_usage_rate": ratio(
            int(raw["applicable_lessons_used"]),
            int(raw["applicable_lessons"]),
        ),
    }


def validate_prediction(item: Any) -> dict[str, Any]:
    # Validate one scalar prediction/actual comparison.
    if not isinstance(item, dict):
        raise ValueError("prediction must be an object")
    if set(item) != PREDICTION_FIELDS:
        raise ValueError(
            "prediction fields must match the canonical contract"
        )

    stage = item["stage"]
    if stage not in STAGES:
        raise ValueError(f"invalid prediction stage: {stage}")

    version = item["version"]
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version < 1
    ):
        raise ValueError("prediction version must be a positive integer")

    for key in ("subject", "unit"):
        if not isinstance(item[key], str) or not item[key]:
            raise ValueError(f"prediction {key} is required")

    confidence = item["confidence"]
    if confidence not in CONFIDENCE_LEVELS:
        raise ValueError(f"invalid prediction confidence: {confidence}")

    numbers: dict[str, float] = {}
    for key in (
        "predicted_point",
        "predicted_min",
        "predicted_max",
    ):
        value = item[key]
        if isinstance(value, bool) or not isinstance(
            value, (int, float)
        ):
            raise ValueError(f"prediction {key} must be numeric")
        if not math.isfinite(float(value)):
            raise ValueError(f"prediction {key} must be finite")
        numbers[key] = float(value)

    actual = item["actual"]
    if actual is not None:
        if isinstance(actual, bool) or not isinstance(
            actual, (int, float)
        ):
            raise ValueError(
                "prediction actual must be numeric or null"
            )
        if not math.isfinite(float(actual)):
            raise ValueError("prediction actual must be finite")

    if numbers["predicted_min"] > numbers["predicted_max"]:
        raise ValueError(
            "predicted_min cannot exceed predicted_max"
        )
    if not (
        numbers["predicted_min"]
        <= numbers["predicted_point"]
        <= numbers["predicted_max"]
    ):
        raise ValueError(
            "predicted_point must be within the prediction range"
        )

    classifications = item["error_classifications"]
    if (
        not isinstance(classifications, list)
        or not all(
            isinstance(value, str) and value
            for value in classifications
        )
        or len(classifications) != len(set(classifications))
    ):
        raise ValueError(
            "error_classifications must be a unique string list"
        )
    unknown = sorted(
        set(classifications) - ERROR_CLASSIFICATIONS
    )
    if unknown:
        raise ValueError(
            f"unknown error classifications: {unknown}"
        )
    return item


def score_prediction(item: dict[str, Any]) -> dict[str, Any]:
    # Score one declared scalar without privileging time.
    validate_prediction(item)

    if item["actual"] is None:
        return {
            "stage": item["stage"],
            "version": item["version"],
            "subject": item["subject"],
            "unit": item["unit"],
            "confidence": item["confidence"],
            "predicted_point": item["predicted_point"],
            "predicted_min": item["predicted_min"],
            "predicted_max": item["predicted_max"],
            "actual": None,
            "range_result": "inconclusive",
            "signed_error": None,
            "absolute_error": None,
            "percentage_error": None,
            "range_distance": None,
            "error_classifications": (
                item["error_classifications"]
            ),
        }

    point = float(item["predicted_point"])
    minimum = float(item["predicted_min"])
    maximum = float(item["predicted_max"])
    actual = float(item["actual"])

    if actual < minimum:
        range_result = "below-range"
        range_distance = minimum - actual
    elif actual > maximum:
        range_result = "above-range"
        range_distance = actual - maximum
    else:
        range_result = "in-range"
        range_distance = 0.0

    signed_error = actual - point
    absolute_error = abs(signed_error)
    percentage_error = (
        None
        if actual == 0
        else rounded((absolute_error / abs(actual)) * 100)
    )

    return {
        "stage": item["stage"],
        "version": item["version"],
        "subject": item["subject"],
        "unit": item["unit"],
        "confidence": item["confidence"],
        "predicted_point": item["predicted_point"],
        "predicted_min": item["predicted_min"],
        "predicted_max": item["predicted_max"],
        "actual": item["actual"],
        "range_result": range_result,
        "signed_error": rounded(signed_error),
        "absolute_error": rounded(absolute_error),
        "percentage_error": percentage_error,
        "range_distance": rounded(range_distance),
        "error_classifications": item["error_classifications"],
    }


def summarize_predictions(
    scores: list[dict[str, Any]],
) -> dict[str, Any]:
    # Summarize conclusive and unavailable scalar comparisons.
    def summarize_bucket(
        bucket: list[dict[str, Any]],
    ) -> dict[str, Any]:
        total = len(bucket)
        conclusive = sum(
            score["range_result"] != "inconclusive"
            for score in bucket
        )
        in_range = sum(
            score["range_result"] == "in-range"
            for score in bucket
        )
        outside_range = conclusive - in_range
        inconclusive = total - conclusive
        return {
            "total": total,
            "conclusive": conclusive,
            "in_range": in_range,
            "outside_range": outside_range,
            "inconclusive": inconclusive,
            "range_hit_rate": ratio(
                in_range,
                conclusive,
            ),
        }

    overall = summarize_bucket(scores)
    by_confidence = {
        level: summarize_bucket(
            [
                score
                for score in scores
                if score["confidence"] == level
            ]
        )
        for level in CONFIDENCE_LEVELS
    }
    return {
        **overall,
        "by_confidence": by_confidence,
    }


def score_session(payload: Any) -> dict[str, Any]:
    """Produce one deterministic session scorecard."""
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")

    expected = {
        "schema_version",
        "session_id",
        "change_id",
        "raw_metrics",
        "predictions",
    }
    if set(payload) != expected:
        raise ValueError(
            "input fields must match the canonical scoring contract"
        )
    if payload["schema_version"] != "1.0":
        raise ValueError("schema_version must be 1.0")
    if not SESSION_ID_RE.fullmatch(
        str(payload["session_id"])
    ):
        raise ValueError("session_id is invalid")
    if not CHANGE_ID_RE.fullmatch(
        str(payload["change_id"])
    ):
        raise ValueError("change_id is invalid")

    raw = validate_raw_metrics(payload["raw_metrics"])
    predictions = payload["predictions"]
    if not isinstance(predictions, list):
        raise ValueError("predictions must be a list")

    scores = [
        score_prediction(item)
        for item in predictions
    ]

    return {
        "schema_version": "1.0",
        "session_id": payload["session_id"],
        "change_id": payload["change_id"],
        "raw_metrics": raw,
        "derived_metrics": derive_metrics(raw),
        "prediction_scores": scores,
        "prediction_summary": summarize_predictions(scores),
    }


def representative_input() -> dict[str, Any]:
    """Return a deterministic self-test input."""
    return {
        "schema_version": "1.0",
        "session_id": "SAGE-SESSION-20260728-001",
        "change_id": "SAGE-CHANGE-20260728-001",
        "raw_metrics": {
            "commands_executed": 20,
            "commands_failed": 2,
            "commands_retried": 1,
            "manual_corrections": 1,
            "phases_total": 5,
            "phases_first_pass": 4,
            "known_failures_encountered": 2,
            "known_failures_recurred": 1,
            "mutation_opportunities": 4,
            "failures_detected_pre_mutation": 3,
            "applicable_lessons": 4,
            "applicable_lessons_used": 3,
            "avoidable_rework_minutes": 30,
            "prompt_to_validated_change_minutes": 180,
        },
        "predictions": [
            {
                "stage": "discovery",
                "version": 1,
                "subject": "active engineering hours",
                "unit": "hours",
                "confidence": "medium",
                "predicted_point": 48,
                "predicted_min": 32,
                "predicted_max": 80,
                "actual": 56,
                "error_classifications": [],
            },
            {
                "stage": "discovery",
                "version": 1,
                "subject": "guardrail failures",
                "unit": "count",
                "confidence": "high",
                "predicted_point": 1,
                "predicted_min": 0,
                "predicted_max": 1,
                "actual": 2,
                "error_classifications": [
                    "range-too-narrow",
                ],
            },
            {
                "stage": "pre-deployment",
                "version": 1,
                "subject": "recurring run-rate delta",
                "unit": "USD/month",
                "confidence": "high",
                "predicted_point": 0,
                "predicted_min": 0,
                "predicted_max": 0,
                "actual": 0,
                "error_classifications": [],
            },
        ],
    }


def self_test() -> list[str]:
    """Run representative and negative scorer tests."""
    failures: list[str] = []

    result = score_session(representative_input())
    expected_derived = {
        "first_pass_phase_success_rate": 0.8,
        "known_failure_recurrence_rate": 0.5,
        "pre_mutation_detection_rate": 0.75,
        "applicable_lesson_usage_rate": 0.75,
    }
    if result["derived_metrics"] != expected_derived:
        failures.append(
            "derived session metrics changed"
        )

    first = result["prediction_scores"][0]
    if (
        first["range_result"] != "in-range"
        or first["signed_error"] != 8.0
        or first["absolute_error"] != 8.0
        or first["percentage_error"] != 14.285714
        or first["range_distance"] != 0.0
    ):
        failures.append(
            "in-range prediction score changed"
        )

    second = result["prediction_scores"][1]
    if (
        second["range_result"] != "above-range"
        or second["range_distance"] != 1.0
    ):
        failures.append(
            "outside-range prediction score changed"
        )

    third = result["prediction_scores"][2]
    if third["percentage_error"] is not None:
        failures.append(
            "zero-actual percentage error must be null"
        )

    summary = result["prediction_summary"]
    if (
        summary["total"] != 3
        or summary["in_range"] != 2
        or summary["range_hit_rate"] != 0.666667
        or summary["by_confidence"]["high"][
            "range_hit_rate"
        ] != 0.5
    ):
        failures.append(
            "prediction summary changed"
        )

    zero_denominators = representative_input()
    for numerator, denominator in (
        ("phases_first_pass", "phases_total"),
        (
            "known_failures_recurred",
            "known_failures_encountered",
        ),
        (
            "failures_detected_pre_mutation",
            "mutation_opportunities",
        ),
        (
            "applicable_lessons_used",
            "applicable_lessons",
        ),
    ):
        zero_denominators["raw_metrics"][numerator] = 0
        zero_denominators["raw_metrics"][denominator] = 0
    zero_result = score_session(zero_denominators)
    if any(
        value is not None
        for value in zero_result["derived_metrics"].values()
    ):
        failures.append(
            "zero denominators must produce null rates"
        )

    unavailable_measurements = representative_input()
    unavailable_measurements["raw_metrics"][
        "avoidable_rework_minutes"
    ] = None
    unavailable_measurements["raw_metrics"][
        "prompt_to_validated_change_minutes"
    ] = None
    unavailable_result = score_session(unavailable_measurements)
    if (
        unavailable_result["raw_metrics"][
            "avoidable_rework_minutes"
        ]
        is not None
        or unavailable_result["raw_metrics"][
            "prompt_to_validated_change_minutes"
        ]
        is not None
    ):
        failures.append(
            "unavailable session measurements must remain null"
        )

    negative_cases: list[tuple[str, dict[str, Any]]] = []

    failed_gt_total = representative_input()
    failed_gt_total["raw_metrics"]["commands_failed"] = 21
    negative_cases.append(
        ("failed commands exceed executed", failed_gt_total)
    )

    point_outside_range = representative_input()
    point_outside_range["predictions"][0][
        "predicted_point"
    ] = 90
    negative_cases.append(
        ("point outside range", point_outside_range)
    )

    duplicate_classification = representative_input()
    duplicate_classification["predictions"][1][
        "error_classifications"
    ] = ["range-too-narrow", "range-too-narrow"]
    negative_cases.append(
        (
            "duplicate error classification",
            duplicate_classification,
        )
    )

    unknown_classification = representative_input()
    unknown_classification["predictions"][1][
        "error_classifications"
    ] = ["unknown-error"]
    negative_cases.append(
        (
            "unknown error classification",
            unknown_classification,
        )
    )

    for label, candidate in negative_cases:
        try:
            score_session(candidate)
        except ValueError:
            continue
        failures.append(
            f"negative scorer test accepted {label}"
        )
    unavailable_actual = representative_input()
    unavailable_actual["predictions"][0]["subject"] = (
        "implementation effort"
    )
    unavailable_actual["predictions"][0]["unit"] = "steps"
    unavailable_actual["predictions"][0]["actual"] = None
    unavailable_result = score_session(unavailable_actual)
    unavailable_score = unavailable_result["prediction_scores"][0]
    unavailable_summary = unavailable_result[
        "prediction_summary"
    ]
    if (
        unavailable_score["subject"] != "implementation effort"
        or unavailable_score["unit"] != "steps"
        or unavailable_score["actual"] is not None
        or unavailable_score["range_result"] != "inconclusive"
        or any(
            unavailable_score[key] is not None
            for key in (
                "signed_error",
                "absolute_error",
                "percentage_error",
                "range_distance",
            )
        )
        or unavailable_summary["total"] != 3
        or unavailable_summary["conclusive"] != 2
        or unavailable_summary["in_range"] != 1
        or unavailable_summary["outside_range"] != 1
        or unavailable_summary["inconclusive"] != 1
        or unavailable_summary["range_hit_rate"] != 0.5
        or unavailable_summary["by_confidence"]["medium"][
            "range_hit_rate"
        ]
        is not None
    ):
        failures.append(
            "scalar-neutral unavailable prediction scoring changed"
        )

    boolean_actual = representative_input()
    boolean_actual["predictions"][0]["actual"] = True
    try:
        score_session(boolean_actual)
    except ValueError:
        pass
    else:
        failures.append(
            "boolean prediction actual was accepted"
        )

    return failures


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Calculate SAGE session metrics and prediction scores"
        )
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    """Run the scorer."""
    args = parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            print("Kalaxy3 SAGE session scoring self-test: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(
            "PASS raw session metrics preserved"
        )
        print(
            "PASS required delivery and learning rates derived"
        )
        print(
            "PASS point and inclusive-range prediction scoring"
        )
        print(
            "PASS scalar-neutral predictions allow unavailable actuals"
        )
        print(
            "PASS zero denominators and zero actuals return null"
        )
        print(
            "PASS unavailable raw measurements remain null"
        )
        print(
            "PASS confidence-bucket range-hit summaries"
        )
        print(
            "PASS session scoring mutation negative tests"
        )
        print(
            "Kalaxy3 SAGE session scoring self-test: PASS"
        )
        return 0

    if args.input is None:
        print("Provide --input FILE or use --self-test.")
        return 2

    try:
        payload = json.loads(
            args.input.read_text(encoding="utf-8")
        )
        scorecard = score_session(payload)
    except (OSError, ValueError, TypeError) as error:
        print(
            "Kalaxy3 SAGE session scoring: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1

    rendered = json.dumps(scorecard, indent=4) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(
            rendered,
            encoding="utf-8",
        )
        print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
