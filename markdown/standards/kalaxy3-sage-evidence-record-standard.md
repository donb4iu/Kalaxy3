---
title: Kalaxy3 SAGE Evidence Record Standard
project: Kalaxy3
record_type: governance-standard
schema_version: "1.2"
status: proposed
created_at: 2026-07-24T23:45:00-05:00
updated_at: 2026-07-25T18:30:00-05:00
valid_as_of: 2026-07-25
owner: Kalaxy3 architecture
intended_path: markdown/standards/kalaxy3-sage-evidence-record-standard.md
companion_template: markdown/templates/sage-evidence-record-template.md
metadata_contract: markdown/standards/sage-evidence-metadata-contract-v1.2.json
publication_process: markdown/standards/kalaxy3-sage-evidence-publication-process.md
indexer: scripts/sage/sage-index.py
legacy_registry: markdown/evidence/legacy-record-registry.json
---

# Kalaxy3 SAGE Evidence Record Standard

## Purpose

**SAGE** means **Systems Architecture & Governance through Evidence**.

A SAGE record preserves the final technical claim, implementation lineage,
direct observations, failed paths, limitations, rebuild instructions,
operational consequences, and revalidation rules for Kalaxy3. It must be usable
by a future operator, reviewer, documentation reader, automation, and LLM
without depending on the original chat session.

The words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and
**MAY** are normative.

## Authoritative representations

Every current SAGE record has four complementary representations:

1. **YAML front matter** — authoritative machine-readable metadata.
2. **Record metadata table** — exact human-readable mirror of front matter.
3. **Five Ws and How** — explanatory context that cannot redefine metadata.
4. **Evidence items** — direct observations, repository evidence, artifacts,
   negative evidence, assumptions, and derived conclusions.

The machine-readable metadata contract is:

```text
markdown/standards/sage-evidence-metadata-contract-v1.2.json
```

The publisher MUST reject missing, renamed, extra, reordered, malformed, or
inconsistent current metadata.

## Schema 1.2 canonical front matter

All schema 1.2 records MUST use these top-level fields in this exact order:

1. `evidence_id`
2. `schema_version`
3. `title`
4. `nav_title`
5. `nav_section`
6. `nav_order`
7. `summary`
8. `primary_subject`
9. `project`
10. `record_type`
11. `status`
12. `classification`
13. `work_session`
14. `work_started_at`
15. `work_completed_at`
16. `evidence_collected_at`
17. `created_at`
18. `updated_at`
19. `valid_as_of`
20. `review_due`
21. `local_timezone`
22. `system_timestamp_timezones`
23. `owner`
24. `author`
25. `operator`
26. `reviewer`
27. `environment`
28. `system`
29. `cluster`
30. `execution_host`
31. `controller_host`
32. `nodes`
33. `node_addresses`
34. `namespaces`
35. `endpoints`
36. `components`
37. `repository`
38. `branch`
39. `implementation_commit`
40. `record_path`
41. `artifact_root`
42. `confidence`
43. `tags`
44. `relationships`

Additional top-level fields are prohibited until the standard, JSON contract,
template, publisher, and self-test are updated together.

## Core metadata rules

| Field | Requirement |
|---|---|
| `evidence_id` | Permanent `SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>` identifier. |
| `schema_version` | Exactly `"1.2"`. |
| `project` and `system` | Exactly `Kalaxy3`. |
| `repository` | Exactly `donb4iu/Kalaxy3`. |
| `branch` | Target branch, normally `main`. |
| `record_path` | Repository-relative Markdown path declared by the package. |
| `artifact_root` | Exactly `markdown/evidence-artifacts/<evidence_id>`. |
| timestamps | RFC3339 with numeric UTC offset. |
| `local_timezone` | IANA timezone name, normally `America/Chicago`. |
| system timestamp zones | IANA timezone names or `UTC`; separate from local time. |
| unavailable values | Only `not-applicable`, `not-captured`, or `pending`. |
| node addresses | `node-name=address`; each node name must exist in `nodes`. |
| endpoints | `purpose=address-or-hostname`. |
| components | `component=exact-version` or `component=version-not-captured`. |
| implementation commit | Full 40-character SHA after publication or `not-applicable`. |
| reviewer | Named reviewer for `accepted`; `pending` is allowed before acceptance. |

