#!/usr/bin/env python3
"""Validate rendered Kalaxy3 centralized-logging configuration."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml


EXPECTED_FILES = (
    "loki-values.yml",
    "fluent-bit-values.yml",
    "grafana-loki-datasource.yml",
)

HOMELAB_ROOT = Path(__file__).resolve().parent.parent
HELM_WRAPPER = HOMELAB_ROOT / "scripts" / "helm"
CHART_LOCK_PATH = HOMELAB_ROOT / "helm-chart-lock.json"
REPOSITORIES_PATH = HOMELAB_ROOT / "helm-repositories.json"


def load_single_document(path: Path) -> dict[str, Any]:
    """Load one nonempty YAML mapping."""
    documents = list(
        yaml.safe_load_all(path.read_text(encoding="utf-8"))
    )

    if len(documents) != 1:
        raise ValueError(
            f"{path.name}: expected one YAML document, "
            f"found {len(documents)}"
        )

    document = documents[0]

    if not isinstance(document, dict):
        raise ValueError(
            f"{path.name}: expected a YAML mapping"
        )

    return document


def load_manifest_stream(path: Path) -> list[dict[str, Any]]:
    """Load Kubernetes objects from a Helm manifest stream."""
    documents = [
        document
        for document in yaml.safe_load_all(
            path.read_text(encoding="utf-8")
        )
        if isinstance(document, dict)
    ]

    if not documents:
        raise ValueError(
            f"{path.name}: no Kubernetes objects rendered"
        )

    return documents


def load_json_mapping(path: Path) -> dict[str, Any]:
    """Load a JSON document whose root must be a mapping."""
    document = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(document, dict):
        raise ValueError(
            f"{path.name}: expected a JSON mapping"
        )

    return document


def validate_loki(document: dict[str, Any]) -> None:
    """Validate Loki values placement, persistence, and retention."""
    if document.get("deploymentMode") != "Monolithic":
        raise ValueError(
            "loki-values.yml: deploymentMode must be Monolithic"
        )

    single_binary = document.get("singleBinary", {})
    selector = single_binary.get("nodeSelector", {})

    if selector.get("kubernetes.io/arch") != "amd64":
        raise ValueError(
            "loki-values.yml: Loki must target amd64"
        )

    if (
        selector.get("kalaxy3.io/workload-pool")
        != "platform-services"
    ):
        raise ValueError(
            "loki-values.yml: Loki must target platform-services"
        )

    persistence = single_binary.get("persistence", {})

    if persistence.get("storageClass") != "longhorn":
        raise ValueError(
            "loki-values.yml: storageClass must be longhorn"
        )

    if persistence.get("size") != "40Gi":
        raise ValueError(
            "loki-values.yml: storage size must be 40Gi"
        )

    limits = document.get("loki", {}).get(
        "limits_config",
        {},
    )

    if limits.get("retention_period") != "168h":
        raise ValueError(
            "loki-values.yml: retention must be 168h"
        )

    storage = document.get("loki", {}).get("storage", {})

    if storage.get("type") != "filesystem":
        raise ValueError(
            "loki-values.yml: storage type must be filesystem"
        )

    bucket_names = storage.get("bucketNames", {})

    if bucket_names != {
        "chunks": "chunks",
        "ruler": "ruler",
    }:
        raise ValueError(
            "loki-values.yml: required chart bucket-name "
            "placeholders are missing"
        )

    if document.get("lokiCanary", {}).get("enabled") is not False:
        raise ValueError(
            "loki-values.yml: Loki Canary must remain disabled"
        )

    if document.get("test", {}).get("enabled") is not False:
        raise ValueError(
            "loki-values.yml: chart test must remain disabled"
        )


def validate_fluent_bit(document: dict[str, Any]) -> None:
    """Validate Fluent Bit output and all-node scheduling values."""
    if document.get("nodeSelector"):
        raise ValueError(
            "fluent-bit-values.yml: collector must not have "
            "a nodeSelector"
        )

    tolerations = document.get("tolerations", [])

    if {"operator": "Exists"} not in tolerations:
        raise ValueError(
            "fluent-bit-values.yml: all-node toleration missing"
        )

    outputs = (
        document.get("config", {})
        .get("pipeline", {})
        .get("outputs", [])
    )

    if not outputs or outputs[0].get("name") != "loki":
        raise ValueError(
            "fluent-bit-values.yml: Loki output missing"
        )


def validate_datasource(document: dict[str, Any]) -> None:
    """Validate Grafana datasource metadata."""
    metadata = document.get("metadata", {})

    if metadata.get("namespace") != "observability":
        raise ValueError(
            "grafana-loki-datasource.yml: namespace must be "
            "observability"
        )

    labels = metadata.get("labels", {})

    if labels.get("grafana_datasource") != "1":
        raise ValueError(
            "grafana-loki-datasource.yml: sidecar label missing"
        )


def run_helm(arguments: list[str]) -> str:
    """Run repository-owned Helm and return standard output."""
    if not HELM_WRAPPER.is_file():
        raise FileNotFoundError(
            f"Repository Helm wrapper is missing: {HELM_WRAPPER}"
        )

    if not os.access(HELM_WRAPPER, os.X_OK):
        raise PermissionError(
            f"Repository Helm wrapper is not executable: "
            f"{HELM_WRAPPER}"
        )

    result = subprocess.run(
        [str(HELM_WRAPPER), *arguments],
        cwd=HOMELAB_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        command = " ".join(
            [str(HELM_WRAPPER), *arguments]
        )

        raise RuntimeError(
            "Repository Helm command failed:\n"
            f"command: {command}\n"
            f"exit: {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

    return result.stdout


def approved_repositories() -> dict[str, dict[str, Any]]:
    """Return approved Helm repositories keyed by name."""
    payload = load_json_mapping(REPOSITORIES_PATH)
    repositories = payload.get("repositories")

    if not isinstance(repositories, list):
        raise ValueError(
            "helm-repositories.json: repositories must be a list"
        )

    result: dict[str, dict[str, Any]] = {}

    for repository in repositories:
        if not isinstance(repository, dict):
            raise ValueError(
                "helm-repositories.json: repository entry "
                "must be a mapping"
            )

        name = repository.get("name")

        if not isinstance(name, str) or not name:
            raise ValueError(
                "helm-repositories.json: repository name missing"
            )

        result[name] = repository

    return result


def render_locked_chart(
    *,
    chart_key: str,
    values_path: Path,
    manifest_path: Path,
    lock: dict[str, Any],
    repositories: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Render one exact chart from the repository lock."""
    charts = lock.get("charts")

    if not isinstance(charts, dict):
        raise ValueError(
            "helm-chart-lock.json: charts must be a mapping"
        )

    chart = charts.get(chart_key)

    if not isinstance(chart, dict):
        raise ValueError(
            f"helm-chart-lock.json: missing chart {chart_key}"
        )

    chart_ref = chart.get("chart")
    version = chart.get("version")
    release = chart.get("release")
    namespace = chart.get("namespace")
    enabled_variable = chart.get("enabled_variable")

    required_strings = {
        "chart": chart_ref,
        "version": version,
        "release": release,
        "namespace": namespace,
    }

    for field, value in required_strings.items():
        if not isinstance(value, str) or not value:
            raise ValueError(
                f"helm-chart-lock.json: "
                f"{chart_key}.{field} is missing"
            )

    if enabled_variable != "deploy_centralized_logging":
        raise ValueError(
            f"helm-chart-lock.json: {chart_key} has unexpected "
            f"activation variable {enabled_variable!r}"
        )

    repository_name = chart_ref.split("/", 1)[0]
    repository = repositories.get(repository_name)

    if not isinstance(repository, dict):
        raise ValueError(
            f"No approved repository for chart {chart_ref}"
        )

    repository_url = repository.get("url")

    if not isinstance(repository_url, str) or not repository_url:
        raise ValueError(
            f"Approved repository URL missing for "
            f"{repository_name}"
        )

    run_helm(
        [
            "repo",
            "add",
            repository_name,
            repository_url,
            "--force-update",
        ]
    )

    manifest = run_helm(
        [
            "template",
            release,
            chart_ref,
            "--version",
            version,
            "--namespace",
            namespace,
            "--include-crds",
            "--values",
            str(values_path),
        ]
    )

    manifest_path.write_text(
        manifest,
        encoding="utf-8",
    )

    print(
        "PASS locked chart render: "
        f"{chart_ref} version={version} "
        f"release={release} namespace={namespace}"
    )

    return chart


