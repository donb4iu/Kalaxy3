#!/usr/bin/env python3
"""Deterministic SAGE implementation-readiness contract for fresh cognition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

DISPOSITIONS = (
    "implementation-ready",
    "knowledge-evidence-capability-gap",
    "material-decision-required",
    "unsupported",
)
REQUIRED_FIELDS = {
    "disposition",
    "rationale",
    "evidence_references",
    "repository_grounding",
    "model_inference",
    "assumptions",
    "dependencies",
    "implementation_recipe",
    "validation",
    "blocking_unknowns",
    "gap_closure",
    "alternatives",
    "limitations",
    "stop_conditions",
    "material_decision_required",
}


class ReadinessError(ValueError):
    """Raised when advisory readiness cannot satisfy the governed contract."""


def stable_json(value: Any) -> str:
    """Render deterministic JSON for identity binding."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value: str) -> str:
    """Hash literal UTF-8 text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    """Hash one file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string_list(payload: Mapping[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ReadinessError(f"readiness.{field} must be a list of strings")
    return list(value)


def _validate_grounding(
    value: object,
    repo: Path | None,
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ReadinessError("readiness.repository_grounding must be a list")
    records: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ReadinessError(
                f"readiness.repository_grounding[{index}] must be an object"
            )
        path = item.get("path")
        digest = item.get("sha256")
        if not isinstance(path, str) or not path.strip():
            raise ReadinessError(
                f"readiness.repository_grounding[{index}].path is required"
            )
        if digest is not None and (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest.lower())
        ):
            raise ReadinessError(
                f"readiness.repository_grounding[{index}].sha256 is invalid"
            )
        record = {"path": path.strip()}
        if isinstance(digest, str):
            record["sha256"] = digest.lower()
        if repo is not None:
            target = (repo / path).resolve()
            try:
                target.relative_to(repo.resolve())
            except ValueError as error:
                raise ReadinessError(
                    f"readiness repository path escapes repository: {path}"
                ) from error
            if not target.is_file():
                raise ReadinessError(
                    f"readiness repository grounding does not exist: {path}"
                )
            if digest is not None and sha256_file(target) != digest.lower():
                raise ReadinessError(
                    f"readiness repository grounding digest changed: {path}"
                )
        records.append(record)
    return records


def validate_readiness_payload(
    payload: Mapping[str, Any],
    repo: Path | None = None,
) -> dict[str, Any]:
    """Validate cognition and derive no semantics that the model can assert itself."""
    if set(payload) != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(payload))
        extra = sorted(set(payload) - REQUIRED_FIELDS)
        raise ReadinessError(
            f"readiness fields are invalid: missing={missing} extra={extra}"
        )
    disposition = payload.get("disposition")
    if disposition not in DISPOSITIONS:
        raise ReadinessError("readiness disposition is invalid")
    rationale = payload.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ReadinessError("readiness.rationale is required")
    material = payload.get("material_decision_required")
    if not isinstance(material, bool):
        raise ReadinessError("readiness.material_decision_required must be boolean")

    result = dict(payload)
    for field in (
        "evidence_references",
        "model_inference",
        "assumptions",
        "dependencies",
        "implementation_recipe",
        "validation",
        "blocking_unknowns",
        "gap_closure",
        "alternatives",
        "limitations",
        "stop_conditions",
    ):
        result[field] = _string_list(payload, field)
    result["repository_grounding"] = _validate_grounding(
        payload.get("repository_grounding"), repo
    )

    recipe = result["implementation_recipe"]
    validation = result["validation"]
    blockers = result["blocking_unknowns"]
    closure = result["gap_closure"]
    alternatives = result["alternatives"]
    grounding = result["repository_grounding"]
    evidence = result["evidence_references"]
    stop_conditions = result["stop_conditions"]

    if disposition == "implementation-ready":
        if material:
            raise ReadinessError(
                "implementation-ready cannot require a material Architect decision"
            )
        if blockers:
            raise ReadinessError(
                "implementation-ready cannot contain blocking unknowns"
            )
        if closure:
            raise ReadinessError(
                "implementation-ready cannot contain gap-closure work"
            )
        if not recipe or not validation:
            raise ReadinessError(
                "implementation-ready requires a concrete recipe and validation"
            )
        if not evidence and not grounding:
            raise ReadinessError(
                "implementation-ready requires evidence or repository grounding"
            )
    elif disposition == "knowledge-evidence-capability-gap":
        if material:
            raise ReadinessError(
                "knowledge-evidence-capability-gap cannot claim a material decision"
            )
        if recipe:
            raise ReadinessError(
                "knowledge-evidence-capability-gap cannot carry an implementation recipe"
            )
        if not blockers or not closure:
            raise ReadinessError(
                "knowledge-evidence-capability-gap requires blockers and gap closure"
            )
    elif disposition == "material-decision-required":
        if not material:
            raise ReadinessError(
                "material-decision-required must set material_decision_required=true"
            )
        if recipe:
            raise ReadinessError(
                "material-decision-required cannot select an implementation recipe"
            )
        if len(alternatives) < 2:
            raise ReadinessError(
                "material-decision-required requires at least two credible alternatives"
            )
    else:
        if material:
            raise ReadinessError("unsupported cannot claim a material decision")
        if recipe:
            raise ReadinessError("unsupported cannot carry an implementation recipe")
        if not blockers or not stop_conditions:
            raise ReadinessError(
                "unsupported requires the unsupported reason and stop conditions"
            )
    return result


def _derived(disposition: str) -> tuple[str, str]:
    mapping = {
        "implementation-ready": (
            "implementation-ready",
            "fresh-first-candidate-generation",
        ),
        "knowledge-evidence-capability-gap": (
            "knowledge-evidence-capability-gap",
            "persistent-collaborator-gap-closure",
        ),
        "material-decision-required": (
            "material-decision-required",
            "architect-decision",
        ),
        "unsupported": ("unsupported", "stop-unsupported"),
    }
    return mapping[disposition]


def build_readiness_record(
    advisory: Mapping[str, Any],
    *,
    request_sha256: str,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Validate fresh cognition and derive SAGE-owned transition semantics."""
    readiness = advisory.get("readiness")
    if not isinstance(readiness, Mapping):
        raise ReadinessError("fresh advisory readiness object is missing")
    validated = validate_readiness_payload(readiness, repo)
    status, next_boundary = _derived(str(validated["disposition"]))
    return {
        "schema_version": "1.0",
        "record_type": "sage-implementation-readiness",
        "authority": "advisory-cognition-deterministically-validated",
        "request_sha256": request_sha256,
        "source_decision": advisory.get("decision"),
        "disposition": validated["disposition"],
        "readiness": validated,
        "status": status,
        "next_boundary": next_boundary,
    }


def load_readiness_record(
    path: Path,
    repo: Path,
    request: str,
) -> dict[str, Any]:
    """Load and revalidate a readiness record at the first-candidate boundary."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ReadinessError("readiness record must be an object")
    if payload.get("record_type") != "sage-implementation-readiness":
        raise ReadinessError("readiness record_type is invalid")
    expected_request = sha256_text(request)
    if payload.get("request_sha256") != expected_request:
        raise ReadinessError("readiness request identity changed")
    readiness = payload.get("readiness")
    if not isinstance(readiness, Mapping):
        raise ReadinessError("readiness record payload is missing")
    validated = validate_readiness_payload(readiness, repo)
    status, next_boundary = _derived(str(validated["disposition"]))
    if payload.get("status") != status or payload.get("next_boundary") != next_boundary:
        raise ReadinessError("readiness derived transition semantics changed")
    result = dict(payload)
    result["readiness"] = validated
    return result


def require_implementation_ready(
    path: Path,
    repo: Path,
    request: str,
) -> dict[str, Any]:
    """Fail closed unless the bound request is explicitly implementation-ready."""
    record = load_readiness_record(path, repo, request)
    if record.get("disposition") != "implementation-ready":
        raise ReadinessError(
            "first-candidate generation requires disposition=implementation-ready"
        )
    return record
