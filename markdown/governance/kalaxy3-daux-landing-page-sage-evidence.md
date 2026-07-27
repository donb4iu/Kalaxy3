---
evidence_id: SAGE-K3-GOVERNANCE-20260726-003
schema_version: "1.2"
title: Kalaxy3 Daux Landing Page Source and Local Render Validation
nav_title: Validate the Kalaxy3 Daux landing page
nav_section: governance
nav_order: 40
summary: Validates the Kalaxy3 Daux landing-page source, container bootstrap, local render, visual identity, and clean feature-branch preservation without changing branch publication automation.
primary_subject: Kalaxy3 Daux landing page
project: Kalaxy3
record_type: change
status: validated
classification: internal
work_session: Kalaxy3 Daux landing-page correction before resuming centralized observability
work_started_at: 2026-07-26T22:22:00-05:00
work_completed_at: 2026-07-26T22:46:00-05:00
evidence_collected_at: 2026-07-26T22:46:00-05:00
created_at: 2026-07-26T22:55:00-05:00
updated_at: 2026-07-26T23:05:18-05:00
valid_as_of: 2026-07-26
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
owner: Don Buddenbaum
author: ChatGPT
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: not-applicable
execution_host: donbs-imac
controller_host: donbs-imac
nodes:
  - donbs-imac
node_addresses:
  - donbs-imac=local
namespaces:
  - not-applicable
endpoints:
  - origin=github.com/donb4iu/Kalaxy3
  - preview=file:///Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU/index.html
components:
  - Daux=daux/daux.io:latest
  - Daux-container-digest=sha256:b29a089551c11303474d972679d3bdeb12a49ba65e552d954f3e0110dc57dd88
  - Docker=version-not-captured
  - source-root=markdown
  - preview-root=/Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU
  - landing-image-sha256=b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130
repository: donb4iu/Kalaxy3
branch: feature/kalaxy3-daux-landing-page
implementation_commit: 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc
record_path: markdown/governance/kalaxy3-daux-landing-page-sage-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003
confidence: high
tags:
  - sage
  - governance
  - documentation
  - daux
  - landing-page
  - local-validation
  - container-bootstrap
  - github-pages
  - scope-control
relationships:
  verifies:
    - Kalaxy3 Daux landing-page source structure
    - Local Daux container bootstrap
    - Rendered Kalaxy3 title, tagline, image, content, search, and table of contents
    - Feature-branch source preservation
  depends_on:
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/standards/kalaxy3-sage-evidence-publication-process.md
    - markdown/templates/sage-evidence-record-template.md
    - markdown/standards/sage-evidence-metadata-contract-v1.2.json
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - markdown/_index.md
    - markdown/config.json
    - markdown/rpi4.png
    - .github/workflows/kalaxy3_build_publish.yml
    - wip/centralized-logging-staged-20260726
  conflicts_with:
    - none
  generated_by:
    - daux/daux.io:latest
    - Local validation script on donbs-imac
    - Manual visual review by Don Buddenbaum
    - ChatGPT working-session evidence synthesis
    - scripts/sage/sage-publish.py
  implemented_by:
    - 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc
  revalidated_by:
    - none
---
# Kalaxy3 Daux Landing Page Source and Local Render Validation

## Executive summary

