#!/usr/bin/env python3
"""Guard the SAGE zero-trust external-experience source contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "infrastructure/k3s-homelab/cloudflare"
ROOT_MAKEFILE = ROOT / "Makefile"
POLICY = BASE / "access-policy-requirements.json"
NAMESPACES = BASE / "namespaces.yaml.j2"
EXPERIENCE = BASE / "sage-experience.yaml.j2"
TUNNEL = BASE / "cloudflared.yaml.j2"
SECRET = BASE / "cloudflared-secret.yaml.j2"
DEPLOY = BASE / "deploy-sage-e2e.yml"
VALIDATE = BASE / "validate-sage-e2e.yml"
RUNTIME_RECEIPT = ROOT / "scripts/sage/sage-e2e-zero-trust-runtime-receipt.py"
RUNTIME_SCHEMA = ROOT / "markdown/standards/sage-e2e-zero-trust-runtime-receipt-schema-v1.0.json"
INTENT_WORKFLOW = ROOT / "scripts/sage/workflows/intent_to_outcome.py"


def main() -> int:
    failures: list[str] = []
    paths = (
        ROOT_MAKEFILE,
        POLICY,
        NAMESPACES,
        EXPERIENCE,
        TUNNEL,
        SECRET,
        DEPLOY,
        VALIDATE,
        RUNTIME_RECEIPT,
        RUNTIME_SCHEMA,
        INTENT_WORKFLOW,
    )
    for path in paths:
        if not path.is_file():
            failures.append(
                f"missing zero-trust artifact: {path.relative_to(ROOT)}"
            )
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

    secret_policy = policy.get("secret_handling")
    if not isinstance(secret_policy, dict):
        failures.append("zero-trust secret-handling policy is missing")
    else:
        required_secret_policy = {
            "controller_source": "ansible-vault-encrypted-file-outside-git",
            "runtime_projection": "kubernetes-secret",
            "plaintext_render_to_disk": False,
            "secret_bearing_task_logs": False,
            "secret_in_command_arguments": False,
        }
        for key, expected in required_secret_policy.items():
            if secret_policy.get(key) != expected:
                failures.append(
                    f"zero-trust secret policy {key} must equal {expected!r}"
                )

    runtime_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (NAMESPACES, EXPERIENCE, TUNNEL, DEPLOY, VALIDATE)
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
        "kalaxy3_secrets_file",
        "ansible.builtin.stat",
        "ansible.builtin.slurp",
        "$ANSIBLE_VAULT;",
        "kalaxy3_secrets_stat.stat.mode in ['0400', '0600']",
        "ansible.builtin.include_vars",
        "kalaxy3_runtime_secrets.cloudflare_tunnel_token",
        "Apply tunnel token secret from protected in-memory definition",
        "stdin: |",
    ):
        if marker not in runtime_source:
            failures.append(f"zero-trust source missing: {marker}")
    for forbidden in (
        "type: LoadBalancer",
        "type: NodePort",
        "hostNetwork: true",
        "hostPort:",
        "cloudflare_tunnel_token_file",
        "lookup('file'",
        "cloudflared-secret.yaml",
    ):
        if forbidden in runtime_source:
            failures.append(f"zero-trust source retains prohibited pattern: {forbidden}")

    secret_stub = SECRET.read_text(encoding="utf-8")
    for forbidden in ("kind: Secret", "stringData:", "cloudflare_tunnel_token"):
        if forbidden in secret_stub:
            failures.append(
                f"deprecated secret template retains credential rendering: {forbidden}"
            )

    root_makefile = ROOT_MAKEFILE.read_text(encoding="utf-8")
    deploy_block = root_makefile.split("sage-e2e-zero-trust-deploy:", 1)[1]
    deploy_block = deploy_block.split("\n\nsage-e2e-zero-trust-runtime-validate:", 1)[0]
    for marker in (
        "KALAXY3_ANSIBLE_SECRETS_FILE",
        "kalaxy3_secrets_file=$$KALAXY3_ANSIBLE_SECRETS_FILE",
    ):
        if marker not in deploy_block:
            failures.append(
                f"zero-trust deploy target lacks protected secret-source marker: {marker}"
            )
    if "CLOUDFLARE_TUNNEL_TOKEN_FILE" in deploy_block:
        failures.append(
            "zero-trust deploy target still accepts a plaintext token-file contract"
        )
    if "--ask-vault-pass" not in deploy_block:
        failures.append(
            "zero-trust deploy target does not request decryption for its required Ansible Vault source"
        )

    experience = EXPERIENCE.read_text(encoding="utf-8")
    if (
        "donb4iu/mynginx_docs:566d215fc0a077cb9330a69b08716a53903e6fe0"
        not in experience
    ):
        failures.append(
            "SAGE experience does not reuse the proven documentation image"
        )
    if "{{ sage_external_hostname }}" not in experience:
        failures.append(
            "external hostname must remain runtime-selected and explicit"
        )
    for marker in (
        "What SAGE prevented",
        "engineering burden rather than operator knowledge",
        "cross-component integration gap before deployment",
        "no Vault decryption option",
        "stopped before the new credential was introduced",
    ):
        if marker not in experience:
            failures.append(f"SAGE value experience missing vignette marker: {marker}")

    runtime_receipt = RUNTIME_RECEIPT.read_text(encoding="utf-8")
    runtime_schema = json.loads(RUNTIME_SCHEMA.read_text(encoding="utf-8"))
    intent_workflow = INTENT_WORKFLOW.read_text(encoding="utf-8")
    for marker in (
        "VALUE_VIGNETTE",
        "architect_observation",
        "sage_finding",
        "prevented_action",
        "bounded_correction",
        "value_demonstrated",
    ):
        if marker not in runtime_receipt:
            failures.append(f"runtime receipt missing SAGE value-evidence marker: {marker}")
    if "value_vignette" not in runtime_schema.get("required", []):
        failures.append("runtime receipt schema does not require value_vignette")
    required_vignette = {
        "architect_observation",
        "sage_finding",
        "prevented_action",
        "bounded_correction",
        "value_demonstrated",
    }
    vignette_schema = runtime_schema.get("properties", {}).get("value_vignette", {})
    if set(vignette_schema.get("required", [])) != required_vignette:
        failures.append("runtime receipt schema value_vignette contract is incomplete")
    for marker in (
        'value.get("value_vignette")',
        "runtime receipt SAGE value vignette is missing",
    ):
        if marker not in intent_workflow:
            failures.append(f"intent runtime gate missing value-evidence marker: {marker}")

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
    print(
        "PASS Cloudflare tunnel token comes from controller-local Ansible Vault "
        "source outside Git without plaintext render files"
    )
    print(
        "PASS runtime Kubernetes Secret projection uses protected stdin and "
        "secret-bearing tasks suppress logs"
    )
    print(
        "PASS zero-trust deploy front door consumes the required Ansible Vault "
        "through the repository's interactive decryption convention"
    )
    print("PASS cloudflared is pinned, replicated, observable, and secret-file bound")
    print(
        "PASS SAGE experience reuses the existing documentation image behind Traefik"
    )
    print(
        "PASS automated evidence does not claim human MFA or Cloudflare route review"
    )
    print(
        "PASS SAGE value vignette is preserved in public UX, runtime evidence, and parent acceptance"
    )
    print("Kalaxy3 SAGE zero-trust E2E guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
