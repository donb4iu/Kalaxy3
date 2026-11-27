"""Regression tests for fail-closed access, one-time approval, and OpenBao signing."""

import base64
import hashlib
import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from sage_signing.config import Settings
from sage_signing.identity import AccessIdentity
from sage_signing.server import SigningGateway
from sage_signing.store import IntentStore
from sage_signing.transit import TransitSigner


class FakeIdentity:
    """Inject a known authenticated subject into isolated gateway tests."""

    def authenticate(self, assertion: str) -> str:
        """Accept only one explicit fake assertion.

        Args:
            assertion: Test-only assertion value.
        """
        if assertion != "good-access-token":
            raise PermissionError("Access denied")
        return "architect-test-subject"


class FakeSigner:
    """Track successful signing calls without external key custody."""

    def __init__(self) -> None:
        """Initialize observed signature invocations."""
        self.calls: list[bytes] = []

    def sign(self, value: bytes) -> tuple[str, int]:
        """Return deterministic fake signature for a passed value.

        Args:
            value: Bytes submitted to the signing backend.
        """
        self.calls.append(value)
        return base64.b64encode(b"s" * 384).decode("ascii"), 1


def settings(tmp: Path) -> Settings:
    """Construct fully explicit test settings.

    Args:
        tmp: Disposable state directory.
    """
    return Settings.from_env({
        "CF_TEAM_DOMAIN": "https://example.cloudflareaccess.com",
        "CF_ACCESS_AUD": "test-aud", "SAGE_SIGNER_EMAIL": "arch@example.com",
        "SAGE_SIGNER_ROLE": "architect",
        "BAO_ADDR": "https://openbao.svc.example",
        "BAO_K8S_ROLE": "sage-architect", "BAO_SIGN_KEY": "sage-architect",
        "BAO_CA_BUNDLE": str(tmp / "ca.pem"),
        "BAO_SA_TOKEN_FILE": str(tmp / "k8s.jwt"),
        "SAGE_SIGN_DB": str(tmp / "state.db"),
        "SAGE_RSA_PADDING": "pkcs1v15",
    })


def call_app(app: SigningGateway, path: str, payload: dict[str, Any],
             assertion: str = "good-access-token") -> tuple[str, dict[str, Any]]:
    """Send one synthetic WSGI request without a network listener.

    Args:
        app: Gateway to exercise.
        path: Requested route.
        payload: JSON body.
        assertion: Supplied test Access assertion.
    """
    body = json.dumps(payload).encode("utf-8")
    environ = {
        "REQUEST_METHOD": "POST", "PATH_INFO": path,
        "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(body)),
        "HTTP_CF_ACCESS_JWT_ASSERTION": assertion, "wsgi.input": io.BytesIO(body),
    }
    status: list[str] = []

    def start_response(value: str, headers: list[tuple[str, str]]) -> None:
        """Capture WSGI response metadata.

        Args:
            value: HTTP status line.
            headers: Response headers.
        """
        status.append(value)

    data = b"".join(app(environ, start_response))
    return status[0], json.loads(data)