Kalaxy3 had useful landing-page content in `markdown/index.md` but lacked the
Daux source-root convention and configuration used by Kalaxy2. This working
session moved the existing content to `markdown/_index.md`, added a
Kalaxy3-specific `markdown/config.json`, and copied the established
`markdown/rpi4.png` landing asset. The existing main-only GitHub Actions
publication workflow was inspected but deliberately not expanded to feature
branches because it pushes generated output directly to `main`. Instead, the
same Daux container family was run locally with the repository mounted
read-only and the preview written under `~/Downloads`. Docker bootstrapped the
previously absent image, Daux generated the complete site, scripted checks
passed, and manual visual review confirmed the Kalaxy3 identity and landing
content. The three source changes were committed as `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc`,
pushed to `origin/feature/kalaxy3-daux-landing-page`, and left with a clean working tree. This record
validates source and local rendering only; merge-to-main and live-site
publication remain pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GOVERNANCE-20260726-003 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Kalaxy3 Daux Landing Page Source and Local Render Validation |
| **Navigation title** | Validate the Kalaxy3 Daux landing page |
| **Navigation section** | governance |
| **Navigation order** | 40 |
| **Summary** | Validates the Kalaxy3 Daux landing-page source, container bootstrap, local render, visual identity, and clean feature-branch preservation without changing branch publication automation. |
| **Primary subject** | Kalaxy3 Daux landing page |
| **Record type** | change |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Kalaxy3 Daux landing-page correction before resuming centralized observability |
| **Started** | 2026-07-26T22:22:00-05:00 |
| **Completed** | 2026-07-26T22:46:00-05:00 |
| **Evidence collected** | 2026-07-26T22:46:00-05:00 |
| **Record created** | 2026-07-26T22:55:00-05:00 |
| **Record updated** | 2026-07-26T23:05:18-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago |
| **Valid as of** | 2026-07-26 |
| **Review due** | event-based |
| **Target record path** | markdown/governance/kalaxy3-daux-landing-page-sage-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/kalaxy3-daux-landing-page |
| **Implementation commit** | 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | not-applicable |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | donbs-imac |
| **Node addresses** | donbs-imac=local |
| **Namespaces** | not-applicable |
| **Endpoints** | origin=github.com/donb4iu/Kalaxy3; preview=file:///Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU/index.html |
| **Components and versions** | Daux=daux/daux.io:latest; Daux-container-digest=sha256:b29a089551c11303474d972679d3bdeb12a49ba65e552d954f3e0110dc57dd88; Docker=version-not-captured; source-root=markdown; preview-root=/Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU; landing-image-sha256=b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130 |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author ChatGPT, operator Don Buddenbaum, owner Don Buddenbaum, and reviewer pending. The affected audience is anyone using the Kalaxy3 generated documentation. |
| **What** | Corrected the Daux landing-page source by renaming `markdown/index.md` to `markdown/_index.md`, adding `markdown/config.json`, adding `markdown/rpi4.png`, locally rendering the complete site, visually validating the result, and preserving the source change in Git. |
| **When** | Work started 2026-07-26T22:22:00-05:00, completed 2026-07-26T22:46:00-05:00, and evidence was collected through 2026-07-26T22:46:00-05:00. Local and system timestamps use America/Chicago. The result is valid as of 2026-07-26 and reviewed event-based. |
| **Where** | Environment homelab; system Kalaxy3; cluster not-applicable; execution host donbs-imac; controller host donbs-imac; nodes donbs-imac; node addresses donbs-imac=local; namespace not-applicable; endpoints origin=github.com/donb4iu/Kalaxy3; preview=file:///Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU/index.html; repository donb4iu/Kalaxy3; branch feature/kalaxy3-daux-landing-page; record markdown/governance/kalaxy3-daux-landing-page-sage-evidence.md. |
| **Why** | Kalaxy3 had an ordinary `markdown/index.md` but no Daux root configuration or landing image, so the generated site lacked the project-level identity and landing-page presentation already used in Kalaxy2. The change was completed before resuming centralized observability so documentation behavior remained clear and separately evidenced. |
| **How** | Audited Kalaxy2 and Kalaxy3 source roots, created a narrow feature branch, preserved existing landing content through a Git rename, added a Kalaxy3-specific configuration and existing image asset, inspected the main-only workflow, rejected risky scope expansion, ran the same Daux container family locally with read-only repository access, validated required HTML and image properties, visually reviewed the page, then committed and pushed only the three source files. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where contains every canonical environment, system, cluster, host, node, address, namespace, endpoint, repository, branch, and record value.
- [x] Why includes rationale and scope control.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Comparison of Kalaxy2 and Kalaxy3 documentation source-root behavior.
- Preservation of the existing Kalaxy3 landing content.
- Daux `_index.md` naming.
- Kalaxy3-specific Daux title, tagline, image, search, modified-date, and
  auto-TOC configuration.
- Reuse and checksum verification of the established `rpi4.png` asset.
- Inspection of the current GitHub Actions generation workflow.
- Local Daux container bootstrap and complete-site generation.
- Scripted HTML and image checks.
- Manual visual validation.
- Feature-branch commit and push.
- Evidence-only SAGE publication.

### Out of scope

