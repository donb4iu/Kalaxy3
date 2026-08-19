#!/usr/bin/env python3
"""Protect the repository-owned SAGE discovery path."""

from __future__ import annotations

import copy
import importlib.util
import os
import subprocess
from pathlib import Path
from types import ModuleType
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
PREFLIGHT_PATH: Final = (
    ROOT / "scripts/sage/sage-change-preflight.py"
)
REQUIRED_MARKERS: Final = {
    "AGENTS.md": "make sage-preflight",
    "SAGE.md": "make sage-guardrails",
    "README.md": "SAGE change discovery",
    "Makefile": "sage-preflight:",
    "scripts/sage/README.md": "sage-change-preflight.py",
    "scripts/sage/sage-change-preflight.py": '"--cached"',
    ".github/workflows/kalaxy3_build_publish.yml": (
        "sage-governance:"
    ),
}


def load_preflight_module() -> ModuleType:
    """Load the preflight implementation for testing."""
    spec = importlib.util.spec_from_file_location(
        "sage_change_preflight",
        PREFLIGHT_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Unable to load SAGE preflight module"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_required_files(
    module: ModuleType,
) -> list[str]:
    """Validate authority-map file references."""
    payload = module.load_authority_map(
        ROOT / "sage-change-authority.json"
    )
    failures = module.validate_authority_map(payload)
    for context in payload["contexts"]:
        for value in context["authoritative_files"]:
            if not (ROOT / value).exists():
                failures.append(
                    f"{context['id']}: "
                    f"authority file missing: {value}"
                )
        working_directory = (
            ROOT / context["working_directory"]
        )
        if not working_directory.is_dir():
            failures.append(
                f"{context['id']}: "
                "working directory missing"
            )
    return failures


def validate_entrypoint_markers() -> list[str]:
    """Require discovery references at entry points."""
    failures: list[str] = []
    for relative, marker in REQUIRED_MARKERS.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(
                f"Missing discovery entry point: {relative}"
            )
            continue
        text = path.read_text(encoding="utf-8")
        if marker not in text:
            failures.append(
                f"{relative} lacks discovery marker "
                f"{marker!r}"
            )
    workflow = (
        ROOT / ".github/workflows/kalaxy3_build_publish.yml"
    ).read_text(encoding="utf-8")
    for marker in (
        "pull_request:",
        "make sage-stage-guardrails",
        "portable-stage:",
        "if: github.event_name == 'push' && github.ref != 'refs/heads/main'",
        "doc:",
        "if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'",
    ):
        if marker not in workflow:
            failures.append(
                "GitHub workflow lacks enforcement marker "
                f"{marker!r}"
            )
    homelab_makefile = (
        ROOT / "infrastructure/k3s-homelab/Makefile"
    ).read_text(encoding="utf-8")
    for marker in (
        "sage-discovery-guardrail:",
        "source-guardrails: sage-discovery-guardrail",
    ):
        if marker not in homelab_makefile:
            failures.append(
                "Homelab Makefile lacks discovery marker "
                f"{marker!r}"
            )

    return failures


def validate_make_request_transport() -> list[str]:
    """Verify that Make preserves literal request text."""
    request = (
        'Add centralized logging for "$HOME" '
        "without expansion"
    )
    environment = dict(os.environ)
    environment["SAGE_REQUEST"] = request
    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            "sage-preflight",
        ],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    failures: list[str] = []
    expected = f"Request: {request}"
    if result.returncode != 0:
        failures.append(
            "Root Make request transport failed: "
            f"{result.stderr.strip()}"
        )
    elif expected not in result.stdout.splitlines():
        failures.append(
            "Root Make request transport altered literal text"
        )

    return failures


