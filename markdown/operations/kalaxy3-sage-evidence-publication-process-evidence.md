---
evidence_id: SAGE-K3-GOVERNANCE-20260725-001
schema_version: "1.0"
title: Repeatable SAGE Evidence Package Generation and Git Publication Process
project: Kalaxy3
record_type: operations
status: validated
classification: internal
created_at: 2026-07-25T17:00:00-05:00
updated_at: 2026-07-25T17:22:08-05:00
valid_as_of: 2026-07-25
review_due: event-based
owner: Don Buddenbaum
author: ChatGPT, based on the Kalaxy3 SAGE standard, template, Kubecost evidence publication experience, and isolated publisher self-test
operator: Don Buddenbaum and scripts/sage/sage-publish.py
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: not-applicable
components:
  - Kalaxy3 SAGE evidence-record standard 1.0
  - Kalaxy3 SAGE evidence-record template 1.0
  - Kalaxy3 SAGE evidence-publication process 1.0
  - Python 3 standard library
  - Git
  - ZIP and SHA-256 package validation
nodes:
  - donbs-imac
namespaces:
  - not-applicable
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: 2fb20594ed442a435567a391f14f21ed123cae8c
record_path: markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md
confidence: high
tags:
  - sage
  - governance
  - evidence-publication
  - git
  - automation
  - checksums
  - reproducibility
  - institutional-memory
relationships:
  verifies:
    - Repeatable SAGE evidence package validation and Git publication
    - Consistent separation of implementation and evidence commits
    - Deterministic implementation commit lineage injection
    - Isolated end-to-end publication self-test
  depends_on:
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/templates/sage-evidence-record-template.md
  supersedes:
    - Ad hoc session-specific SAGE packaging, unzip, staging, commit, pull, and push instructions
  superseded_by:
    - none
  related_to:
    - SAGE-K3-FINOPS-20260724-001
    - markdown/standards/kalaxy3-sage-evidence-publication-process.md
    - markdown/templates/sage-evidence-generation-request.md
    - markdown/templates/sage-evidence-package-manifest-template.json
  conflicts_with:
    - none known
  generated_by:
    - ChatGPT process design and implementation
    - scripts/sage/sage-publish.py self-test
    - SHA-256 implementation file inventory
---

# Repeatable SAGE Evidence Package Generation and Git Publication Process

## Executive summary

Kalaxy3 now has a repository-owned SAGE evidence publication process that replaces session-specific packaging and Git instructions with a stable contract. Evidence generators must produce one ZIP containing `sage-package.json` and a canonical `payload/`; `scripts/sage/sage-publish.py` validates package integrity, SAGE record structure, claim-to-evidence references, canonical paths, and likely secret exposure before it changes Git. For sessions with implementation changes, the publisher creates a dedicated implementation commit, injects its immutable full SHA into the evidence record, generates the final record checksum and publication manifest, creates a separate evidence commit, synchronizes with `origin/main`, and pushes without force. An isolated end-to-end self-test created a temporary remote, published a synthetic split package, produced the required two commits, pushed them, and finished with a clean working tree. The process is technically `validated`; independent reviewer acceptance remains pending.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Owner:** Don Buddenbaum. **Author and process implementer:** ChatGPT using the Kalaxy3 SAGE sources and the observed inconsistencies from the Kubecost evidence-publication session. **Operator:** Don Buddenbaum for repository installation; `scripts/sage/sage-publish.py` for recurring package validation and publication. **Reviewer:** pending. **Affected users:** the Kalaxy3 owner, future evidence reviewers, automation, and AI services that consume repository evidence. |
| **What** | Added a canonical generation request, a package-manifest contract, a governing publication-process standard, a Python validator/publisher, an isolated self-test, and this SAGE evidence record. The process standardizes how the most recent working session becomes a SAGE record, raw artifact directory, checksum, implementation commit, evidence commit, and pushed Git history. |
| **When** | **Designed and implemented:** July 25, 2026 CDT (`UTC-05:00`) after the Kubecost evidence was committed at approximately 16:57 CDT. **Self-test executed:** July 25, 2026 CDT. **Record publication timestamp:** injected by the publisher. **Valid as of:** July 25, 2026. **Review due:** whenever the SAGE standard, template, package schema, Git policy, repository layout, or publisher changes. |
| **Where** | **Repository:** `donb4iu/Kalaxy3`, branch `main`. **Implementation paths:** `scripts/sage/`, `markdown/standards/kalaxy3-sage-evidence-publication-process.md`, and the two SAGE package-generation templates. **Evidence path:** this record under `markdown/operations/` and raw artifacts under `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/`. **Execution environment:** Python 3 and Git on a Kalaxy3 administrative workstation. **Self-test target:** an isolated temporary Git repository and bare remote. |
| **Why** | Previous SAGE sessions used slightly different unzip destinations, file lists, checksum sequences, commit grouping, implementation-SHA updates, pull/rebase order, and push commands. That variation increased the chance of staging unrelated files, recording a provisional SHA, publishing a stale checksum, or leaving repository lineage inconsistent. A repository-enforced process makes evidence production predictable and reviewable. |
| **How** | The evidence generator follows the current SAGE standard, template, and publication process and creates a manifest-declared ZIP. The publisher performs structural and hash validation, synchronizes Git, stages exact implementation paths, commits them, replaces publication tokens, creates the final checksum and publication manifest, stages exact evidence paths, commits evidence, repairs lineage after a safe rebase if needed, pushes, and reports the resulting commits and tree state. |

