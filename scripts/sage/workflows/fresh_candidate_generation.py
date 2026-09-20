#!/usr/bin/env python3
"""Generate the first governed engineering contribution through a fresh role."""

from __future__ import annotations

import hashlib
import json
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

from fresh_role_readiness import (
    ReadinessError,
    require_implementation_ready,
    validate_readiness_payload,
)
from llm_role_invocation import (
    RoleInvocationError,
    build_invocation,
    invoke_ollama_json,
    new_state_dir,
    persist_json,
    resolve_ollama_runtime,
    sha256_json,
    stable_json,
)
from sage_evidence_retrieval import retrieve as retrieve_evidence
from sage_evidence_retrieval import write_result as write_retrieval_result
from semantic_understanding import (
    EngineeringContribution,
    action_record_sha256,
    load_engineering_contribution,
    sha256_file,
)
from workflow import (
    CommandRunner,
    CommandSpec,
    JsonlEventLogger,
    PrimitiveCatalog,
    SageDiscovery,
    WorkflowError,
    load_improvement_action,
)
from workflows.intent_to_outcome import begin_intent

from workflow import AtomicFileWriter

PRIMITIVES_USED = (
    "file.atomic-preserve-mode",
)


WORKFLOW_ID = "sage.fresh-candidate-generation"
WORKFLOW_VERSION = "1.0.1"
ROLE = "fresh-isolated-implementation"
RUNTIME_BOUNDARY = "fresh-role-runtime-qualification"
ROLE_PROMPT_PATH = Path(
    "markdown/templates/sage-fresh-implementation-role-prompt.txt"
)
CONTRIBUTION_SCHEMA_PATH = Path(
    "markdown/standards/sage-engineering-contribution-schema-v1.0.json"
)
ARCHITECT_INTENT_RECORD = "architect-intent.json"
ISOLATION_FIELDS = (
    "inherited_architect_chat_history",
    "persistent_chat_hidden_state",
    "prior_role_chat_history",
    "predecessor_role_chat_history",
    "uncontrolled_filesystem_context",
)
ALLOWED_STRAWMAN_DISPOSITIONS = frozenset({"REUSE", "MODIFY", "REJECT"})
RESULT_FIELDS = {
    "schema_version",
    "record_type",
    "authority",
    "role",
    "context_sha256",
    "contribution",
    "payload",
}


