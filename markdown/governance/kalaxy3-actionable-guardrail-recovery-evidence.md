---
evidence_id: SAGE-K3-GUARDRAIL-20260731-001
schema_version: "1.2"
title: Actionable Guardrail Recovery and Active Centralized Logging Runtime Validation Evidence
nav_title: Recover guardrails and validate active logging
nav_section: governance
nav_order: 410
summary: Documents the reusable SAGE actionable-failure framework, centralized-logging lifecycle recovery, vault-tolerant metadata handling, and live seven-node Loki validation.
primary_subject: SAGE actionable failures
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: Actionable guardrail recovery and logging runtime validation
work_started_at: not-captured
work_completed_at: 2026-07-31T22:01:00-05:00
evidence_collected_at: 2026-07-31T22:13:35-05:00
created_at: 2026-07-31T22:17:00-05:00
updated_at: 2026-07-31T22:26:35-05:00
valid_as_of: 2026-07-31
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Kalaxy3 architecture
author: OpenAI GPT-5.6 Thinking
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donbs-imac
controller_host: donbs-imac
nodes:
  - amd64-01
  - amd64-02
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
node_addresses:
  - not-applicable
namespaces:
  - observability
endpoints:
  - loki-api=service/loki-gateway
  - grafana-datasource=configmap/grafana-datasources
components:
  - SAGE-schema=1.2
  - SAGE-actionable-failure-framework=4c369193731e9fc7832d8c2a0e1e2718a6210e86
  - Loki=18.5.4
  - fluent-bit-collector=1.0.9
  - Longhorn=1.12.0
  - Python=3.12.4
  - ansible-core=2.18.7
  - kubectl=version-not-captured
repository: donb4iu/Kalaxy3
branch: feature/actionable-guardrail-recovery
implementation_commit: 4c369193731e9fc7832d8c2a0e1e2718a6210e86
record_path: markdown/governance/kalaxy3-actionable-guardrail-recovery-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001
confidence: high
tags:
  - sage
  - guardrails
  - validator-runtime
  - centralized-logging
  - loki
  - fluent-bit
  - longhorn
  - evidence
relationships:
  verifies:
    - Actionable validator recovery contract
    - Active centralized logging runtime health
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
    - scripts/sage/sage-evidence-orchestrator.py
    - scripts/sage/sage-publish.py
  implemented_by:
    - 4c369193731e9fc7832d8c2a0e1e2718a6210e86
  revalidated_by:
    - none
---

# Actionable Guardrail Recovery and Active Centralized Logging Runtime Validation Evidence

## Executive summary

Kalaxy3 now has a reusable SAGE actionable-failure framework that distinguishes
target-system failures from validator bootstrap or runtime failures, routes
staged and active centralized-logging checks to the correct lifecycle path,
and reads non-secret YAML metadata without decrypting unrelated `!vault`
values. The live active-state validator passed against the homelab: locked
Loki `18.5.4` and Fluent Bit Collector `1.0.9`, seven ready collectors, Loki
and gateway each `1/1`, Bound `40Gi` Longhorn storage, Grafana datasource
configuration, one recent Loki query result, and log coverage for all seven
nodes. This record is validated, while governance review remains pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GUARDRAIL-20260731-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Actionable Guardrail Recovery and Active Centralized Logging Runtime Validation Evidence |
| **Navigation title** | Recover guardrails and validate active logging |
| **Navigation section** | governance |
| **Navigation order** | 410 |
| **Summary** | Documents the reusable SAGE actionable-failure framework, centralized-logging lifecycle recovery, vault-tolerant metadata handling, and live seven-node Loki validation. |
| **Primary subject** | SAGE actionable failures |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Actionable guardrail recovery and logging runtime validation |
| **Started** | not-captured |
| **Completed** | 2026-07-31T22:01:00-05:00 |
| **Evidence collected** | 2026-07-31T22:13:35-05:00 |
| **Record created** | 2026-07-31T22:17:00-05:00 |
| **Record updated** | 2026-07-31T22:26:35-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-07-31 |
| **Review due** | event-based |
| **Target record path** | markdown/governance/kalaxy3-actionable-guardrail-recovery-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/actionable-guardrail-recovery |
| **Implementation commit** | 4c369193731e9fc7832d8c2a0e1e2718a6210e86 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05 |
| **Node addresses** | not-applicable |
| **Namespaces** | observability |
| **Endpoints** | loki-api=service/loki-gateway; grafana-datasource=configmap/grafana-datasources |
| **Components and versions** | SAGE-schema=1.2; SAGE-actionable-failure-framework=4c369193731e9fc7832d8c2a0e1e2718a6210e86; Loki=18.5.4; fluent-bit-collector=1.0.9; Longhorn=1.12.0; Python=3.12.4; ansible-core=2.18.7; kubectl=version-not-captured |
| **Owner** | Kalaxy3 architecture |
| **Author** | OpenAI GPT-5.6 Thinking |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author OpenAI GPT-5.6 Thinking; operator Don Buddenbaum; owner Kalaxy3 architecture; reviewer pending; affected users are Kalaxy3 operators and reviewers. |
| **What** | The session converted recurring validator and helper failures into a reusable SAGE actionable-failure framework, migrated centralized-logging lifecycle failures, added vault-tolerant metadata handling, and validated the active logging deployment. |
| **When** | Completed 2026-07-31T22:01:00-05:00; evidence collected 2026-07-31T22:13:35-05:00; local timezone America/Chicago; system timestamps America/Chicago; UTC; valid as of 2026-07-31; review due event-based. The exact session start was not captured. |
| **Where** | Environment homelab; cluster kalaxy3; execution host donbs-imac; controller donbs-imac; nodes amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; addresses not-applicable; namespaces observability; endpoints loki-api=service/loki-gateway; grafana-datasource=configmap/grafana-datasources; record markdown/governance/kalaxy3-actionable-guardrail-recovery-evidence.md. |
| **Why** | Operators needed failures to explain detected state, lifecycle mismatch, canonical recovery, prohibited workarounds, and integrity requirements without relying on remembered chat context. |
| **How** | Repository-owned Python, Ansible, Make, SAGE policy, regression tests, live Kubernetes queries, Loki API checks, the evidence orchestrator, and the publisher package contract were used. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- The actionable-failure contract, shared renderer, catalog, registry, audit,
  validator runner, and regression tests.
