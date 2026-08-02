---
evidence_id: SAGE-K3-OBSERVABILITY-20260802-001
schema_version: "1.2"
title: Validated Grafana operations dashboard, telemetry, and alerting
nav_title: Grafana operations dashboard and alerting
nav_section: operations
nav_order: 260
summary: Validates repository-owned Grafana telemetry, a 20-panel operations dashboard, two actionable Prometheus alerts, their live acceptance, failure recovery, and SAGE evidence capture.
primary_subject: Grafana operations observability
project: Kalaxy3
record_type: operations
status: validated
classification: internal
work_session: Grafana operations dashboard, telemetry, alerting, and SAGE closeout
work_started_at: 2026-08-02T00:49:20-05:00
work_completed_at: 2026-08-02T03:43:23-05:00
evidence_collected_at: 2026-08-02T03:43:23-05:00
created_at: 2026-08-02T03:47:00-05:00
updated_at: 2026-08-02T11:08:09-05:00
valid_as_of: 2026-08-02
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Don Buddenbaum
author: Don Buddenbaum
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
  - not-applicable
namespaces:
  - observability
  - kubecost
  - longhorn-system
endpoints:
  - grafana-dashboard=/d/kalaxy3-operations/kalaxy3-operations
  - prometheus-rule=observability/kalaxy3-grafana-operations-alerts
  - prometheus-service=observability/kube-prometheus-stack-prometheus
components:
  - grafana=version-not-captured
  - kube-prometheus-stack=87.19.0
  - fluent-bit-collector=1.0.9
  - longhorn=1.12.0
  - kubecost=version-not-captured
  - sage-evidence-orchestrator=6250100ebf015e5243854a32d2a1741d73ed4484
repository: donb4iu/Kalaxy3
branch: feature/grafana-operations-dashboard
implementation_commit: 6250100ebf015e5243854a32d2a1741d73ed4484
record_path: markdown/operations/kalaxy3-grafana-operations-dashboard-alerting-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001
confidence: high
tags:
  - sage
  - observability
  - grafana
  - prometheus
  - alerting
  - longhorn
  - kubecost
relationships:
  verifies:
    - Grafana operations telemetry, dashboard, and alert evaluation
  depends_on:
    - SAGE-K3-OBS-20260728-003
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - SAGE-K3-OBSERVABILITY-20260725-001
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-evidence-orchestrator.py
    - scripts/sage/sage-publish.py
  implemented_by:
    - fecb97540127ac3abee4100ef7f8dcf74286d769
    - 4dc80e59ea2c0829a809abe60c3bdea61f56613a
    - fa5a752e1bf25c249b09cd0579399b3924b69fc5
    - ab36c484e32c28936f282287c707b0e4087cbaba
    - 55916a36afdee3fd8187f2269995f44e7ba532c2
    - 6250100ebf015e5243854a32d2a1741d73ed4484
  revalidated_by:
    - none
---

# Validated Grafana operations dashboard, telemetry, and alerting

## Executive summary

Kalaxy3 now has repository-owned telemetry coverage for Longhorn and Kubecost, a provisioned 20-panel Grafana operations dashboard, and two Prometheus alert rules that were loaded with healthy inactive state. The implementation is validated at commit `6250100ebf015e5243854a32d2a1741d73ed4484` and preserves the complete recovery history. Pull-request closeout remains conditional on cleaning stale staged or pending dashboard wording and deciding whether to add alert-state panels and visual browser acceptance.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBSERVABILITY-20260802-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Validated Grafana operations dashboard, telemetry, and alerting |
| **Navigation title** | Grafana operations dashboard and alerting |
| **Navigation section** | operations |
| **Navigation order** | 260 |
| **Summary** | Validates repository-owned Grafana telemetry, a 20-panel operations dashboard, two actionable Prometheus alerts, their live acceptance, failure recovery, and SAGE evidence capture. |
| **Primary subject** | Grafana operations observability |
| **Record type** | operations |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Grafana operations dashboard, telemetry, alerting, and SAGE closeout |
| **Started** | 2026-08-02T00:49:20-05:00 |
| **Completed** | 2026-08-02T03:43:23-05:00 |
| **Evidence collected** | 2026-08-02T03:43:23-05:00 |
| **Record created** | 2026-08-02T03:47:00-05:00 |
| **Record updated** | 2026-08-02T11:08:09-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-08-02 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-grafana-operations-dashboard-alerting-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/grafana-operations-dashboard |
| **Implementation commit** | 6250100ebf015e5243854a32d2a1741d73ed4484 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | not-applicable |
| **Namespaces** | observability; kubecost; longhorn-system |
| **Endpoints** | grafana-dashboard=/d/kalaxy3-operations/kalaxy3-operations; prometheus-rule=observability/kalaxy3-grafana-operations-alerts; prometheus-service=observability/kube-prometheus-stack-prometheus |
| **Components and versions** | grafana=version-not-captured; kube-prometheus-stack=87.19.0; fluent-bit-collector=1.0.9; longhorn=1.12.0; kubecost=version-not-captured; sage-evidence-orchestrator=6250100ebf015e5243854a32d2a1741d73ed4484 |
| **Owner** | Don Buddenbaum |
| **Author** | Don Buddenbaum |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author Don Buddenbaum, operator Don Buddenbaum, owner Don Buddenbaum, and reviewer pending executed and documented the work. |
| **What** | Repository-owned ServiceMonitors, the Grafana operations dashboard, Prometheus alert rules, live acceptance, failure recovery, and canonical SAGE evidence capture were completed. |
| **When** | Completed 2026-08-02T03:43:23-05:00; evidence collected 2026-08-02T03:43:23-05:00; local timezone America/Chicago; system timestamps America/Chicago; UTC; valid as of 2026-08-02; review due event-based. |
| **Where** | Environment homelab; cluster kalaxy3; execution host donbs-imac; controller host donbs-imac; nodes arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; namespaces observability; kubecost; longhorn-system; endpoints grafana-dashboard=/d/kalaxy3-operations/kalaxy3-operations; prometheus-rule=observability/kalaxy3-grafana-operations-alerts; prometheus-service=observability/kube-prometheus-stack-prometheus; record markdown/operations/kalaxy3-grafana-operations-dashboard-alerting-evidence.md. |
| **Why** | Operators needed a single repository-governed view of cluster health, Longhorn storage, Kubecost signals, logs, and actionable alert conditions without depending on ad hoc manual configuration. |
| **How** | The branch staged gated definitions, validated rendered resources, used server-side dry runs and repository guardrails, activated through the observability phase, verified live Prometheus and Grafana state, corrected failed paths, and captured the evidence through the canonical SAGE orchestrator. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Repository-owned ServiceMonitors for two Kubecost services and Longhorn manager metrics.
- A provisioned Grafana dashboard with 20 data panels covering cluster, node, Fluent Bit, logs, Longhorn, and Kubecost signals.
- Two warning-level Prometheus alert rules for Fluent Bit coverage and Longhorn aggregate storage utilization.
- Staged deployment gates, live activation, live rule evaluation, guardrail execution, failure recovery, and SAGE evidence capture.
- The SAGE authority-directory capture repair required to preserve this evidence package.

