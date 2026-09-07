# SAGE isolated workflow-manager role

## Objective

Prevent persistent Architect-conversation context from becoming SAGE workflow state
while retaining LLM semantic judgment where SAGE does not yet have sufficient
deterministic semantics.

The operating split is:

- **Architect-facing LLM:** persistent intent collaboration and clarification.
- **SAGE:** authoritative state, context construction, authority, deterministic
  workflow semantics, execution, recovery, evidence, and handoffs.
- **Fresh workflow-manager LLM:** semantic workflow decisions from SAGE-created
  context only.
- **Fresh specialist LLMs:** bounded advisory work when a workflow path requires it.

## First 80/20 integration seam

The existing `sage-intent-to-outcome iterate` path currently requires an external
caller to select one of four governed re-entry boundaries:

- `implementation-local`
- `planning`
- `semantic-confirmation`
- `authority`

The first isolation slice adds `manage-iterate`. SAGE constructs a fresh invocation
from its current objective route, the exact engineering contribution, trigger,
parent checkpoint, affected obligations, and approved-gap-set identity. The
workflow-manager selects the earliest existing SAGE boundary or returns
`architect-clarification-required`.

The selected governed boundary is then passed unchanged to the existing
`begin_candidate_iteration` implementation. No second planner or replacement
orchestrator is introduced.

## Architectural invariant

> Below the Architect-intent boundary, no workflow decision depends on inherited
> Architect-chat or prior role-chat context.

Every workflow-manager call is a fresh role invocation. Conversation history is
absent unless SAGE deliberately represents accepted information as authoritative
context.

## DoD bounding

Discovery does not change Definition of Done.

The workflow manager must not promote adjacent defects, experiments, or process
observations into active work unless they deterministically affect achieving or
proving the active objective. If the supplied SAGE context is insufficient to
understand Architect intent, the role returns a clarification question rather than
speculatively searching for a target.

## Execution substrate

The role-invocation contract is substrate-neutral. Ollama-over-HTTP is the first
reference adapter because prior Kalaxy experience already supports shared inference
as an HTTP service. The same SAGE role/context contract may later be satisfied by
another qualified executor without changing workflow semantics.

## Evolution

As SAGE semantic maturity improves, deterministic SAGE decisions should replace
LLM calls where the correct workflow action can be established without judgment.
The architecture does not require permanent LLM ownership of decisions that SAGE
can later make deterministically.
