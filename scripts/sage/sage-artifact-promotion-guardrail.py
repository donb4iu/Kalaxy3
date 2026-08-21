#!/usr/bin/env python3
"""Guard exact-digest OCI promotion, environment binding, and executor semantics."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    workflow = (ROOT / "scripts/sage/workflows/artifact_promotion.py").read_text(encoding="utf-8")
    cli = (ROOT / "scripts/sage/sage-artifact-promote.py").read_text(encoding="utf-8")
    process = (ROOT / "markdown/standards/kalaxy3-sage-artifact-promotion-process.md").read_text(encoding="utf-8")
    environment = json.loads((ROOT / "infrastructure/k3s-homelab/cloudflare/sage-experience-promotion-environment.json").read_text(encoding="utf-8"))
    experience = (ROOT / "infrastructure/k3s-homelab/cloudflare/sage-experience.yaml.j2").read_text(encoding="utf-8")
    deploy = (ROOT / "infrastructure/k3s-homelab/cloudflare/deploy-sage-e2e.yml").read_text(encoding="utf-8")
    validate = (ROOT / "infrastructure/k3s-homelab/cloudflare/validate-sage-e2e.yml").read_text(encoding="utf-8")
    ci_workflow = (ROOT / ".github/workflows/kalaxy3_build_publish.yml").read_text(encoding="utf-8")
    receipt_schema = json.loads((ROOT / "markdown/standards/sage-artifact-promotion-receipt-schema-v1.0.json").read_text(encoding="utf-8"))
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    baseline = json.loads((ROOT / "markdown/standards/sage-capability-intelligence-workflow-capability-baseline-v1.0.json").read_text(encoding="utf-8"))

    for marker in ("skopeo", "--all", "--preserve-digests", "--raw", "inspect_oci_archive", "rebuild_performed", "identity_is_provenance_only"):
        require(marker in workflow, f"artifact promotion workflow missing marker: {marker}")
    for forbidden in ("docker build", "docker buildx", "build-push-action", "buildx build"):
        require(forbidden not in workflow.lower() and forbidden not in cli.lower(), f"promotion execution retains build path: {forbidden}")
    require('"secrets_in_command_arguments": False' in workflow, "promotion receipt does not explicitly deny secret command arguments")
    require("repository@sha256" in process, "promotion standard does not define digest-bound deployment identity")
    require("Git SHA tags" in process and "not artifact identity" in process, "Git-SHA tag vs OCI digest semantics are not explicit")
    require("historical documentation-publication plumbing" in process, "legacy doc workflow lineage is not correctly classified")
    require("predecessor production-image publication path" in process, "predecessor registry publication lineage is not explicit")
    require("DOCKERHUB_USERNAME" in process and "DOCKERHUB_TOKEN" in process, "existing governed Docker Hub secret lineage is not documented")
    require("HashiCorp Vault" in process, "governed non-GitHub secret-provider alternative is not retained")

    for marker in (
        "promote-proven-stage",
        "promotion_source_sha",
        "promotion_stage_run_id",
        "actions/download-artifact@v4",
        "github-token: ${{ github.token }}",
        "docker/login-action@v3",
        "secrets.DOCKERHUB_USERNAME",
        "secrets.DOCKERHUB_TOKEN",
        "make sage-artifact-promotion-prepare",
        "make sage-artifact-promotion-execute",
        "sage-promotion-evidence-",
    ):
        require(marker in ci_workflow, f"GitHub publication composition missing marker: {marker}")
    require(
        "if: github.event_name == 'workflow_dispatch' && inputs.operation == 'promote-proven-stage'" in ci_workflow,
        "immutable promotion is not explicitly manual-dispatch gated",
    )
    require(
        "if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request' && github.event_name == 'push'" in ci_workflow,
        "historical documentation publication does not preserve inherited non-PR enforcement while restricting execution to main push",
    )
    require(
        "GitHub Actions is the selected qualified promotion executor" in process
        and "local workstation promotion execution is not permitted" in process,
        "Architect-selected GitHub-only publication constraint is not preserved",
    )
    require(ci_workflow.count("docker/build-push-action@v6") == 1, "legacy production build-push path remains alongside portable stage")
    require(ci_workflow.count("docker/login-action@v3") == 1, "Docker Hub credential exposure exists outside the single promotion boundary")
    require("push: true" not in ci_workflow, "GitHub workflow still contains a production rebuild/push path")
    portable_index = ci_workflow.index("  portable-stage:")
    doc_index = ci_workflow.index("  doc:")
    promotion_index = ci_workflow.index("  promote-proven-stage:")
    require(
        portable_index < doc_index < promotion_index,
        "workflow job order no longer preserves portable-stage/doc/promotion trust-region separation",
    )
    portable_region = ci_workflow[portable_index:doc_index]
    doc_region = ci_workflow[doc_index:promotion_index]
    promotion_region = ci_workflow[promotion_index:]
    require(
        "DOCKERHUB_" not in portable_region and "docker/login-action" not in portable_region,
        "portable stage gained production registry credentials",
    )
    require(
        "DOCKERHUB_" not in doc_region and "docker/login-action" not in doc_region,
        "historical documentation job still carries Docker Hub credentials",
    )
    require(
        "secrets.DOCKERHUB_USERNAME" in promotion_region
        and "secrets.DOCKERHUB_TOKEN" in promotion_region
        and promotion_region.count("docker/login-action@v3") == 1,
        "Docker Hub authority is not isolated to the immutable-promotion job",
    )
    prepare_index = ci_workflow.index("make sage-artifact-promotion-prepare")
    login_index = ci_workflow.index("docker/login-action@v3")
    execute_index = ci_workflow.index("make sage-artifact-promotion-execute")
    require(prepare_index < login_index < execute_index, "registry credentials are exposed before promotion prepare or execute ordering drifted")
    tool_name_schema = receipt_schema["properties"]["executor"]["properties"]["tool"]["properties"]["name"]
    require(tool_name_schema.get("type") == "string" and "const" not in tool_name_schema, "promotion receipt schema pins one adapter identity")

    require(environment.get("record_type") == "sage-promotion-environment-manifest", "current environment manifest type drifted")
    require(environment.get("authority") == {"registry_credentials": "executor-runtime-only", "secrets_in_manifest": False, "secrets_in_command_arguments": False}, "environment manifest authority leaks secret semantics")
    require(environment.get("executor_contract", {}).get("identity_is_provenance_only") is True, "executor identity became promotion semantics")
    require(environment.get("artifact_target", {}).get("repository") == "docker.io/donb4iu/mynginx_docs", "current SAGE experience target repository drifted")

    require("image: \"{{ sage_experience_image_ref }}\"" in experience, "SAGE experience is not bound through the verified promotion image ref")
    require("donb4iu/mynginx_docs:566d215fc0a077cb9330a69b08716a53903e6fe0" not in experience, "historical Git-SHA image tag remains hard-coded")
    for marker in ("sage_promotion_receipt_file", "sage-artifact-promotion-receipt", "kalaxy3-home-sage-experience", "sage_experience_image_ref", "@sha256:"):
        require(marker in deploy, f"deployment does not consume promotion receipt: {marker}")
    require("sage_experience_object.spec.template.spec.containers[0].image == sage_expected_image_ref" in validate, "runtime validation does not prove deployed digest-bound image identity")

    mappings = {}
    for family in baseline["families"]:
        for capability in family["capabilities"]:
            mappings[capability["capability_id"]] = capability
    for capability_id in ("artifact.promote-without-rebuild", "environment.binding", "execution.qualified-executor"):
        item = mappings[capability_id]
        require(item.get("disposition") == "implemented" and item.get("implementation"), f"{capability_id} is not mapped to the implemented candidate")
    require("sage-artifact-promotion-self-test" in makefile and "sage-artifact-promotion-guardrail" in makefile, "root Make integration missing artifact-promotion validation")

    print("PASS exact OCI artifact promotion is build-free and digest-preserving")
    print("PASS target registry and deployment binding are explicit non-secret environment authority")
    print("PASS predecessor GitHub publication authority is reused through existing managed Docker Hub secrets")
    print("PASS promotion prepare precedes credential exposure and manual dispatch gates registry mutation")
    print("PASS legacy GitHub production rebuild/push is removed while portable-stage build remains")
    print("PASS executor/tool identity remains replaceable provenance in the promotion receipt schema")
    print("PASS executor qualification is capability-based; engine/machine identity is provenance only")
    print("PASS SAGE experience consumes a promotion receipt and deploys by OCI digest")
    print("PASS three Action-002 workflow capability gaps map to one coherent implementation")
    print("Kalaxy3 SAGE artifact promotion guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE artifact promotion guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
