#!/usr/bin/env python3
"""Render and validate self-contained Kalaxy3 SAGE failures."""

from __future__ import annotations

import argparse
import json
import re
import string
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

REQUIRED_ENTRY_KEYS: Final = {
    "attempted_action",
    "detected_state",
    "why_invalid",
    "likely_intended_outcome",
    "confirm_correct_approach",
    "allowed_actions",
    "prohibited_actions",
    "canonical_recovery",
    "integrity_requirements",
    "authoritative_paths",
    "repository_gap",
}
FAILURE_ID_PATTERN: Final = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")


class ActionableFailureError(RuntimeError):
    """Represent an invalid actionable-failure definition or rendering."""


@dataclass(frozen=True)
class RecoveryStep:
    """Describe one repository-owned recovery command."""

    working_directory: str
    command: str
    required_paths: tuple[str, ...]


@dataclass(frozen=True)
class ActionableFailure:
    """Contain the complete SAGE failure and recovery contract."""

    attempted_action: str
    detected_state: str
    why_invalid: str
    likely_intended_outcome: str
    confirm_correct_approach: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    canonical_recovery: tuple[RecoveryStep, ...]
    integrity_requirements: tuple[str, ...]
    authoritative_paths: tuple[str, ...]
    repository_gap: str


class StrictVariables(dict[str, str]):
    """Reject missing template variables during failure rendering."""

    def __missing__(self, key: str) -> str:
        """Raise for one missing template variable."""
        raise ActionableFailureError(
            f"Missing actionable-failure variable: {key}"
        )


