# Kalaxy3 SAGE Immutable Artifact Promotion Process

## Purpose

This standard defines the next coherent SAGE-ACTION-20260815-002 slice. The problem is specific: SAGE must deploy the exact OCI artifact that was already built and proven by the portable stage rather than rebuilding a second artifact after approval. The existing `mynginx_docs`/Nginx runtime pattern remains valid; this slice changes artifact identity and promotion semantics, not the application runtime architecture.

The inherited `doc` job in `.github/workflows/kalaxy3_build_publish.yml` is historical documentation-publication plumbing and also the predecessor production-image publication path. Its GitHub Pages and Slack behavior remains visible lineage evidence. Its former Docker Hub login plus `docker/build-push-action` production rebuild and Git-SHA `values.yaml` mutation are the exact publication behavior that this slice replaces; they must not remain active in parallel with immutable promotion.

That predecessor path also carries applicable security and authority evidence: Docker Hub publication already uses the repository's GitHub-managed `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets. SAGE must inspect and reuse or explicitly supersede an existing secure publication path before inventing another credential mechanism. For the current Action-002 composition, GitHub Actions remains the first publication executor and reuses those existing secret bindings. HashiCorp Vault remains the governed alternative when promotion moves to a different qualified executor; creating another Docker Hub credential or an ad-hoc operator-local credential store is not justified while the established publication authority remains applicable.

This repository candidate is a **staged implementation** until an actual target promotion receipt and runtime deployment verification pass. Capability-catalog mapping means the repository capability exists and is deterministically testable; it does not fabricate production success evidence.

## Contract

Promotion consumes two governed inputs: a `sage-portable-stage-receipt` plus the retrieved OCI image-layout tar it cryptographically identifies, and a `sage-promotion-environment-manifest` that binds target registry/deployment authority without containing credentials. Retrieval mechanism and workflow engine are adapters/provenance; the local bytes must verify against the stage receipt before any registry mutation is permitted.

`promote.execute(stage receipt, OCI archive, environment manifest)` must:

1. verify the archive SHA-256, OCI index digest, and required linux/amd64 + linux/arm64 child digests against the stage receipt;
2. qualify the executor by required capabilities rather than machine, OS, CPU, runner, or workflow-engine identity;
3. obtain registry credentials only from a governed secret provider already applicable to the selected execution domain, keep them in executor runtime configuration only, and never place them in the environment manifest, command arguments, event log, or promotion receipt; the current GitHub Actions composition reuses the existing `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` GitHub Secrets, while a non-GitHub executor must use HashiCorp Vault or another Architect-approved governed secret provider rather than an ad-hoc local login;
4. copy all OCI manifests with digest preservation and **never invoke a build**;
5. independently read the promoted target raw manifest/index and require its SHA-256 digest and required child descriptors to equal the proven stage values;
6. emit `sage-artifact-promotion-receipt` evidence whose deployment image reference is `repository@sha256:<proven-index-digest>`; and
7. fail closed if the stored artifact is missing/changed, digest preservation is impossible, executor capabilities are insufficient, target verification differs, or authority inputs are incomplete.

A human-readable registry tag is publication metadata only. Git SHA tags remain useful provenance/version labels but are not artifact identity. OCI digest is the deployment identity.

## Current adapter and alternatives

The first implementation proposes Skopeo as the OCI transfer adapter because its copy operation can copy all manifests and request digest preservation, and its raw inspection path supports independent target-manifest verification. Skopeo is an execution component, not SAGE authority, and the Architect may replace it with another adapter if the same contract is proven. Alternatives retained for governed disposition are ORAS with verified OCI-layout/digest-preservation behavior, a registry-native API adapter, or another content-addressed transfer tool. A rebuild-based adapter is prohibited because it violates the accepted intent.

## Publication-lineage composition

The current repository composition preserves GitHub Actions as the trusted publication executor because the predecessor production workflow already demonstrates the required Docker Hub authority and secret-management boundary. Publication is **not** automatic on source push. The operator/Architect explicitly selects the `promote-proven-stage` `workflow_dispatch` operation, supplies the exact source SHA and the successful portable-stage workflow-run ID, and dispatches from that exact source ref.

The promotion job then:

1. checks out and verifies the exact dispatched source SHA before credentials are present;
2. downloads the source-SHA-named OCI archive and portable-stage receipt from the explicitly selected prior workflow run using GitHub's artifact API and read-only Actions permission;
3. verifies receipt source/run/artifact lineage and runs `sage-artifact-promotion-prepare` before registry credentials are exposed;
4. reuses the existing `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` GitHub Secrets through `docker/login-action`; Skopeo is permitted to consume the resulting Docker-compatible executor credential state without receiving a secret on its command line;
5. runs the repository-owned `sage-artifact-promotion-execute` contract, requires exact stage/target digest equality and `rebuild_performed=false`; and
6. persists only non-secret promotion receipt/event/prepare evidence for SAGE reconciliation.

The legacy main-branch documentation job no longer performs a production OCI rebuild or mutates a Git-SHA image version. Documentation publication remains independent of artifact promotion. If GitHub Actions is later replaced by another qualified executor, the immutable promotion contract remains unchanged; only executor and governed-secret-provider provenance changes.

## Environment binding

`infrastructure/k3s-homelab/cloudflare/sage-experience-promotion-environment.json` binds the current SAGE experience target repository and the existing Ansible/Kubernetes deployment seam. Promotion credentials are not stored in this manifest. A successful promotion receipt provides the exact digest-bound `target.image_ref`; the existing zero-trust playbook reads that receipt controller-locally, validates its environment and digest form, renders the existing `sage-experience` Deployment, and applies it through the existing Ansible/Kubernetes path.

This preserves the reasonable Nginx runtime, Traefik ingress, Cloudflare Tunnel, and Cloudflare Access MFA architecture while removing the hard-coded Git-SHA image tag from the deployment contract.

## Executor semantics

Executor identity, operating system, CPU architecture, host name/runner identity, and workflow-engine identity are evidence/provenance only. Promotion semantics are defined by the repository contract and required capabilities. For this SAGE-ACTION-20260815-002 publication slice, GitHub Actions is the selected qualified promotion executor and local workstation promotion execution is not permitted. This selection does not make GitHub Actions part of artifact or promotion semantics: a future governed slice may select another qualified non-local executor, such as a Jenkins agent or Kubernetes/OpenShift workload, only when its publication authority and governed secret source are explicitly approved and it can verify the stage artifact, preserve OCI digests, access the authorized target, and independently inspect the result.

## Evidence and invalidation

The promotion receipt binds stage receipt SHA-256, source Git SHA, archive SHA-256, OCI index and platform digests, environment-manifest SHA-256, target reference, executor provenance, and verification outcomes. If source/stage evidence changes, re-enter stage. If only target environment binding changes, re-enter promotion/environment validation without rebuilding the already-proven artifact unless the stage artifact itself is invalidated. Runtime deployment/Access evidence remains a separate domain.

`observability.lifecycle-events` remains a deferred SAGE-ACTION-20260815-002 capability unless later evidence makes it a prerequisite. External workflow frameworks remain comparison/discovery inputs rather than SAGE authority.
