---
evidence_id: SAGE-K3-FINOPS-20260724-001
schema_version: "1.0"
title: Kubecost Homelab Cost Calibration and Idempotent Helm Reconciliation
project: Kalaxy3
record_type: finops
status: validated
classification: internal
created_at: 2026-07-25T00:03:40-05:00
updated_at: 2026-07-25T00:03:40-05:00
valid_as_of: 2026-07-24
review_due: event-based
owner: Don Buddenbaum
author: ChatGPT, drafted from terminal evidence collected by Don Buddenbaum
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
components:
  - Kubecost 3.2.1
  - Ansible
  - Helm
  - Helm Diff 3.15.10
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
  - longhorn-system
  - kube-system
  - observability
  - metallb-system
  - storage
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: pending
record_path: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md
confidence: medium
tags:
  - sage
  - finops
  - kubecost
  - cost-calibration
  - ansible
  - helm
  - idempotency
  - power-accounting
relationships:
  verifies:
    - Kalaxy3 Kubecost custom-pricing calibration
    - Idempotent Kubecost Helm reconciliation
    - Persistent Kalaxy3 node cost metadata
  depends_on:
    - markdown/installation/kalaxy3-kubecost-installation-and-verification.md
    - markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md
  supersedes:
    - The uncalibrated custom-cost-model gap in markdown/installation/kalaxy3-kubecost-installation-and-verification.md
  superseded_by:
    - none
  related_to:
    - markdown/installation/kalaxy3-observability-and-kubecost.md
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
  conflicts_with:
    - none known
  generated_by:
    - infrastructure/k3s-homelab/playbooks/kubecost-calibration-only.yml
    - infrastructure/k3s-homelab/playbooks/platform.yml
    - ChatGPT evidence-record generation from captured terminal output
---

# Kubecost Homelab Cost Calibration and Idempotent Helm Reconciliation

## Executive summary

Kalaxy3 Kubecost 3.2.1 was changed from an installed but uncalibrated state to a
validated homelab cost model driven by version-controlled node, storage, power,
and shared-infrastructure inputs. Ansible now calculates blended monthly CPU,
RAM, and storage rates, renders Kubecost custom pricing, applies persistent
hardware and cost-profile labels to all seven Kubernetes nodes, includes shared
infrastructure power as monthly overhead, and reconciles the Helm release using
the idempotent `kubernetes.core.helm` module with Helm Diff 3.15.10. The live
release is deployed and healthy, all four Kubecost workloads run on `amd64-02`,
and the final steady-state Ansible run completed with `changed=0` and
`failed=0`. This record is `validated`; acceptance remains pending because the
implementation commit and independent review have not yet been recorded.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Owner and operator:** Don Buddenbaum. **Evidence-record author:** ChatGPT, using terminal evidence supplied by Don Buddenbaum. **Reviewer:** pending. **Affected users:** the Kalaxy3 operator and future users of Kubecost engineering-cost evidence. |
| **What** | Added an inventory-driven Kubecost cost-calibration model; persistent node metadata; shared-power allocation; generated custom CPU, RAM, storage, GPU, network, and shared-overhead values; tagged Kubecost-only Ansible execution; idempotent Helm management; and Helm Diff installation. Applied the calibrated values to the live Kubecost release. |
| **When** | **Implementation and evidence collection:** July 24, 2026, approximately 22:08-23:40 CDT (`UTC-05:00`). **Final idempotency proof:** July 24, 2026 at approximately 23:38 CDT. **Record created:** July 25, 2026 at 00:03:40 CDT. **Valid as of:** July 24, 2026. **Review due:** on material hardware, power, electricity-rate, storage, Kubecost-chart, or calibration-code change. |
| **Where** | **Environment:** Kalaxy3 homelab. **Cluster:** `kalaxy3`. **Execution host:** `donb-mac-mini`. **Ansible/Helm controller:** `arm64-01`. **Kubecost workload node:** `amd64-02`. **Namespace:** `kubecost`. **Frontend address:** `192.168.2.26`. **Repository:** `donb4iu/Kalaxy3`, branch `main`. **Source paths:** `infrastructure/k3s-homelab/inventory`, `playbooks`, and `playbooks/templates`. |
| **Why** | Kubecost was healthy but its custom prices were disabled and empty, so it could not represent Kalaxy3 hardware amortization, electricity, storage, or shared-infrastructure cost. The roadmap requires useful engineering-cost evidence to compare low-power ARM and Intel platforms and guide architecture decisions. The model also had to be rebuildable, reviewable, and idempotent rather than maintained through manual UI changes. |
| **How** | Hardware, lifecycle, storage, and power inputs were stored in Ansible inventory; calibration tasks validate and aggregate those inputs; a Jinja template renders Kubecost values; node labels are reconciled with `kubectl label --overwrite`; the observability phase discovers eligible Kubecost nodes; and `kubernetes.core.helm` applies the base and calibration values. Helm Diff 3.15.10 provides reliable change detection. Validation included syntax checks, rendered-value inspection, live Helm-value inspection, node-label verification, workload health, normal rollout events, Helm release status, and a final no-change reconciliation. |

### Five-W completeness gate

- [x] Who is complete.
- [x] What is complete.
- [x] When is complete and includes timezone.
- [x] Where is complete at both repository and runtime levels.
- [x] Why includes rationale and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- The Kalaxy3 homelab Kubecost custom-pricing model.
- Seven priced Kubernetes nodes: five Raspberry Pi 4 nodes and two Intel nodes.
- Hardware amortization, electricity allocation, logical storage cost, and
  shared-infrastructure electricity.
- Persistent Kubernetes labels describing hardware class, cost profile, node
  role, power class, storage role, and GPU metadata.
- Generated Helm values and live Kubecost reconciliation.
- Ansible tag behavior required for Kubecost-only execution.
- Idempotent Helm management and Helm Diff installation.
- The material failed attempts that led to the accepted implementation.

### Out of scope

- Utility-bill reconciliation or accounting-grade cost certification.
- Direct per-device power-meter measurements.
- AWS, Azure, or other public-cloud billing integration.
- GPU scheduling or GPU cost allocation to Kubernetes workloads.
- Nonzero internet, region, or zone network-egress pricing.
- Historical validation of Kubecost allocation reports after a full reporting
  window.
- Commit and push of the implementation and this evidence record.
- Independent architecture or FinOps review.

### Nonclaims

This record does **not** claim:

- that the current power allocations are precision electrical measurements;
- that the blended cluster-wide rates represent distinct per-node marginal
  prices;
- that Kubecost results have been reconciled to an electric bill or purchase
  ledger;
- that GPUs are available to Kubernetes or separately priced;
- that zero network-egress rates mean network traffic has no operational cost;
- that Helm revision numbers 4 through 6 were failed releases; they were
  intermediate successful reconciliations during idempotency correction;
- that the implementation is accepted governance policy before review and Git
  lineage are completed.

## Final accepted state

```text
Kubecost chart:                 3.2.1
Helm status:                    deployed
Final observed Helm revision:   7
CPU custom price:               0.95500000 per core-month
RAM custom price:               0.12074713 per GiB-month
GPU custom price:               0.00000000
Storage custom price:           0.00076190 per GB-month
Shared overhead:                8.41 per month
Network-cost component:         enabled
Network egress rates:           0.0
Kubecost workload placement:    amd64-02
Kubecost pods ready:            4 of 4
Kubecost pod restarts:          0
Helm Diff version:              3.15.10
Steady-state Ansible result:    ok=30 changed=0 failed=0
Implementation commit:          pending
Reviewer:                       pending
```