### Out of scope

- Alertmanager notification routing, receiver delivery, paging escalation, or forced firing tests.
- Human visual review screenshots or browser interaction evidence.
- Dashboard semantic cleanup after activation.
- A claim that SAGE evidence use quantitatively reduced rework or elapsed time.
- Pull-request merge and branch deletion.

### Nonclaims

- An inactive rule proves current threshold conditions are false; it does not prove a future receiver will deliver a notification.
- Live query results prove the captured acceptance window only, not indefinite service availability.
- The dashboard is operationally live, but not all displayed staging language is semantically current.

## Final accepted state

The validated branch at `6250100ebf015e5243854a32d2a1741d73ed4484` contains three Grafana operations ServiceMonitor definitions, a 20-panel dashboard ConfigMap, and one PrometheusRule containing `FluentBitCoverageDegraded` and `LonghornStorageUtilizationHigh`. The three ServiceMonitor objects and dashboard ConfigMap were persisted in `observability`; Prometheus reported two Kubecost and two Longhorn targets up. Both alert rules loaded with `health=ok`, `state=inactive`, and zero active expression results. Repository and cluster guardrails passed. The final evidence-input bundle captured 14 source inputs, 132 expanded authority files, seven SAGE contexts, and 150 members.

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Three repository-owned ServiceMonitors provide Longhorn and Kubecost scrape coverage and were accepted live. | critical | `EV-001`, `EV-002`, `EV-004` | supported | high |
| `CLM-002` | The Grafana operations dashboard was provisioned with 20 data panels and seven Longhorn or Kubecost queries returned results during acceptance. | critical | `EV-003`, `EV-004` | supported | high |
| `CLM-003` | Two Prometheus alert rules were persisted, loaded healthy, and inactive at acceptance. | critical | `EV-005`, `EV-006` | supported | high |
| `CLM-004` | Failed paths were preserved separately and corrective regressions were added before the accepted state. | high | `EV-004`, `EV-006`, `EV-007`, `EV-008` | supported | high |
| `CLM-005` | The canonical SAGE input bundle captured 14 evidence inputs and 132 tracked authority files without repository or Kubernetes mutation. | critical | `EV-008`, `EV-009` | supported | high |
| `CLM-006` | Functional observability is validated, while dashboard semantic cleanup, alert-state panels, notification delivery, and visual acceptance remain explicit gaps. | high | `EV-003`, `EV-004`, `EV-006`, `EV-009` | supported with limitations | high |

## Problem and decision rationale

### Problem or opportunity

Prometheus, Loki, Longhorn, Kubecost, and Fluent Bit exposed useful signals, but the operational view and alert conditions were not maintained as one repository-owned, validated capability. Ad hoc Grafana editing or direct cluster mutation would have reduced reproducibility and weakened rebuild evidence.

### Decision

Implement telemetry discovery, ServiceMonitors, the dashboard ConfigMap, and PrometheusRule as gated repository artifacts under the observability phase. Validate source structure, rendered YAML, live data contracts, Kubernetes admission, Prometheus target health, dashboard query results, and rule evaluation before recording evidence.

