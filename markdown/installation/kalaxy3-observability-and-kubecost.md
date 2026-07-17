# Kalaxy3 Observability and Kubecost Deployment

**Date:** July 17, 2026  
**Repository:** `Kalaxy3`  
**Target location:** `markdown/kalaxy3-observability-and-kubecost.md`

## Purpose

This document records the Kalaxy3 observability deployment, the Kubecost installation failure on Raspberry Pi 4 nodes, the root cause, and the final configuration that keeps Prometheus and Grafana available on the ARM cluster while reserving Kubecost for a labeled Intel `amd64` node.

The final design is:

- Prometheus, Grafana, and Alertmanager can run on the existing Raspberry Pi cluster.
- Their persistent data uses the `nfs-ssd` StorageClass.
- Kubecost is skipped until a suitable Intel node joins the cluster.
- Every Kubecost workload is constrained to a labeled `amd64` node.
- Kubecost's embedded ClickHouse database uses `local-path`, not NFS.
- MetalLB assigns Kubecost the fixed address `192.168.2.26`.

## Initial observability deployment

The observability phase installed the Prometheus community stack successfully:

```text
TASK [Install Prometheus and Grafana]
changed: [arm64-01]
```

The Kubecost installation then timed out after 20 minutes:

```text
TASK [Install Kubecost]
Error: context deadline exceeded
```

The original Helm command installed Kubecost 3.2.1 and requested the following:

- Cluster ID `kalaxy3`
- Kubecost frontend as a `LoadBalancer`
- NFS-backed local-store persistence
- A 20-minute Helm `--wait` timeout

Helm created the release, but one workload never became ready, causing the release status to become `failed`.

## Troubleshooting

### Cluster resources

The Kubecost namespace showed that most components were healthy:

```text
kubecost-cloud-cost          Running
kubecost-cluster-controller  Running
kubecost-finopsagent         Running
kubecost-forecasting         Running
kubecost-frontend            Running
kubecost-local-store         Running
kubecost-aggregator-0        CrashLoopBackOff
```

All Kubecost PVCs were bound, including:

```text
aggregator-db-storage-kubecost-aggregator-0   Bound   128Gi   nfs-ssd
kubecost-cloud-cost-persistent-configs        Bound   1Gi     nfs-ssd
kubecost-local-store                          Bound   10Gi    nfs-ssd
persistent-configs-kubecost-aggregator-0      Bound   1Gi     nfs-ssd
```

MetalLB was also working correctly:

```text
kubecost-frontend   LoadBalancer   192.168.2.21
```

This eliminated the following as the primary cause:

- PVC provisioning failure
- MetalLB address assignment failure
- General Kubecost image-pull failure
- Failure of the frontend, forecasting, local-store, or cloud-cost components

### Helm access on the K3s node

Helm was installed on `arm64-01`, not on the Mac mini. Running Helm remotely without a kubeconfig caused it to default to `localhost:8080`:

```text
Kubernetes cluster unreachable:
Get "http://localhost:8080/version": connection refused
```

The correct command was:

```bash
ssh pi@192.168.2.51 \
  'sudo helm \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  status kubecost \
  --namespace kubecost \
  --show-resources'
```

Helm confirmed:

```text
STATUS: failed
kubecost-aggregator   0/1
```

The chart notes printed `KUBECOST INSTALLATION SUCCESSFUL`, but that text is static chart output. The authoritative Helm release status was `failed`.

### Aggregator log

The aggregator log revealed the actual failure:

```text
starting embedded clickhouse server
Illegal instruction (core dumped) clickhouse-server
ERROR - CH server did not come up after 100 attempts
```

## Root cause

Kubecost 3.2.1 starts an embedded ClickHouse server inside the aggregator workload. The ClickHouse binary attempted to execute a CPU instruction that the Raspberry Pi 4 processor does not support.

The failure was therefore a CPU instruction-set incompatibility, not a Kubernetes, MetalLB, Helm timeout, storage provisioning, or permissions problem.

Increasing the timeout, changing readiness probes, or adding memory would not correct an `Illegal instruction` crash.

A separate storage concern was also identified: the Kubecost aggregator database had been placed on `nfs-ssd`. The embedded ClickHouse database should use node-local or block storage rather than an NFS filesystem.

## Final deployment strategy

Kubecost remains enabled as an intended component, but Ansible checks for a specifically labeled Intel node before installing it.

The qualifying node must match both selectors:

```yaml
kubernetes.io/arch: amd64
kalaxy3.io/kubecost: "true"
```

This provides two safeguards:

