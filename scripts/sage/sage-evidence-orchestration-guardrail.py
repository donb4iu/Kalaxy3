\
#!/usr/bin/env python3
"""Protect Kalaxy3 automatic SAGE evidence orchestration."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Final


ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-evidence-policy.json"
ORCHESTRATOR_PATH: Final = (
    ROOT / "scripts/sage/sage-evidence-orchestrator.py"
)
REQUIRED_MARKERS: Final = {
    "AGENTS.md": "Automatic SAGE evidence generation",
    "SAGE.md": "sage-evidence-prepare",
    "Makefile": "sage-evidence-prepare:",
    "scripts/sage/README.md": "sage-evidence-orchestrator.py",
    (
        "markdown/standards/"
        "kalaxy3-sage-evidence-orchestration-process.md"
    ): "requester is not required",
}


def load_module() -> ModuleType:
    """Load the evidence orchestrator for direct testing."""
    spec = importlib.util.spec_from_file_location(
        "sage_evidence_orchestrator",
        ORCHESTRATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Unable to load evidence orchestrator"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_policy() -> dict[str, Any]:
    """Load the evidence-orchestration policy."""
    payload = json.loads(
        POLICY_PATH.read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise TypeError("Evidence policy must be an object")
    return payload


def validate_canonical_hash(
    policy: dict[str, Any],
) -> list[str]:
    """Verify the canonical request checksum."""
    path = ROOT / str(policy["canonical_request_path"])
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = str(policy["canonical_request_sha256"])
    if actual == expected:
        return []
    return ["Canonical generation request hash differs from policy"]


def validate_required_paths(
    policy: dict[str, Any],
) -> list[str]:
    """Verify all repository authority paths exist."""
    fields = (
        "canonical_request_path",
        "standard_path",
        "metadata_contract_path",
        "record_template_path",
        "manifest_template_path",
        "publication_process_path",
        "orchestration_process_path",
        "publisher_path",
        "indexer_path",
        "discovery_map_path",
    )
    failures: list[str] = []
    for field in fields:
        path = ROOT / str(policy[field])
        if not path.is_file():
            failures.append(
                f"Policy path does not exist: {field}={path}"
            )
    return failures


def validate_markers() -> list[str]:
    """Verify documentation and Make entry-point markers."""
    failures: list[str] = []
    for relative, marker in REQUIRED_MARKERS.items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Missing orchestration file: {relative}")
            continue
        if marker not in path.read_text(encoding="utf-8"):
            failures.append(
                f"{relative} lacks marker {marker!r}"
            )
    return failures


def validate_make_chain() -> list[str]:
    """Verify evidence guardrails are in the root SAGE chain."""
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    markers = (
        "sage-evidence-self-test",
        "sage-evidence-guardrail",
        "SAGE_EVIDENCE_ORCHESTRATOR",
        "SAGE_EVIDENCE_GUARDRAIL",
    )
    return [
        f"Root Makefile lacks {marker!r}"
        for marker in markers
        if marker not in text
    ]


def validate_authority_map() -> list[str]:
    """Verify evidence discovery points at orchestration authority."""
    payload = json.loads(
        (ROOT / "sage-change-authority.json").read_text(
            encoding="utf-8"
        )
    )
    contexts = {
        str(item["id"]): item
        for item in payload["contexts"]
    }
    evidence = contexts.get("evidence", {})
    required_files = {
        "sage-evidence-policy.json",
        "scripts/sage/sage-evidence-orchestrator.py",
        (
            "markdown/standards/"
            "kalaxy3-sage-evidence-orchestration-process.md"
        ),
    }
    actual_files = set(
        evidence.get("authoritative_files", [])
    )
    failures = [
        f"Evidence context omits authority file {value}"
        for value in sorted(required_files - actual_files)
    ]
    validation = set(
        evidence.get("required_validation", [])
    )
    for command in (
        "make sage-evidence-self-test",
        "make sage-evidence-guardrail",
    ):
        if command not in validation:
            failures.append(
                f"Evidence context omits validation {command}"
            )
    return failures


def mutation_cases(
    policy: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """Create malformed policy mutation cases."""
    cases: list[tuple[str, dict[str, Any]]] = []

    wrong_schema = copy.deepcopy(policy)
    wrong_schema["schema_version"] = "2.0"
    cases.append(("wrong schema", wrong_schema))

    weak_requirements = copy.deepcopy(policy)
    weak_requirements["minimum_quality_requirements"] = ["weak"]
    cases.append(("weakened requirements", weak_requirements))

    missing_examples = copy.deepcopy(policy)
    missing_examples["plain_language_examples"] = []
    cases.append(("missing plain-language cases", missing_examples))

    missing_field = copy.deepcopy(policy)
    missing_field.pop("publisher_path", None)
    cases.append(("missing publisher path", missing_field))
    return cases


def run_negative_tests(
    module: ModuleType,
    policy: dict[str, Any],
) -> list[str]:
    """Require malformed policies to fail validation."""
    failures: list[str] = []
    for label, candidate in mutation_cases(policy):
        if not module.validate_policy(candidate):
            failures.append(
                f"Negative test accepted {label}"
            )
    return failures


def main() -> int:
    """Run the evidence-orchestration guardrail."""
    try:
        module = load_module()
        policy = load_policy()
        failures = module.validate_policy(policy)
        failures.extend(validate_canonical_hash(policy))
        failures.extend(validate_required_paths(policy))
        failures.extend(validate_markers())
        failures.extend(validate_make_chain())
        failures.extend(validate_authority_map())
        failures.extend(run_negative_tests(module, policy))
        failures.extend(module.self_test())
    except (
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        failures = [str(error)]

    if failures:
        print(
            "Kalaxy3 SAGE evidence orchestration guardrail: "
            "FAIL CLOSED"
        )
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical evidence request integrity")
    print("PASS repository-owned evidence policy and authorities")
    print("PASS plain-language evidence request regression tests")
    print("PASS original requester language preservation")
    print("PASS root Make evidence-generation entry points")
    print("PASS evidence policy mutation negative tests")
    print(
        "Kalaxy3 SAGE evidence orchestration guardrail: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
