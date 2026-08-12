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
SOURCE_FIELDS = {
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


def _validate_scope(archive: zipfile.ZipFile, source_files: tuple[ProposedFile, ...]) -> None:
    expected = {SOURCE_MANIFEST_NAME, *(PAYLOAD_PREFIX + item.path for item in source_files)}
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
    if set(payload) != SOURCE_FIELDS:
        raise ProposalError(
            f"planning source fields mismatch: missing={sorted(SOURCE_FIELDS - set(payload))}, "
            f"extra={sorted(set(payload) - SOURCE_FIELDS)}"
        )
    if payload.get("schema_version") != "1.0":
        raise ProposalError("planning source schema_version must be 1.0")
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
    return payload


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
        _validate_scope(archive, source_files)
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