- Migration of the centralized-logging staged validator to shared recovery.
- The active centralized-logging runtime validator and its live cluster result.
- Opaque-tag YAML metadata loading for non-secret validation of files that also
  contain encrypted values.
- Failure chronology, implementation lineage, rollback, rebuild, and remaining
  migration debt.

### Out of scope

- Automatic migration of every audit candidate.
- Decryption or validation of Ansible Vault secret values.
- Long-term Loki retention, disaster recovery restore, load testing, or cost
  optimization.
- Governance acceptance; the reviewer remains pending.

### Nonclaims

This record does **not** claim that all 72 unregistered audit candidates are
true validators, that all historical files require migration, or that a single
successful Loki query proves long-term retention and performance.

## Final accepted state

```text
SAGE actionable failures are repository-owned, runtime-tested, lifecycle-aware,
and able to validate the active centralized-logging deployment across all seven
Kalaxy3 nodes without decrypting unrelated YAML secrets.
```

| Item | Accepted result |
|---|---|
| Actionable-failure framework | Shared contract, renderer, catalog, registry, audit, guardrail, and self-tests passed. |
| Validator runtime behavior | Runtime and bootstrap failures are reported as validator failures rather than target-system results. |
| Centralized-logging lifecycle | Staged rendering and active runtime validation have separate canonical recovery paths. |
| YAML metadata | Unknown tags including `!vault` are opaque, redacted, and unusable as booleans. |
| Active logging | Seven collectors ready; Loki `1/1`; gateway `1/1`; recent logs cover all seven nodes. |
| Storage and datasource | Loki PVC is Bound, `40Gi`, Longhorn; two Grafana datasource ConfigMaps were observed. |
| Remaining debt | Audit reports 74 candidates, 2 registered and migrated, and 72 unregistered candidates requiring classification. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The repository provides a reusable actionable-failure contract and renderer. | critical | `EV-001`; `EV-002` | supported | high |
| `CLM-002` | Validator bootstrap and runtime failures are distinguished from target-system validation results. | critical | `EV-001`; `EV-003` | supported | high |
| `CLM-003` | Centralized-logging lifecycle errors direct operators to the correct staged or active validator. | high | `EV-002`; `EV-003` | supported | high |
| `CLM-004` | Non-secret YAML metadata can be read while unrelated tagged values remain opaque and unexposed. | critical | `EV-001`; `EV-004` | supported | high |
| `CLM-005` | Active centralized logging was healthy and queryable across all seven nodes at collection time. | critical | `EV-005` | supported | high |
| `CLM-006` | Remaining validator migration debt is visible but not yet classified. | normal | `EV-006` | supported | high |
| `CLM-007` | The evidence package is traceable to the validated repository input bundle and authority hashes. | high | `EV-007` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The original operator guidance sent an active deployment through a validator
that was intentionally valid only while centralized logging remained staged.
The resulting failures also exposed recurring defects in validator execution,
helper generation, YAML parsing, and source patching. A local command fix would
have left the broader classes unprotected.

