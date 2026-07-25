---
evidence_id: SAGE-K3-FINOPS-20260724-001
schema_version: "1.0"
title: Kubecost Homelab Cost Calibration, Network Measurement, and Shared Provider-Cost Allocation
project: Kalaxy3
record_type: finops
status: validated
classification: internal
created_at: 2026-07-25T00:03:40-05:00
updated_at: 2026-07-25T16:56:17-05:00
valid_as_of: 2026-07-25
review_due: event-based
owner: Don Buddenbaum
author: ChatGPT, regenerated from the Kalaxy3 SAGE standard, SAGE template, repository evidence, and terminal evidence collected by Don Buddenbaum
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
components:
  - Kubecost chart 3.2.1
  - Kubecost network-costs 0.19.0
  - IBM FinOps Agent
  - Ansible
  - Helm
  - Helm Diff 3.15.10
  - K3s v1.36.2+k3s1
  - Longhorn
  - MetalLB
nodes:
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
  - amd64-01
  - amd64-02
namespaces:
  - kubecost
  - kube-system
  - longhorn-system
  - metallb-system
  - minio
  - observability
  - storage
  - headlamp
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: d1d1339b4a3e54030f39bb0900e8e0934aa445c7
record_path: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md
confidence: medium
tags:
  - sage
  - finops
  - kubecost
  - cost-calibration
  - network-cost
  - network-measurement
  - provider-allocation
  - shared-cost
  - topology-labels
  - ansible
  - helm
  - idempotency
relationships:
  verifies:
    - Kalaxy3 Kubecost custom-pricing calibration
    - Kalaxy3 pod-level network byte measurement
    - Fixed-rate ISP allocation through Kubecost shared overhead
    - Idempotent Kubecost Helm reconciliation
    - Persistent Kalaxy3 node cost and topology metadata
  depends_on:
    - markdown/installation/kalaxy3-kubecost-installation-and-verification.md
    - markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/templates/sage-evidence-record-template.md
  supersedes:
    - The uncalibrated custom-cost-model gap in markdown/installation/kalaxy3-kubecost-installation-and-verification.md
    - The earlier version of this evidence record that ended before network-cost and ISP-allocation validation
  superseded_by:
    - none
  related_to:
    - markdown/installation/kalaxy3-observability-and-kubecost.md
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/templates/sage-evidence-record-template.md
  conflicts_with:
    - none known
  generated_by:
    - infrastructure/k3s-homelab/playbooks/kubecost-calibration-only.yml
    - infrastructure/k3s-homelab/playbooks/platform.yml
    - infrastructure/k3s-homelab/playbooks/tasks/kubecost-calibration.yml
    - infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml
    - infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2
    - Kubecost Allocation API
    - Kubecost network-cost metrics endpoint
    - Manual terminal validation performed from donbs-imac
    - ChatGPT SAGE record regeneration
---

# Kubecost Homelab Cost Calibration, Network Measurement, and Shared Provider-Cost Allocation

## Executive summary

Kalaxy3 Kubecost 3.2.1 is now configured as a reproducible homelab engineering-cost model rather than an uncalibrated cloud-cost installation. Version-controlled Ansible inputs calculate and render custom CPU, RAM, GPU, storage, network, and shared-overhead values; persistent node labels describe hardware, cost, role, GPU, storage, and on-premises topology; the Kubecost network-cost DaemonSet runs on all seven Linux nodes and exports pod-level ingress and egress byte counters; and a fixed `$20.00/month` ISP allocation is represented as shared monthly overhead rather than a fabricated usage-based per-GiB rate. A fixed-window API comparison proved that increasing monthly shared overhead from `$8.41` to `$28.41` increased the same 24-hour allocation by `$0.657530`, matching the expected `$0.657534` within `$0.000004` of rounding. The final Ansible rerun completed with `ok=37`, `changed=0`, and `failed=0`. This record is `validated`, not `accepted`, because the implementation commit SHA and independent reviewer acceptance remain pending and because several cost inputs remain engineering assumptions rather than accounting-grade measurements.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Owner and operator:** Don Buddenbaum. **Evidence collector:** Don Buddenbaum. **Record author:** ChatGPT, using the Kalaxy3 SAGE standard, SAGE template, prior Kubecost record, repository diffs, and terminal evidence supplied by Don Buddenbaum. **Reviewer:** pending. **Affected users:** the Kalaxy3 operator and future consumers of Kubecost engineering-cost evidence. |
| **What** | Calibrated Kubecost custom pricing; corrected the chart path for FinOps Agent custom prices; enabled network-cost collection; replaced an invalid affinity value with a valid Kubernetes affinity object; added persistent on-premises region and zone labels to all seven nodes; kept zone, region, and internet egress unit prices at zero; added `$20.00/month` of ISP cost to shared overhead; validated raw and fully burdened allocation behavior; and proved Ansible/Helm idempotency. |
| **When** | **Initial calibration implementation:** July 24, 2026 CDT. **Network and provider-cost implementation and evidence collection:** July 25, 2026 CDT. **Fixed-window test:** July 25, 2026, approximately 16:17–16:18 CDT. **Final idempotency proof:** July 25, 2026, approximately 16:27–16:31 CDT. **System timestamps used for the fixed window:** UTC. **Valid as of:** July 25, 2026. **Review due:** event-based. |
| **Where** | **Environment:** Kalaxy3 homelab. **Cluster:** `kalaxy3`. **Execution host for final validation:** `donbs-imac`. **Ansible target/controller:** `arm64-01`. **Nodes:** `arm64-01` through `arm64-05`, `amd64-01`, and `amd64-02`. **Kubecost namespace:** `kubecost`. **Allocation endpoint:** `http://192.168.2.26:9090/model/allocation`. **Repository:** `donb4iu/Kalaxy3`, branch `main`. **Primary source paths:** `infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml`, `playbooks/tasks/kubecost-calibration.yml`, `playbooks/tasks/kubecost-node-label.yml`, and `playbooks/templates/kubecost-calibration-values.yml.j2`. |
| **Why** | Kubecost could report Kubernetes usage but could not produce trustworthy Kalaxy3 dollar evidence without local hardware, storage, power, and shared-service inputs. Network bytes also needed to be observable without falsely implying that the flat-rate ISP bill was usage-metered. The design had to remain rebuildable from Git and Ansible, distinguish measurements from assumptions, survive reruns without drift, and produce evidence suitable for future ARM-versus-Intel architecture decisions. |
| **How** | Ansible inventory stores the cost inputs and labels. Calibration tasks validate and aggregate them, then render Helm values. `kubernetes.core.helm` applies the values with Helm Diff change detection. A network-cost DaemonSet measures pod ingress and egress bytes. Region and zone labels allow the collector to classify local traffic. Kubecost Allocation API queries produce raw and fully burdened namespace allocations. A fixed RFC3339 start/end window was used to compare two shared-overhead values against identical usage data. Rollback and rebuild operate through the same version-controlled source files and playbooks. |

### Five-W completeness gate

- [x] Who is complete.
- [x] What is complete.
- [x] When is complete and includes timezone.
- [x] Where is complete at repository and runtime levels.
- [x] Why includes rationale, alternatives, tradeoffs, and expected value.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Kubecost 3.2.1 custom price configuration for the Kalaxy3 homelab.
- Seven Kubernetes nodes: five Raspberry Pi 4 ARM64 nodes and two AMD64 Intel nodes.
- Blended CPU, RAM, GPU, and logical storage price rendering.
- Shared infrastructure power overhead already calculated by the calibration model.
- Addition of a `$20.00/month` attributable ISP allocation.
- Network-cost DaemonSet deployment and scheduling on all seven Linux nodes.
- Persistent Kubernetes region and zone labels for an on-premises single-region/single-zone model.
- Pod-level ingress and egress byte metrics.
- Raw namespace allocation, idle cost, shared namespace redistribution, fixed shared cost, and fully burdened namespace allocation.
- Fixed-window comparison of monthly shared-cost values.
- Failed implementation paths that materially explain the accepted design.
- Idempotent Ansible and Helm reconciliation.
- Rebuild, rollback, troubleshooting, risk, and revalidation guidance.

### Out of scope

- Accounting certification, tax treatment, or Generally Accepted Accounting Principles.
- Reconciliation to an actual ISP invoice, utility bill, purchase ledger, or depreciation schedule.
- Router-, modem-, switch-, or provider-side WAN byte counters.
- Packet payload capture, application protocol inspection, or security monitoring.
- Cloud-provider billing integration.
- Chargeback policy approval.
- Separate GPU workload metering or GPU scheduling.
- Per-node marginal pricing in Kubecost.
- Long-term weekly or monthly trend stability.
- Independent reviewer acceptance.
- Pull-request lineage; this workflow records direct Git commits rather than a pull request.
- Final archival checksums for every raw terminal transcript.

