---
evidence_id: SAGE-K3-OBS-20260804-001
schema_version: "1.2"
title: Active Centralized Logging Runtime Validation and SAGE-Governed Recovery Evidence
nav_title: Validate active centralized logging
nav_section: verification
nav_order: 240
summary: Validates Loki and Fluent Bit across all seven Kalaxy3 nodes, preserves failed operator paths, and records the repository-governed recovery and cluster guardrails.
primary_subject: Centralized logging
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: centralized-logging-validation-and-evidence-closeout-20260804
work_started_at: 2026-08-04T15:01:00-05:00
work_completed_at: 2026-08-04T15:55:00-05:00
evidence_collected_at: 2026-08-04T15:55:00-05:00
created_at: 2026-08-04T19:52:00-05:00
updated_at: 2026-08-04T20:04:09-05:00
valid_as_of: 2026-08-04
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
owner: Don Buddenbaum
author: OpenAI GPT-5.6 Thinking
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donb-mac-mini.local
controller_host: donb-mac-mini.local
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
  - longhorn-system
endpoints:
  - loki-gateway=http://loki-gateway.observability.svc.cluster.local
  - grafana=https://grafana.home.donb4iu.com
components:
  - loki-chart=18.5.4
  - fluent-bit-collector-chart=1.0.9
  - longhorn-chart=1.12.0
  - repository-helm=3.21.3+g1ad6e68
  - python=3.12.4
  - ansible-core=2.18.7
  - uv=0.11.32
  - kubectl=version-not-captured
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: cf6eee9976919be1ed5a9d283e8a609d740eee04
record_path: markdown/verification/kalaxy3-centralized-logging-runtime-validation-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001
confidence: high
tags:
  - sage
  - centralized-logging
  - loki
  - fluent-bit
  - observability
  - runtime-validation
relationships:
  verifies:
    - active centralized-logging runtime validation
    - Kalaxy3 cluster deployment guardrails
  depends_on:
    - SAGE-K3-OBS-20260728-002
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - SAGE-K3-OBS-20260728-001
    - SAGE-K3-GUARDRAIL-20260731-001
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-evidence-orchestrator.py capture
    - OpenAI GPT-5.6 Thinking evidence synthesis
  implemented_by:
    - cf6eee9976919be1ed5a9d283e8a609d740eee04
  revalidated_by:
    - none
---

# Active Centralized Logging Runtime Validation and SAGE-Governed Recovery Evidence

## Executive summary

The active Kalaxy3 centralized-logging deployment was technically validated on
August 4, 2026. Repository-owned validation confirmed Loki `18.5.4`, Fluent Bit
Collector `1.0.9`, seven collectors covering all seven cluster nodes, one Loki
gateway, one Loki workload, recent queryable log data, two Grafana data-source
ConfigMaps, and a bound `40Gi` Longhorn volume. The record is `validated`, not
`accepted`, because independent governance review remains pending. Failed
operator paths and the repository Helm bootstrap recovery are preserved as
separate evidence rather than being presented as successful validation.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBS-20260804-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Active Centralized Logging Runtime Validation and SAGE-Governed Recovery Evidence |
| **Navigation title** | Validate active centralized logging |
| **Navigation section** | verification |
| **Navigation order** | 240 |
| **Summary** | Validates Loki and Fluent Bit across all seven Kalaxy3 nodes, preserves failed operator paths, and records the repository-governed recovery and cluster guardrails. |
| **Primary subject** | Centralized logging |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | centralized-logging-validation-and-evidence-closeout-20260804 |
| **Started** | 2026-08-04T15:01:00-05:00 |
| **Completed** | 2026-08-04T15:55:00-05:00 |
| **Evidence collected** | 2026-08-04T15:55:00-05:00 |
| **Record created** | 2026-08-04T19:52:00-05:00 |
| **Record updated** | 2026-08-04T20:04:09-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago |
| **Valid as of** | 2026-08-04 |
| **Review due** | event-based |
| **Target record path** | markdown/verification/kalaxy3-centralized-logging-runtime-validation-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donb-mac-mini.local |
| **Controller host** | donb-mac-mini.local |
| **Nodes** | amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05 |
| **Node addresses** | not-applicable |
| **Namespaces** | observability; longhorn-system |
| **Endpoints** | loki-gateway=http://loki-gateway.observability.svc.cluster.local; grafana=https://grafana.home.donb4iu.com |
| **Components and versions** | loki-chart=18.5.4; fluent-bit-collector-chart=1.0.9; longhorn-chart=1.12.0; repository-helm=3.21.3+g1ad6e68; python=3.12.4; ansible-core=2.18.7; uv=0.11.32; kubectl=version-not-captured |
| **Owner** | Don Buddenbaum |
| **Author** | OpenAI GPT-5.6 Thinking |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Navigation contract