def load_catalog(path: Path) -> dict[str, Any]:
    """Load the machine-readable actionable-failure catalog."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ActionableFailureError("Failure catalog root must be a mapping")
    failures = payload.get("failures")
    if not isinstance(failures, dict):
        raise ActionableFailureError("Failure catalog requires failures")
    return payload


def require_text(value: Any, field: str) -> str:
    """Return one required nonempty string."""
    if not isinstance(value, str) or not value.strip():
        raise ActionableFailureError(f"{field} must be a nonempty string")
    return value.strip()


def require_text_list(value: Any, field: str) -> tuple[str, ...]:
    """Return one required nonempty list of strings."""
    if not isinstance(value, list) or not value:
        raise ActionableFailureError(f"{field} must be a nonempty list")
    return tuple(
        require_text(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    )


def parse_recovery_steps(value: Any) -> tuple[RecoveryStep, ...]:
    """Parse repository-owned recovery steps."""
    if not isinstance(value, list) or not value:
        raise ActionableFailureError(
            "canonical_recovery must be a nonempty list"
        )
    steps: list[RecoveryStep] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ActionableFailureError(
                f"canonical_recovery[{index}] must be a mapping"
            )
        steps.append(
            RecoveryStep(
                working_directory=require_text(
                    item.get("working_directory"),
                    f"canonical_recovery[{index}].working_directory",
                ),
                command=require_text(
                    item.get("command"),
                    f"canonical_recovery[{index}].command",
                ),
                required_paths=require_text_list(
                    item.get("required_paths"),
                    f"canonical_recovery[{index}].required_paths",
                ),
            )
        )
    return tuple(steps)


def parse_entry(entry: Mapping[str, Any]) -> ActionableFailure:
    """Parse one catalog entry into the shared failure model."""
    missing = sorted(REQUIRED_ENTRY_KEYS - set(entry))
    if missing:
        raise ActionableFailureError(
            f"Failure entry is missing keys: {', '.join(missing)}"
        )
    return ActionableFailure(
        attempted_action=require_text(
            entry["attempted_action"], "attempted_action"
        ),
        detected_state=require_text(
            entry["detected_state"], "detected_state"
        ),
        why_invalid=require_text(entry["why_invalid"], "why_invalid"),
        likely_intended_outcome=require_text(
            entry["likely_intended_outcome"],
            "likely_intended_outcome",
        ),
        confirm_correct_approach=require_text_list(
            entry["confirm_correct_approach"],
            "confirm_correct_approach",
        ),
        allowed_actions=require_text_list(
            entry["allowed_actions"], "allowed_actions"
        ),
        prohibited_actions=require_text_list(
            entry["prohibited_actions"], "prohibited_actions"
        ),
        canonical_recovery=parse_recovery_steps(
            entry["canonical_recovery"]
        ),
        integrity_requirements=require_text_list(
            entry["integrity_requirements"],
            "integrity_requirements",
        ),
        authoritative_paths=require_text_list(
            entry["authoritative_paths"], "authoritative_paths"
        ),
        repository_gap=require_text(
            entry["repository_gap"], "repository_gap"
        ),
    )


def substitute_text(text: str, variables: Mapping[str, str]) -> str:
    """Substitute strict named variables into one string."""
    fields = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(text)
        if field_name
    }
    missing = sorted(fields - set(variables))
    if missing:
        raise ActionableFailureError(
            f"Missing rendering variables: {', '.join(missing)}"
        )
    return text.format_map(StrictVariables(variables))


def substitute_failure(
    failure: ActionableFailure,
    variables: Mapping[str, str],
) -> ActionableFailure:
    """Render all variable-bearing fields in one failure."""
    def render_many(values: Sequence[str]) -> tuple[str, ...]:
        return tuple(substitute_text(value, variables) for value in values)

    steps = tuple(
        RecoveryStep(
            working_directory=substitute_text(
                step.working_directory, variables
            ),
            command=substitute_text(step.command, variables),
            required_paths=render_many(step.required_paths),
        )
        for step in failure.canonical_recovery
    )
    return ActionableFailure(
        attempted_action=substitute_text(
            failure.attempted_action, variables
        ),
        detected_state=substitute_text(failure.detected_state, variables),
        why_invalid=substitute_text(failure.why_invalid, variables),
        likely_intended_outcome=substitute_text(
            failure.likely_intended_outcome, variables
        ),
        confirm_correct_approach=render_many(
            failure.confirm_correct_approach
        ),
        allowed_actions=render_many(failure.allowed_actions),
        prohibited_actions=render_many(failure.prohibited_actions),
        canonical_recovery=steps,
        integrity_requirements=render_many(
            failure.integrity_requirements
        ),
        authoritative_paths=render_many(
            failure.authoritative_paths
        ),
        repository_gap=substitute_text(
            failure.repository_gap, variables
        ),
    )


def bullets(values: Sequence[str]) -> str:
    """Render one indented bullet list."""
    return "\n".join(f"  - {value}" for value in values)


def recovery_lines(steps: Sequence[RecoveryStep]) -> str:
    """Render canonical recovery commands with locations."""
    lines: list[str] = []
    for step in steps:
        lines.append(f"  - cd {step.working_directory}")
        lines.append(f"    {step.command}")
    return "\n".join(lines)


def render_failure(failure: ActionableFailure) -> str:
    """Render a self-contained SAGE actionable failure."""
    confirmation = (
        (*failure.confirm_correct_approach,)
        + tuple(
            f"Authoritative path: {path}"
            for path in failure.authoritative_paths
        )
    )
    return (
        "SAGE ACTION BLOCKED\n\n"
        f"Attempted action:\n  {failure.attempted_action}\n\n"
        f"Detected state:\n  {failure.detected_state}\n\n"
        f"Why this is invalid:\n  {failure.why_invalid}\n\n"
        "Likely intended outcome:\n"
        f"  {failure.likely_intended_outcome}\n\n"
        f"Confirm the correct approach:\n{bullets(confirmation)}\n\n"
        f"Allowed actions:\n{bullets(failure.allowed_actions)}\n\n"
        f"Prohibited actions:\n{bullets(failure.prohibited_actions)}\n\n"
        f"Canonical recovery:\n{recovery_lines(failure.canonical_recovery)}"
        "\n\nSAGE integrity requirements:\n"
        f"{bullets(failure.integrity_requirements)}\n\n"
        f"Repository gap:\n  {failure.repository_gap}"
    )


def catalog_failure(
    catalog: Mapping[str, Any],
    failure_id: str,
    variables: Mapping[str, str],
) -> ActionableFailure:
    """Load and render one identified catalog failure."""
    failures = catalog.get("failures", {})
    if failure_id not in failures:
        raise ActionableFailureError(
            f"Unknown actionable-failure id: {failure_id}"
        )
    entry = failures[failure_id]
    if not isinstance(entry, dict):
        raise ActionableFailureError(
            f"Failure entry {failure_id} must be a mapping"
        )
    return substitute_failure(parse_entry(entry), variables)


def validate_catalog(catalog: Mapping[str, Any]) -> None:
    """Validate all identifiers and entries in one catalog."""
    failures = catalog.get("failures")
    if not isinstance(failures, dict) or not failures:
        raise ActionableFailureError("Catalog has no failures")
    for failure_id, entry in failures.items():
        if not FAILURE_ID_PATTERN.fullmatch(str(failure_id)):
            raise ActionableFailureError(
                f"Invalid actionable-failure id: {failure_id}"
            )
        if not isinstance(entry, dict):
            raise ActionableFailureError(
                f"Failure entry {failure_id} must be a mapping"
            )
        failure = parse_entry(entry)
        if "SAGE infers" not in failure.likely_intended_outcome:
            raise ActionableFailureError(
                f"{failure_id}: intended outcome must label the inference"
            )


def validator_runtime_failure(
    *,
    validator_id: str,
    attempted_action: str,
    command: Sequence[str],
    exit_code: int,
    error_summary: str,
    working_directory: str,
    recovery_command: str,
    authoritative_paths: Sequence[str],
    integrity_requirements: Sequence[str],
) -> ActionableFailure:
    """Build recovery guidance when a validator cannot complete."""
    authorities = tuple(authoritative_paths) or (
        "Run repository discovery to identify authoritative files.",
    )
    integrity = tuple(integrity_requirements) or (
        "Preserve the traceback and complete validator output.",
        "Exercise the validator's real runtime entry path.",
        "Rerun required SAGE guardrails before commit and push.",
    )
    return ActionableFailure(
        attempted_action=attempted_action,
        detected_state=(
            f"Validator {validator_id} failed before validation completed. "
            f"Command={' '.join(command)!r}; exit_code={exit_code}; "
            f"error={error_summary}"
        ),
        why_invalid=(
            "A validator runtime failure is not a valid result for the "
            "system it was intended to inspect."
        ),
        likely_intended_outcome=(
            "SAGE infers that the operator intended to obtain a "
            "trustworthy validation result."
        ),
        confirm_correct_approach=(
            "Exercise the validator's real import and execution path, "
            "not only syntax compilation.",
            "Verify the approved interpreter, dependencies, working "
            "directory, and repository entry point.",
        ),
        allowed_actions=(
            "Preserve the traceback and command output as evidence.",
            "Repair the validator or its approved runtime environment.",
            "Add the exact runtime failure as a regression test.",
        ),
        prohibited_actions=(
            "Do not report a pass.",
            "Do not treat py_compile as sufficient runtime validation.",
            "Do not suppress the exception or bypass repository tooling.",
        ),
        canonical_recovery=(
            RecoveryStep(
                working_directory=working_directory,
                command=recovery_command,
                required_paths=authorities,
            ),
        ),
        integrity_requirements=integrity,
        authoritative_paths=authorities,
        repository_gap=(
            "If the canonical repair does not restore the runtime path, "
            "record a systemic validator-bootstrap or dependency gap."
        ),
    )
def parse_variables(values: Sequence[str]) -> dict[str, str]:
    """Parse repeated NAME=VALUE command-line variables."""
    variables: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ActionableFailureError(
                f"Invalid --set value, expected NAME=VALUE: {value}"
            )
        name, item = value.split("=", 1)
        variables[require_text(name, "variable name")] = item
    return variables


def build_parser() -> argparse.ArgumentParser:
    """Build the actionable-failure command-line parser."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    render = subparsers.add_parser("render")
    render.add_argument("--catalog", type=Path, required=True)
    render.add_argument("--failure-id", required=True)
    render.add_argument("--set", action="append", default=[])
    validate = subparsers.add_parser("validate-catalog")
    validate.add_argument("--catalog", type=Path, required=True)
    return parser


def main() -> int:
    """Run the actionable-failure command-line interface."""
    arguments = build_parser().parse_args()
    try:
        catalog = load_catalog(arguments.catalog)
        validate_catalog(catalog)
        if arguments.command == "validate-catalog":
            print("Kalaxy3 actionable-failure catalog: PASS")
            return 0
        variables = parse_variables(arguments.set)
        failure = catalog_failure(
            catalog, arguments.failure_id, variables
        )
        print(render_failure(failure))
        return 0
    except (ActionableFailureError, OSError, json.JSONDecodeError) as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
