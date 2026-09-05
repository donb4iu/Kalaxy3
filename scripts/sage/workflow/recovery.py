"""Stable recurrence identity and governed next-boundary decisions."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

RECOVERY_DECISION_NAME = "recovery-next-boundary.json"
RECOVERY_CONSUMPTION_NAME = "recovery-governing-change-consumption.json"
ACCEPTED_CONTROL_STATUSES = frozenset({"accepted", "implemented", "validated"})
ACCEPTED_CONTROL_FAILURE_ASSERTION_TYPE = "sage-accepted-control-failure-assertion"
_SHA = re.compile(r"\b[0-9a-f]{40}(?:[0-9a-f]{24})?\b")
_STATE_PATH = re.compile(r"/[^\s]*/\.local/state/kalaxy3/[^\s]+")
_TIMESTAMP = re.compile(r"\b\d{8}-\d{6}(?:-\d{6})?\b")


def _now() -> str:
    """Return the current local ISO-8601 timestamp."""

    return datetime.now().astimezone().isoformat(timespec="seconds")


def stable_json(value: object) -> str:
    """Return deterministic compact JSON for hashing.

    Args:
        value: JSON-compatible value.

    Returns:
        Canonical JSON text.
    """

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def digest_value(value: object) -> str:
    """Hash one JSON-compatible value.

    Args:
        value: JSON-compatible value.

    Returns:
        Lowercase SHA-256 digest.
    """

    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def governing_composition_digest(
    repo: Path,
    paths: Iterable[str],
) -> str:
    """Hash one policy-declared repository composition source set.

    The shared digest keeps recovery producers and consumers on the same
    repository-owned composition evidence instead of duplicating file-set
    hashing in each workflow.
    """

    resolved = repo.expanduser().resolve()
    normalized = tuple(str(item) for item in paths)
    if not normalized or len(set(normalized)) != len(normalized):
        raise ValueError("recovery governing composition paths are invalid")
    evidence: dict[str, str] = {}
    for relative in normalized:
        candidate = Path(relative)
        if (
            not relative.strip()
            or candidate.is_absolute()
            or ".." in candidate.parts
        ):
            raise ValueError(
                f"recovery governing composition path is unsafe: {relative}"
            )
        path = resolved / candidate
        if not path.is_file():
            raise ValueError(
                f"recovery governing composition path is missing: {relative}"
            )
        evidence[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest_value(evidence)


def normalize_failure_text(text: str) -> str:
    """Normalize attempt-local tokens out of a failure signature.

    Args:
        text: Raw failure description.

    Returns:
        Stable failure text suitable for recurrence identity.
    """

    normalized = _STATE_PATH.sub("<sage-state>", text)
    normalized = _SHA.sub("<object-id>", normalized)
    normalized = _TIMESTAMP.sub("<timestamp>", normalized)
    return " ".join(normalized.split())


def build_recovery_identity(
    *,
    request: str,
    component_id: str,
    failure_text: str,
    repository_authority: Mapping[str, Any],
) -> dict[str, Any]:
    """Build stable request/component/failure identity plus authority evidence.

    Args:
        request: Literal governed request.
        component_id: Owning component identifier.
        failure_text: Raw failure description.
        repository_authority: Measured repository authority.

    Returns:
        Recovery identity object.
    """

    request_sha = hashlib.sha256(request.encode("utf-8")).hexdigest()
    signature = digest_value(
        {
            "component_id": component_id,
            "failure": normalize_failure_text(failure_text),
        }
    )
    authority = dict(repository_authority)
    identity_key = digest_value(
        {
            "request_sha256": request_sha,
            "component_id": component_id,
            "failure_signature": signature,
        }
    )
    return {
        "request_sha256": request_sha,
        "component_id": component_id,
        "failure_signature": signature,
        "repository_authority": authority,
        "repository_authority_sha256": digest_value(authority),
        "identity_sha256": identity_key,
    }


def governing_fingerprint(
    governing_evidence: Mapping[str, Any],
) -> str:
    """Hash the governing evidence snapshot that determines recovery re-entry.

    Args:
        governing_evidence: Evidence supporting governing conditions.

    Returns:
        Stable governing-condition fingerprint.
    """

    return digest_value({"governing_evidence": dict(governing_evidence)})


def load_recovery_decisions(
    root: Path,
    identity_sha256: str,
) -> list[dict[str, Any]]:
    """Load prior recovery decisions for one stable failure identity.

    Args:
        root: SAGE local-state root.
        identity_sha256: Stable recovery identity digest.

    Returns:
        Chronologically sorted matching decision objects.
    """

    records: list[dict[str, Any]] = []
    if not root.is_dir():
        return records
    for path in root.rglob(RECOVERY_DECISION_NAME):
        record = _read_json_object(path)
        if record is None:
            continue
        identity = record.get("recovery_identity")
        if (
            isinstance(identity, dict)
            and identity.get("identity_sha256") == identity_sha256
        ):
            records.append({**record, "_path": str(path)})
    return sorted(records, key=lambda item: str(item.get("recorded_at", "")))


def load_consumed_fingerprints(
    root: Path,
    identity_sha256: str,
) -> set[str]:
    """Load governing fingerprints consumed by actual re-entry.

    Args:
        root: SAGE local-state root.
        identity_sha256: Stable recovery identity digest.

    Returns:
        Set of consumed governing-condition fingerprints.
    """

    consumed: set[str] = set()
    if not root.is_dir():
        return consumed
    for path in root.rglob(RECOVERY_CONSUMPTION_NAME):
        record = _read_json_object(path)
        if record is None:
            continue
        if record.get("recovery_identity_sha256") != identity_sha256:
            continue
        fingerprint = record.get("governing_condition_fingerprint")
        if isinstance(fingerprint, str) and fingerprint:
            consumed.add(fingerprint)
    return consumed


def _read_json_object(path: Path) -> dict[str, Any] | None:
    """Read one JSON object, ignoring unreadable history artifacts.

    Args:
        path: Local-state JSON path.

    Returns:
        Parsed object or None.
    """

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _operator_boundary(
    disposition: str,
    owning_component: str,
    control_action_id: str | None,
) -> dict[str, Any]:
    """Build one operator-visible boundary descriptor.

    Args:
        disposition: Recovery disposition.
        owning_component: Component responsible for recovery.
        control_action_id: Governing improvement action when known.

    Returns:
        Operator boundary descriptor.
    """

    if disposition == "successor-action":
        return {
            "kind": "architect-decision",
            "command": None,
            "decision": (
                "Authorize a successor capability-gap/improvement-action boundary "
                f"for accepted control {control_action_id or owning_component}."
            ),
        }
    return {
        "kind": "repository-workflow",
        "command": "make sage-request-execute-self-test",
        "decision": None,
    }


def _bound_recovery_command(
    *,
    disposition: str,
    owning_component: str,
    decision_path: Path,
) -> str:
    """Return the registered continuation command for one recovery owner."""

    resolved = decision_path.expanduser().resolve()
    quoted = json.dumps(str(resolved))
    if disposition == "successor-action":
        return (
            "python3 scripts/sage/sage-improvement-action-transition.py "
            f"--recovery-decision {quoted}"
        )
    implementation_local = {
        "sage.improvement-action-transition": (
            "python3 scripts/sage/sage-improvement-action-transition.py "
            f"--recovery-decision {quoted}"
        ),
        "sage.request-execution": (
            "python3 scripts/sage/sage-request-execute.py "
            f"--recovery-decision {quoted}"
        ),
        "sage.objective-execution": (
            "python3 scripts/sage/sage-objective-execution.py recover "
            f"--recovery-decision {quoted}"
        ),
    }
    command = implementation_local.get(owning_component)
    if command is None:
        raise ValueError(
            "no implementation-local recovery consumer registered for "
            f"{owning_component}"
        )
    return command


def bind_successor_operator_boundary(
    decision: Mapping[str, Any],
    decision_path: Path,
) -> dict[str, Any]:
    """Bind recovery to the repository continuation owned by its boundary."""

    payload = json.loads(json.dumps(decision))
    disposition = str(payload.get("disposition", ""))
    implementation_local = (
        disposition == "repair"
        and payload.get("next_boundary") == "implementation-local"
    )
    if disposition != "successor-action" and not implementation_local:
        return payload
    command = _bound_recovery_command(
        disposition=disposition,
        owning_component=str(payload.get("owning_component", "")),
        decision_path=decision_path,
    )
    payload["operator_boundary"] = {
        "kind": "repository-workflow",
        "command": command,
        "decision": None,
    }
    return payload


def build_accepted_control_failure_assertion(
    *,
    control_action_id: str,
    violated_obligation: str,
    evidence_references: Iterable[str],
) -> dict[str, Any]:
    """Build explicit evidence that an accepted control violated its contract."""

    references = tuple(str(item) for item in evidence_references)
    if not control_action_id:
        raise ValueError("accepted-control failure assertion requires control action id")
    if not violated_obligation.strip():
        raise ValueError("accepted-control failure assertion requires violated obligation")
    if not references or any(not item.strip() for item in references):
        raise ValueError("accepted-control failure assertion requires concrete evidence")
    if len(set(references)) != len(references):
        raise ValueError("accepted-control failure assertion evidence must be unique")
    return {
        "schema_version": "1.0",
        "record_type": ACCEPTED_CONTROL_FAILURE_ASSERTION_TYPE,
        "control_action_id": control_action_id,
        "violated_obligation": violated_obligation,
        "evidence_references": list(references),
    }


def _validate_accepted_control_failure_assertion(
    value: Mapping[str, Any] | None,
    *,
    control_action_id: str | None,
) -> dict[str, Any] | None:
    """Validate distinct evidence that the owning accepted control itself failed."""

    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(
            "accepted-control failure must be a machine-readable evidence assertion"
        )
    expected = {
        "schema_version",
        "record_type",
        "control_action_id",
        "violated_obligation",
        "evidence_references",
    }
    if set(value) != expected:
        raise ValueError("accepted-control failure assertion fields are invalid")
    if (
        value.get("schema_version") != "1.0"
        or value.get("record_type") != ACCEPTED_CONTROL_FAILURE_ASSERTION_TYPE
    ):
        raise ValueError("accepted-control failure assertion version/type is invalid")
    asserted_control = value.get("control_action_id")
    if (
        not isinstance(asserted_control, str)
        or not asserted_control
        or asserted_control != control_action_id
    ):
        raise ValueError("accepted-control failure assertion control identity drifted")
    obligation = value.get("violated_obligation")
    if not isinstance(obligation, str) or not obligation.strip():
        raise ValueError("accepted-control failure assertion lacks violated obligation")
    references = value.get("evidence_references")
    if (
        not isinstance(references, list)
        or not references
        or any(not isinstance(item, str) or not item.strip() for item in references)
        or len(set(references)) != len(references)
    ):
        raise ValueError("accepted-control failure assertion evidence is invalid")
    return {
        "schema_version": "1.0",
        "record_type": ACCEPTED_CONTROL_FAILURE_ASSERTION_TYPE,
        "control_action_id": asserted_control,
        "violated_obligation": obligation,
        "evidence_references": list(references),
    }


def decide_next_boundary(
    *,
    identity: Mapping[str, Any],
    post_retrieval: Mapping[str, Any],
    governing_evidence: Mapping[str, Any],
    previous: Iterable[Mapping[str, Any]],
    consumed_fingerprints: set[str],
    owning_component: str,
    control_action_id: str | None,
    control_action_status: str | None,
    accepted_control_failure: Mapping[str, Any] | None,
    progress_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose one recovery boundary from recurrence and progress evidence."""
    conditions = post_retrieval.get("governing_conditions", {})
    fingerprint = governing_fingerprint(governing_evidence)
    prior = list(previous)
    same = [
        item
        for item in prior
        if item.get("governing_condition_fingerprint") == fingerprint
    ]
    consumed = fingerprint in consumed_fingerprints
    requested = str(
        post_retrieval.get("required_reentry_boundary", "implementation-local")
    )
    failure_assertion = _validate_accepted_control_failure_assertion(
        accepted_control_failure,
        control_action_id=control_action_id,
    )
    accepted_failure = failure_assertion is not None
    progress_sha = digest_value(dict(progress_evidence or {}))
    non_converging = _non_converging_recovery(
        same=same,
        consumed=consumed,
        progress_sha=progress_sha,
    )
    disposition, boundary = _select_disposition(
        same=same,
        consumed=consumed,
        post_retrieval=post_retrieval,
        requested=requested,
        accepted_control_failure=accepted_failure,
        control_action_status=control_action_status,
        non_converging=non_converging,
    )
    attention_required = _architect_attention_required(
        disposition=disposition,
        boundary=boundary,
    )
    control = {
        "action_id": control_action_id,
        "status": control_action_status,
        "accepted_control_failure": accepted_failure,
        "accepted_control_failure_assertion": failure_assertion,
    }
    return _decision_payload(
        identity=identity,
        post_retrieval=post_retrieval,
        governing_evidence=governing_evidence,
        prior=prior,
        fingerprint=fingerprint,
        consumed=consumed,
        disposition=disposition,
        boundary=boundary,
        owning_component=owning_component,
        owning_control=control,
        requested=requested,
        architect_attention_required=attention_required,
        progress_sha=progress_sha,
        non_converging=non_converging,
        accepted_control_failure=accepted_failure,
    )