### Decision drivers

- Git-managed rebuildability and review.
- Reuse of existing Prometheus and Loki infrastructure.
- Fail-closed deployment gates.
- Exact source and artifact hashes.
- Live acceptance instead of render-only claims.
- Preservation of failed attempts as engineering experience.

### Alternatives considered

- Manual Grafana UI configuration was rejected because it would not be reproducible.
- Port-forward-only operational inspection was rejected as the primary workflow because it is clumsy and not a persistent operations surface.
- Alerting without live rule evaluation was rejected because successful YAML admission alone would not prove Prometheus loaded the rules.
- Rewriting authority maps to remove directory references was rejected because the discovery contract intentionally supports both file and directory authorities.

### Tradeoffs and consequences

The repository path is more deliberate and produced several fail-closed interruptions, but each interruption exposed a contract defect before evidence publication. The dashboard remains functionally live while semantic labels and planned alert-state panels require a separate cleanup decision.

## Architecture or change description

### Before

Longhorn and Kubecost endpoint metrics existed, but Prometheus did not have the repository-owned scrape coverage needed by the dashboard. The Grafana dashboard and alert rules were not provisioned as accepted cluster resources.

### After

- Three ServiceMonitors in `observability` select targets in `kubecost` and `longhorn-system`.
- Grafana provisions dashboard UID `kalaxy3-operations` from a ConfigMap.
- Twenty data panels use Prometheus or Loki data sources.
- One PrometheusRule in `observability` defines two warning alerts.
- The observability phase and deployment gates control activation.
- SAGE capture expands directory authorities into deterministic tracked files.

## Source of truth and implementation lineage

### Repository files

Primary implementation paths include:

- `infrastructure/k3s-homelab/playbooks/tasks/observability.yml`
- `infrastructure/k3s-homelab/inventory/group_vars/all/main.yml`
- `infrastructure/k3s-homelab/playbooks/templates/grafana-operations-servicemonitors.yml.j2`
- `infrastructure/k3s-homelab/playbooks/files/grafana-operations-dashboard-configmap.yml`
- `infrastructure/k3s-homelab/playbooks/files/grafana-operations-dashboard-contract.json`
- `infrastructure/k3s-homelab/playbooks/files/grafana-operations-alerts-prometheusrule.yml`
- `infrastructure/k3s-homelab/scripts/validate-grafana-operations-yaml.py`
- `infrastructure/k3s-homelab/scripts/validate-grafana-operations-dashboard.py`
- `infrastructure/k3s-homelab/scripts/validate-grafana-operations-alerts.py`
- `scripts/sage/sage-evidence-orchestrator.py`

### Implementation commit

The requested five implementation checkpoints are:

1. `fecb97540127ac3abee4100ef7f8dcf74286d769` — stage telemetry scrape coverage.
2. `4dc80e59ea2c0829a809abe60c3bdea61f56613a` — stage dashboard definition.
3. `fa5a752e1bf25c249b09cd0579399b3924b69fc5` — activate the dashboard.
4. `ab36c484e32c28936f282287c707b0e4087cbaba` — stage alert rules.
5. `55916a36afdee3fd8187f2269995f44e7ba532c2` — activate alert rules.

The final branch boundary also includes `6250100ebf015e5243854a32d2a1741d73ed4484`, which repairs SAGE authority-directory capture.

### Versioned dependencies

- `kube-prometheus-stack=87.19.0`
- `fluent-bit-collector=1.0.9`
- `longhorn=1.12.0`
- `grafana=version-not-captured`
- `kubecost=version-not-captured`
- `sage-evidence-orchestrator=6250100ebf015e5243854a32d2a1741d73ed4484`

### Controller portability and repository authority

The workflow used the repository virtual environment, kubeconfig, context, pinned Helm binary, source guardrails, deployment guardrail, cluster guardrails, evidence orchestrator, evidence publisher contract, and index reconciliation. The artifact package preserves the authority inventory that governed the work.

### Configuration excerpt

```yaml
deploy_grafana_operations_dashboard: true
deploy_grafana_operations_alerts: true
```

```text
FluentBitCoverageDegraded: sum(up{job="fluent-bit-collector"}) < 7 or absent(up{job="fluent-bit-collector"})
LonghornStorageUtilizationHigh: 100 * sum(longhorn_node_storage_usage_bytes) / sum(longhorn_node_storage_capacity_bytes) > 80
```

## Prerequisites and assumptions

### Proven prerequisites

- The feature branch and upstream matched at each accepted checkpoint.
- The working tree was clean before staged mutations and final capture.
- Repository source, deployment, cluster, evidence, index, and SAGE guardrails passed in the captured runs.
- Prometheus, Grafana, Loki, Longhorn, Kubecost, and Fluent Bit endpoints were reachable in the acceptance environment.

### Assumptions

- Seven Fluent Bit collector targets remain the intended coverage baseline.
- Eighty percent remains the intended Longhorn aggregate warning threshold.
- The existing Grafana sidecar continues loading ConfigMaps labeled for dashboards.
- The Prometheus rule selector continues selecting resources labeled `release=kube-prometheus-stack`.

## Implementation procedure

