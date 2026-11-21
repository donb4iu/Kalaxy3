# SAGE objective-state contract — bounded first enforcement slice

**Parent objective:** #54. **Engineering decision target:** #50. **Historical validated source:** #55.

## Purpose

Do not turn a role's recommendation to redo already validated work into an unchallenged execution action. Preserve the exact scope and evidence of a completed measurement; distinguish that from **unknown** implementation/semantic obligations. This checker is an evidence-based, deterministic pre-dispatch *guardrail*, **not** a new Architect approval authority, canonical state store, Neo4j schema, or orchestration subsystem.

## Evidence and scope

The first recognized validated capability is `source_metadata_identity`. It derives only from the existing #55 native receipt linked by SHA-256 to the previous state-aware episode manifest. The verifier requires:

- Graph/source revision `5e15f72d95827e026637cf4161048b7afbc8072e`.
- 1,388 Git source blobs and 1,388 Neo4j source identities.
- Identical path/OID/digest inventory, no missing/extra/mismatched sources.
- Explicit `graph_page_incomplete=false`, `semantic_relevance_qualified=false`, `complete_context_claim=false`.

This is **metadata parity at a historical pinned revision**. It is not present-day production evidence, full semantic completeness, or final Issue #50 acceptance. The digest link is local integrity evidence; an operator-controlled manifest is not a cryptographic signature or independent authority.

`concept_obligation_coverage`, `semantic_relationship_fidelity`, `tri_state_evidence_presence`, `bidirectional_semantic_retrieval`, `independent_relevance_quality`, `governed_rebuild`, `lifecycle_promotion_recovery`, and `bounded_model_repair` remain **unknown** (not failed, missing, or accepted) unless separately qualified in future repository-governed episodes. Validation of an unknown obligation is an *outstanding evidence task*, not evidence its functionality is absent.

## Deterministic decision consequences

| Proposed action | Outcome | Why |
| --- | --- | --- |
| Recheck source identities at the #55 exact revision | `blocked_repeat` | Completed bounded metadata check already exists |
| Recheck at a different revision with identical blob identities | `blocked_repeat` | A new commit alone does not change source scope |
| Recheck at a different revision with verified Git blob-identity changes | `candidate_new_scope` | The new source universe has not been validated by the old receipt |
| Check an unverified semantic obligation | `candidate` | Bounded validation may produce direct value |
| Implement an unknown obligation or change a validated capability without authority | `blocked` | This checker cannot authorize mutation |
| Missing native receipt, mismatched digest, unknown Git revision | Fail closed / `unverified` | Never substitute model-generated self-attestation |

A verified new Git scope **does not invalidate the previous receipt**; it creates an unverified *new-revision* obligation. An `invalidated` capability status must be supported by a distinct authenticated contradicting or superseding receipt, which this first slice does **not** attempt to create. No model assertion, stale text, or substring match can mark a capability invalidated.

## CLI boundary

`python3 scripts/sage/sage_objective_state_gate.py --receipt RECEIPT.json --manifest EPISODE/episode-manifest.json --proposals PROPOSALS.json --repo REPO --output REPORT.json --strict`

Exit 0: all proposed actions are bounded **candidates only** (not authorized execution). Exit 2: at least one action is blocked or unverified. Exit 3: malformed evidence/contract, no valid report. Reports are created outside the repository and never overwritten. All Git inspection is read-only.

## Non-goals and integration limitation

This contribution introduces a contract, standalone deterministic evaluator, and tests. Existing SAGE dispatchers **must invoke its check before executing a proposed work unit** for this guardrail to govern actual execution. It does not yet claim runtime integration, a full SAGE capability-state ontology, historical revalidation, graph changes, new approval gates, or final Architect acceptance. Future adapters must treat `candidate` as eligible for *existing* Architect authorization—not as preauthorization.