def _non_converging_recovery(
    *,
    same: list[Mapping[str, Any]],
    consumed: bool,
    progress_sha: str,
) -> bool:
    """Return whether a consumed local repair recurred without progress.

    A consumed governance/planning re-entry is not itself a failed local repair.
    Non-convergence begins only after the latest matching decision was an
    implementation-local repair and that repair's progress evidence is unchanged.
    """
    if not same or not consumed:
        return False
    latest = same[-1]
    if (
        latest.get("disposition") != "repair"
        or latest.get("next_boundary") != "implementation-local"
    ):
        return False
    evidence = latest.get("governing_evidence", {})
    if not isinstance(evidence, Mapping):
        return False
    previous_progress = str(evidence.get("recovery_progress_sha256", ""))
    return bool(previous_progress and previous_progress == progress_sha)


def _architect_attention_required(
    *,
    disposition: str,
    boundary: str,
) -> bool:
    """Return whether recovery crosses a material Architect boundary.

    Args:
        disposition: Selected recovery disposition.
        boundary: Selected next boundary.

    Returns:
        True only when recovery requires new material governance attention.
    """
    if disposition == "successor-action":
        return True
    return disposition == "governance-reentry" and boundary != "implementation-local"


def _select_disposition(
    *,
    same: list[Mapping[str, Any]],
    consumed: bool,
    post_retrieval: Mapping[str, Any],
    requested: str,
    accepted_control_failure: bool,
    control_action_status: str | None,
    non_converging: bool,
) -> tuple[str, str]:
    """Select one disposition from recurrence and governing evidence."""

    if same and not consumed and same[-1].get("disposition") == "governance-reentry":
        return "over-governance-blocked", "await-existing-reentry"
    if (
        same
        and accepted_control_failure
        and control_action_status in ACCEPTED_CONTROL_STATUSES
    ):
        return "successor-action", "architect-decision"
    if non_converging:
        return "successor-action", "architect-decision"
    if same:
        return "repair", "implementation-local"
    if post_retrieval.get("disposition") == "governance-reentry":
        return "governance-reentry", requested
    return "repair", "implementation-local"


