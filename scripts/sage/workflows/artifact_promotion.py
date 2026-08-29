"""Immutable OCI artifact promotion with environment binding and executor qualification."""

from __future__ import annotations

import hashlib
import json
import platform
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from workflow import AtomicFileWriter, CommandRunner, CommandSpec, JsonlEventLogger, PrimitiveCatalog, WorkflowError
from workflow.oci import inspect_oci_archive, parse_index_payload, platform_inventory, sha256_file

WORKFLOW_ID = "sage.artifact-promotion"
PRIMITIVES_USED = ("catalog.registry", "logging.events", "command.run", "file.atomic-preserve-mode")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_REPOSITORY = re.compile(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)+$")


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise WorkflowError(f"{label} is missing: {resolved}")
    try:
        value = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WorkflowError(f"{label} is not valid JSON") from error
    if not isinstance(value, Mapping):
        raise WorkflowError(f"{label} must be a JSON object")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError(f"{label} must be a non-empty string")
    return value.strip()


def validate_stage_receipt(path: Path) -> Mapping[str, Any]:
    receipt = _load_json(path, "portable-stage receipt")
    if receipt.get("schema_version") != "1.0" or receipt.get("record_type") != "sage-portable-stage-receipt":
        raise WorkflowError("portable-stage receipt version/type is invalid")
    source = receipt.get("source")
    artifact = receipt.get("artifact")
    build = receipt.get("build_contract")
    if not isinstance(source, Mapping) or not isinstance(artifact, Mapping) or not isinstance(build, Mapping):
        raise WorkflowError("portable-stage receipt structure is incomplete")
    source_sha = _string(source.get("git_sha"), "stage source SHA")
    if not _SHA.fullmatch(source_sha):
        raise WorkflowError("stage source SHA is invalid")
    index_digest = _string(artifact.get("index_digest"), "stage OCI index digest")
    if not _DIGEST.fullmatch(index_digest):
        raise WorkflowError("stage OCI index digest is invalid")
    archive_sha = _string(artifact.get("archive_sha256"), "stage OCI archive SHA-256")
    if not re.fullmatch(r"[0-9a-f]{64}", archive_sha):
        raise WorkflowError("stage OCI archive SHA-256 is invalid")
    if build.get("production_rebuild_permitted") is not False or build.get("external_registry_credentials_used") is not False:
        raise WorkflowError("stage receipt does not preserve the source-stage trust boundary")
    return receipt


def validate_environment_manifest(path: Path) -> Mapping[str, Any]:
    value = _load_json(path, "promotion environment manifest")
    expected_top = {"schema_version", "record_type", "environment_id", "artifact_target", "deployment_binding", "executor_contract", "authority"}
    if set(value) != expected_top or value.get("schema_version") != "1.0" or value.get("record_type") != "sage-promotion-environment-manifest":
        raise WorkflowError("promotion environment manifest version/type/fields are invalid")
    target = value.get("artifact_target")
    binding = value.get("deployment_binding")
    executor = value.get("executor_contract")
    authority = value.get("authority")
    if not all(isinstance(item, Mapping) for item in (target, binding, executor, authority)):
        raise WorkflowError("promotion environment manifest nested contracts are incomplete")
    repository = _string(target.get("repository"), "target repository")
    if not _REPOSITORY.fullmatch(repository) or ":" in repository or "@" in repository:
        raise WorkflowError("target repository must be an untagged registry/repository path")
    prefix = _string(target.get("publication_tag_prefix"), "publication tag prefix")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", prefix):
        raise WorkflowError("publication tag prefix is invalid")
    if target.get("transport") != "docker":
        raise WorkflowError("promotion environment transport must be docker")
    if binding.get("kind") != "ansible-kubernetes-image" or binding.get("receipt_variable") != "sage_promotion_receipt_file":
        raise WorkflowError("deployment binding contract is unsupported")
    expected_executor_fields = {"required_capabilities", "identity_is_provenance_only"}
    if set(executor) != expected_executor_fields:
        raise WorkflowError(
            "executor contract must declare required capabilities and provenance semantics only"
        )
    required_capabilities = set(executor.get("required_capabilities", []))
    if required_capabilities != {"oci-archive-source", "copy-all", "preserve-digests", "raw-inspect"}:
        raise WorkflowError("executor contract does not require the exact promotion capabilities")
    if executor.get("identity_is_provenance_only") is not True:
        raise WorkflowError("executor identity must be provenance only")
    if authority != {"registry_credentials": "executor-runtime-only", "secrets_in_manifest": False, "secrets_in_command_arguments": False}:
        raise WorkflowError("promotion authority contract permits secret coupling")
    return value


