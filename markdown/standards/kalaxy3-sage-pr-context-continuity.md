# SAGE PR context continuity — additive, advisory-only engineering contract

**State:** Proposed contribution; requires repository-native qualification and the existing Architect authority boundaries. **Not** a new SAGE workflow engine, approval process, acceptance threshold, or issue-close automation.

## Purpose

For *future* objective execution, bound each PR to one independently observable milestone while preserving context for isolated role agents across PR boundaries. Do **not** retroactively split Issue #50 / draft PR #51 just to produce a desired shape. PR size is a **means** of reducing interpretive drift, not an acceptance result.

## Existing prior art

This extends `.github/workflows/pr-granularity-advisory.yml` and `scripts/ci/pr_granularity_advisory.py`, which already issue nonblocking warnings when PRs lack a milestone, close unrelated issues, or appear to reference a parent/multi-domain objective. Native GitHub owns issues, PR bodies, commits, reviews, merges and status; SAGE builds attributable evidence relationships and objective-scoped context without becoming GitHub's process controller.

## Prospective PR contribution envelope

- **Parent objective:** Existing Architect-approved or proposed objective reference; parent is not the PR milestone.
- **Milestone issue:** One bounded, independently testable contribution. Multiple domains under a parent do not require one issue per test, and related changes may stay together where they share a coherent acceptance result.
- **Objective contribution:** The observable behavior this PR changes. Retain the user's original objective rather than replacing it with accumulated implementation decisions.
- **Declared change paths:** Bounded path glob list. Comparing these with GitHub's actual changed-file list exposes scope expansion, but paths alone cannot prove semantic relevance.
- **Acceptance evidence:** Attributable test/receipt/source references and the observed outcome, with candidates distinguished from accepted results.
- **Known uncertainties:** Omissions, unsearched source families, unapplied obligations, historical revisions, and current accepted/candidate boundaries, including contradictory evidence when relevant.
- **Next bounded work:** Context another isolated agent needs for the following contribution, including prior art and known limitations; no implicit mandate to implement that work.

The CI evaluator captures declared PR metadata and observed base/head revision, and produces deterministic *candidate* metadata. It does not authenticate links, independently prove source coverage, decide pass/fail, require a preselected number of PRs, or elevate CI warnings to Architect authority.

## Proposed continuity invariant

`objective -> milestone issue -> bounded PR -> source/revision-pinned observed evidence -> unresolved uncertainties -> next objective contribution`

A fresh agent receives governed source context independent of persistent conversation. The PR envelope helps SAGE discover change-specific evidence, but cannot replace independent source inventory or context criticism. Contradictions, alternatives, cross-cutting obligations and feature/main distinction remain discoverable beyond the PR text.

## Initial context-assembly milestone sketch (examples only)

- **Representation:** Reuse the tested deterministic metadata prototype, with provenance and unknowns; no live graph claims.
- **Source discovery:** Integrate pinned Git inventory and read-only Issue #50 retrieval; compare evidence lanes and track misses.
- **Omission challenge:** Independent unselected source review and bounded repair of the packet, with attribution.
- **Isolated consumption:** Two fresh roles receive the same evidence baseline and independent task boundaries.
- **Objective-use measurement:** Compare retrieved sources and interpretations with independently expected relevant evidence; capture effort and intervention cost.

These are **candidate** boundaries, not five required PRs. Combine/split only where actual independently demonstrable behavior and dependencies justify it. Do not stall unrelated Issue #50 work.

## Operational boundaries

- Run on GitHub's trusted **base** revision, with `contents: read`, `pull-requests: read`, and `issues: read` only.
- No `pull_request_target` with untrusted code checkout; no writing secrets or printing tokens.
- A missing, truncated, or inaccessible changed-file list must be reported as **unknown**, never as in-scope verification.
- Warnings are advisory. Jobs succeed even if metadata is missing, incorrect, or unverifiable. No new required checks or merge gates.
- Preserve the existing Git lifecycle adapter and Architect authority. This contribution neither publishes a new issue nor modifies the main/feature history without explicit delegated action.
