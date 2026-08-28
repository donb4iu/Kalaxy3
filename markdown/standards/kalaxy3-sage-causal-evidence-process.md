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

Current readiness is a derived projection. The MVP projection asks whether
required fact types are present **and authority-validated** for one objective.
The projection is not persisted as objective truth. Facts that carry only an
`authority_reference` remain preserved evidence but are explicitly excluded
from readiness. Lineage is derived recursively from predecessor references.

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
result. The MVP includes lineage reconstruction and an `as_of` filter over
first-recorded timestamps for derived views.

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

## First-slice limitations

The MVP deliberately does not claim distributed or replicated storage,
automatic integration into every workflow, supersession/invalidation,
conflict resolution between authorities, a performance-optimized index,
replacement of existing workflow state, or MRP durability. Those remain later
boundaries. The MVP exists to prove the architectural model on one real
happy-path vertical slice without a big-bang rewrite.
