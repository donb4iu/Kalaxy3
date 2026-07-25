---
title: Kalaxy3 SAGE Evidence Generation and Git Publication Process
project: Kalaxy3
record_type: governance-standard
schema_version: "1.1"
status: proposed
created_at: 2026-07-25T17:00:00-05:00
updated_at: 2026-07-25T17:38:00-05:00
valid_as_of: 2026-07-25
owner: Kalaxy3 architecture
standard_path: markdown/standards/kalaxy3-sage-evidence-publication-process.md
record_standard: markdown/standards/kalaxy3-sage-evidence-record-standard.md
metadata_contract: markdown/standards/sage-evidence-metadata-contract-v1.1.json
record_template: markdown/templates/sage-evidence-record-template.md
manifest_template: markdown/templates/sage-evidence-package-manifest-template.json
publisher: scripts/sage/sage-publish.py
---

# Kalaxy3 SAGE Evidence Generation and Git Publication Process

## Purpose

This process makes every working-session evidence publication deterministic.
The evidence generator synthesizes one package. The repository publisher
enforces metadata, structure, checksums, placement, Git lineage, commit
separation, synchronization, and push.

```text
working session and observed evidence
        |
        v
SAGE package generator
  - schema 1.1 front matter
  - canonical Record metadata table
  - Five Ws and How
  - claims and evidence
  - raw artifact package
        |
        v
scripts/sage/sage-publish.py
  - contract validation
  - exact file placement
  - implementation commit
  - SHA injection
  - record checksum
  - evidence commit
  - safe synchronization and push
```

## Authoritative inputs

The generator and publisher MUST use these repository files:

```text
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.1.json
markdown/templates/sage-evidence-record-template.md
markdown/templates/sage-evidence-package-manifest-template.json
markdown/templates/sage-evidence-generation-request.md
```

The JSON metadata contract is the machine-readable authority for:

- record schema version;
- exact front-matter fields and order;
- list-valued fields;
- exact Record metadata table rows and order;
- exact Five-W table row names;
- canonical list separator;
- unavailable-value vocabulary;
- timestamp and timezone requirements.

The publisher MUST reject drift between the JSON contract and its enforcement
constants.

## Division of responsibility

### Evidence generator

The generator MUST:

1. identify the most recent Kalaxy3 working session and its boundaries;
2. use a permanent evidence ID;
3. use record schema `1.1`;
4. populate every canonical front-matter field in exact order;
5. distinguish work, evidence, record, and validity timestamps;
6. use `America/Chicago` as the canonical local timezone unless the session
   evidence proves another location/timezone;
7. record Kubernetes and other system timestamp zones separately, normally
   `UTC`;
8. normalize components as `component=version`;
9. normalize node addresses as `node=address`;
10. normalize endpoints as `purpose=address-or-hostname`;
11. use `not-applicable`, `not-captured`, or `pending` exactly rather than
    inventing synonyms;
12. generate the exact Record metadata table from front matter;
13. use the exact Five Ws and How rows and keep their facts consistent with
    canonical metadata;
14. include all mandatory template sections in order;
15. create atomic claims and map them to evidence IDs;
16. distinguish direct observation, repository evidence, generated artifacts,
    derived conclusions, assumptions, plans, and negative evidence;
17. separate failed paths from accepted state;
18. document limitations, nonclaims, gaps, rollback, rebuild, operations,
    security, and revalidation;
19. use `__SAGE_IMPLEMENTATION_COMMIT__` wherever the implementation SHA belongs;
20. use `__SAGE_PUBLISHED_AT__` wherever publication time belongs;
21. create one valid package manifest;
22. hash every payload file;
23. return one ZIP and only the standard check and publish commands.

The generator MUST NOT:

- create an informal static header with different field names;
- reformat canonical timestamps in the Record metadata table;
- abbreviate timezones or commit SHAs;
- put version numbers only in prose;
- omit node-address relationships;
- introduce a front-matter field not defined by the contract;
- silently convert assumptions into facts;
- omit a failed attempt that materially explains the accepted design;
- include credentials, tokens, private keys, secret values, or unredacted
  Kubernetes Secrets;
- place raw artifacts outside the evidence ID directory;
- provide a custom Git workflow.

### Repository publisher

`scripts/sage/sage-publish.py` MUST:

- reject unsafe ZIP paths, symbolic links, undeclared files, and checksum
  mismatches;
- require package schema `1.1` and record schema `1.1`;
- verify the repository standard, template, metadata contract, and process;
- enforce exact front-matter field order;
- validate RFC3339 timestamps and IANA timezone names;
- validate canonical unavailable values;
- validate node/address, endpoint, component/version, and artifact-root formats;
- require the exact Record metadata table and compare every value with front
  matter;
- require the exact Five-W row order;
- detect material conflicts between Five Ws and metadata;
- validate claims and evidence references;
- scan for high-confidence secret patterns;
- require a clean Git index;
- synchronize safely with `origin/main`;
- stage only manifest-declared implementation paths;
- create a separate implementation commit when implementation changed;
- inject the full immutable implementation SHA;
- copy only declared evidence files;
- generate the final record checksum;
- write a publication manifest containing standard, template, process, and
  metadata-contract hashes;
- stage only declared evidence paths;
- create a separate evidence commit;
- repair the recorded implementation SHA after a safe rebase if necessary;
- push without force;
- report final commits, paths, and actual working-tree state.

## Package format

A package is a ZIP with exactly:

```text
sage-package.json
payload/
  markdown/<category>/<record>.md
  markdown/evidence-artifacts/<evidence-id>/<artifact files>
```