### Preparation

1. Discover live telemetry endpoints, repository authorities, candidate components, and capability gaps.
2. Capture a data contract for Grafana data sources and live metric families.
3. Keep deployment gates closed while source artifacts are generated and validated.

### Execution

1. Stage and validate three ServiceMonitors.
2. Stage and validate the 20-panel dashboard definition.
3. Activate the dashboard and scrape coverage through the observability phase.
4. Correct the live acceptance verifier and resume acceptance without additional cluster mutation.
5. Discover the alert contract and confirm inactive baselines.
6. Stage and validate the two-rule PrometheusRule.
7. Activate the alert gate and deploy only the alert resource.
8. Verify live rule health and state through the Prometheus API.
9. Repair SAGE directory-authority capture and generate the canonical input bundle.

### Expected change

The repository should reproducibly provision telemetry coverage, a Grafana operations dashboard, and actionable Prometheus rules, while all gates and validators fail closed on contract errors.

### Observed change

The resources were persisted and accepted live. Prometheus targets were up, seven newly activated panel queries returned results, and two alert rules evaluated healthy and inactive.

### Failed or superseded paths

1. Parent Ansible tag omission prevented the intended dashboard path.
2. ServiceMonitor object and target namespaces were conflated.
3. `kubectl` all-namespace argument ordering was invalid.
4. Render-only validation incorrectly inherited an already-open live gate.
5. A folded YAML path inserted a space.
6. A Kubernetes-style qualified label was used as a Prometheus rule label.
7. Git porcelain status was stripped and rollback state was captured too late.
8. SAGE capture treated directory authorities as files.
9. The first authority repair repeated the Git status parsing defect.

Each failure was corrected before the accepted checkpoint and is retained in `EV-007` and `EV-008`.

## Evidence items

### `EV-001` — Telemetry endpoint and dashboard data contracts

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001`, `CLM-002` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T01:41:19-05:00 |
| Execution source | donbs-imac |
| Target | Kalaxy3 Prometheus, Grafana, Loki, Longhorn, and Kubecost |
| Tool and version | repository discovery helpers; versioned by branch commits |
| Expected result | Identify usable endpoints, data sources, metrics, and target gaps |
| Actual result | Endpoint and dashboard contracts completed with readiness true |
| Confidence | high |
| Sensitive data | internal addresses retained under internal classification |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-telemetry-endpoint-contract-20260802-004920.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-data-contract-20260802-014120.json` |

**Command, query, source, or observation**

The contracts queried repository state and live Prometheus, Grafana, Loki, Longhorn, and Kubecost endpoints.

**Observed result**

The data contract identified Prometheus, Loki, and alertmanager data sources, existing cluster and Fluent Bit metrics, and endpoint metrics that required new scrape coverage.

**Interpretation**

The contracts justified adding exactly three ServiceMonitors and supported the dashboard query design.

### `EV-002` — Telemetry scrape staging receipt

| Field | Value |
|---|---|
| Classification | `generated-receipt` |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T01:31:00-05:00 |
| Execution source | donbs-imac |
| Target | repository branch |
| Tool and version | telemetry staging helper |
| Expected result | Three validated ServiceMonitors with gate closed and no persistence |
| Actual result | commit `fecb97540127ac3abee4100ef7f8dcf74286d769`; three definitions; no Kubernetes persistence |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-telemetry-scrape-receipt.json` |

**Command, query, source, or observation**

The helper ran source and deployment guardrails, rendered the ServiceMonitors, performed server-side dry-run admission, committed, and pushed.

**Observed result**

One Longhorn and two Kubecost ServiceMonitors were staged while `deploy_grafana_operations_dashboard=false`.

**Interpretation**

The scrape definitions were independently reviewable before live activation.

### `EV-003` — Dashboard definition receipt

| Field | Value |
|---|---|
| Classification | `generated-receipt` |
| Supports or contradicts | `CLM-002`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T02:00:00-05:00 |
| Execution source | donbs-imac |
| Target | Grafana dashboard ConfigMap |
| Tool and version | dashboard staging helper and repository validator |
| Expected result | Twenty validated panels with no live persistence |
| Actual result | commit `4dc80e59ea2c0829a809abe60c3bdea61f56613a`; 20 panels; server dry-run passed |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-definition-receipt.json` |

**Command, query, source, or observation**

The dashboard contract and ConfigMap were copied into a render directory, validated, and admitted by Kubernetes server dry-run.

**Observed result**

The definition contained 12 existing Prometheus panels, one Loki panel, three Longhorn panels, and four Kubecost panels.

**Interpretation**

The dashboard structure was valid, but the staged definition retained pending wording that later became a semantic cleanup gap.

### `EV-004` — Dashboard live activation and recovery

| Field | Value |
|---|---|
| Classification | `live-acceptance` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-004`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T02:30:46-05:00 |
| Execution source | donbs-imac |
| Target | observability namespace and Grafana |
| Tool and version | Ansible observability phase, kubectl, Prometheus API |
| Expected result | Dashboard and ServiceMonitors persisted with live target and query acceptance |
| Actual result | three ServiceMonitors; 20-panel dashboard; two Kubecost and two Longhorn targets up; seven new panel queries returned data |
| Confidence | high |
| Sensitive data | internal scrape URLs retained in source receipt |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-activation-receipt.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-activation-failure.json` |

