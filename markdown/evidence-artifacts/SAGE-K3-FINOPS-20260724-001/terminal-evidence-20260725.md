---
evidence_id: SAGE-K3-FINOPS-20260724-001
artifact_type: consolidated-terminal-evidence
classification: internal
created_at: 2026-07-25T16:31:00-05:00
source: terminal excerpts supplied by Don Buddenbaum during the Kubecost calibration session
completeness: material retained excerpts; verbose repeated output abbreviated where noted
---

# Consolidated terminal evidence — Kubecost network and provider allocation

This artifact preserves material terminal evidence used by
`SAGE-K3-FINOPS-20260724-001`. It is not a byte-for-byte shell transcript.
Repeated Ansible loop output is abbreviated when the claim depends on the task
result or recap rather than every item. No secrets were observed.

## 1. Locate fixed and network-cost inputs

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

grep -RInE \
  'shared.*overhead|fixed_monthly|monthly_overhead|internet|provider|isp' \
  inventory group_vars host_vars playbooks 2>/dev/null
```

Observed:

```text
inventory/group_vars/all/kubecost-calibration.yml:18:    fixed_monthly_overhead_usd: 0.00
inventory/group_vars/all/kubecost-calibration.yml:26:    monthly_overhead_usd: 0.00
inventory/group_vars/all/kubecost-calibration.yml:49:    internet_egress_usd_per_gb: 0.00
inventory/group_vars/all/kubecost-calibration.yml:62:      fixed_monthly_overhead_usd: 0.00
inventory/group_vars/all/kubecost-calibration.yml:73:      fixed_monthly_overhead_usd: 0.00
inventory/group_vars/all/kubecost-calibration.yml:83:      fixed_monthly_overhead_usd: 0.00
inventory/group_vars/all/kubecost-calibration.yml:93:      fixed_monthly_overhead_usd: 0.00
playbooks/tasks/kubecost-calibration.yml:41:        kubecost_calibration.compute.fixed_monthly_overhead_usd
playbooks/tasks/kubecost-calibration.yml:200:        (profile.fixed_monthly_overhead_usd | float)
playbooks/tasks/kubecost-calibration.yml:264:- name: Calculate Kubecost shared monthly overhead
playbooks/tasks/kubecost-calibration.yml:269:          kubecost_calibration.shared.monthly_overhead_usd
playbooks/templates/kubecost-calibration-values.yml.j2:27:        internetNetworkEgress: "0.00000000"
playbooks/phases/phase-00-readiness.yml:95:      register: internet_check
```

## 2. Prior live shared overhead

```bash
helm get values kubecost -n kubecost -o json |
jq -r '.kubecostProductConfigs.sharedOverhead'
```

Observed:

```text
8.41
```

## 3. Apply provider allocation

Source change:

```yaml
shared:
  monthly_overhead_usd: 20.00
```

Targeted apply:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags kubecost \
  --extra-vars install_kubecost=true
```

Material observed result:

```text
TASK [Validate Kubecost allocation percentages] ... ok
TASK [Validate Kubecost node cost inventory] ... all seven nodes passed
TASK [Validate Kubecost storage profiles] ... all four profiles passed
TASK [Apply persistent Kalaxy3 node labels] ... all seven nodes processed
TASK [Calculate Kubecost shared monthly overhead] ... ok
TASK [Render calibrated Kubecost Helm values] ... changed
TASK [Install Kubecost] ... changed

PLAY RECAP
arm64-01 : ok=37 changed=2 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

## 4. Live shared overhead after provider allocation

```bash
helm get values kubecost -n kubecost -o json |
jq -r '.kubecostProductConfigs.sharedOverhead'
```

Observed at approximately 16:13 CDT:

```text
28.41
```

## 5. Moving 24-hour fully burdened query

```bash
SHARED_NAMESPACES="$(
  helm get values kubecost -n kubecost -o json |
  jq -r '.kubecostProductConfigs.sharedNamespaces'
)"

