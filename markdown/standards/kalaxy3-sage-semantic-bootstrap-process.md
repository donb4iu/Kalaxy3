# Kalaxy3 SAGE semantic-understanding bootstrap process

## Purpose

This composition closes the first accepted-action-to-planning seam for `SAGE-ACTION-20260813-001`. It lets SAGE consume an accepted improvement-action contract and an engineering contribution without requiring a human, LLM, or external caller to author `sage-source.json`, hashes, capability IDs, component candidates, selection factors, or capability-gap decisions.

## Responsibility model

The Architect owns intended meaning and semantic confirmation. An LLM or human contributor may propose engineering content, rationale, assumptions, alternatives, and repository files. SAGE owns repository-state facts, provenance binding, context applicability, source-package mechanics, validation selection, and fail-closed progression. Existing request planning remains responsible for repository-derived execution capabilities and component selection. Existing request execution remains responsible for repository mutation and Git boundaries.

Semantic confirmation is not feasibility confirmation and is not mutation authorization. The bootstrap records these assertions separately.

## Flow

1. Require a clean synchronized non-main feature branch.
2. Read exactly one accepted action through the read-only action contract interface.
3. Load an engineering contribution whose manifest contains engineering semantics only; hashes are derived by SAGE.
4. Run exactly one literal preflight pass.
5. Reconcile request-inferred contexts with proposed repository paths and dependency rules from `sage-change-authority.json` without equating semantic applicability with source mutation. Preserve all request-relevant inferred contexts as applicable evidence/governance context; separately derive the narrower implementation-context set that owns the proposed paths and their dependencies. A context is not demonstrably non-applicable merely because no file in that context changes.
6. Emit an immutable semantic-understanding record plus a repository-owned Architect disposition template for its material scope, assumption, and alternative proposals.
7. At the existing Architect continuation boundary, require every material proposal to be dispositioned as `accept`, `reject`, `modify`, or `defer` and bind those decisions to the exact interpreted-understanding digest. Non-accept decisions require rationale; resurfacing a prior disposition requires materially new basis.
8. Deterministically derive the confirmed semantic-understanding record. Accepted/modified effects become **confirmed semantic authority**; rejected/deferred proposals remain decision evidence only. The existing semantic-confirmation record binds the derived result, so no parallel negotiation engine, schema fork, or planner authority model is introduced.
9. Re-verify action, contribution, branch, HEAD, upstream equality, and clean repository state before confirmation. Preserve separate semantic-confirmation, feasibility, and authorization records.
10. Generate the canonical planning source through existing `write_source_package`; a modified implementation scope may only select paths already present in the contribution. The default immutable planning-source filename remains scoped by both action ID and the exact **semantic-confirmation digest**, so **multiple confirmed slices** under one accepted action cannot collide.
11. Derive the routine Git commit subject from the active literal request and hand the source to the existing planning/execution path.

## Context applicability and anti-goose-chase rule

Semantic applicability and source-mutation authority are separate facts. `applicable_contexts` preserves contexts materially implicated by the literal request plus path/dependency contexts. `implementation_contexts` is the narrower set used to govern the proposed repository mutation. Request-relevant contexts with no proposed source mutation remain explicitly visible as `applicable-now-no-proposed-source-mutation`; they are not silently discarded as noise. Demonstrably non-applicable claims require evidence rather than absence of a matching changed path.

New confirmations that carry the split are published through additive request-planning source schema v1.2. Historical v1.1 semantic planning sources keep their original combined-context meaning and remain readable without rewrite; v1.0 sources retain literal-discovery behavior.

For unchanged request, contribution, action contract, and repository authority, semantic bootstrap performs one interpretation/preflight pass. A missing mandatory fact stops progression with an explicit fail-closed reason; registered downstream capability deficiencies continue to use the canonical `capability.gap` mechanism. The composition must not add magic vocabulary, recursively broaden contexts, or repeatedly retrieve unrelated material merely to obtain a passing classification.

## Bootstrap exception

The implementation of this composition may itself be introduced through one explicitly recorded legacy source package because the repository-owned source builder does not exist before this change. That exception is bounded to the bootstrap implementation. After this capability is installed, manually authored `sage-source.json` is not a normal accepted-action implementation path and is covered by regression controls.

## First-slice limitations

The first slice uses the conservative canonical validation set `sage-guardrails`, `sage-index-check`, and `sage-operating-contract-check`. Fit-for-purpose validation minimization, richer feasibility scoring, observability-gap derivation, and external-framework review remain acceptance obligations of the parent action and are not claimed complete by this slice.


## Architect-confirmed planning obligations

Semantic confirmation must preserve more than context and file scope. The confirmed understanding derives a provenance-preserving planning-obligation set from the accepted action outcome, acceptance criteria / Definition of Done, measurement plan, authoritative assumption modifications, deterministic feasibility obligations, and explicit Architect planning directives.

Planning obligations are typed. `capability` obligations identify a domain capability that downstream `component.select` must evaluate; `constraint`, `requirement`, `validation`, `measurement`, `feasibility`, `outcome`, and `lifecycle` obligations remain authoritative planning inputs without being misrepresented as components.

The Architect disposition record may add explicit structured planning directives. A capability directive requires a stable `capability_id`; non-capability directives may not invent one. The confirmed semantic artifact, not the original LLM contribution, is the downstream authority.
