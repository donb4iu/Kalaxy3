---
evidence_id: SAGE-K3-OBS-20260728-002
schema_version: "1.2"
title: Centralized Logging Activation, Deployment, Correction, and Runtime Validation Evidence
nav_title: Deploy centralized logging observability
nav_section: operations
nav_order: 440
summary: Documents activating and deploying Loki and Fluent Bit, correcting Grafana datasource reconciliation, and validating storage, all-node collection, Grafana health, and queryable logs.
primary_subject: Centralized observability logging
project: Kalaxy3
record_type: operations
status: validated
classification: internal
work_session: centralized-logging-deployment-20260728
work_started_at: 2026-07-28T18:51:00-05:00
work_completed_at: 2026-07-28T19:39:00-05:00
evidence_collected_at: 2026-07-28T19:44:00-05:00
created_at: 2026-07-28T19:44:00-05:00
updated_at: 2026-07-28T19:57:17-05:00
valid_as_of: 2026-07-28
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Kalaxy3 architecture
author: ChatGPT
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donbs-imac
controller_host: donbs-imac
nodes:
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
  - amd64-01
  - amd64-02
node_addresses:
  - arm64-01=192.168.2.51
  - arm64-02=192.168.2.52
  - arm64-03=192.168.2.53
  - arm64-04=192.168.2.54
  - arm64-05=192.168.2.55
  - amd64-01=192.168.2.61
  - amd64-02=192.168.2.62
namespaces:
  - observability
  - longhorn-system
  - kubecost
  - metallb-system
  - kube-system
endpoints:
  - grafana=192.168.2.25
  - loki-api=loki.observability.svc.cluster.local:3100
  - loki-gateway=loki-gateway.observability.svc.cluster.local:80
components:
  - SAGE schema=1.2
  - K3s=v1.36.2+k3s1
  - Helm=v3.21.3+g1ad6e68
  - ansible-core=2.18.7
  - kubernetes.core=5.1.0
  - Loki Helm chart=18.5.4
  - Loki application=3.7.4
  - Fluent Bit Collector Helm chart=1.0.9
  - Fluent Bit=5.0.9
  - kube-prometheus-stack Helm chart=87.19.0
  - kube-prometheus-stack application=v0.92.1
  - Grafana=13.1.1
  - Longhorn=1.12.0
repository: donb4iu/Kalaxy3
branch: wip/centralized-logging-staged-20260726
implementation_commit: 4247387a8062a0a353f5704e40c90b1727881a4a
record_path: markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002
confidence: high
tags:
  - sage
  - observability
  - centralized-logging
  - loki
  - fluent-bit
  - grafana
  - longhorn
  - deployment
  - validation
relationships:
  verifies:
    - CLM-001 through CLM-013
  depends_on:
    - SAGE-K3-OBS-20260728-001
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - Kalaxy3 observability platform
  conflicts_with:
    - none
  generated_by:
    - ChatGPT using the Kalaxy3 SAGE evidence-generation bundle
  implemented_by:
    - 4247387a8062a0a353f5704e40c90b1727881a4a
  revalidated_by:
    - none
---

# Centralized Logging Activation, Deployment, Correction, and Runtime Validation Evidence

## Executive summary

This validated record documents the activation and deployment of centralized logging as one component of the broader Kalaxy3 observability platform. Loki 18.5.4 and Fluent Bit Collector 1.0.9 are deployed from exact repository locks; Loki and its gateway are ready on `amd64-02`; one collector is ready on each of seven nodes; the 40 Gi Longhorn volume is attached, healthy, and replicated twice; Grafana loaded and reached the Loki datasource; and recent `cluster="kalaxy3"` logs from every node are queryable. The record also preserves the partial-deployment failure, repository correction, startup backlog behavior, verification-helper mistakes, final guardrails, and unresolved operational tests.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBS-20260728-002 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Centralized Logging Activation, Deployment, Correction, and Runtime Validation Evidence |
| **Navigation title** | Deploy centralized logging observability |
| **Navigation section** | operations |
| **Navigation order** | 440 |
| **Summary** | Documents activating and deploying Loki and Fluent Bit, correcting Grafana datasource reconciliation, and validating storage, all-node collection, Grafana health, and queryable logs. |
| **Primary subject** | Centralized observability logging |
| **Record type** | operations |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | centralized-logging-deployment-20260728 |
| **Started** | 2026-07-28T18:51:00-05:00 |
| **Completed** | 2026-07-28T19:39:00-05:00 |
| **Evidence collected** | 2026-07-28T19:44:00-05:00 |
| **Record created** | 2026-07-28T19:44:00-05:00 |
| **Record updated** | 2026-07-28T19:57:17-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-07-28 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | wip/centralized-logging-staged-20260726 |
| **Implementation commit** | 4247387a8062a0a353f5704e40c90b1727881a4a |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62 |
| **Namespaces** | observability; longhorn-system; kubecost; metallb-system; kube-system |
| **Endpoints** | grafana=192.168.2.25; loki-api=loki.observability.svc.cluster.local:3100; loki-gateway=loki-gateway.observability.svc.cluster.local:80 |
| **Components and versions** | SAGE schema=1.2; K3s=v1.36.2+k3s1; Helm=v3.21.3+g1ad6e68; ansible-core=2.18.7; kubernetes.core=5.1.0; Loki Helm chart=18.5.4; Loki application=3.7.4; Fluent Bit Collector Helm chart=1.0.9; Fluent Bit=5.0.9; kube-prometheus-stack Helm chart=87.19.0; kube-prometheus-stack application=v0.92.1; Grafana=13.1.1; Longhorn=1.12.0 |
| **Owner** | Kalaxy3 architecture |
| **Author** | ChatGPT |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** ChatGPT; **operator:** Don Buddenbaum; **owner:** Kalaxy3 architecture; **reviewer:** pending; **affected users/teams:** Kalaxy3 operators, platform users, and future SAGE reviewers. |
| **What** | Activated and deployed Loki and Fluent Bit Collector, corrected Grafana datasource reconciliation after a partial deployment, resumed the observability phase, and validated exact releases, placement, storage, Grafana health, all-node ingestion, startup-pressure clearance, guardrails, and repository state. |
| **When** | **Completed:** 2026-07-28T19:39:00-05:00; **evidence collected:** 2026-07-28T19:44:00-05:00; **local timezone:** America/Chicago; **system timestamps:** America/Chicago; UTC; **valid as of:** 2026-07-28; **review due:** event-based. Kubernetes and application logs crossed midnight in UTC on 2026-07-29 while the local work session remained 2026-07-28. |
| **Where** | **Environment:** homelab; **cluster:** kalaxy3; **execution host:** donbs-imac; **controller:** donbs-imac; **nodes:** arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; **addresses:** arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62; **namespaces:** observability; longhorn-system; kubecost; metallb-system; kube-system; **endpoints:** grafana=192.168.2.25; loki-api=loki.observability.svc.cluster.local:3100; loki-gateway=loki-gateway.observability.svc.cluster.local:80; **record:** markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md. |
| **Why** | The staged implementation had passed activation readiness and needed a controlled deployment that preserved exact sources, chart locks, placement, storage, validation, and failure evidence. Repository correction was required because the initial datasource task depended on an unavailable remote Python library. |
| **How** | The operator published an isolated activation commit, ran the repository observability phase, inspected the partial deployment, replaced the failing datasource module with repository-established `k3s kubectl apply`, validated and pushed that correction, resumed deployment, and executed read-only runtime tests plus cluster guardrails. Raw terminal and repository-authority artifacts are hashed under the permanent evidence ID. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and explains the UTC date boundary.
- [x] Where is complete at repository, cluster, node, namespace, and endpoint levels.
- [x] Why includes rationale, alternatives, tradeoffs, and governance constraints.
- [x] How is reproducible, bounded, and tied to repository authority.