SHARED_OVERHEAD="$(
  helm get values kubecost -n kubecost -o json |
  jq -r '.kubecostProductConfigs.sharedOverhead'
)"

curl --fail --silent --show-error \
  --get \
  'http://192.168.2.26:9090/model/allocation' \
  --data-urlencode 'window=24h' \
  --data-urlencode 'aggregate=namespace' \
  --data-urlencode 'accumulate=true' \
  --data-urlencode 'shareIdle=true' \
  --data-urlencode "shareNamespaces=${SHARED_NAMESPACES}" \
  --data-urlencode "shareCost=${SHARED_OVERHEAD}" \
  --data-urlencode 'shareSplit=weighted' \
  --output /tmp/kubecost-fully-burdened-provider.json
```

Observed:

```text
NAMESPACE                      SHARED        TOTAL
minio                       30.789750    58.425380
__unmounted__                0.179680     0.340950
headlamp                     0.051130     0.097010
```

```json
{
  "sharedCost": 31.020560000000003,
  "networkCost": 0,
  "totalCost": 58.863339999999994
}
```

This result was not accepted as a comparison with an earlier rolling window.

## 6. Fixed-window definition

```bash
END_UTC="$(date -u '+%Y-%m-%dT%H:%M:00Z')"
START_UTC="$(date -u -v-24H '+%Y-%m-%dT%H:%M:00Z')"
FIXED_WINDOW="${START_UTC},${END_UTC}"
printf 'Fixed window: %s\n' "$FIXED_WINDOW"
```

Observed:

```text
Fixed window: 2026-07-24T21:17:00Z,2026-07-25T21:17:00Z
```

## 7. Fixed-window queries and comparison

```bash
for SHARE_COST in 8.41 28.41; do
  curl --fail --silent --show-error \
    --get \
    'http://192.168.2.26:9090/model/allocation' \
    --data-urlencode "window=${FIXED_WINDOW}" \
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

## 8. Working-tree review

```bash
git status --short
git diff --check
```

Observed:

```text
M inventory/group_vars/all/kubecost-calibration.yml
M playbooks/tasks/kubecost-node-label.yml
M playbooks/templates/kubecost-calibration-values.yml.j2
```

`git diff --check` returned no output.

Material source changes:

```text
monthly_overhead_usd: 0.00 -> 20.00
finopsagent.kubecost -> finopsagent.agent.kubecost
```

A valid Linux affinity object replaced the invalid/default override, and
network prices were restored to variable-driven rendering.

## 9. Final topology-label task

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

## 10. First final apply

```text
TASK [Apply Kubecost topology labels to arm64-01] ... ok
TASK [Apply Kubecost topology labels to arm64-02] ... ok
TASK [Apply Kubecost topology labels to arm64-03] ... ok
TASK [Apply Kubecost topology labels to arm64-04] ... ok
TASK [Apply Kubecost topology labels to arm64-05] ... ok
TASK [Apply Kubecost topology labels to amd64-01] ... ok
TASK [Apply Kubecost topology labels to amd64-02] ... ok
TASK [Render calibrated Kubecost Helm values] ... changed
TASK [Install Kubecost] ... changed

PLAY RECAP
arm64-01 : ok=37 changed=2 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

## 11. Immediate idempotency rerun

```text
TASK [Apply Kubecost topology labels to all seven nodes] ... ok
TASK [Calculate Kubecost shared monthly overhead] ... ok
TASK [Render calibrated Kubecost Helm values] ... ok
TASK [Install Helm Diff plugin] ... ok
TASK [Install Kubecost] ... ok