`validated` and `accepted` records require captured completion and evidence
collection timestamps. `accepted` requires a named reviewer. `confidence:
unknown` is allowed only for `draft`.

## Navigation and discovery contract

SAGE evidence is a human knowledge base as well as an evidence store. Search
alone is insufficient. Every schema 1.2 record MUST provide:

| Field | Requirement |
|---|---|
| `title` | Formal evidentiary title. It may be long enough to be precise. |
| `nav_title` | Plain-language sidebar/index label, 1–80 characters. It identifies the component and outcome. |
| `nav_section` | One of `installation`, `operations`, `architecture`, `decisions`, `finops`, `governance`, `security`, `incidents`, `experiments`, `benchmarks`, `verification`, or `other`. |
| `nav_order` | Integer `0` through `9999`; lower values sort first within a section. |
| `summary` | Single-line 20–360 character explanation of why a human should open the record. |
| `primary_subject` | Primary component, node, system, or capability used for subject indexes. |

The formal title and navigation title intentionally serve different purposes.
For example:

```yaml
title: AMD64 Node Addition and Longhorn Storage Installation Evidence
nav_title: Add amd64-01 and Longhorn storage
nav_section: installation
nav_order: 320
summary: Documents adding amd64-01, provisioning its dedicated disk, and validating Longhorn persistent storage.
primary_subject: Longhorn
```

The publisher MUST reject duplicate current `nav_title` values within the same
`nav_section`.

Every current record MUST contain an explicit `[TOC]` marker after the executive
summary. Mandatory H2 headings provide stable page anchors for Daux.io, MkDocs,
and other renderers.

## Canonical Record metadata table

The Record metadata table MUST contain the exact rows and order defined in the
JSON metadata contract. Every value MUST equal the canonical front-matter value.
Lists are joined with semicolon-space (`; `). Timestamps and commit SHAs are not
reformatted or shortened.

## Five Ws and How

The exact rows are:

```text
Who
What
When
Where
Why
How
```

- **Who** identifies author, operator, owner, reviewer, and affected parties.
- **What** states the final bounded change, decision, failure, or verification.
- **When** repeats canonical completion, collection, timezone, validity, and
  review facts and explains local/UTC differences.
- **Where** repeats canonical environment, hosts, nodes, addresses, namespaces,
  endpoints, and record path.
- **Why** explains problem, alternatives, tradeoffs, expected value, and risk.
- **How** explains implementation, source files, validation, artifacts,
  rollback, rebuild, and troubleshooting.

The Five Ws may add explanation but MUST NOT conflict with canonical metadata.

## Mandatory section order

Schema 1.2 records MUST include these H2 sections in order:

1. Executive summary
2. Record metadata
3. Five Ws and How
4. Scope and boundaries
5. Final accepted state
6. Claims and evidence matrix
7. Problem and decision rationale
8. Architecture or change description
9. Source of truth and implementation lineage
10. Prerequisites and assumptions
11. Implementation procedure
12. Evidence items
13. Verification and acceptance criteria
14. Idempotency and repeatability
15. Security, privacy, and evidence handling
16. Reliability, recovery, rollback, and rebuild
17. Operational considerations and observability
18. Known limitations, evidence gaps, and risks
19. Troubleshooting
20. Freshness, revalidation, and supersession
21. Final completion checklist
22. Git review and publication
23. Appendices

Additional H2 sections MAY be added only when they do not change the required
order or duplicate a canonical purpose.

## Claims and evidence

- Claims MUST be atomic and testable.
- Every critical configuration claim requires direct or generated evidence and
  repository evidence when repository state is material.
- Evidence items MUST identify collector, time, source, target, tool/version,
  expected result, actual result, confidence, sensitivity, and artifact.
