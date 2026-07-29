#!/usr/bin/env python3
"""Discover SAGE authority and validation for a requested change."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Final, Sequence


ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_MAP: Final = ROOT / "sage-change-authority.json"


def normalize(value: str) -> str:
    """Normalize text for deterministic matching."""
    return " ".join(value.lower().replace("_", " ").split())


def load_authority_map(path: Path) -> dict[str, Any]:
    """Load the repository-owned authority map."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Authority map must be a JSON object")
    return payload


def validate_context(
    context: Any,
    context_ids: set[str],
) -> list[str]:
    """Validate one authority context."""
    required = {
        "id",
        "priority",
        "match_terms",
        "path_prefixes",
        "requires",
        "working_directory",
        "authoritative_files",
        "baseline_checks",
        "required_validation",
        "evidence_process",
    }
    if not isinstance(context, dict):
        return ["Context entry is not an object"]

    failures: list[str] = []
    missing = sorted(required - set(context))
    if missing:
        failures.append(
            f"{context.get('id', '<unknown>')}: "
            f"missing fields {missing}"
        )

    context_id = str(context.get("id", ""))
    unknown = sorted(
        set(context.get("requires", [])) - context_ids
    )
    if unknown:
        failures.append(
            f"{context_id}: unknown dependencies {unknown}"
        )
    return failures


def validate_authority_map(
    payload: dict[str, Any],
) -> list[str]:
    """Validate the complete authority map."""
    failures: list[str] = []
    if payload.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")

    contexts = payload.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        return failures + ["contexts must be a non-empty list"]

    ids = [
        str(item.get("id", ""))
        for item in contexts
        if isinstance(item, dict)
    ]
    if len(ids) != len(set(ids)):
        failures.append("Context identifiers are not unique")

    context_ids = set(ids)
    unknown_always = sorted(
        set(payload.get("always_contexts", [])) - context_ids
    )
    if unknown_always:
        failures.append(
            f"Unknown always_contexts: {unknown_always}"
        )

    for context in contexts:
        failures.extend(
            validate_context(context, context_ids)
        )
    return failures


def infer_context_ids(
    payload: dict[str, Any],
    request: str,
    paths: Sequence[str],
) -> set[str]:
    """Infer matching contexts from request and changed paths."""
    request_text = normalize(request)
    normalized_paths = [normalize(path) for path in paths]
    matches = set(payload.get("always_contexts", []))

    for context in payload["contexts"]:
        terms = [
            normalize(term)
            for term in context["match_terms"]
        ]
        prefixes = [
            normalize(item)
            for item in context["path_prefixes"]
        ]

        if any(
            term and term in request_text
            for term in terms
        ):
            matches.add(str(context["id"]))
            continue

        path_match = any(
            path.startswith(prefix)
            for path in normalized_paths
            for prefix in prefixes
            if prefix
        )
        if path_match:
            matches.add(str(context["id"]))
    return matches


def expand_dependencies(
    payload: dict[str, Any],
    context_ids: set[str],
) -> set[str]:
    """Expand recursively required contexts."""
    contexts = {
        str(item["id"]): item
        for item in payload["contexts"]
    }
    expanded = set(context_ids)

    while True:
        before = set(expanded)
        for context_id in tuple(expanded):
            expanded.update(
                contexts[context_id]["requires"]
            )
        if expanded == before:
            return expanded


def ordered_contexts(
    payload: dict[str, Any],
    context_ids: set[str],
) -> list[dict[str, Any]]:
    """Return selected contexts in priority order."""
    selected = [
        item
        for item in payload["contexts"]
        if str(item["id"]) in context_ids
    ]
    return sorted(
        selected,
        key=lambda item: (
            int(item["priority"]),
            str(item["id"]),
        ),
    )


def changed_paths() -> list[str]:
    """Read tracked and untracked changed paths from Git."""
    commands = (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
    )
    paths: set[str] = set()

    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        paths.update(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )
    return sorted(paths)


def print_group(
    label: str,
    values: Sequence[str],
) -> None:
    """Print one labeled report group."""
    print(f"\n{label}:")
    for value in dict.fromkeys(values):
        print(f"  - {value}")


