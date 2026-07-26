---
evidence_id: SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>
schema_version: "1.2"
title: <Formal evidence-record title>
nav_title: <Plain-language navigation title, maximum 80 characters>
nav_section: <installation|operations|architecture|decisions|finops|governance|security|incidents|experiments|benchmarks|verification|other>
nav_order: <integer 0-9999>
summary: <Single-line human navigation summary, 20-360 characters>
primary_subject: <Primary component, system, node, or capability>
project: Kalaxy3
record_type: <installation|architecture-decision|change|verification|incident|experiment|benchmark|operations|security|finops>
status: <draft|implemented|validated|accepted|superseded|retired|rejected>
classification: internal
work_session: <Stable working-session name>
work_started_at: <RFC3339 timestamp with offset or not-captured>
work_completed_at: <RFC3339 timestamp with offset>
evidence_collected_at: <RFC3339 timestamp with offset>
created_at: <RFC3339 timestamp with offset>
updated_at: __SAGE_PUBLISHED_AT__
valid_as_of: <YYYY-MM-DD>
review_due: <YYYY-MM-DD or event-based>
local_timezone: America/Chicago
system_timestamp_timezones:
  - <UTC, IANA timezone, or not-applicable>
owner: <accountable owner>
author: <record author or evidence collector>
operator: <person or automation that performed the work>
reviewer: <named reviewer or pending>
environment: <homelab|development|test|production|research|shared-platform>
system: Kalaxy3
cluster: <cluster name or not-applicable>
execution_host: <host that executed the primary commands or not-applicable>
controller_host: <automation controller or target controller or not-applicable>
nodes:
  - <node name or not-applicable>
node_addresses:
  - <node-name=address or not-applicable>
namespaces:
  - <namespace or not-applicable>
endpoints:
  - <purpose=address-or-hostname or not-applicable>
components:
  - <component=exact-version or component=version-not-captured>
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: __SAGE_IMPLEMENTATION_COMMIT__
record_path: markdown/<category>/<filename>.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>
confidence: <high|medium|low|unknown>
tags:
  - sage
  - <tag>
relationships:
  verifies:
    - <evidence ID, requirement ID, decision ID, or claim>
  depends_on:
    - none
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - none
  conflicts_with:
    - none
  generated_by:
    - <playbook, workflow, tool, or manual process>
  implemented_by:
    - __SAGE_IMPLEMENTATION_COMMIT__
  revalidated_by:
    - none
---

# <Evidence Record Title>

## Executive summary

<State the final observed result in one concise paragraph. Identify whether the
record is complete, provisional, failed, rejected, or superseded. Do not present
planned state as observed state.>

[TOC]

## Record metadata

The values in this table MUST exactly mirror front matter. List fields use
semicolon-space (`; `). Do not reformat timestamps or shorten commit SHAs.

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN> |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | <Formal evidence-record title> |
| **Navigation title** | <same as nav_title> |
| **Navigation section** | <same as nav_section> |
| **Navigation order** | <same as nav_order> |
| **Summary** | <same as summary> |
| **Primary subject** | <same as primary_subject> |
| **Record type** | <record type> |
| **Status** | <status> |
| **Classification** | internal |
| **Work session** | <Stable working-session name> |
| **Started** | <same as work_started_at> |
| **Completed** | <same as work_completed_at> |
| **Evidence collected** | <same as evidence_collected_at> |
| **Record created** | <same as created_at> |
| **Record updated** | __SAGE_PUBLISHED_AT__ |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | <semicolon-joined system_timestamp_timezones> |
| **Valid as of** | <same as valid_as_of> |
| **Review due** | <same as review_due> |
| **Target record path** | markdown/<category>/<filename>.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN> |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | __SAGE_IMPLEMENTATION_COMMIT__ |
| **Environment** | <same as environment> |
| **System** | Kalaxy3 |
| **Cluster** | <same as cluster> |
| **Execution host** | <same as execution_host> |
| **Controller host** | <same as controller_host> |
| **Nodes** | <semicolon-joined nodes> |
| **Node addresses** | <semicolon-joined node_addresses> |
| **Namespaces** | <semicolon-joined namespaces> |
| **Endpoints** | <semicolon-joined endpoints> |
| **Components and versions** | <semicolon-joined components> |
| **Owner** | <same as owner> |
| **Author** | <same as author> |
| **Operator** | <same as operator> |
| **Reviewer** | <same as reviewer> |
| **Confidence** | <same as confidence> |

## Navigation contract

