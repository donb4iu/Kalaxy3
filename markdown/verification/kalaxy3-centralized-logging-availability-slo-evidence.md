---
evidence_id: SAGE-K3-OBSERVABILITY-20260802-002
schema_version: "1.2"
title: Centralized Logging Availability SLO Activation and Failure-Recovery Evidence
nav_title: Centralized logging availability SLO activation
nav_section: verification
nav_order: 220
summary: Verifies live Fluent Bit and Loki availability SLO recording rules, inactive alert state, lifecycle-safe activation, and guarded evidence-capture recovery.
primary_subject: Centralized logging availability SLOs
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: Centralized logging availability SLO hardening
work_started_at: not-captured
work_completed_at: 2026-08-02T22:58:20-05:00
evidence_collected_at: 2026-08-02T23:08:32-05:00
created_at: 2026-08-02T23:09:00-05:00
updated_at: 2026-08-02T23:19:16-05:00
valid_as_of: 2026-08-02
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Don Buddenbaum
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
  - longhorn-system
endpoints:
  - prometheus-service=observability/kube-prometheus-stack-prometheus:http-web
  - prometheusrule=observability/kalaxy3-grafana-operations-alerts
  - loki-service=observability/loki-gateway
components:
  - fluent-bit-collector=1.0.9
  - loki=18.5.4
  - kube-prometheus-stack=87.19.0
  - helm=3.21.3+g1ad6e68
  - ansible-core=2.18.7
  - python=3.12.4
  - SAGE-evidence-schema=1.2
repository: donb4iu/Kalaxy3
branch: feature/centralized-logging-alerts-slos
implementation_commit: 1c41ce3a71d64613abb8bcfc0697223ede4c4733
record_path: markdown/verification/kalaxy3-centralized-logging-availability-slo-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002
confidence: high
tags:
  - sage
  - observability
  - centralized-logging
  - prometheus
  - slo
  - failure-recovery
relationships:
  verifies:
    - centralized logging availability SLO activation
  depends_on:
    - SAGE-K3-OBS-20260728-002
    - SAGE-K3-OBS-20260728-003
    - SAGE-K3-GUARDRAIL-20260731-001
    - SAGE-K3-OBSERVABILITY-20260802-001
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - generated_helper.internal_terminal_wrapper_marker_mismatch
    - generated_helper.evidence_reference_boundary_overreach
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-evidence-orchestrator.py
    - OpenAI GPT-5.6 Thinking
  implemented_by:
    - 1c41ce3a71d64613abb8bcfc0697223ede4c4733
  revalidated_by:
    - none
---

# Centralized Logging Availability SLO Activation and Failure-Recovery Evidence

## Executive summary

Kalaxy3 now evaluates two repository-owned centralized-logging availability
recording rules and three actionable alerts through the existing Grafana
operations PrometheusRule. The accepted live state reports both availability
ratios at `1.0`, all five rules healthy, all three alerts inactive, centralized
logging runtime validation passing, and cluster guardrails passing. The work
also preserved two failed helper paths, retrieved SAGE experience before each
retry, added recurrence guards, and repaired evidence capture so executables,
kubeconfigs, and repository files cannot be misclassified as terminal evidence.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-OBSERVABILITY-20260802-002 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Centralized Logging Availability SLO Activation and Failure-Recovery Evidence |
| **Navigation title** | Centralized logging availability SLO activation |
| **Navigation section** | verification |
| **Navigation order** | 220 |
| **Summary** | Verifies live Fluent Bit and Loki availability SLO recording rules, inactive alert state, lifecycle-safe activation, and guarded evidence-capture recovery. |
| **Primary subject** | Centralized logging availability SLOs |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Centralized logging availability SLO hardening |
| **Started** | not-captured |
| **Completed** | 2026-08-02T22:58:20-05:00 |
| **Evidence collected** | 2026-08-02T23:08:32-05:00 |
| **Record created** | 2026-08-02T23:09:00-05:00 |
| **Record updated** | 2026-08-02T23:19:16-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-08-02 |
| **Review due** | event-based |
| **Target record path** | markdown/verification/kalaxy3-centralized-logging-availability-slo-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/centralized-logging-alerts-slos |
| **Implementation commit** | 1c41ce3a71d64613abb8bcfc0697223ede4c4733 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac |
| **Controller host** | donbs-imac |
| **Nodes** | amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05 |
| **Node addresses** | not-applicable |
| **Namespaces** | observability; longhorn-system |
| **Endpoints** | prometheus-service=observability/kube-prometheus-stack-prometheus:http-web; prometheusrule=observability/kalaxy3-grafana-operations-alerts; loki-service=observability/loki-gateway |
| **Components and versions** | fluent-bit-collector=1.0.9; loki=18.5.4; kube-prometheus-stack=87.19.0; helm=3.21.3+g1ad6e68; ansible-core=2.18.7; python=3.12.4; SAGE-evidence-schema=1.2 |
| **Owner** | Don Buddenbaum |
| **Author** | OpenAI GPT-5.6 Thinking |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Navigation contract