### Decision

Implement the smallest reusable framework that resolves the incident while
covering the broader failure classes:

- define a mandatory actionable-failure contract;
- centralize failure rendering and recovery authority;
- wrap validator execution and preserve bootstrap failures;
- require real import, runtime, output, and helper-entry tests;
- add lifecycle-specific staged and active logging validators;
- add an opaque-tag YAML metadata loader;
- audit the repository for future migration candidates.

### Decision drivers

- An operator must be able to recover without remembered conversational context.
- A validator failure must never be misreported as a target-system result.
- Secret-bearing repository YAML must remain usable for non-secret metadata
  checks without decryption or disclosure.
- The specific incident must remain a regression test while the generic class
  receives repository-wide protection.
- Changes must be small, validated, committed, and pushed in cohesive
  checkpoints.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Patch only the centralized-logging assertion text | Minimal code change | Does not protect other validators or helper failures | rejected |
| Change `deploy_centralized_logging` to false before running the staged validator | Makes the old command pass | Misrepresents active state and risks unintended lifecycle change | rejected |
| Require Vault decryption for metadata validation | Uses standard Ansible semantics | Exposes unnecessary secret dependency and expands access requirements | rejected |
| Ignore validator tracebacks and rerun manually | Fast for one operator | Loses evidence and repeats the same failure class | rejected |
| Generic framework plus first migrated validator and active runtime target | Reusable, testable, lifecycle-correct | Adds governance code and migration debt visibility | accepted |

### Tradeoffs and consequences

- The framework adds code and maintenance responsibilities, but failures are
  now deterministic and self-contained.
- The audit intentionally reports false positives until candidates are
  classified; visibility is preferred over silent gaps.
- The active runtime validator depends on live cluster access and therefore is
  not a render-only or offline test.
- Opaque YAML parsing deliberately refuses to interpret tagged values, which
  prevents accidental secret use but limits validation to ordinary metadata.

## Architecture or change description

```text
operator command
      |
      v
repository Make target
      |
      +--> staged state --> render validator
      |
      +--> active state --> SAGE validator runner
                              |
                              +--> runtime validator completes --> PASS evidence
                              |
                              +--> validator bootstrap/runtime failure
                              |       --> actionable recovery contract
                              |
                              +--> target-system validation failure
                                      --> actionable recovery contract

YAML metadata path:
ordinary key ------------------------------> typed metadata
!vault or unknown tagged payload ----------> opaque redacted value
```

### Before

- Failure messages were duplicated and instance-specific.
- The staged logging validator was incorrectly suggested after activation.
- `py_compile` could pass while dynamic import or runtime output failed.
- A syntactically valid but truncated helper could silently do nothing.
- `yaml.safe_load` failed on unrelated `!vault` tags.
- Repair helpers depended on brittle remembered source anchors.
- No active-state logging validator proved queryable logs from every node.

### After

- The shared catalog and renderer own recovery language.
- Validator failures pass through `scripts/sage/sage-validator-runner.py`.
- Regression tests exercise imports, subprocess failures, terminal output, and
  helper entry points.
- Tagged YAML values are opaque and cannot leak payloads or coerce to booleans.
- `make centralized-logging-runtime-validate` verifies live Helm, workload,
  storage, datasource, API, recency, and all-node coverage.
- The audit reports registered, migrated, planned, and unregistered candidates.

## Source of truth and implementation lineage

### Repository files

```text
AGENTS.md
SAGE.md
Makefile
sage-actionable-failure-registry.json
sage-actionable-failures.json
sage-change-authority.json
scripts/sage/sage_actionable_failure.py
scripts/sage/sage-actionable-failure-guardrail.py
scripts/sage/sage-actionable-failure-self-test.py
scripts/sage/sage-actionable-failure-audit.py
scripts/sage/sage-validator-runner.py
scripts/sage/sage_yaml_metadata.py
scripts/sage/sage-yaml-metadata-self-test.py
infrastructure/k3s-homelab/Makefile
infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime-self-test.py
markdown/standards/kalaxy3-sage-actionable-failure-contract.md
```

### Implementation commits

```text
78b839d Define actionable SAGE failure contract
3aeac1e Add reusable SAGE actionable failure framework
054f625 Migrate centralized logging failures to shared recovery
4c36919 Add vault-tolerant active logging runtime validation
```

