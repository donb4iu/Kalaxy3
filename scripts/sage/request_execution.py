#!/usr/bin/env python3
"""Validate untrusted SAGE request-execution proposal packages."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"
MANIFEST_NAME = "sage-proposal.json"
PAYLOAD_PREFIX = "payload/"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SAFE_TARGET = re.compile(r"^sage-[a-z0-9][a-z0-9-]*$")
SAFE_REMOTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FORBIDDEN_TARGET_PARTS = (
    "publish",
    "deploy",
    "uninstall",
    "activate",
    "commit",
    "push",
    "merge",
    "branch-delete",
)
ALLOWED_MODES = {"0644": 0o644, "0755": 0o755}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "request_sha256",
    "repository",
    "source_files",
    "generated_paths",
    "reconcile_evidence_index",
    "evidence_references",
    "capabilities",
    "candidates",
    "new_primitive_required",
    "validation_commands",
    "operator_plan",
}


class ProposalError(RuntimeError):
    """Raised when an untrusted proposal violates the execution contract."""


@dataclass(frozen=True)
class ProposedFile:
    """One checksum-bound repository source file from a proposal package."""

    path: str
    sha256: str
    mode: int
    payload: bytes


@dataclass(frozen=True)
class ProposalBundle:
    """Validated request-execution package consumed by SAGE."""

    package_path: Path
    manifest: Mapping[str, Any]
    source_files: tuple[ProposedFile, ...]
    generated_paths: tuple[str, ...]

    @property
    def declared_paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.source_files) + self.generated_paths


def sha256_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 digest."""

    return hashlib.sha256(payload).hexdigest()


def request_sha256(request: str) -> str:
    """Bind one proposal to the exact literal request."""

    return sha256_bytes(request.encode("utf-8"))


def require_object(value: object, label: str) -> dict[str, Any]:
    """Return one JSON object or fail closed."""

    if not isinstance(value, dict):
        raise ProposalError(f"{label} must be an object")
    return dict(value)


def require_list(value: object, label: str) -> list[Any]:
    """Return one JSON array or fail closed."""

    if not isinstance(value, list):
        raise ProposalError(f"{label} must be an array")
    return list(value)


def safe_relative_path(value: object, label: str) -> str:
    """Validate one canonical repository-relative POSIX path."""

    if not isinstance(value, str) or not value:
        raise ProposalError(f"{label} must be a non-empty string")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ProposalError(f"{label} is not a safe repository-relative path: {value}")
    normalized = pure.as_posix()
    if normalized != value or value.startswith("/"):
        raise ProposalError(f"{label} is not canonical: {value}")
    return normalized


def validate_operator_plan(value: object) -> dict[str, str]:
    """Validate the deterministic operator Git lifecycle declared by a proposal."""

    payload = require_object(value, "operator_plan")
    if set(payload) != {"commit_message", "push_remote"}:
        raise ProposalError("operator_plan must contain exactly commit_message and push_remote")
    message = payload.get("commit_message")
    remote = payload.get("push_remote")
    if (
        not isinstance(message, str)
        or not message.strip()
        or len(message) > 120
        or "\n" in message
        or "\r" in message
    ):
        raise ProposalError("operator_plan.commit_message must be one non-empty line of at most 120 characters")
    if not isinstance(remote, str) or not SAFE_REMOTE.fullmatch(remote):
        raise ProposalError("operator_plan.push_remote is invalid")
    return {"commit_message": message, "push_remote": remote}


OPERATOR_RESULT_FIELDS = {
    "schema_version",
    "proposal_id",
    "command_sha256",
    "returncode",
    "pasted_output_received",
    "complete_output",
}


def validate_operator_result(value: object, proposal: Mapping[str, Any]) -> dict[str, Any]:
    """Validate untrusted pasted operator-result evidence against one proposal."""

    payload = require_object(value, "operator_result")
    if set(payload) != OPERATOR_RESULT_FIELDS:
        raise ProposalError("operator_result fields are invalid")
    if payload.get("schema_version") != "1.0":
        raise ProposalError("operator_result schema_version must be 1.0")
    if payload.get("proposal_id") != proposal.get("proposal_id"):
        raise ProposalError("operator_result proposal_id does not match the active proposal")
    command = require_object(proposal.get("command"), "proposal.command")
    if payload.get("command_sha256") != command.get("sha256"):
        raise ProposalError("operator_result command_sha256 does not match the active proposal")
    if payload.get("pasted_output_received") is not True:
        raise ProposalError("complete pasted operator output is required")
    returncode = payload.get("returncode")
    if isinstance(returncode, bool) or not isinstance(returncode, int):
        raise ProposalError("operator_result returncode must be an integer")
    output = payload.get("complete_output")
    if not isinstance(output, str):
        raise ProposalError("operator_result complete_output must be a string")
    if returncode != 0:
        raise ProposalError(f"operator command failed with returncode={returncode}")
    return {
        "schema_version": "1.0",
        "proposal_id": str(payload["proposal_id"]),
        "command_sha256": str(payload["command_sha256"]),
        "returncode": returncode,
        "pasted_output_received": True,
        "complete_output_sha256": sha256_bytes(output.encode("utf-8")),
    }


