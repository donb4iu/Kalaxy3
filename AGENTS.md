# Kalaxy3 repository instructions

Every implementation, repair, investigation, documentation change, or
evidence request begins with repository-owned SAGE discovery.

From the repository root, run:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "<the request exactly as received>"
```

The requester is not responsible for enumerating Kalaxy3 governance rules.

Before editing:

1. Read every authoritative file reported by the preflight.
2. Run every reported baseline check.
3. Resolve guardrail failures before implementing the requested change.
4. Use repository-owned registries, locks, templates, and automation.
5. Treat committed, reviewable, inactive work as a staged implementation.
6. Do not activate or deploy until all reported validation passes.
7. Preserve terminal evidence and use the repository-owned SAGE
   publication process.

When resuming existing work, also run:

```bash
python3 scripts/sage/sage-change-preflight.py --changed
```

Do not bypass discovery because a branch already contains implementation
code.

## Enforced repository entry points

Use the repository-root commands for normal work:

```bash
SAGE_REQUEST="<the request exactly as received>" make sage-preflight
make sage-changed
make sage-guardrails
```

The homelab guardrail chain and GitHub validation also execute the
repository-owned discovery guardrail.

## Automatic SAGE evidence generation

The requester does not have to ask with the canonical SAGE wording.

When a request asks to document, preserve, chronicle, or create evidence
for completed work, automatically prepare evidence-generation inputs with:

```bash
SAGE_REQUEST="<request exactly as received>" make sage-evidence-prepare
```

Use the generated bundle to create one schema 1.2 SAGE package. The result
must be at least as complete as the canonical request in
`markdown/templates/sage-evidence-generation-request.md` and must pass:

```bash
SAGE_PACKAGE=~/Downloads/<package>.zip make sage-evidence-check
```

Do not ask the requester to restate schema, template, metadata, evidence,
navigation, checksum, or publication requirements.

## Actionable SAGE failures

SAGE guardrails follow
`markdown/standards/kalaxy3-sage-actionable-failure-contract.md`.

A failure must be self-contained for an operator who knows only the action
they attempted. It must explain the detected state, why the action is
invalid, the inferred goal, how to confirm the authoritative approach,
the exact recovery command, allowed and prohibited actions, and the SAGE
integrity requirements that remain mandatory.

Validate this contract with:

```bash
make sage-actionable-failure-self-test
```

## Capability-intelligence guardrail

Changes affecting mission outcomes, capabilities, target architecture,
authority ownership, alternative decisions, estimates, or rebuild-forward
continuity must run the repository-owned capability-intelligence guardrail.

Preserve source assertions, SAGE inference, predictions, authority decisions,
and observed outcomes as distinct records. Never silently override a scoped
authority. Never replace unknowns with fabricated scores. Predictions remain
scalar-neutral and immutable before outcomes.

```console
make sage-capability-intelligence-guardrail
```

## Operator execution delivery contract

For Kalaxy3 operator workflows, multi-step or mutating execution guidance MUST
be delivered as a downloadable executable helper file by default.

Every delivered helper MUST include:

- a repository-aware fail-closed preflight;
- exercised validation for the helper's actual runtime path;
- a SHA-256 checksum;
- one short invocation.

Do not provide multi-command console blocks unless the operator explicitly
requests console commands. Small read-only inspection commands are permitted
only when they are materially safer or clearer than generating a helper.

Returning to multi-command console guidance after this lesson is surfaced is a
known recurrence, not an isolated formatting mistake. The workflow must stop,
record the recurrence, and restore file-based delivery before continuing.

## Canonical workflow-support contract

Improvement-action identifiers MUST be allocated through
`scripts/sage/sage-action-id.py`. Workflow wrappers must not implement local
identifier allocation.

Python workflow delivery MUST pass the repository-owned undefined-global
guardrail. Syntax compilation and source-token checks are not runtime
validation.

A primitive root cause must be fixed in the primitive with a regression test;
wrapper-only root-cause patches are prohibited.

## Reusable workflow composition contract

New Kalaxy3 operator workflows MUST be thin compositions under
`scripts/sage/workflows/` using versioned primitives from
`scripts/sage/workflow/`.

Do not recreate command execution, Git synchronization, changed-path checks,
SAGE discovery, action lifecycle, Makefile composition, validation, structured
logging, usage aggregation, or closeout logic in workflow wrappers.

Tracked compositions declare `PRIMITIVES_USED`, may not import `subprocess`,
and must pass `make sage-workflow-self-test` and
`make sage-workflow-guardrail`.

A primitive defect is corrected in the primitive with a version increment and
regression test. Wrapper-only root-cause patches are prohibited.
