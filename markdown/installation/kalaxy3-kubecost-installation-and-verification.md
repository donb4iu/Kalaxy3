# Kalaxy3 Kubecost Installation and Verification

## Purpose

This document records the installation, configuration, correction, and
verification of Kubecost on the Kalaxy3 K3s cluster.

It is intended to provide enough detail to:

- understand why Kubecost was added;
- reproduce the installation after a complete Kalaxy3 rebuild;
- keep Kubecost compute workloads away from the primary LLM node;
- restore the required Longhorn-backed persistent storage;
- expose the Kubecost UI through MetalLB;
- recognize the known nonfatal LoadBalancer-pricing warning;
- verify that the installation is healthy.

## Installation Date

The installation and verification described here were completed on
July 21, 2026, local time.

Kubecost logs use UTC timestamps, so log entries immediately after the
installation show July 22, 2026.

## Result Summary

Kubecost is operational on Kalaxy3 with the following state:

| Item | Result |
|---|---|
| Kubecost chart | `kubecost/kubecost` |
| Chart version | `3.2.1` |
| Namespace | `kubecost` |
| Primary workload node | `amd64-02` |
| LLM node preserved | `amd64-01` |
| Persistent storage | Longhorn |
| Longhorn replica count | `2` |
| Frontend service type | `LoadBalancer` |
| Frontend MetalLB address | `192.168.2.26` |
| Frontend port | `9090` |
| FinOps Agent image | `icr.io/ibm-finops/agent:v1.0.20` |
| Pod health | All pods running |
| Pod restarts at verification | `0` |
| Known warning | Nonfatal LoadBalancer pricing warning |

The Kubecost user interface is available on the Kalaxy3 LAN at:

```text
http://192.168.2.26:9090
```

## Why Kubecost Was Added

Kalaxy3 already had Prometheus and Grafana for cluster metrics and
observability. Kubecost adds Kubernetes resource-cost and allocation analysis.

Kubecost provides visibility into:

- CPU allocation and utilization;
- memory allocation and utilization;
- namespace and workload cost allocation;
- pod and container allocation;
- persistent-volume allocation;
- node resource allocation;
- idle and shared cluster resources;
- historical allocation data retained in persistent storage.

Kalaxy3 is a bare-metal homelab rather than an AWS, Azure, or Google Cloud
cluster. Kubecost therefore cannot automatically obtain cloud-provider billing
rates. The deployment is still useful for resource allocation and relative cost
analysis, but accurate dollar values require a separate Kalaxy3 custom cost
model.

## Placement Decision

### Preserve `amd64-01` for the LLM

`amd64-01` is intended to host the primary Kalaxy3 LLM and RAG workloads.

Kubecost includes database, aggregation, local-storage, frontend, and collection
components that consume CPU, memory, storage I/O, and network bandwidth.
Therefore, Kubecost compute workloads were placed on `amd64-02`.

### Longhorn still uses both AMD64 nodes

Although Kubecost application pods run on `amd64-02`, its Longhorn volumes use
two replicas.

This means:

- Kubecost CPU and memory consumption stays on `amd64-02`;
- Kubecost persistent data remains redundant;
- one Longhorn replica may reside on `amd64-01`;
- `amd64-01` can still see Longhorn disk and replication traffic;
- loss of one Longhorn node does not immediately destroy Kubecost data.

This is the intended tradeoff between preserving LLM compute resources and
maintaining storage resilience.

## Prerequisites

Before rebuilding Kubecost, verify the following Kalaxy3 components.

### K3s cluster

```bash
kubectl get nodes -o wide
```

Expected relevant nodes:

```text
amd64-01   Ready
amd64-02   Ready
```

### Longhorn

```bash
kubectl get pods \
  -n longhorn-system

kubectl get storageclass longhorn
```

The Longhorn StorageClass must exist before Kubecost is installed.

### Prometheus and Grafana

```bash
kubectl get pods \
  -n observability
```

Kubecost was installed through the Kalaxy3 observability phase, which also
reconciles Prometheus and Grafana.

### MetalLB

The address `192.168.2.26` must be within the configured Kalaxy3 MetalLB address
pool and must not be assigned to another service.

```bash
kubectl get svc -A \
  -o wide
```

### AMD64 Kubecost label

Only the intended Kubecost compute node should carry the Kubecost scheduling
label.

```bash
kubectl get nodes \
  -L kubernetes.io/arch,kalaxy3.io/kubecost,kalaxy3.io/longhorn
```

Expected intent:

```text
amd64-01   amd64   <none>   true
amd64-02   amd64   true     true
```

The exact column order depends on the `kubectl` command, but
`kalaxy3.io/kubecost=true` should be present only on `amd64-02`.

## Inventory Configuration

The Kalaxy3 Ansible inventory should identify `amd64-02` as the Kubecost node.

Example:

```yaml
kubecost_nodes:
  hosts:
    amd64-02:
```

The node must also remain a member of the appropriate K3s agent and Longhorn
inventory groups.

## Node Labels

The desired Kubernetes labels are:

```text
amd64-01:
  kalaxy3.io/longhorn=true
  node.longhorn.io/create-default-disk=true

amd64-02:
  kalaxy3.io/longhorn=true
  kalaxy3.io/kubecost=true
  node.longhorn.io/create-default-disk=true
```

Apply or repair the Kubecost label with:

```bash
kubectl label node amd64-02 \
  kalaxy3.io/kubecost=true \
  --overwrite
```

Remove the Kubecost label from `amd64-01` with:

```bash
kubectl label node amd64-01 \
  kalaxy3.io/kubecost-
```

Verify:

```bash
kubectl get nodes \
  -L kubernetes.io/arch,kalaxy3.io/kubecost,kalaxy3.io/longhorn
```

The Ansible Longhorn/platform tasks should own these labels so a full rebuild
does not depend on manual commands.

## Kalaxy3 Variables

The relevant Kalaxy3 variables include:

```yaml
install_observability: true
install_kubecost: true

kubecost_storage_size: 32Gi

longhorn_replica_count: 2
```

During the initial installation, Kubecost was enabled explicitly on the command
line:

```bash
--extra-vars 'install_kubecost=true'
```

For a fully automatic rebuild, set `install_kubecost: true` in the intended
Kalaxy3 group variables after the deployment has been accepted.

## Kubecost Helm Values

The Kubecost values template is:

```text
infrastructure/k3s-homelab/playbooks/templates/kubecost-values.yml.j2
```

The effective design is represented by the following values:

```yaml
---
global:
  clusterId: kalaxy3
  defaultStorageClass: longhorn

frontend:
  enabled: true

  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  service:
    type: LoadBalancer
    annotations:
      metallb.io/loadBalancerIPs: "192.168.2.26"

aggregator:
  enabled: true

  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  persistentConfigsStorage:
    storageClass: longhorn
    storageRequest: 1Gi

  aggregatorDbStorage:
    storageClass: longhorn
    storageRequest: 128Gi

  resources:
    requests:
      cpu: 100m
      memory: 3Gi

finopsagent:
  enabled: true

  image:
    registry: icr.io
    repository: ibm-finops/agent
    tag: v1.0.20

  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

localStore:
  enabled: true

  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  persistentVolume:
    enabled: true
    storageClass: longhorn
    size: "{{ kubecost_storage_size }}"
    annotations:
      helm.sh/resource-policy: keep

forecasting:
  enabled: false

cloudCost:
  enabled: false

clusterController:
  enabled: false

networkCosts:
  enabled: false
```

## Important FinOps Agent Image Correction

### Failure observed

The Kubecost chart initially rendered this image:

```text
icr.io/kubecost/agent:v1.0.20
```

The Kubernetes event showed:

```text
Failed to pull image "icr.io/kubecost/agent:v1.0.20":
failed to resolve reference:
icr.io/kubecost/agent:v1.0.20: not found
```

The pod entered:

```text
ImagePullBackOff
```

### Correct image

The working image is:

```text
icr.io/ibm-finops/agent:v1.0.20
```

The permanent correction belongs in
`playbooks/templates/kubecost-values.yml.j2`:

```yaml
finopsagent:
  enabled: true

  image:
    registry: icr.io
    repository: ibm-finops/agent
    tag: v1.0.20
```

### Immediate repair command

If a rebuilt cluster still renders the wrong image, repair it immediately with:

```bash
kubectl set image \
  deployment/kubecost-finopsagent \
  finops-agent=icr.io/ibm-finops/agent:v1.0.20 \
  -n kubecost
```

Then reconcile the Helm release through Ansible so the repair is persistent.

## Ansible Installation Workflow

Run from:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
```

### Syntax check

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --syntax-check
```

### Install or reconcile Kubecost

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars 'platform_phase=observability' \
  --extra-vars 'install_kubecost=true' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

The play performs the following work:

1. gathers facts from `arm64-01`;
2. verifies or installs Helm on the controller;
3. reconciles the configured Helm repositories;
4. selects only the observability platform phase;
5. reconciles Prometheus and Grafana;
6. finds eligible labeled AMD64 Kubecost nodes;
7. renders the Kubecost values template;
8. installs or upgrades Kubecost;
9. waits for the Helm deployment to complete.

`arm64-01` acts as the Ansible and Helm controller. That does not mean Kubecost
application pods run on `arm64-01`.

## Successful Ansible Evidence

The successful reconciliation completed with:

```text
PLAY RECAP
arm64-01 : ok=9 changed=2 unreachable=0 failed=0 skipped=6
```

The following phases were correctly skipped:

- networking and storage;
- administrative UI;
- Longhorn;
- protected UI;
- MinIO.

Only the observability phase was included.

## Installed Workloads

The healthy Kubecost deployment contains:

```text
kubecost-aggregator-0
kubecost-finopsagent-...
kubecost-frontend-...
kubecost-local-store-...
```

Verification showed all four pods:

- ready;
- running;
- scheduled on `amd64-02`;
- reporting zero restarts.

Use:

```bash
kubectl get pods \
  -n kubecost \
  -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount,NODE:.spec.nodeName'
```

Expected form:

```text
NAME                                    READY   RESTARTS   NODE
kubecost-aggregator-0                   true    0          amd64-02
kubecost-finopsagent-...                true    0          amd64-02
kubecost-frontend-...                   true    0          amd64-02
kubecost-local-store-...                true    0          amd64-02
```

## Persistent Storage

Kubecost created three Longhorn-backed PVCs.

| PVC | Capacity | Access mode | StorageClass |
|---|---:|---|---|
| `aggregator-db-storage-kubecost-aggregator-0` | `128Gi` | `RWO` | `longhorn` |
| `kubecost-local-store` | `32Gi` | `RWO` | `longhorn` |
| `persistent-configs-kubecost-aggregator-0` | `1Gi` | `RWO` | `longhorn` |

Verify:

```bash
kubectl get pvc \
  -n kubecost
```

Every PVC must be:

```text
STATUS: Bound
STORAGECLASS: longhorn
```

### Verify Longhorn health and replicas

```bash
kubectl get volumes.longhorn.io \
  -n longhorn-system \
  -o custom-columns='NAME:.metadata.name,STATE:.status.state,HEALTH:.status.robustness,REPLICAS:.spec.numberOfReplicas'
```

For the Kubecost volumes, the desired state is:

```text
STATE: attached
HEALTH: healthy
REPLICAS: 2
```

A volume may be detached when its consuming pod is stopped. That is not itself
an error.

## Network Exposure

The Kubecost frontend service is:

```text
TYPE: LoadBalancer
EXTERNAL-IP: 192.168.2.26
PORT: 9090
```

Verify:

```bash
kubectl get svc kubecost-frontend \
  -n kubecost
```

Expected form:

```text
NAME                TYPE           EXTERNAL-IP    PORT(S)
kubecost-frontend   LoadBalancer   192.168.2.26   9090:...
```

Test from a LAN host:

```bash
curl -I \
  http://192.168.2.26:9090
```

Open in a browser:

```text
http://192.168.2.26:9090
```

## Application Log Verification

### Aggregator

```bash
kubectl logs \
  -n kubecost \
  statefulset/kubecost-aggregator \
  --tail=100
```

Immediately after installation, messages referring to zero file windows may be
normal because the system has not collected enough historical data.

### FinOps Agent

```bash
kubectl logs \
  -n kubecost \
  deployment/kubecost-finopsagent \
  --tail=100
```

Successful startup included:

```text
Starting IBM Finops Agent version v1.0.20
Found configmap pricing-configs, watching...
Successfully created bucket storage
```

`Successfully created bucket storage` confirms that the agent established its
local storage path.

## Known LoadBalancer Pricing Warning

The FinOps Agent currently logs the following warning approximately once per
minute:

```text
WRN Error getting LoadBalancer cost:
strconv.ParseFloat: parsing "": invalid syntax
```

### Interpretation

Kalaxy3 uses MetalLB on bare metal. It does not use a cloud provider that
supplies billed LoadBalancer pricing.

The warning is nonfatal:

- the FinOps Agent remains ready;
- the pod does not restart;
- the frontend remains available;
- the aggregator and local store remain healthy;
- CPU, memory, storage, node, namespace, workload, and allocation collection
  can continue;
- cloud-style LoadBalancer dollar pricing is unavailable.

### Unsuccessful manual pricing experiments

