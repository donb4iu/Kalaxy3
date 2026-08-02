"""Semantic outcome metrics and comparable trend construction."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


RAW_FIELDS = (
    "workflows_started", "workflows_completed", "first_pass_completions",
    "semantic_validations", "semantic_false_passes", "commands_executed",
    "commands_failed", "commands_retried", "manual_corrections",
    "operator_interventions", "authority_checks", "authority_failures",
    "component_candidates_considered", "components_selected", "components_reused",
    "new_components_created", "component_contract_mismatches",
    "direct_execution_violations", "known_failures_encountered",
    "known_failures_recurred", "mutation_opportunities",
    "failures_detected_pre_mutation", "authoritative_repository_git_mutations",
    "disposable_fixture_git_mutations", "github_mutations", "deployment_mutations",
    "avoidable_rework_minutes", "prompt_to_validated_change_minutes",
)

DERIVED_FIELDS = (
    "first_pass_completion_rate", "semantic_false_pass_rate",
    "component_reuse_ratio", "authority_failure_rate",
    "known_failure_recurrence_rate", "pre_mutation_detection_rate",
    "manual_correction_rate", "operator_intervention_rate",
)

DIRECTIONS = {"higher-is-better", "lower-is-better", "neutral"}


def _number(value: Any, field: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be a nonnegative number or null")
    if value < 0:
        raise ValueError(f"{field} must be nonnegative")
    return value


def _subset_ratio(numerator: float | int | None, denominator: float | int | None, label: str) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    if numerator > denominator:
        raise ValueError(f"{label} numerator exceeds denominator")
    return numerator / denominator


def _activity_share(count: float | int | None, commands: float | int | None) -> float | None:
    if count is None or commands is None:
        return None
    denominator = count + commands
    if denominator == 0:
        return None
    return count / denominator


class OutcomeMetrics:
    """Build schema 1.0 reports from explicit raw measurements only."""

    @staticmethod
    def validate_raw(raw_metrics: Mapping[str, Any]) -> dict[str, float | int | None]:
        observed = set(raw_metrics)
        expected = set(RAW_FIELDS)
        if observed != expected:
            missing = sorted(expected - observed)
            extra = sorted(observed - expected)
            raise ValueError(f"raw metric fields mismatch; missing={missing}; extra={extra}")
        return {field: _number(raw_metrics[field], field) for field in RAW_FIELDS}

    @classmethod
    def derive(cls, raw_metrics: Mapping[str, Any]) -> dict[str, float | None]:
        raw = cls.validate_raw(raw_metrics)
        return {
            "first_pass_completion_rate": _subset_ratio(raw["first_pass_completions"], raw["workflows_completed"], "first_pass_completion_rate"),
            "semantic_false_pass_rate": _subset_ratio(raw["semantic_false_passes"], raw["semantic_validations"], "semantic_false_pass_rate"),
            "component_reuse_ratio": _subset_ratio(raw["components_reused"], raw["components_selected"], "component_reuse_ratio"),
            "authority_failure_rate": _subset_ratio(raw["authority_failures"], raw["authority_checks"], "authority_failure_rate"),
            "known_failure_recurrence_rate": _subset_ratio(raw["known_failures_recurred"], raw["known_failures_encountered"], "known_failure_recurrence_rate"),
            "pre_mutation_detection_rate": _subset_ratio(raw["failures_detected_pre_mutation"], raw["mutation_opportunities"], "pre_mutation_detection_rate"),
            "manual_correction_rate": _activity_share(raw["manual_corrections"], raw["commands_executed"]),
            "operator_intervention_rate": _activity_share(raw["operator_interventions"], raw["commands_executed"]),
        }

    @staticmethod
    def trend(*, metric: str, current_report: Mapping[str, Any], baseline_report: Mapping[str, Any], direction: str, comparability_basis: str) -> dict[str, Any]:
        if metric not in DERIVED_FIELDS:
            raise ValueError(f"unsupported derived metric: {metric}")
        if direction not in DIRECTIONS:
            raise ValueError(f"unsupported trend direction: {direction}")
        if not comparability_basis:
            raise ValueError("comparability_basis is required")
        if current_report.get("workflow_class") != baseline_report.get("workflow_class"):
            raise ValueError("trend reports must have the same workflow_class")
        current = current_report.get("derived_metrics", {}).get(metric)
        baseline = baseline_report.get("derived_metrics", {}).get(metric)
        if current is None or baseline is None:
            result = "inconclusive"
        elif current == baseline or direction == "neutral":
            result = "unchanged"
        elif (direction == "higher-is-better" and current > baseline) or (direction == "lower-is-better" and current < baseline):
            result = "improved"
        else:
            result = "regressed"
        return {
            "metric": metric,
            "baseline_report": str(baseline_report.get("report_id", "unknown")),
            "current_value": current,
            "baseline_value": baseline,
            "direction": direction,
            "result": result,
            "comparability_basis": comparability_basis,
        }

    @classmethod
    def build_report(cls, *, report_id: str, captured_at: str, period: Mapping[str, str], workflow_class: str, raw_metrics: Mapping[str, Any], provenance: Iterable[Mapping[str, Any]], limitations: Iterable[str], trends: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
        if not report_id.startswith("SAGE-METRICS-"):
            raise ValueError("report_id must use the SAGE-METRICS namespace")
        if not captured_at or not workflow_class:
            raise ValueError("captured_at and workflow_class are required")
        if not period.get("started_at") or not period.get("completed_at"):
            raise ValueError("period requires started_at and completed_at")
        provenance_items = [dict(item) for item in provenance]
        limitation_items = [item for item in limitations if item]
        if not provenance_items or not limitation_items:
            raise ValueError("provenance and at least one limitation are required")
        raw = cls.validate_raw(raw_metrics)
        derived = cls.derive(raw)
        trend_items = [dict(item) for item in trends]
        for item in trend_items:
            required = {"metric", "baseline_report", "current_value", "baseline_value", "direction", "result", "comparability_basis"}
            if set(item) != required:
                raise ValueError("trend fields do not match schema 1.0")
        return {
            "schema_version": "1.0",
            "report_id": report_id,
            "captured_at": captured_at,
            "period": dict(period),
            "workflow_class": workflow_class,
            "raw_metrics": raw,
            "derived_metrics": derived,
            "trends": trend_items,
            "provenance": provenance_items,
            "limitations": limitation_items,
            "composite_score_enabled": False,
        }
