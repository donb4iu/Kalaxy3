---
title: Kalaxy3 SAGE Evidence Record Standard
project: Kalaxy3
record_type: governance-standard
schema_version: "1.1"
status: proposed
created_at: 2026-07-24T23:45:00-05:00
updated_at: 2026-07-25T17:38:00-05:00
valid_as_of: 2026-07-25
owner: Kalaxy3 architecture
intended_path: markdown/standards/kalaxy3-sage-evidence-record-standard.md
companion_template: markdown/templates/sage-evidence-record-template.md
metadata_contract: markdown/standards/sage-evidence-metadata-contract-v1.1.json
publication_process: markdown/standards/kalaxy3-sage-evidence-publication-process.md
---

# Kalaxy3 SAGE Evidence Record Standard

## SAGE meaning and purpose

**SAGE** means **Systems Architecture & Governance through Evidence**.

SAGE is the Kalaxy3 evidence-driven engineering method. It preserves decisions,
implementation state, observed verification, failed attempts, limitations,
rebuild instructions, operational consequences, and Git lineage as durable,
linked evidence.

A SAGE record must let a future operator answer:

- what state or claim is being asserted;
- who performed, owns, authored, and reviewed the work;
- when the work completed and when evidence was collected;
- where the work ran and which systems, nodes, addresses, namespaces, and
  repository paths it affected;
- why the accepted approach was selected;
- how the result can be reproduced, validated, repaired, rolled back, rebuilt,
  revalidated, or superseded;
- which direct observations and repository changes prove each claim;
- what the record does not prove.

## Normative language

The words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, and
**MAY** are normative.

- **MUST/MUST NOT** define a publication gate enforced by the SAGE publisher or
  mandatory reviewer action.
- **SHOULD/SHOULD NOT** define a strong default that may be overridden only with
  an explicit rationale.
- **MAY** identifies optional content.

## Authoritative metadata principle

Every SAGE record has two metadata representations:

1. **YAML front matter**, which is the machine-readable source of truth.
2. **Record metadata table**, which is the mandatory human-readable mirror.

The Five Ws and How are explanatory evidence. They do not replace metadata.
They must explain the significance and context of the canonical facts without
changing those facts.

The authoritative metadata contract is:

```text
markdown/standards/sage-evidence-metadata-contract-v1.1.json
```

The publisher MUST reject a new record when:

- a required front-matter field is absent;
- front-matter fields are not in canonical order;
- a field uses a noncanonical name for the same concept;
- a required list is omitted instead of using `not-applicable`;
- a timestamp does not follow the required format;
- the human-readable metadata table is absent, reordered, incomplete, or
  inconsistent with front matter;
- the Five Ws introduce conflicting dates, hosts, paths, versions, or owners.

## Metadata schema version 1.1

### Exact front-matter order

All new records MUST use these top-level fields in this exact order:

1. `evidence_id`
2. `schema_version`
3. `title`
4. `project`
5. `record_type`
6. `status`
7. `classification`
8. `work_session`
9. `work_started_at`
10. `work_completed_at`
11. `evidence_collected_at`
12. `created_at`
13. `updated_at`
14. `valid_as_of`
15. `review_due`
16. `local_timezone`
17. `system_timestamp_timezones`
18. `owner`
19. `author`
20. `operator`
21. `reviewer`
22. `environment`
23. `system`
24. `cluster`
25. `execution_host`
26. `controller_host`
27. `nodes`
28. `node_addresses`
29. `namespaces`
30. `endpoints`
31. `components`
32. `repository`
33. `branch`
34. `implementation_commit`
35. `record_path`
36. `artifact_root`
37. `confidence`
38. `tags`
39. `relationships`

Additional top-level fields are prohibited in schema 1.1 unless this standard,
the metadata contract, and the publisher are updated together. Record-specific
facts belong in evidence items, the final-state table, or artifacts rather than
new ad hoc front-matter keys.

### Field semantics