class GatewayTests(unittest.TestCase):
    """Test approval binding and replay denial across a persistent store."""

    def setUp(self) -> None:
        """Create an isolated signing controller and database."""
        self.temp = tempfile.TemporaryDirectory()
        self.signer = FakeSigner()
        store = IntentStore(Path(self.temp.name) / "state.db")
        self.app = SigningGateway(FakeIdentity(), self.signer, store, "pkcs1v15", "architect")
        self.data = (json.dumps({
            "schema": "sage-pr-audit-receipt-v1", "objective": "#50",
            "disposition": "bypassed", "signer_role": "architect",
            "reviewed_head": "a" * 40, "merge_base": "b" * 40,
            "scope_sha256": "a" * 64, "audit_evidence": None,
            "bypass_reason": "Architect accepts this independently reviewed omission",
            "original_query": None,
        }, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.request = {
            "purpose": "Approve SAGE audit receipt #sample",
            "receipt_bytes_b64": base64.b64encode(self.data).decode("ascii"),
        }

    def tearDown(self) -> None:
        """Remove disposable state."""
        self.temp.cleanup()

    def _stage(self) -> dict[str, Any]:
        """Create one valid test intent."""
        status, result = call_app(self.app, "/v1/intents", self.request)
        self.assertEqual(status, "201 Created")
        return result

    def test_valid_intent_and_single_approval(self) -> None:
        """Sign exact supplied bytes and consume the intent only once."""
        intent = self._stage()
        approval = {"intent_id": intent["intent_id"],
                    "confirm_sha256": intent["sha256"]}
        status, result = call_app(self.app, "/v1/approve", approval)
        self.assertEqual(status, "200 OK")
        self.assertEqual(result["sha256"], hashlib.sha256(self.data).hexdigest())
        self.assertEqual(result["signer_role"], "architect")
        self.assertEqual(self.signer.calls, [self.data])
        retry, _ = call_app(self.app, "/v1/approve", approval)
        self.assertEqual(retry, "403 Forbidden")

    def test_other_subject_denied(self) -> None:
        """Forbid reusing an intent approved under a different identity."""
        intent = self._stage()
        self.app.identity = SimpleNamespace(authenticate=lambda assertion: "other-user")
        status, _ = call_app(self.app, "/v1/approve", {
            "intent_id": intent["intent_id"], "confirm_sha256": intent["sha256"],
        })
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(self.signer.calls, [])

    def test_maximum_pending_requests(self) -> None:
        """Bound pending-request resource exhaustion by authenticated actors."""
        for _ in range(20):
            self._stage()
        status, _ = call_app(self.app, "/v1/intents", self.request)
        self.assertEqual(status, "403 Forbidden")

    def test_wrong_digest_denied_without_signing(self) -> None:
        """Block approvals with a mismatched byte digest."""
        intent = self._stage()
        status, _ = call_app(self.app, "/v1/approve", {
            "intent_id": intent["intent_id"], "confirm_sha256": "0" * 64,
        })
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(self.signer.calls, [])

    def test_missing_access_assertion_denied(self) -> None:
        """Do not allow a caller to reach signing stages without Access."""
        status, _ = call_app(self.app, "/v1/intents", self.request, "")
        self.assertEqual(status, "403 Forbidden")

    def test_reject_executed_without_auditor(self) -> None:
        """Do not permit Architect signer to attest independent audit execution."""
        data = json.loads(self.data)
        data["disposition"] = "executed"
        data["signer_role"] = "auditor"
        data["audit_evidence"] = {"path": "evidence/audit.json", "sha256": "f" * 64}
        encoded = (json.dumps(data, sort_keys=True, separators=(",", ":"))
                   + "\n").encode()
        request = dict(self.request, receipt_bytes_b64=base64.b64encode(encoded).decode())
        status, _ = call_app(self.app, "/v1/intents", request)
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(self.signer.calls, [])

    def test_auditor_only_signs_executed(self) -> None:
        """An independent auditor controller rejects an Architect bypass."""
        self.app.signer_role = "auditor"
        status, _ = call_app(self.app, "/v1/intents", self.request)
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(self.signer.calls, [])

    def test_auditor_can_stage_executed(self) -> None:
        """The distinct auditor authority can stage a valid executed receipt."""
        self.app.signer_role = "auditor"
        payload = json.loads(self.data)
        payload["disposition"] = "executed"
        payload["signer_role"] = "auditor"
        payload["audit_evidence"] = {
            "path": "evidence/independent.json", "sha256": "f" * 64,
        }
        payload["bypass_reason"] = None
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":"))
                + "\n").encode()
        request = dict(self.request, receipt_bytes_b64=base64.b64encode(data).decode())
        status, response = call_app(self.app, "/v1/intents", request)
        self.assertEqual(status, "201 Created")
        self.assertEqual(response["signer_role"], "auditor")

    def test_reject_noncanonical_receipt(self) -> None:
        """Do not sign plausible but noncanonical JSON receipts."""
        malformed = b'{"schema":"sage-pr-audit-receipt-v1"}'
        request = dict(self.request, receipt_bytes_b64=base64.b64encode(malformed).decode())
        status, _ = call_app(self.app, "/v1/intents", request)
        self.assertEqual(status, "400 Bad Request")
        self.assertEqual(self.signer.calls, [])

    def test_invalid_base64_denied(self) -> None:
        """Reject malformed source bytes rather than sign ambiguously."""
        request = dict(self.request, receipt_bytes_b64="===bad")
        status, _ = call_app(self.app, "/v1/intents", request)
        self.assertEqual(status, "400 Bad Request")

    def test_expired_intent_denied(self) -> None:
        """Reject approvals for expired staged requests."""
        intent = self._stage()
        with self.app.store._connect() as conn:
            conn.execute("UPDATE intents SET created_at=?", (int(time.time()) - 400,))
        status, _ = call_app(self.app, "/v1/approve", {
            "intent_id": intent["intent_id"], "confirm_sha256": intent["sha256"],
        })
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(self.signer.calls, [])

    def test_fail_closed_without_padding_choice(self) -> None:
        """Require explicit verifier-compatible RSA padding configuration."""
        env = dict(
            CF_TEAM_DOMAIN="https://example.cloudflareaccess.com",
            CF_ACCESS_AUD="aud", SAGE_ARCHITECT_EMAIL="arch@example.com",
            BAO_ADDR="https://openbao.svc.example", BAO_K8S_ROLE="arch",
            BAO_SIGN_KEY="arch", BAO_CA_BUNDLE="/tmp/ca.pem",
            BAO_SA_TOKEN_FILE="/tmp/sa.jwt", SAGE_SIGN_DB="/tmp/state.db",
            SAGE_RSA_PADDING="unknown",
        )
        with self.assertRaises(ValueError):
            Settings.from_env(env)


