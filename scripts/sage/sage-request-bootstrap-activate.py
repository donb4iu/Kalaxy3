#!/usr/bin/env python3
"""One-time repository-owned bootstrap activation for one exact SAGE candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import stat
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

OBJECTIVE_ID = "SAGE-ACTION-20260813-001"
EXPECTED_BRANCH = "fix/sage-lifecycle-break-glass-20260907"
EXPECTED_HEAD = "74c96f458cc0cb9678dd288fc307e90d2f2e8e4f"
EXPECTED_REQUEST_SHA256 = (
    "d6639557fcc3993aa9087eb43356f26678872bb0337cb8a2aa198ff17564a268"
)
EXPECTED_PROPOSAL_SHA256 = (
    "7b1c87539dd458bd696d9a95896035598f041452e15301c20e3094d3b554e7e1"
)
EXPECTED_CONTRIBUTION_SHA256 = (
    "37585f5cd1e3d1cac8d180de0f85506f4b63ebdd5ab8c8a3dd4d2c997af02696"
)
EXPECTED_ARCHITECT_INTENT_SHA256 = (
    "e902132409e2a4dd65a0b6d85525c61f90b8bd76e4c6e71b64549325d10216ad"
)
EXPECTED_OBJECTIVE_DECISION_SHA256 = (
    "09155a35566a8f5cb661ac98a97832316e1601e58c20a3a2092123b08fad6557"
)
EXPECTED_REQUEST_STATE_SHA256 = (
    "37c9bdb0f45c47cbdb91b4389801fe4dfe4b58b7f1d8c8dfd4bcf83c312a4019"
)
EXPECTED_CONTRIBUTION_ID = (
    "SAGE-CONTRIBUTION-20260915-OLLAMA-SERIAL-GATE-ATOMIC-COMPOSITE"
)
FAILURE_CONTEXT = "helm-platform"
FAILURE_CWD = "infrastructure/k3s-homelab"
FAILURE_COMMAND = ("make", "source-guardrails")
FAILURE_MARKERS = (
    "playbooks/tasks/nvidia-device-plugin.yml",
    "lacks Helm binary_path",
    "lacks isolated Helm environment",
)
CANDIDATE_CORRECTION_PATH = (
    "infrastructure/k3s-homelab/playbooks/tasks/nvidia-device-plugin.yml"
)
CANDIDATE_CORRECTION_MARKERS = (
    'binary_path: "{{ helm_binary }}"',
    'environment: "{{ helm_environment }}"',
)

EXPECTED_SOURCE_SIGNATURE = (
    (
        "scripts/sage/workflow/recovery.py",
        "87692f204c8295d241b5ffc12cac238d226d1be0b72413d8b66ca606490897d2",
        0o644,
    ),
    (
        "scripts/sage/workflows/request_execution.py",
        "63040074c46369c505242adfe6482c2db55493991fdf17ab8194758bd7f64d2a",
        0o755,
    ),
    (
        "scripts/sage/sage-request-execute.py",
        "021d7a66d771e31cface4741952750ee5a66a1c95b3631a25b46bc5549913345",
        0o755,
    ),
    (
        "markdown/standards/kalaxy3-sage-recovery-process.md",
        "ddfa4d293c63060ed878359f147866b44eb960abd30317d34168ed4d4959070d",
        0o644,
    ),
    (
        "markdown/standards/kalaxy3-sage-request-execution-process.md",
        "e85f6aef9d6f1ba39910f50560cea50765f450a36525bf5e02b726712ebc4c70",
        0o644,
    ),
    (
        "infrastructure/k3s-homelab/playbooks/tasks/nvidia-device-plugin.yml",
        "77f537ea376127a22242e3af21560a6c37a7194402424659be839cb265420e6b",
        0o644,
    ),
    (
        "infrastructure/k3s-homelab/ollama-platforms.json",
        "c929ccfbff2cde9e5d8782682fd9aaf7c255cf68b06a0cf398abb05b2eb577a1",
        0o644,
    ),
    (
        "infrastructure/k3s-homelab/manifests/ollama.yml.j2",
        "2c57408562884fb8c894f4f1d8aa5088e8bb642fc27325b17d3883a03239d3ae",
        0o644,
    ),
    (
        "infrastructure/k3s-homelab/playbooks/ollama.yml",
        "399a7fc60e244f1bf1c755079268f6ab17227a22a86e0212936132862375f42f",
        0o644,
    ),
    (
        "infrastructure/k3s-homelab/playbooks/validate-ollama.yml",
        "6b66cc41ba7e571128b134c5912424378d01a9f4e5c36fe3b590c6deb35e67e0",
        0o644,
    ),
)

TRUSTED_TARGET_FILES = {
    "Makefile": (
        "a968d816fac80916f2f01c13157a547a269133a5ffaedcad49d48ea04e624966"
    ),
    "sage-change-authority.json": (
        "291962bad3fee58d770e667dc16ed796ca9674393cc424c0695b424cf9dab127"
    ),
    "sage-operating-contract-policy.json": (
        "b10cb97df7a23eb994cfec3427d8c38efd3752150c38fb30da48e89425367b3c"
    ),
    "sage-workflow-primitives.json": (
        "894b27a8a9d324fd3f7a26b2021492c61d314f7db0225daba6dac416229bd6d0"
    ),
    "scripts/sage/request_execution.py": (
        "9a02dedefea55ea5ace91895d582c5753429eec7a946e7bb9e377b76e269181f"
    ),
    "scripts/sage/sage-change-preflight.py": (
        "4a120b9ee621aa69fe7eebb4135059b121ee9fb54ab7eca92fd02dfd9a482599"
    ),
    "scripts/sage/workflow/authority.py": (
        "97f625a1c61f8fd99d6768f4cfc52e4472c5817cf8165602a69388762d44ed38"
    ),
    "scripts/sage/workflow/files.py": (
        "49d9a3567b601a6e069e09b132a3447bfc968e8b95738a4b62998b383378974f"
    ),
    "scripts/sage/workflow/proposal.py": (
        "052952f85a0f04e1d711e5b2aef97e95f5334a1936e5ebdae8f8e5df87a4bffc"
    ),
    "scripts/sage/workflow/safety.py": (
        "6cca541b21e18a16bded077f8847d0ffcd3119115b055eeadf88fc36b2aa576e"
    ),
    "scripts/sage/workflow/validation.py": (
        "a6011a96322dc17ba34d9896208710c513a48a3012e79d4323e71802c8448e4a"
    ),
    "scripts/sage/workflows/request_execution.py": (
        "92b01ffbecc5e7069d7aac7b5eb2f2c96b13a999f787fb5b85fb1b7d0ce7ede4"
    ),
    "scripts/sage/sage-routine-git-lifecycle.py": (
        "5da13c42562549cc0c58ac8d25027bc175bf7d41eb82406e84c7ec9097bbbb48"
    ),
    "scripts/sage/workflows/routine_git_lifecycle.py": (
        "b60914e0c31ad2b68239a9e4a20cb83eb299203d4b670198ba3820081275fe69"
    ),
}


class BootstrapError(RuntimeError):
    """Raised when one bootstrap activation invariant fails closed."""


@dataclass(frozen=True)
class BaselineEntry:
    """One repository-owned baseline validation command."""

    context_id: str
    cwd: Path
    command_text: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class BaselineObservation:
    """One observed pre-stage baseline command result."""

    entry: BaselineEntry
    returncode: int
    output_sha256: str
    stdout: str
    stderr: str


def sha256_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 digest for bytes."""

    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest for one file."""

    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object or fail closed.

    Args:
        path: JSON file to load.
    """

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BootstrapError(f"JSON object required: {path}")
    return value