- Direct observations, repository evidence, generated artifacts, negative
  evidence, assumptions, plans, and derived conclusions MUST be distinguished.
- Failed attempts that materially explain the accepted design MUST be retained
  separately from final state.
- Assumptions and plans cannot prove an observed claim.
- Every `not-captured` value requires an explicit evidence gap.

## Lifecycle

Allowed current statuses are:

```text
draft
implemented
validated
accepted
superseded
retired
rejected
```

`validated` means technical acceptance criteria passed. `accepted` additionally
means governance review completed. A score or checklist cannot override status.

## Historical evidence compatibility

Adopting a newer schema MUST NOT make historical evidence undiscoverable,
unpublished, invalid, or disposable merely because it predates the schema.

The reconciliation process classifies records as:

| Record class | Definition | Behavior |
|---|---|---|
| `sage-current` | Fully conforms to schema 1.2. | Strict validation; errors block publication. |
| `sage-legacy` | Contains a SAGE ID but uses an earlier schema. | Preserved and indexed with compatibility warnings. |
| `legacy-evidence` | Pre-SAGE or nonconforming Markdown identified as evidence. | Preserved and indexed with curated or explicitly inferred metadata. |

Historical source files MUST NOT be silently rewritten by the indexer or
publisher. Curated compatibility metadata belongs in:

```text
markdown/evidence/legacy-record-registry.json
```

The registry may define candidate roots, explicit exclusions, navigation
labels, summaries, dates, subjects, and migration state. Inferred metadata is a
discovery aid; it is not evidence that the historical document contained that
fact.

Pre-SAGE records receive a deterministic identifier based on the repository
path:

```text
LEGACY-K3-<10-CHARACTER-PATH-HASH>
```

Migration to current SAGE creates a new SAGE evidence ID, links the historical
identifier through relationships, and preserves the original file and Git
history. Migration MUST be deliberate and reviewed. Automation MUST NOT invent
missing commits, operators, reviewers, dates, test results, or acceptance.

## Generated catalog and reconciliation

Every SAGE publication MUST reconcile all current and historical evidence and
generate:

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

The Markdown views support humans and documentation renderers. JSON supports
machine and LLM discovery. CSV supports review and analysis. Generated files
MUST be deterministic from repository content and registry data. Only paths
previously declared in `generated-files.json` may be removed as stale.

The catalog MUST:

- include every discovered current, legacy SAGE, and pre-SAGE evidence record;
- identify metadata provenance as authoritative, curated, or inferred;
- preserve source paths and stable IDs;
- expose section, subject, status, validity, migration state, and summary;
- reject duplicate permanent IDs;
- reject duplicate current navigation titles within one section;
- produce migration warnings without hiding records;
- fail its check command when committed generated files are stale.

## Security and privacy

Records and artifacts MUST exclude credentials, private keys, bearer tokens,
Kubernetes Secret values, billing account identifiers, and unnecessary personal
information. Internal IPs, node names, namespaces, and cost values require an
appropriate classification. Network evidence should preserve counters and
labels, not packet payloads, unless separately authorized.

## Rollback, rebuild, and operations

Every record MUST document rollback, rebuild, health checks, failure modes,
troubleshooting, data durability, and revalidation triggers whenever applicable.
An idempotency proof or explicit not-applicable rationale is required.

## Migration from schemas 1.0 and 1.1

Existing records remain valid historical artifacts. They are not templates for
new work. When a legacy record is materially modified or revalidated:

1. preserve the original record and Git history;
2. create or curate a compatibility registry entry if needed;
3. review source evidence rather than inventing missing facts;
4. create a schema 1.2 record with a new permanent SAGE ID when migration is
   justified;
5. link old and new identifiers through relationships;
6. regenerate the evidence catalog;
7. complete technical and governance review appropriate to the new status.

## Completion rule

All newly generated Kalaxy3 SAGE evidence packages MUST use schema 1.2, the
canonical metadata contract, the schema 1.2 template, the publication process,
and the repository publisher. Historical records remain published through the
compatibility catalog until deliberately migrated or explicitly retired.