- The formal title identifies both runtime validation and governed recovery.
- The navigation title is the concise verification label used by generated indexes.
- The verification section groups this record with technical acceptance evidence.
- Navigation order `240` places the record deterministically within that section.
- The summary states the value of opening the record without overstating acceptance.
- The primary subject is centralized logging.
- `[TOC]` is present for page-level navigation.
- Historical records remain governed by the compatibility catalog and are not rewritten by this package.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** OpenAI GPT-5.6 Thinking; **operator:** Don Buddenbaum; **owner:** Don Buddenbaum; **reviewer:** pending; **affected users/teams:** Kalaxy3 operators and future maintainers. The operator executed the commands, the author synthesized the supplied bundle, and the owner remains accountable for acceptance. |
| **What** | Verified the active Loki and Fluent Bit centralized-logging runtime, its persistent storage, chart locks, node coverage, data queryability, and cluster guardrails. Preserved failed invocations and the repository Helm recovery separately from the accepted path. |
| **When** | **Completed:** 2026-08-04T15:55:00-05:00; **evidence collected:** 2026-08-04T15:55:00-05:00; **local timezone:** America/Chicago; **system timestamps:** America/Chicago; **valid as of:** 2026-08-04; **review due:** event-based. The supplied terminal session used local America/Chicago time. |
| **Where** | **Environment:** homelab; **cluster:** kalaxy3; **execution host:** donb-mac-mini.local; **controller:** donb-mac-mini.local; **nodes:** amd64-01, amd64-02, arm64-01, arm64-02, arm64-03, arm64-04, arm64-05; **addresses:** not-applicable to the validated claims; **namespaces:** observability, longhorn-system; **endpoints:** loki-gateway=http://loki-gateway.observability.svc.cluster.local, grafana=https://grafana.home.donb4iu.com; **record:** markdown/verification/kalaxy3-centralized-logging-runtime-validation-evidence.md. |
| **Why** | Centralized logging needed a trustworthy post-activation acceptance result and a durable record of both successful and failed operator paths. Repository-owned workflows were preferred over one-off wrappers so authority, tool bootstrap, chart locks, recovery, and evidence publication remain reproducible. |
| **How** | Synchronized clean `main`, ran SAGE discovery with the literal request, used the canonical runtime validator, bootstrapped repository Helm after a fail-closed result, reran runtime validation, executed cluster guardrails from the SAGE-discovered homelab working directory, captured an immutable input bundle, and synthesized this package under schema 1.2. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Active Loki and Fluent Bit Collector release versions and workload counts.
- Log coverage across all seven named Kalaxy3 nodes.
- Recent Loki query success and Grafana data-source presence.
- Loki Longhorn volume phase, requested size, and storage class.
- Repository Helm bootstrap recovery and cluster-wide deployment guardrails.
- SAGE discovery, evidence baselines, and evidence-input capture.

### Out of scope

- Fresh deployment or configuration mutation during this evidence session.
- Independent restore testing of Loki data from backup.
- Long-duration load, loss, latency, or capacity testing.
- Kubecost post-deployment comparison, because Kubecost was disabled in the supplied cluster guardrail output.
- Governance acceptance by a named reviewer.

### Nonclaims

This record does **not** claim:

- zero log loss under every node, network, or storage failure;
- verified disaster recovery or backup restoration;
- production-grade high availability, because Loki is intentionally monolithic with one replica;
- a measured cost or power delta from centralized logging;
- acceptance beyond the captured technical validation boundary.

## Final accepted state

```text
Technical validation accepted: active centralized logging is healthy at commit
cf6eee9976919be1ed5a9d283e8a609d740eee04; governance acceptance remains pending.
```

| Item | Accepted result |
|---|---|
| Activation gate | `deploy_centralized_logging: true` |
| Loki release | `18.5.4` in `observability` |
| Fluent Bit Collector release | `1.0.9` in `observability` |
| Collector coverage | Seven collectors covering seven named nodes |
| Loki data | At least one recent query result with the `node` label |
| Workloads | Seven collectors, one gateway, one Loki workload |
| Storage | Bound `40Gi` PVC on `longhorn` |
| Grafana integration | Two data-source ConfigMaps observed |
| Cluster controls | Repository bootstrap, source, deployment, access, and lock-reconciliation guardrails passed |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Centralized logging was activated by repository configuration at the validated commit. | critical | `EV-001`; `EV-004` | supported | high |
| `CLM-002` | Loki and Fluent Bit Collector were installed at the repository-locked versions. | critical | `EV-001`; `EV-003`; `EV-004` | supported | high |
| `CLM-003` | Seven collectors provided observed Loki node-label coverage for all seven named nodes. | critical | `EV-003` | supported | high |
| `CLM-004` | Loki persistent storage was bound as `40Gi` on Longhorn. | critical | `EV-001`; `EV-003` | supported | high |
| `CLM-005` | The canonical runtime validator recovered after repository Helm bootstrap and then passed. | high | `EV-002`; `EV-003`; `EV-005` | supported | high |
| `CLM-006` | The homelab cluster guardrail composition passed and reconciled eight installed locked releases. | high | `EV-004` | supported | high |
| `CLM-007` | Failed operator paths were preserved and were not treated as successful validation. | normal | `EV-005` | supported | high |
| `CLM-008` | Evidence reconciliation and orchestration baselines passed before package generation. | normal | `EV-006` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The deployment was already active, but the Mac mini checkout was stale and the
controller lacked repository Helm. Earlier assistance also introduced an
unnecessary downloaded orchestration wrapper and invoked one target from the
wrong working directory. A trustworthy closeout required proving the live state
through repository-owned validators and preserving the failed paths.

