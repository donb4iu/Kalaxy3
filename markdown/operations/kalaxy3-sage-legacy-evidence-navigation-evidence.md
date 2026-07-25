---
evidence_id: SAGE-K3-GOVERNANCE-20260725-003
schema_version: "1.2"
title: Backward-Compatible SAGE Evidence Navigation and Legacy Reconciliation
nav_title: Preserve legacy evidence and generate navigation
nav_section: governance
nav_order: 30
summary: Adds strict navigation metadata for new SAGE records while preserving and indexing schema 1.0, schema 1.1, and pre-SAGE evidence without rewriting historical source files.
primary_subject: SAGE evidence catalog
project: Kalaxy3
record_type: operations
status: validated
classification: internal
work_session: SAGE legacy evidence compatibility and navigation
work_started_at: 2026-07-25T17:50:00-05:00
work_completed_at: 2026-07-25T18:25:00-05:00
evidence_collected_at: 2026-07-25T18:29:00-05:00
created_at: 2026-07-25T18:30:00-05:00
updated_at: 2026-07-25T18:36:43-05:00
valid_as_of: 2026-07-25
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - UTC
owner: Don Buddenbaum
author: ChatGPT
operator: ChatGPT
reviewer: pending
environment: development
system: Kalaxy3
cluster: not-applicable
execution_host: OpenAI-artifact-runtime
controller_host: not-applicable
nodes:
  - not-applicable
node_addresses:
  - not-applicable
namespaces:
  - not-applicable
endpoints:
  - not-applicable
components:
  - SAGE-publisher=1.2
  - SAGE-indexer=1.0
  - Python=version-not-captured
  - Git=version-not-captured
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: eaf461a17a7083b4b8f453c1aa89b6b833a815e3
record_path: markdown/operations/kalaxy3-sage-legacy-evidence-navigation-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003
confidence: high
tags:
  - sage
  - governance
  - navigation
  - legacy-evidence
  - reconciliation
  - dauxio
relationships:
  verifies:
    - SAGE schema 1.2 navigation contract
    - backward-compatible historical evidence indexing
    - deterministic evidence catalog publication
  depends_on:
    - SAGE-K3-GOVERNANCE-20260725-001
    - SAGE-K3-GOVERNANCE-20260725-002
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/standards/kalaxy3-sage-evidence-publication-process.md
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-publish.py
    - scripts/sage/sage-index.py
    - ChatGPT artifact generation
  implemented_by:
    - eaf461a17a7083b4b8f453c1aa89b6b833a815e3
  revalidated_by:
    - none
---

# Backward-Compatible SAGE Evidence Navigation and Legacy Reconciliation

## Executive summary

