"""Deterministic repository-native SAGE evidence retrieval."""

from __future__ import annotations

from datetime import datetime, timezone

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ID_KEYS = (
    "evidence_id",
    "lesson_id",
    "failure_id",
    "action_id",
    "review_id",
    "candidate_id",
    "id",
)
TITLE_KEYS = ("title", "subject", "name", "summary")
FIELD_KEYS = {
    "identifier": ID_KEYS,
    "title": ("title", "name"),
    "subject": ("subject", "subjects"),
    "tags": ("tags", "keywords", "labels", "contexts"),
    "summary": (
        "summary",
        "description",
        "lesson",
        "problem",
        "finding",
        "findings",
        "decision",
        "action",
        "rationale",
    ),
    "status": ("status", "state"),
}


class RetrievalError(RuntimeError):
    """Raised when retrieval violates the repository contract."""


RECONSIDERATION_MUTABLE_FIELDS = frozenset({
    "disposition",
    "disposition_rationale",
    "applicability",
    "value_effect",
    "alternative_effect",
    "augmentations",
    "additional_acceptance_criteria",
    "reconsideration_trigger",
})


def _stable_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def retrieval_basis(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the immutable retrieval basis that an LLM assessment may not rewrite."""
    results: list[dict[str, Any]] = []
    for item in payload.get("results", []):
        if not isinstance(item, Mapping):
            raise RetrievalError("retrieval result entries must be objects")
        results.append({
            key: value
            for key, value in item.items()
            if key not in RECONSIDERATION_MUTABLE_FIELDS
        })
    return {
        "schema_version": payload.get("schema_version"),
        "algorithm_version": payload.get("algorithm_version"),
        "request": payload.get("request"),
        "policy_sha256": payload.get("policy_sha256"),
        "sources": payload.get("sources"),
        "results": results,
    }


def retrieval_basis_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_stable_json_bytes(retrieval_basis(payload))).hexdigest()


def reconsideration_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize finalized evidence participation without manufacturing outcomes."""
    results = [item for item in payload.get("results", []) if isinstance(item, Mapping)]
    final = [item for item in results if item.get("applicability") not in {None, "pending"}]
    return {
        "candidate_count": len(results),
        "assessed_count": len(final),
        "assessment_coverage": (len(final) / len(results)) if results else 1.0,
        "applied_count": sum(item.get("disposition") == "applied" for item in results),
        "contextually_not_applicable_count": sum(
            item.get("applicability") in {
                "contextually-relevant-not-applicable",
                "superseded-for-context",
            }
            for item in results
        ),
        "requires_revalidation_count": sum(
            item.get("applicability") == "requires-revalidation"
            or item.get("value_effect") == "requires-revalidation"
            for item in results
        ),
        "alternative_set_change_count": sum(
            item.get("alternative_effect") not in {None, "pending", "none"}
            for item in results
        ),
        "augmentation_count": sum(len(item.get("augmentations", [])) for item in results),
        "additional_acceptance_criteria_count": sum(
            len(item.get("additional_acceptance_criteria", [])) for item in results
        ),
        "reconsideration_trigger_count": sum(
            bool(str(item.get("reconsideration_trigger", "")).strip()) for item in results
        ),
    }


def requires_contribution_refresh(payload: Mapping[str, Any]) -> bool:
    """Return whether evidence materially changed the candidate contribution."""
    for item in payload.get("results", []):
        if not isinstance(item, Mapping):
            continue
        if item.get("value_effect") in {"redirect", "expand"}:
            return True
        if item.get("alternative_effect") not in {None, "pending", "none"}:
            return True
        if item.get("augmentations") or item.get("additional_acceptance_criteria"):
            return True
    return False


def load_json(path: Path) -> Any:
    """Load one UTF-8 JSON document."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RetrievalError(f"retrieval source missing: {path}") from error
    except json.JSONDecodeError as error:
        raise RetrievalError(f"invalid retrieval JSON: {path}: {error}") from error


def policy_sha256(path: Path) -> str:
    """Return the digest of the exact policy bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar_text(value: Any) -> str:
    """Flatten JSON values into deterministic searchable text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, list):
        return " ".join(scalar_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(
            scalar_text(value[key])
            for key in sorted(value)
        )
    return ""


def key_values(record: Mapping[str, Any], keys: Sequence[str]) -> str:
    """Collect values for matching keys recursively."""
    wanted = set(keys)
    values: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key in sorted(value):
                nested = value[key]
                if key in wanted:
                    values.append(scalar_text(nested))
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(record)
    return " ".join(item for item in values if item)


def looks_like_record(value: Any) -> bool:
    """Return whether a JSON object has a stable record identifier."""
    return isinstance(value, dict) and any(
        key in value and scalar_text(value[key]).strip()
        for key in ID_KEYS
    )


def extract_records(
    payload: Any,
    source_type: str | None = None,
) -> list[Mapping[str, Any]]:
    """Extract records, including the production failure container."""
    if source_type == "failure" and isinstance(payload, dict):
        failures = payload.get("failures")
        if isinstance(failures, dict):
            records: list[Mapping[str, Any]] = []
            for failure_id in sorted(failures):
                value = failures[failure_id]
                if not isinstance(value, dict):
                    continue
                candidate = dict(value)
                candidate.setdefault("failure_id", failure_id)
                candidate.setdefault(
                    "title",
                    str(
                        value.get("attempted_action")
                        or value.get("likely_intended_outcome")
                        or failure_id
                    ),
                )
                candidate.setdefault(
                    "summary",
                    str(
                        value.get("why_invalid")
                        or value.get("repository_gap")
                        or value.get("detected_state")
                        or ""
                    ),
                )
                records.append(candidate)
            return records

    records: list[Mapping[str, Any]] = []

    def visit(value: Any) -> None:
        if looks_like_record(value):
            records.append(value)
            return
        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key])
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return records


def tokenize(text: str, stopwords: Iterable[str]) -> set[str]:
    """Tokenize lower-case terms and remove stopwords."""
    blocked = set(stopwords)
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())
        if len(token) > 1 and token not in blocked
    }


def request_terms(
    request: str,
    policy: Mapping[str, Any],
) -> tuple[set[str], set[str]]:
    """Return literal plus policy-expanded terms and active groups."""
    literal = tokenize(request, policy["stopwords"])
    expanded = set(literal)
    active_groups: set[str] = set()

    for group, members in policy["term_groups"].items():
        member_set = set(members)
        if literal & member_set:
            active_groups.add(group)
            expanded.update(member_set)

    return expanded, active_groups


def identifier(
    record: Mapping[str, Any],
    source_type: str,
    index: int,
) -> str:
    """Return a stable identifier with an explicit fallback."""
    for key in ID_KEYS:
        value = scalar_text(record.get(key)).strip()
        if value:
            return value
    return f"{source_type}-{index:04d}"


def record_title(
    record: Mapping[str, Any],
    fallback: str,
) -> str:
    """Return the first usable title-like value."""
    for key in TITLE_KEYS:
        value = scalar_text(record.get(key)).strip()
        if value:
            return value
    return fallback


def record_path(record: Mapping[str, Any]) -> str:
    """Return an optional repository record path."""
    for key in ("path", "record", "record_path", "file", "source"):
        value = scalar_text(record.get(key)).strip()
        if value:
            return value
    return ""


def record_status(record: Mapping[str, Any]) -> str:
    """Return an optional status value."""
    for key in ("status", "state"):
        value = scalar_text(record.get(key)).strip()
        if value:
            return value
    return ""


def field_score(
    record: Mapping[str, Any],
    terms: set[str],
    policy: Mapping[str, Any],
) -> tuple[int, set[str], list[str]]:
    """Score each matched term once using its strongest configured field."""
    score = 0
    matched: set[str] = set()
    reasons: list[str] = []

    for field, weight in policy["field_weights"].items():
        if field == "body":
            text = scalar_text(record)
        else:
            text = key_values(record, FIELD_KEYS.get(field, (field,)))

        overlap = (
            tokenize(text, policy["stopwords"])
            & terms
            - matched
        )
        if not overlap:
            continue

        contribution = len(overlap) * int(weight)
        score += contribution
        matched.update(overlap)
        reasons.append(
            f"{field} matched {', '.join(sorted(overlap))} "
            f"(+{contribution})"
        )

    return score, matched, reasons


def group_matches(
    record: Mapping[str, Any],
    active_groups: set[str],
    policy: Mapping[str, Any],
) -> set[str]:
    """Return active request groups represented by the record."""
    record_tokens = tokenize(scalar_text(record), policy["stopwords"])
    return {
        group
        for group in active_groups
        if record_tokens & set(policy["term_groups"][group])
    }


def atomic_source_values(
    value: Any,
    path: str,
) -> list[tuple[str, str]]:
    """Flatten exact scalar source values with deterministic JSON paths."""
    if value is None:
        return []
    if isinstance(value, bool):
        return [(path, "true" if value else "false")]
    if isinstance(value, (int, float)):
        return [(path, str(value))]
    if isinstance(value, str):
        return [(path, value)] if value.strip() else []
    if isinstance(value, list):
        values: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            values.extend(
                atomic_source_values(item, f"{path}[{index}]")
            )
        return values
    if isinstance(value, dict):
        values = []
        for key in sorted(value):
            child_path = f"{path}.{key}" if path else key
            values.extend(
                atomic_source_values(value[key], child_path)
            )
        return values
    return []


def fact_field_priority(source_type: str) -> tuple[str, ...]:
    """Return deterministic source-specific fact fields."""
    priorities = {
        "evidence": (
            "summary",
            "primary_subject",
            "status",
            "migration_status",
        ),
        "lesson": (
            "known_resolution",
            "preventive_control",
            "preflight_detection",
            "root_cause",
            "failure_signature",
            "symptoms",
        ),
        "failure": (
            "canonical_recovery",
            "why_invalid",
            "likely_intended_outcome",
            "allowed_actions",
            "confirm_correct_approach",
            "repository_gap",
            "detected_state",
            "prohibited_actions",
        ),
        "improvement_action": (
            "desired_outcome",
            "acceptance_criteria",
            "measurement_plan",
            "current_status",
            "history",
        ),
        "post_session_review": (
            "summary",
            "control_decisions",
            "questions",
            "failures",
            "feedback_planes",
        ),
    }
    return priorities.get(
        source_type,
        ("summary", "title", "status"),
    )


def exact_applicable_facts(
    record: Mapping[str, Any],
    source_type: str,
    terms: set[str],
    policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Select exact source values that overlap the literal request."""
    candidates: list[tuple[int, int, str, str, list[str]]] = []
    seen: set[tuple[str, str]] = set()
    stopwords = policy["stopwords"]

    def consider(
        source_field: str,
        value: Any,
        priority: int,
    ) -> None:
        for path, exact_value in atomic_source_values(
            value,
            source_field,
        ):
            key = (path, exact_value)
            if key in seen:
                continue
            seen.add(key)
            overlap = sorted(
                tokenize(exact_value, stopwords) & terms
            )
            if not overlap:
                continue
            candidates.append(
                (
                    -len(overlap),
                    priority,
                    path,
                    exact_value,
                    overlap,
                )
            )

    for priority, field in enumerate(
        fact_field_priority(source_type)
    ):
        if field in record:
            consider(field, record[field], priority)

    fallback_priority = len(fact_field_priority(source_type)) + 100
    for field in sorted(record):
        consider(field, record[field], fallback_priority)

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
            item[3],
        )
    )
    maximum = int(
        policy.get("quality_fields", {}).get(
            "maximum_applicable_facts",
            5,
        )
    )
    return [
        {
            "source_field": path,
            "value": exact_value,
            "matched_terms": overlap,
        }
        for _, _, path, exact_value, overlap
        in candidates[:maximum]
    ]