def require_digest(path: Path, expected: str, label: str) -> None:
    """Require one exact file digest.

    Args:
        path: File whose bytes are authoritative.
        expected: Required SHA-256 digest.
        label: Human-readable artifact label.
    """

    observed = sha256_file(path)
    if observed != expected:
        raise BootstrapError(
            f"{label} digest drifted: expected {expected}, observed {observed}"
        )


def require_authority_snapshot(
    branch: str,
    head: str,
    clean: bool,
) -> None:
    """Require the exact proposal-bound repository authority.

    Args:
        branch: Observed branch.
        head: Observed HEAD.
        clean: Whether the target worktree is clean.
    """

    if not clean:
        raise BootstrapError("bootstrap target worktree must be clean")
    if branch != EXPECTED_BRANCH or head != EXPECTED_HEAD:
        raise BootstrapError("bootstrap target branch/HEAD authority drifted")


def request_from_state(path: Path) -> str:
    """Load the exact literal request from the packet-bound state.

    Args:
        path: Intent-to-outcome state carrying the literal request.
    """

    require_digest(path, EXPECTED_REQUEST_STATE_SHA256, "request state")
    payload = load_json(path)
    request = payload.get("request")
    if not isinstance(request, str) or not request:
        raise BootstrapError("request state lacks the literal request")
    if sha256_bytes(request.encode("utf-8")) != EXPECTED_REQUEST_SHA256:
        raise BootstrapError("literal request digest drifted")
    if payload.get("objective_id") != OBJECTIVE_ID:
        raise BootstrapError("request state objective identity drifted")
    return request


