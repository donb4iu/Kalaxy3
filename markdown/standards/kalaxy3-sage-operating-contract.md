# Kalaxy3 SAGE Mandatory Operating Contract

## Status

This document defines the Kalaxy3 repository-root operating contract. The
root enforcement implementation is staged on its feature branch until review
and merge. It does not authorize autonomous Git, GitHub, credential, ref,
cluster, or deployment mutation. Final activation evidence is published in a
separate evidence commit after the implementation SHA is known.

## Purpose

Every Kalaxy3 change must begin from current authority and must prefer
repository-owned, versioned engineering capability over newly generated
task-specific machinery. SAGE must make the selected path, rejected
alternatives, capability gaps, runtime validation, failures, corrections,
measurements, and operator mutation boundaries explicit and reviewable.

## Mandatory sequence

A governed change follows this order:

1. Preserve the requester language exactly.
2. Establish current Git, GitHub, SAGE, runtime, telemetry, economics, and
   external-contract authority that is material to the change.
3. Reconcile source assertions, conflicts, freshness, unknowns, and
   applicability without converting inference into fact.
4. Declare the capabilities required to satisfy the request.
5. Search and rank repository-owned components before creating new machinery.
6. Record a component-selection manifest with selected and rejected
   alternatives, versions, evidence, mutation scope, and composition order.
7. Produce a capability-gap receipt before implementing any new primitive.
8. Keep downloaded implementation helpers limited to repository-content edits,
   validation, and read-only Git inspection.
9. Validate the real source-only and operator-runtime paths up to each
   controlled mutation boundary.
10. Diagnose every unexpected failure before another corrective mutation.
11. Present exactly one Git or GitHub mutation boundary for operator execution.
12. Require the operator to paste the complete result and verify the resulting
   state before proposing another boundary.
13. Preserve outcome, reuse, authority, failure, rework, safety, and trend
   measurements without inventing unavailable values.
14. Publish implementation evidence through the repository-owned SAGE process.

## Authority reconciliation

Authority is federated. Operator intent, Git, GitHub, repository policy, SAGE
registries, runtime state, telemetry, economics, and external product or
standards contracts retain their scoped authority.

Every authority assertion must identify:

- authority type and source;
- exact reference;
- capture time and freshness;
- direct statement or measured value;
- confidence when explicitly supplied;
- applicability to the requested change;
- conflicts and unresolved unknowns.

SAGE inference and prediction are separate records. A reconciliation may be
`complete`, `incomplete`, `conflicting`, `stale`, or `unavailable`. Mutation
remains blocked until material authority is complete enough for the proposed
boundary and the operator approves that boundary.

## Component selection and reuse

Required capabilities are declared before implementation. Repository-owned
candidates are ordered using explicit factors rather than an opaque composite
score:

- direct applicability to the required capability;
- compatibility with current authority;
- narrowest sufficient side-effect and mutation scope;
- published interface and version;
- observed successful production executions;
- known failures and unresolved recurrence;
- maturity supported by observed evidence;
- runtime-test coverage;
- secret, credential, and history-safety behavior.

The selection manifest records every selected component, rejected candidate,
unavailable capability, composition step, version, evidence reference, and
rationale. Similarity to a prior helper is not execution evidence.

## Capability-gap receipts

A new primitive or workflow mechanism may be implemented only after a
capability-gap receipt proves that existing candidates are insufficient without
violating the operating contract.

The receipt must preserve:

- the literal request and authority receipt;
- the required capability;
- every existing candidate considered;
- the exact interface or behavior missing from each candidate;
- why composition or configuration cannot close the gap;
- the proposed primitive identifier and responsibility;
- side effects, idempotency, logging, failure mode, and runtime tests;
- operator approval or rejection.

A wrapper-only correction is prohibited when the root cause belongs to an
existing primitive.

## Downloaded implementation-helper boundary

Downloaded helpers may:

- verify repository identity, branch, HEAD, local upstream reference, and
  working-tree state through read-only Git commands;
- run repository-owned discovery, validation, guardrails, and source-only or
  operator-runtime tests;
- create, replace, or restore declared repository files atomically;
- preserve existing permission bits and fsync files and directories;
- write local, non-repository event logs and closeout receipts.

Downloaded helpers must not:

- create or switch branches;
- stage, commit, push, fetch, pull, merge, rebase, reset, clean, tag, update or
  delete refs;
