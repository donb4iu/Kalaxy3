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