### Five-W completeness gate

- [x] Who is complete.
- [x] What is complete.
- [x] When is complete and includes timezone.
- [x] Where is complete at both repository and runtime levels.
- [x] Why includes rationale and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Canonical user wording for requesting evidence from the most recent working session.
- Rules an AI or human evidence generator must follow.
- Canonical ZIP structure and JSON package manifest.
- SHA-256 verification of all packaged payload files.
- SAGE front-matter and heading validation.
- Evidence-ID, path, lifecycle, record-type, Five-W, checklist, and claim-reference validation.
- High-confidence secret-pattern rejection and lower-confidence warnings.
- Exact implementation-path staging.
- Separate implementation and evidence commits.
- Full implementation SHA injection before the evidence commit.
- Final evidence-record checksum generation.
- Publication-manifest generation with standard and template hashes.
- Pre-commit upstream synchronization and non-force push.
- Safe repair when a remote update requires rebase and changes the implementation SHA.
- Isolated self-test against a temporary Git remote.

### Out of scope

- Automatically retrieving a ChatGPT conversation from the local workstation.
- Recovering terminal output that was never supplied or captured.
- Determining whether every technical statement is true solely from Markdown structure.
- Replacing owner or reviewer judgment.
- Signing commits, tags, or evidence with a hardware-backed identity.
- Uploading evidence to external artifact storage.
- Parsing binary artifacts for embedded secrets.
- Supporting arbitrary repositories, branches, or directory layouts without code changes.
- Publishing when local and remote branches have unresolved divergence.

### Nonclaims

This record does **not** claim:

- that structural validation proves operational correctness;
- that secret scanning can detect every sensitive value;
- that Git history alone proves the target system behaved as described;
- that evidence can be complete when the working session did not preserve material output;
- that reviewer acceptance is automated;
- that every future repository or branch policy is compatible with schema `1.0`;
- that a package is trusted merely because its internal hashes are self-consistent;
- that the process eliminates the need to inspect warnings or final Git status.

## Final accepted state

```text
Canonical request:
  Generate the SAGE evidence package for the most recent Kalaxy3 working
  session using the SAGE standard, SAGE template, and SAGE publication process.

Package contract:
  sage-package.json
  payload/markdown/<category>/<record>.md
  payload/markdown/evidence-artifacts/<evidence-id>/<artifacts>

Validation command:
  python3 scripts/sage/sage-publish.py check <package.zip>

Publication command:
  python3 scripts/sage/sage-publish.py publish <package.zip> --push

Split publication:
  commit 1 = exact implementation paths
  commit 2 = evidence record, checksum, artifacts, publication manifest

Implementation lineage:
  full 40-character implementation SHA injected before evidence commit

Self-test:
  temporary remote + temporary working repository + two commits + push
  final result = PASS and clean working tree
```

| Item | Accepted result |
|---|---|
| Generation input | Most recent working-session evidence plus current repository standard, template, and process. |
| Generated deliverable | One ZIP package with JSON manifest and canonical payload tree. |
| Normal operator workflow | One optional `check` command and one `publish --push` command. |
| File placement | Determined exclusively by manifest paths after canonical-path validation. |
| Implementation commit | Created first when `publication_mode` is `split`. |
| Evidence commit | Created second after implementation SHA injection and checksum generation. |
| Pull/rebase timing | Upstream synchronized before commits; safe rebase repair available for a later remote race. |
| Push policy | Normal push only; no force push. |
| Evidence checksum | Generated after publication tokens are replaced. |
| Publication provenance | Stored under the evidence artifact directory with hashes of the governing standard and template. |
| Validation boundary | Structural, traceability, package-integrity, secret-pattern, and Git-workflow enforcement; substantive truth remains a review responsibility. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The process defines one canonical working-session request and one package contract. | high | `EV-001`, `EV-002` | supported | high |
| `CLM-002` | The publisher verifies package paths, manifest fields, payload hashes, SAGE structure, claim references, and likely secret exposure before repository mutation. | critical | `EV-002`, `EV-003` | supported | high |
| `CLM-003` | Split publication stages and commits only manifest-declared implementation paths before evidence files. | critical | `EV-002`, `EV-004` | supported | high |
| `CLM-004` | The publisher injects a full implementation commit SHA and generates the final record checksum before creating the evidence commit. | critical | `EV-002`, `EV-004` | supported | high |
| `CLM-005` | The isolated self-test completed the two-commit publication and push with a clean working tree. | critical | `EV-004` | supported | high |
| `CLM-006` | The process preserves the SAGE standard's mandatory identity, lifecycle, Five-W, evidence, recovery, security, limitation, and supersession requirements. | high | `EV-001`, `EV-002`, `EV-005` | supported | high |
| `CLM-007` | The process reduces, but does not eliminate, evidence-quality and secret-handling risk. | high | `EV-002`, `EV-005` | supported | medium-high |
| `CLM-008` | Future sessions can use one standard check command and one standard publication command instead of session-specific Git instructions. | high | `EV-002`, `EV-005` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The Kubecost session exposed a consistency problem in the publication layer rather than in the evidence content. The evidence itself was detailed and SAGE-oriented, but the path from generated files to Git varied repeatedly:

- one response advised appending to an existing record;
- another generated a replacement ZIP;
- commands alternated between repository root and the infrastructure subdirectory;
- checksum timing differed;
- implementation and evidence were sometimes proposed as one commit and sometimes two;
- implementation SHA insertion required a custom Python replacement block;
- pull/rebase and autostash behavior changed across responses;
- manual `git add` lists were generated for each session;
- a remote update after commits could rewrite the implementation SHA and invalidate the record;
- the evidence ZIP itself had no machine-readable contract defining exactly what could be copied and committed.

This made every SAGE publication a small bespoke release process. Bespoke release processes are difficult to review, automate, and reproduce.

### Decision

Adopt a repository-owned package contract and publisher:

1. The evidence generator synthesizes content but does not mutate Git.
2. The ZIP manifest declares every intended repository file and commit input.
3. The publisher validates the package and repository before committing.
4. Implementation and evidence are separate commits when implementation changed.
5. The implementation SHA is injected deterministically.
6. The final checksum is generated only after injection.
7. A publication manifest records the governing standard and template hashes.
8. Normal publication is one command.

### Decision drivers

- Consistent repository paths.
- Exact staging rather than wildcard or improvised file lists.
- Stable claim-to-implementation lineage.
- Repeatable checksum timing.
- Separation of implementation from evidence.
- Rejection before mutation when a package is malformed.
- Security review before files enter Git.
- No force-push requirement.
- Self-contained standard-library implementation.
- A process simple enough to invoke conversationally.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Continue generating custom shell commands for each session | No new repository code | Repeats the inconsistency that motivated the work | rejected |
| Store only a written checklist | Easy to review | Cannot enforce paths, hashes, commit split, or SHA injection | rejected |
| Use a Makefile target with shell fragments | Familiar invocation | JSON and Markdown validation become fragile; platform differences remain | rejected |
| Use a Bash-only publisher | Available on macOS and Linux | Safe ZIP parsing, JSON validation, and structured checks are harder | rejected |
| Use Python with third-party YAML and schema libraries | Rich validation | Adds dependency installation and version drift | deferred |
| Use Python standard library with JSON manifest | Portable, testable, no dependency bootstrap | Front-matter parsing is intentionally limited to required top-level scalars | accepted |
| Commit implementation and evidence together | One commit | Evidence cannot truthfully reference the final implementation commit before the commit exists | rejected |
| Commit implementation first and evidence second | Immutable implementation lineage | Produces two commits per implemented session | accepted |
| Pull/rebase only after both commits | Familiar prior pattern | A rebase can rewrite the implementation SHA already embedded in evidence | rejected as default |
| Synchronize before commits and repair a later remote race | Preserves normal linear history and lineage | More publisher logic | accepted |
| Automatically mark records `accepted` | Fewer manual steps | Confuses technical validation with governance review | rejected |

### Tradeoffs and consequences

- Future evidence generators must conform to a stricter package contract.
- The publisher can reject a package that a human might have published manually.
- Split sessions create two commits, improving lineage at the cost of a slightly longer history.
- Structural validation improves consistency but does not verify every substantive assertion.
- JSON is used for the package manifest even though the evidence record uses YAML front matter.
- The publisher is tied intentionally to Kalaxy3 repository identity and layout.
- Safe remote-race repair adds complexity but prevents silent stale implementation lineage.
- Reviewer acceptance remains manual and visible.

## Architecture or change description

```text
Most recent working session
  conversation + terminal output + repository evidence
                    |
                    v
Evidence synthesis
  current SAGE standard
  current SAGE template
  publication process
                    |
                    v
ZIP package
  sage-package.json
  payload/<record>
  payload/<raw artifacts>
                    |
          +---------+----------+
          |                    |
          v                    v
       check                publish --push
          |                    |
          |             validate package
          |             synchronize upstream
          |             commit implementation
          |             inject implementation SHA
          |             create record checksum
          |             create publication manifest
          |             commit evidence
          |             repair remote race if needed
          |             push
          v                    v
    no Git change       consistent Git lineage
```

### Before

Publication depended on session-specific instructions. The user manually unzipped files, checked checksums, selected implementation paths, committed implementation, captured the SHA, ran a custom text-replacement script, regenerated checksums, staged evidence, committed again, pulled, pushed, and inspected status. The sequence worked for the Kubecost session but was not a reusable repository capability.

### After

The repository contains:

```text
scripts/sage/sage-publish.py
scripts/sage/README.md
scripts/sage/.gitignore
scripts/sage/.gitignore
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-generation-request.md
markdown/templates/sage-evidence-package-manifest-template.json
```

Future generated packages are checked or published through the same executable.

## Source of truth and implementation lineage

### Repository files

```text
scripts/sage/sage-publish.py
scripts/sage/README.md
scripts/sage/.gitignore
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-generation-request.md
markdown/templates/sage-evidence-package-manifest-template.json
markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md
markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/self-test-output.txt
markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/implementation-file-checksums.sha256
markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/publication-manifest.json
```

### Implementation commit

```text
2fb20594ed442a435567a391f14f21ed123cae8c
```

The publisher replaces this token with the immutable full implementation commit SHA before the evidence commit.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE evidence-record standard | `1.0` | `markdown/standards/kalaxy3-sage-evidence-record-standard.md` |
| SAGE evidence-record template | `1.0` | `markdown/templates/sage-evidence-record-template.md` |
| SAGE package schema | `1.0` | manifest and process standard |
| Python | Python 3; exact workstation version is captured by future session evidence when material | local runtime |
| Git | exact workstation version is captured by future session evidence when material | local runtime |
| ZIP | Python standard-library `zipfile` | Python runtime |
| SHA-256 | Python standard-library `hashlib` | Python runtime |

### Configuration excerpt

```json
{
  "schema_version": "1.0",
  "repository": "donb4iu/Kalaxy3",
  "branch": "main",
  "evidence_id": "SAGE-K3-GOVERNANCE-20260725-001",
  "publication_mode": "split",
  "implementation_paths": [
    "scripts/sage/sage-publish.py",
    "scripts/sage/README.md",
    "scripts/sage/.gitignore",
    "markdown/standards/kalaxy3-sage-evidence-publication-process.md",
    "markdown/templates/sage-evidence-generation-request.md",
    "markdown/templates/sage-evidence-package-manifest-template.json"
  ]
}
```

## Prerequisites and assumptions

### Proven prerequisites

- A normal Git working tree exists.
- The repository contains the SAGE record standard and template.
- Python 3 can compile and execute the publisher.
- Git can create commits and push to a bare remote in the self-test.
- Package files can be hashed and validated with the Python standard library.
- The self-test can complete without modifying the real Kalaxy3 repository.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Future evidence generators can access the current working-session conversation or equivalent supplied evidence. | The generated record may omit material observations. | Require the generator to identify unavailable evidence as gaps. |
| `ASM-002` | The target repository remains `donb4iu/Kalaxy3` with branch `main`. | Publisher rejects the repository or targets the wrong branch. | Update process and code through reviewed SAGE change. |
| `ASM-003` | Python 3 standard-library behavior is sufficiently compatible across the operator's macOS and Linux environments. | Package parsing or Git subprocess behavior differs. | Run `self-test` after Python or operating-system changes. |
| `ASM-004` | Exact implementation paths can be determined from the working session. | Unrelated files could be omitted or a split publication could fail. | Manifest generation must use observed Git status and diff evidence. |
| `ASM-005` | Two commits are acceptable for sessions that change implementation. | Repository history may not match a future squash-only policy. | Revalidate if branch policy changes. |
| `ASM-006` | High-confidence regex patterns are useful for blocking obvious secrets. | A sensitive value may evade detection or a harmless value may warn. | Preserve human review and add patterns after incidents. |
| `ASM-007` | Evidence records use the current template heading names or compatible prefixes. | A template revision can cause rejection. | Version and update validator with the template. |
| `ASM-008` | A safe rebase after a remote race leaves the two local publication commits at `HEAD~1` and `HEAD`. | SHA repair could identify the wrong implementation commit. | Self-test and add a remote-race integration test when that path changes. |

## Implementation procedure

### Preparation

Create the repository-owned files from the generated bootstrap ZIP:

```bash
cd ~/dvlp/Kalaxy3
unzip -o ~/Downloads/kalaxy3-sage-publication-process.zip
chmod +x scripts/sage/sage-publish.py
```

Run syntax and isolated functional validation:

```bash
python3 -m py_compile scripts/sage/sage-publish.py
python3 scripts/sage/sage-publish.py self-test
```

### Execution

Publish this process implementation and its evidence through the new publisher:

```bash
python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-sage-publication-process-evidence.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-sage-publication-process-evidence.zip \
  --push
```

### Expected change

- Six process implementation files are committed first.
- The implementation SHA replaces every publication token in this record.
- This record and two raw artifacts are copied to canonical paths.
- The final record checksum is generated.
- A publication manifest is generated under the evidence ID directory.
- Evidence files are committed second.
- Both commits are pushed to `origin/main`.
- The final status is reported accurately.

### Observed change

The implementation package and evidence package were generated. The publisher passed Python compilation and the isolated end-to-end self-test. Repository publication remains the next operator action and will populate the implementation SHA through the tested mechanism.

## Evidence items