| Item | Accepted result |
|---|---|
| Custom pricing | Enabled in the live Kubecost release. |
| CPU price | `0.95500000` per core-month. |
| RAM price | `0.12074713` per GiB-month. |
| Storage price | `0.00076190` per logical GB-month. |
| GPU price | `0.00000000`; GPU scheduling and separate GPU pricing remain disabled. |
| Shared overhead | `$8.41` per month, derived from `72 W`, `730` hours/month, and `$0.16/kWh`. |
| Network costs | Component enabled with on-prem affinity override; all configured egress rates remain `0.0`. |
| Node metadata | All seven nodes carry persistent Kalaxy3 hardware and cost labels. |
| Workload health | Aggregator, FinOps Agent, frontend, and local store are ready on `amd64-02` with zero restarts. |
| Helm reconciliation | Managed by `kubernetes.core.helm`; Helm Diff 3.15.10 prevents false-positive changes. |
| Repeatability | Final targeted run completed with `changed=0` and did not require a new Helm revision. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The calibration inputs are populated and pass Ansible validation for all seven priced nodes and four storage profiles. | high | `EV-001`, `EV-002` | supported | high |
| `CLM-002` | The generated Kubecost values contain the intended CPU, RAM, storage, GPU, shared-overhead, and network settings with correct YAML types. | critical | `EV-003` | supported | high |
| `CLM-003` | The live Kubecost release uses the generated custom prices and shared overhead. | critical | `EV-004` | supported | high |
| `CLM-004` | Persistent Kalaxy3 node labels describe all seven nodes and survive repeat reconciliation. | high | `EV-005`, `EV-008` | supported | high |
| `CLM-005` | Kubecost remained healthy after the calibrated rollout and all workloads ran on `amd64-02`. | critical | `EV-006` | supported | high |
| `CLM-006` | Kubecost-only Ansible execution now reaches the required eligibility, calibration, and Helm tasks. | high | `EV-007` | supported | high |
| `CLM-007` | Helm reconciliation is idempotent after installing Helm Diff 3.15.10. | critical | `EV-008`, `EV-009` | supported | high |
| `CLM-008` | The power and shared-cost inputs are useful engineering estimates but are not precision measurements. | high | `EV-001`, `EV-010` | supported | medium |
| `CLM-009` | The implementation is ready for Git commit but the commit SHA and review are not yet available. | normal | `EV-011` | partially-supported | high |

## Problem and decision rationale

### Problem or opportunity

Before this work, the installed Kubecost release was healthy but the effective
Helm values showed:

```yaml
customPrices:
  CPU: ""
  GPU: ""
  RAM: ""
  enabled: false
  storage: ""

sharedNamespaces: ""
sharedOverhead: 0

networkCosts:
  enabled: false
```

Kubecost could therefore report Kubernetes allocation and relative utilization,
but it did not have Kalaxy3-specific dollar values for hardware amortization,
electricity, storage, or shared infrastructure. This was a direct gap against
the Kalaxy3 roadmap requirement to produce useful engineering cost evidence
before comparing future control-plane and compute platforms.

### Decision

Use Ansible inventory as the source of truth for Kalaxy3 cost inputs, calculate
blended cluster-wide Kubecost rates deterministically, render those rates into a
separate Helm values file, and apply the values through an idempotent Helm
module. Keep provisional power assumptions explicit and separate from directly
observed runtime evidence.

### Decision drivers

- Rebuildability from Git and Ansible.
- Traceability from hardware assumptions to generated prices.
- Explicit validation of missing or malformed values.
- No dependence on manual Kubecost UI configuration.
- Compatibility with the existing Kubecost 3.2.1 deployment.
- Ability to refine purchase, residual, power, and lifecycle assumptions later
  without rewriting the deployment workflow.
- Persistent node metadata for architecture, capacity, storage, and future
  FinOps grouping.
- True Ansible and Helm idempotency.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Leave custom pricing disabled | No additional implementation work | Kubecost cannot provide Kalaxy3-specific dollar evidence | rejected |
| Maintain prices manually in the Kubecost UI | Fast initial entry | Not rebuildable, not reviewable in Git, and vulnerable to drift | rejected |
| Patch Kubecost pricing ConfigMaps directly | Direct runtime control | Conflicts with Helm ownership and had already produced invalid-field behavior in earlier work | rejected |
| Use public-cloud list prices | Easy external reference | Does not represent owned homelab hardware, residual values, or local electricity | rejected |
| Measure every device with dedicated power meters | Highest measurement quality | Additional hardware and collection process were not available during this work | deferred |
| Use shell `helm upgrade` with forced `changed_when: true` | Familiar and simple | Every run reports changed and creates unnecessary revisions | rejected |
| Use `kubernetes.core.helm` without Helm Diff | Declarative module | Module warned that default idempotency detection could still report false changes | superseded |
| Use `kubernetes.core.helm` with Helm Diff 3.15.10 | Declarative, version-pinned, and idempotent | Adds a managed Helm plugin dependency | accepted |

### Tradeoffs and consequences

- The model is transparent and reproducible but depends on the quality of its
  inventory assumptions.
- Blended prices fit the current deployment but hide per-node cost differences.
- Shared overhead captures non-Kubernetes infrastructure without falsely
  assigning it to a single node, but the allocation is approximate.
- GPU hardware is included in whole-node acquisition and power assumptions,
  while separate GPU pricing remains zero because Kubernetes GPU scheduling is
  not enabled.
- Enabling the network-cost component improves future visibility, but configured
  egress rates remain zero and therefore do not create dollar network charges.
- Applying Helm values restarted Kubecost workloads. The rollout was healthy,
  but reconciliation should still be treated as a controlled operational
  change.

## Architecture or change description

```text
Version-controlled cost inputs

inventory/group_vars/all/kubecost-calibration.yml
inventory/host_vars/arm64-01.yml ... arm64-05.yml
inventory/host_vars/amd64-01.yml ... amd64-02.yml
                 |
                 v
playbooks/tasks/kubecost-calibration.yml
  - validate node and storage inputs
  - aggregate monthly compute cost
  - aggregate logical storage cost
  - calculate blended CPU/RAM/storage prices
  - calculate shared monthly overhead
  - apply persistent node labels
                 |
                 v
/tmp/kalaxy3-kubecost-calibration-values.yaml
                 |
      base values + calibration values
                 |
                 v
kubernetes.core.helm + Helm Diff 3.15.10
                 |
                 v
Kubecost release in namespace kubecost
  - aggregator      -> amd64-02
  - finopsagent     -> amd64-02
  - frontend        -> amd64-02
  - local-store     -> amd64-02
  - Longhorn-backed persistent storage
  - MetalLB frontend address 192.168.2.26
```

### Before

- Custom prices were disabled and empty.
- Shared namespaces were empty and shared overhead was zero.
- Network costs were disabled.
- Cost metadata and power inputs were not consistently represented for all
  nodes.
- Targeted `--tags kubecost` execution initially did not reach the complete task
  chain.
- The Helm command always reported changed.

### After

- Inventory contains node, storage, power, lifecycle, residual-value, and label
  inputs.
- Calibration tasks validate and calculate all required Kubecost values.
- Custom pricing is enabled in the live release.
- Shared namespaces and `$8.41` monthly shared overhead are configured.
- Network-cost collection is enabled with an on-prem affinity override.
- Persistent labels are present on all seven nodes.
- Targeted Kubecost runs execute only the required observability subpath.
- Helm Diff provides a no-change steady state.

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
```

The original global variable file was moved so Ansible could load multiple
files for the `all` group without a file/directory collision:

```text
inventory/group_vars/all.yml
  -> inventory/group_vars/all/main.yml