**Command, query, source, or observation**

The observability phase deployed the ServiceMonitors and dashboard. The first verifier failed because it looked for the Longhorn ServiceMonitor in the target namespace rather than the object namespace.

**Observed result**

The corrected acceptance path found all ServiceMonitors in `observability`, verified selectors for `kubecost` and `longhorn-system`, found four healthy targets, and proved seven activated panel queries.

**Interpretation**

The dashboard and scrape coverage were live; the earlier failure was a verifier defect rather than a deployment defect.

### `EV-005` — Alert contract and staged rules

| Field | Value |
|---|---|
| Classification | `generated-receipt` |
| Supports or contradicts | `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T03:01:00-05:00 |
| Execution source | donbs-imac |
| Target | PrometheusRule definition |
| Tool and version | alert discovery and staging helpers |
| Expected result | Two unique valid warning alerts with inactive baselines |
| Actual result | commit `ab36c484e32c28936f282287c707b0e4087cbaba`; two rules; gate closed; zero active baseline |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-contract-20260802-024450.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-receipt.json` |

**Command, query, source, or observation**

The alert contract measured seven healthy Fluent Bit targets and Longhorn aggregate utilization below the warning threshold before staging.

**Observed result**

`FluentBitCoverageDegraded` used a ten-minute duration, and `LonghornStorageUtilizationHigh` used a fifteen-minute duration. Kubernetes server-side dry-run accepted the corrected rule labels.

**Interpretation**

The rules were structurally and semantically ready for controlled activation.

### `EV-006` — Alert-rule live activation and evaluation

| Field | Value |
|---|---|
| Classification | `live-acceptance` |
| Supports or contradicts | `CLM-003`, `CLM-004`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T03:16:21-05:00 |
| Execution source | donbs-imac |
| Target | Prometheus in observability |
| Tool and version | Ansible observability phase and Prometheus API |
| Expected result | One PrometheusRule with two loaded healthy inactive alerts |
| Actual result | commit `55916a36afdee3fd8187f2269995f44e7ba532c2`; two rules; health ok; state inactive |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-activation-receipt.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-activation-failure.json` |

**Command, query, source, or observation**

The alert-only tagged path opened the alert gate, deployed the PrometheusRule, queried the live rules API, and evaluated both expressions directly.

**Observed result**

Both rules had `health=ok`, `state=inactive`, no last error, and zero active direct-query results. The corrected helper also recovered the interrupted uncommitted gate flip.

**Interpretation**

Prometheus loaded and evaluated both rules successfully. Notification delivery remains outside this evidence boundary.

### `EV-007` — Consolidated implementation terminal evidence

| Field | Value |
|---|---|
| Classification | `operator-transcript` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003`, `CLM-004` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T03:16:21-05:00 |
| Execution source | donbs-imac |
| Target | repository and Kalaxy3 cluster |
| Tool and version | Git, Ansible, kubectl, repository guardrails |
| Expected result | Preserve commands, failures, corrections, commits, and live acceptance |
| Actual result | Six source transcripts consolidated with source hashes |
| Confidence | high |
| Sensitive data | internal hostnames and addresses; no credentials |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-terminal-evidence.txt` |

**Command, query, source, or observation**

The transcript contains the staging, activation, guardrail, commit, push, and acceptance outputs.

**Observed result**

It records successful checkpoints and the dashboard and alert activation failures that preceded acceptance.

**Interpretation**

The transcript provides chronological provenance and prevents the final state from hiding failed paths.

### `EV-008` — SAGE authority-directory repair and capture receipt

| Field | Value |
|---|---|
| Classification | `repository-repair` |
| Supports or contradicts | `CLM-004`, `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T03:43:23-05:00 |
| Execution source | donbs-imac |
| Target | SAGE evidence orchestrator and capture workflow |
| Tool and version | `scripts/sage/sage-evidence-orchestrator.py` at `6250100ebf015e5243854a32d2a1741d73ed4484` |
| Expected result | Directory authorities expand to tracked files and canonical capture succeeds |
| Actual result | repair committed and pushed; 14 inputs and 132 authorities captured |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-sage-authority-directory-capture-fix-receipt.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-sage-capture-repair-terminal-evidence.txt.gz`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/kalaxy3-grafana-operations-evidence-inputs-receipt.json` |

**Command, query, source, or observation**

The first capture failed closed because a directory authority was treated as a file. The orchestrator was repaired to expand directories with tracked-file enumeration, and the corrected helper passed all SAGE guardrails.

**Observed result**

The final input capture produced SHA-256 `1ac7f891b41c39aa967c92f4e2b01562beb89ae259406c351e91bae5d94aa15d` without repository or Kubernetes mutation.

**Interpretation**

The repair aligned evidence capture with the discovery contract and converted a repeated workflow defect into a repository regression.

### `EV-009` — Canonical evidence input bundle

