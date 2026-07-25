---
evidence_id: SAGE-K3-GOVERNANCE-20260725-002
schema_version: "1.1"
title: Canonical SAGE metadata contract and publisher enforcement
project: Kalaxy3
record_type: operations
status: validated
classification: internal
work_session: Standardize SAGE record metadata
work_started_at: not-captured
work_completed_at: 2026-07-25T17:45:00-05:00
evidence_collected_at: 2026-07-25T17:46:00-05:00
created_at: 2026-07-25T17:46:00-05:00
updated_at: 2026-07-25T17:56:05-05:00
valid_as_of: 2026-07-25
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - UTC
owner: Don Buddenbaum
author: ChatGPT
operator: ChatGPT
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: not-applicable
execution_host: ChatGPT-artifact-runtime
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
  - SAGE-record-schema=1.1
  - SAGE-package-schema=1.1
  - Python=3.13.5
  - Git=2.47.3
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: f82b17f36be20fa54cacb850e82f3fdd65e1e48d
record_path: markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002
confidence: high
tags:
  - sage
  - governance
  - metadata
  - evidence
  - publication
  - validation
relationships:
  verifies:
    - Canonical SAGE metadata consistency
    - Publisher enforcement of schema 1.1
  depends_on:
    - SAGE-K3-GOVERNANCE-20260725-001
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
  supersedes:
    - Schema 1.0 metadata guidance for newly generated records
  superseded_by:
    - none
  related_to:
    - SAGE-K3-FINOPS-20260724-001
  conflicts_with:
    - none
  generated_by:
    - ChatGPT artifact generation
    - scripts/sage/sage-publish.py self-test
  implemented_by:
    - f82b17f36be20fa54cacb850e82f3fdd65e1e48d
  revalidated_by:
    - none
---

# Canonical SAGE metadata contract and publisher enforcement

## Executive summary

Kalaxy3 SAGE metadata is now defined by a schema 1.1 machine-readable contract,
a matching record standard and template, and publisher validation that rejects
missing, extra, reordered, renamed, or inconsistent metadata. Every new record
must contain an exact YAML field set, an exact human-readable Record metadata
table, normalized timestamps, timezones, node/address pairs, endpoints, and
component versions, followed by Five Ws and How that explain but do not redefine
the canonical facts. The updated publisher passed an isolated two-commit Git
publication self-test and left the temporary repository clean.

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GOVERNANCE-20260725-002 |
| **Schema version** | 1.1 |
| **Project** | Kalaxy3 |
| **Title** | Canonical SAGE metadata contract and publisher enforcement |
| **Record type** | operations |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Standardize SAGE record metadata |
| **Started** | not-captured |
| **Completed** | 2026-07-25T17:45:00-05:00 |
| **Evidence collected** | 2026-07-25T17:46:00-05:00 |
| **Record created** | 2026-07-25T17:46:00-05:00 |
| **Record updated** | 2026-07-25T17:56:05-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | UTC |
| **Valid as of** | 2026-07-25 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | f82b17f36be20fa54cacb850e82f3fdd65e1e48d |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | not-applicable |
| **Execution host** | ChatGPT-artifact-runtime |
| **Controller host** | not-applicable |
| **Nodes** | not-applicable |
| **Node addresses** | not-applicable |
| **Namespaces** | not-applicable |
| **Endpoints** | not-applicable |
| **Components and versions** | SAGE-record-schema=1.1; SAGE-package-schema=1.1; Python=3.13.5; Git=2.47.3 |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT |
| **Operator** | ChatGPT |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author ChatGPT and operator ChatGPT implemented and tested the update for owner Don Buddenbaum; reviewer pending remains a governance step. |
| **What** | The SAGE standard, template, metadata contract, generation request, package manifest, publication process, and publisher were revised so static metadata is identical across newly generated records. |
| **When** | Completed 2026-07-25T17:45:00-05:00; evidence collected 2026-07-25T17:46:00-05:00; local timezone America/Chicago; system timestamps UTC; valid as of 2026-07-25; review due event-based. |
| **Where** | Environment homelab; cluster not-applicable; execution host ChatGPT-artifact-runtime; controller not-applicable; record markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md. The implementation targets the Kalaxy3 repository governance and publisher files rather than a Kubernetes runtime target. |
| **Why** | Existing evidence records used strong narrative evidence but varied in header labels, timestamp meanings, target representation, and version formatting. A mandatory canonical metadata block and executable validation are required to prevent future drift. |
| **How** | A JSON metadata contract defines exact fields and row order; the Markdown standard and template adopt it; the publisher parses the constrained front matter, validates formats and cross-field relationships, mirrors values into the metadata table, checks Five-W consistency, and executes an isolated Git publication self-test. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- SAGE record schema 1.1.
- Exact front-matter names and order.
- Timestamp and timezone semantics.
- Human-readable Record metadata table.
- Node/address, endpoint, and component/version normalization.
- Five-W consistency with canonical metadata.
- Package manifest schema 1.1.
- Publisher validation and publication-manifest hashes.
- Self-test coverage for the updated contract.

