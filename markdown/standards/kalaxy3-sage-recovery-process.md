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

## Owner-aware implementation-local continuation

An implementation-local repair returns to the repository workflow that owns the
failed component. The shared recovery decision therefore binds the continuation
command by `owning_component` rather than routing every repair through the
improvement-action lifecycle.

Current registered owners are:

- `sage.request-execution` → `sage-request-execute.py --recovery-decision`;
- `sage.improvement-action-transition` →
  `sage-improvement-action-transition.py --recovery-decision`.

Each owner validates its own repair regression, records the immutable recovery
consumption receipt, and performs no repository mutation while consuming the
fingerprint. Unknown implementation-local owners fail closed until a
repository-owned consumer is explicitly registered. Successor-action escalation
is different: it always returns to the improvement-action lifecycle because the
next authority boundary belongs to the Architect, not to the failed component.

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
- successor escalation; and
- required evidence and operator/Architect boundary.

These fields make recurrence precision, prevented loops, consumed governance
changes, operator steps, and avoidable rework measurable.