### Decision

Use the repository-owned SAGE discovery, controller bootstrap, centralized-
logging runtime validator, homelab cluster guardrail composition, evidence
orchestrator, and publisher contract. Classify the resulting record as
`validated` until a named reviewer accepts it.

### Decision drivers

- Deterministic authority and exact chart locks.
- Fail-closed validator behavior.
- Reusable repository primitives instead of session-specific wrappers.
- Preservation of failure and recovery evidence.
- No cluster mutation during evidence closeout.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Downloaded validation wrapper | One command and local receipt | Duplicated orchestration, omitted the governed request, and failed before canonical validation | rejected |
| Ad hoc `kubectl` and `helm` checks | Fast manual inspection | Bypasses repository wrappers, authority, locks, and SAGE failure retrieval | rejected |
| Repository-owned validator and guardrails | Reusable, locked, fail-closed, evidence-aware | Requires controller bootstrap and correct working directory | accepted |
| Defer validation until later | Avoids immediate bootstrap work | Leaves active logging without current acceptance evidence | rejected |

### Tradeoffs and consequences

- The accepted path adds bootstrap steps but makes the controller reproducible.
- Monolithic Loki with one replica is simpler and lower-cost but is not highly available.
- `validated` communicates technical success while preserving the pending review boundary.
- Full disaster-recovery and cost-effectiveness claims remain open.

## Architecture or change description

```text
Kubernetes nodes (7)
  -> Fluent Bit Collector DaemonSet (7 pods)
  -> loki-gateway.observability.svc.cluster.local:80
  -> Loki monolithic singleBinary (1 pod, amd64 platform-services pool)
  -> 40Gi Longhorn persistent volume

Grafana
  -> provisioned Loki data source
  -> in-cluster Loki gateway
```

### Before

The session began with a clean but stale Mac mini checkout and no repository
Helm binary. Active logging existed, but current runtime acceptance had not yet
been obtained from that controller.

### After

The controller was synchronized to `cf6eee9976919be1ed5a9d283e8a609d740eee04`, repository Helm
`3.21.3+g1ad6e68` was installed and checksum-verified, the runtime validator
passed, and the homelab cluster guardrails passed. No repository or cluster
configuration was intentionally changed by the evidence closeout.

## Source of truth and implementation lineage

### Repository files

```text
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/helm-chart-lock.json
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2
infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime-self-test.py
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime-source-self-test.py
scripts/sage/sage-validator-runner.py
scripts/sage/sage-evidence-orchestrator.py
scripts/sage/sage-publish.py
```

### Implementation commit

```text
cf6eee9976919be1ed5a9d283e8a609d740eee04
Update values.yaml [skip ci]
```

