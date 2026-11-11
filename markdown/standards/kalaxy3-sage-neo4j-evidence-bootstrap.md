# SAGE Issue #50 — evidence-first semantic model bootstrap

**Status:** unqualified engineering candidate, not a promoted model. Objective and
nine DoD areas remain Architect-owned in Issue #50; PR #51 remains Draft.

## Existing authority and evidence

The governed Git `main` revision is the repository evidence baseline, **not** a
proof of production deployment. Separate runtime/operational evidence is needed
to assert deployed functionality. The feature revision is unpromoted work in
progress; its records may not override `main` or the active semantic projection.
External proof remains under its native authority, even when referenced in Git.

## Bootstrap without a prior knowledge graph

`python3 scripts/sage/sage-neo4j-evidence-bootstrap.py --repo . --main-ref
refs/remotes/origin/main --out-dir <owned-new-output-path>` consumes **committed
Git objects**, not the mutable working tree or a mandatory vocabulary file.
The caller must fetch and pin `origin/main` and the feature commit independently.
The adapter independently enumerates all tracked blobs, binds source identities,
SHA-256 digests and revisions, and rejects missing source paths. It derives
*provisional* concept identifiers from explicit committed Markdown top-level
headings, JSON policy/component/workflow identities and platform task names.
It does not assert that lexical identity means applicability or implementation.

The initial candidate seed is intentionally bounded to 180 distinct anchors
per evidence universe. That is **not** claimed to represent 100% of Kalaxy3's
concepts, requirements, or architecture. All other sources remain inventoried,
with `not_evaluated` semantic mapping. `candidate_seed_cap_reached` and
`model_coverage_qualified=false` prevent the seed from being mistaken for a
complete ontology. No LLM or novel ontology engine is introduced in this slice.

`main` and the feature branch get distinct candidate projections. Their
common ancestor is recorded; changes on `main` and changes on the feature
are calculated **separately from that ancestor**. A newer `main` file not
present in an older feature checkout is not mislabeled as removed by that
feature. Candidate semantic joins retain their origin paths, exact committed
revisions and source digests. Identical provisional labels are not sufficient
to establish an authoritative relationship.

Literal local Markdown references may become `REFERENCES_SOURCE` edges with
`semantic_authority=source_reference_only`; these are not `DEPENDS_ON`,
`IMPLEMENTS`, `SATISFIES`, nor evidence of runtime status. The existing
Neo4j projection writer keeps them version-scoped and candidate-only. No active
reference is altered, and no deployment is attempted by the bootstrap CLI.

## Independent interpretation and review

Candidate concept-to-evidence links reuse the existing content-aware matcher.
The generated feature projection is passed to the existing blinded review and
independent precision/recall machinery as `evidence_derived_candidate`.
No reviewer answers, semantic approval or acceptance thresholds are produced
by this adapter. Unknown, absent and opaque source formats remain accounted
for. The output packet is not a representative statistical sample unless an
independent review confirms that property.

The source trees, projection candidates, review packet, blank labels template
and a summary receipt are written **outside** the repository with restrictive
permissions. No raw committed source bodies are exported. A changed main or
feature ref changes the projection fingerprint and invalidates the prior review
scope. All outputs remain local until governed publication is separately
qualified.

## Remaining objective gates

Architect-supported concept breadth, independent semantic relevance labels,
paraphrase recall, exact established-link retrieval, live Neo4j integration,
feature/promotion synchronization, atomic active-reference changes, recovery,
external evidence freshness, and break-glass semantic repair remain unqualified.
This bootstrap must not be used as evidence that these DoD areas are complete.
