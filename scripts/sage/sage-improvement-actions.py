#!/usr/bin/env python3
"""Manage SAGE improvement-action lifecycle records safely."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Sequence

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
REGISTRY_PATH: Final = ROOT / "sage-improvement-actions.json"
LEGACY_CONTRACT_FIELDS: Final = (
    "action_id",
    "title",
    "source_lessons",
    "source_sessions",
    "owner",
    "priority",
    "target_control_type",
    "desired_outcome",
    "acceptance_criteria",
    "measurement_plan",
)
CONTRACT_FIELDS: Final = (
    "action_id",
    "title",
    "source_lessons",
    "source_sessions",
    "source_records",
    "owner",
    "priority",
    "target_control_type",
    "desired_outcome",
    "acceptance_criteria",
    "measurement_plan",
)
MUTABLE_CONTRACT_FIELDS: Final = CONTRACT_FIELDS[1:]
SUPPORTED_REGISTRY_SCHEMA_VERSIONS: Final = ("1.1", "1.2")
SOURCE_RECORD_TYPES: Final = ("capability-gap",)
CORE_EVENT_FIELDS: Final = {
    "sequence",
    "from_status",
    "to_status",
    "transition_type",
    "recorded_at",
    "actor",
    "reason",
    "evidence_references",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def parse_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(
            "recorded_at must be an ISO-8601 timestamp"
        ) from error


def contract_fields(value: dict[str, Any]) -> tuple[str, ...]:
    """Return the contract shape without rewriting historical action semantics."""
    if "source_records" in value:
        return CONTRACT_FIELDS
    return LEGACY_CONTRACT_FIELDS


def action_contract(action: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical mutable contract carried by one action."""
    return {
        key: copy.deepcopy(action[key])
        for key in contract_fields(action)
    }


def _source_record_key(value: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(value.get("record_type", "")),
        str(value.get("record_id", "")),
        str(value.get("schema_version", "")),
        str(value.get("sha256", "")),
    )


def validate_source_records(
    records: Any,
    *,
    label: str,
) -> list[str]:
    """Validate portable typed provenance descriptors."""
    failures: list[str] = []
    if not isinstance(records, list):
        return [f"{label} source_records must be a list"]
    keys: list[tuple[str, str, str, str]] = []
    for index, record in enumerate(records, start=1):
        prefix = f"{label} source_records[{index}]"
        if not isinstance(record, dict):
            failures.append(f"{prefix} must be an object")
            continue
        if set(record) != {
            "record_type",
            "record_id",
            "schema_version",
            "sha256",
        }:
            failures.append(f"{prefix} fields invalid")
            continue
        if record.get("record_type") not in SOURCE_RECORD_TYPES:
            failures.append(f"{prefix} record_type invalid")
        record_id = str(record.get("record_id", ""))
        if not re.fullmatch(
            r"SAGE-GAP-[0-9]{8}-[A-Z0-9][A-Z0-9-]*",
            record_id,
        ):
            failures.append(f"{prefix} record_id invalid")
        if record.get("schema_version") != "1.1":
            failures.append(f"{prefix} schema_version invalid")
        digest = str(record.get("sha256", ""))
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            failures.append(f"{prefix} sha256 invalid")
        keys.append(_source_record_key(record))
    if len(keys) != len(set(keys)):
        failures.append(f"{label} source_records must be unique")
    return failures