| Field | Value |
|---|---|
| Classification | `canonical-input-bundle` |
| Supports or contradicts | `CLM-005`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-08-02T03:43:23-05:00 |
| Execution source | SAGE evidence orchestrator |
| Target | schema 1.2 evidence synthesis |
| Tool and version | SAGE orchestrator at `6250100ebf015e5243854a32d2a1741d73ed4484` |
| Expected result | Complete manifest, repository evidence, session context, authority inventory, brief, and terminal inputs |
| Actual result | 150-member ZIP with 14 terminal inputs, 132 authorities, and seven contexts |
| Confidence | high |
| Sensitive data | internal evidence package |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/kalaxy3-grafana-operations-evidence-inputs.zip`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/bundle-manifest.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/sage-session-context.json`; `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/evidence-inventory.json` |

**Command, query, source, or observation**

The orchestrator captured the original request, canonical request, repository boundary, authorities, and evidence files.

**Observed result**

The bundle manifest and permanent inventory contain SHA-256 digests for every preserved input.

**Interpretation**

The bundle is a complete synthesis boundary for this schema 1.2 publication package.

## Verification and acceptance criteria

### Functional verification

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | ServiceMonitor definitions are valid | `EV-002` | three resources admitted by server dry-run | three admitted | pass |
| `AC-002` | Scrape targets are live | `EV-004` | Longhorn and Kubecost targets up | two Longhorn and two Kubecost targets up | pass |
| `AC-003` | Dashboard is provisioned | `EV-004` | UID exists with 20 panels | UID `kalaxy3-operations`, 20 panels | pass |
| `AC-004` | New dashboard queries return data | `EV-004` | seven Longhorn and Kubecost queries return results | seven returned results | pass |
| `AC-005` | Alert resource is admitted | `EV-005` | PrometheusRule server dry-run passes | passed | pass |
| `AC-006` | Alerts are loaded and healthy | `EV-006` | two rules, health ok, no errors | observed | pass |
| `AC-007` | Baseline is not firing | `EV-006` | both states inactive and expressions return zero | observed | pass |
| `AC-008` | Evidence input capture is complete | `EV-008`, `EV-009` | 14 inputs, expanded authority files, clean repository | 14 inputs, 132 authorities, clean | pass |

### Negative verification

- Invalid Prometheus qualified rule labels were rejected by Kubernetes before persistence.
- A malformed folded Ansible path failed render validation before commit.
- Namespace-verifier and Git-status-parser defects failed closed and were corrected.
- The SAGE capture refused a directory authority until the repository orchestrator was repaired.
- Dashboard and alert deployment gates remained closed during staging.

## Idempotency and repeatability

### First accepted run

The first live dashboard deployment persisted three ServiceMonitors and the ConfigMap. The first live alert deployment persisted one PrometheusRule.

### Steady-state rerun

The acceptance resume path was read-only for the already-deployed dashboard resources. The final alert acceptance left a clean working tree. The evidence capture was rerun after the orchestrator repair and produced a checksum-verified bundle without repository or Kubernetes mutation.

### Interpretation

Repository rendering and validation are repeatable. Applying an unchanged Kubernetes manifest should converge, but deletion is not implied by setting a gate false. Full rollback therefore requires both Git reversion and explicit resource removal or a future repository-owned teardown primitive.

## Security, privacy, and evidence handling

### Security controls

- Repository-managed kubeconfig, context, SSH trust, Helm binary, source hashes, and dependency locks were validated.
- Cluster mutations occurred only after explicit gate activation and repository guardrails.
- The SAGE publisher scans the record and text artifacts for known credential patterns.

### Sensitive material excluded

No private keys, bearer tokens, GitHub tokens, kubeconfig client keys, or passwords are included. Internal hostnames, pod addresses, file paths, and scrape URLs remain classified internal because they are required for engineering provenance.

### Redactions and omissions

The supplied transcripts contain redaction-test output but no live secret value. No screenshots were supplied.

### Residual security risk

The record does not validate Grafana authentication, Alertmanager receiver credentials, network policy, or external notification channels. Those controls remain governed by their existing platform records and future alert-delivery evidence.

## Reliability, recovery, rollback, and rebuild

### Failure modes

- Parent and child Ansible tags can make tasks unreachable.
- ServiceMonitor object namespace and target namespace are distinct contracts.
- Render-only validation can accidentally inherit live gates.
- YAML folding can alter file paths.
- Prometheus rule labels use a different naming grammar from Kubernetes metadata labels.
- Human-readable Git porcelain cannot be safely normalized with `.strip()`.
- Evidence discovery and capture must agree on directory authority semantics.

### Rollback

1. Revert the alert activation and dashboard activation commits.
2. Keep staged definitions if rapid reactivation is desired, or revert definition commits for full source rollback.
3. Explicitly remove the PrometheusRule, dashboard ConfigMap, and three ServiceMonitor objects from `observability`; closing gates alone does not delete persisted resources.
4. Re-run source, deployment, cluster, and evidence guardrails.
5. Verify Prometheus no longer loads the rules and Grafana no longer provisions the dashboard.

### Rebuild procedure

