#!/usr/bin/env python3
"""Validate generated Python helper delivery through SAGE primitives."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SAGE_DIR = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    AtomicFileWriter,
    CommandRunner,
    GitSafetyGuardrail,
    JsonlEventLogger,
    PrimitiveCatalog,
    Step,
    ValidationCommand,
    ValidationPlan,
    Workflow,
    WorkflowError,
)

PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "validation.plan",
    "git.safety-guardrail",
    "file.atomic-preserve-mode",
    "workflow.composition",
)

ACTION_ID = "SAGE-ACTION-20260730-001"
VALID_DELIVERY_STATUSES = {"validated", "measured", "closed"}
FIXTURE_MARKER = ".sage-generated-helper-fixture.json"
SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


@dataclass(frozen=True)
class CompanionArtifact:
    """One validated helper companion artifact."""

    path: Path
    sha256: str


@dataclass(frozen=True)
class DeliveryContract:
    """Resolved generated-helper delivery contract."""

    helper: Path
    manifest: Path
    receipt: Path
    fixture: Path
    self_test_argv: tuple[str, ...]
    operator_argv: tuple[str, ...]
    companions: tuple[CompanionArtifact, ...]
    helper_sha256: str
    manifest_sha256: str


@dataclass
class DeliveryExecution:
    """Mutable execution state for the thin workflow."""

    contract: DeliveryContract
    results: tuple[Any, ...] = ()


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_object(path: Path) -> dict[str, Any]:
    """Read one JSON object or fail closed."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise WorkflowError(f"{path}: expected a JSON object")
    return payload


def require_outside_repository(path: Path, label: str) -> Path:
    """Resolve one delivery path outside the live repository."""

    resolved = path.expanduser().resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise WorkflowError(f"{label} must be outside the live repository")
    return resolved


def require_unused_output(path: Path, label: str) -> Path:
    """Reject stale output paths before validation starts."""

    resolved = require_outside_repository(path, label)
    if resolved.exists():
        raise WorkflowError(f"{label} already exists: {resolved}")
    return resolved


def require_action_validated() -> str:
    """Require the improvement action to authorize real delivery."""

    payload = read_object(ROOT / "sage-improvement-actions.json")
    matches = [
        item
        for item in payload.get("actions", [])
        if isinstance(item, dict) and item.get("action_id") == ACTION_ID
    ]
    if len(matches) != 1:
        raise WorkflowError(f"Expected exactly one action {ACTION_ID}")
    status = str(matches[0].get("current_status", ""))
    if status not in VALID_DELIVERY_STATUSES:
        raise WorkflowError(
            f"{ACTION_ID} must be validated before delivery; status={status}"
        )
    return status


def render_argument(value: object, helper: Path, fixture: Path) -> str:
    """Render supported shell-free manifest placeholders."""

    if not isinstance(value, str):
        raise WorkflowError("Command arguments must be strings")
    return (
        value.replace("{python}", sys.executable)
        .replace("{helper}", str(helper))
        .replace("{fixture}", str(fixture))
    )


def resolve_command(
    payload: Mapping[str, Any],
    key: str,
    helper: Path,
    fixture: Path,
) -> tuple[str, ...]:
    """Resolve one declared argv-only helper command."""

    raw = payload.get(key)
    if not isinstance(raw, list) or not raw:
        raise WorkflowError(f"manifest.{key} must be a non-empty array")
    argv = tuple(render_argument(item, helper, fixture) for item in raw)
    if str(helper) not in argv:
        raise WorkflowError(f"manifest.{key} must execute the exact helper")
    return argv


def resolve_fixture(payload: Mapping[str, Any]) -> Path:
    """Validate the explicitly disposable runtime fixture."""

    raw = payload.get("runtime_fixture")
    if not isinstance(raw, str) or not raw:
        raise WorkflowError("manifest.runtime_fixture is required")
    fixture = require_outside_repository(Path(raw), "runtime fixture")
    if not fixture.is_dir():
        raise WorkflowError(f"Runtime fixture is not a directory: {fixture}")
    marker = read_object(fixture / FIXTURE_MARKER)
    if marker.get("disposable") is not True:
        raise WorkflowError("Runtime fixture must declare disposable=true")
    return fixture