def verify_architect_authority(intent: Path, decision: Path) -> None:
    """Verify the exact Architect authorization and path decision.

    Args:
        intent: Architect bootstrap-authorization record.
        decision: Architect-approved objective path decision.
    """

    require_digest(intent, EXPECTED_ARCHITECT_INTENT_SHA256, "Architect intent")
    require_digest(decision, EXPECTED_OBJECTIVE_DECISION_SHA256, "path decision")
    intent_value = load_json(intent)
    decision_value = load_json(decision)
    if intent_value.get("architect_decision") != "approved":
        raise BootstrapError("Architect bootstrap authority is not approved")
    if intent_value.get("objective_id") != OBJECTIVE_ID:
        raise BootstrapError("Architect objective identity drifted")
    if decision_value.get("active_objective_id") != OBJECTIVE_ID:
        raise BootstrapError("objective path identity drifted")
    if decision_value.get("request_sha256") != EXPECTED_REQUEST_SHA256:
        raise BootstrapError("objective path request binding drifted")
    if decision_value.get("proposal_sha256") != EXPECTED_PROPOSAL_SHA256:
        raise BootstrapError("objective path proposal binding drifted")


def verify_target_trust_root(repo: Path) -> None:
    """Require packet-proven pre-candidate controller/support bytes.

    Args:
        repo: Exact target repository checkout.
    """

    for relative, expected in TRUSTED_TARGET_FILES.items():
        path = repo / relative
        if not path.is_file() or path.is_symlink():
            raise BootstrapError(f"trusted target file is missing: {relative}")
        require_digest(path, expected, f"trusted target file {relative}")


def verify_controller_trust_root() -> None:
    """Require unchanged support code before importing controller modules."""

    root = controller_root()
    for relative, expected in TRUSTED_TARGET_FILES.items():
        if relative == "Makefile":
            continue
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise BootstrapError(f"trusted controller file is missing: {relative}")
        require_digest(path, expected, f"trusted controller file {relative}")


def require_source_signature(
    observed: Sequence[tuple[str, str, int]],
    label: str,
) -> None:
    """Require exact declared path, digest, order, and mode signature.

    Args:
        observed: Observed source signature.
        label: Human-readable signature label.
    """

    if tuple(observed) != EXPECTED_SOURCE_SIGNATURE:
        raise BootstrapError(f"{label} path/digest/mode signature drifted")


def signature_from_bundle(bundle: Any) -> tuple[tuple[str, str, int], ...]:
    """Return the exact proposal source signature.

    Args:
        bundle: Validated request-execution proposal bundle.
    """

    return tuple((item.path, item.sha256, item.mode) for item in bundle.source_files)


def verify_proposal_bundle(bundle: Any, proposal: Path) -> None:
    """Require exact proposal package, repository, scope, digests, and modes.

    Args:
        bundle: Validated proposal bundle.
        proposal: Proposal ZIP path.
    """

    require_digest(proposal, EXPECTED_PROPOSAL_SHA256, "request proposal")
    repository = bundle.manifest.get("repository", {})
    if repository != {"branch": EXPECTED_BRANCH, "head": EXPECTED_HEAD}:
        raise BootstrapError("proposal repository authority drifted")
    if bundle.manifest.get("request_sha256") != EXPECTED_REQUEST_SHA256:
        raise BootstrapError("proposal literal-request binding drifted")
    require_source_signature(signature_from_bundle(bundle), "proposal declared")
    if tuple(bundle.generated_paths):
        raise BootstrapError("bootstrap candidate unexpectedly declares generated paths")


def safe_zip_path(name: str) -> str:
    """Validate one canonical ZIP member path.

    Args:
        name: ZIP member name.
    """

    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise BootstrapError(f"unsafe contribution archive path: {name}")
    if pure.as_posix() != name:
        raise BootstrapError(f"non-canonical contribution archive path: {name}")
    return name


def contribution_signature(path: Path) -> tuple[tuple[str, str, int], ...]:
    """Read the exact engineering-contribution payload signature.

    Args:
        path: Engineering contribution ZIP.
    """

    with zipfile.ZipFile(path, "r") as archive:
        names = [safe_zip_path(item.filename) for item in archive.infolist()]
        if len(names) != len(set(names)):
            raise BootstrapError("contribution contains duplicate archive paths")
        manifest = json.loads(archive.read("engineering-contribution.json"))
        return _contribution_signature_from_archive(archive, manifest, names)


def _contribution_signature_from_archive(
    archive: zipfile.ZipFile,
    manifest: Mapping[str, Any],
    names: Sequence[str],
) -> tuple[tuple[str, str, int], ...]:
    """Build and validate one contribution signature.

    Args:
        archive: Open contribution ZIP.
        manifest: Parsed engineering contribution manifest.
        names: Canonical archive member names.
    """

    if manifest.get("contribution_id") != EXPECTED_CONTRIBUTION_ID:
        raise BootstrapError("engineering contribution identity drifted")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise BootstrapError("engineering contribution files are invalid")
    signature: list[tuple[str, str, int]] = []
    for item in files:
        signature.append(_contribution_file_signature(archive, item, names))
    expected_names = {"engineering-contribution.json"}
    expected_names.update(f"payload/{item[0]}" for item in signature)
    if set(names) != expected_names:
        raise BootstrapError("engineering contribution archive scope drifted")
    return tuple(signature)