```

### Implementation commit

```text
Pending. The working tree contained the intended Kubecost calibration changes,
but no commit SHA was captured before this record was generated.
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| Kubecost chart | `3.2.1` | `oci://public.ecr.aws/kubecost/kubecost` |
| Helm Diff | `3.15.10` | `https://github.com/databus23/helm-diff` |
| K3s/Kubernetes | `v1.36.2+k3s1` | observed node output |
| FinOps Agent image | `v1.0.20` | `icr.io/ibm-finops/agent` from existing Kubecost base values |
| Ansible | not captured | evidence gap |
| Helm client | not captured | evidence gap |
| `kubernetes.core` collection | not captured | evidence gap |

### Configuration excerpt

```yaml
kubecost_calibration:
  electricity_rate_usd_per_kwh: 0.16
  hours_per_month: 730

  compute:
    cpu_cost_share: 0.60
    ram_cost_share: 0.40
    fixed_monthly_overhead_usd: 0.00

  gpu:
    pricing_enabled: false

  shared:
    monthly_overhead_usd: 0.00
    average_watts: 72.00
    power_accounting:
      method: ups-load-allocation
      confidence: medium-low
      measured: false
      source_ups: cyberpower1500
      source_total_watts: 162.00
      raspberry_pi_nodes_watts: 90.00
      nfs_server_watts: 35.00
      switch_2_5gbe_watts: 10.00
      switch_10gbe_watts: 22.00
      hdmi_kvm_watts: 5.00
    namespaces:
      - kube-system
      - kubecost
      - longhorn-system
      - metallb-system
      - observability
      - storage

  network:
    enabled: true
    internet_egress_usd_per_gb: 0.00
    region_egress_usd_per_gb: 0.00
    zone_egress_usd_per_gb: 0.00
```

Representative node power inputs:

```yaml
# arm64-01 through arm64-05
average_watts: 18

# amd64-01
average_watts: 92

# amd64-02
average_watts: 68
```

Representative storage inputs:

```yaml
longhorn:
  purchase_price_usd: 120.00
  residual_value_usd: 60.00
  useful_life_months: 60
  average_watts: 0.00
  raw_capacity_gb: 2000
  replication_factor: 2

minio_local:
  purchase_price_usd: 120.00
  residual_value_usd: 0.00
  useful_life_months: 60
  average_watts: 0.00
  raw_capacity_gb: 5000
  replication_factor: 1.25

nfs_ssd:
  purchase_price_usd: 120.00
  residual_value_usd: 60.00
  useful_life_months: 60
  average_watts: 0
  raw_capacity_gb: 1000
  replication_factor: 1

nfs_hdd:
  purchase_price_usd: 1000.00
  residual_value_usd: 600.00
  useful_life_months: 60
  average_watts: 0
  raw_capacity_gb: 8000
  replication_factor: 1
```

Generated values excerpt:

```yaml
finopsagent:
  kubecost:
    customPrices:
      enabled: true
      CPU: "0.95500000"
      RAM: "0.12074713"
      GPU: "0.00000000"
      storage: "0.00076190"
      spotCPU: "0.95500000"
      spotRAM: "0.12074713"
      spotGPU: "0.00000000"
      zoneNetworkEgress: "0.0"
      regionNetworkEgress: "0.0"
      internetNetworkEgress: "0.0"

kubecostProductConfigs:
  sharedNamespaces: >-
    kube-system,kubecost,longhorn-system,metallb-system,observability,storage
  sharedOverhead: "8.41"

networkCosts:
  enabled: true
  affinity: {}
```

## Prerequisites and assumptions

### Proven prerequisites

- Kubecost 3.2.1 was already deployed in namespace `kubecost`.
- All Kubecost pods were already constrained to the eligible AMD64 node.
- Both Intel nodes and all five Pi nodes were `Ready`.
- Longhorn provided Kubecost persistent storage.
- `arm64-01` could execute Ansible, `kubectl`, and Helm against the cluster.
- Node and storage calibration records were populated sufficiently for all
  validation assertions to pass.
- The `kubernetes.core` collection was available because both
  `kubernetes.core.helm` and `kubernetes.core.helm_plugin` executed
  successfully.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The electricity rate is `$0.16/kWh`. | All electricity-derived costs are biased. | Replace with the current blended utility rate and rerun calibration. |
| `ASM-002` | `730` hours is an appropriate average month. | Small monthly cost variance. | Retain as an annualized average or use a reporting-period-specific hour count. |
| `ASM-003` | Five Pi systems consume an allocated `18 W` each, including attached boot and data enclosures. | ARM compute power cost is overstated or understated. | Measure each Pi system with a plug-level meter. |
| `ASM-004` | Intel UPS load can be allocated as `92 W` to `amd64-01` and `68 W` to `amd64-02`. | Intel blended compute cost is biased. | Capture per-node power under idle and representative load. |
| `ASM-005` | Shared rack power is reasonably represented by `72 W`. | Shared overhead is biased. | Measure NFS server, switches, and KVM independently. |
| `ASM-006` | Storage-device power is already included in node or shared allocations and must remain `0` in storage profiles to avoid double counting. | Cost is double counted or omitted. | Confirm electrical boundaries whenever storage hardware or UPS wiring changes. |
| `ASM-007` | Residual values and 60-month useful lives represent reasonable engineering depreciation assumptions. | Monthly amortization is biased. | Review against actual resale value and replacement history annually. |
| `ASM-008` | Separate GPU pricing should remain zero while GPUs are not Kubernetes-schedulable. | Future GPU workloads may be underallocated. | Enable GPU pricing only after the device plugin, scheduling, and workload requests are validated. |

The assumptions are material to dollar precision. They do not prevent the
technical deployment from being validated, but they keep the overall cost-model
confidence at `medium` rather than `high`.

## Implementation procedure

### Preparation

The existing live Helm state was backed up before applying calibration:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

mkdir -p /tmp/kalaxy3-kubecost-backup

if helm status kubecost -n kubecost >/dev/null 2>&1; then
  helm get values kubecost \
    -n kubecost \
    --all \
    > /tmp/kalaxy3-kubecost-backup/values-before-calibration.yaml

  helm status kubecost \
    -n kubecost \
    > /tmp/kalaxy3-kubecost-backup/status-before-calibration.txt
fi
```

The backup is operationally useful but temporary because `/tmp` is not a
durable evidence store.

### Calibration-only execution

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/kubecost-calibration-only.yml
```

This execution validated inputs, calculated prices, reconciled node labels, and
rendered:

```text
/tmp/kalaxy3-kubecost-calibration-values.yaml
```

It intentionally did not perform a live Helm upgrade.

### Rendered-value inspection

```bash
ansible arm64-01 \
  -i inventory/hosts.yml \
  --become \
  --module-name ansible.builtin.fetch \
  --args \
  "src=/tmp/kalaxy3-kubecost-calibration-values.yaml \
   dest=/tmp/kalaxy3-kubecost-calibration-values.yaml \
   flat=yes"
```

A Python YAML parse confirmed the generated values and the Boolean type of
`networkCosts.enabled`.

### Live execution

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

`install_kubecost=true` was provided as an execution-time override. The
inventory value remained `false` at the time of evidence capture.

### Expected change

- Validate all cost inputs.
- Render the same calibration values already inspected.
- Apply persistent node labels.
- Install Helm Diff when absent.
- Reconcile the Kubecost release.
- Restart workloads only when values materially changed.
- Converge with no changes on a later identical execution.

### Observed change

- The first accepted calibration-only run applied missing node labels and
  rendered the values file.
- The live release changed from uncalibrated values to calibrated values.
- Kubecost workloads rolled and returned to `Ready` on `amd64-02`.
- Helm Diff 3.15.10 was installed.
- The final identical run completed with `changed=0`.

## Evidence items

### `EV-001` — Node, storage, and power inputs populated