1. Restore the repository at commit `6250100ebf015e5243854a32d2a1741d73ed4484` or a descendant that preserves these paths.
2. Use the repository virtual environment, kubeconfig, context, pinned Helm tooling, and phase playbooks.
3. Run source, deployment, and cluster guardrails.
4. Execute the observability phase with the dashboard and alert gates enabled.
5. Verify three ServiceMonitors in `observability`, four healthy Longhorn or Kubecost targets, dashboard UID `kalaxy3-operations`, 20 panels, and two healthy alert rules.
6. Re-run the evidence contract and publisher checks.

### Data durability and backup impact

The work adds monitoring configuration and does not migrate application data. Rollback affects visibility and alert evaluation, not Longhorn volume contents or Kubecost source data.

## Operational considerations and observability

### Health signals

- Prometheus target health for Kubecost and Longhorn.
- Grafana dashboard provisioning and panel query results.
- `FluentBitCoverageDegraded` health and state.
- `LonghornStorageUtilizationHigh` health and state.
- Prometheus rule evaluation errors.
- Grafana sidecar dashboard load status.
- SAGE index reconciliation and evidence publisher checks.

### Routine verification

Re-run the dashboard acceptance queries and Prometheus rules API after observability upgrades, label changes, namespace changes, or node-count changes.

### Capacity, performance, cost, and sustainability

The Longhorn rule warns at aggregate utilization above 80 percent. Kubecost panels expose node hourly cost, management cost, CPU allocation, and memory allocation. No performance benchmark or additional resource-cost measurement was captured for the dashboard itself.

## Known limitations, evidence gaps, and risks

1. **Dashboard semantic state:** Longhorn and Kubecost row titles, descriptions, the dashboard tag, and ConfigMap stage label may still say staged or pending even though live queries work. Owner: Grafana operations follow-up before PR acceptance.
2. **Alert-state panels:** dedicated dashboard panels for the two alert rules were planned but are not evidenced. Owner: Grafana operations follow-up or explicit scope decision.
3. **Visual acceptance:** no screenshot or human browser review artifact was captured. Trigger: before UI acceptance or release notes.
4. **Notification delivery:** no Alertmanager receiver, routing, silence, or end-to-end notification test was performed. Trigger: before claiming paging readiness.
5. **Version evidence:** exact Grafana and Kubecost versions were not included in the captured receipts; component metadata therefore uses `version-not-captured`.
6. **Evidence effectiveness:** prior evidence and guardrails were retrieved, but no causal metric proves they reduced rework or elapsed time. The repeated Git porcelain defect shows recurrence remained possible.
7. **Teardown primitive:** gates prevent deployment but do not delete already-persisted resources. A repository-owned teardown primitive would improve rollback repeatability.
8. **Reviewer acceptance:** reviewer remains pending, so lifecycle status is validated rather than accepted.

## Troubleshooting

### Dashboard panels show no Longhorn or Kubecost data

Confirm the ServiceMonitor objects exist in `observability`, then separately inspect `namespaceSelector.matchNames`, service labels, endpoint ports, and Prometheus target health.

### Ansible tagged run skips the intended tasks

Include the parent `observability` tag and the appropriate child tag. Validate the tagged path in check mode before committing a gate change.

### PrometheusRule is rejected by Kubernetes

Use Prometheus-compatible rule label names such as `severity` and `component`. Keep qualified labels such as `kalaxy3.io/component` in Kubernetes object metadata only.

### Git reports an unexpected sole-file change

Use NUL-delimited porcelain bytes and preserve leading status columns. Do not call `.strip()` before parsing.

### SAGE capture reports an authority path is not a file

Confirm the repaired orchestrator is present. Directory authorities must expand deterministically through tracked files before hashing and ZIP capture.

## Freshness, revalidation, and supersession

### Revalidate when

- Grafana, kube-prometheus-stack, Fluent Bit, Longhorn, or Kubecost is upgraded.
- Service, namespace, label, port, or metric names change.
- The cluster node count changes from seven.
- Alert thresholds, durations, or routing are changed.
- Dashboard staged wording or alert-state panels are updated.
- The SAGE metadata contract, publisher, orchestrator, or indexer changes.

### Scheduled review

Review is event-based and must occur before the feature branch is accepted or whenever any revalidation trigger occurs.

### Supersession rule

A future evidence record supersedes this record only when it identifies this evidence ID, preserves the source artifacts, and documents the changed dashboard, alert, or SAGE contract.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects validation without claiming reviewer acceptance.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope, out-of-scope items, and nonclaims are explicit.
- [x] Implementation lineage includes the five requested checkpoints and the SAGE repair.
- [x] Relationships and supersession fields are populated.

### Evidence

- [x] Every critical claim references evidence IDs.
- [x] Expected and observed results are separated.
- [x] Failed attempts are preserved separately from the accepted final state.
- [x] Source receipts, transcripts, input bundle, manifest, context, and hashes are permanent artifacts.
- [x] Limitations and confidence are explicit.
- [x] Evidence-use effectiveness is not overstated.

### Safety and operations

- [x] Sensitive values are excluded or classified.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback, rebuild, and data-durability impacts are documented.
- [x] Operational health checks and revalidation triggers are documented.
- [x] Gates, idempotency limits, and teardown behavior are documented.

### Review acceptance