def source_record_descriptor(path: Path) -> dict[str, Any]:
    """Validate one governed source receipt and return its portable descriptor."""
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"source record {path} must be an object")
    if payload.get("schema_version") != "1.1":
        raise ValueError(f"source record {path} schema_version invalid")
    if payload.get("gap_kind") != "domain-capability":
        raise ValueError(f"source record {path} is not a domain capability gap")
    gap_id = require_string(payload.get("gap_id"), f"source record {path} gap_id")
    if not re.fullmatch(r"SAGE-GAP-[0-9]{8}-[A-Z0-9][A-Z0-9-]*", gap_id):
        raise ValueError(f"source record {path} gap_id invalid")
    require_string(
        payload.get("required_capability"),
        f"source record {path} required_capability",
    )
    require_string(
        payload.get("authority_receipt"),
        f"source record {path} authority_receipt",
    )
    require_string(
        payload.get("component_manifest"),
        f"source record {path} component_manifest",
    )
    candidates = payload.get("candidates_considered")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(f"source record {path} candidates_considered invalid")
    gap = payload.get("gap")
    if not isinstance(gap, dict):
        raise ValueError(f"source record {path} gap invalid")
    if gap.get("new_primitive_required") is not False:
        raise ValueError(f"source record {path} may not authorize a primitive")
    if gap.get("new_domain_capability_required") is not True:
        raise ValueError(f"source record {path} does not prove a domain gap")
    if payload.get("proposed_primitive") is not None:
        raise ValueError(f"source record {path} proposed_primitive must be null")
    approval = payload.get("approval")
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        raise ValueError(f"source record {path} requires Architect approval")
    for field in ("reviewed_by", "reviewed_at", "rationale"):
        require_string(
            approval.get(field),
            f"source record {path} approval {field}",
        )
    references = payload.get("evidence_references")
    if (
        not isinstance(references, list)
        or not references
        or len(references) != len(set(references))
        or not all(isinstance(value, str) and value for value in references)
    ):
        raise ValueError(f"source record {path} evidence_references invalid")
    return {
        "record_type": "capability-gap",
        "record_id": gap_id,
        "schema_version": "1.1",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def load_verified_source_records(paths: Sequence[Path]) -> list[dict[str, Any]]:
    """Return portable descriptors for verified governed source receipts."""
    records = [source_record_descriptor(path) for path in paths]
    failures = validate_source_records(records, label="verified")
    if failures:
        raise ValueError("; ".join(failures))
    return records


def require_verified_declared_sources(
    contract: dict[str, Any],
    verified_source_records: Sequence[dict[str, Any]],
) -> None:
    """Require typed source_records to match receipts verified for this mutation."""
    declared = contract.get("source_records", [])
    verified = list(verified_source_records)
    if declared:
        if not verified:
            raise ValueError(
                "source_records require --source-record-file verification"
            )
        if declared != verified:
            raise ValueError(
                "declared source_records do not match verified source receipts"
            )
    elif verified:
        raise ValueError(
            "verified source receipts were supplied but source_records are absent"
        )


def contract_sha256(contract: dict[str, Any]) -> str:
    """Return the stable digest used for stale-contract protection."""
    payload = json.dumps(
        contract,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_contract(
    contract: Any,
    *,
    label: str,
) -> list[str]:
    """Validate one action contract independent of lifecycle history."""
    failures: list[str] = []
    if not isinstance(contract, dict):
        return [f"{label} must be an object"]
    fields = contract_fields(contract)
    if set(contract) != set(fields):
        return [f"{label} fields must match a supported contract version"]

    action_id = str(contract.get("action_id", ""))
    if not re.fullmatch(r"SAGE-ACTION-[0-9]{8}-[0-9]{3}", action_id):
        failures.append(f"{label} action_id invalid")
    for key in ("title", "owner", "desired_outcome"):
        try:
            require_string(contract.get(key), f"{label} {key}")
        except ValueError as error:
            failures.append(str(error))

    lessons = contract.get("source_lessons")
    sessions = contract.get("source_sessions")
    source_records = contract.get("source_records", [])
    if not isinstance(lessons, list):
        failures.append(f"{label} source_lessons must be a list")
        lessons = []
    if not isinstance(sessions, list):
        failures.append(f"{label} source_sessions must be a list")
        sessions = []
    if not lessons and not sessions and not source_records:
        failures.append(f"{label}: at least one governed source is required")
    for source_label, values in (
        ("source_lessons", lessons),
        ("source_sessions", sessions),
    ):
        if (
            len(values) != len(set(values))
            or not all(isinstance(value, str) and value for value in values)
        ):
            failures.append(f"{label}: {source_label} invalid")
    failures.extend(
        validate_source_records(source_records, label=label)
    )

    if contract.get("priority") not in (
        "low",
        "medium",
        "high",
        "critical",
    ):
        failures.append(f"{label}: priority invalid")
    if contract.get("target_control_type") not in (
        "manual",
        "template",
        "preflight",
        "guardrail",
        "runbook",
        "automation",
        "no-action",
    ):
        failures.append(f"{label}: target_control_type invalid")
    for key in ("acceptance_criteria", "measurement_plan"):
        values = contract.get(key)
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(value, str) and value for value in values)
        ):
            failures.append(f"{label}: {key} must be non-empty")
    return failures