| Field | Value |
|---|---|
| Classification | `repository-evidence` and `direct-observation` |
| Supports or contradicts | `CLM-001`, `CLM-008` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 22:08-22:17 CDT |
| Execution source | `donb-mac-mini` |
| Target | Ansible inventory files |
| Tool and version | `grep`, version not captured |
| Expected result | Seven node watt values populated; no remaining null purchase or watt fields |
| Actual result | pass |
| Confidence | high for repository state; medium for power precision |
| Sensitive data | none |
| Artifact | inline terminal evidence and repository files |

**Commands**

```bash
grep -n 'average_watts' \
  inventory/host_vars/arm64-*.yml \
  inventory/host_vars/amd64-*.yml

grep -RniE \
  'purchase_price_usd: null|average_watts: null|average_incremental_watts: null' \
  inventory/host_vars \
  inventory/group_vars/all/kubecost-calibration.yml
```

**Observed result**

```text
inventory/host_vars/arm64-01.yml:5:  average_watts: 18
inventory/host_vars/arm64-02.yml:5:  average_watts: 18
inventory/host_vars/arm64-03.yml:5:  average_watts: 18
inventory/host_vars/arm64-04.yml:5:  average_watts: 18
inventory/host_vars/arm64-05.yml:5:  average_watts: 18
inventory/host_vars/amd64-01.yml:16:  average_watts: 92
inventory/host_vars/amd64-02.yml:11:  average_watts: 68
```

The null-value search returned no output.

**Interpretation**

This proves the repository had complete values for the fields guarded by the
search. It does not prove that the watt allocations are precision
measurements.

### `EV-002` — Calibration input validation and aggregation passed

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 22:43-22:47 CDT |
| Execution source | `donb-mac-mini`, targeting `arm64-01` |
| Target | Calibration-only Ansible workflow |
| Tool and version | Ansible, version not captured |
| Expected result | All seven nodes and four storage profiles validate and calculate |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Command**

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/kubecost-calibration-only.yml
```

**Observed result**

```text
TASK [Validate Kubecost allocation percentages]
ok: [arm64-01]
msg: All assertions passed

TASK [Validate Kubecost node cost inventory]
ok: [arm64-01] => (item=arm64-01)
ok: [arm64-01] => (item=arm64-02)
ok: [arm64-01] => (item=arm64-03)
ok: [arm64-01] => (item=arm64-04)
ok: [arm64-01] => (item=arm64-05)
ok: [arm64-01] => (item=amd64-01)
ok: [arm64-01] => (item=amd64-02)

TASK [Validate Kubecost storage profiles]
ok: [arm64-01] => (item=longhorn)
ok: [arm64-01] => (item=minio_local)
ok: [arm64-01] => (item=nfs_ssd)
ok: [arm64-01] => (item=nfs_hdd)

TASK [Calculate monthly storage totals]
ok: [arm64-01] => (item=longhorn)
ok: [arm64-01] => (item=minio_local)
ok: [arm64-01] => (item=nfs_ssd)
ok: [arm64-01] => (item=nfs_hdd)

TASK [Calculate Kubecost blended prices]
ok: [arm64-01]

TASK [Calculate Kubecost shared monthly overhead]
ok: [arm64-01]

TASK [Render calibrated Kubecost Helm values]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=24 changed=8 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

**Interpretation**

The first complete calibration run proved that the model could validate all
configured inputs and produce output. The `changed=8` result was expected
because labels and the rendered file were being established.

### `EV-003` — Generated custom prices and YAML type

| Field | Value |
|---|---|
| Classification | `generated-artifact` and `direct-observation` |
| Supports or contradicts | `CLM-002` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 22:57-22:58 CDT |
| Execution source | `donb-mac-mini`, fetched from `arm64-01` |
| Target | `/tmp/kalaxy3-kubecost-calibration-values.yaml` |
| Tool and version | Ansible fetch and Python/PyYAML, versions not captured |
| Expected result | Nonzero CPU, RAM, and storage prices; zero GPU; nonzero shared overhead; Boolean network flag |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | fetched file checksum `0f6842e2bb480a74a41bdae26124c1f227f81fa2` |

**Observed result**

```text
arm64-01 | SUCCESS =>
    changed: false
    checksum: 0f6842e2bb480a74a41bdae26124c1f227f81fa2
    dest: /tmp/kalaxy3-kubecost-calibration-values.yaml
    md5sum: 3dfee97b9a2f452d46c8f2cb8219f008

CPU: 0.95500000
RAM: 0.12074713
Storage: 0.00076190
GPU: 0.00000000
Shared overhead: 8.41
Network enabled: True bool
```

**Interpretation**

This proves the rendered file contained the intended values and that
`networkCosts.enabled` parsed as a Boolean rather than a string. It does not
prove Kubecost had yet consumed those values; live Helm evidence is separate.

### `EV-004` — Live Helm values and release status

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:15-23:40 CDT |
| Execution source | `donb-mac-mini` |
| Target | Helm release `kubecost` in namespace `kubecost` |
| Tool and version | Helm, client version not captured |
| Expected result | Deployed release with calibrated user-supplied values |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Commands**

```bash
helm status kubecost -n kubecost

helm get values kubecost \
  -n kubecost |
grep -A35 -E \
  'customPrices:|sharedNamespaces:|sharedOverhead:|networkCosts:'
```

**Observed result**

```text
NAME: kubecost
NAMESPACE: kubecost
STATUS: deployed
REVISION: 4
```

Immediately after the calibrated deployment, Helm user values showed:

```yaml
customPrices:
  CPU: "0.95500000"
  GPU: "0.00000000"
  RAM: "0.12074713"
  enabled: true
  internetNetworkEgress: "0.0"
  regionNetworkEgress: "0.0"
  spotCPU: "0.95500000"
  spotGPU: "0.00000000"
  spotRAM: "0.12074713"
  storage: "0.00076190"
  zoneNetworkEgress: "0.0"

sharedNamespaces: kube-system,kubecost,longhorn-system,metallb-system,observability,storage
sharedOverhead: "8.41"

networkCosts:
  affinity: {}
  enabled: true
```

After intermediate idempotency corrections, the final observed state was:

```text
LAST DEPLOYED: Fri Jul 24 23:29:46 2026
STATUS: deployed
REVISION: 7
```

**Interpretation**

This proves that the live release consumed the calibrated values. Revision 7 is
the accepted final release. Revisions 4 through 6 were created by successful
intermediate reconciliations while the Ansible Helm change-detection behavior
was being corrected.

### `EV-005` — Persistent node labels

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-004` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:00 CDT |
| Execution source | `donb-mac-mini` |
| Target | All Kalaxy3 Kubernetes nodes |
| Tool and version | `kubectl`, version not separately captured |
| Expected result | Correct hardware, cost, role, power, storage, and GPU labels |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Command**

```bash
kubectl get nodes \
  -L kalaxy3.io/hardware-class \
  -L kalaxy3.io/cost-profile \
  -L kalaxy3.io/node-role \
  -L kalaxy3.io/power-class \
  -L kalaxy3.io/storage-role \
  -L kalaxy3.io/gpu-model
