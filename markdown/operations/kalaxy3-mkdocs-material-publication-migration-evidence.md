---
evidence_id: SAGE-K3-DOCS-20260729-001
schema_version: "1.2"
title: Kalaxy3 Daux-to-MkDocs Material Documentation Publication Migration Evidence
nav_title: Migrate documentation publication to MkDocs Material
nav_section: operations
nav_order: 670
summary: Documents the staged replacement of Daux with MkDocs Material, strict build and navigation validation, GitHub Pages publication, rollback, and remaining review gaps.
primary_subject: Kalaxy3 documentation publication
project: Kalaxy3
record_type: change
status: validated
classification: internal
work_session: Kalaxy3 Daux-to-MkDocs Material publication migration
work_started_at: 2026-07-29T17:19:32-05:00
work_completed_at: 2026-07-29T18:50:25-05:00
evidence_collected_at: 2026-07-29T19:52:15-05:00
created_at: 2026-07-29T19:53:00-05:00
updated_at: 2026-07-29T20:01:35-05:00
valid_as_of: 2026-07-29
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Kalaxy3 architecture
author: OpenAI GPT-5.6 Thinking
operator: Don Buddenbaum
reviewer: pending
environment: shared-platform
system: Kalaxy3
cluster: not-applicable
execution_host: donb-mac-mini
controller_host: donb-mac-mini
nodes:
  - not-applicable
node_addresses:
  - not-applicable
namespaces:
  - not-applicable
endpoints:
  - github-pages=https://donb4iu.github.io/docs/Kalaxy3/
  - evidence-catalog=https://donb4iu.github.io/docs/Kalaxy3/evidence/
  - search-index=https://donb4iu.github.io/docs/Kalaxy3/search/search_index.json
components:
  - mkdocs=1.6.1
  - mkdocs-material=9.7.7
  - python=3.12
  - github-actions=version-not-captured
  - github-pages=version-not-captured
  - nginx-documentation-image=f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45
repository: donb4iu/Kalaxy3
branch: feature/mkdocs-material-evidence
implementation_commit: 68065a4f3a7b3bac00710ac9706025e513e140c5
record_path: markdown/operations/kalaxy3-mkdocs-material-publication-migration-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001
confidence: high
tags:
  - sage
  - documentation
  - mkdocs-material
  - github-pages
  - publication
  - migration
relationships:
  verifies:
    - Kalaxy3 documentation publication migration
  depends_on:
    - none
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - SAGE evidence orchestration governance
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-publish.py
  implemented_by:
    - 68065a4f3a7b3bac00710ac9706025e513e140c5
  revalidated_by:
    - none
---
# Kalaxy3 Daux-to-MkDocs Material Documentation Publication Migration Evidence

## Executive summary