class ProviderInvoker(Protocol):
    """Callable contract matching the repository provider invocation API."""

    def __call__(
        self,
        *,
        envelope: Mapping[str, Any],
        system_instruction: str,
        endpoint: str,
        model: str,
        timeout_seconds: int = 180,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Invoke one fresh JSON role through the configured provider."""


RuntimeResolver = Callable[[], tuple[str, str]]
LifecycleStarter = Callable[[Path, str, str, Path], Mapping[str, Any]]


def _persist_role_json(path: Path, value: Mapping[str, Any]) -> None:
    """Persist one local role artifact through the registered atomic-file primitive."""
    AtomicFileWriter((path.parent,)).write_text(
        path,
        stable_json(value),
        new_mode=0o600,
    )




def _runtime(repo: Path, state_dir: Path) -> CommandRunner:
    """Create the repository-owned command runtime for bounded discovery."""
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(("sage.discovery", "logging.events"))
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(("sage.discovery", "logging.events")),
    )
    return CommandRunner(logger, allowed_roots=(repo, state_dir))


def _discover(repo: Path, request: str, runner: CommandRunner) -> SageDiscovery:
    """Run one bounded repository-owned SAGE discovery pass."""
    result = runner.run(
        CommandSpec(
            primitive_id="sage.discovery",
            label="Discover first-candidate bounded context",
            argv=(
                "python3",
                "scripts/sage/sage-change-preflight.py",
                "--request",
                request,
            ),
            cwd=repo,
            environment={"SAGE_REQUEST": request},
        )
    )
    return SageDiscovery.parse(request, result.stdout)


def _authority_files(repo: Path, contexts: Sequence[str]) -> tuple[Path, ...]:
    """Resolve only files explicitly authorized by selected SAGE contexts."""
    authority_path = repo / "sage-change-authority.json"
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    selected = {str(value) for value in contexts}
    entries = [
        item
        for item in payload.get("contexts", [])
        if isinstance(item, Mapping) and str(item.get("id")) in selected
    ]
    declared = [
        str(path)
        for item in entries
        for path in item.get("authoritative_files", [])
    ]
    return _expand_declared_files(repo, declared)


def _expand_declared_files(repo: Path, declared: Sequence[str]) -> tuple[Path, ...]:
    """Expand repository-relative authoritative file or directory declarations."""
    files: set[Path] = set()
    for relative in declared:
        candidate = (repo / relative).resolve()
        try:
            candidate.relative_to(repo)
        except ValueError as error:
            raise WorkflowError(
                f"authoritative path escapes repository: {relative}"
            ) from error
        if candidate.is_dir():
            files.update(
                path.resolve()
                for path in candidate.rglob("*")
                if path.is_file()
            )
        elif candidate.is_file():
            files.add(candidate)
        else:
            raise WorkflowError(f"authoritative path is missing: {relative}")
    return tuple(sorted(files, key=lambda path: str(path.relative_to(repo))))


def _decode_utf8(payload: bytes, label: str) -> str:
    """Decode bounded source bytes for the text-only fresh-role contract."""
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise WorkflowError(f"fresh-role context is not UTF-8 text: {label}") from error


def _repository_file_records(
    repo: Path,
    paths: Sequence[Path],
) -> list[dict[str, str]]:
    """Describe and inline exact whitelisted repository bytes for the fresh role."""
    records: list[dict[str, str]] = []
    for path in paths:
        payload = path.read_bytes()
        records.append({
            "path": str(path.relative_to(repo)),
            "sha256": sha256_file(path),
            "source_class": "sage-selected-repository",
            "content": _decode_utf8(payload, str(path.relative_to(repo))),
        })
    return records


def _parse_provenance_text(text: str) -> dict[str, Any]:
    """Parse repository provenance supplied as JSON or line-oriented key/value text."""
    stripped = text.strip()
    if stripped.startswith("{"):
        payload = json.loads(stripped)
        if not isinstance(payload, dict):
            raise WorkflowError("strawman provenance JSON must be an object")
        return dict(payload)
    result: dict[str, Any] = {}
    for line in stripped.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value.lower() in {"true", "false"}:
            result[key] = value.lower() == "true"
        else:
            result[key] = value
    return result


def _load_strawman_provenance(path: Path, artifact: Path) -> dict[str, Any]:
    """Load and validate explicit non-authoritative persistent-LLM provenance."""
    payload = _parse_provenance_text(path.read_text(encoding="utf-8"))
    required = {
        "classification": "persistent-llm-strawman",
        "authority": "none",
        "lifecycle_status": "optional-prior-work-only",
    }
    for field, expected in required.items():
        if payload.get(field) != expected:
            raise WorkflowError(f"strawman provenance {field} must be {expected!r}")
    payload["artifact_sha256"] = sha256_file(artifact)
    payload["source_provenance_sha256"] = sha256_file(path)
    return payload


def _strawman_context(
    artifact: Path | None,
    provenance: Path | None,
) -> dict[str, Any] | None:
    """Inline optional strawman bytes as explicitly non-authoritative prior work."""
    if (artifact is None) != (provenance is None):
        raise WorkflowError(
            "strawman artifact and provenance must be supplied together"
        )
    if artifact is None or provenance is None:
        return None
    resolved = artifact.expanduser().resolve()
    source = provenance.expanduser().resolve()
    if not resolved.is_file() or not source.is_file():
        raise WorkflowError("strawman artifact or provenance is missing")
    metadata = _load_strawman_provenance(source, resolved)
    contribution = load_engineering_contribution(resolved)
    files = [_strawman_file(item) for item in contribution.source_files]
    return {
        "provenance": metadata,
        "artifact_sha256": contribution.package_sha256,
        "manifest": dict(contribution.manifest),
        "files": files,
    }


def _strawman_file(item: Any) -> dict[str, Any]:
    """Render one strawman contribution file as bounded text prior work."""
    return {
        "path": item.path,
        "mode": format(item.mode, "04o"),
        "sha256": item.sha256,
        "content": _decode_utf8(item.payload, item.path),
    }


def _selected_context(
    repo: Path,
    action: Mapping[str, Any],
    request: str,
    discovery: SageDiscovery,
    retrieval: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_sha256: str,
    strawman: Mapping[str, Any] | None,
    architect_intent_artifact_sha256: str,
) -> dict[str, Any]:
    """Build exact SAGE-selected context consumable by the real JSON runtime."""
    paths = _authority_files(repo, discovery.contexts)
    schema_path = repo / CONTRIBUTION_SCHEMA_PATH
    prompt_path = repo / ROLE_PROMPT_PATH
    return {
        "architect_intent": dict(action),
        "architect_intent_source": {
            "record_type": "architect_intent",
            "path": ARCHITECT_INTENT_RECORD,
            "artifact_sha256": architect_intent_artifact_sha256,
            "action_record_sha256": action_record_sha256(action),
            "source_class": "architect-owned-intent",
        },
        "action_record_sha256": action_record_sha256(action),
        "literal_request": request,
        "implementation_readiness": dict(readiness),
        "implementation_readiness_sha256": readiness_sha256,
        "contexts": list(discovery.contexts),
        "repository_files": _repository_file_records(repo, paths),
        "evidence_retrieval": dict(retrieval),
        "role_prompt_sha256": sha256_file(prompt_path),
        "contribution_schema_sha256": sha256_file(schema_path),
        "contribution_schema": json.loads(schema_path.read_text(encoding="utf-8")),
        "persistent_llm_strawman": None if strawman is None else dict(strawman),
        "source_classes": {
            "repository": "sage-selected-repository",
            "external": "current-external-engineering",
            "strawman": "persistent-llm-strawman",
        },
    }


def _prepare_context(
    repo: Path,
    action: Mapping[str, Any],
    request: str,
    state_dir: Path,
    readiness: Mapping[str, Any],
    readiness_sha256: str,
    strawman: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str, Path]:
    """Discover, retrieve, bind, and persist one fresh implementation context."""
    runner = _runtime(repo, state_dir)
    discovery = _discover(repo, request, runner)
    retrieval = retrieve_evidence(
        repo=repo,
        policy_path=repo / "sage-evidence-retrieval-policy.json",
        request=request,
    )
    retrieval_path = state_dir / "evidence-retrieval.json"
    write_retrieval_result(retrieval_path, retrieval)
    architect_intent_path = state_dir / ARCHITECT_INTENT_RECORD
    _persist_role_json(architect_intent_path, action)
    selected = _selected_context(
        repo,
        action,
        request,
        discovery,
        retrieval,
        readiness,
        readiness_sha256,
        strawman,
        sha256_file(architect_intent_path),
    )
    digest = sha256_json(selected)
    context = {"selected_context_sha256": digest, "selected_context": selected}
    context_path = state_dir / "fresh-role-context.json"
    _persist_role_json(context_path, context)
    return context, digest, context_path


def _invocation_request(strawman: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build the bounded first-candidate task and result contract."""
    return {
        "record_type": "llm_role_invocation",
        "task": "author-first-engineering-contribution",
        "output_record_type": "sage-fresh-implementation-result",
        "output_schema_version": "1.0",
        "payload_encoding": "utf-8-text",
        "required_strawman_dispositions": strawman is not None,
        "persistent_llm_fallback_allowed": False,
        "fresh_critic_required": True,
    }


def _runtime_blocker(objective_id: str, reason: str) -> dict[str, Any]:
    """Render missing or failed fresh inference as a governed non-mutation blocker."""
    return {
        "status": "capability-blocked",
        "objective_id": objective_id,
        "blocker_class": "fresh-role-inference-runtime",
        "reason": reason,
        "repository_mutation": False,
        "next_boundary": RUNTIME_BOUNDARY,
        "fresh_critic_required": True,
        "self_approved": False,
    }


def repository_fresh_role_invoker(
    envelope: Mapping[str, Any],
    system_instruction: str,
    runtime_resolver: RuntimeResolver,
    provider_invoker: ProviderInvoker,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    """Invoke the repository-owned fresh-role runtime and fail closed."""
    try:
        endpoint, model = runtime_resolver()
        result, receipt = provider_invoker(
            envelope=envelope,
            system_instruction=system_instruction,
            endpoint=endpoint,
            model=model,
        )
    except RoleInvocationError as error:
        return None, None, str(error)
    return result, receipt, None


def _validate_invocation_contract(envelope: Mapping[str, Any]) -> None:
    """Validate repository and semantic identities of one fresh invocation."""
    if envelope.get("record_type") != "sage-llm-role-invocation":
        raise WorkflowError("repository fresh-role invocation envelope is invalid")
    request = envelope.get("request")
    context = envelope.get("context")
    valid_request = (
        isinstance(request, Mapping)
        and request.get("record_type") == "llm_role_invocation"
    )
    if not valid_request:
        raise WorkflowError("first-candidate invocation semantic record is invalid")
    if not isinstance(context, Mapping):
        raise WorkflowError("first-candidate invocation context is invalid")
    selected = context.get("selected_context")
    if not isinstance(selected, Mapping):
        raise WorkflowError("first-candidate selected context is invalid")
    source = selected.get("architect_intent_source")
    if not isinstance(source, Mapping) or source.get("path") != ARCHITECT_INTENT_RECORD:
        raise WorkflowError("Architect intent source identity is invalid")


def _validate_role_result(
    result: Mapping[str, Any],
    context_sha256: str,
) -> None:
    """Validate the fresh implementation semantic result before packaging."""
    if set(result) != RESULT_FIELDS:
        raise WorkflowError("fresh implementation result fields are invalid")
    checks = (
        (result.get("schema_version") == "1.0", "schema_version is invalid"),
        (
            result.get("record_type") == "sage-fresh-implementation-result",
            "record_type is invalid",
        ),
        (result.get("authority") == "advisory", "authority must be advisory"),
        (result.get("role") == ROLE, "role identity is invalid"),
        (result.get("context_sha256") == context_sha256, "context identity changed"),
        (isinstance(result.get("contribution"), Mapping), "contribution is invalid"),
        (isinstance(result.get("payload"), list), "payload is invalid"),
    )
    for valid, message in checks:
        if not valid:
            raise WorkflowError(f"fresh implementation {message}")


def _validate_receipt(
    receipt: Mapping[str, Any],
    envelope: Mapping[str, Any],
    result: Mapping[str, Any],
) -> None:
    """Bind result identity to the actual provider/model/invocation receipt."""
    required = {
        "provider",
        "model_requested",
        "model_reported",
        "invocation_sha256",
        "role_result_sha256",
        "architect_chat_history_included",
        "role_chat_history_included",
        "predecessor_chat_history_included",
    }
    if not required.issubset(receipt):
        raise WorkflowError("fresh-role invocation receipt is incomplete")
    if not isinstance(receipt.get("provider"), str) or not str(receipt["provider"]).strip():
        raise WorkflowError("fresh-role provider identity is missing")
    for field in ("model_requested", "model_reported"):
        if not isinstance(receipt.get(field), str) or not str(receipt[field]).strip():
            raise WorkflowError(f"fresh-role receipt {field} is missing")
    if receipt.get("invocation_sha256") != sha256_json(envelope):
        raise WorkflowError("fresh-role invocation receipt identity does not match")
    if receipt.get("role_result_sha256") != sha256_json(result):
        raise WorkflowError("fresh-role result receipt identity does not match")
    for field in (
        "architect_chat_history_included",
        "role_chat_history_included",
        "predecessor_chat_history_included",
    ):
        if receipt.get(field) is not False:
            raise WorkflowError(
                f"fresh-role receipt isolation field is invalid: {field}"
            )


def _validate_isolation(provenance: Mapping[str, Any]) -> None:
    """Require every prohibited inherited context source to remain excluded."""
    isolation = provenance.get("isolation")
    if not isinstance(isolation, Mapping):
        raise WorkflowError("fresh contribution isolation provenance is missing")
    for field in ISOLATION_FIELDS:
        if isolation.get(field) is not False:
            raise WorkflowError(
                f"fresh contribution isolation field is invalid: {field}"
            )


def _validate_external_sources(provenance: Mapping[str, Any]) -> None:
    """Validate external source provenance without converting it to repository truth."""
    sources = provenance.get("external_sources", [])
    if not isinstance(sources, list):
        raise WorkflowError("fresh contribution external_sources must be a list")
    required = {"source", "retrieved_at", "claim_supported", "candidate_influence"}
    for index, item in enumerate(sources):
        if not isinstance(item, Mapping) or not required.issubset(item):
            raise WorkflowError(f"external_sources[{index}] provenance is incomplete")
        if item.get("source_class") != "current-external-engineering":
            raise WorkflowError(f"external_sources[{index}] source_class is invalid")
        for field in sorted(required):
            if not isinstance(item.get(field), str) or not str(item[field]).strip():
                raise WorkflowError(f"external_sources[{index}].{field} is invalid")


def _validate_strawman_dispositions(
    contributor: Mapping[str, Any],
    strawman: Mapping[str, Any] | None,
) -> None:
    """Require explicit fresh-role treatment when persistent prior work exists."""
    dispositions = contributor.get("strawman_dispositions", [])
    if not isinstance(dispositions, list):
        raise WorkflowError("strawman_dispositions must be a list")
    if strawman is None and dispositions:
        raise WorkflowError("strawman dispositions exist without a supplied strawman")
    if strawman is not None and not dispositions:
        raise WorkflowError("supplied strawman lacks fresh-role dispositions")
    digest = None if strawman is None else strawman.get("artifact_sha256")
    for index, item in enumerate(dispositions):
        _validate_strawman_disposition(item, index, digest)


def _validate_strawman_disposition(
    item: object,
    index: int,
    strawman_sha256: object,
) -> None:
    """Validate one fresh-role disposition of persistent-LLM prior work."""
    if not isinstance(item, Mapping):
        raise WorkflowError(f"strawman_dispositions[{index}] must be an object")
    if item.get("disposition") not in ALLOWED_STRAWMAN_DISPOSITIONS:
        raise WorkflowError(f"strawman_dispositions[{index}] disposition is invalid")
    for field in ("scope", "rationale"):
        if not isinstance(item.get(field), str) or not str(item[field]).strip():
            raise WorkflowError(f"strawman_dispositions[{index}].{field} is required")
    if strawman_sha256 is not None and item.get("artifact_sha256") != strawman_sha256:
        raise WorkflowError(
            f"strawman_dispositions[{index}] artifact digest is invalid"
        )


def _validate_epistemic_basis(provenance: Mapping[str, Any]) -> None:
    """Require implementation cognition to separate evidence from inference."""
    basis = provenance.get("epistemic_basis")
    if not isinstance(basis, Mapping):
        raise WorkflowError("fresh contribution epistemic_basis is missing")
    required = {
        "evidence_relied_on", "model_inference", "assumptions",
        "unknowns", "validation", "stop_conditions",
    }
    if set(basis) != required:
        raise WorkflowError("fresh contribution epistemic_basis fields are invalid")
    for field in sorted(required):
        value = basis.get(field)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise WorkflowError(f"fresh contribution epistemic_basis.{field} is invalid")


def _declared_provenance(
    manifest: Mapping[str, Any],
    context_sha256: str,
    strawman: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate role-declared provenance before receipt fields are attached."""
    contributor = manifest.get("contributor")
    if not isinstance(contributor, Mapping):
        raise WorkflowError("fresh contribution contributor metadata is missing")
    provenance = contributor.get("fresh_role_provenance")
    if not isinstance(provenance, Mapping):
        raise WorkflowError("fresh contribution fresh_role_provenance is missing")
    if provenance.get("role") != ROLE:
        raise WorkflowError("fresh contribution role provenance is invalid")
    if provenance.get("context_sha256") != context_sha256:
        raise WorkflowError("fresh contribution context provenance is invalid")
    _validate_isolation(provenance)
    _validate_external_sources(provenance)
    _validate_epistemic_basis(provenance)
    _validate_strawman_dispositions(contributor, strawman)
    return dict(contributor), dict(provenance)


def _receipt_bound_manifest(
    result: Mapping[str, Any],
    receipt: Mapping[str, Any],
    context_sha256: str,
    strawman: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Attach runtime-attested provider/model identities to role-authored manifest."""
    manifest = json.loads(json.dumps(result["contribution"]))
    contributor, provenance = _declared_provenance(manifest, context_sha256, strawman)
    for field in ("provider", "model"):
        if field in provenance:
            raise WorkflowError(f"fresh role may not self-assert runtime {field}")
    provenance.update({
        "provider": receipt["provider"],
        "model": receipt["model_reported"],
        "model_requested": receipt["model_requested"],
        "invocation_sha256": receipt["invocation_sha256"],
        "role_result_sha256": receipt["role_result_sha256"],
        "invocation_receipt_sha256": sha256_json(receipt),
    })
    contributor["fresh_role_provenance"] = provenance
    manifest["contributor"] = contributor
    return manifest


def _payload_by_path(result: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Index role-authored UTF-8 payload records by repository-relative path."""
    indexed: dict[str, Mapping[str, Any]] = {}
    for index, item in enumerate(result["payload"]):
        if not isinstance(item, Mapping):
            raise WorkflowError(f"payload[{index}] must be an object")
        if set(item) != {"path", "mode", "content"}:
            raise WorkflowError(f"payload[{index}] fields are invalid")
        path = item.get("path")
        if not isinstance(path, str) or not path.strip() or path in indexed:
            raise WorkflowError(f"payload[{index}] path is invalid or duplicated")
        if item.get("mode") not in {"0644", "0755"}:
            raise WorkflowError(f"payload[{index}] mode is invalid")
        if not isinstance(item.get("content"), str):
            raise WorkflowError(f"payload[{index}] content must be UTF-8 text")
        indexed[path] = item
    return indexed


def _write_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    payload: bytes,
    mode: int = 0o644,
) -> None:
    """Write one deterministic regular-file member to a contribution package."""
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (stat.S_IFREG | mode) << 16
    archive.writestr(info, payload)


def _package_role_result(
    destination: Path,
    result: Mapping[str, Any],
    receipt: Mapping[str, Any],
    context_sha256: str,
    strawman: Mapping[str, Any] | None,
) -> EngineeringContribution:
    """Package one JSON role result into the existing contribution contract."""
    manifest = _receipt_bound_manifest(result, receipt, context_sha256, strawman)
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise WorkflowError("fresh contribution files are missing")
    payload = _payload_by_path(result)
    declared = {
        str(item.get("path")): item
        for item in files
        if isinstance(item, Mapping)
    }
    if set(payload) != set(declared) or len(declared) != len(files):
        raise WorkflowError("fresh contribution payload does not match manifest files")
    with zipfile.ZipFile(destination, "x") as archive:
        _write_zip_member(
            archive,
            "engineering-contribution.json",
            stable_json(manifest).encode("utf-8"),
        )
        for path in sorted(payload):
            item = payload[path]
            if item["mode"] != declared[path].get("mode"):
                raise WorkflowError(f"fresh contribution mode mismatch: {path}")
            _write_zip_member(
                archive,
                f"payload/{path}",
                str(item["content"]).encode("utf-8"),
                int(str(item["mode"]), 8),
            )
    return load_engineering_contribution(destination)


def _validate_final_provenance(
    contribution: EngineeringContribution,
    receipt: Mapping[str, Any],
    context_sha256: str,
    strawman: Mapping[str, Any] | None,
) -> None:
    """Revalidate packaged contribution provenance against the provider receipt."""
    contributor = contribution.manifest.get("contributor")
    if not isinstance(contributor, Mapping):
        raise WorkflowError("packaged contributor provenance is missing")
    provenance = contributor.get("fresh_role_provenance")
    if not isinstance(provenance, Mapping):
        raise WorkflowError("packaged fresh-role provenance is missing")
    expected = {
        "role": ROLE,
        "provider": receipt.get("provider"),
        "model": receipt.get("model_reported"),
        "context_sha256": context_sha256,
        "invocation_sha256": receipt.get("invocation_sha256"),
        "role_result_sha256": receipt.get("role_result_sha256"),
    }
    for field, value in expected.items():
        if provenance.get(field) != value:
            raise WorkflowError(f"packaged fresh-role provenance mismatch: {field}")
    _validate_isolation(provenance)
    _validate_external_sources(provenance)
    _validate_epistemic_basis(provenance)
    _validate_strawman_dispositions(contributor, strawman)


def _enter_existing_lifecycle(
    repo: Path,
    action_id: str,
    request: str,
    contribution: EngineeringContribution,
    context_path: Path,
    context_sha256: str,
    invocation_path: Path,
    receipt_path: Path,
    result_path: Path,
    lifecycle_starter: LifecycleStarter,
) -> Mapping[str, Any]:
    """Hand the generated candidate to the unchanged deterministic lifecycle."""
    lifecycle = lifecycle_starter(repo, action_id, request, contribution.package_path)
    return {
        "status": "candidate-generated",
        "context": str(context_path),
        "context_sha256": context_sha256,
        "invocation": str(invocation_path),
        "invocation_receipt": str(receipt_path),
        "role_result": str(result_path),
        "contribution": str(contribution.package_path),
        "contribution_sha256": contribution.package_sha256,
        "lifecycle": dict(lifecycle),
        "fresh_critic_required": True,
        "self_approved": False,
    }


def _package_and_validate(
    state_dir: Path,
    result: Mapping[str, Any],
    receipt: Mapping[str, Any],
    context_sha256: str,
    prior_work: Mapping[str, Any] | None,
) -> EngineeringContribution:
    """Package a fresh result and revalidate its receipt-bound provenance."""
    contribution = _package_role_result(
        state_dir / "fresh-engineering-contribution.zip",
        result,
        receipt,
        context_sha256,
        prior_work,
    )
    _validate_final_provenance(
        contribution, receipt, context_sha256, prior_work
    )
    return contribution


def _generate_with_action(
    repo: Path,
    action_id: str,
    request: str,
    action: Mapping[str, Any],
    prior_work: Mapping[str, Any] | None,
    readiness: Mapping[str, Any],
    readiness_sha256: str,
    runtime_resolver: RuntimeResolver,
    provider_invoker: ProviderInvoker,
    lifecycle_starter: LifecycleStarter,
) -> Mapping[str, Any]:
    """Run the corrected fresh-role adapter after intent and prior-work validation."""
    state_dir = new_state_dir("fresh-candidate")
    context, context_sha256, context_path = _prepare_context(
        repo, action, request, state_dir, readiness, readiness_sha256, prior_work
    )
    envelope = build_invocation(
        role=ROLE,
        objective_id=action_id,
        request=_invocation_request(prior_work),
        context=context,
    )
    _validate_invocation_contract(envelope)
    invocation_path = state_dir / "fresh-role-invocation.json"
    _persist_role_json(invocation_path, envelope)
    prompt = (repo / ROLE_PROMPT_PATH).read_text(encoding="utf-8")
    raw, receipt, blocker = repository_fresh_role_invoker(
        envelope, prompt, runtime_resolver, provider_invoker
    )
    if blocker is not None:
        blocked = _runtime_blocker(action_id, blocker)
        _persist_role_json(state_dir / "fresh-role-blocker.json", blocked)
        return blocked
    result = dict(raw or {})
    observed_receipt = dict(receipt or {})
    _validate_role_result(result, context_sha256)
    _validate_receipt(observed_receipt, envelope, result)
    result_path = state_dir / "fresh-role-result.json"
    receipt_path = state_dir / "fresh-role-invocation-receipt.json"
    _persist_role_json(result_path, result)
    _persist_role_json(receipt_path, observed_receipt)
    contribution = _package_and_validate(
        state_dir, result, observed_receipt, context_sha256, prior_work
    )
    return _enter_existing_lifecycle(
        repo, action_id, request, contribution, context_path, context_sha256,
        invocation_path, receipt_path, result_path, lifecycle_starter
    )


def generate_first_candidate(
    repo: Path,
    action_id: str,
    request: str,
    *,
    readiness: Path,
    strawman: Path | None = None,
    strawman_provenance: Path | None = None,
    runtime_resolver: RuntimeResolver = resolve_ollama_runtime,
    provider_invoker: ProviderInvoker = invoke_ollama_json,
    lifecycle_starter: LifecycleStarter = begin_intent,
) -> Mapping[str, Any]:
    """Create the first fresh contribution and enter the existing SAGE lifecycle."""
    resolved = repo.expanduser().resolve()
    action = load_improvement_action(resolved, action_id)
    if action.get("current_status") != "accepted":
        raise WorkflowError(
            f"{action_id} must be accepted before first-candidate generation"
        )
    readiness_path = readiness.expanduser().resolve()
    readiness_record = require_implementation_ready(
        readiness_path, resolved, request
    )
    readiness_sha256 = sha256_file(readiness_path)
    prior_work = _strawman_context(strawman, strawman_provenance)
    return _generate_with_action(
        resolved,
        action_id,
        request,
        action,
        prior_work,
        readiness_record,
        readiness_sha256,
        runtime_resolver,
        provider_invoker,
        lifecycle_starter,
    )


def _fixture_role_result(context_sha256: str) -> dict[str, Any]:
    """Build one valid fresh implementation result for deterministic self-test."""
    manifest = {
        "schema_version": "1.0",
        "contribution_id": "SAGE-CONTRIBUTION-FRESH-ROLE-SELF-TEST",
        "contributor": {
            "participant_class": "llm",
            "identity": "fresh-role-self-test",
            "fresh_role_provenance": {
                "role": ROLE,
                "context_sha256": context_sha256,
                "isolation": {field: False for field in ISOLATION_FIELDS},
                "external_sources": [],
                "epistemic_basis": {
                    "evidence_relied_on": ["fixture repository grounding"],
                    "model_inference": [],
                    "assumptions": [],
                    "unknowns": [],
                    "validation": ["fixture validation"],
                    "stop_conditions": ["fixture failure"],
                },
            },
            "strawman_dispositions": [],
        },
        "summary": "Self-test first candidate",
        "rationale": "Exercise receipt-bound fresh-role contribution packaging.",
        "assumptions": [],
        "alternatives": ["No change"],
        "files": [{"path": "fixture.txt", "mode": "0644"}],
    }
    return {
        "schema_version": "1.0",
        "record_type": "sage-fresh-implementation-result",
        "authority": "advisory",
        "role": ROLE,
        "context_sha256": context_sha256,
        "contribution": manifest,
        "payload": [{"path": "fixture.txt", "mode": "0644", "content": "fixture\n"}],
    }


def _fixture_receipt(
    envelope: Mapping[str, Any],
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one receipt matching the real repository receipt identity fields."""
    return {
        "provider": "ollama",
        "model_requested": "fixture-model",
        "model_reported": "fixture-model",
        "invocation_sha256": sha256_json(envelope),
        "role_result_sha256": sha256_json(result),
        "architect_chat_history_included": False,
        "role_chat_history_included": False,
        "predecessor_chat_history_included": False,
    }


def _self_test_result_and_receipt(root: Path) -> EngineeringContribution:
    """Exercise actual invocation-envelope and receipt-bound package contracts."""
    selected = {
        "architect_intent": {"action_id": "SAGE-ACTION-FIXTURE"},
        "architect_intent_source": {
            "record_type": "architect_intent",
            "path": ARCHITECT_INTENT_RECORD,
            "artifact_sha256": "a" * 64,
            "action_record_sha256": "b" * 64,
            "source_class": "architect-owned-intent",
        },
        "literal_request": "first candidate self-test",
    }
    context_sha256 = sha256_json(selected)
    context = {"selected_context_sha256": context_sha256, "selected_context": selected}
    envelope = build_invocation(
        role=ROLE,
        objective_id="SAGE-ACTION-FIXTURE",
        request=_invocation_request(None),
        context=context,
    )
    _validate_invocation_contract(envelope)
    result = _fixture_role_result(context_sha256)
    receipt = _fixture_receipt(envelope, result)
    _validate_role_result(result, context_sha256)
    _validate_receipt(receipt, envelope, result)
    contribution = _package_role_result(
        root / "candidate.zip", result, receipt, context_sha256, None
    )
    _validate_final_provenance(contribution, receipt, context_sha256, None)
    policy = envelope.get("context_policy", {})
    if any(policy.get(field) for field in (
        "architect_chat_history_included",
        "role_chat_history_included",
        "predecessor_chat_history_included",
        "executor_filesystem_access_required",
    )):
        raise RuntimeError("fresh invocation inherited forbidden context")
    return contribution


def _self_test_lifecycle(root: Path, contribution: EngineeringContribution) -> None:
    """Exercise unchanged lifecycle handoff and non-self-approval semantics."""
    observed: dict[str, Any] = {}

    def starter(
        repo: Path,
        action_id: str,
        request: str,
        package: Path,
    ) -> Mapping[str, Any]:
        """Capture one synthetic lifecycle call."""
        observed.update({"package": package, "action_id": action_id})
        return {"status": "semantic-confirmation-required"}

    result = _enter_existing_lifecycle(
        root,
        "SAGE-ACTION-FIXTURE",
        "first candidate self-test",
        contribution,
        root / "context.json",
        "a" * 64,
        root / "invocation.json",
        root / "receipt.json",
        root / "result.json",
        starter,
    )
    if observed.get("package") != contribution.package_path:
        raise RuntimeError("generated contribution did not enter existing lifecycle")
    if (
        result.get("fresh_critic_required") is not True
        or result.get("self_approved") is not False
    ):
        raise RuntimeError("fresh critic/non-self-approval boundary changed")


def _self_test_runtime_blocker() -> None:
    """Exercise missing runtime fail-closed behavior with no persistent fallback."""
    try:
        resolve_ollama_runtime({})
    except RoleInvocationError as error:
        blocked = _runtime_blocker("SAGE-ACTION-FIXTURE", str(error))
    else:
        raise RuntimeError("missing fresh-role runtime did not fail closed")
    if blocked["repository_mutation"] or blocked["next_boundary"] != RUNTIME_BOUNDARY:
        raise RuntimeError("runtime blocker changed governed non-mutation semantics")


def _self_test_readiness_gate(root: Path) -> None:
    """Exercise all readiness dispositions plus unsupported grounding."""
    grounded = root / "grounded.py"
    grounded.write_text("# grounded\n", encoding="utf-8")
    base = {
        "disposition": "implementation-ready",
        "rationale": "fixture",
        "evidence_references": ["fixture:evidence"],
        "repository_grounding": [{"path": "grounded.py"}],
        "model_inference": [],
        "assumptions": [],
        "dependencies": [],
        "implementation_recipe": ["apply fixture"],
        "validation": ["validate fixture"],
        "blocking_unknowns": [],
        "gap_closure": [],
        "alternatives": [],
        "limitations": [],
        "stop_conditions": ["validation failure"],
        "material_decision_required": False,
    }
    validate_readiness_payload(base, root)
    for disposition in (
        "knowledge-evidence-capability-gap",
        "material-decision-required",
        "unsupported",
    ):
        candidate = dict(base)
        candidate["disposition"] = disposition
        candidate["implementation_recipe"] = []
        if disposition == "knowledge-evidence-capability-gap":
            candidate["blocking_unknowns"] = ["missing capability"]
            candidate["gap_closure"] = ["supply capability"]
        elif disposition == "material-decision-required":
            candidate["alternatives"] = ["A", "B"]
            candidate["material_decision_required"] = True
        else:
            candidate["blocking_unknowns"] = ["unsupported"]
        validate_readiness_payload(candidate, root)
    hallucinated = dict(base)
    hallucinated["repository_grounding"] = [{"path": "does-not-exist.py"}]
    try:
        validate_readiness_payload(hallucinated, root)
    except ReadinessError:
        pass
    else:
        raise RuntimeError("unsupported repository grounding was accepted")


def run_contract_self_test() -> None:
    """Exercise the corrected first-candidate adapter without provider mutation."""
    with tempfile.TemporaryDirectory(prefix="sage-first-candidate-") as raw:
        root = Path(raw)
        _self_test_readiness_gate(root)
        contribution = _self_test_result_and_receipt(root)
        _self_test_lifecycle(root, contribution)
        _self_test_runtime_blocker()
    print("PASS four implementation-readiness dispositions are deterministically validated")
    print("PASS unsupported repository grounding cannot masquerade as implementation-ready")
    print("PASS first candidate uses repository build_invocation contract")
    print("PASS first candidate binds the Architect intent source projection")
    print("PASS repository fresh-role invoker preserves the semantic invocation record")
    print("PASS provider/model/context identity is bound from invocation receipt")
    print("PASS fresh role requires no filesystem access to consume SAGE context")
    print("PASS role JSON is packaged into existing engineering contribution contract")
    print("PASS generated candidate enters existing deterministic lifecycle")
    print("PASS separate critic/non-self-approval boundary remains intact")
    print("PASS missing fresh-role runtime fails closed without persistent fallback")