```

**Observed result**

```text
NAME       HARDWARE-CLASS         COST-PROFILE        NODE-ROLE       POWER-CLASS     STORAGE-ROLE   GPU-MODEL
amd64-01   intel-i5-11600-128gb   amd64-high-memory   worker          high-capacity   longhorn       rtx-3090
amd64-02   intel-i5-11600-64gb    amd64-standard      worker          high-capacity   longhorn       rtx-3060-ti
arm64-01   raspberry-pi-4-8gb     arm64-low-power     control-plane   low-power       minio
arm64-02   raspberry-pi-4-8gb     arm64-low-power     control-plane   low-power       minio
arm64-03   raspberry-pi-4-8gb     arm64-low-power     control-plane   low-power       minio
arm64-04   raspberry-pi-4-8gb     arm64-low-power     worker          low-power       minio
arm64-05   raspberry-pi-4-8gb     arm64-low-power     worker          low-power       minio
```

**Interpretation**

This proves all seven nodes had the intended descriptive labels. The final
Ansible run later reported every label operation as `ok`, proving steady-state
convergence.

### `EV-006` — Healthy calibrated workload rollout

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:17 CDT |
| Execution source | `donb-mac-mini` |
| Target | Namespace `kubecost` |
| Tool and version | `kubectl`, version not separately captured |
| Expected result | Four ready workloads on `amd64-02`, zero restarts, no warning events |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Commands**

```bash
kubectl get pods \
  -n kubecost \
  -o wide

kubectl get deployments,statefulsets \
  -n kubecost

kubectl get events \
  -n kubecost \
  --sort-by='.lastTimestamp' |
tail -30
```

**Observed result**

```text
NAME                                    READY   STATUS    RESTARTS   NODE
kubecost-aggregator-0                   1/1     Running   0          amd64-02
kubecost-finopsagent-576777b756-d5f6p   1/1     Running   0          amd64-02
kubecost-frontend-67589b6bd4-ktdnf      1/1     Running   0          amd64-02
kubecost-local-store-7bdf4dbdc9-2nrpz   1/1     Running   0          amd64-02
```

```text
deployment.apps/kubecost-finopsagent   1/1
 deployment.apps/kubecost-frontend      1/1
 deployment.apps/kubecost-local-store   1/1
 statefulset.apps/kubecost-aggregator   1/1
```

The captured event tail contained normal rollout events such as
`SuccessfulCreate`, `Started`, `ScalingReplicaSet`, and MetalLB
`nodeAssigned`. No warning event was shown.

**Interpretation**

This proves the calibrated rollout recovered successfully, remained pinned to
`amd64-02`, and did not introduce immediate restart or readiness failures. It
does not prove long-duration stability or cost-report accuracy.

### `EV-007` — Kubecost-only tag path and variable loading

| Field | Value |
|---|---|
| Classification | `direct-observation` and `repository-evidence` |
| Supports or contradicts | `CLM-006` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:03-23:15 CDT |
| Execution source | `donb-mac-mini` |
| Target | `playbooks/platform.yml` and `playbooks/tasks/observability.yml` |
| Tool and version | Ansible, version not captured |
| Expected result | Targeted run reaches eligibility, calibration, and Helm tasks |
| Actual result | pass after corrective changes |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence and repository files |

**Observed task sequence**

```text
TASK [Run observability phase]
included: .../playbooks/tasks/observability.yml for arm64-01

TASK [Find eligible Kubecost Intel nodes]
ok: [arm64-01]

TASK [Prepare calibrated Kubecost pricing]
included: .../playbooks/tasks/kubecost-calibration.yml for arm64-01

TASK [Install Kubecost]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=29 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

**Interpretation**

This proves the targeted `--tags kubecost` command executes the full required
path. The parent observability include and the eligibility task both require the
`kubecost` tag because `include_tasks` is dynamic.

### `EV-008` — Helm Diff installation and Helm idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-004`, `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:29-23:35 CDT |
| Execution source | `donb-mac-mini`, targeting `arm64-01` |
| Target | Helm plugin installation and Kubecost release |
| Tool and version | Helm Diff 3.15.10 |
| Expected result | Plugin installed once; unchanged Kubecost release reports `ok` |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Observed result**

```text
TASK [Install Helm Diff plugin]
changed: [arm64-01]

TASK [Install Kubecost]
ok: [arm64-01]

PLAY RECAP
arm64-01 : ok=30 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

Version verification:

```text
arm64-01 | CHANGED | rc=0 >>
3.15.10
```

The ad-hoc Ansible `command` task reported `CHANGED` because the command module
assumes a command changes state unless told otherwise. The command itself only
printed the plugin version.

**Interpretation**

This proves Helm Diff 3.15.10 was available on the same controller where Helm
reconciliation runs, and the Helm module already recognized that Kubecost did
not need another upgrade.

### `EV-009` — Final steady-state no-change reconciliation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:35-23:38 CDT |
| Execution source | `donb-mac-mini`, targeting `arm64-01` |
| Target | Complete tagged Kubecost workflow |
| Tool and version | Ansible, version not captured; Helm Diff 3.15.10 |
| Expected result | No changed tasks and no failure |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Command**

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

**Observed result**

```text
TASK [Install Helm Diff plugin]
ok: [arm64-01]

TASK [Install Kubecost]
ok: [arm64-01]

PLAY RECAP
arm64-01 : ok=30 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

All node-label operations, calculations, rendered values, plugin state, and the
Helm release were also reported as `ok`.

**Interpretation**

This is the final idempotency proof. It demonstrates that the complete targeted
workflow converges without modifying the cluster or creating another Helm
revision when source inputs and runtime state already match.

### `EV-010` — Derived shared-power and monthly-overhead calculation

| Field | Value |
|---|---|
| Classification | `derived-conclusion` |
| Supports or contradicts | `CLM-008` |
| Collected by | Ansible calibration logic |
| Collected at | 2026-07-24 22:47-22:58 CDT |
| Execution source | `arm64-01` |
| Target | Shared-infrastructure cost model |
| Tool and version | Ansible/Jinja, versions not captured |
| Expected result | Shared power converts to a deterministic monthly amount |
| Actual result | pass |
| Confidence | medium |
| Sensitive data | none |
| Artifact | generated values file |

**Calculation**

```text
Shared power:       72 W
Hours per month:   730 h
Electricity rate:  $0.16/kWh

72 * 730 * 0.16 / 1000 = 8.4096
Rendered monthly shared overhead = 8.41
```

A broader derived monthly model using the declared aggregate capacities is:

```text
CPU:      44 cores * 0.95500000          = 42.02
RAM:     232 GiB   * 0.12074713          = 28.01333416
Storage: 14,000 GB * 0.00076190          = 10.6666
Shared:                                     8.4096
                                            -----------
Derived modeled total:                     89.10953416/month
Rounded modeled total:                     89.11/month
```

**Interpretation**

The arithmetic is deterministic, but the result inherits the uncertainty of
purchase, useful-life, residual-value, and power assumptions. It is suitable
for engineering comparison and trend evidence, not accounting certification.

### `EV-011` — Repository state before commit

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-009` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 23:40-23:41 CDT |
| Execution source | `donb-mac-mini` |
| Target | Git working tree |
| Tool and version | Git, version not captured |
| Expected result | Intended files visible and unrelated PDF unstaged |
| Actual result | partial; files existed but were not yet fully staged or committed |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline terminal evidence |

**Observed result**

```text
 M inventory/group_vars/all/kubecost-calibration.yml
R  inventory/group_vars/all.yml -> inventory/group_vars/all/main.yml
 M inventory/host_vars/amd64-01.yml
 M inventory/host_vars/amd64-02.yml
 M inventory/host_vars/arm64-01.yml
 M inventory/host_vars/arm64-02.yml
 M inventory/host_vars/arm64-03.yml
 M inventory/host_vars/arm64-04.yml
 M inventory/host_vars/arm64-05.yml
 M playbooks/platform.yml
 M playbooks/tasks/kubecost-calibration.yml
 M playbooks/tasks/kubecost-node-label.yml
 M playbooks/tasks/observability.yml
 M playbooks/templates/kubecost-calibration-values.yml.j2