def _contribution_file_signature(
    archive: zipfile.ZipFile,
    item: Any,
    names: Sequence[str],
) -> tuple[str, str, int]:
    """Validate one engineering contribution file entry.

    Args:
        archive: Open contribution ZIP.
        item: Manifest file entry.
        names: Canonical archive member names.
    """

    if not isinstance(item, Mapping):
        raise BootstrapError("engineering contribution file entry is invalid")
    relative = str(item.get("path", ""))
    mode_text = str(item.get("mode", ""))
    if mode_text not in {"0644", "0755"}:
        raise BootstrapError(f"invalid contribution file mode: {relative}")
    member = f"payload/{relative}"
    if member not in names:
        raise BootstrapError(f"missing contribution payload: {relative}")
    payload = archive.read(member)
    return relative, sha256_bytes(payload), int(mode_text, 8)


def verify_contribution(path: Path, bundle: Any) -> None:
    """Require exact contribution package and proposal-equivalent payload.

    Args:
        path: Exact atomic composite contribution ZIP.
        bundle: Validated request proposal bundle.
    """

    require_digest(path, EXPECTED_CONTRIBUTION_SHA256, "engineering contribution")
    signature = contribution_signature(path)
    require_source_signature(signature, "engineering contribution")
    if signature != signature_from_bundle(bundle):
        raise BootstrapError("contribution and proposal payload signatures differ")
    correction = next(
        item
        for item in bundle.source_files
        if item.path == CANDIDATE_CORRECTION_PATH
    )
    text = correction.payload.decode("utf-8")
    if any(marker not in text for marker in CANDIDATE_CORRECTION_MARKERS):
        raise BootstrapError("candidate-correctable baseline proof drifted")


def normalize(value: str) -> str:
    """Normalize authority matching text.

    Args:
        value: Text to normalize.
    """

    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def inferred_context_ids(payload: Mapping[str, Any], paths: Sequence[str]) -> set[str]:
    """Infer authority contexts from exact declared candidate paths.

    Args:
        payload: Current repository authority map.
        paths: Exact proposal-declared paths.
    """

    matches = set(str(item) for item in payload.get("always_contexts", []))
    normalized = [normalize(path) for path in paths]
    for context in payload.get("contexts", []):
        if not isinstance(context, Mapping):
            raise BootstrapError("authority context is not an object")
        prefixes = [normalize(str(item)) for item in context.get("path_prefixes", [])]
        if any(path.startswith(prefix) for path in normalized for prefix in prefixes if prefix):
            matches.add(str(context.get("id", "")))
    return expand_context_dependencies(payload, matches)


def expand_context_dependencies(
    payload: Mapping[str, Any],
    selected: set[str],
) -> set[str]:
    """Expand repository-owned context dependencies.

    Args:
        payload: Current repository authority map.
        selected: Initially inferred context identifiers.
    """

    contexts = {str(item["id"]): item for item in payload.get("contexts", [])}
    expanded = set(selected)
    while True:
        before = set(expanded)
        for context_id in tuple(expanded):
            if context_id not in contexts:
                raise BootstrapError(f"unknown authority context: {context_id}")
            expanded.update(str(item) for item in contexts[context_id].get("requires", []))
        if before == expanded:
            return expanded


def parse_validation_command(command: str) -> tuple[str, ...]:
    """Parse one shell-free repository validation command.

    Args:
        command: Repository-owned validation command string.
    """

    argv = tuple(shlex.split(command, posix=True))
    if len(argv) == 2 and argv[0] == "make" and argv[1]:
        return argv
    if len(argv) >= 2 and argv[0] == "python3":
        script = PurePosixPath(argv[1])
        if not script.is_absolute() and ".." not in script.parts and script.suffix == ".py":
            return argv
    raise BootstrapError(f"unsupported baseline validation command: {command!r}")


def baseline_entries(repo: Path, paths: Sequence[str]) -> tuple[BaselineEntry, ...]:
    """Derive deduplicated baseline commands from current authority.

    Args:
        repo: Exact target repository checkout.
        paths: Exact proposal-declared paths.
    """

    authority = load_json(repo / "sage-change-authority.json")
    selected = inferred_context_ids(authority, paths)
    contexts = [item for item in authority["contexts"] if str(item["id"]) in selected]
    contexts.sort(key=lambda item: (int(item["priority"]), str(item["id"])))
    return deduplicate_baseline_entries(repo, contexts)


def deduplicate_baseline_entries(
    repo: Path,
    contexts: Sequence[Mapping[str, Any]],
) -> tuple[BaselineEntry, ...]:
    """Build one ordered baseline plan from selected contexts.

    Args:
        repo: Exact target repository checkout.
        contexts: Selected repository-owned authority contexts.
    """

    result: list[BaselineEntry] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for context in contexts:
        cwd = (repo / str(context["working_directory"])).resolve()
        cwd.relative_to(repo)
        for command in context["baseline_checks"]:
            argv = parse_validation_command(str(command))
            key = (str(cwd), argv)
            if key not in seen:
                result.append(BaselineEntry(str(context["id"]), cwd, str(command), argv))
                seen.add(key)
    return tuple(result)