def next_operator_boundary(boundary: str) -> str | None:
    """Return the next deterministic Git boundary after successful verification."""

    order = {"stage": "commit", "commit": "push", "push": None}
    if boundary not in order:
        raise ProposalError(f"request execution cannot continue unsupported boundary: {boundary}")
    return order[boundary]


def validate_repository(value: object) -> dict[str, str]:
    """Validate the branch/head authority bound into a proposal."""

    payload = require_object(value, "repository")
    if set(payload) != {"branch", "head"}:
        raise ProposalError("repository must contain exactly branch and head")
    branch = payload.get("branch")
    head = payload.get("head")
    if not isinstance(branch, str) or not branch or branch == "main":
        raise ProposalError("proposal repository.branch must be a non-main branch")
    if not isinstance(head, str) or not GIT_OBJECT_ID.fullmatch(head):
        raise ProposalError("proposal repository.head must be a 40- or 64-character Git object id")
    return {"branch": branch, "head": head}


def validate_source_entry(value: object, index: int) -> tuple[str, str, int]:
    """Validate one source-file manifest entry."""

    item = require_object(value, f"source_files[{index}]")
    if set(item) != {"path", "sha256", "mode"}:
        raise ProposalError(f"source_files[{index}] has unexpected fields")
    path = safe_relative_path(item.get("path"), f"source_files[{index}].path")
    digest = item.get("sha256")
    mode = item.get("mode")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise ProposalError(f"source_files[{index}].sha256 is invalid")
    if mode not in ALLOWED_MODES:
        raise ProposalError(f"source_files[{index}].mode must be 0644 or 0755")
    return path, digest, ALLOWED_MODES[str(mode)]


def validate_generated_paths(values: object) -> tuple[str, ...]:
    """Validate generated repository paths reconciled by a fixed SAGE action."""

    result = tuple(
        safe_relative_path(item, f"generated_paths[{index}]")
        for index, item in enumerate(require_list(values, "generated_paths"))
    )
    if len(set(result)) != len(result):
        raise ProposalError("generated_paths contains duplicates")
    return result


def validate_validation_command(value: object, index: int) -> dict[str, Any]:
    """Allow only one shell-free, repository SAGE Make validation target."""

    item = require_object(value, f"validation_commands[{index}]")
    allowed = {"label", "argv", "timeout_seconds"}
    if set(item) - allowed or not {"label", "argv"}.issubset(item):
        raise ProposalError(f"validation_commands[{index}] fields are invalid")
    label = item.get("label")
    argv = require_list(item.get("argv"), f"validation_commands[{index}].argv")
    if not isinstance(label, str) or not label:
        raise ProposalError(f"validation_commands[{index}].label is required")
    if len(argv) != 2 or argv[0] != "make" or not isinstance(argv[1], str):
        raise ProposalError("proposal validations must be exactly: make sage-<target>")
    target = argv[1]
    if not SAFE_TARGET.fullmatch(target):
        raise ProposalError(f"unsafe SAGE validation target: {target}")
    if any(part in target for part in FORBIDDEN_TARGET_PARTS):
        raise ProposalError(f"mutating/publication validation target is forbidden: {target}")
    timeout = item.get("timeout_seconds", 600)
    if not isinstance(timeout, (int, float)) or not 1 <= float(timeout) <= 3600:
        raise ProposalError(f"validation_commands[{index}].timeout_seconds is invalid")
    return {"label": label, "argv": ["make", target], "timeout_seconds": float(timeout)}


def validate_capability(value: object, index: int) -> dict[str, Any]:
    """Validate one explicit required-capability declaration."""

    item = require_object(value, f"capabilities[{index}]")
    allowed = {"capability_id", "description", "required"}
    if set(item) != allowed:
        raise ProposalError(f"capabilities[{index}] fields are invalid")
    capability_id = item.get("capability_id")
    description = item.get("description")
    required = item.get("required")
    if not isinstance(capability_id, str) or not capability_id:
        raise ProposalError(f"capabilities[{index}].capability_id is required")
    if not isinstance(description, str) or not description:
        raise ProposalError(f"capabilities[{index}].description is required")
    if not isinstance(required, bool):
        raise ProposalError(f"capabilities[{index}].required must be boolean")
    return item


def validate_candidate(value: object, index: int) -> dict[str, Any]:
    """Validate one explicit repository component candidate."""

    item = require_object(value, f"candidates[{index}]")
    required = {
        "candidate_id", "capability_ids", "component_id", "version",
        "source_path", "maturity", "selection_factors",
        "evidence_references", "rationale",
    }
    if set(item) != required:
        raise ProposalError(f"candidates[{index}] fields are invalid")
    for key in ("candidate_id", "component_id", "version", "maturity", "rationale"):
        if not isinstance(item.get(key), str) or not item.get(key):
            raise ProposalError(f"candidates[{index}].{key} is required")
    safe_relative_path(item.get("source_path"), f"candidates[{index}].source_path")
    capabilities = require_list(item.get("capability_ids"), f"candidates[{index}].capability_ids")
    evidence = require_list(item.get("evidence_references"), f"candidates[{index}].evidence_references")
    if not capabilities or not all(isinstance(entry, str) and entry for entry in capabilities):
        raise ProposalError(f"candidates[{index}].capability_ids is invalid")
    if not all(isinstance(entry, str) and entry for entry in evidence):
        raise ProposalError(f"candidates[{index}].evidence_references is invalid")
    require_object(item.get("selection_factors"), f"candidates[{index}].selection_factors")
    return item


