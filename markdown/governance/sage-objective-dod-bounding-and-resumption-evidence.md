# Objective DoD bounding and future-resumption evidence

**Evidence:** `SAGE-EVIDENCE-20260907-DOD-BOUNDING-001`
**Status:** Architect-accepted observation
**Date:** 2026-09-07

## Lesson

A feature or architecture objective must not acquire a larger Definition of Done merely because work exposes additional interesting questions.

The governing question is whether resolving an adjacent experiment, defect, or use case can materially change achievement, proof, design selection, remediation, or acceptance of the active objective. If it cannot, preserve it as evidence and continue.

## Why this was learned

The LLM role-agent isolation exercise produced enough evidence to support the current design direction. Continuing into the 24-example implementation, delegated `find it` discovery, contamination sensitivity characterization, or every possible future role combination would have expanded the DoD without changing the isolation decision.

## Governing rule

> **Discovery does not change Definition of Done.**

A discovered condition alters the active objective only when evidence establishes that it deterministically affects achieving or proving the objective, or when the Architect explicitly changes/delegates the objective.

Otherwise:

`observe -> preserve evidence -> continue objective`

Recording the observation creates no deployment, promotion, invalidation, remediation, migration, or implementation obligation.

## 80/20 implication

The 80/20 rule applies to the objective and decision-relevant proof. Additional characterization is justified only when plausible outcomes could select a different architecture, remediation, acceptance decision, or materially different objective path.

If all plausible outcomes lead to the same current design choice, the work belongs as future evidence rather than current scope.

## Feature resumption

When a paused feature resumes, SAGE should surface relevant observations, lessons, and prior evidence. They are reconsidered against the resumed objective. This is a **consideration obligation**, not automatic scope inclusion.

Possible dispositions are: use now, retain as background, defer again, promote to a separate Architect-owned objective, or discard as no longer applicable.

## Current dispositions

- Agent-isolation architecture: evidence sufficient for current design direction; implementation is a later bounded objective.
- `24 examples should be a list`: return to the SAGE thin slice when resumed; not additional isolation proof.
- Delegated `find it`: preserve as a future use case.
- Contamination sensitivity characterization: preserve for future root-cause investigation if drift recurs and quantification could enable a different control.
- Current Kalaxy3/SAGE WIP remains valid future-state input.
