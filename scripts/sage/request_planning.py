#!/usr/bin/env python3
"""Validate source-only planning inputs and emit executor-compatible proposals."""

from __future__ import annotations

import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from request_execution import (
    HEX64,
    MANIFEST_NAME,
    PAYLOAD_PREFIX,
    ProposedFile,
    ProposalBundle,
    ProposalError,
    load_proposal,
    request_sha256,
    require_list,
    require_object,
    safe_relative_path,
    sha256_bytes,
    validate_generated_paths,
    validate_operator_plan,
    validate_repository,
    validate_source_entry,
    validate_validation_command,
)

SOURCE_MANIFEST_NAME = "sage-source.json"
SOURCE_FIELDS_V1_0 = {
    "schema_version",
    "request_sha256",
    "repository",
    "source_files",
    "generated_paths",
    "reconcile_evidence_index",
    "evidence_references",
    "validation_commands",
    "operator_plan",
}
SOURCE_FIELDS_V1_1 = SOURCE_FIELDS_V1_0 | {"semantic_authority"}
SOURCE_FIELDS_V1_2 = SOURCE_FIELDS_V1_1
SOURCE_FIELDS_V1_3 = SOURCE_FIELDS_V1_2
SEMANTIC_UNDERSTANDING_NAME = "semantic/semantic-understanding.json"
SEMANTIC_CONFIRMATION_NAME = "semantic/semantic-confirmation.json"



@dataclass(frozen=True)
class PlanningSourceBundle:
    """Checksum-bound source content awaiting repository-owned planning."""

    package_path: Path
    manifest: Mapping[str, Any]
    source_files: tuple[ProposedFile, ...]
    generated_paths: tuple[str, ...]

    @property
    def declared_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.source_files) + self.generated_paths

    @property
    def semantic_authority(self) -> Mapping[str, Any] | None:
        value = self.manifest.get("semantic_authority")
        return value if isinstance(value, Mapping) else None