Kalaxy3 SAGE schema 1.2 now separates formal evidence titles from concise navigation labels, requires page-level table-of-contents support, and generates section, subject, status, current, legacy, and migration views during publication. The repository indexer preserves older SAGE and pre-SAGE Markdown without rewriting it, assigns deterministic legacy IDs, records metadata provenance, and exposes all discovered evidence through Markdown, JSON, and CSV catalogs. An isolated split-publication test successfully published a schema 1.2 record alongside a pre-SAGE static-header record, pushed both commits to a temporary remote, verified catalog freshness, and left the working tree clean.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GOVERNANCE-20260725-003 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Backward-Compatible SAGE Evidence Navigation and Legacy Reconciliation |
| **Navigation title** | Preserve legacy evidence and generate navigation |
| **Navigation section** | governance |
| **Navigation order** | 30 |
| **Summary** | Adds strict navigation metadata for new SAGE records while preserving and indexing schema 1.0, schema 1.1, and pre-SAGE evidence without rewriting historical source files. |
| **Primary subject** | SAGE evidence catalog |
| **Record type** | operations |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | SAGE legacy evidence compatibility and navigation |
| **Started** | 2026-07-25T17:50:00-05:00 |
| **Completed** | 2026-07-25T18:25:00-05:00 |
| **Evidence collected** | 2026-07-25T18:29:00-05:00 |
| **Record created** | 2026-07-25T18:30:00-05:00 |
| **Record updated** | 2026-07-25T18:36:43-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | UTC |
| **Valid as of** | 2026-07-25 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-sage-legacy-evidence-navigation-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | eaf461a17a7083b4b8f453c1aa89b6b833a815e3 |
| **Environment** | development |
| **System** | Kalaxy3 |
| **Cluster** | not-applicable |
| **Execution host** | OpenAI-artifact-runtime |
| **Controller host** | not-applicable |
| **Nodes** | not-applicable |
| **Node addresses** | not-applicable |
| **Namespaces** | not-applicable |
| **Endpoints** | not-applicable |
| **Components and versions** | SAGE-publisher=1.2; SAGE-indexer=1.0; Python=version-not-captured; Git=version-not-captured |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT |
| **Operator** | ChatGPT |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author ChatGPT and operator ChatGPT implemented and tested the process for owner Don Buddenbaum; reviewer pending remains the governance state. |
| **What** | The session added schema 1.2 navigation metadata, a page TOC requirement, a backward-compatible evidence indexer, a curated legacy registry, deterministic legacy IDs, generated human and machine catalogs, and automatic catalog reconciliation in the SAGE publisher. |
| **When** | Completed 2026-07-25T18:25:00-05:00; evidence collected 2026-07-25T18:29:00-05:00; local timezone America/Chicago; system timestamps UTC; valid as of 2026-07-25; review due event-based. |
| **Where** | Environment development; cluster not-applicable; execution host OpenAI-artifact-runtime; controller not-applicable; record markdown/operations/kalaxy3-sage-legacy-evidence-navigation-evidence.md. The implementation targets repository standards, templates, scripts, and markdown/evidence navigation paths. |
| **Why** | Existing evidence was technically strong but stove-piped, difficult to browse through filename-derived Daux.io navigation, and at risk of becoming invisible when stricter schemas were introduced. The accepted design preserves historical evidence while making all records discoverable to humans and machines. |
| **How** | The schema adds authoritative navigation fields; the indexer scans configured roots and SAGE IDs, applies curated or inferred discovery metadata, assigns stable legacy IDs, generates deterministic Markdown/JSON/CSV indexes, and is called automatically by the two-commit publisher. An isolated Git remote verifies publication, push, legacy preservation, catalog freshness, and clean state. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Schema 1.2 formal and navigation metadata.
- Explicit `[TOC]` requirement for current records.
- Legacy SAGE and pre-SAGE discovery.
- Deterministic legacy IDs.
- Curated legacy registry and inferred metadata provenance.
- Generated current, legacy, migration, section, subject, status, JSON, and CSV views.
- Automatic reconciliation during SAGE publication.
- Safe stale generated-file removal.
- Isolated split publication and push testing.

### Out of scope

- Automatic semantic conversion of historical evidence into current SAGE records.
- Automatic invention of missing authors, dates, commits, reviewers, or validation results.
- Daux.io or MkDocs theme configuration.
- Manual curation of every existing legacy record in this implementation session.
- Independent reviewer acceptance.

### Nonclaims

This record does **not** claim:

- that inferred legacy metadata is authoritative;
- that every Markdown document is evidence;
- that all legacy records are ready for automatic migration;
- that documentation search alone is sufficient navigation;
- that historical source files should be rewritten to satisfy schema 1.2;
- that the generated catalog replaces the source record.

## Final accepted state

```text
Current record validation: strict schema 1.2
Historical record handling: preserve and index
Legacy source rewriting: prohibited
Page-level navigation: explicit [TOC]
Collection navigation: generated Markdown indexes
Machine discovery: catalog.json and catalog.csv
Legacy identity: deterministic LEGACY-K3 path hash
Metadata provenance: authoritative, curated, or inferred
Publisher reconciliation: automatic before evidence commit
Isolated publication test: pass
Temporary remote push: pass
Final test working tree: clean
Reviewer: pending
```

