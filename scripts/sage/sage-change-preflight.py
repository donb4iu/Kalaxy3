#!/usr/bin/env python3
"""Discover SAGE authority and validation for a requested change."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Final, Sequence

from workflow import (
    CommandRunner,
    JsonlEventLogger,
    PrimitiveCatalog,
    ValidationCommand,
    ValidationPlan,
)


ROOT: Final = Path(__file__).resolve().parents[2]
DEFAULT_MAP: Final = ROOT / "sage-change-authority.json"


def normalize(value: str) -> str:
    """Normalize text for deterministic matching."""
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


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



VALIDATION_PRIMITIVES: Final = (
    "logging.events",
    "validation.plan",
)
SAFE_MAKE_TARGET: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
SHELL_CONTROL_TOKENS: Final = frozenset({
    ";", "&&", "||", "|", ">", ">>", "<", "<<", "&",
})


def parse_repository_validation_command(command: str) -> tuple[str, ...]:
    """Parse one repository-owned validation command without shell semantics."""

    if not isinstance(command, str) or not command.strip():
        raise ValueError("validation command must be a non-empty string")
    argv = tuple(shlex.split(command, posix=True))
    if not argv or any(token in SHELL_CONTROL_TOKENS for token in argv):
        raise ValueError(f"validation command contains unsupported shell syntax: {command!r}")
    if argv[0] == "make":
        if len(argv) != 2 or SAFE_MAKE_TARGET.fullmatch(argv[1]) is None:
            raise ValueError(f"validation make command is not a single target: {command!r}")
        return argv
    if argv[0] == "python3":
        if len(argv) < 2:
            raise ValueError(f"validation python command lacks a script path: {command!r}")
        script = Path(argv[1])
        if (
            script.is_absolute()
            or ".." in script.parts
            or "." in script.parts
            or not script.parts
            or script.parts[0] != "scripts"
            or script.suffix != ".py"
        ):
            raise ValueError(f"validation python script is not repository-scoped: {command!r}")
        return argv
    raise ValueError(
        f"validation command executable is unsupported: {argv[0]!r}"
    )


def context_validation_entries(
    contexts: Sequence[dict[str, Any]],
    field: str,
) -> list[tuple[str, Path, str, tuple[str, ...]]]:
    """Return deduplicated context-owned validation commands and working directories."""

    if field not in {"baseline_checks", "required_validation"}:
        raise ValueError(f"unsupported validation field: {field}")
    entries: list[tuple[str, Path, str, tuple[str, ...]]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for context in contexts:
        context_id = str(context["id"])
        working_directory = str(context["working_directory"])
        cwd = (ROOT / working_directory).resolve()
        try:
            cwd.relative_to(ROOT)
        except ValueError as error:
            raise ValueError(
                f"{context_id}: validation working directory escapes repository"
            ) from error
        if not cwd.is_dir():
            raise ValueError(
                f"{context_id}: validation working directory is missing: {working_directory}"
            )
        for command in context[field]:
            command_text = str(command)
            argv = parse_repository_validation_command(command_text)
            if argv[0] == "python3" and not (cwd / argv[1]).is_file():
                raise ValueError(
                    f"{context_id}: validation script is missing from working directory: {argv[1]}"
                )
            key = (str(cwd), argv)
            if key in seen:
                continue
            seen.add(key)
            entries.append((context_id, cwd, command_text, argv))
    return entries


def run_context_validation(
    contexts: Sequence[dict[str, Any]],
    field: str,
) -> Path:
    """Run one repository-owned context validation phase through validation.plan."""

    entries = context_validation_entries(contexts, field)
    if not entries:
        raise ValueError(f"{field} produced no validation commands")
    state_dir = (
        Path("~/.local/state/kalaxy3/sage-context-validation").expanduser()
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(ROOT / "sage-workflow-primitives.json")
    catalog.require(VALIDATION_PRIMITIVES)
    event_log = state_dir / "events.jsonl"
    logger = JsonlEventLogger(
        event_log,
        "sage.context-validation",
        primitive_versions=catalog.versions_for(VALIDATION_PRIMITIVES),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(ROOT, state_dir),
    )
    phase = "baseline" if field == "baseline_checks" else "required"
    for context_id, cwd, command_text, argv in entries:
        ValidationPlan(
            cwd,
            runner,
            (
                ValidationCommand(
                    f"{phase} validation [{context_id}]: {command_text}",
                    argv,
                    3600.0,
                ),
            ),
        ).run()
    print(
        f"Kalaxy3 SAGE context {phase} validation: PASS "
        f"({len(entries)} commands)"
    )
    print(f"Context validation event log: {event_log}")
    return event_log



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
        (
            "Activate the complete Kalaxy3 SAGE mandatory operating "
            "contract with repository-owned components, composition "
            "manifests, capability-gap receipts, failure diagnosis "
            "including what should have been done, measurable outcome "
            "and safety statistics, Git safety, and an "
            "operator-executed Git mutation gate"
        ): {
            "workflow-primitives",
            "continuous-improvement",
            "repository-governance",
            "evidence",
        },
        "Create a causal fact graph with immutable predecessor links and derived readiness projections": {
            "causal-evidence",
            "workflow-primitives",
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


    vocabulary_equivalence_cases = (
        (
            "repair request execution safety composition",
            "repair request-execution safety composition",
        ),
        (
            "continue checkpoint promotion workflow",
            "continue checkpoint-promotion workflow",
        ),
    )
    for spaced_request, hyphenated_request in vocabulary_equivalence_cases:
        spaced_contexts = infer_for_request(payload, spaced_request)
        hyphenated_contexts = infer_for_request(
            payload,
            hyphenated_request,
        )
        if spaced_contexts != hyphenated_contexts:
            failures.append(
                f"{hyphenated_request!r} did not classify equivalently "
                f"to {spaced_request!r}"
            )
        if "workflow-primitives" not in hyphenated_contexts:
            failures.append(
                f"{hyphenated_request!r} did not infer workflow-primitives"
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
        "SAGE discovery normalization paths": (
            [
                "scripts/sage/sage-change-preflight.py",
                "scripts/sage/sage-change-discovery-guardrail.py",
            ],
            {
                "workflow-primitives",
                "repository-governance",
                "evidence",
            },
        ),
        "request-planning entrypoint path": (
            ["scripts/sage/sage-request-plan.py"],
            {
                "workflow-primitives",
                "repository-governance",
                "evidence",
                "continuous-improvement",
            },
        ),
        "causal-evidence discovery paths": (
            [
                "scripts/sage/causal_evidence.py",
                "scripts/sage/sage-causal-evidence.py",
                "markdown/standards/sage-causal-evidence-fact-schema-v1.0.json",
                "markdown/standards/kalaxy3-sage-causal-evidence-process.md",
            ],
            {
                "causal-evidence",
                "workflow-primitives",
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

    for context in payload["contexts"]:
        for field in ("baseline_checks", "required_validation"):
            for command in context[field]:
                try:
                    parse_repository_validation_command(str(command))
                except ValueError as error:
                    failures.append(
                        f"{context['id']} {field} command is not shell-free repository validation: {error}"
                    )

    unsafe_commands = (
        "sh -c 'echo unsafe'",
        "make sage-index-check && echo unsafe",
        "python3 ../outside.py",
    )
    for command in unsafe_commands:
        try:
            parse_repository_validation_command(command)
        except ValueError:
            pass
        else:
            failures.append(
                f"unsafe validation command was accepted: {command!r}"
            )

    return failures


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Infer repository-owned SAGE authority"
    )
    parser.add_argument("--request", default="")
    parser.add_argument("--changed", action="store_true")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--run-baseline-validation", action="store_true")
    parser.add_argument("--run-required-validation", action="store_true")
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

    if args.changed and args.path:
        print("Use either --changed or explicit --path values, not both.")
        return 2
    if args.run_baseline_validation and args.run_required_validation:
        print("Choose only one context validation phase.")
        return 2
    if (args.run_baseline_validation or args.run_required_validation) and not (args.changed or args.path):
        print("Context validation requires --changed or at least one --path.")
        return 2
    paths = changed_paths() if args.changed else list(dict.fromkeys(args.path))
    if not args.request and not paths:
        print("Provide --request TEXT, --path PATH, or use --changed.")
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
    contexts = ordered_contexts(payload, selected)
    render_report(
        args.request,
        paths,
        contexts,
    )
    try:
        if args.run_baseline_validation:
            run_context_validation(contexts, "baseline_checks")
        elif args.run_required_validation:
            run_context_validation(contexts, "required_validation")
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Kalaxy3 SAGE context validation: FAIL CLOSED\n  - {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
