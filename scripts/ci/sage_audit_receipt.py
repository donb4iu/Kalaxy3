#!/usr/bin/env python3
"""Issue and verify revision-bound, independently signed SAGE PR audit receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = "sage-pr-audit-receipt-v1"
RECEIPTS = ".sage/audit-receipts"
REVISION = re.compile(r"^[0-9a-f]{40,64}$")
OBJECTIVE = re.compile(r"^(?:#[1-9][0-9]*|SAGE-[A-Za-z0-9-]+)$")
TRAILER = re.compile(r"^SAGE-Audit-Receipt-SHA256: ([0-9a-f]{64})$")


class ReceiptError(Exception):
    """A bounded SAGE audit-receipt validation error."""


def git(repo: Path, *args: str) -> bytes:
    """Execute a read-only Git operation.

    Args:
        repo: Repository root.
        args: Git subcommand arguments.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=False
    )
    if result.returncode:
        raise ReceiptError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def openssl(args: Sequence[str], data: bytes | None = None) -> bytes:
    """Run OpenSSL without invoking a shell.

    Args:
        args: OpenSSL subcommand arguments.
        data: Optional input bytes.
    """
    result = subprocess.run(
        ["openssl", *args], input=data, capture_output=True, check=False
    )
    if result.returncode:
        raise ReceiptError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def source_bytes(repo: Path, revision: str, path: str) -> bytes:
    """Read a Git-tracked blob without accessing untrusted working-tree files.

    Args:
        repo: Repository containing the object.
        revision: A revision already verified by the caller.
        path: Relative repository path.
    """
    if path.startswith("/") or ".." in Path(path).parts or ":" in path:
        raise ReceiptError("Invalid evidence path")
    if path.startswith(f"{RECEIPTS}/"):
        raise ReceiptError("Receipt paths cannot be audit evidence")
    return git(repo, "show", f"{revision}:{path}")


def revision_scope(repo: Path, base: str, head: str) -> tuple[str, str]:
    """Hash the exact PR change set, excluding receipt and signature files.

    Args:
        repo: Git repository.
        base: Base branch revision.
        head: Candidate PR revision.
    """
    ancestor = git(repo, "merge-base", base, head).decode().strip()
    diff = git(
        repo, "diff", "--raw", "-z", "--no-renames", "--no-ext-diff",
        ancestor, head, "--", ".", f":(exclude){RECEIPTS}/**",
    )
    return ancestor, hashlib.sha256(diff).hexdigest()


def encode(payload: Mapping[str, Any]) -> bytes:
    """Canonicalize receipt data for hashing and signature verification.

    Args:
        payload: JSON-compatible receipt mapping.
    """
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()


def signed_digest(data: bytes, key: Path) -> bytes:
    """Create an OpenSSL SHA-256 signature with an explicitly supplied key.

    Args:
        data: Exact receipt bytes.
        key: Private signing key path, never copied into the repository.
    """
    return openssl(["dgst", "-sha256", "-sign", str(key)], data)


def check_signature(data: bytes, signature: bytes, key: Path) -> None:
    """Verify a signature using temporary signature storage only.

    Args:
        data: Receipt bytes.
        signature: Signature bytes.
        key: Trusted public key path.
    """
    import tempfile

    with tempfile.TemporaryDirectory(prefix="sage-receipt-") as directory:
        file = Path(directory) / "receipt.sig"
        file.write_bytes(signature)
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(key),
             "-signature", str(file)], input=data,
            capture_output=True, check=False,
        )
    if result.returncode:
        raise ReceiptError("Receipt signature does not match trusted role key")


def evidence_entry(repo: Path, revision: str, path: str) -> dict[str, str]:
    """Bind a source artifact to its exact committed content hash.

    Args:
        repo: Git repository.
        revision: Committed source revision.
        path: Source artifact relative path.
    """
    data = source_bytes(repo, revision, path)
    return {"path": path, "sha256": hashlib.sha256(data).hexdigest()}


