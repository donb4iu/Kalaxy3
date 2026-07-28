---
evidence_id: SAGE-K3-OBS-20260728-001
schema_version: "1.2"
title: Iterative SAGE-Governed Observability Staging and Activation-Readiness Evidence
nav_title: Stage centralized logging through SAGE guardrails
nav_section: operations
nav_order: 430
summary: Documents the iterative ChatGPT-SAGE discovery, correction, validation, commit, and push cycle that made Kalaxy3 centralized logging activation-ready without deploying Loki or Fluent Bit.
primary_subject: Centralized observability logging
project: Kalaxy3
record_type: change
status: validated
classification: internal
work_session: centralized-logging-staged-20260726
work_started_at: 2026-07-26T12:44:00-05:00
work_completed_at: 2026-07-28T00:48:00-05:00
evidence_collected_at: 2026-07-28T00:48:00-05:00
created_at: 2026-07-28T01:02:00-05:00
updated_at: 2026-07-28T01:16:57-05:00
valid_as_of: 2026-07-28
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
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
endpoints:
  - not-applicable
components:
  - SAGE schema=1.2
  - K3s=v1.36.2+k3s1
  - Helm=v3.21.3+g1ad6e68
  - ansible-core=2.18.7
  - kubernetes.core=5.1.0
  - Loki Helm chart=18.5.4
  - Fluent Bit Collector Helm chart=1.0.9
  - Longhorn=1.12.0
repository: donb4iu/Kalaxy3
branch: wip/centralized-logging-staged-20260726
implementation_commit: a4a11fc03dec92663a7e31924e8b3690d68aec4e
record_path: markdown/operations/kalaxy3-sage-observability-iterative-readiness-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001
confidence: high
tags:
  - sage
  - observability
  - centralized-logging
  - helm
  - loki
  - fluent-bit
  - guardrails
relationships:
  verifies:
    - CLM-001 through CLM-010
  depends_on:
    - SAGE repository governance and schema 1.2
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - staged centralized logging implementation
  conflicts_with:
    - none
  generated_by:
    - ChatGPT using the Kalaxy3 SAGE evidence-generation bundle
  implemented_by:
    - a4a11fc03dec92663a7e31924e8b3690d68aec4e
  revalidated_by:
    - none
---

# Iterative SAGE-Governed Observability Staging and Activation-Readiness Evidence

## Executive summary

This validated record preserves the full iterative engineering loop by which ChatGPT and the repository-owned SAGE process discovered, corrected, validated, committed, and pushed Kalaxy3 observability changes. The final staged implementation has exact approved Helm sources and chart locks, Loki-compatible values, repository-owned manifest rendering, retired obsolete Kubernetes Dashboard source, reconciled workload-pool labels, and successful Kubernetes server-side dry-runs. `deploy_centralized_logging` remained `false`; Loki and Fluent Bit were not deployed.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBS-20260728-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Iterative SAGE-Governed Observability Staging and Activation-Readiness Evidence |
| **Navigation title** | Stage centralized logging through SAGE guardrails |
| **Navigation section** | operations |
| **Navigation order** | 430 |
| **Summary** | Documents the iterative ChatGPT-SAGE discovery, correction, validation, commit, and push cycle that made Kalaxy3 centralized logging activation-ready without deploying Loki or Fluent Bit. |
| **Primary subject** | Centralized observability logging |
| **Record type** | change |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | centralized-logging-staged-20260726 |
| **Started** | 2026-07-26T12:44:00-05:00 |
| **Completed** | 2026-07-28T00:48:00-05:00 |
| **Evidence collected** | 2026-07-28T00:48:00-05:00 |
| **Record created** | 2026-07-28T01:02:00-05:00 |
| **Record updated** | 2026-07-28T01:16:57-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago |
| **Valid as of** | 2026-07-28 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-sage-observability-iterative-readiness-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | wip/centralized-logging-staged-20260726 |
| **Implementation commit** | a4a11fc03dec92663a7e31924e8b3690d68aec4e |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62 |
| **Namespaces** | observability; longhorn-system |
| **Endpoints** | not-applicable |
| **Components and versions** | SAGE schema=1.2; K3s=v1.36.2+k3s1; Helm=v3.21.3+g1ad6e68; ansible-core=2.18.7; kubernetes.core=5.1.0; Loki Helm chart=18.5.4; Fluent Bit Collector Helm chart=1.0.9; Longhorn=1.12.0 |
| **Owner** | Kalaxy3 architecture |
| **Author** | ChatGPT |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** ChatGPT; **operator:** Don Buddenbaum; **owner:** Kalaxy3 architecture; **reviewer:** pending; **affected users/teams:** Kalaxy3 operators and future reviewers. |
| **What** | The session established and exercised SAGE-governed observability staging, corrected Helm and Loki compatibility defects, retired obsolete Dashboard source, separated placement-label reconciliation from activation, applied two intended node labels, and proved activation readiness without deploying centralized logging. |
| **When** | **Completed:** 2026-07-28T00:48:00-05:00; **evidence collected:** 2026-07-28T00:48:00-05:00; **local timezone:** America/Chicago; **system timestamps:** America/Chicago; **valid as of:** 2026-07-28; **review due:** event-based. The terminal timestamps and record timestamps use the same local UTC-05:00 offset. |
| **Where** | **Environment:** homelab; **cluster:** kalaxy3; **execution host:** donbs-imac; **controller:** donbs-imac; **nodes:** arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; **addresses:** arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62; **namespaces:** observability; longhorn-system; **endpoints:** not-applicable; **record:** markdown/operations/kalaxy3-sage-observability-iterative-readiness-evidence.md. |
| **Why** | Centralized logging needed to become reviewable and activation-ready without bypassing repository authority, silently deploying software, or losing the failed paths that explain the final design. SAGE supplied the discovery, source, validation, evidence, and publication contracts used to constrain each correction. |
| **How** | ChatGPT repeatedly inspected repository authorities, proposed exact terminal blocks, evaluated observed failures, converted each failure into repository-owned automation or validation, ran guardrails and dry-runs, created small commits, pushed secured checkpoints, and generated this evidence package through the SAGE schema 1.2 process. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Repository-owned SAGE change discovery, source authority, evidence orchestration, and publication contracts used during the session.
- Approved Helm repositories, URL fingerprints, and exact Loki and Fluent Bit Collector chart locks.
- Loki chart compatibility values, Fluent Bit all-node collection values, Grafana datasource rendering, and exact-chart manifest assertions.
- Retirement of obsolete Kubernetes Dashboard source while retaining the supported Headlamp path.
- Workload-pool label reconciliation for `amd64-01=ai` and `amd64-02=platform-services`.
- Failed validation paths, corrective iterations, idempotency, cluster guardrails, server-side dry-runs, commits, and pushes.