The Kalaxy3 documentation publication path was migrated from Daux to a pinned MkDocs 1.6.1 and MkDocs Material 9.7.7 toolchain. The implementation was staged and validated before activation, the generated site was published through the repository workflow, representative GitHub Pages resources returned HTTP 200, and SAGE guardrails passed. This record is technically validated; independent reviewer acceptance remains pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-DOCS-20260729-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Kalaxy3 Daux-to-MkDocs Material Documentation Publication Migration Evidence |
| **Navigation title** | Migrate documentation publication to MkDocs Material |
| **Navigation section** | operations |
| **Navigation order** | 670 |
| **Summary** | Documents the staged replacement of Daux with MkDocs Material, strict build and navigation validation, GitHub Pages publication, rollback, and remaining review gaps. |
| **Primary subject** | Kalaxy3 documentation publication |
| **Record type** | change |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Kalaxy3 Daux-to-MkDocs Material publication migration |
| **Started** | 2026-07-29T17:19:32-05:00 |
| **Completed** | 2026-07-29T18:50:25-05:00 |
| **Evidence collected** | 2026-07-29T19:52:15-05:00 |
| **Record created** | 2026-07-29T19:53:00-05:00 |
| **Record updated** | 2026-07-29T20:01:35-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-07-29 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-mkdocs-material-publication-migration-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/mkdocs-material-evidence |
| **Implementation commit** | 68065a4f3a7b3bac00710ac9706025e513e140c5 |
| **Environment** | shared-platform |
| **System** | Kalaxy3 |
| **Cluster** | not-applicable |
| **Execution host** | donb-mac-mini |
| **Controller host** | donb-mac-mini |
| **Nodes** | not-applicable |
| **Node addresses** | not-applicable |
| **Namespaces** | not-applicable |
| **Endpoints** | github-pages=https://donb4iu.github.io/docs/Kalaxy3/; evidence-catalog=https://donb4iu.github.io/docs/Kalaxy3/evidence/; search-index=https://donb4iu.github.io/docs/Kalaxy3/search/search_index.json |
| **Components and versions** | mkdocs=1.6.1; mkdocs-material=9.7.7; python=3.12; github-actions=version-not-captured; github-pages=version-not-captured; nginx-documentation-image=f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45 |
| **Owner** | Kalaxy3 architecture |
| **Author** | OpenAI GPT-5.6 Thinking |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** OpenAI GPT-5.6 Thinking; **operator:** Don Buddenbaum; **owner:** Kalaxy3 architecture; **reviewer:** pending; **affected users and teams:** Kalaxy3 operators and documentation readers. |
| **What** | Replaced the Daux publication path with a pinned MkDocs Material build, validation, promotion, navigation, GitHub Pages, and nginx documentation-image workflow while preserving Markdown in Git and SAGE evidence artifacts. |
| **When** | **Completed:** 2026-07-29T18:50:25-05:00; **evidence collected:** 2026-07-29T19:52:15-05:00; **local timezone:** America/Chicago; **system timestamps:** America/Chicago; UTC; **valid as of:** 2026-07-29; **review due:** event-based. GitHub-generated commits recorded UTC timestamps while operator evidence used America/Chicago. |
| **Where** | **Environment:** shared-platform; **cluster:** not-applicable; **execution host:** donb-mac-mini; **controller:** donb-mac-mini; **nodes:** not-applicable; **addresses:** not-applicable; **namespaces:** not-applicable; **endpoints:** github-pages=https://donb4iu.github.io/docs/Kalaxy3/; evidence-catalog=https://donb4iu.github.io/docs/Kalaxy3/evidence/; search-index=https://donb4iu.github.io/docs/Kalaxy3/search/search_index.json; **record:** markdown/operations/kalaxy3-mkdocs-material-publication-migration-evidence.md. |
| **Why** | Replace an older documentation generator with a repository-controlled, pinned, reproducible publication toolchain that supports explicit navigation validation, searchable output, GitHub Pages publication, and preserved SAGE evidence. |
| **How** | Added pinned documentation dependencies and repository scripts, staged strict builds, added CI validation and deterministic promotion, activated MkDocs publication through pull request review, validated generated output and navigation, published through GitHub Actions, and retained rollback and rebuild procedures. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Pinned MkDocs and MkDocs Material dependencies.
- Repository-owned source preparation, build validation, promotion, publication validation, and navigation validation.
- Migration commit and workflow-generated publication lineage.
- Tracked `docs/` output, representative public endpoints, nginx documentation image version, rollback, rebuild, and SAGE controls.
- Concise evidence packaging that preserves unique claim-supporting results without publishing redundant raw transcripts.

### Out of scope

- Exhaustive browser testing of every generated page.
- Interactive search behavior beyond successful retrieval of the generated search index.
- Custom-domain routing and a running in-cluster nginx pod.
- Independent governance acceptance, which remains pending.
- Rewriting legacy evidence records or clearing existing curation notices.

### Nonclaims

This record does **not** claim that every public link, browser, device, custom-domain route, or deployed nginx instance was tested. It does not claim reviewer acceptance, and it does not treat the excluded oversized transcript as necessary proof.

## Final accepted state

```text
Markdown in Git
  -> repository source preparation
  -> pinned MkDocs Material strict build
  -> build and navigation validation
  -> deterministic docs/ promotion
  -> GitHub Actions publication
  -> GitHub Pages and nginx documentation image
```

| Item | Accepted result |
|---|---|
| Source Markdown | 116 Markdown files staged from repository sources |
| Staged source | 202 total staged files with 16 compatibility rewrites |
| Generated site | 115 HTML pages and 246 total files |
| Publication reproducibility | 244 non-sitemap files byte-identical; 2 sitemap files match after normalizing generated timestamps and gzip metadata |
| Navigation | 126 primary links, 77 published evidence-artifact files, and 0 evidence-artifact links in primary navigation |
| Legacy generator output | No Daux-generated output remained in tracked `docs/` |
| Public publication | Landing page, evidence catalog, and search index returned HTTP 200 |
| nginx image lineage | `APP_VERSION` references merge commit `f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45` |
| SAGE controls | Guardrails and index reconciliation passed |
| Governance review | Technical validation complete; reviewer acceptance pending |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The pinned MkDocs Material staging target completed and generated the recorded source and site inventories. | critical | `EV-001`, `EV-008` | supported | high |
| `CLM-002` | Tracked publication output matches a fresh strict build except for documented sitemap timestamp and gzip metadata volatility. | critical | `EV-002`, `EV-008` | supported | high |
| `CLM-003` | Primary navigation excludes evidence-artifact files while retaining their published files. | high | `EV-003`, `EV-008` | supported | high |
| `CLM-004` | The accepted tracked state contains MkDocs output, no Daux-generated output, and the nginx image references the migration merge commit. | high | `EV-004`, `EV-008` | supported | high |
| `CLM-005` | Representative public landing, evidence catalog, and search-index resources were reachable with HTTP 200. | high | `EV-005` | supported | high |
| `CLM-006` | Repository SAGE guardrails and evidence index reconciliation passed after the migration and evidence-governance follow-up. | high | `EV-006`, `EV-007` | supported | high |
| `CLM-007` | The migration was implemented as staged, reviewable commits before publication activation and workflow-generated output commits. | high | `EV-007`, `EV-008` | supported | high |
| `CLM-008` | The evidence package excludes redundant raw output while preserving its provenance and all unique decision-relevant results. | normal | `EV-009` | supported | high |

