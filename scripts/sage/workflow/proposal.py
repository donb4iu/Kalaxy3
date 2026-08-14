"""Operator-executed one-boundary Git and GitHub proposal primitive."""
from __future__ import annotations

import hashlib
import json
import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping

from .files import AtomicFileWriter
from .git_inspect import GitAuthoritySnapshot
from .model import WorkflowError

_PROPOSAL_ID = re.compile(r"^SAGE-GIT-[0-9]{8}-[0-9]{3}$")
_FORBIDDEN_TOKENS = ("\n", "\r", ";", "&&", "||", "`", "$(")
_COMMAND_BOUNDARIES = {
    "create-branch": ("git", "switch"),
    "switch-branch": ("git", "switch"),
    "stage": ("git", "add"),
    "commit": ("git", "commit"),
    "push": ("git", "push"),
    "routine-git-lifecycle": ("python3", "scripts/sage/sage-routine-git-lifecycle.py"),
    "branch-delete": ("git", "branch"),
    "tag": ("git", "tag"),
    "other-git-mutation": ("git",),
}
_BROWSER_BOUNDARIES = {
    "pull-request-create": "create-pull-request",
    "pull-request-merge": "merge-pull-request",
}
_SECRET_NAMES = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
}




def render_operator_command(argv: Iterable[str]) -> dict[str, object]:
    """Render one operator command through the canonical proposal serializer."""

    command = tuple(str(argument) for argument in argv)
    if not command:
        raise WorkflowError("Operator command must not be empty")
    digest_input = json.dumps(
        list(command),
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return {
        "display": shlex.join(command),
        "argv": list(command),
        "sha256": hashlib.sha256(digest_input).hexdigest(),
        "contains_secret": False,
        "command_count": 1,
        "executed_by_helper": False,
    }


class OperatorGitProposal:
    """Build and optionally write one operator boundary without executing it."""

    @staticmethod
    def _validate_command(
        boundary: str,
        argv: tuple[str, ...],
    ) -> None:
        if boundary in _BROWSER_BOUNDARIES:
            raise WorkflowError(
                f"{boundary} requires build_browser(); GitHub CLI proposals are prohibited"
            )
        if boundary not in _COMMAND_BOUNDARIES:
            raise WorkflowError(f"Unsupported mutation boundary: {boundary}")
        if len(argv) < 2:
            raise WorkflowError("Proposal command must contain at least two arguments")
        prefix = _COMMAND_BOUNDARIES[boundary]
        if argv[: len(prefix)] != prefix:
            raise WorkflowError(
                f"Command does not match boundary {boundary}: {argv}"
            )
        for argument in argv:
            if any(token in argument for token in _FORBIDDEN_TOKENS):
                raise WorkflowError(
                    f"Proposal command contains shell composition: {argument!r}"
                )
            upper = argument.upper()
            if any(name in upper for name in _SECRET_NAMES):
                raise WorkflowError(
                    "Proposal command must not contain credential names or values"
                )
        if boundary == "branch-delete" and "-d" not in argv and "-D" not in argv:
            raise WorkflowError("branch-delete proposal must declare -d or -D")

    @staticmethod
    def _validate_browser(
        boundary: str,
        action: str,
        url: str,
    ) -> None:
        expected_action = _BROWSER_BOUNDARIES.get(boundary)
        if expected_action is None:
            raise WorkflowError(
                f"Boundary {boundary} does not support browser review"
            )
        if action != expected_action:
            raise WorkflowError(
                f"Browser action does not match boundary {boundary}: {action}"
            )
        prefix = "https://github.com/"
        if (
            not url.startswith(prefix)
            or "#" in url
            or any(character.isspace() for character in url)
        ):
            raise WorkflowError(
                "Browser proposal must use an uncredentialed HTTPS GitHub browser URL"
            )
        remainder = url[len(prefix) :]
        path_only = remainder.split("?", 1)[0]
        segments = path_only.split("/")
        if len(segments) < 4 or not segments[0] or not segments[1]:
            raise WorkflowError("Browser proposal GitHub path is incomplete")
        upper = url.upper()
        if any(name in upper for name in _SECRET_NAMES):
            raise WorkflowError(
                "Browser proposal must not contain credential names or values"
            )

    @staticmethod
    def _validate_common(
        *,
        proposal_id: str,
        change_scope: Iterable[str],
        validation: Iterable[Mapping[str, object]],
        post_operator_verification: Iterable[str],
    ) -> tuple[tuple[str, ...], tuple[dict[str, object], ...], tuple[str, ...]]:
        if not _PROPOSAL_ID.fullmatch(proposal_id):
            raise WorkflowError(f"Invalid proposal_id: {proposal_id}")
        scope = tuple(dict.fromkeys(change_scope))
        checks = tuple(dict(item) for item in validation)
        verification = tuple(post_operator_verification)
        if not scope:
            raise WorkflowError("change_scope must not be empty")
        if not checks:
            raise WorkflowError("validation must not be empty")
        if not verification:
            raise WorkflowError("post-operator verification must not be empty")
        for check in checks:
            if check.get("status") != "pass":
                raise WorkflowError("All proposal validation entries must pass")
            if not check.get("label") or not check.get("reference"):
                raise WorkflowError("Validation entries require label and reference")
            digest = check.get("sha256")
            if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                raise WorkflowError("Validation sha256 must be null or 64 lowercase hex")
        return scope, checks, verification

    @staticmethod
    def _repository_payload(repository: GitAuthoritySnapshot) -> dict[str, object]:
        return {
            "path": repository.path,
            "branch": repository.branch,
            "head": repository.head,
            "upstream_head": repository.upstream_head,
            "working_tree_status": repository.working_tree_status,
        }

    @staticmethod
    def _command_payload(argv: tuple[str, ...]) -> dict[str, object]:
        return render_operator_command(argv)

    @staticmethod
    def _browser_payload(action: str, url: str) -> dict[str, object]:
        digest_input = json.dumps(
            {"action": action, "url": url},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return {
            "provider": "github-browser",
            "action": action,
            "url": url,
            "sha256": hashlib.sha256(digest_input).hexdigest(),
            "contains_secret": False,
            "opened_by_helper": False,
            "mutation_performed_by_helper": False,
        }

    @classmethod
    def build(
        cls,
        *,
        proposal_id: str,
        controller: str,
        repository: GitAuthoritySnapshot,
        authority_receipt: str,
        component_manifest: str,
        boundary: str,
        change_scope: Iterable[str],
        validation: Iterable[Mapping[str, object]],
        command_argv: Iterable[str],
        expected_result: str,
        risk: str,
        rollback: str,
        post_command_verification: Iterable[str],
        created_at: str | None = None,
    ) -> dict[str, object]:
        argv = tuple(command_argv)
        cls._validate_command(boundary, argv)
        scope, checks, verification = cls._validate_common(
            proposal_id=proposal_id,
            change_scope=change_scope,
            validation=validation,
            post_operator_verification=post_command_verification,
        )
        timestamp = created_at or datetime.now().astimezone().isoformat(timespec="seconds")
        return {
            "schema_version": "1.0",
            "proposal_id": proposal_id,
            "created_at": timestamp,
            "controller": controller,
            "repository": cls._repository_payload(repository),
            "authority_receipt": authority_receipt,
            "component_manifest": component_manifest,
            "boundary": boundary,
            "change_scope": list(scope),
            "validation": list(checks),
            "command": cls._command_payload(argv),
            "expected_result": expected_result,
            "risk": risk,
            "rollback": rollback,
            "post_command_verification": list(verification),
            "operator_contract": {
                "execution_mode": "operator-executed",
                "approval_required": True,
                "pasted_output_required": True,
                "next_boundary_blocked_until_verified": True,
            },
        }

    @classmethod
    def build_browser(
        cls,
        *,
        proposal_id: str,
        controller: str,
        repository: GitAuthoritySnapshot,
        authority_receipt: str,
        component_manifest: str,
        boundary: str,
        change_scope: Iterable[str],
        validation: Iterable[Mapping[str, object]],
        browser_action: str,
        browser_url: str,
        expected_result: str,
        risk: str,
        rollback: str,
        post_interaction_verification: Iterable[str],
        created_at: str | None = None,
    ) -> dict[str, object]:
        cls._validate_browser(boundary, browser_action, browser_url)
        scope, checks, verification = cls._validate_common(
            proposal_id=proposal_id,
            change_scope=change_scope,
            validation=validation,
            post_operator_verification=post_interaction_verification,
        )
        timestamp = created_at or datetime.now().astimezone().isoformat(timespec="seconds")
        return {
            "schema_version": "1.1",
            "proposal_id": proposal_id,
            "created_at": timestamp,
            "controller": controller,
            "repository": cls._repository_payload(repository),
            "authority_receipt": authority_receipt,
            "component_manifest": component_manifest,
            "boundary": boundary,
            "change_scope": list(scope),
            "validation": list(checks),
            "browser": cls._browser_payload(browser_action, browser_url),
            "expected_result": expected_result,
            "risk": risk,
            "rollback": rollback,
            "post_interaction_verification": list(verification),
            "operator_contract": {
                "execution_mode": "browser-review",
                "approval_required": True,
                "operator_confirmation_required": True,
                "pasted_output_required": False,
                "next_boundary_blocked_until_verified": True,
            },
        }

    @staticmethod
    def write(
        destination: Path,
        payload: Mapping[str, object],
        writer: AtomicFileWriter,
    ) -> str:
        schema_version = payload.get("schema_version")
        if schema_version == "1.0":
            command = payload.get("command")
            if (
                not isinstance(command, Mapping)
                or command.get("executed_by_helper") is not False
            ):
                raise WorkflowError("Command proposal must declare executed_by_helper=false")
        elif schema_version == "1.1":
            browser = payload.get("browser")
            if (
                not isinstance(browser, Mapping)
                or browser.get("opened_by_helper") is not False
                or browser.get("mutation_performed_by_helper") is not False
            ):
                raise WorkflowError(
                    "Browser proposal must remain operator-opened and operator-approved"
                )
        else:
            raise WorkflowError(f"Unsupported operator proposal schema: {schema_version}")
        text = json.dumps(payload, indent=4, sort_keys=False) + "\n"
        return writer.write_text(destination, text, new_mode=0o644)