### Out of scope

- Activating `deploy_centralized_logging`.
- Installing Loki or Fluent Bit Collector.
- Post-deployment log ingestion, query, retention-expiry, restart, failure-recovery, performance, and Kubecost measurements.
- Rewriting historical evidence or resolving existing legacy-registry curation notices.

### Nonclaims

This record does **not** claim that centralized logging is operating in the cluster, that application logs are queryable in Grafana, or that the staged design has completed post-deployment reliability and cost validation.

## Final accepted state

```text
Repository-owned SAGE governance
  -> approved and fingerprinted Helm sources
  -> exact Loki 18.5.4 and Fluent Bit Collector 1.0.9 locks
  -> repository-owned values and exact-chart rendering
  -> unique amd64-02 platform-services placement
  -> Kubernetes server-side dry-run acceptance
  -> deploy_centralized_logging=false
  -> no Loki or Fluent Bit release or workload
```

| Item | Accepted result |
|---|---|
| SAGE workflow | Repository discovery, guardrails, evidence orchestration, and publisher remain authoritative. |
| Helm sources | `grafana-community` and `fluent` repositories are approved with URL SHA-256 fingerprints. |
| Chart locks | Loki `18.5.4` and Fluent Bit Collector `1.0.9` are exact and gated by `deploy_centralized_logging`. |
| Loki staging | Monolithic filesystem deployment, Longhorn `40Gi`, `168h` retention, AMD64 platform-services placement, no Canary, and no chart test. |
| Collector staging | One Fluent Bit Collector DaemonSet is rendered for all nodes with Loki output and persistent buffering. |
| Placement | `amd64-01=ai`; `amd64-02=platform-services`; the Loki selector resolves uniquely to `amd64-02`. |
| Activation | Gate remains `false`; server-side dry-runs persisted no logging resources. |
| Repository | Branch and remote matched at `a4a11fc03dec92663a7e31924e8b3690d68aec4e` with divergence `0 0` and a clean tree. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | SAGE repository authorities governed discovery, validation, evidence generation, and publication for this session. | critical | `EV-001`; `EV-002` | supported | high |
| `CLM-002` | Loki and Fluent Bit Collector use approved repositories and exact chart locks tied to the staged activation variable. | critical | `EV-003` | supported | high |
| `CLM-003` | The locked charts render manifests matching the intended placement, storage, retention, and all-node collector design. | critical | `EV-004`; `EV-008` | supported | high |
| `CLM-004` | Obsolete Kubernetes Dashboard source was retired while the supported Headlamp release remained governed. | high | `EV-005` | supported | high |
| `CLM-005` | Live workload-pool labels match repository intent and select only `amd64-02` for the staged Loki workload. | critical | `EV-006` | supported | high |
| `CLM-006` | Placement-label reconciliation reaches steady state with `changed=0` and `failed=0`. | high | `EV-007` | supported | high |
| `CLM-007` | Kubernetes accepted Loki, Fluent Bit, and Grafana datasource manifests through server-side dry-run without persisting resources. | critical | `EV-008`; `EV-010` | supported | high |
| `CLM-008` | Source, deployment, cluster, Helm-lock, render, and SAGE guardrails passed at the final checkpoint. | critical | `EV-009` | supported | high |
| `CLM-009` | Centralized logging remained a staged observability implementation and no Loki or Fluent Bit deployment occurred. | critical | `EV-010` | supported | high |
| `CLM-010` | Failed checks exposed real process defects and each accepted correction was reconciled into repository-owned automation before push. | high | `EV-011`; `EV-012` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The initial observability work was technically reviewable but not yet safe to activate. The session exposed several defects: repository-source and chart-lock gaps, Loki chart compatibility requirements, obsolete Dashboard source, missing live workload-pool labels, placement reconciliation coupled to deployment, a controller kubeconfig path intended for remote K3s nodes, and an unavailable Python Kubernetes client in the controller virtual environment.

### Decision

Treat centralized logging as a staged observability implementation. Use SAGE to discover authoritative files and validation duties, correct each defect in repository-owned code, preserve failed attempts as evidence, keep the activation gate false, and stop after placement and Kubernetes dry-run readiness.

### Decision drivers

- Prevent accidental deployment while implementation and evidence mature.
- Keep Git and repository-owned automation authoritative across controllers.
- Lock third-party repositories and charts exactly.
- Convert live prerequisite changes into repeatable and idempotent automation.
- Preserve the reasoning value of failed checks rather than publishing only a polished final result.
- Make the eventual activation a bounded, separately reviewable step.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Deploy immediately and debug live | Fastest route to runtime feedback | High blast radius; weak lineage; harder rollback; violates staged intent | rejected |
| Leave placement labels as manual commands | Simple one-time change | Controller and cluster state would diverge from repository intent | rejected |
| Install the Python Kubernetes client ad hoc | Retains `kubernetes.core.k8s` for label patching | Adds an ungoverned controller dependency for a simple operation | rejected |
| Reuse repository-owned `kubectl label` with server dry-run | No new dependency; auditable; idempotent; works from repository kubeconfig | Requires explicit changed-state parsing | accepted |
| Hide failed attempts from final evidence | Cleaner narrative | Loses causal evidence and future troubleshooting value | rejected |

