#!/usr/bin/env python3
"""Run a validator and convert runtime failures into SAGE recovery guidance."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    """Build the validator-runner command-line parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--validator-id", required=True)
    parser.add_argument("--attempted-action", required=True)
    parser.add_argument("--working-directory", default=".")
    parser.add_argument("--recovery-command", required=True)
    parser.add_argument("--authoritative-path", action="append", default=[])
    parser.add_argument("--integrity-requirement", action="append", default=[])
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def normalize_command(command: Sequence[str]) -> list[str]:
    """Normalize the validator command after an optional separator."""
    normalized = list(command)
    if normalized and normalized[0] == "--":
        normalized = normalized[1:]
    if not normalized:
        raise ValueError("A validator command is required after --")
    return normalized


def trim_failure(stdout: str, stderr: str) -> str:
    """Return a bounded validator failure summary."""
    combined = "\n".join(
        value.strip() for value in (stderr, stdout) if value.strip()
    )
    if not combined:
        return "The validator returned nonzero without diagnostic output."
    return combined[-3000:]


def render_fallback(
    *,
    validator_id: str,
    attempted_action: str,
    command: Sequence[str],
    exit_code: int,
    error_summary: str,
    working_directory: str,
    recovery_command: str,
    authoritative_paths: Sequence[str],
    framework_error: str,
) -> str:
    """Render dependency-free recovery if shared rendering also fails."""
    authority = "\n".join(
        f"  - {path}" for path in authoritative_paths
    ) or "  - Run repository discovery to identify authority."
    return (
        "SAGE ACTION BLOCKED\n\n"
        f"Attempted action:\n  {attempted_action}\n\n"
        "Detected state:\n"
        f"  Validator {validator_id} failed before validation completed.\n"
        f"  Command: {' '.join(command)}\n"
        f"  Exit code: {exit_code}\n"
        f"  Error: {error_summary}\n"
        f"  Shared framework error: {framework_error}\n\n"
        "Why this is invalid:\n"
        "  A validator failure is not a target-system validation result.\n\n"
        "Likely intended outcome:\n"
        "  SAGE infers that the operator intended a trustworthy result.\n\n"
        "Confirm the correct approach:\n"
        f"{authority}\n"
        "  - Exercise the validator's real runtime entry path.\n\n"
        "Allowed actions:\n"
        "  - Preserve the traceback and command output.\n"
        "  - Repair the validator or approved runtime environment.\n"
        "  - Add the exact failure as a regression test.\n\n"
        "Prohibited actions:\n"
        "  - Do not report a pass.\n"
        "  - Do not treat py_compile as sufficient runtime validation.\n"
        "  - Do not suppress the exception or bypass repository tooling.\n\n"
        "Canonical recovery:\n"
        f"  - cd {working_directory}\n"
        f"    {recovery_command}\n\n"
        "SAGE integrity requirements:\n"
        "  - Preserve failed and successful runtime evidence.\n"
        "  - Rerun required SAGE guardrails before commit.\n"
        "  - Commit and push a cohesive validated repair.\n\n"
        "Repository gap:\n"
        "  The shared failure framework also failed. Record a systemic "
        "validator-bootstrap gap if recovery does not restore execution."
    )


def render_shared(
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
) -> str:
    """Render validator failure through the shared SAGE framework."""
    from sage_actionable_failure import (
        render_failure,
        validator_runtime_failure,
    )

    failure = validator_runtime_failure(
        validator_id=validator_id,
        attempted_action=attempted_action,
        command=command,
        exit_code=exit_code,
        error_summary=error_summary,
        working_directory=working_directory,
        recovery_command=recovery_command,
        authoritative_paths=authoritative_paths,
        integrity_requirements=integrity_requirements,
    )
    return render_failure(failure)


def main() -> int:
    """Run the validator and convert runtime failure into SAGE guidance."""
    arguments = build_parser().parse_args()
    try:
        command = normalize_command(arguments.command)
    except ValueError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2

    working_directory = (ROOT / arguments.working_directory).resolve()
    result = subprocess.run(
        command,
        cwd=working_directory,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode == 0:
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        print(f"SAGE validator runtime: PASS ({arguments.validator_id})")
        return 0

    summary = trim_failure(result.stdout, result.stderr)
    try:
        message = render_shared(
            validator_id=arguments.validator_id,
            attempted_action=arguments.attempted_action,
            command=command,
            exit_code=result.returncode,
            error_summary=summary,
            working_directory=arguments.working_directory,
            recovery_command=arguments.recovery_command,
            authoritative_paths=arguments.authoritative_path,
            integrity_requirements=arguments.integrity_requirement,
        )
    except Exception as framework_error:  # noqa: BLE001
        message = render_fallback(
            validator_id=arguments.validator_id,
            attempted_action=arguments.attempted_action,
            command=command,
            exit_code=result.returncode,
            error_summary=summary,
            working_directory=arguments.working_directory,
            recovery_command=arguments.recovery_command,
            authoritative_paths=arguments.authoritative_path,
            framework_error=repr(framework_error),
        )
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
