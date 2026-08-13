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

- `git.inspect` exposes only allowlisted read-only Git inspection. It may inspect local refs, compare local ancestry/path deltas, and read exact remote branch heads with `git ls-remote`; it has no fetch, branch, stage, commit, push, ref-update, GitHub-mutation, or deployment method.
- `file.atomic-preserve-mode` performs same-directory temporary writes, file and directory fsync, atomic replacement, existing-mode preservation, allowed-root checks, and transactional rollback.
- `operator.git-proposal` supports two explicit operator modes. Git boundaries retain the schema 1.0 one-command contract. Pull-request creation and merge use schema 1.1 `browser-review` proposals containing one checksum-bound, uncredentialed `https://github.com/` interaction URL. The primitive never executes the Git command, opens the browser, clicks GitHub controls, or performs GitHub mutation; the next boundary remains blocked until operator confirmation and independent verification succeed. Browser URL validation and encoding are local deterministic string operations; production proposal/workflow modules do not import HTTP-client libraries.
- `git.safety-guardrail` rejects production-helper Git, GitHub, credential-inheritance, and deployment mutation paths. Mutating Git is permitted only in an explicitly declared isolated temporary-repository fixture.

The mixed-authority `git.repository` primitive remains unavailable to downloaded implementation helpers. In addition to isolated temporary-repository tests and legacy operator-owned compositions, it may be consumed by the exact tracked `scripts/sage/workflows/routine_git_lifecycle.py` controller for `commit_and_push` only, after a checksum-bound operator approval and exact authority checks. No other production path receives this allowance.

`git.safety-guardrail@1.3.0` makes that exception explicit and narrow and delegates literal read-only Git classification to the canonical `git.inspect` argument contract instead of maintaining a second allowlist. The exact routine Git lifecycle controller path may import `GitRepository` and call only `commit_and_push`; branch creation, fetch, direct Git mutation, GitHub mutation, credential inheritance, deployment mutation, malformed read-only variants, and the same controller code at any other path still fail closed. This prepares the repository for a bounded one-approval stage → commit → push composition without weakening the downloaded-helper boundary or authorizing autonomous mutation.

The implemented controller is `scripts/sage/workflows/routine_git_lifecycle.py`, invoked only through the repository-owned CLI `scripts/sage/sage-routine-git-lifecycle.py` from a checksum-bound `operator.git-proposal@1.2.0` `routine-git-lifecycle` boundary. Before mutation it independently verifies the active request state, exact proposal command digest, feature branch and HEAD, declared path scope, pass-only validation receipts, synchronized upstream and remote feature branch, and frozen `origin/main`. One operator execution then authorizes exactly stage → commit → push through `git.repository.commit_and_push`. The controller records a local receipt and uses `git.inspect` to prove the resulting single-commit topology, exact path delta, clean tree, upstream equality, and remote feature-branch identity.

Request execution independently repeats the post-mutation Git proof before closeout. Existing stage → commit → push continuation remains only for compatibility with already-open states; new ordinary validated request execution uses the one-approval routine controller and fails closed when its authority prerequisites are unavailable or changed.

Every new Phase 2 primitive is linked to an approved capability-gap receipt and an approved component-selection manifest under `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/`. The framework remains a staged implementation; deployment and autonomous Git or GitHub mutation remain unauthorized.


## Decision and diagnosis primitives

Framework version 0.4.0 adds four pilot primitives:

- `authority.reconcile@1.0.0` keeps scoped source assertions separate from inference, reports conflicts and unknowns, and blocks mutation unless material authority is complete.
- `component.select@1.0.0` ranks repository-owned candidates using explicit ordered factors, retains rejected alternatives, and emits a versioned composition manifest without an opaque composite score.
- `capability.gap@1.0.0` proves configuration and composition are insufficient and requires operator approval before a new primitive may be implemented.
- `failure.diagnose@1.0.0` records direct evidence, expected and actual component paths, divergence, ownership, lesson use, recurrence, avoidable rework when measured, and a reusable correction before another corrective mutation.

These primitives construct typed in-memory records. Repository writes remain the responsibility of `file.atomic-preserve-mode`; Git and GitHub mutation remain operator-executed boundaries.


## Semantic outcome measurement

Framework version 0.5.0 adds `metrics.outcome@1.0.0`. The primitive:

- requires every schema 1.0 raw metric to be present, using `null` when measurement is unavailable;
- derives rates only after raw validation and never converts an unavailable value into zero;
- keeps authoritative repository Git mutations separate from disposable fixture Git mutations;
- rejects numerator values that cannot be a subset of their denominator;
- compares reports only when `workflow_class` matches and records the explicit comparability basis;
- emits no composite score.

Manual correction and operator intervention rates are activity shares: the count divided by commands executed plus that count. Other derived metrics use the numerator and denominator named in `sage-operating-contract-policy.json`. A zero denominator produces `null`, not zero.

The initial report at `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/outcome-metrics-baseline.json` preserves known measurements and leaves unavailable command, recurrence, intervention, fixture-mutation, elapsed-time, and rework measurements null. It is a baseline, not evidence of an improving trend.

## Root operating-contract composition

Framework version 0.6.0 adds no new primitive. The approved root-enforcement
manifest proves the existing primitives are sufficient and rejects an
autonomous mutation engine.

`scripts/sage/workflows/operating_contract.py` contains a thin two-boundary
composition. The pre-mutation sequence permits declared repository-content
writes and stops at one operator proposal. The post-operator sequence starts
with read-only verification of pasted output, then records outcome metrics and
evidence.

`make sage-operating-contract-check` runs positive, negative, ordering, and
fail-closed runtime tests plus the root policy guardrail. The target is a
dependency of the normal repository self-test and guardrail chains.