### Tradeoffs and consequences

- The final design is more repeatable and reviewable, but activation is intentionally delayed.
- Server-side dry-run proves API acceptance, not runtime health or log delivery.
- Two node labels changed live before deployment; their intended state is now represented in repository automation.
- Disabling Loki Canary and the chart test avoids an incompatible test path, but shifts validation responsibility to repository render checks and later post-deployment tests.

## Architecture or change description

```text
ChatGPT request
  -> SAGE change discovery and authority map
  -> repository inspection
  -> defect or failed check
  -> bounded repository correction
  -> syntax, source, deployment, render, cluster, and SAGE guardrails
  -> commit and push checkpoint
  -> repeat until activation-ready

Staged observability data path after activation:
K3s node logs
  -> Fluent Bit Collector DaemonSet on all seven nodes
  -> loki-gateway.observability.svc.cluster.local
  -> monolithic Loki on amd64-02
  -> Longhorn 40Gi filesystem storage with 168h retention
  -> Grafana datasource
```

### Before

Chart source and compatibility details were incomplete, obsolete Dashboard source remained, logging placement labels were declared but absent live, label reconciliation was coupled to deployment, and controller-local execution assumptions caused check-mode failures.

### After

Approved repositories and chart locks are exact; Loki and Fluent Bit manifests are validated from repository-owned values; Dashboard source is retired; the placement prerequisite is independently reconciled and idempotent; the unique target is ready and Longhorn-schedulable; the API accepts all manifests in dry-run; and the activation gate remains false.

## Source of truth and implementation lineage

### Repository files

```text
AGENTS.md
SAGE.md
sage-change-authority.json
sage-evidence-policy.json
markdown/standards/kalaxy3-sage-change-discovery-process.md
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/kalaxy3-sage-evidence-orchestration-process.md
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-evidence-orchestrator.py
scripts/sage/sage-index.py
scripts/sage/sage-publish.py
infrastructure/k3s-homelab/helm-repositories.json
infrastructure/k3s-homelab/helm-chart-lock.json
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/playbooks/tasks/centralized-logging-node-labels.yml
infrastructure/k3s-homelab/playbooks/reconcile-centralized-logging-labels.yml
infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2
infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml
infrastructure/k3s-homelab/scripts/validate-centralized-logging-yaml.py
```

### Implementation commit

```text
a4a11fc03dec92663a7e31924e8b3690d68aec4e
Separate logging placement label reconciliation
```

Session checkpoint sequence:

```text
133d844  Add repository-owned SAGE change governance
abea253b763bbede21226ca559354bcc0ca19650  Lock centralized logging Helm charts
69237e1bffe586a5cdb115b5f56cb8f193d8c404  Complete Loki chart compatibility values
8e41f83ac5475cb5ee6ab46b749bd468c8c923e8  Retire obsolete Kubernetes Dashboard source
82da6e90932ac6dd8caafaf03c7d415e6887d2a2  Validate locked centralized logging charts
a4a11fc03dec92663a7e31924e8b3690d68aec4e  Separate logging placement label reconciliation
```

The full SHA for the earlier `133d844` governance checkpoint was not present in the captured generator bundle; the short reference and subject are preserved from the session transcript as an explicit lineage limitation.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE record schema | 1.2 | Metadata contract and publisher |
| K3s | v1.36.2+k3s1 | Live node output |
| Helm | v3.21.3+g1ad6e68 | Repository controller preflight |
| ansible-core | 2.18.7 | Repository controller preflight |
| kubernetes.core | 5.1.0 | Repository controller preflight |
| Loki chart | 18.5.4 | `helm-chart-lock.json` |
| Fluent Bit Collector chart | 1.0.9 | `helm-chart-lock.json` |
| Longhorn chart | 1.12.0 | `helm-chart-lock.json` and lock reconciliation |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Helm repository fingerprints, chart lock, repository Helm wrapper, virtual environment, and playbooks captured in `EV-001` through `EV-004`. |
| Controller bootstrap | `make centralized-logging-render` invokes controller preflight and repository Helm installation. |
| Controller preflight | Core, Helm, and cluster scopes passed on `donbs-imac`. |
| Controller host | `donbs-imac` |
| Execution host | `donbs-imac` |
| Machine-local authoritative state | Kubeconfig and credentials remain local execution inputs; persistent deployment intent is stored in the repository. |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual runtime changes were reconciled into repository-owned automation.
- [x] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
deploy_centralized_logging: false
centralized_logging_namespace: observability
centralized_logging_workload_pool: platform-services
centralized_logging_expected_node: amd64-02
loki_storage_class: longhorn
loki_storage_size: 40Gi
loki_retention_period: 168h
```

## Prerequisites and assumptions

### Proven prerequisites

- The repository branch and its remote matched at `a4a11fc03dec92663a7e31924e8b3690d68aec4e` (`EV-002`).
- All seven inventory hosts passed noninteractive SSH and privilege-escalation preflight (`EV-009`).
- `amd64-02` was Ready, labeled `platform-services`, and Longhorn Ready and Schedulable (`EV-006`).
- The `longhorn` StorageClass existed with `driver.longhorn.io`, `Retain`, and `Immediate` binding (`EV-006`).
- The repository Helm wrapper and exact chart locks rendered both staged charts (`EV-004`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The current observability namespace and Prometheus/Grafana release remain healthy when logging is later activated. | Datasource or ServiceMonitor integration could fail despite manifest acceptance. | Validate Grafana datasource discovery, Prometheus target health, and dashboard loading after activation. |
| `ASM-002` | Longhorn capacity on `amd64-02` is sufficient for the requested `40Gi` volume and seven-day retention under actual log volume. | PVC pressure or retention behavior could differ from the staged estimate. | Measure ingestion volume, PVC use, compaction, and retention expiry after deployment. |
| `ASM-003` | Disabling Loki Canary and chart tests is acceptable when replaced by repository checks and explicit runtime acceptance tests. | Some data-path failures may not be detected automatically. | Add post-deployment write, query, restart, and recovery tests before acceptance. |

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
grep -nE '^deploy_centralized_logging:[[:space:]]*false$' inventory/group_vars/all/main.yml
make source-guardrails
make deployment-guardrail
```

