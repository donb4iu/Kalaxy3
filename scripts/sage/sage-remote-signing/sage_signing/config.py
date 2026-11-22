"""Validated, fail-closed SAGE signing controller configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    """Immutable Cloudflare Access and OpenBao signing parameters."""

    team_domain: str
    audience: str
    signer_email: str
    signer_role: str
    bao_url: str
    bao_role: str
    bao_key: str
    bao_ca: str
    sa_token_file: Path
    db_path: Path
    padding: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        """Read mandatory settings without permissive defaults.

        Args:
            env: Optional environment mapping for tests or deployment.
        """
        source = os.environ if env is None else env
        names = (
            "CF_TEAM_DOMAIN", "CF_ACCESS_AUD", "SAGE_SIGNER_EMAIL", "SAGE_SIGNER_ROLE",
            "BAO_ADDR", "BAO_K8S_ROLE", "BAO_SIGN_KEY", "BAO_CA_BUNDLE",
            "BAO_SA_TOKEN_FILE", "SAGE_SIGN_DB", "SAGE_RSA_PADDING",
        )
        values = {name: source.get(name, "").strip() for name in names}
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError("Missing mandatory settings: " + ", ".join(missing))
        team = values["CF_TEAM_DOMAIN"].rstrip("/")
        bao = values["BAO_ADDR"].rstrip("/")
        if not _is_https_origin(team) or not _is_https_origin(bao):
            raise ValueError("Cloudflare and OpenBao must be HTTPS origins")
        padding = values["SAGE_RSA_PADDING"]
        if values["SAGE_SIGNER_ROLE"] not in {"architect", "auditor"}:
            raise ValueError("SAGE_SIGNER_ROLE must be architect or auditor")
        if padding != "pkcs1v15":
            raise ValueError("PR #61 requires RSA PKCS#1 v1.5 with SHA-256")
        if "/" in values["BAO_SIGN_KEY"] or "/" in values["BAO_K8S_ROLE"]:
            raise ValueError("OpenBao role and signing key must be simple names")
        return cls(
            team, values["CF_ACCESS_AUD"],
            values["SAGE_SIGNER_EMAIL"].casefold(),
            values["SAGE_SIGNER_ROLE"], bao,
            values["BAO_K8S_ROLE"], values["BAO_SIGN_KEY"],
            values["BAO_CA_BUNDLE"], Path(values["BAO_SA_TOKEN_FILE"]),
            Path(values["SAGE_SIGN_DB"]), padding,
        )


def _is_https_origin(value: str) -> bool:
    """Reject insecure or path-bearing remote origins.

    Args:
        value: Candidate scheme/host/port origin.
    """
    parsed = urlsplit(value)
    return bool(
        parsed.scheme == "https" and parsed.hostname and not parsed.username
        and not parsed.password and not parsed.path and not parsed.query
        and not parsed.fragment
    )
