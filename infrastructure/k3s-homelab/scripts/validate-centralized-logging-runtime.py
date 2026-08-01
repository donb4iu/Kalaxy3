#!/usr/bin/env python3
"""Validate the active Kalaxy3 centralized-logging deployment."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Final, Iterator, Sequence


ROOT: Final = Path(__file__).resolve().parent.parent
REPO_ROOT: Final = ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts/sage"))
from sage_yaml_metadata import load_yaml_metadata
INVENTORY_PATH: Final = ROOT / "inventory/group_vars/all/main.yml"
LOCK_PATH: Final = ROOT / "helm-chart-lock.json"
HELM_WRAPPER: Final = ROOT / "scripts/helm"
NAMESPACE: Final = "observability"
ACTIONABLE_FAILURE_IDS: Final = (
    "centralized_logging.runtime_requires_active_gate",
)
REQUIRED_SECTIONS: Final = (
    "SAGE ACTION BLOCKED",
    "Attempted action",
    "Detected state",
    "Why this is invalid",
    "Likely intended outcome",
    "Confirm the correct approach",
    "Allowed actions",
    "Prohibited actions",
    "Canonical recovery",
    "SAGE integrity requirements",
    "Repository gap",
)


class ValidationError(RuntimeError):
    """Represent an actionable centralized-logging validation failure."""


def actionable_failure(
    *,
    attempted: str,
    detected: str,
    why: str,
    intended: str,
    confirm: str,
    allowed: Sequence[str],
    prohibited: Sequence[str],
    recovery: str,
    integrity: str,
    gap: str,
) -> str:
    """Build a self-contained SAGE actionable failure message."""
    allowed_text = "\n".join(f"  - {item}" for item in allowed)
    prohibited_text = "\n".join(f"  - {item}" for item in prohibited)
    return (
        "SAGE ACTION BLOCKED\n\n"
        f"Attempted action:\n  {attempted}\n\n"
        f"Detected state:\n  {detected}\n\n"
        f"Why this is invalid:\n  {why}\n\n"
        f"Likely intended outcome:\n  {intended}\n\n"
        f"Confirm the correct approach:\n  {confirm}\n\n"
        f"Allowed actions:\n{allowed_text}\n\n"
        f"Prohibited actions:\n{prohibited_text}\n\n"
        f"Canonical recovery:\n  {recovery}\n\n"
        f"SAGE integrity requirements:\n  {integrity}\n\n"
        f"Repository gap:\n  {gap}"
    )


def load_mapping(path: Path) -> dict[str, Any]:
    """Load repository JSON or opaque-tag YAML metadata."""
    if path.suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValidationError(f"{path}: expected a mapping")
        return payload
    return load_yaml_metadata(path)


def run_text(command: Sequence[str]) -> str:
    """Run a command and return standard output."""
    result = subprocess.run(
        list(command),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout


def run_json(command: Sequence[str]) -> dict[str, Any]:
    """Run a command whose output must be a JSON mapping."""
    payload = json.loads(run_text(command))
    if not isinstance(payload, dict):
        raise ValidationError(
            f"command returned non-mapping JSON: {' '.join(command)}"
        )
    return payload


def resolve_kubectl() -> str:
    """Return the repository wrapper or installed kubectl executable."""
    wrapper = ROOT / "scripts/kubectl"
    if wrapper.is_file() and wrapper.stat().st_mode & 0o111:
        return str(wrapper)
    executable = shutil.which("kubectl")
    if executable:
        return executable
    raise ValidationError(
        actionable_failure(
            attempted="Validate active centralized logging.",
            detected="No repository kubectl wrapper or kubectl executable.",
            why=(
                "Runtime state cannot be established without the cluster "
                "authority used by the repository."
            ),
            intended=(
                "SAGE infers that the operator intended to validate the "
                "already active logging deployment."
            ),
            confirm=(
                "Review infrastructure/k3s-homelab/scripts and the source "
                "guardrails for the repository-owned kubectl authority."
            ),
            allowed=(
                "Install or restore the repository-approved kubectl path.",
                "Run make source-guardrails after restoring tooling.",
            ),
            prohibited=(
                "Do not substitute an unapproved cluster client.",
                "Do not bypass runtime validation.",
            ),
            recovery="make source-guardrails",
            integrity=(
                "Preserve kubeconfig authority, cluster context, terminal "
                "evidence, and repository-owned tooling."
            ),
            gap=(
                "If no approved kubectl authority exists, record a systemic "
                "repository capability gap."
            ),
        )
    )


def require_active_gate() -> None:
    """Require centralized logging to be active before runtime validation."""
    inventory = load_mapping(INVENTORY_PATH)
    active = inventory.get("deploy_centralized_logging")
    if active is True:
        return
    raise ValidationError(
        actionable_failure(
            attempted="Validate active centralized logging.",
            detected=f"deploy_centralized_logging={active!r}.",
            why=(
                "The runtime validator is valid only after the repository "
                "activation gate is true."
            ),
            intended=(
                "SAGE infers that the operator may intend staged render "
                "validation instead."
            ),
            confirm=(
                "Inspect inventory/group_vars/all/main.yml and run "
                "SAGE_REQUEST='Validate centralized logging' make "
                "sage-preflight from the repository root."
            ),
            allowed=(
                "Run make centralized-logging-render while staged.",
                "Review the authoritative activation gate.",
            ),
            prohibited=(
                "Do not enable logging merely to satisfy this validator.",
                "Do not bypass the lifecycle gate.",
            ),
            recovery="make centralized-logging-render",
            integrity=(
                "Preserve lifecycle truth, authoritative inventory, "
                "guardrails, and failed-path evidence."
            ),
            gap=(
                "If lifecycle state is ambiguous, discovery must identify "
                "and correct the authority gap."
            ),
        )
    )


def expected_releases(lock: dict[str, Any]) -> dict[str, str]:
    """Return expected centralized-logging release chart versions."""
    charts = lock.get("charts")
    if not isinstance(charts, dict):
        raise ValidationError("helm-chart-lock.json: charts must be a mapping")
    expected: dict[str, str] = {}
    for chart in charts.values():
        if not isinstance(chart, dict):
            continue
        release = chart.get("release")
        version = chart.get("version")
        if release in {"loki", "fluent-bit-collector"}:
            if not isinstance(version, str):
                raise ValidationError(f"{release}: lock version missing")
            expected[release] = version
    if set(expected) != {"loki", "fluent-bit-collector"}:
        raise ValidationError("centralized-logging chart locks are incomplete")
    return expected


def validate_helm_releases() -> dict[str, str]:
    """Validate active Helm releases against repository chart locks."""
    if not HELM_WRAPPER.is_file():
        raise ValidationError(f"repository Helm wrapper missing: {HELM_WRAPPER}")
    releases = json.loads(
        run_text(
            (
                str(HELM_WRAPPER),
                "list",
                "--namespace",
                NAMESPACE,
                "--output",
                "json",
            )
        )
    )
    if not isinstance(releases, list):
        raise ValidationError("Helm list output must be a list")
    actual = {
        item.get("name"): item
        for item in releases
        if isinstance(item, dict)
    }
    expected = expected_releases(load_mapping(LOCK_PATH))
    for release, version in expected.items():
        item = actual.get(release)
        if not item or item.get("status") != "deployed":
            raise ValidationError(f"Helm release {release} is not deployed")
        chart = str(item.get("chart", ""))
        if not chart.endswith(f"-{version}"):
            raise ValidationError(
                f"{release}: live chart {chart!r} does not match {version}"
            )
    return expected


def kubectl_json(kubectl: str, arguments: Sequence[str]) -> dict[str, Any]:
    """Run kubectl and return one JSON mapping."""
    return run_json((kubectl, *arguments, "-o", "json"))


def ready_count(status: dict[str, Any], key: str) -> int:
    """Return one integer Kubernetes status count."""
    value = status.get(key, 0)
    return int(value) if isinstance(value, int) else 0


def validate_workloads(kubectl: str) -> dict[str, int]:
    """Validate collector, Loki, and gateway readiness."""
    daemonset = kubectl_json(
        kubectl,
        ("-n", NAMESPACE, "get", "daemonset", "fluent-bit-collector"),
    )
    status = daemonset.get("status", {})
    desired = ready_count(status, "desiredNumberScheduled")
    ready = ready_count(status, "numberReady")
    available = ready_count(status, "numberAvailable")
    if not desired or ready != desired or available != desired:
        raise ValidationError(
            f"Fluent Bit readiness mismatch: "
            f"desired={desired} ready={ready} available={available}"
        )
    statefulset = kubectl_json(
        kubectl,
        ("-n", NAMESPACE, "get", "statefulset", "loki"),
    )
    loki_status = statefulset.get("status", {})
    if ready_count(loki_status, "readyReplicas") != 1:
        raise ValidationError("Loki StatefulSet is not 1/1 ready")
    gateway = kubectl_json(
        kubectl,
        ("-n", NAMESPACE, "get", "deployment", "loki-gateway"),
    )
    gateway_status = gateway.get("status", {})
    if ready_count(gateway_status, "availableReplicas") != 1:
        raise ValidationError("Loki gateway is not 1/1 available")
    return {"collectors": desired, "loki": 1, "gateway": 1}


def validate_storage(kubectl: str) -> dict[str, str]:
    """Validate Loki persistent storage and placement authority."""
    pvc = kubectl_json(
        kubectl,
        ("-n", NAMESPACE, "get", "pvc", "storage-loki-0"),
    )
    phase = pvc.get("status", {}).get("phase")
    spec = pvc.get("spec", {})
    storage_class = spec.get("storageClassName")
    requested = (
        spec.get("resources", {})
        .get("requests", {})
        .get("storage")
    )
    if phase != "Bound":
        raise ValidationError(f"Loki PVC phase is {phase!r}, not Bound")
    if storage_class != "longhorn":
        raise ValidationError(
            f"Loki PVC storageClassName is {storage_class!r}"
        )
    if requested != "40Gi":
        raise ValidationError(f"Loki PVC request is {requested!r}")
    return {
        "phase": str(phase),
        "storage_class": str(storage_class),
        "requested": str(requested),
    }


def validate_datasource(kubectl: str) -> int:
    """Require at least one repository-labeled Grafana datasource."""
    payload = kubectl_json(
        kubectl,
        (
            "-n",
            NAMESPACE,
            "get",
            "configmap",
            "-l",
            "grafana_datasource=1",
        ),
    )
    items = payload.get("items", [])
    if not isinstance(items, list) or not items:
        raise ValidationError("Grafana Loki datasource ConfigMap is missing")
    return len(items)


@contextmanager
def port_forward(kubectl: str) -> Iterator[str]:
    """Expose the Loki gateway locally for API validation."""
    command = (
        kubectl,
        "-n",
        NAMESPACE,
        "port-forward",
        "service/loki-gateway",
        "13100:80",
    )
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        yield "http://127.0.0.1:13100"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def http_json(url: str) -> dict[str, Any]:
    """Fetch one Loki JSON response."""
    with urllib.request.urlopen(url, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError(f"Loki returned non-mapping JSON: {url}")
    return payload


def wait_for_loki(base_url: str) -> None:
    """Wait briefly for the port-forwarded Loki API."""
    last_error = ""
    for _ in range(20):
        try:
            payload = http_json(f"{base_url}/loki/api/v1/labels")
            if payload:
                return
        except Exception as error:  # noqa: BLE001
            last_error = str(error)
        time.sleep(0.5)
    raise ValidationError(f"Loki API did not become ready: {last_error}")


def node_names(kubectl: str) -> set[str]:
    """Return all current Kubernetes node names."""
    payload = kubectl_json(kubectl, ("get", "nodes"))
    items = payload.get("items", [])
    if not isinstance(items, list):
        raise ValidationError("kubectl node list is invalid")
    return {
        str(item.get("metadata", {}).get("name"))
        for item in items
        if isinstance(item, dict)
    }


def label_values(base_url: str, label: str) -> set[str]:
    """Return all values for one Loki label."""
    encoded = urllib.parse.quote(label, safe="")
    payload = http_json(
        f"{base_url}/loki/api/v1/label/{encoded}/values"
    )
    data = payload.get("data", [])
    if not isinstance(data, list):
        return set()
    return {str(value) for value in data}


def select_node_label(
    candidates: Sequence[str],
    values: dict[str, set[str]],
    nodes: set[str],
) -> str | None:
    """Select the Loki label whose values cover every node."""
    for candidate in candidates:
        if nodes and nodes.issubset(values.get(candidate, set())):
            return candidate
    return None


def validate_loki_data(kubectl: str) -> dict[str, Any]:
    """Validate Loki API health, recent logs, and all-node coverage."""
    nodes = node_names(kubectl)
    candidates = (
        "kubernetes_host",
        "node_name",
        "node",
        "host",
        "kubernetes_node_name",
        "kubernetes_node",
        "k8s_node_name",
    )
    with port_forward(kubectl) as base_url:
        wait_for_loki(base_url)
        labels_payload = http_json(f"{base_url}/loki/api/v1/labels")
        labels = set(labels_payload.get("data", []))
        available = [item for item in candidates if item in labels]
        values = {
            label: label_values(base_url, label)
            for label in available
        }
        selected = select_node_label(available, values, nodes)
        if selected is None:
            raise ValidationError(
                "Loki labels do not prove log coverage for every node; "
                f"nodes={sorted(nodes)} candidates={available}"
            )
        query = urllib.parse.urlencode(
            {
                "query": f'{{{selected}=~".+"}}',
                "limit": "1",
                "start": str(int((time.time() - 21600) * 1_000_000_000)),
            }
        )
        payload = http_json(
            f"{base_url}/loki/api/v1/query_range?{query}"
        )
        result = payload.get("data", {}).get("result", [])
        if not isinstance(result, list) or not result:
            raise ValidationError("Loki returned no logs from the last 6 hours")
    return {
        "node_label": selected,
        "covered_nodes": sorted(nodes),
        "recent_query_results": len(result),
    }


def validate_runtime() -> dict[str, Any]:
    """Run every active centralized-logging validation."""
    require_active_gate()
    kubectl = resolve_kubectl()
    return {
        "helm_releases": validate_helm_releases(),
        "workloads": validate_workloads(kubectl),
        "storage": validate_storage(kubectl),
        "datasource_configmaps": validate_datasource(kubectl),
        "loki_data": validate_loki_data(kubectl),
        "kubectl": kubectl,
    }


def parse_arguments() -> argparse.Namespace:
    """Parse runtime-validator command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit only the final JSON validation summary.",
    )
    return parser.parse_args()


def main() -> int:
    """Validate active logging and print the result."""
    arguments = parse_arguments()
    try:
        summary = validate_runtime()
    except (
        json.JSONDecodeError,
        OSError,
        ValidationError,
        urllib.error.URLError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2
    if arguments.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Kalaxy3 centralized logging runtime validation: PASS")
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