### Execution

```bash
.venv/bin/ansible-playbook -i inventory/hosts.yml   playbooks/reconcile-centralized-logging-labels.yml

make centralized-logging-render

kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply   --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/manifests/loki-manifests.yml

kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply   --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/manifests/fluent-bit-manifests.yml

kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply   --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/grafana-loki-datasource.yml

make cluster-guardrails
```

### Expected change

Only the two declared workload-pool labels should be persisted. Rendering and server-side dry-runs should not create Helm releases or Kubernetes logging resources. The activation gate should remain false.

### Observed change

`amd64-01` changed to `ai`; `amd64-02` changed to `platform-services`; a rerun reported `changed=0`; all rendered objects were accepted by the API in server dry-run; no logging release or workload appeared; and the branch was pushed cleanly with divergence `0 0` (`EV-006` through `EV-010`).

### Failed or superseded paths

1. A readiness script attempted to parse vaulted inventory YAML with a generic YAML loader; `!vault` prevented reliable extraction. The approach was superseded by repository-aware extraction and direct inventory inspection.
2. Repository declarations existed but both live workload-pool labels were missing. The session separated label reconciliation into a dedicated prerequisite playbook.
3. The first dedicated check-mode run used `/etc/rancher/k3s/k3s.yaml`, a remote-node path unavailable on the iMac controller. The playbook was corrected to use the repository controller kubeconfig.
4. The next check-mode run reached the correct kubeconfig but `kubernetes.core.k8s` could not import the Python `kubernetes` client from the repository virtual environment. Rather than adding an ad hoc dependency, the task was changed to the repository-owned `kubectl label` pattern with server-side dry-run.
5. The final check-mode preview changed nothing; the actual label reconciliation changed only the two intended nodes and became idempotent.

## Evidence items

### `EV-001` — SAGE authority discovery and evidence contract

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001` |
| Collected by | ChatGPT |
| Collected at | 2026-07-28T00:48:00-05:00 |
| Execution source | generator input bundle |
| Target | Kalaxy3 repository governance and evidence authorities |
| Tool and version | SAGE schema 1.2 |
| Expected result | Authoritative discovery, validation, and publication paths are identified |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/repository-authority-evidence.md` |

**Command, query, source, or observation**

```bash
SAGE_REQUEST='Generate a comprehensive SAGE evidence package ...' make sage-evidence-brief
SAGE_REQUEST='Generate a comprehensive SAGE evidence package ...' make sage-evidence-prepare
```

**Observed result**

```text
Inferred contexts included repository-governance, evidence, helm-platform,
observability, centralized-logging, storage, and k3s-cluster.
Kalaxy3 SAGE evidence-generation inputs: PASS
Bundle: /private/tmp/kalaxy3-sage-evidence-inputs.zip
```

**Interpretation**

SAGE identified the repository-owned standards, metadata contract, templates, publisher, indexer, Helm authorities, observability files, and required validation. It proves governance discovery, not runtime logging behavior.

### `EV-002` — Published implementation checkpoint and clean branch

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001`; `CLM-008` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:48:00-05:00 |
| Execution source | donbs-imac |
| Target | Git branch `wip/centralized-logging-staged-20260726` |
| Tool and version | Git=version-not-recorded |
| Expected result | Local and remote commit match with zero divergence and clean tree |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
git push origin wip/centralized-logging-staged-20260726
git fetch origin
git rev-list --left-right --count HEAD...origin/wip/centralized-logging-staged-20260726
git status
```

**Observed result**

```text
local=a4a11fc03dec92663a7e31924e8b3690d68aec4e
remote=a4a11fc03dec92663a7e31924e8b3690d68aec4e
PASS local and remote checkpoints match
0  0
nothing to commit, working tree clean
```

**Interpretation**

The final staged implementation checkpoint was secured remotely and the repository was clean before evidence generation.

### `EV-003` — Approved repositories and exact chart locks

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002` |
| Collected by | ChatGPT |
| Collected at | 2026-07-28T00:48:00-05:00 |
| Execution source | generator input bundle |
| Target | Helm repository and chart-lock contracts |
| Tool and version | SAGE source guardrail=repository version |
| Expected result | Logging charts have approved HTTPS repositories, fingerprints, exact versions, namespaces, releases, and activation variable |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/repository-authority-evidence.md` |

**Command, query, source, or observation**

```text
infrastructure/k3s-homelab/helm-repositories.json
infrastructure/k3s-homelab/helm-chart-lock.json
```

**Observed result**

```text
grafana-community URL fingerprint: 206ac5464a9fcfa3442aa8c4f732e5017d88ffedfbee02e2ff2bed5cb58e67e3
fluent URL fingerprint: b16bb56016f47f67656cfbd58474bd8df8db9000c48377b2cef31927f3c33910
loki: grafana-community/loki 18.5.4, release loki, namespace observability
fluent_bit_collector: fluent/fluent-bit-collector 1.0.9, release fluent-bit-collector, namespace observability
both enabled_variable: deploy_centralized_logging
```

**Interpretation**

The repository, not controller-local Helm state, owns the accepted sources and versions.

