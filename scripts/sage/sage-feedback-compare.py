#!/usr/bin/env python3
"""Compare SAGE cost and observability snapshots deterministically."""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
from typing import Any, Final

AFTER_WINDOWS: Final = {
    "immediate",
    "stabilization",
    "trend",
    "economic",
}
MEASUREMENT_TYPES: Final = {
    "measured",
    "allocated",
    "estimated",
    "inferred",
}
CONFIDENCE_RATINGS: Final = {
    "high",
    "medium",
    "low",
}
DIRECTIONS: Final = {
    "lower-is-better",
    "higher-is-better",
    "neutral",
}
PROVENANCE_SOURCE_TYPES: Final = {
    "sage-evidence",
    "kubecost",
    "prometheus",
    "loki",
    "terminal",
    "manual",
}


def require_number(value: Any, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def percentage_change(before: float, after: float) -> float | None:
    if before == 0:
        return None
    return round(((after - before) / abs(before)) * 100, 6)


def number_comparison(before: float, after: float) -> dict[str, Any]:
    delta = after - before
    return {
        "before": before,
        "after": after,
        "delta": round(delta, 6),
        "percentage_change": percentage_change(before, after),
    }


def validate_provenance(items: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError(f"{label} provenance must be non-empty")
    validated: list[dict[str, Any]] = []
    required = {
        "source_type",
        "reference",
        "measurement_type",
        "captured_at",
    }
    for index, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(
                f"{label} provenance item {index} fields invalid"
            )
        if item["source_type"] not in PROVENANCE_SOURCE_TYPES:
            raise ValueError(
                f"{label} provenance source_type invalid"
            )
        if item["measurement_type"] not in MEASUREMENT_TYPES:
            raise ValueError(
                f"{label} provenance measurement_type invalid"
            )
        if not isinstance(item["reference"], str) or not item["reference"]:
            raise ValueError(
                f"{label} provenance reference required"
            )
        if not isinstance(item["captured_at"], str) or not item["captured_at"]:
            raise ValueError(
                f"{label} provenance captured_at required"
            )
        validated.append(copy.deepcopy(item))
    return validated


def validate_cost(cost: Any, label: str) -> dict[str, Any]:
    required = {
        "currency",
        "recurring_run_rate_per_month",
        "one_time_change_cost",
        "avoidable_rework_cost",
        "unit_economics",
        "measurement_type",
        "confidence",
    }
    if not isinstance(cost, dict) or set(cost) != required:
        raise ValueError(f"{label} cost fields invalid")
    currency = cost["currency"]
    if (
        not isinstance(currency, str)
        or len(currency) != 3
        or currency.upper() != currency
    ):
        raise ValueError(f"{label} currency invalid")
    if cost["measurement_type"] not in MEASUREMENT_TYPES:
        raise ValueError(f"{label} measurement_type invalid")
    if cost["confidence"] not in CONFIDENCE_RATINGS:
        raise ValueError(f"{label} confidence invalid")

    unit_economics = cost["unit_economics"]
    if not isinstance(unit_economics, dict) or not unit_economics:
        raise ValueError(f"{label} unit_economics must be non-empty")
    normalized_units: dict[str, dict[str, Any]] = {}
    for key, item in unit_economics.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(item, dict)
            or set(item) != {"value", "unit"}
            or not isinstance(item["unit"], str)
            or not item["unit"]
        ):
            raise ValueError(
                f"{label} unit_economics entry invalid: {key}"
            )
        normalized_units[key] = {
            "value": require_number(
                item["value"],
                f"{label} unit_economics.{key}.value",
            ),
            "unit": item["unit"],
        }

    return {
        "currency": currency,
        "recurring_run_rate_per_month": require_number(
            cost["recurring_run_rate_per_month"],
            f"{label} recurring_run_rate_per_month",
        ),
        "one_time_change_cost": require_number(
            cost["one_time_change_cost"],
            f"{label} one_time_change_cost",
        ),
        "avoidable_rework_cost": require_number(
            cost["avoidable_rework_cost"],
            f"{label} avoidable_rework_cost",
        ),
        "unit_economics": normalized_units,
        "measurement_type": cost["measurement_type"],
        "confidence": cost["confidence"],
    }


def validate_observability(
    metrics: Any,
    label: str,
) -> dict[str, dict[str, Any]]:
    if not isinstance(metrics, dict) or not metrics:
        raise ValueError(
            f"{label} observability_metrics must be non-empty"
        )
    normalized: dict[str, dict[str, Any]] = {}
    for key, item in metrics.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(item, dict)
            or set(item) != {"value", "unit", "direction"}
        ):
            raise ValueError(
                f"{label} observability metric invalid: {key}"
            )
        if not isinstance(item["unit"], str) or not item["unit"]:
            raise ValueError(
                f"{label} observability unit invalid: {key}"
            )
        if item["direction"] not in DIRECTIONS:
            raise ValueError(
                f"{label} observability direction invalid: {key}"
            )
        normalized[key] = {
            "value": require_number(
                item["value"],
                f"{label} observability_metrics.{key}.value",
            ),
            "unit": item["unit"],
            "direction": item["direction"],
        }
    return normalized


