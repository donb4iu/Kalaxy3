"""Federated authority reconciliation for governed SAGE changes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

_ALLOWED_AUTHORITY_TYPES = {
    "operator-intent",
    "git",
    "github",
    "repository-policy",
    "sage",
    "runtime",
    "telemetry",
    "economics",
    "external-contract",
}
_ALLOWED_FRESHNESS = {"current", "stale", "unknown", "not-applicable"}
_ALLOWED_MEASUREMENT_TYPES = {"measured", "declared", "inferred", "unavailable"}
_ALLOWED_APPLICABILITY = {"material", "supporting", "not-applicable", "unknown"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class AuthorityAssertion:
    assertion_id: str
    authority_type: str
    source_kind: str
    reference: str
    captured_at: str
    freshness: str
    subject: str
    statement: str
    measurement_type: str
    confidence: str
    applicability: str
    evidence_sha256: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AuthorityAssertion":
        return cls(**{field: value.get(field) for field in cls.__dataclass_fields__})

    def validate(self) -> None:
        for field in ("assertion_id", "source_kind", "reference", "captured_at", "subject", "statement"):
            if not isinstance(getattr(self, field), str) or not getattr(self, field):
                raise ValueError(f"Authority assertion {self.assertion_id!r} has invalid {field}")
        if self.authority_type not in _ALLOWED_AUTHORITY_TYPES:
            raise ValueError(f"Unsupported authority type: {self.authority_type}")
        if self.freshness not in _ALLOWED_FRESHNESS:
            raise ValueError(f"Unsupported freshness: {self.freshness}")
        if self.measurement_type not in _ALLOWED_MEASUREMENT_TYPES:
            raise ValueError(f"Unsupported measurement type: {self.measurement_type}")
        if self.applicability not in _ALLOWED_APPLICABILITY:
            raise ValueError(f"Unsupported applicability: {self.applicability}")
        if self.measurement_type == "inferred" and self.source_kind != "inference":
            raise ValueError("Inferred assertions must identify source_kind=inference")
        if self.measurement_type != "inferred" and self.source_kind == "inference":
            raise ValueError("Source assertions and inference must remain separate")

    def to_dict(self) -> dict[str, Any]:
        return {field: getattr(self, field) for field in self.__dataclass_fields__}


@dataclass(frozen=True)
class AuthorityReceipt:
    schema_version: str
    receipt_id: str
    request: str
    captured_at: str
    repository: Mapping[str, Any]
    assertions: tuple[AuthorityAssertion, ...]
    conflicts: tuple[Mapping[str, Any], ...]
    unknowns: tuple[Mapping[str, Any], ...]
    reconciliation: Mapping[str, Any]
    mutation_gate: Mapping[str, Any]
    evidence_references: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "request": self.request,
            "captured_at": self.captured_at,
            "repository": dict(self.repository),
            "assertions": [item.to_dict() for item in self.assertions],
            "conflicts": [dict(item) for item in self.conflicts],
            "unknowns": [dict(item) for item in self.unknowns],
            "reconciliation": dict(self.reconciliation),
            "mutation_gate": dict(self.mutation_gate),
            "evidence_references": list(self.evidence_references),
        }


class AuthorityReconciler:
    """Reconcile scoped authority without converting inference into fact."""

    def __init__(self, required_types: Iterable[str]) -> None:
        required = tuple(dict.fromkeys(required_types))
        unknown = sorted(set(required) - _ALLOWED_AUTHORITY_TYPES)
        if unknown:
            raise ValueError(f"Unsupported required authority types: {unknown}")
        self.required_types = required

    def reconcile(
        self,
        *,
        receipt_id: str,
        request: str,
        repository: Mapping[str, Any],
        assertions: Iterable[AuthorityAssertion | Mapping[str, Any]],
        evidence_references: Iterable[str],
        captured_at: str | None = None,
    ) -> AuthorityReceipt:
        if not request:
            raise ValueError("Literal request is required")
        items = tuple(
            item if isinstance(item, AuthorityAssertion) else AuthorityAssertion.from_mapping(item)
            for item in assertions
        )
        if not items:
            disposition = "unavailable"
        identifiers: set[str] = set()
        for item in items:
            item.validate()
            if item.assertion_id in identifiers:
                raise ValueError(f"Duplicate authority assertion: {item.assertion_id}")
            identifiers.add(item.assertion_id)

        material = tuple(item for item in items if item.applicability == "material")
        by_subject: dict[str, list[AuthorityAssertion]] = {}
        for item in material:
            by_subject.setdefault(item.subject, []).append(item)
        conflicts: list[dict[str, Any]] = []
        for index, (subject, group) in enumerate(sorted(by_subject.items()), 1):
            statements = {item.statement for item in group if item.measurement_type != "unavailable"}
            if len(statements) > 1:
                conflicts.append({
                    "conflict_id": f"CONFLICT-{index:03d}",
                    "assertion_ids": [item.assertion_id for item in group],
                    "summary": f"Material authority disagrees for {subject}",
                    "materiality": "blocking",
                    "resolution_status": "unresolved",
                    "resolution": None,
                })

        observed_types = {item.authority_type for item in material if item.measurement_type != "unavailable"}
        unknowns: list[dict[str, Any]] = []
        for authority_type in self.required_types:
            if authority_type not in observed_types:
                unknowns.append({
                    "unknown_id": f"UNKNOWN-{len(unknowns)+1:03d}",
                    "subject": authority_type,
                    "materiality": "blocking",
                    "resolution_required": True,
                    "reason": "Required material authority is unavailable",
                })
        for item in material:
            if item.measurement_type == "unavailable" or item.freshness == "unknown":
                unknowns.append({
                    "unknown_id": f"UNKNOWN-{len(unknowns)+1:03d}",
                    "subject": item.subject,
                    "materiality": "blocking",
                    "resolution_required": True,
                    "reason": "Material authority value is unavailable or freshness is unknown",
                })

        stale = any(item.freshness == "stale" for item in material)
        if conflicts:
            disposition = "conflicting"
        elif stale:
            disposition = "stale"
        elif unknowns:
            disposition = "incomplete"
        elif not material:
            disposition = "unavailable"
        else:
            disposition = "complete"
        complete = disposition == "complete"
        summary = (
            "Material authority is complete and mutation may be proposed for operator review."
            if complete
            else f"Material authority is {disposition}; mutation remains blocked."
        )
        return AuthorityReceipt(
            schema_version="1.0",
            receipt_id=receipt_id,
            request=request,
            captured_at=captured_at or _iso_now(),
            repository=dict(repository),
            assertions=items,
            conflicts=tuple(conflicts),
            unknowns=tuple(unknowns),
            reconciliation={
                "disposition": disposition,
                "material_authority_complete": complete,
                "source_assertions_separate_from_inference": True,
                "summary": summary,
            },
            mutation_gate={
                "status": "review-ready" if complete else "blocked",
                "reason": summary,
                "operator_approval_required": True,
                "mutation_performed": False,
            },
            evidence_references=tuple(dict.fromkeys(evidence_references)),
        )
