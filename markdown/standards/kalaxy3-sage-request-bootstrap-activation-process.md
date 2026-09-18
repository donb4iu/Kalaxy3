# Kalaxy3 SAGE Request Bootstrap Activation Process

## Purpose

This composition exists only to cross the proven request-execution bootstrap deadlock for `SAGE-ACTION-20260813-001`. It does not replace ordinary request execution, lower a validator, or create a general break-glass path.

The controller is repository-owned and must be trusted independently of the atomic candidate it activates. The target checkout remains bound to branch `fix/sage-lifecycle-break-glass-20260907` at HEAD `74c96f458cc0cb9678dd288fc307e90d2f2e8e4f`. The controller may therefore be executed from an independently governed checkout while `SAGE_BOOTSTRAP_TARGET_REPO` identifies the exact clean target checkout. Integrating the controller must not advance or dirty that target checkout before activation.

## Exact authority

Activation is hard-bound in repository code to the approved objective, literal-request digest, Architect-intent digest, objective-path-decision digest, proposal package digest, atomic-composite contribution digest, target branch and HEAD, ten declared repository paths, per-file SHA-256 values, and file modes. Any drift fails before repository mutation.

The target's pre-candidate request-execution parser, request-execution composition, atomic file primitive, authority, proposal, validation, safety, routine-Git controller, Makefile, primitive registry, and change-authority map are also checksum-bound to the packet-proven current trust root. Candidate `scripts/sage/...` bytes are read only as inert proposal/contribution data before staging.

## Two-gate activation

Before mutation the controller runs the unchanged discovery, Git authority, Architect objective-path authority, federated authority reconciliation, component selection, capability-gap decision, Python payload validation, and Python safety-baseline capture from the trusted controller checkout.

It derives baseline commands only from the target repository's current `sage-change-authority.json`. Every pre-stage baseline command must pass except exactly `helm-platform: make source-guardrails` in `infrastructure/k3s-homelab`. That single failure is accepted only when its output proves the already-recorded NVIDIA Helm `binary_path` and isolated-environment defect and the exact checksum-bound candidate contains the correcting bytes. An unrelated or additional failure is a pre-mutation blocker.

Immediately before writes the controller re-verifies the clean target branch and HEAD plus proposal/contribution identity and scope. It then reuses `file.atomic-preserve-mode` for exactly the ten declared files and verifies the resulting SHA-256 values and modes.

After staging, the exact deferred `make source-guardrails` command must pass. The complete context-derived baseline must also pass. The controller then runs unchanged request-execution changed-path discovery, context-derived required validation, proposal supplemental validation, `git diff --check`, proposal-bound Python safety checks, and authority checks. Candidate control files may execute only through those post-stage validation commands; they never own transaction or rollback control.

## Failure and continuation

Any mismatch or post-stage failure rolls back the atomic transaction through the preloaded trusted atomic-file controller. SAGE independently requires the original clean target branch and HEAD after rollback. An unverified rollback remains fail-closed.

Only pass-only validation plus authority, component-selection, and capability-gap receipts permit the existing `routine-git-lifecycle` operator proposal to be emitted. Bootstrap activation does not execute Git/GitHub mutation and does not claim Kubernetes, GPU, host, credential, deployment, or Ollama runtime success.

After this one-hop blocker is removed, control returns immediately to the approved atomic Ollama candidate path. Reuse for another objective, proposal, contribution, branch, HEAD, request, or source signature requires repository source changes and normal governance; there is no runtime option for broadening the authority.

## Regression contract

`make sage-request-bootstrap-activate-self-test` deterministically exercises branch/HEAD drift, dirty-worktree rejection, proposal/contribution signature drift, undeclared path and file-mode drift, unrelated baseline failure, the exact candidate-correctable baseline case, post-stage pass-only continuation gating, rejection of unresolved same-baseline state, verified rollback state, and candidate-control-code rejection before post-stage validation.
