"""Human-in-the-loop SAGE remote signing client for macOS or Linux."""

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def cloudflare_token(url: str) -> str:
    """Acquire an application JWT using the user's interactive Access session.

    Args:
        url: Cloudflare Access application HTTPS origin.
    """
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment):
        raise ValueError("SAGE_SIGN_URL must be an HTTPS origin")
    result = subprocess.run(
        ["cloudflared", "access", "token", "--app", url],
        capture_output=True, text=True, check=True, timeout=120,
    )
    token = result.stdout.strip()
    if not token or token.count(".") != 2:
        raise RuntimeError("No valid-looking Cloudflare Access token returned")
    return token


def post_json(url: str, token: str, path: str,
              body: dict[str, object]) -> dict[str, Any]:
    """Send one bounded HTTPS request through the configured Access application.

    Args:
        url: Exact Cloudflare-protected SAGE service origin.
        token: User's application-specific Access JWT.
        path: Fixed signing-controller route.
        body: Non-secret signing metadata and exact receipt bytes.
    """
    request = Request(
        url.rstrip("/") + path,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Cf-Access-Token": token,
                 "Cf-Access-Jwt-Assertion": token},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise RuntimeError("Malformed signing-controller response")
    return result


def sign_receipt(file: Path, purpose: str, url: str) -> Path:
    """Obtain explicit terminal confirmation for exactly one receipt signature.

    Args:
        file: Existing, governed receipt bytes to sign.
        purpose: Human-readable audit action description.
        url: Cloudflare Access-protected signing service origin.
    """
    if not sys.stdin.isatty():
        raise PermissionError("Human interactive terminal required")
    data = file.read_bytes()
    if not 1 <= len(data) <= 65536:
        raise ValueError("Receipt must be between 1 and 65536 bytes")
    digest = hashlib.sha256(data).hexdigest()
    print(f"RECEIPT={file.resolve()}\nPURPOSE={purpose}\nSHA256={digest}")
    try:
        receipt = json.loads(data)
    except (ValueError, UnicodeError) as error:
        raise ValueError("Expected canonical SAGE audit receipt") from error
    print("REVIEW=", json.dumps({
        "objective": receipt.get("objective"),
        "disposition": receipt.get("disposition"),
        "signer_role": receipt.get("signer_role"),
        "reviewed_head": receipt.get("reviewed_head"),
        "audit_evidence": receipt.get("audit_evidence"),
        "bypass_reason": receipt.get("bypass_reason"),
    }, sort_keys=True))
    token = cloudflare_token(url)
    staged = post_json(url, token, "/v1/intents", {
        "purpose": purpose, "receipt_bytes_b64": base64.b64encode(data).decode("ascii"),
    })
    if (staged.get("sha256") != digest or not staged.get("intent_id")
            or staged.get("signer_role") != receipt.get("signer_role")
            or staged.get("disposition") != receipt.get("disposition")):
        raise RuntimeError("Remote staged digest does not match local receipt")
    print("Review the receipt content locally before approving this exact digest.")
    typed = input("Type the full SHA256 digest to authorize this signature: ").strip()
    if typed != digest:
        raise PermissionError("Digest confirmation did not match")
    signed = post_json(url, token, "/v1/approve", {
        "intent_id": staged["intent_id"], "confirm_sha256": typed,
    })
    if signed.get("sha256") != digest:
        raise RuntimeError("Signed response digest mismatch")
    return _save_result(file, signed)


def _save_result(receipt: Path, signed: dict[str, Any]) -> Path:
    """Write signature metadata under owner-only permissions without overwriting.

    Args:
        receipt: Original source receipt filename.
        signed: Verified-digest response from signer.
    """
    destination = receipt.with_name(receipt.name + ".sage-signature.json")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    descriptor = os.open(destination, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(signed, handle, indent=2)
        handle.write("\n")
    print(f"SIGNATURE_OUTPUT={destination}")
    return destination


def main() -> int:
    """Parse CLI options and return a non-zero status on any failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt_file", type=Path)
    parser.add_argument("purpose", help="Human-readable audit action (10-200 chars)")
    args = parser.parse_args()
    try:
        url = os.environ["SAGE_SIGN_URL"]
        sign_receipt(args.receipt_file, args.purpose, url)
    except (OSError, ValueError, RuntimeError, PermissionError,
            subprocess.CalledProcessError, subprocess.TimeoutExpired,
            HTTPError, URLError) as exc:
        print(f"ERROR={type(exc).__name__}: signing incomplete", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