### Nonclaims

This record does **not** claim:

- that `$20.00/month` is the objectively correct ISP allocation; it is an explicit operator-selected policy input;
- that a fixed-rate ISP bill should be modeled as a per-GiB network price;
- that `networkCost: 0` means network usage is absent or operationally free;
- that Kubecost network byte counters are identical to provider-billed WAN traffic;
- that all observed pod traffic leaves the homelab;
- that shared cost is only the ISP allocation;
- that `__unmounted__` is an application namespace or should be hidden;
- that a rolling `window=24h` result can be compared safely with another query executed later;
- that the current blended CPU, RAM, and storage rates preserve per-node economic differences;
- that the current topology labels represent multiple physical regions or fault zones;
- that the model is accepted governance policy before review and Git lineage are completed.

## Final accepted state

```text
Kubecost chart:                    3.2.1
K3s/Kubernetes:                    v1.36.2+k3s1
Priced nodes:                      7
Network-cost collectors:          7 desired / 7 current / 7 ready
Network-cost image:               icr.io/kubecost/network-costs:v0.19.0
Topology region:                   kalaxy3-home
Topology zone:                     kalaxy3-lan
Network byte metrics:              ingress and egress counters present
Zone egress unit price:            $0.00000000/GiB
Region egress unit price:          $0.00000000/GiB
Internet egress unit price:        $0.00000000/GiB
Prior shared monthly overhead:     $8.41
ISP allocation added:              $20.00/month
Current shared monthly overhead:   $28.41
Fixed allocation window:           2026-07-24T21:17:00Z to 2026-07-25T21:17:00Z
Total with $8.41/month:            $60.822290
Total with $28.41/month:           $61.479820
Observed 24-hour increase:         $0.657530
Expected 24-hour increase:         $0.657534
Rounding difference:               $0.000004
Final Ansible recap:               ok=37 changed=0 unreachable=0 failed=0
Implementation commit:             d1d1339b4a3e54030f39bb0900e8e0934aa445c7
Reviewer:                          pending
```

| Item | Accepted result |
|---|---|
| Custom pricing path | Rendered under `finopsagent.agent.kubecost.customPrices`, matching the chart structure used by the live release. |
| Network measurement | Enabled and scheduled on all seven Linux nodes. |
| Network pricing | All unit prices remain zero because the provider charge is modeled as fixed monthly overhead. |
| Provider allocation | `$20.00/month` added to shared overhead, producing `$28.41/month` total. |
| Topology classification | All nodes labeled `region=kalaxy3-home` and `zone=kalaxy3-lan`; local traffic can be classified as same-region and same-zone. |
| Allocation API | Raw and fully burdened namespace results returned HTTP 200 and reconciled when all adjustment fields were included. |
| Shared-cost behavior | Fixed monthly share cost is prorated into the requested time window and distributed with shared namespace and idle sharing rules. |
| Fixed-window proof | The same 24-hour usage window showed the expected `$20/month` proration delta within rounding. |
| Idempotency | The immediate steady-state rerun reported `changed=0` and `failed=0`. |
| Governance state | Technical validation passed; commit and independent review remain pending. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Kubecost receives calibrated custom CPU, RAM, GPU, storage, and network prices from version-controlled Ansible/Jinja sources. | critical | `EV-001`, `EV-002`, `EV-013` | supported | high |
| `CLM-002` | The live shared monthly overhead is `$28.41`, consisting of the prior `$8.41` plus a `$20.00` provider allocation. | critical | `EV-003`, `EV-008`, `EV-009` | supported | high |
| `CLM-003` | The network-cost DaemonSet runs one ready collector on each of the seven Kalaxy3 nodes. | critical | `EV-004`, `EV-005` | supported | high |
| `CLM-004` | Persistent region and zone labels allow the on-premises collectors to classify local traffic without cloud-provider topology discovery. | high | `EV-005`, `EV-006`, `EV-013` | supported | high |
| `CLM-005` | Pod-level ingress and egress byte counters are being exported. | critical | `EV-006` | supported | high |
| `CLM-006` | Network monetary cost remains zero because all configured per-GiB rates are zero, even while bytes are measured. | high | `EV-001`, `EV-006`, `EV-007` | supported | high |
| `CLM-007` | Raw namespace allocation results reconcile only when adjustments are included with CPU, RAM, PV, network, shared, and total fields. | high | `EV-007` | supported | high |
| `CLM-008` | Kubecost correctly prorates an additional `$20.00/month` shared cost into a fixed 24-hour window. | critical | `EV-009` | supported | high |
| `CLM-009` | A moving `window=24h` comparison can be misleading because the underlying usage window changes between queries. | high | `EV-010`, `EV-009` | supported | high |
| `CLM-010` | Shared cost in a fully burdened response includes redistributed idle/shared-namespace cost and is not synonymous with the ISP allocation. | high | `EV-007`, `EV-010` | supported | medium |
| `CLM-011` | The final Ansible and Helm implementation is idempotent. | critical | `EV-011`, `EV-012` | supported | high |
| `CLM-012` | The original empty-string affinity approach was invalid because Kubernetes expected an affinity object. | high | `EV-014` | supported | high |
| `CLM-013` | The cost model is useful for engineering comparison but remains dependent on explicit hardware, power, lifecycle, and provider-allocation assumptions. | critical | `EV-001`, `EV-015` | supported | medium |
| `CLM-014` | The implementation is not yet an accepted SAGE source of truth because commit and reviewer lineage remain pending. | normal | `EV-016` | supported | high |

## Problem and decision rationale

### Problem or opportunity

Kubecost was installed and operational, but installation alone did not make its dollar outputs representative of Kalaxy3. The homelab owns its hardware, uses local storage, consumes household electricity, and pays a flat-rate internet bill. Public-cloud default pricing, empty custom-price fields, or manual UI settings would not represent that environment or survive a rebuild.

Network accounting introduced a separate modeling problem. Kalaxy3 needs visibility into pod ingress and egress bytes, but the ISP bill is not usage-metered. Assigning an arbitrary internet egress price per GiB would create a false causal relationship between traffic volume and provider cost. Conversely, leaving the network-cost component disabled would hide a useful operational dimension.

The solution therefore had to answer two distinct questions:

1. **How much network traffic do workloads generate?**
2. **How should a fixed monthly provider bill be allocated?**

Those questions require different mechanisms.

### Decision

- Use the Kubecost network-cost collector to measure pod-level ingress and egress bytes.
- Keep all zone, region, and internet egress unit prices at `$0.00/GiB`.
- Represent the attributable ISP share as fixed monthly `sharedOverhead`.
- Persist on-premises region and zone labels through Ansible.
- Compare cost-model changes only on identical fixed windows.
- Keep all cost and topology inputs version-controlled and reproducible.
- Preserve visible unattributed cost such as `__unmounted__` rather than concealing it.

### Decision drivers

- Accuracy of economic meaning.
- Separation of measurement from pricing policy.
- Rebuildability from Git and Ansible.
- Deterministic rendering of Helm values.
- Compatibility with Kubecost 3.2.1.
- Avoidance of cloud-only topology assumptions.
- Ability to distinguish raw allocation from fully burdened allocation.
- Evidence suitable for architecture comparisons.
- Idempotent operational behavior.
- Explicit limitations rather than false precision.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Leave network-cost disabled | Simpler deployment | No pod-level network evidence | rejected |
| Enable network-cost and invent a per-GiB ISP rate | Produces nonzero network dollar fields | Misrepresents a flat-rate bill and can over- or under-allocate cost based on traffic | rejected |
| Enable network-cost with zero unit prices and add fixed provider cost to shared overhead | Separates byte measurement from fixed-cost allocation | Shared cost is less directly intuitive and requires explanation | accepted |
| Use the chart's default topology affinity | Minimal override work | Expected cloud region/zone labels and did not fit the on-premises cluster | rejected |
| Set `affinity: ""` to disable chart affinity | Concise | Renders a string where Kubernetes requires an `Affinity` object; Helm upgrade fails | rejected |
| Use `affinity: {}` | Valid YAML object | Less explicit than the accepted Linux scheduling rule | superseded |
| Use a valid Linux node-affinity object | Type-safe, explicit, permits every Linux Kalaxy3 node | Must be maintained if non-Linux nodes are added | accepted |
| Apply topology labels manually only | Fast recovery | Not rebuildable and vulnerable to drift | rejected |
| Persist labels through Ansible | Reproducible and self-healing | Current values are hardcoded for one site and one zone | accepted |
| Compare repeated `window=24h` queries | Convenient | Windows move and underlying allocation changes | rejected for validation |
| Compare explicit RFC3339 start/end windows | Identical usage basis and reproducible delta | Requires slightly more scripting | accepted |
| Hide `__unmounted__` | Cleaner report | Conceals unattributed storage cost and weakens governance | rejected |
| Leave `__unmounted__` visible and investigate it | Preserves cost accountability | Adds an exception that must be managed | accepted |