The supplied repository evidence identifies this as the clean synchronized HEAD
used for runtime validation. Earlier centralized-logging implementation lineage
is preserved by related records and Git history rather than reconstructed here.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| Loki chart | 18.5.4 | `helm-chart-lock.json` and runtime validator |
| Fluent Bit Collector chart | 1.0.9 | `helm-chart-lock.json` and runtime validator |
| Longhorn chart | 1.12.0 | `helm-chart-lock.json` and cluster guardrails |
| Repository Helm | 3.21.3+g1ad6e68 | controller bootstrap output |
| Python | 3.12.4 | controller preflight output |
| ansible-core | 2.18.7 | controller preflight output |
| uv | 0.11.32 | controller preflight output |
| kubectl | version-not-captured | runtime validator reported the binary path only |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | `helm-chart-lock.json`, repository Helm installer, `.venv`, and controller preflight |
| Controller bootstrap | `make -C infrastructure/k3s-homelab controller-helm` |
| Controller preflight | Core, Helm, cluster, SSH, Ansible privilege, and playbook syntax checks passed in `EV-004` |
| Controller host | donb-mac-mini.local |
| Execution host | donb-mac-mini.local |
| Machine-local authoritative state | None identified; controller binaries and trust are validated against repository contracts |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual runtime changes were reconciled into repository-owned automation or no manual change was made in this session.
- [x] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
deploy_centralized_logging: true
centralized_logging_namespace: observability
centralized_logging_workload_pool: platform-services
centralized_logging_expected_node: amd64-02
loki_storage_class: longhorn
loki_storage_size: 40Gi
loki_retention_period: 168h
```

## Prerequisites and assumptions

### Proven prerequisites

- Clean synchronized `main` at `cf6eee9976919be1ed5a9d283e8a609d740eee04` was established before validation (`EV-006`).
- SAGE change discovery passed for runtime validation and evidence closeout (`EV-006`).
- Repository Helm was installed at the expected version and SHA-256 (`EV-002`).
- Repository virtual environment, Python, Ansible, collections, SSH trust, and privilege escalation passed (`EV-004`).
- Repository kubeconfig and context provided read-only Helm access (`EV-004`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | One recent Loki query result is sufficient to prove current end-to-end ingestion, not sustained completeness. | Intermittent or selective loss could remain undetected. | Add scheduled multi-window ingestion and loss checks. |
| `ASM-002` | The supplied terminal transcript accurately preserves the material command outputs. | Omitted output could weaken traceability. | Retain raw receipts and rerun canonical validators at review time. |
| `ASM-003` | No cluster mutation occurred during validation targets. | An unexpected mutating target could alter the observed system. | Review target definitions and compare Git and cluster state during revalidation. |

The assumptions bound the claims but do not prevent technical `validated` status.

## Implementation procedure

### Preparation

```bash
python3 ~/Downloads/kalaxy3_macmini_repo_audit.py
python3 ~/Downloads/kalaxy3_sync_main_and_reaudit.py
SAGE_REQUEST="Validate the active centralized-logging implementation on synchronized main, run the repository-owned validation workflow, and identify the first unresolved hardening gap without modifying repository or cluster state." make -C ~/dvlp/Kalaxy3 sage-preflight
```

The downloaded audit and synchronization helpers were session bootstrap aids,
not repository evidence-generation primitives. The one-off validation wrapper
was rejected after it duplicated existing repository behavior.

### Execution

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab controller-helm
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab cluster-guardrails
make -C ~/dvlp/Kalaxy3 sage-index-check sage-evidence-guardrail
python3 ~/dvlp/Kalaxy3/scripts/sage/sage-evidence-orchestrator.py capture --request "Create and reconcile the complete SAGE evidence package for the active centralized-logging deployment and validation, using repository-owned evidence workflows and all available terminal evidence, including the repository Helm bootstrap recovery, runtime validation, the failed root cluster-guardrails invocation, and the successful homelab cluster guardrails; reconcile indexes and publication artifacts without changing cluster state." --terminal-evidence ~/Downloads/kalaxy3-centralized-logging-terminal-evidence-20260804.txt
```

### Expected change

Obtain a trustworthy read-only validation result, recover any approved controller
bootstrap gap, preserve failures, and create one evidence-input bundle without
changing cluster configuration.

### Observed change

The initial validator was blocked because repository Helm was missing. The
canonical bootstrap installed and verified Helm. The rerun passed with seven
collectors and all seven nodes covered. Cluster guardrails then passed. The
evidence orchestrator created `/private/tmp/kalaxy3-sage-evidence-inputs.zip`.

### Failed or superseded paths

- A 400-line downloaded validation wrapper duplicated repository orchestration and failed because it omitted `SAGE_REQUEST`.
- Direct `sage-preflight` without `SAGE_REQUEST` failed closed as designed.
- Runtime validation before repository Helm bootstrap was blocked and produced a SAGE failure-retrieval receipt.
- Root-level `cluster-guardrails` failed because SAGE assigned that target to `infrastructure/k3s-homelab`.
- None of these failures was reported as a logging validation pass.

## Evidence items

### `EV-001` — Repository configuration and locked dependency snapshot

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`; `CLM-002`; `CLM-004` |
| Collected by | SAGE evidence orchestrator and OpenAI GPT-5.6 Thinking |
| Collected at | 2026-08-04T19:52:00-05:00 |
| Execution source | Captured repository authority bundle |
| Target | Kalaxy3 centralized-logging source of truth |
| Tool and version | sage-evidence-orchestrator=repository commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Active gate, exact chart locks, Longhorn persistence, and collector routing are present |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/repository-authority-snapshot.md` SHA-256 `df74e2a2890e70f89daeba8643597510a206e28aee6bcac2206bd770582df014` |

**Command, query, source, or observation**

```text
Read the authoritative configuration files supplied in the immutable SAGE input bundle.
```

**Observed result**

```text
deploy_centralized_logging=true
loki=18.5.4
fluent-bit-collector=1.0.9
loki_storage_class=longhorn
loki_storage_size=40Gi
loki_retention_period=168h
```

**Interpretation**

`EV-001` proves the repository-declared intended state and exact locked versions.
It does not alone prove that the live cluster matched that state.