## Problem and decision rationale

### Problem or opportunity

Kalaxy3 needed a documentation publication path that remained Markdown-first and Git-authoritative while providing a modern renderer, deterministic staging, navigation validation, search output, and repeatable publication. The prior Daux-generated output did not provide the desired repository-owned migration and validation contract.

### Decision

Adopt pinned MkDocs 1.6.1 and MkDocs Material 9.7.7, keep Markdown in Git as the source of truth, stage and validate publication before activation, publish generated output through the existing repository workflow, and preserve SAGE artifacts without exposing them in primary navigation.

### Decision drivers

- Repository authority and controller portability.
- Pinned dependencies and repeatable builds.
- Explicit validation before activation.
- Searchable GitHub Pages output.
- Preservation of evidence artifacts without navigation clutter.
- Rollback through Git history and reproducible rebuild commands.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Retain Daux | No migration effort | Retains the older publication path and does not establish the new strict MkDocs validation contract | rejected |
| Publish MkDocs immediately | Faster activation | Skips staged review and increases publication risk | rejected |
| Build a custom documentation platform | Maximum control | High implementation and maintenance cost; duplicates mature tooling | rejected |
| MkDocs Material with staged validation | Pinned, repository-controlled, searchable, and reviewable | Requires compatibility rewrites and generated-output controls | accepted |

### Tradeoffs and consequences

- The generated `docs/` tree remains large and workflow-generated.
- Sitemap files contain expected volatile metadata and require semantic normalization during reproducibility checks.
- Future dependency upgrades require fresh validation.
- The migration improves operator rebuildability and documentation discoverability without replacing GitHub Pages.

## Architecture or change description

```text
Before:
Markdown sources -> Daux generation -> tracked docs/ -> publication

After:
Markdown sources
  -> scripts/docs/prepare-mkdocs-source.py
  -> pinned MkDocs Material strict build
  -> scripts/docs/validate-mkdocs-build.py
  -> scripts/docs/validate-mkdocs-navigation.py
  -> scripts/docs/promote-mkdocs-site.py
  -> scripts/docs/validate-mkdocs-publication.py
  -> tracked docs/
  -> GitHub Actions
  -> GitHub Pages and nginx documentation image
```

### Before

Daux was the publication generator, and the repository did not yet have the complete MkDocs staging, validation, promotion, and navigation workflow.

### After

MkDocs Material is the active publication renderer. The repository owns the dependency lock, source preparation, validation, promotion, workflow activation, generated output, navigation controls, and evidence lineage.

## Source of truth and implementation lineage

### Repository files

```text
mkdocs.yml
requirements-docs.txt
requirements-docs.lock.txt
Makefile
scripts/docs/prepare-mkdocs-source.py
scripts/docs/validate-mkdocs-build.py
scripts/docs/promote-mkdocs-site.py
scripts/docs/validate-mkdocs-publication.py
scripts/docs/validate-mkdocs-navigation.py
.github/workflows/kalaxy3_build_publish.yml
yaml/nginx-docs/k8s-doc-to-nginx/values.yaml
docs/
```

### Implementation commit

```text
68065a4f3a7b3bac00710ac9706025e513e140c5
Update values.yaml [skip ci]
```

The evidence-only package resolves the implementation commit to `68065a4f3a7b3bac00710ac9706025e513e140c5`, the fully published repository state containing the merge, generated documentation, and nginx values update.

### Migration lineage

