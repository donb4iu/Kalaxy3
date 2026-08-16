#!/usr/bin/env python3
"""Create a source-bound receipt for a portable multi-architecture OCI stage artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from workflow import AtomicFileWriter, WorkflowError  # noqa: E402

_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_INDEX_MEDIA_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be a non-empty string")
    return value.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise WorkflowError(f"{label} must be an object")
    return value


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
    if len(payload) > 8 * 1024 * 1024:
        raise WorkflowError(f"OCI archive metadata member is unexpectedly large: {name}")
    return payload


def _index_payload_for_digest(archive: tarfile.TarFile, digest: str) -> tuple[bytes, str]:
    expected = _string(digest, "OCI index digest")
    if not _DIGEST.fullmatch(expected):
        raise WorkflowError("OCI index digest must be sha256:<64 lowercase hex>")
    root = _read_member(archive, "index.json")
    if "sha256:" + hashlib.sha256(root).hexdigest() == expected:
        return root, "index.json"
    blob_name = "blobs/sha256/" + expected.removeprefix("sha256:")
    blob = _read_member(archive, blob_name)
    if "sha256:" + hashlib.sha256(blob).hexdigest() != expected:
        raise WorkflowError("OCI index blob content does not match declared digest")
    return blob, blob_name


def _parse_index(payload: bytes, label: str) -> Mapping[str, Any]:
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


def _platform_inventory(index: Mapping[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
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


def build_receipt(
    *,
    source_sha: str,
    image_repository: str,
    stage_tag: str,
    index_digest: str,
    oci_archive: Path,
    storage_artifact_name: str,
    storage_artifact_id: str,
    storage_artifact_digest: str,
    workflow_run_id: str,
    workflow_run_attempt: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source = _string(source_sha, "source SHA")
    if not _SHA.fullmatch(source):
        raise WorkflowError("source SHA must be a lowercase Git SHA-1 or SHA-256 object ID")
    repository = _string(image_repository, "logical image repository")
    tag = _string(stage_tag, "stage tag")
    if tag != f"stage-{source}":
        raise WorkflowError("stage tag must be exactly stage-<source-sha>")
    expected_index = _string(index_digest, "OCI index digest")
    if not _DIGEST.fullmatch(expected_index):
        raise WorkflowError("OCI index digest is invalid")
    archive_path = oci_archive.expanduser().resolve()
    if not archive_path.is_file():
        raise WorkflowError(f"OCI stage archive is missing: {archive_path}")
    archive_sha = _sha256_file(archive_path)
    stored_digest = _string(storage_artifact_digest, "storage artifact digest")
    if not _HEX_SHA256.fullmatch(stored_digest):
        raise WorkflowError("storage artifact digest must be 64 lowercase hex characters")
    artifact_id = _string(storage_artifact_id, "storage artifact ID")
    if not artifact_id.isdigit() or int(artifact_id) <= 0:
        raise WorkflowError("storage artifact ID must be a positive integer string")

    try:
        with tarfile.open(archive_path, mode="r:*") as archive:
            layout = json.loads(_read_member(archive, "oci-layout").decode("utf-8"))
            if not isinstance(layout, Mapping) or layout.get("imageLayoutVersion") != "1.0.0":
                raise WorkflowError("OCI archive has an invalid oci-layout marker")
            index_payload, index_location = _index_payload_for_digest(archive, expected_index)
            index = _parse_index(index_payload, "OCI image index")
    except tarfile.TarError as error:
        raise WorkflowError("OCI stage artifact is not a readable OCI tar archive") from error

    platforms, additional = _platform_inventory(index)
    timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "schema_version": "1.0",
        "record_type": "sage-portable-stage-receipt",
        "stage_contract": "kalaxy3-portable-stage-v1",
        "source": {"git_sha": source},
        "artifact": {
            "format": "oci-layout-tar",
            "logical_image_repository": repository,
            "stage_tag": tag,
            "archive_sha256": archive_sha,
            "index_digest": expected_index,
            "index_location": index_location,
            "media_type": str(index["mediaType"]),
            "platforms": platforms,
            "additional_manifests": additional,
            "storage": {
                "provider": "github-actions-artifact",
                "artifact_name": _string(storage_artifact_name, "storage artifact name"),
                "artifact_id": artifact_id,
                "artifact_digest": stored_digest,
            },
        },
        "build_contract": {
            "dockerfile": "yaml/nginx-docs/k8s-doc-to-nginx/nginx/Dockerfile.stage",
            "source_validation": "make sage-stage-guardrails",
            "documentation_validation": "make docs-mkdocs-publication-test",
            "external_registry_credentials_used": False,
            "production_rebuild_permitted": False,
        },
        "invocation": {
            "provider": "github-actions",
            "workflow_run_id": _string(workflow_run_id, "workflow run ID"),
            "workflow_run_attempt": _string(workflow_run_attempt, "workflow run attempt"),
        },
        "generated_at": timestamp,
    }


def _fixture_archive(path: Path, index: Mapping[str, Any], digest: str) -> None:
    import io
    root = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [{
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "digest": digest,
            "size": len(json.dumps(index, separators=(",", ":")).encode("utf-8")),
            "annotations": {"org.opencontainers.image.ref.name": "fixture"},
        }],
    }
    files = {
        "oci-layout": json.dumps({"imageLayoutVersion": "1.0.0"}).encode(),
        "index.json": json.dumps(root, separators=(",", ":")).encode(),
        "blobs/sha256/" + digest.removeprefix("sha256:"): json.dumps(index, separators=(",", ":")).encode(),
    }
    with tarfile.open(path, "w") as archive:
        for name, payload in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-stage-receipt-") as raw:
        root = Path(raw)
        amd = "sha256:" + "a" * 64
        arm = "sha256:" + "b" * 64
        index = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [
                {"digest": amd, "platform": {"os": "linux", "architecture": "amd64"}},
                {"digest": arm, "platform": {"os": "linux", "architecture": "arm64"}},
                {"digest": "sha256:" + "c" * 64, "platform": {"os": "unknown", "architecture": "unknown"}},
            ],
        }
        raw_index = json.dumps(index, separators=(",", ":")).encode("utf-8")
        digest = "sha256:" + hashlib.sha256(raw_index).hexdigest()
        archive = root / "stage.oci.tar"
        _fixture_archive(archive, index, digest)
        value = build_receipt(
            source_sha="d" * 40,
            image_repository="example/image",
            stage_tag="stage-" + "d" * 40,
            index_digest=digest,
            oci_archive=archive,
            storage_artifact_name="sage-stage-oci-" + "d" * 40,
            storage_artifact_id="101",
            storage_artifact_digest="e" * 64,
            workflow_run_id="202",
            workflow_run_attempt="1",
            generated_at="2026-08-16T07:00:00Z",
        )
        if [item["architecture"] for item in value["artifact"]["platforms"]] != ["amd64", "arm64"]:
            raise RuntimeError("required multi-architecture platform inventory failed")
        if value["build_contract"]["external_registry_credentials_used"] is not False:
            raise RuntimeError("stage receipt did not preserve credential-free stage contract")
        try:
            build_receipt(
                source_sha="d" * 40,
                image_repository="example/image",
                stage_tag="stage-" + "d" * 40,
                index_digest="sha256:" + "f" * 64,
                oci_archive=archive,
                storage_artifact_name="fixture",
                storage_artifact_id="101",
                storage_artifact_digest="e" * 64,
                workflow_run_id="202",
                workflow_run_attempt="1",
            )
        except WorkflowError:
            pass
        else:
            raise RuntimeError("stage receipt accepted an index digest mismatch")
        broken = dict(index)
        broken["manifests"] = [index["manifests"][0]]
        broken_raw = json.dumps(broken, separators=(",", ":")).encode("utf-8")
        broken_digest = "sha256:" + hashlib.sha256(broken_raw).hexdigest()
        broken_archive = root / "broken.oci.tar"
        _fixture_archive(broken_archive, broken, broken_digest)
        try:
            build_receipt(
                source_sha="d" * 40,
                image_repository="example/image",
                stage_tag="stage-" + "d" * 40,
                index_digest=broken_digest,
                oci_archive=broken_archive,
                storage_artifact_name="fixture",
                storage_artifact_id="101",
                storage_artifact_digest="e" * 64,
                workflow_run_id="202",
                workflow_run_attempt="1",
            )
        except WorkflowError:
            pass
        else:
            raise RuntimeError("stage receipt accepted a missing arm64 manifest")
    print("PASS exact source-SHA stage tag binding")
    print("PASS OCI archive, index digest, and child-manifest validation")
    print("PASS required linux/amd64 + linux/arm64 stage artifact")
    print("PASS immutable artifact-storage identity without external registry credentials")
    print("Kalaxy3 SAGE portable stage receipt self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha")
    parser.add_argument("--image-repository")
    parser.add_argument("--stage-tag")
    parser.add_argument("--index-digest")
    parser.add_argument("--oci-archive", type=Path)
    parser.add_argument("--storage-artifact-name")
    parser.add_argument("--storage-artifact-id")
    parser.add_argument("--storage-artifact-digest")
    parser.add_argument("--workflow-run-id")
    parser.add_argument("--workflow-run-attempt")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    required = (
        args.source_sha,
        args.image_repository,
        args.stage_tag,
        args.index_digest,
        args.oci_archive,
        args.storage_artifact_name,
        args.storage_artifact_id,
        args.storage_artifact_digest,
        args.workflow_run_id,
        args.workflow_run_attempt,
        args.output,
    )
    if any(item is None for item in required):
        raise WorkflowError("all stage receipt arguments are required")
    value = build_receipt(
        source_sha=args.source_sha,
        image_repository=args.image_repository,
        stage_tag=args.stage_tag,
        index_digest=args.index_digest,
        oci_archive=args.oci_archive,
        storage_artifact_name=args.storage_artifact_name,
        storage_artifact_id=args.storage_artifact_id,
        storage_artifact_digest=args.storage_artifact_digest,
        workflow_run_id=args.workflow_run_id,
        workflow_run_attempt=args.workflow_run_attempt,
    )
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    AtomicFileWriter((output.parent,)).write_text(
        output, json.dumps(value, indent=2) + "\n", new_mode=0o600
    )
    print("Kalaxy3 SAGE portable stage receipt: PASS")
    print(f"Source SHA:       {value['source']['git_sha']}")
    print(f"OCI index digest: {value['artifact']['index_digest']}")
    print(f"OCI archive SHA:  {value['artifact']['archive_sha256']}")
    print(f"Artifact ID:      {value['artifact']['storage']['artifact_id']}")
    print(f"Receipt:          {output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, WorkflowError, RuntimeError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE portable stage receipt: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