### Out of scope

- Automatic migration of every historical schema 1.0 record.
- Verification of the factual truth of arbitrary evidence content.
- Replacement of independent reviewer judgment.
- Kubernetes runtime changes.

### Nonclaims

This record does **not** claim:

- that every historical Kalaxy3 evidence record already conforms to schema 1.1;
- that structural validation proves all factual statements;
- that a static metadata table is a substitute for direct evidence;
- that the Five Ws are unnecessary once metadata is canonical.

## Final accepted state

```text
New-record schema:         1.1
Package schema:            1.1
Front-matter fields:       exact and ordered
Static metadata table:     mandatory and value-mirrored
Five-W rows:               exact and consistency-checked
Unavailable vocabulary:   not-applicable, not-captured, pending
Local timezone format:     IANA name
Canonical timestamp:       RFC3339 with numeric offset
Component format:          component=version
Node address format:       node=address
Endpoint format:           purpose=value
Publisher self-test:       PASS
Git publication pattern:   implementation commit + evidence commit
```

| Item | Accepted result |
|---|---|
| Metadata authority | YAML front matter is authoritative; the Record metadata table is its deterministic human-readable mirror. |
| Explanatory evidence | Five Ws and How explain the canonical metadata and may not redefine it. |
| Enforcement | The publisher rejects field-order drift, row drift, value mismatch, malformed timestamps, malformed relationships, and unresolved template markers. |
| Historical records | Schema 1.0 records remain historical and migrate when modified, revalidated, or superseded. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Schema 1.1 defines one exact canonical metadata field set and order. | critical | `EV-001`, `EV-002` | supported | high |
| `CLM-002` | The Record metadata table is validated against front matter field by field. | critical | `EV-001`, `EV-003` | supported | high |
| `CLM-003` | The publisher rejects malformed timestamps, timezones, component versions, node addresses, and endpoints. | high | `EV-001`, `EV-003` | supported | high |
| `CLM-004` | The Five Ws remain mandatory and are checked for consistency with canonical metadata. | high | `EV-001`, `EV-003` | supported | high |
| `CLM-005` | The updated publisher completes an isolated split publication and push. | critical | `EV-004`, `EV-005` | supported | high |
| `CLM-006` | Historical schema 1.0 records are preserved and migrated only when materially updated. | normal | `EV-002` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The schema 1.0 standard required front matter but did not define an exact field
set, exact field order, exact timestamp semantics, or an exact human-readable
metadata block. As a result, one record might use a compact static header while
another relied on a longer front matter list and Five-W prose. Both could be
technically useful yet differ in labels such as `Completed`, target path,
component versions, node addresses, and system timestamps.

### Decision

Adopt schema 1.1 with a machine-readable metadata contract and enforce it in the
repository publisher. Preserve both canonical metadata and Five-W explanatory
evidence.

### Decision drivers

- Consistent human scanning across records.
- Machine indexing and future lineage-graph ingestion.
- Unambiguous work, evidence, record, and validity timestamps.
- Explicit local versus UTC/system timestamp handling.
- Stable target and version representation.
- Automated rejection rather than style guidance alone.
- Incremental preservation of historical records.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Keep Five Ws only | Rich context | Static facts remain differently formatted and hard to compare | rejected |
| Keep informal static headers only | Concise and familiar | Does not capture rationale, ownership, evidence boundaries, or reproducibility | rejected |
| Recommend a static table without validation | Easy to adopt | Drift continues because recommendations are not publication gates | rejected |
| Define canonical front matter and exact mirrored table, then enforce it | Consistent for humans and automation while preserving context | More fields and a schema migration boundary | accepted |
| Rewrite all historical records immediately | Uniform repository appearance | High churn and risk of altering historical evidence | rejected |

### Tradeoffs and consequences

- New records are longer at the top, but materially easier to compare.
- The publisher is stricter and may reject packages that previously passed.
- Record generators must use exact values rather than stylistic variants.
- Historical schema 1.0 evidence remains valid but cannot be used as the new
  template.
- Process updates that replace the publisher still require a reviewed bootstrap
  extraction before the new publisher can validate its own update.

## Architecture or change description

