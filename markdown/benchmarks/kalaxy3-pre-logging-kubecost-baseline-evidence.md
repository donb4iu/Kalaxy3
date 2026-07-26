---
evidence_id: SAGE-K3-OBSERVABILITY-20260725-001
schema_version: "1.2"
title: "Pre-Logging Kubecost Cost Baseline for Centralized Logging Comparison"
nav_title: "Capture pre-logging Kubecost baseline"
nav_section: benchmarks
nav_order: 100
summary: "Preserves checksum-verified 24-hour and 72-hour Kubecost control measurements before centralized logging changes cluster resource use and cost."
primary_subject: "Centralized logging cost baseline"
project: Kalaxy3
record_type: benchmark
status: validated
classification: internal
work_session: "Pre-centralized-logging Kubecost baseline capture"
work_started_at: 2026-07-25T20:59:49-05:00
work_completed_at: 2026-07-25T21:01:00-05:00
evidence_collected_at: 2026-07-25T21:01:00-05:00
created_at: 2026-07-25T21:15:14-05:00
updated_at: 2026-07-25T21:34:25-05:00
valid_as_of: 2026-07-25
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - "UTC"
  - "America/Chicago"
owner: "Don Buddenbaum"
author: "ChatGPT using the Kalaxy3 SAGE process and evidence collected by Don Buddenbaum"
operator: "Don Buddenbaum"
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donbs-imac
controller_host: not-applicable
nodes:
  - "arm64-01"
  - "arm64-02"
  - "arm64-03"
  - "arm64-04"
  - "arm64-05"
  - "amd64-01"
  - "amd64-02"
node_addresses:
  - "arm64-01=192.168.2.51"
  - "arm64-02=192.168.2.52"
  - "arm64-03=192.168.2.53"
  - "arm64-04=192.168.2.54"
  - "arm64-05=192.168.2.55"
  - "amd64-01=192.168.2.61"
  - "amd64-02=192.168.2.62"
namespaces:
  - "headlamp"
  - "kube-system"
  - "kubecost"
  - "longhorn-system"
  - "metallb-system"
  - "minio"
  - "observability"
  - "storage"
endpoints:
  - "kubecost-frontend=http://192.168.2.26:9090"
  - "kubecost-allocation-api=http://192.168.2.26:9090/model/allocation"
components:
  - "K3s=v1.36.2+k3s1"
  - "Kubecost=3.2.1"
  - "IBM-FinOps-Agent=v1.0.20"
  - "kube-prometheus-stack=87.19.0"
  - "Longhorn=v1.12.0"
  - "MetalLB=v0.16.1"
  - "Traefik=v3.7.1"
  - "Headlamp=0.43.0"
  - "NFS-subdir-external-provisioner=4.0.18"
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: 4388c30c5f3f4ceafd233377582cded704889b8f
record_path: markdown/benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001
confidence: high
tags:
  - "sage"
  - "observability"
  - "kubecost"
  - "benchmark"
  - "baseline"
  - "centralized-logging"
  - "pre-change"
  - "cost-comparison"
relationships:
  verifies:
    - Pre-centralized-logging Kubecost control baseline
  depends_on:
    - SAGE-K3-FINOPS-20260724-001
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - Planned centralized logging implementation and post-logging comparison
  conflicts_with:
    - none
  generated_by:
    - Manual cluster and Kubecost evidence capture from donbs-imac
    - Kubecost Allocation API
    - Kalaxy3 SAGE publication process
  implemented_by:
    - 4388c30c5f3f4ceafd233377582cded704889b8f
  revalidated_by:
    - none
---

# Pre-Logging Kubecost Cost Baseline for Centralized Logging Comparison

## Executive summary

Kalaxy3 captured and checksum-verified a pre-centralized-logging cost and
resource baseline using Kubecost, Kubernetes, Helm, and point-in-time resource
observations. The retained evidence includes explicit 24-hour and 72-hour UTC
allocation windows, raw and fully burdened cost results, seven-node cluster
state, workload placement, storage state, Helm releases, live Kubecost values,
and node and pod usage. This record validates the baseline capture only. It is
not evidence that Fluent Bit, OpenTelemetry Collector, Loki, or another
centralized logging implementation has been installed, configured, or tested.
A later post-logging record must use the same comparison method and reference,
extend, or supersede this baseline without deleting it.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBSERVABILITY-20260725-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Pre-Logging Kubecost Cost Baseline for Centralized Logging Comparison |
| **Navigation title** | Capture pre-logging Kubecost baseline |
| **Navigation section** | benchmarks |
| **Navigation order** | 100 |
| **Summary** | Preserves checksum-verified 24-hour and 72-hour Kubecost control measurements before centralized logging changes cluster resource use and cost. |
| **Primary subject** | Centralized logging cost baseline |
| **Record type** | benchmark |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Pre-centralized-logging Kubecost baseline capture |
| **Started** | 2026-07-25T20:59:49-05:00 |
| **Completed** | 2026-07-25T21:01:00-05:00 |
| **Evidence collected** | 2026-07-25T21:01:00-05:00 |
| **Record created** | 2026-07-25T21:15:14-05:00 |
| **Record updated** | 2026-07-25T21:34:25-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | UTC; America/Chicago |
| **Valid as of** | 2026-07-25 |
| **Review due** | event-based |
| **Target record path** | markdown/benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | 4388c30c5f3f4ceafd233377582cded704889b8f |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | not-applicable |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62 |
| **Namespaces** | headlamp; kube-system; kubecost; longhorn-system; metallb-system; minio; observability; storage |
| **Endpoints** | kubecost-frontend=http://192.168.2.26:9090; kubecost-allocation-api=http://192.168.2.26:9090/model/allocation |
| **Components and versions** | K3s=v1.36.2+k3s1; Kubecost=3.2.1; IBM-FinOps-Agent=v1.0.20; kube-prometheus-stack=87.19.0; Longhorn=v1.12.0; MetalLB=v0.16.1; Traefik=v3.7.1; Headlamp=0.43.0; NFS-subdir-external-provisioner=4.0.18 |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT using the Kalaxy3 SAGE process and evidence collected by Don Buddenbaum |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Navigation contract