def validate_loki_manifests(path: Path) -> None:
    """Validate the rendered Loki Kubernetes objects."""
    documents = load_manifest_stream(path)

    workloads = [
        document
        for document in documents
        if document.get("kind") in {
            "Deployment",
            "StatefulSet",
        }
    ]

    if not workloads:
        raise ValueError(
            "Loki manifests: no Deployment or StatefulSet rendered"
        )

    placement_matches = 0
    persistence_matches = 0

    for workload in workloads:
        specification = workload.get("spec") or {}
        pod_specification = (
            specification.get("template", {})
            .get("spec", {})
        )
        selector = pod_specification.get("nodeSelector") or {}

        if selector:
            if selector.get("kubernetes.io/arch") != "amd64":
                raise ValueError(
                    "Loki manifests: unexpected architecture "
                    f"selector {selector}"
                )

            if (
                selector.get("kalaxy3.io/workload-pool")
                != "platform-services"
            ):
                raise ValueError(
                    "Loki manifests: unexpected workload-pool "
                    f"selector {selector}"
                )

            placement_matches += 1

        claims = specification.get(
            "volumeClaimTemplates",
            [],
        ) or []

        for claim in claims:
            claim_specification = claim.get("spec") or {}
            requests = (
                claim_specification.get("resources", {})
                .get("requests", {})
            )

            if (
                claim_specification.get("storageClassName")
                == "longhorn"
                and requests.get("storage") == "40Gi"
            ):
                persistence_matches += 1

    if placement_matches < 1:
        raise ValueError(
            "Loki manifests: required amd64/platform-services "
            "placement was not rendered"
        )

    if persistence_matches < 1:
        raise ValueError(
            "Loki manifests: Longhorn 40Gi persistence "
            "was not rendered"
        )

    test_hooks = []

    for document in documents:
        metadata = document.get("metadata") or {}
        annotations = metadata.get("annotations") or {}
        hook = str(annotations.get("helm.sh/hook") or "")

        if "test" in hook:
            test_hooks.append(document)

    if test_hooks:
        raise ValueError(
            "Loki manifests: unexpected Helm test hooks rendered"
        )

    manifest = path.read_text(encoding="utf-8")

    required_configuration = (
        "object_store: filesystem",
        "chunks_directory: /var/loki/chunks",
        "rules_directory: /var/loki/rules",
    )

    for setting in required_configuration:
        if setting not in manifest:
            raise ValueError(
                "Loki manifests: missing filesystem setting "
                f"{setting}"
            )

    print(
        "PASS Loki manifests: "
        "amd64/platform-services, Longhorn=40Gi, "
        "filesystem storage, no test hook"
    )


