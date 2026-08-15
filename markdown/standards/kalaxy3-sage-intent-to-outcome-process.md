# Kalaxy3 SAGE intent-to-outcome process

## Purpose

The intent-to-outcome front door is a thin repository-owned composition over existing SAGE child workflows. It does not create a parallel orchestration system and it does not duplicate primitive behavior.

The normal lifecycle is:

Architect intent → semantic understanding → Architect dispositions → request planning → request execution → routine Git lifecycle → runtime evidence → checkpoint promotion.

## Existing component rule

The front door calls the existing semantic bootstrap, request planning, request execution, routine-receipt continuation, and checkpoint promotion compositions. It must not acquire direct Git, GitHub, credential, Kubernetes, Helm, or Ansible mutation authority.

A new low-level primitive still requires a separately proven capability gap.

## One-time bootstrap seam

The first installation of this front door necessarily uses the already-established semantic-bootstrap, request-planning, and request-execution path. After the source exists in the repository, `adopt-request` may bind that in-flight request-execution state into the new parent lifecycle. This one-time bootstrap seam is explicit evidence, not a normal operating mode.

## Runtime evidence

Source validation and Git persistence do not prove the operational outcome. Promotion is blocked until a versioned zero-trust runtime receipt proves workload readiness, the Traefik origin path, tunnel readiness, monitoring configuration, unauthenticated Access interception, authorized MFA access, and non-publication of privileged management surfaces.

Automated runtime validation must not fabricate a human MFA success or Cloudflare-account route review. The repository-owned runtime receipt command combines automated evidence only after the Architect explicitly verifies those trust-boundary outcomes.

## Checkpoint promotion

After runtime acceptance, the front door delegates promotion to the existing checkpoint-promotion composition. Browser approval boundaries and exact merge verification remain unchanged.

Safe local-main reconciliation and source-branch retirement remain part of this E2E Definition of Done. The current checkpoint-promotion controller has already demonstrated that it stops before those final actions; this slice must treat that as a remaining composition gap to close without bypassing existing Git safety primitives.