### Tradeoffs and consequences

- Network usage is visible, but network dollar cost remains zero by design.
- Provider cost is allocated consistently, but the selected `$20.00/month` share is a policy assumption.
- Shared-cost distribution can concentrate heavily on the few namespaces not designated as shared.
- In the observed fully burdened sample, MinIO received nearly all distributed cost because it was the dominant non-shared workload.
- `__unmounted__` also received shared cost; this is mechanically consistent but operationally undesirable because it represents unattributed storage.
- Fixed-window comparisons are methodologically sound but require exact UTC timestamps and retained query parameters.
- Blended CPU/RAM/storage prices are useful for cluster-level engineering decisions but hide node-specific marginal economics.
- Topology labels improve classification but currently describe a single logical home region and LAN zone, not independent physical fault domains.
- Helm reconciliation can restart Kubecost workloads; changes should be treated as controlled operational events.

## Architecture or change description

```text
Version-controlled engineering-cost inputs
  inventory/group_vars/all/kubecost-calibration.yml
  inventory/host_vars/<node>.yml
        |
        v
Ansible calibration and validation
  playbooks/tasks/kubecost-calibration.yml
  playbooks/tasks/kubecost-node-label.yml
        |
        +--> persistent node hardware/cost/topology labels
        |
        v
Rendered Helm values
  /tmp/kalaxy3-kubecost-calibration-values.yaml
        |
        v
kubernetes.core.helm + Helm Diff
        |
        v
Kubecost 3.2.1
  - FinOps Agent custom prices
  - shared namespaces
  - shared monthly overhead
  - network-cost DaemonSet
  - Allocation API
        |
        +--> pod ingress/egress byte counters
        |
        +--> raw namespace allocation
        |
        +--> shareIdle + shareNamespaces + shareCost
                |
                v
          fully burdened namespace allocation
```

### Cost and traffic semantics

```text
Network measurement:
pod traffic -> network-cost collectors -> byte counters

Network pricing:
byte counters × $0.00/GiB -> $0 networkCost

Fixed ISP allocation:
$20.00/month -> sharedOverhead -> prorated to query window
             -> distributed with shareIdle/shareNamespaces/shareSplit rules
```

### Before

- Network-cost was disabled or could not be reconciled correctly.
- The first affinity override rendered as a string and was rejected by Kubernetes.
- Nodes lacked the region and zone labels needed for clean traffic classification.
- Collector logs reported that the local node region could not be located and that traffic could not be classified.
- Provider cost was not represented in the shared monthly overhead.
- Repeated rolling 24-hour queries were initially compared as if they represented the same data.
- The earlier SAGE record ended before network byte evidence, provider allocation, and fixed-window validation were complete.

### After

- `networkCosts.enabled` is rendered from the calibration source.
- A valid Linux node-affinity object allows one collector on every Kalaxy3 node.
- Ansible persists `topology.kubernetes.io/region=kalaxy3-home` and `topology.kubernetes.io/zone=kalaxy3-lan`.
- Collector classification errors were cleared after labeling and restart.
- Pod ingress and egress counters are present.
- All configured network unit prices remain zero.
- `$20.00/month` is added to shared overhead, producing `$28.41/month`.
- Fixed-window validation proves the expected proration.
- Final Ansible reconciliation is idempotent.

## Source of truth and implementation lineage

### Repository files

```text
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml
infrastructure/k3s-homelab/inventory/host_vars/arm64-01.yml
infrastructure/k3s-homelab/inventory/host_vars/arm64-02.yml
infrastructure/k3s-homelab/inventory/host_vars/arm64-03.yml
infrastructure/k3s-homelab/inventory/host_vars/arm64-04.yml
infrastructure/k3s-homelab/inventory/host_vars/arm64-05.yml
infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
infrastructure/k3s-homelab/playbooks/platform.yml
infrastructure/k3s-homelab/playbooks/kubecost-calibration-only.yml
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/playbooks/tasks/kubecost-calibration.yml
infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml
infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2
markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md
markdown/evidence-artifacts/SAGE-K3-FINOPS-20260724-001/terminal-evidence-20260725.md
```

### Implementation commit

```text
Commit: d1d1339b4a3e54030f39bb0900e8e0934aa445c7
Message: Validate Kubecost network and provider cost allocation

Implementation scope:
- infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml
- infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml
- infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| Kubecost chart | `3.2.1` | live Helm release and prior repository evidence |
| Network-cost image | `v0.19.0` | observed DaemonSet image |
| K3s/Kubernetes | `v1.36.2+k3s1` | observed cluster baseline |
| Helm Diff | `3.15.10` | prior calibration evidence |
| FinOps Agent | `v1.0.20` in prior evidence | existing Kubecost base values; revalidation recommended on chart upgrade |
| Ansible client | not captured in final transcript | evidence gap |
| Helm client | not captured in final transcript | evidence gap |
| `kubernetes.core` collection | not captured in final transcript | evidence gap |

### Configuration excerpt

```yaml
kubecost_calibration:
  shared:
    monthly_overhead_usd: 20.00
    average_watts: 72.00

  network:
    enabled: true
    zone_egress_usd_per_gb: 0.00
    region_egress_usd_per_gb: 0.00
    internet_egress_usd_per_gb: 0.00
```

```yaml
finopsagent:
  agent:
    kubecost:
      customPrices:
        enabled: true
        CPU: >-
          {{ '%.8f' | format(kubecost_cpu_core_month_usd | float) }}
        RAM: >-
          {{ '%.8f' | format(kubecost_ram_gib_month_usd | float) }}
        GPU: >-
          {{ '%.8f' | format(kubecost_gpu_month_usd | float) }}
        storage: >-
          {{ '%.8f' | format(kubecost_storage_gb_month_usd | float) }}
        zoneNetworkEgress: >-
          {{
            '%.8f'
            | format(
                kubecost_calibration.network.zone_egress_usd_per_gb
                | float
              )
          }}
        regionNetworkEgress: >-
          {{
            '%.8f'
            | format(
                kubecost_calibration.network.region_egress_usd_per_gb
                | float
              )
          }}
        internetNetworkEgress: >-
          {{
            '%.8f'
            | format(
                kubecost_calibration.network.internet_egress_usd_per_gb
                | float
              )
          }}

networkCosts:
  enabled: >-
    {{
      kubecost_calibration.network.enabled
      | bool
      | ternary('true', 'false')
    }}
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/os
                operator: In
                values:
                  - linux
```

```yaml
- name: Apply Kubecost topology labels to {{ kubecost_node_name }}
  ansible.builtin.command:
    argv:
      - kubectl
      - label
      - node
      - "{{ kubecost_node_name }}"
      - topology.kubernetes.io/region=kalaxy3-home
      - topology.kubernetes.io/zone=kalaxy3-lan
      - --overwrite
  environment:
    KUBECONFIG: "{{ kalaxy3_kubeconfig }}"
  register: kubecost_topology_label_command
  changed_when: >-
    'not labeled' not in kubecost_topology_label_command.stdout
```

## Prerequisites and assumptions

### Proven prerequisites

- The kubeconfig used from `donbs-imac` reached the Kalaxy3 API through the kube-vip endpoint.
- All seven nodes were joined and available to Ansible and Kubernetes.
- Kubecost 3.2.1 was installed and reachable at `192.168.2.26:9090`.
- The calibration inventory passed assertions for all seven nodes and four storage profiles.
- Helm Diff was installed and available to the Helm module.
- The Kubecost Allocation API returned HTTP 200 for raw and fully burdened queries.
- `jq`, `curl`, `awk`, `helm`, `kubectl`, `ansible-playbook`, and macOS `date` were available on the execution host.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | `$20.00/month` is a reasonable share of the household ISP bill attributable to Kalaxy3. | Fully burdened costs are over- or understated. | Record provider bill, allocation rationale, and review when bill or usage changes. |
| `ASM-002` | `730` hours is an acceptable average month for proration. | Small monthly-to-daily differences compared with calendar-month accounting. | Compare with actual calendar days if accounting precision is required. |
| `ASM-003` | Existing node purchase prices, residual values, useful lives, and power assumptions remain reasonable. | CPU/RAM/storage rates become stale or biased. | Revalidate after hardware, power-meter, electricity-rate, or lifecycle changes. |
| `ASM-004` | All current Kalaxy3 nodes belong to one logical region and one logical LAN zone. | Same-zone classification could hide actual fault-domain or network-cost differences. | Introduce distinct labels if the cluster spans rooms, buildings, sites, or routed segments. |
| `ASM-005` | Kubecost network counters are sufficient for workload engineering evidence. | They may not reconcile to WAN billing, NAT, retransmission, router, or provider counters. | Compare against router/modem/provider telemetry if available. |
| `ASM-006` | The selected shared namespaces represent platform services that should be redistributed to consuming workloads. | Application costs may be shifted incorrectly. | Review namespace policy before chargeback or showback publication. |
| `ASM-007` | Weighted sharing is appropriate for the current workload mix. | MinIO or another dominant workload may receive nearly all shared cost. | Compare weighted, even, and explicit allocation policies. |
| `ASM-008` | The chart's current `shareCost` semantics continue to treat the supplied value as monthly and prorate it into the query window. | Future chart/API changes could invalidate the formula. | Repeat fixed-window delta validation after every Kubecost upgrade. |

Material assumptions prevent `accepted` status unless the owner and reviewer explicitly accept the residual risk.

## Implementation procedure

### Preparation

Locate the source of fixed and network costs:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

grep -RInE \
  'shared.*overhead|fixed_monthly|monthly_overhead|internet|provider|isp' \
  inventory \
  group_vars \
  host_vars \
  playbooks \
  2>/dev/null
```

