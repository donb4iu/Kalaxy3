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

The parent must also **persist the planning source before planning**. Semantic confirmation and request planning are separate evidence domains: if semantic confirmation succeeds and planning later fails closed, the parent may not remain falsely recorded as still waiting for Architect confirmation. A **planning failure** therefore preserves the already-completed semantic child, the checksum-bound planning source, and `planning` as the next governed boundary. The parent may then enter a governed candidate iteration without replaying semantic confirmation.

Request planning and request mutation are also separate authority domains. After planning produces the **exact planning proposal**, the front door persists that proposal and stops at an Architect **objective-path decision** boundary before calling request execution. The decision is checksum-bound to the literal request and exact proposal package. `continue-planned` resumes the same persisted proposal only after that Architect authority is available; it does not replan, substitute a candidate, or create a second semantic-confirmation cycle. The same split applies to initial semantic-confirmation completion and later candidate iterations so a plan-then-execute composition cannot outrun its own mutation-authority gate.

If the semantic child was completed directly or by another compatible caller, the parent validates the child request, action, contribution, confirmation digest, Architect disposition digest, and planning-source existence before reconciling it. This **completed semantic child** reconciliation changes only parent orchestration state; it does not regenerate semantic evidence or fabricate a second confirmation.

A request-execution child may also **already self-closed** when the repository-owned routine Git lifecycle consumes its receipt, performs post-operator verification, records metrics/evidence closeout, and marks the child boundary complete before the intent-to-outcome parent is resumed. In that case the parent **must not replay** the consumed Git boundary. Parent continuation validates the child request binding, canonical routine receipt and recorded digest, and the referenced verification/metrics/evidence closeout artifacts, then reconciles only the parent state to `source-git-complete` with `runtime-validation` as the next boundary.

The completed-child reconciliation also binds the **canonical routine receipt commit**
to the current iteration's `candidate_head`. The normal continuation and stale-parent
reconciliation paths must derive that exact source identity from the same verified
receipt rather than maintain separate interpretations.

Runtime acceptance fails closed when the current iteration has no candidate source
commit. Runtime evidence cannot create an implementation generation whose source
identity is unknown. Repair of missing parent lineage never edits intent state by
hand and never replays an already consumed Git lifecycle boundary.

## One-time bootstrap seam

The first installation of this front door necessarily uses the already-established semantic-bootstrap, request-planning, and request-execution path. After the source exists in the repository, `adopt-request` may bind that in-flight request-execution state into the new parent lifecycle. This one-time bootstrap seam is explicit evidence, not a normal operating mode.

## Runtime evidence

Source validation and Git persistence do not prove the operational outcome. Promotion is blocked until a versioned zero-trust runtime receipt proves workload readiness, the Traefik origin path, tunnel readiness, monitoring configuration, unauthenticated Access interception, authorized MFA access, and non-publication of privileged management surfaces.

Automated runtime validation must not fabricate a human MFA success or Cloudflare-account route review. The repository-owned runtime receipt command combines automated evidence only after the Architect explicitly verifies those trust-boundary outcomes.

## Checkpoint promotion

After runtime acceptance, the front door delegates promotion to the existing checkpoint-promotion composition. Browser approval boundaries and exact merge verification remain unchanged.

Safe local-main reconciliation and source-branch retirement remain part of this E2E Definition of Done. The checkpoint-promotion composition closes the bounded pre-promotion reconciliation case in which both the source branch and current `main` have unique, disjoint-path changes: it emits operator-executed merge and push boundaries, proves exact merge-parent topology, and immediately re-enters full checkpoint promotion against current target authority. Overlapping-path reconciliation still fails closed for Architect disposition. After successful promotion, the existing branch-lifecycle composition owns the separate post-promotion closeout: it independently proves source containment and stable remote authority, governs operator-executed fast-forward-only local-main reconciliation and exact remote/local source retirement, and emits a **repository-lineage milestone**. Git remains the delegated high-resolution mechanical chronicle; the SAGE milestone preserves implementation-neutral objective meaning, authority anchors, verified lineage assertions, and durable reconstruction references without duplicating every Git event.


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