- The formal title states the complete evidentiary claim.
- The navigation title provides a concise human-facing label.
- The verification section groups this record with live acceptance evidence.
- The navigation order is deterministic within that section.
- The summary explains the operational value and recovery boundary.
- The primary subject is the centralized-logging availability SLO capability.
- `[TOC]` is present for compatible page-level navigation.
- Historical records remain linked through relationships and are not rewritten.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author OpenAI GPT-5.6 Thinking synthesized the record; operator Don Buddenbaum executed the repository-owned helpers; owner Don Buddenbaum is accountable for Kalaxy3; reviewer pending remains an explicit review boundary; affected users are Kalaxy3 operators. |
| **What** | The session added and activated Fluent Bit coverage and Loki workload-availability recording rules, retained three actionable alerts, verified live values and alert state, preserved lifecycle and helper failures, and repaired evidence-input filtering. |
| **When** | Started not-captured; completed 2026-08-02T22:58:20-05:00; evidence collected 2026-08-02T23:08:32-05:00; local timezone America/Chicago; system timestamps America/Chicago and UTC; valid as of 2026-08-02; review due event-based. |
| **Where** | Environment homelab; cluster kalaxy3; execution host donbs-imac; controller donbs-imac; nodes amd64-01, amd64-02, arm64-01, arm64-02, arm64-03, arm64-04, and arm64-05; addresses not-applicable; namespaces observability and longhorn-system; endpoints prometheus-service=observability/kube-prometheus-stack-prometheus:http-web, prometheusrule=observability/kalaxy3-grafana-operations-alerts, and loki-service=observability/loki-gateway; record markdown/verification/kalaxy3-centralized-logging-availability-slo-evidence.md. |
| **Why** | The active logging deployment lacked explicit repository-owned availability SLO recording rules and a Loki workload-availability alert. Extending the existing PrometheusRule reused a proven deployment path, avoided a parallel alert framework, preserved lifecycle truth, and made failures and recovery auditable. |
| **How** | Repository SAGE discovery selected the existing Grafana operations alert framework; a two-file implementation was validated, committed, and pushed; the tagged observability phase reconciled the PrometheusRule; Prometheus and runtime checks established live acceptance; failure-triggered retrieval and production-shaped self-tests guarded repeated helper defects; the repository orchestrator captured safe evidence inputs. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- The two repository-owned SLO recording rules:
  `kalaxy3:fluent_bit_coverage_ratio` and
  `kalaxy3:loki_workload_ready_ratio`.
- The alerts `FluentBitCoverageDegraded`,
  `LokiWorkloadAvailabilityDegraded`, and
  `LonghornStorageUtilizationHigh`.
- Source validation, Ansible check mode, server-side dry-run, tagged activation,
  Prometheus rule acceptance, and active centralized-logging runtime validation.
- The active-lifecycle render rejection, helper marker mismatch, and safe
  evidence-input filtering recovery.
- Branch, commit, source hashes, artifact hashes, and SAGE evidence lineage.

### Out of scope

- Proving seven-day retention expiry.
- Longhorn backup, restore, replica-failure, or node-loss recovery.
- Sustained ingestion throughput, query latency, and capacity limits.
- Alertmanager notification delivery to an external receiver.
- Post-deployment Kubecost comparison and long-term storage-growth analysis.
- Merging the feature branch or closing a pull request.

### Nonclaims

This record does **not** claim:

- that the logging platform has complete disaster-recovery coverage;
- that the alerts have been forced through pending and firing states;
- that notification routing has been end-to-end tested;
- that retention, capacity, storage growth, or cost targets are satisfied;
- that one successful session proves autonomous or model-independent learning.

## Final accepted state

```text
Branch: feature/centralized-logging-alerts-slos
Implementation commit: 1c41ce3a71d64613abb8bcfc0697223ede4c4733
PrometheusRule: observability/kalaxy3-grafana-operations-alerts
Recording rules: 2
Alert rules: 3
Rule health: ok
Alert state: inactive
Fluent Bit coverage ratio: 1.0
Loki workload-ready ratio: 1.0
Centralized logging runtime: pass
Cluster guardrails: pass
```

| Item | Accepted result |
|---|---|
| Repository lineage | Local and remote feature branch matched commit `1c41ce3a71d64613abb8bcfc0697223ede4c4733`; working tree clean |
| Source scope | Exactly the PrometheusRule and its validator changed in the implementation commit |
| PrometheusRule | Resource `observability/kalaxy3-grafana-operations-alerts`, generation 2, resource version `10738565` |
| SLO values | Fluent Bit coverage `1.0`; Loki workload-ready ratio `1.0` |
| Rule health | Two recording rules and three alerts loaded with health `ok` |
| Alert state | All three alerts inactive at acceptance |
| Logging runtime | Seven collectors, one Loki gateway, one Loki workload, all seven nodes represented, 40 Gi Longhorn PVC Bound |
| Evidence capture | Safe UTF-8 textual artifacts selected; kubeconfig, binaries, executables, symlinks, and repository paths rejected |
| Repository mutation during activation and capture | none |
| Cluster mutation | PrometheusRule reconciled during activation; capture recovery was read-only |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Commit `1c41ce3a71d64613abb8bcfc0697223ede4c4733` contains the validated two-file logging availability SLO implementation. | critical | `EV-001` | supported | high |
| `CLM-002` | The PrometheusRule was reconciled through the repository-owned tagged observability path without a Git mutation. | critical | `EV-002`; `EV-003` | supported | high |
| `CLM-003` | Both centralized-logging availability recording values were `1.0` at live acceptance. | critical | `EV-002` | supported | high |
| `CLM-004` | All five rules were healthy and all three alerts were inactive at live acceptance. | critical | `EV-002`; `EV-003` | supported | high |
| `CLM-005` | The staged render validator correctly failed closed in the active lifecycle and the canonical runtime validator passed. | high | `EV-003`; `EV-004` | supported | high |
| `CLM-006` | The helper wrapper-marker mismatch was recorded, retrieved through SAGE, and protected by a production-shaped recurrence test. | high | `EV-001`; `EV-005` | supported | high |
| `CLM-007` | Evidence capture now excludes unsafe or nontext path references and completed without repository or cluster mutation. | critical | `EV-006`; `EV-007` | supported | high |
| `CLM-008` | Current logging runtime covered all seven nodes and used a Bound 40 Gi Longhorn volume. | high | `EV-002`; `EV-008` | supported | high |

## Problem and decision rationale

### Problem or opportunity