Confirm the live pre-change shared overhead:

```bash
helm get values kubecost \
  -n kubecost \
  -o json |
jq -r '.kubecostProductConfigs.sharedOverhead'
```

### Execution

1. Set `shared.monthly_overhead_usd: 20.00` in `inventory/group_vars/all/kubecost-calibration.yml`.
2. Correct and preserve `finopsagent.agent.kubecost.customPrices`.
3. Keep network unit prices driven by calibration variables and currently set to zero.
4. Enable network costs from the calibration source.
5. Render a valid Linux node-affinity object.
6. Add persistent topology labels through Ansible.
7. Apply the targeted Kubecost phase:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

8. Verify the live shared overhead.
9. Query raw and fully burdened allocation data.
10. Compare the old and new overhead against one fixed window.
11. Rerun Ansible to prove convergence.

### Expected change

- Helm values and the release change once.
- `sharedOverhead` becomes `28.41`.
- The network-cost DaemonSet has seven ready pods.
- Topology classification errors disappear.
- Network byte metrics appear.
- Monetary network cost remains zero.
- The fixed-window difference equals `$20 × 24 / 730`.
- A second Ansible run reports no changes.

### Observed change

- The first final deployment run reported `changed=2`, corresponding to rendered values and Helm release reconciliation.
- The live shared overhead returned `28.41`.
- The network-cost DaemonSet reported `7/7/7`.
- Ingress and egress metric series were observed.
- Fixed-window totals differed by `$0.657530`, matching the expected `$0.657534`.
- The immediate second run reported `changed=0` and `failed=0`.

### Failed and superseded implementation paths

#### Invalid affinity type

A temporary `affinity: ""` rendered a string into the DaemonSet specification. Kubernetes expected a structured `Affinity` object and rejected the Helm patch. This was a schema/type error, not a transient cluster failure.

#### Missing region and zone labels

Collectors initially logged:

```text
Could not locate region for local node
Failed to classify TransportData as NetworkTraffic
```

Adding region and zone labels to every node and restarting the DaemonSet cleared the classification error.

#### Rolling-window comparison

A later rolling `window=24h` query returned a lower total after the provider allocation was added. The underlying usage window had moved. The accepted validation uses an explicit start and end timestamp.

#### Hardcoded network prices during intermediate editing

An intermediate template used literal zero strings. The final implementation restored calibration-variable rendering so inventory remains the source of truth while still producing `0.00000000`.

## Evidence items

### `EV-001` — Repository cost and network source configuration

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-006`, `CLM-013` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:21–16:26 CDT |
| Execution source | `donbs-imac` |
| Target | Kalaxy3 repository working tree |
| Tool and version | Git; version not captured |
| Expected result | Only intended files modified; no whitespace errors |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline and terminal appendix |

**Command**

```bash
git status --short
git diff --check
git --no-pager diff -- \
  inventory/group_vars/all/kubecost-calibration.yml \
  playbooks/tasks/kubecost-node-label.yml \
  playbooks/templates/kubecost-calibration-values.yml.j2
```

**Observed result**

```text
M inventory/group_vars/all/kubecost-calibration.yml
M playbooks/tasks/kubecost-node-label.yml
M playbooks/templates/kubecost-calibration-values.yml.j2
```

The diff changed `monthly_overhead_usd` from `0.00` to `20.00`, added persistent topology labels, corrected the FinOps Agent path, preserved variable-driven zero network prices, enabled network costs, and replaced the invalid affinity with a valid object. `git diff --check` produced no output.

**Interpretation**

This proves the intended source files changed and passed Git whitespace validation. It does not prove runtime behavior by itself.

### `EV-002` — Rendered and live custom-pricing structure

| Field | Value |
|---|---|
| Classification | `repository-evidence` and `generated-artifact` |
| Supports or contradicts | `CLM-001`, `CLM-006` |
| Collected by | Don Buddenbaum and Ansible |
| Collected at | 2026-07-25, exact minute distributed across implementation session |
| Execution source | `donbs-imac`; rendering target `arm64-01` |
| Target | rendered Kubecost Helm values and live Helm release |
| Tool and version | Ansible, Helm, Jinja; client versions not captured |
| Expected result | Custom prices under `finopsagent.agent.kubecost.customPrices`; network prices rendered as numeric strings |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | repository template; rendered temporary values not durably archived |

**Relevant source**

```yaml
finopsagent:
  agent:
    kubecost:
      customPrices:
        enabled: true
        zoneNetworkEgress: "0.00000000"
        regionNetworkEgress: "0.00000000"
        internetNetworkEgress: "0.00000000"
```

**Interpretation**

The accepted path corrects the earlier structural mismatch and preserves eight-decimal network values. The temporary rendered file was not separately checksummed in the retained final sequence.

### `EV-003` — Provider overhead source located and updated

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:01–16:05 CDT |
| Execution source | `donbs-imac` |
| Target | `inventory/group_vars/all/kubecost-calibration.yml` |
| Tool and version | `grep`, Git |
| Expected result | Locate source variable rather than edit rendered files |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Observed source**

```text
inventory/group_vars/all/kubecost-calibration.yml:26:
    monthly_overhead_usd: 0.00
```

**Accepted change**

```yaml
shared:
  monthly_overhead_usd: 20.00
```

**Interpretation**

This proves the provider allocation was entered in the intended source-of-truth file.

### `EV-004` — Network-cost DaemonSet readiness

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25; exact minute not preserved in the retained excerpt |
| Execution source | Kalaxy3 administrative client |
| Target | `kubecost-network-costs` DaemonSet |
| Tool and version | `kubectl`; client version not captured |
| Expected result | desired, current, and ready counts equal seven |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Observed result**

```text
DESIRED   CURRENT   READY
7         7         7
```

**Interpretation**

One ready collector existed per priced node. This does not prove that every possible traffic path is visible.

### `EV-005` — Topology labels persisted on all nodes

| Field | Value |
|---|---|
| Classification | `direct-observation` and `repository-evidence` |
| Supports or contradicts | `CLM-003`, `CLM-004` |
| Collected by | Don Buddenbaum and Ansible |
| Collected at | 2026-07-25; final idempotency evidence at 16:27–16:31 CDT |
| Execution source | `donbs-imac`; target task executed through `arm64-01` |
| Target | all seven Kubernetes nodes |
| Tool and version | Ansible and `kubectl`; versions not captured |
| Expected result | every node has one region and one zone label; rerun reports no change |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | repository task and terminal appendix |

**Labels**

```text
topology.kubernetes.io/region=kalaxy3-home
topology.kubernetes.io/zone=kalaxy3-lan
```

**Final task behavior**

```text
Apply Kubecost topology labels to arm64-01 ... ok
Apply Kubecost topology labels to arm64-02 ... ok
Apply Kubecost topology labels to arm64-03 ... ok
Apply Kubecost topology labels to arm64-04 ... ok
Apply Kubecost topology labels to arm64-05 ... ok
Apply Kubecost topology labels to amd64-01 ... ok
Apply Kubecost topology labels to amd64-02 ... ok
```

**Interpretation**

The labels are automation-managed rather than one-time manual state. They represent one logical home region and one LAN zone, not independent fault domains.

### `EV-006` — Network metrics and classification

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-004`, `CLM-005`, `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25; exact minute not preserved in retained excerpt |
| Execution source | port-forwarded collector metrics endpoint |
| Target | Kubecost network-cost collector |
| Tool and version | `curl`, network-costs `v0.19.0` |
| Expected result | ingress and egress counters; local traffic classified same-region and same-zone |
| Actual result | pass |
| Confidence | high |
| Sensitive data | namespace and pod labels only; no packet payload captured |
| Artifact | terminal appendix |

**Observed metric names**

```text
kubecost_pod_network_egress_bytes_total
kubecost_pod_network_ingress_bytes_total
```

**Observed local classification labels**

```text
internet="false"
same_region="true"
same_zone="true"
```

Twelve matching metric series were retained, including traffic associated with `minio`, `metallb-system`, `observability`, and `kubecost`.

**Interpretation**

Network bytes are measured and topologically classified. The evidence does not establish router- or provider-side WAN totals.

### `EV-007` — Raw namespace allocation and reconciliation

| Field | Value |
|---|---|
| Classification | `direct-observation` and `derived-conclusion` |
| Supports or contradicts | `CLM-006`, `CLM-007`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25; exact minute not preserved in retained excerpt |
| Execution source | `donbs-imac` |
| Target | Kubecost Allocation API |
| Tool and version | `curl`, `jq`, Kubecost 3.2.1 |
| Expected result | HTTP 200, namespace allocations, calculated fields reconcile to total when adjustments included |
| Actual result | pass |
| Confidence | high |
| Sensitive data | internal namespace names and cost values |
| Artifact | terminal appendix |

**Query**

```bash
curl --fail --silent --show-error \
  'http://192.168.2.26:9090/model/allocation?window=24h&aggregate=namespace&accumulate=true' \
  -o /tmp/kubecost-allocation-namespace.json