- [x] Reviewer is explicitly pending.
- [x] Record remains validated rather than accepted.
- [x] Dashboard semantic cleanup and visual acceptance are carried as follow-up gates.
- [x] Alertmanager delivery is not claimed.

## Git review and publication

This package uses evidence-only publication on branch `feature/grafana-operations-dashboard` and binds the record to implementation commit `6250100ebf015e5243854a32d2a1741d73ed4484`. The repository publisher will validate the package, replace the publication timestamp token, generate the record checksum and publication manifest, reconcile evidence navigation, commit the evidence, and optionally push.

## Appendices and raw artifacts

### Artifact inventory

| Artifact path | SHA-256 |
|---|---|
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/evidence-inventory.json` | `18696798ee990c89eb5296d12014935e1bd8b691ab9a1ab5f27518444ed071e7` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/bundle-manifest.json` | `395096ec1e4c1e1c017bbb05a5851745869bf11465956cabdf068048aa3acdb5` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/kalaxy3-grafana-operations-evidence-inputs-receipt.json` | `698013ad7cf06668566342dda12495d802fd134e9b650f42a37487554a0b83db` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/kalaxy3-grafana-operations-evidence-inputs.zip` | `1ac7f891b41c39aa967c92f4e2b01562beb89ae259406c351e91bae5d94aa15d` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/repository-evidence.md` | `4aa91cd20e67cf55baa606b974e6ca9b96d21bce329bc764383c5845c9549c6d` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/sage-evidence-generation-brief.md` | `e854fda8641096d80a359add187387397420f6d90f5a29acdeb5290a2e47da08` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/sage-session-context.json` | `a32e12f872ce2e85b3484f464d208ac7db556c41c589bf5fe015955b27eba661` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-evidence-closeout-contract-20260802-031900.json` | `6314bca12ea8779e44d11a46d7efd2a979679928cf46242161cd554b7f68065d` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-contract-20260802-024450.json` | `d2cecee412f258d7ad591dc5df6dd00923030a553c6072e9e3e839e9b9d7562e` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-activation-failure.json` | `58e8112a149d3381fee142c40d5dd714262b7f84256629a2e9678e46fdbd2870` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-activation-receipt.json` | `2ef6677efe6f63728f2332fe9b9484260858310a973ffa8e1b3f9f22e2d0c861` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-alert-rules-receipt.json` | `9300740a4efa4d96eac5c9d16bbca05544f2d6494241557fca0e0e46b425c4a0` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-activation-failure.json` | `36db1696f4eb6977fca225816c83bc04f6eb9db806baacdda855a19fafa56397` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-activation-receipt.json` | `4cdf768dadc62e38d36abc898aa7237fbcc246356b0302bb70111b381a88db01` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-data-contract-20260802-014120.json` | `ac9e28dafe5b51cc789df872e29507002f875315012fb8dd1d441aa7c38890f0` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-dashboard-definition-receipt.json` | `a4ba885396d36818280dc290b7fbec54f39e7af3a9e259474254592e5f5341dc` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-telemetry-scrape-receipt.json` | `8327f92b6398c369544f7ca4a5f059e15d17650d29d83bd6c6779a98bbe05ba0` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-operations-terminal-evidence.txt` | `ce4ff3ef3103a0016f4bf634ac42eb8ba6c94dda310c5c625d5e110993fa3c9c` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-sage-capture-repair-terminal-evidence.txt.gz` | `37f1c41e3109ea9cd83f57e357f482f43dd6d238720e0d2b0250167b686313cd` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-grafana-telemetry-endpoint-contract-20260802-004920.json` | `99e7c5e2966a98054e4d325300cd2fa8be7cb122143485b7a539a45ff984c3a9` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/source/kalaxy3-sage-authority-directory-capture-fix-receipt.json` | `34b2b135db2d9190beed993465bb1b82313832d38dd12aeae1d06bf788cc10ae` |
| `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/terminal-evidence-summary.md` | `3afc2d303db7fc6949ab36d79608598ac0eeba2a2f33f46d2332974b0084901b` |

The machine-readable inventory at `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/evidence-inventory.json` is authoritative for artifact hashes.

### Original requester language

```text
Generate a SAGE-compliant evidence package for the completed Kalaxy3 Grafana operations dashboard, telemetry scrape coverage, and actionable alerting work on feature/grafana-operations-dashboard. Include all available terminal evidence and JSON receipts; explain what was done, why it was done, and how it was validated; preserve the complete failure chronology and corrective lessons; identify the five implementation commits and live acceptance outcomes; document rollback, rebuild, remaining validation gaps, evidence-use metrics, recurrence indicators, and reusable workflow improvements; and prepare the package for SAGE publication and pull-request closeout.
```

### Additional notes

- Canonical input bundle SHA-256: `1ac7f891b41c39aa967c92f4e2b01562beb89ae259406c351e91bae5d94aa15d`.
- Capture receipt SHA-256: `698013ad7cf06668566342dda12495d802fd134e9b650f42a37487554a0b83db`.
- The full source bundle is nested under `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-001/input/kalaxy3-grafana-operations-evidence-inputs.zip` for replay and independent inspection.
