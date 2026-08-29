# Kalaxy3 SAGE Request Execution Process

## Purpose

SAGE request execution closes the gap between repository discovery and one exact operator mutation boundary. The literal request remains authoritative. An LLM or other producer may supply an **untrusted proposal** package, but the proposal is not authority and does not execute itself.

The repository-owned executor binds the proposal to the exact literal request, current branch and HEAD, checksum-bound source files, declared generated files, repository evidence references, explicit capabilities, repository component candidates, and an allowlisted validation plan. A proposal that requires a new low-level primitive fails closed; a new primitive must follow the separate capability-gap approval process.

## Governing sequence

The executor uses `scripts/sage/workflows/operating_contract.py` and preserves its mandatory pre-mutation order:

1. Preserve the literal request and retrieve current SAGE evidence.
2. Inspect the current clean Git authority without mutation.
3. Perform federated authority reconciliation using SAGE-owned assertions; proposal-supplied authority assertions are not accepted.
4. Perform explicit component selection against the live versioned primitive registry.
5. Record the capability gap decision. Version 1 proceeds only when existing composition closes the gap.
6. Apply only checksum-bound declared repository content through an atomic transaction.
7. Reconcile evidence indexes only through the fixed repository `sage-index.py reconcile` path when the proposal declares generated evidence paths.
8. Run changed-path SAGE discovery and the proposal's shell-free SAGE validation targets.
9. Scan proposed Python source through the repository Git/GitHub/credential/deployment safety guardrail.
10. Emit one non-executed operator proposal. When the feature branch has a synchronized upstream and live remote `main` still matches the captured authority, the proposal is the one-approval `routine-git-lifecycle` controller boundary; otherwise request execution fails closed rather than silently broadening authority.

The **routine Git lifecycle** is the ordinary one-approval path after validation. For ordinary validated changes, the operator executes one checksum-bound `routine-git-lifecycle` proposal using command-proposal schema 1.2. That one approval invokes the exact tracked repository controller at `scripts/sage/sage-routine-git-lifecycle.py`, which delegates mutation only to `scripts/sage/workflows/routine_git_lifecycle.py` and `git.repository.commit_and_push`.
Before any mutation the controller re-verifies the feature branch, approved HEAD, exact declared paths, synchronized upstream and remote feature branch, frozen remote `main`, pass-only validation receipts, authority/component receipts, and the proposal command digest.
The bounded controller performs exactly stage → commit → push. It does not create or switch branches, merge, rebase, reset, delete refs, mutate GitHub, inherit credential variables, or mutate deployment state. It records a checksum-bound local controller receipt and event log.

The repository-owned controller receipt is first-class continuation evidence. The same approved controller command immediately delegates that receipt to request execution; no caller-authored `SAGE_OPERATOR_RESULT`, `pasted_output_received`, pasted terminal output, or request-specific result binder is part of the ordinary routine path. SAGE then runs the mandatory post-operator sequence:
1. Bind the repository-owned receipt to the exact active proposal, frozen authorities, declared scope, resulting commit, and controller command digest.
2. Independently inspect the resulting Git state through `git.inspect` and prove exactly one commit descends directly from the approved HEAD, the committed path delta equals the declared scope, the working tree is clean, local HEAD equals its upstream, and the remote feature branch equals that same commit.
3. Record directly observed outcomes through `metrics.outcome`, preserving unavailable measurements as null and recording the boundary-result digest as provenance.
4. Write local evidence closeout through `evidence.closeout`.
5. Mark the repository Git lifecycle complete before the one approved controller command returns success. No additional stage, commit, push, or continuation approval is emitted.

If post-mutation closeout fails after the controller receipt exists, `sage-request-continue-routine` is the repository-owned recovery path and consumes only that canonical receipt; it does not reconstruct operator output. The legacy pasted operator-result continuation remains available only for already-open/manual `stage`, `commit`, and `push` boundaries and genuinely external interactions that SAGE cannot deterministically observe. During the one-time schema-1.2 activation edge, an already-open checksum-bound `routine-git-lifecycle` proposal created under schema 1.0 may be executed by the repository-owned routine controller and closed from its stronger repository receipt; proposal generation itself never falls back and all newly generated routine proposals remain schema 1.2. New ordinary request execution uses the one-approval routine lifecycle and fails closed when its authority prerequisites are not satisfied.
The proposal package declares the single-line commit message and `origin` push remote used by that deterministic lifecycle. Repository state, not terminal text, remains authoritative: SAGE records the receipt digest and independently verifies Git before closeout.
The transaction commits only after all validation and safety checks pass and the operator proposal has been written. Any unexpected failure triggers rollback of the declared repository content before closeout and requires failure retrieval and diagnosis before retry.

## Failure recovery evidence

Failure recovery is evidence, not an inference from exception handling. **rollback is not inferred** merely because request execution entered a failure path.

