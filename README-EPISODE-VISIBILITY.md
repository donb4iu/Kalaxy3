# SAGE objective-episode visibility — first repository-owned vertical slice

## Objective and RACI boundary

GitHub Project defines the governed functional episode; the linked Issue is its live, operator-facing event surface. GitHub Actions—not the LLM—emits deterministic episode transitions. The Architect retains promotion authority.

- **Responsible:** trusted GitHub Actions readback operator
- **Accountable:** Architect
- **Consulted:** independently qualified Referee / Reviewer (their approvals are not inferred)
- **Informed:** Project/Issue observers see each episode and GitHub Actions evidence
- **No authority:** episode publication cannot approve, merge, promote, or change Project status

## Observable contract

One run-and-attempt-scoped comment is created at `begin` and updated at `finish` on the issue already linked to the Project. The comment shows objective, responsible/accountable roles, source SHA, branch, actor, run URL, current status, evidence pointer, and next decision.

The start, complete/blocked, and transport-test states are kept separate. The terminal state `observed` requires a live receipt whose repository, Project, issue, source SHA, and run ID match the actual Actions context. A branch transport exercise is explicitly not an AC5/production success claim.

The source JSON events are retained as Actions artifacts for 30 days; the issue comment is a discoverable projection, not an immutable Git fact or a substitute for governed persistence. The Project Status field is not changed.

## Credential separation

`ac5-readback`: read-only protected Projects credential, no issues-write token. `episode-start` and `episode-finish`: GitHub's scoped `GITHUB_TOKEN` with `issues:write`, **no Projects credential**. LLM participants receive neither. All jobs use Actions, not the operator Mac.

The qualification workflow runs on `qualification/sage-episode-visibility-*`, executes unit tests without credentials, then requires the existing `sage-projects-qualification` environment approval to exercise real issue-comment publication. It does not touch production Project fields or merge anything.

## Scope and limitation

This integrates episode publication with the issue #44 / PR #48 read-back workflow, as the first vertical slice. Other SAGE workflows must explicitly call the same generic publisher at their own functional boundaries; it does **not** claim that every SAGE function is instrumented. Project and Issue numbers are workflow inputs, not hard-coded inside the publisher.

The `feature/sage-episode-visibility-v1` branch is based on PR #48's reviewed head, so the new visibility capability remains a separately reviewable change and does not mutate PR #48 or `main`. Its first production use requires an explicit Architect promotion decision.

## Qualification and acceptance

1. GitHub Actions branch preflight passes `test_sage_episode_visibility.py`.
2. Human approves the `sage-projects-qualification` environment for the exact qualification SHA.
3. Project-linked issue shows an `running` episode and then `transport_exercised` under one run marker; no AC5 success claim.
4. Remote run and artifact verify, temporary qualification branch is removed, feature branch remains for review.
5. Source review confirms main workflow's start/finish jobs' permissions and live receipt binding.
6. Architect explicitly approves promotion before production execution on main.

No extra Python dependencies; uses Python 3 standard library only.
