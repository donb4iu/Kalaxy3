# Kalaxy3 SAGE causal evidence graph

## Purpose

The causal evidence graph is the Architect-approved post-Action-002 convergence
direction. It does not replace the established SAGE roles, guardrails, authority
boundaries, evidence obligations, recovery rules, or capability contracts. It
provides a shared causal representation on which those existing contracts can
converge.

The model explicitly rejects a monolithic mutable objective state machine.
Independent actors and workflows may produce evidence-backed facts concurrently.
Synchronization occurs only when one fact causally depends on another fact or
when an existing SAGE authority boundary requires it.

## MVP behavior

The MVP is a content-addressed immutable object store under SAGE local state.
Each fact records the objective, semantic fact type, producer identity, an
authority reference, the result of validating any bound SAGE authority receipt,
zero or more causal predecessor fact IDs, evidence references, collision-safe
evidence file digests, and factual attributes.

A fact ID is derived from the canonical fact identity. `recorded_at` represents
the first time SAGE persisted that identity and is not part of the identity
digest. Re-recording the same semantic fact is idempotent.

Facts with no causal relationship require no shared mutable transition and can
be recorded independently. A dependent fact may reference only predecessor
facts already present in the store. This enforces causal ordering without
inventing a global total order.

Current readiness is a derived projection. The projection asks whether required
fact types are present **and authority-validated** for one objective after
applying any authority-validated lifecycle relations visible at the requested
`as_of` time. The projection is not persisted as objective truth. Facts that
carry only an `authority_reference` remain preserved evidence but are explicitly
excluded from readiness. Lineage is derived recursively from predecessor
references.

## MVP proof

The repository self-test demonstrates that a mere textual authority reference
cannot satisfy readiness. It then uses the existing `authority.reconcile`
primitive to create and revalidate a complete authority receipt, records two
independently recordable validated root facts, and records one validated
convergence fact depending on both. The derived readiness view remains false
before convergence and becomes true afterward. Lineage replay must recover
both roots and the convergence fact.

After repository integration, the real MVP validation must use an existing
completed SAGE objective and real independently produced evidence receipts.
The fixture proves the contract; it does not satisfy the real-objective
acceptance criterion.


## Minimum-resilience behavior

MRP adds correction history without mutating historical facts. The existing
`sage-causal-evidence-fact` record remains the only stored object shape and the
existing generic `record` front door remains the write path. Two reserved fact
types express lifecycle relations:

- `fact-invalidated` depends on exactly one `target_fact_id`. Its attributes
  declare `relation_kind: invalidation`, the same `target_fact_id`, and a
  non-empty `reason`.
- `fact-superseded` depends on the `target_fact_id` followed by one
  `replacement_fact_id`. Its attributes declare `relation_kind: supersession`,
  both identifiers, and a non-empty `reason`. The replacement must belong to the
  same objective and preserve the target's semantic fact type.

Relation facts are ordinary immutable facts and therefore require the same
claim/evidence-scoped SAGE authority validation before they can affect derived
truth. An unvalidated relation remains preserved but has no projection effect.
A relation cannot target another relation in this minimum contract; correction
of relation semantics is deferred to a later conflict-resolution slice rather
than introducing recursive mutable status.

A validated invalidation or supersession makes its target inactive in current
projections. Any ordinary fact that causally depends, directly or transitively,
on an inactive fact is also inactive. A supersession does not automatically
make the replacement authoritative: the replacement contributes only when its
own fact authority is validated. Relation facts themselves remain historical
evidence and do not become inactive merely because they depend on the fact whose
lifecycle they describe.

`project --as-of` applies only facts and relations recorded at or before the
requested timezone-aware ISO-8601 cutoff. This allows the same immutable store to
reconstruct the knowable state immediately before and after a correction. The
derived view surfaces `inactive_fact_ids`, per-fact inactivity reasons, and the
validated `relation_effects` that caused those results. No old fact is deleted,
rewritten, or silently relabeled.

When a lifecycle relation is caused by a diagnosed execution-path divergence,
its optional `actual_path_reference` and `correction_reference` attributes point
to the existing SAGE failure-diagnosis / recovery evidence. The causal graph does
not duplicate `actual_path`, `expected_path`, ownership, divergence, or reusable
correction semantics that are already owned by `failure.diagnose`; it preserves
references so the Architect can assemble actual-path context for retrospective
and counterfactual review.

## Authority

The graph records authority; it does not create authority.

An `authority_reference` is descriptive provenance only. It never makes a fact
authoritative by itself. A fact may contribute to derived objective truth only
when a bound authority receipt validates as complete, current,
non-conflicting, and review-ready through the existing SAGE
`authority.reconcile` mechanism. An unreadable, incomplete, stale, conflicting,
unknown, or otherwise invalid authority receipt fails closed.

This validation does not grant new scope to the receipt. Repository, operator,
runtime, telemetry, external-contract, and other authorities retain the scopes
defined by their existing SAGE mechanisms. The causal graph merely records the
validated result and its collision-safe receipt identity.

The LLM remains an untrusted proposer. The Architect retains intent,
architectural-fitness, scope, tradeoff, and disposition authority. SAGE
validates, persists, derives, and enforces according to existing governed
contracts.

## Historical reconstruction and counterfactual use

Because facts are immutable and causal edges are preserved, the graph is
intended to support reconstruction of the evidence path that produced a
result. Lineage reconstruction preserves the original dependency path. The MRP
`as_of` projection additionally reconstructs which authority-validated facts
were active before and after later invalidation or supersession relations.

Counterfactual architectural assessment remains Architect-owned. A later slice
may assemble actual-path context and alternatives from the graph, but SAGE
must not decide which architecture the Architect should have selected.

## Relationship to existing workflow evidence

Existing append-only structured event logs and checksummed closeout evidence
remain valid evidence sources. The causal graph is not a second workflow
engine and does not require existing workflows to be rewritten before they
can participate. Migration is incremental: a workflow may first contribute
facts that reference its existing receipts and bind its existing authority
receipt.

## Remaining limitations

The MVP+MRP slice deliberately does not claim distributed or replicated storage,
automatic integration into every workflow, conflict resolution between
competing lifecycle relations or authorities, correction of relation facts by
meta-relations, a performance-optimized index, replacement of existing workflow
state, or cryptographic protection of the first-recorded timestamp outside the
existing local-state controls. Those remain later boundaries. Migration remains
incremental: existing workflows can continue producing their current evidence
and contribute causal facts and lifecycle relations when useful.