PLAY RECAP
arm64-01 : ok=37 changed=0 unreachable=0 failed=0 skipped=0 rescued=0 ignored=0
```

## 12. Network-cost readiness

Retained observation:

```text
DaemonSet kubecost-network-costs
DESIRED: 7
CURRENT: 7
READY:   7
IMAGE:   icr.io/kubecost/network-costs:v0.19.0
RESTARTS: 0
```

## 13. Topology labels

Diagnostic command used during implementation:

```bash
kubectl label nodes --all \
  topology.kubernetes.io/region=kalaxy3-home \
  topology.kubernetes.io/zone=kalaxy3-lan \
  --overwrite
```

The final state is persisted through Ansible rather than relying on this manual
command.

## 14. Network classification errors before labels

```text
Could not locate region for local node
Failed to classify TransportData as NetworkTraffic
```

After labels and DaemonSet restart, retained validation found no matching
classification errors.

## 15. Network metrics

A collector was port-forwarded from port `3001` to local port `13001`.

Retained metric names:

```text
kubecost_pod_network_egress_bytes_total
kubecost_pod_network_ingress_bytes_total
```

Retained local classification labels:

```text
internet="false"
same_region="true"
same_zone="true"
```

Twelve matching series were retained, including `minio`, `metallb-system`,
`observability`, and `kubecost`.

## 16. Raw namespace allocation

```bash
curl --fail --silent --show-error \
  'http://192.168.2.26:9090/model/allocation?window=24h&aggregate=namespace&accumulate=true' \
  -o /tmp/kubecost-allocation-namespace.json
```

Retained namespaces:

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

Retained detailed allocation:

```text
NAMESPACE             CPU       RAM       PV       NET   SHARED   ADJUST  TOTAL
__idle__            34.6146   14.3606   0        0     0        0       48.9752
minio                0.8714    0.2336   5.6526   0     0        1.1390   7.8965
observability        0.2991    0.1981   0.0691   0     0        0.5255   1.0919
longhorn-system      2.0394    0.0673   0        0     0       -1.1187   0.9880
kubecost             0.4343    0.3367   0.2016   0     0       -0.3503   0.6223
metallb-system       0.1221    0.0911   0        0     0        0.2092   0.4224
kube-system          0.1448    0.0189   0        0     0        0.1964   0.3601
__unmounted__        0         0        0.1759   0     0       -0.0069   0.1689
storage              0.0052    0.0019   0        0     0        0.0088   0.0160
headlamp             0.0007    0.0013   0        0     0        0.0025   0.0045
```

Summary:

```text
total cluster 24h cost: approximately $60.5458
idle:                   approximately $48.9752
non-idle:               approximately $11.5706
idle percentage:        approximately 80.89%
network monetary cost:  $0
```

## 17. Earlier fully burdened allocation at `$8.41/month`

Shared namespaces:

```text
kube-system,kubecost,longhorn-system,metallb-system,observability,storage
```

Observed:

```text
NAMESPACE       SHARED       NETWORK    TOTAL
minio           31.478430    0          60.369070
__unmounted__    0.184080    0           0.353020
headlamp         0.052250    0           0.100200
```

```json
{
  "sharedCost": 31.71476,
  "networkCost": 0,
  "totalCost": 60.82229
}
```

This demonstrates that `sharedCost` includes more than fixed monthly overhead.

## 18. Invalid affinity failure

A temporary empty-string affinity caused Helm to fail:

```text
UPGRADE FAILED: cannot patch "kubecost-network-costs" with kind DaemonSet
```

The verbose patch showed a string for a field expected to deserialize into
`v1.Affinity`.

Accepted correction:

```yaml
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

## 19. Evidence not retained as durable raw files

No original checksums were captured for:

```text
/tmp/kalaxy3-kubecost-calibration-values.yaml
/tmp/kubecost-allocation-namespace.json
/tmp/kubecost-fully-burdened-provider.json
/tmp/kubecost-overhead-8.41.json
/tmp/kubecost-overhead-28.41.json
```

Future evidence collection should copy material outputs into the evidence
artifact directory and checksum them before cleanup.