## Scope and boundaries

### In scope

- Activation of `deploy_centralized_logging` and publication of commit `9c8b0e68aa742dad796d6871df24faf78f4485aa` before cluster mutation.
- Installation and reconciliation of exact Loki and Fluent Bit Collector chart locks.
- The partial deployment, datasource failure, repository correction, server-side dry-run, commit `4247387a8062a0a353f5704e40c90b1727881a4a`, and successful resumed deployment.
- Loki and gateway placement, all-node collector readiness, Longhorn storage, Grafana datasource loading and health, Loki queries, all-node stream labels, startup ingestion pressure, and final cluster guardrails.
- Operator-side verification-helper failures that explain how final evidence collection was hardened.

### Out of scope

- Long-term retention-expiry proof for the configured `168h` retention period.
- Longhorn backup, restore, replica-failure, node-loss, and disaster-recovery tests for Loki data.
- Sustained throughput, capacity, and resource-cost benchmarking under representative workloads.
- Alerting and SLOs for ingestion rejection, 429 responses, collector buffering, storage pressure, and query latency.
- Automated repository rollback or deactivation logic; current rollback remains a controlled manual procedure.
- Acceptance by a named reviewer; status remains `validated`, not `accepted`.

### Nonclaims

- This record does not claim that centralized logging is the entirety of Kalaxy3 observability.
- It does not claim high availability for the monolithic single-replica Loki process.
- It does not claim that every historical log line was ingested; old entries were intentionally rejected by Loki's active time windows during startup.
- It does not claim that the full observability phase is Helm-revision idempotent; `kube-prometheus-stack` advanced to revision 12 during repeated reconciliation.

## Final accepted state

```text
Activation gate:               true
Loki release:                  loki-18.5.4, revision 1, deployed
Loki application:              3.7.4
Loki topology:                 monolithic single replica plus gateway
Loki placement:                amd64-02
Fluent Bit Collector release:  fluent-bit-collector-1.0.9, revision 1, deployed
Fluent Bit application:        5.0.9
Collector coverage:            one ready pod on each of seven nodes
Loki PVC:                      storage-loki-0, Bound, 40Gi, longhorn
Longhorn volume:               attached, healthy, two replicas
Grafana datasource:            uid=loki, type=loki, health=OK
Log query:                     recent cluster=kalaxy3 streams returned
Node-stream coverage:          all seven nodes observed
Startup errors, final window:  zero 429 and zero old-timestamp errors in five minutes
Guardrails:                    eight installed locked releases, zero permitted new releases
Repository:                    clean and synchronized at 4247387a8062a0a353f5704e40c90b1727881a4a
```

| Item | Accepted result |
|---|---|
| Deployment gate | Active and represented in repository state. |
| Loki | Exact chart deployed, runtime ready, placed on the intended AMD64 platform node. |
| Collection | Exact Fluent Bit Collector chart deployed as an all-node DaemonSet. |
| Storage | Bound Longhorn PVC and healthy two-replica attached volume. |
| Grafana | Datasource ConfigMap loaded and successful health response returned. |
| Ingestion | Recent logs queryable and all seven node labels present. |
| Startup pressure | Initial backlog generated 429 and old-entry rejection, then cleared in the final five-minute observation. |
| Governance | Source, deployment, cluster, and SAGE controls reconciled; repository clean and remote-synchronized. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The deployment gate was activated and pushed before cluster deployment. | high | `EV-001`; `EV-003` | supported | high |
| `CLM-002` | Loki 18.5.4 is deployed at Helm revision 1. | critical | `EV-002`; `EV-004`; `EV-005` | supported | high |
| `CLM-003` | Fluent Bit Collector 1.0.9 is deployed at Helm revision 1. | critical | `EV-002`; `EV-004`; `EV-006` | supported | high |
| `CLM-004` | The initial datasource failure was caused by an unavailable Python Kubernetes client after both logging releases installed. | high | `EV-002`; `EV-003` | supported | high |
| `CLM-005` | Repository commit `4247387a8062a0a353f5704e40c90b1727881a4a` corrected datasource reconciliation with `k3s kubectl apply`. | critical | `EV-003`; `EV-011` | supported | high |
| `CLM-006` | Loki and its gateway are ready on `amd64-02`. | critical | `EV-005` | supported | high |
| `CLM-007` | Exactly one ready collector runs on each of seven nodes. | critical | `EV-006` | supported | high |
| `CLM-008` | Loki uses a Bound 40 Gi Longhorn PVC backed by an attached, healthy, two-replica volume. | critical | `EV-007` | supported | high |
| `CLM-009` | Grafana loaded the `loki` datasource and successfully connected to Loki. | critical | `EV-008` | supported | high |
| `CLM-010` | Recent `cluster="kalaxy3"` logs are queryable and include streams from all seven nodes. | critical | `EV-009` | supported | high |
| `CLM-011` | Initial ingestion-rate and historical-timestamp errors cleared in the final five-minute window. | high | `EV-010` | supported | high |
| `CLM-012` | Final cluster reconciliation found eight installed locked releases and zero permitted new releases, with a clean synchronized repository. | critical | `EV-011` | supported | high |
| `CLM-013` | Ad hoc verification-helper failures were distinguishable from repository or cluster failures and did not invalidate the final runtime result. | normal | `EV-012`; `EV-009`; `EV-011` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The staged implementation was activation-ready but had not yet been exercised against the live cluster. Activation introduced a real state transition: two new Helm releases, an all-node collector, a persistent logging backend, and a Grafana datasource. The first live run exposed a controller/target dependency mismatch after the logging workloads were already installed.

### Decision

Proceed through secured checkpoints: first publish the gate activation without touching the cluster; then deploy through the repository observability phase; preserve the partial state when datasource provisioning failed; correct the repository instead of installing an ad hoc Python dependency on `arm64-01`; resume the same phase; and require runtime validation before declaring completion.

### Decision drivers