Before a governance re-entry is consumed or rejected as a duplicate, the parent
filters recovery decisions to the **current recovery composition** using the
repository-owned composition digest recorded in governing evidence. A
**historical consumed recovery decision** from an older composition remains visible
as history but does not block a candidate whose governing recovery composition has
changed. A consumed decision for the current composition still fails closed on a
duplicate re-entry. This prevents stale recovery state from masquerading as current
authority without weakening consumed-fingerprint loop prevention.

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

## Evidence reconsideration before semantic commitment

Initial LLM ideation remains intent-first: the first engineering contribution is
formed from the intended future state and current/world engineering knowledge
before accumulated SAGE evidence is allowed to narrow the solution space. The
front door then performs deterministic evidence retrieval. When relevant prior
evidence exists, semantic commitment pauses at an `evidence-reconsideration`
boundary so that remembered experience can challenge or augment the candidate
without becoming institutional inertia.

The retrieved source facts, rank, provenance, confidence, and recency remain
checksum-bound. The LLM may add contextual assessment only. Each relevant item
receives an applicability assessment and a separate value-effect assessment. An
existing overlapping capability creates a **consideration obligation, not a selection preference**: reuse, augmentation, replacement, intentional
coexistence, and do-nothing remain legitimate alternatives when evaluated against
the same Architect-owned intent, constraints, Definition of Done, risk, and
current evidence. This makes accidental divergent stacks observable without
forbidding deliberate redundancy.

A material assessment that redirects or expands alternatives, proposes a bounded
augmentation, or adds acceptance criteria requires a refreshed engineering
contribution before semantic confirmation. Evidence-derived acceptance criteria
are proposals, not authority; they become planning obligations only after the
Architect dispositions them through the existing semantic-confirmation boundary.
Evidence that is currently inapplicable, diminished, superseded for the context,
or requires revalidation preserves its rationale and reconsideration trigger so
it can participate again when conditions change. Mere retrieval does not create a
mandatory human gate; material architectural meaning or tradeoffs retain the
existing Architect boundary.

## Implementation-generation lineage

Each governed implementation generation preserves the accepted action, candidate
head, evidence-reconsideration lineage, runtime evidence, and promotion outcome so
that an implementation can remain **historically justified** even when later
technology changes its comparative fitness. Stable intent and acceptance criteria
are kept distinct from the technology generation that happened to satisfy them.

Later evidence may therefore support retain, adapt, rebuild, replace, or
intentional coexistence without rewriting the original decision as an error. A
new generation may supersede an older one only through the normal evidence,
semantic, authority, validation, runtime, and promotion boundaries. SAGE does not
autonomously modernize implementations. The preserved lineage provides the
evidence path for explaining what assumptions changed, which criteria remain,
why a successor generation is expected to add value, and whether later observed
outcomes support that prediction.

## Earliest affected boundary

SAGE re-enters only the **earliest affected boundary**:

- `implementation-local`: governing meaning, authority, capability requirements, safety/trust boundaries, and Architect-confirmed implementation scope are unchanged. The active mutation set may narrow to any subset of that confirmed implementation scope; merely touching a different subset of already-authorized paths does not require semantic restart. Expansion outside the confirmed scope does. SAGE reuses the confirmed semantic source and the prior complete component plan, so semantic discovery, evidence retrieval, and component reselection are not repeated.
- `planning`: confirmed semantic meaning and file scope remain valid, but planning/capability evaluation must be recomputed. SAGE reuses confirmed semantics and re-enters request planning. When the trigger is an Architect-reviewed domain capability gap set, the iteration may carry the checksum-bound **approved domain-capability gap set** as explicit planning authority only for the exact staged engineering contribution and semantic-confirmation lineage bound into that approval; candidate substitution fails closed. This never converts the gap itself into proof that the staged implementation succeeded.

