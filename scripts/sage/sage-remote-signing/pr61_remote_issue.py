#!/usr/bin/env python3
"""Issue a PR #61-compatible receipt using a separately authorized remote signer."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Sequence

from tools.operator import sign_receipt

TRUSTED_VERIFIER_SHA256 = (
    "04c4b5c1502ed5f01585f9db06dc5b78abff387400ad90102bf8c3a7afbc3e19"
)
TRUSTED_VERIFIER_PATH = "scripts/ci/sage_audit_receipt.py"
TRUSTED_KEY_ROOT = ".github/sage/authorized-signers"


def git_blob(repo: Path, revision: str, filename: str) -> bytes:
    """Read an exact Git object rather than candidate working-tree contents.

    Args:
        repo: Checkout containing the trusted base.
        revision: Git revision trusted as the PR base.
        filename: Expected repository-relative file.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{filename}"],
        capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Missing trusted-base artifact: {filename}")
    return result.stdout


def trusted_module(repo: Path, base: str, directory: Path) -> ModuleType:
    """Import only the captured, checksum-pinned PR #61 verifier.

    Args:
        repo: Checkout with the trusted base revision.
        base: Exact base revision or remote-tracking branch.
        directory: Temporary directory for the verified module.
    """
    data = git_blob(repo, base, TRUSTED_VERIFIER_PATH)
    if hashlib.sha256(data).hexdigest() != TRUSTED_VERIFIER_SHA256:
        raise RuntimeError("Trusted PR #61 verifier changed; revalidate integration")
    path = directory / "sage_audit_receipt_trusted.py"
    path.write_bytes(data)
    spec = importlib.util.spec_from_file_location("sage_audit_trusted", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import validated verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def receipt_arguments(options: argparse.Namespace) -> argparse.Namespace:
    """Build existing PR #61 payload inputs without changing its contract.

    Args:
        options: Parsed remote signer CLI arguments.
    """
    return argparse.Namespace(
        repo=options.repo, base=options.base, objective=options.objective,
        disposition=options.disposition, audit_path=options.audit_path,
        reason=options.reason, original_query_ref=options.original_query_ref,
    )


def checked_signature(response: dict[str, object], digest: str,
                      role: str) -> bytes:
    """Check the remote signature envelope before local OpenSSL verification.

    Args:
        response: JSON returned by the remote signer.
        digest: Original canonical receipt SHA-256.
        role: Expected independent signing authority.
    """
    if (response.get("sha256") != digest or response.get("signer_role") != role
            or response.get("signature_algorithm") != "pkcs1v15"
            or response.get("hash_algorithm") != "sha2-256"):
        raise RuntimeError("Remote signature metadata is incompatible with PR #61")
    signature = response.get("signature_b64")
    if not isinstance(signature, str):
        raise RuntimeError("Remote signature missing")
    result = base64.b64decode(signature, validate=True)
    if len(result) != 384:
        raise RuntimeError("Expected RSA-3072 signature")
    return result


def write_receipt(repo: Path, digest: str, data: bytes,
                  signature: bytes) -> None:
    """Write only two Git-candidate receipt files, never a private key.

    Args:
        repo: Feature checkout.
        digest: Canonical receipt SHA-256.
        data: Verified exact canonical receipt bytes.
        signature: Independently verified raw RSA signature.
    """
    directory = repo / ".sage/audit-receipts"
    directory.mkdir(parents=True, exist_ok=True)
    paths = (directory / f"{digest}.json", directory / f"{digest}.sig")
    if any(path.exists() for path in paths):
        raise RuntimeError("Receipt exists; refusing overwrite")
    try:
        for path, value in zip(paths, (data, signature)):
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            with os.fdopen(descriptor, "wb") as target:
                target.write(value)
    except BaseException:
        for path in paths:
            path.unlink(missing_ok=True)
        raise


def issue_remote(options: argparse.Namespace) -> str:
    """Prepare, remotely sign, independently verify, and write PR #61 files.

    Args:
        options: Approved CLI inputs from the existing objective.
    """
    repo = options.repo.resolve()
    role = "auditor" if options.disposition == "executed" else "architect"
    with tempfile.TemporaryDirectory(prefix="sage-pr61-remote-") as temp:
        directory = Path(temp)
        verifier = trusted_module(repo, options.base, directory)
        if verifier.git(repo, "status", "--porcelain"):
            raise RuntimeError("Commit all source and evidence before signing")
        payload = verifier.issue_payload(receipt_arguments(options))
        data = verifier.encode(payload)
        digest = hashlib.sha256(data).hexdigest()
        key_bytes = git_blob(repo, options.base, f"{TRUSTED_KEY_ROOT}/{role}.pem")
        trusted_key = directory / f"{role}.pem"
        trusted_key.write_bytes(key_bytes)
        source_file = directory / "receipt.json"
        source_file.write_bytes(data)
        metadata_file = sign_receipt(source_file, options.purpose, options.sign_url)
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        signature = checked_signature(metadata, digest, role)
        verifier.check_signature(data, signature, trusted_key)
        if verifier.git(repo, "status", "--porcelain"):
            raise RuntimeError("Git source changed during signing; retry")
        if verifier.encode(verifier.issue_payload(receipt_arguments(options))) != data:
            raise RuntimeError("Committed source scope changed during signing")
        write_receipt(repo, digest, data, signature)
    return digest


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse remote-signing arguments preserving PR #61 evidence semantics.

    Args:
        argv: Optional CLI argument sequence.
    """
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo", type=Path, required=True)
    cli.add_argument("--base", default="origin/main")
    cli.add_argument("--objective", required=True)
    cli.add_argument("--disposition", choices=("executed", "bypassed",
                                               "not_applicable"), required=True)
    cli.add_argument("--audit-path", default="")
    cli.add_argument("--reason", default="")
    cli.add_argument("--original-query-ref", default="")
    cli.add_argument("--sign-url", default=os.environ.get("SAGE_SIGN_URL", ""))
    cli.add_argument("--purpose", required=True)
    return cli.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Issue a bounded candidate or fail without asserting PR qualification.

    Args:
        argv: Optional command-line arguments.
    """
    options = parse_args(argv)
    try:
        if not options.sign_url:
            raise ValueError("SAGE_SIGN_URL / --sign-url required")
        digest = issue_remote(options)
        print("SAGE_AUDIT_REMOTE_RECEIPT=ISSUED")
        print(f"SAGE_AUDIT_RECEIPT_SHA256={digest}")
        print("Commit only .sage/audit-receipts/<digest>.json and .sig")
        print(f"SAGE-Audit-Receipt-SHA256: {digest}")
    except (OSError, ValueError, RuntimeError, PermissionError) as error:
        print(f"SAGE_AUDIT_REMOTE_RECEIPT=BLOCKED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
