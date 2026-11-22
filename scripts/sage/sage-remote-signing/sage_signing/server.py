"""Minimal WSGI request approval and single-use OpenBao signing gateway."""

import base64
import binascii
import hashlib
import io
import json
import secrets
from typing import Callable, Iterable, Protocol
from wsgiref.types import WSGIEnvironment

from sage_signing.config import Settings
from sage_signing.receipt_policy import check_receipt
from sage_signing.identity import AccessIdentity
from sage_signing.store import Intent, IntentStore
from sage_signing.transit import TransitSigner


class Identity(Protocol):
    """Verify a Cloudflare application assertion."""

    def authenticate(self, assertion: str) -> str:
        """Return authenticated subject or raise PermissionError."""


class Signer(Protocol):
    """Sign exact bytes without revealing the private signing key."""

    def sign(self, value: bytes) -> tuple[str, int]:
        """Return Base64 signature and Transit key version."""


class SigningGateway:
    """Two-phase signing service: create intent, then explicit confirmation."""

    def __init__(self, identity: Identity, signer: Signer, store: IntentStore,
                 padding: str, signer_role: str) -> None:
        """Inject verifier, signer, and durable intent store.

        Args:
            identity: Authenticated Cloudflare Access verifier.
            signer: Restricted OpenBao Transit signer.
            store: One-time request-state database.
            padding: Verified receipt-compatible padding algorithm.
            signer_role: Isolated signer role under PR #61.
        """
        self.identity = identity
        self.signer = signer
        self.store = store
        self.padding = padding
        self.signer_role = signer_role

    def stage(self, subject: str, request: dict[str, object]) -> dict[str, object]:
        """Stage exact receipt bytes for later human confirmation.

        Args:
            subject: JWT-verified requester identity.
            request: Source bytes in Base64 plus a human-readable purpose.
        """
        import time
        purpose = request.get("purpose", "")
        encoded = request.get("receipt_bytes_b64", "")
        if not isinstance(purpose, str) or not (10 <= len(purpose) <= 200):
            raise ValueError("Purpose must be 10 to 200 characters")
        if not isinstance(encoded, str) or len(encoded) > 90000:
            raise ValueError("Invalid or oversized receipt")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Receipt must be valid Base64") from exc
        if not (1 <= len(data) <= 65536):
            raise ValueError("Receipt must contain 1-65536 bytes")
        receipt = check_receipt(data, self.signer_role)
        digest = hashlib.sha256(data).hexdigest()
        intent = Intent(secrets.token_urlsafe(24), subject, digest, data,
                        purpose, int(time.time()))
        self.store.stage(intent)
        return {"intent_id": intent.intent_id, "sha256": digest,
                "purpose": purpose, "signer_role": self.signer_role,
                "disposition": receipt["disposition"], "expires_in_seconds": 300}

    def approve(self, subject: str, request: dict[str, object]) -> dict[str, object]:
        """Consume a matching digest challenge and sign its exact bytes once.

        Args:
            subject: JWT-verified approval identity.
            request: Intent identifier and full confirmed hexadecimal digest.
        """
        intent_id = request.get("intent_id", "")
        digest = request.get("confirm_sha256", "")
        if not isinstance(intent_id, str) or len(intent_id) > 100:
            raise ValueError("Invalid intent identifier")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Invalid confirmation digest")
        intent = self.store.consume(intent_id, subject, digest)
        signature, version = self.signer.sign(intent.data)
        return {"intent_id": intent_id, "sha256": intent.digest,
                "signature_b64": signature, "key_version": version,
                "signature_algorithm": self.padding, "hash_algorithm": "sha2-256", "signer_role": self.signer_role}

    def __call__(self, environ: WSGIEnvironment,
                 start_response: Callable[..., object]) -> Iterable[bytes]:
        """Handle one request, rejecting missing assertion or invalid input.

        Args:
            environ: WSGI request environment.
            start_response: Server callback for HTTP response status/headers.
        """
        method, path = environ.get("REQUEST_METHOD"), environ.get("PATH_INFO")
        if method == "GET" and path == "/healthz":
            return _respond(start_response, "200 OK", {"status": "alive"})
        if method != "POST" or path not in {"/v1/intents", "/v1/approve"}:
            return _respond(start_response, "404 Not Found", {"error": "not_found"})
        try:
            subject = self.identity.authenticate(
                str(environ.get("HTTP_CF_ACCESS_JWT_ASSERTION", ""))
            )
            payload = _read_json(environ)
            if path == "/v1/intents":
                return _respond(start_response, "201 Created", self.stage(subject, payload))
            return _respond(start_response, "200 OK", self.approve(subject, payload))
        except PermissionError:
            return _respond(start_response, "403 Forbidden", {"error": "denied"})
        except (ValueError, KeyError, UnicodeError):
            return _respond(start_response, "400 Bad Request", {"error": "invalid_input"})
        except Exception:
            return _respond(start_response, "503 Service Unavailable", {"error": "unavailable"})


def _read_json(environ: WSGIEnvironment) -> dict[str, object]:
    """Bound input length and require JSON object payload.

    Args:
        environ: WSGI request environment.
    """
    size = int(environ.get("CONTENT_LENGTH", "-1"))
    if size < 2 or size > 100000:
        raise ValueError("Unexpected request size")
    content_type = str(environ.get("CONTENT_TYPE", ""))
    if content_type.split(";", 1)[0] != "application/json":
        raise ValueError("Expected application/json")
    stream = environ.get("wsgi.input", io.BytesIO())
    value = json.loads(stream.read(size))
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


def _respond(start_response: Callable[..., object], status: str,
             payload: dict[str, object]) -> Iterable[bytes]:
    """Serialize one no-store JSON response.

    Args:
        start_response: WSGI status callback.
        status: HTTP status line.
        payload: JSON-safe reply.
    """
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    start_response(status, [("Content-Type", "application/json"),
                            ("Content-Length", str(len(body))),
                            ("Cache-Control", "no-store")])
    return [body]


def make_application() -> SigningGateway:
    """Construct production WSGI app; refuse startup without complete settings."""
    settings = Settings.from_env()
    return SigningGateway(
        AccessIdentity(settings), TransitSigner(settings),
        IntentStore(settings.db_path), settings.padding, settings.signer_role,
    )
