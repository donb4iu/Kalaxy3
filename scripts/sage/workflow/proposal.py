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
_BOUNDARY_COMMANDS = {
    "create-branch": ("git", "switch"),
    "switch-branch": ("git", "switch"),
    "stage": ("git", "add"),
    "commit": ("git", "commit"),
    "push": ("git", "push"),
    "pull-request-create": ("gh", "pr", "create"),
    "pull-request-merge": ("gh", "pr", "merge"),
    "branch-delete": ("git", "branch"),
    "tag": ("git", "tag"),
    "other-git-mutation": ("git",),
}
_SECRET_NAMES = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
}


class OperatorGitProposal:
    """Build and optionally write a proposal without executing its command."""

    @staticmethod
    def _validate_command(
        boundary: str,
        argv: tuple[str, ...],
    ) -> None:
        if boundary not in _BOUNDARY_COMMANDS:
            raise WorkflowError(f"Unsupported mutation boundary: {boundary}")
        if len(argv) < 2:
            raise WorkflowError("Proposal command must contain at least two arguments")
        prefix = _BOUNDARY_COMMANDS[boundary]
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
    def _command_payload(argv: tuple[str, ...]) -> dict[str, object]:
        digest_input = json.dumps(
            list(argv),
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return {
            "display": shlex.join(argv),
            "argv": list(argv),
            "sha256": hashlib.sha256(digest_input).hexdigest(),
            "contains_secret": False,
            "command_count": 1,
            "executed_by_helper": False,
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
        if not _PROPOSAL_ID.fullmatch(proposal_id):
            raise WorkflowError(f"Invalid proposal_id: {proposal_id}")
        argv = tuple(command_argv)
        cls._validate_command(boundary, argv)
        scope = tuple(dict.fromkeys(change_scope))
        checks = tuple(dict(item) for item in validation)
        verification = tuple(post_command_verification)
        if not scope:
            raise WorkflowError("change_scope must not be empty")
        if not checks:
            raise WorkflowError("validation must not be empty")
        if not verification:
            raise WorkflowError("post_command_verification must not be empty")
        for check in checks:
            if check.get("status") != "pass":
                raise WorkflowError("All proposal validation entries must pass")
            if not check.get("label") or not check.get("reference"):
                raise WorkflowError("Validation entries require label and reference")
            digest = check.get("sha256")
            if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", str(digest)):
                raise WorkflowError("Validation sha256 must be null or 64 lowercase hex")

        timestamp = created_at or datetime.now().astimezone().isoformat(timespec="seconds")
        return {
            "schema_version": "1.0",
            "proposal_id": proposal_id,
            "created_at": timestamp,
            "controller": controller,
            "repository": {
                "path": repository.path,
                "branch": repository.branch,
                "head": repository.head,
                "upstream_head": repository.upstream_head,
                "working_tree_status": repository.working_tree_status,
            },
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

    @staticmethod
    def write(
        destination: Path,
        payload: Mapping[str, object],
        writer: AtomicFileWriter,
    ) -> str:
        if payload.get("command", {}).get("executed_by_helper") is not False:  # type: ignore[union-attr]
            raise WorkflowError("Proposal must declare executed_by_helper=false")
        text = json.dumps(payload, indent=4, sort_keys=False) + "\n"
        return writer.write_text(destination, text, new_mode=0o644)
