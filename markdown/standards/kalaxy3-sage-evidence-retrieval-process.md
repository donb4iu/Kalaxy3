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