### `EV-004` — Exact locked-chart rendering and manifest assertions

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:47:00-05:00 |
| Execution source | donbs-imac |
| Target | rendered Loki and Fluent Bit manifests |
| Tool and version | Helm=v3.21.3+g1ad6e68 |
| Expected result | Exact locked charts render and satisfy repository assertions |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make centralized-logging-render
```

**Observed result**

```text
PASS locked chart render: grafana-community/loki version=18.5.4 release=loki namespace=observability
PASS locked chart render: fluent/fluent-bit-collector version=1.0.9 release=fluent-bit-collector namespace=observability
PASS Loki manifests: amd64/platform-services, Longhorn=40Gi, filesystem storage, no test hook
PASS Fluent Bit manifests: one all-node DaemonSet in observability
PASS locked centralized-logging chart validation
```

**Interpretation**

The rendered objects match the staged architecture. This does not prove rollout or data-path behavior.

### `EV-005` — Obsolete Kubernetes Dashboard source retirement

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-004` |
| Collected by | ChatGPT |
| Collected at | 2026-07-28T00:48:00-05:00 |
| Execution source | repository evidence and session transcript |
| Target | UI Helm source governance |
| Tool and version | Git=version-not-recorded |
| Expected result | Dashboard source and lock references removed; supported Headlamp path retained |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/repository-authority-evidence.md` |

**Command, query, source, or observation**

```text
8e41f83ac5475cb5ee6ab46b749bd468c8c923e8 Retire obsolete Kubernetes Dashboard source
```

**Observed result**

```text
The current approved repository contract contains Headlamp and no Kubernetes Dashboard repository.
The current chart lock contains Headlamp 0.43.0 and no Kubernetes Dashboard release.
Session validation confirmed no Dashboard release or resources.
```

**Interpretation**

The current repository source contract supports Headlamp and excludes the obsolete Dashboard path. Historical documentation was preserved separately.

### `EV-006` — Live placement and Longhorn readiness

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:47:00-05:00 |
| Execution source | donbs-imac |
| Target | amd64-01, amd64-02, and Longhorn node amd64-02 |
| Tool and version | kubectl=cluster client |
| Expected result | Exact labels, unique selector, Ready node, and schedulable Longhorn target |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
kubectl --kubeconfig kubeconfig-kalaxy3.yaml get nodes   -L kubernetes.io/arch -L kalaxy3.io/workload-pool -o wide
kubectl --kubeconfig kubeconfig-kalaxy3.yaml get nodes   --selector='kubernetes.io/arch=amd64,kalaxy3.io/workload-pool=platform-services' -o name
kubectl --kubeconfig kubeconfig-kalaxy3.yaml -n longhorn-system   get nodes.longhorn.io amd64-02 -o json
```

**Observed result**

```text
amd64-01=ai
amd64-02=platform-services
node/amd64-02
architecture=amd64
workload_pool=platform-services
ready=True
longhorn_ready=True
longhorn_schedulable=True
```

**Interpretation**

The intended Loki selector has one eligible node and that node can host Longhorn-backed stateful storage.

### `EV-007` — Placement reconciliation idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:47:00-05:00 |
| Execution source | donbs-imac |
| Target | dedicated centralized-logging label reconciliation playbook |
| Tool and version | ansible-core=2.18.7 |
| Expected result | Second run reports no changes and no failures |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
.venv/bin/ansible-playbook -i inventory/hosts.yml   playbooks/reconcile-centralized-logging-labels.yml
```

**Observed result**

```text
localhost : ok=5 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
PASS label reconciliation is idempotent
```

**Interpretation**

The live prerequisite can be reapplied safely and has converged to repository intent.

### `EV-008` — Kubernetes server-side dry-run acceptance

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003`; `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:47:00-05:00 |
| Execution source | donbs-imac |
| Target | Kalaxy3 Kubernetes API and observability namespace |
| Tool and version | kubectl=cluster client |
| Expected result | API accepts all staged objects without persistence |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/manifests/loki-manifests.yml
kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/manifests/fluent-bit-manifests.yml
kubectl --kubeconfig kubeconfig-kalaxy3.yaml apply --dry-run=server --validate=true   --field-manager=kalaxy3-centralized-logging-readiness   -f /tmp/kalaxy3-centralized-logging-render/grafana-loki-datasource.yml
```

**Observed result**

```text
PASS Loki manifests accepted by Kubernetes dry-run
PASS Fluent Bit manifests accepted by Kubernetes dry-run
PASS Grafana datasource accepted by Kubernetes dry-run
PASS server-side dry-run persisted no logging resources
```

**Interpretation**

The current API and installed CRDs accept the staged object set. The evidence remains pre-deployment and does not prove pod startup or log flow.

### `EV-009` — Final guardrail and lock reconciliation results

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-008` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:47:00-05:00 |
| Execution source | donbs-imac |
| Target | repository, seven-node inventory, and installed Helm releases |
| Tool and version | SAGE guardrails=repository versions |
| Expected result | Required guardrails pass and staged releases are skipped |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make source-guardrails
make deployment-guardrail
make centralized-logging-render
make cluster-guardrails
make -C ../.. sage-guardrails
```

**Observed result**

```text
Kalaxy3 SAGE source guardrails: PASS
Kalaxy3 SAGE deployment guardrail: PASS
Kalaxy3 SAGE bootstrap guardrails: PASS
Kalaxy3 Helm lock reconciliation: PASS
PASS 6 installed locked releases; 0 permitted new releases
SKIP fluent_bit_collector: release is not enabled
SKIP loki: release is not enabled
Kalaxy3 SAGE cluster deployment guardrails: PASS
Kalaxy3 repository SAGE guardrails: PASS
```

**Interpretation**

The final repository and cluster state passed the required controls while the two logging releases remained disabled by the staged activation variable.

### `EV-010` — Negative evidence that logging remained undeployed

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-007`; `CLM-009` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:48:00-05:00 |
| Execution source | donbs-imac |
| Target | Helm releases and Kubernetes logging resources |
| Tool and version | Helm=v3.21.3+g1ad6e68; kubectl=cluster client |
| Expected result | No logging release or persisted logging resource exists and activation gate is false |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
scripts/helm list --all-namespaces --short | grep -E '^(loki|fluent-bit-collector)$'
kubectl --kubeconfig kubeconfig-kalaxy3.yaml -n observability get   deployment,statefulset,daemonset,pod,service,pvc,configmap,secret,serviceaccount,role,rolebinding -o name
grep -nE '^deploy_centralized_logging:[[:space:]]*false$' inventory/group_vars/all/main.yml
```

