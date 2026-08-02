"""Evidence-based repository component selection and composition manifests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

_APPLICABILITY = {"direct": 0, "partial": 1, "none": 2, "unknown": 3}
_AUTHORITY = {"compatible": 0, "unknown": 1, "conflicting": 2}
_SCOPE = {"least-authority": 0, "insufficient": 1, "broader-than-required": 2, "unknown": 3}
_TESTS = {"positive-and-negative": 0, "positive-only": 1, "source-only": 2, "none": 3, "unknown": 4}
_RECURRENCE = {"no": 0, "unknown": 1, "yes": 2}


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass(frozen=True)
class RequiredCapability:
    capability_id: str
    description: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"capability_id": self.capability_id, "description": self.description, "required": self.required}


@dataclass(frozen=True)
class ComponentCandidate:
    candidate_id: str
    capability_ids: tuple[str, ...]
    component_id: str
    version: str
    source_path: str
    maturity: str
    selection_factors: Mapping[str, Any]
    evidence_references: tuple[str, ...]
    rationale: str

    def rank_key(self) -> tuple[Any, ...]:
        factors = self.selection_factors
        return (
            _APPLICABILITY.get(str(factors.get("applicability")), 99),
            _AUTHORITY.get(str(factors.get("authority_compatibility")), 99),
            _SCOPE.get(str(factors.get("mutation_scope_fit")), 99),
            0 if factors.get("published_interface_verified") is True else 1,
            _RECURRENCE.get(str(factors.get("open_recurrence")), 99),
            _TESTS.get(str(factors.get("runtime_test_coverage")), 99),
            -(factors.get("successful_production_executions") or 0),
            factors.get("failed_production_executions") if isinstance(factors.get("failed_production_executions"), int) else 10**9,
            self.component_id,
            self.version,
        )

    def eligible(self) -> bool:
        factors = self.selection_factors
        return (
            factors.get("applicability") == "direct"
            and factors.get("authority_compatibility") == "compatible"
            and factors.get("mutation_scope_fit") == "least-authority"
            and factors.get("published_interface_verified") is True
            and factors.get("open_recurrence") != "yes"
            and factors.get("runtime_test_coverage") in {"positive-and-negative", "positive-only"}
        )

    def to_dict(self, disposition: str) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "capability_ids": list(self.capability_ids),
            "component_id": self.component_id,
            "version": self.version,
            "source_path": self.source_path,
            "maturity": self.maturity,
            "disposition": disposition,
            "selection_factors": dict(self.selection_factors),
            "evidence_references": list(self.evidence_references),
            "rationale": self.rationale,
        }


class ComponentSelector:
    """Select components by explicit ordered factors, never an opaque score."""

    def build_manifest(
        self,
        *,
        manifest_id: str,
        request: str,
        authority_receipt: str,
        capabilities: Iterable[RequiredCapability],
        candidates: Iterable[ComponentCandidate],
        approval: Mapping[str, Any],
        created_at: str | None = None,
    ) -> dict[str, Any]:
        required = tuple(capabilities)
        candidate_items = tuple(candidates)
        if not required or not candidate_items:
            raise ValueError("Capabilities and candidates are required")
        capability_ids = {item.capability_id for item in required}
        if len(capability_ids) != len(required):
            raise ValueError("Capability identifiers must be unique")
        candidate_ids = {item.candidate_id for item in candidate_items}
        if len(candidate_ids) != len(candidate_items):
            raise ValueError("Candidate identifiers must be unique")
        selections: list[dict[str, Any]] = []
        selected_ids: set[str] = set()
        gaps: list[str] = []
        for capability in required:
            applicable = [item for item in candidate_items if capability.capability_id in item.capability_ids]
            eligible = sorted((item for item in applicable if item.eligible()), key=lambda item: item.rank_key())
            if eligible:
                chosen = eligible[0]
                selected_ids.add(chosen.candidate_id)
                selections.append({
                    "capability_id": capability.capability_id,
                    "candidate_id": chosen.candidate_id,
                    "component_id": chosen.component_id,
                    "version": chosen.version,
                    "selection_basis": chosen.rationale,
                })
            elif capability.required:
                gaps.append(capability.capability_id)
        dispositions = [item.to_dict("selected" if item.candidate_id in selected_ids else ("gap" if any(cap in gaps for cap in item.capability_ids) else "rejected")) for item in candidate_items]
        composition = [
            {
                "sequence": index,
                "step_id": f"composition-step-{index}",
                "capability_id": selection["capability_id"],
                "component_id": selection["component_id"],
                "version": selection["version"],
                "purpose": next(item.description for item in required if item.capability_id == selection["capability_id"]),
                "side_effect_scope": "declared-by-component",
            }
            for index, selection in enumerate(selections, 1)
        ]
        return {
            "schema_version": "1.0",
            "manifest_id": manifest_id,
            "request": request,
            "created_at": created_at or _now(),
            "authority_receipt": authority_receipt,
            "required_capabilities": [item.to_dict() for item in required],
            "candidates": dispositions,
            "selections": selections,
            "composition": composition,
            "capability_gap_receipts": gaps,
            "approval": dict(approval),
            "composite_score_enabled": False,
        }

    @staticmethod
    def require_complete(manifest: Mapping[str, Any]) -> None:
        if manifest.get("composite_score_enabled") is not False:
            raise ValueError("Opaque composite ranking is forbidden")
        gaps = manifest.get("capability_gap_receipts", [])
        if gaps:
            raise ValueError(f"Unresolved capability gaps: {gaps}")
        required = {item["capability_id"] for item in manifest.get("required_capabilities", []) if item.get("required") is True}
        selected = {item["capability_id"] for item in manifest.get("selections", [])}
        if required != selected:
            raise ValueError("Required capability coverage is incomplete")
