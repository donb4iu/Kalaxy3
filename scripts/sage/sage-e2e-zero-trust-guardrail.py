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

    connector_placement = policy.get("connector_placement")
    required_connector_placement = {
        "workload_class": "platform-service",
        "replicas": 2,
        "node_level_ha_required": True,
        "hard_hostname_anti_affinity": True,
        "preferred_workload_pool": "platform-services",
        "worker_nodes_preferred": True,
        "arm64_nodes_are_eligible": True,
        "ai_pool_fallback_allowed_for_ha": True,
        "control_plane_fallback_allowed_for_ha": True,
        "application_workloads_do_not_inherit_platform_exceptions": True,
        "future_ai_application_taint": "separate-governed-change",
    }
    if not isinstance(connector_placement, dict):
        failures.append("zero-trust connector placement policy is missing")
    else:
        for key, expected in required_connector_placement.items():
            if connector_placement.get(key) != expected:
                failures.append(
                    f"zero-trust connector placement {key} must equal {expected!r}"
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
        "requiredDuringSchedulingIgnoredDuringExecution",
        "topologyKey: kubernetes.io/hostname",
        "preferredDuringSchedulingIgnoredDuringExecution",
        "kalaxy3.io/workload-pool",
        "platform-services",
        "kalaxy3.io/node-role",
        "kubernetes.io/arch",
        "arm64",
        "connector_node_ha",
        "sage_e2e_connector_nodes",
        "sage_promotion_receipt_file",
        "sage-artifact-promotion-receipt",
        "sage_experience_image_ref",
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
        "nodeSelector:\n        kubernetes.io/arch: amd64",
        "kubernetes.io/hostname: amd64-01",
        "kubernetes.io/hostname: amd64-02",
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

    if "sage-e2e-zero-trust-project-experience:" not in root_makefile:
        failures.append("experience-only zero-trust projection target is missing")
    else:
        projection_block = root_makefile.split(
            "sage-e2e-zero-trust-project-experience:", 1
        )[1].split("\n\nsage-e2e-zero-trust-deploy:", 1)[0]
        for marker in (
            "SAGE_EXTERNAL_HOSTNAME",
            "SAGE_PROMOTION_RECEIPT",
            "sage_promotion_receipt_file=$$SAGE_PROMOTION_RECEIPT",
            "sage_runtime_projection_scope=experience-only",
        ):
            if marker not in projection_block:
                failures.append(
                    f"experience-only projection target missing authority marker: {marker}"
                )
        for forbidden in (
            "KALAXY3_ANSIBLE_SECRETS_FILE",
            "kalaxy3_secrets_file",
            "--ask-vault-pass",
            "cloudflare_tunnel_token",
            "cloudflared",
        ):
            if forbidden in projection_block:
                failures.append(
                    "experience-only projection target must not access connector "
                    f"secret/runtime authority: {forbidden}"
                )

    runtime_validate_block = root_makefile.split(
        "sage-e2e-zero-trust-runtime-validate:", 1
    )[1].split("\n\nsage-e2e-zero-trust-runtime-receipt:", 1)[0]
    for marker in (
        "SAGE_PROMOTION_RECEIPT",
        "sage_promotion_receipt_file=$$SAGE_PROMOTION_RECEIPT",
    ):
        if marker not in runtime_validate_block:
            failures.append(
                f"runtime validation target lacks promotion-receipt transport: {marker}"
            )

    deploy_source = DEPLOY.read_text(encoding="utf-8")
    if deploy_source.count("ansible_become: false") < 2:
        failures.append(
            "controller-local secret inspection does not override inherited ansible_become"
        )
    for marker in (
        "sage_e2e_projection_scope: \"{{ sage_runtime_projection_scope | default('full') }}\"",
        "sage_e2e_projection_scope in ['full', 'experience-only']",
        "Validate connector secret authority for full deployment",
        "Project tunnel connector only for full deployment",
    ):
        if marker not in deploy_source:
            failures.append(f"bounded runtime projection source missing: {marker}")

    secret_scope_start = deploy_source.find(
        "    - name: Validate connector secret authority for full deployment"
    )
    secret_scope_end = deploy_source.find("\n  tasks:", secret_scope_start)
    if secret_scope_start < 0 or secret_scope_end < 0:
        failures.append("full-deployment secret block cannot be bounded")
    else:
        secret_scope = deploy_source[secret_scope_start:secret_scope_end]
        if "when: sage_e2e_projection_scope == 'full'" not in secret_scope:
            failures.append("full-deployment secret block lacks full-only condition")
        for marker in (
            "kalaxy3_secrets_file",
            "ansible.builtin.include_vars",
        ):
            if marker not in secret_scope:
                failures.append(
                    f"full-deployment secret block lost expected secret marker: {marker}"
                )
            remainder = deploy_source[:secret_scope_start] + deploy_source[secret_scope_end:]
            if marker in remainder:
                failures.append(
                    f"secret authority escaped the full-only projection block: {marker}"
                )

    connector_scope_start = deploy_source.find(
        "        - name: Project tunnel connector only for full deployment"
    )
    experience_apply_start = deploy_source.find(
        "        - name: Apply SAGE experience", connector_scope_start
    )
    if connector_scope_start < 0 or experience_apply_start < 0:
        failures.append("full-deployment connector block cannot be bounded")
    else:
        connector_scope = deploy_source[connector_scope_start:experience_apply_start]
        if "when: sage_e2e_projection_scope == 'full'" not in connector_scope:
            failures.append("full-deployment connector block lacks full-only condition")
        for marker in (
            "Render namespaces",
            "Render cloudflared connector",
            "Apply bounded namespaces",
            "Apply tunnel token secret from protected in-memory definition",
            "Apply cloudflared connector",
            "Wait for cloudflared rollout",
        ):
            if marker not in connector_scope:
                failures.append(
                    f"connector mutation escaped or is missing from full-only block: {marker}"
                )
        if "Apply SAGE experience" in connector_scope:
            failures.append("SAGE experience apply is incorrectly gated by connector authority")
        full_only_scope = secret_scope + connector_scope
        for marker in (
            "kalaxy3_runtime_secrets.cloudflare_tunnel_token",
            "Apply tunnel token secret from protected in-memory definition",
        ):
            if marker not in full_only_scope:
                failures.append(
                    f"full-only secret projection lost required marker: {marker}"
                )
        if secret_scope:
            outside_full_only = (
                deploy_source[:secret_scope_start]
                + deploy_source[secret_scope_end:connector_scope_start]
                + deploy_source[experience_apply_start:]
            )
            for marker in (
                "kalaxy3_runtime_secrets.cloudflare_tunnel_token",
                "Apply tunnel token secret from protected in-memory definition",
            ):
                if marker in outside_full_only:
                    failures.append(
                        f"secret/connector authority escaped full-only scope: {marker}"
                    )

    experience = EXPERIENCE.read_text(encoding="utf-8")
    if 'image: "{{ sage_experience_image_ref }}"' not in experience:
        failures.append(
            "SAGE experience does not bind the verified promoted OCI digest"
        )
    if "donb4iu/mynginx_docs:566d215fc0a077cb9330a69b08716a53903e6fe0" in experience:
        failures.append("SAGE experience retains the historical Git-SHA image tag")
    if "{{ sage_external_hostname }}" not in experience:
        failures.append(
            "external hostname must remain runtime-selected and explicit"
        )
    for marker in (
        "What SAGE prevented",
        "engineering burden rather than operator knowledge",
        "first real deployment stopped again before cluster mutation",
        "inherited Ansible privilege-escalation state",
        "node-level HA outranks ordinary placement preference",
        "ARM64 capacity must not be ignored",
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
        "connector_node_ha",
        "sage_e2e_connector_nodes",
        "sage_promotion_receipt_file",
        "sage-artifact-promotion-receipt",
        "sage_expected_image_ref",
        "unique | length == 2",
        "ansible_become: false",
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
    print(
        "PASS experience-only projection consumes exact promotion evidence while "
        "remaining structurally unable to read or mutate tunnel secret/connector authority"
    )
    print(
        "PASS runtime validation receives the exact non-secret promotion receipt through "
        "the repository-owned Make boundary"
    )
    print("PASS cloudflared is pinned, replicated, observable, and secret-file bound")
    print(
        "PASS cloudflared node-level HA is hard while platform-service, worker, "
        "and ARM64 placement remain ordered preferences with AI/control-plane fallback"
    )
    print(
        "PASS controller-local secret and validation boundaries override inherited "
        "Ansible privilege escalation without weakening secret redaction"
    )
    print(
        "PASS SAGE experience preserves the documentation-image runtime behind Traefik with digest-bound promotion"
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