1. ARM nodes can never satisfy the architecture requirement.
2. Kubecost does not automatically consume every Intel node; only an explicitly labeled node is eligible.

All Kubecost workloads are pinned to the selected Intel node. This is more restrictive than pinning only the aggregator, but it keeps the entire Kubecost installation together and prevents future chart changes from scheduling an incompatible workload on a Pi.

## Repository changes

### Observability task file

**File:**

```text
playbooks/tasks/observability.yml
```

The Prometheus and Grafana task remains NFS-backed and available to the current Pi cluster:

```yaml
---
- name: Install Prometheus and Grafana
  ansible.builtin.command: >-
    helm upgrade --install kube-prometheus-stack
    prometheus-community/kube-prometheus-stack
    --namespace observability
    --create-namespace
    --set prometheus.prometheusSpec.retention={{
      prometheus_retention
    }}
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName={{
      nfs_ssd_storage_class
    }}
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage={{
      prometheus_storage_size
    }}
    --set grafana.persistence.enabled=true
    --set grafana.persistence.storageClassName={{
      nfs_ssd_storage_class
    }}
    --set grafana.persistence.size={{
      grafana_storage_size
    }}
    --set grafana.service.type=LoadBalancer
    --set grafana.service.loadBalancerIP=192.168.2.25
    --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.storageClassName={{
      nfs_ssd_storage_class
    }}
    --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=5Gi
    --wait
    --timeout 20m
  when: install_observability | bool
  changed_when: true

- name: Find eligible Kubecost Intel nodes
  ansible.builtin.command:
    argv:
      - k3s
      - kubectl
      - get
      - nodes
      - --selector=kubernetes.io/arch=amd64,kalaxy3.io/kubecost=true
      - --output=name
  register: kubecost_eligible_nodes
  changed_when: false
  when:
    - install_observability | bool
    - install_kubecost | bool

- name: Write Kubecost Helm values
  ansible.builtin.template:
    src: kubecost-values.yml.j2
    dest: /tmp/kubecost-values.yml
    mode: "0644"
  when:
    - install_observability | bool
    - install_kubecost | bool
    - kubecost_eligible_nodes.stdout | default('') | trim | length > 0

- name: Install Kubecost
  ansible.builtin.command:
    argv:
      - helm
      - upgrade
      - --install
      - kubecost
      - kubecost/kubecost
      - --version
      - "3.2.1"
      - --namespace
      - kubecost
      - --create-namespace
      - --values
      - /tmp/kubecost-values.yml
      - --wait
      - --timeout
      - 30m
  changed_when: true
  when:
    - install_observability | bool
    - install_kubecost | bool
    - kubecost_eligible_nodes.stdout | default('') | trim | length > 0

- name: Report that Kubecost is waiting for an Intel node
  ansible.builtin.debug:
    msg: >-
      Kubecost was skipped because no labeled amd64 node is currently
      available. After an Intel node joins, label it with
      kalaxy3.io/kubecost=true and rerun the observability phase.
  when:
    - install_observability | bool
    - install_kubecost | bool
    - kubecost_eligible_nodes.stdout | default('') | trim | length == 0
```

The earlier `Assign Kubecost LoadBalancer address` task was removed. The MetalLB address is now declared in the Helm values before the Service is created.

### Kubecost Helm values template

**File:**

```text
playbooks/templates/kubecost-values.yml.j2
```

```yaml
---
global:
  clusterId: kalaxy3

frontend:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  service:
    type: LoadBalancer
    annotations:
      metallb.io/loadBalancerIPs: "192.168.2.26"

aggregator:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  persistentConfigsStorage:
    storageClass: local-path
    storageRequest: 1Gi

  aggregatorDbStorage:
    storageClass: local-path
    storageRequest: 128Gi

localStore:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  persistentVolume:
    enabled: true
    storageClass: local-path
    size: 32Gi

forecasting:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

cloudCost:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

clusterController:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

finopsagent:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

networkCosts:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"
```

## Feature variables

The intended state is:

```yaml
install_observability: true
install_kubecost: true
```

Locate the existing variable definitions with:

```bash
rg -n "install_observability|install_kubecost" .
```

`install_kubecost: true` now means "install when an eligible node exists." It no longer means "attempt installation on the current Pi-only cluster."

## Removal of the failed Kubecost installation

The failed release and its NFS-backed PVCs must be removed before the corrected deployment. Kubernetes cannot change an existing PVC's StorageClass from `nfs-ssd` to `local-path`.

```bash
ssh pi@192.168.2.51 \
  'sudo helm \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  uninstall kubecost \
  --namespace kubecost || true'

kubectl delete namespace kubecost --ignore-not-found
```