def _context_map(repo: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    payload = require_object(
        json.loads((repo / "sage-change-authority.json").read_text(encoding="utf-8")),
        "sage-change-authority.json",
    )
    contexts = {
        str(item["id"]): item
        for item in payload.get("contexts", [])
        if isinstance(item, dict) and item.get("id")
    }
    always = tuple(str(item) for item in payload.get("always_contexts", []))
    return contexts, always


def _path_matches(prefix: str, path: str) -> bool:
    return path == prefix or path.startswith(prefix)


def derive_applicable_contexts(repo: Path, proposed_paths: tuple[str, ...]) -> tuple[str, ...]:
    """Derive path/dependency contexts used by semantic understanding and planning."""

    contexts, always = _context_map(repo)
    selected = set(always)
    for context_id, context in contexts.items():
        prefixes = tuple(str(item) for item in context.get("path_prefixes", []))
        if any(_path_matches(prefix, path) for prefix in prefixes for path in proposed_paths):
            selected.add(context_id)
    changed = True
    while changed:
        changed = False
        for context_id in tuple(selected):
            context = contexts.get(context_id, {})
            for required in context.get("requires", []):
                if required not in selected:
                    selected.add(str(required))
                    changed = True
    ordered = [item for item in always if item in selected]
    ordered.extend(sorted(selected - set(ordered)))
    return tuple(ordered)


SEMANTIC_APPLICABLE_DISPOSITIONS = {
    "applicable",  # v1.0 compatibility
    "applicable-now",
    "applicable-now-no-proposed-source-mutation",
    "applicable-by-proposed-path-or-dependency",
}


def reconcile_semantic_contexts(
    repo: Path,
    inferred_contexts: tuple[str, ...],
    proposed_paths: tuple[str, ...],
) -> dict[str, Any]:
    """Preserve semantic applicability without conflating it with mutation scope."""

    inferred = tuple(dict.fromkeys(str(item) for item in inferred_contexts))
    implementation = derive_applicable_contexts(repo, proposed_paths)
    applicable = tuple(dict.fromkeys((*inferred, *implementation)))
    dispositions: list[dict[str, str]] = []
    for context_id in applicable:
        if context_id in inferred and context_id in implementation:
            disposition = "applicable-now"
        elif context_id in inferred:
            disposition = "applicable-now-no-proposed-source-mutation"
        else:
            disposition = "applicable-by-proposed-path-or-dependency"
        dispositions.append({"context_id": context_id, "disposition": disposition})
    return {
        "applicable_contexts": applicable,
        "implementation_contexts": implementation,
        "context_dispositions": tuple(dispositions),
    }


def resolve_context_authorities(repo: Path, context_ids: tuple[str, ...]) -> tuple[str, ...]:
    """Resolve exact authority files for an already-governed context set without expansion."""

    contexts, always = _context_map(repo)
    if not context_ids or len(set(context_ids)) != len(context_ids):
        raise ProposalError("semantic authority contexts must be non-empty and unique")
    missing_always = [item for item in always if item not in context_ids]
    if missing_always:
        raise ProposalError(f"semantic authority omits always contexts: {missing_always}")
    authorities: set[str] = set()
    selected = set(context_ids)
    for context_id in context_ids:
        context = contexts.get(context_id)
        if not isinstance(context, Mapping):
            raise ProposalError(f"semantic authority context is unknown: {context_id}")
        missing_requires = [str(item) for item in context.get("requires", []) if str(item) not in selected]
        if missing_requires:
            raise ProposalError(
                f"semantic authority context {context_id} omits required contexts: {missing_requires}"
            )
        for raw in context.get("authoritative_files", []):
            relative = str(raw)
            parts = Path(relative).parts
            if Path(relative).is_absolute() or ".." in parts:
                raise ProposalError(f"unsafe semantic authority path: {relative}")
            path = repo / relative
            if not path.exists():
                raise ProposalError(f"semantic authority path is missing: {relative}")
            if path.is_file():
                path.read_bytes()
            authorities.add(relative)
    return tuple(sorted(authorities))


def _semantic_artifact_payload(value: bytes, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ProposalError(f"{label} is not valid JSON") from error
    return dict(require_object(parsed, label))


def _validate_planning_obligations(values: object) -> list[dict[str, Any]]:
    obligations = require_list(values, "semantic planning_obligations")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(obligations):
        item = require_object(raw, f"semantic planning_obligations[{index}]")
        expected = {"obligation_id", "kind", "description", "required", "capability_id", "source"}
        if set(item) != expected:
            raise ProposalError("semantic planning obligation fields are invalid")
        obligation_id = item.get("obligation_id")
        kind = item.get("kind")
        description = item.get("description")
        source = item.get("source")
        required = item.get("required")
        capability_id = item.get("capability_id")
        if not all(isinstance(value, str) and value for value in (obligation_id, kind, description, source)):
            raise ProposalError("semantic planning obligation string values are invalid")
        if obligation_id in seen:
            raise ProposalError("semantic planning obligation identifiers must be unique")
        seen.add(str(obligation_id))
        if not isinstance(required, bool):
            raise ProposalError("semantic planning obligation required must be boolean")
        if kind == "capability":
            if not isinstance(capability_id, str) or not capability_id:
                raise ProposalError("semantic capability obligation requires capability_id")
        elif capability_id is not None:
            raise ProposalError("semantic non-capability obligation may not set capability_id")
        normalized.append({
            "obligation_id": str(obligation_id),
            "kind": str(kind),
            "description": str(description),
            "required": required,
            "capability_id": capability_id,
            "source": str(source),
        })
    return normalized


def _validate_semantic_artifacts(
    understanding_bytes: bytes,
    confirmation_bytes: bytes,
    request: str,
    declared_paths: tuple[str, ...],
) -> dict[str, Any]:
    understanding = _semantic_artifact_payload(understanding_bytes, "semantic understanding")
    confirmation = _semantic_artifact_payload(confirmation_bytes, "semantic confirmation")
    if understanding.get("schema_version") != "1.0" or understanding.get("record_type") != "sage-semantic-understanding":
        raise ProposalError("semantic understanding version/type is invalid")
    if understanding.get("literal_request") != request:
        raise ProposalError("semantic understanding literal request mismatch")
    action = require_object(understanding.get("action"), "semantic understanding action")
    if action.get("status") != "accepted" or not isinstance(action.get("action_id"), str):
        raise ProposalError("semantic understanding action is not accepted")
    interpretation = require_object(understanding.get("interpretation"), "semantic understanding interpretation")
    scope = require_list(interpretation.get("implementation_scope"), "semantic implementation_scope")
    if tuple(scope) != declared_paths:
        raise ProposalError("semantic implementation scope does not equal planning source scope")
    applicable = require_list(interpretation.get("applicable_contexts"), "semantic applicable_contexts")
    if not applicable or not all(isinstance(item, str) and item for item in applicable) or len(set(applicable)) != len(applicable):
        raise ProposalError("semantic applicable_contexts must be non-empty unique strings")
    has_implementation_contexts = "implementation_contexts" in interpretation
    implementation_raw = interpretation.get("implementation_contexts", applicable)
    implementation = require_list(implementation_raw, "semantic implementation_contexts")
    if not implementation or not all(isinstance(item, str) and item for item in implementation) or len(set(implementation)) != len(implementation):
        raise ProposalError("semantic implementation_contexts must be non-empty unique strings")
    if not set(implementation).issubset(set(applicable)):
        raise ProposalError("semantic implementation_contexts must be a subset of applicable_contexts")
    dispositions_raw = require_list(interpretation.get("context_dispositions"), "semantic context_dispositions")
    dispositions: list[dict[str, str]] = []
    for index, raw in enumerate(dispositions_raw):
        item = require_object(raw, f"semantic context_dispositions[{index}]")
        if set(item) != {"context_id", "disposition"}:
            raise ProposalError("semantic context disposition fields are invalid")
        context_id = item.get("context_id")
        disposition = item.get("disposition")
        if not isinstance(context_id, str) or not context_id or not isinstance(disposition, str) or not disposition:
            raise ProposalError("semantic context disposition values are invalid")
        dispositions.append({"context_id": context_id, "disposition": disposition})
    if len({item["context_id"] for item in dispositions}) != len(dispositions):
        raise ProposalError("semantic context dispositions contain duplicate context ids")
    disposition_map = {item["context_id"]: item["disposition"] for item in dispositions}
    if not set(applicable).issubset(set(disposition_map)):
        raise ProposalError("semantic context dispositions must cover every applicable context")
    if any(disposition_map[item] not in SEMANTIC_APPLICABLE_DISPOSITIONS for item in applicable):
        raise ProposalError("semantic applicable context has a non-applicable disposition")
    understanding_sha = sha256_bytes(understanding_bytes)
    confirmation_sha = sha256_bytes(confirmation_bytes)
    if confirmation.get("schema_version") != "1.0" or confirmation.get("record_type") != "sage-semantic-confirmation":
        raise ProposalError("semantic confirmation version/type is invalid")
    if confirmation.get("actor_role") != "architect" or confirmation.get("meaning") != "architect-confirmed":
        raise ProposalError("semantic confirmation lacks Architect meaning authority")
    if confirmation.get("action_id") != action.get("action_id"):
        raise ProposalError("semantic confirmation action mismatch")
    if confirmation.get("semantic_understanding_sha256") != understanding_sha:
        raise ProposalError("semantic confirmation does not bind the embedded understanding")
    planning_obligations = None
    if "planning_obligations" in interpretation:
        planning_obligations = _validate_planning_obligations(
            interpretation.get("planning_obligations")
        )
    authority = {
        "semantic_understanding_sha256": understanding_sha,
        "semantic_confirmation_sha256": confirmation_sha,
        "applicable_contexts": list(applicable),
        "context_dispositions": dispositions,
    }
    if has_implementation_contexts:
        authority["implementation_contexts"] = list(implementation)
    if planning_obligations is not None:
        authority["planning_obligations"] = planning_obligations
    return authority


def resolve_planning_authority(repo: Path, source: PlanningSourceBundle, discovery: Any) -> dict[str, Any]:
    """Resolve planner authority, preserving Architect-confirmed semantics when present."""

    raw_contexts = tuple(str(item) for item in discovery.contexts)
    semantic = source.semantic_authority
    if semantic is None:
        return {
            "authority_mode": "literal-discovery",
            "raw_inferred_contexts": list(raw_contexts),
            "contexts": list(raw_contexts),
            "authoritative_files": list(discovery.authorities),
            "semantic_authority": None,
        }
    confirmed_applicable = tuple(str(item) for item in semantic["applicable_contexts"])
    confirmed_implementation = tuple(
        str(item) for item in semantic.get("implementation_contexts", confirmed_applicable)
    )
    dispositions = tuple(semantic["context_dispositions"])
    disposition_ids = {str(item["context_id"]) for item in dispositions}
    unexpected = sorted(set(raw_contexts) - disposition_ids)
    if unexpected:
        raise ProposalError(
            "literal discovery found contexts absent from Architect-confirmed semantic dispositions; "
            f"return to semantic confirmation: {unexpected}"
        )
    derived = derive_applicable_contexts(repo, source.declared_paths)
    if derived != confirmed_implementation:
        raise ProposalError(
            "Architect-confirmed implementation contexts no longer match current path/dependency authority; "
            "return to semantic confirmation"
        )
    authorities = resolve_context_authorities(repo, confirmed_implementation)
    return {
        "authority_mode": "architect-confirmed-semantic",
        "raw_inferred_contexts": list(raw_contexts),
        "contexts": list(confirmed_implementation),
        "applicable_contexts": list(confirmed_applicable),
        "authoritative_files": list(authorities),
        "semantic_authority": dict(semantic),
    }


def _archive_payload(archive: zipfile.ZipFile, relative: str, expected: str) -> bytes:
    name = PAYLOAD_PREFIX + relative
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise ProposalError(f"planning source payload is missing: {relative}") from error
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ProposalError(f"planning source payload may not be a symlink: {relative}")
    payload = archive.read(info)
    if sha256_bytes(payload) != expected:
        raise ProposalError(f"planning source payload digest mismatch: {relative}")
    return payload


def _parse_sources(archive: zipfile.ZipFile, values: object) -> tuple[ProposedFile, ...]:
    entries = require_list(values, "source_files")
    if not entries:
        raise ProposalError("source_files must not be empty")
    result: list[ProposedFile] = []
    seen: set[str] = set()
    for index, raw in enumerate(entries):
        path, digest, mode = validate_source_entry(raw, index)
        if path in seen:
            raise ProposalError(f"duplicate source path: {path}")
        seen.add(path)
        result.append(ProposedFile(path, digest, mode, _archive_payload(archive, path, digest)))
    return tuple(result)


def _validate_scope(
    archive: zipfile.ZipFile,
    source_files: tuple[ProposedFile, ...],
    manifest: Mapping[str, Any],
) -> None:
    expected = {SOURCE_MANIFEST_NAME, *(PAYLOAD_PREFIX + item.path for item in source_files)}
    if manifest.get("schema_version") in {"1.1", "1.2", "1.3"}:
        expected.update({SEMANTIC_UNDERSTANDING_NAME, SEMANTIC_CONFIRMATION_NAME})
    observed = set()
    for info in archive.infolist():
        if info.is_dir():
            continue
        safe_relative_path(info.filename, "planning source archive member")
        observed.add(info.filename)
    if observed != expected:
        raise ProposalError(
            f"planning source archive scope mismatch: expected={sorted(expected)}, observed={sorted(observed)}"
        )


def _validate_manifest(payload: Mapping[str, Any], request: str) -> dict[str, Any]:
    version = payload.get("schema_version")
    if version == "1.0":
        expected_fields = SOURCE_FIELDS_V1_0
    elif version == "1.1":
        expected_fields = SOURCE_FIELDS_V1_1
    elif version == "1.2":
        expected_fields = SOURCE_FIELDS_V1_2
    elif version == "1.3":
        expected_fields = SOURCE_FIELDS_V1_3
    else:
        raise ProposalError("planning source schema_version must be 1.0, 1.1, 1.2, or 1.3")
    if set(payload) != expected_fields:
        raise ProposalError(
            f"planning source fields mismatch: missing={sorted(expected_fields - set(payload))}, "
            f"extra={sorted(set(payload) - expected_fields)}"
        )
    if payload.get("request_sha256") != request_sha256(request):
        raise ProposalError("planning source is not bound to the exact literal request")
    validate_repository(payload.get("repository"))
    payload = dict(payload)
    payload["operator_plan"] = validate_operator_plan(payload.get("operator_plan"))
    if not isinstance(payload.get("reconcile_evidence_index"), bool):
        raise ProposalError("reconcile_evidence_index must be boolean")
    commands = [
        validate_validation_command(item, index)
        for index, item in enumerate(require_list(payload["validation_commands"], "validation_commands"))
    ]
    if not commands:
        raise ProposalError("validation_commands must not be empty")
    evidence = require_list(payload["evidence_references"], "evidence_references")
    if not evidence or not all(isinstance(item, str) and item for item in evidence):
        raise ProposalError("evidence_references must contain non-empty strings")
    payload["validation_commands"] = commands
    payload["evidence_references"] = list(dict.fromkeys(evidence))
    if version in {"1.1", "1.2", "1.3"}:
        semantic = require_object(payload.get("semantic_authority"), "semantic_authority")
        expected_semantic = {
            "semantic_understanding_sha256",
            "semantic_confirmation_sha256",
            "applicable_contexts",
            "context_dispositions",
        }
        if version in {"1.2", "1.3"}:
            expected_semantic.add("implementation_contexts")
        if version == "1.3":
            expected_semantic.add("planning_obligations")
        if set(semantic) != expected_semantic:
            raise ProposalError("semantic_authority fields are invalid")
        for field in ("semantic_understanding_sha256", "semantic_confirmation_sha256"):
            value = semantic.get(field)
            if not isinstance(value, str) or HEX64.fullmatch(value) is None:
                raise ProposalError(f"semantic_authority {field} is invalid")
        applicable = require_list(semantic.get("applicable_contexts"), "semantic_authority.applicable_contexts")
        if not applicable or not all(isinstance(item, str) and item for item in applicable) or len(set(applicable)) != len(applicable):
            raise ProposalError("semantic_authority applicable_contexts are invalid")
        if version in {"1.2", "1.3"}:
            implementation = require_list(semantic.get("implementation_contexts"), "semantic_authority.implementation_contexts")
            if not implementation or not all(isinstance(item, str) and item for item in implementation) or len(set(implementation)) != len(implementation):
                raise ProposalError("semantic_authority implementation_contexts are invalid")
            if not set(implementation).issubset(set(applicable)):
                raise ProposalError("semantic_authority implementation_contexts must be a subset of applicable_contexts")
        dispositions = require_list(semantic.get("context_dispositions"), "semantic_authority.context_dispositions")
        if not dispositions:
            raise ProposalError("semantic_authority context_dispositions are required")
        normalized_semantic = {
            "semantic_understanding_sha256": str(semantic["semantic_understanding_sha256"]),
            "semantic_confirmation_sha256": str(semantic["semantic_confirmation_sha256"]),
            "applicable_contexts": list(applicable),
            "context_dispositions": [dict(require_object(item, "semantic context disposition")) for item in dispositions],
        }
        if version in {"1.2", "1.3"}:
            normalized_semantic["implementation_contexts"] = list(implementation)
        if version == "1.3":
            normalized_semantic["planning_obligations"] = _validate_planning_obligations(
                semantic.get("planning_obligations")
            )
        payload["semantic_authority"] = normalized_semantic
    return payload


def write_source_package(
    path: Path,
    request: str,
    *,
    repository: Mapping[str, Any],
    source_files: tuple[ProposedFile, ...],
    generated_paths: tuple[str, ...] = (),
    reconcile_evidence_index: bool = False,
    evidence_references: list[str],
    validation_commands: list[Mapping[str, Any]],
    operator_plan: Mapping[str, Any],
    semantic_understanding_path: Path | None = None,
    semantic_confirmation_path: Path | None = None,
) -> PlanningSourceBundle:
    """Write a canonical planning source without caller-authored sage-source.json."""

    if not source_files:
        raise ProposalError("repository-owned planning source must contain source files")
    if (semantic_understanding_path is None) != (semantic_confirmation_path is None):
        raise ProposalError("semantic planning source requires both understanding and confirmation")
    declared_paths = tuple(item.path for item in source_files) + tuple(generated_paths)
    semantic_authority = None
    understanding_bytes = None
    confirmation_bytes = None
    schema_version = "1.0"
    if semantic_understanding_path is not None and semantic_confirmation_path is not None:
        understanding_file = semantic_understanding_path.expanduser().resolve()
        confirmation_file = semantic_confirmation_path.expanduser().resolve()
        if not understanding_file.is_file() or not confirmation_file.is_file():
            raise ProposalError("semantic planning-source artifacts are missing")
        understanding_bytes = understanding_file.read_bytes()
        confirmation_bytes = confirmation_file.read_bytes()
        semantic_authority = _validate_semantic_artifacts(
            understanding_bytes,
            confirmation_bytes,
            request,
            declared_paths,
        )
        if "planning_obligations" in semantic_authority:
            schema_version = "1.3"
        else:
            schema_version = "1.2" if "implementation_contexts" in semantic_authority else "1.1"
    manifest_input: dict[str, Any] = {
        "schema_version": schema_version,
        "request_sha256": request_sha256(request),
        "repository": dict(repository),
        "source_files": [
            {"path": item.path, "sha256": item.sha256, "mode": f"{item.mode:04o}"}
            for item in source_files
        ],
        "generated_paths": list(generated_paths),
        "reconcile_evidence_index": reconcile_evidence_index,
        "evidence_references": list(evidence_references),
        "validation_commands": [dict(item) for item in validation_commands],
        "operator_plan": dict(operator_plan),
    }
    if semantic_authority is not None:
        manifest_input["semantic_authority"] = semantic_authority
    manifest = _validate_manifest(manifest_input, request)
    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ProposalError(f"planning source package already exists: {destination}")
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(SOURCE_MANIFEST_NAME, json.dumps(manifest, indent=2) + "\n")
        if understanding_bytes is not None and confirmation_bytes is not None:
            archive.writestr(SEMANTIC_UNDERSTANDING_NAME, understanding_bytes)
            archive.writestr(SEMANTIC_CONFIRMATION_NAME, confirmation_bytes)
        for item in source_files:
            info = zipfile.ZipInfo(PAYLOAD_PREFIX + item.path)
            info.external_attr = (stat.S_IFREG | item.mode) << 16
            archive.writestr(info, item.payload)
    return load_source_bundle(destination, request)


def load_source_bundle(path: Path, request: str) -> PlanningSourceBundle:
    """Load one source-only package without caller-authored planning semantics."""

    package = path.expanduser().resolve()
    if not package.is_file():
        raise ProposalError(f"planning source package is missing: {package}")
    with zipfile.ZipFile(package) as archive:
        try:
            raw_manifest = json.loads(archive.read(SOURCE_MANIFEST_NAME))
        except KeyError as error:
            raise ProposalError(f"planning source archive lacks {SOURCE_MANIFEST_NAME}") from error
        manifest = _validate_manifest(require_object(raw_manifest, SOURCE_MANIFEST_NAME), request)
        source_files = _parse_sources(archive, manifest["source_files"])
        generated = validate_generated_paths(manifest["generated_paths"])
        if set(generated) & {item.path for item in source_files}:
            raise ProposalError("generated_paths overlap source_files")
        if generated and manifest["reconcile_evidence_index"] is not True:
            raise ProposalError("generated_paths require reconcile_evidence_index=true")
        _validate_scope(archive, source_files, manifest)
        if manifest.get("schema_version") in {"1.1", "1.2", "1.3"}:
            try:
                understanding_bytes = archive.read(SEMANTIC_UNDERSTANDING_NAME)
                confirmation_bytes = archive.read(SEMANTIC_CONFIRMATION_NAME)
            except KeyError as error:
                raise ProposalError("semantic planning source artifacts are missing") from error
            declared_paths = tuple(item.path for item in source_files) + generated
            observed = _validate_semantic_artifacts(
                understanding_bytes,
                confirmation_bytes,
                request,
                declared_paths,
            )
            if observed != manifest.get("semantic_authority"):
                raise ProposalError("semantic planning source manifest/artifact authority mismatch")
    return PlanningSourceBundle(package, manifest, source_files, generated)


def proposal_manifest(
    source: PlanningSourceBundle,
    *,
    capabilities: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    evidence_references: list[str],
) -> dict[str, Any]:
    """Construct the existing executor proposal schema from a planned source package."""

    return {
        "schema_version": "1.0",
        "request_sha256": source.manifest["request_sha256"],
        "repository": dict(source.manifest["repository"]),
        "source_files": [
            {"path": item.path, "sha256": item.sha256, "mode": f"{item.mode:04o}"}
            for item in source.source_files
        ],
        "generated_paths": list(source.generated_paths),
        "reconcile_evidence_index": bool(source.manifest["reconcile_evidence_index"]),
        "evidence_references": list(dict.fromkeys(evidence_references)),
        "capabilities": capabilities,
        "candidates": candidates,
        "new_primitive_required": False,
        "validation_commands": list(source.manifest["validation_commands"]),
        "operator_plan": dict(source.manifest["operator_plan"]),
    }


def write_proposal_package(
    path: Path,
    source: PlanningSourceBundle,
    *,
    capabilities: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    evidence_references: list[str],
    request: str,
) -> ProposalBundle:
    """Write and re-parse one executor-compatible proposal package."""

    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    manifest = proposal_manifest(
        source,
        capabilities=capabilities,
        candidates=candidates,
        evidence_references=evidence_references,
    )
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2) + "\n")
        for item in source.source_files:
            info = zipfile.ZipInfo(PAYLOAD_PREFIX + item.path)
            info.external_attr = (stat.S_IFREG | item.mode) << 16
            archive.writestr(info, item.payload)
    return load_proposal(destination, request)


