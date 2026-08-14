#!/usr/bin/env python3
"""Engineering-contribution and semantic-understanding contracts for SAGE."""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from request_execution import ProposedFile, ProposalError, safe_relative_path, sha256_bytes

CONTRIBUTION_MANIFEST = "engineering-contribution.json"
PAYLOAD_PREFIX = "payload/"
CONTRIBUTION_FIELDS = {
    "schema_version",
    "contribution_id",
    "contributor",
    "summary",
    "rationale",
    "assumptions",
    "alternatives",
    "files",
}


def stable_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class EngineeringContribution:
    package_path: Path
    package_sha256: str
    manifest: Mapping[str, Any]
    source_files: tuple[ProposedFile, ...]

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(item.path for item in self.source_files)


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProposalError(f"{label} must be a non-empty string")
    return value.strip()


def _validate_manifest(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProposalError("engineering contribution manifest must be an object")
    if set(value) != CONTRIBUTION_FIELDS:
        raise ProposalError("engineering contribution fields are invalid")
    if value.get("schema_version") != "1.0":
        raise ProposalError("engineering contribution schema_version must be 1.0")
    _require_string(value.get("contribution_id"), "contribution_id")
    contributor = value.get("contributor")
    if not isinstance(contributor, dict):
        raise ProposalError("contributor must be an object")
    participant = _require_string(contributor.get("participant_class"), "contributor.participant_class")
    if participant not in {"human", "llm"}:
        raise ProposalError("contributor.participant_class must be human or llm")
    _require_string(contributor.get("identity"), "contributor.identity")
    _require_string(value.get("summary"), "summary")
    _require_string(value.get("rationale"), "rationale")
    for field in ("assumptions", "alternatives"):
        items = value.get(field)
        if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
            raise ProposalError(f"{field} must contain only non-empty strings")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise ProposalError("files must contain at least one proposed repository file")
    seen: set[str] = set()
    for index, item in enumerate(files):
        if not isinstance(item, dict) or set(item) != {"path", "mode"}:
            raise ProposalError(f"files[{index}] must contain path and mode only")
        path = _require_string(item.get("path"), f"files[{index}].path")
        safe_relative_path(path, f"files[{index}].path")
        if path in seen:
            raise ProposalError(f"duplicate contribution path: {path}")
        if path in {"sage-improvement-actions.json", "sage-source.json"}:
            raise ProposalError(f"engineering contribution may not author SAGE control artifact: {path}")
        seen.add(path)
        if item.get("mode") not in {"0644", "0755"}:
            raise ProposalError(f"files[{index}].mode must be 0644 or 0755")
    return dict(value)


def load_engineering_contribution(path: Path) -> EngineeringContribution:
    package = path.expanduser().resolve()
    if not package.is_file():
        raise ProposalError(f"engineering contribution package is missing: {package}")
    with zipfile.ZipFile(package) as archive:
        try:
            manifest = _validate_manifest(json.loads(archive.read(CONTRIBUTION_MANIFEST)))
        except KeyError as error:
            raise ProposalError(f"engineering contribution lacks {CONTRIBUTION_MANIFEST}") from error
        expected = {CONTRIBUTION_MANIFEST}
        source_files: list[ProposedFile] = []
        for item in manifest["files"]:
            relative = str(item["path"])
            name = PAYLOAD_PREFIX + relative
            expected.add(name)
            try:
                info = archive.getinfo(name)
            except KeyError as error:
                raise ProposalError(f"engineering contribution payload is missing: {relative}") from error
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ProposalError(f"engineering contribution payload may not be a symlink: {relative}")
            payload = archive.read(info)
            declared_mode = int(str(item["mode"]), 8)
            source_files.append(ProposedFile(relative, sha256_bytes(payload), declared_mode, payload))
        observed = {info.filename for info in archive.infolist() if not info.is_dir()}
        if observed != expected:
            raise ProposalError(
                f"engineering contribution scope mismatch: expected={sorted(expected)}, observed={sorted(observed)}"
            )
    return EngineeringContribution(package, sha256_file(package), manifest, tuple(source_files))


def action_record_sha256(action: Mapping[str, Any]) -> str:
    return hashlib.sha256(stable_json(dict(action)).encode("utf-8")).hexdigest()
