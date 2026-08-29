"""Content-addressed causal evidence facts and derived objective views for SAGE."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from workflow.authority import AuthorityAssertion, AuthorityReconciler

SCHEMA_VERSION = "1.0"
FACT_ID_PREFIX = "sha256:"


class CausalEvidenceError(RuntimeError):
    """Fail-closed causal evidence contract error."""


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _stable_json(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CausalEvidenceError(f"{label} must be a non-empty string")
    return value.strip()


def _require_fact_id(value: object, label: str) -> str:
    text = _require_string(value, label)
    if not text.startswith(FACT_ID_PREFIX):
        raise CausalEvidenceError(f"{label} must begin with {FACT_ID_PREFIX}")
    digest = text[len(FACT_ID_PREFIX):]
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise CausalEvidenceError(f"{label} must contain a lowercase SHA-256 digest")
    return text


def _normalize_strings(values: Iterable[str], label: str) -> tuple[str, ...]:
    result: list[str] = []
    for raw in values:
        value = _require_string(raw, label)
        if value not in result:
            result.append(value)
    return tuple(result)


def evidence_descriptor(path: Path) -> dict[str, str]:
    """Return collision-safe evidence identity while preserving source metadata."""
    source = path.expanduser().resolve()
    if not source.is_file():
        raise CausalEvidenceError(f"evidence file is missing: {source}")
    return {
        "source_path": str(source),
        "source_name": source.name,
        "sha256": _sha256_file(source),
    }


def _authority_validation(
    path: Path | None,
    *,
    objective_id: str,
) -> dict[str, Any]:
    """Validate an existing SAGE authority receipt for the asserted objective."""
    if path is None:
        return {
            "validated": False,
            "receipt": None,
            "receipt_id": None,
            "disposition": "unvalidated",
        }

    source = path.expanduser().resolve()
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CausalEvidenceError(
            f"authority receipt is unreadable: {source}: {error}"
        ) from error
    if not isinstance(value, dict):
        raise CausalEvidenceError("authority receipt must be a JSON object")

    required_top = {
        "schema_version",
        "receipt_id",
        "request",
        "captured_at",
        "repository",
        "assertions",
        "conflicts",
        "unknowns",
        "reconciliation",
        "mutation_gate",
        "evidence_references",
    }
    missing = sorted(required_top - set(value))
    if missing:
        raise CausalEvidenceError(
            f"authority receipt is incomplete: missing={missing}"
        )
    if value.get("schema_version") != "1.0":
        raise CausalEvidenceError("authority receipt schema version is unsupported")

    raw_assertions = value.get("assertions")
    if not isinstance(raw_assertions, list) or not raw_assertions:
        raise CausalEvidenceError("authority receipt assertions are missing")
    assertions = tuple(
        AuthorityAssertion.from_mapping(item)
        for item in raw_assertions
        if isinstance(item, Mapping)
    )
    if len(assertions) != len(raw_assertions):
        raise CausalEvidenceError("authority receipt assertions are malformed")
    for assertion in assertions:
        assertion.validate()

    material_types = tuple(dict.fromkeys(
        item.authority_type
        for item in assertions
        if item.applicability == "material"
        and item.measurement_type != "unavailable"
    ))
    if not material_types:
        raise CausalEvidenceError(
            "authority receipt contains no usable material authority"
        )

    reconciled = AuthorityReconciler(material_types).reconcile(
        receipt_id=_require_string(value.get("receipt_id"), "authority.receipt_id"),
        request=_require_string(value.get("request"), "authority.request"),
        repository=value.get("repository")
        if isinstance(value.get("repository"), Mapping)
        else {},
        assertions=assertions,
        evidence_references=tuple(
            item for item in value.get("evidence_references", [])
            if isinstance(item, str)
        ),
        captured_at=_require_string(
            value.get("captured_at"),
            "authority.captured_at",
        ),
    )

    authority_objective = _require_string(objective_id, "objective_id")
    expected_action_reference = f"action:{authority_objective}"
    raw_evidence_references = value.get("evidence_references")
    if not isinstance(raw_evidence_references, list):
        raise CausalEvidenceError("authority receipt evidence_references are invalid")
    if expected_action_reference not in raw_evidence_references:
        raise CausalEvidenceError(
            "authority receipt is not applicable to objective: "
            f"{authority_objective}"
        )

    original_reconciliation = value.get("reconciliation")
    original_gate = value.get("mutation_gate")
    if not isinstance(original_reconciliation, Mapping):
        raise CausalEvidenceError("authority receipt reconciliation is invalid")
    if not isinstance(original_gate, Mapping):
        raise CausalEvidenceError("authority receipt mutation gate is invalid")

    if original_reconciliation.get("disposition") != "complete":
        raise CausalEvidenceError(
            "authority receipt is not complete"
        )
    if original_reconciliation.get("material_authority_complete") is not True:
        raise CausalEvidenceError(
            "authority receipt does not establish complete material authority"
        )
    if value.get("conflicts") not in ([], ()):
        raise CausalEvidenceError("authority receipt contains unresolved conflicts")
    if value.get("unknowns") not in ([], ()):
        raise CausalEvidenceError("authority receipt contains unresolved unknowns")
    if original_gate.get("status") != "review-ready":
        raise CausalEvidenceError("authority receipt is not review-ready")
    if reconciled.reconciliation.get("disposition") != "complete":
        raise CausalEvidenceError(
            "authority receipt does not revalidate through authority.reconcile"
        )
    if reconciled.reconciliation.get("material_authority_complete") is not True:
        raise CausalEvidenceError(
            "authority receipt revalidation is incomplete"
        )

    return {
        "validated": True,
        "receipt": evidence_descriptor(source),
        "receipt_id": _require_string(
            value.get("receipt_id"),
            "authority.receipt_id",
        ),
        "disposition": "complete",
    }


@dataclass(frozen=True)
class RecordedFact:
    fact_id: str
    path: Path
    payload: Mapping[str, Any]


class CausalEvidenceStore:
    """Immutable content-addressed fact store with derived projections."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.objects = self.root / "objects"
        self.objects.mkdir(parents=True, exist_ok=True)

    def _path_for(self, fact_id: str) -> Path:
        value = _require_fact_id(fact_id, "fact_id")
        return self.objects / (value[len(FACT_ID_PREFIX):] + ".json")

    @staticmethod
    def _identity_payload(
        *,
        objective_id: str,
        fact_type: str,
        producer: Mapping[str, str],
        authority_reference: str,
        authority_validation: Mapping[str, Any],
        dependencies: Sequence[str],
        evidence_references: Sequence[str],
        evidence_files: Sequence[Mapping[str, str]],
        attributes: Mapping[str, Any],
    ) -> dict[str, Any]:
        validated = authority_validation.get("validated")
        if not isinstance(validated, bool):
            raise CausalEvidenceError(
                "authority_validation.validated must be boolean"
            )
        receipt = authority_validation.get("receipt")
        if receipt is not None and not isinstance(receipt, Mapping):
            raise CausalEvidenceError(
                "authority_validation.receipt must be an object or null"
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "objective_id": _require_string(objective_id, "objective_id"),
            "fact_type": _require_string(fact_type, "fact_type"),
            "producer": {
                "participant_class": _require_string(
                    producer.get("participant_class"),
                    "producer.participant_class",
                ),
                "identity": _require_string(
                    producer.get("identity"),
                    "producer.identity",
                ),
            },
            "authority_reference": _require_string(
                authority_reference,
                "authority_reference",
            ),
            "authority_validation": {
                "validated": validated,
                "receipt": dict(receipt) if receipt is not None else None,
                "receipt_id": authority_validation.get("receipt_id"),
                "disposition": _require_string(
                    authority_validation.get("disposition"),
                    "authority_validation.disposition",
                ),
            },
            "dependencies": list(
                _normalize_strings(dependencies, "dependencies[]")
            ),
            "evidence_references": list(
                _normalize_strings(evidence_references, "evidence_references[]")
            ),
            "evidence_files": [dict(item) for item in evidence_files],
            "attributes": dict(attributes),
        }

    def record(
        self,
        *,
        objective_id: str,
        fact_type: str,
        producer: Mapping[str, str],
        authority_reference: str,
        authority_receipt: Path | None = None,
        dependencies: Sequence[str] = (),
        evidence_references: Sequence[str] = (),
        evidence_paths: Sequence[Path] = (),
        attributes: Mapping[str, Any] | None = None,
    ) -> RecordedFact:
        normalized_dependencies = tuple(
            _require_fact_id(item, "dependencies[]")
            for item in dependencies
        )
        for dependency in normalized_dependencies:
            if not self._path_for(dependency).is_file():
                raise CausalEvidenceError(
                    f"causal dependency does not exist: {dependency}"
                )

        descriptors = tuple(evidence_descriptor(path) for path in evidence_paths)
        authority = _authority_validation(
            authority_receipt,
            objective_id=objective_id,
        )
        identity = self._identity_payload(
            objective_id=objective_id,
            fact_type=fact_type,
            producer=producer,
            authority_reference=authority_reference,
            authority_validation=authority,
            dependencies=normalized_dependencies,
            evidence_references=evidence_references,
            evidence_files=descriptors,
            attributes=attributes or {},
        )
        digest = _sha256_bytes(_stable_json(identity))
        fact_id = FACT_ID_PREFIX + digest
        destination = self._path_for(fact_id)

        if destination.exists():
            existing = self.load(fact_id)
            if existing.get("identity") != identity:
                raise CausalEvidenceError(
                    f"fact identity collision detected: {fact_id}"
                )
            return RecordedFact(fact_id, destination, existing)

        payload = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "sage-causal-evidence-fact",
            "fact_id": fact_id,
            "recorded_at": _now(),
            "identity": identity,
        }
        encoded = json.dumps(payload, indent=2, sort_keys=False) + "\n"

        fd, raw = tempfile.mkstemp(
            prefix=".causal-fact-",
            dir=str(self.objects),
            text=True,
        )
        temp = Path(raw)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temp, destination)
            except FileExistsError:
                existing = self.load(fact_id)
                if existing.get("identity") != identity:
                    raise CausalEvidenceError(
                        f"fact identity collision detected: {fact_id}"
                    )
                return RecordedFact(fact_id, destination, existing)
            finally:
                temp.unlink(missing_ok=True)
        except Exception:
            temp.unlink(missing_ok=True)
            raise

        return RecordedFact(fact_id, destination, payload)

    def load(self, fact_id: str) -> dict[str, Any]:
        path = self._path_for(fact_id)
        if not path.is_file():
            raise CausalEvidenceError(f"fact does not exist: {fact_id}")
        value = json.loads(path.read_text(encoding="utf-8"))
        self._validate_fact(value, expected_id=fact_id)
        return value

    def _validate_fact(
        self,
        value: object,
        *,
        expected_id: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise CausalEvidenceError("causal fact must be an object")
        if value.get("schema_version") != SCHEMA_VERSION:
            raise CausalEvidenceError("causal fact schema version invalid")
        if value.get("record_type") != "sage-causal-evidence-fact":
            raise CausalEvidenceError("causal fact record type invalid")
        fact_id = _require_fact_id(value.get("fact_id"), "fact_id")
        if expected_id is not None and fact_id != expected_id:
            raise CausalEvidenceError("causal fact path/identity mismatch")
        _require_string(value.get("recorded_at"), "recorded_at")
        identity = value.get("identity")
        if not isinstance(identity, dict):
            raise CausalEvidenceError("causal fact identity must be an object")
        recomputed = FACT_ID_PREFIX + _sha256_bytes(_stable_json(identity))
        if recomputed != fact_id:
            raise CausalEvidenceError("causal fact content digest mismatch")
        self._identity_payload(
            objective_id=identity.get("objective_id"),
            fact_type=identity.get("fact_type"),
            producer=identity.get("producer", {}),
            authority_reference=identity.get("authority_reference"),
            authority_validation=identity.get("authority_validation", {}),
            dependencies=identity.get("dependencies", ()),
            evidence_references=identity.get("evidence_references", ()),
            evidence_files=identity.get("evidence_files", ()),
            attributes=identity.get("attributes", {}),
        )
        return value

    def facts(
        self,
        *,
        objective_id: str | None = None,
        as_of: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        result: list[dict[str, Any]] = []
        for path in sorted(self.objects.glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            self._validate_fact(
                value,
                expected_id=FACT_ID_PREFIX + path.stem,
            )
            identity = value["identity"]
            if objective_id is not None and identity["objective_id"] != objective_id:
                continue
            if as_of is not None and str(value["recorded_at"]) > as_of:
                continue
            result.append(value)
        return tuple(result)

    def verify(self) -> dict[str, Any]:
        facts = self.facts()
        known = {item["fact_id"] for item in facts}
        dangling: list[dict[str, str]] = []
        for fact in facts:
            for dependency in fact["identity"]["dependencies"]:
                if dependency not in known:
                    dangling.append(
                        {"fact_id": fact["fact_id"], "dependency": dependency}
                    )
        if dangling:
            raise CausalEvidenceError(
                f"dangling causal dependencies: {dangling}"
            )
        return {
            "status": "pass",
            "fact_count": len(facts),
            "root": str(self.root),
        }

    def project(
        self,
        *,
        objective_id: str,
        required_fact_types: Sequence[str],
        as_of: str | None = None,
    ) -> dict[str, Any]:
        requirements = _normalize_strings(
            required_fact_types,
            "required_fact_types[]",
        )
        facts = self.facts(objective_id=objective_id, as_of=as_of)
        by_type: dict[str, list[str]] = {}
        ignored_unvalidated: list[str] = []
        for fact in facts:
            validation = fact["identity"]["authority_validation"]
            if validation.get("validated") is not True:
                ignored_unvalidated.append(fact["fact_id"])
                continue
            by_type.setdefault(
                fact["identity"]["fact_type"],
                [],
            ).append(fact["fact_id"])
        missing = [item for item in requirements if not by_type.get(item)]
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": "sage-causal-evidence-derived-view",
            "objective_id": objective_id,
            "as_of": as_of,
            "required_fact_types": list(requirements),
            "satisfied": {
                item: sorted(by_type.get(item, []))
                for item in requirements
                if by_type.get(item)
            },
            "missing_fact_types": missing,
            "ignored_unvalidated_fact_ids": sorted(ignored_unvalidated),
            "ready": not missing,
            "fact_count": len(facts),
            "validated_fact_count": sum(len(value) for value in by_type.values()),
        }

    def lineage(self, fact_id: str) -> dict[str, Any]:
        target = self.load(fact_id)
        seen: set[str] = set()
        ordered: list[dict[str, Any]] = []

        def visit(current_id: str) -> None:
            if current_id in seen:
                return
            current = self.load(current_id)
            for dependency in current["identity"]["dependencies"]:
                visit(dependency)
            seen.add(current_id)
            ordered.append(current)

        visit(target["fact_id"])
        return {
            "schema_version": SCHEMA_VERSION,
            "record_type": "sage-causal-evidence-lineage",
            "target_fact_id": target["fact_id"],
            "objective_id": target["identity"]["objective_id"],
            "facts": ordered,
        }


def _fixture_authority_receipt(
    path: Path,
    objective_id: str = "SAGE-ACTION-FIXTURE-VALIDATED",
) -> None:
    assertions = (
        AuthorityAssertion(
            "AUTH-001",
            "git",
            "repository",
            "HEAD",
            "2026-08-27T22:00:00-05:00",
            "current",
            "git.head",
            "fixture-head",
            "measured",
            "high",
            "material",
            None,
        ),
    )
    receipt = AuthorityReconciler(("git",)).reconcile(
        receipt_id="SAGE-AUTH-FIXTURE-001",
        request="fixture",
        repository={"branch": "feature/fixture", "head": "fixture-head"},
        assertions=assertions,
        evidence_references=(f"action:{objective_id}", "fixture"),
        captured_at="2026-08-27T22:00:00-05:00",
    )
    path.write_text(
        json.dumps(receipt.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="sage-causal-evidence-") as raw:
        root = Path(raw)
        store = CausalEvidenceStore(root)
        authority_receipt = root / "authority.json"
        _fixture_authority_receipt(authority_receipt)

        left_evidence = root / "branch-a" / "receipt.json"
        right_evidence = root / "branch-b" / "receipt.json"
        left_evidence.parent.mkdir()
        right_evidence.parent.mkdir()
        left_evidence.write_text('{"branch":"a"}\n', encoding="utf-8")
        right_evidence.write_text('{"branch":"b"}\n', encoding="utf-8")

        producer = {"participant_class": "repository-workflow", "identity": "fixture"}

        unvalidated = store.record(
            objective_id="SAGE-ACTION-FIXTURE",
            fact_type="artifact-proven",
            producer=producer,
            authority_reference="fixture:mere-reference",
            evidence_paths=(left_evidence,),
        )
        unvalidated_view = store.project(
            objective_id="SAGE-ACTION-FIXTURE",
            required_fact_types=("artifact-proven",),
        )
        if unvalidated_view["ready"] is not False:
            raise RuntimeError(
                "mere authority_reference incorrectly satisfied readiness"
            )
        if unvalidated.fact_id not in unvalidated_view["ignored_unvalidated_fact_ids"]:
            raise RuntimeError("unvalidated fact was not surfaced by projection")

        wrong_authority_receipt = root / "wrong-authority.json"
        _fixture_authority_receipt(
            wrong_authority_receipt,
            "SAGE-ACTION-FIXTURE-OTHER",
        )
        try:
            store.record(
                objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
                fact_type="wrong-scope-authority",
                producer=producer,
                authority_reference="fixture:wrong-objective-authority",
                authority_receipt=wrong_authority_receipt,
                evidence_paths=(left_evidence,),
            )
        except CausalEvidenceError:
            pass
        else:
            raise RuntimeError(
                "complete authority receipt for another objective was accepted"
            )

        left = store.record(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            fact_type="artifact-proven",
            producer=producer,
            authority_reference="fixture:artifact-authority",
            authority_receipt=authority_receipt,
            evidence_paths=(left_evidence,),
        )
        right = store.record(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            fact_type="environment-qualified",
            producer=producer,
            authority_reference="fixture:environment-authority",
            authority_receipt=authority_receipt,
            evidence_paths=(right_evidence,),
        )

        before = store.project(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            required_fact_types=(
                "artifact-proven",
                "environment-qualified",
                "runtime-validated",
            ),
        )
        if before["ready"] is not False:
            raise RuntimeError("derived view became ready before convergence")

        convergence = store.record(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            fact_type="runtime-validated",
            producer=producer,
            authority_reference="fixture:runtime-authority",
            authority_receipt=authority_receipt,
            dependencies=(left.fact_id, right.fact_id),
            attributes={"result": "pass"},
        )
        after = store.project(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            required_fact_types=(
                "artifact-proven",
                "environment-qualified",
                "runtime-validated",
            ),
        )
        if after["ready"] is not True:
            raise RuntimeError(
                "validated derived view did not become ready after convergence"
            )

        lineage = store.lineage(convergence.fact_id)
        ids = [item["fact_id"] for item in lineage["facts"]]
        if (
            ids[-1] != convergence.fact_id
            or left.fact_id not in ids
            or right.fact_id not in ids
        ):
            raise RuntimeError("causal lineage reconstruction failed")

        duplicate = store.record(
            objective_id="SAGE-ACTION-FIXTURE-VALIDATED",
            fact_type="artifact-proven",
            producer=producer,
            authority_reference="fixture:artifact-authority",
            authority_receipt=authority_receipt,
            evidence_paths=(left_evidence,),
        )
        if duplicate.fact_id != left.fact_id:
            raise RuntimeError("idempotent fact identity failed")

        store.verify()

    print("PASS mere authority_reference cannot satisfy derived readiness")
    print("PASS existing authority.reconcile receipt validation gates objective truth")
    print("PASS complete authority receipt for another objective fails closed")
    print("PASS independent causal branches record without a global mutable state")
    print("PASS dependent convergence derives objective readiness")
    print("PASS immutable fact identity is content-addressed and idempotent")
    print("PASS lineage reconstructs the evidence path")
    print("PASS full fact-store replay verifies causal dependencies")
    print("Kalaxy3 SAGE causal evidence MVP self-test: PASS")