The publication implementation commit is the full SHA
`4c369193731e9fc7832d8c2a0e1e2718a6210e86`.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE record schema | 1.2 | `markdown/standards/sage-evidence-metadata-contract-v1.2.json` |
| Loki Helm chart | 18.5.4 | `infrastructure/k3s-homelab/helm-chart-lock.json` and live Helm result |
| Fluent Bit Collector chart | 1.0.9 | chart lock and live Helm result |
| Longhorn | 1.12.0 | lock reconciliation output |
| Python | 3.12.4 | controller preflight |
| ansible-core | 2.18.7 | controller preflight |
| kubectl | version not captured | live executable path `/usr/local/bin/kubectl` |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Helm locks, SAGE policy, Make targets, Python validators, Ansible playbooks |
| Controller bootstrap | `make cluster-guardrails` and repository `.venv` |
| Controller preflight | Python `3.12.4`, ansible-core `2.18.7`, repository Helm and cluster access passed |
| Controller host | `donbs-imac` |
| Execution host | `donbs-imac` |
| Machine-local authoritative state | none claimed; credentials and kubeconfig remain controller-local operational inputs |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual runtime changes were reconciled into repository-owned automation.
- [x] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
deploy_centralized_logging: true
```

The opaque-tag loader reads this plain lifecycle gate while treating unrelated
tagged values as opaque. No encrypted payload is included in this record.

## Prerequisites and assumptions

### Proven prerequisites

- `EV-005`: the active cluster was reachable through the configured kubectl
  context and returned runtime state.
- `EV-001`: the repository SAGE self-tests and guardrails passed.
- `EV-004`: the metadata loader parsed the real inventory without decryption.
- `EV-007`: the input bundle included the standard, contract, template,
  publisher, indexer, source snapshots, and terminal transcript.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Commit `4c36919` remains reachable from the publication branch. | Evidence lineage could break. | Publisher checks the full implementation commit before publication. |
| `ASM-002` | Current node names remain the intended logging coverage boundary. | New or renamed nodes could lack logs. | Re-run `make centralized-logging-runtime-validate` after topology changes. |
| `ASM-003` | One recent query result is sufficient for the session acceptance boundary. | It does not prove retention or sustained throughput. | Add retention and volume tests when those become explicit requirements. |

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
git switch feature/actionable-guardrail-recovery
git fetch origin feature/actionable-guardrail-recovery
git status --short --branch
```

### Execution

```bash
make sage-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
python3 scripts/sage/sage-actionable-failure-audit.py --summary
```

Implementation was delivered through four cohesive commits listed above. The
final evidence package is evidence-only and binds publication to full
implementation SHA `4c369193731e9fc7832d8c2a0e1e2718a6210e86`.

### Expected change

- Invalid lifecycle actions produce self-contained recovery guidance.
- Validator bootstrap failures remain distinguishable from target failures.
- Active logging can be verified without modifying deployment state.
- Vault-tagged configuration does not require decryption for plain metadata
  checks.
- Live logs are queryable from every current node.

### Observed change

`EV-001` through `EV-006` show the framework tests, lifecycle migration,
vault-tolerant parsing, live runtime PASS, and visible migration debt.

### Failed or superseded paths

1. **Global Ansible interpreter:** rejected because repository validation must
   use the pinned `.venv`.
2. **Staged validator after activation:** rejected because
   `deploy_centralized_logging=true` makes the render-only path invalid.
3. **Dynamic dataclass import:** failed because the module was missing from
   `sys.modules` before `exec_module`.
4. **Truncated helper:** exited silently because syntactically valid content
   ended before a `main()` entry point.
5. **Vault YAML parsing:** `yaml.safe_load` raised a constructor error on
   unrelated `!vault` content.
6. **Brittle source repair:** failed because an exact source anchor did not
   match the actual `ROOT` layout.
7. **Invented evidence command:** `generate` was not a valid orchestrator
   subcommand; the repository contract is `brief`, `capture`, `check`, and
   `self-test`.
8. **Input bundle checked as final package:** rejected because the capture ZIP
   correctly lacked `sage-package.json`; this final package resolves that
   boundary.

## Evidence items

### `EV-001` — Repository framework self-tests and guardrails

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`; `CLM-002`; `CLM-004` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | SAGE actionable-failure framework |
| Tool and version | Python=3.12.4; SAGE-schema=1.2 |
| Expected result | Renderer, incident regressions, negative mutations, runtime regressions, and YAML metadata tests pass |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make sage-self-test
```

**Observed result**

```text
PASS reusable actionable-failure renderer
PASS original incident regression cases
PASS actionable-failure negative mutation tests
PASS validator bootstrap/runtime failure regression
PASS vault-tolerant inventory metadata
PASS vault and unknown tags remain opaque
Kalaxy3 SAGE lessons discovery self-test: PASS
```

