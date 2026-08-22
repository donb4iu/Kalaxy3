"""Structured failure diagnosis before another corrective mutation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


POST_RETRIEVAL_GOVERNING_CONDITIONS = (
    "authority",
    "scope",
    "required_capability",
    "safety_requirements",
    "repository_owned_composition",
    "approval_or_mutation_boundaries",
)


def classify_post_retrieval_continuation(
    *,
    retrieval_performed: bool,
    attempted_action_authorized: bool,
    governing_changes: Mapping[str, bool],
) -> dict[str, Any]:
    """Classify corrective retry versus governance re-entry deterministically."""

    if retrieval_performed is not True:
        raise ValueError("Post-retrieval continuation requires completed failure retrieval")
    if set(governing_changes) != set(POST_RETRIEVAL_GOVERNING_CONDITIONS):
        raise ValueError("Post-retrieval governing-condition fields are invalid")
    if any(not isinstance(value, bool) for value in governing_changes.values()):
        raise ValueError("Post-retrieval governing-condition values must be boolean")
    if not isinstance(attempted_action_authorized, bool):
        raise ValueError("Post-retrieval attempted-action authorization must be boolean")

    changed = [
        name for name in POST_RETRIEVAL_GOVERNING_CONDITIONS
        if governing_changes[name]
    ]
    if not attempted_action_authorized:
        disposition = "governance-reentry"
        required_boundary = "authority"
        reason = "The attempted action is no longer authorized."
    elif not changed:
        disposition = "implementation-local-retry"
        required_boundary = "implementation-local"
        reason = (
            "Authority, scope, required capability, safety requirements, "
            "repository-owned composition, and approval or mutation boundaries "
            "are unchanged."
        )
    elif "authority" in changed:
        disposition = "governance-reentry"
        required_boundary = "authority"
        reason = "Repository or execution authority changed."
    elif any(
        name in changed
        for name in ("scope", "safety_requirements", "approval_or_mutation_boundaries")
    ):
        disposition = "governance-reentry"
        required_boundary = "semantic-confirmation"
        reason = "A semantic, safety, or approval-boundary condition changed."
    else:
        disposition = "governance-reentry"
        required_boundary = "planning"
        reason = "Required capability or repository-owned composition changed."

    return {
        "schema_version": "1.0",
        "record_type": "sage-post-retrieval-continuation-decision",
        "retrieval_performed": True,
        "attempted_action_authorized": attempted_action_authorized,
        "governing_conditions": dict(governing_changes),
        "changed_conditions": changed,
        "disposition": disposition,
        "required_reentry_boundary": required_boundary,
        "reason": reason,
    }


def require_post_retrieval_boundary(
    decision: Mapping[str, Any],
    requested_boundary: str,
) -> None:
    """Fail closed when a corrective path does not match the classified boundary."""

    required = decision.get("required_reentry_boundary")
    if requested_boundary != required:
        raise ValueError(
            "Post-retrieval continuation boundary mismatch: "
            f"required={required}, requested={requested_boundary}"
        )


class FailureDiagnoser:
    """Record expected and actual paths, ownership, recurrence, and correction."""

    @staticmethod
    def diagnose(
        *,
        diagnosis_id: str,
        failure_id: str,
        attempted_action: str,
        what_failed: str,
        direct_evidence: Iterable[Mapping[str, Any]],
        actual_path: Mapping[str, Any],
        expected_path: Mapping[str, Any],
        why_actual_path_differed: str,
        ownership: str,
        mutation_effect: Mapping[str, Any],
        lesson_use: Mapping[str, Any],
        previous_failure_references: Iterable[str],
        avoidable_rework_minutes: float | None,
        correction: Mapping[str, Any],
        evidence_references: Iterable[str],
        recorded_at: str | None = None,
    ) -> dict[str, Any]:
        evidence = [dict(item) for item in direct_evidence]
        if not evidence:
            raise ValueError("Direct failure evidence is required")
        for label, path in (("actual_path", actual_path), ("expected_path", expected_path)):
            for field in ("component_id", "component_version", "source_path", "description"):
                if not path.get(field):
                    raise ValueError(f"{label}.{field} is required")
        if not why_actual_path_differed:
            raise ValueError("The divergence reason is required")
        if ownership not in {"primitive", "composition", "policy", "authority", "environment", "operator", "external-dependency"}:
            raise ValueError(f"Unsupported failure ownership: {ownership}")
        previous = list(dict.fromkeys(previous_failure_references))
        recurred = bool(previous)
        disposition = correction.get("disposition")
        if disposition not in {"create-control", "update-primitive", "update-composition", "update-policy", "update-authority", "environment-repair", "operator-correction", "no-action"}:
            raise ValueError("Correction disposition is invalid")
        if not correction.get("reusable_correction"):
            raise ValueError("Reusable correction is required")
        if disposition == "no-action" and not correction.get("no_action_rationale"):
            raise ValueError("No-action decisions require evidence-backed rationale")
        if recurred and not (correction.get("regression_test_required") or correction.get("action_reference")):
            raise ValueError("A recurrence requires a regression control or improvement action")
        applicable = lesson_use.get("applicable_lesson_ids", [])
        surfaced = lesson_use.get("surfaced_lesson_ids", [])
        used = lesson_use.get("used_lesson_ids", [])
        if lesson_use.get("retrieval_performed") is not True:
            raise ValueError("Failure-triggered lesson retrieval is required")
        if set(used) - set(surfaced):
            raise ValueError("Used lessons must have been surfaced")
        if set(surfaced) - set(applicable):
            raise ValueError("Surfaced lessons must be applicable")
        return {
            "schema_version": "1.0",
            "diagnosis_id": diagnosis_id,
            "failure_id": failure_id,
            "recorded_at": recorded_at or _now(),
            "attempted_action": attempted_action,
            "what_failed": what_failed,
            "direct_evidence": evidence,
            "classification": "known" if recurred else "new",
            "actual_path": dict(actual_path),
            "expected_path": dict(expected_path),
            "divergence": {
                "why_actual_path_differed": why_actual_path_differed,
                "selection_failure": actual_path.get("component_id") != expected_path.get("component_id"),
                "authority_failure": bool(correction.get("authority_failure", False)),
                "contract_mismatch": bool(correction.get("contract_mismatch", False)),
            },
            "ownership": ownership,
            "mutation_effect": dict(mutation_effect),
            "lesson_use": dict(lesson_use),
            "recurrence": {
                "recurred": recurred,
                "previous_failure_references": previous,
                "avoidable_rework_minutes": avoidable_rework_minutes,
            },
            "correction": dict(correction),
            "evidence_references": list(dict.fromkeys(evidence_references)),
        }