Centralized logging was active and healthy, but its existing operations rule
measured only direct Fluent Bit target count and Longhorn utilization. It did
not expose reusable availability ratios for engineering evidence, and it had no
Loki workload-availability alert. During implementation, the generic staged
render validator was also inapplicable to the already active lifecycle. Two
generated helpers then exposed separate evidence-handling defects: one relied
on an outer error wrapper absent from its internal transcript, and another
recursively selected arbitrary path values as terminal evidence.

### Decision

Extend the existing repository-owned Grafana operations PrometheusRule and
validator rather than create a second alert framework. Record Fluent Bit and
Loki availability as ratios with objective label `1`, alert when either ratio
is absent or below `1` for ten minutes, retain the Longhorn utilization alert,
activate through the tagged observability phase, and require live Prometheus
acceptance. Treat the active render rejection as expected negative evidence.
After helper failures, require failure-triggered retrieval and executable
recurrence tests before retry. Restrict evidence input to approved-root,
approved-suffix, strict UTF-8 text artifacts.

### Decision drivers

- Reuse the proven PrometheusRule deployment and validation path.
- Preserve true active lifecycle state instead of toggling an activation gate.
- Make availability values queryable and usable in later evidence.
- Keep alert definitions, validation, deployment, and recovery repository-owned.
- Fail closed on repeated helper defects before any source or cluster mutation.
- Prevent secret-bearing or binary files from entering evidence packages.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Create a separate logging PrometheusRule framework | Strong component isolation | Duplicates deployment, labels, validation, and evidence paths | rejected |
| Keep only raw target and replica queries | No repository change | No reusable SLO series or objective labels; weaker evidence lineage | rejected |
| Temporarily set centralized logging inactive to run staged render validation | Reuses the render-only validator | Falsifies lifecycle state and weakens evidence integrity | rejected |
| Bypass the failed render assertion | Faster local progress | Violates the actionable-failure contract and hides an invalid path | rejected |
| Accept any path referenced by receipts as evidence | Maximizes capture volume | Includes executables, kubeconfigs, repository source, and non-UTF-8 data | rejected |
| Filter evidence by suffix only | Simple | Does not prevent repository paths, symlinks, secret-bearing names, or binaries with misleading suffixes | rejected |
| Use approved roots, suffixes, strict UTF-8, size limits, and explicit decisions | Deterministic, auditable, safer | May omit relevant artifacts outside the approved roots until deliberately staged | accepted |

### Tradeoffs and consequences

- Availability ratios are simple and understandable, but the Fluent Bit ratio
  currently assumes the seven-node topology.
- Ten-minute alert windows reduce transient noise but delay detection.
- Workload readiness is a useful Loki availability proxy but does not prove
  successful ingestion, persistence, or query correctness by itself.
- Evidence filtering reduces exposure risk but requires explicit handling for
  future binary evidence formats.
- The failed paths increase session effort, but preserving them produced
  reusable recurrence controls and measurable failure-retrieval evidence.

## Architecture or change description

```text
Fluent Bit collector targets ──> kalaxy3:fluent_bit_coverage_ratio ──┐
                                                                    ├─> warning after 10m below 1 or absent
Loki StatefulSet + gateway ──> kalaxy3:loki_workload_ready_ratio ───┘

Longhorn capacity and usage ──> LonghornStorageUtilizationHigh after 15m

Repository source
  -> validator and negative tests
  -> Ansible check mode
  -> tagged observability reconciliation
  -> Prometheus operator validation
  -> live rule health, values, and inactive-state acceptance
```

### Before

- Fluent Bit coverage was an alert-only expression based on healthy-target
  count.
- No reusable Fluent Bit availability ratio existed.
- No Loki workload-availability recording rule or alert existed.
- Evidence input discovery could follow arbitrary path-like receipt values.

### After

- Two named SLO recording rules carry component, SLO, and objective labels.
- Fluent Bit and Loki alerts depend on the recorded ratios and use ten-minute
  stabilization windows.
- The Longhorn utilization alert remains in the same rule group.
- The Prometheus operator accepted the five-rule group.
- Evidence input decisions explicitly record accepted and rejected paths.

## Source of truth and implementation lineage

### Repository files

```text
infrastructure/k3s-homelab/playbooks/files/grafana-operations-alerts-prometheusrule.yml
infrastructure/k3s-homelab/scripts/validate-grafana-operations-alerts.py
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/helm-chart-lock.json
scripts/sage/sage-evidence-orchestrator.py
scripts/sage/sage-publish.py
```

### Implementation commit

```text
1c41ce3a71d64613abb8bcfc0697223ede4c4733
Add centralized logging availability SLO alerts
```

Base commit:

```text
7524944470204915399e4b4461971b4373ae5b4b
```

Source hashes at activation:

```text
c5f2d10a8cf315e5ed2db13c4414c18d0bd70b6aea15018e4db44d3597edae02  infrastructure/k3s-homelab/playbooks/files/grafana-operations-alerts-prometheusrule.yml
1bf094b0733cfc57541d49583011ddd72982307ec089a51723f25fdef8c44d57  infrastructure/k3s-homelab/scripts/validate-grafana-operations-alerts.py
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| Fluent Bit collector chart | 1.0.9 | `helm-chart-lock.json` and runtime validation |
| Loki chart | 18.5.4 | `helm-chart-lock.json` and runtime validation |
| kube-prometheus-stack chart | 87.19.0 | Helm lock reconciliation |
| Helm | 3.21.3+g1ad6e68 | repository-managed controller preflight |
| ansible-core | 2.18.7 | repository virtual environment |
| Python | 3.12.4 | repository controller preflight |
| SAGE evidence schema | 1.2 | canonical metadata contract |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Helm chart lock, repository fingerprints, Python environment, playbooks, manifests, and validators |
| Controller bootstrap | Repository controller and cluster preflight targets |
| Controller preflight | Core, Helm, cluster, SSH, and Ansible access checks passed |
| Controller host | donbs-imac |
| Execution host | donbs-imac |
| Machine-local authoritative state | Kubeconfig and local binaries were used operationally but were explicitly excluded from evidence artifacts and are not implementation authority |

- [x] Another supported controller can recreate the toolchain from a clean checkout.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual runtime changes were reconciled into repository-owned automation.
- [x] Controller and execution-host versions are recorded in `components`.

### Configuration excerpt

```yaml
- record: kalaxy3:fluent_bit_coverage_ratio
  expr: sum(up{job="fluent-bit-collector"}) / 7
  labels:
    component: logging
    slo: fluent-bit-coverage
    objective: "1"