| Field | Required meaning and format |
|---|---|
| `evidence_id` | Permanent `SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>` identifier. It never changes when the file is renamed. |
| `schema_version` | Exactly `"1.1"` for records generated after adoption of this revision. |
| `title` | Concise title describing the evidenced result, not a planned task. |
| `project` | Exactly `Kalaxy3`. |
| `record_type` | One allowed lifecycle domain: `installation`, `architecture-decision`, `change`, `verification`, `incident`, `experiment`, `benchmark`, `operations`, `security`, or `finops`. |
| `status` | One allowed lifecycle status defined below. |
| `classification` | Data-handling classification, normally `internal`. |
| `work_session` | Stable short name for the working session, capability, incident, or validation run. |
| `work_started_at` | RFC3339 timestamp with numeric offset, or `not-captured` when genuinely unavailable. Never infer a start time. |
| `work_completed_at` | RFC3339 timestamp with numeric offset for the completed implementation or validation. `validated` and `accepted` records require a captured value. |
| `evidence_collected_at` | RFC3339 timestamp with numeric offset for the final material evidence capture. `validated` and `accepted` records require a captured value. |
| `created_at` | RFC3339 timestamp with numeric offset for creation of the record. |
| `updated_at` | RFC3339 timestamp with numeric offset. A package may use the publisher token until publication. |
| `valid_as_of` | `YYYY-MM-DD`, representing the date through which the final claim is known to hold. |
| `review_due` | `YYYY-MM-DD` or exactly `event-based`. Detailed triggers belong in the freshness section. |
| `local_timezone` | IANA timezone name such as `America/Chicago`; never an abbreviation such as `CST` or `CDT`. |
| `system_timestamp_timezones` | Nonempty list of timezones used by Kubernetes, APIs, logs, devices, or other evidence. Use `UTC` when applicable or `not-applicable`. |
| `owner` | Accountable person or stable role. |
| `author` | Person or automation that assembled the record. |
| `operator` | Person or automation that performed the implementation or validation. |
| `reviewer` | Named reviewer, `pending`, or `not-applicable` only when the standard permits no review. `accepted` requires a named reviewer. |
| `environment` | Canonical environment name: `homelab`, `development`, `test`, `production`, `research`, or `shared-platform`. |
| `system` | Exactly `Kalaxy3`. |
| `cluster` | Cluster name or `not-applicable`. |
| `execution_host` | Host from which the primary commands were executed, or `not-applicable`. |
| `controller_host` | Automation controller or target through which changes were applied, or `not-applicable`. |
| `nodes` | Nonempty list of node names or one item `not-applicable`. |
| `node_addresses` | Nonempty list using `node-name=address`, or one item `not-applicable`. Node names must exist in `nodes`. |
| `namespaces` | Nonempty list of Kubernetes namespaces or one item `not-applicable`. |
| `endpoints` | Nonempty list using `purpose=address-or-hostname`, or one item `not-applicable`. |
| `components` | Nonempty list using `component=version`; use `version-not-captured` only when the version is unavailable and identify the gap. |
| `repository` | Exactly `donb4iu/Kalaxy3`. |
| `branch` | Target Git branch, normally `main`. |
| `implementation_commit` | Full 40-character Git SHA, publisher token before split publication, or `not-applicable` for evidence-only records where no implementation exists. |
| `record_path` | Canonical repository-relative Markdown path. |
| `artifact_root` | Exactly `markdown/evidence-artifacts/<evidence_id>`. |
| `confidence` | `high`, `medium`, `low`, or `unknown`; `unknown` is allowed only in `draft`. |
| `tags` | Nonempty list of stable search terms. |
| `relationships` | Required lineage map using the relationship types defined below. |

### Canonical unavailable values

Use only:

- `not-applicable` when the concept does not apply;
- `not-captured` when it applied but was not recorded;
- `pending` for an unresolved governance role or action.