def _decision_payload(
    *,
    identity: Mapping[str, Any],
    post_retrieval: Mapping[str, Any],
    governing_evidence: Mapping[str, Any],
    prior: list[Mapping[str, Any]],
    fingerprint: str,
    consumed: bool,
    disposition: str,
    boundary: str,
    owning_component: str,
    owning_control: Mapping[str, Any],
    requested: str,
    architect_attention_required: bool,
    progress_sha: str,
    non_converging: bool,
    accepted_control_failure: bool,
) -> dict[str, Any]:
    """Build the versioned recovery next-boundary payload."""

    references = [
        str(item.get("_path"))
        for item in prior
        if item.get("_path")
    ]
    return {
        "schema_version": "1.0",
        "record_type": "sage-recovery-next-boundary",
        "recorded_at": _now(),
        "recovery_identity": dict(identity),
        "classification": "recurrence" if prior else "new",
        "previous_failure_references": references,
        "governing_conditions": dict(post_retrieval.get("governing_conditions", {})),
        "governing_evidence": {
            **dict(governing_evidence),
            "recovery_progress_sha256": progress_sha,
        },
        "governing_condition_fingerprint": fingerprint,
        "governing_change_consumed": consumed,
        "disposition": disposition,
        "next_boundary": boundary,
        "owning_component": owning_component,
        "owning_control": dict(owning_control),
        "architect_attention_required": architect_attention_required,
        "reason": _reason(
            disposition,
            requested,
            bool(prior),
            non_converging=non_converging,
            accepted_control_failure=accepted_control_failure,
        ),
        "required_evidence": _required_evidence(),
        "mutation_authority": "repository-workflow",
        "operator_boundary": _operator_boundary(
            disposition,
            owning_component,
            str(owning_control.get("action_id") or "") or None,
        ),
        "metrics": _metrics(
            disposition,
            bool(prior),
            architect_attention_required,
            non_converging=non_converging,
        ),
    }