def is_deferred_failure(entry: BaselineEntry, output: str) -> bool:
    """Return whether one failure is exactly the authorized starting-state defect.

    Args:
        entry: Failed baseline command identity.
        output: Combined command output.
    """

    if entry.context_id != FAILURE_CONTEXT:
        return False
    if entry.argv != FAILURE_COMMAND or entry.cwd.as_posix().endswith(FAILURE_CWD) is False:
        return False
    return all(marker in output for marker in FAILURE_MARKERS)


def validate_baseline_observations(
    observations: Sequence[BaselineObservation],
) -> BaselineObservation:
    """Allow exactly one concrete contribution-bound starting-state failure.

    Args:
        observations: Complete pre-stage baseline observations.
    """

    failures = [item for item in observations if item.returncode != 0]
    if len(failures) != 1:
        raise BootstrapError("pre-stage baseline must have exactly one deferred failure")
    failure = failures[0]
    if not is_deferred_failure(failure.entry, failure.stdout + failure.stderr):
        raise BootstrapError("pre-stage baseline failure is unrelated or unproven")
    return failure


def require_controller_origin(origin: str, phase: str) -> None:
    """Prevent candidate control code from becoming transaction authority.

    Args:
        origin: Controller source classification.
        phase: Activation phase name.
    """

    if phase != "post-stage-validation" and origin != "trusted-controller-checkout":
        raise BootstrapError("candidate control code cannot be pre-validation authority")


def require_git_continuation_receipts(
    validation: Sequence[Mapping[str, Any]],
    authority_path: Path | None,
    component_path: Path | None,
    gap_path: Path | None,
) -> None:
    """Require pass-only receipts before emitting the Git continuation.

    Args:
        validation: Validation receipt mappings.
        authority_path: Authority receipt path.
        component_path: Component selection receipt path.
        gap_path: Capability-gap receipt path.
    """

    if not validation or any(item.get("status") != "pass" for item in validation):
        raise BootstrapError("Git continuation requires pass-only validation receipts")
    receipt_paths = (authority_path, component_path, gap_path)
    if any(path is None or not path.is_file() for path in receipt_paths):
        raise BootstrapError("Git continuation requires authority/component/gap receipts")


def require_post_stage_baseline(status: str) -> None:
    """Require the deferred baseline to be resolved after staging.

    Args:
        status: Observed post-stage baseline status.
    """

    if status != "pass":
        raise BootstrapError("post-stage deferred baseline must pass")


def rollback_closeout_status(recovery: Mapping[str, Any]) -> str:
    """Classify rollback outcome without inferring success.

    Args:
        recovery: Repository rollback verification evidence.
    """

    if recovery.get("transaction_started") is not True:
        return "failed-pre-mutation"
    if recovery.get("rollback_verified") is True:
        return "failed-rolled-back"
    return "failed-rollback-unverified"


def verify_written_candidate(repo: Path, bundle: Any) -> None:
    """Verify exact staged bytes, modes, and scope after atomic writes.

    Args:
        repo: Target repository checkout.
        bundle: Exact validated proposal bundle.
    """

    for item in bundle.source_files:
        path = repo / item.path
        if sha256_file(path) != item.sha256:
            raise BootstrapError(f"staged candidate digest drifted: {item.path}")
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != item.mode:
            raise BootstrapError(f"staged candidate mode drifted: {item.path}")


def stable_json(value: Mapping[str, Any]) -> str:
    """Render deterministic repository-style JSON.

    Args:
        value: JSON object to render.
    """

    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def controller_root() -> Path:
    """Return the trusted controller checkout root."""

    return Path(__file__).resolve().parents[2]


def import_trusted_request_execution() -> Any:
    """Import request-execution controller code from this trusted checkout."""

    verify_controller_trust_root()
    sage_dir = controller_root() / "scripts" / "sage"
    sys.path.insert(0, str(sage_dir))
    from workflows import request_execution as trusted  # pylint: disable=import-outside-toplevel

    return trusted


def run_pre_stage_baseline(context: Any, trusted: Any) -> BaselineObservation:
    """Run every current baseline command and return the sole deferred failure.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
    """

    entries = baseline_entries(context.repo, context.bundle.declared_paths)
    observations = [run_baseline_entry(context, trusted, entry) for entry in entries]
    return validate_baseline_observations(observations)