```

**Observed namespaces**

```text
__idle__
__unmounted__
headlamp
kube-system
kubecost
longhorn-system
metallb-system
minio
observability
storage
```

**Observed raw 24-hour summary**

```text
Total cluster cost:  $60.5458
Idle cost:           $48.9752
Non-idle cost:       $11.5706
Idle percentage:     approximately 80.89%
Network cost:        $0
```

**Interpretation**

CPU, RAM, persistent volume, adjustment, and total fields reconciled when adjustment fields were included. The high idle share is useful engineering evidence but is sensitive to the selected window and workload activity.

### `EV-008` — Live shared overhead is `$28.41`

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:13 CDT |
| Execution source | `donbs-imac` |
| Target | live Kubecost Helm release |
| Tool and version | Helm; client version not captured |
| Expected result | `28.41` |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Command**

```bash
helm get values kubecost \
  -n kubecost \
  -o json |
jq -r '.kubecostProductConfigs.sharedOverhead'
```

**Observed result**

```text
28.41
```

**Interpretation**

The live release received the combined monthly overhead. This observation alone does not isolate the provider portion; `EV-003` provides the source value.

### `EV-009` — Fixed-window provider-cost proration

| Field | Value |
|---|---|
| Classification | `direct-observation` and `derived-conclusion` |
| Supports or contradicts | `CLM-002`, `CLM-008`, `CLM-009` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:17–16:18 CDT |
| Execution source | `donbs-imac` |
| Target | Kubecost Allocation API |
| Tool and version | `curl`, `jq`, `awk`, Kubecost 3.2.1 |
| Expected result | Total delta equals `$20 × 24 / 730 = $0.657534` within rounding |
| Actual result | pass |
| Confidence | high |
| Sensitive data | internal cost values only |
| Artifact | terminal appendix |

**Fixed window**

```text
2026-07-24T21:17:00Z,2026-07-25T21:17:00Z
```

**Observed result**

```text
With $8.41/month:  $60.822290
With $28.41/month: $61.479820
Difference:         $0.657530
Expected:           $0.657534
```

**Interpretation**

The `$0.000004` difference is numeric rounding. This is direct evidence that the extra `$20.00/month` is prorated correctly in the tested version.

### `EV-010` — Moving-window comparison produced a misleading lower total

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | supports `CLM-009`, informs `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:14–16:15 CDT |
| Execution source | `donbs-imac` |
| Target | Kubecost Allocation API |
| Tool and version | `curl`, `jq`, Kubecost 3.2.1 |
| Expected result | Informational; demonstrate why moving windows cannot prove the delta |
| Actual result | informational |
| Confidence | high |
| Sensitive data | internal cost values |
| Artifact | terminal appendix |

**Observed rolling-window result**

```text
NAMESPACE                      SHARED        TOTAL
minio                       30.789750    58.425380
__unmounted__                0.179680     0.340950
headlamp                     0.051130     0.097010

sharedCost: 31.020560000000003
networkCost: 0
totalCost: 58.863339999999994
```

**Interpretation**

The total was lower than an earlier query despite increased overhead because the underlying rolling usage window changed. This failed comparison method led to the fixed-window acceptance test.

### `EV-011` — First final deployment changed two resources

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-011` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:27–16:29 CDT |
| Execution source | `donbs-imac` |
| Target | `arm64-01` and live Kubecost Helm release |
| Tool and version | Ansible; version not captured |
| Expected result | Rendered values and Helm release change once |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Observed recap**

```text
arm64-01 : ok=37 changed=2 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

The changed tasks were `Render calibrated Kubecost Helm values` and `Install Kubecost`.

**Interpretation**

The first run applied the cleaned final template. This is expected implementation evidence, not idempotency evidence.

### `EV-012` — Steady-state idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-004`, `CLM-011` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:29–16:31 CDT |
| Execution source | `donbs-imac` |
| Target | `arm64-01` and live Kubecost Helm release |
| Tool and version | Ansible; version not captured |
| Expected result | `changed=0`, `failed=0` |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Observed recap**

```text
arm64-01 : ok=37 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

**Interpretation**

The full targeted flow converged, including cost validation, seven node-label loops, rendered values, Helm Diff, and Helm reconciliation.

### `EV-013` — Final source diff validation

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-004` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25 16:26 CDT |
| Execution source | `donbs-imac` |
| Target | final repository working tree |
| Tool and version | Git |
| Expected result | No whitespace errors; valid final structure |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Observed result**

`git diff --check` returned no output. The final diff showed valid `KUBECONFIG` handling, output-based topology-label idempotency, newline at end of file, variable-driven network rates, source-driven `networkCosts.enabled`, and a valid Linux affinity object.

**Interpretation**

Repository evidence agrees with runtime evidence.

### `EV-014` — Invalid string affinity rejected

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-012` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-25; exact minute not preserved |
| Execution source | Ansible/Helm execution |
| Target | `kubecost-network-costs` DaemonSet |
| Tool and version | Helm/Kubernetes |
| Expected result | Invalid value rejected |
| Actual result | fail for attempted design; pass as negative evidence |
| Confidence | high |
| Sensitive data | none |
| Artifact | terminal appendix |

**Relevant error**

```text
UPGRADE FAILED: cannot patch "kubecost-network-costs" with kind DaemonSet
spec.affinity: invalid value
```

The retained verbose error showed a string where Kubernetes required a `v1.Affinity` object.

**Interpretation**

This supports the accepted structured affinity and prevents recurrence of the same type error.

### `EV-015` — Cost-model assumptions remain estimates

| Field | Value |
|---|---|
| Classification | `assumption` and `derived-conclusion` |
| Supports or contradicts | `CLM-013` |
| Collected by | Don Buddenbaum and ChatGPT |
| Collected at | 2026-07-24 through 2026-07-25 CDT |
| Execution source | inventory and evidence review |
| Target | Kalaxy3 cost model |
| Tool and version | Ansible inventory; not applicable |
| Expected result | Assumptions explicit |
| Actual result | informational |
| Confidence | medium |
| Sensitive data | none |
| Artifact | this record |

**Observed assumptions**

- acquisition and residual values are inventory inputs;
- useful lives are policy inputs;
- power values are estimates or UPS allocations rather than per-device precision measurements;
- `$20.00/month` ISP allocation is operator-selected;
- network unit prices are intentionally zero.

**Interpretation**

The mechanics are validated, while absolute economic accuracy remains bounded by input quality.

### `EV-016` — Governance lineage remains incomplete

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-014` |
| Collected by | ChatGPT |
| Collected at | 2026-07-25 16:31 CDT |
| Execution source | evidence review |
| Target | SAGE record governance fields |
| Tool and version | SAGE standard 1.0 |
| Expected result | Commit and reviewer recorded for accepted status |
| Actual result | partial |
| Confidence | high |
| Sensitive data | none |
| Artifact | this record |

**Observed result**

```text
implementation_commit: d1d1339b4a3e54030f39bb0900e8e0934aa445c7
reviewer: pending
```

**Interpretation**