- alert: LokiWorkloadAvailabilityDegraded
  expr: >-
    kalaxy3:loki_workload_ready_ratio < 1
    or absent(kalaxy3:loki_workload_ready_ratio)
  for: 10m
  labels:
    severity: warning
    component: logging
    slo: loki-workload-availability
    objective: "1"
```

## Prerequisites and assumptions

### Proven prerequisites

- The repository branch and remote matched the accepted implementation commit
  before activation and evidence capture (`EV-001`, `EV-002`, `EV-006`).
- The Grafana operations dashboard and alert deployment gates were active
  (`EV-002`).
- Source, deployment, Helm repository, cluster, evidence, index, and discovery
  guardrails passed (`EV-001`, `EV-002`, `EV-008`).
- The active centralized-logging runtime validator passed before and after
  activation (`EV-002`, `EV-003`, `EV-008`).
- Prometheus returned both candidate ratio inputs as `1.0` before source
  mutation (`EV-001`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The cluster remains a seven-node topology while the Fluent Bit denominator is `7`. | Scale changes can make the ratio incorrect. | Revalidate and revise the expression whenever inventory node count changes. |
| `ASM-002` | StatefulSet and Deployment readiness are sufficient first-order proxies for Loki workload availability. | A ready workload can still fail ingestion or queries. | Add ingestion rejection, buffering, storage pressure, and query-latency SLOs. |
| `ASM-003` | Inactive alerts plus healthy rule evaluation demonstrate correct normal-state behavior. | Threshold transitions and notification delivery may still be wrong. | Perform controlled synthetic pending, firing, recovery, and receiver tests. |

## Implementation procedure

### Preparation

```bash
python3 ~/Downloads/kalaxy3_sage_create_logging_alerts_branch.py
python3 ~/Downloads/kalaxy3_sage_recover_marker_and_stage_logging_availability_slos.py
```

### Execution

```bash
python3 ~/Downloads/kalaxy3_sage_activate_logging_availability_slos.py
python3 ~/Downloads/kalaxy3_sage_recover_evidence_capture_filtering.py
```

Repository-owned implementation and activation paths exercised by the helpers:

```bash
make sage-preflight
make sage-discovery-guardrail
make sage-index-check
make sage-evidence-guardrail
make centralized-logging-runtime-validate
.venv/bin/ansible-playbook playbooks/phases/phase-05-observability.yml \
  --check --diff --tags observability,grafana-operations-alerts
.venv/bin/ansible-playbook playbooks/phases/phase-05-observability.yml \
  --tags observability,grafana-operations-alerts
```

### Expected change

The feature branch should contain exactly the PrometheusRule and validator
changes; the active rule resource should contain two recording rules and three
alerts; Prometheus should report the rules healthy and the alerts inactive in a
healthy cluster; evidence capture should include only safe textual artifacts.

### Observed change

The two files were committed and pushed as
`1c41ce3a71d64613abb8bcfc0697223ede4c4733`. The tagged phase reconciled the
PrometheusRule, both recording rules evaluated to `1.0`, all three alerts were
inactive, runtime and cluster guardrails passed, and the recovered evidence
capture produced bundle SHA-256
`cc729eb7a1d8d94fc55ac7b8ce49861bb60e519ff75868af88dbe412d081ad44`
(`EV-001`, `EV-002`, `EV-006`).

### Failed or superseded paths

1. `centralized-logging-render` rejected the operation because logging was
   already active. This was expected fail-closed behavior. The activation gate
   was not changed; `centralized-logging-runtime-validate` was used instead
   (`EV-003`, `EV-004`).
2. A recovery helper required the outer wrapper line
   `FAILED: Command failed...`, but its internal terminal artifact ended with
   the stable Make failure line. SAGE failure retrieval was run, and the
   replacement fixture omitted the wrapper line and required stable
   repository-owned markers (`EV-001`, `EV-005`).
3. The first evidence collector recursively followed arbitrary path strings,
   selecting Python, `kubectl`, a kubeconfig, and repository files. The
   orchestrator failed strict UTF-8 decoding. The replacement ran
   failure-triggered retrieval and enforced approved roots, approved suffixes,
   strict UTF-8, regular-file, size, and kubeconfig exclusions (`EV-006`,
   `EV-007`).

## Evidence items

### `EV-001` — Staged implementation receipt

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-001`; `CLM-005`; `CLM-006` |
| Collected by | SAGE staging helper |
| Collected at | 2026-08-02T22:39:06-05:00 |
| Execution source | donbs-imac |
| Target | feature branch and staged PrometheusRule |
| Tool and version | Python=3.12.4; Git=version-not-captured |
| Expected result | Two approved files committed and pushed; no cluster persistence |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/staging-receipt.json` |

**Command, query, source, or observation**

```text
record_type: sage-logging-availability-slo-staging
status: pass
commit: 1c41ce3a71d64613abb8bcfc0697223ede4c4733
cluster_mutation: none-server-dry-run-only
```

**Observed result**

```text
Two-file cohesive commit pushed; required validations passed; working tree clean.
```

**Interpretation**

This proves implementation lineage and pre-activation validation. It does not
prove live Prometheus acceptance.

### `EV-002` — Activation and live-acceptance receipt

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-003`; `CLM-004`; `CLM-008` |
| Collected by | SAGE activation helper |
| Collected at | 2026-08-02T22:58:20-05:00 |
| Execution source | donbs-imac |
| Target | kalaxy3 cluster and observability namespace |
| Tool and version | kubectl=version-not-captured; Prometheus=chart 87.19.0 |
| Expected result | Two healthy recording rules, three healthy inactive alerts, both ratios 1.0 |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/activation-receipt.json` |

**Command, query, source, or observation**

```text
Prometheus rule API, instant queries, PrometheusRule resource, runtime validator, and cluster guardrails
```

**Observed result**

```text
kalaxy3:fluent_bit_coverage_ratio = 1.0
kalaxy3:loki_workload_ready_ratio = 1.0
rule health = ok
alert state = inactive
```

**Interpretation**

This directly supports the accepted normal-state runtime claims at the captured
time. It does not prove threshold transition or notification delivery.

### `EV-003` — Activation terminal transcript

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-004`; `CLM-005`; `CLM-008` |
| Collected by | SAGE activation helper |
| Collected at | 2026-08-02T22:58:20-05:00 |
| Execution source | donbs-imac |
| Target | tagged observability phase and Prometheus API |
| Tool and version | ansible-core=2.18.7; kubectl=version-not-captured |
| Expected result | Check-mode diff, controlled reconciliation, live acceptance, no Git changes |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/activation-terminal.txt` |

**Command, query, source, or observation**

```bash
.venv/bin/ansible-playbook playbooks/phases/phase-05-observability.yml \
  --tags observability,grafana-operations-alerts