| Commit | Subject | Role |
|---|---|---|
| `e189736f4bb50320ce86172573d67a3d31c7c869` | Stage MkDocs Material build tooling | Staged implementation |
| `74e33f43397d3b0a11ef6513a6341b972b4d509d` | Validate staged MkDocs build in CI | CI validation |
| `37932675820699086929dc28ae8d5edfa30dd0e3` | Add staged MkDocs publication promotion | Promotion and publication checks |
| `aaddd47ca5eed40b5f07231bf5693bae27c080cc` | Switch documentation publication to MkDocs Material | Activation |
| `b0f30233d8dadd914699487cd231875318b5c8cd` | Extend SAGE discovery for MkDocs changes | Discovery governance |
| `6f3d443619d218895393235bc578742cdf29f0f3` | Register MkDocs navigation validator authority | Authority registration |
| `48af6904a9f2632e85500af64e5b25eed2467c87` | Hide evidence artifacts from MkDocs navigation | Navigation guardrail |
| `f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45` | Merge pull request 2 | Reviewed integration |
| `bdf6d5df2c4c2b0adc4404565bfdf6529b888537` | Generate Kalaxy3 MkDocs Material documentation | Workflow-generated site |
| `68065a4f3a7b3bac00710ac9706025e513e140c5` | Update values.yaml | Published image lineage |

### Evidence-governance follow-up

| Commit | Subject | Outcome |
|---|---|---|
| `b7b4de511d1d7da8a5b87f780b52043e75f2410d` | Classify SAGE evidence orchestrator changes | Added a specialized changed-path context |
| `6014d04b839cd08c17a880eb168780b967b94535` | Allow GitHub Actions secret references in SAGE capture | Removed a false positive while retaining literal-credential detection |

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| MkDocs | 1.6.1 | `requirements-docs.txt` and `requirements-docs.lock.txt` |
| MkDocs Material | 9.7.7 | `requirements-docs.txt` and `requirements-docs.lock.txt` |
| Python | 3.12 | Validation environment |
| GitHub Actions | version not captured | `.github/workflows/kalaxy3_build_publish.yml` |
| GitHub Pages | version not captured | Public endpoint observation |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | `requirements-docs.txt`, `requirements-docs.lock.txt`, and `mkdocs.yml` |
| Controller bootstrap | Install the locked requirements from a clean checkout |
| Controller preflight | `make docs-mkdocs-stage` and `make sage-guardrails` |
| Controller host | `donb-mac-mini` |
| Execution host | `donb-mac-mini` |
| Machine-local authoritative state | none; the excluded raw transcript is provenance only |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual publication changes were reconciled into repository-owned workflow and values files.
- [x] Controller and execution-host versions are represented in `components`, with unavailable external service versions identified.

### Configuration excerpt

```yaml
site_name: Kalaxy3 K3s Cluster
strict: true
```

Pinned dependencies:

```text
mkdocs==1.6.1
mkdocs-material==9.7.7
```

## Prerequisites and assumptions

### Proven prerequisites