This cleanup does not affect the separate `observability` namespace containing Prometheus and Grafana.

## Intel node onboarding

After an Intel node joins the K3s cluster, label it explicitly.

For a node named `amd64-01`:

```bash
kubectl label node amd64-01 \
  kalaxy3.io/kubecost=true \
  --overwrite
```

To label every currently joined `amd64` node:

```bash
for node in $(kubectl get nodes \
  --selector=kubernetes.io/arch=amd64 \
  --output=name); do
  kubectl label "${node}" \
    kalaxy3.io/kubecost=true \
    --overwrite
done
```

Verify the architecture and label:

```bash
kubectl get nodes \
  -L kubernetes.io/arch,kalaxy3.io/kubecost
```

Expected pattern:

```text
NAME       ARCH    KUBECOST
arm64-01   arm64
arm64-02   arm64
arm64-03   arm64
arm64-04   arm64
arm64-05   arm64
amd64-01   amd64   true
```

After labeling the node, rerun the observability phase. Ansible should detect at least one eligible node, render the Kubecost values file, and install the release.

## Validation performed

### Ansible syntax check

From the repository root:

```bash
ansible-playbook \
  playbooks/k3s.yml \
  --syntax-check \
  --vault-id kalaxy3@prompt
```

Expected result:

```text
playbook: playbooks/k3s.yml
```

### YAML parsing

```bash
ruby -e '
require "yaml"

ARGV.each do |file|
  YAML.safe_load(
    File.read(file),
    permitted_classes: [],
    permitted_symbols: [],
    aliases: true
  )
  puts "#{file}: YAML OK"
end
' \
  playbooks/tasks/observability.yml \
  playbooks/templates/kubecost-values.yml.j2
```

### Helm rendering without installation

Copy the template to the Helm node:

```bash
scp \
  playbooks/templates/kubecost-values.yml.j2 \
  pi@192.168.2.51:/tmp/kubecost-values.yml
```

Render and validate the chart:

```bash
ssh pi@192.168.2.51 '
  sudo helm \
    --kubeconfig /etc/rancher/k3s/k3s.yaml \
    template kubecost kubecost/kubecost \
    --version 3.2.1 \
    --namespace kubecost \
    --values /tmp/kubecost-values.yml \
    --validate \
    > /tmp/kubecost-rendered.yaml &&
  echo "Kubecost Helm rendering: OK"
'
```

### Kubernetes manifest dry run

```bash
ssh pi@192.168.2.51 '
  sudo k3s kubectl apply \
    --dry-run=client \
    --filename /tmp/kubecost-rendered.yaml \
    > /dev/null &&
  echo "Rendered Kubernetes manifests: OK"
'
```

### Node-selector verification

```bash
ssh pi@192.168.2.51 '
  grep \
    --line-number \
    --after-context=3 \
    "nodeSelector:" \
    /tmp/kubecost-rendered.yaml
'
```

The rendered manifest contained eight workload selectors. Every selector required:

```yaml
nodeSelector:
  kalaxy3.io/kubecost: "true"
  kubernetes.io/arch: amd64
```

This confirmed that the Kubecost workloads could not schedule on any Raspberry Pi node.

## Post-install verification

After Kubecost is installed on the Intel node, verify placement:

```bash
kubectl get pods \
  --namespace kubecost \
  --output=wide
```

Every Kubecost pod should show the labeled Intel node in the `NODE` column.

Verify the aggregator database PVC:

```bash
kubectl get pvc \
  --namespace kubecost \
  aggregator-db-storage-kubecost-aggregator-0
```

Expected StorageClass:

```text
local-path
```

Verify the fixed MetalLB address:

```bash
kubectl get service \
  --namespace kubecost \
  kubecost-frontend
```

Expected external address:

```text
192.168.2.26
```

## Outcome

The observability phase is now split according to workload compatibility:

| Component | Architecture | Persistent storage | Address |
|---|---|---|---|
| Prometheus | ARM or AMD64 | `nfs-ssd` | Internal |
| Grafana | ARM or AMD64 | `nfs-ssd` | `192.168.2.25` |
| Alertmanager | ARM or AMD64 | `nfs-ssd` | Internal |
| Kubecost | Labeled AMD64 only | `local-path` | `192.168.2.26` |
| Kubecost ClickHouse | Labeled AMD64 only | `local-path`, 128 GiB | Internal |

The original Helm timeout was not hidden or bypassed. Its underlying cause was identified, and the deployment was redesigned so incompatible ARM nodes are excluded before Helm runs.