def validate_policy(policy: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(policy, dict):
        return ["policy must be an object"]

    lifecycle = policy.get(
        "improvement_action_lifecycle_policy"
    )
    if not isinstance(lifecycle, dict):
        return [
            "improvement_action_lifecycle_policy "
            "must be an object"
        ]

    if lifecycle.get("statuses") != policy.get(
        "improvement_action_statuses"
    ):
        failures.append(
            "action lifecycle statuses must match policy"
        )

    statuses = set(lifecycle.get("statuses", []))
    transitions = lifecycle.get("allowed_transitions")
    if not isinstance(transitions, dict):
        failures.append("action allowed_transitions missing")
    elif set(transitions) != statuses:
        failures.append(
            "action transitions must cover every status"
        )
    else:
        for source, targets in transitions.items():
            if (
                not isinstance(targets, list)
                or len(targets) != len(set(targets))
                or not set(targets).issubset(statuses)
            ):
                failures.append(
                    f"invalid action transitions for {source}"
                )

    expected_terminal = ["closed", "rejected"]
    if lifecycle.get("terminal_statuses") != expected_terminal:
        failures.append("action terminal statuses changed")

    for key in (
        "history_append_only",
        "dry_run_default",
        "apply_requires_explicit_flag",
        "atomic_write_required",
        "direct_status_edits_forbidden",
        "registration_requires_source",
        "contract_amendment_requires_expected_sha256",
        "contract_amendment_preserves_prior_values",
        "contract_amendment_status_unchanged",
    ):
        if lifecycle.get(key) is not True:
            failures.append(
                f"improvement_action_lifecycle_policy.{key} "
                "must be true"
            )

    if lifecycle.get("initial_status") != "identified":
        failures.append("action initial status changed")
    if lifecycle.get("contract_amendment_allowed_statuses") != [
        "identified"
    ]:
        failures.append(
            "action contract amendments must be identified-only"
        )
    if lifecycle.get("source_record_types") != list(SOURCE_RECORD_TYPES):
        failures.append("action source_record_types changed")
    if lifecycle.get("source_record_verification_required") is not True:
        failures.append("action source record verification must remain required")
    if lifecycle.get("contract_amendment_mutable_fields") != list(
        MUTABLE_CONTRACT_FIELDS
    ):
        failures.append(
            "action contract amendment mutable fields changed"
        )
    return failures


def validate_registry(
    registry: Any,
    policy: dict[str, Any],
) -> list[str]:
    """Validate action contracts and append-only lifecycle/amendment history."""
    failures: list[str] = []
    if not isinstance(registry, dict):
        return ["action registry must be an object"]
    registry_version = registry.get("schema_version")
    if registry_version not in SUPPORTED_REGISTRY_SCHEMA_VERSIONS:
        failures.append(
            "action registry schema_version must be 1.1 or 1.2"
        )
    if registry.get("registry_type") != "improvement-actions":
        failures.append(
            "action registry_type must be improvement-actions"
        )

    actions = registry.get("actions")
    if not isinstance(actions, list):
        failures.append("actions must be a list")
        return failures

    statuses = set(policy["improvement_action_statuses"])
    lifecycle = policy["improvement_action_lifecycle_policy"]
    allowed = lifecycle["allowed_transitions"]
    amendment_statuses = set(
        lifecycle["contract_amendment_allowed_statuses"]
    )
    identifiers: list[str] = []

    for item in actions:
        if not isinstance(item, dict):
            failures.append("action entry must be an object")
            continue

        fields = contract_fields(item)
        required = {
            *fields,
            "current_status",
            "history",
        }
        if set(item) != required:
            failures.append(
                "action fields must match the contract"
            )

        action_id = str(item.get("action_id", ""))
        identifiers.append(action_id)
        failures.extend(
            validate_contract(
                {
                    key: item.get(key)
                    for key in fields
                },
                label=action_id or "action",
            )
        )

        if registry_version == "1.1" and "source_records" in item:
            failures.append(
                f"{action_id}: source_records require registry schema 1.2"
            )

        status = item.get("current_status")
        if status not in statuses:
            failures.append(
                f"{action_id}: current_status invalid"
            )

        history = item.get("history")
        if not isinstance(history, list) or not history:
            failures.append(
                f"{action_id}: history must be non-empty"
            )
            continue

        previous_status: str | None = None
        previous_time: datetime | None = None
        previous_amendment_after: dict[str, Any] | None = None

        for index, event in enumerate(history, start=1):
            if not isinstance(event, dict):
                failures.append(
                    f"{action_id}: history event invalid"
                )
                continue

            event_type = event.get("transition_type")
            expected_fields = set(CORE_EVENT_FIELDS)
            if event_type == "contract-amendment":
                expected_fields.add("amendment")
            if set(event) != expected_fields:
                failures.append(
                    f"{action_id}: event fields invalid"
                )
            if event.get("sequence") != index:
                failures.append(
                    f"{action_id}: event sequence not contiguous"
                )

            source = event.get("from_status")
            target = event.get("to_status")
            if index == 1:
                if source is not None:
                    failures.append(
                        f"{action_id}: initial source must be null"
                    )
                if target != "identified":
                    failures.append(
                        f"{action_id}: initial status must be identified"
                    )
                if event_type != "initial-registration":
                    failures.append(
                        f"{action_id}: initial event type invalid"
                    )
            elif event_type == "status-transition":
                if source != previous_status:
                    failures.append(
                        f"{action_id}: event chain not contiguous"
                    )
                if (
                    source not in allowed
                    or target not in allowed[source]
                ):
                    failures.append(
                        f"{action_id}: transition "
                        f"{source} -> {target} not allowed"
                    )
            elif event_type == "contract-amendment":
                if source != previous_status or target != source:
                    failures.append(
                        f"{action_id}: amendment must preserve status"
                    )
                if source not in amendment_statuses:
                    failures.append(
                        f"{action_id}: amendment status not allowed"
                    )
                amendment = event.get("amendment")
                if not isinstance(amendment, dict):
                    failures.append(
                        f"{action_id}: amendment metadata invalid"
                    )
                else:
                    failures.extend(
                        validate_amendment(
                            action_id,
                            amendment,
                            previous_amendment_after,
                        )
                    )
                    after_contract = amendment.get("after_contract")
                    if isinstance(after_contract, dict):
                        previous_amendment_after = after_contract
            else:
                if index != 1:
                    failures.append(
                        f"{action_id}: transition event type invalid"
                    )

            for key in ("actor", "reason"):
                try:
                    require_string(
                        event.get(key),
                        f"{action_id} event {key}",
                    )
                except ValueError as error:
                    failures.append(str(error))

            references = event.get("evidence_references")
            if (
                not isinstance(references, list)
                or not references
                or len(references) != len(set(references))
                or not all(
                    isinstance(value, str) and value
                    for value in references
                )
            ):
                failures.append(
                    f"{action_id}: evidence references invalid"
                )

            try:
                parsed = datetime.fromisoformat(
                    str(event.get("recorded_at", "")).replace(
                        "Z",
                        "+00:00",
                    )
                )
                if (
                    previous_time is not None
                    and parsed < previous_time
                ):
                    failures.append(
                        f"{action_id}: timestamps regress"
                    )
                previous_time = parsed
            except ValueError:
                failures.append(
                    f"{action_id}: recorded_at invalid"
                )

            previous_status = str(target)

        if previous_status != status:
            failures.append(
                f"{action_id}: final event and status differ"
            )
        if previous_amendment_after is not None:
            if previous_amendment_after != action_contract(item):
                failures.append(
                    f"{action_id}: current contract does not match "
                    "latest amendment"
                )

    if len(identifiers) != len(set(identifiers)):
        failures.append("action identifiers must be unique")
    return failures


def validate_amendment(
    action_id: str,
    amendment: dict[str, Any],
    previous_after: dict[str, Any] | None,
) -> list[str]:
    """Validate one immutable contract-amendment receipt."""
    failures: list[str] = []
    required = {
        "changed_fields",
        "before_contract",
        "after_contract",
        "before_contract_sha256",
        "after_contract_sha256",
    }
    if set(amendment) != required:
        return [f"{action_id}: amendment fields invalid"]

    before = amendment.get("before_contract")
    after = amendment.get("after_contract")
    failures.extend(
        validate_contract(
            before,
            label=f"{action_id} amendment before_contract",
        )
    )
    failures.extend(
        validate_contract(
            after,
            label=f"{action_id} amendment after_contract",
        )
    )
    if not isinstance(before, dict) or not isinstance(after, dict):
        return failures

    if before.get("action_id") != action_id:
        failures.append(
            f"{action_id}: amendment before action_id changed"
        )
    if after.get("action_id") != action_id:
        failures.append(
            f"{action_id}: amendment after action_id changed"
        )
    if previous_after is not None and before != previous_after:
        failures.append(
            f"{action_id}: amendment contract chain not contiguous"
        )

    changed = amendment.get("changed_fields")
    expected_changed = [
        key
        for key in MUTABLE_CONTRACT_FIELDS
        if before.get(key) != after.get(key)
    ]
    if (
        not isinstance(changed, list)
        or changed != expected_changed
        or not changed
    ):
        failures.append(
            f"{action_id}: amendment changed_fields invalid"
        )

    before_digest = amendment.get("before_contract_sha256")
    after_digest = amendment.get("after_contract_sha256")
    if (
        not isinstance(before_digest, str)
        or before_digest != contract_sha256(before)
    ):
        failures.append(
            f"{action_id}: amendment before digest invalid"
        )
    if (
        not isinstance(after_digest, str)
        or after_digest != contract_sha256(after)
    ):
        failures.append(
            f"{action_id}: amendment after digest invalid"
        )
    return failures


def action_by_id(
    registry: dict[str, Any],
    action_id: str,
) -> dict[str, Any]:
    matches = [
        item
        for item in registry.get("actions", [])
        if isinstance(item, dict)
        and item.get("action_id") == action_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"action {action_id} must appear exactly once"
        )
    return matches[0]


def plan_registration(
    registry: dict[str, Any],
    policy: dict[str, Any],
    draft: dict[str, Any],
    *,
    recorded_at: str,
    actor: str,
    reason: str,
    evidence_references: Sequence[str],
    verified_source_records: Sequence[dict[str, Any]] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    fields = contract_fields(draft)
    if set(draft) != set(fields):
        raise ValueError("registration draft fields invalid")
    if "source_records" in draft and registry.get("schema_version") != "1.2":
        raise ValueError("source_records require registry schema_version 1.2")
    failures = validate_contract(draft, label=str(draft.get("action_id", "action")))
    if failures:
        raise ValueError("; ".join(failures))
    require_verified_declared_sources(draft, verified_source_records)
    if any(
        item.get("action_id") == draft["action_id"]
        for item in registry["actions"]
        if isinstance(item, dict)
    ):
        raise ValueError("action_id already exists")

    require_string(actor, "actor")
    require_string(reason, "reason")
    parse_timestamp(recorded_at)
    if (
        not evidence_references
        or len(evidence_references)
        != len(set(evidence_references))
        or not all(
            isinstance(value, str) and value
            for value in evidence_references
        )
    ):
        raise ValueError("evidence references invalid")

    updated = copy.deepcopy(registry)
    action = copy.deepcopy(draft)
    action["current_status"] = "identified"
    action["history"] = [
        {
            "sequence": 1,
            "from_status": None,
            "to_status": "identified",
            "transition_type": "initial-registration",
            "recorded_at": recorded_at,
            "actor": actor,
            "reason": reason,
            "evidence_references": list(
                evidence_references
            ),
        }
    ]
    ordered_fields = list(fields[:4])
    if "source_records" in fields:
        ordered_fields.append("source_records")
    ordered_fields.extend(
        [
            "current_status",
            "owner",
            "priority",
            "target_control_type",
            "desired_outcome",
            "acceptance_criteria",
            "measurement_plan",
            "history",
        ]
    )
    ordered = {key: action[key] for key in ordered_fields}
    updated["actions"].append(ordered)

    failures = validate_registry(updated, policy)
    if failures:
        raise ValueError(
            "planned registration invalid: "
            + "; ".join(failures)
        )
    return updated, ordered



def plan_amendment(
    registry: dict[str, Any],
    policy: dict[str, Any],
    replacement: dict[str, Any],
    *,
    expected_contract_sha256: str,
    recorded_at: str,
    actor: str,
    reason: str,
    evidence_references: Sequence[str],
    verified_source_records: Sequence[dict[str, Any]] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Plan one pre-acceptance contract amendment without changing status."""
    replacement_fields = contract_fields(replacement)
    if set(replacement) != set(replacement_fields):
        raise ValueError("amendment replacement fields invalid")
    if "source_records" in replacement and registry.get("schema_version") != "1.2":
        raise ValueError("source_records require registry schema_version 1.2")
    action_id = require_string(
        replacement.get("action_id"),
        "amendment action_id",
    )
    action = action_by_id(registry, action_id)
    source = str(action["current_status"])
    lifecycle = policy["improvement_action_lifecycle_policy"]
    if source not in lifecycle["contract_amendment_allowed_statuses"]:
        raise ValueError(
            f"contract amendment is not allowed from {source}"
        )

    require_string(actor, "actor")
    require_string(reason, "reason")
    parse_timestamp(recorded_at)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_contract_sha256):
        raise ValueError("expected contract SHA-256 invalid")
    if (
        not evidence_references
        or len(evidence_references)
        != len(set(evidence_references))
        or not all(
            isinstance(value, str) and value
            for value in evidence_references
        )
    ):
        raise ValueError("evidence references invalid")

    before = action_contract(action)
    if replacement.get("source_records", []) != before.get("source_records", []):
        require_verified_declared_sources(
            replacement,
            verified_source_records,
        )
    elif verified_source_records:
        raise ValueError(
            "source receipt verification was supplied but source_records did not change"
        )
    before_digest = contract_sha256(before)
    if expected_contract_sha256 != before_digest:
        raise ValueError(
            "stale action contract: expected SHA-256 does not match"
        )

    failures = validate_contract(
        replacement,
        label=f"{action_id} replacement",
    )
    if failures:
        raise ValueError("; ".join(failures))

    changed_fields = [
        key
        for key in MUTABLE_CONTRACT_FIELDS
        if before.get(key) != replacement.get(key)
    ]
    if not changed_fields:
        raise ValueError("contract amendment has no changes")
    permitted = set(lifecycle["contract_amendment_mutable_fields"])
    if not set(changed_fields).issubset(permitted):
        raise ValueError("contract amendment changes forbidden fields")

    updated = copy.deepcopy(registry)
    changed = action_by_id(updated, action_id)
    for key in list(changed):
        if key in MUTABLE_CONTRACT_FIELDS and key not in replacement:
            del changed[key]
    for key in replacement_fields[1:]:
        changed[key] = copy.deepcopy(replacement[key])

    after = action_contract(changed)
    event = {
        "sequence": len(changed["history"]) + 1,
        "from_status": source,
        "to_status": source,
        "transition_type": "contract-amendment",
        "recorded_at": recorded_at,
        "actor": actor,
        "reason": reason,
        "evidence_references": list(evidence_references),
        "amendment": {
            "changed_fields": changed_fields,
            "before_contract": before,
            "after_contract": after,
            "before_contract_sha256": before_digest,
            "after_contract_sha256": contract_sha256(after),
        },
    }
    changed["history"].append(event)

    failures = validate_registry(updated, policy)
    if failures:
        raise ValueError(
            "planned amendment invalid: "
            + "; ".join(failures)
        )
    return updated, event


def plan_transition(
    registry: dict[str, Any],
    policy: dict[str, Any],
    *,
    action_id: str,
    to_status: str,
    recorded_at: str,
    actor: str,
    reason: str,
    evidence_references: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    action = action_by_id(registry, action_id)
    source = str(action["current_status"])
    allowed = policy[
        "improvement_action_lifecycle_policy"
    ]["allowed_transitions"]
    if (
        source not in allowed
        or to_status not in allowed[source]
    ):
        raise ValueError(
            f"transition {source} -> {to_status} is not allowed"
        )

    require_string(actor, "actor")
    require_string(reason, "reason")
    parse_timestamp(recorded_at)
    if (
        not evidence_references
        or len(evidence_references)
        != len(set(evidence_references))
        or not all(
            isinstance(value, str) and value
            for value in evidence_references
        )
    ):
        raise ValueError("evidence references invalid")

    updated = copy.deepcopy(registry)
    changed = action_by_id(updated, action_id)
    event = {
        "sequence": len(changed["history"]) + 1,
        "from_status": source,
        "to_status": to_status,
        "transition_type": "status-transition",
        "recorded_at": recorded_at,
        "actor": actor,
        "reason": reason,
        "evidence_references": list(evidence_references),
    }
    changed["current_status"] = to_status
    changed["history"].append(event)

    failures = validate_registry(updated, policy)
    if failures:
        raise ValueError(
            "planned transition invalid: "
            + "; ".join(failures)
        )
    return updated, event


def atomic_write(registry: dict[str, Any]) -> None:
    original = REGISTRY_PATH.read_text(encoding="utf-8")
    text = json.dumps(registry, indent=4) + "\n"

    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-sage-actions-",
        dir=ROOT,
    ) as temp_dir:
        temp_path = Path(temp_dir) / "actions.json"
        temp_path.write_text(text, encoding="utf-8")
        try:
            os.replace(temp_path, REGISTRY_PATH)
        except OSError:
            REGISTRY_PATH.write_text(
                original,
                encoding="utf-8",
            )
            raise


def representative_policy() -> dict[str, Any]:
    statuses = [
        "identified",
        "accepted",
        "implemented",
        "validated",
        "measured",
        "closed",
        "rejected",
    ]
    return {
        "improvement_action_statuses": statuses,
        "improvement_action_lifecycle_policy": {
            "statuses": statuses,
            "allowed_transitions": {
                "identified": ["accepted", "rejected"],
                "accepted": ["implemented", "rejected"],
                "implemented": ["accepted", "validated"],
                "validated": ["implemented", "measured"],
                "measured": ["validated", "closed"],
                "closed": [],
                "rejected": [],
            },
            "initial_status": "identified",
            "terminal_statuses": ["closed", "rejected"],
            "history_append_only": True,
            "dry_run_default": True,
            "apply_requires_explicit_flag": True,
            "atomic_write_required": True,
            "direct_status_edits_forbidden": True,
            "registration_requires_source": True,
            "source_record_types": list(SOURCE_RECORD_TYPES),
            "source_record_verification_required": True,
            "contract_amendment_allowed_statuses": ["identified"],
            "contract_amendment_mutable_fields": list(
                MUTABLE_CONTRACT_FIELDS
            ),
            "contract_amendment_requires_expected_sha256": True,
            "contract_amendment_preserves_prior_values": True,
            "contract_amendment_status_unchanged": True,
        },
    }


def representative_draft() -> dict[str, Any]:
    return {
        "action_id": "SAGE-ACTION-20260728-001",
        "title": "Require downloadable implementation scripts",
        "source_lessons": [
            "SAGE-LESSON-20260728-001",
        ],
        "source_sessions": [],
        "owner": "repository-workflow",
        "priority": "high",
        "target_control_type": "template",
        "desired_outcome": (
            "Prevent interactive heredoc failures."
        ),
        "acceptance_criteria": [
            "Large terminal payloads are delivered as scripts.",
        ],
        "measurement_plan": [
            "Measure heredoc failure recurrence.",
        ],
    }


def run_self_tests() -> list[str]:
    failures: list[str] = []
    policy = representative_policy()
    registry = {
        "schema_version": "1.2",
        "registry_type": "improvement-actions",
        "actions": [],
    }

    failures.extend(validate_policy(policy))
    failures.extend(validate_registry(registry, policy))

    original = copy.deepcopy(registry)
    try:
        registered, action = plan_registration(
            registry,
            policy,
            representative_draft(),
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Register an evidence-backed action.",
            evidence_references=[
                "SAGE-LESSON-20260728-001",
            ],
        )
        if action["current_status"] != "identified":
            failures.append("initial action status changed")

        replacement = representative_draft()
        replacement["title"] = "Amended fixture action"
        replacement["desired_outcome"] = (
            "Preserve amended intent before acceptance."
        )
        expected = contract_sha256(action_contract(action))
        amended, amendment_event = plan_amendment(
            registered,
            policy,
            replacement,
            expected_contract_sha256=expected,
            recorded_at="2026-07-28T23:00:30-05:00",
            actor="self-test",
            reason="Reconcile the identified action contract.",
            evidence_references=["self-test:amendment"],
        )
        amended_action = action_by_id(
            amended,
            action["action_id"],
        )
        if amended_action["current_status"] != "identified":
            failures.append("amendment changed action status")
        if amendment_event["sequence"] != 2:
            failures.append("amendment sequence changed")
        if amendment_event["transition_type"] != (
            "contract-amendment"
        ):
            failures.append("amendment event type changed")
        if amendment_event["amendment"]["before_contract"] != (
            action_contract(action)
        ):
            failures.append("prior action contract was not preserved")

        accepted, event = plan_transition(
            amended,
            policy,
            action_id=action["action_id"],
            to_status="accepted",
            recorded_at="2026-07-28T23:01:00-05:00",
            actor="self-test",
            reason="Accept the improvement action.",
            evidence_references=["self-test:accepted"],
        )
        if event["sequence"] != 3:
            failures.append("action transition sequence changed")
        if action_by_id(
            accepted,
            action["action_id"],
        )["current_status"] != "accepted":
            failures.append("accepted action status changed")

        try:
            plan_amendment(
                accepted,
                policy,
                replacement,
                expected_contract_sha256=contract_sha256(
                    action_contract(
                        action_by_id(
                            accepted,
                            action["action_id"],
                        )
                    )
                ),
                recorded_at="2026-07-28T23:02:00-05:00",
                actor="self-test",
                reason="Invalid post-acceptance amendment.",
                evidence_references=["self-test:invalid"],
            )
            failures.append(
                "post-acceptance contract amendment was accepted"
            )
        except ValueError:
            pass

        try:
            plan_amendment(
                registered,
                policy,
                replacement,
                expected_contract_sha256="0" * 64,
                recorded_at="2026-07-28T23:00:30-05:00",
                actor="self-test",
                reason="Stale amendment attempt.",
                evidence_references=["self-test:stale"],
            )
            failures.append("stale contract amendment was accepted")
        except ValueError:
            pass

        try:
            plan_amendment(
                registered,
                policy,
                representative_draft(),
                expected_contract_sha256=expected,
                recorded_at="2026-07-28T23:00:30-05:00",
                actor="self-test",
                reason="No-op amendment attempt.",
                evidence_references=["self-test:no-op"],
            )
            failures.append("no-op contract amendment was accepted")
        except ValueError:
            pass
    except ValueError as error:
        failures.append(f"valid action lifecycle failed: {error}")

    if registry != original:
        failures.append("dry-run planning mutated registry")

    no_source = representative_draft()
    no_source["source_lessons"] = []
    try:
        plan_registration(
            registry,
            policy,
            no_source,
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Invalid source-free action.",
            evidence_references=["self-test"],
        )
        failures.append("source-free action was accepted")
    except ValueError:
        pass

    source_record_fixture = {
        "schema_version": "1.1",
        "gap_id": "SAGE-GAP-20260815-PROVENANCE",
        "request": "Prove typed improvement-action provenance.",
        "created_at": "2026-08-15T23:00:00-05:00",
        "authority_receipt": "self-test:authority",
        "component_manifest": "self-test:components",
        "required_capability": "typed improvement-action provenance",
        "gap_kind": "domain-capability",
        "candidates_considered": [
            {
                "component_id": "sage.action-lifecycle",
                "version": "1.0.0",
                "source_path": "scripts/sage/sage-improvement-actions.py",
                "insufficiency": "Lesson/session-only origin is insufficient.",
                "composition_can_close_gap": False,
            }
        ],
        "gap": {
            "missing_interface_or_behavior": "Typed non-session origin",
            "why_configuration_is_insufficient": "Contract shape is fixed.",
            "why_composition_is_insufficient": "Origin cannot be represented.",
            "new_primitive_required": False,
            "new_domain_capability_required": True,
        },
        "proposed_primitive": None,
        "approval": {
            "status": "approved",
            "reviewed_by": "Architect",
            "reviewed_at": "2026-08-15T23:00:00-05:00",
            "rationale": "Approve bounded provenance correction.",
        },
        "evidence_references": ["self-test:provenance-gap"],
    }
    with tempfile.TemporaryDirectory(prefix="sage-source-record-self-test-") as temp_dir:
        record_path = Path(temp_dir) / "capability-gap.json"
        record_path.write_text(
            json.dumps(source_record_fixture, indent=2) + "\n",
            encoding="utf-8",
        )
        verified = load_verified_source_records([record_path])
        source_draft = representative_draft()
        source_draft["source_lessons"] = []
        source_draft["source_sessions"] = []
        source_draft["source_records"] = verified
        try:
            with_source, source_action = plan_registration(
                registry,
                policy,
                source_draft,
                recorded_at="2026-08-15T23:01:00-05:00",
                actor="self-test",
                reason="Register capability-gap-origin action.",
                evidence_references=["self-test:provenance-gap"],
                verified_source_records=verified,
            )
            if source_action.get("source_records") != verified:
                failures.append("verified source_records were not preserved")
            if validate_registry(with_source, policy):
                failures.append("source-record action registry failed validation")
        except ValueError as error:
            failures.append(f"valid source-record registration failed: {error}")
        try:
            plan_registration(
                registry,
                policy,
                source_draft,
                recorded_at="2026-08-15T23:01:00-05:00",
                actor="self-test",
                reason="Reject unverified typed source.",
                evidence_references=["self-test:unverified"],
            )
            failures.append("unverified source_record was accepted")
        except ValueError:
            pass

    legacy_registry = {
        "schema_version": "1.1",
        "registry_type": "improvement-actions",
        "actions": [],
    }
    if validate_registry(legacy_registry, policy):
        failures.append("legacy 1.1 action registry compatibility failed")

    try:
        registered, _ = plan_registration(
            registry,
            policy,
            representative_draft(),
            recorded_at="2026-07-28T23:00:00-05:00",
            actor="self-test",
            reason="Register action.",
            evidence_references=["self-test"],
        )
        plan_transition(
            registered,
            policy,
            action_id="SAGE-ACTION-20260728-001",
            to_status="closed",
            recorded_at="2026-07-28T23:01:00-05:00",
            actor="self-test",
            reason="Invalid jump.",
            evidence_references=["self-test"],
        )
        failures.append("invalid action transition accepted")
    except ValueError:
        pass

    altered = copy.deepcopy(policy)
    altered["improvement_action_lifecycle_policy"][
        "dry_run_default"
    ] = False
    if not validate_policy(altered):
        failures.append("non-dry-run action policy accepted")
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage SAGE improvement actions"
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--register-file", type=Path)
    parser.add_argument("--amend-file", type=Path)
    parser.add_argument("--expected-contract-sha256")
    parser.add_argument("--action-id")
    parser.add_argument("--to-status")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument(
        "--evidence-reference",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--source-record-file",
        action="append",
        type=Path,
        default=[],
        help=(
            "Verify a governed source receipt and bind its portable descriptor "
            "to a registration or identified contract amendment."
        ),
    )
    parser.add_argument("--recorded-at")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        failures = run_self_tests()
        if failures:
            print(
                "Kalaxy3 SAGE improvement-action self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("PASS canonical improvement-action lifecycle")
        print("PASS evidence-backed registration")
        print("PASS append-only contiguous action history")
        print("PASS dry-run registration, amendment, and transition planning")
        print("PASS identified-only contract amendment with stale-digest protection")
        print(
            "PASS prior and resulting action contracts preserved "
            "in amendment history"
        )
        print("PASS explicit apply required for mutation")
        print("PASS invalid transitions fail closed")
        print(
            "Kalaxy3 SAGE improvement-action self-test: PASS"
        )
        return 0

    try:
        policy = load_json(POLICY_PATH)
        registry = load_json(REGISTRY_PATH)
        failures = validate_policy(policy)
        failures.extend(validate_registry(registry, policy))
        if failures:
            raise ValueError("; ".join(failures))

        if args.status:
            print("Kalaxy3 SAGE improvement actions: PASS")
            print(f"Actions: {len(registry['actions'])}")
            for action in registry["actions"]:
                print(
                    f"  - {action['action_id']}: "
                    f"{action['current_status']} — "
                    f"{action['title']}"
                )
            return 0

        recorded_at = (
            args.recorded_at
            or datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
        )

        if (
            args.register_file is not None
            and args.amend_file is not None
        ):
            raise ValueError(
                "registration and amendment are mutually exclusive"
            )

        verified_source_records = load_verified_source_records(
            args.source_record_file
        )

        if args.register_file is not None:
            draft = load_json(args.register_file)
            planned, event = plan_registration(
                registry,
                policy,
                draft,
                recorded_at=recorded_at,
                actor=args.actor or "",
                reason=args.reason or "",
                evidence_references=(
                    args.evidence_reference
                ),
                verified_source_records=verified_source_records,
            )
        elif args.amend_file is not None:
            replacement = load_json(args.amend_file)
            if not args.expected_contract_sha256:
                raise ValueError(
                    "--expected-contract-sha256 is required "
                    "for amendment"
                )
            planned, event = plan_amendment(
                registry,
                policy,
                replacement,
                expected_contract_sha256=(
                    args.expected_contract_sha256
                ),
                recorded_at=recorded_at,
                actor=args.actor or "",
                reason=args.reason or "",
                evidence_references=(
                    args.evidence_reference
                ),
                verified_source_records=verified_source_records,
            )
        else:
            if verified_source_records:
                raise ValueError(
                    "--source-record-file is valid only for registration or amendment"
                )
            if not args.action_id or not args.to_status:
                raise ValueError(
                    "use --status, --register-file, --amend-file, "
                    "or provide --action-id and --to-status"
                )
            planned, event = plan_transition(
                registry,
                policy,
                action_id=args.action_id,
                to_status=args.to_status,
                recorded_at=recorded_at,
                actor=args.actor or "",
                reason=args.reason or "",
                evidence_references=(
                    args.evidence_reference
                ),
            )

        print(
            json.dumps(
                {
                    "mode": "apply" if args.apply else "dry-run",
                    "event": event,
                },
                indent=4,
            )
        )

        if not args.apply:
            print("DRY RUN: action registry unchanged")
            return 0

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if status:
            raise ValueError(
                "working tree must be clean before --apply"
            )

        atomic_write(planned)
        print("APPLIED improvement-action registry mutation")
        return 0
    except (
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        TypeError,
    ) as error:
        print(
            "Kalaxy3 SAGE improvement actions: FAIL CLOSED"
        )
        print(f"  - {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
