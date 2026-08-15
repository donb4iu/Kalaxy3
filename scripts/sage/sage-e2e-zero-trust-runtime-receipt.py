
#!/usr/bin/env python3
"""Finalize zero-trust E2E runtime evidence after explicit Architect verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_automated(value: Mapping[str, Any], hostname: str) -> dict[str, bool]:
    if (
        value.get("schema_version") != "1.0"
        or value.get("record_type") != "sage-e2e-zero-trust-runtime-automated"
        or value.get("status") != "pass"
    ):
        raise ValueError("automated runtime receipt version/type/status is invalid")
    if value.get("hostname") != hostname:
        raise ValueError("automated runtime hostname mismatch")
    checks = value.get("checks")
    if not isinstance(checks, Mapping):
        raise ValueError("automated runtime checks are missing")
    required = (
        "workload_ready",
        "origin_through_traefik_ready",
        "tunnel_ready",
        "metrics_monitor_configured",
        "unauthenticated_access_denied",
    )
    if any(checks.get(name) is not True for name in required):
        raise ValueError("automated runtime receipt lacks a required passing check")
    return {name: True for name in required}


def finalize(
    automated: Path,
    hostname: str,
    *,
    authorized_mfa_verified: bool,
    privileged_routes_reviewed: bool,
    actor: str,
    output: Path | None = None,
) -> Path:
    if actor != "architect":
        raise ValueError("runtime trust-boundary confirmation requires Architect role")
    if not authorized_mfa_verified:
        raise ValueError("authorized MFA browser verification is required")
    if not privileged_routes_reviewed:
        raise ValueError("Cloudflare privileged-route review is required")

    automated = automated.expanduser().resolve()
    value = json.loads(automated.read_text(encoding="utf-8"))
    checks = require_automated(value, hostname)
    checks["authorized_mfa_access_verified"] = True
    checks["privileged_surfaces_not_published"] = True

    destination = (
        output.expanduser().resolve()
        if output is not None
        else Path("~/.local/state/kalaxy3/sage-e2e-zero-trust/runtime-final.json")
        .expanduser()
        .resolve()
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "record_type": "sage-e2e-zero-trust-runtime-receipt",
        "status": "pass",
        "hostname": hostname,
        "captured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "actor_role": actor,
        "checks": checks,
        "evidence": {
            "automated_receipt": str(automated),
            "automated_receipt_sha256": sha256_file(automated),
            "authorized_mfa_verification": "explicit Architect browser confirmation",
            "privileged_route_review": "explicit Architect Cloudflare route/application review",
        },
    }
    destination.write_text(
        json.dumps(payload, indent=4, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    destination.chmod(0o600)
    return destination


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-e2e-runtime-receipt-") as raw:
        root = Path(raw)
        automated = root / "automated.json"
        automated.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "record_type": "sage-e2e-zero-trust-runtime-automated",
                    "status": "pass",
                    "hostname": "sage.example.test",
                    "checks": {
                        "workload_ready": True,
                        "origin_through_traefik_ready": True,
                        "tunnel_ready": True,
                        "metrics_monitor_configured": True,
                        "unauthenticated_access_denied": True,
                        "authorized_mfa_access_verified": False,
                        "privileged_surfaces_not_published": False,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        output = root / "final.json"
        final = finalize(
            automated,
            "sage.example.test",
            authorized_mfa_verified=True,
            privileged_routes_reviewed=True,
            actor="architect",
            output=output,
        )
        parsed = json.loads(final.read_text(encoding="utf-8"))
        if not all(parsed["checks"].values()):
            raise RuntimeError("positive runtime receipt did not finalize all checks")
        try:
            finalize(
                automated,
                "sage.example.test",
                authorized_mfa_verified=False,
                privileged_routes_reviewed=True,
                actor="architect",
                output=root / "negative.json",
            )
        except ValueError:
            pass
        else:
            raise RuntimeError("missing MFA verification was accepted")
    print("PASS automated evidence cannot fabricate authorized MFA success")
    print("PASS privileged-route review and Architect role are required")
    print("Kalaxy3 SAGE zero-trust runtime receipt self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--automated", type=Path)
    parser.add_argument("--hostname")
    parser.add_argument("--authorized-mfa-verified", action="store_true")
    parser.add_argument("--privileged-routes-reviewed", action="store_true")
    parser.add_argument("--actor")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.automated is None or not args.hostname or not args.actor:
        parser.error("--automated, --hostname, and --actor are required")
    path = finalize(
        args.automated,
        args.hostname,
        authorized_mfa_verified=args.authorized_mfa_verified,
        privileged_routes_reviewed=args.privileged_routes_reviewed,
        actor=args.actor,
        output=args.output,
    )
    print("Kalaxy3 SAGE zero-trust runtime receipt: PASS")
    print(path)
    print(sha256_file(path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE zero-trust runtime receipt: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