Technical validation is complete, but the record should not be marked `accepted`.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Source inputs are version-controlled | `EV-001`, `EV-003`, `EV-013` | Intended files only; no diff errors | Three intended files; no `diff --check` output | pass |
| `AC-002` | Custom price chart path is correct | `EV-002` | `finopsagent.agent.kubecost.customPrices` | present | pass |
| `AC-003` | Network-cost is enabled | `EV-001`, `EV-004` | enabled and scheduled | 7/7/7 collectors | pass |
| `AC-004` | Every node has on-prem topology labels | `EV-005` | seven labeled nodes | seven task results `ok` | pass |
| `AC-005` | Network metrics exist | `EV-006` | ingress and egress byte counters | both present | pass |
| `AC-006` | Local traffic classifies cleanly | `EV-006` | same region/zone, not internet | observed | pass |
| `AC-007` | Unit network prices remain zero | `EV-001`, `EV-002`, `EV-007` | `$0/GiB`; `networkCost=0` | observed | pass |
| `AC-008` | Provider allocation appears in live overhead | `EV-003`, `EV-008` | `$28.41/month` | `28.41` | pass |
| `AC-009` | Provider delta prorates correctly | `EV-009` | approximately `$0.657534` | `$0.657530` | pass |
| `AC-010` | Allocation query returns and reconciles | `EV-007` | HTTP 200 and total reconciliation | observed | pass |
| `AC-011` | Failed affinity design is removed | `EV-013`, `EV-014` | valid object, no string | observed | pass |
| `AC-012` | Automation converges | `EV-011`, `EV-012` | first change, then `changed=0` | `2`, then `0` | pass |
| `AC-013` | Secrets are excluded | security review | no secrets in record | none observed | pass |
| `AC-014` | Implementation commit recorded | `EV-016` | Git SHA | `d1d1339b4a3e54030f39bb0900e8e0934aa445c7` | pass |
| `AC-015` | Independent review completed | `EV-016` | reviewer acceptance | pending | partial |

### Functional verification

```bash
SHARED_NAMESPACES="$(
  helm get values kubecost \
    -n kubecost \
    -o json |
  jq -r '.kubecostProductConfigs.sharedNamespaces'
)"

for SHARE_COST in 8.41 28.41; do
  curl --fail --silent --show-error \
    --get \
    'http://192.168.2.26:9090/model/allocation' \
    --data-urlencode \
      'window=2026-07-24T21:17:00Z,2026-07-25T21:17:00Z' \
    --data-urlencode 'aggregate=namespace' \
    --data-urlencode 'accumulate=true' \
    --data-urlencode 'shareIdle=true' \
    --data-urlencode "shareNamespaces=${SHARED_NAMESPACES}" \
    --data-urlencode "shareCost=${SHARE_COST}" \
    --data-urlencode 'shareSplit=weighted' \
    --output "/tmp/kubecost-overhead-${SHARE_COST}.json"
done
```

Observed:

```text
With $8.41/month:  $60.822290
With $28.41/month: $61.479820
Difference:         $0.657530
Expected:           $0.657534
```

### Negative verification

#### Invalid affinity is rejected

```yaml
affinity: ""
```

Observed: Helm upgrade failed because the DaemonSet affinity field was not a valid object.

#### Moving window is not accepted as proof

A later rolling 24-hour result was `$58.86334`, below the earlier result despite higher shared overhead. The comparison was rejected because the windows were not identical.

## Idempotency and repeatability

### First accepted run

```text
arm64-01 : ok=37 changed=2 unreachable=0 failed=0
```

Expected changes:

- render final calibrated values;
- reconcile the Kubecost Helm release.

### Steady-state rerun

```text
arm64-01 : ok=37 changed=0 unreachable=0 failed=0
```

### Interpretation

The accepted automation is idempotent for the tested state. The topology-label task is imperative but reports steady state through `kubectl label --overwrite` output. The Helm module uses Helm Diff to avoid false-positive changes. Idempotency must be revalidated after Ansible, Helm, Helm Diff, Kubernetes, or chart upgrades because command output and diff behavior may change.

## Security, privacy, and evidence handling

### Security controls

- Cost inputs and nonsecret topology labels are stored in Git.
- `KUBECONFIG` is passed through the task environment rather than embedded in the record.
- No Kubernetes Secret manifests are included.
- No Basic Auth material, tokens, private keys, passwords, or provider account identifiers are included.
- The record includes internal IP addresses and node names and is classified `internal`.
- Network evidence consists of counters and Kubernetes labels, not packet payloads.

### Sensitive material excluded

Never include:

- kubeconfig client keys or certificates;
- bearer tokens;
- Ansible Vault passwords;
- Kubernetes Secret values;
- ISP account number, billing identifier, or payment information;
- terminal history containing credentials;
- packet contents or unnecessary personal information.

### Redactions and omissions

- Verbose Helm managed-field data from the failed DaemonSet patch was omitted because it did not add material evidence and greatly increased record size.
- Full repeated Ansible task output was reduced to material task names and recaps.
- No secret values were observed in retained excerpts.

### Residual security risk

- Internal addresses and topology names disclose homelab structure. Keep the record in the internal repository.
- Network metrics expose namespace and pod metadata. Restrict access to Kubecost and Prometheus according to Kalaxy3 administrative controls.
- The Kubecost frontend address is LAN reachable; authentication and exposure policy are governed by separate records.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Invalid affinity type | Helm error referencing DaemonSet affinity | Network-cost rollout fails | Restore structured affinity and rerun Ansible |
| Missing topology labels | Collector logs report missing region or failed classification | Metrics may exist but classification is incomplete | Reapply labels and restart DaemonSet |
| Network-cost pod not ready | Desired/current/ready mismatch | One or more nodes lack traffic metrics | Inspect pod events, selectors, tolerations, and logs |
| Wrong custom-price chart path | Live values omit or ignore prices | Allocation uses incomplete pricing | Restore `finopsagent.agent.kubecost.customPrices` |
| Hardcoded prices diverge from inventory | Repository and rendered values disagree | Source-of-truth drift | Render all values from calibration variables |
| Rolling-window comparison | Totals change unexpectedly | False configuration conclusion | Use explicit RFC3339 start/end window |
| Misread `sharedCost` | Operator assumes it is only ISP cost | Incorrect reporting | Isolate provider delta with fixed-window A/B test |
| `__unmounted__` grows | Allocation contains unattributed PV cost | Cost lacks workload ownership | Identify PV/PVC ownership and correct metadata |
| MinIO receives most shared cost | Weighted output is highly concentrated | Showback may appear disproportionate | Review sharing policy; compare alternate policies |
| Kubeconfig unavailable | Ansible or `kubectl` cannot reach cluster | Labels and Helm reconciliation fail | Restore verified kubeconfig and context |
| Helm Diff unavailable | Module may report false changes | Unnecessary releases or restarts | Reinstall pinned Helm Diff |
| Provider allocation becomes stale | Bill or usage share changes | Fully burdened cost becomes misleading | Update source and rerun fixed-window validation |

### Rollback

Preferred source-controlled rollback:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

git diff -- \
  inventory/group_vars/all/kubecost-calibration.yml \
  playbooks/tasks/kubecost-node-label.yml \
  playbooks/templates/kubecost-calibration-values.yml.j2
```

Either revert the implementation commit after it exists or deliberately restore previous values:

```yaml
shared:
  monthly_overhead_usd: 0.00

network:
  enabled: false
```

Then reconcile:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

Emergency Helm rollback, only after reviewing history:

```bash
helm history kubecost -n kubecost
helm rollback kubecost <known-good-revision> -n kubecost --wait
```

A Helm-only rollback creates temporary drift from Git/Ansible. Reconcile or revert the source immediately afterward.

### Rebuild procedure

1. Clone or update the Kalaxy3 repository.
2. Restore the verified Kalaxy3 kubeconfig.
3. Confirm all seven nodes are `Ready`.
4. Confirm Longhorn and Kubecost prerequisites.
5. Review `inventory/group_vars/all/kubecost-calibration.yml`.
6. Review every priced node's host variables.
7. Run syntax and diff checks.
8. Apply the targeted Kubecost playbook.
9. Verify live Helm values.
10. Verify node labels.
11. Verify DaemonSet `7/7/7`.
12. Inspect collector logs for classification errors.
13. Confirm ingress and egress metrics.
14. Run a raw allocation query.
15. Run a fully burdened fixed-window query.
16. Repeat Ansible and require `changed=0`.
17. Update evidence, checksum, and implementation commit.

### Data durability and backup impact

- The changes modify Helm values, node labels, and cost metadata; they do not intentionally delete Kubecost PVCs.
- Kubecost state remains Longhorn-backed according to dependent installation evidence.
- Helm reconciliation can restart workloads.
- Final post-change PVC binding and Longhorn replica health were not recaptured in this final sequence and remain a revalidation item.
- Temporary API result files under `/tmp` are not durable evidence unless copied into `markdown/evidence-artifacts`.

## Operational considerations and observability

### Health signals

- `kubectl get daemonset kubecost-network-costs -n kubecost`
- `kubectl get pods -n kubecost -o wide`
- collector logs for region/classification errors;
- network metric series count;
- `kubecost_pod_network_ingress_bytes_total`;
- `kubecost_pod_network_egress_bytes_total`;
- Allocation API HTTP status;
- nonzero or unexpected `networkCost`;
- `__idle__` share;
- `__unmounted__` cost;
- shared-cost concentration;
- Helm release status and revision;
- Ansible recap.

### Routine verification

```bash
kubectl get daemonset kubecost-network-costs -n kubecost

