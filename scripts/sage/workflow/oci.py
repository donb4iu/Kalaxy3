"""Read-only OCI image-layout archive inspection for SAGE stage and promotion workflows."""

from __future__ import annotations

import hashlib
import json
import re
import tarfile
from pathlib import Path
from typing import Any, Mapping

from .model import WorkflowError

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_INDEX_MEDIA_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkflowError(f"{label} must be an object")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be a non-empty string")
    return value.strip()


def _read_member(archive: tarfile.TarFile, name: str) -> bytes:
    try:
        info = archive.getmember(name)
    except KeyError as error:
        raise WorkflowError(f"OCI archive is missing {name}") from error
    if not info.isfile():
        raise WorkflowError(f"OCI archive member is not a regular file: {name}")
    handle = archive.extractfile(info)
    if handle is None:
        raise WorkflowError(f"OCI archive member is unreadable: {name}")
    payload = handle.read()
    if len(payload) > 16 * 1024 * 1024:
        raise WorkflowError(f"OCI archive metadata member is unexpectedly large: {name}")
    return payload


def _require_digest_blob(archive: tarfile.TarFile, digest: str, label: str) -> bytes:
    value = _string(digest, label)
    if not _DIGEST.fullmatch(value):
        raise WorkflowError(f"{label} must be sha256:<64 lowercase hex>")
    name = "blobs/sha256/" + value.removeprefix("sha256:")
    payload = _read_member(archive, name)
    observed = "sha256:" + hashlib.sha256(payload).hexdigest()
    if observed != value:
        raise WorkflowError(f"{label} blob content does not match descriptor digest")
    return payload


def index_payload_for_digest(archive: tarfile.TarFile, digest: str) -> tuple[bytes, str]:
    expected = _string(digest, "OCI index digest")
    if not _DIGEST.fullmatch(expected):
        raise WorkflowError("OCI index digest must be sha256:<64 lowercase hex>")
    root = _read_member(archive, "index.json")
    if "sha256:" + hashlib.sha256(root).hexdigest() == expected:
        return root, "index.json"
    blob = _require_digest_blob(archive, expected, "OCI index digest")
    return blob, "blobs/sha256/" + expected.removeprefix("sha256:")


def parse_index_payload(payload: bytes, label: str = "OCI image index") -> Mapping[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkflowError(f"{label} is not valid JSON") from error
    data = _mapping(value, label)
    if data.get("schemaVersion") != 2 or data.get("mediaType") not in _INDEX_MEDIA_TYPES:
        raise WorkflowError(f"{label} is not an OCI/Docker multi-platform image index")
    manifests = data.get("manifests")
    if not isinstance(manifests, list) or not manifests:
        raise WorkflowError(f"{label} has no manifests")
    return data


def platform_inventory(index: Mapping[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    required: dict[tuple[str, str], str] = {}
    additional: list[dict[str, str]] = []
    for raw in index["manifests"]:
        item = _mapping(raw, "OCI index manifest descriptor")
        digest = _string(item.get("digest"), "OCI child digest")
        if not _DIGEST.fullmatch(digest):
            raise WorkflowError("OCI child digest is invalid")
        platform = item.get("platform")
        if isinstance(platform, Mapping):
            os_name = str(platform.get("os", "")).strip()
            architecture = str(platform.get("architecture", "")).strip()
        else:
            os_name = ""
            architecture = ""
        key = (os_name, architecture)
        if key in {("linux", "amd64"), ("linux", "arm64")}:
            if key in required:
                raise WorkflowError(f"duplicate required platform manifest: {os_name}/{architecture}")
            required[key] = digest
        else:
            additional.append({
                "digest": digest,
                "platform": f"{os_name or 'unknown'}/{architecture or 'unknown'}",
            })
    expected = {("linux", "amd64"), ("linux", "arm64")}
    if set(required) != expected:
        missing = sorted(f"{os_name}/{arch}" for os_name, arch in expected - set(required))
        raise WorkflowError(f"OCI index is missing required platforms: {missing}")
    platforms = [
        {"os": os_name, "architecture": architecture, "digest": required[(os_name, architecture)]}
        for os_name, architecture in (("linux", "amd64"), ("linux", "arm64"))
    ]
    return platforms, additional


def inspect_oci_archive(path: Path, expected_index_digest: str) -> dict[str, Any]:
    archive_path = path.expanduser().resolve()
    if not archive_path.is_file():
        raise WorkflowError(f"OCI stage archive is missing: {archive_path}")
    try:
        with tarfile.open(archive_path, mode="r:*") as archive:
            layout = json.loads(_read_member(archive, "oci-layout").decode("utf-8"))
            if not isinstance(layout, Mapping) or layout.get("imageLayoutVersion") != "1.0.0":
                raise WorkflowError("OCI archive has an invalid oci-layout marker")
            payload, location = index_payload_for_digest(archive, expected_index_digest)
            index = parse_index_payload(payload)
    except (tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WorkflowError("OCI stage artifact is not a readable OCI image-layout tar archive") from error
    platforms, additional = platform_inventory(index)
    return {
        "archive_sha256": sha256_file(archive_path),
        "index_digest": expected_index_digest,
        "index_location": location,
        "media_type": str(index["mediaType"]),
        "platforms": platforms,
        "additional_manifests": additional,
        "index_payload": payload,
    }