When confirmed semantics are reused for a successor implementation candidate, the semantic artifacts are not rewritten to impersonate new Architect confirmation. The repository-owned reuse composition instead rebinds the planning-source payload to the successor contribution and records that contribution's exact package path and SHA-256 as implementation-local provenance. Downstream planning treats this as the effective staged candidate only after checksum and payload-equality verification, while the original semantic understanding/confirmation digests remain governing meaning authority.
- `semantic-confirmation`: meaning, scope, trust boundary, or another semantic condition changed. SAGE re-enters the existing semantic-bootstrap workflow.
- `authority`: the governing action or authority changed. SAGE records the invalidation and stops for the appropriate authority boundary rather than freelancing continuation.

Only downstream state at or after the selected boundary is invalidated. Runtime and promotion evidence from an earlier candidate never transfer automatically to a new iteration.

## Promotion separation

Runtime verification may make the current candidate eligible for promotion only when the current iteration has no unresolved findings. Checkpoint persistence, source validation, and remote synchronization remain insufficient by themselves.

## Objective-first route

Before a new candidate mutation or gap-remediation candidate is prepared, the
intent-to-outcome front door preserves a machine-readable **objective-first
route**. The route is derived from the accepted action, current intent state,
current candidate iteration, existing evidence references, and the engineering
contribution's proposed alternatives. It is an extension of the existing
intent-to-outcome composition, not a second planner or parallel orchestration
system.

The route exposes the active objective, explicit **parent delivery re-entry**
when the accepted action names one, remaining accepted-action obligations,
current evidence references, dependencies, alternatives (including do-nothing),
the current candidate, next governed boundary, known limitations, deferred debt,
assurance state, integration/maturity state, and guardrail/collaboration feedback
fields. Unknown risk, reversibility, expected-value, time-to-evidence, assurance,
and human-effort values remain explicitly `unassessed` or unavailable rather
than being manufactured.

`python3 scripts/sage/sage-intent-to-outcome.py route --state <state.json>` is a
**read-only route** inspection boundary. It can project the objective route from
legacy intent state without rewriting historical evidence. Candidate-iteration
entry refreshes and persists the route before semantic/planning/execution child
work is started so a gap cannot silently become the objective.

## Value-preserving integration and maturity separation

Canonical **value-preserving integration** eligibility is distinct from source
validation, capability maturity, runtime/production promotion, and objective
completion. The route therefore carries these states separately. This first
bounded composition does not infer integration eligibility from a successful
commit, push, source guardrail, or runtime receipt; eligibility remains
`unassessed` until executable assurance and nondelegable-constraint evidence
support the claim.

A limitation may therefore remain visible without automatically becoming proof
that all useful non-regressive work must be discarded. Its eventual governed
disposition is one of: integrate with monitoring/protective controls, block
dependent activity until fixed, or defer remediation. The current route records
observed unresolved findings conservatively as blocking until a later governed
disposition supplies the missing risk, detectability, reversibility, recovery
cost, dependencies, and reconsideration basis.

## BDD-style assurance and active technical debt

The route includes a **BDD-style assurance** surface that separates source
validation, runtime-evidence mapping, and requirement/scenario coverage. Until
approved functional and nonfunctional obligations are mapped to executable
regression scenarios, coverage remains `unassessed` and those obligations are
reported as uncovered or weak. Passing existing guardrails does not silently
claim a complete behavioral model.

Deferred limitations are **active technical debt**, not a passive backlog.
Debt records remain attached to the objective route and are intended to carry
rationale, risk, detectability, reversibility, remediation/recovery cost,
dependencies, opportunity cost, monitoring, and reconsideration triggers. A
later slice may automate the economic crossover evaluation, but this route
contract establishes the location where that decision evidence lives.