- Enabling the publication workflow on feature branches.
- Changing `.github/workflows/kalaxy3_build_publish.yml`.
- Committing locally generated `docs/`.
- Merging the feature branch to `main`.
- Waiting for or validating the main-only GitHub Actions run.
- Validating the public GitHub Pages or `docs.donb4iu.com` result.
- Replacing Daux with MkDocs Material.
- Resuming or changing centralized observability.
- Designing a new Kalaxy3-specific image.
- Establishing image licensing or attribution provenance.

### Nonclaims

This record does **not** claim:

- that the new landing page was live on the public site at evidence collection;
- that GitHub Actions regenerated or committed `docs/`;
- that the branch was merged to `main`;
- that the Daux `latest` tag is immutable;
- that Docker or Daux package versions beyond the observed image digest were
  captured;
- that the build was executed twice to prove deterministic repeatability;
- that the reused Raspberry Pi image depicts every Kalaxy3 architecture;
- that feature-branch publishing was implemented.

## Final accepted state

```text
Source landing page:        markdown/_index.md
Daux configuration:         markdown/config.json
Configured image:           markdown/rpi4.png
Title:                      Kalaxy3 K3s Cluster
Tagline:                    ARM64 and AMD64 homelab architecture, operations, and evidence
Search:                     enabled
Automatic TOC:              enabled
Modified date:              enabled
Local Daux bootstrap:       PASS
Complete local generation:  PASS
Scripted landing checks:    PASS
Manual visual review:       PASS
Preview repository writes:  none
Workflow files changed:     none
Generated docs committed:   none
Implementation reference:   640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc
Remote feature branch:      origin/feature/kalaxy3-daux-landing-page
Working tree after push:    clean
Merged to main:             pending
Live publication checked:   pending
```

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Kalaxy3 lacked the Daux source-root landing configuration used by Kalaxy2. | high | `EV-001` | supported | high |
| `CLM-002` | The implementation preserves existing Kalaxy3 landing content while adopting Daux's `_index.md` convention. | high | `EV-003`, `EV-006` | supported | high |
| `CLM-003` | The configuration renders a Kalaxy3-specific title, tagline, search, auto-TOC, modified date, and image. | critical | `EV-003`, `EV-004`, `EV-005` | supported | high |
| `CLM-004` | The same Daux container family used by GitHub Actions bootstrapped locally without host Daux installation. | high | `EV-002`, `EV-004` | supported | high |
| `CLM-005` | Local validation did not modify workflow files or generated repository `docs/`. | critical | `EV-002`, `EV-004`, `EV-006` | supported | high |
| `CLM-006` | The complete Daux source tree generated successfully, including the landing image. | critical | `EV-004` | supported | high |
| `CLM-007` | The rendered page visibly presents the intended Kalaxy3 identity and landing content. | critical | `EV-005` | supported | high |
| `CLM-008` | The source-only implementation was committed and pushed cleanly to its feature branch. | high | `EV-006` | supported | high |
| `CLM-009` | Final main-branch and live-site publication remained unvalidated during this session. | critical | `EV-007` | supported | high |

## Problem and decision rationale

### Problem or opportunity

Kalaxy3's Markdown root contained `index.md`, while Kalaxy2 demonstrated that
the intended Daux landing-page mechanism used `_index.md`, a root `config.json`,
and a configured image. Kalaxy3 therefore had content but lacked the source
structure that controls project identity and Daux's landing presentation.

### Decision

Make the smallest source correction:

1. rename `markdown/index.md` to `markdown/_index.md`;
2. add a Kalaxy3-specific `markdown/config.json`;
3. copy the already-used `rpi4.png` asset;
4. validate locally with the same Daux container family;
5. leave feature-branch automation and generated `docs/` outside the change.

### Decision drivers

- Preserve the existing Kalaxy3 landing content and links.
- Restore expected Daux landing behavior.
- Avoid stale Kalaxy2 naming.
- Avoid workflow risk from a job that pushes generated output directly to
  `main`.