The packaged record does not include its final checksum because publication
replaces tokens. The publisher creates:

```text
markdown/<category>/<record>.md.sha256
markdown/evidence-artifacts/<evidence-id>/publication-manifest.json
```

## Package manifest schema 1.1

| Field | Requirement |
|---|---|
| `schema_version` | Exactly `1.1`. |
| `record_schema_version` | Exactly `1.1`. |
| `metadata_contract_path` | Exactly `markdown/standards/sage-evidence-metadata-contract-v1.1.json`. |
| `repository` | Exactly `donb4iu/Kalaxy3`. |
| `branch` | Target branch, normally `main`. |
| `evidence_id` | Permanent SAGE evidence ID. |
| `record_path` | Canonical repository path. |
| `record_checksum_path` | Exactly `record_path + .sha256`. |
| `artifact_paths` | Files under the exact evidence ID artifact root. |
| `implementation_paths` | Exact implementation paths changed during the session. |
| `publication_mode` | `split` or `evidence-only`. |
| `implementation_commit_message` | Imperative implementation commit subject. |
| `evidence_commit_message` | Imperative evidence commit subject. |
| `files` | Every packaged payload file and its SHA-256. |

## Publication modes

### Split

Use when implementation or configuration changed:

```text
commit 1: implementation paths only
commit 2: evidence record, checksum, artifacts, publication manifest
```

### Evidence-only

Use when the session only validates or documents an existing implementation.
`implementation_paths` must be empty. The manifest may name an existing full
implementation SHA; otherwise the publisher uses current `HEAD`.

## Standard commands

### Check

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

No manual unzip, stage, commit, rebase, or push step belongs to the normal
process.

### Self-test

```bash
cd ~/dvlp/Kalaxy3
python3 scripts/sage/sage-publish.py self-test
```

The self-test creates a temporary bare remote and working repository, publishes
a synthetic schema 1.1 split package, validates both commits and metadata
mirroring, pushes, and requires a clean final tree.

## Validation gates

The publisher rejects:

- package schema other than `1.1`;
- record schema other than `1.1`;
- invalid ZIP structure or hash inventory;
- missing repository contract files;
- drift between contract JSON and publisher constants;
- missing, extra, or reordered front-matter fields;
- noncanonical timestamp, timezone, unavailable-value, component, address, or
  endpoint formats;
- a Record metadata row that is missing, extra, reordered, or inconsistent;
- a Five-W row that is missing, extra, reordered, or materially inconsistent;
- unsupported lifecycle status or record type;
- missing required section or unresolved template marker;
- missing evidence referenced by a claim;
- incomplete Five-W or final checklist in a validated/accepted record;
- an accepted record with a pending reviewer;
- a split package without the implementation token;
- a high-confidence secret pattern;
- preexisting staged changes;
- wrong branch or remote;
- diverged local and remote history;
- no implementation change in split mode;
- unexpected staged files;
- final checksum mismatch;
- unsafe Git or push failure.

Warnings are printed and require review; they do not silently disappear.

## Consistency rules

1. Front matter is authoritative.
2. Record metadata mirrors front matter exactly.
3. Five Ws explain metadata and may not redefine it.
4. Components and versions always use `name=version`.
5. Nodes and addresses always use `node=address`.
6. Endpoints always use `purpose=value`.
7. Lists use semicolon-space in the human-readable metadata table.
8. Timestamps remain RFC3339 in canonical displays.
9. Local timezone uses an IANA name; system timestamp zones remain separate.
10. Missing concepts use only canonical unavailable values.
11. Implementation and evidence commits remain separate when implementation
    changed.
12. Historical evidence IDs never change.

## Evidence-package generation checklist

### Canonical metadata

- [ ] Schema version is 1.1.
- [ ] Every front-matter field exists in exact order.
- [ ] Work completion and evidence collection timestamps are distinct.
- [ ] Local and system timestamp timezones are explicit.
- [ ] Nodes, addresses, endpoints, and components use canonical formats.
- [ ] The artifact root matches the evidence ID.
- [ ] No ad hoc front-matter keys exist.
- [ ] Record metadata exactly mirrors front matter.
- [ ] Five Ws agree with metadata.

### Evidence record

- [ ] All mandatory headings exist in order.
- [ ] Scope, exclusions, and nonclaims are explicit.
- [ ] Atomic claims map to evidence items.
- [ ] Expected and observed results are separated.
- [ ] Failed paths are separated from accepted state.
- [ ] Idempotency is proven or not applicable.
- [ ] Security and secret review is complete.
- [ ] Rollback, rebuild, operations, troubleshooting, and revalidation are
      complete.
- [ ] Implementation and publication tokens are present where required.

### Artifacts and publication

- [ ] Material terminal evidence is preserved.
- [ ] Raw artifacts use the evidence ID directory.
- [ ] Sensitive data is removed or redacted.
- [ ] Every payload file is hashed.
- [ ] Exact implementation paths are listed.
- [ ] Commit messages are imperative and specific.
- [ ] Package passes `check`.
- [ ] Package is published only through the script.

## Limitations

- Structural validation cannot prove that every factual statement is true.
- Exact metadata prevents naming drift but cannot supply evidence that was not
  captured.
- Secret scanning is conservative and cannot guarantee absence of all sensitive
  material.
- Legacy schema 1.0 records remain valid historical artifacts but are not
  accepted as templates for new records.
- A process update that replaces the publisher itself requires a reviewed
  bootstrap extraction before the new publisher can validate its own update.
