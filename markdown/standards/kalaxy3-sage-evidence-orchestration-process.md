# Kalaxy3 SAGE Evidence Orchestration Process

## Purpose

This process makes canonical SAGE evidence generation the default result of
Kalaxy3 work rather than a special response that depends on the requester
knowing a particular prompt.

The requester is not required to mention SAGE, schema 1.2, metadata fields,
templates, checksums, publication mechanics, or evidence-navigation rules.

## Required behavior

When evidence is requested, or when completed work is being preserved, the
implementer or evidence generator MUST:

1. preserve the original requester language verbatim;
2. run repository-owned SAGE discovery;
3. load the canonical evidence-generation request automatically;
4. load the standard, metadata contract, record template, manifest template,
   publication process, publisher, and indexer;
5. collect available repository and terminal evidence;
6. identify missing runtime observations as evidence gaps;
7. generate a schema 1.2 package at least as complete as the canonical
   working-session evidence request;
8. validate the package through `scripts/sage/sage-publish.py check`;
9. return only the package and standard check and publication commands.

## Repository entry points

Prepare a self-contained generation-input bundle:

```bash
SAGE_REQUEST="<request exactly as received>" make sage-evidence-prepare
```

Print the generation brief without creating a bundle:

```bash
SAGE_REQUEST="<request exactly as received>" make sage-evidence-brief
```

Validate a generated evidence package:

```bash
SAGE_PACKAGE=~/Downloads/<package>.zip make sage-evidence-check
```

## Quality floor

The machine-readable quality floor is:

```text
sage-evidence-policy.json
```

The policy is additive to the evidence standard and publication process. It
cannot weaken either authority.

A generated package is not complete merely because it contains Markdown. It
must preserve failed paths, rationale, alternatives, direct observations,
repository evidence, limitations, rollback, rebuild, security, operations,
idempotency or an explicit gap, freshness, and revalidation rules.

## Evidence-generation input bundle

The orchestration bundle is not the final SAGE package. It is a
self-contained, checksummed input for an evidence generator and contains:

- the original requester language;
- the canonical generation request;
- inferred SAGE contexts;
- repository status, diffs, changed paths, and lineage;
- checksummed authoritative files;
- optional redaction-checked terminal evidence;
- explicit evidence gaps;
- the final output and validation contract.

The final generated package must still pass the repository publisher.

## Fail-closed rules

Evidence orchestration MUST fail when:

- the canonical request checksum changes without a policy update;
- a required authority file is missing;
- the quality floor is weakened;
- request text cannot be preserved literally;
- supplied terminal evidence contains potential secret material;
- an input bundle is directed into the repository working tree;
- the resulting SAGE package fails publisher validation.

## Plain-language acceptance cases

The following requests must receive the same canonical evidence context
without requiring the requester to restate SAGE rules:

- “Document what we just did.”
- “Create the evidence for this work.”
- “Finish this change and preserve the evidence.”
- “Repair centralized logging.”
- “Add Loki and Fluent Bit.”

## Publication boundary

Preparation and validation do not authorize publication. Publication remains
controlled by `scripts/sage/sage-publish.py` and the requester’s explicit
approval.