Several manual `pricing-configs` ConfigMap structures were tested.

The chart-managed ConfigMap originally had metadata but no populated pricing
data. Attempts to place pricing JSON under `default.json` caused the agent to
interpret `default.json` as a field name:

```text
error setting custom pricing field:
no such field: Default.json in obj
```

Direct ConfigMap keys for the following values were also tested:

```text
loadBalancer
LBIngressDataCost
FirstFiveForwardingRulesCost
AdditionalForwardingRuleCost
```

The warning continued.

### Accepted operational decision

Do not maintain a manual `pricing-configs` patch in Ansible.

Allow Helm to own the ConfigMap and treat the recurring LoadBalancer-cost
message as a known nonfatal limitation of the current on-premises deployment.

Restore the Helm-managed ConfigMap after any experiment with:

```bash
kubectl delete configmap pricing-configs \
  -n kubecost
```

Then rerun the observability phase:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars 'platform_phase=observability' \
  --extra-vars 'install_kubecost=true' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

Verify that the restored ConfigMap is owned by Helm:

```bash
kubectl get configmap pricing-configs \
  -n kubecost \
  -o yaml
```

Expected metadata includes:

```text
meta.helm.sh/release-name: kubecost
meta.helm.sh/release-namespace: kubecost
app.kubernetes.io/managed-by: Helm
```

## Region Warning

The agent may also report that it cannot determine a default region from node
labels.

For Kalaxy3, region and zone labels can be added as topology metadata:

```bash
kubectl label nodes --all \
  topology.kubernetes.io/region=kalaxy3-homelab \
  topology.kubernetes.io/zone=kalaxy3-lan \
  --overwrite
```

This topology labeling is optional and should be added to Ansible if Kalaxy3
will rely on it after rebuilds.

## Custom Kalaxy3 Cost Model

The Kubecost deployment is complete, but actual homelab dollar calibration is
a separate task.

Kubecost does not yet know Kalaxy3's actual:

- hardware purchase cost;
- expected equipment lifetime;
- electricity rate;
- measured power consumption;
- CPU cost;
- memory cost;
- disk cost;
- NFS storage cost;
- Longhorn storage overhead;
- network cost.

Until those values are modeled, Kubecost provides useful allocation and
relative-cost information but not a complete accounting-grade operating cost.

MetalLB itself has no separately billed cloud LoadBalancer fee. Infrastructure,
power, hardware, and network costs should be represented through the broader
Kalaxy3 cost model instead.

## Complete Rebuild Sequence

After rebuilding the Kalaxy3 cluster, use the following order.

### 1. Rebuild and verify the base cluster

```bash
kubectl get nodes -o wide
kubectl get pods -A
```

### 2. Verify both AMD64 nodes

```bash
kubectl get nodes amd64-01 amd64-02 \
  -o wide
```

### 3. Verify Longhorn prerequisites and mounts

```bash
ssh pi@192.168.2.61 \
  'findmnt /mnt/longhorn'

ssh pi@192.168.2.62 \
  'findmnt /mnt/longhorn'
```

### 4. Install or reconcile Longhorn

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars 'platform_phase=longhorn' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

### 5. Verify Longhorn

```bash
kubectl get pods \
  -n longhorn-system

kubectl get storageclass longhorn
```

### 6. Verify Kubecost node labels

```bash
kubectl get nodes \
  -L kubernetes.io/arch,kalaxy3.io/kubecost,kalaxy3.io/longhorn
```

Correct labels if required:

```bash
kubectl label node amd64-02 \
  kalaxy3.io/kubecost=true \
  --overwrite

kubectl label node amd64-01 \
  kalaxy3.io/kubecost-
```

### 7. Install observability and Kubecost

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars 'platform_phase=observability' \
  --extra-vars 'install_kubecost=true' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

### 8. Watch the Kubecost pods

```bash
kubectl get pods \
  -n kubecost \
  -o wide \
  --watch
```

### 9. Repair the FinOps Agent image if necessary

First inspect:

```bash
kubectl get deployment kubecost-finopsagent \
  -n kubecost \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

It must return:

```text
icr.io/ibm-finops/agent:v1.0.20
```

Repair if required:

```bash
kubectl set image \
  deployment/kubecost-finopsagent \
  finops-agent=icr.io/ibm-finops/agent:v1.0.20 \
  -n kubecost