### `EV-002` — Repository Helm bootstrap recovery

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-04T15:23:00-05:00 |
| Execution source | donb-mac-mini.local terminal |
| Target | Repository-controlled Helm toolchain |
| Tool and version | install-repository-helm.py=commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Install and checksum-verify the repository Helm binary |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/terminal-evidence-20260804.txt` SHA-256 `7e0320f7037ea00d0e46210a475cee3ccd0e5eccff03d81549794390d85d687d` |

**Command, query, source, or observation**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab controller-helm
```

**Observed result**

```text
PASS repository Helm v3.21.3+g1ad6e68 (darwin-amd64)
PASS Helm binary SHA-256 f4f7708f4af5dd29fd0061b0cc3cb5b47648ff3b7a0ff6ab8a134ba83f392940
```

**Interpretation**

`EV-002` proves the approved controller recovery restored the missing repository
Helm dependency. It does not itself validate centralized logging.

### `EV-003` — Active centralized-logging runtime validation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-003`; `CLM-004`; `CLM-005` |
| Collected by | Don Buddenbaum through `sage-validator-runner.py` |
| Collected at | 2026-08-04T15:25:00-05:00 |
| Execution source | donb-mac-mini.local |
| Target | `kalaxy3` cluster, `observability` and Longhorn storage |
| Tool and version | centralized_logging.runtime=commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Locked releases, healthy workloads, recent log data, all-node coverage, data source presence, and bound storage |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/centralized-logging-runtime-validation.json` SHA-256 `9ec1661030e4e1b87d35971a4d290f43e82bef63c2f37a8bd812f87ee5067329` |

**Command, query, source, or observation**

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
```

**Observed result**

```text
Kalaxy3 centralized logging runtime validation: PASS
collectors=7
gateway=1
loki=1
covered_nodes=amd64-01,amd64-02,arm64-01,arm64-02,arm64-03,arm64-04,arm64-05
recent_query_results=1
storage_phase=Bound
storage_requested=40Gi
storage_class=longhorn
datasource_configmaps=2
SAGE validator runtime: PASS (centralized_logging.runtime)
```

**Interpretation**

`EV-003` is the primary direct runtime evidence. It supports the bounded health,
coverage, release, data, integration, and storage claims as of the captured run.

### `EV-004` — Homelab cluster deployment guardrails

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001`; `CLM-002`; `CLM-006` |
| Collected by | Don Buddenbaum through repository Make composition |
| Collected at | 2026-08-04T15:34:00-05:00 |
| Execution source | donb-mac-mini.local |
| Target | Kalaxy3 controller, inventory hosts, Helm releases, and cluster access |
| Tool and version | cluster-guardrails=commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Controller, authority, source, access, syntax, deployment, and lock reconciliation pass |
| Actual result | pass |
| Confidence | high |
| Sensitive data | internal node names; no credentials |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/terminal-evidence-20260804.txt` SHA-256 `7e0320f7037ea00d0e46210a475cee3ccd0e5eccff03d81549794390d85d687d` |

**Command, query, source, or observation**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab cluster-guardrails
```

**Observed result**

```text
Kalaxy3 controller preflight (core): PASS
Kalaxy3 SAGE discovery guardrail: PASS
Kalaxy3 Helm repository guardrail: PASS
Kalaxy3 SAGE source guardrails: PASS
Kalaxy3 Ansible access preflight (all): PASS
Kalaxy3 SAGE bootstrap guardrails: PASS
Kalaxy3 controller preflight (helm): PASS
Kalaxy3 controller preflight (cluster): PASS
Kalaxy3 SAGE deployment guardrail: PASS
PASS 8 installed locked releases; 0 permitted new releases
Kalaxy3 Helm lock reconciliation: PASS
Kalaxy3 SAGE cluster deployment guardrails: PASS
```

**Interpretation**

`EV-004` proves the broader repository and controller contract passed and that
installed enabled releases matched the lock. It complements rather than replaces
the runtime validator.

### `EV-005` — Failure-triggered SAGE retrieval and corrected operator paths

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-005`; `CLM-007` |
| Collected by | Don Buddenbaum and SAGE validator runner |
| Collected at | 2026-08-04T15:22:34-05:00 |
| Execution source | donb-mac-mini.local and local SAGE state |
| Target | Runtime-validator bootstrap and operator working-directory selection |
| Tool and version | sage-validator-runner=commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Invalid or incomplete execution paths fail closed and provide recovery |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/failure-recovery-ledger.md` SHA-256 `b78d7034417723e12b6c903f3208e650c32d2b655554aff2daccf5fcc12bd982` |

**Command, query, source, or observation**

```text
Run canonical validation before repository Helm bootstrap; invoke cluster guardrails from the wrong root directory.
```

**Observed result**

```text
SAGE ACTION BLOCKED
Repository Helm is missing. Run: make controller-helm

make: *** No rule to make target `cluster-guardrails'. Stop.
```

**Interpretation**

`EV-005` proves failed paths were visible, preserved, and corrected through
repository authority. It does not count either failed path as runtime success.