- A failure before `AtomicFileTransaction` exists is recorded as `failed-pre-mutation`; no repository rollback is claimed.
- When a repository transaction exists, SAGE may call rollback, but `repository_content_restored` becomes true only after independent `git.inspect` verification proves the worktree is clean and the branch and HEAD still equal the proposal-bound authority.
- A rollback attempt that cannot be independently verified is recorded as `failed-rollback-unverified` and remains fail-closed.
- Failure diagnosis and closeout preserve the measured recovery state so later planning does not mistake control-flow intent for observed repository state.

### Post-retrieval continuation classification

After the mandatory first unexpected-failure retrieval, SAGE records a deterministic post-retrieval continuation decision before corrective retry guidance. The decision records whether authority, scope, required capability, safety requirements, repository-owned composition, or approval or mutation boundaries changed, and whether the attempted action remains authorized.

When none of those governing conditions changed, the required re-entry boundary is `implementation-local`; repair, an exact regression, revalidation, and retry stay inside the same governed request. Repeating discovery or replanning for that unchanged failure class is rejected as unnecessary over-governance. When a governing condition changed, implementation-local retry is rejected: authority changes return to `authority`, semantic/safety/approval-boundary changes return to `semantic-confirmation`, and required-capability or repository-composition changes return to `planning`. The decision is written beside the failure diagnosis and referenced as failure evidence so the continuation reason remains observable and measurable.

### Stable recovery identity and recurrence ownership

The post-retrieval decision is paired with the shared
`sage-recovery-next-boundary` contract. SAGE persists a stable recovery identity
from the literal request, owning component, normalized failure signature, and
separate repository-authority evidence. It also hashes the evidence behind the
six governing conditions so a repository-owned composition change has a stable
governing-condition fingerprint rather than being reported as changed on every
retry.

A new governing fingerprint may cause its earliest required re-entry once.
Intent-to-outcome writes a consumption receipt when that re-entry actually
starts. The same unconsumed governance re-entry is reported as
`await-existing-reentry`; the same consumed fingerprint returns to
implementation-local repair/regression/revalidation when governing conditions
remain unchanged.

Consumed fingerprint state, recurrence of the controlled workload, and
accepted/implemented/validated lifecycle status are context only. They do not
prove an accepted control failed. **Accepted-control failure assertion**
evidence must separately identify the owning action, the promised obligation
that was violated, and concrete evidence references. Only that distinct
assertion permits `successor-action` / `architect-decision`; a genuine evidenced
control failure still enters the improvement-action lifecycle and emits the
successor capability-gap/improvement-action Architect boundary exactly once.

## Proposal package

A proposal ZIP contains exactly `sage-proposal.json` plus `payload/<repository-relative-path>` for every source file. The manifest is governed by `sage-request-execution-proposal-schema-v1.0.json` and binds:

- the exact literal request by SHA-256;
- expected non-main branch and exact Git object ID returned by `git rev-parse HEAD` (40-character SHA-1 or 64-character SHA-256);
- source paths, content hashes, and file modes;
- generated paths and whether repository evidence-index reconciliation is required;
- evidence references used by the proposal;
- required capabilities and explicit repository component candidates;
- `new_primitive_required=false` for this composition;
- a one-line commit message and validated `origin` push remote for the bounded one-approval stage → commit → push controller; and
- shell-free validation commands restricted to non-mutating `make sage-*` targets.

Unknown archive files, path traversal, symlinks, duplicate paths, stale digests, request mismatch, branch/HEAD mismatch, unregistered component versions, unsafe validation targets, unsafe Python source, unresolved capability selection, or changed-path scope drift fail closed.

## Authority and human boundary

SAGE owns discovery, authority reconciliation, component selection, capability-gap gating, atomic application, validation, safety analysis, failure diagnosis, and construction of the operator proposal. Human or model expertise can propose content, rationale, alternatives, evidence references, and capabilities, but cannot convert those claims into authority by putting them in the package.

The request executor itself performs **no Git mutation**, **no GitHub mutation**, and **no deployment mutation**. It may change only declared repository content atomically. For ordinary validated changes it emits one non-executed command proposal that invokes the exact repository-owned routine Git controller. The operator's execution of that one proposal is the explicit approval for the bounded stage/commit/push lifecycle. SAGE must then complete independent post-operator verification, outcome metrics, and evidence closeout before the request is complete.

## Canonical request planning

Normal request execution no longer requires a caller to invent `capabilities`,
`candidates`, `selection_factors`, or capability-gap decisions. The canonical
entry point is `sage-request-plan`, which accepts the same literal request plus
a checksum-bound source-only package and derives those fields from current
repository authority, the mandatory operating contract, and
`sage-workflow-primitives.json`.

The planner emits the unchanged request-execution proposal schema. Direct
caller-authored capabilities and candidates are a bootstrap-only legacy path
and are prohibited when the repository planner applies. Request execution
continues to validate all planned semantics against the live primitive registry
before repository mutation.