def resolve_companions(
    payload: Mapping[str, Any],
) -> tuple[CompanionArtifact, ...]:
    """Validate every declared companion path and digest."""

    raw = payload.get("companion_artifacts", [])
    if not isinstance(raw, list):
        raise WorkflowError("manifest.companion_artifacts must be an array")
    companions: list[CompanionArtifact] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise WorkflowError(f"companion_artifacts[{index}] must be an object")
        path = require_outside_repository(
            Path(str(item.get("path", ""))),
            f"companion artifact {index}",
        )
        expected = item.get("sha256")
        if not path.is_file():
            raise WorkflowError(f"Companion artifact is missing: {path}")
        if not isinstance(expected, str) or len(expected) != 64:
            raise WorkflowError(f"Companion digest is invalid: {path}")
        observed = file_sha256(path)
        if observed != expected:
            raise WorkflowError(f"Companion digest mismatch: {path}")
        companions.append(CompanionArtifact(path, observed))
    return tuple(companions)


def load_contract(
    helper_path: Path,
    manifest_path: Path,
    receipt_path: Path,
) -> DeliveryContract:
    """Resolve and validate the complete delivery manifest."""

    helper = require_outside_repository(helper_path, "helper")
    manifest = require_outside_repository(manifest_path, "manifest")
    receipt = require_unused_output(receipt_path, "receipt")
    if not helper.is_file() or not manifest.is_file():
        raise WorkflowError("Helper and manifest must both exist")
    payload = read_object(manifest)
    if payload.get("schema_version") != "1.0":
        raise WorkflowError("Manifest schema_version must be 1.0")
    helper_digest = file_sha256(helper)
    if payload.get("helper_sha256") != helper_digest:
        raise WorkflowError("Manifest helper_sha256 does not match helper")
    fixture = resolve_fixture(payload)
    companions = resolve_companions(payload)
    self_test = resolve_command(payload, "self_test_argv", helper, fixture)
    operator = resolve_command(payload, "operator_argv", helper, fixture)
    validate_command_semantics(self_test, operator, companions)
    return DeliveryContract(
        helper=helper,
        manifest=manifest,
        receipt=receipt,
        fixture=fixture,
        self_test_argv=self_test,
        operator_argv=operator,
        companions=companions,
        helper_sha256=helper_digest,
        manifest_sha256=file_sha256(manifest),
    )


def validate_command_semantics(
    self_test: tuple[str, ...],
    operator: tuple[str, ...],
    companions: tuple[CompanionArtifact, ...],
) -> None:
    """Require distinct self-test and exact operator paths."""

    if "--self-test" not in self_test:
        raise WorkflowError("self_test_argv must include --self-test")
    if "--self-test" in operator:
        raise WorkflowError("operator_argv must exercise the non-self-test path")
    operator_paths = {Path(value).expanduser().resolve() for value in operator}
    omitted = [str(item.path) for item in companions if item.path not in operator_paths]
    if omitted:
        raise WorkflowError(f"operator_argv omits companions: {omitted}")


def validate_helper_safety(execution: DeliveryExecution) -> dict[str, object]:
    """Reject Git, GitHub, credential, or deployment mutation capability."""

    violations = GitSafetyGuardrail.scan_paths((execution.contract.helper,))
    if violations:
        rendered = "; ".join(item.render() for item in violations)
        raise WorkflowError(rendered)
    return {"status": "pass", "violations": 0}


def validation_commands(contract: DeliveryContract) -> tuple[ValidationCommand, ...]:
    """Build the exact ordered source and runtime validation plan."""

    pyc = contract.fixture / ".sage-generated-helper.pyc"
    compile_code = (
        "import py_compile,sys;"
        "py_compile.compile(sys.argv[1],cfile=sys.argv[2],doraise=True)"
    )
    return (
        ValidationCommand(
            "Compile exact generated helper",
            (sys.executable, "-c", compile_code, str(contract.helper), str(pyc)),
        ),
        ValidationCommand(
            "Run repository undefined-global guardrail",
            (
                sys.executable,
                "scripts/sage/sage-python-static-guardrail.py",
                str(contract.helper),
            ),
        ),
        ValidationCommand("Run declared helper self-test", contract.self_test_argv),
        ValidationCommand("Run exact non-self-test operator path", contract.operator_argv),
    )