?? playbooks/kubecost-calibration-only.yml
?? ../../markdown/research/kubecost-on-aws-dev-account-kindle.pdf
```

**Interpretation**

The implementation files were present in the working tree. The unrelated PDF
was untracked and must not be staged with this evidence record. No implementation
commit was captured, so repository lineage remains incomplete.

### `EV-012` — Negative evidence and failed-attempt chronology

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | Troubleshooting and design rationale |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-24 22:35-23:29 CDT |
| Execution source | `donb-mac-mini` and `arm64-01` |
| Target | Calibration and deployment workflow |
| Tool and version | Ansible, Helm, kubectl; versions partially captured |
| Expected result | Failures identify incomplete task ordering, loop handling, tags, and idempotency dependencies |
| Actual result | informative; each failure was corrected |
| Confidence | high |
| Sensitive data | none |
| Artifact | inline excerpts below |

**Observed failures and accepted corrections**

1. **Compute accumulator was undefined**

   ```text
   'kubecost_compute_monthly_usd' is undefined
   ```

   Correction: initialize compute totals before the node loop.

2. **Outer and inner loops both used `item`**

   ```text
   The variable 'item' is already in use.
   ```

   The malformed command passed a label dictionary as the node name.
   Correction: use `kubecost_node` for the outer loop and `kubecost_label` for
   the inner loop.

3. **Storage Jinja expression had invalid syntax**

   ```text
   Syntax error in template: expected token ')', got 'kubecost_calibration'
   ```

   Correction: replace the monthly storage calculation with explicit,
   independently parenthesized amortization, electricity, and logical-capacity
   expressions.

4. **Dynamic observability include was not tagged**

   The first targeted run performed only fact gathering:

   ```text
   PLAY RECAP
   arm64-01 : ok=1 changed=0 unreachable=0 failed=0
   ```

   Correction: add `observability` and `kubecost` tags to the parent dynamic
   include in `playbooks/platform.yml`.

5. **Global variables were split across a file and same-named directory**

   ```text
   'install_observability' is undefined
   ```

   Correction: move `inventory/group_vars/all.yml` to
   `inventory/group_vars/all/main.yml` so both global variable files load.

6. **Eligible-node discovery task was untagged**

   ```text
   'kubecost_eligible_nodes' is undefined
   ```

   Correction: add the `kubecost` tag to the task that registers
   `kubecost_eligible_nodes`.

7. **Imperative Helm command forced every run to report changed**

   Correction: replace it with `kubernetes.core.helm`.

8. **Helm module lacked reliable diff support**

   ```text
   The default idempotency check can fail to report changes in certain cases.
   Install helm diff >= 3.4.1 for better results.
   ```

   Correction: manage Helm Diff `v3.15.10` through
   `kubernetes.core.helm_plugin`.

**Interpretation**

These failures are not part of the final accepted state. They provide causal
evidence for task ordering, variable layout, loop-variable isolation, dynamic
include tagging, and Helm Diff as required elements of the final design.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | All node and storage inputs validate | `EV-001`, `EV-002` | Seven nodes and four storage profiles pass assertions | All assertions passed | pass |
| `AC-002` | Generated values are complete and parse correctly | `EV-003` | Nonzero CPU/RAM/storage, zero GPU, shared overhead, Boolean network flag | Exact expected values observed; Boolean type confirmed | pass |
| `AC-003` | Live Helm release uses calibrated values | `EV-004` | `customPrices.enabled: true` and expected values | Values present in Helm user values | pass |
| `AC-004` | Node metadata is present on all nodes | `EV-005` | Seven nodes labeled according to hardware and role | All seven rows matched intended metadata | pass |
| `AC-005` | Kubecost remains healthy after rollout | `EV-006` | Four ready pods, zero restarts, correct node | Four ready pods on `amd64-02`, zero restarts | pass |
| `AC-006` | Targeted Kubecost run reaches all required tasks | `EV-007` | Eligibility, calibration, and install tasks execute | Required sequence observed | pass |
| `AC-007` | Helm reconciliation does not create false changes | `EV-008`, `EV-009` | Plugin installed; later install task reports `ok` | Helm Diff 3.15.10 installed; final run unchanged | pass |
| `AC-008` | Complete workflow is idempotent | `EV-009` | `changed=0`, `failed=0` | `ok=30 changed=0 failed=0` | pass |
| `AC-009` | Implementation is committed and traceable | `EV-011` | Git commit SHA recorded | Commit pending | not-run |
| `AC-010` | Independent review is recorded | front matter | Reviewer decision recorded | Reviewer pending | not-run |
| `AC-011` | Kubecost allocation UI/API reflects calibrated dollar totals after collection window | gap `GAP-003` | Reported allocation visibly uses custom prices | Not captured | not-run |

### Functional verification

```bash
kubectl get pods \
  -n kubecost \
  -o wide
```

Observed:

```text
kubecost-aggregator-0                   1/1 Running 0 amd64-02
kubecost-finopsagent-576777b756-d5f6p   1/1 Running 0 amd64-02
kubecost-frontend-67589b6bd4-ktdnf      1/1 Running 0 amd64-02
kubecost-local-store-7bdf4dbdc9-2nrpz   1/1 Running 0 amd64-02
```

### Negative verification

The final node-placement evidence showed no Kubecost workload on an ARM64 node.
The final event tail contained no warning events. The final Ansible execution
showed no changed or failed task.

```text
PLAY RECAP
arm64-01 : ok=30 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

## Idempotency and repeatability

### First accepted live run

```text
TASK [Install Kubecost]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=29 changed=1 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

This run applied the calibrated Helm values.

### Helm module without Helm Diff

```text
TASK [Install Kubecost]
changed: [arm64-01]

WARNING: The default idempotency check can fail to report changes in certain
cases. Install helm diff >= 3.4.1 for better results.
```

### Helm Diff installation run

```text
TASK [Install Helm Diff plugin]
changed: [arm64-01]

TASK [Install Kubecost]
ok: [arm64-01]
```

### Steady-state rerun

```text
TASK [Install Helm Diff plugin]
ok: [arm64-01]

TASK [Install Kubecost]
ok: [arm64-01]

PLAY RECAP
arm64-01 : ok=30 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

### Interpretation

The final automation is idempotent. Calculations, labels, rendered values,
plugin installation, and the Helm release all converge without changes. The
live Helm revision remained 7 after the final no-change run.

## Security, privacy, and evidence handling

### Security controls

- The calibration values contain no Kubernetes Secret values.
- The generated Helm values include cost and topology metadata only.
- Kubecost workloads remain pinned to explicitly eligible AMD64 nodes.
- The calibration workflow uses the existing K3s kubeconfig on `arm64-01` but
  does not record its contents.
- The evidence record is classified `internal` because it contains hostnames,
  internal IP addresses, hardware inventory, and cost assumptions.

### Sensitive material excluded

The record does not contain:

- kubeconfig contents;
- service-account tokens;
- passwords, private keys, or vault secrets;
- Kubernetes Secret manifests;
- UPS serial numbers;
- shell history unrelated to this implementation.

### Redactions and omissions

- Long terminal output was reduced to material task, error, value, health, and
  recap lines.
- Exact node acquisition prices are not repeated here because the captured
  terminal output did not include them; the inventory files remain the source
  of truth.
- The unrelated research PDF remained untracked and is intentionally excluded
  from the implementation commit scope.

### Residual security risk

- Kubecost frontend exposure and authentication controls are governed by
  separate installation/access evidence and were not revalidated in this work.
- Hardware and cost metadata can reveal internal capacity and should not be
  published outside the intended documentation boundary without review.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Missing or null cost input | Ansible assertion failure | Calibration stops before Helm | Populate the specific inventory field and rerun calibration-only playbook |