- The formal title identifies this as a cost baseline rather than a logging installation record.
- The navigation title is the concise human-facing label used in generated evidence indexes.
- The `benchmarks` section groups this record with controlled measurements.
- The primary subject distinguishes the planned centralized-logging comparison from general Kubecost calibration.
- The explicit `[TOC]` exposes the fixed SAGE sections in Daux.io and compatible renderers.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** ChatGPT using the Kalaxy3 SAGE process and evidence collected by Don Buddenbaum; **operator:** Don Buddenbaum; **owner:** Don Buddenbaum; **reviewer:** pending; **affected users/teams:** the Kalaxy3 operator and future consumers of observability-cost evidence. |
| **What** | Captured an immutable pre-logging benchmark consisting of 24-hour and 72-hour raw and fully burdened Kubecost allocations plus contemporaneous cluster, workload, storage, Helm, and resource-usage snapshots. The primary boundary is that this proves the control measurement, not centralized logging implementation or performance. |
| **When** | **Completed:** 2026-07-25T21:01:00-05:00; **evidence collected:** 2026-07-25T21:01:00-05:00; **local timezone:** America/Chicago; **system timestamps:** UTC; America/Chicago; **valid as of:** 2026-07-25; **review due:** event-based. The Kubecost windows ended at 2026-07-26T01:59:00Z, the same instant as 2026-07-25T20:59:00-05:00. |
| **Where** | **Environment:** homelab; **cluster:** kalaxy3; **execution host:** donbs-imac; **controller:** not-applicable; **nodes:** arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; **addresses:** arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62; **namespaces:** headlamp; kube-system; kubecost; longhorn-system; metallb-system; minio; observability; storage; **endpoints:** kubecost-frontend=http://192.168.2.26:9090; kubecost-allocation-api=http://192.168.2.26:9090/model/allocation; **record:** markdown/benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md. |
| **Why** | Centralized logging will add DaemonSets, collectors, storage, network traffic, and backend workloads. A before-state is required to quantify incremental CPU, RAM, persistent-volume, network, idle, and shared cost without delaying the project for a 30-day control period. |
| **How** | Fixed UTC windows were queried through the Kubecost Allocation API for raw and fully burdened namespace allocations; cluster state was captured with `kubectl`, Helm state with `helm`, resource usage with `kubectl top`, and live Kubecost values with `helm get values`. Every retained source artifact was hashed, the source checksum file was verified, and this evidence-only package binds the record to repository commit `4388c30c5f3f4ceafd233377582cded704889b8f`. |

### Five-W completeness gate

- [x] Who is complete and agrees with canonical metadata.
- [x] What is complete and states the baseline-only boundary.
- [x] When is complete and includes local and system timestamp timezones.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes the decision to avoid a 30-day blocking wait.
- [x] How is reproducible and verifiable from retained artifacts.

## Scope and boundaries

### In scope

- Kubecost raw allocation for fixed 24-hour and 72-hour windows.
- Kubecost fully burdened allocation using shared namespaces, shared idle, weighted splitting, and `$28.41/month` shared overhead.
- Seven-node readiness, addresses, K3s version, and point-in-time resource usage.
- Existing pod, workload, storage, and Helm-release inventory before centralized logging.
- Live Kubecost pricing and persistence values at capture time.
- Artifact integrity through both the original internal checksum file and the SAGE package manifest.
- Derived daily averages and fixed-share proration checks.

### Out of scope

- Installation, configuration, or validation of Fluent Bit, OpenTelemetry Collector, Loki, OpenSearch, or another centralized log pipeline.
- Application-level log completeness, parsing quality, retention, querying, alerting, or recovery.
- Thirty-day trend stability or accounting-certified cost.
- Independent router, ISP, utility-bill, or hardware power-meter reconciliation.
- A causal claim that a future cost change was produced by logging; that requires a post-change matched comparison.

### Nonclaims

This record does **not** claim:

- that centralized logging is installed or operational;
- that the 24-hour and 72-hour windows are independent samples;
- that the cluster was unchanged throughout both historical windows;
- that the observed values are long-term monthly averages;
- that `networkCost: 0` means no traffic occurred;
- that a later unmatched rolling window is a valid comparison;
- that the absence of logging-named Helm releases alone rules out every possible manually installed logger.

## Final accepted state

```text
Evidence state: validated pre-centralized-logging control snapshot
Capture directory: markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging
Repository state represented: 4388c30c5f3f4ceafd233377582cded704889b8f
24-hour window: 2026-07-25T01:59:00Z to 2026-07-26T01:59:00Z
72-hour window: 2026-07-23T01:59:00Z to 2026-07-26T01:59:00Z
24-hour raw total: $59.50089
24-hour fully burdened total: $60.43491
72-hour raw total: $182.74493
72-hour fully burdened total: $185.54701
72-hour fully burdened daily average: $61.84900
Logging implementation proof: not provided by this record
```