def validate_promotion_inputs(stage_receipt_path: Path, archive_path: Path, environment_path: Path) -> dict[str, Any]:
    receipt = validate_stage_receipt(stage_receipt_path)
    environment = validate_environment_manifest(environment_path)
    artifact = receipt["artifact"]
    identity = inspect_oci_archive(archive_path, str(artifact["index_digest"]))
    if identity["archive_sha256"] != artifact["archive_sha256"]:
        raise WorkflowError("retrieved OCI archive SHA-256 does not match the proven stage receipt")
    expected_platforms = artifact.get("platforms")
    if expected_platforms != identity["platforms"]:
        raise WorkflowError("retrieved OCI platform digests do not match the proven stage receipt")
    source_sha = str(receipt["source"]["git_sha"])
    target = environment["artifact_target"]
    tag = str(target["publication_tag_prefix"]) + source_sha
    repository = str(target["repository"])
    return {
        "stage_receipt": receipt,
        "stage_receipt_sha256": sha256_file(stage_receipt_path.expanduser().resolve()),
        "environment": environment,
        "environment_sha256": sha256_file(environment_path.expanduser().resolve()),
        "archive_identity": identity,
        "publication_tag": tag,
        "target_tag_reference": f"{repository}:{tag}",
        "target_transport_reference": f"docker://{repository}:{tag}",
        "source_transport_reference": f"oci-archive:{archive_path.expanduser().resolve()}:{artifact['stage_tag']}",
    }


def build_runner(repo: Path, event_log: Path) -> tuple[CommandRunner, PrimitiveCatalog]:
    resolved_repo = repo.expanduser().resolve()
    catalog = PrimitiveCatalog.load(resolved_repo / "sage-workflow-primitives.json")
    versions = catalog.versions_for(PRIMITIVES_USED)
    logger = JsonlEventLogger(event_log.expanduser().resolve(), WORKFLOW_ID, primitive_versions=versions)
    runner = CommandRunner(logger, allowed_roots=(resolved_repo, Path.home(), Path("/tmp")))
    return runner, catalog


def qualify_executor(
    runner: CommandRunner,
    repo: Path,
    required_capabilities: set[str],
) -> dict[str, Any]:
    # Skopeo is the first implemented adapter, selected by implementation rather than environment semantics.
    tool = "skopeo"
    version = runner.run(
        CommandSpec("command.run", "Qualify OCI promotion adapter version", (tool, "--version"), repo)
    )
    if tool not in version.stdout.lower():
        raise WorkflowError("selected OCI promotion adapter did not identify itself")
    copy_help = runner.run(
        CommandSpec("command.run", "Qualify OCI copy capabilities", (tool, "copy", "--help"), repo)
    )
    for marker in ("--all", "--preserve-digests"):
        if marker not in copy_help.stdout + copy_help.stderr:
            raise WorkflowError(f"selected OCI promotion adapter lacks copy capability: {marker}")
    inspect_help = runner.run(
        CommandSpec("command.run", "Qualify raw target inspection", (tool, "inspect", "--help"), repo)
    )
    if "--raw" not in inspect_help.stdout + inspect_help.stderr:
        raise WorkflowError("selected OCI promotion adapter lacks raw-manifest inspection")
    capabilities = ["oci-archive-source", "copy-all", "preserve-digests", "raw-inspect"]
    if set(capabilities) != required_capabilities:
        raise WorkflowError("selected OCI promotion adapter does not satisfy required capabilities")
    return {
        "tool": tool,
        "version": version.stdout.strip(),
        "version_output_sha256": hashlib.sha256(version.stdout.encode("utf-8")).hexdigest(),
        "capabilities": capabilities,
    }


def prepare_promotion(*, repo: Path, stage_receipt: Path, archive: Path, environment: Path, event_log: Path, executor_id: str, workflow_engine: str) -> dict[str, Any]:
    inputs = validate_promotion_inputs(stage_receipt, archive, environment)
    runner, _ = build_runner(repo, event_log)
    required_capabilities = set(inputs["environment"]["executor_contract"]["required_capabilities"])
    qualification = qualify_executor(
        runner,
        repo.expanduser().resolve(),
        required_capabilities,
    )
    return {
        "schema_version": "1.0",
        "record_type": "sage-artifact-promotion-plan",
        "status": "ready",
        "stage": {
            "receipt_sha256": inputs["stage_receipt_sha256"],
            "source_git_sha": inputs["stage_receipt"]["source"]["git_sha"],
            "archive_sha256": inputs["archive_identity"]["archive_sha256"],
            "index_digest": inputs["archive_identity"]["index_digest"],
        },
        "environment": {"manifest_sha256": inputs["environment_sha256"], "environment_id": inputs["environment"]["environment_id"]},
        "target": {"tag_reference": inputs["target_tag_reference"], "expected_index_digest": inputs["archive_identity"]["index_digest"]},
        "executor": {"workflow_engine": workflow_engine, "executor_id": executor_id, "qualification": qualification, "identity_is_provenance_only": True},
        "mutation_performed": False,
    }


