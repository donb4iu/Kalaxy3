# SAGE semantic encyclopedia — initial conceptual model

**Context:** Issue #50, existing Neo4j query projection. **Purpose:** assemble and navigate what SAGE knows from a question, independent of what the answer will be used for. This document describes the model, not a new governance or acceptance process.

## Core model

| Element | What it represents | What it does **not** assert |
|---|---|---|
| **Source** | An evidence item with stable identity, origin, version, content digest, and optional external authority | That the content is accurate or current |
| **Concept** | A named point of semantic navigation; may be a subject, capability, objective, constraint, issue, history, or freely proposed idea | That the name is a proven classification |
| **Association** | An edge between sources and concepts, between concepts, or among evidence objects; has its own provenance and optional qualifiers | That it is useful, complete, causal, or correct |
| **Context and claim** | Source-attested section, literal reference, typed assertion, historical condition, or recorded decision | That SAGE should act on it or suppress other evidence |
| **Use observation** | Evidence of an association being surfaced, opened, relied on, questioned, or applied in an objective episode | That an unused item is false or unimportant |
| **Outcome observation** | Evidence associated with the outcome of an objective, including subsequent correction or revision | That the model can infer causal value from correlation alone |

Source identity and content authority stay with governed Git and original external systems. Neo4j is a rebuildable semantic navigation projection. Concepts, associations, metadata and observations can evolve without changing original evidence.

## Relationships are navigational, not admission decisions

An association may be literal, source-asserted, inferred, proposed by an Architect or LLM, mechanically generated, or historically observed. Its origin and qualification are **returned as metadata**, never used as a precondition for inclusion or traversal. Speculative associations are first-class *candidate knowledge*, not facts masquerading as source testimony.

The general model permits broad and potentially wrong associations. In the illustrative “all objectives are cats” case, a proposed `objective → cat` relationship would be available immediately with provenance identifying it as a proposal. Later use and correction can inform its value. SAGE does not need a prior demonstration that the association helps anyone.

Every inventoried source belongs to the `full-repository-corpus` navigation concept. This is a structural starting point, not an assertion about its subject. The model can therefore reach even opaque, historical, or initially unclassified evidence. Source-derived concepts are no longer arbitrarily truncated at 180.

## Query and traversal

A question produces one or more concept entry points. Traversal can follow edges in either direction across the connected graph; a source or concept UID is also a valid starting point. Return what exists, together with identity, lineage and all available relationship metadata. Pagination and bounded traversal depth control transport and resource use only. They are not relevance thresholds or judgments about purpose.

The current Issue #50 projection supports source–concept candidates, concept–concept links, literal source references, source sections, source-attested relationship claims, and complete corpus browsing. `semantic_walk` extends its read-only API with bidirectional, bounded-depth graph paths and unaltered relationship properties. This is graph **navigation**, not LLM reasoning or semantic evaluation.

An Architect and LLM can use the returned knowledge for an RFP, a rebuild, troubleshooting, innovation, or a question no one anticipated. SAGE need not know which. The pair may combine known evidence with new inference and external knowledge, distinguishing those from established facts.

## Value emerges through use

Useful observations include which links were surfaced, examined, cited, challenged, corrected or applied; the objective and circumstances in which they were used; and any measured later outcomes. These observations can support *subsequent* model evolution. Absence of use is not proof of irrelevance. Measures of retrieval usefulness should come from real episodes where possible, not a synthetic gate invented before application.

No usage observations are fabricated by this initial patch. It creates the source-complete conceptual foundation on which real usage evidence can later accumulate through existing SAGE evidence and objective records.

## Implemented continuation in this contribution

- Preserve all committed sources and their existing source provenance.
- Remove the initial 180-concept seed cap so every eligible source-derived candidate concept is retained.
- Add one explicit candidate navigation association from every source to `full-repository-corpus`; retain other candidate and attested relationships unchanged.
- Add `semantic_walk` for one-to-three-hop bidirectional traversal from a source or concept UID. All represented edge properties are returned without an applicability/relevance filter.
- Retain the existing source/relationship count verification, projection identity and all established tests.

This does **not** imply that every potentially meaningful subject association has already been discovered, that actual feedback has been recorded, or that a live Neo4j server has been exercised by this patch. These are statements of current implementation state, not additional acceptance gates.
