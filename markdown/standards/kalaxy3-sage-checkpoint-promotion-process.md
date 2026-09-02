# Kalaxy3 SAGE checkpoint promotion process

Checkpoint persistence and trust-boundary promotion are distinct lifecycle
operations. A synchronized checkpoint commit or push preserves engineering
state for business continuity; it does not assert validation, promotability,
merge readiness, deployment readiness, or completion. Incomplete and
dependency-blocked checkpoints are explicitly allowed to remain non-promotable.
Promotion to `main` requires a clean synchronized source branch, independent
remote-source equality, a frozen target whose local remote-tracking ref matches
the independently read remote branch head, proof that the source descends from
that frozen target, and the conjunction of every applicable validation gate.
`make sage-guardrails` always applies. Documentation and homelab paths add their
existing publication and cluster guardrails.
The implementation action is provenance, not a circular eligibility gate.
Promotion eligibility is established by current authority and validation
receipts.

## Pre-promotion source reconciliation

The source-descends-from-target requirement remains mandatory. When a clean,
synchronized source branch contains unique work but current `main` has also
advanced since the branch fork, checkpoint promotion does not weaken or bypass
that ancestry gate. Instead, before promotion validation, the composition may
enter one bounded **source reconciliation** sub-lifecycle using the same
least-authority Git facts and operator-proposal model.

Reconciliation is eligible only when the local and independently read remote
source heads agree, the local `origin/main` and independently read remote target
agree, both sides have a non-empty unique delta, and the source-side and
target-side three-dot changed-path sets are disjoint. Any overlapping changed
path fails closed for explicit Architect-owned reconciliation; SAGE does not
guess conflict resolution.

For an eligible divergence, SAGE emits exactly one checksum-bound operator Git
proposal to merge the **exact frozen target SHA** into the source branch with a
normal merge commit (`--no-ff`, no rebase, reset, force push, or history
rewriting). After the operator result, `git.inspect` must prove that the new
source HEAD is exactly one merge commit whose first parent is the frozen source
and whose second parent is the frozen target, while the live remote source still
equals the frozen pre-merge source. SAGE then emits exactly one source-branch
push proposal. After that push is independently verified, the reconciliation
state closes and the composition immediately restarts ordinary checkpoint
promotion using the reconciled source HEAD and the then-current target
authority. All applicable promotion gates are rerun; reconciliation itself
earns no promotability claim.

If `main` advances again, the restarted promotion evaluates the new authority
again rather than treating the earlier reconciliation as current. Source-branch
retirement remains outside this blocker-remediation slice and is reconsidered
only after successful promotion; its deferral does not weaken the requirement
that `main` become authoritative for the promoted source.

The repository-owned `sage.checkpoint-promotion` composition uses `git.inspect`
for Git facts and `github.inspect` for pull-request facts. It does not import
`GitRepository`, perform workflow-side `git fetch`, invoke `gh` through the
command runner, call GitHub APIs directly, or inherit GitHub credentials.
PR creation and merge remain `operator.git-proposal` boundaries, but they use the
schema 1.1 `browser-review` mode rather than GitHub CLI commands. PR creation emits a
checksum-bound GitHub compare URL with the base branch, head branch, title, and body
pre-populated; the operator only reviews the rendered GitHub form and approves creation.
If an earlier operator-approved promotion attempt already created exactly one open,
non-draft pull request whose base, head branch, and head SHA match the newly frozen
source, SAGE may reuse that existing review state instead of fabricating or requesting
a duplicate PR-create mutation. `github.inspect` must independently identify the
exact PR, prove affirmative mergeability, converge the complete required check set on
one successful exact-source check suite, and `git.inspect` must prove the frozen target
has not advanced. Only then may SAGE emit the browser-review merge proposal directly.
If no exact PR exists, the normal PR-create boundary remains required; ambiguous or
mismatched PR state fails closed.
After PR creation approval, `github.inspect` performs the same exact base, head branch,
source SHA, open state, non-draft state, mergeability, required-check, and frozen-target
verification before a merge proposal may be emitted.

Persisted operator-boundary identity is recovery context, not authority over Git/GitHub
chronology. On continuation SAGE independently observes the exact PR for the frozen base,
head branch, and source SHA. If that PR is already merged, SAGE does not replay PR creation
or merge merely because an earlier state record names one of those boundaries. It instead
re-proves the exact-source required checks, exact frozen base, merged state, and target
advancement, records that no satisfied mutation was replayed, and proceeds directly to the
bounded post-merge graph refresh. An absent, ambiguous, closed-unmerged, mismatched, or
otherwise invalid exact PR still fails closed. The configured operator boundaries therefore
describe available authority surfaces, not a mandatory mechanical sequence.
For merge, the operator reviews the independently verified PR page, selects Create a
merge commit if GitHub presents multiple merge methods, and performs the final merge
approval. The workflow itself never opens the browser or clicks GitHub controls. After
the operator merge, `github.inspect` verifies the exact PR identity, closed/merged
state, and `merged_at`. GitHub's `merge_commit_sha` is retained when present but is
nullable because the REST response may omit it for an already merged PR. SAGE therefore
reads the live remote target head only to prove that the frozen target has advanced, then
emits one exact operator proposal for `git fetch origin main`. After that bounded refresh,
`git.inspect` requires local `origin/main` to equal the independently read live remote
target and finds exactly one reachable merge commit whose first parent is the frozen
target and whose second parent is the frozen source. If GitHub supplied a merge commit
SHA, it must equal that Git proof. Commits produced by repository automation after the
merge are permitted only as descendants of that exact merge commit. After the merge
interaction, the source branch itself may also receive a synchronized repair or recovery
commit without rewriting the frozen promotion source; continuation requires that the frozen
source remain an ancestor of the current synchronized source branch. Before PR verification,
source equality remains exact.
Any target advancement before merge, source divergence, stale local target, ambiguous
PR, head/base/SHA mismatch, missing affirmative merged state, missing/failed gate,
unexpected operator command, local/remote target divergence after fetch, non-unique or
wrong-parent merge topology, GitHub/Git merge-SHA disagreement, or failed final ancestry
proof fails closed.
Ordinary `sage.request-execution` remains the repository-content
`stage -> commit -> push` lifecycle. The checkpoint-promotion workflow is a
separate higher-trust composition.

The deterministic dependency-deadlock regression proves that blocked work may
be checkpointed safely while remaining non-promotable, then becomes eligible
only after the dependency is resolved and the complete applicable gate passes.
## Exact-source CI convergence (prospective after PR #21)
Promotion mergeability is necessary but not sufficient. After PR creation, or after reuse of an exact already-open PR, and before SAGE offers the merge boundary, `github.inspect` reads the policy-required GitHub check runs for the exact frozen source SHA. The complete required-check set must converge on exactly one check suite in which every required check is uniquely present, `completed`, and `success`. Missing, queued, in-progress, failed, cancelled, stale, neutral, skipped, incoherent, or multiply successful required-check suites fail closed.
The source-SHA binding is deliberate. The portable-stage workflow runs on feature-branch `push` so its authoritative stage evidence is attached to the exact source commit rather than only to GitHub's synthetic pull-request merge ref. Additional pull-request checks remain useful integration evidence but do not replace frozen-source identity.

This is a prospective correction learned from PR #21. Historical PR #21 check state is preserved and is not rewritten.