```text
working-session facts
        |
        v
schema 1.1 YAML front matter  <--- machine-readable authority
        |
        +--> exact Record metadata table  <--- human-readable mirror
        |
        +--> Five Ws and How               <--- explanation and rationale
        |
        v
claims -> evidence items -> acceptance criteria
        |
        v
sage-publish.py validation
        |
        v
implementation commit -> SHA injection -> evidence commit -> push
```

### Before

The standard listed common front-matter fields and required Five Ws, but record
generators could choose different static header labels, omit target detail, use
free-form component strings, or blur completion time with record creation time.

### After

The contract defines and the publisher enforces exact field names, order,
values, static rows, list formats, timestamp semantics, and Five-W consistency.

## Source of truth and implementation lineage

### Repository files

```text
scripts/sage/sage-publish.py
scripts/sage/README.md
scripts/sage/.gitignore
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.1.json
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-record-template.md
markdown/templates/sage-evidence-generation-request.md
markdown/templates/sage-evidence-package-manifest-template.json
```

### Implementation commit

```text
f82b17f36be20fa54cacb850e82f3fdd65e1e48d
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE record schema | 1.1 | metadata contract and standard |
| SAGE package schema | 1.1 | manifest template and publisher |
| Python | 3.13.5 | artifact runtime observation |
| Git | 2.47.3 | artifact runtime observation |

### Configuration excerpt

```json
{
  "record_schema_version": "1.1",
  "canonical_list_separator": "; ",
  "timestamp_format": "RFC3339 with numeric UTC offset",
  "timezone_format": "IANA timezone name or UTC"
}
```

## Prerequisites and assumptions

### Proven prerequisites

- The existing repository publisher and two-commit process were previously
  installed and published.
- Python standard library and Git were available for the isolated self-test.
- The current standard and template were available as the migration baseline.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Schema 1.1 fields cover the stable metadata needed by current Kalaxy3 evidence domains. | A future domain may require a new canonical field. | Version the contract and publisher together rather than adding ad hoc fields. |
| `ASM-002` | Semicolon-space is an adequate deterministic list rendering for the metadata table. | Values containing semicolons would be ambiguous. | Prohibit semicolons in canonical list items and revise the schema if needed. |

## Implementation procedure

### Preparation

The schema 1.0 standard, template, and publication process were reviewed to
identify the enforcement gap between recommended front matter and actual record
variation.

### Execution

- Added a JSON metadata contract.
- Rewrote the standard and template for schema 1.1.
- Updated the generation request and package manifest.
- Updated the publication process.
- Extended the publisher parser and validation gates.
- Updated publication-manifest hashing.
- Updated the isolated self-test to generate a complete schema 1.1 record.

### Expected change

The publisher should accept a canonical schema 1.1 record, create two commits,
inject the implementation SHA, generate checksums and a publication manifest,
push to a temporary remote, and leave the tree clean.

### Observed change

The isolated self-test completed successfully and reported a clean working tree.

### Failed or superseded paths

A purely descriptive requirement was rejected because it would not prevent
future generators from choosing alternate labels or formats. The accepted
implementation makes metadata conformance executable.

## Evidence items

### `EV-001` — Machine-readable metadata contract

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003`, `CLM-004` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T17:42:00-05:00 |
| Execution source | ChatGPT-artifact-runtime |
| Target | markdown/standards/sage-evidence-metadata-contract-v1.1.json |
| Tool and version | Python=3.13.5 |
| Expected result | Exact field order, rows, lists, and format contract |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | implementation file and implementation-file-checksums.sha256 |

**Command, query, source, or observation**

```text
Review the JSON contract and compare it with publisher constants.
```

**Observed result**

```text
39 canonical top-level fields
37 canonical Record metadata rows
6 canonical Five-W rows
```

**Interpretation**

The contract provides a stable machine-readable definition. It does not itself
enforce conformance without the publisher.