- Prove container bootstrap without installing Daux on the iMac.
- Keep the correction separate from centralized observability.
- Keep source and generated publication responsibilities distinct.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Leave `markdown/index.md` unchanged | No source change | Continues missing Daux landing configuration and project identity | rejected |
| Copy Kalaxy2 files unchanged | Fast | Publishes stale “Kalaxy2 MicroK8s Cluster” identity | rejected |
| Add workflow triggers for feature branches | Automatic branch builds | Existing workflow pushes `HEAD:main` and publishes artifacts; scope and safety risk | rejected for this session |
| Build directly into repository `docs/` | Exact local reproduction | Produces a large generated diff owned by the main-only workflow | rejected |
| Build to `~/Downloads` with repository read-only | Safe, reviewable, no generated repository changes | Manual invocation required | accepted |
| Design a new Kalaxy3 image | Better architectural representation | Expands scope and requires design and provenance work | deferred |
| Reuse existing `rpi4.png` | Established visual continuity and known checksum | Image emphasizes only the Raspberry Pi portion of a mixed cluster | accepted as interim |

### Tradeoffs and consequences

- The landing image does not represent the AMD64 portion of Kalaxy3.
- The workflow continues to use a mutable `latest` tag, though the observed
  digest is captured.
- The local preview proves renderer behavior but not GitHub-hosted publication.
- Branch validation remains manual.
- Future MkDocs migration may change landing-page conventions.
- Reused image provenance remains an explicit evidence gap.

## Architecture or change description

```text
feature/kalaxy3-daux-landing-page
  |
  +-- markdown/_index.md
  |     +--> preserved Kalaxy3 landing content and navigation links
  |
  +-- markdown/config.json
  |     +--> title: Kalaxy3 K3s Cluster
  |     +--> tagline: ARM64 and AMD64 homelab architecture, operations, and evidence
  |     +--> image: rpi4.png
  |     +--> search, auto_toc, date_modified
  |
  +-- markdown/rpi4.png
  |     +--> SHA-256 b6e1fc...
  |
  +-- local read-only Docker mount
        |
        +--> daux/daux.io:latest
        |     digest sha256:b29a089...
        |
        +--> /Users/donbuddenbaum/Downloads/kalaxy3-daux-preview.A2g1MU
              +--> index.html
              +--> rpi4.png
              +--> complete generated documentation tree
```

The existing main workflow remains:

```text
checkout repository
run daux/daux.io:latest
rm -rf docs
generate markdown -> docs
commit docs
push HEAD:main
publish pages and documentation image
```

It was inspected but not modified.

## Source of truth and implementation lineage

### Repository files

```text
markdown/_index.md
markdown/config.json
markdown/rpi4.png
.github/workflows/kalaxy3_build_publish.yml
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-publish.py
scripts/sage/sage-index.py
```

### Implementation commit

```text
640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc
Add Kalaxy3 Daux landing page
```

The evidence-only publisher must resolve this Git commit reference to the full
implementation commit and replace `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc`.

### Versioned dependencies

| Component/tool | Version or identity | Source |
|---|---|---|
| Daux container | `daux/daux.io:latest` | existing GitHub workflow and local validator |
| Observed Daux image digest | `sha256:b29a089551c11303474d972679d3bdeb12a49ba65e552d954f3e0110dc57dd88` | Docker pull output |
| Docker engine | not-captured | evidence gap |
| Daux application version | not-captured | evidence gap; container digest preserved |
| Landing image | SHA-256 `b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130` | Kalaxy2 and Kalaxy3 local source observation |

### Configuration excerpt

```json
{
  "title": "Kalaxy3 K3s Cluster",
  "tagline": "ARM64 and AMD64 homelab architecture, operations, and evidence",
  "image": "rpi4.png",
  "html": {
    "auto_toc": true,
    "date_modified": true,
    "search": true
  },
  "author": "Don Buddenbaum"
}
```

## Prerequisites and assumptions

### Proven prerequisites