def execute_runtime_plan(
    execution: DeliveryExecution,
    runner: CommandRunner,
) -> dict[str, object]:
    """Execute the exact source and runtime validation paths."""

    plan = ValidationPlan(ROOT, runner, validation_commands(execution.contract))
    execution.results = plan.run()
    return {
        "status": "pass",
        "checks": len(execution.results),
        "output_sha256": [item.output_sha256 for item in execution.results],
    }


def receipt_payload(
    execution: DeliveryExecution,
    event_log: Path,
    action_status: str,
) -> dict[str, object]:
    """Build the final machine-readable delivery receipt."""

    contract = execution.contract
    return {
        "schema_version": "1.0",
        "record_type": "sage-generated-helper-delivery-validation",
        "status": "pass",
        "action_id": ACTION_ID,
        "action_status": action_status,
        "helper": {"path": str(contract.helper), "sha256": contract.helper_sha256},
        "manifest": {"path": str(contract.manifest), "sha256": contract.manifest_sha256},
        "runtime_fixture": str(contract.fixture),
        "companion_artifacts": [
            {"path": str(item.path), "sha256": item.sha256}
            for item in contract.companions
        ],
        "commands": {
            "self_test": list(contract.self_test_argv),
            "operator": list(contract.operator_argv),
        },
        "validation": [
            {
                "returncode": item.returncode,
                "duration_ms": item.duration_ms,
                "output_sha256": item.output_sha256,
            }
            for item in execution.results
        ],
        "event_log": {"path": str(event_log), "sha256": file_sha256(event_log)},
    }


def write_receipt(
    execution: DeliveryExecution,
    event_log: Path,
    action_status: str,
) -> str:
    """Write the final receipt atomically after all validation passes."""

    payload = json.dumps(
        receipt_payload(execution, event_log, action_status),
        indent=2,
    ) + "\n"
    writer = AtomicFileWriter((execution.contract.receipt.parent,))
    return writer.write_text(execution.contract.receipt, payload)


def build_workflow(
    execution: DeliveryExecution,
    logger: JsonlEventLogger,
    catalog: PrimitiveCatalog,
    runner: CommandRunner,
) -> Workflow:
    """Build the thin generated-helper validation composition."""

    steps = (
        Step(
            "validate-helper-safety",
            "git.safety-guardrail",
            lambda: validate_helper_safety(execution),
        ),
        Step(
            "validate-source-and-runtime-paths",
            "validation.plan",
            lambda: execute_runtime_plan(execution, runner),
        ),
    )
    return Workflow(
        workflow_id="sage.generated-helper-delivery",
        logger=logger,
        catalog=catalog,
        steps=steps,
    )


def execute(helper: Path, manifest: Path, receipt: Path) -> dict[str, object]:
    """Validate one real helper delivery and write its final receipt."""

    action_status = require_action_validated()
    contract = load_contract(helper, manifest, receipt)
    event_log = require_unused_output(
        receipt.with_name(receipt.name + ".events.jsonl"),
        "event log",
    )
    catalog = PrimitiveCatalog.load(ROOT / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        event_log,
        "sage.generated-helper-delivery",
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(ROOT, contract.fixture, contract.helper.parent),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    execution = DeliveryExecution(contract)
    build_workflow(execution, logger, catalog, runner).run()
    receipt_digest = write_receipt(execution, event_log, action_status)
    return {
        "status": "pass",
        "receipt": str(contract.receipt),
        "receipt_sha256": receipt_digest,
        "event_log": str(event_log),
    }


def parse_args() -> argparse.Namespace:
    """Parse the production validation CLI."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--helper", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """Run one fail-closed generated-helper delivery validation."""

    args = parse_args()
    try:
        result = execute(args.helper, args.manifest, args.receipt)
    except (json.JSONDecodeError, OSError, TypeError, ValueError, WorkflowError) as error:
        print("Kalaxy3 generated-helper delivery: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    print("Kalaxy3 generated-helper delivery: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
