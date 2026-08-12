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

The repository-owned `sage.checkpoint-promotion` composition uses `git.inspect`
for Git facts and `github.inspect` for pull-request facts. It does not import
`GitRepository`, perform workflow-side `git fetch`, invoke `gh` through the
command runner, call GitHub APIs directly, or inherit GitHub credentials.

PR creation and merge remain `operator.git-proposal` boundaries, but they use the
schema 1.1 `browser-review` mode rather than GitHub CLI commands. PR creation emits a
checksum-bound GitHub compare URL with the base branch, head branch, title, and body
pre-populated; the operator only reviews the rendered GitHub form and approves creation.
After that approval, `github.inspect` verifies the exact base, head branch, source SHA,
open state, non-draft state, and affirmative mergeability while `git.inspect` proves the
remote target has not advanced. Only then may a browser-review merge proposal for that
exact PR page be emitted.

For merge, the operator reviews the independently verified PR page, selects Create a
merge commit if GitHub presents multiple merge methods, and performs the final merge
approval. The workflow itself never opens the browser or clicks GitHub controls. After
the operator merge, `github.inspect` verifies the exact merged PR and merge commit.
`git.inspect` independently verifies the remote target branch is that merge commit.
Because final ancestry proof requires the merge object in the local graph, SAGE next
emits one exact operator proposal for
`git fetch origin main`. After that bounded refresh, `git.inspect` requires
local `origin/main` and the remote target to equal the verified merge commit and
proves the frozen source head is an ancestor of `origin/main`.

Any target advancement, source divergence, stale local target, ambiguous PR,
head/base/SHA mismatch, missing merge facts, missing/failed gate, unexpected
operator command, or failed final ancestry proof fails closed.

Ordinary `sage.request-execution` remains the repository-content
`stage -> commit -> push` lifecycle. The checkpoint-promotion workflow is a
separate higher-trust composition.

The deterministic dependency-deadlock regression proves that blocked work may
be checkpointed safely while remaining non-promotable, then becomes eligible
only after the dependency is resolved and the complete applicable gate passes.