def validate_snapshot(
    snapshot: Any,
    label: str,
) -> dict[str, Any]:
    required = {
        "snapshot_id",
        "captured_at",
        "observation_window",
        "cost",
        "observability_metrics",
        "provenance",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != required:
        raise ValueError(f"{label} snapshot fields invalid")
    for key in ("snapshot_id", "captured_at"):
        if not isinstance(snapshot[key], str) or not snapshot[key]:
            raise ValueError(f"{label} {key} required")
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "captured_at": snapshot["captured_at"],
        "observation_window": snapshot["observation_window"],
        "cost": validate_cost(snapshot["cost"], label),
        "observability_metrics": validate_observability(
            snapshot["observability_metrics"],
            label,
        ),
        "provenance": validate_provenance(
            snapshot["provenance"],
            label,
        ),
    }


def metric_result(direction: str, delta: float) -> str:
    if delta == 0:
        return "unchanged"
    if direction == "neutral":
        return "neutral"
    if direction == "lower-is-better":
        return "improved" if delta < 0 else "regressed"
    return "improved" if delta > 0 else "regressed"


def compare(payload: Any) -> dict[str, Any]:
    required = {
        "schema_version",
        "comparison_id",
        "change_id",
        "baseline",
        "after",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("comparison input fields invalid")
    if payload["schema_version"] != "1.0":
        raise ValueError("schema_version must be 1.0")
    for key in ("comparison_id", "change_id"):
        if not isinstance(payload[key], str) or not payload[key]:
            raise ValueError(f"{key} required")

    baseline = validate_snapshot(payload["baseline"], "baseline")
    after = validate_snapshot(payload["after"], "after")

    if baseline["observation_window"] != "baseline":
        raise ValueError(
            "baseline observation_window must be baseline"
        )
    if after["observation_window"] not in AFTER_WINDOWS:
        raise ValueError(
            "after observation_window must be immediate, "
            "stabilization, trend, or economic"
        )

    before_cost = baseline["cost"]
    after_cost = after["cost"]
    if before_cost["currency"] != after_cost["currency"]:
        raise ValueError("baseline and after currency must match")
    if set(before_cost["unit_economics"]) != set(
        after_cost["unit_economics"]
    ):
        raise ValueError(
            "baseline and after unit-economic metrics must match"
        )

    unit_economics: dict[str, Any] = {}
    for key in sorted(before_cost["unit_economics"]):
        before_item = before_cost["unit_economics"][key]
        after_item = after_cost["unit_economics"][key]
        if before_item["unit"] != after_item["unit"]:
            raise ValueError(
                f"unit-economic unit mismatch: {key}"
            )
        comparison = number_comparison(
            before_item["value"],
            after_item["value"],
        )
        comparison["unit"] = before_item["unit"]
        unit_economics[key] = comparison

    before_metrics = baseline["observability_metrics"]
    after_metrics = after["observability_metrics"]
    if set(before_metrics) != set(after_metrics):
        raise ValueError(
            "baseline and after observability metrics must match"
        )

    observability_metrics: dict[str, Any] = {}
    for key in sorted(before_metrics):
        before_item = before_metrics[key]
        after_item = after_metrics[key]
        if before_item["unit"] != after_item["unit"]:
            raise ValueError(
                f"observability unit mismatch: {key}"
            )
        if before_item["direction"] != after_item["direction"]:
            raise ValueError(
                f"observability direction mismatch: {key}"
            )
        comparison = number_comparison(
            before_item["value"],
            after_item["value"],
        )
        comparison["unit"] = before_item["unit"]
        comparison["direction"] = before_item["direction"]
        comparison["result"] = metric_result(
            before_item["direction"],
            comparison["delta"],
        )
        observability_metrics[key] = comparison

    return {
        "schema_version": "1.0",
        "comparison_id": payload["comparison_id"],
        "change_id": payload["change_id"],
        "baseline_snapshot_id": baseline["snapshot_id"],
        "after_snapshot_id": after["snapshot_id"],
        "observation_window": after["observation_window"],
        "cost_comparison": {
            "currency": before_cost["currency"],
            "recurring_run_rate_per_month": number_comparison(
                before_cost["recurring_run_rate_per_month"],
                after_cost["recurring_run_rate_per_month"],
            ),
            "one_time_change_cost": (
                after_cost["one_time_change_cost"]
            ),
            "avoidable_rework_cost": number_comparison(
                before_cost["avoidable_rework_cost"],
                after_cost["avoidable_rework_cost"],
            ),
            "unit_economics": unit_economics,
            "measurement_types": {
                "baseline": before_cost["measurement_type"],
                "after": after_cost["measurement_type"],
            },
            "confidence": {
                "baseline": before_cost["confidence"],
                "after": after_cost["confidence"],
            },
        },
        "observability_comparison": {
            "baseline_window": "baseline",
            "after_window": after["observation_window"],
            "metrics": observability_metrics,
        },
        "provenance": {
            "baseline": baseline["provenance"],
            "after": after["provenance"],
        },
    }


def representative_input() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "comparison_id": "SAGE-FEEDBACK-20260728-001",
        "change_id": "SAGE-CHANGE-20260728-001",
        "baseline": {
            "snapshot_id": "baseline-001",
            "captured_at": "2026-07-28T20:00:00-05:00",
            "observation_window": "baseline",
            "cost": {
                "currency": "USD",
                "recurring_run_rate_per_month": 100,
                "one_time_change_cost": 0,
                "avoidable_rework_cost": 40,
                "unit_economics": {
                    "cost_per_validated_change": {
                        "value": 10,
                        "unit": "USD/change",
                    }
                },
                "measurement_type": "measured",
                "confidence": "high",
            },
            "observability_metrics": {
                "error_rate": {
                    "value": 0.05,
                    "unit": "ratio",
                    "direction": "lower-is-better",
                },
                "availability": {
                    "value": 0.99,
                    "unit": "ratio",
                    "direction": "higher-is-better",
                },
                "throughput": {
                    "value": 20,
                    "unit": "changes/month",
                    "direction": "neutral",
                },
            },
            "provenance": [
                {
                    "source_type": "kubecost",
                    "reference": "SAGE-K3-FINOPS-20260724-001",
                    "measurement_type": "measured",
                    "captured_at": "2026-07-28T20:00:00-05:00",
                }
            ],
        },
        "after": {
            "snapshot_id": "trend-001",
            "captured_at": "2026-07-28T22:00:00-05:00",
            "observation_window": "trend",
            "cost": {
                "currency": "USD",
                "recurring_run_rate_per_month": 90,
                "one_time_change_cost": 250,
                "avoidable_rework_cost": 20,
                "unit_economics": {
                    "cost_per_validated_change": {
                        "value": 8,
                        "unit": "USD/change",
                    }
                },
                "measurement_type": "measured",
                "confidence": "high",
            },
            "observability_metrics": {
                "error_rate": {
                    "value": 0.02,
                    "unit": "ratio",
                    "direction": "lower-is-better",
                },
                "availability": {
                    "value": 0.995,
                    "unit": "ratio",
                    "direction": "higher-is-better",
                },
                "throughput": {
                    "value": 25,
                    "unit": "changes/month",
                    "direction": "neutral",
                },
            },
            "provenance": [
                {
                    "source_type": "prometheus",
                    "reference": "SAGE-K3-OBS-20260728-003",
                    "measurement_type": "measured",
                    "captured_at": "2026-07-28T22:00:00-05:00",
                }
            ],
        },
    }