def run_baseline_entry(context: Any, trusted: Any, entry: BaselineEntry) -> BaselineObservation:
    """Run one baseline command while preserving expected failure evidence.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
        entry: Baseline command to run.
    """

    result = context.runner.run(
        trusted.CommandSpec(
            primitive_id="validation.plan",
            label=f"bootstrap baseline [{entry.context_id}]: {entry.command_text}",
            argv=entry.argv,
            cwd=entry.cwd,
            timeout_seconds=3600,
            expected_codes=(0, 1, 2),
        ),
        step_id=(
            f"bootstrap-baseline-{entry.context_id}-"
            f"{sha256_bytes(entry.command_text.encode())[:12]}"
        ),
    )
    return BaselineObservation(
        entry=entry,
        returncode=result.returncode,
        output_sha256=result.output_sha256,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def verify_target_authority(context: Any) -> None:
    """Reverify exact target branch/HEAD/scope immediately before writes.

    Args:
        context: Trusted request-execution context.
    """

    context.inspector.require_clean()
    context.inspector.require_branch(EXPECTED_BRANCH)
    context.inspector.require_head(EXPECTED_HEAD)
    snapshot = context.inspector.snapshot()
    require_authority_snapshot(snapshot.branch, snapshot.head, True)


def stage_exact_candidate(context: Any, trusted: Any) -> dict[str, str]:
    """Atomically stage only the exact checksum-bound candidate scope.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
    """

    paths = tuple(context.repo / item for item in context.bundle.declared_paths)
    context.transaction = trusted.AtomicFileTransaction(context.writer, paths)
    digests: dict[str, str] = {}
    for item in context.bundle.source_files:
        digest = context.transaction.write_bytes(
            context.repo / item.path,
            item.payload,
            new_mode=item.mode,
        )
        if digest != item.sha256:
            raise BootstrapError(f"atomic write digest mismatch: {item.path}")
        digests[item.path] = digest
    context.inspector.require_exact_paths(context.bundle.declared_paths)
    verify_written_candidate(context.repo, context.bundle)
    return digests


def run_post_stage_baseline(context: Any, trusted: Any) -> dict[str, Any]:
    """Require the exact deferred command and complete baseline to pass post-stage.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
    """

    entry = next(
        item
        for item in baseline_entries(context.repo, context.bundle.declared_paths)
        if item.context_id == FAILURE_CONTEXT and item.argv == FAILURE_COMMAND
    )
    result = trusted.ValidationPlan(
        entry.cwd,
        context.runner,
        (trusted.ValidationCommand("Resolve exact deferred baseline", entry.argv, 3600.0),),
    ).run()[0]
    require_post_stage_baseline("pass")
    full = trusted.context_policy_validation(context, field="baseline")
    return {
        "label": "Context-derived baseline validation",
        "reference": "sage-change-authority.json",
        "status": "pass",
        "deferred_command_sha256": result.output_sha256,
        "sha256": full["sha256"],
    }


def write_bootstrap_receipt(
    context: Any,
    trusted: Any,
    status: str,
    details: Mapping[str, Any],
) -> Path:
    """Write deterministic local bootstrap evidence.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
        status: Bootstrap outcome status.
        details: Outcome details.
    """

    payload = {
        "schema_version": "1.0",
        "record_type": "sage-request-bootstrap-activation",
        "objective_id": OBJECTIVE_ID,
        "status": status,
        "bindings": fixed_bindings(),
        "details": dict(details),
        "deployment_or_runtime_success_claimed": False,
        "git_mutation_performed": False,
    }
    return trusted.write_state(context, "bootstrap-activation-receipt.json", payload)


def fixed_bindings() -> dict[str, Any]:
    """Return the immutable one-time bootstrap authority bindings."""

    return {
        "branch": EXPECTED_BRANCH,
        "head": EXPECTED_HEAD,
        "request_sha256": EXPECTED_REQUEST_SHA256,
        "proposal_sha256": EXPECTED_PROPOSAL_SHA256,
        "contribution_sha256": EXPECTED_CONTRIBUTION_SHA256,
        "architect_intent_sha256": EXPECTED_ARCHITECT_INTENT_SHA256,
        "objective_path_decision_sha256": EXPECTED_OBJECTIVE_DECISION_SHA256,
        "source_signature": [
            {"path": path, "sha256": digest, "mode": f"{mode:04o}"}
            for path, digest, mode in EXPECTED_SOURCE_SIGNATURE
        ],
    }


def prepare_context(args: argparse.Namespace, trusted: Any) -> tuple[Any, str]:
    """Build and fully bind the trusted request-execution context.

    Args:
        args: Parsed activation CLI arguments.
        trusted: Preloaded trusted request-execution module.
    """

    repo = args.repo.expanduser().resolve()
    request = request_from_state(args.request_state.expanduser().resolve())
    verify_architect_authority(args.architect_intent, args.objective_decision)
    verify_target_trust_root(repo)
    require_controller_origin("trusted-controller-checkout", "pre-stage")
    require_digest(args.proposal, EXPECTED_PROPOSAL_SHA256, "request proposal")
    context = trusted.build_context(repo, request, args.proposal.expanduser().resolve())
    verify_proposal_bundle(context.bundle, args.proposal)
    verify_contribution(args.contribution, context.bundle)
    return context, request


def run_pre_mutation_actions(context: Any, trusted: Any, decision: Path) -> None:
    """Run unchanged authority, selection, safety, and gap gates pre-mutation.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
        decision: Exact Architect-approved objective path decision.
    """

    os.environ[trusted.OBJECTIVE_PATH_DECISION_ENV] = str(decision.resolve())
    trusted.discovery_action(context)
    trusted.git_action(context)
    trusted.authority_action(context)
    trusted.selection_action(context)
    trusted.gap_action(context)
    trusted.capture_python_safety_baseline(context)
    trusted.validate_python_payloads(context)


def run_post_mutation_actions(context: Any, trusted: Any) -> Mapping[str, Any]:
    """Run unchanged hard validation and emit only the existing Git boundary.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
    """

    context.context_baseline_validation = run_post_stage_baseline(context, trusted)
    trusted.validation_action(context)
    trusted.safety_action(context)
    require_git_continuation_receipts(
        context.validation,
        context.authority_path,
        context.component_path,
        context.gap_path,
    )
    return trusted.proposal_action(context)


def activation_success(
    context: Any,
    trusted: Any,
    proposal_payload: Mapping[str, Any],
    pre_failure: BaselineObservation,
) -> Mapping[str, Any]:
    """Commit repository content and persist pass-only continuation evidence.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
        proposal_payload: Existing governed Git boundary.
        pre_failure: Exact deferred starting-state observation.
    """

    if context.transaction is None or context.proposal_path is None:
        raise BootstrapError("successful bootstrap lacks transaction or Git boundary")
    context.transaction.commit()
    state = trusted.write_execution_state(context, proposal_payload)
    receipt = write_bootstrap_receipt(
        context,
        trusted,
        "operator-review-required",
        {
            "deferred_baseline_output_sha256": pre_failure.output_sha256,
            "operator_proposal": str(context.proposal_path),
            "request_execution_state": str(state),
            "validation": list(context.validation),
        },
    )
    trusted.write_closeout(
        context,
        "operator-review-required",
        {
            "bootstrap_receipt": str(receipt),
            "proposal": str(context.proposal_path),
            "state": str(state),
        },
    )
    return {
        "status": "operator-review-required",
        "proposal": str(context.proposal_path),
        "state": str(state),
        "receipt": str(receipt),
    }


def activation_failure(context: Any, trusted: Any, error: Exception) -> None:
    """Rollback and independently verify original target authority on failure.

    Args:
        context: Trusted request-execution context.
        trusted: Preloaded trusted request-execution module.
        error: Activation exception.
    """

    recovery = trusted.recover_repository_after_failure(context)
    status = rollback_closeout_status(recovery)
    receipt = write_bootstrap_receipt(
        context,
        trusted,
        status,
        {"error": f"{type(error).__name__}: {error}", "recovery": dict(recovery)},
    )
    trusted.write_closeout(
        context,
        status,
        {"bootstrap_receipt": str(receipt), "recovery": dict(recovery)},
    )
    if (
        recovery.get("transaction_started") is True
        and recovery.get("rollback_verified") is not True
    ):
        raise BootstrapError("bootstrap rollback could not be independently verified") from error


def activate(args: argparse.Namespace) -> Mapping[str, Any]:
    """Execute the one exact bootstrap activation composition.

    Args:
        args: Parsed activation CLI arguments.
    """

    trusted = import_trusted_request_execution()
    context, _request = prepare_context(args, trusted)
    try:
        run_pre_mutation_actions(context, trusted, args.objective_decision)
        verify_target_authority(context)
        pre_failure = run_pre_stage_baseline(context, trusted)
        verify_target_authority(context)
        verify_proposal_bundle(context.bundle, args.proposal)
        verify_contribution(args.contribution, context.bundle)
        stage_exact_candidate(context, trusted)
        proposal_payload = run_post_mutation_actions(context, trusted)
        return activation_success(context, trusted, proposal_payload, pre_failure)
    except Exception as error:
        activation_failure(context, trusted, error)
        raise


def expect_failure(action: Any, fragment: str) -> None:
    """Require one deterministic negative self-test failure.

    Args:
        action: Zero-argument callable expected to fail.
        fragment: Required failure-text fragment.
    """

    try:
        action()
    except BootstrapError as error:
        if fragment not in str(error):
            raise RuntimeError(f"unexpected self-test failure: {error}") from error
    else:
        raise RuntimeError(f"expected bootstrap rejection containing {fragment!r}")


def fixture_entry(context_id: str, argv: tuple[str, ...]) -> BaselineEntry:
    """Build one deterministic self-test baseline entry.

    Args:
        context_id: Fixture context identity.
        argv: Fixture command argv.
    """

    cwd = Path("/fixture") / FAILURE_CWD
    return BaselineEntry(context_id, cwd, " ".join(argv), argv)


def fixture_observation(
    context_id: str,
    argv: tuple[str, ...],
    returncode: int,
    output: str,
) -> BaselineObservation:
    """Build one deterministic self-test baseline observation.

    Args:
        context_id: Fixture context identity.
        argv: Fixture command argv.
        returncode: Fixture return code.
        output: Fixture standard output.
    """

    entry = fixture_entry(context_id, argv)
    return BaselineObservation(entry, returncode, sha256_bytes(output.encode()), output, "")


def run_self_test() -> None:
    """Run deterministic positive and negative bootstrap authority tests."""

    expect_failure(
        lambda: require_authority_snapshot("other", EXPECTED_HEAD, True),
        "authority drifted",
    )
    expect_failure(
        lambda: require_authority_snapshot(EXPECTED_BRANCH, "0" * 40, True),
        "authority drifted",
    )
    expect_failure(
        lambda: require_authority_snapshot(EXPECTED_BRANCH, EXPECTED_HEAD, False),
        "must be clean",
    )
    expect_failure(
        lambda: require_controller_origin("candidate-package", "pre-stage"),
        "cannot be pre-validation authority",
    )
    unrelated = [
        fixture_observation(
            "repository-governance",
            ("make", "sage-self-test"),
            2,
            "failure",
        )
    ]
    expect_failure(lambda: validate_baseline_observations(unrelated), "unrelated or unproven")
    markers = "\n".join(FAILURE_MARKERS)
    authorized = [fixture_observation(FAILURE_CONTEXT, FAILURE_COMMAND, 2, markers)]
    deferred = validate_baseline_observations(authorized)
    if deferred.entry.argv != FAILURE_COMMAND:
        raise RuntimeError("authorized deferred baseline identity changed")
    expect_failure(
        lambda: require_git_continuation_receipts(
            [{"status": "failed"}], Path("/x"), Path("/y"), Path("/z")
        ),
        "pass-only",
    )
    test_signature_guards()
    test_post_stage_and_rollback_guards()
    print("SAGE request bootstrap activation self-test: PASS")


def test_signature_guards() -> None:
    """Exercise proposal/contribution scope, digest, and mode drift guards."""

    altered = list(EXPECTED_SOURCE_SIGNATURE)
    altered[0] = (altered[0][0], "0" * 64, altered[0][2])
    expect_failure(
        lambda: require_source_signature(altered, "proposal"),
        "signature drifted",
    )
    altered = list(EXPECTED_SOURCE_SIGNATURE)
    altered[0] = (altered[0][0] + ".extra", altered[0][1], altered[0][2])
    expect_failure(
        lambda: require_source_signature(altered, "proposal"),
        "signature drifted",
    )
    altered = list(EXPECTED_SOURCE_SIGNATURE)
    altered[0] = (altered[0][0], altered[0][1], 0o755)
    expect_failure(
        lambda: require_source_signature(altered, "proposal"),
        "signature drifted",
    )
    expect_failure(
        lambda: require_digest(Path(__file__), "0" * 64, "proposal"),
        "digest drifted",
    )
    expect_failure(
        lambda: require_digest(Path(__file__), "f" * 64, "contribution"),
        "digest drifted",
    )


def test_post_stage_and_rollback_guards() -> None:
    """Exercise post-stage baseline, validation, and rollback guards."""

    require_post_stage_baseline("pass")
    expect_failure(
        lambda: require_post_stage_baseline("failed"),
        "must pass",
    )
    expect_failure(
        lambda: require_git_continuation_receipts(
            [{"status": "candidate-correction-pending"}], None, None, None
        ),
        "pass-only",
    )
    expect_failure(
        lambda: require_git_continuation_receipts(
            [{"status": "pass"}], None, None, None
        ),
        "authority/component/gap receipts",
    )
    recovery = {"transaction_started": True, "rollback_verified": True}
    if rollback_closeout_status(recovery) != "failed-rolled-back":
        raise RuntimeError("verified rollback classification changed")
    failed = {"transaction_started": True, "rollback_verified": False}
    if rollback_closeout_status(failed) != "failed-rollback-unverified":
        raise RuntimeError("unverified rollback classification changed")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    """Parse activation CLI arguments.

    Args:
        argv: Command-line arguments excluding program name.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--request-state", type=Path)
    parser.add_argument("--proposal", type=Path)
    parser.add_argument("--contribution", type=Path)
    parser.add_argument("--architect-intent", type=Path)
    parser.add_argument("--objective-decision", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    required = (
        "request_state",
        "proposal",
        "contribution",
        "architect_intent",
        "objective_decision",
    )
    if not args.self_test and any(getattr(args, name) is None for name in required):
        parser.error(
            "activation requires request-state, proposal, contribution, "
            "architect-intent, and objective-decision"
        )
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run self-test or one exact activation.

    Args:
        argv: Optional CLI argument sequence.
    """

    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    if args.self_test:
        run_self_test()
        return 0
    result = activate(args)
    print(stable_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