### `EV-001` — SAGE record standard requires consistency and lineage

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-006` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25 CDT |
| Execution source | Kalaxy3 SAGE standard review |
| Target | `markdown/standards/kalaxy3-sage-evidence-record-standard.md` |
| Tool and version | File review; schema version `1.0` |
| Expected result | Standard identifies the consistency, evidence-lineage, mandatory-section, acceptance, and repository-organization requirements |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | existing repository standard |

**Command, query, source, or observation**

```text
The standard requires permanent evidence identity, explicit Five Ws and How,
claim-to-evidence traceability, lifecycle status, direct and repository
evidence, expected-versus-observed results, implementation lineage,
idempotency, security review, recovery, limitations, freshness, and canonical
artifact storage.
```

**Observed result**

```text
The standard explicitly identifies inconsistency as the primary weakness in
existing records and requires mandatory sections in a fixed order.
```

**Interpretation**

This establishes the governance need for a repeatable publication process. It does not prove the publisher implementation.

### `EV-002` — Publisher source implements package and Git gates

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003`, `CLM-004`, `CLM-006`, `CLM-007`, `CLM-008` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25 CDT |
| Execution source | generated implementation review |
| Target | `scripts/sage/sage-publish.py` |
| Tool and version | Python 3 source review |
| Expected result | Source contains manifest, hash, path, record, secret, Git, commit, checksum, push, and self-test logic |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | implementation file and checksum artifact |

**Command, query, source, or observation**

```bash
python3 -m py_compile scripts/sage/sage-publish.py
```

**Observed result**

```text
Compilation completed without error.
```

**Interpretation**

The source is syntactically valid and directly contains the required gates. Syntax validation does not prove all runtime paths.

### `EV-003` — Package-validation behavior is exercised by self-test publication

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004` |
| Collected by | `scripts/sage/sage-publish.py` |
| Collected at | 2026-07-25 CDT |
| Execution source | temporary self-test repository |
| Target | synthetic split SAGE package |
| Tool and version | publisher schema `1.0` |
| Expected result | Package accepted only after manifest, payload, record, and Git validation |
| Actual result | pass |
| Confidence | high |
| Sensitive data | synthetic test data only |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/self-test-output.txt` |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-publish.py self-test
```

**Observed result**

```text
The self-test reached publication completion, created an implementation commit,
created an evidence commit, pushed to origin/main, and reported a clean working
tree.
```

**Interpretation**

A synthetically valid split package traversed the same validation and publication path intended for real packages.

### `EV-004` — End-to-end temporary remote publication passed

| Field | Value |
|---|---|
| Classification | `direct-observation` and `generated-artifact` |
| Supports or contradicts | `CLM-003`, `CLM-004`, `CLM-005` |
| Collected by | ChatGPT execution environment |
| Collected at | 2026-07-25 CDT |
| Execution source | isolated temporary Git working tree |
| Target | isolated temporary bare remote |
| Tool and version | Git and Python 3 |
| Expected result | Two commits, successful push, clean final tree, explicit PASS |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none; temporary synthetic repository |
| Artifact | `self-test-output.txt` |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-publish.py self-test
```

**Observed result**

```text
Publication completed with a clean working tree.
Evidence ID:           SAGE-K3-TEST-20260725-001
Implementation commit: 07d61b06f5bbcde38c7940911cc8bb3492ad8741
Evidence commit:       e8221e7de243051705f8b7fd2e4e32e27bed143a
Record:                markdown/operations/sage-publication-self-test.md
Checksum:              markdown/operations/sage-publication-self-test.md.sha256
Published to:          origin/main

SAGE publication self-test: PASS
```

**Interpretation**

This proves the normal split publication path can complete against Git without modifying the real Kalaxy3 repository. It does not exercise every rejection or rebase-conflict path.

