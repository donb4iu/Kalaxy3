"""Cloudflare Access assertion validation, independent of request headers."""

from typing import Any

import jwt
from jwt import PyJWKClient

from sage_signing.config import Settings


class AccessIdentity:
    """Verify Cloudflare Access JWTs against pinned issuer and application AUD."""

    def __init__(self, settings: Settings) -> None:
        """Pin the issuer and certificate endpoint at initialization.

        Args:
            settings: Validated controller configuration.
        """
        self.settings = settings
        self.jwks = PyJWKClient(
            settings.team_domain + "/cdn-cgi/access/certs",
            cache_jwk_set=True, lifespan=300, timeout=5,
        )

    def authenticate(self, assertion: str) -> str:
        """Return an authorized subject or reject the access assertion.

        Args:
            assertion: Cloudflare Access application JWT, not a user header.
        """
        if not assertion or len(assertion) > 8192:
            raise PermissionError("Missing or oversized Cloudflare assertion")
        try:
            key = self.jwks.get_signing_key_from_jwt(assertion)
            claims: dict[str, Any] = jwt.decode(
                assertion, key.key, algorithms=["RS256"],
                audience=self.settings.audience, issuer=self.settings.team_domain,
                options={"require": ["exp", "iat", "iss", "aud", "sub", "email"]},
                leeway=15,
            )
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise PermissionError("Cloudflare assertion rejected") from exc
        email = claims.get("email")
        subject = claims.get("sub")
        if not isinstance(email, str) or email.casefold() != self.settings.signer_email:
            raise PermissionError("Signer identity not authorized")
        if not isinstance(subject, str) or not subject:
            raise PermissionError("Missing authenticated subject")
        return subject