def execute_promotion(*, repo: Path, stage_receipt: Path, archive: Path, environment: Path, event_log: Path, output: Path, executor_id: str, workflow_engine: str) -> dict[str, Any]:
    inputs = validate_promotion_inputs(stage_receipt, archive, environment)
    runner, _ = build_runner(repo, event_log)
    required_capabilities = set(inputs["environment"]["executor_contract"]["required_capabilities"])
    qualification = qualify_executor(
        runner,
        repo.expanduser().resolve(),
        required_capabilities,
    )
    tool = str(qualification["tool"])
    state_dir = output.expanduser().resolve().parent
    state_dir.mkdir(parents=True, exist_ok=True)
    digest_file = state_dir / ".promotion-copy-digest.txt"
    digest_file.unlink(missing_ok=True)
    copy_argv = (
        tool, "copy", "--all", "--preserve-digests", "--digestfile", str(digest_file),
        inputs["source_transport_reference"], inputs["target_transport_reference"],
    )
    runner.run(CommandSpec("command.run", "Promote exact OCI content without rebuild", copy_argv, repo.expanduser().resolve(), timeout_seconds=1800.0))
    if not digest_file.is_file():
        raise WorkflowError("OCI copy did not emit destination digest evidence")
    copied_digest = digest_file.read_text(encoding="utf-8").strip()
    expected_digest = str(inputs["archive_identity"]["index_digest"])
    if copied_digest != expected_digest:
        raise WorkflowError("OCI copy destination digest differs from the proven stage digest")
    raw = runner.run(CommandSpec("command.run", "Independently inspect promoted OCI index", (tool, "inspect", "--raw", inputs["target_transport_reference"]), repo.expanduser().resolve()))
    raw_bytes = raw.stdout.encode("utf-8")
    observed_digest = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    if observed_digest != expected_digest:
        raise WorkflowError("independent target registry digest differs from the proven stage digest")
    target_index = parse_index_payload(raw_bytes, "promoted target OCI index")
    target_platforms, _ = platform_inventory(target_index)
    if target_platforms != inputs["archive_identity"]["platforms"]:
        raise WorkflowError("promoted target platform digests differ from the proven stage artifact")
    repository = str(inputs["environment"]["artifact_target"]["repository"])
    image_ref = f"{repository}@{expected_digest}"
    receipt = {
        "schema_version": "1.0",
        "record_type": "sage-artifact-promotion-receipt",
        "status": "pass",
        "stage": {
            "receipt_sha256": inputs["stage_receipt_sha256"],
            "source_git_sha": inputs["stage_receipt"]["source"]["git_sha"],
            "archive_sha256": inputs["archive_identity"]["archive_sha256"],
            "index_digest": expected_digest,
            "platforms": inputs["archive_identity"]["platforms"],
        },
        "environment": {"manifest_sha256": inputs["environment_sha256"], "environment_id": inputs["environment"]["environment_id"]},
        "target": {
            "transport": "docker", "repository": repository, "publication_tag": inputs["publication_tag"],
            "tag_reference": inputs["target_tag_reference"], "image_ref": image_ref,
            "index_digest": observed_digest, "platforms": target_platforms,
        },
        "executor": {
            "workflow_engine": workflow_engine, "executor_id": executor_id,
            "os": platform.system().lower() or "unknown", "architecture": platform.machine().lower() or "unknown",
            "tool": {"name": qualification["tool"], "version": qualification["version"], "version_output_sha256": qualification["version_output_sha256"]},
            "identity_is_provenance_only": True,
        },
        "evidence": {"event_log_sha256": sha256_file(event_log.expanduser().resolve())},
        "verification": {
            "archive_sha_match": True, "index_digest_match": True, "platform_digests_match": True,
            "copy_preserved_digests": True, "independent_target_raw_digest_match": True,
            "rebuild_performed": False, "secrets_in_command_arguments": False,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    writer = AtomicFileWriter((output.expanduser().resolve().parent,))
    writer.write_text(output.expanduser().resolve(), json.dumps(receipt, indent=2) + "\n", new_mode=0o600)
    digest_file.unlink(missing_ok=True)
    return receipt