class AccessTests(unittest.TestCase):
    """Test cryptographic claim validation with an ephemeral RSA test key."""

    def setUp(self) -> None:
        """Create a disposable JWT signing key and verifier."""
        self.temp = tempfile.TemporaryDirectory()
        self.config = settings(Path(self.temp.name))
        self.identity = AccessIdentity(self.config)
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.identity.jwks.get_signing_key_from_jwt = lambda token: SimpleNamespace(
            key=self.key.public_key()
        )

    def tearDown(self) -> None:
        """Clean up temporary identity configuration."""
        self.temp.cleanup()

    def _assertion(self, **changes: Any) -> str:
        """Produce a signed JWT with overrides for negative tests.

        Args:
            changes: Replacement JWT claim values.
        """
        claims: dict[str, Any] = {
            "sub": "stable-architect-id", "email": "arch@example.com",
            "iss": self.config.team_domain, "aud": self.config.audience,
            "iat": int(time.time()), "exp": int(time.time()) + 120,
        }
        claims.update(changes)
        return jwt.encode(claims, self.key, algorithm="RS256")

    def test_valid_access_identity(self) -> None:
        """Accept the correctly signed, authorized Architect identity."""
        self.assertEqual(self.identity.authenticate(self._assertion()),
                         "stable-architect-id")

    def test_wrong_audience_rejected(self) -> None:
        """Reject tokens minted for a different Access application."""
        with self.assertRaises(PermissionError):
            self.identity.authenticate(self._assertion(aud="another-app"))

    def test_wrong_issuer_rejected(self) -> None:
        """Reject a signed JWT from a non-configured issuer."""
        with self.assertRaises(PermissionError):
            self.identity.authenticate(self._assertion(iss="https://evil.example"))

    def test_wrong_email_rejected(self) -> None:
        """Deny other Cloudflare identities despite valid token signatures."""
        with self.assertRaises(PermissionError):
            self.identity.authenticate(self._assertion(email="other@example.com"))

    def test_expired_rejected(self) -> None:
        """Reject expired bearer tokens."""
        with self.assertRaises(PermissionError):
            self.identity.authenticate(self._assertion(exp=int(time.time()) - 600))


class TransitTests(unittest.TestCase):
    """Verify fixed OpenBao API parameters and secret-free outputs."""

    def test_signature_interoperability(self) -> None:
        """Independently verify OpenBao-envelope-compatible RSA/SHA256 output."""
        import dataclasses

        for scheme in ("pkcs1v15", "pss"):
            with self.subTest(scheme=scheme), tempfile.TemporaryDirectory() as loc:
                config = dataclasses.replace(settings(Path(loc)), padding=scheme)
                config.sa_token_file.write_text("example-jwt")
                private = rsa.generate_private_key(public_exponent=65537, key_size=3072)
                algorithm = (padding.PKCS1v15() if scheme == "pkcs1v15" else
                             padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                         salt_length=hashes.SHA256().digest_size))

                def fake_post(url: str, **kwargs: Any) -> Any:
                    """Emulate Transit returning a valid cryptographic signature.

                    Args:
                        url: Backend route.
                        kwargs: Input sign arguments.
                    """
                    payload = {"auth": {"client_token": "testing"}}
                    if "/transit/sign/" in url:
                        signed = base64.b64decode(kwargs["json"]["input"])
                        signature = private.sign(signed, algorithm, hashes.SHA256())
                        payload = {"data": {"signature": "vault:v1:" +
                            base64.b64encode(signature).decode("ascii")}}
                    return SimpleNamespace(raise_for_status=lambda: None,
                                           json=lambda: payload)

                with patch("sage_signing.transit.requests.post", side_effect=fake_post):
                    output, version = TransitSigner(config).sign(b"canonical-receipt")
                self.assertEqual(version, 1)
                private.public_key().verify(base64.b64decode(output),
                                            b"canonical-receipt", algorithm,
                                            hashes.SHA256())

    def test_kubernetes_auth_and_rsa_sign(self) -> None:
        """Use Kubernetes auth and verify exact signing payload fields."""
        with tempfile.TemporaryDirectory() as location:
            config = settings(Path(location))
            config.sa_token_file.write_text("test-service-account-jwt")
            calls: list[tuple[str, dict[str, Any]]] = []

            def fake_post(url: str, **kwargs: Any) -> Any:
                """Capture API requests and supply deterministic OpenBao responses.

                Args:
                    url: OpenBao API endpoint.
                    kwargs: HTTP options and request JSON.
                """
                calls.append((url, kwargs))
                payload = {"auth": {"client_token": "vault-test-token"}}
                if "/transit/sign/" in url:
                    payload = {"data": {"signature": "vault:v1:" +
                        base64.b64encode(b"x" * 384).decode("ascii")}}
                return SimpleNamespace(raise_for_status=lambda: None,
                                       json=lambda: payload)

            with patch("sage_signing.transit.requests.post", side_effect=fake_post):
                result, version = TransitSigner(config).sign(b"exact bytes")
            self.assertEqual(version, 1)
            self.assertEqual(base64.b64decode(result), b"x" * 384)
            self.assertIn("/auth/kubernetes/login", calls[0][0])
            self.assertEqual(calls[1][1]["json"]["signature_algorithm"], "pkcs1v15")
            self.assertEqual(base64.b64decode(calls[1][1]["json"]["input"]),
                             b"exact bytes")
            self.assertEqual(calls[1][1]["verify"], config.bao_ca)


if __name__ == "__main__":
    unittest.main()