```

**Observed result**

```text
PrometheusRule changed and provisioned; subsequent resource and Prometheus API checks passed.
```

**Interpretation**

The transcript shows the applied path and detailed responses. The concise
machine-readable acceptance claim remains `EV-002`.

### `EV-004` — Active lifecycle failure and recovery

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-005` |
| Collected by | SAGE validator runner and failure retrieval gate |
| Collected at | 2026-08-02T22:39:07-05:00 |
| Execution source | donbs-imac |
| Target | staged render validator and active runtime validator |
| Tool and version | SAGE-validator=repository commit 1c41ce3a71d64613abb8bcfc0697223ede4c4733 |
| Expected result | Render-only validation rejects active state; runtime validation passes |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/active-lifecycle-failure-retrieval.json` |

**Command, query, source, or observation**

```bash
make centralized-logging-render
make centralized-logging-runtime-validate
```

**Observed result**

```text
Render validator: expected fail-closed
Canonical runtime recovery: pass
```

**Interpretation**

The rejection protects lifecycle truth. It is not an implementation failure and
was not bypassed.

### `EV-005` — Helper marker mismatch recurrence guard

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-006` |
| Collected by | SAGE failure retrieval and marker-recovery helper |
| Collected at | 2026-08-02T22:39:07-05:00 |
| Execution source | donbs-imac |
| Target | generated helper terminal-marker verification |
| Tool and version | Python=3.12.4 |
| Expected result | Stable repository markers accepted without requiring an absent wrapper line |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/helper-marker-failure-retrieval.json` |

**Command, query, source, or observation**

```text
Failure ID: generated_helper.internal_terminal_wrapper_marker_mismatch
```

**Observed result**

```text
Failure-triggered retrieval completed; production-shaped fixture passed; source mutation before recovery was none.
```

**Interpretation**

The guard addresses the observed mismatch. It does not constitute a general
proof for every future transcript format.

### `EV-006` — Evidence-input capture recovery receipt

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-007` |
| Collected by | SAGE evidence-capture recovery helper |
| Collected at | 2026-08-02T23:08:32-05:00 |
| Execution source | donbs-imac |
| Target | repository-owned evidence orchestration input bundle |
| Tool and version | SAGE-evidence-schema=1.2; Python=3.12.4 |
| Expected result | Safe evidence bundle created; no repository or cluster mutation |
| Actual result | pass |
| Confidence | high |
| Sensitive data | unsafe paths rejected |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/capture-recovery-receipt.json` |

**Command, query, source, or observation**

```text
Bundle SHA-256: cc729eb7a1d8d94fc55ac7b8ce49861bb60e519ff75868af88dbe412d081ad44
```

**Observed result**

```text
status: pass
repository_mutation: none
cluster_mutation: none-read-only-validation-only
```

**Interpretation**

The recovered capture supplied the trusted synthesis boundary for this record.

### `EV-007` — Evidence artifact selection and rejection manifest

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-007` |
| Collected by | SAGE evidence-capture recovery helper |
| Collected at | 2026-08-02T23:08:32-05:00 |
| Execution source | donbs-imac |
| Target | candidate evidence paths |
| Tool and version | Python=3.12.4 |
| Expected result | Only approved-root strict UTF-8 text artifacts accepted |
| Actual result | pass |
| Confidence | high |
| Sensitive data | kubeconfig and non-authoritative paths rejected |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/evidence-selection.json` |

**Command, query, source, or observation**

```text
Policy: approved suffixes, strict UTF-8, 20 MiB limit, approved roots, no kubeconfig, no repository paths, no binaries or executables
```

**Observed result**

```text
Python symlink rejected
kubeconfig rejected
PrometheusRule source path rejected
validator source path rejected
kubectl rejected
safe receipts and transcripts accepted
```

**Interpretation**

The manifest closes the observed evidence-boundary defect and preserves every
selection decision.

### `EV-008` — Current validation and runtime capture

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-008`; `CLM-007` |
| Collected by | repository-owned SAGE validation targets |
| Collected at | 2026-08-02T23:08:32-05:00 |
| Execution source | donbs-imac |
| Target | repository indexes, evidence contracts, and centralized logging runtime |
| Tool and version | SAGE-evidence-schema=1.2; Loki=18.5.4; Fluent-Bit-collector=1.0.9 |
| Expected result | Guardrails and runtime validation pass |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/capture-validation-terminal.txt` |

**Command, query, source, or observation**

```bash
make sage-discovery-guardrail
make sage-index-check
make sage-evidence-self-test
make sage-evidence-guardrail
make centralized-logging-runtime-validate
```

**Observed result**

```text
All checks passed; seven nodes covered; 40 Gi Longhorn PVC Bound; seven collectors, one gateway, and one Loki workload.
```

**Interpretation**

This revalidated the evidence and runtime boundary after activation. It does
not replace future scheduled or event-triggered revalidation.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Exact approved implementation lineage | `EV-001` | clean pushed commit with two files | commit and remote matched | pass |
| `AC-002` | PrometheusRule persisted | `EV-002`; `EV-003` | named resource with five rules | resource version `10738565`, two records, three alerts | pass |
| `AC-003` | Fluent Bit coverage normal state | `EV-002` | ratio `1.0` | `1.0` | pass |
| `AC-004` | Loki workload availability normal state | `EV-002` | ratio `1.0` | `1.0` | pass |
| `AC-005` | Rule evaluation health | `EV-002` | all five `ok` | all five `ok` | pass |
| `AC-006` | Alert normal state | `EV-002` | all three inactive | all three inactive | pass |
| `AC-007` | Active lifecycle integrity | `EV-003`; `EV-004` | render rejected and runtime path passed | observed | pass |
| `AC-008` | Safe evidence capture | `EV-006`; `EV-007` | no binary, kubeconfig, executable, or repository-source evidence | unsafe paths rejected; bundle created | pass |
| `AC-009` | Current logging runtime | `EV-002`; `EV-008` | seven-node coverage and Bound storage | observed | pass |

### Functional verification

```bash
make centralized-logging-runtime-validate
```

Observed:

```text
Kalaxy3 centralized logging runtime validation: PASS
```

### Negative verification

```bash
make centralized-logging-render
```

Observed:

```text
SAGE ACTION BLOCKED because deploy_centralized_logging=True.
Canonical recovery: make centralized-logging-runtime-validate
```

The negative result is expected and proves the staged-only validator cannot
falsify the active lifecycle.

## Idempotency and repeatability

### First accepted run

```text
Tagged activation changed the rule source and provisioned the PrometheusRule.
Live acceptance then reported two ratios at 1.0 and three inactive alerts.
```

### Steady-state rerun

```text
A second apply with changed=0 was not captured.
Ansible check mode before activation showed only the expected PrometheusRule diff.
Post-activation runtime, cluster, index, evidence, and discovery checks passed.
```

### Interpretation

The declarative repository source, exact hashes, tagged phase, and validation
path support repeatability. Steady-state deployment idempotency remains an
explicit evidence gap and must be proven by a later changed=0 reconciliation.

## Security, privacy, and evidence handling

### Security controls

- Repository-owned Helm and source guardrails validated pinned and trusted
  deployment inputs.
- The activation used the repository kubeconfig and context without embedding
  kubeconfig contents in evidence.
- Evidence filtering allowed only approved-root regular files with approved
  suffixes, strict UTF-8 decoding, and a 20 MiB maximum.
- Kubeconfig names, executables, binaries, symlinks, and repository source paths
  were rejected and recorded.
- The package contains no Kubernetes Secret manifests or credential material.

### Sensitive material excluded

- The kubeconfig was rejected.
- Python and `kubectl` executables were rejected.
- Repository source paths were referenced by hash and commit rather than copied
  as terminal evidence.
- The selection manifest preserves exclusions without copying rejected content.

### Redactions and omissions

- Node addresses are not included because they are not required to validate the
  rule behavior.
- Full machine-local authentication configuration is omitted.
- Large terminal output is retained only in the artifact path designated for
  this evidence ID.

### Residual security risk

Terminal transcripts can contain future sensitive output even when they are
valid UTF-8. Publisher secret scanning and operator review remain required
before publication.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Fluent Bit target loss | Coverage ratio below `1` or absent for ten minutes | Partial log collection | Inspect DaemonSet, affected nodes, and Loki delivery |
| Loki replica unready | Workload-ready ratio below `1` or absent for ten minutes | Log ingestion or query degradation | Inspect rollout, readiness, nodes, and Longhorn state |
| Longhorn utilization above 80 percent | Existing storage alert for fifteen minutes | Capacity and write risk | Review capacity, replicas, snapshots, and volume growth |
| Active lifecycle sent to staged validator | SAGE actionable failure | Validation blocked without mutation | Run active runtime validator |
| Helper expects unstable wrapper text | Production-shaped self-test failure or marker mismatch | Workflow stops before mutation | Retrieve failure evidence and validate stable repository markers |
| Evidence path is binary, secret-bearing, or outside approved roots | Selection-manifest rejection or UTF-8 failure | Capture stops or artifact omitted | Stage an approved redacted textual artifact deliberately |
| Rule evaluation unhealthy | Prometheus rules API health not `ok` | Acceptance fails | Inspect operator validation, expression syntax, and source hashes |

### Rollback

Use repository history to restore the previous PrometheusRule and validator,
validate the reverted sources, and reconcile only the tagged Grafana operations
alert path. The implementation parent is:

```text
7524944470204915399e4b4461971b4373ae5b4b
```

A rollback must preserve the active logging gate and run:

```bash
make centralized-logging-runtime-validate
make cluster-guardrails
```

The record does not prescribe an unreviewed destructive Git command. Rollback
must use the repository-owned change and publication workflow.

### Rebuild procedure

1. Check out the published Kalaxy3 branch containing the implementation commit.
2. Run repository controller, Helm, and cluster preflight.
3. Run SAGE discovery and the source, deployment, and cluster guardrails.
4. Validate the PrometheusRule and validator self-tests.
5. Exercise the tagged observability phase in check mode.
6. Reconcile `observability,grafana-operations-alerts`.
7. Verify the PrometheusRule resource, loaded rule health, inactive normal
   state, both recording values, logging runtime, and cluster guardrails.
8. Regenerate evidence through the canonical orchestrator and publisher.

### Data durability and backup impact

The change modifies monitoring rules and does not migrate Loki data or alter
the 40 Gi Longhorn PVC. It therefore does not create a new data rollback
operation. Existing gaps remain for backup, restore, replica failure, node loss,
recovery-point objectives, and recovery-time objectives.

## Operational considerations and observability

### Health signals

- `kalaxy3:fluent_bit_coverage_ratio`
- `kalaxy3:loki_workload_ready_ratio`
- `FluentBitCoverageDegraded`
- `LokiWorkloadAvailabilityDegraded`
- `LonghornStorageUtilizationHigh`
- Prometheus rules API health and alert state
- Centralized-logging runtime validator
- Fluent Bit collector count and covered node labels
- Loki workload and gateway readiness
- Longhorn PVC phase, size, and storage class

### Routine verification

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
make centralized-logging-runtime-validate
make cluster-guardrails
```

