# Kalaxy3 SAGE deterministic evidence retrieval process

## Status

This process defines the first repository-native SAGE retrieval vertical
slice. It deliberately uses deterministic repository data rather than
embeddings, a graph database, or an external service.

## Purpose

A successful SAGE preflight must distinguish between:

1. no structured lesson matched the request; and
2. no relevant engineering experience exists.

The second conclusion cannot be inferred from the first. Retrieval therefore
searches the canonical evidence catalog and the structured lesson, failure,
improvement-action, and post-session-review registries.

## Inputs

The literal change request is mandatory. Retrieval sources and scoring weights
are controlled by `sage-evidence-retrieval-policy.json`.

## Deterministic ranking

The implementation tokenizes the literal request, expands only
repository-defined term groups, applies fixed integer field and source weights,
and sorts by score, identifier, and source path.

## Evidence disposition

Every candidate begins as `pending`. Before implementation closeout, each
candidate must become `applied`, `reviewed-not-applicable`, or `rejected`, with
a rationale.

## Validation tiers

Source-only validation covers parsing, deterministic ranking, negative
selection, and disposition validation without third-party packages. Operator
validation later proves that retrieval informed the Grafana dashboard and
records recurrence, rework, and time to validated implementation.

## First acceptance case

For the Kalaxy3 operations-dashboard request, retrieval must surface relevant
observability, centralized-logging, storage, Kubecost, and runtime-validation
evidence even when `sage-lessons.json` reports no directly applicable lesson.

## Relevance eligibility

Source type and validation status are ranking bonuses, not evidence of
relevance. A candidate must first match at least one substantive request term.
When the request activates domain groups, the candidate must match at least
one non-governance domain group before bonuses are applied.

Each request term is scored only once, using the strongest configured field,
so the same word in a title and full record body does not inflate the result.

Registries may store identifiers inside records or as mapping keys. Both forms
must produce the same stable identifier and record count.

## Failure-triggered retrieval before retry

An unexpected implementation or validation failure is a mandatory retrieval
trigger, not permission to immediately produce another speculative correction.

Before another corrective mutation, SAGE searches repository evidence,
lessons, actionable failures, decisions, validation records, and canonical
recovery. When an authoritative schema, registry, source file, or structured
command interface exists, that production contract is inspected before a
replacement parser or recovery helper is written.

Repository validators enforce this rule through
`scripts/sage/sage-validator-runner.py`. Every nonzero validator result that
is not already an actionable-failure passthrough invokes
`scripts/sage/sage-failure-retrieval-gate.py` before retry guidance is emitted.
The gate writes a local, non-repository receipt containing the literal failure
request, source counts, ranked results, and a digest of the bounded error
summary.

A result with no match is valid: classify the failure as new and inspect
repository authority before retrying. A second failure in the same class
requires a lesson or improvement action before another speculative attempt.

## Retrieval quality fields

Every ranked result must expose relevance, confidence, exact applicable facts,
source location, and recency without inventing metadata.

- Relevance remains the deterministic score, matched terms, matched request
  groups, and score reasons.
- `confidence` copies the record's explicit `confidence` field. When the source
  record has no confidence field, the result says `not-recorded`; confidence is
  never inferred from source type, status, identifier, or ranking.
- `applicable_facts` contains exact scalar values copied from the source record.
  Every value includes its exact JSON field path and the literal request terms
  that matched it. Retrieval does not paraphrase these facts.
- `source_section` identifies the first applicable fact's exact record field,
  plus an explicit navigation section and source document when the record
  supplies them.
- `recency` uses explicit ISO date or timestamp fields only. Evidence prefers
  `valid_as_of`; post-session reviews use `recorded_at`; improvement actions may
  use `history[*].recorded_at`. Missing recency is `not-recorded`. Dates are
  never inferred from identifiers, file names, Git metadata, or filesystem
  modification times.
- Explicit recency is a tie-breaker only after relevance score. It cannot make
  an irrelevant record relevant or outweigh stronger literal relevance.

The source-only test suite must prove exact fact provenance, non-inference for
missing confidence and dates, explicit recency tie-breaking, production failure
registry support, and schema enforcement.

## Contextual reconsideration and innovation participation

Retrieval is not complete when SAGE merely ranks prior experience. The ranked
source facts remain immutable, and the retrieval result carries a digest over
that immutable basis. An LLM contribution may add only the contextual assessment
fields; changing source facts, rank, provenance, confidence, or recency fails
closed.

This contract is published additively as retrieval-result schema v1.1. Historical
v1.0 retrieval results remain readable without rewrite; they do not acquire
contextual-reconsideration authority retroactively. New in-loop reconsideration
requires v1.1 so the immutable retrieval basis and assessment fields are explicit.

For every retrieved candidate that participates in an architecture decision, the
LLM records two distinct judgments before implementation commitment:

1. **Applicability** -- whether the evidence is applicable, partially applicable,
   contextually relevant but not currently applicable, requires revalidation, or
   has been superseded for this context.
2. **Value effect** -- whether reconsidering that evidence strengthens, weakens,
   redirects, expands, or does not materially change the current candidate.

The assessment also records whether the evidence changes the architectural
alternative set through reuse, augmentation, replacement, intentional
coexistence, or addition of an existing capability as an explicit alternative.
It may propose bounded augmentations and additional acceptance criteria. Evidence
that is currently non-applicable, requires revalidation, or is superseded for the
current context carries a reconsideration trigger rather than being forgotten.
Historical truth is not rewritten merely because current comparative fitness
changes.

Existing capability creates a **consideration obligation, not a selection
preference**. When retrieved evidence exposes materially overlapping capability,
reuse, augment, replace, intentional coexistence, and do-nothing remain legitimate
Architect choices against the same intent, constraints, Definition of Done, and
current evidence. This specifically prevents accidental divergent stacks while
allowing deliberate redundancy when the Definition of Done justifies it.

The intent-to-outcome front door owns the lifecycle gate. Initial LLM ideation is
preserved before the retrieval result constrains the candidate. If relevant
evidence exists, the front door pauses at `evidence-reconsideration`; a finalized
assessment and, when the assessment materially changes alternatives or criteria,
a refreshed engineering contribution are required before semantic confirmation.
Additional acceptance criteria become Architect-dispositioned semantic proposals
and, when accepted, downstream planning obligations.

The minimum observability contract reports candidate count, assessment coverage,
alternative-set changes caused by rediscovered prior capability, augmentations,
additional acceptance criteria, revalidation needs, and reconsideration triggers.
These are process/evidence facts; SAGE does not manufacture unavailable human
effort or claim that retrieval reduced rework until measured outcomes support it.