def explicit_confidence(
    record: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, str]:
    """Copy explicit confidence without inference."""
    value = scalar_text(record.get("confidence")).strip()
    if value:
        return {
            "value": value,
            "source_field": "confidence",
            "basis": "explicit-source-field",
        }
    missing = str(
        policy.get("quality_fields", {}).get(
            "confidence_missing_value",
            "not-recorded",
        )
    )
    return {
        "value": missing,
        "source_field": "",
        "basis": "not-recorded",
    }


def parse_explicit_date(value: Any) -> datetime | None:
    """Parse an explicit ISO date or timestamp."""
    text = scalar_text(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(
            text.replace("Z", "+00:00")
        )
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def explicit_recency(
    record: Mapping[str, Any],
    source_type: str,
) -> dict[str, str]:
    """Return recency using explicit source-field precedence."""
    preferred = {
        "evidence": (
            "valid_as_of",
            "completed_at",
            "updated_at",
            "created_at",
        ),
        "post_session_review": (
            "recorded_at",
            "updated_at",
            "created_at",
        ),
    }.get(
        source_type,
        (
            "valid_as_of",
            "recorded_at",
            "completed_at",
            "updated_at",
            "created_at",
        ),
    )

    for field in preferred:
        exact_value = scalar_text(record.get(field)).strip()
        if parse_explicit_date(exact_value) is not None:
            return {
                "value": exact_value,
                "source_field": field,
                "basis": "explicit-source-field",
            }

    if source_type == "improvement_action":
        history = record.get("history")
        candidates: list[tuple[datetime, int, str]] = []
        if isinstance(history, list):
            for index, item in enumerate(history):
                if not isinstance(item, dict):
                    continue
                exact_value = scalar_text(
                    item.get("recorded_at")
                ).strip()
                parsed = parse_explicit_date(exact_value)
                if parsed is not None:
                    candidates.append(
                        (parsed, index, exact_value)
                    )
        if candidates:
            _, index, exact_value = max(
                candidates,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                ),
            )
            return {
                "value": exact_value,
                "source_field": (
                    f"history[{index}].recorded_at"
                ),
                "basis": "explicit-source-field",
            }

    return {
        "value": "",
        "source_field": "",
        "basis": "not-recorded",
    }