- Docker was running on `donbs-imac`.
- The public Daux container image was pullable.
- The feature branch contained the three expected source changes.
- `markdown/index.md` was absent after the rename.
- The repository could be mounted read-only.
- `~/Downloads` could host a writable temporary preview.
- The configured image checksum matched the observed Kalaxy2 source asset.
- The remote feature branch accepted the implementation commit.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The reused `rpi4.png` asset is appropriate to retain in Kalaxy3. | Visual or licensing concerns may require replacement. | Review asset provenance and replace under a separate documented change. |
| `ASM-002` | The main workflow will render the committed source the same way as the local container invocation. | Hosted output could differ due to image drift or workflow context. | Validate generated `docs/index.html` and the live page after merge. |
| `ASM-003` | Existing relative links preserved by the rename remain correct in hosted output. | Some links could fail after publication. | Perform link checks or targeted navigation review after main generation. |
| `ASM-004` | The short implementation reference uniquely resolves in the repository. | Publisher cannot bind the evidence to an exact commit. | Run package `check`; replace with `git rev-parse 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc` only if resolution fails. |

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
git switch -c feature/kalaxy3-daux-landing-page
```

Audit Kalaxy2 and Kalaxy3 Markdown roots, configuration, landing content, image
identity, and repository cleanliness.

### Execution

```bash
git mv markdown/index.md markdown/_index.md
cp ../Kalaxy2/markdown/rpi4.png markdown/rpi4.png
```

Create `markdown/config.json` with the accepted Kalaxy3 title, tagline, image,
and HTML options.

Inspect the existing publication workflow before choosing the validation path.

### Local validation

The validator:

```text
requires the exact feature branch
requires _index.md, config.json, and rpi4.png
requires index.md to be absent
checks Docker availability
creates a temporary preview under ~/Downloads
mounts the repository read-only
runs daux/daux.io:latest
validates index.html, title, tagline, content, image reference, and checksum
prints repository status
opens the local page
```

### Git preservation

```bash
git add markdown/_index.md markdown/config.json markdown/rpi4.png
git diff --cached --check
git commit -m "Add Kalaxy3 Daux landing page"
git push -u origin feature/kalaxy3-daux-landing-page
```

## Evidence items

### `EV-001` — Kalaxy2 and Kalaxy3 source-root audit

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:23:00-05:00 |
| Execution source | `donbs-imac` |
| Target | `~/dvlp/Kalaxy2/markdown` and `~/dvlp/Kalaxy3/markdown` |
| Tool and version | `find`, `cat`, `sed`, `file`, `shasum`; versions not captured |
| Expected result | Determine whether Kalaxy3 had equivalent Daux landing-page inputs |
| Actual result | Kalaxy2 had `_index.md`, `config.json`, and configured `rpi4.png`; Kalaxy3 had only `index.md` at the root |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md` |

### `EV-002` — Workflow inspection and scope decision

| Field | Value |
|---|---|
| Classification | `repository-evidence` and `decision-evidence` |
| Supports or contradicts | `CLM-004`, `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:30:00-05:00 |
| Execution source | `donbs-imac` |
| Target | `.github/workflows/kalaxy3_build_publish.yml` |
| Tool and version | `sed`; version not captured |
| Expected result | Identify the repository-owned Daux generation command and publication behavior |
| Actual result | Workflow uses `daux/daux.io:latest`, generates `markdown` to `docs`, commits generated output, and pushes `HEAD:main`; feature-branch automation was excluded |
| Confidence | high |
| Sensitive data | Workflow secret names observed but no secret values captured |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md` |

### `EV-003` — Source implementation

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002`, `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:27:00-05:00 |
| Execution source | `donbs-imac` |
| Target | `markdown/_index.md`, `markdown/config.json`, `markdown/rpi4.png` |
| Tool and version | Git and standard shell tools; versions not captured |
| Expected result | Preserve existing content, add Kalaxy3 identity, and provide the configured image |
| Actual result | Three intended source changes only |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/source-index.md`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/source-config.json`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md` |

### `EV-004` — Local Daux bootstrap and complete generation

| Field | Value |
|---|---|
| Classification | `direct-observation` and `generated-artifact` |
| Supports or contradicts | `CLM-003`, `CLM-004`, `CLM-005`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:31:00-05:00 through 2026-07-26T22:43:00-05:00 |
| Execution source | `donbs-imac` |
| Target | Local read-only Kalaxy3 checkout and temporary preview |
| Tool and version | Docker version not captured; Daux image digest captured |
| Expected result | Pull the Daux image if absent, generate the full site, validate the landing page, and leave repository generated output untouched |
| Actual result | pass; all listed Daux outputs succeeded and validator returned `Local Daux validation: PASS` |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/daux-validation-output.txt`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validate-daux-landing-page.sh`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validation-summary.json` |

### `EV-005` — Visual landing-page review

