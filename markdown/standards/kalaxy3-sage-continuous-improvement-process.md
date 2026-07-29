# Kalaxy3 SAGE Continuous-Improvement Process

## Purpose

This standard extends repository-owned SAGE so evidence becomes reusable
engineering capability rather than only immutable proof of completed work.

Continuous improvement must use prior evidence, cost baselines,
observability, structured lessons, predictions, confidence, process
measurements, and candidate sizing to improve future prompt resolution.

This process extends existing SAGE discovery and publication authority. It
does not create a parallel evidence system.

The machine-readable contracts are:

- `markdown/standards/sage-change-candidate-schema-v1.0.json`;
- `markdown/standards/sage-session-improvement-schema-v1.0.json`.

Candidate and session documents must conform to these contracts before
registry publication or outcome scoring.

## Authoritative discovery behavior

Requests involving continuous improvement, lessons learned, predictions,
forecast accuracy, T-shirt sizing, confidence calibration, cost comparison,
observability feedback, candidate sequencing, staged implementation, or
frequent feature-branch pushes must infer the `continuous-improvement`
context.

The context depends on:

- `repository-governance`;
- `evidence`.

A request that should use this context must fail closed until the context is
present and its authoritative files and validations pass.

## Required feedback planes

Continuous improvement evaluates four feedback planes:

1. **Delivery** — effort, elapsed time, failures, retries, first-pass
   success, recovery, and avoidable rework.
2. **Operations** — availability, errors, latency, saturation, reliability,
   capacity, security, and diagnosability.
3. **Economics** — one-time change cost, recurring run-rate delta, unit
   economics, cost provenance, and avoided cost.
4. **Learning** — applicable lessons, lesson use, known-failure recurrence,
   prediction accuracy, confidence calibration, and improvement actions.

Raw measurements must be retained. A composite score must not be introduced
until stable baselines and justified weighting rules exist.

## Required change sequence

A governed change follows this sequence:

1. Preserve the requester language exactly.
2. Run repository-owned SAGE discovery.
3. Identify relevant evidence and applicable prior lessons.
4. Establish delivery, operational, economic, and learning baselines.
5. Record a discovery-stage prediction before substantial implementation.
6. Assign multidimensional T-shirt sizing and explain confidence.
7. Register or update the candidate.
8. Implement through small cohesive commits.
9. Validate and push each cohesive commit to the feature branch.
10. Record a pre-deployment prediction before state-changing deployment.
11. Keep activation and deployment gates closed until validation passes.
12. Observe the result through defined observation windows.
13. Compare baseline, predicted, and actual outcomes.
14. Classify prediction errors and recurring failures.
15. Publish implementation evidence through the existing SAGE process.
16. Extract lessons and improvement actions.
17. Measure whether comparable future sessions improve.

## Predictions

Predictions must be recorded before their outcomes are known.

A recorded prediction is immutable. A revised prediction is a new version
and does not replace earlier versions.

The minimum stages are:

- **discovery** — after authority and baseline discovery but before
  substantial implementation;
- **pre-deployment** — after implementation validation but before runtime
  mutation.

Every prediction must identify:

- estimate;
- range;
- confidence;
- confidence basis;
- assumptions;
- known unknowns;
- failure conditions.

Post-change review must compare predictions with actual results and explain
prediction misses, including incomplete discovery, prior lessons not
applied, inaccurate baselines, scope changes, implementation defects,
environmental changes, dependency behavior, operator error, new failure
modes, narrow ranges, and miscalibrated confidence.

## T-shirt sizing and confidence

Sizing uses `XS`, `S`, `M`, `L`, and `XL`.

Sizing must separately evaluate:

- implementation effort;
- elapsed duration;
- technical uncertainty;
- operational risk;
- blast radius;
- validation burden;
- cost exposure;
- dependency complexity.

Size and confidence are independent. Small work with low confidence may
require more discovery than large work with high confidence.

`XL` work should normally be decomposed before implementation.

Confidence must be `high`, `medium`, or `low` and must include a written
basis.

## Cost feedback

Material changes must identify relevant cost views:

- one-time engineering and migration cost;
- recurring run-rate delta;
- unit economics;
- avoidable rework cost;
- measurement provenance and confidence.

Measured, allocated, estimated, and inferred costs must remain
distinguishable.

A cost increase is not automatically a regression. Added capability,
reliability, risk reduction, and useful output must be considered.

## Observability feedback

Candidates must identify relevant telemetry and observation windows.

Standard windows are:

- **baseline** — behavior before the change;
- **immediate** — deployment and startup validation;
- **stabilization** — delayed failures and resource pressure;
- **trend** — normal operating comparison;
- **economic** — normalized recurring cost and unit economics.

A change is not operationally validated merely because its resources became
ready once.

## Lessons and improvement actions

A lesson converts evidence into reusable engineering memory.

A lesson should identify:

- failure signature;
- applicable context;
- symptoms;
- root cause;
- known resolution;
- preventive control;
- preflight detection;
- first and latest supporting evidence;
- recurrence count;
- automation status.

A recurring known failure requires an explicit explanation of why the lesson
was not surfaced, applied, or enforced.

Improvement actions follow this lifecycle:

    identified
      → accepted
      → implemented
      → validated
      → measured
      → closed

Rejected actions preserve their rejection rationale.

## Candidate and branch policy

A candidate must identify its request, context, branch, baseline, status,
dependencies, predictions, size, confidence, expected value, cost plan,
observability plan, implementation outline, validation plan, deployment
gate, and revalidation triggers.

Committed, reviewable, inactive work is a **staged implementation**.

Implementation branches must use small cohesive commits. Every cohesive
commit must be validated and pushed to the active feature branch rather than
waiting until the end of the workstream.

Candidate branches must be revalidated before activation because repository
state, cluster state, cost baselines, and telemetry may change.

## Post-session review

The review must answer:

- What failed?
- Was it previously known?
- Was the applicable lesson surfaced and used?
- Why did any known failure recur?
- Could it have been detected before mutation?
- How did effort, cost, and operational behavior compare with predictions?
- Was prediction confidence calibrated appropriately?
- What guardrail, preflight, template, automation, runbook, lesson, or
  explicit no-action decision should result?
- Did the session measurably improve delivery, operations, economics, or
  learning?

## Staged implementation sequence

This workstream will add the complete capability through separate cohesive
commits:

1. discovery authority and regression coverage;
2. machine-readable policy and registries;
3. candidate and session schemas;
4. lessons and experience-aware preflight;
5. predictions, metrics, confidence, and sizing;
6. cost and observability feedback;
7. candidate lifecycle and staged-implementation tooling;
8. guardrails, baseline extraction, and scorecards;
9. SAGE implementation evidence.

Deployment and activation remain closed until the complete staged
implementation passes its required validation.

## Maturity boundary

Kalaxy3 must not claim quantitatively managed or optimizing maturity until
multiple comparable sessions demonstrate:

- stable metric definitions;
- calibrated predictions;
- declining known-failure recurrence;
- improving first-pass success;
- predictable execution ranges;
- measurable cost-value trends;
- demonstrated conversion of evidence into preventive controls.
