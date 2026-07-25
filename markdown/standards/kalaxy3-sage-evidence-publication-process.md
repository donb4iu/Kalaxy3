---
title: Kalaxy3 SAGE Evidence Generation and Git Publication Process
project: Kalaxy3
record_type: governance-standard
schema_version: "1.0"
status: proposed
created_at: 2026-07-25T17:00:00-05:00
valid_as_of: 2026-07-25
owner: Kalaxy3 architecture
standard_path: markdown/standards/kalaxy3-sage-evidence-publication-process.md
record_standard: markdown/standards/kalaxy3-sage-evidence-record-standard.md
record_template: markdown/templates/sage-evidence-record-template.md
manifest_template: markdown/templates/sage-evidence-package-manifest-template.json
publisher: scripts/sage/sage-publish.py
---

# Kalaxy3 SAGE Evidence Generation and Git Publication Process

## Purpose

This process removes variation from working-session evidence publication. The
evidence generator is responsible for synthesizing a SAGE-compliant package.
The repository publisher is responsible for deterministic validation, file
placement, checksums, Git commits, remote synchronization, and push.

The workflow intentionally separates reasoning from repository mutation:

```text
working session and observed evidence
        |
        v
SAGE evidence generator
  - standard and template conformance
  - record and artifact synthesis
  - package manifest and file hashes
        |
        v
one immutable ZIP package
        |
        v
scripts/sage/sage-publish.py
  - package validation
  - implementation commit
  - implementation SHA injection
  - evidence checksum and publication manifest
  - evidence commit
  - upstream synchronization
  - push and final status
```

## Governing sources

Every package must be generated from the versions present in the target
repository:

```text
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/templates/sage-evidence-record-template.md
markdown/standards/kalaxy3-sage-evidence-publication-process.md
```

The evidence-record standard defines identity, lifecycle, evidence classes,
mandatory sections, acceptance rules, repository organization, and security
boundaries. The template defines the concrete record structure and evidence
fields. This process defines the package contract and the only supported Git
publication sequence.

## Canonical invocation

After a working session, say:

> Generate the SAGE evidence package for the most recent Kalaxy3 working
> session using the SAGE standard, SAGE template, and SAGE publication process.

The expanded reusable wording is stored in:

```text
markdown/templates/sage-evidence-generation-request.md
```

## Responsibilities

### Evidence generator

The generator must:

1. use the most recent working-session conversation and supplied terminal
   evidence as the primary observation source;
2. use repository diffs, statuses, commits, manifests, and checksums as
   repository evidence;
3. read the current SAGE standard, template, and publication process;
4. preserve exact commands and material output while trimming unrelated noise;
5. separate direct observation, repository evidence, generated artifacts,
   derived conclusions, assumptions, plans, and negative evidence;
6. use a permanent evidence ID in the standard form;
7. use all template sections in template order;
8. include explicit limitations, nonclaims, evidence gaps, failure paths,
   rollback, rebuild, operations, and revalidation triggers;
9. use `__SAGE_IMPLEMENTATION_COMMIT__` wherever the implementation SHA belongs;
10. use `__SAGE_PUBLISHED_AT__` for the publication timestamp when needed;
11. generate a valid `sage-package.json`;
12. hash every packaged payload file;
13. create one ZIP and return only the standard check and publish commands.

The generator must not:

- silently convert assumptions into observed facts;
- omit failed attempts that explain the accepted design;
- include credentials, tokens, private keys, secret values, or unredacted
  Kubernetes Secrets;
- place raw artifacts outside the evidence ID directory;
- tell the operator to stage files manually;
- invent a session-specific Git sequence.

### Repository publisher

`scripts/sage/sage-publish.py` must:

- reject unsafe ZIP paths and symbolic links;
- verify the package manifest and every payload SHA-256;
- verify the evidence ID and canonical paths;
- verify required front matter and template headings;
- verify claim-to-evidence references;
- scan for high-confidence secret patterns;
- require a clean Git index;
- synchronize with `origin/main` before commits;
- stage only manifest-declared implementation files;
- create a separate implementation commit when implementation changed;
- inject the immutable implementation commit SHA into the record;
- copy only manifest-declared evidence files;
- generate the final record SHA-256;
- write a publication manifest containing the standard and template hashes;
- stage only declared evidence files;
- create the evidence commit;
- repair the recorded implementation SHA if an upstream rebase rewrites it;
- push without force;
- display final commits, paths, and working-tree state.

## Package format

A package is a ZIP with this exact top-level structure:

```text
sage-package.json
payload/
  markdown/<category>/<record>.md
  markdown/evidence-artifacts/<evidence-id>/<artifact files>
```

The record checksum is not packaged as final evidence because publication
replaces the implementation SHA token. The publisher generates the final:

```text
markdown/<category>/<record>.md.sha256
```

The publisher also creates:

```text
markdown/evidence-artifacts/<evidence-id>/publication-manifest.json
```

### Manifest fields