### `EV-005` — Canonical request, process, and manifest templates agree

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-006`, `CLM-007`, `CLM-008` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25 CDT |
| Execution source | generated process files |
| Target | publication process and templates |
| Tool and version | manual cross-file review |
| Expected result | Same package structure and commands across process and templates |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | implementation files and checksum artifact |

**Command, query, source, or observation**

```text
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-generation-request.md
markdown/templates/sage-evidence-package-manifest-template.json
scripts/sage/README.md
```

**Observed result**

```text
All files use sage-package.json + payload/, the same check command, the same
publish --push command, and the same split/evidence-only publication model.
```

**Interpretation**

The human-facing and machine-facing instructions are aligned at generation time.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Canonical generation phrase exists | `EV-005` | One reusable request | present | pass |
| `AC-002` | Package contract is machine-readable | `EV-002`, `EV-005` | JSON schema fields and file hashes | present | pass |
| `AC-003` | Publisher compiles | `EV-002` | no syntax error | no error | pass |
| `AC-004` | Unsafe or undeclared ZIP content is rejected by code path | `EV-002` | path, symlink, count, size, inventory checks | implemented | pass |
| `AC-005` | Record structure and lineage are validated | `EV-002` | front matter, headings, claims, evidence, tokens | implemented | pass |
| `AC-006` | Split implementation and evidence commits are created | `EV-004` | two commits | observed | pass |
| `AC-007` | Full implementation SHA is injected | `EV-004` | 40-character SHA | observed | pass |
| `AC-008` | Final checksum is generated | `EV-004` | record `.sha256` path | observed | pass |
| `AC-009` | Push completes without force | `EV-004` | origin/main updated | observed | pass |
| `AC-010` | Final self-test tree is clean | `EV-004` | no working-tree changes | observed | pass |
| `AC-011` | Process limitations are explicit | `EV-005` | limitation section present | observed | pass |
| `AC-012` | Real Kalaxy3 publication is complete | publisher output after operator runs package | two commits pushed to `origin/main` | not yet observed in this package | partial |

### Functional verification

```bash
python3 scripts/sage/sage-publish.py self-test
```

Observed:

```text
SAGE publication self-test: PASS
```

### Negative verification

The publisher contains rejection paths for:

```text
unsafe ZIP paths
symbolic links
more than 500 ZIP entries
more than 500 MiB uncompressed payload
manifest schema mismatch
payload checksum mismatch
noncanonical record or artifact path
invalid evidence ID
missing mandatory front matter or section
missing claim evidence
incomplete validated/accepted checklist
accepted record with pending reviewer
publication token mismatch
high-confidence secret pattern
preexisting staged changes
wrong branch or repository remote
diverged branch
unexpected staged path
checksum mismatch
unsafe push/rebase state
```

Observed:

```text
The source contains explicit SageError rejection paths. A complete fault-injection
suite remains future work.
```

## Idempotency and repeatability

### First accepted run

```text
Publication completed with a clean working tree.
Implementation commit created.
Evidence commit created.
Push completed.
```

### Steady-state rerun

The publisher intentionally does not republish the same split package into a clean repository because no implementation changes remain. A repeated split publication is expected to stop with:

```text
No implementation changes found for split publication
```

The self-test itself is repeatable because it creates a new isolated temporary repository on every run. Multiple self-test executions completed independently without touching Kalaxy3.

### Interpretation

Publication is repeatable but not blindly idempotent: evidence publication creates permanent Git history exactly once per package and implementation state. Rejection of a second split publication prevents duplicate evidence commits based on nonexistent implementation changes. The self-test is safely repeatable.

## Security, privacy, and evidence handling

### Security controls

- ZIP extraction rejects absolute paths, parent traversal, and symbolic links.
- Package file count and uncompressed size are bounded.
- Every payload file must be declared and SHA-256 matched.
- Record and artifact paths are constrained to canonical repository locations.
- The Git index must be empty before publication.
- Only manifest-declared paths are staged.
- High-confidence private key, kubeconfig key, bearer token, and GitHub token patterns are fatal.
- Lower-confidence password, token, and secret assignments produce warnings.
- No force push is used.
- Diverged branches require manual resolution.
- The publication manifest records standard and template hashes.
- Binary artifacts are not decoded or interpreted by the publisher.

### Sensitive material excluded

Never include:

- credentials, access tokens, passwords, private keys, or secret values;
- kubeconfig key material;
- unredacted Kubernetes Secret manifests;
- Basic Auth hashes unless explicitly approved and protected;
- ISP account identifiers or payment information;
- terminal history that contains secrets;
- unnecessary personal information;
- packet payloads when counters are sufficient.

### Redactions and omissions

- The self-test uses synthetic identities and a reserved invalid email address.
- Temporary repository paths are not material and are omitted from the retained artifact.
- No real remote credential was needed for the bare local remote.

### Residual security risk

- Regex scanning cannot detect every encoded or context-specific secret.
- A malicious but internally self-consistent package can pass its own payload hashes; substantive trust still depends on the evidence source and review.
- Binary files may contain sensitive data that the script does not parse.
- Git remote authentication remains outside the publisher and depends on the workstation configuration.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Package hash mismatch | Publisher exits before Git mutation | Package is not published | Regenerate or redownload package; do not bypass validation |
| Existing staged changes | Publisher exits | Prevents accidental commit contamination | Commit, unstage, or reset unrelated index state |
| Missing implementation change in split mode | Explicit error | Duplicate or stale publication prevented | Use a new package or evidence-only mode when appropriate |
| Wrong branch or remote | Explicit repository-contract error | Publication blocked | Switch to correct repository and branch |
| Branch divergence | Explicit error | Automatic publication blocked | Resolve divergence manually, then rerun |
| Remote race before push | Upstream ancestry check | Push delayed | Publisher rebases, repairs implementation SHA, regenerates checksum, and amends evidence when safe |
| Rebase conflict | Rebase abort and error | Publication commits remain local | Resolve upstream conflict manually; revalidate record lineage |
| Secret-pattern rejection | Explicit error naming file and pattern | Sensitive evidence is not committed | Redact or remove secret and regenerate hashes/package |
| Warning-level secret pattern | Warning output | Human review required | Inspect exact file before accepting publication |
| Evidence record validation failure | Explicit missing field/section/ID error | Publication blocked | Correct generator output and rebuild package |
| Push authentication failure | Git error | Local commits exist but remote is unchanged | Repair Git authentication, verify commits, rerun push or publication recovery procedure |

### Rollback

Before push, remove the two local commits while preserving files only when intentionally restarting publication:

```bash
git reset --mixed HEAD~2
```

After push, prefer a non-destructive revert:

```bash
git revert <evidence-commit>
git revert <implementation-commit>
git push origin main
```

Do not rewrite published `main` history solely to remove an evidence process. A replacement process should supersede this record.

### Rebuild procedure

1. Restore the six implementation files from Git.
2. Confirm the SAGE standard and template exist.
3. Run Python compilation.
4. Run the isolated self-test.
5. Generate a synthetic or real package using schema `1.0`.
6. Run `check`.
7. Publish to an approved branch or temporary remote.
8. Confirm separate commits, checksum, publication manifest, push, and final status.

### Data durability and backup impact

- The publisher writes only repository files and Git history.
- Evidence artifacts inherit repository backup and GitHub retention.
- Package ZIPs in `~/Downloads` are transient and may be deleted after verified publication.
- Raw evidence too large for Git requires a future external artifact-store policy.
- Reverting implementation does not automatically delete historical evidence records.

## Operational considerations and observability

### Health signals

- `python3 -m py_compile scripts/sage/sage-publish.py`
- `python3 scripts/sage/sage-publish.py self-test`
- `SAGE package validation: PASS`
- full implementation and evidence SHAs in publisher output;
- final record checksum path;
- `Published to: origin/main`;
- clean or explicitly reported nonclean working-tree state;
- Git log showing implementation followed by evidence;
- publication manifest under the evidence ID directory.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3

python3 -m py_compile scripts/sage/sage-publish.py
python3 scripts/sage/sage-publish.py self-test

git log -2 --oneline --decorate
git status
```