**Interpretation**

The tests prove the exercised framework paths in the captured repository state.
They do not prove that every repository validator has been migrated.

### `EV-002` — Centralized-logging lifecycle migration

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`; `CLM-003` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | `playbooks/validate-centralized-logging.yml` |
| Tool and version | ansible-core=2.18.7 |
| Expected result | Global interpreter and active lifecycle misuse fail with the complete SAGE contract |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-actionable-failure-self-test.py
```

**Observed result**

```text
PASS original incident regression cases
PASS actionable-failure validator registry
```

**Interpretation**

The original incident is retained as a regression case and its recovery text is
owned by the shared catalog rather than duplicated in the playbook.

### `EV-003` — Validator-runtime failure classification

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-002`; `CLM-003` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | `scripts/sage/sage-validator-runner.py` |
| Tool and version | Python=3.12.4 |
| Expected result | A validator exception is reported as validation-not-completed with canonical recovery |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make sage-validator-runtime-self-test
```

**Observed result**

```text
SAGE validator runtime: PASS (sage.actionable_failure_self_test)
```

**Interpretation**

The runner preserves validator execution integrity and prevents an internal
exception from being mistaken for a target-system failure.

### `EV-004` — Opaque-tag YAML metadata regression

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-004` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | real inventory and synthetic tagged YAML |
| Tool and version | PyYAML=version-not-captured |
| Expected result | Plain booleans remain typed; tagged payloads are opaque, redacted, and reject boolean coercion |
| Actual result | pass |
| Confidence | high |
| Sensitive data | encrypted payload excluded |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make sage-yaml-metadata-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
```

**Observed result**

```text
PASS ordinary YAML metadata
PASS vault and unknown tags remain opaque
PASS opaque values reject boolean coercion
PASS vault-tolerant inventory metadata
```

**Interpretation**

The validator can read the plain activation gate without requiring or exposing
unrelated secret values. It intentionally cannot validate the content of
encrypted values.

### `EV-005` — Live active centralized-logging validation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-005` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | Kalaxy3 cluster namespace `observability` |
| Tool and version | kubectl=version-not-captured; Loki=18.5.4; fluent-bit-collector=1.0.9 |
| Expected result | Locked releases deployed; workloads ready; storage Bound; datasource present; recent logs cover every node |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

**Observed result**

```json
{
  "datasource_configmaps": 2,
  "helm_releases": {
    "fluent-bit-collector": "1.0.9",
    "loki": "18.5.4"
  },
  "loki_data": {
    "covered_nodes": [
      "amd64-01",
      "amd64-02",
      "arm64-01",
      "arm64-02",
      "arm64-03",
      "arm64-04",
      "arm64-05"
    ],
    "node_label": "node",
    "recent_query_results": 1
  },
  "storage": {
    "phase": "Bound",
    "requested": "40Gi",
    "storage_class": "longhorn"
  },
  "workloads": {
    "collectors": 7,
    "gateway": 1,
    "loki": 1
  }
}
```

**Interpretation**

The observation proves active logging health and all-node coverage at the
collection time. It does not establish long-term retention, throughput, or
disaster-recovery performance.

### `EV-006` — Actionable-failure coverage audit

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-006` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | tracked repository validator candidates |
| Tool and version | SAGE-actionable-failure-audit=4c369193731e9fc7832d8c2a0e1e2718a6210e86 |
| Expected result | Migrated coverage and remaining candidates are visible |
| Actual result | informational |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 scripts/sage/sage-actionable-failure-audit.py --summary
```

**Observed result**

```text
candidate_count: 74
registered_count: 2
migrated_count: 2
planned_count: 0
unregistered_count: 72
```

**Interpretation**

The audit proves coverage debt is visible. It does not prove that all 72
candidates are active validators or should be migrated.

### `EV-007` — Evidence input provenance and authority hashes

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-007` |
| Collected by | repository SAGE evidence orchestrator |
| Collected at | 2026-07-31T22:13:35-05:00 |
| Execution source | donbs-imac |
| Target | SAGE input bundle and authority inventory |
| Tool and version | sage-evidence-orchestrator=1.2-contract |
| Expected result | Original request, repository HEAD, authority hashes, and terminal evidence are traceable |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/evidence-input-provenance.json` |

**Command, query, source, or observation**

```text
Input bundle SHA-256: 6cea752b879d96796977f3aacd5e2b73df17572b0ca0d2dbc88d54bd1c16b111
```

**Observed result**

```text
The bundle contains 47 entries, including the metadata contract, template,
publisher, indexer, implementation authorities, repository context, and
terminal evidence.
```

**Interpretation**