- Preserve repository authority and controller portability.
- Avoid disguising a partial deployment as either total success or total failure.
- Reuse the existing K3s CLI authority already available on the execution node.
- Keep Loki and Fluent Bit on exact, approved chart locks.
- Require evidence of the actual data path, not only pod readiness.
- Retain failed paths that explain the final implementation and validation method.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Install the Python Kubernetes client globally on `arm64-01` | Minimal task rewrite | Adds a remote package dependency not established by the repository and creates controller drift | rejected |
| Run the datasource task only from the macOS controller | Existing Python environment | Splits phase execution authority and requires controller-specific kubeconfig handling | rejected |
| Use repository-established `k3s kubectl apply` on the execution host | No new dependency, simple, auditable, works with existing K3s authority | Changed-state detection must parse command output | accepted |
| Roll back Loki and Fluent Bit immediately after datasource failure | Restores pre-deployment state | Discards healthy installed work and adds unnecessary storage churn | rejected |
| Ignore startup 429 and old-entry errors | Faster closure | Could hide persistent loss or an undersized ingestion path | rejected |
| Raise Loki limits immediately | May accelerate backlog drain | Changes capacity policy before measuring whether startup pressure is transient | deferred |

### Tradeoffs and consequences

- A single-replica monolithic Loki is economical and simple, but not process-highly-available.
- Retained Longhorn storage provides disk replication, but does not replace tested backup and restore.
- The all-node collector provides broad coverage, but a first start can replay significant local backlog and transiently exceed ingestion limits.
- `auth_enabled: false` simplifies internal single-tenant operation, but makes network isolation and Grafana access controls important.
- Re-running the broad observability phase reconciles desired state but advanced the Prometheus stack Helm revision even when its locked chart stayed unchanged.

## Architecture or change description

```text
K3s container logs on seven nodes
  -> Fluent Bit Collector DaemonSet
     labels: cluster, namespace, pod, container, node
     disk buffering: /var/lib/fluent-bit
  -> loki-gateway.observability.svc.cluster.local:80
  -> monolithic Loki 3.7.4 on amd64-02
     retention configuration: 168h
     filesystem object store
  -> Longhorn 40Gi RWO volume, two replicas
  -> Grafana datasource uid=loki
  -> Grafana at 192.168.2.25
```

### Before

`deploy_centralized_logging` was `false`; Loki and Fluent Bit releases and the Grafana datasource were absent. Placement labels, exact chart locks, values, dry-runs, and readiness evidence were already staged and validated by `SAGE-K3-OBS-20260728-001`.

### After

The gate is `true`; both exact logging releases are deployed; the datasource is present and healthy; the intended node and all-node collection topology are realized; persistent storage is attached and healthy; recent logs are queryable from all nodes; and the startup burst cleared during final observation.

## Source of truth and implementation lineage

### Repository files

```text
AGENTS.md
SAGE.md
sage-change-authority.json
sage-evidence-policy.json
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-index.py
scripts/sage/sage-publish.py
infrastructure/k3s-homelab/helm-repositories.json
infrastructure/k3s-homelab/helm-chart-lock.json
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/playbooks/platform.yml
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/playbooks/tasks/centralized-logging-node-labels.yml
infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2
infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml
infrastructure/k3s-homelab/scripts/validate-centralized-logging-yaml.py
infrastructure/k3s-homelab/scripts/sage-deployment-guardrail.py
infrastructure/k3s-homelab/scripts/sage-source-guardrails.py
```

### Implementation commit

```text
4247387a8062a0a353f5704e40c90b1727881a4a
Use kubectl for Grafana datasource reconciliation
```

Supporting checkpoint:

```text
9c8b0e68aa742dad796d6871df24faf78f4485aa
Activate centralized logging deployment
```

The implementation commit is the final repository correction governing the successful live deployment; the earlier activation commit is preserved as a separate secured checkpoint.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE record schema | 1.2 | Metadata contract and publisher |
| K3s | v1.36.2+k3s1 | Controller and cluster preflight |
| Helm | v3.21.3+g1ad6e68 | Repository Helm wrapper preflight |
| ansible-core | 2.18.7 | Repository virtual environment preflight |
| kubernetes.core collection | 5.1.0 | Repository virtual environment preflight |
| Loki chart | 18.5.4 | `helm-chart-lock.json` and live Helm list |
| Loki application | 3.7.4 | Live Helm list and pod image |
| Fluent Bit Collector chart | 1.0.9 | `helm-chart-lock.json` and live Helm list |
| Fluent Bit | 5.0.9 | Live Helm list and pod image |
| kube-prometheus-stack chart | 87.19.0 | Lock reconciliation and live Helm list |
| kube-prometheus-stack application | v0.92.1 | Live Helm list |
| Grafana | 13.1.1 | Live pod image |
| Longhorn chart | 1.12.0 | Lock reconciliation |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Chart repositories, locks, values, task logic, metadata contract, and publisher are hashed in `EV-003` and `EV-011`. |
| Controller bootstrap | `make cluster-guardrails` recreates and validates the repository Python and Helm toolchain. |
| Controller preflight | Core, Helm, cluster, SSH, and privilege-escalation checks passed in `EV-011`. |
| Controller host | donbs-imac |
| Execution host | donbs-imac controlling the Ansible execution on arm64-01 |
| Machine-local authoritative state | Local kubeconfig, SSH, vault access, and temporary API credentials are execution inputs; persistent desired state remains in Git. |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] The failed datasource path was reconciled into repository-owned automation.
- [x] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
install_observability: true
deploy_centralized_logging: true
install_kubecost: false
centralized_logging_namespace: observability
centralized_logging_workload_pool: platform-services
centralized_logging_expected_node: amd64-02
loki_storage_class: longhorn
loki_storage_size: 40Gi
loki_retention_period: 168h
```

```yaml
loki:
  auth_enabled: false
  limits_config:
    retention_period: "168h"
singleBinary:
  replicas: 1
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/workload-pool: platform-services
  persistence:
    enabled: true
    storageClass: longhorn
    size: 40Gi
```

## Prerequisites and assumptions

### Proven prerequisites

- The branch was clean, synchronized, and at evidence commit `9e6a2bb70cb1f4f718a28bcd7552a21db6f46a19` before activation (`EV-001`).
- The activation checkpoint passed source, deployment, cluster, and SAGE guardrails before deployment (`EV-001`).
- `amd64-02` was the unique `amd64` node labeled `platform-services` (`EV-001`).
- Longhorn was present and the logging chart requested 40 Gi before activation (`EV-001`, `EV-007`).
- All seven inventory hosts were reachable with noninteractive SSH and privilege escalation (`EV-011`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The final five-minute error-free collector window is representative of steady state. | Future restarts may replay enough backlog to trigger sustained 429 responses or dropped old records. | Observe restart behavior and alert on collector output errors and Loki rejected samples. |
| `ASM-002` | Seven-day retention and compaction behave as configured on filesystem storage. | Storage may fill or records may persist or disappear outside policy. | Measure volume growth and verify expiry after more than 168 hours. |
| `ASM-003` | Two Longhorn replicas provide adequate durability for this homelab workload. | Simultaneous node or disk loss could exceed protection. | Add recurring backups and execute restore and replica-failure tests. |
| `ASM-004` | Internal cluster network trust is sufficient while Loki authentication is disabled. | A compromised pod could query cluster logs. | Add or validate NetworkPolicy and least-privilege access before broader tenancy. |

These assumptions prevent `accepted` status until the owner and reviewer explicitly accept the residual risks or the listed tests close them.

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
SAGE_REQUEST='<activation request>' make sage-preflight
make -C infrastructure/k3s-homelab centralized-logging-render
make -C infrastructure/k3s-homelab source-guardrails
make -C infrastructure/k3s-homelab deployment-guardrail
make -C infrastructure/k3s-homelab cluster-guardrails
```

