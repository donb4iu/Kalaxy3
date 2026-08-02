---
title: Kalaxy3 MkDocs Evidence Navigation Process
project: Kalaxy3
record_type: governance-standard
schema_version: "1.0"
status: proposed
created_at: 2026-08-02T12:33:00-05:00
updated_at: 2026-08-02T12:33:00-05:00
valid_as_of: 2026-08-02
owner: Kalaxy3 architecture
navigation_policy: mkdocs-navigation-policy.json
template_policy: sage-evidence-template-policy.json
workflow_composition: scripts/sage/workflows/evidence_navigation.py
---

# Kalaxy3 MkDocs Evidence Navigation Process

## Purpose

The documentation site MUST remain navigable as the SAGE evidence catalog
expands. Formal evidence titles, generated indexes, historical compatibility,
and primary-site navigation have different responsibilities and MUST NOT be
flattened into one inferred sidebar.

## Versioned policies

`mkdocs-navigation-policy.json` is the authority for primary navigation. It
defines the landing page, top-level exclusions, label limits, curated Evidence
pages, catalog-record exclusion, and Material navigation classes.

`sage-evidence-template-policy.json` is the authority for current-template
compatibility. It identifies the metadata contract, template, catalog,
publisher, current class, immutable historical classes, and compatible heading
sequence.

Policy changes are repository changes and require rendered-site validation and
SAGE evidence. Python constants MUST NOT duplicate policy values.

## Shared libraries

The implementation uses reusable support modules:

- `scripts/sage/workflow/markdown.py` parses Markdown front matter, headings,
  metadata labels, and safe repository paths.
- `scripts/sage/workflow/evidence_records.py` loads the evidence catalog,
  metadata contract, template policy, template, and publication authorities.
- `scripts/docs/navigation_support.py` builds navigation and parses rendered
  Material navigation from the same policy.

Command-line scripts MUST remain thin adapters over these modules. They MUST
NOT reimplement catalog loading, Markdown parsing, URL mapping, policy values,
or rendered-navigation parsing.

## Generated navigation

`scripts/docs/generate-mkdocs-navigation.py` generates
`.mkdocs-work/mkdocs.generated.yml` and
`.mkdocs-work/navigation-manifest.json` after source preparation.

Cataloged evidence records remain published and searchable but are excluded
from primary navigation. Humans reach them through seven curated Evidence
pages: overview, current, historical, migration report, section, status, and
subject.

## Validation

`scripts/docs/validate-mkdocs-navigation.py` validates the rendered Material
site, not just configuration source. It verifies primary-link count, label
length, curated Evidence entries, catalog-record exclusion, artifact
publication, record HTML generation, and index reachability.

`scripts/sage/sage-evidence-template-guardrail.py` verifies that the JSON
contract, current template, publisher, and catalog share one authority model.
Previously published compatible records remain immutable.

`scripts/sage/sage-evidence-navigation-architecture-guardrail.py` audits the
implementation against policy-driven configuration, shared parsing, thin CLIs,
registered primitive composition, exact new-template enforcement, immutable
history, and absence of domain-level Git mutation.

## Workflow composition

`scripts/sage/workflows/evidence_navigation.py` declares the reusable SAGE
composition. It uses registered discovery, read-only Git inspection, atomic
file transactions, validation plans, failure diagnosis, operator Git
proposals, closeout evidence, and workflow lifecycle events.

Downloaded transport helpers are temporary. They MUST compose repository-owned
primitives and MUST NOT become the authoritative implementation.

## Source-path namespaces

Evidence paths cross two valid namespaces during publication:

- Repository catalogs use paths rooted at `markdown/`.
- Staged MkDocs manifests use paths relative to the staged source root.

The shared navigation library normalizes both forms before URL generation. It
rejects absolute paths, parent traversal, backslashes, empty paths, and
non-Markdown suffixes. Generators and validators must use this shared mapping
rather than implementing namespace conversion independently.

## Section-index contract

The Evidence landing page is a Material section index, not an ordinary child
label. The policy declares it separately as `index_page`. The generated
navigation places that path first under the `Evidence` section, allowing
Material to render the section itself as the clickable landing link.

The validator compares exact URL-and-label pairs:

- `evidence/` must render as `Evidence`.
- Each curated child must render with its policy label and generated URL.

This avoids treating a section index as a child named `Overview` and keeps the
generator, renderer, and validator on one shared contract.

## Executable runtime validation contract

`SAGE-LESSON-20260801-001` applies to this workflow. Compilation and isolated
helper tests do not establish that a changed guardrail works. Before delivery,
every changed Python command MUST execute its normal repository entry point
against the complete authority set needed by that command.

For the evidence-navigation architecture guardrail, `--self-test` MUST invoke
the same `audit(repo)` function used by the no-argument command. The full
`make sage-evidence-guardrail` chain and the staged MkDocs publication test MUST
also pass before the implementation can be described as validated.

A validation report containing `operator_repository_path: not-run-here`,
`normal_entry_point: not-executed`, or an equivalent unresolved state MUST NOT
support a success, safety, readiness, or delivery claim. After a repeated
same-class runtime failure, another delivery is prohibited until the existing
lesson is retrieved and an executable regression control covers the failure.
