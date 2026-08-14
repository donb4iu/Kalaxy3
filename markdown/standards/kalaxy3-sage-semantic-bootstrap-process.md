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
5. Reconcile inferred contexts with the proposed repository paths and dependency rules from `sage-change-authority.json`. Inferred contexts outside the proposed repository scope are explicitly dispositioned rather than recursively explored.
6. Emit an immutable semantic-understanding record and stop at an exact repository-owned Architect confirmation command.
7. On exact-digest Architect confirmation, re-verify action, contribution, branch, HEAD, upstream equality, and clean repository state.
8. Preserve separate semantic-confirmation, feasibility, and authorization records. Record feasibility as sufficient only for planning-source generation; runtime and outcome feasibility remain subject to downstream deterministic validation and evidence.
9. Generate the canonical planning source through repository-owned `write_source_package`.
10. Render Architect and planning handoff commands through the existing repository-owned operator-command serializer in `scripts/sage/workflow/proposal.py`; semantic-bootstrap workflow code does not own shell quoting.
11. Hand the source to the existing `sage-request-plan` and `sage-request-execute` paths.

## Anti-goose-chase rule

For unchanged request, contribution, action contract, and repository authority, semantic bootstrap performs one interpretation/preflight pass. A missing mandatory fact stops progression with an explicit fail-closed reason; registered downstream capability deficiencies continue to use the canonical `capability.gap` mechanism. The composition must not add magic vocabulary, recursively broaden contexts, or repeatedly retrieve unrelated material merely to obtain a passing classification.

## Bootstrap exception

The implementation of this composition may itself be introduced through one explicitly recorded legacy source package because the repository-owned source builder does not exist before this change. That exception is bounded to the bootstrap implementation. After this capability is installed, manually authored `sage-source.json` is not a normal accepted-action implementation path and is covered by regression controls.

## First-slice limitations

The first slice uses the conservative canonical validation set `sage-guardrails`, `sage-index-check`, and `sage-operating-contract-check`. Fit-for-purpose validation minimization, richer feasibility scoring, observability-gap derivation, and external-framework review remain acceptance obligations of the parent action and are not claimed complete by this slice.