def _metrics(
    disposition: str,
    recurred: bool,
    architect_attention_required: bool,
    *,
    non_converging: bool,
) -> dict[str, bool | int]:
    """Return observable recovery-decision metrics.

    Args:
        disposition: Selected recovery disposition.
        recurred: Whether the stable failure identity was previously observed.
        architect_attention_required: Whether a new material boundary is needed.

    Returns:
        Recovery metrics suitable for continuous-improvement aggregation.
    """
    local_repair = disposition == "repair" and not architect_attention_required
    return {
        "recurrence_detected": recurred,
        "prevented_duplicate_reentry": disposition == "over-governance-blocked",
        "successor_escalation": disposition == "successor-action",
        "architect_attention_required": architect_attention_required,
        "avoided_architect_recovery_round_trips": 1 if local_repair else 0,
        "non_convergence_detected": non_converging,
    }

def _required_evidence() -> list[str]:
    """Return the common evidence required before another mutation."""

    return [
        "failure retrieval receipt",
        "stable recovery identity",
        "governing-condition fingerprint",
        "repository authority",
        "regression/revalidation evidence",
    ]


def _reason(
    disposition: str,
    requested_boundary: str,
    recurred: bool,
    *,
    non_converging: bool,
    accepted_control_failure: bool,
) -> str:
    """Render one concise deterministic recovery reason.

    Args:
        disposition: Selected recovery disposition.
        requested_boundary: Boundary requested by post-retrieval classification.
        recurred: Whether prior stable-failure evidence exists.

    Returns:
        Human-readable reason consistent with recurrence classification.
    """

    if disposition == "successor-action" and non_converging:
        return (
            "A consumed implementation-local recovery recurred with unchanged "
            "progress evidence; the local loop is non-converging and must exit. "
            "No already-authorized alternative is evidenced by this recovery "
            "decision, so a governed Architect boundary is required."
        )
    if disposition == "repair":
        if recurred:
            return (
                "The failure recurred without a new governing-condition "
                "fingerprint; repair, regression, and revalidation stay "
                "implementation-local under existing governing authority."
            )
        return (
            "The failure is new and does not require governance re-entry; "
            "repair, regression, and revalidation stay implementation-local "
            "under existing governing authority."
        )
    reasons = {
        "over-governance-blocked": (
            "The same governing fingerprint already emitted a re-entry that has "
            "not been consumed; another governance loop is blocked."
        ),
        "successor-action": (
            "Distinct evidence shows the accepted owning control violated its "
            "promised obligation; the current lifecycle cannot silently amend "
            "that accepted control."
        ),
        "governance-reentry": (
            f"A genuinely new governing fingerprint requires one "
            f"{requested_boundary} re-entry."
        ),
    }
    return reasons[disposition]


