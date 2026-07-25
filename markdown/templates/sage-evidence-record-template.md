---
evidence_id: SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>
schema_version: "1.0"
title: <Concise evidence-record title>
project: Kalaxy3
record_type: <installation|architecture-decision|change|verification|incident|experiment|benchmark|operations|security|finops>
status: <draft|implemented|validated|accepted|superseded|retired|rejected>
classification: internal
created_at: <YYYY-MM-DDThh:mm:ss-05:00>
updated_at: <YYYY-MM-DDThh:mm:ss-05:00>
valid_as_of: <YYYY-MM-DD>
review_due: <YYYY-MM-DD or event-based>
owner: <accountable owner>
author: <record author or evidence collector>
operator: <person or automation that performed the work>
reviewer: <reviewer or pending>
environment: <homelab|development|test|production|research|shared-platform>
system: Kalaxy3
cluster: <cluster name>
components:
  - <component>
nodes:
  - <node or not-applicable>
namespaces:
  - <namespace or not-applicable>
repository: donb4iu/Kalaxy3
branch: <branch>
implementation_commit: <Git SHA or pending>
record_path: markdown/<category>/<filename>.md
confidence: <high|medium|low|unknown>
tags:
  - <tag>
relationships:
  verifies:
    - <evidence ID, requirement ID, decision ID, or claim>
  depends_on:
    - <evidence ID or none>
  supersedes:
    - <evidence ID or none>
  superseded_by:
    - <evidence ID or none>
  related_to:
    - <evidence ID or none>
  conflicts_with:
    - <evidence ID or none>
  generated_by:
    - <playbook, workflow, tool, or manual>
---

# <Evidence Record Title>

## Executive summary

<State the accepted result in one concise paragraph. Identify whether the
record is complete, provisional, failed, or superseded. Do not describe a
planned state as an observed result.>

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** `<name>`; **operator:** `<name or automation>`; **owner:** `<name or role>`; **reviewer:** `<name, pending, or not required>`; **affected users/teams:** `<list or none>`. |
| **What** | <Exactly what changed, was decided, failed, or was verified. Include the final claim and the main boundary.> |
| **When** | **Implemented:** `<timestamp and timezone>`; **evidence collected:** `<timestamp and timezone>`; **system timestamps:** `<timezone if different>`; **valid as of:** `<date>`; **review due:** `<date or trigger>`. |
| **Where** | **Environment:** `<environment>`; **cluster:** `<cluster>`; **nodes:** `<nodes>`; **namespaces:** `<namespaces>`; **endpoints:** `<addresses/hostnames>`; **repository paths:** `<paths>`; **execution host:** `<host>`. |
| **Why** | <Problem, opportunity, decision drivers, expected value, safety or governance need, and why the accepted approach was selected.> |
| **How** | <Implementation method, automation, validation approach, rollback/rebuild path, and where supporting evidence is stored.> |

### Five-W completeness gate

- [ ] Who is complete.
- [ ] What is complete.
- [ ] When is complete and includes timezone.
- [ ] Where is complete at both repository and runtime levels.
- [ ] Why includes rationale and tradeoffs.
- [ ] How is reproducible and verifiable.

Any unchecked item is an explicit evidence gap and prevents `validated` or
`accepted` status.

## Scope and boundaries

### In scope

- <Included component, change, claim, or verification>

### Out of scope

- <Explicit exclusions>

### Nonclaims

This record does **not** claim:

- <A tempting conclusion that the evidence does not support>

## Final accepted state

```text
<Component/state summary>
```

| Item | Accepted result |
|---|---|
| <item> | <result> |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | <Atomic, testable claim> | <critical|high|normal|low> | `EV-001`, `EV-002` | <supported|partially-supported|contradicted|unverified> | <high|medium|low> |

Rules:

- Each claim must be atomic and testable.
- Every critical claim requires direct observation or generated evidence plus
  repository evidence when configuration is involved.
- Assumptions and planned work cannot prove a claim.

## Problem and decision rationale

### Problem or opportunity

<Describe the condition that required action.>

### Decision

<State the accepted decision plainly.>

### Decision drivers

- <driver>

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| <option> | <benefit> | <cost/risk> | <accepted|rejected|deferred> |

### Tradeoffs and consequences

- <Positive consequence>
- <Negative consequence>
- <Operational consequence>

## Architecture or change description

```text
<Architecture, sequence, topology, or before/after diagram>
```

### Before

<Previous state or not applicable.>

### After

<Accepted state.>

## Source of truth and implementation lineage

### Repository files

```text
<repository-relative path>
```

### Implementation commit

