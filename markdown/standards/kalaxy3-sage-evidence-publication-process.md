---
title: Kalaxy3 SAGE Evidence Generation and Git Publication Process
project: Kalaxy3
record_type: governance-standard
schema_version: "1.2"
status: proposed
created_at: 2026-07-25T17:00:00-05:00
updated_at: 2026-07-26T13:56:37-05:00
valid_as_of: 2026-07-25
owner: Kalaxy3 architecture
standard_path: markdown/standards/kalaxy3-sage-evidence-publication-process.md
record_standard: markdown/standards/kalaxy3-sage-evidence-record-standard.md
metadata_contract: markdown/standards/sage-evidence-metadata-contract-v1.2.json
record_template: markdown/templates/sage-evidence-record-template.md
manifest_template: markdown/templates/sage-evidence-package-manifest-template.json
publisher: scripts/sage/sage-publish.py
indexer: scripts/sage/sage-index.py
legacy_registry: markdown/evidence/legacy-record-registry.json
---

# Kalaxy3 SAGE Evidence Generation and Git Publication Process

## Purpose

This process makes working-session evidence publication deterministic while
preserving all historical evidence. The generator creates one package. The
repository publisher validates, commits, resolves lineage, reconciles current
and legacy evidence, generates navigation, and optionally pushes.

```text
working session
  -> schema 1.2 package
  -> package validation
  -> implementation commit
  -> evidence installation and SHA resolution
  -> current + legacy evidence reconciliation
  -> catalog and migration views
  -> evidence commit
  -> safe synchronization and push
```

## Authoritative repository files

```text
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-record-template.md
markdown/templates/sage-evidence-package-manifest-template.json
markdown/templates/sage-evidence-generation-request.md
markdown/evidence/legacy-record-registry.json
scripts/sage/sage-publish.py
scripts/sage/sage-index.py
```

The JSON contract and publisher constants MUST agree exactly.

## Multi-controller execution contract

The repository, rather than a particular workstation, is the publication and
deployment source of truth.

Before generating or publishing evidence, the controller MUST synchronize the
declared branch, use the repository-created virtual environment, install exact
repository dependencies, pass controller preflight, identify the actual
controller and execution hosts, and preserve implementation lineage through a
full Git commit SHA.

Changing controller hosts MUST NOT change dependency selection, generated
configuration, deployment behavior, evidence structure, or the target
environment. Machine-local persistent configuration must be reconciled into
the repository before evidence can claim repeatability.

## Generator responsibilities

The evidence generator MUST:

1. identify the most recent Kalaxy3 working session and its boundaries;
2. use package and record schema `1.2`;
3. assign a permanent SAGE evidence ID;
4. populate every canonical field in exact order;
5. provide formal title, navigation title, section, order, summary, and primary
   subject;
6. distinguish work, evidence, record, validity, local-time, and system-time
   semantics;
7. create the exact Record metadata table from front matter;
8. include `[TOC]` and all mandatory sections in order;
9. keep Five Ws consistent with canonical metadata;
10. create atomic claims and evidence items;
11. include repository changes, terminal evidence, expected and observed
    results, failed paths, limitations, rollback, rebuild, security, operations,
    and revalidation;
12. use `__SAGE_IMPLEMENTATION_COMMIT__` and `__SAGE_PUBLISHED_AT__` tokens;
13. place artifacts under the evidence ID directory;
14. hash every package payload file;
15. return one ZIP and only the standard check and publish commands.

The generator MUST NOT provide a custom unzip, Git add, commit, pull, or push
workflow.

## Publisher responsibilities

`scripts/sage/sage-publish.py` MUST:

- reject unsafe ZIP paths, links, undeclared files, and checksum mismatches;
- require package and record schema `1.2`;
- enforce the metadata and navigation contracts;
- validate table mirroring, Five-W consistency, headings, claims, evidence,
  checklists, and secret patterns;
- synchronize safely with the declared branch and remote;
- stage only manifest-declared implementation paths;
- create a separate implementation commit when required;
- inject the full implementation SHA and publication timestamp;
- create the final evidence checksum and publication manifest;
- call the evidence indexer after the record is installed;
- stage generated catalog additions, changes, and safe stale removals in the
  evidence commit;
- create a separate evidence commit;
- repair the implementation SHA after a safe rebase when necessary;
- push without force;
- report commits, paths, warnings, and working-tree state.

## Evidence reconciliation

`scripts/sage/sage-index.py` MUST:

1. discover all records under configured candidate roots;
2. discover SAGE IDs outside candidate roots;
3. include explicit registry records;
4. classify records as `sage-current`, `sage-legacy`, or `legacy-evidence`;
5. use authoritative schema 1.2 navigation metadata for current records;
6. use curated registry metadata when supplied;
7. use clearly identified inferred metadata only when necessary for discovery;
8. assign deterministic `LEGACY-K3-*` identifiers to pre-SAGE records;
9. preserve source files without rewriting them;
10. reject duplicate IDs and duplicate current navigation titles within a
    section;