def validate_manifest(payload: Mapping[str, Any], request: str) -> dict[str, Any]:
    """Validate proposal metadata before any repository mutation."""

    if set(payload) != TOP_LEVEL_FIELDS:
        extra = sorted(set(payload) - TOP_LEVEL_FIELDS)
        missing = sorted(TOP_LEVEL_FIELDS - set(payload))
        raise ProposalError(f"proposal fields mismatch: missing={missing}, extra={extra}")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ProposalError("proposal schema_version must be 1.0")
    if payload.get("request_sha256") != request_sha256(request):
        raise ProposalError("proposal is not bound to the exact literal request")
    validate_repository(payload.get("repository"))
    payload["operator_plan"] = validate_operator_plan(payload.get("operator_plan"))
    if payload.get("new_primitive_required") is not False:
        raise ProposalError("request execution v1 cannot authorize a new low-level primitive")
    if not isinstance(payload.get("reconcile_evidence_index"), bool):
        raise ProposalError("reconcile_evidence_index must be boolean")
    return dict(payload)


def archive_payload(archive: zipfile.ZipFile, relative: str, expected: str) -> bytes:
    """Read one regular checksum-bound payload entry."""

    name = PAYLOAD_PREFIX + relative
    try:
        info = archive.getinfo(name)
    except KeyError as error:
        raise ProposalError(f"proposal payload is missing: {relative}") from error
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ProposalError(f"proposal payload may not be a symlink: {relative}")
    payload = archive.read(info)
    if sha256_bytes(payload) != expected:
        raise ProposalError(f"proposal payload digest mismatch: {relative}")
    return payload


def parse_sources(archive: zipfile.ZipFile, values: object) -> tuple[ProposedFile, ...]:
    """Load and verify every declared source payload."""

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
        result.append(ProposedFile(path, digest, mode, archive_payload(archive, path, digest)))
    return tuple(result)


def validate_collections(manifest: dict[str, Any]) -> None:
    """Validate capability, candidate, evidence, and command collections."""

    capabilities = [
        validate_capability(item, index)
        for index, item in enumerate(require_list(manifest["capabilities"], "capabilities"))
    ]
    candidates = [
        validate_candidate(item, index)
        for index, item in enumerate(require_list(manifest["candidates"], "candidates"))
    ]
    commands = [
        validate_validation_command(item, index)
        for index, item in enumerate(require_list(manifest["validation_commands"], "validation_commands"))
    ]
    evidence = require_list(manifest["evidence_references"], "evidence_references")
    if not capabilities or not candidates or not commands:
        raise ProposalError("capabilities, candidates, and validation_commands must be non-empty")
    if not evidence or not all(isinstance(item, str) and item for item in evidence):
        raise ProposalError("evidence_references must contain non-empty strings")
    manifest["capabilities"] = capabilities
    manifest["candidates"] = candidates
    manifest["validation_commands"] = commands
    manifest["evidence_references"] = list(dict.fromkeys(evidence))


def validate_archive_scope(archive: zipfile.ZipFile, source_files: tuple[ProposedFile, ...]) -> None:
    """Reject undeclared files or path traversal inside the ZIP."""

    expected = {MANIFEST_NAME, *(PAYLOAD_PREFIX + item.path for item in source_files)}
    observed: set[str] = set()
    for info in archive.infolist():
        if info.is_dir():
            continue
        safe_relative_path(info.filename, "archive member")
        observed.add(info.filename)
    if observed != expected:
        raise ProposalError(
            f"proposal archive scope mismatch: expected={sorted(expected)}, observed={sorted(observed)}"
        )


def load_proposal(path: Path, request: str) -> ProposalBundle:
    """Load one checksum-bound, fail-closed request execution proposal."""

    package = path.expanduser().resolve()
    if not package.is_file():
        raise ProposalError(f"proposal package is missing: {package}")
    with zipfile.ZipFile(package) as archive:
        try:
            raw_manifest = json.loads(archive.read(MANIFEST_NAME))
        except KeyError as error:
            raise ProposalError(f"proposal archive lacks {MANIFEST_NAME}") from error
        manifest = validate_manifest(require_object(raw_manifest, MANIFEST_NAME), request)
        validate_collections(manifest)
        source_files = parse_sources(archive, manifest["source_files"])
        generated = validate_generated_paths(manifest["generated_paths"])
        if set(generated) & {item.path for item in source_files}:
            raise ProposalError("generated_paths overlap source_files")
        if generated and manifest["reconcile_evidence_index"] is not True:
            raise ProposalError("generated_paths require reconcile_evidence_index=true")
        validate_archive_scope(archive, source_files)
    return ProposalBundle(package, manifest, source_files, generated)