def validate_fluent_bit_manifests(path: Path) -> None:
    """Validate the rendered Fluent Bit Kubernetes objects."""
    documents = load_manifest_stream(path)

    daemonsets = [
        document
        for document in documents
        if document.get("kind") == "DaemonSet"
    ]

    if len(daemonsets) != 1:
        raise ValueError(
            "Fluent Bit manifests: expected one DaemonSet, "
            f"found {len(daemonsets)}"
        )

    daemonset = daemonsets[0]
    metadata = daemonset.get("metadata") or {}

    if metadata.get("namespace") != "observability":
        raise ValueError(
            "Fluent Bit manifests: namespace must be observability"
        )

    pod_specification = (
        daemonset.get("spec", {})
        .get("template", {})
        .get("spec", {})
    )

    selector = pod_specification.get("nodeSelector") or {}

    for forbidden_key in (
        "kubernetes.io/arch",
        "kalaxy3.io/workload-pool",
    ):
        if forbidden_key in selector:
            raise ValueError(
                "Fluent Bit manifests: collector must remain "
                f"all-node; found selector {selector}"
            )

    tolerations = pod_specification.get("tolerations") or []

    if not any(
        isinstance(toleration, dict)
        and toleration.get("operator") == "Exists"
        for toleration in tolerations
    ):
        raise ValueError(
            "Fluent Bit manifests: all-node toleration missing"
        )

    containers = pod_specification.get("containers") or []

    if not containers:
        raise ValueError(
            "Fluent Bit manifests: no collector container rendered"
        )

    print(
        "PASS Fluent Bit manifests: "
        "one all-node DaemonSet in observability"
    )


def validate_locked_charts(render_dir: Path) -> None:
    """Render and validate exact centralized-logging chart locks."""
    lock = load_json_mapping(CHART_LOCK_PATH)
    repositories = approved_repositories()
    manifest_dir = render_dir / "manifests"

    if manifest_dir.exists():
        shutil.rmtree(manifest_dir)

    manifest_dir.mkdir(
        parents=True,
        mode=0o755,
    )

    loki_manifest = manifest_dir / "loki-manifests.yml"
    fluent_manifest = (
        manifest_dir / "fluent-bit-manifests.yml"
    )

    render_locked_chart(
        chart_key="loki",
        values_path=render_dir / "loki-values.yml",
        manifest_path=loki_manifest,
        lock=lock,
        repositories=repositories,
    )

    render_locked_chart(
        chart_key="fluent_bit_collector",
        values_path=render_dir / "fluent-bit-values.yml",
        manifest_path=fluent_manifest,
        lock=lock,
        repositories=repositories,
    )

    validate_loki_manifests(loki_manifest)
    validate_fluent_bit_manifests(fluent_manifest)

    print(
        "PASS locked centralized-logging chart validation"
    )


def main() -> int:
    """Validate rendered values and exact locked charts."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "render_dir",
        type=Path,
        help="Directory containing rendered logging YAML",
    )
    args = parser.parse_args()
    render_dir: Path = args.render_dir

    missing = [
        name
        for name in EXPECTED_FILES
        if not (render_dir / name).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing rendered files: {', '.join(missing)}"
        )

    loki = load_single_document(
        render_dir / "loki-values.yml"
    )
    fluent_bit = load_single_document(
        render_dir / "fluent-bit-values.yml"
    )
    datasource = load_single_document(
        render_dir / "grafana-loki-datasource.yml"
    )

    validate_loki(loki)
    validate_fluent_bit(fluent_bit)
    validate_datasource(datasource)

    for name in EXPECTED_FILES:
        print(f"PASS YAML: {name}")

    print(
        "PASS placement: Loki=platform-services; "
        "Fluent Bit=all nodes"
    )
    print("PASS activation gate: validated by playbook")

    validate_locked_charts(render_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
