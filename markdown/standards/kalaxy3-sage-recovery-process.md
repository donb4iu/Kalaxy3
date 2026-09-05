# Kalaxy3 SAGE Self-Directing Recovery Process

## Purpose

SAGE recovery is a deterministic continuation contract, not an instruction for
the operator or LLM to inspect source and invent the next step. Every
fail-closed outcome must end with one machine-readable next-boundary decision
or an explicit terminal/no-action decision.

The shared contract is governed by `sage-recovery-policy.json`, implemented
by `scripts/sage/workflow/recovery.py`, and used with the existing
`failure.diagnose`, request-execution, post-retrieval,
intent-to-outcome, and improvement-action lifecycle controls. It introduces no
new low-level primitive.

## Stable recovery identity

A recovery identity preserves separate facts for:

- the SHA-256 of the literal request;
- the owning component identifier;
- a normalized failure signature that removes attempt-local Git object IDs,
  local-state paths, and timestamps; and
- measured repository authority evidence.

The stable identity digest is derived from request, component, and failure
signature. Repository authority is preserved beside that identity and hashed
separately so a recurrence is not misclassified as new merely because an
authorized repair advanced HEAD.

## Governing-condition fingerprint

After the required first failure retrieval, SAGE measures the six existing
post-retrieval governing conditions: authority, scope, required capability,
safety requirements, repository-owned composition, and approval/mutation
boundaries. Those booleans are backed by deterministic evidence digests and
combined into one governing-condition fingerprint.

A fingerprint is new only when current governing evidence differs from the
prior matching failure. A new governance change may re-enter the earliest
required governance boundary exactly once. An unchanged fingerprint cannot
cause repeated discovery, retrieval, semantic confirmation, or planning.

## Re-entry consumption

Intent-to-outcome records an immutable
`sage-recovery-governing-change-consumption` receipt when it actually starts the
governance re-entry emitted by recovery. The receipt binds the recovery identity,
governing fingerprint, required boundary, actual consumed boundary, and durable
consumer state.

If the same failure recurs before the emitted boundary is consumed, SAGE blocks
another governance loop and reports `await-existing-reentry`. If it recurs
after the fingerprint is consumed, SAGE stays at implementation-local
repair/regression/revalidation unless the recurrence proves that the accepted
owning control itself failed.

Recovery re-entry applicability is also scoped to the **current recovery composition**.
A governance decision records the repository-owned composition digest that supported
its boundary. Intent-to-outcome compares that digest with the current digest of the
policy-declared governing composition before applying duplicate-consumption blocking.
A **historical consumed recovery decision** from an older composition remains durable
evidence but cannot block a later candidate after that governing composition changes.
A consumed decision whose composition digest still matches current authority continues
to block duplicate re-entry. This freshness check does not invent a new boundary; the
caller must still enter the earliest boundary justified by current governing evidence.

## Owner-aware implementation-local continuation

An implementation-local repair returns to the repository workflow that owns the
failed component. The shared recovery decision therefore binds the continuation
command by `owning_component` rather than routing every repair through the
improvement-action lifecycle.

Current registered owners are:

- `sage.request-execution` → `sage-request-execute.py --recovery-decision`;
- `sage.improvement-action-transition` →
  `sage-improvement-action-transition.py --recovery-decision`; and
- `sage.objective-execution` →
  `sage-objective-execution.py recover --recovery-decision`.

For objective execution, an implementation-local repair remains inside the exact
material objective-path approval already recorded for that execution. Recovery
records the existing approval digest and `architect_approval_reused=true`; the
repair attempt is not a new approval atom and does not require an Architect
round trip. Architect attention is required only when recovery selects a material
governance re-entry, an evidenced accepted-control successor boundary, or a
non-converging local recovery whose consumed correction produced no new progress
evidence. Recurrence by itself is evidence, not a material decision-surface change.
A consumed planning, semantic, or other governance re-entry does not by itself constitute a failed local repair. Non-convergence is evaluated only after an implementation-local repair decision has itself become the latest matching recovery step and the same failure recurs without material progress.


