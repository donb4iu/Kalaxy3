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

## Session metrics and prediction scoring

Every completed improvement session must preserve raw measurements before
calculating derived rates. The canonical raw fields are defined by
`sage-continuous-improvement-policy.json` and validated by
`scripts/sage/sage-session-score.py`.

Derived rates use these rules:

- first-pass success is first-pass phases divided by total phases;
- known-failure recurrence is recurring known failures divided by known
  failures encountered;
- pre-mutation detection is failures detected before mutation divided by
  mutation opportunities;
- lesson usage is applicable lessons used divided by applicable lessons;
- a zero denominator produces `null`, not a misleading zero.

Prediction scoring uses the recorded point estimate, inclusive range, actual
value, and confidence. Signed error is actual minus the point estimate.
Absolute error is the magnitude of signed error. Percentage error is absolute
error divided by the absolute actual value and is `null` when actual is zero.
Range distance is zero inside the range and otherwise measures distance to the
nearest range boundary.

Range-hit rates must be retained by confidence level so calibration can be
evaluated across comparable sessions. The scorer must not collapse delivery,
operations, economics, and learning into a composite score before stable
baselines and justified weights exist.

The canonical scorecard contract is
`markdown/standards/sage-session-scorecard-schema-v1.0.json`. Completed
scorecards may be registered in `sage-session-improvement-registry.json`
after their implementation evidence is published.

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

### Experience-aware preflight

Repository-root `sage-preflight`, `sage-changed`, and `sage-self-test`
must load `sage-lessons.json` through `scripts/sage/sage-lessons.py`.
Applicable accepted, automated, and validated lessons must be surfaced
before implementation begins. A malformed lesson registry fails closed.

The preflight report must preserve the lesson identifier, failure signature,
preventive controls, and pre-mutation detection guidance. An applicable
lesson that is not used must be explained during post-session review.

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

## Cost and observability feedback comparison

Cost and observability feedback must compare one canonical `baseline`
snapshot with one `immediate`, `stabilization`, `trend`, or `economic`
snapshot.

The comparison must preserve:

- recurring monthly run rate;
- one-time change cost;
- avoidable-rework cost;
- named unit-economics measurements;
- named observability measurements;
- measurement type and confidence;
- source references and capture times.

Baseline and after snapshots must use matching currency, metric names, units,
and observability directions. Percentage change is `null` when the baseline
is zero.

Observability results are derived from each metric's declared direction:

- `lower-is-better`;
- `higher-is-better`;
- `neutral`.

The comparison may classify individual measurements as improved, regressed,
unchanged, or neutral. It must not create a composite quality score.

The machine-readable contract and implementation are:

- `markdown/standards/sage-feedback-comparison-schema-v1.0.json`;
- `scripts/sage/sage-feedback-compare.py`;
- `scripts/sage/sage-feedback-guardrail.py`;
- `sage-feedback-baseline-registry.json`.

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

## Candidate lifecycle controls

Candidate status is governed by an append-only lifecycle registry rather
than an unrecorded status edit.

The lifecycle is:

```text
discovery-needed
  → sized
  → decision-ready
  → sequenced
  → staged-implementation
  → active
  → validated
  → closed
```

Supported rework transitions return a candidate to the nearest appropriate
earlier state. `superseded` and `closed` are terminal.

Every transition must preserve:

- source and target status;
- sequence number;
- timestamp and actor;
- reason;
- validation references;
- candidate commit.

The default transition mode is dry-run. Mutation requires the explicit
`--apply` flag.

A staged implementation cannot become active unless:

- its deployment gate is open;
- a pre-deployment prediction exists;
- revalidation is current;
- the candidate branch is checked out;
- the local and remote feature branch are synchronized;
- validation evidence is supplied;
- the expected commit matches `HEAD`.

The foundational continuous-improvement candidate remains a staged
implementation with a closed deployment gate. This capability does not
activate it or mutate the cluster.

The machine-readable authority is:

- `sage-change-candidate-lifecycle-registry.json`;
- `markdown/standards/sage-change-candidate-lifecycle-schema-v1.0.json`;
- `scripts/sage/sage-candidate-lifecycle.py`;
- `scripts/sage/sage-candidate-lifecycle-guardrail.py`.

## Improvement actions and baseline extraction

Improvement actions convert accepted lessons into controlled engineering
changes. The lifecycle is:

```text
identified
  → accepted
  → implemented
  → validated
  → measured
  → closed
```

`rejected` is a terminal outcome for an evidence-backed no-action decision.
Supported rework transitions return an action to the nearest appropriate
earlier state.

Each action must reference at least one lesson or session and preserve:

- owner and priority;
- intended control type;
- desired outcome;
- acceptance criteria;
- measurement plan;
- append-only transition history;
- evidence references for every lifecycle event.

Action planning is dry-run by default. Registry mutation requires the explicit
`--apply` flag and a clean working tree.

Repository baseline extraction records measured Git and registry state against
an explicit baseline and current commit. When no canonical session records
exist, process metrics remain `null`; they are not inferred from terminal
narrative or commit volume.

The initial baseline records:

- Git commits and change volume;
- candidate, lesson, action, session, feedback, and lifecycle counts;
- the preserved discovery prediction;
- measurement quality and provenance;
- explicit limitations.

The baseline must not create a composite maturity or quality score.

The machine-readable authority is:

- `sage-improvement-actions.json`;
- `sage-continuous-improvement-baseline-registry.json`;
- `markdown/standards/sage-improvement-action-schema-v1.0.json`;
- `markdown/standards/sage-continuous-improvement-baseline-schema-v1.0.json`;
- `scripts/sage/sage-improvement-actions.py`;
- `scripts/sage/sage-baseline-extract.py`;
- `scripts/sage/sage-learning-guardrail.py`.

## Live-session measurement semantics

The live-session recorder measures only commands that pass through the
canonical recording boundary. It counts engineering, repository mutation,
validation, evidence, commit, push, and recovery commands. Commands that ran
before the declared boundary, unrecorded shell navigation, and unrecorded
display-only commands are not reconstructed later.

The recorder preserves two different clocks:

- command runtime records how long a command process ran;
- session elapsed time records the wall-clock interval from the declared
  session start through completion.

Neither value is automatically equivalent to active human effort. Active human
effort and waiting time remain unavailable unless they are explicitly timed
and classified.

A manual correction is an unplanned adjustment or recovery caused by an
incorrect earlier command, implementation assumption, validation result, or
tool behavior. Planned implementation iteration is not automatically a manual
correction.

A failed safety or validation command remains a failed command. When that
failure prevents an invalid commit, push, activation, or cluster mutation, it
also counts as successful pre-mutation detection. These two classifications
measure different outcomes and must both be preserved.

Unknown values are represented as `null`. A numeric zero means the value was
measured and the measured result was zero. Missing or unmeasured values must
never be silently converted to zero.

The canonical ledger stores non-sensitive command labels and command digests.
Raw command text may be retained only after redaction review. Credentials,
tokens, passwords, and secret values are prohibited.

The live-session measurement policy does not create a composite score and does
not open any deployment or activation gate.

### Repository-owned active sessions

An active session is separate from the completed session-improvement registry.
The active-session registry contains only sessions that are currently being
measured. A completed session is created later, after implementation,
validation, prediction comparison, and post-session review are available.

The repository-owned recorder supports four operations:

- `start` registers a declared measurement boundary and opens the local event
  ledger;
- `run` executes one classified command and stores only its non-sensitive
  label, SHA-256 command digest, timing, outcome, lesson use, and correction
  metadata;
- `note` records a baseline, observation, decision, limitation, or evidence
  gap;
- `status` summarizes raw active-session events without inventing missing
  measurements.

Runtime ledgers are written under `.sage/active-sessions/` and are excluded
from Git. The tracked active-session registry stores the session identity,
branch, baseline commit, prediction versions, measurement boundary, and local
ledger location. Credentials, secret values, and raw command text are not
permitted in the canonical event format.

Starting or closing a session is an explicit mutation. The recorder does not
open a deployment gate, activate a staged implementation, or mutate the
cluster.

## Post-session review

### Machine-readable review and lesson-to-control decisions

A canonical post-session review must reference a canonical session record and
preserve the implementation commit and evidence references.

The review must answer every repository-owned post-session question, classify
each failure as known or new, record whether applicable lessons were surfaced
and used, and record whether the failure recurred or could have been detected
before mutation.

Delivery, operations, economics, and learning feedback remain separate. The
review must not collapse them into a composite score.

Every lesson referenced by a failure must receive exactly one explicit control
decision:

- create an evidence-backed improvement-action draft; or
- record a reasoned no-action decision because an adequate control already
  exists or the evidence does not justify another control.

A create-action decision must produce a draft that conforms to the canonical
improvement-action registration contract. Review validation never mutates the
review or action registries. Review publication and action registration remain
separate, explicit operations.

The machine-readable authority is:

- `sage-post-session-review-registry.json`;
- `markdown/standards/sage-post-session-review-schema-v1.0.json`;
- `scripts/sage/sage-post-session-review.py`;
- `scripts/sage/sage-post-session-review-guardrail.py`.


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