def mutation_cases(
    payload: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """Create malformed authority-map cases."""
    cases: list[tuple[str, dict[str, Any]]] = []

    wrong_schema = copy.deepcopy(payload)
    wrong_schema["schema_version"] = "2.0"
    cases.append(("wrong schema", wrong_schema))

    duplicate = copy.deepcopy(payload)
    duplicate["contexts"][1]["id"] = (
        duplicate["contexts"][0]["id"]
    )
    cases.append(("duplicate context", duplicate))
    unknown = copy.deepcopy(payload)
    unknown["contexts"][0]["requires"] = [
        "missing-context"
    ]
    cases.append(("unknown dependency", unknown))

    missing_required = copy.deepcopy(payload)
    del missing_required["contexts"][0]["match_terms"]
    cases.append(
        ("missing required context field", missing_required)
    )

    empty = copy.deepcopy(payload)
    empty["contexts"] = []
    cases.append(("empty contexts", empty))
    return cases


def run_negative_tests(
    module: ModuleType,
) -> list[str]:
    """Require malformed maps to fail validation."""
    payload = module.load_authority_map(
        ROOT / "sage-change-authority.json"
    )
    failures: list[str] = []

    for label, candidate in mutation_cases(payload):
        if not module.validate_authority_map(candidate):
            failures.append(
                f"Negative test accepted {label}"
            )
    return failures


def validate_request_vocabulary_normalization_mutation(
    module: ModuleType,
) -> list[str]:
    # Prove hyphen equivalence depends on the canonical normalizer.
    payload = module.load_authority_map(
        ROOT / "sage-change-authority.json"
    )
    original_normalize = module.normalize

    def legacy_normalize(value: str) -> str:
        return " ".join(value.lower().replace("_", " ").split())
    failures: list[str] = []
    module.normalize = legacy_normalize
    try:
        cases = (
            (
                "repair request execution safety composition",
                "repair request-execution safety composition",
            ),
            (
                "continue checkpoint promotion workflow",
                "continue checkpoint-promotion workflow",
            ),
        )
        for spaced_request, hyphenated_request in cases:
            spaced_contexts = module.infer_for_request(
                payload,
                spaced_request,
            )
            hyphenated_contexts = module.infer_for_request(
                payload,
                hyphenated_request,
            )
            if "workflow-primitives" not in spaced_contexts:
                failures.append(
                    f"Canonical authority missing for {spaced_request!r}"
                )
            if "workflow-primitives" in hyphenated_contexts:
                failures.append(
                    f"Legacy normalizer unexpectedly classified "
                    f"{hyphenated_request!r}"
                )
    finally:
        module.normalize = original_normalize
    return failures


def validate_request_planning_changed_path_mapping_mutation(
    module: ModuleType,
) -> list[str]:
    """Prove request-planning changed-path ownership depends on its explicit mapping."""
    payload = module.load_authority_map(
        ROOT / "sage-change-authority.json"
    )
    candidate = copy.deepcopy(payload)
    owners = [
        item for item in candidate["contexts"]
        if item.get("id") == "workflow-primitives"
    ]
    if len(owners) != 1:
        return ["workflow-primitives context is not uniquely defined"]
    prefixes = owners[0].get("path_prefixes", [])
    target = "scripts/sage/sage-request-plan.py"
    if target not in prefixes:
        return ["request-planning entrypoint mapping is absent before mutation"]
    owners[0]["path_prefixes"] = [
        value for value in prefixes if value != target
    ]
    initial = module.infer_context_ids(candidate, "", [target])
    always = set(candidate.get("always_contexts", []))
    if "workflow-primitives" in initial:
        return ["mutation-negative retained workflow-primitives after mapping removal"]
    if initial != always:
        return ["mutation-negative did not recreate always-context-only classification"]
    return []


def main() -> int:
    """Run the discovery-path guardrail."""
    try:
        module = load_preflight_module()
        failures = validate_required_files(module)
        failures.extend(validate_entrypoint_markers())
        failures.extend(validate_make_request_transport())
        failures.extend(run_negative_tests(module))
        failures.extend(
            validate_request_vocabulary_normalization_mutation(
                module
            )
        )
        failures.extend(
            validate_request_planning_changed_path_mapping_mutation(
                module
            )
        )
        failures.extend(
            module.run_self_tests(
                module.load_authority_map(
                    ROOT / "sage-change-authority.json"
                )
            )
        )
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
    ) as error:
        failures = [str(error)]
    if failures:
        print(
            "Kalaxy3 SAGE discovery guardrail: "
            "FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        "PASS repository-root SAGE discovery entry points"
    )
    print(
        "PASS machine-readable change-authority map"
    )
    print(
        "PASS authoritative file and directory references"
    )
    print(
        "PASS request and changed-path classification tests"
    )
    print(
        "PASS literal request transport through root Makefile"
    )
    print(
        "PASS authority-map mutation negative tests"
    )
    print("PASS request-vocabulary normalization mutation negatives")
    print("PASS request-planning changed-path mapping mutation negative")
    print("Kalaxy3 SAGE discovery guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