Guardrail and collaboration effectiveness also remain first-class route data.
Activations, prevented defects, false positives, break-glass use, manual
corrections, unplanned recovery steps, operator boundaries, and interpretation
burden are represented without inventing unavailable values. Evidence
reconsideration adds deterministic process observations such as retrieved-candidate
count, finalized applicability/value coverage, prior-capability changes to the
alternative set, revalidation needs, reconsideration triggers, and implementation
generation status. Existing outcome metrics and continuous-improvement evidence
remain the authoritative sources for populating human-effort and predicted-versus-
observed value fields; unavailable measurements remain unavailable.

## Bounded Action-001 delivery and Action-002 re-entry

For `SAGE-ACTION-20260823-001`, the first coherent implementation slice is the
objective-route contract and read-only projection on the existing
intent-to-outcome front door. It deliberately reuses capability intelligence,
semantic bootstrap, request planning/execution, recovery, evidence, and
promotion compositions rather than reimplementing them.

The registration-to-Git persistence composition seam observed while registering
Action-001 remains explicit deferred technical debt for this slice; fixing that
seam is not allowed to displace the parent delivery objective. Cloudflare's
Access/MFA-protected SAGE experience may consume the route in a later bounded
slice, but this slice does not alter external-access or privileged-surface
policy. The counterfactual architecture-convergence review remains triggered
only after `SAGE-ACTION-20260815-002` completes and must not block its runtime or
promotion work.

## Completed-child reconciliation after interrupted parent persistence

A request child can self-close successfully through the repository-owned routine
Git lifecycle while a recovery interruption prevents the parent intent state from
persisting the request-child pointer and refreshed planning lineage. In that
specific stale-parent condition, SAGE must not replay planning, request execution,
or Git mutation, and it must not create a second intent lineage merely to make the
state machine advance.

`continue-request` therefore has an explicit **completed-child reconciliation**
mode. It is valid only when the existing parent is still
`planning-source-ready`, has no planning proposal or request-child pointer, and
its current iteration still represents the untouched planning boundary. The
caller must supply the exact completed request state, its canonical routine Git
receipt, and the exact **refreshed planning lineage** source used to produce the
child proposal.

SAGE validates the child against the parent's literal request, validates the
proposal package and digest recorded by request execution, reuses
`validate_reusable_plan_lineage` to prove the supplied planning source and child
proposal belong together, and reuses `reconcile_completed_request_child` to
validate the completed routine-Git receipt and its verification, metrics, and
closeout evidence. Only after those checks pass does the parent persist the
actual planning source, planning proposal, request-execution state, and candidate
commit and advance to `source-git-complete` with `runtime-validation` as the next
boundary.

This is a recovery of missing lineage persistence, not an alternate adoption or
planning path. Ordinary `continue-request` retains its existing
`request-operator-review-required` gate, and incomplete or active children cannot
use the stale-parent reconciliation mode.

## Objective execution unit and path critic

`SAGE-ACTION-20260823-001` extends the existing objective-first route with a
bounded **objective execution unit**. The Architect approval atom is the material
objective/path decision surface, not each deterministic engineering command.
Ordered and conditional work remains explicit and evidence-producing, but a
repository-owned objective executor may consume delegated deterministic adapter
proposals without returning every routine step to the Architect.

The first 80/20 proof is ordinary post-promotion branch closeout. The objective
plan is persisted before mutation and binds the exact objective, delegated
`sage.branch-lifecycle` adapter digest, ordered/conditional work, dependencies,
expected evidence, recovery behavior, component/interface reconciliation, and
material-intervention triggers. The Architect approves the exact plan digest
once. The existing branch-lifecycle composition continues to own Git proposal
construction, containment checks, fast-forward-only semantics, remote/local
retirement, and repository-lineage verification.

Execution deviations are classified separately from objective replanning.
`implementation-local-correction` means objective meaning, authority, approved
scope envelope, constraints, material risk envelope, and intended outcome remain
unchanged. Such corrections remain inside the approved objective authority and
must be evidenced. `true-replan` means at least one material dimension changed;
execution stops for Architect disposition and the remaining suffix requires
approval when its decision surface changes.