The gate was changed from `false` to `true`, committed as `9c8b0e68aa742dad796d6871df24faf78f4485aa`, pushed, and verified without deploying logging.

### Execution

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

.venv/bin/ansible-playbook   -i inventory/hosts.yml   playbooks/platform.yml   --extra-vars 'platform_phase=observability'   --vault-id kalaxy3@prompt
```

After the datasource failure, the repository task was corrected, server-side dry-run and guardrails passed, commit `4247387a8062a0a353f5704e40c90b1727881a4a` was pushed, and the same observability phase was rerun.

### Expected change

- Install exactly one locked Loki release and one locked Fluent Bit Collector release.
- Schedule Loki and its gateway on the unique intended node.
- Run one collector on every node.
- Provision the Grafana datasource.
- Preserve Longhorn-backed Loki storage and return queryable logs.

### Observed change

The first run installed both logging releases but stopped at datasource provisioning (`EV-002`). The corrected rerun left both logging releases at revision 1, created the datasource, and completed without failure (`EV-004`). Runtime checks then passed for topology, storage, datasource health, ingestion, all-node coverage, and final guardrails (`EV-005` through `EV-011`).

### Failed or superseded paths

- `kubernetes.core.k8s` on `arm64-01` failed because `/usr/bin/python3` lacked the Python Kubernetes library. Installing the library ad hoc was rejected; `k3s kubectl apply` became the accepted repository path.
- A revision-report helper raised a shell-quoting `NameError`; no observability phase ran in that attempt.
- A Secret-reading helper used Python standard input for both script and JSON and raised `JSONDecodeError`; the deployment itself had already completed through datasource creation.
- A dictionary-key quoting helper raised `KeyError`; it was read-only.
- Bash indirect expansion pasted into zsh failed during parsing with `event not found`; no command ran.
- The final verification explicitly invoked Bash, used file-backed JSON, and retained cleanup traps.

## Evidence items

### `EV-001` — Activation checkpoint and predeployment guardrails

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum with repository automation |
| Collected at | 2026-07-28T18:52:00-05:00 |
| Execution source | donbs-imac and donb4iu/Kalaxy3 |
| Target | branch, deployment gate, and kalaxy3 predeployment state |
| Tool and version | Git=version-not-captured; Make=version-not-captured; Helm=v3.21.3+g1ad6e68; Ansible=2.18.7 |
| Expected result | Gate active, guardrails pass, commit pushed, logging releases still absent |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
SAGE_REQUEST='<activation request>' make sage-preflight
make -C infrastructure/k3s-homelab centralized-logging-render
make -C infrastructure/k3s-homelab cluster-guardrails
git commit -m 'Activate centralized logging deployment'
git push origin wip/centralized-logging-staged-20260726
```

**Observed result**

```text
PASS activation validation did not deploy logging
activation_commit=9c8b0e68aa742dad796d6871df24faf78f4485aa
local=9c8b0e68aa742dad796d6871df24faf78f4485aa
remote=9c8b0e68aa742dad796d6871df24faf78f4485aa
PASS centralized logging activation checkpoint published
READY FOR CLUSTER DEPLOYMENT
```

**Interpretation**

The repository gate and activation checkpoint preceded live deployment. This evidence does not prove runtime behavior; later evidence items do.

### `EV-002` — Partial deployment and datasource failure

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-003`; `CLM-004` |
| Collected by | Don Buddenbaum with Ansible and Helm |
| Collected at | 2026-07-28T19:09:00-05:00 |
| Execution source | donbs-imac controlling arm64-01 |
| Target | observability namespace |
| Tool and version | ansible-core=2.18.7; Helm=v3.21.3+g1ad6e68; Kubernetes API=K3s v1.36.2+k3s1 |
| Expected result | Entire observability phase completes |
| Actual result | partial |
| Confidence | high |
| Sensitive data | vault prompt retained without password value |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-transcript.txt` |

**Command, query, source, or observation**

```bash
.venv/bin/ansible-playbook -i inventory/hosts.yml playbooks/platform.yml   --extra-vars 'platform_phase=observability' --vault-id kalaxy3@prompt
```

**Observed result**

```text
TASK [Install Loki] changed
TASK [Install Fluent Bit Collector] changed
TASK [Provision Grafana Loki datasource] FAILED
Failed to import the required Python library (kubernetes) on arm64-01's /usr/bin/python3

loki                  revision 1 deployed loki-18.5.4
fluent-bit-collector  revision 1 deployed fluent-bit-collector-1.0.9
Grafana datasource ConfigMap absent
```

**Interpretation**

The live state was partial: logging workloads and storage existed, but Grafana integration did not. The failure isolated a repository task dependency and did not justify uninstalling healthy releases.

### `EV-003` — Repository correction, dry-run, guardrails, and push

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`; `CLM-004`; `CLM-005` |
| Collected by | ChatGPT and Don Buddenbaum |
| Collected at | 2026-07-28T19:16:00-05:00 |
| Execution source | donbs-imac and donb4iu/Kalaxy3 |
| Target | `playbooks/tasks/observability.yml` and branch checkpoint |
| Tool and version | Git=version-not-captured; kubectl=K3s v1.36.2+k3s1; SAGE schema=1.2 |
| Expected result | Remove remote Python-client dependency without creating datasource during validation |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/repository-authority-evidence.md` |

**Command, query, source, or observation**

```bash
kubectl apply --dry-run=server --validate=true   -f /tmp/kalaxy3-centralized-logging-render/grafana-loki-datasource.yml
make -C infrastructure/k3s-homelab cluster-guardrails
make sage-guardrails
git commit -m 'Use kubectl for Grafana datasource reconciliation'
git push origin wip/centralized-logging-staged-20260726
```

**Observed result**

```text
configmap/grafana-datasource-loki created (server dry run)
PASS datasource remains absent
PASS 8 installed locked releases; 0 permitted new releases
correction_commit=4247387a8062a0a353f5704e40c90b1727881a4a
local=4247387a8062a0a353f5704e40c90b1727881a4a
remote=4247387a8062a0a353f5704e40c90b1727881a4a
0  0
```

**Interpretation**

The accepted correction reused existing K3s authority, passed API validation, preserved the live partial deployment, and was pushed before resumption.