| Item | Accepted result |
|---|---|
| New SAGE records | Strict schema 1.2 metadata and navigation validation. |
| Schema 1.0 and 1.1 records | Preserved and indexed as `sage-legacy`. |
| Pre-SAGE records | Preserved and indexed as `legacy-evidence`. |
| Curated metadata | Stored outside historical source in the legacy registry. |
| Inferred metadata | Clearly labeled and included in the migration report. |
| Navigation | Generated by section, subject, status, class, and recency. |
| Publication | Catalog changes committed with evidence, not implementation. |
| Migration | Deliberate, reviewed, and non-destructive. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Schema 1.2 enforces canonical navigation metadata and an explicit page TOC for new records. | critical | `EV-001`, `EV-002` | supported | high |
| `CLM-002` | The indexer preserves and catalogs both current SAGE and pre-SAGE evidence without rewriting historical source files. | critical | `EV-001`, `EV-002` | supported | high |
| `CLM-003` | The publisher automatically reconciles generated navigation before creating the evidence commit. | critical | `EV-001`, `EV-002` | supported | high |
| `CLM-004` | The isolated end-to-end test created implementation and evidence commits, pushed them, verified catalog freshness, and ended clean. | critical | `EV-001` | supported | high |
| `CLM-005` | The implementation files are captured with independent SHA-256 values. | high | `EV-003` | supported | high |

## Problem and decision rationale

### Problem or opportunity

Kalaxy3 evidence records were independently readable but collection-level discovery depended on directory names, filenames, and search. Long formal titles were cryptic in sidebar navigation, mandatory section anchors were not explicitly connected to renderer behavior, and a stricter schema risked excluding valuable historical evidence.

### Decision

Add strict navigation metadata to new records and a separate reconciliation layer that catalogs all historical evidence without modifying it.

### Decision drivers

- Human discoverability through Daux.io now and MkDocs later.
- Stable machine discovery for LLM and automation use.
- Preservation of every existing evidence document.
- Clear distinction between authoritative and inferred metadata.
- Deterministic output and publication behavior.
- No automatic fabrication during migration.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Depend only on full-text search | No additional metadata | No guided reading order, weak current/superseded discovery, opaque legacy coverage | rejected |
| Put a manual global TOC in every record | Human-visible | Duplicated global state drifts immediately | rejected |
| Wait for MkDocs migration | Avoid interim work | Renderer change does not infer semantics or preserve legacy relationships | rejected |
| Rewrite all historical records automatically | Uniform appearance | Invents facts, destroys provenance, and creates false compliance | rejected |
| Strict current schema plus generated backward-compatible catalog | Preserves history and improves navigation | Requires registry curation and generated outputs | accepted |

### Tradeoffs and consequences

- The catalog may initially contain imperfect inferred titles or summaries.
- Candidate roots may need registry additions for evidence stored elsewhere.
- Generated files add repository churn when evidence changes, but the changes are deterministic and reviewable.
- Legacy warnings do not block unrelated current publication; duplicate IDs and unsafe paths still block.

## Architecture or change description

```text
schema 1.2 SAGE records ------------------+
                                          |
schema 1.0/1.1 SAGE records --------------+--> sage-index.py
                                          |      - classify
pre-SAGE Markdown in candidate roots ------+      - curate/infer
                                          |      - assign legacy IDs
legacy-record-registry.json ---------------+      - validate duplicates
                                                 - generate indexes
                                                        |
                                                        v
markdown/evidence/
  index.md current.md legacy.md migration-report.md
  catalog.json catalog.csv
  sections/ subjects/ status/
                                                        |
                                                        v
sage-publish.py stages generated navigation
with the evidence commit and pushes safely
```

### Before

