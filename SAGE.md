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
