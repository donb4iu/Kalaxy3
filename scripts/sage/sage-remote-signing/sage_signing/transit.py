"""OpenBao Transit RSA signing via narrowly scoped Kubernetes authentication."""

import base64
import re
from typing import Any

import requests

from sage_signing.config import Settings


class TransitSigner:
    """Request signatures only through a private TLS-protected OpenBao endpoint."""

    def __init__(self, settings: Settings) -> None:
        """Store validated connection parameters.

        Args:
            settings: Cloudflare/OpenBao configuration.
        """
        self.settings = settings

    def sign(self, value: bytes) -> tuple[str, int]:
        """Sign exact source bytes and return raw signature Base64 and key version.

        Args:
            value: Exact bytes required by the independently verified receipt.
        """
        jwt_text = self.settings.sa_token_file.read_text(encoding="utf-8").strip()
        if not jwt_text:
            raise RuntimeError("Kubernetes service account token missing")
        auth = self._post(
            "/v1/auth/kubernetes/login",
            {"role": self.settings.bao_role, "jwt": jwt_text}, None,
        )
        token = auth.get("auth", {}).get("client_token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("OpenBao Kubernetes login failed")
        payload: dict[str, Any] = {
            "input": base64.b64encode(value).decode("ascii"),
            "prehashed": False,
            "signature_algorithm": self.settings.padding,
        }
        if self.settings.padding == "pss":
            payload["salt_length"] = "hash"
        path = f"/v1/transit/sign/{self.settings.bao_key}/sha2-256"
        response = self._post(path, payload, token)
        signature = response.get("data", {}).get("signature", "")
        match = re.fullmatch(r"vault:v([1-9][0-9]*):([A-Za-z0-9+/=]+)", signature)
        if match is None:
            raise RuntimeError("Unrecognized OpenBao signature envelope")
        raw = base64.b64decode(match.group(2), validate=True)
        if len(raw) != 384:
            raise RuntimeError("Expected 3072-bit RSA signature")
        return base64.b64encode(raw).decode("ascii"), int(match.group(1))

    def _post(self, path: str, body: dict[str, Any], token: str | None) -> dict[str, Any]:
        """Send bounded TLS HTTP request, without logging credentials.

        Args:
            path: Fixed internal OpenBao API route.
            body: Transit or Kubernetes authentication request.
            token: Short-lived OpenBao token or None for Kubernetes login.
        """
        headers = {"X-Vault-Token": token} if token else {}
        response = requests.post(
            self.settings.bao_url + path, json=body, headers=headers,
            verify=self.settings.bao_ca, timeout=(3, 8),
        )
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise RuntimeError("Malformed OpenBao response")
        return result
