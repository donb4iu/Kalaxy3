"""Capability-gap receipt creation and approval enforcement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class CapabilityGapRecorder:
    """Record unresolved capability gaps without conflating domain gaps with primitives."""

    @staticmethod
    def _candidates(
        candidates_considered: Iterable[Mapping[str, Any]],
        *,
        primitive_required: bool,
    ) -> list[dict[str, Any]]:
        candidates = [dict(item) for item in candidates_considered]
        if not candidates:
            raise ValueError("At least one existing candidate must be considered")
        for item in candidates:
            for field in (
                "component_id",
                "version",
                "source_path",
                "insufficiency",
                "composition_can_close_gap",
            ):
                if field not in item:
                    raise ValueError(f"Candidate is missing {field}")
            if primitive_required and item["composition_can_close_gap"] is True:
                raise ValueError(
                    "A new primitive is not justified when composition can close the gap"
                )
        return candidates

    @staticmethod
    def create(
        *,
        gap_id: str,
        request: str,
        authority_receipt: str,
        component_manifest: str,
        required_capability: str,
        candidates_considered: Iterable[Mapping[str, Any]],
        missing_interface_or_behavior: str,
        why_configuration_is_insufficient: str,
        why_composition_is_insufficient: str,
        proposed_primitive: Mapping[str, Any],
        approval: Mapping[str, Any],
        evidence_references: Iterable[str],
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Create the historical primitive-gap receipt shape."""

        candidates = CapabilityGapRecorder._candidates(
            candidates_considered,
            primitive_required=True,
        )
        required_fields = (
            "primitive_id",
            "responsibility",
            "side_effects",
            "idempotency",
            "logging",
            "failure_mode",
            "runtime_tests",
            "initial_maturity",
        )
        for field in required_fields:
            if field not in proposed_primitive:
                raise ValueError(f"Proposed primitive is missing {field}")
        if proposed_primitive.get("initial_maturity") != "pilot":
            raise ValueError("New primitives must begin at pilot maturity")
        return {
            "schema_version": "1.0",
            "gap_id": gap_id,
            "request": request,
            "created_at": created_at or _now(),
            "authority_receipt": authority_receipt,
            "component_manifest": component_manifest,
            "required_capability": required_capability,
            "candidates_considered": candidates,
            "gap": {
                "missing_interface_or_behavior": missing_interface_or_behavior,
                "why_configuration_is_insufficient": why_configuration_is_insufficient,
                "why_composition_is_insufficient": why_composition_is_insufficient,
                "new_primitive_required": True,
            },
            "proposed_primitive": dict(proposed_primitive),
            "approval": dict(approval),
            "evidence_references": list(dict.fromkeys(evidence_references)),
        }

    @staticmethod
    def create_domain(
        *,
        gap_id: str,
        request: str,
        authority_receipt: str,
        component_manifest: str,
        required_capability: str,
        candidates_considered: Iterable[Mapping[str, Any]],
        missing_interface_or_behavior: str,
        why_configuration_is_insufficient: str,
        why_composition_is_insufficient: str,
        approval: Mapping[str, Any],
        evidence_references: Iterable[str],
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Record a domain capability gap without inventing a SAGE primitive."""

        candidates = CapabilityGapRecorder._candidates(
            candidates_considered,
            primitive_required=False,
        )
        return {
            "schema_version": "1.1",
            "gap_id": gap_id,
            "request": request,
            "created_at": created_at or _now(),
            "authority_receipt": authority_receipt,
            "component_manifest": component_manifest,
            "required_capability": required_capability,
            "gap_kind": "domain-capability",
            "candidates_considered": candidates,
            "gap": {
                "missing_interface_or_behavior": missing_interface_or_behavior,
                "why_configuration_is_insufficient": why_configuration_is_insufficient,
                "why_composition_is_insufficient": why_composition_is_insufficient,
                "new_primitive_required": False,
                "new_domain_capability_required": True,
            },
            "proposed_primitive": None,
            "approval": dict(approval),
            "evidence_references": list(dict.fromkeys(evidence_references)),
        }

    @staticmethod
    def assert_implementation_allowed(receipt: Mapping[str, Any]) -> None:
        if receipt.get("gap", {}).get("new_primitive_required") is not True:
            raise ValueError("Receipt does not prove a new primitive is required")
        approval = receipt.get("approval", {})
        if approval.get("status") != "approved":
            raise PermissionError(
                "Capability gap must be operator-approved before implementation"
            )
        if not approval.get("reviewed_by") or not approval.get("reviewed_at"):
            raise PermissionError("Approval must identify reviewer and review time")

    @staticmethod
    def assert_domain_selection_required(receipt: Mapping[str, Any]) -> None:
        """Require a domain gap to stop planning without authorizing a primitive."""

        if receipt.get("schema_version") != "1.1":
            raise ValueError("Domain capability gap receipt version is invalid")
        if receipt.get("gap_kind") != "domain-capability":
            raise ValueError("Receipt is not a domain capability gap")
        gap = receipt.get("gap", {})
        if gap.get("new_primitive_required") is not False:
            raise ValueError("Domain capability gap may not authorize a new primitive")
        if gap.get("new_domain_capability_required") is not True:
            raise ValueError("Domain capability gap must remain unresolved")
        if receipt.get("proposed_primitive") is not None:
            raise ValueError("Domain capability gap may not propose a SAGE primitive")
