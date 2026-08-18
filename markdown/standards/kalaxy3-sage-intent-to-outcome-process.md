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

A request-execution child may also **already self-closed** when the repository-owned routine Git lifecycle consumes its receipt, performs post-operator verification, records metrics/evidence closeout, and marks the child boundary complete before the intent-to-outcome parent is resumed. In that case the parent **must not replay** the consumed Git boundary. Parent continuation validates the child request binding, canonical routine receipt and recorded digest, and the referenced verification/metrics/evidence closeout artifacts, then reconciles only the parent state to `source-git-complete` with `runtime-validation` as the next boundary.

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

A commit or push is persistence only. If an unfinished candidate is deliberately persisted, unresolved findings make that persistence a durable **non-promotable** checkpoint; persistence is not required before another same-class correction is accumulated into the current candidate. A persisted checkpoint is not objective failure, validation success, or promotion eligibility.

The one-time bootstrap seam may adopt a pre-front-door request execution as iteration 1 with an explicit historical candidate head and unresolved findings. For an iterative objective, adoption must also preserve the prior confirmed planning source and inherit the checksum-bound planning proposal from the adopted request-execution state; the source/proposal pair is validated before it becomes reusable lineage. This preserves the zero-trust iteration-1 lineage rather than rewriting or discarding it.

## Candidate union and serial validation

A governed objective may expose related defects incrementally. Serial validation
is expected and useful: validation may reveal A, then B, then C. That does **not**
require A, B, and C to become separately promotable changes.

When a newly observed defect belongs to the same Architect-authorized correction
class and the current candidate has not crossed into a live operator mutation
boundary, the unfinished candidate may be superseded by a cumulative candidate:

`A -> A+B -> A+B+C -> validate union -> checkpoint/promote`

The superseded revision is recorded as `superseded-in-progress`. It does not
have to become independently valid or promotable. A durable non-promotable
checkpoint remains available when persistence is useful, but persistence is not
a prerequisite for adding the next related correction. Promotion remains
fail-closed until the current union candidate satisfies every applicable
mandatory gate and has no unresolved findings.

A live `request-operator-review-required` boundary is not silently superseded by
this rule. Its outstanding mutation must first be dispositioned through a
governed path so an obsolete approved command cannot race a newer candidate.

## Authoritative shared-responsibility role contract

This workflow consumes the accepted `SAGE-ACTION-20260811-001` role contract;
it does not redefine the roles in workflow-local vocabulary. The following
responsibility boundaries remain authoritative:

- The metamodel defines four first-class participant classes: human participants,
  LLM, Kalaxy3 evidence/experience, and deterministic orchestration/execution,
  with SAGE defined as the governing system-engineering federation that
  reconciles their inputs into governed decisions.
- Human participant roles include stakeholder/sponsor/product owner,
  architect/engineer, operator, and reviewer/approver; the same human may hold
  multiple roles, and authority is represented as an explicit governed property
  rather than inferred from technical capability.
- Shared-responsibility vocabulary defines Accountable Owner, Responsible,
  Contributor, Authority-Approver, and optional Informed responsibilities per
  activity; capability overlap is allowed while accountability and legitimate
  authority remain explicit.
- The human Architect role has end-to-end accountable architectural
  responsibility for intended future state, requirements, constraints,
  Definition of Done, approval boundaries, and architectural fitness; multiple
  qualified humans may hold the role, but nothing inside SAGE can make the
  Architect unable to regain architectural control.
- Architect break-glass intervention is exceptional, explicit, minimum-scope,
  attributable, and records trigger, rationale, controls or assumptions
  overridden, resulting risk, and required post-verification; it cannot nullify
  external legal, security, compliance, or other nondelegable constraints, and
  recurring intervention classes become continuous-improvement evidence.
- The LLM is a first-class contributor of external/world knowledge,
  state-of-practice patterns, alternatives, critique, risk identification, and
  verification ideas, while remaining untrusted with authority: it cannot be
  the Accountable Architect, sole source of legitimate stakeholder intent, or
  holder of human-reserved approval authority.
- Kalaxy3 is explicitly modeled as accumulated local evidence and experience,
  including current facts, validated lessons, standards, workflow experience,
  measurements, and reusable capability; SAGE reconciles this local experience
  with human intent, LLM knowledge, and current evidence.
- Deterministic orchestration/execution owns reproducible workflow state,
  transitions, decisions, branches, retry, compensation, continuation, and exact
  mutation boundaries; LLM output may propose or inform these operations but
  does not own deterministic workflow state or transition authority.

## Intent-first innovation boundary

The LLM's architecture contribution is not limited to behavior or capability
names that current SAGE already understands. It expands the possible solution
space from the Architect-owned intended future state, requirements, constraints,
Definition of Done, approval boundaries, and architectural fitness, using its
defined contribution of external/world knowledge, state-of-practice patterns,
alternatives, critique, risk identification, and verification ideas.

The LLM may therefore propose innovative behavior, architectural capabilities,
and alternative solution constructs that are absent from current SAGE. Evidence
and risk then inform selection, including likelihood of successful
implementation, maturity and evidence of successful use, operational risk,
cost/economic basis, observability/measurement basis, security, reliability,
reversibility, portability, skills, vendor dependency, and uncertainty.
Experimental or novel alternatives are not excluded merely because SAGE does
not yet implement or name them; maturity and evidence deficits are explicit
inputs to Architect disposition.

Only after alternatives have been proposed and evaluated does SAGE reconcile
the selected or investigated direction with current repository capability,
evidence, constraints, authority, and deterministic transition mechanisms.
**Current SAGE capabilities constrain the governed transition path; they do not
define the future-state solution space.**

## Earliest affected boundary

SAGE re-enters only the **earliest affected boundary**:

- `implementation-local`: governing meaning, authority, capability requirements, safety/trust boundaries, and Architect-confirmed implementation scope are unchanged. The active mutation set may narrow to any subset of that confirmed implementation scope; merely touching a different subset of already-authorized paths does not require semantic restart. Expansion outside the confirmed scope does. SAGE reuses the confirmed semantic source and the prior complete component plan, so semantic discovery, evidence retrieval, and component reselection are not repeated.
- `planning`: confirmed semantic meaning and file scope remain valid, but planning/capability evaluation must be recomputed. SAGE reuses confirmed semantics and re-enters request planning.
- `semantic-confirmation`: meaning, scope, trust boundary, or another semantic condition changed. SAGE re-enters the existing semantic-bootstrap workflow.
- `authority`: the governing action or authority changed. SAGE records the invalidation and stops for the appropriate authority boundary rather than freelancing continuation.

Only downstream state at or after the selected boundary is invalidated. Runtime and promotion evidence from an earlier candidate never transfer automatically to a new iteration.

## Promotion separation

Runtime verification may make the current candidate eligible for promotion only when the current iteration has no unresolved findings. Checkpoint persistence, source validation, and remote synchronization remain insufficient by themselves.