- `title` is the formal evidentiary title and MAY be long enough to be precise.
- `nav_title` is the concise human-facing label shown in generated indexes.
- `nav_section` controls section grouping.
- `nav_order` controls deterministic order within a section.
- `summary` explains why a human should open the record.
- `primary_subject` drives subject indexes.
- `[TOC]` is mandatory so Daux.io and compatible renderers expose page-level headings.
- These fields are authoritative only for schema 1.2 records. Historical records are indexed through the compatibility registry and are never rewritten automatically.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** `<exact author>`; **operator:** `<exact operator>`; **owner:** `<exact owner>`; **reviewer:** `<exact reviewer>`; **affected users/teams:** `<list or none>`. Explain responsibilities without changing canonical names. |
| **What** | <Exactly what changed, was decided, failed, or was verified. Include the final claim and primary boundary.> |
| **When** | **Completed:** `<exact work_completed_at>`; **evidence collected:** `<exact evidence_collected_at>`; **local timezone:** `<exact local_timezone>`; **system timestamps:** `<exact semicolon-joined system_timestamp_timezones>`; **valid as of:** `<exact valid_as_of>`; **review due:** `<exact review_due>`. Explain any local/UTC date difference. |
| **Where** | **Environment:** `<exact environment>`; **cluster:** `<exact cluster>`; **execution host:** `<exact execution_host>`; **controller:** `<exact controller_host>`; **nodes:** `<canonical nodes>`; **addresses:** `<canonical node_addresses>`; **namespaces:** `<canonical namespaces>`; **endpoints:** `<canonical endpoints>`; **record:** `<exact record_path>`. |
| **Why** | <Problem, opportunity, decision drivers, expected value, alternatives, tradeoffs, safety, and governance rationale.> |
| **How** | <Implementation method, source files, automation, validation, artifacts, rollback, rebuild, and troubleshooting path.> |

### Five-W completeness gate

- [ ] Who is complete and agrees with metadata.
- [ ] What is complete.
- [ ] When is complete, uses canonical timestamps, and includes timezone context.
- [ ] Where is complete at repository and runtime levels and agrees with metadata.
- [ ] Why includes rationale, alternatives, and tradeoffs.
- [ ] How is reproducible and verifiable.

Any unchecked item is an explicit evidence gap and prevents `validated` or
`accepted` status.

## Scope and boundaries

### In scope

- <Included component, change, claim, or verification>

### Out of scope

- <Explicit exclusion>

### Nonclaims

This record does **not** claim:

- <Tempting conclusion not supported by the evidence>

## Final accepted state

```text
<Concise component and state summary>
```

| Item | Accepted result |
|---|---|
| <item> | <result> |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | <Atomic testable claim> | <critical|high|normal|low> | `EV-001` | <supported|partially-supported|contradicted|unverified> | <high|medium|low> |

Rules:

- Every claim is atomic and testable.
- Every critical configuration claim requires direct or generated evidence and
  repository evidence.
- Assumptions and planned work cannot prove a claim.

## Problem and decision rationale

### Problem or opportunity

<Condition requiring action.>

### Decision

<Accepted decision.>

### Decision drivers

- <driver>

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| <option> | <benefit> | <cost or risk> | <accepted|rejected|deferred> |

### Tradeoffs and consequences

- <positive consequence>
- <negative consequence>
- <operational consequence>

## Architecture or change description

```text
<Architecture, topology, sequence, or before/after diagram>
```

### Before

<Previous state or not-applicable.>

### After

<Final evidenced state.>

## Source of truth and implementation lineage

### Repository files

```text
<repository-relative path>
```

### Implementation commit

```text
__SAGE_IMPLEMENTATION_COMMIT__
<commit subject or pending before publication>
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| <component matching front matter> | <exact version> | <repository, image, chart, package, device, or observation> |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | <paths and exact versions> |
| Controller bootstrap | <repository command or target> |
| Controller preflight | <command and result> |
| Controller host | <canonical controller_host> |
| Execution host | <canonical execution_host> |
| Machine-local authoritative state | none, or explain as an evidence gap |

- [ ] Another supported controller can recreate the toolchain from a clean checkout.
- [ ] No workstation contains the only authoritative deployment configuration.
- [ ] Manual runtime changes were reconciled into repository-owned automation.
- [ ] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
<Minimum relevant configuration; redact secrets>
```

## Prerequisites and assumptions

### Proven prerequisites

- <Prerequisite with evidence ID>

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | <assumption> | <risk> | <test or evidence needed> |

A material assumption prevents `accepted` status unless the owner and reviewer
explicitly accept the residual risk.

## Implementation procedure

### Preparation

```bash
<preparation commands>
```

### Execution

```bash
<implementation commands>
```

### Expected change

<Expected state transition.>

### Observed change

<Actual state transition with evidence IDs.>

### Failed or superseded paths

<Separate failed attempts from the final accepted implementation.>

## Evidence items

Repeat for every material evidence item.

### `EV-001` — <Evidence title>

| Field | Value |
|---|---|
| Classification | `<direct-observation|generated-artifact|repository-evidence|derived-conclusion|external-authority|assumption|planned|negative-evidence>` |
| Supports or contradicts | `CLM-001` |
| Collected by | <person or automation> |
| Collected at | <RFC3339 timestamp with offset> |
| Execution source | <host, runner, browser, device, or repository> |
| Target | <cluster, node, namespace, service, endpoint, or file> |
| Tool and version | <tool=version or version-not-captured> |
| Expected result | <expected result or informational> |
| Actual result | <pass|fail|partial|informational> |
| Confidence | <high|medium|low> |
| Sensitive data | <none, redacted, or description> |
| Artifact | <repository path, URI, checksum, or inline> |

