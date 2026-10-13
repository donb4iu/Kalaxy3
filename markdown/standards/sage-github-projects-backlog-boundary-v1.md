# SAGE GitHub Projects backlog authority — candidate v1

Status: **candidate; not governed, connected, or activated**.

Parent functional objective: **Architecture Helper Dashboard**, including secure Cloudflare remote participation, RACI functional observability, decision support, and patch/recovery review.

Immediate work: preserve unfinished and deferred Kalaxy3 work in a GitHub Projects backlog without replacing Git source authority or SAGE evidence authority.

## Authority

- Architect controls objective, priority and material authority changes.
- GitHub Projects/Issues owns work identity, backlog state, prioritization and iteration data **after independently verified baseline activation**.
- Git owns branches, commits, diffs and PRs. Unqualified source may be preserved on WIP branches without promotion claims.
- SAGE validates and records execution evidence; does not implement another backlog engine.
- LLMs propose, never call arbitrary GitHub mutations. Deterministic delegated adapters may later execute exact authorized proposals.

## Discovery slice

`workflow.projects_inspect` permits only fixed read-only GraphQL document shapes, bounded responses, explicit credentials from outside repository source, and fail-closed pagination. It does not own secrets and has no mutation entry point. GitHub GraphQL transport is HTTP POST but queries have no mutation operations.

The initial adapter scopes to user-owned Projects. Organization-owned Projects, credential qualification, Vault binding, cursor pagination, a migration mutation adapter, and independent post-import verification are **not implemented**. Do not assert complete coverage when listing pagination is present.

## Migration guardrails

1. Reconcile existing GitHub issues and projects before creating work items.
2. Deduplicate SAGE records by **functional work**, not by execution attempt count.
3. Preserve original Git/SAGE evidence links and provenance.
4. Treat accepted/implemented/validated SAGE action statuses as governance facts, not proof of functional completion.
5. Never invent priority, story points, ownership, or completed-work claims.
6. Preserve break-glass history, original dashboard scope and resumption obligation.
7. Apply approved changes through a separate exact-batch mutation adapter with independent read-back verification.
8. Return to dashboard delivery after backlog baseline acceptance.

## Acceptance maturity

- This slice: source-only read adapter and tests.
- Next: credential authority binding and live authenticated, non-secret discovery; compare existing items to candidate manifest.
- Later: approved idempotent import and coverage verification, then backlog authority activation.
- Functional proof: recover dashboard after a bounded RACI repair using the backlog without persistent LLM reconstruction.