Rule-specific acceptance should also verify the persisted PrometheusRule, the
loaded rule group, both ratio values, and alert states through the repository
activation or revalidation workflow.

### Capacity, performance, cost, and sustainability

- **Capacity:** No sustained ingestion, query, or storage-growth limit was
  established.
- **Performance:** Normal-state ratio evaluation passed; query latency and
  evaluation cost were not benchmarked.
- **Cost:** No post-deployment Kubecost comparison was captured.
- **Sustainability/power:** The two lightweight recording rules and one new
  alert were not separately power-profiled.

### Evidence-use metrics

- Failure-triggered retrieval was used for the wrapper-marker defect, the
  active-lifecycle render path, and the unsafe evidence-reference boundary.
- Prior evidence IDs were retrieved and used to select the existing operations
  alert framework and active runtime validation path.
- The final implementation and activation succeeded after those controls were
  applied.
- This session does not establish a causal reduction in rework or time to
  validation, and it does not support a maturity claim.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | `work_started_at` is `not-captured`; artifact filenames provide chronology but not a canonical start timestamp. | Session duration cannot be measured precisely. | Don Buddenbaum | next session-time capture improvement |
| `GAP-002` | evidence-gap | Seven-day retention expiry was not observed. | Retention behavior remains unproven. | Don Buddenbaum | after seven-day observation window |
| `GAP-003` | evidence-gap | Loki and Longhorn backup and restore were not exercised. | Recovery-point and recovery-time claims are unavailable. | Don Buddenbaum | before disaster-recovery acceptance |
| `GAP-004` | evidence-gap | Longhorn replica failure and node-loss behavior were not tested. | Storage resilience remains partially evidenced. | Don Buddenbaum | controlled resilience test |
| `GAP-005` | evidence-gap | Sustained ingestion throughput, buffering, rejection, query latency, and capacity were not benchmarked. | Scaling limits and alert thresholds remain unknown. | Don Buddenbaum | capacity test phase |
| `GAP-006` | evidence-gap | Long-term storage growth was not measured. | Time-to-capacity cannot be predicted. | Don Buddenbaum | recurring storage trend collection |
| `GAP-007` | evidence-gap | Post-deployment Kubecost comparison was not captured. | Incremental cost is unquantified. | Don Buddenbaum | next Kubecost evidence window |
| `GAP-008` | evidence-gap | Alerts were not deliberately driven through pending, firing, recovery, and external notification delivery. | Actionability beyond normal-state evaluation is unproven. | Don Buddenbaum | controlled alert test |
| `GAP-009` | evidence-gap | A steady-state tagged reconciliation with changed=0 was not captured. | Deployment idempotency is not directly proven. | Don Buddenbaum | next safe revalidation |
| `GAP-010` | review | Reviewer remains pending. | The record is validated, not accepted. | Don Buddenbaum | pull-request review |
| `RISK-001` | risk | The Fluent Bit denominator is a fixed seven-node topology. | Inventory changes can distort the ratio. | Don Buddenbaum | any node-count change |
| `RISK-002` | risk | Readiness can remain healthy while ingestion or query behavior degrades. | Availability can be overstated. | Don Buddenbaum | add service-level ingestion and query SLOs |

