"""Deterministic repository-native SAGE evidence retrieval."""

from __future__ import annotations

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


def extract_records(payload: Any) -> list[Mapping[str, Any]]:
    """Extract identified records from registry container shapes."""
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
    """Score configured fields and explain contributions."""
    score = 0
    matched: set[str] = set()
    reasons: list[str] = []

    for field, weight in policy["field_weights"].items():
        if field == "body":
            text = scalar_text(record)
        else:
            text = key_values(record, FIELD_KEYS.get(field, (field,)))
        overlap = tokenize(text, policy["stopwords"]) & terms
        if not overlap:
            continue
        contribution = len(overlap) * int(weight)
        score += contribution
        matched.update(overlap)
        reasons.append(
            f"{field} matched {', '.join(sorted(overlap))} (+{contribution})"
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
    """Return one candidate or None below the threshold."""
    record_id = identifier(record, source_type, index)
    score, matched, reasons = field_score(record, terms, policy)

    source_weight = int(policy["source_weights"].get(source_type, 0))
    score += source_weight
    reasons.append(f"source type {source_type} (+{source_weight})")

    groups = group_matches(record, active_groups, policy)
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
        "disposition": "pending",
        "disposition_rationale": "",
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
        records = extract_records(load_json(repo / relative))
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
            item["identifier"],
            item["source_path"],
        )
    )
    selected = candidates[: limit or int(policy["default_limit"])]
    for rank, candidate in enumerate(selected, start=1):
        candidate["rank"] = rank

    return {
        "schema_version": "1.0",
        "algorithm_version": policy["algorithm_version"],
        "request": request,
        "policy_sha256": policy_sha256(policy_path),
        "sources": sources,
        "results": selected,
    }


def validate_result(
    payload: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    require_final: bool = False,
) -> None:
    """Validate structure and evidence-use dispositions."""
    required = {
        "schema_version",
        "algorithm_version",
        "request",
        "policy_sha256",
        "sources",
        "results",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise RetrievalError(f"retrieval result missing fields: {missing}")

    allowed = set(policy["allowed_dispositions"])
    for expected_rank, result in enumerate(payload["results"], start=1):
        if result.get("rank") != expected_rank:
            raise RetrievalError("retrieval ranks must be contiguous")
        disposition = result.get("disposition")
        if disposition not in allowed:
            raise RetrievalError(
                f"unsupported disposition: {disposition!r}"
            )
        rationale = str(result.get("disposition_rationale", "")).strip()
        if disposition != "pending" and not rationale:
            raise RetrievalError(
                f"{result.get('identifier')} disposition needs rationale"
            )
        if require_final and disposition == "pending":
            raise RetrievalError(
                f"{result.get('identifier')} disposition is still pending"
            )


def write_result(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one canonical retrieval JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