### `EV-004` — Successful resumed observability phase

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-003`; `CLM-005` |
| Collected by | Don Buddenbaum with Ansible |
| Collected at | 2026-07-28T19:28:00-05:00 |
| Execution source | donbs-imac controlling arm64-01 |
| Target | observability namespace and Grafana datasource ConfigMap |
| Tool and version | ansible-core=2.18.7; Helm=v3.21.3+g1ad6e68 |
| Expected result | Logging releases reconcile and datasource is created |
| Actual result | pass |
| Confidence | high |
| Sensitive data | vault prompt retained without password value |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
.venv/bin/ansible-playbook -i inventory/hosts.yml playbooks/platform.yml   --extra-vars 'platform_phase=observability' --vault-id kalaxy3@prompt
```

**Observed result**

```text
TASK [Install Loki] ok
TASK [Install Fluent Bit Collector] ok
TASK [Provision Grafana Loki datasource] changed
PLAY RECAP arm64-01: ok=26 changed=2 failed=0
loki revision=1 deployed
fluent-bit-collector revision=1 deployed
kube-prometheus-stack revision=12 deployed
```

**Interpretation**

The correction completed the missing integration without incrementing either logging release revision. The broader phase did increment the Prometheus stack revision, which is retained as an idempotency limitation.

### `EV-005` — Loki release, rollout, and placement

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-006` |
| Collected by | Don Buddenbaum with Helm and kubectl |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac |
| Target | Loki StatefulSet and gateway Deployment |
| Tool and version | Helm=v3.21.3+g1ad6e68; kubectl=K3s v1.36.2+k3s1 |
| Expected result | Exact release deployed and all Loki pods ready on amd64-02 |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
scripts/helm list -n observability --filter '^loki$'
kubectl -n observability get pods -l app.kubernetes.io/instance=loki -o wide
```

**Observed result**

```text
loki revision=1 status=deployed chart=loki-18.5.4 app=3.7.4
loki-0                          2/2 Running amd64-02
loki-gateway-5c75989494-97v27   2/2 Running amd64-02
PASS Loki and gateway are ready on amd64-02
```

**Interpretation**

The intended single-node monolithic topology is realized. This is placement and readiness evidence, not a high-availability claim.

### `EV-006` — Fluent Bit release and all-node collector coverage

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003`; `CLM-007` |
| Collected by | Don Buddenbaum with Helm and kubectl |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac |
| Target | Fluent Bit Collector DaemonSet and seven cluster nodes |
| Tool and version | Helm=v3.21.3+g1ad6e68; Fluent Bit=5.0.9 |
| Expected result | Exact release deployed and one ready collector per node |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
scripts/helm list -n observability --filter '^fluent-bit-collector$'
kubectl -n observability get pods   -l app.kubernetes.io/instance=fluent-bit-collector -o json
```

**Observed result**

```text
fluent-bit-collector revision=1 status=deployed chart=fluent-bit-collector-1.0.9 app=5.0.9
PASS exactly one ready Fluent Bit Collector runs on every node
```

**Interpretation**

Collector scheduling and readiness cover every current Kubernetes node. The later log-label test proves data from those nodes reached Loki.

### `EV-007` — Loki Longhorn storage

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-008` |
| Collected by | Don Buddenbaum with kubectl |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac |
| Target | `storage-loki-0` PVC and Longhorn volume |
| Tool and version | kubectl=K3s v1.36.2+k3s1; Longhorn=1.12.0 |
| Expected result | Bound 40Gi Longhorn PVC and attached healthy two-replica volume |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
kubectl -n observability get pvc storage-loki-0
kubectl -n longhorn-system get volumes.longhorn.io <volume-handle> -o json
```

**Observed result**

```text
phase=Bound
storage_class=longhorn
requested=40Gi
state=attached
robustness=healthy
replicas=2
```

**Interpretation**

The runtime volume matches repository intent and has two Longhorn replicas. Backup and restore remain untested.

### `EV-008` — Grafana datasource loading and health

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-009` |
| Collected by | Don Buddenbaum with kubectl, curl, and Grafana API |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac local port-forward |
| Target | Grafana datasource uid `loki` |
| Tool and version | Grafana=13.1.1; curl=version-not-captured |
| Expected result | Datasource exists with internal gateway URL and health status OK |
| Actual result | pass |
| Confidence | high |
| Sensitive data | credentials decoded to temporary mode-0600 file, never displayed, then deleted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
curl --user '<redacted>' http://127.0.0.1:13000/api/datasources
curl --user '<redacted>' http://127.0.0.1:13000/api/datasources/uid/loki/health
```

**Observed result**

```text
name=Loki
uid=loki
type=loki
url=http://loki-gateway.observability.svc.cluster.local
{"message":"Data source successfully connected.","status":"OK"}
PASS Grafana reached Loki successfully
```

**Interpretation**

Grafana's live API, not only the ConfigMap, confirmed that the datasource was loaded and reachable.

### `EV-009` — Queryable recent logs and all-node stream labels

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-010`; `CLM-013` |
| Collected by | Don Buddenbaum with Loki HTTP API |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac local port-forward |
| Target | Loki query API and node label-values API |
| Tool and version | Loki=3.7.4; curl=version-not-captured |
| Expected result | Recent Kalaxy3 streams returned and all seven node names present |
| Actual result | pass |
| Confidence | high |
| Sensitive data | sample labels retained; log payloads omitted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
GET /loki/api/v1/query_range?query={cluster="kalaxy3"}
GET /loki/api/v1/label/node/values
```

**Observed result**

```text
stream_count=6
PASS recent Kalaxy3 logs are queryable
expected=['amd64-01', 'amd64-02', 'arm64-01', 'arm64-02', 'arm64-03', 'arm64-04', 'arm64-05']
observed=['amd64-01', 'amd64-02', 'arm64-01', 'arm64-02', 'arm64-03', 'arm64-04', 'arm64-05']
PASS Loki contains recent streams from all seven nodes
```

**Interpretation**

This proves an end-to-end current data path from every node through Fluent Bit to Loki. It does not prove lossless ingestion of the initial historical backlog.

### `EV-010` — Startup backlog errors and clearance

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-011` |
| Collected by | Don Buddenbaum with kubectl logs |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac |
| Target | all seven Fluent Bit Collector pods |
| Tool and version | Fluent Bit=5.0.9; Loki=3.7.4 |
| Expected result | Initial pressure is identified and no longer appears in the final observation window |
| Actual result | pass |
| Confidence | high |
| Sensitive data | log metadata retained; message payloads minimized |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-transcript.txt` |

**Command, query, source, or observation**

```bash
kubectl -n observability logs <collector-pod> --since=5m
grep -E 'HTTP status=429|ingestion rate limit exceeded|timestamp too old|entry too far behind'
```

**Observed result**

```text
Initial: HTTP 429 at 4194304 bytes/sec and HTTP 400 for entries too old or too far behind.
Final five-minute scan:
recent_rate_limit_errors=0
recent_old_timestamp_errors=0
```

**Interpretation**

The observed startup pressure cleared. This evidence supports monitoring and later tuning rather than an immediate unmeasured limit increase.