Every completed execution persists a comparable `sage-objective-episode` with
the planned path, counterfactual path when material, actual path, local
corrections, true replans, Architect interventions, component use, evidence
cost, outcome, path-efficiency metrics, and improvement observations. The
branch-closeout target is one objective approval with zero routine follow-up
interventions while preserving delegated Git chronology and lineage guarantees.

The bounded LLM path critic is advisory evidence, not an authority or migration
engine. SAGE persists an `sage-llm-path-critic-request` covering
objective-equivalent efficiency, unnecessary operator boundaries, component
reuse, mutation/evidence cost, recovery burden, and architecture/technology
fitness. LLM findings are persisted as content-addressed revisitable causal
observations with context, rationale, expected benefit, affected components,
and measurable indicators. Recommendations may include retain, blue/green
migration, parallel/canary adoption, selective adoption, replacement, or
deferral, but never authorize autonomous migration.

This slice deliberately excludes universal orchestration, graph-engine
migration, automatic technology migration, full maturity UX, and dynamic model
invocation. Those remain evidence-driven future opportunities.


### Objective-execution implementation-local recovery

The objective execution unit reuses SAGE's repository-owned recovery identity,
recurrence, next-boundary, and consumption contracts. A deterministic failure
inside an unchanged Architect-approved objective decision surface is recorded
as an implementation-local correction, receives canonical failure retrieval,
is validated through the owning objective-execution component, and retries the
same deterministic suffix. Persisted command-result evidence is reused so a
failure after mutation but before delegated adapter continuation does not
replay the mutation.

A failure that indicates changed authority, containment, approved scope,
constraints, material risk, plan/adapter binding, or another material decision
surface remains fail-closed and does not earn automatic continuation. Repeated
unchanged failures remain subject to the shared recurrence-aware recovery
policy and may escalate to its governed successor boundary. This slice does not
grant an LLM autonomous source repair, replanning authority, or migration
authority.


### Pre-semantic candidate persistence

Semantic and evidence-reconsideration boundaries require clean repository
authority. An exact validated dirty candidate therefore uses a bounded
candidate-persistence authorization composition before semantic continuation.
That composition verifies exact dirty scope and synchronized feature authority,
then emits an operator-approved `routine-git-lifecycle` proposal. The existing
routine Git controller remains the sole stage/commit/push mutation owner and
verifies exact scope, single-commit topology, remote synchronization, and the
clean post-state. This bootstrap seam grants no semantic, merge, promotion,
branch-retirement, deployment, or objective-completion authority.

## Runtime applicability with promotion retained

Runtime validation is an applicability-sensitive assurance domain; it is not a
universal requirement to manufacture deployment evidence for every
source-validated repository candidate.

For a source-only candidate whose accepted objective requires governed
checkpoint promotion but does not change the deployed workload, Traefik origin,
Cloudflare tunnel, Access/MFA policy, monitoring configuration, or privileged
publication surface, the Architect may explicitly record **runtime not
applicable** for that bounded candidate.

The `runtime not applicable` disposition is not a runtime pass. No runtime receipt is created,
`runtime-verified` is not claimed, and the candidate retains
`source-validations-passed` as its actual assurance state.

For this disposition, **promotion remains applicable** when source validation
passed, a canonical candidate commit exists, there are no unresolved findings,
and the Architect explicitly records the applicability decision. The normal
checkpoint-promotion composition, browser approval boundaries, merge
verification, and post-promotion branch lifecycle remain unchanged.

Candidates for which runtime behavior is applicable continue to use the existing
`sage-e2e-zero-trust-runtime-receipt` contract and `record-runtime` path. The
runtime-N/A path cannot substitute for, weaken, or reinterpret those trust
boundary checks.

A later candidate iteration clears the prior candidate's delivery-applicability
disposition. Runtime or promotion applicability never transfers automatically
between candidate generations.


### Objective-architecture correction: semantic closeout and planning critique