| Field | Value |
|---|---|
| Classification | `direct-observation` and `visual-evidence` |
| Supports or contradicts | `CLM-003`, `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:43:00-05:00 |
| Execution source | Browser on `donbs-imac` |
| Target | Local generated `index.html` |
| Tool and version | Browser version not captured |
| Expected result | Intended title, tagline, image, search, call-to-action, landing content, and TOC are visible |
| Actual result | pass |
| Confidence | high |
| Sensitive data | Browser chrome removed from packaged screenshot |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/rendered-landing-page.png` |

### `EV-006` — Git commit and remote branch

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002`, `CLM-005`, `CLM-008` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T22:46:00-05:00 |
| Execution source | `donbs-imac` |
| Target | `origin/feature/kalaxy3-daux-landing-page` |
| Tool and version | Git version not captured |
| Expected result | Commit and push only the three source changes and finish clean |
| Actual result | pass; implementation reference `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc`, branch up to date, working tree clean |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/implementation-commit-summary.txt`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md` |

### `EV-007` — Publication gap declaration

| Field | Value |
|---|---|
| Classification | `negative-evidence` and `scope-evidence` |
| Supports or contradicts | `CLM-009` |
| Collected by | Don Buddenbaum and ChatGPT |
| Collected at | 2026-07-26T22:46:00-05:00 |
| Execution source | Working-session state |
| Target | `main`, generated `docs`, and public site |
| Tool and version | not-applicable |
| Expected result | Distinguish local validation from hosted publication |
| Actual result | branch not yet merged; hosted generation and live page not validated |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md`; `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validation-summary.json` |

## Verification and acceptance criteria

| Criterion | Expected result | Observed result | Evidence | Status |
|---|---|---|---|---|
| Source naming | `_index.md` exists and `index.md` does not | pass | `EV-003`, `EV-004` | pass |
| Kalaxy3 identity | Correct title and tagline | pass in source and render | `EV-003`, `EV-004`, `EV-005` | pass |
| Landing image | Generated image exists and checksum matches | pass | `EV-003`, `EV-004` | pass |
| Search and TOC | Enabled and visually present | pass | `EV-003`, `EV-005` | pass |
| Complete Daux generation | No generation failure in full source tree | pass | `EV-004` | pass |
| Host bootstrap | Daux image absent initially and pulled successfully | pass | `EV-004` | pass |
| Repository safety | Local preview does not change `docs/` or workflow source | pass | `EV-002`, `EV-004`, `EV-006` | pass |
| Scope control | No feature-branch publication automation added | pass | `EV-002`, `EV-006` | pass |
| Git preservation | Source commit pushed and tree clean | pass | `EV-006` | pass |
| Main publication | Workflow generates new `docs` from merged source | not yet observed | `EV-007` | pending |
| Live-site validation | Public site displays new landing page | not yet observed | `EV-007` | pending |

Acceptance result: all local source and rendering criteria passed. Hosted
publication criteria remain pending, so this record remains `validated`.

## Idempotency and repeatability

### Test performed

One complete local Daux run was captured. The repository was mounted read-only,
the preview directory was newly created, and validation used explicit content
and checksum assertions.

### Observed result

```text
Local Daux validation: PASS
repository generated output unchanged
working source state limited to three intended files
```

### Limitation

A second run against a new preview directory was not captured. Therefore this
record establishes successful reproducible procedure and non-mutating local
validation, but it does not claim byte-for-byte deterministic output across
multiple runs. The `latest` image tag is mutable; the observed digest is
preserved for revalidation.

## Security, privacy, and evidence handling

### Security controls

- Repository mounted read-only during local rendering.
- Preview written outside the repository.
- No workflow change or feature-branch publication was introduced.
- No generated `docs/` were committed from the local run.
- Existing workflow secret values were never displayed.
- The implementation was isolated on a feature branch.
- The source commit was pushed before SAGE package publication.

### Privacy handling

- The original screenshot contained unrelated browser tabs and file-browser
  chrome.
- The packaged visual artifact was cropped to preserve only the rendered page.
- The original screenshot is referenced only by checksum and is not packaged.
- No email bodies, passwords, tokens, cookies, or GitHub credentials are
  included.

### Residual risks