### `EV-011` — Final source, deployment, cluster, and Git reconciliation

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-005`; `CLM-012`; `CLM-013` |
| Collected by | repository guardrails and Git |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac and donb4iu/Kalaxy3 |
| Target | controller toolchain, seven inventory hosts, Helm locks, branch and working tree |
| Tool and version | SAGE schema=1.2; Helm=v3.21.3+g1ad6e68; ansible-core=2.18.7 |
| Expected result | All controls pass, no missing releases, clean synchronized repository |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/repository-authority-evidence.md` |

**Command, query, source, or observation**

```bash
make cluster-guardrails
git status
git rev-parse HEAD
git rev-parse origin/wip/centralized-logging-staged-20260726
```

**Observed result**

```text
PASS noninteractive SSH authentication for 7 inventory hosts
PASS noninteractive Ansible privilege escalation for 7 inventory hosts
PASS 8 installed locked releases; 0 permitted new releases
Kalaxy3 Helm lock reconciliation: PASS
Kalaxy3 SAGE cluster deployment guardrails: PASS
52:deploy_centralized_logging: true
nothing to commit, working tree clean
HEAD and origin/wip/centralized-logging-staged-20260726: 4247387a8062a0a353f5704e40c90b1727881a4a
```

**Interpretation**

The final runtime state agrees with exact locks and the branch remained clean and published. Guardrails do not replace the longer-duration operational tests listed as gaps.

### `EV-012` — Verification-helper failures and final hardened method

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-013` |
| Collected by | Don Buddenbaum and ChatGPT |
| Collected at | 2026-07-28T19:39:00-05:00 |
| Execution source | donbs-imac interactive zsh and explicit Bash validation |
| Target | ad hoc evidence-collection wrappers |
| Tool and version | zsh=version-not-captured; Bash=version-not-captured; Python=3.12.4 |
| Expected result | Verification wrapper runs without changing cluster state |
| Actual result | informational |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-transcript.txt` |

**Command, query, source, or observation**

```text
NameError from shell-quoted revision helper
JSONDecodeError from standard-input conflict
KeyError from dictionary-key quoting
zsh event-not-found from Bash indirect expansion
final explicit Bash and file-backed JSON validation: PASS
```

**Observed result**

```text
Each failed wrapper stopped before or during read-only verification.
The final explicit-Bash validation completed every acceptance check.
```

**Interpretation**

These failures were operator-side tooling defects. Retaining them prevents future reviewers from misclassifying them as cluster failures and documents the safer verification pattern.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Gate activated and published before deployment | `EV-001` | Active gate, synchronized commit, releases absent at checkpoint | `9c8b0e68aa742dad796d6871df24faf78f4485aa` published and no logging deployment | pass |
| `AC-002` | Exact logging releases deployed | `EV-002`; `EV-004`; `EV-005`; `EV-006` | Locked charts deployed | Loki 18.5.4 and Fluent Bit Collector 1.0.9 at revision 1 | pass |
| `AC-003` | Datasource correction is repository-owned | `EV-003` | No ad hoc target dependency | `k3s kubectl apply` committed and pushed | pass |
| `AC-004` | Intended backend placement | `EV-005` | Loki and gateway on amd64-02 | Both ready on amd64-02 | pass |
| `AC-005` | All-node collection | `EV-006` | Seven ready pods, one per node | Exact node set matched | pass |
| `AC-006` | Persistent storage | `EV-007` | Bound 40Gi Longhorn volume, healthy, two replicas | All values matched | pass |
| `AC-007` | Grafana integration | `EV-008` | Loaded datasource and successful health | status OK | pass |
| `AC-008` | End-to-end log path | `EV-009` | Recent query returns streams from every node | Query and label-values tests passed | pass |
| `AC-009` | Startup pressure cleared | `EV-010` | Zero matching errors in final five-minute window | zero 429 and zero old-timestamp matches | pass |
| `AC-010` | Governance reconciliation | `EV-011` | All guards pass, locks match, Git clean | eight locked releases, zero new, clean synchronized branch | pass |

### Functional verification

```bash
scripts/helm list --namespace observability
kubectl --kubeconfig kubeconfig-kalaxy3.yaml -n observability get pods,pvc -o wide
curl http://127.0.0.1:13000/api/datasources/uid/loki/health
curl --get http://127.0.0.1:13100/loki/api/v1/query_range   --data-urlencode 'query={cluster="kalaxy3"}'
curl http://127.0.0.1:13100/loki/api/v1/label/node/values
```

Observed:

```text
Exact releases deployed; every workload ready; storage healthy; Grafana status OK;
recent streams returned; all seven node labels present.
```

### Negative verification

```bash
grep -E 'HTTP status=429|ingestion rate limit exceeded|timestamp too old|entry too far behind'   <all collector logs from the final five minutes>
```

Observed:

```text
recent_rate_limit_errors=0
recent_old_timestamp_errors=0
```

The test establishes a clean final window; it does not erase or hide the earlier startup errors.

## Idempotency and repeatability

### First accepted run

```text
Initial run:
  kube-prometheus-stack revision 10 -> 11
  Loki absent -> revision 1 deployed
  Fluent Bit Collector absent -> revision 1 deployed
  datasource failed before creation
```

### Steady-state rerun

```text
Corrected rerun:
  Loki revision 1 -> revision 1, task ok
  Fluent Bit Collector revision 1 -> revision 1, task ok
  datasource absent -> created
  kube-prometheus-stack revision 11 -> 12
```

### Interpretation

The logging Helm releases demonstrated reconciliation without revision churn during the corrected rerun. The datasource `kubectl apply` task has deterministic changed-state parsing, but a second post-creation Ansible rerun was not captured, so its steady-state `changed=0` result remains an evidence gap. The full observability phase is repeatable but not revision-idempotent because it advanced `kube-prometheus-stack` despite retaining the same locked chart. This does not change runtime intent, but it creates unnecessary Helm history and should be corrected or explicitly accepted.

## Security, privacy, and evidence handling

### Security controls

- Approved Helm repositories use HTTPS and repository-recorded URL fingerprints.
- Exact chart versions are enforced by the deployment guardrail and reconciled against live releases.
- Loki and its gateway are ClusterIP services; no direct external Loki endpoint was created.
- Grafana access uses its existing authentication and was tested through a local port-forward.
- Temporary Grafana credentials were decoded into a mode-0600 file, never printed, and deleted by cleanup.
- Loki analytics reporting is disabled by repository values.
- Evidence scanning found no private keys, bearer tokens, kubeconfig client keys, or credential values.

### Sensitive material excluded

- Ansible vault password and vault contents.
- Grafana username and password values.
- Kubernetes Secret data after decoding.
- Kubeconfig client key and certificate data.
- Log message bodies not required to prove the data path.

### Redactions and omissions

- Authentication values are represented as `<redacted>` or described without disclosure.
- The record retains internal RFC1918 addresses and service names because they are material to cluster operations and rebuild.
- Sample Loki evidence retains labels but omits log-line payloads that may contain workload data.