**Observed result**

```text
PASS Loki and Fluent Bit Helm releases are absent
PASS centralized logging resources are absent
PASS server-side dry-run persisted no logging resources
52:deploy_centralized_logging: false
NO LOGGING DEPLOYMENT OCCURRED
```

**Interpretation**

The only persistent runtime changes were the two intended node labels. No centralized logging component was installed.

### `EV-011` — Failed controller kubeconfig path

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:36:00-05:00 |
| Execution source | donbs-imac |
| Target | first dedicated placement-label check-mode run |
| Tool and version | ansible-core=2.18.7 |
| Expected result | Server-side label preview from the controller |
| Actual result | fail |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
.venv/bin/ansible-playbook -i inventory/hosts.yml   playbooks/reconcile-centralized-logging-labels.yml --check --diff
```

**Observed result**

```text
Could not find or access '/etc/rancher/k3s/k3s.yaml' on the Ansible Controller.
localhost : ok=4 changed=0 unreachable=0 failed=1
```

**Interpretation**

The playbook inherited a remote-node kubeconfig path on a local controller. The failure occurred before a cluster write and led to an explicit repository controller kubeconfig override.

### `EV-012` — Missing Python Kubernetes client and accepted correction

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-28T00:41:00-05:00 |
| Execution source | donbs-imac |
| Target | placement-label task implementation |
| Tool and version | ansible-core=2.18.7; kubernetes.core=5.1.0 |
| Expected result | Check-mode preview without adding controller dependencies or changing labels |
| Actual result | pass after one failed attempt |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` |

**Command, query, source, or observation**

```text
Failed path: kubernetes.core.k8s using the repository virtual environment.
Accepted path: repository-owned kubectl label --dry-run=server in Ansible check mode,
followed by kubectl label --overwrite for the bounded apply.
```

**Observed result**

```text
Failed to import the required Python library (kubernetes) on donbs-imac.local's
Python .../.venv/bin/python.

After correction:
Preview centralized logging workload-pool label: ok for amd64-01 and amd64-02
localhost : ok=5 changed=0 unreachable=0 failed=0 skipped=1
PASS amd64-01 remains unlabeled after server dry-run
PASS amd64-02 remains unlabeled after server dry-run
```

**Interpretation**

The session avoided an ad hoc dependency, reused an existing repository execution pattern, and proved that the preview path was non-mutating before applying the labels.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Approved exact chart sources and versions | `EV-003` | fingerprinted repositories and fixed versions | observed | pass |
| `AC-002` | Exact locked charts render | `EV-004` | Loki and Fluent Bit manifests satisfy assertions | observed | pass |
| `AC-003` | Unique Loki placement | `EV-006` | selector returns only `node/amd64-02` | observed | pass |
| `AC-004` | Placement automation is idempotent | `EV-007` | rerun has `changed=0` and `failed=0` | observed | pass |
| `AC-005` | API accepts staged object set | `EV-008` | three server-side dry-runs pass | observed | pass |
| `AC-006` | No deployment occurs | `EV-010` | no releases or resources and gate false | observed | pass |
| `AC-007` | Repository and cluster guardrails pass | `EV-009` | all required final controls pass | observed | pass |
| `AC-008` | Failed paths are preserved and corrected in source | `EV-011`; `EV-012` | causal failures and accepted corrections are documented | observed | pass |

### Functional verification

```bash
make centralized-logging-render
.venv/bin/ansible-playbook -i inventory/hosts.yml playbooks/reconcile-centralized-logging-labels.yml
make cluster-guardrails
```

Observed:

```text
PASS locked centralized-logging chart validation
PASS label reconciliation is idempotent
Kalaxy3 SAGE cluster deployment guardrails: PASS
```

### Negative verification

```bash
scripts/helm list --all-namespaces --short | grep -E '^(loki|fluent-bit-collector)$'
grep -nE '^deploy_centralized_logging:[[:space:]]*false$' inventory/group_vars/all/main.yml
```

Observed:

```text
No Loki or Fluent Bit release matched.
52:deploy_centralized_logging: false
NO LOGGING DEPLOYMENT OCCURRED
```

## Idempotency and repeatability

### First accepted run

```text
Reconcile centralized logging workload-pool label:
changed for amd64-01
changed for amd64-02
localhost : ok=5 changed=1 unreachable=0 failed=0 skipped=1
```

### Steady-state rerun

```text
Reconcile centralized logging workload-pool label:
ok for amd64-01
ok for amd64-02
localhost : ok=5 changed=0 unreachable=0 failed=0 skipped=1
```

### Interpretation

The prerequisite playbook converges to the inventory-declared label state. Exact-chart rendering is deterministic under the repository lock, while server-side dry-run is intentionally non-persistent.

## Security, privacy, and evidence handling

### Security controls

- Repository-owned Helm wrapper and isolated Helm state prevent inherited controller overrides.
- Approved repository URLs are HTTPS-only and protected by recorded URL SHA-256 fingerprints.
- Exact chart versions prevent unconstrained dependency drift.
- The deployment gate prevents accidental Loki or Fluent Bit installation during staging.
- Server-side dry-run used a dedicated field manager and was followed by absence checks.
- Terminal evidence excludes kubeconfig contents, credentials, Secret values, private keys, and authentication material.

### Sensitive material excluded

- Kubeconfig data and client credentials.
- Passwords, tokens, private keys, and Kubernetes Secret contents.
- Unnecessary personal or workstation data beyond the named operator and controller host required for lineage.

### Redactions and omissions

