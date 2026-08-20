# Kalaxy3 SAGE Immutable Artifact Promotion Process

## Purpose

This standard defines the next coherent SAGE-ACTION-20260815-002 slice. The problem is specific: SAGE must deploy the exact OCI artifact that was already built and proven by the portable stage rather than rebuilding a second artifact after approval. The existing `mynginx_docs`/Nginx runtime pattern remains valid; this slice changes artifact identity and promotion semantics, not the application runtime architecture.

The inherited `doc` job in `.github/workflows/kalaxy3_build_publish.yml` is historical documentation-publication plumbing. It remains visible evidence and is not silently treated as the target SAGE application promotion architecture. This slice does not delete or modernize that job merely because it has Daux-era lineage.

This repository candidate is a **staged implementation** until an actual target promotion receipt and runtime deployment verification pass. Capability-catalog mapping means the repository capability exists and is deterministically testable; it does not fabricate production success evidence.

## Contract

Promotion consumes two governed inputs: a `sage-portable-stage-receipt` plus the retrieved OCI image-layout tar it cryptographically identifies, and a `sage-promotion-environment-manifest` that binds target registry/deployment authority without containing credentials. Retrieval mechanism and workflow engine are adapters/provenance; the local bytes must verify against the stage receipt before any registry mutation is permitted.

`promote.execute(stage receipt, OCI archive, environment manifest)` must:

1. verify the archive SHA-256, OCI index digest, and required linux/amd64 + linux/arm64 child digests against the stage receipt;
2. qualify the executor by required capabilities rather than machine, OS, CPU, runner, or workflow-engine identity;
3. keep registry credentials in executor runtime configuration only, never the environment manifest, command arguments, event log, or promotion receipt;
4. copy all OCI manifests with digest preservation and **never invoke a build**;
5. independently read the promoted target raw manifest/index and require its SHA-256 digest and required child descriptors to equal the proven stage values;
6. emit `sage-artifact-promotion-receipt` evidence whose deployment image reference is `repository@sha256:<proven-index-digest>`; and
7. fail closed if the stored artifact is missing/changed, digest preservation is impossible, executor capabilities are insufficient, target verification differs, or authority inputs are incomplete.

A human-readable registry tag is publication metadata only. Git SHA tags remain useful provenance/version labels but are not artifact identity. OCI digest is the deployment identity.

## Current adapter and alternatives

The first implementation proposes Skopeo as the OCI transfer adapter because its copy operation can copy all manifests and request digest preservation, and its raw inspection path supports independent target-manifest verification. Skopeo is an execution component, not SAGE authority, and the Architect may replace it with another adapter if the same contract is proven. Alternatives retained for governed disposition are ORAS with verified OCI-layout/digest-preservation behavior, a registry-native API adapter, or another content-addressed transfer tool. A rebuild-based adapter is prohibited because it violates the accepted intent.

## Environment binding

`infrastructure/k3s-homelab/cloudflare/sage-experience-promotion-environment.json` binds the current SAGE experience target repository and the existing Ansible/Kubernetes deployment seam. Promotion credentials are not stored in this manifest. A successful promotion receipt provides the exact digest-bound `target.image_ref`; the existing zero-trust playbook reads that receipt controller-locally, validates its environment and digest form, renders the existing `sage-experience` Deployment, and applies it through the existing Ansible/Kubernetes path.

This preserves the reasonable Nginx runtime, Traefik ingress, Cloudflare Tunnel, and Cloudflare Access MFA architecture while removing the hard-coded Git-SHA image tag from the deployment contract.

## Executor semantics

Executor identity, operating system, CPU architecture, host name/runner identity, and workflow-engine identity are evidence/provenance only. Promotion semantics are defined by the repository contract and required capabilities. A qualified workstation, GitHub Actions runner, Jenkins agent, Kubernetes/OpenShift workload, or future engine may execute the same promotion contract if it can verify the stage artifact, preserve OCI digests, access the authorized target, and independently inspect the result.

## Evidence and invalidation

The promotion receipt binds stage receipt SHA-256, source Git SHA, archive SHA-256, OCI index and platform digests, environment-manifest SHA-256, target reference, executor provenance, and verification outcomes. If source/stage evidence changes, re-enter stage. If only target environment binding changes, re-enter promotion/environment validation without rebuilding the already-proven artifact unless the stage artifact itself is invalidated. Runtime deployment/Access evidence remains a separate domain.

`observability.lifecycle-events` remains a deferred SAGE-ACTION-20260815-002 capability unless later evidence makes it a prerequisite. External workflow frameworks remain comparison/discovery inputs rather than SAGE authority.