def reuse_confirmed_source_package(
    path: Path,
    prior_source_path: Path,
    request: str,
    *,
    repository: Mapping[str, Any],
    source_files: tuple[ProposedFile, ...],
    evidence_reference: str,
) -> PlanningSourceBundle:
    """Rebind changed bytes to unchanged confirmed semantics without rediscovery."""

    prior = load_source_bundle(prior_source_path, request)
    if prior.semantic_authority is None:
        raise ProposalError("implementation-local iteration requires confirmed semantic authority")
    expected_paths = tuple(item.path for item in prior.source_files)
    observed_paths = tuple(item.path for item in source_files)
    if observed_paths != expected_paths:
        raise ProposalError(
            "implementation-local iteration changed governed file scope; return to semantic confirmation"
        )
    with zipfile.ZipFile(prior.package_path) as archive:
        understanding_bytes = archive.read(SEMANTIC_UNDERSTANDING_NAME)
        confirmation_bytes = archive.read(SEMANTIC_CONFIRMATION_NAME)
    observed_authority = _validate_semantic_artifacts(
        understanding_bytes,
        confirmation_bytes,
        request,
        observed_paths + tuple(prior.generated_paths),
    )
    if observed_authority != prior.semantic_authority:
        raise ProposalError("prior confirmed semantic authority no longer validates")
    manifest_input = dict(prior.manifest)
    manifest_input["repository"] = dict(repository)
    manifest_input["source_files"] = [
        {"path": item.path, "sha256": item.sha256, "mode": f"{item.mode:04o}"}
        for item in source_files
    ]
    manifest_input["evidence_references"] = list(
        dict.fromkeys([*prior.manifest["evidence_references"], evidence_reference])
    )
    manifest = _validate_manifest(manifest_input, request)
    destination = path.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ProposalError(f"planning source package already exists: {destination}")
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(SOURCE_MANIFEST_NAME, json.dumps(manifest, indent=2) + "\n")
        archive.writestr(SEMANTIC_UNDERSTANDING_NAME, understanding_bytes)
        archive.writestr(SEMANTIC_CONFIRMATION_NAME, confirmation_bytes)
        for item in source_files:
            info = zipfile.ZipInfo(PAYLOAD_PREFIX + item.path)
            info.external_attr = (stat.S_IFREG | item.mode) << 16
            archive.writestr(info, item.payload)
    return load_source_bundle(destination, request)
