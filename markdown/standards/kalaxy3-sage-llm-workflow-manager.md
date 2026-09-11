# SAGE isolated workflow-manager role

## Objective

Keep the persistent Architect-facing conversation above the published SAGE request and
continuation boundary. When deterministic SAGE cannot choose a candidate-iteration
re-entry boundary, SAGE constructs explicit context for one fresh advisory workflow-manager
invocation. Architect chat and prior role chat are not inherited.

## Published continuation seam

The existing `sage-intent-to-outcome-iterate` Make target remains the operator-facing
continuation entry. The caller supplies objective state, the candidate engineering
contribution, the observed trigger, and lineage checkpoint. It does not select a SAGE
re-entry boundary. SAGE invokes a fresh workflow manager and validates that its output is
only one existing boundary or an Architect clarification request.

The low-level `iterate --reentry-boundary` command remains available to repository-owned
SAGE compositions that already possess deterministic recovery or authority evidence. It
is not the normal Architect-facing continuation choice.

## Authority split

The workflow manager is advisory. It cannot execute commands, acquire Architect authority,
or invent a mutation path. Its allowed decisions are limited to the existing
`implementation-local`, `planning`, `semantic-confirmation`, and `authority` boundaries,
plus `architect-clarification-required`. The selected boundary is delegated unchanged to
the existing intent-to-outcome candidate-iteration workflow.

Discovery does not expand Definition of Done. Ambiguous Architect intent returns to an
Architect clarification boundary rather than authorizing speculative discovery.

## Fresh context

Every invocation contains only a system role contract plus one SAGE-created JSON envelope.
The envelope identifies the objective, preserves the literal request from SAGE state,
contains the current objective route and exact engineering-contribution provenance, and
states the governing decision limits. No Architect-chat, role-chat, or predecessor-chat
history is supplied.

## Runtime capability boundary

Ollama-over-HTTP remains a reference adapter, not architecture. Runtime endpoint and model
are resolved from SAGE execution configuration rather than command arguments on the
published continuation interface. If the runtime is absent or unreachable, SAGE returns a
non-mutation `workflow-manager-runtime-qualification` blocker. The persistent caller does
not implement around the missing inference capability.

## Evolution

Deterministic SAGE semantics remain preferred. As SAGE can establish a continuation without
judgment, the fresh LLM call should be bypassed rather than preserved as permanent workflow
authority.
