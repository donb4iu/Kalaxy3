# Kalaxy3 SAGE Portable Stage Process

## Status and scope

This standard defines the first prospective delivery slice after PR #21. It is a **staged implementation**: it introduces a portable source-validation and multi-architecture OCI stage-artifact contract plus exact-source CI convergence, while leaving the existing main-branch production rebuild path in place until a later governed slice can consume the stage receipt and promote the exact artifact. The production rebuild remains legacy in this first slice and must not be described as build-once promotion.

The four-role SAGE architecture remains authoritative. Human/Architect authority, LLM contribution, Kalaxy3 evidence/experience, and deterministic orchestration/execution retain their existing responsibilities. A CI engine, runner, container builder, artifact store, stage artifact, receipt, or environment manifest does not acquire semantic or approval authority.

## Portable stage contract v1

The portable stage is defined by repository-owned source, not by one runner product. GitHub Actions is an invoker, not the stage definition. The first implementation uses GitHub-hosted Linux runners to invoke repository Make targets and Buildx, but the same Dockerfile and receipt contract can be invoked by a self-hosted builder, Kubernetes build pod, or another workflow engine without changing SAGE authority semantics.

The contract has three parts:

1. `make sage-stage-guardrails` is the hosted/source-safe SAGE validation domain. It deliberately excludes controller-local `.venv`, kubeconfig/SSH, live-cluster access, and runtime deployment operations. `make sage-guardrails` remains the full controller-capable contract and still includes those validations where applicable.
2. `yaml/nginx-docs/k8s-doc-to-nginx/nginx/Dockerfile.stage` defines the source-to-runtime build. Its stage image runs source-safe SAGE validation and strict MkDocs publication validation, then the runtime image copies only the already-validated generated site. Buildx exports one OCI image-layout tar containing Linux amd64 and arm64 manifests.
3. `sage-portable-stage-receipt` binds the exact source Git SHA to the OCI index digest, archive digest, required child-platform digests, and immutable workflow-artifact storage identity. The OCI tar SHA-256 and the GitHub artifact-container SHA-256 are recorded separately. A human-readable logical tag such as `stage-<source-sha>` is metadata only; digest is artifact identity.

A feature-branch `push` is intentionally used for the authoritative source-stage checks because GitHub's `pull_request` execution context may use a synthetic merge ref. The stage check therefore binds to the exact feature-branch source SHA that SAGE freezes for promotion. PR validation may still run as additional integration evidence.

## Stage trust boundary

The source branch and its generated candidate are not permitted to receive production or external-registry credentials merely to create stage evidence. The first stage implementation exports the multi-architecture result locally as an OCI image-layout tar and persists it through an immutable GitHub Actions artifact. The job has read-only repository permission and no Docker Hub login or other external registry credential. This keeps artifact construction separate from later publication/promotion authority.

GitHub Actions artifact retention is finite. Therefore a stage artifact is eligible for later promotion only while the immutable stored artifact and its bound receipt remain available and verify successfully. Expiration or loss is not permission to rebuild during promotion; it invalidates that stage artifact and requires governed re-entry to stage.

## Promotion convergence

Checkpoint promotion still performs its repository/controller validations locally. After the operator creates the PR, `github.inspect` additionally reads GitHub's GET-only check-run API for the frozen source SHA and fails closed unless all policy-required GitHub Actions checks are completed with `success`. Mergeability alone is no longer evidence of CI success.

The first required checks are:

- `SAGE source governance`
- `MkDocs Material publication validation`
- `Portable OCI stage artifact`

This directly closes the PR #21 defect in which a red hosted-CI result remained visible but did not participate in checkpoint-promotion convergence. PR #21 remains immutable historical evidence; this contract is prospective.

## Artifact and production demarcation

Stage v1 emits a source-SHA-bound multi-architecture OCI image-layout tar and a receipt containing the OCI index digest, archive SHA-256, amd64 and arm64 child digests, and GitHub artifact storage identity/digest. The stage artifact is created without external-registry credentials.

This slice intentionally does **not** change the existing `main` publication job that rebuilds the documentation image, pushes it to Docker Hub, and updates `values.yaml`. That path is the historical production behavior and remains a known capability gap. A subsequent governed slice must replace it with `promote.execute(stage receipt, environment manifest)`, retrieve and verify the exact frozen stage artifact, bind target publication/deployment authority, publish or deploy the exact already-proven OCI content without rebuilding, and emit target runtime evidence. Until that slice is validated, no production build-once claim is permitted.

## Current engineering guidance corroboration

The following vendor guidance is corroborating engineering evidence, not SAGE authority and not a vendor selection:

- **AWS** documents OCI image support in Amazon ECR and multi-architecture images through manifest lists. Sources: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-manifest-formats.html and https://docs.aws.amazon.com/AmazonECR/latest/userguide/docker-push-multi-architecture-image.html
- **Microsoft Azure** documents a manifest digest as the unique SHA-256 identity of an artifact and supports manifest lists/OCI image indexes for multi-architecture images in Azure Container Registry. Sources: https://learn.microsoft.com/en-us/azure/container-registry/container-registry-concepts and https://learn.microsoft.com/en-us/azure/container-registry/push-multi-architecture-images
- **Google Cloud** documents OCI image indexes/manifest lists as multi-platform image structures and distinguishes tags from image-digest identity in Artifact Registry. Sources: https://cloud.google.com/artifact-registry/docs/supported-formats and https://cloud.google.com/artifact-registry/docs/docker/names
- **IBM Cloud** documents image digests as immutable references to image manifests and supports manifest lists/OCI image indexes whose child manifests represent different architectures. Sources: https://cloud.ibm.com/docs/Registry?topic=Registry-registry_overview and https://cloud.ibm.com/docs/Registry?topic=Registry-troubleshoot-manifest-list-error
- **Docker/BuildKit** documents the OCI exporter as a local OCI image-layout tar output and multi-platform builds as one manifest list/index over the requested platforms. Source: https://docs.docker.com/reference/cli/docker/buildx/build/
- **GitHub Actions** documents v4 artifacts as immutable and exposes a SHA-256 artifact digest. GitHub security guidance also requires least-privilege credentials and treats runner code as able to access credentials supplied to that job. Sources: https://github.com/actions/upload-artifact and https://docs.github.com/en/actions/reference/security/secure-use

The common implementation-neutral conclusion is: generate and validate once in stage, identify the result by content digest, preserve multi-platform child identity, keep untrusted/source-stage execution away from production credentials, and make later environment promotion consume that immutable identity rather than rebuilding it.

## Deferred action-002 obligations

This first slice does not close all of SAGE-ACTION-20260815-002. The following remain governed follow-on work:

- replace the legacy main rebuild with exact stage-receipt/artifact promotion and target environment binding;
- define environment manifests and environment-specific secret/routing/topology/runtime verification;
- establish durable artifact retention/publication authority appropriate for production promotion;
- pin or otherwise govern mutable base-image inputs where bit-for-bit repeatability is required;
- separate build, stage, controller-qualification, promotion, and runtime evidence invalidation domains;
- reconcile a separately completed promotion child into parent intent state without historical rewriting;
- codify constraint-aware governed phasing as a reusable lifecycle contract;
- expose the PR #21 lineage, decision, prevented defect, stage evidence, learning, and delivered value in the external SAGE thin-slice experience.
