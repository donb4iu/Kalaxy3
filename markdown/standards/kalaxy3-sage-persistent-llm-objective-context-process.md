# Kalaxy3 SAGE persistent-LLM Architect-objective context process

## Purpose

Persistent-LLM commentary is an Architect-facing projection over SAGE evidence.
Its first responsibility is to preserve the meaning of the founding
Architect-expressed objective, not to narrate SAGE's internal workflow.

This requirement creates an independent alignment audit: a result can be
technically correct at the SAGE layer while still revealing that the process
has drifted away from the objective that caused the work to exist.

## Required Architect-objective explanation

Every persistent Architect-facing LLM result MUST lead with a succinct but
complete explanation that is grounded in the founding Architect-expressed
objective associated with the active SAGE request.

The explanation MUST describe, in system/use-case terms:

1. **What changed or was learned toward the Architect's objective.**
   State what was accomplished, not accomplished, proven, disproven, or learned.
2. **Why the work was necessary for that objective.**
   Preserve the causal connection between the work and the requested outcome.
3. **What the outcome means from the Architect's perspective.**
   State what is now possible, safer, proven, unchanged, or still functionally
   blocked.

The explanation MUST remain understandable and useful if all SAGE-specific
terminology and the entire SAGE trace are removed.

## Founding-objective authority

The contextual explanation MUST be derived from the founding Architect request
that caused the SAGE request to exist. A narrower objective, action identifier,
fresh-role interpretation, recovery boundary, planning source, candidate state,
or other SAGE-owned derivative MUST NOT silently replace that founding
objective as the explanation's frame.

When the Architect explicitly changes the objective, the new Architect
direction becomes the governing frame with preserved provenance to the prior
objective.

## Separation from the SAGE trace

Detailed SAGE commentary remains valuable supporting evidence: roles, receipts,
digests, validations, lifecycle state, recovery classification, and next
boundaries explain how SAGE knows what it knows. They are subordinate to the
Architect-objective explanation and MUST NOT substitute for it.

A phrase such as "the guardrail passed", "semantic confirmation completed", or
"the lifecycle advanced" is not sufficient objective context unless the
Architect's founding objective was explicitly to change that SAGE capability.

## Alignment-defect semantics

A missing, SAGE-internal-only, materially incomplete, or semantically drifted
Architect-objective explanation is a persistent-LLM alignment defect.

The defect:

- is recorded as an audit failure in the presentation/alignment layer;
- does not erase valid engineering evidence or roll back already-proven work;
- must be corrected before the persistent LLM represents the result as aligned
  progress or relies on its own summary to introduce a new objective decision.

## Machine-checkable audit projection

A persistent result may be projected to JSON for deterministic audit using:

- `founding_architect_objective`
- `founding_request_sha256`
- `progress`
- `why`
- `effect`
- `remaining`
- `sage_trace`

The guardrail validates the binding when the founding request is supplied and
rejects an internal-only explanation when the founding objective is not itself
a SAGE capability objective.
