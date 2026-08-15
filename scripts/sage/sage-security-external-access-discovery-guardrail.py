#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "scripts/sage/sage-change-preflight.py"
AUTHORITY = ROOT / "sage-change-authority.json"

VIABILITY_REQUEST = """Deliver the next end-to-end Kalaxy3/SAGE viability slice as one governed intent-to-outcome proof, not as an academic SAGE-only enhancement. The slice must deliver a useful operational capability into the Kalaxy3 Kubernetes cluster, expose a safe externally viewable experience, reconcile security/privacy/compliance, observability, networking, Traefik, MetalLB, Kubernetes, deployment guardrails, secret-handling, and existing Phase 7 Cloudflare/security decisions. Evaluate Cloudflare Tunnel/Access for external publication without unmanaged router port forwarding, while keeping public presentation, authenticated operational views, and privileged management surfaces as different trust classes."""

def load_preflight():
    spec = importlib.util.spec_from_file_location("sage_change_preflight_external_access", PREFLIGHT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SAGE change preflight")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def main() -> int:
    module = load_preflight()
    payload = module.load_authority_map(AUTHORITY)
    contexts = {item["id"]: item for item in payload["contexts"]}
    require("security" in contexts and "external-access" in contexts, "durable security/external-access authority is absent")
    require("security" in contexts["external-access"]["requires"], "external-access no longer inherits security authority")

    request = ("Expose a read-only SAGE value experience through Cloudflare Tunnel with DNS, TLS, "
               "Cloudflare Access where authentication is appropriate, encrypted secret handling, "
               "explicit trust boundaries, and no router port forwarding.")
    inferred = module.infer_for_request(payload, request)
    require("external-access" in inferred, "external-access request authority was not discovered")
    require("security" in inferred, "security request authority was not discovered")

    viability = module.infer_for_request(payload, VIABILITY_REQUEST)
    require("external-access" in viability, "original viability request class still omits external-access")
    require("security" in viability, "original viability request class still omits security")
    require("helm-platform" in viability and "k3s-cluster" in viability and "observability" in viability, "viability dependency envelope regressed")

    paths = [
        "infrastructure/k3s-homelab/playbooks/tasks/cloudflare.yml",
        "infrastructure/k3s-homelab/playbooks/templates/cloudflared-values.yml.j2",
    ]
    expanded = module.expand_dependencies(payload, module.infer_context_ids(payload, "", paths))
    require("external-access" in expanded, "Cloudflare changed paths did not discover external-access")
    require("security" in expanded, "Cloudflare changed paths did not inherit security")

    phase_paths = ["markdown/Infrastructure/K3s_Homelab/04_Phased_Deployment.md"]
    phase_expanded = module.expand_dependencies(payload, module.infer_context_ids(payload, "", phase_paths))
    require("external-access" in phase_expanded and "security" in phase_expanded, "Phase 7 design authority is not classified as security/external-access")

    mutated = copy.deepcopy(payload)
    mutated["contexts"] = [c for c in mutated["contexts"] if c.get("id") != "external-access"]
    mutated_inferred = module.infer_for_request(mutated, request)
    require("external-access" not in mutated_inferred, "mutation-negative fixture still discovered removed external-access authority")

    mutated_security = copy.deepcopy(payload)
    for c in mutated_security["contexts"]:
        if c.get("id") == "security":
            c["match_terms"] = []
            c["path_prefixes"] = []
        if c.get("id") == "external-access":
            c["requires"] = [x for x in c.get("requires", []) if x != "security"]
    security_inferred = module.infer_for_request(mutated_security, "Review RBAC, secret handling, MFA, TLS, and privileged trust boundaries.")
    require("security" not in security_inferred, "mutation-negative fixture still discovered stripped security authority")

    print("PASS security and external-access request discovery")
    print("PASS original end-to-end viability request class includes security/external-access")
    print("PASS Cloudflare and Phase 7 changed paths preserve dependency authority")
    print("PASS security/external-access authority mutation negatives")
    print("Kalaxy3 SAGE security/external-access discovery guardrail: PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, TypeError, KeyError) as error:
        print("Kalaxy3 SAGE security/external-access discovery guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