### `EV-006` — Repository synchronization and evidence baselines

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-008` |
| Collected by | Don Buddenbaum through SAGE repository workflows |
| Collected at | 2026-08-04T15:55:00-05:00 |
| Execution source | donb-mac-mini.local and captured SAGE input bundle |
| Target | Repository `main`, evidence catalog, template, navigation, and orchestration contracts |
| Tool and version | sage-evidence-orchestrator=commit cf6eee9976919be1ed5a9d283e8a609d740eee04 |
| Expected result | Clean synchronized repository, zero stale generated paths, passing evidence guardrails, and one immutable generation bundle |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/input-bundle-manifest.json` SHA-256 `6d51cb010b7f548d3224b68db1fb8ceba7dbb2190e159d7707ccdbbc1d95ec8c` |

**Command, query, source, or observation**

```bash
make -C ~/dvlp/Kalaxy3 sage-index-check sage-evidence-guardrail
python3 scripts/sage/sage-evidence-orchestrator.py capture --request "..." --terminal-evidence ~/Downloads/kalaxy3-centralized-logging-terminal-evidence-20260804.txt
```

**Observed result**

```text
SAGE evidence reconciliation: PASS
Records: 37
Generated paths: 51
Changed paths: 0
Kalaxy3 SAGE evidence orchestration guardrail: PASS
Kalaxy3 SAGE evidence template guardrail: PASS
Kalaxy3 evidence navigation architecture guardrail: PASS
Kalaxy3 SAGE evidence-generation inputs: PASS
Bundle: /private/tmp/kalaxy3-sage-evidence-inputs.zip
```

**Interpretation**

`EV-006` proves the generation boundary was clean and governed. Legacy curation
notices remained pre-existing review items and did not alter generated paths.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Runtime validator completes through the repository wrapper | `EV-003` | PASS | PASS | pass |
| `AC-002` | Locked logging releases are installed | `EV-001`; `EV-003`; `EV-004` | Loki `18.5.4`, collector `1.0.9` | Exact versions observed | pass |
| `AC-003` | Every named node is represented in recent Loki data | `EV-003` | Seven named nodes | Seven named nodes | pass |
| `AC-004` | Collector workload covers every cluster node | `EV-003` | Seven collectors | Seven collectors | pass |
| `AC-005` | Loki storage is persistent and bound | `EV-001`; `EV-003` | Bound `40Gi` Longhorn | Bound `40Gi` Longhorn | pass |
| `AC-006` | Repository and cluster deployment guardrails pass | `EV-004` | PASS | PASS | pass |
| `AC-007` | Failed paths remain distinguishable from accepted results | `EV-005` | Preserved and corrected | Preserved and corrected | pass |
| `AC-008` | Evidence baselines and capture pass without cluster mutation | `EV-006` | PASS | PASS | pass |

### Functional verification

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
```

Observed:

```text
Kalaxy3 centralized logging runtime validation: PASS
SAGE validator runtime: PASS (centralized_logging.runtime)
```

### Negative verification

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
# before repository Helm bootstrap
```

Observed:

```text
SAGE ACTION BLOCKED
Repository Helm is missing. Run: make controller-helm
```

The fail-closed result prevented a bootstrap failure from being misreported as a
logging validation result.

## Idempotency and repeatability

### First accepted run

```text
Repository Helm was bootstrapped, then centralized-logging runtime validation
and cluster guardrails passed.
```

### Steady-state rerun

```text
The runtime validator is read-only and can be rerun through the same Make target.
The evidence-index baseline reported Changed paths: 0 before package creation.
A post-bootstrap second runtime execution passed without another repair.
```

### Interpretation

The canonical validation path is repeatable and intended to be read-only. The
session does not provide a full Ansible `changed=0` deployment rerun, so it does
not claim end-to-end deployment idempotency. Repository Helm installation is
checksum-pinned and reported PASS when invoked again during cluster guardrails.

## Security, privacy, and evidence handling

### Security controls

- Repository-managed Helm, uv, Python environment, kubeconfig, context, and SSH trust were validated.
- Helm repositories require HTTPS, unique names and URLs, and pinned URL fingerprints.
- Deployment releases must match the repository lock.
- Validation used repository wrappers rather than inherited bare Helm state.
- The package scanner and publisher reject common private-key, kubeconfig-key, bearer-token, and GitHub-token patterns.

### Sensitive material excluded

- No credentials, tokens, passwords, private keys, Kubernetes Secret values, or authentication hashes are included.
- Terminal evidence was reduced to material commands and results.
- Internal node names and service endpoints are retained under `classification: internal` because they are needed for reproducibility.

### Redactions and omissions

- Node IP addresses were not required for the bounded runtime claims and are represented as `not-applicable` in canonical metadata.
- Raw kubeconfig, SSH files, and complete environment variables were excluded.
- Verbose guardrail output was summarized where the exact line was not necessary to support a claim; the supplied terminal artifact retains the session-level evidence.