```text
<Git SHA, commit subject, pull request, or pending>
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| <component> | <version> | <repository, image, chart, package, or device> |

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

A material assumption prevents `accepted` status unless the residual risk is
explicitly accepted by the owner and reviewer.

## Implementation procedure

### Preparation

```bash
<preparation commands>
```

### Execution

```bash
<implementation command>
```

### Expected change

<Describe what should change.>

### Observed change

<Describe what actually changed. Reference evidence IDs.>

## Evidence items

Repeat this subsection for every material evidence item.

### `EV-001` — <Evidence title>

| Field | Value |
|---|---|
| Classification | `<direct-observation|generated-artifact|repository-evidence|derived-conclusion|external-authority|assumption|planned|negative-evidence>` |
| Supports or contradicts | `CLM-001` |
| Collected by | <person or automation> |
| Collected at | <timestamp and timezone> |
| Execution source | <Mac mini, CI runner, arm64-01, browser, device, etc.> |
| Target | <cluster/node/namespace/service/file> |
| Tool and version | <tool and version> |
| Expected result | <expected result or informational> |
| Actual result | <pass|fail|partial|informational> |
| Confidence | <high|medium|low> |
| Sensitive data | <none, redacted, or description> |
| Artifact | <repository path, external artifact URI, checksum, or inline> |

**Command, query, source, or observation**

```bash
<exact command or source reference>
```

**Observed result**

```text
<exact relevant output; trim unrelated noise and identify omissions>
```

**Interpretation**

<Explain exactly what this proves and what it does not prove. Derived claims
must cite the evidence IDs used.>

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

<Record security rejection, failed access, absent scheduling, destructive-action
refusal, or another condition that must not occur.>

```bash
<negative test>
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
<changed=0 or equivalent repeatability proof>
```

### Interpretation

<State whether automation is idempotent, a command is intentionally imperative,
or repeatability is not applicable.>

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

- <What was redacted and why, or “none.”>

### Residual security risk

- <risk and accepted mitigation>

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| <failure> | <signal> | <impact> | <action> |

### Rollback

```bash
<rollback command or procedure>
```

### Rebuild procedure

1. <step>
2. <step>
3. <verification step>

### Data durability and backup impact

<Describe affected persistent data, reclaim policy, backup requirements, and
recovery point limitations.>

## Operational considerations and observability

### Health signals

- <metric, log, event, endpoint, or command>

### Routine verification

```bash
<health check>
```

### Capacity, performance, and cost impact

- **Capacity:** <impact>
- **Performance:** <impact>
- **Cost:** <impact>
- **Sustainability/power:** <impact>

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | <limitation|evidence-gap|risk|technical-debt> | <description> | <impact> | <owner> | <date/event> |

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

- a referenced component or chart version changes;
- a source-of-truth path changes;
- the node, namespace, endpoint, replica count, or architecture changes;
- the relevant playbook or manifest changes;
- a security control changes;
- an acceptance test no longer passes;
- a conflicting evidence record is accepted;
- <record-specific trigger>.

### Scheduled review

```text
<date, cadence, or event-based review>
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve this
record for lineage, and identify which claims remain valid.

## Final completion checklist

### Governance

- [ ] Evidence ID is unique and permanent.
- [ ] Status accurately reflects completeness.
- [ ] Owner, author/operator, and reviewer are identified.
- [ ] Five Ws and How are complete.
- [ ] Scope and nonclaims are explicit.
- [ ] Implementation commit is recorded.
- [ ] Relationships and supersession fields are complete.

### Evidence

- [ ] Every critical claim has supporting evidence.
- [ ] Expected and observed results are separated.
- [ ] Direct observations identify source, target, time, and tool.
- [ ] Derived conclusions reference evidence IDs.
- [ ] Assumptions and planned work are marked.
- [ ] Failed attempts are separated from the accepted final state.
- [ ] Idempotency or repeatability is proven or marked not applicable.

### Safety and operations

- [ ] Secrets and sensitive data are excluded or redacted.
- [ ] Security limitations and residual risks are recorded.
- [ ] Rollback and rebuild are documented.
- [ ] Operational health checks are documented.
- [ ] Known limitations and evidence gaps have owners or triggers.
- [ ] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | <name> | <accept|reject|conditional> | <date> | <notes> |
| Reviewer | <name> | <accept|reject|conditional> | <date> | <notes> |

## Git review and publication

```bash
cd ~/dvlp/Kalaxy3

git diff --check
git status --short
git diff -- <implementation paths> <this evidence record>
```

Stage only intentional source and evidence files:

```bash
git add -- \
  <implementation paths> \
  markdown/<category>/<this-record>.md
```

Commit and publish:

```bash
git commit -m "<imperative summary>"
git pull --rebase origin main
git push origin main
git status
```

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| <artifact> | `markdown/evidence-artifacts/<evidence-id>/<file>` | `<checksum>` | <yes/no/redacted> | <policy> |

### Additional notes

<Optional context that does not belong in the accepted-state narrative.>