### `EV-002` — Standard and template revision

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-004`, `CLM-006` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T17:42:00-05:00 |
| Execution source | ChatGPT-artifact-runtime |
| Target | SAGE standard and template |
| Tool and version | Markdown=1.1-contract |
| Expected result | Exact metadata and migration requirements documented |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | implementation files and checksums |

**Command, query, source, or observation**

```text
Compare schema 1.1 standard and template with the metadata contract.
```

**Observed result**

```text
The standard and template contain the same field order, row order, timestamp
rules, canonical unavailable values, and migration boundary.
```

**Interpretation**

The documents make the contract usable by humans and generators.

### `EV-003` — Publisher contract enforcement

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T17:42:00-05:00 |
| Execution source | ChatGPT-artifact-runtime |
| Target | scripts/sage/sage-publish.py |
| Tool and version | Python=3.13.5 |
| Expected result | Publisher rejects metadata drift and contract mismatch |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | implementation file and checksum |

**Command, query, source, or observation**

```bash
python3 -m py_compile scripts/sage/sage-publish.py
```

**Observed result**

```text
Compilation succeeded.
```

**Interpretation**

Compilation proves syntax validity. Runtime behavior is separately proven by
`EV-004`.

### `EV-004` — Isolated publication self-test

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-005` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T17:42:00-05:00 |
| Execution source | ChatGPT-artifact-runtime |
| Target | Temporary Git working repository and bare remote |
| Tool and version | Python=3.13.5; Git=2.47.3 |
| Expected result | Separate commits, successful push, final clean tree, PASS |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/self-test-output.txt |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-publish.py self-test
```

**Observed result**

```text
Publication completed with a clean working tree.
SAGE publication self-test: PASS
```

**Interpretation**

The test proves the complete isolated schema 1.1 publication path. It does not
prove the truth of future session evidence.


### `EV-005` — Bootstrap and real package publication test

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-005` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25T17:45:00-05:00 |
| Execution source | ChatGPT-artifact-runtime |
| Target | Temporary legacy-style repository upgraded by the bootstrap package |
| Tool and version | Python=3.13.5; Git=2.47.3 |
| Expected result | Bootstrap files become one implementation commit; evidence becomes a second commit; push succeeds; tree is clean |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/package-publication-test-output.txt |

**Command, query, source, or observation**

```text
Install the bootstrap files into a temporary repository containing legacy
placeholders, then publish the actual schema 1.1 evidence package with --push.
```

**Observed result**

```text
Publication completed with a clean working tree.
Implementation commit: created
Evidence commit: created
Published to: origin/main
Final working tree: clean
```

**Interpretation**

This test proves the reviewed bootstrap-plus-publication transition path, not
only the publisher's internal synthetic self-test.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Exact metadata contract exists | `EV-001` | JSON field and row definitions | observed | pass |
| `AC-002` | Standard and template agree with contract | `EV-001`, `EV-002` | identical schema semantics | observed | pass |
| `AC-003` | Publisher enforces contract | `EV-003` | parse and validation functions present | observed | pass |
| `AC-004` | Publisher code compiles | `EV-003` | zero syntax errors | observed | pass |
| `AC-005` | Full split publication works | `EV-004`, `EV-005` | two commits, push, clean tree | observed | pass |
| `AC-006` | Historical records are preserved | `EV-002` | migration guidance, no mass rewrite | observed | pass |

### Functional verification

```bash
python3 scripts/sage/sage-publish.py self-test
```

Observed:

```text
SAGE publication self-test: PASS
```

### Negative verification

The publisher includes explicit rejection paths for reordered front matter,
metadata-table mismatch, malformed timestamps, invalid timezones, malformed
`name=value` entries, unresolved markers, incomplete checklists, and package
contract drift.

## Idempotency and repeatability

### First accepted run

The isolated self-test created a fresh repository, implementation commit,
evidence commit, and push.

### Steady-state rerun

The self-test was run repeatedly against fresh temporary environments and
completed successfully without modifying Kalaxy3.

### Interpretation

The self-test is repeatable rather than an in-place idempotency test. Normal
publication remains deterministic for a package and fails if there is no split
implementation change.

## Security, privacy, and evidence handling

### Security controls

- No credentials or Kubernetes secrets are required.
- ZIP path traversal and symbolic links remain prohibited.
- Payload hashes and exact inventories remain mandatory.
- Existing secret scanning remains active.
- Contract paths and Git staging remain allowlisted.

### Sensitive material excluded

No credentials, tokens, private keys, passwords, authentication hashes, or
personal data are included.

### Redactions and omissions

None.

### Residual security risk

Structural validation cannot detect every possible secret or false statement.
Human review remains required.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Contract and publisher constants differ | `check` reports contract drift | Publication blocked | Update standard, contract, template, process, and publisher together |
| Legacy package uses schema 1.0 | Unsupported schema error | New publication blocked | Regenerate package from schema 1.1 template |
| Metadata table differs from front matter | Field-specific mismatch | Publication blocked | Regenerate the table directly from front matter |
| Invalid timestamp or timezone | Validation error names field | Publication blocked | Use RFC3339 offset and IANA timezone |
| Node/address or component entry is malformed | `name=value` validation error | Publication blocked | Normalize the list item |
| New domain needs another field | Generator tempted to add ad hoc key | Contract fragmentation | Version the contract and publisher together |

### Rollback