The provenance artifact establishes the inputs used to generate this package.
The repository publisher remains the authority for final publication,
token replacement, checksum creation, and catalog reconciliation.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Shared actionable failures render complete recovery guidance | `EV-001`; `EV-002` | complete contract and passing regressions | passed | pass |
| `AC-002` | Validator failures remain distinct from target failures | `EV-003` | runtime wrapper reports validation-not-completed | passed | pass |
| `AC-003` | Tagged YAML metadata does not require secret decryption | `EV-004` | plain gate parsed and tagged values opaque | passed | pass |
| `AC-004` | Active logging releases match repository locks | `EV-005` | Loki `18.5.4`; collector `1.0.9` | matched | pass |
| `AC-005` | Logging workloads and storage are healthy | `EV-005` | 7 collectors, Loki `1/1`, gateway `1/1`, Bound `40Gi` Longhorn | observed | pass |
| `AC-006` | Recent Loki data covers every current node | `EV-005` | all seven nodes represented | observed | pass |
| `AC-007` | Remaining migration debt is explicitly visible | `EV-006` | counts and candidate list reported | observed | pass |
| `AC-008` | Evidence inputs are traceable and hashed | `EV-007` | original request, authority inventory, transcript, bundle digest | present | pass |

### Functional verification

```bash
make sage-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

Observed:

```text
Kalaxy3 SAGE actionable failure self-test: PASS
Kalaxy3 centralized logging runtime validation: PASS
SAGE validator runtime: PASS (centralized_logging.runtime)
```

### Negative verification

```bash
make -C infrastructure/k3s-homelab centralized-logging-render
```

Observed:

```text
The active lifecycle rejects the staged render validator and directs the
operator to make centralized-logging-runtime-validate.
```

## Idempotency and repeatability

### First accepted run

The framework and validator changes were applied in four small commits. Earlier
helper failures stopped before commit and preserved the working state for
repair.

### Steady-state rerun

Framework self-tests, the YAML metadata self-test, the live runtime validator,
the evidence index check, and evidence guardrails passed on rerun. The final
feature branch was clean and synchronized at `4c369193731e9fc7832d8c2a0e1e2718a6210e86` before evidence
capture.

### Interpretation

The validators are repeatable read-only checks. The evidence publisher is
responsible for deterministic token replacement, checksum creation, catalog
reconciliation, one evidence commit, and push. Live runtime output may change
as cluster topology or logs change.

## Security, privacy, and evidence handling

### Security controls

- The opaque-tag loader discards tagged payload content and retains only the tag.
- Opaque values reject boolean coercion to prevent accidental use as ordinary
  metadata.
- Repository-managed Python, Ansible, Helm, kubeconfig, and SSH trust checks
  passed.
- The package includes hashes rather than copying secret-bearing authority
  files into permanent artifacts.
- The publisher scans record and text artifacts for high-confidence secret
  patterns.

### Sensitive material excluded

- No Vault ciphertext, credentials, tokens, passwords, private keys,
  Kubernetes Secret values, or authentication hashes are included.
- Node IP addresses are not needed for the validated claim and are recorded as
  `not-applicable`.
- The original input bundle is referenced by checksum rather than embedded in
  the publication payload.

### Redactions and omissions

- Encrypted YAML payloads are omitted.
- Full user home paths appear only where needed for terminal provenance.
- kubectl and PyYAML versions were not captured.

### Residual security risk

A future validator could bypass the opaque loader or print tagged source text.
The SAGE contract, source review, self-tests, and secret scanning reduce but do
not eliminate that risk.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Wrong Ansible interpreter | Actionable interpreter assertion | Untrusted or mismatched validation environment | Use repository `.venv/bin/ansible-playbook` |
| Staged validator used after activation | Lifecycle assertion | Invalid result and possible pressure to change state | Run `make centralized-logging-runtime-validate` |
| Validator import or internal exception | SAGE validator runner | Validation does not complete | Preserve traceback, repair runtime, add regression test |
| Helper truncation or missing entry point | Helper self-test and startup marker | Silent no-op | Reject helper, restore complete entry point, rerun |
| Unknown YAML tag | Metadata loader self-test | Validator bootstrap failure | Use opaque-tag loader; never decrypt for unrelated metadata |
| Loki API unavailable | Runtime validator | Cannot prove queryability | Inspect gateway, port-forward, pods, service, and events |
| Node missing from Loki labels | All-node coverage check | Logging gap for that node | Inspect collector placement and labels, then revalidate |
| Catalog or package drift | Publisher and indexer checks | Publication blocked | Correct schema/package and rerun standard commands |

### Rollback

For the unmerged feature branch:

```bash
git switch feature/actionable-guardrail-recovery
git revert 4c369193731e9fc7832d8c2a0e1e2718a6210e86
git revert 054f625f8c76b41b012bc86c1053f0fb96054d8b
git revert 3aeac1ebe4037907876efbaf9c01d0225f410a11
git revert 78b839d8e852905e4d216d017c1eb6db3fe8285f
```

Reverts should be reviewed and validated rather than used to bypass a current
failure. If the branch has merged, perform the reverts through a separate
reviewed branch.

### Rebuild procedure

1. Clone `donb4iu/Kalaxy3` and check out the commit or merged descendant that
   contains `4c369193731e9fc7832d8c2a0e1e2718a6210e86`.
2. Recreate the repository-managed homelab virtual environment and controller
   tools through existing bootstrap procedures.
3. Run `make sage-self-test`.
4. Run `make -C infrastructure/k3s-homelab cluster-guardrails`.
5. Confirm `deploy_centralized_logging: true` through the opaque metadata path.
6. Run `make -C infrastructure/k3s-homelab centralized-logging-runtime-validate`.
7. Confirm chart locks, seven collectors, workload readiness, Bound Longhorn
   storage, datasource configuration, recent query results, and all-node
   coverage.
8. Re-run `python3 scripts/sage/sage-index.py check`.

### Data durability and backup impact

The change adds validation and governance code; it does not modify Loki data,
PVC contents, reclaim policy, or backups. The live observation confirms a Bound
Longhorn PVC but does not test backup restoration, recovery point, or recovery
time.

## Operational considerations and observability

### Health signals

- Helm release status and locked chart version.
- Fluent Bit desired, ready, and available collector counts.
- Loki StatefulSet ready replicas.
- Loki gateway available replicas.
- Loki pod readiness and restart state.
- Loki PVC phase, requested size, and StorageClass.
- Grafana datasource ConfigMaps.
- Loki API labels, recent query results, and node coverage.
- Actionable-failure audit counts.
- SAGE self-test and guardrail results.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3
make sage-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
python3 scripts/sage/sage-actionable-failure-audit.py --summary
```