| Field | Purpose |
|---|---|
| `schema_version` | Package contract version; currently `1.0`. |
| `repository` | Must be `donb4iu/Kalaxy3`. |
| `branch` | Target branch; normally `main`. |
| `evidence_id` | Permanent SAGE evidence ID. |
| `record_path` | Canonical repository path for the record. |
| `record_checksum_path` | Must be `record_path + .sha256`. |
| `artifact_paths` | Files under `markdown/evidence-artifacts/<evidence-id>/`. |
| `implementation_paths` | Exact working-tree paths belonging to the implementation. |
| `publication_mode` | `split` or `evidence-only`. |
| `implementation_commit_message` | Commit subject for implementation files. |
| `evidence_commit_message` | Commit subject for evidence files. |
| `files` | Packaged payload paths and their SHA-256 values. |

The machine-readable template is:

```text
markdown/templates/sage-evidence-package-manifest-template.json
```

## Publication modes

### Split publication

Use when the working session changed implementation or configuration files.
The publisher creates:

```text
commit 1: implementation files only
commit 2: evidence record, checksum, raw artifacts, publication manifest
```

The evidence record references commit 1.

### Evidence-only publication

Use when the working session only verified an existing implementation or
created documentation. `implementation_paths` must be empty. The manifest may
provide `evidence_only_implementation_commit`; otherwise the publisher uses the
current `HEAD` as the implementation lineage.

## Standard commands

### Validate without changing the repository

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

No manual `unzip`, `git add`, `git commit`, `pull`, or `push` step is part of
the normal process.

### Publisher self-test

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py self-test
```

The self-test creates a temporary bare remote and working repository, publishes
a synthetic split package, pushes it, validates the two commits, and requires a
clean final tree. It does not modify Kalaxy3.

## Validation gates

A package is rejected when any of these conditions holds:

- invalid or unsafe ZIP structure;
- missing or invalid manifest;
- payload checksum mismatch;
- evidence ID format violation;
- record or artifact path outside canonical directories;
- unsupported lifecycle status or record type;
- missing mandatory front matter;
- missing or out-of-order template section;
- unresolved template placeholder;
- missing evidence item referenced by a claim;
- incomplete Five-W gate on a validated or accepted record;
- accepted record with a pending reviewer;
- publication token missing in a split package;
- high-confidence secret pattern;
- existing staged Git changes;
- wrong branch or repository remote;
- diverged local and remote branch;
- no implementation change in split mode;
- unexpected staged file;
- final checksum mismatch;
- Git command failure or push rejection that cannot be repaired safely.

Warnings do not silently disappear. Possible low-confidence secret assignments
are printed for operator review.

## Git consistency rules

1. Fetch and synchronize before creating commits.
2. Never stage by directory wildcard when the manifest can enumerate files.
3. Never combine implementation and evidence in one commit when implementation
   changed.
4. Never record a short or provisional implementation SHA.
5. Never use force push.
6. If a rebase changes the implementation SHA, update the record, checksum, and
   publication manifest, then amend only the evidence commit.
7. Do not claim a clean tree when unrelated files remain.
8. Preserve historical evidence IDs and supersession relationships.

## Evidence-package generation checklist

### Record

- [ ] Permanent evidence ID selected.
- [ ] Current standard and template used.
- [ ] All mandatory headings present in order.
- [ ] Five Ws and How complete or gaps explicit.
- [ ] Scope, exclusions, and nonclaims explicit.
- [ ] Atomic claims mapped to evidence items.
- [ ] Expected and observed results separated.
- [ ] Failed paths separated from accepted state.
- [ ] Idempotency proven or marked not applicable.
- [ ] Security and secret review complete.
- [ ] Rollback, rebuild, operations, troubleshooting, and revalidation complete.
- [ ] Implementation SHA token present.

### Artifacts

- [ ] Material terminal evidence preserved.
- [ ] Large raw output stored outside the main record.
- [ ] Artifact paths use the evidence ID directory.
- [ ] Sensitive data removed or redacted.
- [ ] Every payload file hashed in the manifest.

### Publication

- [ ] Exact implementation paths listed.
- [ ] Commit messages are imperative and specific.
- [ ] Correct publication mode selected.
- [ ] Package passes `check`.
- [ ] Package is published through the script.
- [ ] Final commits and push are recorded in terminal output.

## Limitations

- The publisher validates structure and traceability, not the truth of every
  technical statement. Human or AI evidence synthesis must remain grounded in
  the working session.
- The publisher cannot recover terminal evidence that was never captured or
  supplied.
- Secret scanning is conservative but cannot guarantee that every sensitive
  value is detected.
- A Git commit proves repository lineage, not operational correctness.
- Reviewer acceptance remains a governance action outside automatic
  publication.
- External evidence and images require separate provenance and retention rules.
- The current implementation expects a normal non-bare Git working tree and
  Python 3 with the standard library.

## Revalidation and change control

Revalidate this publication process when:

- the SAGE record standard or template changes;
- package schema `1.0` changes;
- repository organization changes;
- Git branch policy changes;
- evidence IDs or lifecycle rules change;
- the publisher script changes;
- a package passes validation but produces an incorrect commit or path;
- a secret escapes detection;
- a Git rebase or remote race is not handled correctly.

Changes to this process should include a successful publisher self-test and a
SAGE evidence record describing the change.