| Item | Accepted result |
|---|---|
| Source integrity | Every original baseline file passed the retained SHA-256 checksum verification. |
| Kubecost API | All four retained allocation responses report HTTP-style `code: 200`. |
| Nodes | Seven nodes were `Ready` at capture. |
| Kubecost configuration | Shared overhead was `$28.41/month`; network unit prices were zero; Longhorn-backed Kubecost storage was configured. |
| Logging baseline boundary | No workload or Helm-release entry containing Loki, Fluent, OTel, or OpenTelemetry appeared in the retained snapshots. |
| Comparison readiness | The baseline is suitable as a preserved pre-change reference when the post-change record uses the same parameters and states the timing limitations. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The pre-logging evidence directory is internally checksum-verifiable. | critical | `EV-001` | supported | high |
| `CLM-002` | The retained 24-hour raw Kubecost total is `$59.50089`. | high | `EV-002`, `EV-006` | supported | high |
| `CLM-003` | The retained 24-hour fully burdened total is `$60.43491`. | high | `EV-003`, `EV-006` | supported | high |
| `CLM-004` | The retained 72-hour raw total is `$182.74493`. | high | `EV-004`, `EV-006` | supported | high |
| `CLM-005` | The retained 72-hour fully burdened total is `$185.54701`. | high | `EV-005`, `EV-006` | supported | high |
| `CLM-006` | All seven Kalaxy3 nodes were Ready at capture. | critical | `EV-007` | supported | high |
| `CLM-007` | The snapshot contains no Loki, Fluent Bit, OTel, or OpenTelemetry workload or Helm-release name. | critical | `EV-008` | supported within captured inventories | high |
| `CLM-008` | The fully burdened total exceeds the raw total by the expected prorated `$28.41/month` fixed share cost. | high | `EV-002`, `EV-003`, `EV-004`, `EV-005`, `EV-011` | supported | high |
| `CLM-009` | The latest 24-hour fully burdened total is within approximately 2.29% of the 72-hour daily average. | normal | `EV-011` | supported | high |
| `CLM-010` | This record is a baseline only and does not prove centralized logging functionality. | critical | `EV-008`, `EV-012` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The next planned capability is centralized logging. Collectors on every node,
a telemetry gateway, a log backend, object or persistent storage, and Grafana
integration will alter the very costs Kubecost is intended to measure. Without
a preserved control snapshot, later resource and cost changes could not be
compared against a documented before-state.

### Decision

Capture and publish both 24-hour and 72-hour pre-change windows immediately,
then proceed with logging implementation instead of making a 30-day baseline a
project gate. Treat longer windows as later trend evidence, not prerequisites.

### Decision drivers

- Avoid blocking engineering work for 30 days.
- Preserve a recent control window before logging workloads exist.
- Retain both short-window sensitivity and a modest multi-day average.
- Use fixed UTC timestamps rather than repeated moving-window comparisons.
- Preserve raw and fully burdened views because they answer different questions.
- Keep baseline evidence separate from implementation evidence.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Wait 30 days before proceeding | Stronger long-term trend | Unnecessary project delay and still vulnerable to unrelated cluster changes | rejected |
| Capture only a 24-hour window | Fast and recent | More sensitive to daily workload variation | rejected as sole evidence |
| Capture only a 72-hour window | Smoother average | Blurs recent changes and overlaps multiple cluster states | rejected as sole evidence |
| Capture 24-hour and 72-hour windows now | Immediate progress plus a short multi-day reference | Windows overlap and are not independent | accepted |
| Deploy logging without a baseline | Fastest | No defensible incremental-cost comparison | rejected |

### Tradeoffs and consequences

- Work can proceed immediately, but comparison confidence is below a stable 30-day study.
- The 72-hour daily average reduces some short-term noise, but recent Kubecost changes occurred within the historical windows.
- The baseline is durable and reproducible as evidence, but the exact historical API responses cannot be recaptured if lost.
- Future comparison must separate logging effects from unrelated workload changes.

## Architecture or change description

```text
Current measured state
  Kubernetes workloads without centralized logging
        |
        +--> Kubecost Allocation API
        |      +--> raw 24h and 72h allocations
        |      +--> fully burdened 24h and 72h allocations
        |
        +--> kubectl snapshots
        |      +--> nodes and point-in-time usage
        |      +--> pods and workload controllers
        |      +--> PVC and PV state
        |
        +--> Helm snapshots
               +--> release inventory
               +--> live Kubecost values

Future state, not implemented by this record
  Fluent Bit -> OpenTelemetry gateway -> log backend -> Grafana
        |
        +--> matched post-change Kubecost comparison
```

### Before

No durable, checksum-bound pre-centralized-logging benchmark package existed.

### After

The repository can preserve exact pre-change JSON and text artifacts plus a
SAGE record that defines how they may and may not be used. Cluster runtime state
was not changed by the capture.

## Source of truth and implementation lineage

### Repository files

```text
markdown/benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md
markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/
```

### Implementation commit

```text
4388c30c5f3f4ceafd233377582cded704889b8f
```