def render_report(
    request: str,
    paths: Sequence[str],
    contexts: Sequence[dict[str, Any]],
) -> None:
    """Render the discovery report."""
    print("Kalaxy3 SAGE change discovery: PASS")
    print(f"Repository: {ROOT}")
    print(
        f"Request: "
        f"{request or '<changed-path discovery>'}"
    )

    if paths:
        print_group("Changed paths considered", paths)

    print_group(
        "Inferred SAGE contexts",
        [str(item["id"]) for item in contexts],
    )

    for context in contexts:
        print(f"\n[{context['id']}]")
        print(
            "  Working directory: "
            f"{context['working_directory']}"
        )
        print_group(
            "  Authoritative files",
            context["authoritative_files"],
        )
        print_group(
            "  Baseline checks before editing",
            context["baseline_checks"],
        )
        print_group(
            "  Required validation after editing",
            context["required_validation"],
        )
        print_group(
            "  Evidence process",
            context["evidence_process"],
        )

    print("\nImplementation policy:")
    print(
        "  - Read every listed authoritative file "
        "before editing."
    )
    print(
        "  - Run baseline checks before implementation."
    )
    print(
        "  - Treat inactive reviewable code as a "
        "staged implementation."
    )
    print(
        "  - Run validation before activation or publication."
    )
    print(
        "  - Preserve terminal evidence for the SAGE record."
    )


def infer_for_request(
    payload: dict[str, Any],
    request: str,
) -> set[str]:
    """Infer and expand contexts for one request."""
    initial = infer_context_ids(payload, request, [])
    return expand_dependencies(payload, initial)


def run_self_tests(
    payload: dict[str, Any],
) -> list[str]:
    """Run deterministic discovery regression tests."""
    cases = {
        "Add centralized logging with Loki and Fluent Bit": {
            "centralized-logging",
            "observability",
            "helm-platform",
            "storage",
            "repository-governance",
            "evidence",
        },
        "Replace Daux with MkDocs Material documentation": {
            "documentation",
            "repository-governance",
            "evidence",
        },
        "Add a new K3s control plane node and validate etcd": {
            "k3s-cluster",
            "repository-governance",
            "evidence",
        },
        (
            "agreed, make it so, but remember frequent pushes "
            "to a feature branch is good practice"
        ): {
            "continuous-improvement",
            "repository-governance",
            "evidence",
        },
        "Add prediction accuracy and T-shirt sizing": {
            "continuous-improvement",
            "repository-governance",
            "evidence",
        },
    }
    failures: list[str] = []

    for request, expected in cases.items():
        actual = infer_for_request(payload, request)
        missing = sorted(expected - actual)
        if missing:
            failures.append(
                f"{request!r} did not infer {missing}"
            )

    path_cases = {
        "Helm repository path": (
            [
                "infrastructure/k3s-homelab/"
                "helm-repositories.json"
            ],
            {
                "helm-platform",
                "repository-governance",
                "evidence",
            },
        ),
        "documentation path": (
            ["README.md"],
            {
                "documentation",
                "repository-governance",
                "evidence",
            },
        ),
        "continuous-improvement path": (
            [
                "markdown/standards/"
                "kalaxy3-sage-continuous-improvement-process.md"
            ],
            {
                "continuous-improvement",
                "repository-governance",
                "evidence",
            },
        ),
    }

    for label, (paths, expected) in path_cases.items():
        initial = infer_context_ids(payload, "", paths)
        actual = expand_dependencies(payload, initial)
        missing = sorted(expected - actual)
        if missing:
            failures.append(
                f"{label} did not infer {missing}"
            )

    return failures


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Infer repository-owned SAGE authority"
    )
    parser.add_argument("--request", default="")
    parser.add_argument("--changed", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--authority-map",
        type=Path,
        default=DEFAULT_MAP,
    )
    return parser.parse_args()


def main() -> int:
    """Run SAGE change discovery."""
    args = parse_args()

    try:
        payload = load_authority_map(args.authority_map)
    except (OSError, ValueError, TypeError) as error:
        print(
            "Kalaxy3 SAGE change discovery: FAIL"
            f"\n  - {error}"
        )
        return 1

    failures = validate_authority_map(payload)
    if failures:
        print("Kalaxy3 SAGE change discovery: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    if args.self_test:
        failures = run_self_tests(payload)
        if failures:
            print(
                "Kalaxy3 SAGE change discovery self-test: FAIL"
            )
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print(
            "Kalaxy3 SAGE change discovery self-test: PASS"
        )
        return 0

    paths = changed_paths() if args.changed else []
    if not args.request and not paths:
        print("Provide --request TEXT or use --changed.")
        return 2

    initial = infer_context_ids(
        payload,
        args.request,
        paths,
    )
    always = set(payload.get("always_contexts", []))
    if initial == always:
        print(
            "Kalaxy3 SAGE change discovery: UNCLASSIFIED"
        )
        print(
            "Add a context mapping before implementation."
        )
        return 2

    selected = expand_dependencies(payload, initial)
    render_report(
        args.request,
        paths,
        ordered_contexts(payload, selected),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