### Residual security risk

- `loki.auth_enabled: false` means any workload with network reachability to the internal service may query logs. NetworkPolicy or another internal authorization boundary is not proven.
- Centralized logs may contain operational or application-sensitive data. No content-classification, masking, or retention exception policy was validated in this session.
- Grafana remains the intended human access layer; direct Loki exposure must remain internal.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Loki process or gateway unavailable | Pod readiness, `/ready`, Grafana datasource health, failed collector flushes | Queries unavailable; collectors buffer and retry subject to local capacity | Inspect rollout, pod logs, node health, and Longhorn attachment; restart only after preserving evidence. |
| Ingestion rate exceeded | Fluent Bit HTTP 429 and Loki rejected-sample metrics or logs | Delayed ingestion and possible buffer growth | Confirm whether pressure is transient; tune limits or collector replay behavior through repository values after measuring volume. |
| Entries too old or too far behind | Fluent Bit HTTP 400 output | Historical backlog lines are dropped | Decide whether old backlog is required; adjust startup position or Loki time windows only through reviewed repository policy. |
| Longhorn volume degraded or detached | PVC, Longhorn volume state and robustness | Loki may become unavailable or lose durability | Restore replica health, reattach, or recover from backup after testing procedure. |
| `amd64-02` unavailable | Pending Loki pods and failed placement selector | Single-replica backend unavailable | Restore the node or execute a reviewed placement change; monolithic Loki has no current failover replica. |
| Grafana datasource missing or unhealthy | ConfigMap absence, Grafana API health | Logs exist but are unavailable through Grafana | Re-run corrected observability phase and verify sidecar/API loading. |

### Rollback

The repository currently lacks a tested automated centralized-logging rollback path. A controlled emergency rollback should first preserve or snapshot required Loki data, then use the repository-managed Helm and kubeconfig tools:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

scripts/helm uninstall fluent-bit-collector   --namespace observability   --wait

scripts/helm uninstall loki   --namespace observability   --wait

kubectl --kubeconfig kubeconfig-kalaxy3.yaml   --namespace observability   delete configmap grafana-datasource-loki
```

Then change `deploy_centralized_logging` to `false`, run repository guardrails, commit, and publish the rollback intent. Because Loki persistence uses Retain semantics and Longhorn uses retained storage, confirm PVC and PV disposition explicitly; do not delete persistent data as part of an unreviewed rollback.

### Rebuild procedure

1. Clone or update `donb4iu/Kalaxy3` on a supported controller and check out the target branch or the later accepted mainline commit.
2. Run repository controller preflight and cluster guardrails.
3. Verify all seven nodes, workload-pool labels, `amd64-02` readiness, Longhorn schedulability, and the `longhorn` StorageClass.
4. Verify the exact approved repository and chart locks.
5. Confirm `install_observability: true` and `deploy_centralized_logging: true`.
6. Run `playbooks/platform.yml` with `platform_phase=observability` and the repository vault authority.
7. Wait for Loki, gateway, and collector rollouts.
8. Verify the 40 Gi PVC and Longhorn volume health.
9. Verify the Grafana datasource through Grafana's API.
10. Query recent `cluster="kalaxy3"` streams and require all seven node labels.
11. Run final cluster guardrails and publish a new revalidation record.

### Data durability and backup impact

The Loki filesystem is stored on a 40 Gi Longhorn RWO volume with two replicas and retained PVC behavior. This protects against a single storage-replica loss under expected Longhorn behavior, but no backup destination, snapshot schedule, restoration procedure, recovery point objective, or recovery time objective was validated. Replication is not a backup. The record must be revalidated after the first tested snapshot and restore.

## Operational considerations and observability

### Health signals

- `kubectl rollout status` for `statefulset/loki`, `deployment/loki-gateway`, and `daemonset/fluent-bit-collector`.
- Ready collector count equal to current node count.
- Loki `/ready` endpoint.
- Grafana datasource health API for uid `loki`.
- Fluent Bit output errors, retry count, storage backlog, and filesystem use.
- Loki rejected samples by reason, ingestion rate, query latency, compactor activity, and disk use.
- Longhorn volume state, robustness, replica count, and capacity.
- Helm release status and chart-lock reconciliation.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

scripts/helm list --namespace observability
kubectl --kubeconfig kubeconfig-kalaxy3.yaml   --namespace observability   get statefulset,deployment,daemonset,pod,pvc -o wide
make cluster-guardrails
```

A complete revalidation should also exercise Grafana datasource health and a bounded recent Loki query from a local port-forward.

### Capacity, performance, cost, and sustainability

- **Capacity:** Loki requests 250m CPU and 512 MiB memory with a 2 GiB memory limit; gateway requests 50m CPU and 64 MiB; each collector requests 50m CPU and 64 MiB. Actual utilization and daily log volume were not captured.
- **Performance:** Current queries succeeded, but sustained ingestion and query latency were not benchmarked. Initial backlog briefly exceeded the observed 4 MiB/s ingestion limit.
- **Cost:** The deployment adds a 40 Gi Longhorn volume, compute on `amd64-02`, and seven collector pods. Kubecost comparison is required after sufficient accumulation time.
- **Sustainability/power:** Running Loki on an existing platform-services node avoids a dedicated host, but incremental power has not been measured.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Seven-day retention expiry and compactor deletion were configured but not observed across a full retention window. | Retention policy could differ from intent or storage could fill. | Kalaxy3 architecture | after 8 days of operation |
| `GAP-002` | evidence-gap | No Loki backup, snapshot, restore, replica-loss, or node-loss recovery test was executed. | Durability and recovery objectives are unproven. | Kalaxy3 architecture | before acceptance |
| `GAP-003` | risk | Initial replay generated 429 responses and rejected historical lines, although the final five-minute window was clean. | Future restarts may delay or drop backlog. | Observability owner | on any recurrence or planned restart test |
| `GAP-004` | technical-debt | The full observability phase advanced `kube-prometheus-stack` from revision 10 to 12 during repeated reconciliation. | Helm history churn obscures meaningful changes. | Kalaxy3 automation owner | next observability automation refinement |
| `GAP-005` | evidence-gap | A second post-creation datasource reconciliation was not captured. | Datasource task steady-state `changed=0` is expected but unproven. | Kalaxy3 automation owner | next observability rerun |
| `GAP-006` | risk | Loki authentication is disabled and no NetworkPolicy evidence was captured. | Cluster workloads may have broader log-query access than intended. | Kalaxy3 security owner | before additional tenants or sensitive workloads |
| `GAP-007` | evidence-gap | No sustained throughput, resource-use, query-latency, or Kubecost comparison was captured. | Capacity and operating cost are unknown. | Kalaxy3 FinOps owner | after 7–14 days of representative load |
| `GAP-008` | technical-debt | Automated repository rollback and deactivation are not implemented or tested. | Emergency rollback depends on careful manual commands. | Kalaxy3 automation owner | before acceptance |
| `GAP-009` | risk | Monolithic Loki has one process replica on `amd64-02`. | Node or process loss interrupts logging queries and ingestion until recovery. | Kalaxy3 architecture | when availability requirements change |
| `GAP-010` | evidence-gap | No alert rules or SLOs were validated for ingestion rejection, collector buffering, storage, readiness, or datasource health. | Failures may rely on manual detection. | Observability owner | next observability iteration |