- invoke GitHub mutation through `gh`, APIs, or browser automation;
- deploy, activate, or mutate cluster state;
- use personal credentials inside generated code;
- combine multiple operator mutation boundaries.

## Validation

Syntax, token presence, or source inspection alone is not runtime validation.

Each changed contract or primitive must have:

- source-only validation from a clean dependency-minimal environment;
- operator-runtime validation where repository-managed dependencies or live
  APIs are material;
- positive tests for the intended path;
- negative tests that prove forbidden mutation, credential, history, and
  capability-bypass paths fail closed;
- exact-path validation up to the controlled mutation boundary;
- rollback validation for transactional repository writes;
- regression coverage for every observed failure class.

A successful command is not sufficient when the semantic outcome is wrong.
Validation must verify the resulting state and declared outcome.

## Failure diagnosis

Before another correction after an unexpected failure, SAGE records:

- what failed and the direct evidence;
- whether the failure was known or new;
- what should have happened;
- which component and version should have been used;
- which component or path was actually used;
- why the actual path differed;
- ownership: primitive, composition, policy, authority, environment, operator,
  or external dependency;
- whether mutation occurred and whether detection was pre-mutation;
- lesson retrieval and use;
- recurrence and avoidable rework when measured;
- the reusable correction or an evidence-backed no-action decision.

A second failure in the same class requires a lesson, regression control, or
improvement action before another speculative attempt.

## Operator-executed Git and GitHub mutation gate

Git and GitHub mutations are operator-executed. A proposal contains exactly one
boundary and exactly one command. It includes:

- controller, repository, branch, HEAD, and local upstream state;
- authority and component-selection receipts;
- exact changed or staged paths;
- completed validation and evidence references;
- expected result, risks, rollback, and post-command verification;
- a secret-free command representation and digest;
- a statement that no helper executed the command.

No next boundary is proposed until the operator pastes the complete output and
the resulting state is verified read-only.

## Measurements

Raw measurements are retained before derived rates. Unknown or unmeasured
values are `null`, never inferred as zero.

Required raw measurements include:

- workflows started and completed;
- first-pass completions;
- semantic validations and semantic false passes;
- commands executed, failed, and retried;
- manual corrections and operator interventions;
- authority checks and authority failures;
- component candidates considered, selected, reused, and newly created;
- component-contract mismatches and direct-execution violations;
- known failures encountered and recurred;
- mutation opportunities and pre-mutation detections;
- authoritative-repository, disposable-fixture, GitHub, and deployment
  mutations as separate categories;
- avoidable rework and prompt-to-validated-change duration when measured.

Derived rates are reported only with valid denominators. Trends compare
explicitly comparable workflow classes and remain `improved`, `regressed`,
`unchanged`, or `inconclusive`. No composite process-quality score is allowed
until stable baselines and justified weighting rules exist.

## Versioned machine-readable contracts

The staged operating-contract authority consists of:

- `sage-operating-contract-policy.json`;
- `markdown/standards/sage-authority-reconciliation-schema-v1.0.json`;
- `markdown/standards/sage-component-selection-manifest-schema-v1.0.json`;
- `markdown/standards/sage-capability-gap-receipt-schema-v1.0.json`;
- `markdown/standards/sage-failure-diagnosis-schema-v1.0.json`;
- `markdown/standards/sage-operator-git-proposal-schema-v1.0.json`;
- `markdown/standards/sage-outcome-metrics-schema-v1.0.json`.

## Staged implementation sequence

1. Policy and schemas.
2. Least-authority Git inspection, mode-preserving atomic writes, operator
   proposals, and Git-safety guardrails.
3. Authority reconciliation, component selection, capability gaps, failure
   diagnosis, and composition-manifest integration.
4. Semantic outcome metrics and comparable-session trends.
5. Root-policy and Make integration, two-boundary composition, positive and
   negative runtime tests, and repository guardrails.
6. Split SAGE evidence publication after the root-enforcement implementation
   commit is known.

The root-enforcement code remains a staged implementation until merged. Even
after repository enforcement is active, deployment and autonomous Git or
GitHub mutation remain unauthorized.


## Root enforcement composition

`scripts/sage/workflows/operating_contract.py` composes the registered
primitives into two workflows. The pre-mutation workflow ends with exactly one
operator proposal. The post-operator workflow begins only after complete pasted
output is available and performs read-only verification, semantic outcome
measurement, and evidence closeout.

The root enforcement gate is:

```bash
make sage-operating-contract-check
```

It is also included in `make sage-self-test` and `make sage-guardrails`.