This is an evidence-only publication. The commit is the exact repository state
recorded in `baseline-metadata.txt`; it is not a claim that this record changed
cluster implementation code.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| K3s | `v1.36.2+k3s1` | `nodes.txt` |
| Kubecost | `3.2.1` | `helm-releases.txt` |
| IBM FinOps Agent | `v1.0.20` | `kubecost-live-values.yaml` |
| kube-prometheus-stack | `87.19.0` | `helm-releases.txt` |
| Longhorn | `v1.12.0` | `helm-releases.txt` |
| MetalLB | `v0.16.1` | `helm-releases.txt` |
| Traefik | `v3.7.1` | `helm-releases.txt` |
| Headlamp | `0.43.0` | `helm-releases.txt` |
| `kubectl`, Helm, `jq`, `curl`, `shasum` | version-not-captured | command execution evidence |

### Configuration excerpt

```yaml
kubecostProductConfigs:
  sharedNamespaces: kube-system,kubecost,longhorn-system,metallb-system,observability,storage
  sharedOverhead: "28.41"
networkCosts:
  enabled: "true"
finopsagent:
  agent:
    kubecost:
      customPrices:
        internetNetworkEgress: "0.00000000"
        regionNetworkEgress: "0.00000000"
        zoneNetworkEgress: "0.00000000"
```

## Prerequisites and assumptions

### Proven prerequisites

- `EV-001` proves the retained source directory is internally checksum-consistent.
- `EV-002` through `EV-005` prove the Allocation API returned retained result structures for both windows and views.
- `EV-007` proves seven Ready nodes were present at capture.
- `EV-008` proves cluster, workload, and Helm inventories were captured.
- `EV-010` proves the live Kubecost values used for the benchmark were retained.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Logging was not deployed under an unrelated name or unmanaged object omitted from the captured resource kinds. | The before-state could already include some logging cost. | Search all workload kinds, ConfigMaps, Services, and images before deployment. |
| `ASM-002` | `$28.41/month` remains the appropriate shared-overhead input for the post-change comparison. | A pricing change could be mistaken for logging cost. | Freeze or explicitly normalize pricing inputs between compared queries. |
| `ASM-003` | Unrelated workloads remain reasonably comparable between windows. | Workload drift could dominate the logging delta. | Capture workload inventories and use namespace/workload-level comparisons. |
| `ASM-004` | Average-month proration uses 730 hours. | Small difference from calendar-month accounting. | Keep the same proration convention in post-change evidence. |

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
EVIDENCE_ID="SAGE-K3-OBSERVABILITY-20260725-001"
BASELINE_DIR="markdown/evidence-artifacts/${EVIDENCE_ID}/pre-logging"
mkdir -p "$BASELINE_DIR"
```

### Execution

The capture defined one common end instant and explicit 24-hour and 72-hour starts,
retrieved live shared-cost inputs, queried raw and fully burdened allocations,
and captured Kubernetes, Helm, storage, and resource-usage state.

```bash
END_UTC="$(date -u '+%Y-%m-%dT%H:%M:00Z')"
START_24H="$(date -u -v-24H '+%Y-%m-%dT%H:%M:00Z')"
START_72H="$(date -u -v-72H '+%Y-%m-%dT%H:%M:00Z')"
```

Raw and fully burdened requests used:

```text
aggregate=namespace
accumulate=true
shareIdle=true                 fully burdened only
shareNamespaces=<live value>  fully burdened only
shareCost=28.41               fully burdened only
shareSplit=weighted           fully burdened only
```

Cluster snapshots used `kubectl get`, `kubectl top`, `helm list -A`, and
`helm get values kubecost -n kubecost -o yaml`.

### Evidence integrity

```bash
find "$BASELINE_DIR" \
  -type f \
  ! -name checksums.sha256 \
  -print0 |
sort -z |
xargs -0 shasum -a 256 \
  > "${BASELINE_DIR}/checksums.sha256"

shasum -a 256 -c \
  "${BASELINE_DIR}/checksums.sha256"
