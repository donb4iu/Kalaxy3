#!/usr/bin/env python3
"""Fail closed unless Helm repository authority remains intact."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit


ROOT: Final = Path(__file__).resolve().parents[1]
REGISTRY_PATH: Final = ROOT / "helm-repositories.json"
REQUIRED_FIELDS: Final = {"name", "url", "url_sha256"}
TRUSTED_REPOSITORIES: Final = {
    "fluent": "https://fluent.github.io/helm-charts/",
    "grafana": "https://grafana.github.io/helm-charts",
    "grafana-community": (
        "https://grafana-community.github.io/helm-charts"
    ),
    "headlamp": "https://kubernetes-sigs.github.io/headlamp/",
    "kubernetes-dashboard": "https://kubernetes.github.io/dashboard/",
    "longhorn": "https://charts.longhorn.io",
    "metallb": "https://metallb.github.io/metallb",
    "nfs": (
        "https://kubernetes-sigs.github.io/"
        "nfs-subdir-external-provisioner"
    ),
    "prometheus-community": (
        "https://prometheus-community.github.io/helm-charts"
    ),
}


def sha256_text(value: str) -> str:
    """Calculate a lowercase SHA-256 digest.

    Args:
        value: Text to hash.

    Returns:
        Sixty-four-character hexadecimal digest.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_registry(path: Path) -> dict[str, Any]:
    """Load the Helm repository registry.

    Args:
        path: Registry JSON path.

    Returns:
        Parsed registry object.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Helm repository registry must be an object")
    return payload


def validate_url(name: str, url: str) -> list[str]:
    """Validate one approved repository URL.

    Args:
        name: Repository name.
        url: Repository URL.

    Returns:
        Validation failure messages.
    """
    failures: list[str] = []
    parsed = urlsplit(url)

    if url != url.strip():
        failures.append(f"{name}: repository URL contains whitespace")
    if parsed.scheme != "https":
        failures.append(f"{name}: repository URL is not HTTPS")
    if not parsed.hostname:
        failures.append(f"{name}: repository URL lacks a hostname")
    if parsed.username or parsed.password:
        failures.append(f"{name}: repository URL contains credentials")
    if parsed.query or parsed.fragment:
        failures.append(f"{name}: repository URL has query or fragment")
    if parsed.port is not None:
        failures.append(f"{name}: repository URL uses an explicit port")

    return failures


def validate_entry(item: Any, index: int) -> list[str]:
    """Validate one repository registry entry.

    Args:
        item: Registry entry.
        index: Entry position.

    Returns:
        Validation failure messages.
    """
    if not isinstance(item, dict):
        return [f"repository[{index}] is not an object"]

    failures: list[str] = []
    fields = set(item)

    if fields != REQUIRED_FIELDS:
        failures.append(
            f"repository[{index}] fields are {sorted(fields)}; "
            f"expected {sorted(REQUIRED_FIELDS)}"
        )

    name = str(item.get("name", ""))
    url = str(item.get("url", ""))
    fingerprint = str(item.get("url_sha256", ""))

    if re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) is None:
        failures.append(f"repository[{index}] has invalid name {name!r}")

    failures.extend(validate_url(name or f"repository[{index}]", url))

    if re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None:
        failures.append(f"{name}: URL fingerprint is not exact SHA-256")
    elif fingerprint != sha256_text(url):
        failures.append(f"{name}: URL fingerprint does not match URL")

    return failures


def validate_registry(
    payload: dict[str, Any],
    trusted: dict[str, str],
) -> list[str]:
    """Validate registry schema, uniqueness, and trusted authority.

    Args:
        payload: Parsed repository registry.
        trusted: Independently controlled repository mapping.

    Returns:
        Validation failure messages.
    """
    failures: list[str] = []

    if payload.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")

    repositories = payload.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        return failures + ["repositories must be a non-empty list"]

    for index, item in enumerate(repositories):
        failures.extend(validate_entry(item, index))

    entries = [item for item in repositories if isinstance(item, dict)]
    names = [str(item.get("name", "")) for item in entries]
    urls = [str(item.get("url", "")) for item in entries]

    if len(names) != len(set(names)):
        failures.append("repository names are not unique")
    if len(urls) != len(set(urls)):
        failures.append("repository URLs are not unique")

    actual = {
        str(item.get("name", "")): str(item.get("url", ""))
        for item in entries
    }
    if actual != trusted:
        failures.append("repository authority differs from trusted mapping")

    return failures


def build_negative_cases(
    payload: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """Build repository-integrity mutation cases.

    Args:
        payload: Valid registry payload.

    Returns:
        Named malformed registry payloads.
    """
    cases: list[tuple[str, dict[str, Any]]] = []

    wrong_schema = copy.deepcopy(payload)
    wrong_schema["schema_version"] = "2.0"
    cases.append(("wrong schema", wrong_schema))

    duplicate_name = copy.deepcopy(payload)
    duplicate_name["repositories"][1]["name"] = (
        duplicate_name["repositories"][0]["name"]
    )
    cases.append(("duplicate name", duplicate_name))

    duplicate_url = copy.deepcopy(payload)
    duplicate_url["repositories"][1]["url"] = (
        duplicate_url["repositories"][0]["url"]
    )
    duplicate_url["repositories"][1]["url_sha256"] = sha256_text(
        duplicate_url["repositories"][1]["url"]
    )
    cases.append(("duplicate URL", duplicate_url))

    insecure_url = copy.deepcopy(payload)
    insecure_url["repositories"][0]["url"] = "http://example.invalid/charts"
    insecure_url["repositories"][0]["url_sha256"] = sha256_text(
        insecure_url["repositories"][0]["url"]
    )
    cases.append(("HTTP URL", insecure_url))

    wrong_hash = copy.deepcopy(payload)
    wrong_hash["repositories"][0]["url_sha256"] = "0" * 64
    cases.append(("wrong URL fingerprint", wrong_hash))

    altered_url = copy.deepcopy(payload)
    altered_url["repositories"][0]["url"] = (
        "https://example.invalid/altered"
    )
    altered_url["repositories"][0]["url_sha256"] = sha256_text(
        altered_url["repositories"][0]["url"]
    )
    cases.append(("altered trusted URL", altered_url))

    missing = copy.deepcopy(payload)
    missing["repositories"].pop()
    cases.append(("missing trusted repository", missing))

    extra = copy.deepcopy(payload)
    extra["repositories"].append(
        {
            "name": "unapproved",
            "url": "https://example.invalid/charts",
            "url_sha256": sha256_text(
                "https://example.invalid/charts"
            ),
        }
    )
    cases.append(("extra unapproved repository", extra))

    return cases


def run_negative_tests(payload: dict[str, Any]) -> list[str]:
    """Require every repository mutation to fail validation.

    Args:
        payload: Valid registry payload.

    Returns:
        Negative-test failures.
    """
    failures: list[str] = []

    for label, candidate in build_negative_cases(payload):
        if not validate_registry(candidate, TRUSTED_REPOSITORIES):
            failures.append(f"negative test accepted {label}")

    return failures


def main() -> int:
    """Run Helm repository integrity validation.

    Returns:
        Process exit status.
    """
    try:
        payload = load_registry(REGISTRY_PATH)
    except (OSError, ValueError, TypeError) as error:
        print("Kalaxy3 Helm repository guardrail: FAIL CLOSED")
        print(f"  - {error}")
        return 1

    failures = validate_registry(payload, TRUSTED_REPOSITORIES)
    failures.extend(run_negative_tests(payload))

    if failures:
        print("Kalaxy3 Helm repository guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS Helm repository schema and required fields")
    print("PASS repository names and URLs are unique")
    print("PASS HTTPS-only repository URL policy")
    print("PASS repository URL SHA-256 fingerprints")
    print("PASS independently controlled repository authority mapping")
    print("PASS repository tamper and mutation negative tests")
    print("Kalaxy3 Helm repository guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
