#!/usr/bin/env python3
"""Install the exact repository-pinned Helm binary under .tools."""

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
LOCK_PATH = ROOT / "helm-platforms.json"
DESTINATION = ROOT / ".tools/helm"


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
            f"Unsupported Helm controller platform: {os_name}-{machine}"
        )
    return f"{os_map[os_name]}-{arch_map[machine]}"


def isolated_environment() -> dict[str, str]:
    state = ROOT / ".helm"
    environment = dict(os.environ)
    for name in list(environment):
        if (
            name == "KUBECONFIG"
            or name.startswith("HELM_KUBE")
            or name == "HELM_NAMESPACE"
        ):
            environment.pop(name, None)

    environment.update(
        {
            "HELM_CONFIG_HOME": str(state / "config"),
            "HELM_CACHE_HOME": str(state / "cache"),
            "HELM_DATA_HOME": str(state / "data"),
            "HELM_PLUGINS": str(state / "plugins"),
            "HELM_REGISTRY_CONFIG": str(state / "registry/config.json"),
            "HELM_REPOSITORY_CONFIG": str(state / "repositories.yaml"),
            "HELM_REPOSITORY_CACHE": str(state / "repository-cache"),
        }
    )

    for directory in (
        state / "config",
        state / "cache",
        state / "data",
        state / "plugins",
        state / "registry",
        state / "repository-cache",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    return environment


def version_output() -> str:
    if not DESTINATION.is_file():
        return ""

    result = subprocess.run(
        [str(DESTINATION), "version", "--short"],
        cwd=ROOT,
        env=isolated_environment(),
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def binary_is_accepted(
    expected_version: str,
    expected_sha256: str,
) -> bool:
    if not DESTINATION.is_file() or not os.access(DESTINATION, os.X_OK):
        return False

    if sha256_file(DESTINATION) != expected_sha256:
        return False

    current = version_output()
    return (
        current == expected_version
        or current.startswith(expected_version + "+")
    )


def write_executable(content: bytes) -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    temporary = DESTINATION.with_suffix(".new")
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
    os.replace(temporary, DESTINATION)


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    expected_version = str(lock["version"])
    key = platform_key()
    metadata = lock.get("platforms", {}).get(key)

    if not isinstance(metadata, dict):
        raise RuntimeError(f"No repository Helm artifact is pinned for {key}")

    expected_archive_sha256 = str(metadata.get("sha256", "")).lower()
    expected_binary_sha256 = str(
        metadata.get("binary_sha256", "")
    ).lower()

    for label, value in (
        ("archive", expected_archive_sha256),
        ("binary", expected_binary_sha256),
    ):
        if len(value) != 64 or any(
            character not in "0123456789abcdef"
            for character in value
        ):
            raise RuntimeError(
                f"Invalid Helm {label} SHA-256 for {key}: {value!r}"
            )

    if binary_is_accepted(
        expected_version,
        expected_binary_sha256,
    ):
        print(
            f"PASS repository Helm {version_output()} ({key})"
        )
        print(
            f"PASS Helm binary SHA-256 {expected_binary_sha256}"
        )
        return 0

    request = urllib.request.Request(
        str(metadata["url"]),
        headers={"User-Agent": "Kalaxy3-SAGE-Helm-installer/2.0"},
    )

    with tempfile.TemporaryDirectory(prefix="kalaxy3-helm-") as temp_dir:
        archive_path = Path(temp_dir) / str(metadata["archive"])

        with urllib.request.urlopen(request, timeout=120) as response:
            archive_path.write_bytes(response.read())

        actual_archive_sha256 = sha256_file(archive_path)
        if actual_archive_sha256 != expected_archive_sha256:
            raise RuntimeError(
                "Helm archive checksum mismatch: "
                f"expected {expected_archive_sha256}, "
                f"found {actual_archive_sha256}"
            )

        member_name = f"{key}/helm"
        with tarfile.open(archive_path, "r:gz") as archive:
            member = archive.getmember(member_name)
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(
                    f"Helm binary missing from {archive_path}"
                )
            binary = extracted.read()

        actual_binary_sha256 = sha256_bytes(binary)
        if actual_binary_sha256 != expected_binary_sha256:
            raise RuntimeError(
                "Extracted Helm binary checksum mismatch: "
                f"expected {expected_binary_sha256}, "
                f"found {actual_binary_sha256}"
            )

        write_executable(binary)

    if not binary_is_accepted(
        expected_version,
        expected_binary_sha256,
    ):
        raise RuntimeError(
            "Installed Helm failed version or binary checksum validation"
        )

    print(f"PASS repository Helm {version_output()} ({key})")
    print(f"PASS Helm binary SHA-256 {expected_binary_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