### Capacity, performance, cost, and sustainability

- **Capacity:** the record confirms a `40Gi` Loki PVC but does not measure
  retention headroom.
- **Performance:** one recent query succeeded; latency and sustained ingestion
  were not benchmarked.
- **Cost:** no new runtime workload was deployed by this change; validator
  execution is transient.
- **Sustainability/power:** no measurable ongoing power increase is claimed.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | `work_started_at` is `not-captured`; only completion and collection times are authoritative. | Session duration cannot be calculated. | Kalaxy3 architecture | next evidence session |
| `GAP-002` | technical-debt | Audit reports 72 unregistered candidates that require classification before migration. | Some active validators may still fail non-actionably. | Kalaxy3 architecture | prioritize by operational risk |
| `GAP-003` | limitation | Candidate count includes possible historical, generated, bootstrap-only, or false-positive files. | Raw count overstates confirmed validator debt. | Kalaxy3 architecture | candidate classification work |
| `GAP-004` | evidence-gap | kubectl and PyYAML versions were not captured. | Tool-version reproducibility is incomplete for those two tools. | Kalaxy3 architecture | next runtime validator edit |
| `GAP-005` | evidence-gap | Long-term retention, ingestion volume, query latency, and restore behavior were not tested. | Runtime PASS is bounded to current health and one recent result. | Kalaxy3 architecture | when retention or DR is evaluated |
| `GAP-006` | risk | The active validator uses live cluster access and may fail because of controller connectivity rather than logging health. | Operators must distinguish access failure from target failure. | Kalaxy3 architecture | any runtime validation failure |
| `GAP-007` | governance | Reviewer is pending. | Status is validated, not accepted. | Kalaxy3 architecture | PR review |

## Troubleshooting

### Validator reports a bootstrap or runtime failure

**Meaning**

The validator did not complete and therefore produced no trustworthy target
result.

**Checks**

```bash
make sage-validator-runtime-self-test
python3 scripts/sage/sage-actionable-failure-guardrail.py
```

**Recovery**

Preserve the traceback, verify repository-managed interpreter and dependencies,
repair the validator, add the exact case as a regression test, and rerun the
canonical target.

### Runtime validator fails on `!vault`

**Meaning**

A validator is using a general YAML loader rather than the repository opaque-tag
metadata loader.

**Checks**

```bash
make sage-yaml-metadata-self-test
grep -R "yaml.safe_load" infrastructure/k3s-homelab/scripts scripts/sage
```

**Recovery**