def run_self_tests() -> list[str]:
    failures: list[str] = []
    result = compare(representative_input())

    recurring = result["cost_comparison"][
        "recurring_run_rate_per_month"
    ]
    if recurring["delta"] != -10 or recurring[
        "percentage_change"
    ] != -10:
        failures.append("recurring run-rate comparison changed")

    if result["cost_comparison"][
        "one_time_change_cost"
    ] != 250:
        failures.append("one-time change cost changed")

    unit = result["cost_comparison"]["unit_economics"][
        "cost_per_validated_change"
    ]
    if unit["delta"] != -2 or unit[
        "percentage_change"
    ] != -20:
        failures.append("unit-economics comparison changed")

    metrics = result["observability_comparison"]["metrics"]
    if metrics["error_rate"]["result"] != "improved":
        failures.append("lower-is-better result changed")
    if metrics["availability"]["result"] != "improved":
        failures.append("higher-is-better result changed")
    if metrics["throughput"]["result"] != "neutral":
        failures.append("neutral result changed")

    zero = representative_input()
    zero["baseline"]["cost"][
        "recurring_run_rate_per_month"
    ] = 0
    zero_result = compare(zero)
    if zero_result["cost_comparison"][
        "recurring_run_rate_per_month"
    ]["percentage_change"] is not None:
        failures.append(
            "zero baseline percentage must remain null"
        )

    cases: list[tuple[str, dict[str, Any]]] = []

    currency = representative_input()
    currency["after"]["cost"]["currency"] = "EUR"
    cases.append(("currency mismatch", currency))

    metric = representative_input()
    del metric["after"]["observability_metrics"]["throughput"]
    cases.append(("metric-set mismatch", metric))

    direction = representative_input()
    direction["after"]["observability_metrics"][
        "error_rate"
    ]["direction"] = "higher-is-better"
    cases.append(("direction mismatch", direction))

    window = representative_input()
    window["after"]["observation_window"] = "baseline"
    cases.append(("invalid after window", window))

    no_provenance = representative_input()
    no_provenance["after"]["provenance"] = []
    cases.append(("missing provenance", no_provenance))

    for label, candidate in cases:
        try:
            compare(candidate)
        except ValueError:
            continue
        failures.append(f"negative test accepted {label}")

    if "composite_score" in result:
        failures.append("composite score must remain absent")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare SAGE cost and observability snapshots"
    )
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        failures = run_self_tests()
        if failures:
            print("Kalaxy3 SAGE feedback comparison self-test: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS recurring and one-time cost comparisons")
        print("PASS unit-economics and avoidable-rework comparisons")
        print("PASS observability direction and window comparisons")
        print("PASS provenance and measurement types preserved")
        print("PASS zero-baseline percentages remain null")
        print("PASS comparison mutation negative tests")
        print(
            "Kalaxy3 SAGE feedback comparison self-test: PASS"
        )
        return 0

    if args.input is None or args.output is None:
        print("Provide --input and --output, or use --self-test.")
        return 2

    try:
        payload = json.loads(
            args.input.read_text(encoding="utf-8")
        )
        result = compare(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=4) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, TypeError) as error:
        print(f"Kalaxy3 SAGE feedback comparison: FAIL: {error}")
        return 1

    print(f"WROTE {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
