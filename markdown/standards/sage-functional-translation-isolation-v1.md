# SAGE Functional Translation Isolation — bounded first slice

## Active objective and purpose
The Architect-owned parent objective remains **SAGE Human Participation Workbench**: deliver a read-only browser experience showing functional objectives, demonstrated progress, evidence maturity, uncertainty, choices, human decisions, and next work. No browser delivery has yet been independently verified. The isolation work is a **necessary blocker/risk-removal dependency**, not a competing objective. Return immediately to delivering the workbench after the bounded slice is validated.

## Authority boundaries
1. **Persistent LLM:** a replaceable functional stakeholder adapter. May send goal, known functional status, verified evidence references, functional constraints, and unmet needs. Cannot send Git commands, SAGE primitive names, workflow state transitions, role prompts, source patches, or conversational history through this interface. It has no execution authority.
2. **Fresh translator:** a *single semantic decision episode*, using an entirely new invocation with no inherited dialogue. Its trusted context is only the governed SAGE interface and selectively retrieved, provenance-qualified objective evidence. It emits a checksum-bound disposition: `executable`, `clarify`, or `blocked`. It cannot mutate repositories or approve its own output. Clarification returns to the persistent functional adapter; retries are new invocations, not continued conversations.
3. **SAGE:** deterministic validation, authoritative planning, approval and execution contracts. Its existing approval-atomic execution may continue without the translator. Git remains authoritative for Git operations; SAGE records verified results.
4. **RACI:** Responsible delivers functional work and updates progress; Accountable challenges drift and owns outcome assessment; independent Reviewer checks outcome and patch evidence; Architect owns intent/scope/authority. Operational activation is a distinct requirement; PR #35 promotion alone does not prove it.

## Durable objective progress
Persist the objective id, Architect intent, success evidence, functional maturity, verified accomplishments with provenance, unresolved gaps, current activity, actor responsibility, next value-producing action, active blockers, detour start and return obligation. **Do not** persist an LLM conversation as authoritative progress. Each completion and handoff must be independently rehydratable from governed objective records. Pre-implementation exploration can count as progress but must not be mislabeled as validated software.

## Patch mechanism
A blocked fresh translator emits a minimal reproducible *defect candidate*: functional requirement, failing SAGE boundary, expected/observed behavior, evidence, and impact on objective delivery. A deterministic classifier distinguishes ambiguous functional intent, translator error, deficient implementation, and genuinely absent governed capability. Only the latter two may proceed to patch consideration. A fresh Responsible implementation role can produce a bounded candidate under existing authority; an independent Reviewer validates a regression for the **original functional behavior**. Accountable checks that the detour removed the blocker and returns to the parent objective. Material authority/scope expansion is routed to the Architect. Deferrable cleanup is recorded but not executed. Recurring failures require a lesson and new guardrail, not blind same-class retries.

## Lifetimes and termination
Translator lifespan: one invocation and one decision. No memory between invocations. SAGE execution and objective evidence may persist longer. Mechanical execution errors are corrected by delegated adapters under approved authority without spawning translator sessions. Material new evidence may start a new isolated decision episode. No automatic loop of self-generated patch requests.

## MVP acceptance
- A malicious or accidental SAGE operation embedded as an extra field in the functional request fails closed.
- No persistent dialogue or translator output is included as trusted source authority.
- A translator response is cryptographically bound to the exact functional request.
- `clarify` and `blocked` outcomes are explicit and bounded.
- An already-approved execution can resume without re-invoking the translator.
- A fresh Responsible role can recover the workbench objective, current maturity, and next functional step without user reconstruction.
- A bounded patch is successful **only if** the previously blocked functional dashboard milestone can then advance.

## Implemented vs outstanding
This package implements the **input/output contract validator and offline negative tests**. It does not yet wire the existing `llm_role_invocation.py` runtime, enforce process-level context isolation, persist objective progress in governed Git, activate RACI roles, or deliver the dashboard. Do not claim those capabilities from these tests. Integrate them with repository-owned workflows using exact source/authority validation and independent review.
