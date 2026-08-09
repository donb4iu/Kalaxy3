# Kalaxy3 SAGE Request Execution Process

## Purpose

SAGE request execution closes the gap between repository discovery and one exact operator mutation boundary. The literal request remains authoritative. An LLM or other producer may supply an **untrusted proposal** package, but the proposal is not authority and does not execute itself.

The repository-owned executor binds the proposal to the exact literal request, current branch and HEAD, checksum-bound source files, declared generated files, repository evidence references, explicit capabilities, repository component candidates, and an allowlisted validation plan. A proposal that requires a new low-level primitive fails closed; a new primitive must follow the separate capability-gap approval process.

## Governing sequence

The executor uses `scripts/sage/workflows/operating_contract.py` and preserves its mandatory pre-mutation order:

1. Preserve the literal request and retrieve current SAGE evidence.
2. Inspect the current clean Git authority without mutation.
3. Perform federated authority reconciliation using SAGE-owned assertions; proposal-supplied authority assertions are not accepted.
4. Perform explicit component selection against the live versioned primitive registry.
5. Record the capability gap decision. Version 1 proceeds only when existing composition closes the gap.
6. Apply only checksum-bound declared repository content through an atomic transaction.
7. Reconcile evidence indexes only through the fixed repository `sage-index.py reconcile` path when the proposal declares generated evidence paths.
8. Run changed-path SAGE discovery and the proposal's shell-free SAGE validation targets.
9. Scan proposed Python source through the repository Git/GitHub/credential/deployment safety guardrail.
10. Emit one non-executed operator proposal for the exact Git staging boundary.

After the operator executes a proposal and returns the complete result, SAGE resumes through the mandatory post-operator sequence rather than handing control back to ad hoc instructions:

1. Verify the pasted operator result is bound to the exact proposal command and independently verify the resulting Git state through `git.inspect`.
2. Record directly observed boundary outcomes through `metrics.outcome`, preserving unavailable measurements as null.
3. Write local evidence closeout through `evidence.closeout`.
4. Only after those three steps pass, emit the next deterministic operator proposal: stage → commit → push.
5. After push verification confirms the branch is clean and equal to its upstream, mark the repository Git lifecycle complete. No further mutation boundary is emitted automatically.

The proposal package declares the single-line commit message and push remote used by that deterministic lifecycle. Pasted operator output is untrusted evidence: SAGE hashes it, records no raw output in closeout, and verifies repository state independently.

The transaction commits only after all validation and safety checks pass and the operator proposal has been written. Any unexpected failure triggers rollback of the declared repository content before closeout and requires failure retrieval and diagnosis before retry.

## Proposal package

A proposal ZIP contains exactly `sage-proposal.json` plus `payload/<repository-relative-path>` for every source file. The manifest is governed by `sage-request-execution-proposal-schema-v1.0.json` and binds:

- the exact literal request by SHA-256;
- expected non-main branch and exact Git object ID returned by `git rev-parse HEAD` (40-character SHA-1 or 64-character SHA-256);
- source paths, content hashes, and file modes;
- generated paths and whether repository evidence-index reconciliation is required;
- evidence references used by the proposal;
- required capabilities and explicit repository component candidates;
- `new_primitive_required=false` for this composition;
- a one-line commit message and validated push remote for the deterministic stage → commit → push operator plan; and
- shell-free validation commands restricted to non-mutating `make sage-*` targets.

Unknown archive files, path traversal, symlinks, duplicate paths, stale digests, request mismatch, branch/HEAD mismatch, unregistered component versions, unsafe validation targets, unsafe Python source, unresolved capability selection, or changed-path scope drift fail closed.

## Authority and human boundary

SAGE owns discovery, authority reconciliation, component selection, capability-gap gating, atomic application, validation, safety analysis, failure diagnosis, and construction of the operator proposal. Human or model expertise can propose content, rationale, alternatives, evidence references, and capabilities, but cannot convert those claims into authority by putting them in the package.

The executor performs **no Git mutation**, **no GitHub mutation**, and **no deployment mutation**. It may change only declared repository content atomically. Every generated Git command is a single non-executed operator proposal. The operator reviews and runs exactly one proposal, returns the complete output, and SAGE must complete post-operator verification, outcome metrics, and evidence closeout before it can emit the next boundary.

## Canonical request planning

Normal request execution no longer requires a caller to invent `capabilities`,
`candidates`, `selection_factors`, or capability-gap decisions. The canonical
entry point is `sage-request-plan`, which accepts the same literal request plus
a checksum-bound source-only package and derives those fields from current
repository authority, the mandatory operating contract, and
`sage-workflow-primitives.json`.

The planner emits the unchanged request-execution proposal schema. Direct
caller-authored capabilities and candidates are a bootstrap-only legacy path
and are prohibited when the repository planner applies. Request execution
continues to validate all planned semantics against the live primitive registry
before repository mutation.

## Reuse objective

This is a repository-owned reusable composition rather than a task-specific downloaded helper. The first intended consumer is the centralized-logging end-to-end SAGE thin slice. Future request classes can reuse the same request-to-operator contract by supplying a checksum-bound proposal package that passes the same authority, component, validation, safety, and exact-scope gates.
