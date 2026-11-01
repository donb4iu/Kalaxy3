"""Resolve SAGE Projects credentials only inside trusted execution processes.

LLM participants receive work-item data and receipts, never credential objects.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Mapping


class ProjectsCredentialError(RuntimeError):
    """Describe credential unavailability without exposing secret material."""


def resolve_projects_token(source: str, environment: Mapping[str, str]) -> str:
    """Resolve one governed credential from an Actions secret or Vault projection.

    Args:
        source: ``actions-secret`` or ``vault-file``.
        environment: Trusted executor's explicitly supplied environment.
    """
    if source == "actions-secret":
        if environment.get("GITHUB_ACTIONS") != "true":
            raise ProjectsCredentialError("Actions credential requires Actions runtime")
        token = environment.get("SAGE_PROJECTS_CREDENTIAL", "")
    elif source == "vault-file":
        filename = environment.get("SAGE_PROJECTS_VAULT_FILE", "")
        if not filename:
            raise ProjectsCredentialError("Vault-projected file reference required")
        path = Path(filename)
        if not path.is_absolute() or path.is_symlink():
            raise ProjectsCredentialError("Vault file path must be absolute and not a symlink")
        try:
            metadata = path.stat()
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
                raise ProjectsCredentialError("Vault file permissions must be private")
            token = path.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            raise ProjectsCredentialError("Vault credential file unavailable") from None
    else:
        raise ProjectsCredentialError("Unapproved credential source")
    if not token or any(char in token for char in "\r\n\x00"):
        raise ProjectsCredentialError("Missing or malformed Projects credential")
    return token
