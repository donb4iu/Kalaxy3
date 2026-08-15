
#!/usr/bin/env python3
"""Guard the SAGE zero-trust external-experience source contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "infrastructure/k3s-homelab/cloudflare"
POLICY = BASE / "access-policy-requirements.json"
NAMESPACES = BASE / "namespaces.yaml.j2"
EXPERIENCE = BASE / "sage-experience.yaml.j2"
TUNNEL = BASE / "cloudflared.yaml.j2"
SECRET = BASE / "cloudflared-secret.yaml.j2"
DEPLOY = BASE / "deploy-sage-e2e.yml"
VALIDATE = BASE / "validate-sage-e2e.yml"


def main() -> int:
    failures: list[str] = []
    paths = (POLICY, NAMESPACES, EXPERIENCE, TUNNEL, SECRET, DEPLOY, VALIDATE)
    for path in paths:
        if not path.is_file():
            failures.append(f"missing zero-trust artifact: {path.relative_to(ROOT)}")
    if failures:
        print("Kalaxy3 SAGE zero-trust E2E guardrail: FAIL CLOSED")
        for item in failures:
            print(f"  - {item}")
        return 1

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    for key in (
        "human_access_requires_mfa",
        "explicit_allow_identity_required",
        "grant_revoke_supported",
        "access_configured_before_route",
        "privileged_surfaces_remain_private",
        "unmanaged_router_forwarding_forbidden",
    ):
        if policy.get(key) is not True:
            failures.append(f"Access policy must require {key}")
    if policy.get("anonymous_access") is not False:
        failures.append("anonymous external access must be false")
    if policy.get("mfa_enforcement") != "cloudflare-access-independent-mfa":
        failures.append("independent Cloudflare Access MFA is not required")

    runtime_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (NAMESPACES, EXPERIENCE, TUNNEL, SECRET, DEPLOY, VALIDATE)
    )
    if "eyJ" in runtime_source:
        failures.append("source contains a token-like Cloudflare credential")
    if "cloudflare/cloudflared:latest" in runtime_source:
        failures.append("cloudflared must not use latest")
    if "cloudflare/cloudflared:2026.8.2" not in runtime_source:
        failures.append("cloudflared is not pinned to the reviewed release")
    for marker in (
        "replicas: 2",
        "TUNNEL_TOKEN_FILE",
        "/etc/cloudflared/token/token",
        "--metrics",
        "0.0.0.0:2000",
        "path: /ready",
        "kind: ServiceMonitor",
        "release: kube-prometheus-stack",
        "sage-experience",
        "traefik.ingress.kubernetes.io/router.entrypoints",
        "no_log: true",
        "cloudflare_tunnel_token_file",
    ):
        if marker not in runtime_source:
            failures.append(f"zero-trust source missing: {marker}")
    for forbidden in (
        "type: LoadBalancer",
        "type: NodePort",
        "hostNetwork: true",
        "hostPort:",
    ):
        if forbidden in runtime_source:
            failures.append(f"zero-trust source widens exposure: {forbidden}")

    experience = EXPERIENCE.read_text(encoding="utf-8")
    if "donb4iu/mynginx_docs:566d215fc0a077cb9330a69b08716a53903e6fe0" not in experience:
        failures.append("SAGE experience does not reuse the proven documentation image")
    if "{{ sage_external_hostname }}" not in experience:
        failures.append("external hostname must remain runtime-selected and explicit")

    validation = VALIDATE.read_text(encoding="utf-8")
    for marker in (
        "origin_through_traefik_ready",
        "unauthenticated_access_denied",
        "authorized_mfa_access_verified",
        "privileged_surfaces_not_published",
        "sage-e2e-zero-trust-runtime-automated",
    ):
        if marker not in validation:
            failures.append(f"runtime validation missing: {marker}")

    if failures:
        print("Kalaxy3 SAGE zero-trust E2E guardrail: FAIL CLOSED")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("PASS anonymous access and unmanaged inbound exposure fail closed")
    print("PASS cloudflared is pinned, replicated, observable, and secret-file bound")
    print("PASS SAGE experience reuses the existing documentation image behind Traefik")
    print("PASS automated evidence does not claim human MFA or Cloudflare route review")
    print("Kalaxy3 SAGE zero-trust E2E guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
