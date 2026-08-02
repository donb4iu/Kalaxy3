# Kalaxy3 SAGE change discovery

SAGE means **Systems Architecture & Governance through Evidence**.

A requester should be able to describe the desired outcome without knowing
Kalaxy3's internal governance structure. The repository is responsible for
discovering and presenting that structure before implementation begins.

## Start every change

From the repository root:

```bash
python3 scripts/sage/sage-change-preflight.py \
  --request "Add centralized logging"
```

The preflight reads `sage-change-authority.json` and reports:

- inferred SAGE contexts;
- authoritative repository files;
- required working directories;
- baseline checks that must pass before editing;
- validation required after editing;
- evidence and publication requirements.

For resumed or externally modified work:

```bash
python3 scripts/sage/sage-change-preflight.py --changed
```

## Fail-closed behavior

A request that does not match a specialized context is reported as
`UNCLASSIFIED`. Implementation must stop until the authority map is
extended.

The discovery path itself is protected by:

```bash
python3 scripts/sage/sage-change-discovery-guardrail.py
```

## Staged implementation policy

Implementation may be committed and reviewed before activation. Such work
is a **staged implementation**. Activation or deployment occurs only after
every discovered guardrail and validation step passes.

## Evidence

All implementation and validation evidence follows:

- `markdown/standards/kalaxy3-sage-evidence-record-standard.md`
- `markdown/standards/kalaxy3-sage-evidence-publication-process.md`
- `markdown/standards/sage-evidence-metadata-contract-v1.2.json`
- `markdown/templates/sage-evidence-record-template.md`
- `scripts/sage/sage-publish.py`
- `scripts/sage/sage-index.py`

## Repository command entry points

The normal entry point is:

```bash
SAGE_REQUEST="Add centralized logging" make sage-preflight
```

Validate the complete repository-owned discovery path with:

```bash
make sage-guardrails
```

The homelab source guardrails depend on the discovery guardrail, and pull
requests run the repository SAGE guardrails before publication jobs are
eligible to run.

## Automatic evidence generation

Ordinary requester language automatically receives the canonical SAGE
evidence contract.

Prepare a checksummed generator-input bundle:

```bash
SAGE_REQUEST="Document what we just did." make sage-evidence-prepare
```

Print the same generation brief without creating a ZIP:

```bash
SAGE_REQUEST="Document what we just did." make sage-evidence-brief
```

Validate the final generated package:

```bash
SAGE_PACKAGE=~/Downloads/<package>.zip make sage-evidence-check
```

The requester need not know the SAGE standard, schema, template, metadata,
navigation, artifact, checksum, or publication commands.

## Actionable failure recovery

The authoritative failure-response contract is
`markdown/standards/kalaxy3-sage-actionable-failure-contract.md`.

Guardrails fail closed and provide a repository-owned recovery path. When
the correct path cannot be determined, SAGE identifies the uncertainty,
directs the operator to repository discovery, preserves the failure as
evidence, and reports a systemic capability gap instead of suggesting an
undocumented workaround.

## Capability intelligence and federated decisions

SAGE renders the versioned Kalaxy3 mission, preferred target, current
multidimensional capability state, WAR and CAF lenses, federated authority
assertions, conflicts, alternative branches, immutable predictions, selected
decisions, actual outcomes, and learning.

SAGE is a decision partner rather than the sole authority. Unknown and immature
dimensions remain visible and reduce certainty without becoming false success
or failure. Rebuild-forward assurance preserves required capability outcomes
while allowing a better successor implementation.

```console
make sage-capability-intelligence-render
make sage-capability-intelligence-check
make sage-capability-intelligence-self-test
make sage-capability-intelligence-guardrail
```

## Canonical workflow support

The workflow-support layer owns improvement-action identifier allocation and
Python runtime-name validation.

- ID allocation uses exact first-free set membership.
- Local allocator implementations are prohibited.
- Undefined global references fail closed before delivery.
- Exact registration paths are exercised through the canonical action tool.
- Failures update shared primitives and regression tests.

## Workflow primitives and composition

The repository-owned workflow framework turns repeated operational patterns
into versioned engineering experience.

- `sage-workflow-primitives.json` is the primitive and policy registry.
- `scripts/sage/workflow/` contains reusable typed primitives.
- `scripts/sage/workflows/` contains thin capability compositions.
- `make sage-workflow-self-test` exercises runtime paths.
- `make sage-workflow-guardrail` blocks duplicated workflow machinery.
- `make sage-workflow-usage` summarizes observed events by primitive version.

Primitive maturity is based on measured successful executions and recurrence,
not code age or resemblance to prior helpers.

## Mandatory operating-contract enforcement

The complete repository-content and operator-verification sequence is defined
by `scripts/sage/workflows/operating_contract.py`. It is deliberately split at
the Git or GitHub mutation boundary: helpers prepare and validate one proposal,
the operator executes it, and a second read-only phase verifies pasted output
before outcomes and evidence are recorded.

```bash
make sage-operating-contract-check
```

This target runs the runtime composition self-test and the root guardrail. Both
are included in the normal repository SAGE chains. Root enforcement does not
authorize autonomous Git, GitHub, credential, ref, cluster, or deployment
mutation. Final evidence uses split publication after the implementation commit
is known.