Use `scripts/sage/sage_yaml_metadata.py` for non-secret metadata. Do not decrypt
or print unrelated secret values.

### Staged validator rejects active logging

**Meaning**

The deployment is already active; the render-only validator is not the correct
lifecycle path.

**Checks**

```bash
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

**Recovery**

Do not change the activation gate solely to satisfy validation. Use the active
runtime target.

### A node is absent from Loki coverage

**Meaning**

The recent Loki label values do not include every current Kubernetes node.

**Checks**

```bash
kubectl get nodes
kubectl -n observability get daemonset fluent-bit-collector
kubectl -n observability get pods -o wide
```

**Recovery**

Correct collector scheduling, readiness, or label mapping, wait for recent log
ingestion, and rerun the runtime validator.

## Freshness, revalidation, and supersession

### Revalidate when

- the actionable-failure contract, catalog, renderer, runner, audit, or registry
  changes;
- a validator is migrated or a new validator family is added;
- Python, PyYAML, Ansible, Helm, kubectl, Loki, Fluent Bit, or Longhorn changes;
- centralized logging changes lifecycle state;
- cluster nodes, namespace, datasource, service, PVC, labels, or topology change;
- a collector, Loki, or gateway loses readiness;
- Loki retention, query, or ingestion requirements change;
- the evidence publisher, metadata contract, template, or indexer changes;
- an acceptance test no longer passes.

### Scheduled review

```text
event-based: review on any relevant validator, logging, cluster-topology, or SAGE publication change
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve this
record and evidence ID, and identify which framework and runtime claims remain
valid.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects completeness.
- [x] Owner, author, operator, and reviewer are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is recorded.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version or an explicit gap.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Idempotency and repeatability are bounded and documented.
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
| Owner | Kalaxy3 architecture | conditional | 2026-07-31 | Technical validation passed; governance review remains pending. |
| Reviewer | pending | pending | pending | Review through the feature-branch PR. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-actionable-guardrail-evidence-SAGE-K3-GUARDRAIL-20260731-001.zip

python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-actionable-guardrail-evidence-SAGE-K3-GUARDRAIL-20260731-001.zip   --push
```

The package uses evidence-only publication and binds lineage to
`4c369193731e9fc7832d8c2a0e1e2718a6210e86`. The publisher will replace the publication timestamp, create the
record checksum and publication manifest, reconcile generated indexes, commit
the evidence, and push the branch.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Terminal evidence | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/terminal-evidence.md` | `0a22381d6a46523d4a3c2b2a52fcb8b8cd547c28b26f568baaa400f9aa357703` | no | permanent with evidence ID |
| Evidence input provenance | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-001/evidence-input-provenance.json` | `3eb99bce49c25ad4b0ed81d15748f9378a48e354e10149739518266ea2bb1bda` | no | permanent with evidence ID |
| Input bundle | `kalaxy3-actionable-guardrail-evidence-inputs-20260731-221335.zip` | `6cea752b879d96796977f3aacd5e2b73df17572b0ca0d2dbc88d54bd1c16b111` | not embedded; source bundle may contain encrypted repository text | retain outside repository until publication review completes |

### Original requester language

```text
Generate a SAGE-compliant evidence record for the actionable guardrail recovery and active centralized-logging runtime validation completed on feature/actionable-guardrail-recovery. Include commits 78b839d, 3aeac1e, 054f625, and 4c36919. Preserve all available terminal evidence. Explain the invalid validator guidance, unmanaged Ansible interpreter failure, staged validator used after activation, dataclass dynamic-import bootstrap failure, silently truncated helper without an invoked main entry point, vault-tag YAML ConstructorError, brittle source-anchor repair failure, and the incorrect assumption that evidence generation used a generate subcommand. Explain the broader failure class and generic protection for each incident. Document the actionable-failure contract, shared renderer and catalog, validator runtime wrapper, real runtime-path tests, helper entry-point tests, opaque-tag YAML metadata loader, lifecycle routing, audit, and active logging runtime validator. Record Loki 18.5.4, Fluent Bit Collector 1.0.9, seven ready collectors, Loki 1/1, gateway 1/1, Bound 40Gi Longhorn storage, Grafana datasource configuration, recent Loki query results, and logs covering all seven nodes. Identify remaining validator-candidate classification and migration debt, remaining validation gaps, rollback, and rebuild guidance. Use the repository SAGE standard, metadata contract, template, policy, orchestrator, publisher, and indexer.
```

### Publication-package generation note

The repository orchestrator `capture` output was an input bundle, not a final
publication package. This schema 1.2 package adds `sage-package.json` and a
`payload/` tree and is intended for validation and publication only through
`scripts/sage/sage-publish.py`.