**Command, query, source, or observation**

```bash
<exact command or source reference>
```

**Observed result**

```text
<exact relevant output; identify trimmed noise>
```

**Interpretation**

<What the evidence proves and does not prove. Derived conclusions cite evidence
IDs.>

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | <requirement> | `EV-001` | <expected> | <observed> | <pass|fail|partial|not-run> |

### Functional verification

```bash
<functional test>
```

Observed:

```text
<result>
```

### Negative verification

```bash
<test of a condition that must not occur>
```

Observed:

```text
<expected rejection or absence>
```

## Idempotency and repeatability

### First accepted run

```text
<recap or result>
```

### Steady-state rerun

```text
<changed=0 or equivalent proof>
```

### Interpretation

<State whether automation is idempotent, intentionally imperative, or not
applicable.>

## Security, privacy, and evidence handling

### Security controls

- <control>

### Sensitive material excluded

Never include:

- credentials, tokens, passwords, private keys, or secret values;
- unredacted Kubernetes Secret manifests;
- authentication hashes unless explicitly approved and protected;
- unnecessary personal information;
- terminal history containing secrets.

### Redactions and omissions

- <redaction and reason, or none>

### Residual security risk

- <risk and mitigation>

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| <failure> | <signal> | <impact> | <action> |

### Rollback

```bash
<rollback procedure>
```

### Rebuild procedure

1. <step>
2. <step>
3. <verification step>

### Data durability and backup impact

<Affected persistent data, reclaim policy, backups, recovery point, and
recovery-time limitations.>

## Operational considerations and observability

### Health signals

- <metric, log, event, endpoint, command, or user-visible behavior>

### Routine verification

```bash
<health check>
```

### Capacity, performance, cost, and sustainability

- **Capacity:** <impact>
- **Performance:** <impact>
- **Cost:** <impact>
- **Sustainability/power:** <impact>

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | <limitation|evidence-gap|risk|technical-debt> | <description> | <impact> | <owner> | <date or event> |

Every `not-captured` metadata value must appear here.

## Troubleshooting

### <Symptom>

**Meaning**

<Interpretation.>

**Checks**

```bash
<diagnostic commands>
```

**Recovery**

```bash
<repair commands>
```

## Freshness, revalidation, and supersession

### Revalidate when

- a component version changes;
- a canonical metadata value changes;
- a source-of-truth path changes;
- a node, address, namespace, endpoint, replica count, or architecture changes;
- a relevant playbook, manifest, or security control changes;
- an acceptance test no longer passes;
- a conflicting evidence record is accepted;
- <record-specific trigger>.

### Scheduled review

```text
<date, cadence, or event-based review>
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve the
record and evidence ID, and state which claims remain valid.

## Final completion checklist and reviewer acceptance

### Governance

- [ ] Evidence ID is unique and permanent.
- [ ] Schema version is 1.2.
- [ ] Front matter follows the exact metadata contract and order.
- [ ] Record metadata exactly mirrors front matter.
- [ ] Status accurately reflects completeness.
- [ ] Owner, author, operator, and reviewer are identified.
- [ ] Five Ws and How agree with canonical metadata.
- [ ] Scope and nonclaims are explicit.
- [ ] Implementation commit is recorded or validly not-applicable.
- [ ] Relationships and supersession fields are complete.

### Evidence

- [ ] Every critical claim has supporting evidence.
- [ ] Expected and observed results are separated.
- [ ] Direct observations identify source, target, time, and tool version.
- [ ] Derived conclusions reference evidence IDs.
- [ ] Assumptions and planned work are marked.
- [ ] Failed attempts are separated from final state.
- [ ] Idempotency or repeatability is proven or not-applicable.
- [ ] Every not-captured value has an evidence gap.

### Safety and operations

- [ ] Secrets and sensitive data are excluded or redacted.
- [ ] Security limitations and residual risks are recorded.
- [ ] Rollback, rebuild, and data-durability impacts are documented.
- [ ] Operational health checks are documented.
- [ ] Known limitations and gaps have owners or triggers.
- [ ] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | <name> | <accept|reject|conditional|pending> | <date or pending> | <notes> |
| Reviewer | <name or pending> | <accept|reject|conditional|pending> | <date or pending> | <notes> |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/<sage-package>.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/<sage-package>.zip \
  --push
```

Do not invent a session-specific unzip, stage, commit, rebase, or push sequence.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| <artifact> | `markdown/evidence-artifacts/<evidence-id>/<file>` | <checksum> | <yes|no|redacted> | <policy> |

### Additional notes

<Context that does not belong in the final-state narrative.>
