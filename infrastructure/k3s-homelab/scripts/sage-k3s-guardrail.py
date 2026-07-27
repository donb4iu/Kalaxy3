#!/usr/bin/env python3
"""Validate the exact repository K3s release lock and install path."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def group_k3s_version() -> str:
    text = (
        ROOT / "inventory/group_vars/all/main.yml"
    ).read_text(encoding="utf-8")
    match = re.search(
        r'(?m)^k3s_version:\s*["\']?([^"\'\s]+)["\']?\s*$',
        text,
    )
    if match is None:
        raise RuntimeError("Unable to read k3s_version from group variables")
    return match.group(1)


def main() -> int:
    lock = json.loads(
        (ROOT / "k3s-platforms.json").read_text(encoding="utf-8")
    )
    failures: list[str] = []

    version = str(lock.get("version", ""))
    if re.fullmatch(
        r"v[0-9]+\.[0-9]+\.[0-9]+\+k3s[0-9]+",
        version,
    ) is None:
        failures.append(f"K3s version is not exact: {version!r}")

    if group_k3s_version() != version:
        failures.append(
            "inventory k3s_version does not match k3s-platforms.json"
        )

    installer = lock.get("install_script", {})
    installer_url = str(installer.get("url", ""))
    installer_sha256 = str(installer.get("sha256", ""))
    release_commit = str(lock.get("release_commit", ""))

    if not re.fullmatch(r"[0-9a-f]{40}", release_commit):
        failures.append("K3s release_commit is not a full Git commit")
    if release_commit and release_commit not in installer_url:
        failures.append(
            "K3s installer URL is not pinned to release_commit"
        )
    if re.fullmatch(r"[0-9a-f]{64}", installer_sha256) is None:
        failures.append("K3s installer checksum is not exact")

    required_platforms = {"linux-amd64", "linux-arm64"}
    platforms = lock.get("platforms", {})
    if set(platforms) != required_platforms:
        failures.append(
            "K3s lock must contain exactly linux-amd64 and linux-arm64"
        )

    for key in sorted(required_platforms):
        metadata = platforms.get(key, {})
        checksum = str(metadata.get("sha256", ""))
        url = str(metadata.get("url", ""))
        if re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            failures.append(f"K3s checksum is invalid for {key}")
        if not url.startswith(
            "https://github.com/k3s-io/k3s/releases/download/"
        ):
            failures.append(f"K3s URL is not an official release for {key}")

    task = (
        ROOT / "playbooks/tasks/install-k3s.yml"
    ).read_text(encoding="utf-8")
    for required in (
        "k3s-platforms.json",
        "INSTALL_K3S_SKIP_DOWNLOAD",
        "k3s_release_lock.install_script.sha256",
        "k3s_release_lock.platforms[k3s_platform].sha256",
        "k3s_final_binary.stat.checksum",
    ):
        if required not in task:
            failures.append(
                f"install-k3s.yml is missing {required!r}"
            )

    playbook = (
        ROOT / "playbooks/k3s.yml"
    ).read_text(encoding="utf-8")
    if playbook.count("tasks/install-k3s.yml") != 3:
        failures.append(
            "playbooks/k3s.yml must use the locked installer for "
            "first server, joined servers, and agents"
        )

    if failures:
        print("Kalaxy3 SAGE K3s release guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"PASS exact K3s release {version}")
    print(f"PASS commit-pinned installer {release_commit}")
    print("PASS linux-amd64 and linux-arm64 binary checksums")
    print("PASS installed K3s binary checksum enforcement")
    print("Kalaxy3 SAGE K3s release guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