## Troubleshooting

### Grafana datasource task fails with missing Python Kubernetes library

**Meaning**

The old `kubernetes.core.k8s` task was executed on `arm64-01`, whose `/usr/bin/python3` lacked the Python Kubernetes client.

**Checks**

```bash
git log -1 --oneline -- infrastructure/k3s-homelab/playbooks/tasks/observability.yml
grep -n -A18 'Provision Grafana Loki datasource'   infrastructure/k3s-homelab/playbooks/tasks/observability.yml
```

**Recovery**

```bash
# Require commit 4247387a8062a0a353f5704e40c90b1727881a4a or its accepted successor,
# then rerun the repository observability phase.
```

Do not install an untracked target dependency as the primary fix.

### Fluent Bit reports HTTP 429

**Meaning**

Collector replay or current volume exceeds Loki's accepted ingestion rate.

**Checks**

```bash
kubectl -n observability logs daemonset/fluent-bit-collector --since=10m   | grep -E 'HTTP status=429|ingestion rate limit exceeded'
kubectl -n observability logs statefulset/loki -c loki --since=10m
```

**Recovery**

First determine whether the condition clears. If sustained, measure ingestion volume and buffer growth, then change Loki limits or collector replay behavior in repository templates and validate through exact-chart rendering and SAGE evidence.

### Fluent Bit reports entries too old or too far behind

**Meaning**

Local container-log backlog is older than Loki's active ingestion window or is behind the newest accepted stream timestamp.

**Checks**

```bash
kubectl -n observability logs daemonset/fluent-bit-collector --since=30m   | grep -E 'timestamp too old|entry too far behind'
```

**Recovery**

Do not silently broaden acceptance windows. Decide whether historical replay is required, then implement a repository policy for collector start position or Loki out-of-order and age limits.

### Loki pod is Pending or volume is degraded

**Meaning**

The unique placement target, PVC, or Longhorn volume cannot satisfy the monolithic backend.

**Checks**

```bash
kubectl -n observability describe pod loki-0
kubectl -n observability get pvc storage-loki-0 -o wide
kubectl -n longhorn-system get volumes.longhorn.io
kubectl get node amd64-02 --show-labels
```

**Recovery**

Restore `amd64-02` readiness, expected labels, and Longhorn health. A placement change must be reviewed and validated before application.

### Grafana does not show Loki after ConfigMap creation

**Meaning**

The sidecar may not have observed the ConfigMap, the datasource may have invalid content, or Grafana may reject or fail to reach the service.

**Checks**

```bash
kubectl -n observability get configmap grafana-datasource-loki -o yaml
kubectl -n observability logs deployment/kube-prometheus-stack-grafana   -c grafana-sc-datasources --since=10m
```

**Recovery**

Re-run the corrected observability phase, wait for sidecar reconciliation, and verify `/api/datasources/uid/loki/health` through a local port-forward.

### Validation helper fails before cluster checks

**Meaning**

Shell quoting, standard-input reuse, or shell-language assumptions may have broken an ad hoc wrapper.

**Checks**

```text
Use explicit Bash for Bash syntax.
Use file-backed JSON when Python reads a heredoc script.
Avoid nested single-quote Python expressions inside shell single quotes.
```

**Recovery**

Treat the helper failure separately from the cluster state, confirm whether any mutating command ran, and rerun bounded read-only checks with explicit shell and temporary-file cleanup.

## Freshness, revalidation, and supersession

### Revalidate when

- Loki, Fluent Bit Collector, Grafana, kube-prometheus-stack, Longhorn, K3s, Helm, Ansible, or SAGE versions change.
- `deploy_centralized_logging`, placement labels, expected node, namespace, storage class, storage size, retention, resources, or service endpoints change.
- A node is added, removed, renamed, readdressed, or changes architecture or role.
- Loki or Fluent Bit restarts and a backlog replay occurs.
- Any 429, old-timestamp, buffer-growth, storage, readiness, or datasource-health incident occurs.
- A backup or restore path is implemented or tested.
- NetworkPolicy, authentication, tenancy, or log-content policy changes.
- The broad observability phase idempotency behavior is corrected.
- A conflicting or superseding evidence record is published.

### Scheduled review

```text
event-based; additionally review after the first full 168-hour retention cycle and after 7–14 days of Kubecost and resource evidence
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve this record and evidence ID, and state which deployment, storage, security, and runtime claims remain valid.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects validated but not reviewer-accepted completeness.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is represented by the publication token.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Idempotency and its limitations are documented.
- [x] No metadata value uses `not-captured`.

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
| Owner | Kalaxy3 architecture | pending | pending | Runtime deployment is validated; owner acceptance awaits gap review. |
| Reviewer | pending | pending | pending | Named reviewer has not yet accepted the record. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-centralized-logging-deployment-evidence.zip

python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-centralized-logging-deployment-evidence.zip   --push
```

The publisher replaces `4247387a8062a0a353f5704e40c90b1727881a4a` with `4247387a8062a0a353f5704e40c90b1727881a4a`, replaces `2026-07-28T19:57:17-05:00`, creates the record checksum and publication manifest, reconciles evidence indexes, commits the evidence, and pushes the branch.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Full terminal transcript | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-transcript.txt` | `2f485cb3b549c8581cfa8c1630173e560d44fdf535b15ccbc7d2894ba2fb4aa7` | no credential values; internal addresses retained | permanent with record |
| Curated terminal evidence | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/terminal-evidence.md` | `a0d8d8e4c6fd63969552e41eebbb4397745b28ac25b14ede8bd42a25ad56f4c7` | no | permanent with record |
| Repository authority evidence | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/repository-authority-evidence.md` | `eeaab35660e82905d28af7742c3d2d39b73021cb7f104e62e5425c3ebb2834c2` | no | permanent with record |
| Generation provenance | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-002/generation-provenance.md` | `c93f57a10b0e1c87b3f16abdd9deea0001c4bcf2fe2d5fe8506529a28b8d5d27` | no | permanent with record |

### Additional notes

- Input generation bundle SHA-256: `58e54271cab85e4e3307959ac0e2d6e6dc87ce61b010ec42ec5a2f5c48673c39`.
- Supplied terminal transcript SHA-256: `2f485cb3b549c8581cfa8c1630173e560d44fdf535b15ccbc7d2894ba2fb4aa7`.
- This record depends on `SAGE-K3-OBS-20260728-001`, which established activation readiness without deploying logging.
- The initial `curl` connection-refused messages in the final successful validation were expected local port-forward startup races; readiness loops subsequently passed and are not service-failure evidence.
- `kube-prometheus-stack` revision 12 is retained as an operational observation, not as evidence of a chart-version change.