Revert the implementation commit and its evidence commit together, then restore
the previous publisher package schema if an emergency rollback is required.
Do not partially revert only the standard or only the publisher.

### Rebuild procedure

1. Restore the eight implementation files from Git.
2. Run `python3 -m py_compile scripts/sage/sage-publish.py`.
3. Run `python3 scripts/sage/sage-publish.py self-test`.
4. Generate a schema 1.1 test package.
5. Run `check` before any publication.

### Data durability and backup impact

No Kubernetes or application data is changed. Git history is the durable backup
for the governance files and evidence record.

## Operational considerations and observability

### Health signals

- Publisher `check` result.
- Publisher self-test result.
- Contract/publisher drift errors.
- Final Git commit and working-tree report.
- Publication manifest hashes.

### Routine verification

```bash
python3 -m py_compile scripts/sage/sage-publish.py
python3 scripts/sage/sage-publish.py self-test
```

### Capacity, performance, cost, and sustainability

- **Capacity:** Negligible repository growth.
- **Performance:** Additional validation is linear in record and package size.
- **Cost:** No direct infrastructure cost.
- **Sustainability/power:** Negligible compared with cluster workloads.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | `work_started_at` is not-captured because the exact start of this conversational design task was not preserved. | The duration of the design work cannot be calculated exactly. | Don Buddenbaum | no remediation required; capture exact start in future packages |
| `GAP-002` | limitation | The publisher parses a constrained YAML subset rather than arbitrary YAML. | Complex front-matter structures outside the contract are rejected. | Kalaxy3 architecture | contract version change |
| `GAP-003` | limitation | Structural consistency does not prove factual accuracy. | A well-formed record can still contain unsupported claims. | Reviewer | every acceptance review |
| `GAP-004` | technical-debt | Existing schema 1.0 records remain heterogeneous until materially migrated. | Repository-wide searches must understand both schemas during transition. | Kalaxy3 architecture | each record modification or revalidation |
| `GAP-005` | risk | Strict validation can block publication when a generator uses a harmless stylistic variation. | Additional regeneration may be required. | Publisher owner | monitor rejected packages |

## Troubleshooting

### Front-matter order error

**Meaning**

A field is missing, extra, renamed, or out of order.

**Checks**

Compare the record with the JSON contract and schema 1.1 template.

**Recovery**

Regenerate the entire canonical front matter rather than manually moving one
line at a time.

### Record metadata mismatch

**Meaning**

The human-readable static table no longer mirrors front matter.

**Checks**

Use the field named in the publisher error.

**Recovery**

Regenerate the table directly from the canonical front-matter values.

### Five-W consistency error

**Meaning**

Who, When, or Where omits or contradicts a canonical value.

**Checks**

Review the required exact values reported by the publisher.

**Recovery**

Explain the canonical value without reformatting or substituting another value.

## Freshness, revalidation, and supersession

### Revalidate when

- the SAGE record schema changes;
- the package schema changes;
- the metadata contract changes;
- required fields or static rows change;
- the publisher parser or validation changes;
- a new record domain needs new canonical metadata;
- a self-test or package check fails;
- the Git publication process changes.

### Scheduled review

```text
event-based, plus review before each schema version change
```

### Supersession rule

A later schema must preserve this evidence ID, identify which schema 1.1 claims
remain valid, and update the standard, template, contract, process, manifest,
publisher, and self-test together.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.1.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects completeness.
- [x] Owner, author, operator, and reviewer are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is recorded or validly not-applicable.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Idempotency or repeatability is proven or not-applicable.
- [x] Every not-captured value has an evidence gap.

### Safety and operations

- [x] Secrets and sensitive data are excluded or redacted.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback, rebuild, and data-durability impacts are documented.
- [x] Operational health checks are documented.
- [x] Known limitations and gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | pending | pending | Confirm the schema 1.1 metadata contract. |
| Reviewer | pending | pending | pending | Review strictness and migration policy. |

## Git review and publication

After the reviewed bootstrap files are extracted, publish through the updated
repository process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-sage-metadata-contract-evidence.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-sage-metadata-contract-evidence.zip \
  --push
```

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Self-test output | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/self-test-output.txt` | package manifest | no | repository history |
| Implementation checksums | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/implementation-file-checksums.sha256` | package manifest | no | repository history |
| Bootstrap publication test | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/package-publication-test-output.txt` | package manifest | no | repository history |
| Publication manifest | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260725-002/publication-manifest.json` | generated at publication | no | repository history |

### Additional notes

The bootstrap is necessary only because the publisher is one of the files being
replaced. Future ordinary working-session packages require only `check` and
`publish --push`.
