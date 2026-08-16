#!/usr/bin/env python3
"""Guard the first portable-stage contract and its explicit legacy demarcation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/kalaxy3_build_publish.yml").read_text(encoding="utf-8")
    dockerfile = (ROOT / "yaml/nginx-docs/k8s-doc-to-nginx/nginx/Dockerfile.stage").read_text(encoding="utf-8")
    process = (ROOT / "markdown/standards/kalaxy3-sage-portable-stage-process.md").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "markdown/standards/sage-portable-stage-receipt-schema-v1.0.json").read_text(encoding="utf-8"))

    require("sage-stage-guardrails:" in makefile, "portable stage source-guardrail target missing")
    require("sage-e2e-zero-trust-source-guardrail:" in makefile, "source-only zero-trust guardrail missing")
    require("sage-e2e-zero-trust-controller-guardrail:" in makefile, "controller-only zero-trust guardrail missing")
    require("sage-guardrails: sage-stage-guardrails sage-e2e-zero-trust-controller-guardrail" in makefile, "full repository guardrail no longer retains controller validation")
    stage_block = makefile.split("sage-stage-guardrails:", 1)[1].split("sage-guardrails:", 1)[0]
    require("cluster-guardrails" not in stage_block and ".venv/bin/ansible-playbook" not in stage_block, "portable stage transitively names controller/live-cluster execution")

    require("make sage-stage-guardrails" in workflow, "GitHub source validation does not invoke portable stage guardrails")
    require("Portable OCI stage artifact" in workflow, "portable stage check is missing")
    require("yaml/nginx-docs/k8s-doc-to-nginx/nginx/Dockerfile.stage" in workflow, "portable stage Dockerfile is not invoked")
    require("linux/amd64,linux/arm64" in workflow, "portable stage does not build both required architectures")
    require("stage-${{ github.sha }}" in workflow, "portable stage tag is not source-SHA bound")
    require("outputs: type=oci,dest=${{ env.STAGE_ARCHIVE }}" in workflow, "portable stage does not export an OCI image-layout artifact")
    require("push: false" in workflow, "portable source stage unexpectedly pushes directly to a registry")
    require("docker/login-action" not in workflow.split("  portable-stage:", 1)[1].split("\n  doc:", 1)[0], "portable source stage consumes external registry credentials")
    require("actions/upload-artifact@v4" in workflow, "portable stage artifact/receipt is not persisted")
    require("steps.stage_artifact.outputs.artifact-digest" in workflow, "stage receipt is not bound to immutable workflow-artifact digest")
    require("scripts/sage/sage-stage-receipt.py" in workflow, "portable stage receipt producer is not invoked")
    require("github.ref == 'refs/heads/main'" in workflow, "main writer is not explicitly restricted after broadening push validation")

    for marker in (
        "FROM python:3.12-slim AS stage",
        "RUN make sage-stage-guardrails",
        "docs-mkdocs-publication-test",
        "FROM nginx AS runtime",
        "COPY --from=stage /workspace/.mkdocs-work/publication-test/docs/",
        'io.kalaxy3.sage.stage-contract="portable-stage-v1"',
    ):
        require(marker in dockerfile, f"portable stage Dockerfile missing marker: {marker}")
    require("cluster-guardrails" not in dockerfile and ".venv/bin/ansible-playbook" not in dockerfile, "portable stage image contains controller/live-cluster execution")

    require(schema.get("properties", {}).get("record_type", {}).get("const") == "sage-portable-stage-receipt", "portable stage receipt schema drifted")
    storage = schema.get("properties", {}).get("artifact", {}).get("properties", {}).get("storage", {}).get("properties", {})
    require(storage.get("provider", {}).get("const") == "github-actions-artifact", "portable stage receipt storage identity drifted")
    build = schema.get("properties", {}).get("build_contract", {}).get("properties", {})
    require(build.get("external_registry_credentials_used", {}).get("const") is False, "portable stage receipt allows external registry credentials")
    for marker in (
        "GitHub Actions is an invoker, not the stage definition",
        "production rebuild remains legacy in this first slice",
        "digest is artifact identity",
        "no Docker Hub login or other external registry credential",
        "PR #21",
        "AWS",
        "Azure",
        "Google Cloud",
        "IBM Cloud",
    ):
        require(marker in process, f"portable stage process missing marker: {marker}")

    print("PASS hosted stage and controller/live-cluster validation domains are separated")
    print("PASS repository-owned multi-architecture OCI stage artifact and receipt contract")
    print("PASS source-stage artifact creation uses no external registry credential")
    print("PASS immutable workflow-artifact storage identity is receipt-bound")
    print("PASS legacy production rebuild is explicitly demarcated rather than silently claimed as promotion")
    print("Kalaxy3 SAGE portable stage guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE portable stage guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