```

### Expected change

- No Kubernetes or Helm implementation resource changes.
- One new untracked evidence directory before SAGE publication.
- Four successful Allocation API artifacts plus supporting snapshots.
- Every source artifact verifies against `checksums.sha256`.

### Observed change

- The baseline directory contained the expected JSON, YAML, and text artifacts.
- All entries listed in the retained checksum file returned `OK`.
- Repository status showed only the new evidence-artifact directory as untracked before publication.

## Evidence items

### `EV-001` — Original artifact checksum verification

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-001` |
| Command or source | `shasum -a 256 -c markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/checksums.sha256` |
| Execution source and target | `donbs-imac`; retained pre-logging artifact directory |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago |
| Expected result | Every listed file returns `OK` |
| Observed result | All 18 original files returned `OK` |
| Status | pass |
| Confidence | high |
| Sensitive material | none observed |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/checksums.sha256` |

**Interpretation**

The original capture directory was intact when packaged. The SAGE package adds
a second manifest-level hash for every payload file.

### `EV-002` — Raw 24-hour allocation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-002`, `CLM-008` |
| Command or source | Kubecost Allocation API fixed 24-hour raw query |
| Execution source and target | `donbs-imac`; `kubecost-allocation-api` |
| Collection time and timezone | 2026-07-25T20:59:49-05:00; API window in UTC |
| Expected result | Response code 200 and namespace allocation data |
| Observed result | `code: 200`; total `$59.50089` |
| Status | pass |
| Confidence | high |
| Sensitive material | internal namespace and cost data |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-24h.json` |

### `EV-003` — Fully burdened 24-hour allocation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-003`, `CLM-008` |
| Command or source | Kubecost Allocation API fixed 24-hour fully burdened query |
| Execution source and target | `donbs-imac`; `kubecost-allocation-api` |
| Collection time and timezone | 2026-07-25T20:59:49-05:00; API window in UTC |
| Expected result | Response code 200 with shared idle, namespaces, fixed share cost, and weighted split |
| Observed result | `code: 200`; total `$60.43491`; shared cost `$32.62710` |
| Status | pass |
| Confidence | high |
| Sensitive material | internal namespace and cost data |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-24h.json` |

### `EV-004` — Raw 72-hour allocation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-004`, `CLM-008` |
| Command or source | Kubecost Allocation API fixed 72-hour raw query |
| Execution source and target | `donbs-imac`; `kubecost-allocation-api` |
| Collection time and timezone | 2026-07-25T20:59:49-05:00; API window in UTC |
| Expected result | Response code 200 and namespace allocation data |
| Observed result | `code: 200`; total `$182.74493`; network cost `$0.00001` |
| Status | pass |
| Confidence | high |
| Sensitive material | internal namespace and cost data |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-72h.json` |

### `EV-005` — Fully burdened 72-hour allocation

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-005`, `CLM-008` |
| Command or source | Kubecost Allocation API fixed 72-hour fully burdened query |
| Execution source and target | `donbs-imac`; `kubecost-allocation-api` |
| Collection time and timezone | 2026-07-25T20:59:49-05:00; API window in UTC |
| Expected result | Response code 200 with shared-cost allocation |
| Observed result | `code: 200`; total `$185.54701`; shared cost `$100.37668` |
| Status | pass |
| Confidence | high |
| Sensitive material | internal namespace and cost data |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-72h.json` |

### `EV-006` — Generated summary files

| Field | Value |
|---|---|
| Classification | generated-evidence |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004`, `CLM-005` |
| Command or source | `jq` aggregation of retained Allocation API JSON |
| Execution source and target | `donbs-imac`; four allocation artifacts |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago |
| Expected result | CPU, RAM, PV, network, shared, and total fields for each view and window |
| Observed result | Four summary JSON files retained and checksummed |
| Status | pass |
| Confidence | high |
| Sensitive material | internal cost data |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-*-summary.json` |

### `EV-007` — Seven-node readiness and point-in-time usage

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-006` |
| Command or source | `kubectl get nodes -o wide`; `kubectl top nodes` |
| Execution source and target | `donbs-imac`; `kalaxy3` |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago |
| Expected result | Seven Ready nodes and resource-usage rows |
| Observed result | Seven Ready nodes; all seven had CPU and memory observations |
| Status | pass |
| Confidence | high |
| Sensitive material | internal node names and IP addresses |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/nodes.txt`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/node-usage.txt` |

### `EV-008` — Workload and Helm inventory before logging

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | `CLM-007`, `CLM-010` |
| Command or source | `kubectl get pods`; `kubectl get deploy,statefulset,daemonset`; `helm list -A` |
| Execution source and target | `donbs-imac`; `kalaxy3` |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago and UTC release timestamps |
| Expected result | Complete retained snapshot of named workload controllers, pods, and Helm releases |
| Observed result | Snapshots retained; no Loki, Fluent, OTel, or OpenTelemetry name appears |
| Status | pass within captured resource kinds |
| Confidence | high |
| Sensitive material | internal topology and workload metadata |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/pods.txt`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/workloads.txt`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/helm-releases.txt` |

### `EV-009` — Storage and pod-usage snapshot

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | baseline context for `CLM-010` |
| Command or source | `kubectl get pvc,pv -A -o wide`; `kubectl top pods -A` |
| Execution source and target | `donbs-imac`; `kalaxy3` |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago |
| Expected result | Durable storage mapping and point-in-time pod usage |
| Observed result | Kubecost, MinIO, and observability claims plus pod CPU and memory rows retained |
| Status | pass |
| Confidence | high |
| Sensitive material | internal storage and workload metadata |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/storage.txt`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/pod-usage.txt` |

### `EV-010` — Live Kubecost values

| Field | Value |
|---|---|
| Classification | direct-observation |
| Supports or contradicts | configuration context for `CLM-008` |
| Command or source | `helm get values kubecost -n kubecost -o yaml` |
| Execution source and target | `donbs-imac`; Kubecost Helm release |
| Collection time and timezone | 2026-07-25T21:00:00-05:00; America/Chicago |
| Expected result | Retained live custom prices, shared settings, storage, and network settings |
| Observed result | `$28.41` shared overhead; zero unit network prices; Longhorn persistence; network costs enabled |
| Status | pass |
| Confidence | high |
| Sensitive material | no credentials or secret values observed |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/kubecost-live-values.yaml` |

### `EV-011` — Derived stability and proration analysis

