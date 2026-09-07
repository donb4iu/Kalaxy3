# SAGE LLM role-agent shared-context architecture checkpoint

**Checkpoint:** `SAGE-CHECKPOINT-20260907-LLM-AGENT-CONTEXT-001`
**Status:** Architect-directed architecture milestone; experiment approved in principle,
production integration not yet authorized.
**Date:** 2026-09-07

## Functional milestone

Kalaxy3/SAGE should test whether the LLM integration can preserve two distinct
forms of shared context without allowing one to pollute the other:

1. **Architect ↔ LLM intent collaboration**
   - Persistent enough to support an efficient architectural partnership.
   - Preserves shorthand, evolving intent, prior discussion, challenge, judgment,
     and continuity needed for productive Architect interaction.
   - Does not become the canonical SAGE system state merely because it exists in
     conversation.

2. **SAGE-owned shared context for LLM role-agents**
   - SAGE constructs the authoritative context required for an LLM invocation to
     assume a specific contributor role and deliver a specific SAGE capability.
   - Role-agents may be fresh/disposable invocations.
   - Agent A's unaccepted conversational interpretation is not automatically
     inherited by Agent B.
   - Cross-role continuity comes from SAGE-governed objective state, evidence,
     accepted decisions, lessons, capability outputs, and explicit handoffs.

The design goal is not to make the Architect-facing LLM stateless. It is to
prevent the persistent intent-level relationship from becoming an ungoverned
memory bus for specialized SAGE agents.

## Why this milestone matters

The recent thin-slice experience exposed a recurring failure mode: the LLM can
accumulate its own interpretations, process discoveries, and task-level defects
until that self-authored worldview becomes more salient than the Architect-owned
objective and authoritative evidence. Simple functional corrections can then
expand into large amounts of internally logical but low-value process work.

The working hypothesis is that SAGE can preserve the useful Architect/LLM
partnership while isolating the execution of specialized LLM-delivered SAGE
capabilities from conversational context pollution.

## Existing SAGE compatibility

This checkpoint does **not** declare existing SAGE capability obsolete.

Existing accepted success, validated evidence, useful workflow capability,
guardrails, recovery, verification, causal evidence, orchestration, and current
work-in-progress remain legitimate evidence and candidate future-state inputs.

A future role-agent architecture may:

- retain existing capability;
- augment it;
- wrap it behind a role/capability handoff;
- coexist with it during migration;
- replace it when comparative evidence justifies replacement; or
- leave it unchanged.

A different future architecture is not evidence that accepted historical success
was invalid.

## WIP continuity rule

This checkpoint is intentionally compatible with the Kalaxy3/SAGE Git state in
which it is recorded.

- No current branch, commit, staged change, uncommitted change, or untracked WIP
  is invalidated merely because this architecture hypothesis exists.
- The checkpoint records repository state as provenance; it does not require a
  clean working tree.
- Future-state planning must reconsider useful WIP and already-earned capability
  as evidence before replacing or discarding it.
- Migration, if justified, should be incremental unless objective-level evidence
  demonstrates that compatibility is infeasible or materially harmful.
- Discovery of an unnecessary or improvable current mechanism does not create a
  requirement to remove it from the active path unless it deterministically
  affects achieving or proving the objective.

## Candidate orchestration implication

A directed graph is a candidate implementation mechanism only if evidence shows
that SAGE needs deterministic selection and handoff among role-scoped LLM
capabilities.

If used, its useful abstraction is expected to be approximately:

`objective/state -> SAGE capability / LLM role -> governed handoff -> next capability/state`

It should not become a micro-task graph that asks the LLM to duplicate process
already encoded by SAGE.

## Required compatibility experiment

The experiment must compare at least:

1. long-lived Architect↔LLM conversation carrying both intent and implicit agent
   state;
2. persistent Architect↔LLM intent collaboration plus SAGE-owned shared context
   and fresh role-agents;
3. an over-isolated control where Architect interaction is also made stateless;
4. a contamination control where unaccepted prior LLM narrative is deliberately
   injected into a role-agent context.

Historical replay should include:

- Kalaxy2 / Cloudflare workable prior art;
- the SAGE UI observation that 24 examples should be surfaced as a list;
- a successful SAGE objective episode that uses existing orchestration,
  evidence, recovery, verification, and learning capability;
- the recent multi-day drift episode as a negative-control case.

## Required evidence

Success must be externally viewable. An authorized reviewer outside SAGE's
internal execution context must be able to understand:

- the functional objective;
- which role/capability was invoked;
- which context SAGE supplied;
- provenance of relevant evidence and accepted history;
- the role output and governed handoff;
- objective/value effect;
- unsupported assumptions, uncertainty, and counter-evidence;
- comparison with the conversational baseline;
- Architect interventions needed to restore intent or focus.

The reviewer must not need the historical Architect↔LLM conversation or private
chain-of-thought to evaluate the result.

## Approval boundary

This checkpoint preserves the architecture milestone and authorizes continued
evidence gathering/compatibility testing.

It does **not** by itself authorize:

- replacement of current SAGE orchestration;
- a directed-graph migration;
- removal of existing capability;
- invalidation of current WIP;
- production adoption of fresh role-agent orchestration.

Those remain future Architect decisions based on evidence.

## Candidate meta-lesson

**Construct role-specific LLM capability context from SAGE-owned authoritative
state rather than using accumulated conversational interpretation as implicit
cross-agent state, while preserving the persistent Architect↔LLM collaboration
needed for intent-level system architecture.**

The candidate remains unvalidated until the compatibility experiment establishes
that the approach improves or preserves objective focus, historical compatibility,
reuse of useful SAGE capability, Architect efficiency, and architectural
innovation.