- Terminal output was reduced to materially relevant lines; no secret-bearing configuration was copied.
- The full short-lived render directory was not packaged because it can be regenerated from locked repository inputs.

### Residual security risk

- Loki authentication is disabled inside the cluster values; network exposure and access controls must be reviewed during activation.
- Fluent Bit will read node log paths after activation; namespace and data-sensitivity handling require operational review.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Wrong or missing placement label | Selector does not return exactly `node/amd64-02` | Loki cannot schedule as intended | Run the dedicated label reconciliation playbook and verify selector output. |
| Controller uses remote kubeconfig path | Ansible reports `/etc/rancher/k3s/k3s.yaml` missing | Prerequisite automation cannot reach cluster | Use repository controller kubeconfig authority in the dedicated localhost playbook. |
| Python Kubernetes client unavailable | `kubernetes.core.k8s` import failure | Module-based label patch fails | Use the repository-owned `kubectl` label task and server-side dry-run. |
| Locked chart no longer renders | `make centralized-logging-render` fails | Activation blocked | Update values and lock together under SAGE review; do not deploy. |
| Longhorn target not schedulable | Longhorn node condition is not True | Loki PVC or pod placement fails | Repair Longhorn node readiness before activation. |
| Dry-run unexpectedly persists resources | Absence verification finds logging objects | Staging boundary violated | Stop, inspect field-manager actions, remove unintended resources, and rerun guardrails. |

### Rollback

```bash
kubectl --kubeconfig infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml   label node amd64-01 kalaxy3.io/workload-pool-

kubectl --kubeconfig infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml   label node amd64-02 kalaxy3.io/workload-pool-
```

A repository rollback should revert the placement-label reconciliation commit only when the labels are no longer part of intended platform placement. No Loki or Fluent Bit uninstall is required because neither release was installed.

### Rebuild procedure

1. Clone and synchronize `donb4iu/Kalaxy3` at the implementation checkpoint or a later accepted descendant.
2. Run repository controller bootstrap and core, Helm, and cluster preflight.
3. Verify `deploy_centralized_logging: false`.
4. Run source and deployment guardrails.
5. Run the dedicated placement-label reconciliation playbook.
6. Verify the unique `amd64-02` selector and Longhorn readiness.
7. Run `make centralized-logging-render`.
8. Run the three server-side Kubernetes dry-runs.
9. Verify no logging release or object persisted.
10. Run cluster and SAGE guardrails.

### Data durability and backup impact

No logging data or PVC was created. The staged Loki values request a `40Gi` Longhorn volume with retention behavior and retained persistence policies after activation, but durability, backup, recovery-point, and recovery-time behavior remain untested until deployment.

## Operational considerations and observability

### Health signals

- Node readiness and the `kalaxy3.io/workload-pool` labels.
- Longhorn node Ready and Schedulable conditions.
- Locked-chart render assertions.
- Helm release absence before activation.
- Kubernetes logging-resource absence after dry-run.
- After activation: Loki gateway readiness, StatefulSet readiness, Fluent Bit DaemonSet availability, PodMonitor targets, Grafana datasource discovery, ingestion errors, query success, PVC usage, and retention expiry.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
make centralized-logging-render
make cluster-guardrails
kubectl --kubeconfig kubeconfig-kalaxy3.yaml get nodes   -L kubernetes.io/arch -L kalaxy3.io/workload-pool
scripts/helm list --all-namespaces
```

### Capacity, performance, cost, and sustainability

- **Capacity:** A `40Gi` Longhorn volume is staged; actual seven-day log volume is unmeasured.
- **Performance:** Resource requests and limits are defined, but ingestion throughput and query latency are unmeasured.
- **Cost:** No new workloads were deployed, so this session added no logging runtime allocation; post-deployment Kubecost comparison is pending.
- **Sustainability/power:** No new continuously running workload was introduced; incremental power must be measured after activation.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Full 40-character SHA for the earlier `133d844` SAGE governance checkpoint was absent from the captured generator bundle. | Earlier governance lineage is preserved only by short reference and subject in this record. | Kalaxy3 architecture | Resolve during review when the commit is reachable. |
| `GAP-002` | evidence-gap | The vaulted-YAML parsing failure is preserved as a session observation, but its complete raw terminal transcript was not supplied in the generator input ZIP. | Exact traceback cannot be independently replayed from the package. | Kalaxy3 architecture | Attach or recover the original transcript when available. |
| `GAP-003` | limitation | Server-side dry-run does not prove pod scheduling, image pulls, readiness, log ingestion, queryability, or restart recovery. | Activation could reveal runtime defects. | Kalaxy3 architecture | On activation. |
| `GAP-004` | evidence-gap | Loki retention expiry, compaction, PVC growth, backup, restore, and failure recovery are untested. | Data durability and capacity confidence remain provisional. | Kalaxy3 architecture | After at least one retention window. |
| `GAP-005` | evidence-gap | Fluent Bit delivery from every node, buffering during Loki outage, duplicate handling, and backpressure are untested. | Collection reliability is not yet proven. | Kalaxy3 architecture | Post-deployment acceptance. |
| `GAP-006` | evidence-gap | Grafana datasource discovery and user queries are untested because the datasource ConfigMap was only dry-run. | Operator usability is not yet proven. | Kalaxy3 architecture | Post-deployment acceptance. |
| `GAP-007` | risk | Loki Canary and the chart test are disabled for chart compatibility. | Automated end-to-end detection is reduced. | Kalaxy3 architecture | Replace with explicit runtime smoke and recovery tests. |
| `GAP-008` | evidence-gap | Kubecost, power, and performance impact are unmeasured because no logging workload was deployed. | Cost and sustainability claims cannot yet be made. | Kalaxy3 architecture | Compare pre- and post-deployment baselines. |

## Troubleshooting

### Check mode cannot find `/etc/rancher/k3s/k3s.yaml`

**Meaning**

The localhost playbook inherited a kubeconfig path intended for a remote K3s server.

**Checks**

```bash
grep -n 'kalaxy3_kubeconfig'   playbooks/reconcile-centralized-logging-labels.yml   inventory/group_vars/all/main.yml
```

**Recovery**

Use the repository controller kubeconfig path in the dedicated localhost playbook and rerun `--check --diff`. Confirm both labels remain unchanged after preview.

### Ansible cannot import the Python Kubernetes client

**Meaning**

The selected virtual environment does not contain the Python client required by `kubernetes.core.k8s`.

**Checks**

```bash
.venv/bin/python -c 'import kubernetes'
```

**Recovery**

Do not add an ad hoc dependency for this label-only path. Use the accepted repository-owned `kubectl label --dry-run=server` preview and `kubectl label --overwrite` reconciliation task.

### Loki chart render reports missing bucket names or test dependency

**Meaning**

Chart `18.5.4` validates bucket-name keys even with filesystem storage, and the chart test expects Loki Canary.

**Checks**

```bash
grep -nE 'bucketNames|lokiCanary|test:'   playbooks/templates/loki-values.yml.j2
make centralized-logging-render
```

**Recovery**

Retain the filesystem placeholder bucket names and explicitly disable both Loki Canary and the chart test unless a later chart-lock change is separately validated.

### Unique placement selector returns no node or multiple nodes

**Meaning**

Live placement labels do not match inventory intent.

**Checks**

```bash
kubectl --kubeconfig kubeconfig-kalaxy3.yaml get nodes   --selector='kubernetes.io/arch=amd64,kalaxy3.io/workload-pool=platform-services'   -o name
```

**Recovery**

Run `playbooks/reconcile-centralized-logging-labels.yml`, verify `amd64-01=ai` and `amd64-02=platform-services`, and require exactly `node/amd64-02` before activation.

## Freshness, revalidation, and supersession

### Revalidate when

- either approved logging Helm repository URL or fingerprint changes;
- Loki or Fluent Bit Collector chart version changes;
- the SAGE metadata, publisher, discovery, or evidence-orchestration contract changes;
- the logging activation variable changes;
- placement labels, expected node, architecture, Longhorn state, namespace, storage size, or retention changes;
- Loki Canary or chart-test policy changes;
- the observability phase, templates, validator, or dedicated label playbook changes;
- a dry-run, render, lock reconciliation, or cluster guardrail stops passing;
- centralized logging is activated or removed.

### Scheduled review

```text
event-based: immediately before activation, after initial deployment acceptance,
and after the first complete 168-hour retention window
```

### Supersession rule

When a deployment evidence record proves runtime ingestion and operations, set this record to `superseded` only for activation-readiness claims it replaces. Preserve the iterative failure and governance history and link the later record through `superseded_by`.

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
- [x] Every unavailable or incomplete source fact has an evidence gap.

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
| Owner | Kalaxy3 architecture | pending | pending | Technical validation is complete; deployment remains staged. |
| Reviewer | pending | pending | pending | Governance acceptance and activation approval are separate future actions. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-sage-observability-iterative-evidence.zip

python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-sage-observability-iterative-evidence.zip   --push
```