| Field | Value |
|---|---|
| Classification | derived-conclusion |
| Supports or contradicts | `CLM-008`, `CLM-009` |
| Command or source | deterministic arithmetic over `EV-002` through `EV-005` |
| Execution source and target | package generation; retained summary JSON |
| Collection time and timezone | 2026-07-25T21:15:14-05:00; America/Chicago |
| Expected result | Fixed share delta matches `$28.41 × hours / 730`; daily averages computed |
| Observed result | 24h delta `$0.93402` versus `$0.93402740`; 72h delta `$2.80208` versus `$2.80208219`; 24h fully burdened total is approximately `2.286%` below the 72h daily average |
| Status | pass |
| Confidence | high |
| Sensitive material | internal cost values |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/baseline-analysis.json` |

### `EV-012` — Baseline-only evidence boundary

| Field | Value |
|---|---|
| Classification | derived-conclusion |
| Supports or contradicts | `CLM-010` |
| Command or source | evidence-scope review of all retained artifacts |
| Execution source and target | SAGE record generation; baseline artifact set |
| Collection time and timezone | 2026-07-25T21:15:14-05:00; America/Chicago |
| Expected result | Planned logging work remains distinct from observed baseline state |
| Observed result | No logging deployment output, configuration, health test, log query, retention test, or recovery test exists in this record |
| Status | pass |
| Confidence | high |
| Sensitive material | none |
| Artifact | this evidence record |

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Preserve original artifact integrity | `EV-001` | Every internal checksum passes | All 18 original files returned `OK` | pass |
| `AC-002` | Capture a fixed 24-hour raw allocation | `EV-002` | Code 200 and total value | `$59.50089` | pass |
| `AC-003` | Capture a fixed 24-hour fully burdened allocation | `EV-003` | Code 200 and shared-cost result | `$60.43491` total | pass |
| `AC-004` | Capture a fixed 72-hour raw allocation | `EV-004` | Code 200 and total value | `$182.74493` | pass |
| `AC-005` | Capture a fixed 72-hour fully burdened allocation | `EV-005` | Code 200 and shared-cost result | `$185.54701` total | pass |
| `AC-006` | Preserve cluster context | `EV-007`, `EV-008`, `EV-009` | Nodes, workloads, storage, and usage retained | present | pass |
| `AC-007` | Preserve pricing context | `EV-010` | Live shared and unit-price values retained | present | pass |
| `AC-008` | Validate fixed share proration | `EV-011` | Observed and expected deltas agree within rounding | agreement within less than `$0.00001` | pass |
| `AC-009` | Prevent scope overclaim | `EV-012` | Record states that logging is not implemented | explicit | pass |
| `AC-010` | Bind to repository state | `EV-001`, baseline metadata | Commit equals `4388c30c5f3f4ceafd233377582cded704889b8f` | exact match | pass |

### Functional verification

```bash
shasum -a 256 -c \
  markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/checksums.sha256
```

Observed:

```text
Every listed original baseline artifact: OK
```

### Negative verification

```bash
grep -Ei 'loki|fluent|otel|opentelemetry' \
  markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/helm-releases.txt \
  markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/workloads.txt \
  markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/pods.txt
```

Observed:

```text
No matching line in the retained snapshots.
```

This negative check is bounded to the captured names and resource kinds.

## Idempotency and repeatability

### First accepted run

```text
Four allocation responses, four generated summaries, cluster snapshots, live
values, and a checksum inventory were created under the evidence ID directory.
```

### Steady-state rerun

```text
Not applicable as byte-identical idempotency: the queries are time-dependent and
a rerun at a later instant intentionally produces a different fixed window.
Artifact verification is repeatable: the retained checksums returned OK.
```

### Interpretation

The capture method is repeatable, but the measurements are intentionally
time-bound. Future evidence must preserve exact windows and parameters rather
than expect identical cost values. The artifact-integrity check is deterministic.

## Security, privacy, and evidence handling

### Security controls

- Evidence is classified `internal`.
- The package contains cluster addresses, workload names, storage mappings, and cost data but no authentication material.
- The publisher scans record and text artifacts for common private-key, bearer-token, GitHub-token, and password patterns.
- The original checksum file and package manifest provide two integrity layers.

### Sensitive material excluded

- No kubeconfig was captured.
- No Kubernetes Secret manifest or decoded Secret value was captured.
- No password, token, private key, provider account identifier, or billing account number was captured.
- The `$20/month` provider allocation is represented indirectly inside the current `$28.41` shared overhead; no provider invoice is present.

### Redactions and omissions

- No redaction was required in the supplied baseline files.
- Command output was retained as text rather than screenshots.

### Residual security risk

Internal IP addresses and infrastructure names reveal Kalaxy3 topology. Publish
only to the intended repository and documentation access boundary.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Allocation API unavailable | `curl --fail` exits nonzero or JSON missing `code: 200` | Missing cost window | Restore Kubecost service and rerun with a new documented window |
| Window variables differ between raw and fully burdened queries | Metadata or filenames disagree | Invalid comparison | Re-run all views from one captured end instant |
| Shared pricing changes | Live values differ from post-change record | Cost delta confounded | Normalize pricing or report pricing change separately |
| Artifact corruption | `shasum -c` fails | Evidence cannot be trusted | Restore from Git or original archive and reverify |
| Workload drift | Pod or workload inventories differ materially | Logging delta cannot be isolated | Compare namespaces and document unrelated changes |
| Missing metrics-server data | `kubectl top` contains errors | Point-in-time usage context incomplete | Restore metrics-server and capture a supplemental observation |

### Rollback

The capture changed no cluster resources. Repository rollback is evidence-only:

```bash
git revert <evidence-commit-sha>
```

Do not delete the record after it has been referenced; mark it superseded if a
replacement is accepted.

### Rebuild procedure

1. Confirm Kubecost is reachable and its live values are retained.
2. Define one UTC end instant and exact 24-hour and 72-hour starts.
3. Query raw and fully burdened namespace allocations with identical windows.
4. Capture nodes, pods, controllers, PVCs, PVs, Helm releases, and resource usage.
5. Write capture metadata including shared namespaces, overhead, and repository commit.
6. Generate summaries from the raw JSON.
7. Generate and verify the checksum inventory.
8. Generate and publish a new evidence record; do not overwrite this historical window.

### Data durability and backup impact

The record and artifacts become durable through Git history and the remote
repository. The capture does not modify workload data, PVCs, or backup policy.
The historical API responses cannot be reconstructed exactly if both local and
Git copies are lost.

## Operational considerations and observability

### Health signals

- Allocation API response code and parseable JSON.
- Seven Ready nodes.
- Complete `kubectl top` output or documented errors.
- Kubecost Helm release status `deployed`.
- Internal and package SHA-256 validation.
- Stable shared-overhead and custom-price inputs across compared windows.

### Routine verification

```bash
python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-pre-logging-kubecost-baseline-sage-package.zip
```

After publication:

```bash
python3 scripts/sage/sage-index.py check
shasum -a 256 -c \
  markdown/benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md.sha256