- `daux/daux.io:latest` can move to a different digest.
- The main workflow can write directly to `main`.
- The image's original licensing and attribution provenance was not established.
- Local file rendering does not prove public hosting.
- The screenshot proves visual state at one browser width only.

## Reliability, recovery, rollback, and rebuild

### Reliability

The source correction is small and reversible. Existing landing content was
renamed rather than rewritten. Local validation exercised the complete
documentation source tree, reducing the risk of a root configuration change
breaking unrelated pages.

### Rollback

Before merge, delete the feature branch or revert `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc`.

After merge, use a normal Git revert of the implementation and allow the
main-only Daux workflow to regenerate `docs`. Do not manually edit generated
HTML as the primary rollback.

### Rebuild

```bash
cd ~/dvlp/Kalaxy3
git switch feature/kalaxy3-daux-landing-page

docker run --rm   --volume "$PWD:/build:ro"   --volume "$preview_dir:/preview"   --workdir /build   --entrypoint /bin/sh   daux/daux.io:latest   -lc '/daux/bin/daux generate -s markdown -d /preview'
```

For exact historical reproduction, use the captured container digest rather
than assuming the future `latest` tag resolves identically.

### Recovery from build failure

- Confirm Docker is running.
- Confirm `_index.md`, `config.json`, and `rpi4.png` exist.
- Validate `config.json` syntax.
- Confirm the image checksum.
- Pull the captured image or current workflow image.
- Generate to a new external preview directory.
- Do not weaken the workflow or commit partial generated output to work around
  a local failure.

## Operational considerations and observability

- After merge, watch the existing GitHub Actions workflow.
- Confirm the generated documentation commit appears on `main`.
- Pull the generated commit before deleting the feature branch.
- Verify `docs/index.html` contains the title, tagline, landing content, and
  image reference.
- Open the public page and test the “View Documentation” path.
- Verify representative architecture, installation, operations, security, and
  evidence links.
- Record a superseding revalidation if hosted output differs from local output.
- Resume centralized observability only after this correction is merged and
  its publication state is known.

## Known limitations, evidence gaps, and risks

| Gap or risk | Effect | Owner | Trigger or resolution |
|---|---|---|---|
| Full 40-character implementation SHA not captured in the working-session transcript | Package relies on repository resolution of `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc` | Don Buddenbaum | Publisher `check`; use `git rev-parse 640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc` if needed |
| Docker engine version not captured | Exact host runtime lineage incomplete | Don Buddenbaum | Capture during next documentation toolchain review |
| Daux application version not captured separately | Image digest is stronger than tag but internal application version is unknown | Don Buddenbaum | Query container version during next review |
| `latest` tag is mutable | Future rebuild may differ | Don Buddenbaum | Pin digest or version in a separate workflow change |
| Main workflow publication not yet run | Generated repository and public site remain unproven | Don Buddenbaum | Merge, monitor workflow, and validate hosted result |
| Image provenance not established | Attribution or licensing may require review | Don Buddenbaum | Locate original asset source or replace with an owned Kalaxy3 graphic |
| Image represents Raspberry Pi only | Landing visual underrepresents AMD64 nodes | Don Buddenbaum | Replace under a separate design change |
| Build was run once | Byte-for-byte determinism not proven | Don Buddenbaum | Run twice with captured digest if deterministic evidence becomes necessary |
| No automated link checker was run | Broken destination links may remain | Don Buddenbaum | Add targeted post-publication link validation |

No identified gap contradicts the local source and render claims.

## Troubleshooting

### Daux image cannot be pulled

Confirm Docker network access and retry. Preserve the failure output. Do not
change workflow permissions or publish partial output.

### `index.html` is missing

Confirm:

```text
markdown/_index.md exists
markdown/index.md is absent
markdown/config.json is valid JSON
source path is markdown
destination is writable
```

### Title or tagline is missing

Inspect `markdown/config.json` and generated `index.html`. Rebuild to a new
preview directory to avoid reviewing stale output.

### Image is missing

Confirm:

```text
config image value is rpi4.png
markdown/rpi4.png exists
SHA-256 is b6e1fc370b51949345cf8b4cd98dca9d335fc605a0fea6f84650c5b456df4130
generated preview contains rpi4.png
index.html references rpi4.png
```

### Repository `docs/` changes locally