def build_consumption_record(
    decision: Mapping[str, Any],
    *,
    consumed_boundary: str,
    consumer_reference: str,
) -> dict[str, Any]:
    """Record that a previously emitted governing re-entry was consumed.

    Args:
        decision: Recovery next-boundary decision.
        consumed_boundary: Re-entry boundary actually started.
        consumer_reference: Durable consumer state reference.

    Returns:
        Immutable consumption record.
    """

    identity = decision.get("recovery_identity", {})
    return {
        "schema_version": "1.0",
        "record_type": "sage-recovery-governing-change-consumption",
        "recorded_at": _now(),
        "recovery_identity_sha256": identity.get("identity_sha256"),
        "governing_condition_fingerprint": decision.get(
            "governing_condition_fingerprint"
        ),
        "required_reentry_boundary": decision.get("next_boundary"),
        "consumed_boundary": consumed_boundary,
        "consumer_reference": consumer_reference,
    }


def latest_matching_reentry(
    root: Path,
    request_sha256: str,
    boundary: str,
    *,
    repository_owned_composition_sha256: str | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    """Find the newest applicable recovery re-entry for a request and boundary.

    Args:
        root: SAGE local-state root.
        request_sha256: Literal request digest.
        boundary: Re-entry boundary being started.
        repository_owned_composition_sha256: Optional current recovery-composition
            digest. When supplied, decisions emitted by older compositions remain
            historical and are not treated as current re-entry authority.

    Returns:
        Matching decision path/object pair, or None.
    """

    if (
        repository_owned_composition_sha256 is not None
        and re.fullmatch(r"[0-9a-f]{64}", repository_owned_composition_sha256)
        is None
    ):
        raise ValueError("current recovery composition digest is invalid")
    candidates: list[tuple[Path, dict[str, Any]]] = []
    if not root.is_dir():
        return None
    for path in root.rglob(RECOVERY_DECISION_NAME):
        payload = _read_json_object(path)
        if payload is None:
            continue
        identity = payload.get("recovery_identity")
        if not isinstance(identity, dict):
            continue
        if identity.get("request_sha256") != request_sha256:
            continue
        if payload.get("next_boundary") != boundary:
            continue
        if repository_owned_composition_sha256 is not None:
            evidence = payload.get("governing_evidence")
            if not isinstance(evidence, dict):
                continue
            if (
                evidence.get("repository_owned_composition_sha256")
                != repository_owned_composition_sha256
            ):
                continue
        candidates.append((path, payload))
    candidates.sort(key=lambda item: str(item[1].get("recorded_at", "")))
    return candidates[-1] if candidates else None