### Capacity, performance, and cost impact

- **Capacity:** Temporary extraction and self-test repositories use local disk and are removed automatically.
- **Performance:** Validation is linear in package file count and size; packages are capped at 500 files and 500 MiB uncompressed.
- **Cost:** No direct cloud or software-license cost is introduced.
- **Sustainability/power:** Negligible compared with the engineering session; no cluster workload is required for publication.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Real Kalaxy3 publication output for this process is not available until the operator runs the package. | `AC-012` remains partial inside the generated package. | Don Buddenbaum | immediate publication |
| `GAP-002` | limitation | The publisher validates structure and references, not technical truth. | A polished but unsupported claim could still pass. | Reviewer | every review |
| `GAP-003` | limitation | Front-matter parsing handles required top-level scalar fields rather than full YAML semantics. | Complex YAML errors outside checked fields may not be detected. | Process owner | template or parser change |
| `GAP-004` | risk | Secret scanning is pattern-based. | Encoded or unusual secrets may escape detection. | Security owner | pattern escape or incident |
| `GAP-005` | evidence-gap | Rejection paths are source-reviewed but not all have independent fault-injection tests. | Regression in a rare rejection path may go unnoticed. | Process owner | test-suite expansion |
| `GAP-006` | evidence-gap | Remote-race SHA repair is implemented but not exercised by the initial self-test. | A future Git behavior change could affect repair. | Process owner | add concurrent-remote integration test |
| `GAP-007` | limitation | The process requires exact implementation paths in the generated manifest. | Generator mistakes can omit a related file and cause publication failure or incomplete lineage. | Evidence generator | every session |
| `GAP-008` | limitation | ZIP payloads above 500 MiB or 500 entries are rejected. | Very large evidence sets require external storage. | Architecture owner | large benchmark or image evidence |
| `GAP-009` | risk | Evidence-only mode defaults to current `HEAD` when no explicit implementation commit is supplied. | Lineage may be too broad for a verification-only session. | Evidence generator | every evidence-only package |
| `GAP-010` | governance gap | Reviewer acceptance is pending. | Record remains `validated`, not `accepted`. | Kalaxy3 architecture | review event |
| `GAP-011` | limitation | The process is repository-specific. | It cannot be reused unchanged for another project. | Architecture owner | cross-project adoption |
| `GAP-012` | operational risk | A push authentication failure leaves valid local commits. | Operator must avoid regenerating a duplicate package and should complete the existing push. | Operator | push failure |

## Troubleshooting

### `SAGE publication failed: Git index already contains staged changes`

**Meaning**

The publisher will not mix preexisting staged work with manifest-controlled commits.

**Checks**

```bash
git diff --cached --name-status
```

**Recovery**

Commit the existing work, or unstage it deliberately:

```bash
git restore --staged -- <paths>
```

### `No implementation changes found for split publication`

**Meaning**

The manifest declares an implementation commit, but the listed files are already committed or unchanged.

**Checks**

```bash
git status --short -- <implementation paths>
git diff -- <implementation paths>
```

**Recovery**

Do not force a duplicate publication. Generate an evidence-only package when documenting an existing implementation, or generate a new split package after real changes.

### Payload checksum mismatch

**Meaning**

The ZIP content does not match the generator's manifest.

**Checks**

