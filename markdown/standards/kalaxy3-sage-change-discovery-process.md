# Kalaxy3 SAGE Change Discovery Process

## Purpose

This standard ensures that a requester can state a desired outcome without
having to know or restate Kalaxy3 governance rules.

The repository MUST establish the applicable SAGE context before analysis,
editing, deployment, publication, or recovery work begins.

## Authoritative discovery components

The authoritative discovery path consists of:

- `AGENTS.md`
- `SAGE.md`
- `sage-change-authority.json`
- `scripts/sage/sage-change-preflight.py`
- `scripts/sage/sage-change-discovery-guardrail.py`

## Required sequence

For every request:

1. Preserve the request as received.
2. Run the SAGE change preflight from the repository root.
3. Infer all applicable change contexts.
4. Expand required dependent contexts.
5. Read every reported authoritative file.
6. Run every baseline check before editing.
7. Resolve failures before implementation.
8. Implement through repository-owned automation and authority files.
9. Treat inactive reviewable work as a staged implementation.
10. Run every required validation before activation.
11. Preserve terminal evidence.
12. Publish evidence through the repository-owned SAGE process.

## Resumed work

A pre-existing branch or partial implementation does not bypass discovery.

The implementer MUST run request-based discovery and MAY additionally run:

```bash
python3 scripts/sage/sage-change-preflight.py --changed
```

## Unclassified requests

The preflight MUST fail closed when no specialized context can be inferred.

The authority map must then be extended and protected by regression and
mutation tests before implementation continues.

## Acceptance criteria

The discovery path is compliant only when:

- repository-root entry points direct implementers to SAGE discovery;
- request classification is machine-readable and deterministic;
- dependencies between change contexts are expanded automatically;
- authoritative files and working directories exist;
- baseline and post-change validation are reported;
- regression tests recognize representative Kalaxy3 requests;
- malformed authority maps fail validation;
- the requester need not enumerate internal governance rules.

## Enforcement entry points

The repository root MUST provide `make sage-preflight`, `make sage-changed`,
and `make sage-guardrails`.

Component guardrail chains MUST depend on the repository-owned discovery
guardrail. Pull requests MUST run the discovery self-test, discovery
guardrail, and evidence-index check. Publication jobs MUST NOT run for
pull-request events.

## Evidence-generation handoff

Discovery MUST hand the original request, inferred contexts, authority
files, validation requirements, repository state, and evidence gaps to the
repository-owned evidence orchestrator.

The handoff MUST automatically apply the canonical generation request.
Requesters are not responsible for remembering or reproducing the SAGE
evidence prompt.