Do not use variants such as `N/A`, `none`, `unknown`, `TBD`, `later`, blank
strings, omitted list fields, or prose explanations in place of these values.
Any `not-captured` value MUST be represented as an evidence gap with an owner
and revalidation trigger.

### Timestamp rules

- All timestamps MUST use RFC3339 with a numeric UTC offset.
- The local timezone MUST separately use an IANA name.
- Human-friendly dates MAY appear in prose, but the canonical timestamp MUST
  also be present.
- Kubernetes and most cluster API timestamps SHOULD be recorded as `UTC` in
  `system_timestamp_timezones`.
- A local work date and a UTC system date may differ. This is not a conflict
  when both timezone contexts are explicit.
- `created_at` and `updated_at` describe the record, not the work.
- `work_completed_at` describes the implementation or validation event.
- `evidence_collected_at` describes the final material evidence capture.
- `valid_as_of` describes claim freshness and is not a substitute for a
  completion timestamp.

### Components and versions

Component versions MUST be represented in the front matter as exact list items:

```yaml
components:
  - K3s=v1.36.2+k3s1
  - Longhorn=v1.12.0
```

Do not use free-form variants such as:

```yaml
components:
  - K3s version 1.36
  - current Longhorn
```

When a version is material but unavailable:

```yaml
components:
  - Ansible=version-not-captured
```

and create an explicit evidence gap.

### Targets, addresses, namespaces, and endpoints

Targets MUST remain relational rather than split into ambiguous unlabeled
values:

```yaml
nodes:
  - amd64-01
node_addresses:
  - amd64-01=192.168.2.61
namespaces:
  - longhorn-system
endpoints:
  - kubernetes-api=https://192.168.2.50:6443
```

When the record covers several nodes, every captured address MUST identify its
node. When a node address is not material or not captured, use:

```yaml
node_addresses:
  - not-applicable
```

or:

```yaml
node_addresses:
  - amd64-01=not-captured
```

and document the gap when appropriate.

## Mandatory record metadata table

Every record MUST contain `## Record metadata` immediately after the executive
summary and before `## Five Ws and How`.

The table is a deterministic mirror of front matter. It MUST use the exact row
names and exact row order defined in the metadata contract. List values MUST be
joined using semicolon-space (`; `). Values MUST be identical to front matter;
no date reformatting, abbreviations, alternate hostnames, or shortened commit
SHAs are allowed.

Example:

```markdown
## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-STORAGE-20260719-001 |
| **Schema version** | 1.1 |
| **Project** | Kalaxy3 |
| **Title** | AMD64 node and Longhorn installation |
| **Record type** | installation |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Add amd64-01 and Longhorn storage |
| **Started** | not-captured |
| **Completed** | 2026-07-19T21:30:00-05:00 |
| **Evidence collected** | 2026-07-19T22:15:00-05:00 |
| **Record created** | 2026-07-19T22:30:00-05:00 |
| **Record updated** | 2026-07-19T22:30:00-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | UTC |
| **Valid as of** | 2026-07-19 |
| **Review due** | event-based |
| **Target record path** | markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-STORAGE-20260719-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | pending |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donb-mac-mini |
| **Controller host** | arm64-01 |
| **Nodes** | amd64-01 |
| **Node addresses** | amd64-01=192.168.2.61 |
| **Namespaces** | longhorn-system |
| **Endpoints** | kubernetes-api=https://192.168.2.50:6443 |
| **Components and versions** | K3s=v1.36.2+k3s1; Longhorn=v1.12.0 |
| **Owner** | Don Buddenbaum |
| **Author** | Don Buddenbaum |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |
```

This table replaces informal, record-specific static headers. A record MAY add
a concise final-state table later, but it MUST NOT create a competing metadata
header with different labels or values.

## Mandatory Five Ws and How

Every record MUST include the exact six table rows in this order:

1. Who
2. What
3. When
4. Where
5. Why
6. How

The Five Ws and How MUST use the canonical metadata rather than restating it
in a different format.