def issue_payload(args: argparse.Namespace) -> dict[str, Any]:
    """Assemble a scoped audit disposition without asserting authorization.

    Args:
        args: Validated command-line arguments.
    """
    if not OBJECTIVE.fullmatch(args.objective):
        raise ReceiptError("Objective ID must be an issue reference or SAGE ID")
    head = git(args.repo, "rev-parse", "HEAD").decode().strip()
    ancestor, scope_hash = revision_scope(args.repo, args.base, head)
    role = "auditor" if args.disposition == "executed" else "architect"
    evidence = None
    if args.disposition == "executed":
        if not args.audit_path:
            raise ReceiptError("An executed audit requires committed audit evidence")
        evidence = evidence_entry(args.repo, head, args.audit_path)
    elif not args.reason or len(args.reason.strip()) < 12:
        raise ReceiptError("A bypass requires a meaningful Architect justification")
    return {
        "schema": SCHEMA,
        "objective": args.objective,
        "disposition": args.disposition,
        "signer_role": role,
        "reviewed_head": head,
        "merge_base": ancestor,
        "scope_sha256": scope_hash,
        "audit_evidence": evidence,
        "bypass_reason": args.reason.strip() if role == "architect" else None,
        "original_query": (evidence_entry(args.repo, head, args.original_query_ref)
                           if args.original_query_ref else None),
    }


def issue(args: argparse.Namespace) -> str:
    """Write a signed candidate receipt for a later closeout Git commit.

    Args:
        args: Issuance parameters, including a private key path.
    """
    if git(args.repo, "status", "--porcelain"):
        raise ReceiptError("Commit changes and evidence before issuing the receipt")
    payload = issue_payload(args)
    data = encode(payload)
    digest = hashlib.sha256(data).hexdigest()
    target = args.repo / RECEIPTS
    target.mkdir(parents=True, exist_ok=True)
    file = target / f"{digest}.json"
    signature = target / f"{digest}.sig"
    if file.exists() or signature.exists():
        raise ReceiptError("Receipt already exists; do not overwrite it")
    file.write_bytes(data)
    signature.write_bytes(signed_digest(data, args.signing_key))
    return digest


def trailer_digest(repo: Path, head: str) -> str:
    """Read the exact audit receipt digest from the PR closeout commit.

    Args:
        repo: Candidate Git repository.
        head: Head revision to inspect.
    """
    message = git(repo, "show", "-s", "--format=%B", head).decode()
    matches = [m.group(1) for line in message.splitlines()
               if (m := TRAILER.fullmatch(line.strip()))]
    if len(matches) != 1:
        raise ReceiptError("PR head must have exactly one audit receipt SHA trailer")
    return matches[0]


def validate_payload(payload: Mapping[str, Any]) -> str:
    """Validate an untrusted receipt's structure and role assignment.

    Args:
        payload: Untrusted JSON data.
    """
    if payload.get("schema") != SCHEMA:
        raise ReceiptError("Wrong receipt schema")
    if not OBJECTIVE.fullmatch(str(payload.get("objective", ""))):
        raise ReceiptError("Invalid objective reference")
    disposition = payload.get("disposition")
    if disposition not in ("executed", "bypassed", "not_applicable"):
        raise ReceiptError("Invalid audit disposition")
    expected_role = "auditor" if disposition == "executed" else "architect"
    if payload.get("signer_role") != expected_role:
        raise ReceiptError("Signer role does not match disposition")
    reason = str(payload.get("bypass_reason") or "").strip()
    if disposition != "executed" and len(reason) < 12:
        raise ReceiptError("Missing meaningful bypass justification")
    if disposition == "executed" and not isinstance(
        payload.get("audit_evidence"), dict
    ):
        raise ReceiptError("Missing auditor evidence artifact")
    for field in ("merge_base", "reviewed_head"):
        if not REVISION.fullmatch(str(payload.get(field, ""))):
            raise ReceiptError(f"Invalid {field} revision")
    if not re.fullmatch(r"[0-9a-f]{64}", str(payload.get("scope_sha256", ""))):
        raise ReceiptError("Invalid reviewed scope digest")
    return expected_role