The package uses `evidence-only` publication and pins the implementation lineage to `a4a11fc03dec92663a7e31924e8b3690d68aec4e`. The publisher owns token replacement, record checksum creation, publication manifest creation, catalog reconciliation, evidence commit, safe synchronization, and push.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Terminal evidence | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/terminal-evidence.md` | recorded in `sage-package.json` | no | permanent with evidence record |
| Repository authority evidence | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/repository-authority-evidence.md` | recorded in `sage-package.json` | no | permanent with evidence record |
| Generation provenance | `markdown/evidence-artifacts/SAGE-K3-OBS-20260728-001/generation-provenance.md` | recorded in `sage-package.json` | no | permanent with evidence record |

### Original requester language

```text
Generate a comprehensive SAGE evidence package for the iterative SAGE governance and observability work completed on branch wip/centralized-logging-staged-20260726. Document how ChatGPT used the repository-owned SAGE discovery, authority, guardrail, evidence, and publication processes to inspect the repository, identify defects, propose corrections, validate them, commit them, and publish each secured checkpoint. Include the initial SAGE governance implementation, approved Helm repository and chart-lock corrections, Kubernetes Dashboard source retirement, Loki chart compatibility corrections, repository-owned exact-chart rendering and Kubernetes manifest validation, and observability placement-label reconciliation. Preserve the important failed validation attempts involving vaulted YAML parsing, missing live workload-pool labels, incorrect controller kubeconfig authority, and the unavailable Python Kubernetes client because those failures demonstrate the iterative discovery-and-correction process rather than only the final successful state. Explain the correction made for each discovered issue and the repository authority that governed it. Include every implementation commit and push checkpoint, source guardrails, deployment guardrails, K3s guardrails, cluster guardrails, Helm lock reconciliation, exact chart renders, server-side Kubernetes dry-runs, SAGE guardrails, the two intentional workload-pool node-label changes, the final activation-readiness result, remaining activation work, remaining post-deployment validation gaps, and explicit confirmation that Loki and Fluent Bit were not deployed. Describe centralized logging as a staged observability implementation, not as the entirety of the observability work. Frame the session as an evidence-driven engineering loop: SAGE discovery, repository inspection, defect identification, repository-owned correction, validation, refinement, guardrail reconciliation, commit, push, and secured checkpoint.
```

### Evidence-driven engineering loop

```text
SAGE discovery
  -> repository inspection
  -> defect identification
  -> repository-owned correction
  -> validation
  -> refinement
  -> guardrail reconciliation
  -> commit
  -> push
  -> secured checkpoint
```

### Additional notes

The record deliberately describes centralized logging as one staged observability capability. Existing Prometheus, Grafana, Kubecost, Longhorn, Headlamp, and broader platform observability remain separate capabilities and are not collapsed into the centralized-logging claim.