### Residual security risk

- Internal topology metadata could aid reconnaissance if published outside the intended repository. Keep the record within the repository's internal evidence classification and access controls.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Repository Helm missing | Runtime validator reports missing repository Helm and SAGE blocks the result | Validation cannot begin | `make -C infrastructure/k3s-homelab controller-helm`, then rerun canonical validation |
| Fluent Bit collector absent on a node | Collector count or Loki node coverage differs from seven | Node logs may be unavailable | Inspect DaemonSet rollout, node tolerations, pod events, and retry after correction |
| Loki PVC not bound | Runtime storage phase differs from `Bound` | Loki may be unavailable or non-durable | Inspect PVC, Longhorn volume, replicas, node placement, and storage events |
| Loki gateway or query path unavailable | Runtime validator cannot obtain recent results | Centralized search is unavailable | Inspect gateway, service endpoints, Loki pod logs, and network policy |
| Chart drift | Helm lock reconciliation fails | Runtime may differ from repository authority | Reconcile through locked repository deployment workflow; do not bypass the lock |
| Wrong Make working directory | No target is found | Validation sequence stops | Use the working directory assigned by SAGE discovery |

### Rollback

```text
No rollback was executed because this session performed validation and evidence
capture only. A future rollback must use the repository-owned observability
playbook and activation gate, preserve the retained Longhorn volume according
to policy, and obtain a new SAGE preflight before mutation.
```

### Rebuild procedure

1. Obtain a clean `main` checkout of `donb4iu/Kalaxy3`.
2. Run the repository controller preflight and bootstrap targets, including repository Helm.
3. Apply the repository-owned observability phase with centralized logging activated.
4. Confirm locked Loki and Fluent Bit Collector releases in `observability`.
5. Run `centralized-logging-runtime-validate` and homelab `cluster-guardrails`.
6. Recreate evidence through the repository evidence orchestrator and publisher.

### Data durability and backup impact

Loki uses a `40Gi` Longhorn-backed filesystem volume with retain behavior on
scale-down and deletion in the bundled values. The runtime validator proved the
PVC was bound, but this session did not capture a backup, restore test, recovery
point objective, or recovery time objective. Monolithic single-replica Loki is
a reliability limitation even when the underlying Longhorn volume has storage
replication.

## Operational considerations and observability

### Health signals

- `centralized-logging-runtime-validate` PASS or fail-closed output.
- Collector count versus expected cluster node count.
- Loki recent-query result count and set of `node` label values.
- Loki gateway and single-binary workload readiness.
- Loki PVC phase, storage class, and requested capacity.
- Grafana data-source ConfigMap count.
- Helm lock reconciliation and cluster guardrail status.
- Fluent Bit ServiceMonitor and dashboard resources declared by repository values.

### Routine verification

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab cluster-guardrails
```

### Capacity, performance, cost, and sustainability

- **Capacity:** Loki has `40Gi` requested storage and `168h` retention; no utilization or exhaustion forecast was captured.
- **Performance:** The record proves query success, not ingestion latency, query latency, or peak throughput.
- **Cost:** Additional collector, gateway, Loki, and Longhorn resources consume cluster capacity; Kubecost comparison was not available because its release was disabled in the captured guardrail output.
- **Sustainability/power:** No direct wattage measurement was captured for centralized logging.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | `kubectl` version was not captured; metadata records `kubectl=version-not-captured`. | Limits exact controller-tool reproduction evidence. | Don Buddenbaum | Next controller preflight or validator enhancement |
| `GAP-002` | evidence-gap | No Loki backup or restore test was performed. | Disaster-recovery claims remain unverified. | Don Buddenbaum | Before relying on logging for incident forensics |
| `GAP-003` | limitation | Loki uses one monolithic replica. | Pod or node disruption can cause service interruption despite persistent storage. | Don Buddenbaum | Availability requirement changes |
| `GAP-004` | evidence-gap | No sustained ingestion-loss, latency, or load test was captured. | Intermittent loss or performance limits may remain undetected. | Don Buddenbaum | Before raising retention or workload volume materially |
| `GAP-005` | evidence-gap | No post-deployment Kubecost comparison was available because Kubecost was disabled. | Cost impact is not quantified. | Don Buddenbaum | Kubecost re-enabled and stable |
| `GAP-006` | governance | Named reviewer acceptance is pending. | Record is validated but not accepted. | Don Buddenbaum | Evidence publication review |
| `GAP-007` | technical-debt | The session initially used a large downloaded validation wrapper instead of a thin composition of repository primitives. | Repeats a known workflow failure and increases maintenance risk. | Don Buddenbaum | Add or enforce root-level composition and file-delivery guardrail coverage |
| `GAP-008` | technical-debt | `cluster-guardrails` was not exposed at repository root and was first invoked from the wrong directory. | Operator path is easier to misuse. | Don Buddenbaum | Decide whether root delegation belongs in the operating contract |

## Troubleshooting

### Runtime validator reports repository Helm is missing

**Meaning**

The approved validator cannot inspect Helm state because the repository-managed
binary is absent. This is a controller bootstrap failure, not a logging result.

**Checks**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab controller-helm
```