The first live post-promotion execution of the bounded objective unit exposed a
design contradiction in the initial implementation. The process contract said
Git remained the delegated high-resolution mechanical chronicle, but the active
objective executor represented `switch-main`, `fast-forward-main`,
`delete-remote`, and `delete-local` as SAGE-owned lifecycle phases. Automating
those phases under one approval reduced approval count but did not actually
preserve the intended ownership boundary.

The corrected active path therefore models ordinary post-promotion closeout as
one semantic objective operation: **reconcile authoritative main and retire the
promoted source while preserving containment, no-history-rewrite, authority,
and repository-lineage guarantees**. The delegated Git adapter may perform the
mechanics required to realize that outcome, including idempotent continuation
after partial mechanical progress, but those mechanics are not the active SAGE
objective graph. Git remains the detailed mechanical chronology. SAGE records
the objective authority, before/after semantic lineage, verified graph/ref
invariants, correction/replan evidence, and comparable objective episode.

Adapter identity is bound and verified before mutation. A Git branch switch
inside an already-approved delegated operation does not redefine adapter
identity merely because the worktree then exposes another branch's file bytes.
A genuine pre-execution adapter change still fails closed. Execution failures
are material only when evidence identifies a changed objective meaning,
authority or containment, approved scope, constraint or history-safety
property, material risk envelope, or intended outcome. Error-word matching must
not manufacture all material dimensions from an implementation-local failure.

The LLM path critic also participates **before Architect path approval**, not
only after an execution episode. Plan creation persists a planning critic
request that requires explicit assessment of:

- semantic/governance ownership versus delegated-system mechanics;
- duplication of another system's native lifecycle, chronology, state machine,
  or control plane;
- repeated graph/state-machine structures that may justify evaluating a
  directed-graph, workflow, or other purpose-fit representation;
- existing engines, representations, platforms, components, or systems of
  record that may be better owners of the behavior; and
- an objective-equivalent path with lower operator-boundary,
  mutation/evidence, recovery, or duplicated-control cost.

The critic remains advisory and cannot approve a path or authorize migration.
Its exact observation is evidence bound into subsequent Architect approval, so
the Architect reviews the proposed implementation and its architectural
critique at the same material decision surface. Repeated architectural
observations accumulate as revisitable causal evidence; they do not
autonomously trigger graph-engine or technology migration.

The failed first-generation closeout episode remains immutable evidence. The
correction supersedes its false material classification and stepwise active
implementation without rewriting the historical failure.

### Promoted-generation implementation-local successor semantics

A successfully promoted implementation generation is a durable predecessor for
later evidence-backed implementation-local correction. Starting a successor
must not retroactively mark that promoted iteration non-promotable, attach the
new defect as an unresolved finding on the old candidate, or otherwise rewrite
its successful historical disposition. The predecessor remains reconstructable
through its existing iteration and implementation-generation evidence; the new
trigger belongs to the successor iteration.

Implementation-local inheritance preserves the Architect-approved **decision
surface**, not accidental equality of the previous staged payload. A successor
may therefore narrow its active source set to any non-empty, mode-compatible
subset of the previously approved/confirmed source envelope. Expansion outside
that envelope or changing an authorized path's mode remains material and fails
closed. The corrected proposal payload must still exactly match the checksum-
bound successor engineering contribution.

Likewise, a successor generation may execute from a newly governed,
synchronized non-`main` feature branch. Feature-branch identity and repository
HEAD are provenance for the implementation attempt; they are not themselves
the Architect-owned objective meaning or approval surface. The prior and
successor branch bindings, source-scope relation, exact proposal digests, and
contribution payload remain explicit inherited-decision evidence. Binding an
implementation-local successor directly to `main` remains prohibited.

These rules do not transfer runtime or promotion success to the successor. They
only allow the already-confirmed objective and implementation envelope to
produce a new candidate without fabricating semantic rediscovery or rewriting
the previously promoted generation.
