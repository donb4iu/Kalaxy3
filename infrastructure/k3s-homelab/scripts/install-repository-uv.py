#!/usr/bin/env python3
"""Install exact repository-pinned uv and uvx binaries under .tools."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "uv-platforms.json"
TOOLS = ROOT / ".tools"
UV = TOOLS / "uv"
UVX = TOOLS / "uvx"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def platform_key() -> str:
    os_name = platform.system().lower()
    machine = platform.machine().lower()
    os_map = {"darwin": "darwin", "linux": "linux"}
    arch_map = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    if os_name not in os_map or machine not in arch_map:
        raise RuntimeError(
            f"Unsupported uv controller platform: {os_name}-{machine}"
        )
    return f"{os_map[os_name]}-{arch_map[machine]}"


def installed_version() -> str:
    if not UV.is_file():
        return ""

    result = subprocess.run(
        [str(UV), "--version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    parts = result.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else ""


def archive_member(archive: tarfile.TarFile, basename: str) -> bytes:
    matches = [
        member
        for member in archive.getmembers()
        if member.isfile() and Path(member.name).name == basename
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one {basename!r} binary in uv archive; "
            f"found {len(matches)}"
        )

    extracted = archive.extractfile(matches[0])
    if extracted is None:
        raise RuntimeError(f"Unable to extract {basename!r}")
    return extracted.read()


def write_executable(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".new")
    temporary.write_bytes(content)
    temporary.chmod(
        stat.S_IRUSR
        | stat.S_IWUSR
        | stat.S_IXUSR
        | stat.S_IRGRP
        | stat.S_IXGRP
        | stat.S_IROTH
        | stat.S_IXOTH
    )
    os.replace(temporary, path)


def binaries_are_accepted(
    expected_version: str,
    uv_sha256: str,
    uvx_sha256: str,
) -> bool:
    for path, expected_hash in (
        (UV, uv_sha256),
        (UVX, uvx_sha256),
    ):
        if not path.is_file() or not os.access(path, os.X_OK):
            return False
        if sha256_file(path) != expected_hash:
            return False

    return installed_version() == expected_version


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    expected_version = str(lock["version"])
    key = platform_key()
    metadata = lock.get("platforms", {}).get(key)

    if not isinstance(metadata, dict):
        raise RuntimeError(f"No repository uv artifact is pinned for {key}")

    archive_sha256 = str(metadata.get("sha256", "")).lower()
    uv_sha256 = str(metadata.get("binary_sha256", "")).lower()
    uvx_sha256 = str(
        metadata.get("uvx_binary_sha256", "")
    ).lower()

    for label, value in (
        ("archive", archive_sha256),
        ("uv binary", uv_sha256),
        ("uvx binary", uvx_sha256),
    ):
        if len(value) != 64 or any(
            character not in "0123456789abcdef"
            for character in value
        ):
            raise RuntimeError(
                f"Invalid uv {label} SHA-256 for {key}: {value!r}"
            )

    if binaries_are_accepted(
        expected_version,
        uv_sha256,
        uvx_sha256,
    ):
        print(f"PASS repository uv {expected_version} ({key})")
        print(f"PASS uv binary SHA-256 {uv_sha256}")
        print(f"PASS uvx binary SHA-256 {uvx_sha256}")
        return 0

    request = urllib.request.Request(
        str(metadata["url"]),
        headers={"User-Agent": "Kalaxy3-SAGE-uv-installer/2.0"},
    )

    with tempfile.TemporaryDirectory(prefix="kalaxy3-uv-") as temp_dir:
        archive_path = Path(temp_dir) / str(metadata["archive"])

        with urllib.request.urlopen(request, timeout=120) as response:
            archive_path.write_bytes(response.read())

        actual_archive_sha256 = sha256_file(archive_path)
        if actual_archive_sha256 != archive_sha256:
            raise RuntimeError(
                "uv archive checksum mismatch: "
                f"expected {archive_sha256}, "
                f"found {actual_archive_sha256}"
            )

        with tarfile.open(archive_path, "r:gz") as archive:
            uv_binary = archive_member(archive, "uv")
            uvx_binary = archive_member(archive, "uvx")

        actual_uv_sha256 = sha256_bytes(uv_binary)
        actual_uvx_sha256 = sha256_bytes(uvx_binary)

        if actual_uv_sha256 != uv_sha256:
            raise RuntimeError(
                "Extracted uv binary checksum mismatch: "
                f"expected {uv_sha256}, found {actual_uv_sha256}"
            )
        if actual_uvx_sha256 != uvx_sha256:
            raise RuntimeError(
                "Extracted uvx binary checksum mismatch: "
                f"expected {uvx_sha256}, found {actual_uvx_sha256}"
            )

        write_executable(UV, uv_binary)
        write_executable(UVX, uvx_binary)

    if not binaries_are_accepted(
        expected_version,
        uv_sha256,
        uvx_sha256,
    ):
        raise RuntimeError(
            "Installed uv or uvx failed version/checksum validation"
        )

    print(f"PASS repository uv {expected_version} ({key})")
    print(f"PASS uv binary SHA-256 {uv_sha256}")
    print(f"PASS uvx binary SHA-256 {uvx_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