```

Then correct the Helm values template and rerun Ansible.

### 10. Verify pods, PVCs, and service

```bash
kubectl get pods \
  -n kubecost \
  -o custom-columns='NAME:.metadata.name,READY:.status.containerStatuses[*].ready,RESTARTS:.status.containerStatuses[*].restartCount,NODE:.spec.nodeName'

kubectl get pvc \
  -n kubecost

kubectl get svc kubecost-frontend \
  -n kubecost
```

### 11. Verify logs

```bash
kubectl logs \
  -n kubecost \
  statefulset/kubecost-aggregator \
  --tail=100

kubectl logs \
  -n kubecost \
  deployment/kubecost-finopsagent \
  --tail=100
```

### 12. Open the UI

```text
http://192.168.2.26:9090
```

## Troubleshooting

### `ImagePullBackOff`

Inspect the image and events:

```bash
POD="$(
  kubectl get pods \
    -n kubecost \
    -l app.kubernetes.io/name=finopsagent \
    -o jsonpath='{.items[0].metadata.name}'
)"

kubectl get pod "${POD}" \
  -n kubecost \
  -o jsonpath='Image: {.spec.containers[0].image}{"\n"}'

kubectl describe pod "${POD}" \
  -n kubecost |
  sed -n '/Events:/,$p'
```

The known bad image is:

```text
icr.io/kubecost/agent:v1.0.20
```

The working image is:

```text
icr.io/ibm-finops/agent:v1.0.20
```

### Pod scheduled on the wrong node

Inspect labels:

```bash
kubectl get nodes \
  -L kalaxy3.io/kubecost
```

Inspect the pod's selector and assigned node:

```bash
kubectl get pod \
  -n kubecost \
  -o wide

kubectl get deployment kubecost-finopsagent \
  -n kubecost \
  -o jsonpath='{.spec.template.spec.nodeSelector}{"\n"}'
```

The Kubecost selector must include:

```yaml
kubernetes.io/arch: amd64
kalaxy3.io/kubecost: "true"
```

Only `amd64-02` should match both labels.

### PVC remains pending

Check:

```bash
kubectl describe pvc \
  -n kubecost

kubectl get storageclass

kubectl get nodes.longhorn.io \
  -n longhorn-system
```

Confirm:

- the `longhorn` StorageClass exists;
- Longhorn nodes are schedulable;
- both Longhorn disks have usable capacity;
- the requested replica count can be satisfied.

### Frontend has no external IP

Check:

```bash
kubectl describe svc kubecost-frontend \
  -n kubecost

kubectl get ipaddresspools.metallb.io \
  -n metallb-system

kubectl get l2advertisements.metallb.io \
  -n metallb-system
```

Confirm that `192.168.2.26` is available and part of the advertised pool.

### Frontend is unreachable

Check:

```bash
kubectl get endpoints kubecost-frontend \
  -n kubecost

curl -v \
  http://192.168.2.26:9090
```

Also verify LAN routing and host firewall rules.

### Repeated LoadBalancer warning

This is currently accepted:

```text
Error getting LoadBalancer cost:
strconv.ParseFloat: parsing "": invalid syntax
```

Do not repeatedly patch `pricing-configs` unless a later Kubecost or FinOps Agent
release documents a supported on-premises LoadBalancer pricing configuration.

## Final Acceptance Checklist

- [x] Kubecost chart installed.
- [x] Kubecost namespace created.
- [x] Aggregator running.
- [x] FinOps Agent running.
- [x] Frontend running.
- [x] Local store running.
- [x] Correct FinOps Agent image configured.
- [x] All Kubecost pods scheduled on `amd64-02`.
- [x] `amd64-01` preserved for LLM compute.
- [x] Aggregator database PVC bound.
- [x] Local-store PVC bound.
- [x] Persistent-config PVC bound.
- [x] All Kubecost PVCs use Longhorn.
- [x] Longhorn replica target set to two.
- [x] Frontend exposed through MetalLB.
- [x] Frontend assigned `192.168.2.26`.
- [x] Ansible observability phase completes without failure.
- [x] Helm owns the final `pricing-configs` ConfigMap.
- [x] LoadBalancer pricing warning documented as nonfatal.
- [ ] Kalaxy3 custom hardware and electricity pricing calibrated.
- [ ] Final repository changes committed and pushed.

## Operational Status

At the completion of this work:

```text
Deployment:          Complete
Scheduling:          Complete
Persistent storage: Complete
Network access:      Complete
Data collection:     Operational
Pod stability:       Healthy
Ansible rebuild:     Documented
Custom cost model:   Not calibrated
Known warning:       LoadBalancer pricing only
```