def recency_sort_value(recency: Mapping[str, Any]) -> float:
    """Return a deterministic numeric tie-break value."""
    if recency.get("basis") != "explicit-source-field":
        return float("-inf")
    parsed = parse_explicit_date(recency.get("value"))
    if parsed is None:
        return float("-inf")
    return parsed.timestamp()


def exact_source_section(
    record: Mapping[str, Any],
    facts: list[dict[str, Any]],
) -> dict[str, str]:
    """Identify the exact record field and navigation location."""
    record_field = (
        str(facts[0]["source_field"])
        if facts
        else ""
    )
    navigation = scalar_text(record.get("nav_section")).strip()
    source_document = scalar_text(
        record.get("source_path")
        or record.get("record_path")
    ).strip()
    return {
        "record_field": record_field,
        "navigation_section": navigation,
        "source_document": source_document,
    }

def score_record(
    record: Mapping[str, Any],
    *,
    source_type: str,
    source_path: str,
    index: int,
    terms: set[str],
    active_groups: set[str],
    policy: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return a relevant ranked candidate or None."""
    record_id = identifier(record, source_type, index)
    base_score, matched, reasons = field_score(record, terms, policy)
    groups = group_matches(record, active_groups, policy)

    minimum_terms = int(policy.get("minimum_matched_terms", 1))
    if len(matched) < minimum_terms:
        return None

    domain_groups = active_groups - {"validation", "evidence"}
    if domain_groups and not (groups & domain_groups):
        return None

    score = base_score
    source_weight = int(policy["source_weights"].get(source_type, 0))
    score += source_weight
    reasons.append(f"source type {source_type} (+{source_weight})")

    if groups:
        bonus = len(groups) * 3
        score += bonus
        reasons.append(
            f"request groups {', '.join(sorted(groups))} (+{bonus})"
        )

    status = record_status(record)
    if status.lower() in set(policy["validated_status_values"]):
        score += 2
        reasons.append(f"validated status {status} (+2)")

    if score < int(policy["minimum_score"]):
        return None

    facts = exact_applicable_facts(
        record,
        source_type,
        terms,
        policy,
    )
    if not facts:
        return None

    confidence = explicit_confidence(record, policy)
    recency = explicit_recency(record, source_type)
    section = exact_source_section(record, facts)

    return {
        "rank": 0,
        "source_type": source_type,
        "identifier": record_id,
        "title": record_title(record, record_id),
        "source_path": source_path,
        "record_path": record_path(record),
        "status": status,
        "score": score,
        "matched_terms": sorted(matched),
        "matched_groups": sorted(groups),
        "reasons": reasons,
        "confidence": confidence,
        "applicable_facts": facts,
        "source_section": section,
        "recency": recency,
        "disposition": "pending",
        "disposition_rationale": "",
        "applicability": "pending",
        "value_effect": "pending",
        "alternative_effect": "pending",
        "augmentations": [],
        "additional_acceptance_criteria": [],
        "reconsideration_trigger": "",
    }


def load_candidates(
    repo: Path,
    policy: Mapping[str, Any],
    terms: set[str],
    active_groups: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load and score configured repository sources."""
    candidates: list[dict[str, Any]] = []
    source_summary: list[dict[str, Any]] = []

    for source in policy["sources"]:
        relative = source["path"]
        source_type = source["source_type"]
        records = extract_records(load_json(repo / relative), source_type)
        source_summary.append(
            {
                "path": relative,
                "source_type": source_type,
                "records_loaded": len(records),
            }
        )
        for index, record in enumerate(records, start=1):
            candidate = score_record(
                record,
                source_type=source_type,
                source_path=relative,
                index=index,
                terms=terms,
                active_groups=active_groups,
                policy=policy,
            )
            if candidate is not None:
                candidates.append(candidate)

    return candidates, source_summary


def retrieve(
    *,
    repo: Path,
    policy_path: Path,
    request: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """Retrieve deterministically ranked repository experience."""
    policy = load_json(policy_path)
    if not request.strip():
        raise RetrievalError("literal retrieval request is required")

    terms, groups = request_terms(request, policy)
    candidates, sources = load_candidates(repo, policy, terms, groups)
    candidates.sort(
        key=lambda item: (
            -int(item["score"]),
            -recency_sort_value(item["recency"]),
            item["identifier"],
            item["source_path"],
        )
    )
    selected = candidates[: limit or int(policy["default_limit"])]
    for rank, candidate in enumerate(selected, start=1):
        candidate["rank"] = rank

    payload = {
        "schema_version": "1.1",
        "algorithm_version": policy["algorithm_version"],
        "request": request,
        "policy_sha256": policy_sha256(policy_path),
        "sources": sources,
        "results": selected,
    }
    payload["retrieval_basis_sha256"] = retrieval_basis_sha256(payload)
    return payload


def validate_result(
    payload: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    require_final: bool = False,
) -> None:
    """Validate structure, quality fields, and dispositions."""
    version = str(payload.get("schema_version", ""))
    if version not in {"1.0", "1.1"}:
        raise RetrievalError(f"unsupported retrieval result schema version: {version!r}")
    required = {
        "schema_version",
        "algorithm_version",
        "request",
        "policy_sha256",
        "sources",
        "results",
    }
    if version == "1.1":
        required.add("retrieval_basis_sha256")
    missing = sorted(required - set(payload))
    if missing:
        raise RetrievalError(
            f"retrieval result missing fields: {missing}"
        )

    if payload.get("algorithm_version") != policy.get(
        "algorithm_version"
    ):
        raise RetrievalError(
            "retrieval algorithm version does not match policy"
        )
    if version == "1.1":
        observed_basis = str(payload.get("retrieval_basis_sha256", ""))
        expected_basis = retrieval_basis_sha256(payload)
        if observed_basis != expected_basis:
            raise RetrievalError(
                "retrieval immutable basis changed during evidence reconsideration"
            )

    allowed = set(policy["allowed_dispositions"])
    reconsideration = policy.get("reconsideration_contract", {})
    applicability_values = set(reconsideration.get("applicability_values", ()))
    value_effect_values = set(reconsideration.get("value_effect_values", ()))
    alternative_effect_values = set(reconsideration.get("alternative_effect_values", ()))
    trigger_required = set(reconsideration.get("reconsideration_trigger_required_for", ()))
    quality_required = {
        "confidence",
        "applicable_facts",
        "source_section",
        "recency",
    }
    for expected_rank, result in enumerate(
        payload["results"],
        start=1,
    ):
        if result.get("rank") != expected_rank:
            raise RetrievalError(
                "retrieval ranks must be contiguous"
            )

        missing_quality = sorted(
            quality_required - set(result)
        )
        if missing_quality:
            raise RetrievalError(
                f"{result.get('identifier')} missing quality fields: "
                f"{missing_quality}"
            )

        confidence = result.get("confidence")
        if not isinstance(confidence, dict):
            raise RetrievalError(
                f"{result.get('identifier')} confidence must be an object"
            )
        confidence_basis = confidence.get("basis")
        if confidence_basis not in {
            "explicit-source-field",
            "not-recorded",
        }:
            raise RetrievalError(
                f"{result.get('identifier')} confidence basis is invalid"
            )
        if (
            confidence_basis == "explicit-source-field"
            and (
                not str(confidence.get("value", "")).strip()
                or confidence.get("source_field") != "confidence"
            )
        ):
            raise RetrievalError(
                f"{result.get('identifier')} explicit confidence "
                "lacks source provenance"
            )
        if (
            confidence_basis == "not-recorded"
            and str(confidence.get("source_field", "")).strip()
        ):
            raise RetrievalError(
                f"{result.get('identifier')} inferred confidence "
                "is prohibited"
            )

        facts = result.get("applicable_facts")
        if not isinstance(facts, list) or not facts:
            raise RetrievalError(
                f"{result.get('identifier')} needs exact applicable facts"
            )
        for fact in facts:
            if not isinstance(fact, dict):
                raise RetrievalError(
                    f"{result.get('identifier')} fact must be an object"
                )
            if (
                not str(fact.get("source_field", "")).strip()
                or not str(fact.get("value", "")).strip()
                or not isinstance(fact.get("matched_terms"), list)
                or not fact.get("matched_terms")
            ):
                raise RetrievalError(
                    f"{result.get('identifier')} fact lacks exact "
                    "source value or request overlap"
                )

        section = result.get("source_section")
        if not isinstance(section, dict):
            raise RetrievalError(
                f"{result.get('identifier')} source section "
                "must be an object"
            )
        if not str(section.get("record_field", "")).strip():
            raise RetrievalError(
                f"{result.get('identifier')} source section "
                "lacks record field"
            )
        if section.get("record_field") != facts[0].get(
            "source_field"
        ):
            raise RetrievalError(
                f"{result.get('identifier')} primary source section "
                "does not match the first exact fact"
            )

        recency = result.get("recency")
        if not isinstance(recency, dict):
            raise RetrievalError(
                f"{result.get('identifier')} recency must be an object"
            )
        recency_basis = recency.get("basis")
        if recency_basis not in {
            "explicit-source-field",
            "not-recorded",
        }:
            raise RetrievalError(
                f"{result.get('identifier')} recency basis is invalid"
            )
        if recency_basis == "explicit-source-field":
            if (
                not str(recency.get("value", "")).strip()
                or not str(
                    recency.get("source_field", "")
                ).strip()
                or parse_explicit_date(
                    recency.get("value")
                ) is None
            ):
                raise RetrievalError(
                    f"{result.get('identifier')} explicit recency "
                    "is invalid"
                )
        elif (
            str(recency.get("value", "")).strip()
            or str(recency.get("source_field", "")).strip()
        ):
            raise RetrievalError(
                f"{result.get('identifier')} inferred recency "
                "is prohibited"
            )

        disposition = result.get("disposition")
        if disposition not in allowed:
            raise RetrievalError(
                f"unsupported disposition: {disposition!r}"
            )
        rationale = str(
            result.get("disposition_rationale", "")
        ).strip()
        if disposition != "pending" and not rationale:
            raise RetrievalError(
                f"{result.get('identifier')} disposition "
                "needs rationale"
            )
        if version == "1.0":
            if require_final and disposition == "pending":
                raise RetrievalError(
                    f"{result.get('identifier')} legacy evidence disposition is still pending"
                )
            continue
        applicability = result.get("applicability")
        value_effect = result.get("value_effect")
        alternative_effect = result.get("alternative_effect")
        if applicability not in applicability_values:
            raise RetrievalError(
                f"{result.get('identifier')} applicability is invalid: {applicability!r}"
            )
        if value_effect not in value_effect_values:
            raise RetrievalError(
                f"{result.get('identifier')} value_effect is invalid: {value_effect!r}"
            )
        if alternative_effect not in alternative_effect_values:
            raise RetrievalError(
                f"{result.get('identifier')} alternative_effect is invalid: {alternative_effect!r}"
            )
        for field in ("augmentations", "additional_acceptance_criteria"):
            values = result.get(field)
            if not isinstance(values, list) or not all(
                isinstance(item, str) and item.strip() for item in values
            ):
                raise RetrievalError(
                    f"{result.get('identifier')} {field} must contain only non-empty strings"
                )
        trigger = str(result.get("reconsideration_trigger", "")).strip()
        if applicability in trigger_required and not trigger:
            raise RetrievalError(
                f"{result.get('identifier')} {applicability} requires a reconsideration trigger"
            )
        if require_final and (
            disposition == "pending"
            or applicability == "pending"
            or value_effect == "pending"
            or alternative_effect == "pending"
        ):
            raise RetrievalError(
                f"{result.get('identifier')} evidence reconsideration is still pending"
            )
        if require_final:
            expected_disposition = None
            if applicability in {"applicable", "partially-applicable"}:
                expected_disposition = "applied"
            elif applicability in {
                "contextually-relevant-not-applicable",
                "superseded-for-context",
            }:
                expected_disposition = "reviewed-not-applicable"
            elif applicability == "requires-revalidation":
                expected_disposition = "requires-revalidation"
            if expected_disposition is not None and disposition != expected_disposition:
                raise RetrievalError(
                    f"{result.get('identifier')} disposition/applicability mismatch: "
                    f"expected={expected_disposition}, observed={disposition}"
                )


def write_result(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one canonical retrieval JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