```

### Capacity, performance, and cost impact

- **Capacity:** Evidence capture added repository files only; no cluster workload.
- **Performance:** API and inventory reads created transient administrative load only.
- **Cost:** The fully burdened baseline is `$60.43491` for 24 hours and `$185.54701` for 72 hours.
- **Sustainability/power:** No new continuous service was introduced. Existing power assumptions remain inherited from the Kubecost calibration record.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | limitation | The 24-hour and 72-hour windows overlap. | They are complementary views, not independent samples. | Don Buddenbaum | every comparison |
| `GAP-002` | evidence-gap | The final network-cost DaemonSet was only about five hours old in the pod snapshot. | Historical windows do not represent a long steady state after all recent Kubecost changes. | Don Buddenbaum | interpret post-change delta |
| `GAP-003` | limitation | Kubecost main pods were about 21 hours old in the snapshot. | Some of the 72-hour allocation depends on retained historical metrics rather than one unchanged Kubecost runtime. | Don Buddenbaum | future baseline review |
| `GAP-004` | risk | Unrelated workloads may change before or after logging deployment. | Total cluster delta may not equal logging cost. | Don Buddenbaum | post-logging comparison |
| `GAP-005` | limitation | The snapshot checks names in selected workload kinds and Helm releases. | A differently named or unmanaged logging component could be missed. | Don Buddenbaum | pre-deployment inventory |
| `GAP-006` | evidence-gap | Administrative tool versions were not captured. | Exact command behavior may vary on future clients. | Don Buddenbaum | next capture |
| `GAP-007` | limitation | `networkCost` is zero or negligible because unit network prices are configured as zero. | Monetary network impact cannot be inferred from this field. | Don Buddenbaum | provider-pricing change |
| `GAP-008` | risk | The 72-hour raw result contains `$0.00001` network cost while fully burdened is zero. | Tiny adjustment or floating precision noise can be overinterpreted. | Don Buddenbaum | treat as negligible unless repeated |
| `GAP-009` | limitation | Point-in-time `kubectl top` is not a 24-hour or 72-hour utilization average. | It provides context, not a trend. | Don Buddenbaum | post-change capture |
| `GAP-010` | planned-work | Centralized logging Ansible code is not part of this record. | No logging functionality is validated. | Don Buddenbaum | next engineering task |

## Troubleshooting

### Package validation reports a checksum mismatch

**Meaning**

A payload file changed after the manifest was generated.

**Checks**

```bash
python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-pre-logging-kubecost-baseline-sage-package.zip
```

**Recovery**

Rebuild the package from the verified source directory. Do not edit files inside
the ZIP manually.

### Internal checksum validation fails

**Meaning**

The baseline directory no longer matches the original capture.

**Checks**

```bash
shasum -a 256 -c \
  markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/checksums.sha256
```

**Recovery**

Restore the artifact from the original transfer archive or Git and re-run the
check. If the original cannot be restored, mark the evidence invalid rather than
generating replacement hashes for changed historical data.

### Post-logging total differs unexpectedly

**Meaning**

The delta may include pricing, workload, storage, or time-window differences.

**Checks**

```text
Compare exact start/end timestamps.
Compare sharedNamespaces and sharedOverhead.
Compare custom CPU, RAM, storage, and network prices.
Compare workload, node, and PVC inventories.
Compare raw namespace allocations before fully burdened totals.
```

**Recovery**

Normalize query parameters and isolate logging namespaces and workloads. If the
windows are not comparable, capture a new control and state why this baseline
was not used.

## Freshness, revalidation, and supersession

### Revalidate when

- centralized logging is deployed;
- a post-logging cost window is captured;
- Kubecost chart, allocation semantics, pricing inputs, shared namespaces, or shared overhead changes;
- nodes, storage classes, namespaces, or major workloads change;
- artifact checksum verification fails;
- another record contradicts the baseline metadata or window values.

### Scheduled review

```text
Event-based: at centralized logging deployment and matched post-change capture.
```

### Supersession rule

A post-logging comparison record should normally `depend_on` and `related_to`
this baseline. It may `supersede` this record only if it becomes the accepted
authoritative before-and-after analysis while preserving this record and its
artifacts for lineage. If a new pre-change capture replaces this one before
deployment, mark this record `superseded` and link the replacement.

## Final completion checklist

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema 1.2 front matter follows canonical order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status is limited to validation of the baseline capture.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How are complete.
- [x] Scope, exclusions, and nonclaims are explicit.
- [x] Repository state commit is recorded.
- [x] Relationships and supersession rules are defined.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and artifact.
- [x] Derived conclusions reference direct evidence.
- [x] Artifact checksums are preserved.
- [x] Assumptions and planned work are marked.
- [x] Repeatability is explained without claiming byte-identical reruns.
- [x] The record does not claim centralized logging implementation.

### Safety and operations

- [x] Secrets and sensitive values are excluded.
- [x] Internal topology exposure is documented.
- [x] Rollback and rebuild are documented.
- [x] Health checks and troubleshooting are documented.
- [x] Known limitations and evidence gaps have owners and triggers.
- [x] Revalidation and supersession rules are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | validated baseline capture | 2026-07-25 | Approved for use as a pre-change comparison with stated limitations. |
| Reviewer | pending | pending | pending | Independent review is not required for `validated` status but remains pending. |

## Git review and publication

Validate and publish only through the repository-owned SAGE process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-pre-logging-kubecost-baseline-sage-package.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-pre-logging-kubecost-baseline-sage-package.zip \
  --push
```