| Invalid Jinja expression | Ansible template finalization error | No rendered values | Correct the calculation block; run syntax check and calibration-only playbook |
| Loop-variable collision | Warning plus malformed `kubectl label` command | Labels fail | Use distinct `loop_var` names for node and label loops |
| Dynamic include not tagged | Targeted run lists or executes only parent/facts | Kubecost tasks skipped | Add `kubecost` tag to parent include and required child tasks |
| Global vars file/directory collision | Variables such as `install_observability` undefined | Targeted workflow fails | Keep all `all` variables under `inventory/group_vars/all/` |
| Eligible-node variable undefined | `kubecost_eligible_nodes` undefined | Calibration/install blocked | Tag the discovery task and verify it runs first |
| Helm false-positive change | Helm task reports changed on identical input | Unnecessary release revisions and pod restarts | Install and pin Helm Diff; use `kubernetes.core.helm` |
| Kubecost rollout failure | Pods not ready, warning events, Helm status failed | Cost reporting unavailable | Inspect pods/events/logs and roll back to a known-good revision |
| Power estimate becomes stale | Hardware or UPS wiring changes | Cost model becomes inaccurate | Update allocations and revalidate |

### Rollback

Review history before selecting a target:

```bash
helm history kubecost -n kubecost
```

Revision 3 was the last observed pre-calibration deployed release. A rollback
candidate is:

```bash
helm rollback kubecost 3 \
  -n kubecost \
  --wait \
  --timeout 30m
```

Then verify:

```bash
helm status kubecost -n kubecost
kubectl get pods -n kubecost -o wide
```

Rollback to revision 3 would intentionally remove the new custom prices,
shared overhead, and enabled network-cost settings. If later releases exist,
select the appropriate known-good revision from `helm history` instead of
blindly using revision 3.

### Rebuild procedure

1. Restore or clone the Kalaxy3 repository.
2. Confirm the global variable layout:

   ```text
   inventory/group_vars/all/main.yml
   inventory/group_vars/all/kubecost-calibration.yml
   ```

3. Confirm host cost metadata exists for all seven priced nodes.
4. Verify Kubecost prerequisites and the eligible node:

   ```bash
   kubectl get nodes -L kubernetes.io/arch,kalaxy3.io/kubecost
   kubectl get storageclass longhorn
   ```

5. Validate syntax:

   ```bash
   ansible-playbook \
     -i inventory/hosts.yml \
     playbooks/platform.yml \
     --syntax-check
   ```

6. Render and validate calibration without Helm:

   ```bash
   ansible-playbook \
     -i inventory/hosts.yml \
     playbooks/kubecost-calibration-only.yml
   ```

7. Inspect the generated values:

   ```bash
   ansible arm64-01 \
     -i inventory/hosts.yml \
     --become \
     --module-name ansible.builtin.command \
     --args 'cat /tmp/kalaxy3-kubecost-calibration-values.yaml'
   ```

8. Apply the live release:

   ```bash
   ansible-playbook \
     -i inventory/hosts.yml \
     playbooks/platform.yml \
     --tags kubecost \
     --extra-vars install_kubecost=true
   ```

9. Verify Helm values, status, pods, labels, and events.
10. Run the same command again and require `changed=0`.

### Data durability and backup impact

- The change reconciled Helm values and restarted Kubecost pods.
- Existing Longhorn-backed persistent volumes were retained by the release.
- No data-loss event was observed.
- PVC binding, Longhorn replica health, and historical-data continuity were not
  directly revalidated during this calibration session and remain evidence
  gaps.
- The pre-change Helm backup was written to `/tmp` on the Mac mini and is not a
  durable backup until copied into an approved evidence-artifact location.

## Operational considerations and observability

### Health signals

- `helm status kubecost -n kubecost`
- `kubectl get pods -n kubecost -o wide`
- `kubectl get deployments,statefulsets -n kubecost`
- `kubectl get events -n kubecost --sort-by=.lastTimestamp`
- `helm get values kubecost -n kubecost`
- Ansible recap and changed count
- Helm revision number and last-deployed timestamp
- Kubecost frontend and allocation reports after collection windows

### Routine verification

```bash
helm status kubecost -n kubecost |
grep -E 'LAST DEPLOYED:|STATUS:|REVISION:'

kubectl get pods -n kubecost -o wide

helm get values kubecost -n kubecost |
grep -A35 -E \
  'customPrices:|sharedNamespaces:|sharedOverhead:|networkCosts:'

ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

The final Ansible command should produce `changed=0` unless inventory or runtime
state has intentionally changed.

### Capacity, performance, and cost impact

- **Capacity:** The model covers seven nodes and approximately 14,000 logical GB
  represented by the four storage profiles. It does not add cluster capacity.
- **Performance:** Calibration itself is lightweight. A material Helm-value
  change restarts Kubecost workloads; the observed rollout completed in roughly
  two minutes.
- **Cost:** The derived engineering model is approximately `$89.11/month` using
  declared aggregate capacities and current assumptions. This is not a billed
  amount.
- **Sustainability/power:** The model makes approximately `322 W` of allocated
  infrastructure power visible: `162 W` rack UPS allocation plus `160 W` Intel
  UPS allocation. The UPS load readings and allocations are approximate.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Implementation commit SHA is pending. | Repository lineage is incomplete; status cannot become accepted. | Don Buddenbaum | before publication |
| `GAP-002` | evidence-gap | Independent reviewer decision is pending. | Governance acceptance is incomplete. | Kalaxy3 architecture | before status changes to accepted |
| `GAP-003` | evidence-gap | No Kubecost UI or API allocation report was captured after the documented data-collection window. | Values are proven in Helm, but end-user cost presentation is not yet directly proven. | Don Buddenbaum | after at least 25 minutes of stable collection |
| `GAP-004` | limitation | Power is allocated from rounded UPS load readings rather than measured per device. | Dollar precision is medium-low for electricity. | Don Buddenbaum | when plug-level meters are available or wiring changes |
| `GAP-005` | limitation | CPU and RAM rates are blended cluster-wide. | Per-node marginal-cost differences are hidden. | Kalaxy3 architecture | if Kubecost or a companion model supports node-specific pricing |
| `GAP-006` | limitation | GPU pricing is zero and GPUs are not Kubernetes-schedulable. | Future GPU workloads would require a new model. | Kalaxy3 architecture | before enabling Kubernetes GPU workloads |
| `GAP-007` | limitation | Network-cost component is enabled but egress rates are zero. | Traffic may be measured without dollar allocation. | Kalaxy3 architecture | when WAN or inter-site charges become material |
| `GAP-008` | evidence-gap | PVC, Longhorn replica health, and historical-data continuity were not recaptured after the rollout. | Immediate pod health is proven, but storage continuity evidence is incomplete. | Don Buddenbaum | before acceptance or after any storage alert |
| `GAP-009` | evidence-gap | Ansible, Helm client, and `kubernetes.core` versions were not recorded. | Toolchain reproducibility is incomplete. | Don Buddenbaum | next maintenance run |
| `GAP-010` | technical-debt | Pre-change Helm backup remains under `/tmp`. | Backup may disappear on reboot or cleanup. | Don Buddenbaum | before relying on it for rollback evidence |
| `GAP-011` | risk | Acquisition prices, residual values, and useful lives can age without review. | Cost evidence becomes stale while remaining technically valid. | Kalaxy3 architecture | annual review or hardware replacement |
| `GAP-012` | evidence-gap | The unrelated research PDF was untracked and intentionally excluded; final staging/commit evidence was not captured. | No risk to runtime; publication lineage is incomplete. | Don Buddenbaum | during Git commit |

## Troubleshooting

### Calibration fails with an undefined accumulator

**Meaning**

A total is used before its initialization task.

**Checks**

```bash
grep -n -A15 -B5 \
  'Initialize Kubecost compute totals\|Calculate monthly compute totals' \
  playbooks/tasks/kubecost-calibration.yml