## Governed improvement-action transitions

The tracked `sage.improvement-action-transition` composition reuses the existing `sage.action-lifecycle` client. The primitive also exposes canonical pre-acceptance contract amendment for `identified` actions. Amendment uses dry-run-then-explicit-apply semantics, requires the expected current contract SHA-256, preserves complete before/after contract snapshots and changed-field provenance, leaves lifecycle status unchanged, and fails closed after acceptance or on stale authority. The composition supplies `git.inspect` as the repository-state dependency because the lifecycle client consumes only repository root, clean-state enforcement, and exact changed-path verification. The production composition itself does not import or instantiate `GitRepository`, and the lifecycle client does not perform Git mutation.

The same composition owns either one authorized improvement-action status transition or one identified contract amendment; amendment does not create a parallel orchestration path. It requires a clean synchronized non-main feature branch, invokes the canonical lifecycle tool in dry-run-then-explicit-apply order, permits only `sage-improvement-actions.json` to change, runs the registered lifecycle/learning/workflow/operating-contract validation plan, and emits exactly one `operator.git-proposal` stage boundary. The registry mutation is transactionally rolled back when validation or proposal creation fails.

After the operator executes the emitted stage command, the composition delegates verification and the remaining commit/push boundaries to the existing request-execution continuation state machine. This preserves the Phase-2 rule that Git mutation is operator-executed one boundary at a time while avoiding external lifecycle or Git choreography. `git.repository` remains restricted to its documented temporary-test and legacy scope.

## Least-authority GitHub inspection

`github.inspect` is the repository-owned read-only authority for GitHub pull-request state.
It uses only fixed GET-only GitHub REST endpoints needed to list or get pull requests and
returns structured repository, pull-request, base-branch, head-branch, head-SHA,
mergeability, merged-state, merged-at, and nullable merge-commit facts. A closed PR with
`merged=true` and a valid `merged_at` is an affirmative GitHub merge-state observation;
`merge_commit_sha` is retained when present but is not required because exact merge
identity is independently proven from Git topology after the operator fetch.

Generated workflow compositions must consume `github.inspect`; they must not invoke `gh`
or GitHub HTTP APIs directly. `operator.git-proposal` remains the exclusive pull-request
creation and merge mutation boundary. For those boundaries, `operator.git-proposal@1.1.0`
uses `browser-review`: PR creation receives a GitHub compare URL with base/head, title, and
body fully prepared, while PR merge receives the exact verified pull-request page URL.
The operator reviews GitHub's rendered state and performs the final create/merge approval.
No GitHub CLI installation is required. The inspector does not inherit `GH_TOKEN`,
`GITHUB_TOKEN`, `GITHUB_PAT`, or `GH_CONFIG_DIR`; transport or access failure fails closed.

Pull-request lookup after an operator boundary must be unambiguous and must match the
expected base branch, head branch, and head SHA. A requested mergeability or merged-state
claim must be affirmatively verifiable before workflow continuation.

`git.safety-guardrail` rejects direct GitHub API use outside the exact trusted
`scripts/sage/workflow/github_inspect.py` primitive path and continues to reject direct
`gh`, mixed Git mutation authority, credential inheritance, and deployment mutation.

## Canonical workflow framework version authority

`workflow.FRAMEWORK_VERSION` is the canonical live runtime framework-version authority.
`sage-workflow-primitives.json` declares the repository framework version and current
contract guardrails compare that declaration and workflow state to the canonical runtime
authority; current guardrails must not duplicate a semantic-version literal.

Historical evidence, recorded closeouts, migration phases, and explicit regression fixtures
retain the version they actually exercised. They are historical facts or test inputs rather
than live framework-version authorities and must not be rewritten merely because the current
framework advances.

## Checkpoint promotion composition

`sage.checkpoint-promotion` is a higher-trust composition distinct from ordinary
request-execution persistence. It reuses `git.inspect`, `github.inspect`,
`validation.plan`, and `operator.git-proposal`. It does not import
`GitRepository` or execute Git/GitHub mutation. PR creation and merge are
operator proposals. A final exact operator `git fetch origin main` refresh is
required only after GitHub has independently confirmed the exact PR is merged so
`git.inspect` can truthfully prove the exact ordered-parent merge topology and source
containment in the refreshed target graph. Post-merge repository automation may advance
`main`; those commits are valid only when they remain descendants of that exact merge.
A synchronized source branch may advance after the merge interaction for a governed repair
or recovery only when the frozen promotion source remains an ancestor; the PR identity and
Git topology proof remain bound to the original frozen source SHA.

## Browser-backed GitHub operator approval

Browser-backed GitHub proposals are navigation and approval contracts, not mutation helpers.
The proposal binds the exact GitHub URL and intended browser action with SHA-256, prohibits
embedded credentials, and records that neither browser opening nor mutation is performed by
the helper. A browser-result receipt binds the proposal identifier and interaction digest to
an explicit operator confirmation; that confirmation is never treated as proof that GitHub
changed. `github.inspect` supplies the authoritative post-click PR facts and `git.inspect`
continues to enforce source and frozen-target authority.

GitHub PR-create URLs follow GitHub's documented compare/query-parameter contract using
`quick_pull=1`, `title`, and `body`. The source SHA is not trusted from the URL: after the
operator clicks Create pull request, `github.inspect` must observe the exact expected head
SHA and frozen base SHA before merge can be proposed. Merge proposals open only the exact
independently verified PR page. The later merge-state, refreshed local/remote target equality, exact ordered-parent merge
topology, and ancestry checks remain authoritative, so squash/rebase, wrong-PR, divergent
automation, or ambiguous-merge outcomes fail closed.