The evidence-only publisher binds the record to repository commit `4388c30c5f3f4ceafd233377582cded704889b8f`,
creates the final record checksum and publication manifest, reconciles legacy
and current evidence indexes, commits the evidence, and pushes without an ad
hoc Git sequence.

## Appendices

### Artifact inventory

| Artifact | SHA-256 before publication | Sensitive data | Retention |
|---|---|---|---|
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-24h-summary.json` | `95aef469ced007d7be576220643fe6a201212542096a8f3bd22d474fb734f9c5` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-24h.json` | `de279e26c658de06423983dc01e906aa96f3d4fbc30770a87cd03578cbecccdd` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-72h-summary.json` | `d6607743cbf27c916579e7f5745a39e12ff7dd035741077f62ca7534743ade09` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-fully-burdened-72h.json` | `cd2bbc5f35771af6d4298ee45ec0477206dfcf4f592a0a4ec756f9ca3c74f426` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-24h-summary.json` | `f52b43ca3fc2e5f49e73225738284b9cba6e89086e80d94eb63ee3c8d54bee8f` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-24h.json` | `ddffbff515f1309e89a5eeac6b909db0e0eb73e4b84d6e35890d3875966006ea` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-72h-summary.json` | `8f18ae99fbd5fd82a6807afa08dc233954eb5167971ff6c0e140cbe1f70a198c` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/allocation-raw-72h.json` | `01dcfef1ea8cc06c30eaa51215dd463d93042158e5ae9314e6932fc0e6aa5ca5` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/baseline-analysis.json` | `90812132fcd86f43ea969b2ab894a5a3e1357d9f28f5774b67c4e7dbea999120` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/baseline-metadata.txt` | `720ee326e01e50ef8cf3984f684a390068724cde8facf140781ada460a22c45e` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/checksums.sha256` | `ccf4ce31ce179536165576111c8adb81de5252c9bed96e4db63db652572efa09` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/helm-releases.txt` | `87d7df50ab7fb47b68bcb7fed27e750cc26c686532fe13710f94280bdc8f11e0` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/kubecost-live-values.yaml` | `6228ce79a33fd0ecca8a8e3535ef34aec1ba05337eeab0a8e7f2d153dd316858` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/node-usage.txt` | `170b01f03523c5cab87e7dc2242041c6413098d65841d0749e8d9598e32f42f0` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/nodes.txt` | `6e114eaea4d624902433a9d987790d7aa8c4032bf474f4b7524ce3374f563834` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/pod-usage.txt` | `fd63fe712efc7794a038f6072df330570d5c1ae10658a22efa85e822efe088d4` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/pods.txt` | `0a9d3e2578ffc87eea37b90d2f026d8ff61416a1195f952f250e274514e33631` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/source-input-archive.sha256` | `16a3320c48fa0ca444c57f160ded8bcb2dba7ad922d68985364008820db911dd` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/storage.txt` | `60ef9b6c7f9de8d51c2155acc21c106bd32a6f1dbbcc86c0d6bbc523803419de` | no secrets observed; internal operational metadata | repository history |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260725-001/pre-logging/workloads.txt` | `2503cd90ebeb610ece003611f3a7e732060403c070fc026a6dfbc385db0d29cb` | no secrets observed; internal operational metadata | repository history |

### Baseline comparison summary

| Measurement | 24 hours | 72 hours | 72-hour daily average |
|---|---:|---:|---:|
| Raw total | `$59.50089` | `$182.74493` | `$60.91498` |
| Fully burdened total | `$60.43491` | `$185.54701` | `$61.84900` |
| Shared cost | `$32.62710` | `$100.37668` | `$33.45889` |
| Network cost | `$0.00000` | `$0.00000` fully burdened | approximately `$0.00000` |

The 24-hour fully burdened result is approximately `$1.41409`, or `2.286%`,
below the 72-hour daily average. That modest difference supports proceeding,
but it does not eliminate the timing and workload-drift limitations.

### Required post-logging comparison plan

The later record should:

1. capture exact fixed post-change windows;
2. use the same aggregation, accumulation, idle-sharing, shared namespace, fixed share cost, and weighted split parameters;
3. retain raw and fully burdened JSON;
4. retain current pricing and shared-overhead values;
5. capture nodes, pods, workloads, PVCs, PVs, Helm releases, and resource usage;
6. isolate Fluent Bit, OpenTelemetry, Loki, and Grafana-related namespaces and workloads;
7. report unrelated cluster changes;
8. calculate absolute and percentage deltas;
9. distinguish implementation health from cost impact;
10. reference this evidence ID and preserve this baseline even if superseded.

### Next engineering task

Planned, not implemented by this record:

```text
Build centralized logging as disabled-by-default Ansible code, including
Fluent Bit collection, an OpenTelemetry Collector gateway, a log backend,
Grafana integration, resource requests, retention, rollback, and acceptance tests.
```