| Requirement | Required explanatory content |
|---|---|
| **Who** | Explain author, evidence collector, operator, owner, reviewer, and affected users. Names and roles must agree with metadata. |
| **What** | Explain the change, incident, decision, capability, final claim, and boundaries. |
| **When** | Explain work completion, evidence collection, local timezone, system timestamp timezone, valid-as-of date, and review timing. The canonical timestamps must appear unchanged. |
| **Where** | Explain environment, cluster, execution host, controller, nodes, addresses, namespaces, endpoints, and repository paths. Canonical values must appear unchanged. |
| **Why** | Explain the problem, decision drivers, alternatives, tradeoffs, risk, and expected value. |
| **How** | Explain implementation sequence, source changes, commands, validation, rollback, rebuild, troubleshooting, and artifact locations. |

A static metadata block answers **which facts** apply. The Five Ws and How
explain **what those facts mean and why they matter**. Both are required.

## Evidence classifications

Every evidence item MUST use one classification:

| Classification | Meaning |
|---|---|
| `direct-observation` | Output observed from the target system, API, hardware, or user-visible behavior. |
| `generated-artifact` | Deterministically rendered report, manifest, package, checksum, or test output. |
| `repository-evidence` | Version-controlled source, configuration, commit, diff, tag, or pull request. |
| `derived-conclusion` | Calculation or inference based on identified evidence IDs. |
| `external-authority` | Vendor documentation, standards, specifications, or other authoritative external source. |
| `assumption` | Material fact believed for the work but not proven. |
| `planned` | Intended future state not yet implemented or validated. |
| `negative-evidence` | Failed test, absent resource, rejected response, or observation that a condition did not hold. |

Direct observations and repository evidence SHOULD support every critical
configuration claim. Assumptions and planned statements cannot satisfy an
acceptance criterion.

## Confidence levels

| Confidence | Use |
|---|---|
| `high` | Direct, repeatable evidence from the correct target with clear provenance and no material contradiction. |
| `medium` | Credible evidence exists, but precision, coverage, freshness, or repeatability is limited. |
| `low` | Evidence is indirect, incomplete, provisional, or substantially assumption-based. |
| `unknown` | Confidence has not been assessed; allowed only in `draft`. |

## Record lifecycle

Use exactly one status:

| Status | Meaning |
|---|---|
| `draft` | Record assembly is incomplete. |
| `implemented` | Change exists, but validation or governance evidence is incomplete. |
| `validated` | Technical acceptance criteria passed and material evidence is recorded. |
| `accepted` | Validated, reviewed, and designated the current Kalaxy3 source of truth. |
| `superseded` | A newer record replaces some or all claims. |
| `retired` | The capability or configuration no longer exists. |
| `rejected` | An attempted design was evaluated and intentionally not accepted. |

A `validated` or `accepted` record MUST have:

- captured `work_completed_at` and `evidence_collected_at` timestamps;
- a complete metadata table;
- a complete Five-W gate;
- no unchecked mandatory final-checklist item;
- an implementation commit or an explicitly valid evidence-only lineage;
- all critical claims supported by evidence.

An `accepted` record additionally requires a named reviewer and recorded review
decision.

## Required evidence lineage

Every record MUST define these relationship keys, using `none` when no
relationship exists:

- `verifies`
- `depends_on`
- `supersedes`
- `superseded_by`
- `related_to`
- `conflicts_with`
- `generated_by`
- `implemented_by`
- `revalidated_by`

Use evidence IDs and repository-relative paths. Avoid prose-only lineage.

## Mandatory record sections

All schema 1.1 records MUST contain these sections in this order:

1. Machine-readable front matter.
2. Title and executive summary.
3. Record metadata.
4. Five Ws and How.
5. Scope and boundaries.
6. Final accepted state.
7. Claims and evidence matrix.
8. Problem and decision rationale.
9. Architecture or change description.
10. Source of truth and implementation lineage.
11. Prerequisites and assumptions.
12. Implementation procedure.
13. Evidence items.
14. Verification and acceptance criteria.
15. Idempotency and repeatability.
16. Security, privacy, and evidence handling.
17. Reliability, recovery, rollback, and rebuild.
18. Operational considerations and observability.
19. Known limitations, evidence gaps, and risks.
20. Troubleshooting.
21. Freshness, revalidation, and supersession.
22. Final completion checklist and reviewer acceptance.
23. Git review and publication.
24. Appendices and raw artifacts.

A section may state `not-applicable`, but it MUST NOT disappear.

## Evidence item minimum fields

Each material evidence item MUST identify:

- evidence ID;
- classification;
- claims supported or contradicted;
- collector;
- collection timestamp and timezone;
- execution source;
- target;
- tool and exact version or `version-not-captured`;
- command, query, file, API, test, or observation;
- expected result;
- observed result;
- result state: pass, fail, partial, or informational;
- confidence;
- sensitive-data review and redactions;
- artifact path and checksum when externalized.

## Acceptance rules

A SAGE record is publishable only when:

- metadata schema and order are valid;
- the metadata table exactly mirrors front matter;
- all Five Ws and How are complete and nonconflicting;
- every critical claim has identified evidence;
- direct evidence and repository evidence agree where configuration is involved;
- expected and observed results are separated;
- failed attempts are separated from the accepted state;
- idempotency or repeatability is tested when automation is involved;
- rollback, rebuild, and data-durability consequences are documented;
- secrets and sensitive material are excluded or redacted;
- limitations, assumptions, and evidence gaps are explicit;
- source-of-truth paths and implementation lineage are recorded;
- freshness and supersession rules are defined.

## Evidence-record identifier

Use:

```text
SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>
```

The date represents the working session or material event date in the canonical
local timezone. The ID is permanent.

## Repository organization

```text
markdown/
├── standards/
│   ├── kalaxy3-sage-evidence-record-standard.md
│   ├── sage-evidence-metadata-contract-v1.1.json
│   └── kalaxy3-sage-evidence-publication-process.md
├── templates/
│   ├── sage-evidence-record-template.md
│   ├── sage-evidence-generation-request.md
│   └── sage-evidence-package-manifest-template.json
├── installation/
├── operations/
├── architecture/
├── decisions/
└── evidence-artifacts/
    └── <evidence-id>/
```

Large raw logs, rendered YAML, screenshots, benchmark output, and archives MUST
be stored under the evidence ID artifact root and referenced by checksum.

## Migration from schema 1.0

Existing schema 1.0 records remain historical evidence and do not require
immediate rewriting. When a 1.0 record is modified, revalidated, or
superseded, migrate it to 1.1:

1. preserve the evidence ID;
2. change `schema_version` to `1.1`;
3. add the exact canonical metadata fields in order;
4. distinguish work, evidence, record, and validity timestamps;
5. normalize node addresses, endpoints, and component versions;
6. add the mandatory Record metadata table;
7. reconcile the Five Ws to canonical metadata;
8. add missing lineage keys;
9. run the publisher check;
10. record migration as implementation and evidence when material.

Do not mass-edit old records solely for appearance. Migrate when the record is
next relied upon as current evidence.

## SAGE quality score

| Category | Points |
|---|---:|
| Canonical metadata and static table | 15 |
| Five Ws and How | 10 |
| Final claim and scope | 10 |
| Claim-to-evidence traceability | 15 |
| Direct observed evidence | 10 |
| Repository and commit lineage | 10 |
| Reproducible implementation and rebuild | 10 |
| Acceptance and functional tests | 10 |
| Idempotency or repeatability | 5 |
| Security and data handling | 5 |
| Risks, limitations, freshness, and supersession | 10 |
| **Total** | **100** |

A quality score does not override lifecycle status or missing review.

## Adoption decision

All newly generated Kalaxy3 SAGE records MUST use schema 1.1, the canonical
metadata contract, the schema 1.1 template, and the repository publisher.