**Recovery**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab controller-helm
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
```

### Root Make reports no `cluster-guardrails` target

**Meaning**

The target belongs to the homelab working directory identified by SAGE discovery.

**Checks**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab -n cluster-guardrails
```

**Recovery**

```bash
make -C ~/dvlp/Kalaxy3/infrastructure/k3s-homelab cluster-guardrails
```

### Runtime validation reports missing node coverage

**Meaning**

At least one expected cluster node is absent from recent Loki `node` labels or a
collector is missing.

**Checks**

```bash
make -C ~/dvlp/Kalaxy3 centralized-logging-runtime-validate
```

**Recovery**

Use the validator output to inspect the Fluent Bit Collector DaemonSet, missing
node pod placement, gateway delivery, and Loki ingestion. Apply corrections only
through a new governed SAGE change request.

## Freshness, revalidation, and supersession

### Revalidate when

- Loki, Fluent Bit Collector, Longhorn, Helm, Python, Ansible, uv, or kubectl versions change;
- `deploy_centralized_logging`, namespace, workload-pool, storage, retention, labels, routing, or Grafana data-source configuration changes;
- a node is added, removed, renamed, or changes architecture;
- the expected collector count changes;
- a Loki query, collector rollout, gateway, data source, or PVC acceptance test fails;
- the repository validator, Make target, chart lock, or controller bootstrap contract changes;
- a backup and restore capability is added;
- a conflicting or superseding evidence record is accepted.

### Scheduled review

```text
event-based: revalidate on any trigger above or before using the logs as sole incident-forensics evidence
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve this
record and evidence ID, and identify which historical claims remain valid.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique within the supplied generation context and permanent after publication.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects technical validation and pending review.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is recorded.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Repeatability is documented without overstating deployment idempotency.
- [x] Every version-not-captured value has an evidence gap.

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
| Owner | Don Buddenbaum | conditional | 2026-08-04 | Technical validation complete; governance acceptance remains pending publication review. |
| Reviewer | pending | pending | pending | A named reviewer is required before status may become `accepted`. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-centralized-logging-validation-sage-package.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-centralized-logging-validation-sage-package.zip \
  --push
```

The publisher owns publication-token replacement, record checksum generation,
publication-manifest creation, catalog reconciliation, evidence commit, and push.
Do not invent a manual unzip, stage, commit, rebase, or push sequence.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| terminal-evidence-20260804.txt | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/terminal-evidence-20260804.txt` | `7e0320f7037ea00d0e46210a475cee3ccd0e5eccff03d81549794390d85d687d` | no | Permanent with evidence record |
| centralized-logging-runtime-validation.json | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/centralized-logging-runtime-validation.json` | `9ec1661030e4e1b87d35971a4d290f43e82bef63c2f37a8bd812f87ee5067329` | no | Permanent with evidence record |
| repository-authority-snapshot.md | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/repository-authority-snapshot.md` | `df74e2a2890e70f89daeba8643597510a206e28aee6bcac2206bd770582df014` | no | Permanent with evidence record |
| input-bundle-manifest.json | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/input-bundle-manifest.json` | `6d51cb010b7f548d3224b68db1fb8ceba7dbb2190e159d7707ccdbbc1d95ec8c` | no | Permanent with evidence record |
| failure-recovery-ledger.md | `markdown/evidence-artifacts/SAGE-K3-OBS-20260804-001/failure-recovery-ledger.md` | `b78d7034417723e12b6c903f3208e650c32d2b655554aff2daccf5fcc12bd982` | no | Permanent with evidence record |

### Original requester language

```text
Create and reconcile the complete SAGE evidence package for the active centralized-logging deployment and validation, using repository-owned evidence workflows and all available terminal evidence, including the repository Helm bootstrap recovery, runtime validation, the failed root cluster-guardrails invocation, and the successful homelab cluster guardrails; reconcile indexes and publication artifacts without changing cluster state.
```

### Canonical generation request applied

```text
Generate the SAGE evidence package for the most recent Kalaxy3 working session using the repository SAGE evidence-record standard, canonical metadata contract, evidence-record template, evidence-publication process, and evidence-navigation compatibility rules. Use schema 1.2, populate canonical metadata, preserve failures and gaps, produce one valid ZIP with sage-package.json and payload, and return only the package and standard check and publication commands.
```

### Additional notes

The input bundle manifest is preserved as an artifact so the package can be
traced back to its captured authorities and terminal evidence. Package hashes
are computed before publication-token replacement, as required by the publisher.