def verify(args: argparse.Namespace) -> str:
    """Verify the receipt, role signature, revision scope, and source evidence.

    Args:
        args: Verifier arguments supplied by trusted CI.
    """
    actual_head = git(args.repo, "rev-parse", "HEAD").decode().strip()
    if actual_head != args.head:
        raise ReceiptError("Candidate checkout does not match PR head SHA")
    digest = trailer_digest(args.repo, args.head)
    data = git(args.repo, "show", f"{args.head}:{RECEIPTS}/{digest}.json")
    if len(data) > 65536:
        raise ReceiptError("Receipt exceeds 64 KiB limit")
    if hashlib.sha256(data).hexdigest() != digest:
        raise ReceiptError("Receipt bytes do not match commit trailer SHA-256")
    payload = json.loads(data)
    if not isinstance(payload, dict) or encode(payload) != data:
        raise ReceiptError("Receipt must use canonical JSON serialization")
    role = validate_payload(payload)
    signature = git(args.repo, "show", f"{args.head}:{RECEIPTS}/{digest}.sig")
    if len(signature) > 16384:
        raise ReceiptError("Signature exceeds 16 KiB limit")
    check_signature(data, signature, args.trusted_keys / f"{role}.pem")
    ancestor, scope_hash = revision_scope(args.repo, args.base, args.head)
    if (payload.get("merge_base"), payload.get("scope_sha256")) != (
        ancestor, scope_hash
    ):
        raise ReceiptError("PR changes differ from the signed review scope")
    reviewed = payload.get("reviewed_head", "")
    git(args.repo, "merge-base", "--is-ancestor", str(reviewed), args.head)
    for field in ("audit_evidence", "original_query"):
        item = payload.get(field)
        if item is not None:
            if not isinstance(item, dict) or item != evidence_entry(
                args.repo, reviewed, item["path"]
            ):
                raise ReceiptError(f"{field} changed or digest mismatched")
    return digest


def parser() -> argparse.ArgumentParser:
    """Build the two-operation receipt CLI."""
    cli = argparse.ArgumentParser(description=__doc__)
    ops = cli.add_subparsers(dest="operation", required=True)
    issue_cmd = ops.add_parser("issue")
    issue_cmd.add_argument("--repo", type=Path, required=True)
    issue_cmd.add_argument("--base", default="origin/main")
    issue_cmd.add_argument("--objective", required=True)
    issue_cmd.add_argument(
        "--disposition", choices=["executed", "bypassed", "not_applicable"],
        required=True,
    )
    issue_cmd.add_argument("--audit-path", default="")
    issue_cmd.add_argument("--reason", default="")
    issue_cmd.add_argument("--original-query-ref", default="")
    issue_cmd.add_argument("--signing-key", type=Path, required=True)
    verify_cmd = ops.add_parser("verify")
    verify_cmd.add_argument("--repo", type=Path, required=True)
    verify_cmd.add_argument("--base", required=True)
    verify_cmd.add_argument("--head", required=True)
    verify_cmd.add_argument("--trusted-keys", type=Path, required=True)
    return cli


def main(argv: Sequence[str] | None = None) -> int:
    """Issue or verify a signed receipt and return a CI-safe exit code.

    Args:
        argv: Optional command-line arguments.
    """
    args = parser().parse_args(argv)
    try:
        if args.operation == "issue":
            digest = issue(args)
            print("SAGE_AUDIT_RECEIPT=CREATED")
            print(f"SAGE_AUDIT_RECEIPT_SHA256={digest}")
            print(f"Stage and commit {RECEIPTS}/{digest}.json and .sig")
            print(f"SAGE-Audit-Receipt-SHA256: {digest}")
        else:
            digest = verify(args)
            print(f"SAGE_AUDIT_RECEIPT=VERIFIED SHA256={digest}")
        return 0
    except (ReceiptError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"SAGE_AUDIT_RECEIPT=FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