## Troubleshooting

### Render validation is blocked while logging is active

**Meaning**

The staged-only validator correctly refuses the active lifecycle.

**Checks**

```bash
grep -n "deploy_centralized_logging" \
  infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
```

**Recovery**

```bash
cd infrastructure/k3s-homelab
make centralized-logging-runtime-validate
```

Do not change the activation gate merely to satisfy the render validator.

### A recording rule is absent or unhealthy

**Meaning**

The Prometheus operator has not loaded the expected source or the expression
cannot evaluate.

**Checks**

```text
Inspect the persisted PrometheusRule, operator validation annotation, loaded
rule group, source hashes, and Prometheus rule health.
```

**Recovery**

Re-run source validation and check mode, then reconcile only the tagged
Grafana operations alert path after review.

### An alert is active in a supposedly healthy cluster

**Meaning**

The ratio is absent or below objective, or Longhorn utilization exceeds the
existing threshold.

**Checks**

```text
Inspect the alert query, recording value, target or replica readiness, node
coverage, Loki delivery, and Longhorn capacity.
```

**Recovery**

Repair the affected workload or storage condition; do not weaken the alert to
hide the symptom.

### Evidence orchestration reports a UTF-8 failure

**Meaning**

A nontext file may have crossed the evidence-input boundary.