kubectl get nodes \
  -L topology.kubernetes.io/region,topology.kubernetes.io/zone

helm get values kubecost \
  -n kubecost \
  -o json |
jq '{
  sharedNamespaces: .kubecostProductConfigs.sharedNamespaces,
  sharedOverhead: .kubecostProductConfigs.sharedOverhead,
  networkCosts: .networkCosts,
  customPrices: .finopsagent.agent.kubecost.customPrices
}'
```

Use a fixed report window:

```bash
curl --fail --silent --show-error \
  --get \
  'http://192.168.2.26:9090/model/allocation' \
  --data-urlencode 'window=<RFC3339_START>,<RFC3339_END>' \
  --data-urlencode 'aggregate=namespace' \
  --data-urlencode 'accumulate=true'
```

### Capacity, performance, and cost impact

- **Capacity:** One network-cost pod runs on each of seven nodes.
- **Performance:** Collector overhead was not benchmarked in this record.
- **Cost:** Provider allocation adds `$20.00/month`; tested 24-hour delta is `$0.65753`.
- **Sustainability/power:** Existing estimates remain part of the model; this change added no new measured power value.
- **Reporting:** MinIO dominates fully burdened application cost under the current weighted sharing policy.
- **Governance:** `__unmounted__` remains visible as an attribution exception.

### How to interpret allocation fields

| Field | Meaning in this record |
|---|---|
| `cpuCost` | CPU allocation cost under calibrated blended CPU pricing |
| `ramCost` | RAM allocation cost under calibrated blended RAM pricing |
| `pvCost` | Persistent-volume cost under calibrated logical storage pricing |
| `networkCost` | Byte-based network charge; zero because all unit rates are zero |
| `sharedCost` | Redistributed idle/shared namespace cost plus prorated fixed `shareCost`; not only ISP cost |
| adjustment fields | Reconciliation corrections required to match `totalCost` |
| `totalCost` | Final allocation after component costs and adjustments |
| `__idle__` | Unallocated cluster capacity before idle sharing |
| `__unmounted__` | Persistent storage cost not attributed to a mounted workload allocation |

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | assumption | `$20.00/month` ISP allocation is a policy choice, not invoice-derived evidence. | Absolute fully burdened cost may be biased. | Don Buddenbaum | provider bill or usage-share change |
| `GAP-002` | evidence-gap | No router, modem, or ISP byte counter was reconciled to Kubecost metrics. | Network bytes are workload evidence, not provider billing evidence. | Don Buddenbaum | telemetry becomes available |
| `GAP-003` | limitation | All per-GiB network prices are zero. | `networkCost` cannot rank workloads by monetary network charge. | Don Buddenbaum | provider adopts usage pricing |
| `GAP-004` | methodology risk | Rolling `24h` windows are not comparable across execution times. | False cost-change conclusions. | Operator | every comparative report |
| `GAP-005` | allocation-policy risk | Weighted sharing concentrates cost on dominant non-shared workloads such as MinIO. | Showback may be mechanically correct but strategically unhelpful. | Don Buddenbaum | before chargeback/showback adoption |
| `GAP-006` | technical-debt | `__unmounted__` receives cost and shared allocation. | Some storage remains unattributed. | Storage/Kubecost owner | investigate before acceptance |
| `GAP-007` | limitation | Blended CPU/RAM/storage rates hide node-specific economics. | ARM-versus-Intel marginal comparison is limited. | Kalaxy3 architecture | platform comparison phase |
| `GAP-008` | assumption | Power values are estimates or UPS allocations, not per-device continuous measurements. | Energy and sustainability conclusions have medium confidence. | Don Buddenbaum | power metering introduced |
| `GAP-009` | limitation | GPU custom price remains zero and GPU scheduling is not validated. | GPU workloads cannot be separately costed. | Kalaxy3 architecture | Kubernetes GPU enablement |
| `GAP-010` | limitation | All nodes use one hardcoded region and zone. | No physical failure-domain or routed-zone distinction. | Kalaxy3 architecture | multi-site or multi-zone expansion |
| `GAP-012` | governance gap | Independent reviewer is pending. | Record cannot be `accepted`. | Kalaxy3 architecture | SAGE review |
| `GAP-013` | evidence-gap | Final Ansible, Helm, and `kubernetes.core` versions were not captured. | Reproduction may vary after tool upgrades. | Don Buddenbaum | next validation |
| `GAP-014` | evidence-gap | Full raw logs and generated values were not durably archived at collection time. | Some exact output context is unavailable. | Don Buddenbaum | next evidence capture |
| `GAP-015` | evidence-gap | No stable weekly or monthly baseline has been collected. | Current values may reflect transient workload activity. | FinOps owner | after 7- and 30-day windows |
| `GAP-016` | limitation | Monthly proration uses `730` average hours. | Small difference from calendar-specific month lengths. | FinOps owner | accounting-grade reporting |
| `GAP-017` | compatibility risk | `shareCost` behavior is validated for the current version only. | Upgrade may alter semantics or precision. | Kubecost owner | every chart upgrade |
| `GAP-018` | evidence-gap | Post-final-rollout PVC and Longhorn replica health were not recaptured. | Storage continuity is inferred, not freshly proven. | Storage owner | before acceptance |
| `GAP-019` | performance gap | Network collector CPU/RAM overhead was not benchmarked. | Collector impact on small ARM nodes is unknown. | Observability owner | capacity review |
| `GAP-020` | data-quality risk | Namespace classification policy may change as workloads are added. | Shared/non-shared allocation can drift from intent. | FinOps owner | namespace or platform change |

## Troubleshooting

### Network-cost Helm upgrade fails on affinity

**Meaning**

The rendered value is not a valid Kubernetes affinity object.

**Checks**

```bash
helm template kubecost \
  oci://public.ecr.aws/kubecost/kubecost \
  --version 3.2.1 \
  -n kubecost \
  -f <base-values> \
  -f /tmp/kalaxy3-kubecost-calibration-values.yaml |
grep -n -A20 -B5 'affinity:'
```

**Recovery**

Restore the structured Linux affinity in the Jinja template and rerun Ansible.

### Collectors report missing region

**Meaning**

Nodes lack topology labels required for classification.

**Checks**

```bash
kubectl get nodes \
  -L topology.kubernetes.io/region,topology.kubernetes.io/zone

kubectl logs \
  -n kubecost \
  daemonset/kubecost-network-costs \
  --tail=200
```

**Recovery**

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true

kubectl rollout restart \
  daemonset/kubecost-network-costs \
  -n kubecost
```

### Network bytes exist but network cost is zero

**Meaning**

This is the accepted design when unit prices are zero.

**Checks**

```bash
helm get values kubecost \
  -n kubecost \
  -o json |
jq '.finopsagent.agent.kubecost.customPrices'
```

**Recovery**

No recovery is required unless the provider pricing model changes. Do not invent a per-GiB price for a fixed bill.

### Fully burdened total appears lower after adding overhead

**Meaning**

The compared queries likely used different rolling windows.

**Checks**

Print exact windows and compare the underlying raw allocation.

**Recovery**

Use one explicit fixed RFC3339 start/end window for both `shareCost` values.

### `sharedCost` appears much larger than the daily ISP amount

**Meaning**

`sharedCost` includes redistributed idle and shared-namespace costs in addition to fixed provider cost.

**Checks**

Run the same fixed window with two `shareCost` values and subtract totals.

**Recovery**

Report the provider-attributable delta rather than treating all `sharedCost` as ISP cost.

### MinIO receives nearly all fully burdened cost

**Meaning**

MinIO is the dominant non-shared workload under weighted splitting.

**Checks**

Compare raw non-shared usage and review `sharedNamespaces`.

**Recovery**

Review policy. Compare even splitting, explicit business units, or label-based reports, but do not change policy solely to make results look balanced.

### `__unmounted__` appears

**Meaning**

Kubecost sees storage cost not attributed to a mounted workload allocation.

**Checks**

```bash
kubectl get pv,pvc -A -o wide
```

Review deleted workloads, detached Longhorn volumes, storage classes, and allocation metadata.

**Recovery**

Correct ownership or clean up only after confirming no retained data is required. Do not hide the namespace from evidence.

### Ansible reports changes on every run

**Meaning**

Potential causes include rendered-value drift, missing Helm Diff, unstable command output, or chart-generated changes.

**Checks**

```bash
helm plugin list
git diff --check
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true \
  --check
```

**Recovery**