Implementation-local recovery is permitted only while it demonstrates bounded
convergence. SAGE compares value-producing progress evidence independently from
the governing-condition fingerprint: a recurrence after a consumed local repair may remain local only when new evidence
demonstrates material objective-relevant movement toward validated completion. A
changed progress fingerprint alone is not progress: changed bytes, a different
error, command execution without verification, incidental local-state changes, or
equivalent-path cycling cannot reset non-convergence. The same recurrence without
new material verified progress is non-converging and must exit the local loop.
This is not a fixed retry-count policy. The comparison asks whether the prior
repair materially advanced validated execution evidence. The recovery decision
must evaluate any already-authorized alternative evidenced by the current
composition; when no such alternative is evidenced, the local loop stops at a
governed Architect boundary rather than retrying the same repair indefinitely.

Each owner validates its own repair regression and, on first consumption,
records the immutable recovery consumption receipt without performing repository
mutation. If the same implementation-local fingerprint is already consumed, the
owner treats the consumer as idempotent: it revalidates the repair control, writes
no second consumption receipt, performs no repository mutation, and returns
`already-consumed`. The owner must carry a behavioral regression proving the
first-consumption/second-consumption sequence, including receipt immutability and
revalidation on recurrence. This does not authorize semantic or governance replay
and does not freeze candidate bytes; the literal request wording remains unchanged
while the bounded implementation-local candidate correction may be revised before
the owning lifecycle is retried. Unknown implementation-local owners fail closed
until a repository-owned consumer is explicitly registered. Successor-action
escalation is different: it always returns to the improvement-action lifecycle
because the next authority boundary belongs to the Architect, not to the failed
component.

## Accepted-control escalation

Accepted lifecycle status (`accepted`, `implemented`, or `validated`),
recurrence of the controlled workload, and consumption of a governing-condition
fingerprint are context only; none of them proves that the accepted control
itself failed. Successor escalation requires a distinct machine-readable
**accepted-control failure assertion** naming the owning action, the specific
violated control obligation, and concrete evidence references.

Without that assertion, an unchanged recurrence stays on
implementation-local repair/regression/revalidation even when an earlier
governance re-entry was consumed. This preserves the Action-20260821 recovery
invariant: new governing change re-enters once, unchanged recurrence repairs
locally, and only an evidenced accepted-control failure enters successor
governance.

When the assertion demonstrates failure of an owning control in accepted
lifecycle lineage, the current action is not silently amended. Recovery emits
one exact repository-owned action-lifecycle command bound to the recovery
decision. The action lifecycle validates the recurrence and the assertion
before materializing the explicit Architect decision boundary for a
successor capability-gap/improvement action. The boundary carries the
stable recovery identity, owning component/control, violated obligation,
evidence references,
reason, required evidence, and mutation authority without requiring source
inspection or route invention by the operator or LLM.

Improvement-action lifecycle failures, including discovery/preflight failures,
must invoke this recovery contract before returning fail-closed so the closeout
contains one machine-readable next boundary rather than only an exception.

## Remote-main authority

Current `origin/main` is observed and frozen as repository authority evidence.
Request execution does not require current remote main to be an ancestor of an
otherwise synchronized governed feature HEAD unless an applicable repository
authority explicitly declares that constraint.

## Observability

Every recovery decision records:

- new versus recurrence classification;
- previous failure references;
- governing fingerprint and consumption state;
- selected next-boundary disposition;
- owning component and control;
- prevented duplicate re-entry;
- successor escalation;
- whether Architect attention is required;
- avoided Architect recovery round trips for implementation-local repair; and
- required evidence and operator/Architect boundary.

Objective execution additionally records whether the existing material-path
approval was reused and the approval digest that governed the correction. These
fields make recurrence precision, prevented loops, consumed governance changes,
operator steps, Architect-attention economy, and avoidable rework measurable.
