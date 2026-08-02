# Kalaxy3 SAGE Workflow Primitives and Composition Process

## Purpose

Kalaxy3 workflow automation MUST accumulate engineering experience rather than
recreating repository, Git, discovery, lifecycle, validation, Makefile,
logging, and evidence behavior in each downloaded helper.

New operator workflows are thin compositions of repository-owned, versioned
primitives. The framework begins at pilot maturity. No historical execution
count is fabricated or inferred from similar one-off scripts.

## Primitive design contract

Every primitive has one responsibility and a stable typed interface. Its
registry entry declares:

- version and evidence-based maturity;
- side effects and mutation boundary;
- idempotency and retry behavior;
- structured logging behavior;
- fail-closed behavior;
- runtime-path tests.

Primitive implementations use dependency injection for command execution and
event logging. They do not use `shell=True`. Commands have explicit argument
vectors, working directories, timeouts, expected return codes, and
secret-redaction inputs.

## Structured logging

Workflow events are append-only JSONL records under the operator's local SAGE
state directory. Events store labels and SHA-256 digests, not raw command
arguments or raw terminal output.

Every event identifies the workflow, sequence, primitive, primitive version,
step, status, and timestamp. Mutation and validation events include duration
and result provenance. Log writes are fsync-backed.

`scripts/sage/sage-workflow-usage.py` summarizes observed successes and
failures by primitive version. It does not backfill unobserved executions.

## Mutation safety

Mutations are dry-run by default and require explicit `apply=True`.

Git mutation primitives require:

- the intended branch;
- clean working state before mutation;
- synchronized local and remote commits;
- exact changed and staged path scopes;
- diff validation;
- immediate commit and push;
- clean synchronized state afterward.

File writes that serve as evidence or state use temporary files, fsync, and
atomic replacement.

## Makefile composition

Aggregate Make targets are extended through prerequisites, not by inserting
recipe lines into an unknown target body.

The complete candidate Makefile MUST be written to a temporary file and
parsed with GNU Make for the new target and each modified aggregate target
before repository replacement. Candidate Makefile parsing is a required
mutation gate.

## Composition contract

Tracked workflow compositions live under `scripts/sage/workflows/`.

A composition:

- declares `PRIMITIVES_USED`;
- imports repository-owned primitives;
- contains ordering and capability-specific parameters only;
- does not import `subprocess` or reimplement command, Git, discovery,
  lifecycle, Makefile, validation, logging, or closeout helpers;
- stops on the first failed primitive.

## Evolution from evidence

A failure is classified against the primitive version that produced it.

When the root cause is in a primitive, the correction MUST update the
primitive, add a regression test, and increment its version. A wrapper-only
patch is prohibited for a primitive root cause.

Maturity is evidence-based:

- `pilot`: zero through two successful production executions;
- `validated`: three through nine successful production executions and no
  unresolved recurrence;
- `stable`: at least ten successful production executions with measured reuse.

No primitive is called stable because its code resembles prior one-off
helpers.

## Required measurements

SAGE records:

- primitive reuse ratio;
- direct-execution violations;
- successful executions and failures by primitive version;
- known-failure recurrences;
- wrapper-only defects;
- time to validated implementation;
- avoidable rework.

These measurements determine which primitives are hardened, replaced, or
deprecated.

## Least-authority safety foundations

Phase 2 adds four pilot primitives without activating autonomous mutation:

- `git.inspect` exposes only allowlisted local read-only Git inspection. It has no fetch, branch, stage, commit, push, ref, GitHub, or deployment method.
- `file.atomic-preserve-mode` performs same-directory temporary writes, file and directory fsync, atomic replacement, existing-mode preservation, allowed-root checks, and transactional rollback.
- `operator.git-proposal` emits one schema 1.0 operator-executed boundary containing exactly one secret-free command. It never executes the proposed command and blocks the next boundary until pasted output is verified.
- `git.safety-guardrail` rejects production-helper Git, GitHub, credential-inheritance, and deployment mutation paths. Mutating Git is permitted only in an explicitly declared isolated temporary-repository fixture.

The mixed-authority `git.repository` primitive remains available only to isolated temporary-repository tests and legacy operator-owned compositions until migrated. Downloaded implementation helpers must use `git.inspect` for repository state and must not import or instantiate `GitRepository`.

Every new Phase 2 primitive is linked to an approved capability-gap receipt and an approved component-selection manifest under `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/`. The framework remains a staged implementation; deployment and autonomous Git or GitHub mutation remain unauthorized.