Stop and inspect the mount and destination. The accepted validator mounts the
repository read-only and writes to `~/Downloads`; local generated `docs/`
changes are outside this session's scope.

### GitHub workflow publishes an unexpected page

Preserve the workflow log and generated commit, compare the container digest,
and revert the implementation if the public page is materially broken. Do not
hand-edit generated HTML.

## Freshness, revalidation, and supersession

### Revalidate when

- the branch is merged into `main`;
- the GitHub Actions workflow regenerates `docs`;
- the public site updates;
- Daux image tag or digest changes;
- `config.json`, `_index.md`, or `rpi4.png` changes;
- the documentation workflow changes;
- Daux is replaced by MkDocs Material;
- the landing image is replaced;
- the repository source root changes;
- any required link fails.

### Scheduled review

```text
Event-based, plus review during the planned Daux-to-MkDocs migration.
```

### Supersession rule

A hosted-publication follow-up may revalidate this record without superseding
it if the source decision remains unchanged. A renderer migration or landing
design replacement should supersede this record and preserve its artifacts.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the metadata contract order.
- [x] Record metadata mirrors front matter.
- [x] Status reflects local validation and pending hosted publication.
- [x] Owner, author, operator, and reviewer are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation reference is recorded.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every local critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool identity.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned hosted work are marked.
- [x] Scope decisions are separated from implementation.
- [x] Repeatability limitations are explicit.
- [x] Every not-captured value has an evidence gap.

### Safety and operations

- [x] Secrets and sensitive browser content are excluded.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback and rebuild are documented.
- [x] Hosted operational checks are documented.
- [x] Known limitations and gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | accept | 2026-07-26 | Accepted local source and render result; hosted publication remains pending. |
| Reviewer | pending | pending | pending | Independent review is required before status may become accepted. |

## Git review and publication

Use only the repository publisher:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-daux-landing-page-sage-package.zip

python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-daux-landing-page-sage-package.zip   --push
```

Do not manually unpack, stage, commit, rebase, or push evidence-package files.

After evidence publication, merge the feature branch without squashing so the
resolved implementation commit and evidence commit remain in history. The
main-only Daux workflow then owns generated `docs/`.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Working-session terminal evidence | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/terminal-evidence.md` | `13961bf7103d6d0b120967ab0fbb47c768a1c369aaf483e146796ade67872596` | no | retain |
| Raw Daux validator output | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/daux-validation-output.txt` | `7669776de8932a3841cd8ad5660b0203a0b308423b851e0650befb50577afb32` | no | retain |
| Cropped rendered-page screenshot | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/rendered-landing-page.png` | `587de6573e6983bd4e2a1681f8df8dd02bd07bf3fe2c17b43ecda43b74cf309d` | unrelated browser chrome removed | retain |
| Executed local validator | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validate-daux-landing-page.sh` | `fc830559d04ec8b24214f8af71a7c0145779abc23c1d3d2b3d53c146d9c88ca8` | no | retain |
| Config source snapshot | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/source-config.json` | `59505adfd4cb94d94cc6b66eac2a8c08694efb05481d10e0fa06b0560375af89` | no | retain |
| Landing source snapshot | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/source-index.md` | `40bd2608d8e43c62dfd10dc74d4a5cbf0b6dea6bee14bb1aa9f8f6f9f934a93d` | no | retain |
| Implementation summary | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/implementation-commit-summary.txt` | `4eccf00fa59adda1193fca6c3db230c3b89be46bb8dd64806cb19c9de10260c3` | no | retain |
| Machine-readable validation | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validation-summary.json` | `64ab0fba7fdfbc1525e152f9e7e78fa87b21f7e244e93a7c34a147092b19bd08` | no | retain |
| External source checksums | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/external-artifact-checksums.sha256` | `af3459c17cefa6ddf8d999d6aff865e2cae2423c9b619fd8804932e255e9e244` | no | retain |

### Additional notes

This is an evidence-only package. The publisher must resolve the implementation
reference `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc0b8d9eff7cc25b9bc1a95df9ef211fcdc`, replace `640c64a0b8d9eff7cc25b9bc1a95df9ef211fcdc`,
replace `2026-07-26T23:05:18-05:00`, generate the record checksum and publication
manifest, update evidence indexes, commit the evidence, and push the feature
branch.
