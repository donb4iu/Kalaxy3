#!/usr/bin/env python3
# Guard the repository-owned SAGE active-session contract.

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[2]
POLICY_PATH: Final = ROOT / "sage-continuous-improvement-policy.json"
AUTHORITY_PATH: Final = ROOT / "sage-change-authority.json"
REGISTRY_PATH: Final = ROOT / "sage-active-session-registry.json"
SCHEMA_PATH: Final = (
    ROOT
    / "markdown/standards/sage-active-session-schema-v1.0.json"
)
TOOL_PATH: Final = ROOT / "scripts/sage/sage-active-session.py"
GITIGNORE_PATH: Final = ROOT / ".gitignore"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_tool() -> Any:
    specification = importlib.util.spec_from_file_location(
        "sage_active_session",
        TOOL_PATH,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load active-session tool")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def validate_policy(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["policy must be an object"]
    if (
        payload.get("registries", {}).get("active_sessions")
        != "sage-active-session-registry.json"
    ):
        failures.append("active-session registry path changed")
    if (
        payload.get("contracts", {}).get("active_session_schema")
        != (
            "markdown/standards/"
            "sage-active-session-schema-v1.0.json"
        )
    ):
        failures.append("active-session schema path changed")
    if (
        payload.get("active_session_path")
        != "scripts/sage/sage-active-session.py"
    ):
        failures.append("active-session tool path changed")
    if (
        payload.get("active_session_guardrail_path")
        != "scripts/sage/sage-active-session-guardrail.py"
    ):
        failures.append("active-session guardrail path changed")
    if (
        payload.get("live_session_measurement_policy", {}).get(
            "composite_score_enabled"
        )
        is not False
    ):
        failures.append("active-session composite scoring opened")
    return failures


def validate_schema(payload: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(payload, dict):
        return ["active-session schema must be an object"]
    if payload.get("$id") != (
        "https://kalaxy3.local/"
        "sage-active-session-schema-v1.0.json"
    ):
        failures.append("active-session schema ID changed")
    if set(payload.get("$defs", {})) != {
        "command_event",
        "note_event",
    }:
        failures.append("active-session event definitions changed")
    command_properties = payload.get("$defs", {}).get(
        "command_event",
        {},
    ).get("properties", {})
    if "command" in command_properties or "command_text" in command_properties:
        failures.append("raw command field added to event schema")
    required_known_failure_fields = {
        "known_failure_encountered",
        "known_failure_recurred",
    }
    if not required_known_failure_fields.issubset(
        set(command_properties)
    ):
        failures.append("known-failure event fields are incomplete")
    return failures


def validate_authority(payload: Any) -> list[str]:
    contexts = payload.get("contexts", []) if isinstance(payload, dict) else []
    matches = [
        item
        for item in contexts
        if isinstance(item, dict)
        and item.get("id") == "continuous-improvement"
    ]
    if len(matches) != 1:
        return ["continuous-improvement authority missing"]
    context = matches[0]
    failures: list[str] = []
    required_files = {
        "sage-active-session-registry.json",
        "markdown/standards/sage-active-session-schema-v1.0.json",
        "scripts/sage/sage-active-session.py",
        "scripts/sage/sage-active-session-guardrail.py",
    }
    if not required_files.issubset(
        set(context.get("authoritative_files", []))
    ):
        failures.append("active-session authorities are incomplete")
    required_prefixes = {
        "sage-active-session-",
        "markdown/standards/sage-active-session-",
        "scripts/sage/sage-active-session",
    }
    if not required_prefixes.issubset(
        set(context.get("path_prefixes", []))
    ):
        failures.append(
            "active-session path classification is incomplete"
        )
    return failures


def mutation_tests(tool: Any) -> list[str]:
    failures: list[str] = []
    registry = load_json(REGISTRY_PATH)
    session = {
        "schema_version": "1.0",
        "session_id": "SAGE-SESSION-20260729-999",
        "change_id": "SAGE-CHANGE-20260729-999",
        "status": "active",
        "branch": "feature/self-test",
        "baseline_commit": "a" * 40,
        "started_at": "2026-07-29T21:00:00-05:00",
        "measurement_boundary": {
            "included_from": "self-test",
            "excluded_prior_commands": [],
            "reason": "self-test",
        },
        "prediction_versions": [1],
        "runtime_ledger": (
            ".sage/active-sessions/"
            "SAGE-SESSION-20260729-999/events.jsonl"
        ),
        "command_storage_policy": "label-and-digest-only",
        "deployment_gate": "closed",
    }
    duplicate = copy.deepcopy(registry)
    duplicate["sessions"] = [session, copy.deepcopy(session)]
    if not tool.validate_registry(duplicate):
        failures.append("duplicate sessions were accepted")

    opened = copy.deepcopy(registry)
    opened["sessions"] = [copy.deepcopy(session)]
    opened["sessions"][0]["deployment_gate"] = "open"
    if not tool.validate_registry(opened):
        failures.append("open deployment gate was accepted")
    return failures


def main() -> int:
    failures: list[str] = []
    try:
        tool = load_tool()
        failures.extend(validate_policy(load_json(POLICY_PATH)))
        failures.extend(validate_schema(load_json(SCHEMA_PATH)))
        failures.extend(validate_authority(load_json(AUTHORITY_PATH)))
        failures.extend(
            tool.validate_registry(load_json(REGISTRY_PATH))
        )
        failures.extend(mutation_tests(tool))
        if ".sage/active-sessions/" not in (
            GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        ):
            failures.append("runtime ledger path is not ignored")
        result = subprocess.run(
            [sys.executable, str(TOOL_PATH), "--self-test"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append("active-session tool self-test failed")
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
    ) as error:
        failures.append(str(error))

    if failures:
        print("Kalaxy3 SAGE active-session guardrail: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("PASS canonical active-session policy references")
    print("PASS active-session and event schema contract")
    print("PASS valid active-session registry")
    print("PASS authority and path classification")
    print("PASS local runtime ledger exclusion")
    print("PASS duplicate and open-gate mutation negatives")
    print("PASS repository-owned recorder self-test")
    print("Kalaxy3 SAGE active-session guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