## Reuse objective

This is a repository-owned reusable composition rather than a task-specific downloaded helper. The first intended consumer is the centralized-logging end-to-end SAGE thin slice. Future request classes can reuse the same request-to-operator contract by supplying a checksum-bound proposal package that passes the same authority, component, validation, safety, and exact-scope gates.


## Context-derived baseline and required validation

Proposal-declared `validation_commands` are supplemental validation inputs; they
are not allowed to replace repository-owned context policy. Before repository
mutation, request execution derives the implementation context from the exact
declared proposal paths and runs every deduplicated `baseline_checks` command
owned by those contexts. This is **context-derived baseline validation** and is
performed before the atomic write begins.

After the atomic write and before any operator Git proposal is emitted, request
execution reruns changed-path SAGE discovery and executes every deduplicated
`required_validation` command for the resulting contexts. This is
**context-derived required validation**. Commands come only from the current
`sage-change-authority.json`, retain each context's declared working directory,
and execute shell-free through the existing `validation.plan` primitive.
Repository authority may currently declare a single Make target or a
repository-relative Python validator; unsupported command shapes fail closed
rather than falling back to shell interpretation.

Proposal-supplied safe `make sage-*` validations still run afterward as
additional checks. A failure in either context-derived phase is a request
execution failure; after a transaction has opened, the normal verified rollback
and recovery path applies. This prevents a planning source from weakening the
validation contract merely by omitting checks that discovery already knows are
required.

## Proposal-bound Python safety baseline

Request execution captures whole-source safety findings for each existing Python
source path only after the clean working tree and exact proposal HEAD have been
verified and before repository writes begin. That capture is the proposal-bound
baseline for the transaction.

The post-validation helper-safety step still uses the repository-owned
`GitSafetyGuardrail`, but an existing Python module is rejected only for newly
introduced safety findings beyond that verified baseline. An unchanged
pre-existing finding is recorded as baseline state; it is not reinterpreted as
behavior introduced by the proposal.

New Python files have an empty proposal-bound baseline. Generated or new Python
files therefore retain the whole-source fail-closed contract: direct subprocess,
Git or GitHub mutation, credential inheritance or embedding, deployment
mutation, and every other prohibited finding remains blocking.

The comparison preserves duplicate findings and includes the source statement in
each finding identity so moving unchanged source does not create a false new
finding while changed unsafe statements remain fail closed. This exception is
scoped only to baseline findings captured inside the current atomic
request-execution transaction; it does not weaken `GitSafetyGuardrail` itself or
authorize pre-existing unsafe behavior for reuse.

## Legacy continuation-state compatibility

Request-execution continuation states opened before the bounded routine Git
lifecycle introduced `base_main_head` remain compatibility inputs only for the
legacy `stage`, `commit`, and `push` boundaries. The loader may accept that
exact legacy state shape without synthesizing missing main-branch authority.

Every newly written state and every `routine-git-lifecycle` state must include
a valid 40-hex `base_main_head`. Missing or malformed main authority fails
closed. This compatibility exception does not authorize new legacy states and
does not relax frozen-main verification for the one-approval routine Git
lifecycle controller.

## Architect objective-path decision gate

SAGE request execution treats the active Architect-owned objective as the reason
for work. An LLM-proposed tactical SAGE boundary is not itself mutation authority.

Before the existing request-execution authority step can authorize repository
mutation, the operator supplies a checksum-bound `sage-objective-path-decision`
record through `SAGE_OBJECTIVE_PATH_DECISION`. The decision is bound to the exact
literal request and exact proposal package.

The Architect-facing decision surface uses **5W1H**:

- **Who** owns, decides, or performs the work.
- **What** changes and what outcome is produced.
- **Why** the path has value to the active objective now.
- **When** it must happen rather than be deferred.
- **Where** it applies in the objective, architecture, or lifecycle.
- **How** it advances value, removes a blocker, controls material risk, and will be verified.

The record also states the deferral consequence and the **next value-producing milestone**. SAGE accepts three classifications:

1. `direct-objective-value`
2. `necessary-blocker-material-risk`
3. `deferrable-sage-internal-improvement`

A `deferrable-sage-internal-improvement` is a deferrable SAGE/internal improvement
and cannot authorize mutation for the active delivery objective. Discovering an internal SAGE imperfection therefore does not
silently make it the next objective.

The LLM may propose the 5W1H and classification, but decision authority remains
the Architect. Mutation requires an Architect-approved decision whose basis is
`operator-supplied-to-governed-execution`. SAGE copies the validated decision
into the request-execution state directory as `objective-path-decision.json`
before mutation, preserving provenance and audit evidence.

This gate reuses the existing federated authority reconciliation path; it does
not introduce another planner, mutation engine, or lifecycle.