- Current records had formal titles but no separate navigation title contract.
- Page-level TOC behavior was not mandatory.
- Historical evidence had no unified catalog or metadata provenance.
- Publication did not reconcile collection-level navigation.

### After

- Current records have strict formal and navigation metadata.
- `[TOC]` is mandatory.
- Historical evidence is classified and indexed without rewriting.
- The publisher reconciles and commits generated navigation automatically.

## Source of truth and implementation lineage

### Repository files

```text
markdown/evidence/legacy-record-registry.json
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/templates/sage-evidence-generation-request.md
markdown/templates/sage-evidence-package-manifest-template.json
markdown/templates/sage-evidence-record-template.md
scripts/sage/README.md
scripts/sage/sage-index.py
scripts/sage/sage-publish.py
```

### Implementation commit

```text
eaf461a17a7083b4b8f453c1aa89b6b833a815e3
Enforce SAGE navigation and preserve legacy evidence
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE publisher | 1.2 | repository source |
| SAGE indexer | 1.0 | repository source |
| Python | version-not-captured | execution environment |
| Git | version-not-captured | execution environment |

### Configuration excerpt

```json
{
  "registry_version": "1.0",
  "candidate_roots": [
    "markdown/installation",
    "markdown/operations",
    "markdown/architecture",
    "markdown/decisions"
  ],
  "exclude_paths": [],
  "records": []
}
```

## Prerequisites and assumptions

### Proven prerequisites

- Python standard library includes JSON, CSV, hashing, ZIP, and subprocess support.
- Git supports isolated repositories, bare remotes, commit, rebase checks, and push.
- The repository contains the SAGE standard, template, publisher, indexer, and registry.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Existing evidence is primarily under configured candidate roots or has a SAGE ID. | Some evidence may not appear until registered. | Review migration report and add curated registry entries or roots. |
| `ASM-002` | `[TOC]` is supported or harmless in the chosen renderer. | A renderer may display the marker literally. | Validate Daux.io and MkDocs builds; adapt renderer configuration without removing canonical headings. |
| `ASM-003` | Path-derived legacy IDs remain stable while files remain at the same paths. | Renaming a legacy file changes its inferred ID. | Curate an explicit registry ID before intentional renames. |

## Implementation procedure

1. Add navigation fields to schema 1.2 and its exact metadata table.
2. Require `[TOC]` in current records.
3. Add the legacy registry.
4. Implement candidate discovery and SAGE-ID discovery.
5. Classify current, legacy SAGE, and pre-SAGE records.
6. Generate deterministic IDs and navigation metadata.
7. Generate all Markdown, JSON, and CSV outputs.
8. Integrate reconciliation into evidence publication.
9. Add publication-manifest hashes for the indexer and registry.
10. Extend the isolated self-test with a static-header legacy fixture.
11. Require both current and legacy classes in the test catalog.
12. Run catalog freshness verification after publication.

## Evidence items

### `EV-001` — Isolated publication and legacy reconciliation test

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003`, `CLM-004` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T18:29:00-05:00 |
| Execution source | OpenAI-artifact-runtime |
| Target | temporary Git repository and bare remote |
| Tool and version | SAGE-publisher=1.2; SAGE-indexer=1.0 |
| Expected result | Two commits, successful push, current and legacy catalog classes, fresh generated files, clean tree |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/self-test-output.txt`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/upgrade-publication-test-output.txt` |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-publish.py self-test
```

**Observed result**

```text
Publication completed with a clean working tree.
SAGE publication and legacy reconciliation self-test: PASS
Upgrade test catalog classes: sage-current, sage-legacy, legacy-evidence
Upgrade test catalog freshness: PASS
Upgrade test working tree: clean
```

**Interpretation**

The complete tested path published a strict current record and preserved a pre-SAGE static-header record in the generated catalog.

### `EV-002` — Repository contract and implementation review

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T18:29:00-05:00 |
| Execution source | OpenAI-artifact-runtime |
| Target | SAGE standards, templates, publisher, indexer, and registry |
| Tool and version | Python=version-not-captured |
| Expected result | Schema, template, indexer, publisher, and process implement the same compatibility contract |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline repository paths and package payload |

**Command, query, source, or observation**

```bash
python3 -m py_compile scripts/sage/sage-publish.py scripts/sage/sage-index.py
python3 scripts/sage/sage-publish.py self-test
```

**Observed result**

```text
Compilation succeeded.
Self-test passed.
```

**Interpretation**

The code and governing documents implement the same strict-current and preserve-legacy model.

### `EV-003` — Implementation file checksums

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-005` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T18:29:00-05:00 |
| Execution source | OpenAI-artifact-runtime |
| Target | ten implementation files |
| Tool and version | SHA-256=standard-library-and-shasum |
| Expected result | One digest for every declared implementation file |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/implementation-file-checksums.sha256` |

**Command, query, source, or observation**

```bash
shasum -a 256 <each implementation file>
```

**Observed result**

```text
Ten implementation paths have SHA-256 values.
```

**Interpretation**

The artifact supports package and source integrity review.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Current records require navigation metadata | `EV-002` | strict fields and table rows | implemented | pass |
| `AC-002` | Current records require page TOC | `EV-002` | missing marker rejected | implemented | pass |
| `AC-003` | Pre-SAGE evidence remains cataloged | `EV-001` | legacy class present | observed | pass |
| `AC-004` | Historical source is not rewritten | `EV-001`, `EV-002` | index generation only | observed | pass |
| `AC-005` | Publisher reconciles catalog | `EV-001`, `EV-002` | generated files in evidence commit | observed | pass |
| `AC-006` | Catalog is fresh after publication | `EV-001` | index check passes | observed | pass |
| `AC-007` | Publication pushes safely | `EV-001` | push succeeds without force | observed | pass |
| `AC-008` | Final test tree is clean | `EV-001` | no working-tree changes | observed | pass |

## Idempotency and repeatability

The self-test creates a fresh temporary repository and remote on every run. The generated catalog is deterministic from source records and registry values. After publication, `sage-index.py check` regenerates expected content in memory and reports no stale paths. Reconciliation only rewrites generated files when content differs and only removes paths declared by the prior generated-files manifest.

## Security, privacy, and evidence handling

- Historical source is read-only during reconciliation.
- ZIP path and checksum protections remain enforced.
- Secret scanning remains active for current records and artifacts.
- Generated catalog exposes internal paths, titles, nodes, and summaries and should remain under repository classification controls.
- No credentials or secret values are included in this package.
- Curated metadata is separate from historical evidence to avoid false provenance.

## Reliability, recovery, rollback, and rebuild

### Rollback

Revert the implementation commit and evidence commit. Generated catalog files can be restored by rerunning the previous publisher or checking out the previous evidence commit.

### Rebuild

```bash
python3 scripts/sage/sage-index.py reconcile
python3 scripts/sage/sage-index.py check
```

### Failure behavior

- Duplicate IDs stop reconciliation.
- Duplicate current navigation titles within a section stop reconciliation.
- Missing legacy metadata produces warnings, not deletion.
- Unsafe paths stop reconciliation.
- Stale catalogs fail the check command.
- Only previously declared generated paths are eligible for stale removal.

## Operational considerations and observability

Operators should review:

```text
markdown/evidence/index.md
markdown/evidence/legacy.md
markdown/evidence/migration-report.md
markdown/evidence/catalog.json
```

Routine checks:

```bash
python3 scripts/sage/sage-index.py check
python3 scripts/sage/sage-publish.py self-test
```

The migration report is the curation work queue. Inferred records should be curated when their title, summary, date, owner, or primary subject is materially unclear.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence gap | Python and Git versions were not captured. | Exact tool reproduction is incomplete. | Don Buddenbaum | next process revalidation |
| `GAP-002` | discovery limitation | Evidence outside configured roots without a SAGE ID requires a registry entry. | A record could remain undiscovered. | Don Buddenbaum | migration report review |
| `GAP-003` | metadata limitation | Inferred titles and summaries may be imperfect. | Human navigation may need curation. | Don Buddenbaum | legacy review |
| `GAP-004` | renderer risk | `[TOC]` behavior depends on documentation configuration. | Marker may render differently. | Documentation owner | Daux.io or MkDocs build |
| `GAP-005` | identity risk | Moving an uncurated legacy file changes its path-derived ID. | Relationships may break. | Documentation owner | before legacy rename |
| `GAP-006` | governance gap | Reviewer remains pending. | Record is validated, not accepted. | Kalaxy3 architecture | review event |

## Troubleshooting

### A record is missing from the catalog

Add its directory to `candidate_roots` or add an explicit registry record. Do not move or rewrite the source merely to make it discoverable.

### A legacy title is poor

Add a curated `nav_title`, `summary`, `primary_subject`, and `nav_section` in the registry. The source file remains unchanged.

### A catalog check reports stale files

```bash
python3 scripts/sage/sage-index.py reconcile
python3 scripts/sage/sage-index.py check
```

Review the generated diff before committing.

### A legacy ID would change before a rename

Add an explicit registry `evidence_id` using the existing deterministic ID, commit the registry, then rename and update `source_path` deliberately.

### Publication fails on a legacy warning

Warnings alone do not fail publication. Check for a duplicate ID, unsafe path, malformed registry, or current schema error.

## Freshness, revalidation, and supersession

Revalidate when:

- SAGE record, package, catalog, or registry schema changes;
- publisher or indexer behavior changes;
- Daux.io is replaced or materially reconfigured;
- MkDocs navigation is introduced;
- candidate evidence roots change;
- a legacy record is renamed or migrated;
- duplicate or missing records are reported;
- generated catalog check fails;
- security scanning or Git publication behavior changes.

A superseding record must preserve this evidence ID, link the new record, state which compatibility guarantees remain valid, and preserve the historical migration report.

## Final completion checklist

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Navigation title, section, order, summary, and primary subject are present.
- [x] Record metadata exactly mirrors front matter.
- [x] An explicit page TOC is present.
- [x] Status accurately reflects technical validation and pending review.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope, exclusions, and nonclaims are explicit.
- [x] Implementation commit token is present for publication.
- [x] Claims map to evidence items.
- [x] Expected and observed results are separated.
- [x] Current and legacy records were both tested.
- [x] Historical source preservation is explicit.
- [x] Metadata provenance is explicit.
- [x] Idempotency and catalog freshness are tested.
- [x] Security and secret handling are documented.
- [x] Rollback, rebuild, operations, and troubleshooting are documented.
- [x] Limitations and migration risks are recorded.
- [x] Revalidation criteria are defined.

## Git review and publication

Normal publication uses:

```bash
python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-sage-legacy-navigation-evidence.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-sage-legacy-navigation-evidence.zip \
  --push
```

Expected commits:

```text
Enforce SAGE navigation and preserve legacy evidence
Add SAGE evidence for legacy navigation
```

The evidence commit also contains generated catalog changes from the actual Kalaxy3 repository.

## Appendices and raw artifacts

| Artifact | Path | Purpose |
|---|---|---|
| Self-test output | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/self-test-output.txt` | Proves isolated publication, push, compatibility catalog, freshness check, and clean tree. |
| Upgrade publication test | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/upgrade-publication-test-output.txt` | Proves schema 1.1, pre-SAGE, and schema 1.2 records coexist in one fresh catalog after two-commit publication. |
| Implementation checksums | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-003/implementation-file-checksums.sha256` | Supports integrity review of the implementation files. |
| Publication manifest | Generated at publication | Captures resolved implementation SHA and governing-file hashes. |