**Checks**

```text
Review the evidence selection manifest for accepted and rejected paths.
```

**Recovery**

Supply a deliberate redacted UTF-8 representation under an approved evidence
root. Do not pass the binary, executable, or kubeconfig directly.

## Freshness, revalidation, and supersession

### Revalidate when

- the Fluent Bit, Loki, kube-prometheus-stack, Helm, Ansible, Python, or SAGE
  version changes;
- the node count changes;
- the PrometheusRule, validator, observability task, chart lock, or activation
  gate changes;
- the namespace, service, rule name, storage class, or PVC size changes;
- a recording value is absent or below objective;
- any of the three alerts becomes active unexpectedly;
- centralized-logging runtime or cluster guardrails fail;
- evidence selection policy or publisher secret scanning changes;
- a related evidence record supersedes the accepted architecture or runtime.

### Scheduled review

```text
Event-based: before merge, after a topology or component change, after a
controlled alert test, and when the remaining hardening evidence is collected.
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve
`SAGE-K3-OBSERVABILITY-20260802-002`, and state which live acceptance claims
remain valid.

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
| Owner | Don Buddenbaum | pending | pending | Owner review occurs with the feature-branch publication. |
| Reviewer | pending | pending | pending | A named reviewer is required before status can become accepted. |

## Git review and publication

Use only the canonical repository publisher:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-centralized-logging-availability-slo-evidence-package.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-centralized-logging-availability-slo-evidence-package.zip \
  --push
```

The package uses evidence-only publication and binds the record to implementation
commit `1c41ce3a71d64613abb8bcfc0697223ede4c4733`.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| activation-receipt.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/activation-receipt.json` | `9c2d6d1b15dc2978b5172fb1d2fc34ede08c115431a8c25a4b0b39e5fe36888c` | no | repository retention |
| activation-retrieval.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/activation-retrieval.json` | `7bdd5c442a03276d269815197b4c216abe42a874582eae0d11dba959026e04f5` | no | repository retention |
| activation-terminal.txt | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/activation-terminal.txt` | `ac10d96eb4670a12c8bf87956fc0d248083201393d22747c0e1393b1be76dcc2` | no | repository retention |
| active-lifecycle-failure-retrieval.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/active-lifecycle-failure-retrieval.json` | `14d0f3fe9e7741d21317ab940165ec63c4054553b69906015290a95f56982f2b` | no | repository retention |
| artifact-inventory.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/artifact-inventory.json` | `cb3dc84c6d3d34238bf7dc77af33feecefcdb28486faa1ae637c3e1b10308641` | no | repository retention |
| capture-recovery-receipt.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/capture-recovery-receipt.json` | `0cd0118d92bd81b6f432e1fa868406d7ec6353a833aa2cf10d3efd88173adae9` | no | repository retention |
| capture-validation-terminal.txt | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/capture-validation-terminal.txt` | `d7fb84368cbb8487b7d68f10376c4fffc5830dfda7a841e7e720c679b3e26ffd` | no | repository retention |
| evidence-selection.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/evidence-selection.json` | `a1d85e7f9b5e710d589034e9eaccfeb46ec452c8238da95b9621172c2185844c` | no | repository retention |
| helper-marker-failure-retrieval.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/helper-marker-failure-retrieval.json` | `9557c1eeaff0ad75c048951b7521e975a2a844302c5350b699a37ceddcdc3b99` | no | repository retention |
| initial-render-failure-terminal.txt | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/initial-render-failure-terminal.txt` | `8f4ae1886da9902c0807a24360a69d04a1c64b2f7770b5f1adb8c3a2b13aaec8` | no | repository retention |
| staging-authorities.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/staging-authorities.json` | `646f5c72fe8ebbe269778a1d874a4dbc5c6bce57f9c98005930346d8d3df9f43` | no | repository retention |
| staging-receipt.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/staging-receipt.json` | `f21604c02d0f469acb160658e8abe1a15c05f6bfc639b1ebc5ad7c2c34128c72` | no | repository retention |
| staging-retrieval.json | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/staging-retrieval.json` | `c4155367f5e5e40a2700740a989097758d25d0e04f262a08c431857803687562` | no | repository retention |
| staging-terminal-redacted.txt | `markdown/evidence-artifacts/SAGE-K3-OBSERVABILITY-20260802-002/staging-terminal-redacted.txt` | `c27b3485c6d132f4ff553789460f69ddfa594038391532aa4ab7927ae8a0f959` | no | repository retention |

### Additional notes

- The input bundle SHA-256 is
  `cc729eb7a1d8d94fc55ac7b8ce49861bb60e519ff75868af88dbe412d081ad44`.
- The selection manifest SHA-256 is
  `a1d85e7f9b5e710d589034e9eaccfeb46ec452c8238da95b9621172c2185844c`.
- The activation receipt SHA-256 is
  `9c2d6d1b15dc2978b5172fb1d2fc34ede08c115431a8c25a4b0b39e5fe36888c`.
- The staging receipt SHA-256 is
  `f21604c02d0f469acb160658e8abe1a15c05f6bfc639b1ebc5ad7c2c34128c72`.
- Empty intermediate terminal files were not promoted into this evidence
  package; the selection manifest preserves their existence and hashes.
- The staging transcript normalized the already-redacted test line
  `token=[REDACTED]` to `token: redacted`; the artifact inventory records
  that transformation.
- Publication replaces the implementation and publication timestamp tokens,
  writes the record checksum and publication manifest, and reconciles indexes
  through repository-owned automation.