11. generate Markdown, JSON, and CSV catalogs plus section, subject, status,
    legacy, and migration views;
12. remove only stale paths declared by the previous generated-files manifest;
13. report legacy and curation warnings without blocking unrelated current
    evidence publication;
14. fail `check` when generated catalog files are stale.

The compatibility model is asymmetric by design:

```text
new schema 1.2 record -> strict publication gate
schema 1.0/1.1 record -> preserve, index, warn, migrate deliberately
pre-SAGE Markdown     -> preserve, assign stable legacy ID, curate or infer
```

Historical records are never automatically rewritten to satisfy the current
schema.

## Legacy registry

The registry is:

```text
markdown/evidence/legacy-record-registry.json
```

It contains:

- `registry_version`;
- candidate evidence roots;
- explicit exclusions;
- optional curated records keyed by `source_path`.

A curated record may define `nav_title`, `nav_section`, `nav_order`, `summary`,
`primary_subject`, dates, status, owner, tags, confidence, and migration status.
Curated values improve navigation but do not change the historical source.

## Package format

A package ZIP contains exactly:

```text
sage-package.json
payload/
  markdown/<category>/<record>.md
  markdown/evidence-artifacts/<evidence-id>/<artifact files>
```

The publisher creates the final checksum and publication manifest after token
replacement. Generated catalogs are repository outputs, not package payload.

## Manifest schema 1.2

| Field | Requirement |
|---|---|
| `schema_version` | Exactly `1.2`. |
| `record_schema_version` | Exactly `1.2`. |
| `metadata_contract_path` | Exact schema 1.2 contract path. |
| `repository` | `donb4iu/Kalaxy3`. |
| `branch` | Target branch. |
| `evidence_id` | Permanent SAGE ID. |
| `record_path` | Canonical record path. |
| `record_checksum_path` | `record_path + .sha256`. |
| `artifact_paths` | Files under the evidence ID artifact root. |
| `implementation_paths` | Exact changed implementation files. |
| `publication_mode` | `split` or `evidence-only`. |
| commit messages | Imperative and specific. |
| `files` | Every payload path and prepublication SHA-256. |

## Publication modes

### Split

Use when implementation changed:

```text
commit 1: declared implementation files
commit 2: evidence, checksum, artifacts, publication manifest, generated catalog
```

### Evidence-only

Use when no implementation changed. The package may name an existing full
implementation SHA; otherwise the current `HEAD` is used.

## Standard commands

### Check a package

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py check \
  ~/Downloads/<sage-package>.zip
```

### Publish and push

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/<sage-package>.zip \
  --push
```

### Reconcile or verify navigation independently

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-index.py reconcile
python3 scripts/sage/sage-index.py check
```

### Self-test

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py self-test
```

The self-test MUST publish a current schema 1.2 record and preserve a pre-SAGE
legacy record in an isolated temporary repository and remote.

## Publication gates

Publication fails for:

- schema or contract drift;
- unsafe package structure;
- missing, extra, reordered, or inconsistent current metadata;
- invalid navigation values or duplicate current navigation titles;
- missing `[TOC]` or mandatory section;
- missing evidence referenced by a claim;
- incomplete validated/accepted checklists;
- high-confidence secret patterns;
- preexisting staged changes;
- wrong branch, remote, or diverged history;
- unexpected staged files;
- checksum failure;
- catalog reconciliation failure;
- duplicate permanent IDs;
- stale generated catalog in `sage-index.py check`;
- unsafe Git or push failure.

Legacy deficiencies produce migration warnings rather than record deletion or
unrelated publication failure, except duplicate IDs or unsafe paths.

## Generated outputs

```text
markdown/evidence/index.md
markdown/evidence/current.md
markdown/evidence/legacy.md
markdown/evidence/migration-report.md
markdown/evidence/catalog.json
markdown/evidence/catalog.csv
markdown/evidence/sections/
markdown/evidence/subjects/
markdown/evidence/status/
markdown/evidence/generated-files.json
```

These files are generated and MUST NOT be edited manually. The registry is
curated and MUST NOT be overwritten by the indexer.

## Process request

The normal user request is:

> Generate the SAGE evidence package for this working session using the Kalaxy3
> SAGE standard, template, and publication process.

The response should contain one ZIP plus the standard `check` and `publish`
commands. No session-specific Git procedure is required.

## Limitations

- Structural validation cannot prove every factual statement.
- Inferred legacy metadata is useful for discovery but is not authoritative.
- Candidate roots may need registry additions for evidence stored elsewhere.
- Secret scanning cannot guarantee absence of every sensitive value.
- Documentation renderers still control visual styling, but the catalog and
  navigation semantics are repository-owned and renderer-neutral.
- Migration remains a reviewed activity; the indexer does not fabricate a
  compliant record from incomplete history.