Restore the pinned Helm Diff plugin, compare rendered values, and inspect the Helm diff before applying.

## Freshness, revalidation, and supersession

### Revalidate when

- Kubecost chart, network-cost image, FinOps Agent, K3s, Helm, Helm Diff, Ansible, or `kubernetes.core` changes;
- any custom-price chart path changes;
- the Allocation API changes;
- the provider bill or `$20.00/month` allocation changes;
- electricity rate, hardware purchase price, residual value, useful life, or power estimate changes;
- a node is added, removed, replaced, or changes role;
- a new architecture, GPU, or storage class is introduced;
- the cluster spans another site, routed segment, region, or fault zone;
- shared namespace or split policy changes;
- `__unmounted__` cost grows materially;
- DaemonSet readiness is not `7/7/7`;
- collector classification errors return;
- fixed-window proration no longer matches the expected formula;
- Ansible no longer converges to `changed=0`;
- a conflicting or superseding SAGE record is accepted.

### Scheduled review

```text
Event-based, plus quarterly review of:
- provider allocation;
- shared namespace policy;
- idle percentage;
- __unmounted__ cost;
- cost-input freshness;
- 7-day and 30-day allocation baselines.
```

### Supersession rule

When replaced:

1. keep this evidence ID permanent;
2. set `status: superseded`;
3. populate `superseded_by`;
4. state which claims remain valid;
5. preserve failed-path evidence;
6. link the new implementation commit and revalidation evidence;
7. do not delete historical cost values solely because newer values exist.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Status reflects technical validation without claiming review acceptance.
- [x] Owner, author, operator, and reviewer state are identified.
- [x] Five Ws and How are complete.
- [x] Scope, exclusions, and nonclaims are explicit.
- [x] Implementation commit is recorded.
- [x] Relationships and supersession fields are populated.

### Evidence

- [x] Every critical technical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Failed attempts are separated from the accepted final state.
- [x] Direct observations and repository evidence agree.
- [x] Fixed-window provider proration is proven.
- [x] Network byte measurement is proven.
- [x] Idempotency is proven.
- [x] Assumptions and limitations are explicit.
- [ ] Full original logs are archived with original checksums.
- [ ] Post-final-rollout PVC and Longhorn replica health are recaptured.
- [ ] 7-day and 30-day baselines are captured.

### Safety and operations

- [x] Secrets and sensitive values are excluded.
- [x] Internal metadata is classified.
- [x] Rollback and rebuild are documented.
- [x] Health checks and troubleshooting are documented.
- [x] Risks and gaps have owners or triggers.
- [x] Revalidation and supersession rules are defined.

### SAGE quality score

| Category | Score | Maximum | Notes |
|---|---:|---:|---|
| Five Ws and How | 15 | 15 | Complete |
| Final claim and scope | 10 | 10 | Complete |
| Claim-to-evidence traceability | 15 | 15 | Complete |
| Direct observed evidence | 9 | 10 | Full original logs not durably archived |
| Repository and commit lineage | 10 | 10 | Source paths and implementation commit complete |
| Reproducible implementation and rebuild | 10 | 10 | Complete |
| Acceptance and functional tests | 10 | 10 | Technical tests complete |
| Idempotency or repeatability | 5 | 5 | Proven |
| Security and data handling | 5 | 5 | Complete |
| Risks, limitations, and assumptions | 5 | 5 | Complete |
| Freshness and supersession | 5 | 5 | Complete |
| **Total** | **99** | **100** | SAGE-grade technical record; reviewer acceptance pending |

A high score does not override lifecycle state. The record remains `validated` until commit and reviewer acceptance are recorded.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | pending | pending | Confirm provider allocation policy, shared namespace policy, and residual gaps. |
| Reviewer | pending | pending | pending | Verify claim/evidence traceability and implementation commit. |

## Git review and publication

From the repository root:

```bash
cd ~/dvlp/Kalaxy3

git diff --check
git status --short

git diff -- \
  infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml \
  infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2 \
  markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md \
  markdown/evidence-artifacts/SAGE-K3-FINOPS-20260724-001/terminal-evidence-20260725.md
```

Stage only intended files:

```bash
git add -- \
  infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml \
  infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2 \
  markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md \
  markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md.sha256 \
  markdown/evidence-artifacts/SAGE-K3-FINOPS-20260724-001/terminal-evidence-20260725.md
```

Validate the staged change:

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Commit and publish:

```bash
git commit -m "Validate Kubecost network and provider cost allocation"
git pull --rebase origin main
git push origin main
git status
```

After the implementation commit:

1. confirm `implementation_commit` equals `d1d1339b4a3e54030f39bb0900e8e0934aa445c7`;
2. regenerate and verify the SHA-256 file;
3. commit the evidence record and terminal artifact;
4. complete owner and reviewer decisions when reviewed.

## Appendices and linked raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| SAGE evidence record | `markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md` | companion `.sha256` file | internal topology and cost metadata; no secrets | repository history |
| Consolidated terminal evidence | `markdown/evidence-artifacts/SAGE-K3-FINOPS-20260724-001/terminal-evidence-20260725.md` | calculate after placement if required | internal hostnames, paths, IPs, costs; no secrets observed | repository history |
| Rendered calibration values | `/tmp/kalaxy3-kubecost-calibration-values.yaml` | not retained in final sequence | internal configuration; no secret observed | temporary |
| Raw allocation output | `/tmp/kubecost-allocation-namespace.json` | not captured | internal cost and namespace metadata | temporary |
| Fully burdened provider output | `/tmp/kubecost-fully-burdened-provider.json` | not captured | internal cost and namespace metadata | temporary |
| Fixed-window old-overhead output | `/tmp/kubecost-overhead-8.41.json` | not captured | internal cost and namespace metadata | temporary |
| Fixed-window new-overhead output | `/tmp/kubecost-overhead-28.41.json` | not captured | internal cost and namespace metadata | temporary |

### Cost formulas and interpretation

#### Node monthly cost

```text
monthly amortization =
  (purchase price - residual value) / useful life months

monthly electricity =
  average watts / 1000 × hours per month × electricity rate

monthly node cost =
  monthly amortization + monthly electricity + fixed monthly overhead
```

#### Blended CPU and RAM prices

```text
cluster monthly compute cost = sum(monthly cost of priced nodes)
CPU pool = cluster monthly compute cost × CPU cost share
RAM pool = cluster monthly compute cost × RAM cost share
CPU price = CPU pool / total priced CPU cores
RAM price = RAM pool / total priced GiB
```

#### Storage price

```text
monthly storage profile cost = amortization + electricity + fixed overhead
logical billable capacity = raw capacity / replication factor
storage price = total monthly storage cost / total logical billable GB
```

#### Shared overhead

```text
existing shared infrastructure power cost: $8.41/month
operator-selected ISP allocation:          $20.00/month
total sharedOverhead:                      $28.41/month
```

#### Fixed-window provider delta

```text
$20.00 × 24 hours / 730 hours = $0.657534
observed API delta:             $0.657530
rounding difference:            $0.000004
```

### Raw versus fully burdened allocation

**Raw allocation** preserves platform namespaces and idle cost separately. It is useful for understanding resource consumption and unused cluster capacity.

**Fully burdened allocation** can share idle cost, redistribute selected shared namespaces, add a fixed monthly share cost, and split those amounts according to policy.

Therefore:

```text
fully burdened total != raw application resource cost only
sharedCost != ISP cost only
```

The provider allocation is isolated by comparing identical fixed-window queries that differ only in `shareCost`.

### Why `__unmounted__` must remain visible

`__unmounted__` is evidence that some persistent-volume cost could not be associated with a mounted workload allocation. Hiding it would improve presentation while reducing accountability. Treat it as an exception queue:

1. identify the PV and storage class;
2. identify current or former PVC ownership;
3. determine whether storage is retained intentionally;
4. repair attribution or remove unused storage safely;
5. rerun the same fixed-window report.

### Why MinIO receives most shared cost

With `shareIdle=true`, platform namespaces designated as shared, and weighted splitting, Kubecost allocates shared amounts to remaining workloads according to weight. In the observed window, MinIO was overwhelmingly the largest non-shared workload, so it received approximately 99% of distributed shared cost. That is mechanically consistent with the chosen policy. It is not proof that MinIO caused the fixed ISP bill or that weighted splitting is the best business policy.

### Evidence boundary

The strongest supported statement is:

```text
Available repository and runtime evidence supports that Kalaxy3 Kubecost
measures pod-level network bytes, applies zero usage-based network rates,
prorates a $20.00 monthly provider allocation through shared cost, and
reconciles idempotently for the tested Kubecost 3.2.1 configuration.
```

The evidence does not support an accounting-certified total cost of ownership, provider billing reconciliation, or universal chargeback policy.
