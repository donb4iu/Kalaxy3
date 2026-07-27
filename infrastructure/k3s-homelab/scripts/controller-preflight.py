#!/usr/bin/env python3
"""Validate Kalaxy3 controller, Helm, and cluster-access authority."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_command(
    arguments: List[str],
    environment: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        arguments,
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def required_ansible_core() -> str:
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    match = re.search(r"(?m)^ansible-core==([^\s]+)$", text)
    if match is None:
        raise RuntimeError("requirements.txt must pin ansible-core exactly")
    return match.group(1)


def required_collections() -> Dict[str, str]:
    text = (ROOT / "requirements.yml").read_text(encoding="utf-8")
    pairs = re.findall(
        r"- name:\s*(\S+)\s*\n\s*version:\s*[\"']?([^\"'\s]+)",
        text,
    )
    if not pairs:
        raise RuntimeError("No exact collection requirements found")
    return dict(pairs)


def installed_collections() -> Dict[str, str]:
    galaxy = ROOT / ".venv/bin/ansible-galaxy"
    payload = json.loads(
        run_command([str(galaxy), "collection", "list", "--format", "json"])
    )
    installed: Dict[str, str] = {}
    for collections in payload.values():
        for name, metadata in collections.items():
            installed[name] = str(metadata["version"])
    return installed


def controller_platform_key() -> str:
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
            f"Unsupported controller platform: {os_name}-{machine}"
        )
    return f"{os_map[os_name]}-{arch_map[machine]}"


def validate_active_venv() -> None:
    expected = (ROOT / ".venv").resolve()
    actual = Path(sys.prefix).resolve()
    if actual != expected:
        raise RuntimeError(
            "Preflight must run from the repository .venv: "
            f"expected {expected}, found {actual}"
        )
    print(f"PASS repository virtual environment {actual}")


def validate_uv() -> None:
    expected_version = (
        ROOT / ".uv-version"
    ).read_text(encoding="utf-8").strip()
    lock = json.loads(
        (ROOT / "uv-platforms.json").read_text(encoding="utf-8")
    )
    if lock.get("version") != expected_version:
        raise RuntimeError(
            ".uv-version and uv-platforms.json disagree"
        )

    key = controller_platform_key()
    metadata = lock.get("platforms", {}).get(key)
    if not isinstance(metadata, dict):
        raise RuntimeError(f"No pinned uv artifact for {key}")

    for field in ("sha256", "binary_sha256", "uvx_binary_sha256"):
        if re.fullmatch(
            r"[0-9a-f]{64}",
            str(metadata.get(field, "")),
        ) is None:
            raise RuntimeError(f"Invalid uv {field} for {key}")

    uv = ROOT / ".tools/uv"
    uvx = ROOT / ".tools/uvx"
    for executable, field in (
        (uv, "binary_sha256"),
        (uvx, "uvx_binary_sha256"),
    ):
        if not executable.is_file() or not os.access(executable, os.X_OK):
            raise RuntimeError(
                f"Repository executable is missing: {executable}"
            )
        actual_hash = sha256(executable)
        expected_hash = str(metadata[field])
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"{executable.name} checksum mismatch: "
                f"expected {expected_hash}, found {actual_hash}"
            )

    output = run_command([str(uv), "--version"]).strip()
    parts = output.split()
    actual_version = parts[1] if len(parts) >= 2 else ""
    if actual_version != expected_version:
        raise RuntimeError(
            f"uv mismatch: expected {expected_version}, "
            f"found {actual_version or output}"
        )

    print(f"PASS uv {actual_version} ({key})")
    print(f"PASS uv binary SHA-256 {metadata['binary_sha256']}")
    print(f"PASS uvx binary SHA-256 {metadata['uvx_binary_sha256']}")


def validate_python() -> None:
    expected = (
        ROOT / ".python-version"
    ).read_text(encoding="utf-8").strip()
    actual = ".".join(str(value) for value in sys.version_info[:3])
    if actual != expected:
        raise RuntimeError(
            f"Python mismatch: expected {expected}, found {actual}"
        )

    managed_root = (ROOT / ".python").resolve()
    base_prefix = Path(sys.base_prefix).resolve()
    if managed_root != base_prefix and managed_root not in base_prefix.parents:
        raise RuntimeError(
            "Python is not repository-managed: "
            f"expected under {managed_root}, found {base_prefix}"
        )

    print(f"PASS Python {actual}")


def validate_ansible() -> None:
    ansible = ROOT / ".venv/bin/ansible"
    output = run_command([str(ansible), "--version"])
    match = re.search(r"ansible \[core ([^\]]+)\]", output)
    if match is None:
        raise RuntimeError("Unable to determine ansible-core version")

    expected_core = required_ansible_core()
    actual_core = match.group(1)
    if actual_core != expected_core:
        raise RuntimeError(
            f"ansible-core mismatch: expected {expected_core}, "
            f"found {actual_core}"
        )
    print(f"PASS ansible-core {actual_core}")

    installed = installed_collections()
    for name, expected in required_collections().items():
        actual = installed.get(name)
        if actual != expected:
            raise RuntimeError(
                f"{name} mismatch: expected {expected}, found {actual}"
            )
        print(f"PASS {name} {actual}")


def inventory_hosts() -> dict[str, str]:
    executable = ROOT / ".venv/bin/ansible-inventory"
    payload = json.loads(
        run_command(
            [
                str(executable),
                "-i",
                str(ROOT / "inventory/hosts.yml"),
                "--list",
            ]
        )
    )

    hostvars = payload.get("_meta", {}).get("hostvars", {})
    if not isinstance(hostvars, dict) or not hostvars:
        raise RuntimeError("Effective Ansible inventory contains no hosts")

    discovered: dict[str, str] = {}
    for name, variables in hostvars.items():
        if not isinstance(variables, dict):
            raise RuntimeError(
                f"Invalid effective inventory variables for {name}"
            )
        address = variables.get("ansible_host")
        if not address:
            raise RuntimeError(
                f"Effective inventory host {name} lacks ansible_host"
            )
        discovered[str(name)] = str(address)
    return discovered


def validate_ssh_trust() -> None:
    trust_path = ROOT / "inventory/ssh_known_hosts"
    lines = [
        line.strip()
        for line in trust_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]

    trusted: dict[str, str] = {}
    for line in lines:
        fields = line.split()
        if len(fields) != 3 or fields[1] != "ssh-ed25519":
            raise RuntimeError(
                f"Invalid repository SSH trust entry: {line}"
            )
        if fields[0].startswith("|"):
            raise RuntimeError(
                "Hashed hostnames are not allowed in repository trust data"
            )

        names = fields[0].split(",")
        if len(names) != 2:
            raise RuntimeError(
                f"SSH trust entry must contain hostname and IP: {line}"
            )
        trusted[names[0]] = names[1]

    expected = inventory_hosts()
    if trusted != expected:
        raise RuntimeError(
            "Repository SSH trust does not exactly match inventory hosts: "
            f"expected {expected}, found {trusted}"
        )

    ansible_config = (
        ROOT / "ansible.cfg"
    ).read_text(encoding="utf-8")
    for required in (
        "UserKnownHostsFile=inventory/ssh_known_hosts",
        "GlobalKnownHostsFile=/dev/null",
        "StrictHostKeyChecking=yes",
        "BatchMode=yes",
    ):
        if required not in ansible_config:
            raise RuntimeError(
                f"ansible.cfg does not enforce {required}"
            )

    print(f"PASS SSH host trust {len(trusted)} nodes")
    print("PASS SSH authentication is configured for noninteractive mode")


def helm_environment() -> dict[str, str]:
    state = ROOT / ".helm"
    environment = dict(os.environ)

    for name in list(environment):
        if (
            name == "KUBECONFIG"
            or name.startswith("HELM_KUBE")
            or name == "HELM_NAMESPACE"
        ):
            environment.pop(name, None)

    expected = {
        "HELM_CONFIG_HOME": state / "config",
        "HELM_CACHE_HOME": state / "cache",
        "HELM_DATA_HOME": state / "data",
        "HELM_PLUGINS": state / "plugins",
        "HELM_REGISTRY_CONFIG": state / "registry/config.json",
        "HELM_REPOSITORY_CONFIG": state / "repositories.yaml",
        "HELM_REPOSITORY_CACHE": state / "repository-cache",
    }
    environment.update({key: str(value) for key, value in expected.items()})

    for path in expected.values():
        directory = path if path.suffix == "" else path.parent
        directory.mkdir(parents=True, exist_ok=True)

    return environment


def validate_helm() -> None:
    lock = json.loads(
        (ROOT / "helm-platforms.json").read_text(encoding="utf-8")
    )
    expected_version = (
        ROOT / ".helm-version"
    ).read_text(encoding="utf-8").strip()
    if lock.get("version") != expected_version:
        raise RuntimeError(
            ".helm-version and helm-platforms.json disagree"
        )

    key = controller_platform_key()
    metadata = lock.get("platforms", {}).get(key)
    if not isinstance(metadata, dict):
        raise RuntimeError(f"No pinned Helm artifact for {key}")

    for field in ("sha256", "binary_sha256"):
        if re.fullmatch(
            r"[0-9a-f]{64}",
            str(metadata.get(field, "")),
        ) is None:
            raise RuntimeError(f"Invalid Helm {field} for {key}")

    executable = ROOT / ".tools/helm"
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise RuntimeError(f"Repository-local Helm is missing: {executable}")

    actual_hash = sha256(executable)
    expected_hash = str(metadata["binary_sha256"])
    if actual_hash != expected_hash:
        raise RuntimeError(
            "Helm binary checksum mismatch: "
            f"expected {expected_hash}, found {actual_hash}"
        )

    output = run_command(
        [str(executable), "version", "--short"],
        helm_environment(),
    ).strip()
    if not (
        output == expected_version
        or output.startswith(expected_version + "+")
    ):
        raise RuntimeError(
            f"Helm mismatch: expected {expected_version}, found {output}"
        )

    wrapper = ROOT / "scripts/helm"
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        raise RuntimeError(
            "Repository Helm wrapper is missing or not executable"
        )

    wrapper_text = wrapper.read_text(encoding="utf-8")
    required_markers = (
        'KUBECONFIG = ROOT / "kubeconfig-kalaxy3.yaml"',
        "SANITIZED_NAMES",
        "HELM_KUBE",
        "--kubeconfig",
        "--kube-context",
        "current-context",
    )
    for required in required_markers:
        if required not in wrapper_text:
            raise RuntimeError(
                f"Repository Helm wrapper lacks {required!r}"
            )

    print(f"PASS Helm {output} ({key})")
    print(f"PASS Helm binary SHA-256 {expected_hash}")
    print(f"PASS Helm binary {executable}")
    print(f"PASS Helm state {(ROOT / '.helm').resolve()}")
    print("PASS Helm wrapper sanitizes inherited cluster overrides")


def validate_kubeconfig() -> tuple[Path, str]:
    kubeconfig = ROOT / "kubeconfig-kalaxy3.yaml"
    if not kubeconfig.is_file():
        raise RuntimeError(
            f"Repository Kalaxy3 kubeconfig is missing: {kubeconfig}"
        )

    mode = stat.S_IMODE(kubeconfig.stat().st_mode)
    if mode & 0o077:
        raise RuntimeError(
            "Repository Kalaxy3 kubeconfig permissions are too broad: "
            f"{oct(mode)}; expected no group/other access"
        )

    payload = yaml.safe_load(kubeconfig.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("Repository kubeconfig is not a YAML mapping")

    current_context = str(payload.get("current-context", "")).strip()
    contexts = payload.get("contexts", [])
    context_names = {
        str(item.get("name", ""))
        for item in contexts
        if isinstance(item, dict)
    }
    if not current_context or current_context not in context_names:
        raise RuntimeError(
            "Repository kubeconfig current-context is missing or invalid"
        )

    context_item = next(
        item
        for item in contexts
        if isinstance(item, dict) and item.get("name") == current_context
    )
    cluster_name = str(
        context_item.get("context", {}).get("cluster", "")
    )
    clusters = payload.get("clusters", [])
    cluster_names = {
        str(item.get("name", ""))
        for item in clusters
        if isinstance(item, dict)
    }
    if not cluster_name or cluster_name not in cluster_names:
        raise RuntimeError(
            "Repository kubeconfig current context references no valid cluster"
        )

    print(f"PASS Helm kubeconfig {kubeconfig.resolve()}")
    print(f"PASS kubeconfig current context {current_context}")
    return kubeconfig, current_context


def validate_cluster_access() -> None:
    kubeconfig, context = validate_kubeconfig()
    wrapper = ROOT / "scripts/helm"
    output = run_command(
        [
            str(wrapper),
            "list",
            "--all-namespaces",
            "--max",
            "1",
            "--output",
            "json",
        ]
    )
    parsed = json.loads(output)
    if not isinstance(parsed, list):
        raise RuntimeError("Helm cluster-access probe returned invalid JSON")

    print(
        "PASS read-only Helm access through repository kubeconfig "
        f"and context {context}"
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        choices=("core", "helm", "cluster", "all"),
        default="all",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    validate_active_venv()

    if arguments.scope in {"core", "all"}:
        validate_uv()
        validate_python()
        validate_ansible()
        validate_ssh_trust()

    if arguments.scope in {"helm", "all"}:
        validate_helm()

    if arguments.scope in {"cluster", "all"}:
        validate_cluster_access()

    print(
        f"Kalaxy3 controller preflight ({arguments.scope}): PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