- The feature work was merged into the repository before workflow-generated publication output was committed (`EV-007`).
- The pinned documentation dependencies and repository scripts exist in Git (`EV-008`).
- The evidence branch was clean and synchronized when concise evidence was captured (`EV-009`).
- Public GitHub Pages resources were reachable during evidence collection (`EV-005`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | GitHub Pages and the repository workflow remain enabled after evidence collection. | Future publication may become unavailable even though the recorded migration was valid on 2026-07-29. | Re-run representative endpoint checks and inspect the current workflow on any publication failure. |
| `ASM-002` | The generated nginx image is deployed only through repository-controlled automation. | Runtime content could differ from the recorded image lineage. | Validate the running image digest and exposed content when in-cluster runtime assurance is required. |

These assumptions concern future availability and runtime deployment; they do not prove the recorded build or publication claims.

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
python3 -m pip install -r requirements-docs.lock.txt
make docs-mkdocs-stage
```

### Execution

The historical implementation was divided into small, reviewable commits:

1. Stage the MkDocs toolchain and source-preparation logic.
2. Add CI validation.
3. Add deterministic promotion and publication validation.
4. Switch the workflow from Daux to MkDocs Material.
5. Extend SAGE discovery and navigation authority.
6. Merge the publication pull request.
7. Let the workflow generate `docs/` and update the nginx values lineage.

### Expected change

A strict MkDocs Material build should generate a complete tracked site, preserve searchable evidence content, omit evidence artifacts from primary navigation, remove Daux-generated output, and publish through the repository workflow.

### Observed change

The strict build, publication comparison, navigation validation, generated inventory, representative public resources, and SAGE guardrails all passed (`EV-001` through `EV-008`).

### Failed or superseded paths

- A context-only request was initially unclassified; the exact requester language was retained and combined with the resolved task.
- Byte comparison initially failed only for sitemap files; normalized XML proved the logical content matched.
- An oversized transcript repeatedly triggered secret scanning because it contained duplicate diagnostics and credential-shaped examples.
- A GitHub Actions secret reference caused a scanner false positive; a regression-tested repository fix was committed.
- Evidence-orchestrator modifications initially lacked a specialized changed-path context; the authority map was corrected.
- The final evidence design excluded redundant raw output and preserved only its provenance.

## Evidence items

### `EV-001` — Strict MkDocs staging result

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | repository staged MkDocs source and site |
| Tool and version | mkdocs=1.6.1; mkdocs-material=9.7.7 |
| Expected result | Strict source preparation, build validation, and navigation validation pass. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```bash
make docs-mkdocs-stage
```

**Observed result**

```text
Source preparation: PASS
Markdown files: 116
Total staged files: 202
Compatibility link rewrites: 16
Build validation: PASS
Generated HTML files: 115
Total generated files: 246
Navigation validation: PASS
Published artifact files: 77
```

**Interpretation**

The pinned staging target produced the documented source and output inventories. The observation does not prove every page renders correctly in every browser.

### `EV-002` — Tracked publication reproducibility comparison

| Field | Value |
|---|---|
| Classification | generated-artifact |
| Supports or contradicts | `CLM-002` |
| Collected by | repository validation automation |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | `.mkdocs-work/site` and `docs/` |
| Tool and version | python=3.12 |
| Expected result | All logical generated content matches the tracked publication. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
Compare path inventories and SHA-256 values; normalize only sitemap lastmod values and gzip metadata.
```

**Observed result**

```text
Total files: 246
Byte-identical non-sitemap files: 244
Normalized sitemap files: 2
Non-sitemap differences: 0
Normalized sitemap differences: 0
```

**Interpretation**

The tracked publication is reproducible from the fresh strict build. This treats only generated sitemap timestamps and gzip container metadata as volatile.

### `EV-003` — Navigation exclusion and artifact preservation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | tracked `docs/` site |
| Tool and version | python=3.12 |
| Expected result | Evidence artifacts remain published but are absent from primary navigation. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```bash
python3 scripts/docs/validate-mkdocs-navigation.py --site docs
```

**Observed result**

```text
Primary navigation links: 126
Published artifact files: 77
Evidence artifacts in navigation: 0
```

**Interpretation**

The navigation guardrail prevents raw evidence artifacts from cluttering primary navigation while retaining them as published files.

### `EV-004` — Final tracked repository state

| Field | Value |
|---|---|
| Classification | repository-evidence |
| Supports or contradicts | `CLM-004` |
| Collected by | repository validation automation |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | `docs/` and `yaml/nginx-docs/k8s-doc-to-nginx/values.yaml` |
| Tool and version | git=version-not-captured |
| Expected result | MkDocs output is tracked, Daux output is absent, and nginx lineage references the migration merge. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
Inspect tracked generated-file inventory, Daux output paths, and APP_VERSION.
```

**Observed result**

```text
Tracked generated files: 246
Tracked HTML pages: 115
Tracked evidence-artifact files: 77
Daux-generated outputs: 0
APP_VERSION: f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45
```

**Interpretation**

The accepted repository state is MkDocs-based and records the merge commit used for the nginx documentation image lineage.

### `EV-005` — Representative public GitHub Pages resources

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-005` |
| Collected by | repository evidence preparation |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | public GitHub Pages endpoints |
| Tool and version | python-urllib=3.12 |
| Expected result | Representative public resources return HTTP 200 with nonempty content. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
HTTP GET the landing page, evidence catalog, and search index.
```

**Observed result**

```text
Landing: HTTP 200, text/html, 65,855 bytes
Evidence catalog: HTTP 200, text/html, 71,013 bytes
Search index: HTTP 200, application/json, 1,812,126 bytes
```

**Interpretation**

Representative GitHub Pages resources were publicly reachable during evidence collection. This is not an exhaustive link or browser test.

### `EV-006` — SAGE guardrails and index reconciliation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | repository SAGE governance and evidence indexes |
| Tool and version | python=3.12; make=version-not-captured |
| Expected result | Required guardrails and evidence reconciliation pass. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```bash
make sage-guardrails
make sage-index-check
```

**Observed result**

```text
SAGE guardrails: PASS
SAGE evidence reconciliation: PASS
Records: 30
Generated paths: 44
Changed paths: 0
```

**Interpretation**

The migration and evidence-governance state passed repository-owned checks. Existing legacy and curation notices were nonblocking and outside this migration's scope.

### `EV-007` — Evidence-orchestration governance repair

| Field | Value |
|---|---|
| Classification | repository-evidence |
| Supports or contradicts | `CLM-006`, `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | Git repository |
| Target | SAGE changed-path authority and evidence orchestrator |
| Tool and version | git=version-not-captured |
| Expected result | Evidence-orchestrator changes are classified and workflow secret references do not create false positives. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
Inspect commits b7b4de5 and 6014d04 and rerun SAGE self-tests and guardrails.
```

**Observed result**

```text
b7b4de5 Classify SAGE evidence orchestrator changes
6014d04 Allow GitHub Actions secret references in SAGE capture
Post-commit SAGE validation: PASS
```

**Interpretation**

The evidence workflow learned from the failed path: specialized changed-path discovery now covers the orchestrator, and secret-reference regression coverage remains fail-closed for literal credentials.

### `EV-008` — Migration commit and publication lineage

| Field | Value |
|---|---|
| Classification | repository-evidence |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003`, `CLM-004`, `CLM-007` |
| Collected by | repository evidence preparation |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | Git repository |
| Target | migration, merge, generated documentation, and nginx values commits |
| Tool and version | git=version-not-captured |
| Expected result | Staging and validation commits precede activation, merge, and workflow-generated publication commits. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
Inspect full commit subjects, timestamps, and short statistics for the migration lineage.
```

**Observed result**

```text
e189736 Stage MkDocs Material build tooling
74e33f4 Validate staged MkDocs build in CI
3793267 Add staged MkDocs publication promotion
aaddd47 Switch documentation publication to MkDocs Material
48af690 Hide evidence artifacts from MkDocs navigation
f4212d7 Merge pull request 2
bdf6d5d Generate Kalaxy3 MkDocs Material documentation
68065a4 Update values.yaml
```

**Interpretation**

The implementation was staged and validated before activation and merge, then completed through workflow-generated site and values commits.

### `EV-009` — Concise evidence boundary and raw-transcript provenance

| Field | Value |
|---|---|
| Classification | generated-artifact |
| Supports or contradicts | `CLM-008` |
| Collected by | repository evidence preparation |
| Collected at | 2026-07-29T19:52:15-05:00 |
| Execution source | donb-mac-mini |
| Target | evidence-generation inputs |
| Tool and version | python=3.12 |
| Expected result | Preserve unique evidence and source provenance without packaging redundant credential-shaped diagnostic output. |
| Actual result | pass |
| Confidence | high |
| Sensitive data | excluded from package |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` |

**Command, query, source, or observation**

```text
Create a concise claim-oriented artifact; retain only the excluded transcript path, size, and SHA-256.
```

**Observed result**

```text
Raw transcript bytes: 648,271
Raw transcript SHA-256: f69e5edf2e988b5f9878ceb77673a14bd8307e1c3f8255b1660b9f1f4e07ccac
Concise artifact bytes: 9,784
Concise artifact SHA-256: 0992267b6d12fae1b1c903ecb0cdc7cc6cf4f766c58978ad4a9aefed95f47003
```

**Interpretation**

The package preserves traceability while removing repeated output and scanner noise. The excluded transcript is not required to support any migration claim.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Strict pinned build completes. | `EV-001` | Successful staged source, build, and navigation validation. | All stages passed with recorded inventories. | pass |
| `AC-002` | Tracked publication is reproducible. | `EV-002` | No logical differences from a fresh build. | 244 files byte-identical and 2 normalized sitemaps equal. | pass |
| `AC-003` | Evidence artifacts are not primary navigation entries. | `EV-003` | 0 artifact links in navigation. | 0 artifact links; 77 artifact files retained. | pass |
| `AC-004` | Daux output is removed and nginx lineage is recorded. | `EV-004` | No Daux-generated output and merge SHA in values. | Requirement met. | pass |
| `AC-005` | Representative public resources are available. | `EV-005` | HTTP 200 and nonempty content. | Three representative resources returned HTTP 200. | pass |
| `AC-006` | Repository governance passes. | `EV-006`, `EV-007` | Guardrails and index checks pass. | Requirement met. | pass |
| `AC-007` | Migration follows staged implementation and reviewed activation. | `EV-008` | Staging and validation precede activation and merge. | Commit lineage confirms the sequence. | pass |
| `AC-008` | Evidence is concise and traceable. | `EV-009` | Unique results retained; redundant transcript excluded with provenance. | Requirement met. | pass |

### Functional verification

```bash
make docs-mkdocs-stage
python3 scripts/docs/validate-mkdocs-navigation.py --site docs
make sage-guardrails
make sage-index-check
```

Observed:

```text
All commands completed successfully. The generated inventory, navigation result, and SAGE reconciliation matched the values recorded in EV-001, EV-003, and EV-006.
```

### Negative verification

```text
Confirm evidence artifacts in primary navigation equal 0.
Confirm Daux-generated output paths are absent.
Confirm non-sitemap publication differences equal 0.
```

Observed:

```text
Evidence artifacts in navigation: 0
Daux-generated outputs: 0
Non-sitemap publication differences: 0
```

## Idempotency and repeatability

### First accepted run

```text
The workflow generated and tracked 246 files, including 115 HTML pages, and updated the nginx values lineage.
```

### Steady-state rerun

```text
A fresh strict rerun produced the same 246-path inventory. All 244 non-sitemap files were byte-identical, and both sitemap files matched after normalizing documented volatile metadata.
```

### Interpretation

The build and publication are repeatable at the logical-content level. Sitemap generation is intentionally time-sensitive, so raw byte equality is not required for the two sitemap files.

## Security, privacy, and evidence handling

### Security controls

- The repository-owned scanner rejects private keys, bearer credentials, recognized GitHub tokens, and kubeconfig client-key material.
- GitHub Actions secret references are accepted only as references; literal credential assignments remain blocked.
- The evidence artifact contains no secret values.
- Raw diagnostic output is not packaged when it is redundant or contains credential-shaped examples.

### Sensitive material excluded

The 648,271-byte raw transcript was excluded. Its path, size, and SHA-256 were retained for provenance, but its contents are not needed to prove any claim.

### Redactions and omissions

No claim-supporting result was redacted. Repetitive guardrail output, diagnostic examples, and potential credential-shaped strings were omitted by evidence design rather than transformed and republished.

### Residual security risk

Future source or terminal artifacts may contain previously unknown secret formats. The publisher's current fatal scanner patterns and human review remain required before publication.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| MkDocs strict build fails | `make docs-mkdocs-stage` returns nonzero | Publication must not proceed | Correct source, link, dependency, or configuration errors and rerun |
| Generated publication differs | Publication comparison reports path or content changes | Tracked `docs/` may not represent the source build | Regenerate through the repository promotion workflow and inspect the diff |
| Sitemap-only byte differences | Changed `sitemap.xml` or compressed sitemap | False reproducibility failure | Compare normalized XML and ignore only generated timestamp and gzip metadata |
| Evidence artifacts enter navigation | Navigation validator reports a nonzero count | Primary navigation becomes noisy | Restore navigation exclusions and rerun validation |
| Public publication is unavailable | Representative endpoint returns non-200 or empty content | Readers cannot access the site | Inspect workflow status, GitHub Pages configuration, and generated output |
| Evidence capture rejects input | SAGE secret scanner fails closed | Evidence publication stops | Remove redundant material, exclude sensitive content, and preserve concise provenance |
| Dependency upgrade changes output | Strict build or comparison changes | Revalidation required | Update lock files deliberately and repeat all acceptance tests |

### Rollback

```bash
cd ~/dvlp/Kalaxy3
git revert 68065a4f3a7b3bac00710ac9706025e513e140c5
git revert bdf6d5df2c4c2b0adc4404565bfdf6529b888537
git revert f4212d7a07da5d4ef88cfc1cb2f5e659c037ca45
```

Review generated reversions before pushing. A narrower rollback may revert only the activation commit and regenerate the prior publication state from the selected Git revision.

### Rebuild procedure

1. Check out the desired repository revision on a supported controller.
2. Install `requirements-docs.lock.txt`.
3. Run `make docs-mkdocs-stage`.
4. Run navigation and publication validation.
5. Promote the staged site through the repository-owned promotion target.
6. Let the repository workflow publish generated output and update nginx values.
7. Re-run representative public endpoint checks and SAGE guardrails.

### Data durability and backup impact

The migration changes generated documentation and publication configuration, not cluster application data. Git history is the recovery source for Markdown, configuration, scripts, generated output, and evidence. External GitHub availability is outside repository backup guarantees.

## Operational considerations and observability

### Health signals

- `make docs-mkdocs-stage` result.
- Navigation validator counts.
- Fresh-versus-tracked publication comparison.
- GitHub Actions workflow status.
- HTTP status and content size for representative public resources.
- nginx documentation image lineage in `values.yaml`.
- `make sage-guardrails` and `make sage-index-check`.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3
make docs-mkdocs-stage
python3 scripts/docs/validate-mkdocs-navigation.py --site docs
make sage-index-check
```

### Capacity, performance, cost, and sustainability

- **Capacity:** The tracked site contains 246 generated files, including 77 evidence-artifact files.
- **Performance:** The public search index was approximately 1.8 MB during collection; browser search latency was not measured.
- **Cost:** No direct incremental hosting cost was captured; GitHub Pages and workflow usage should be reviewed if repository or traffic volume grows.
- **Sustainability/power:** No measurable homelab power impact was attributed to this documentation migration.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Independent reviewer acceptance is pending. | The record remains validated rather than accepted. | Kalaxy3 architecture | reviewer assignment |
| `GAP-002` | evidence-gap | Every public page, link, browser, and interactive search query was not tested. | Undetected page-specific defects may remain. | Kalaxy3 architecture | publication defect or navigation change |
| `GAP-003` | evidence-gap | A running in-cluster nginx pod and custom-domain route were not validated. | Repository and GitHub Pages evidence do not prove runtime cluster delivery. | Kalaxy3 operations | nginx deployment validation |
| `GAP-004` | evidence-gap | GitHub Actions and GitHub Pages service versions were not captured. | Exact external platform implementation cannot be reproduced locally. | Kalaxy3 architecture | external platform change |
| `GAP-005` | risk | MkDocs or Material upgrades may change generated output or navigation. | Publication reproducibility may break. | Kalaxy3 architecture | dependency change |
| `GAP-006` | limitation | The raw transcript was excluded because it was redundant and contained credential-shaped diagnostic material. | Line-by-line replay of every failed evidence attempt is unavailable in the published package. | Kalaxy3 architecture | forensic review request |
| `GAP-007` | technical-debt | Existing legacy and curation notices were not remediated. | Historical records continue to require separate curation. | Kalaxy3 architecture | legacy evidence curation workstream |

## Troubleshooting

### Strict build fails

**Meaning**

A source, link, dependency, or configuration error prevents a publishable staged site.

**Checks**

```bash
python3 -m pip install -r requirements-docs.lock.txt
make docs-mkdocs-stage
```

**Recovery**

Correct the first strict-build error, rerun staging, and do not promote output until all validators pass.

### Publication comparison reports only sitemap files

**Meaning**

MkDocs regenerated timestamps or compressed-container metadata.

**Checks**

```text
Decompress both sitemap variants, normalize lastmod values, and compare XML trees.
```

**Recovery**

Accept the rerun only when all non-sitemap files are byte-identical and normalized sitemap XML matches.

### SAGE evidence capture rejects an oversized transcript

**Meaning**

The input contains redundant output or strings matching secret-screening rules.

**Checks**

```text
Identify which unique claims need support and whether the rejected lines add any evidence.
```

**Recovery**

Create a concise claim-oriented artifact, preserve excluded-source provenance with path, size, and SHA-256, and rerun the repository-owned capture process.

### Evidence-orchestrator change is unclassified

**Meaning**

Changed-path discovery does not recognize the affected repository authority.

**Checks**

```bash
python3 scripts/sage/sage-change-preflight.py --changed
```

**Recovery**

Update the repository authority map with a specialized non-default context, validate the discovery guardrail, and commit the governance change separately.

## Freshness, revalidation, and supersession

### Revalidate when

- `mkdocs.yml`, documentation dependencies, source-preparation scripts, validators, promotion logic, or workflow changes.
- GitHub Pages configuration or public paths change.
- nginx documentation-image configuration changes.
- Navigation policy changes.
- A representative public resource fails.
- A rollback is executed.
- A conflicting evidence record is accepted.

### Scheduled review

```text
event-based
```

### Supersession rule

When replaced, set the record status to `superseded`, preserve `SAGE-K3-DOCS-20260729-001`, populate the successor relationship, and state which build, publication, and governance claims remain valid.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent within the generated package.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects technical validation and pending review.
- [x] Owner, author, operator, and reviewer are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is represented by the publication token and evidence-only manifest SHA.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version or a documented unavailable version.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Idempotency and repeatability are documented.
- [x] Unavailable external component versions are represented as evidence gaps.

### Safety and operations

- [x] Secrets and sensitive data are excluded.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback, rebuild, and data-durability impacts are documented.
- [x] Operational health checks are documented.
- [x] Known limitations and gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Kalaxy3 architecture | conditional | 2026-07-29 | Technical validation complete; preserve pending reviewer gate. |
| Reviewer | pending | pending | pending | Independent governance acceptance has not occurred. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-mkdocs-material-publication-sage-package.zip
python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-mkdocs-material-publication-sage-package.zip   --push
```

The package uses evidence-only publication and resolves the implementation commit to `68065a4f3a7b3bac00710ac9706025e513e140c5`. The publisher creates the record checksum, publication manifest, generated evidence indexes, and evidence commit.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Concise migration evidence | `markdown/evidence-artifacts/SAGE-K3-DOCS-20260729-001/concise-evidence.txt` | `0992267b6d12fae1b1c903ecb0cdc7cc6cf4f766c58978ad4a9aefed95f47003` | no | permanent with evidence record |

### Generation-input provenance

```text
Input bundle SHA-256: 3101ac28f293c847c4509d1339a77819bc077757ac017c2b9aa59446aff9df87
Input bundle type: SAGE evidence-generation inputs
Input bundle use: authority snapshot, repository state, and concise evidence source
Input bundle retention: generation-time source; not copied into the final evidence package
```

### Additional notes

The package intentionally contains one concise artifact rather than a raw transcript dump. This preserves the evidence needed to reproduce and review the claims while avoiding redundant output and credential-shaped diagnostic material.
