# Kalaxy3 SAGE intent-to-outcome process

## Purpose

The intent-to-outcome front door is a thin repository-owned composition over existing SAGE child workflows. It does not create a parallel orchestration system and it does not duplicate primitive behavior.

The normal lifecycle is:

Architect intent → semantic understanding → Architect dispositions → request planning → candidate iteration(s) → request execution → routine Git lifecycle → runtime evidence → checkpoint promotion.

## Existing component rule

The front door calls the existing semantic bootstrap, request planning, request execution, routine-receipt continuation, and checkpoint promotion compositions. It must not acquire direct Git, GitHub, credential, Kubernetes, Helm, or Ansible mutation authority.

A new low-level primitive still requires a separately proven capability gap.

## Child-interface compatibility

The front door must consume published child-workflow results through compatibility-resolved interfaces. A child that has already completed semantic confirmation and persisted a planning source must not be rerun merely because a parent wrapper expected a different compatible result-field name. Recovery preserves the completed child state and resumes at planning.

## One-time bootstrap seam

The first installation of this front door necessarily uses the already-established semantic-bootstrap, request-planning, and request-execution path. After the source exists in the repository, `adopt-request` may bind that in-flight request-execution state into the new parent lifecycle. This one-time bootstrap seam is explicit evidence, not a normal operating mode.

## Runtime evidence

Source validation and Git persistence do not prove the operational outcome. Promotion is blocked until a versioned zero-trust runtime receipt proves workload readiness, the Traefik origin path, tunnel readiness, monitoring configuration, unauthenticated Access interception, authorized MFA access, and non-publication of privileged management surfaces.

Automated runtime validation must not fabricate a human MFA success or Cloudflare-account route review. The repository-owned runtime receipt command combines automated evidence only after the Architect explicitly verifies those trust-boundary outcomes.

## Checkpoint promotion

After runtime acceptance, the front door delegates promotion to the existing checkpoint-promotion composition. Browser approval boundaries and exact merge verification remain unchanged.

Safe local-main reconciliation and source-branch retirement remain part of this E2E Definition of Done. The current checkpoint-promotion controller has already demonstrated that it stops before those final actions; this slice must treat that as a remaining composition gap to close without bypassing existing Git safety primitives.


## Governed candidate iteration

The active objective is distinct from its mutable **candidate iteration**. Each iteration records its number, parent checkpoint, triggering observation, affected planning obligations, validation state, unresolved findings, accumulated learning, invalidated downstream state, next governed boundary, and promotion eligibility.

A commit or push is persistence only. A candidate with unresolved findings is a durable **non-promotable** checkpoint; it is not objective failure, validation success, or promotion eligibility.

The one-time bootstrap seam may adopt a pre-front-door request execution as iteration 1 with an explicit historical candidate head and unresolved findings. For an iterative objective, adoption must also preserve the prior confirmed planning source and inherit the checksum-bound planning proposal from the adopted request-execution state; the source/proposal pair is validated before it becomes reusable lineage. This preserves the zero-trust iteration-1 lineage rather than rewriting or discarding it.

## Earliest affected boundary

SAGE re-enters only the **earliest affected boundary**:

- `implementation-local`: governing meaning, authority, capability requirements, safety/trust boundaries, and Architect-confirmed implementation scope are unchanged. The active mutation set may narrow to any subset of that confirmed implementation scope; merely touching a different subset of already-authorized paths does not require semantic restart. Expansion outside the confirmed scope does. SAGE reuses the confirmed semantic source and the prior complete component plan, so semantic discovery, evidence retrieval, and component reselection are not repeated.
- `planning`: confirmed semantic meaning and file scope remain valid, but planning/capability evaluation must be recomputed. SAGE reuses confirmed semantics and re-enters request planning.
- `semantic-confirmation`: meaning, scope, trust boundary, or another semantic condition changed. SAGE re-enters the existing semantic-bootstrap workflow.
- `authority`: the governing action or authority changed. SAGE records the invalidation and stops for the appropriate authority boundary rather than freelancing continuation.

Only downstream state at or after the selected boundary is invalidated. Runtime and promotion evidence from an earlier candidate never transfer automatically to a new iteration.

## Promotion separation

Runtime verification may make the current candidate eligible for promotion only when the current iteration has no unresolved findings. Checkpoint persistence, source validation, and remote synchronization remain insufficient by themselves.