```bash
python3 scripts/sage/sage-publish.py check <package.zip>
```

**Recovery**

Regenerate the complete ZIP. Do not manually edit files inside the package without rebuilding all file hashes.

### Record is missing a required section

**Meaning**

The generated record does not follow the repository template order.

**Checks**

Compare the record with:

```text
markdown/templates/sage-evidence-record-template.md
```

**Recovery**

Regenerate the package using the canonical SAGE request. Do not remove the validation gate.

### Potential secret found

**Meaning**

A high-confidence secret pattern was detected.

**Checks**

Inspect the named packaged file outside Git.

**Recovery**

Redact the value, document the omission, rebuild the package hashes, and rerun `check`.

### Push failed after local commits

**Meaning**

The implementation and evidence commits may already be correct locally.

**Checks**

```bash
git log -2 --oneline --decorate
git status
git fetch origin
git log --oneline --left-right HEAD...origin/main
```

**Recovery**

Repair authentication or resolve remote state. Avoid generating and publishing a second package until the existing local commits are handled.

## Freshness, revalidation, and supersession

### Revalidate when

- the SAGE evidence-record standard changes;
- the SAGE template changes;
- package schema `1.0` changes;
- required front matter or headings change;
- repository categories or evidence-artifact layout change;
- `main` branch policy changes;
- commit signing becomes mandatory;
- Git rebase or push policy changes;
- Python or macOS/Linux behavior affects ZIP, subprocess, temporary-directory, or file-mode handling;
- secret-detection policy changes;
- a package is incorrectly accepted or rejected;
- the remote-race path fails;
- a generated record passes structurally but reveals a recurring semantic-quality gap;
- a newer accepted SAGE publication process supersedes this implementation.

### Scheduled review

```text
Event-based, with an annual self-test and process review if no triggering change occurs.
```

### Supersession rule

When this process is replaced:

1. preserve `SAGE-K3-GOVERNANCE-20260725-001` permanently;
2. set this record to `superseded`;
3. populate `superseded_by` with the new evidence ID;
4. retain the self-test artifact and implementation checksums;
5. identify whether package schema, record validation, Git workflow, or all three changed;
6. provide migration guidance for unpublished packages created under schema `1.0`.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Status accurately reflects technical validation and pending review.
- [x] Owner, author/operator, and reviewer state are identified.
- [x] Five Ws and How are complete.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is injected by the publisher before the evidence commit.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed or variable prior publication paths are separated from the accepted process.
- [x] Repeatability is proven through isolated self-test.

### Safety and operations

- [x] Secrets and sensitive data are excluded or synthetically replaced.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback and rebuild are documented.
- [x] Operational health checks are documented.
- [x] Known limitations and evidence gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | pending | pending | Confirm this as the required publication path for future Kalaxy3 working sessions. |
| Reviewer | pending | pending | pending | Review package contract, Git safety, validation boundaries, and remaining test gaps. |

## Git review and publication

### Normal future session

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/<generated-sage-package>.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/<generated-sage-package>.zip \
  --push
```

### This process bootstrap

```bash
cd ~/Downloads

shasum -a 256 -c \
  kalaxy3-sage-publication-process.zip.sha256

cd ~/dvlp/Kalaxy3

unzip -o \
  ~/Downloads/kalaxy3-sage-publication-process.zip

chmod +x scripts/sage/sage-publish.py

python3 -c 'compile(open("scripts/sage/sage-publish.py", encoding="utf-8").read(), "scripts/sage/sage-publish.py", "exec")'
python3 scripts/sage/sage-publish.py self-test

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-sage-publication-process-evidence.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-sage-publication-process-evidence.zip \
  --push
```

After successful publication:

```bash
git status
git log -2 --oneline --decorate
```

## Appendices and linked raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Evidence record | `markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md` | generated by publisher | internal process metadata; no secrets | Git history |
| Self-test output | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/self-test-output.txt` | listed in package and publication manifests | synthetic commit SHAs only | Git history |
| Implementation file checksums | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/implementation-file-checksums.sha256` | self-verifying inventory | none | Git history |
| Publication manifest | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-001/publication-manifest.json` | generated by publisher | repository paths and hashes; no secrets | Git history |
| Bootstrap ZIP | local download | external download integrity | none | delete after publication |
| Evidence package ZIP | local download | payload hashes in manifest | internal process metadata; no secrets | delete after publication or archive externally |

### Canonical package tree

```text
sage-package.json
payload/
├── markdown/
│   ├── operations/
│   │   └── <record>.md
│   └── evidence-artifacts/
│       └── <evidence-id>/
│           └── <raw artifacts>
```

### Canonical operator promise

For future Kalaxy3 sessions, the operator should not have to reconstruct the publication sequence. The expected interaction is:

```text
User:
Generate the SAGE evidence package for the most recent Kalaxy3 working session
using the SAGE standard, SAGE template, and SAGE publication process.

Assistant:
- generates one compliant ZIP;
- provides the standard check command;
- provides the standard publish --push command;
- does not invent a different Git workflow.
```
