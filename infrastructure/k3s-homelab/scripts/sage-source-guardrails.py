#!/usr/bin/env python3
"""Reject source paths that bypass Kalaxy3 repository authority."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()


def normalized_shell_text(text: str) -> str:
    return re.sub(r"\\\r?\n", " ", text)


def download_to_shell(text: str) -> bool:
    normalized = normalized_shell_text(text)
    pattern = re.compile(
        r"(?is)\b(?:curl|wget)\b.{0,1500}?\|\s*"
        r"(?:env\b.{0,800}?)?\b(?:sh|bash)\b"
    )
    return pattern.search(normalized) is not None


def bare_helm(text: str) -> bool:
    patterns = (
        re.compile(
            r"(?m)^\s*(?:cmd:\s*)?helm\s+"
            r"(?:upgrade|install|repo|pull|template|lint|plugin|version|"
            r"uninstall|list|status)\b"
        ),
        re.compile(r"(?m)^\s*-\s*helm\s*$"),
        re.compile(r"(?m)^\s*command:\s*helm\b"),
    )
    return any(pattern.search(text) for pattern in patterns)


def task_blocks(text: str) -> list[str]:
    starts = [
        match.start()
        for match in re.finditer(r"(?m)^\s*-\s+name:", text)
    ]
    if not starts:
        return [text]
    starts.append(len(text))
    return [
        text[starts[index] : starts[index + 1]]
        for index in range(len(starts) - 1)
    ]


def helm_command_operation(block: str) -> bool:
    return (
        "{{ helm_binary }}" in block
        and re.search(r"(?m)^\s*(?:cmd:\s*)?.*\bupgrade\b", block)
        is not None
        and "--install" in block
    )


def operational_files() -> list[Path]:
    paths = [ROOT / "Makefile"]
    for directory in (ROOT / "playbooks", ROOT / "scripts"):
        for path in directory.rglob("*"):
            if not path.is_file() or path.resolve() == SELF:
                continue
            if "__pycache__" in path.parts:
                continue
            paths.append(path)
    return sorted(set(paths))


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def exact_sha256(value: object) -> bool:
    return re.fullmatch(r"[0-9a-f]{64}", str(value)) is not None


def run_negative_tests() -> list[str]:
    failures: list[str] = []
    single_line = (
        "curl -fsSL https://example.invalid/install.sh"
        + " | "
        + "sh"
    )
    multiline = (
        "curl -fsSL \\\n"
        "  https://example.invalid/install.sh \\\n"
        "  | \\\n"
        "  env INSTALL_ROOT=/tmp sh"
    )
    safe_download = "python3 scripts/install-repository-tool.py"

    if not download_to_shell(single_line):
        failures.append("negative test missed a single-line pipeline")
    if not download_to_shell(multiline):
        failures.append("negative test missed a multiline pipeline")
    if download_to_shell(safe_download):
        failures.append("negative test rejected a safe verified installer")
    return failures


def validate_binary_locks(failures: list[str]) -> None:
    helm_lock = json.loads(
        (ROOT / "helm-platforms.json").read_text(encoding="utf-8")
    )
    helm_version = (
        ROOT / ".helm-version"
    ).read_text(encoding="utf-8").strip()
    if helm_lock.get("version") != helm_version:
        failures.append(
            ".helm-version does not match helm-platforms.json"
        )

    for key, metadata in helm_lock.get("platforms", {}).items():
        for field in ("sha256", "binary_sha256"):
            if not exact_sha256(metadata.get(field)):
                failures.append(
                    f"Helm {field} is invalid for {key}"
                )

    uv_lock = json.loads(
        (ROOT / "uv-platforms.json").read_text(encoding="utf-8")
    )
    uv_version = (
        ROOT / ".uv-version"
    ).read_text(encoding="utf-8").strip()
    if uv_lock.get("version") != uv_version:
        failures.append(
            ".uv-version does not match uv-platforms.json"
        )

    for key, metadata in uv_lock.get("platforms", {}).items():
        for field in (
            "sha256",
            "binary_sha256",
            "uvx_binary_sha256",
        ):
            if not exact_sha256(metadata.get(field)):
                failures.append(
                    f"uv {field} is invalid for {key}"
                )


def validate_makefile(failures: list[str]) -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    required = (
        "controller-bootstrap: controller-uv controller-helm",
        "$(PREFLIGHT) --scope core",
        "$(PREFLIGHT) --scope helm",
        "phase-0: bootstrap-guardrails",
        "phase-1: bootstrap-guardrails",
        "phase-2: k3s-guardrails",
        "phase-3: cluster-guardrails",
        "deploy: cluster-guardrails",
        "uninstall: recovery-guardrails confirm-uninstall",
        "recovery-guardrails:",
        "uninstall-syntax:",
        'test "$(CONFIRM_UNINSTALL)" = "kalaxy3"',
    )
    for marker in required:
        if marker not in makefile:
            failures.append(
                f"Makefile lacks staged control {marker!r}"
            )

    prohibited = (
        "phase-0: guardrails",
        "phase-1: guardrails",
        "phase-2: guardrails",
        "uninstall: guardrails",
        "recovery-guardrails: controller-helm",
        "recovery-guardrails: cluster-access",
        "recovery-guardrails: deployment-guardrail",
    )
    for marker in prohibited:
        if marker in makefile:
            failures.append(
                f"Makefile recovery/bootstrap deadlock remains: {marker!r}"
            )


def validate_helm_wrapper(failures: list[str]) -> None:
    text = (ROOT / "scripts/helm").read_text(encoding="utf-8")
    for marker in (
        'KUBECONFIG = ROOT / "kubeconfig-kalaxy3.yaml"',
        "SANITIZED_NAMES",
        "name.startswith(\"HELM_KUBE\")",
        "--kubeconfig",
        "--kube-context",
        "current-context",
        "BLOCKED_ARGUMENT_PREFIXES",
    ):
        if marker not in text:
            failures.append(
                f"scripts/helm lacks cluster authority marker {marker!r}"
            )


def validate_platform_helm(failures: list[str]) -> None:
    text = (
        ROOT / "playbooks/platform.yml"
    ).read_text(encoding="utf-8")
    for marker in (
        "KUBECONFIG: /etc/rancher/k3s/k3s.yaml",
        'HELM_KUBEAPISERVER: ""',
        'HELM_KUBECAFILE: ""',
        'HELM_KUBECONTEXT: ""',
        'HELM_KUBETOKEN: ""',
        "binary_sha256",
        "remote_helm_binary.stat.checksum",
    ):
        if marker not in text:
            failures.append(
                f"platform.yml lacks Helm control {marker!r}"
            )


def validate_task_blocks(failures: list[str]) -> None:
    for path in sorted((ROOT / "playbooks").rglob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for block in task_blocks(text):
            heading = block.splitlines()[0].strip()

            uses_command_helm = (
                "ansible.builtin.command" in block
                and "{{ helm_binary }}" in block
            )
            uses_module_helm = (
                "kubernetes.core.helm:" in block
                or "kubernetes.core.helm_plugin:" in block
                or "kubernetes.core.helm_repository:" in block
            )

            if (
                uses_command_helm
                and 'environment: "{{ helm_environment }}"' not in block
            ):
                failures.append(
                    f"{path.relative_to(ROOT)}: {heading} "
                    "lacks isolated Helm environment"
                )

            if uses_module_helm:
                if 'binary_path: "{{ helm_binary }}"' not in block:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {heading} "
                        "lacks Helm binary_path"
                    )
                if 'environment: "{{ helm_environment }}"' not in block:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {heading} "
                        "lacks isolated Helm environment"
                    )

            if helm_command_operation(block):
                if "--version" not in block:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {heading} "
                        "lacks --version"
                    )
                lock_refs = re.findall(
                    r"helm_chart_lock\.charts\."
                    r"([A-Za-z0-9_]+)\.version",
                    block,
                )
                if len(set(lock_refs)) != 1:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {heading} "
                        "must use exactly one chart lock version"
                    )

            if "kubernetes.core.helm:" in block:
                if re.search(
                    r"chart_version:\s*[\"']?\{\{\s*"
                    r"helm_chart_lock\.charts\.[A-Za-z0-9_]+\.version"
                    r"\s*\}\}[\"']?",
                    block,
                ) is None:
                    failures.append(
                        f"{path.relative_to(ROOT)}: {heading} "
                        "chart_version is not lock-derived"
                    )


def main() -> int:
    failures = run_negative_tests()
    validate_binary_locks(failures)
    validate_makefile(failures)
    validate_helm_wrapper(failures)
    validate_platform_helm(failures)

    repository_registry = json.loads(
        (ROOT / "helm-repositories.json").read_text(encoding="utf-8")
    )
    repositories = repository_registry.get("repositories", [])
    names = [str(item.get("name", "")) for item in repositories]
    urls = [str(item.get("url", "")) for item in repositories]
    if len(names) != len(set(names)):
        failures.append("Helm repository names are not unique")
    if len(urls) != len(set(urls)):
        failures.append("Helm repository URLs are not unique")
    for item in repositories:
        if not str(item.get("url", "")).startswith("https://"):
            failures.append(
                f"Helm repository is not HTTPS: {item!r}"
            )

    for path in operational_files():
        text = read_text(path)
        if text is None:
            continue
        relative = path.relative_to(ROOT)

        if download_to_shell(text):
            failures.append(
                f"{relative}: download-to-shell pipeline is prohibited"
            )
        if path.suffix in {".yml", ".yaml"} and bare_helm(text):
            failures.append(
                f"{relative}: unauthorized bare Helm execution"
            )
        if (
            path.suffix == ".py"
            and "shell=True" in text
            and ("curl" in text or "wget" in text)
        ):
            failures.append(
                f"{relative}: Python shell download execution is prohibited"
            )

    validate_task_blocks(failures)

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
            failures.append(
                f"ansible.cfg is missing SSH control {required!r}"
            )

    if failures:
        print("Kalaxy3 SAGE source guardrails: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS staged bootstrap, deployment, and recovery gates")
    print("PASS repository-managed uv and Helm binary hashes")
    print("PASS commit-pinned and checksum-verified K3s references")
    print("PASS repository-owned SSH trust and noninteractive mode")
    print("PASS repository-owned Helm kubeconfig/context authority")
    print("PASS isolated local and remote Helm environments")
    print("PASS no bare Helm or download-to-shell paths")
    print("PASS Helm task lock-reference coverage")
    print("PASS download-to-shell negative tests")
    print("Kalaxy3 SAGE source guardrails: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