```

**Recovery**

Ensure the initialization task appears before the loop and defines:

```yaml
kubecost_compute_monthly_usd
kubecost_total_cpu_cores
kubecost_total_memory_gib
```

### Node-label command receives a dictionary as a node name

**Meaning**

Nested loops reused `item`.

**Recovery**

Use distinct loop variables:

```yaml
loop_control:
  loop_var: kubecost_node
```

and:

```yaml
loop_control:
  loop_var: kubecost_label
```

### Targeted Kubecost run performs only fact gathering

**Meaning**

The dynamic observability include is not tagged.

**Checks**

```bash
sed -n '54,66p' playbooks/platform.yml
```

**Recovery**

The parent include must contain:

```yaml
tags:
  - observability
  - kubecost
```

### `install_observability` is undefined

**Meaning**

Ansible is not loading the global variable file because both
`group_vars/all.yml` and `group_vars/all/` exist.

**Recovery**

Use:

```text
inventory/group_vars/all/main.yml
inventory/group_vars/all/kubecost-calibration.yml
```

Verify:

```bash
ansible-inventory \
  -i inventory/hosts.yml \
  --host arm64-01 |
grep -E \
  '"install_observability"|"install_kubecost"|"kubecost_calibration"'
```

### `kubecost_eligible_nodes` is undefined

**Meaning**

The discovery task was skipped during tagged execution.

**Recovery**

Add:

```yaml
tags:
  - kubecost
```

on the task that registers `kubecost_eligible_nodes`.

### Helm reports changed on every identical run

**Meaning**

Either an imperative Helm command is still used or Helm Diff is absent.

**Checks**

```bash
ansible arm64-01 \
  -i inventory/hosts.yml \
  --become \
  --module-name ansible.builtin.command \
  --args 'helm diff version'
```

Expected:

```text
3.15.10
```

**Recovery**

Manage Helm with `kubernetes.core.helm` and install Helm Diff with
`kubernetes.core.helm_plugin`.

### Kubecost pods do not recover after a values change

**Checks**

```bash
helm status kubecost -n kubecost
kubectl get pods -n kubecost -o wide
kubectl get events -n kubecost --sort-by='.lastTimestamp' | tail -50
kubectl logs -n kubecost kubecost-aggregator-0 --tail=200
```

**Recovery**

Correct the reported workload or storage problem, rerun the tagged Ansible
workflow, or roll back to a known-good Helm revision.

## Freshness, revalidation, and supersession

### Revalidate when

- the Kubecost chart version changes from `3.2.1`;
- the Helm Diff version or Helm module behavior changes;
- a node is added, removed, replaced, or materially upgraded;
- RAM, CPU, GPU, disk, or storage-role metadata changes;
- UPS wiring or the set of powered devices changes;
- measured power replaces UPS allocation estimates;
- the electricity rate changes materially;
- acquisition price, residual value, or useful-life assumptions change;
- MinIO or Longhorn capacity or replication changes;
- network egress becomes chargeable;
- GPU scheduling is enabled;
- any source-of-truth file listed in this record moves or changes;
- the final Ansible run no longer converges with `changed=0`;
- Kubecost reports a different effective custom price;
- a conflicting SAGE record is accepted.

### Scheduled review

```text
Event-based, plus an annual review of acquisition, residual-value, useful-life,
electricity-rate, and power assumptions.
```

### Supersession rule

When replaced, set `status: superseded`, populate `superseded_by`, preserve this
record for lineage, and identify whether the deployment claims, price claims,
or both were replaced. A measurement-only update may supersede the cost values
without invalidating the automation and idempotency evidence.

## Final completion checklist

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Status accurately reflects completeness.
- [x] Owner, author/operator, and reviewer state are identified.
- [x] Five Ws and How are complete.
- [x] Scope and nonclaims are explicit.
- [ ] Implementation commit is recorded.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical technical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from the accepted final state.
- [x] Idempotency is proven.
- [ ] Kubecost UI/API allocation output after the collection window is captured.
- [ ] Post-rollout PVC and Longhorn replica health are recaptured.

### Safety and operations

- [x] Secrets and sensitive data are excluded or redacted.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback and rebuild are documented.
- [x] Operational health checks are documented.
- [x] Known limitations and evidence gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | pending | pending | Record must be reviewed after adding the implementation commit. |
| Reviewer | pending | pending | pending | Independent SAGE review not yet performed. |

## Git review and publication

From the repository root:

```bash
cd ~/dvlp/Kalaxy3

git diff --check
git status --short

git diff -- \
  infrastructure/k3s-homelab/inventory/group_vars \
  infrastructure/k3s-homelab/inventory/host_vars \
  infrastructure/k3s-homelab/playbooks/platform.yml \
  infrastructure/k3s-homelab/playbooks/kubecost-calibration-only.yml \
  infrastructure/k3s-homelab/playbooks/tasks/observability.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-calibration.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml \
  infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2 \
  markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md
```

Stage only the implementation and evidence record. Do not stage the unrelated
research PDF:

```bash
git add -- \
  infrastructure/k3s-homelab/inventory/group_vars/all/main.yml \
  infrastructure/k3s-homelab/inventory/group_vars/all/kubecost-calibration.yml \
  infrastructure/k3s-homelab/inventory/host_vars/arm64-01.yml \
  infrastructure/k3s-homelab/inventory/host_vars/arm64-02.yml \
  infrastructure/k3s-homelab/inventory/host_vars/arm64-03.yml \
  infrastructure/k3s-homelab/inventory/host_vars/arm64-04.yml \
  infrastructure/k3s-homelab/inventory/host_vars/arm64-05.yml \
  infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml \
  infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml \
  infrastructure/k3s-homelab/playbooks/platform.yml \
  infrastructure/k3s-homelab/playbooks/kubecost-calibration-only.yml \
  infrastructure/k3s-homelab/playbooks/tasks/observability.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-calibration.yml \
  infrastructure/k3s-homelab/playbooks/tasks/kubecost-node-label.yml \
  infrastructure/k3s-homelab/playbooks/templates/kubecost-calibration-values.yml.j2 \
  markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md
```

Validate the staged change:

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Commit and publish:

```bash
git commit -m "Add calibrated Kubecost pricing and SAGE evidence"
git pull --rebase origin main
git push origin main
git status
```

After committing, update this record with the implementation commit SHA and
change the owner decision when review is complete.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| SAGE evidence record | `markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md` | generated after file creation; see packaged artifact checksum | no secrets; internal infrastructure metadata | repository history |
| Generated calibration values | `/tmp/kalaxy3-kubecost-calibration-values.yaml` | `0f6842e2bb480a74a41bdae26124c1f227f81fa2` was the Ansible-reported checksum, not explicitly labeled SHA-256 | no | temporary unless archived |
| Pre-calibration Helm values | `/tmp/kalaxy3-kubecost-backup/values-before-calibration.yaml` | not captured | potentially internal configuration; no secret observed | temporary |
| Pre-calibration Helm status | `/tmp/kalaxy3-kubecost-backup/status-before-calibration.txt` | not captured | no secret observed | temporary |
| Terminal transcripts | Captured in the implementation conversation; material excerpts are inline in this record | not captured | no secrets observed | retain through this record or export to approved artifact storage |

### Additional notes

- Helm revision 7 is correct. The final no-change Ansible run demonstrated that
  no additional revision was created after idempotency was fixed.
- The inventory value `install_kubecost: false` remained unchanged during the
  live validation; `--extra-vars install_kubecost=true` enabled Kubecost for the
  targeted execution only. Decide separately whether automatic full-platform
  rebuilds should enable Kubecost by default.
- The existing Kubecost installation record remains useful for installation,
  storage, image, and compatibility history. This record supersedes only its
  statement that actual Kalaxy3 dollar calibration remained future work.
