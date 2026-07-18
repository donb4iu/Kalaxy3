# Longhorn, Kubecost, and Intel Node Preparation

**Project:** Kalaxy3  
**Date:** July 17, 2026  
**Status:** Ansible design checkpoint before completing the MinIO changes  
**Document path:** `markdown/installation/longhorn-kubecost-intel-node-preparation.md`

## Purpose

This document records the storage and scheduling changes made after the initial
Kubecost deployment failed on the Raspberry Pi cluster.

It is intended to provide enough information to reproduce the design when
rebuilding the Kalaxy3 cluster.

The key decisions were:

- Keep MinIO storage on the five Raspberry Pi nodes.
- Install Longhorn only on the three Intel/AMD64 nodes.
- Store Longhorn data on each Intel node's dedicated 1 TB HDD.
- Mount each Intel HDD at `/mnt/longhorn`.
- Run Kubecost only on explicitly labeled AMD64 nodes.
- Store Kubecost's active ClickHouse database on Longhorn block storage.
- Do not use NFS, MinIO, or K3s `local-path` for the active ClickHouse database.
- Configure MinIO separately as object storage after the Longhorn work is
  complete.
- Finish and validate the Ansible changes before adding Intel nodes to the
  inventory and cluster.

## Existing cluster

The current K3s cluster contains five Raspberry Pi 4 nodes:

| Node | Address | K3s role | Data mount |
|---|---|---|---|
| `arm64-01` | `192.168.2.51` | Server | `/mnt/minio` |
| `arm64-02` | `192.168.2.52` | Server | `/mnt/minio` |
| `arm64-03` | `192.168.2.53` | Server | `/mnt/minio` |
| `arm64-04` | `192.168.2.54` | Agent | `/mnt/minio` |
| `arm64-05` | `192.168.2.55` | Agent | `/mnt/minio` |

Each Pi has a dedicated 1 TB HDD intended for MinIO.

The future Intel nodes are expected to be:

| Node | Expected address | Intended storage |
|---|---|---|
| `amd64-01` | `192.168.2.61` | Longhorn |
| `amd64-02` | `192.168.2.62` | Longhorn |
| `amd64-03` | `192.168.2.63` | Longhorn |

Each Intel node has a dedicated 1 TB HDD that will be mounted at:

```text
/mnt/longhorn
```

## Storage architecture

The eight 1 TB data disks are divided by workload:

```text
Five Raspberry Pi nodes
└── 5 × 1 TB HDD
    └── /mnt/minio
        └── MinIO distributed object storage

Three Intel/AMD64 nodes
└── 3 × 1 TB HDD
    └── /mnt/longhorn
        └── Longhorn replicated Kubernetes block storage
```

The two storage systems must not use the same disk or mount path.

### MinIO responsibilities

MinIO is intended to provide S3-compatible object storage for:

- Kubecost federated and long-term cost data
- Longhorn backups
- Application object data
- Backup archives

MinIO does not replace the active ClickHouse block-storage volume.

### Longhorn responsibilities

Longhorn is intended to provide persistent block volumes for:

- Kubecost's embedded ClickHouse database
- Kubecost persistent configuration
- Future stateful Kubernetes workloads requiring block storage

The Longhorn disks exist only on the Intel nodes.

## Why Kubecost was changed

The first Kubecost 3.2.1 installation was attempted on the Pi-only ARM64
cluster.

Helm created most Kubecost resources successfully, but the aggregator
StatefulSet never became ready:

```text
kubecost-aggregator   0/1
```

The aggregator logs showed:

```text
starting embedded clickhouse server
Illegal instruction (core dumped) clickhouse-server
ERROR - CH server did not come up after 100 attempts
```

The Raspberry Pi 4 CPU could not execute an instruction used by the embedded
ClickHouse binary.

This was not caused by:

- Helm timeout duration
- MetalLB
- Service configuration
- Image pulling
- PVC provisioning
- NFS permissions
- Kubernetes readiness probes

Increasing the Helm timeout would not correct the CPU incompatibility.

## Why NFS and local-path were rejected

The initial installation placed Kubecost persistent volumes on `nfs-ssd`.

That was changed because the active ClickHouse database needs persistent
block storage rather than NFS-backed file storage.

K3s `local-path` was also rejected as the final design because it ties the
volume to one machine without Longhorn replication or storage management.

The final design is:

```text
Kubecost ClickHouse active database
└── Longhorn ReadWriteOnce block volume

Kubecost federated and long-term object data
└── MinIO S3-compatible object storage
```

## Scheduling design

Labels separate the storage and application responsibilities.

### Raspberry Pi MinIO nodes

The five Pis use:

```text
kalaxy3.io/minio=true
```

MinIO workloads will also require:

```text
kubernetes.io/arch=arm64
```

The existing Ansible inventory already contains:

```yaml
minio_nodes:
  hosts:
    arm64-01:
    arm64-02:
    arm64-03:
    arm64-04:
    arm64-05:
```

### Intel Longhorn nodes

The Intel nodes will use:

```text
kalaxy3.io/longhorn=true
node.longhorn.io/create-default-disk=true
```

Longhorn data will be created only on nodes carrying the Longhorn disk label.

### Intel Kubecost nodes

Kubecost workloads will require both:

```text
kubernetes.io/arch=amd64
kalaxy3.io/kubecost=true
```

This prevents Kubecost components from being scheduled onto Raspberry Pi
nodes.

## Planned Intel inventory groups

The Intel nodes should not be added to the active inventory until:

- Ubuntu is installed.
- Static addresses are assigned.
- SSH authentication works.
- The Ansible account works with privilege escalation.
- The dedicated HDD is mounted at `/mnt/longhorn`.

Once those prerequisites are complete, add the following groups to:

```text
infrastructure/k3s-homelab/inventory/hosts.yml
```

```yaml
longhorn_nodes:
  hosts:
    amd64-01:
    amd64-02:
    amd64-03:

kubecost_nodes:
  hosts:
    amd64-01:
    amd64-02:
    amd64-03:
```

The nodes must also be added under the appropriate `k3s_servers` or
`k3s_agents` inventory group.

The `minio_nodes` group remains unchanged and must contain only the five Pis.

## Longhorn host prerequisites

Every Intel node that stores Longhorn volumes must have the required host
packages installed.

The Ansible prerequisite task installs:

```yaml
- open-iscsi
- nfs-common
- cryptsetup
- dmsetup
```

The iSCSI service must be enabled and running:

```bash
sudo systemctl enable --now iscsid
sudo systemctl status iscsid
```

Before Longhorn installation, verify that `/mnt/longhorn` is the dedicated
1 TB HDD and not the operating-system filesystem:

```bash
findmnt /mnt/longhorn
df -h /mnt/longhorn
lsblk -f
```

## Longhorn variables

The intended Longhorn variables are:

```yaml
install_longhorn: true
longhorn_data_path: /mnt/longhorn
longhorn_replica_count: 1
```

The Longhorn chart version must be pinned in the variables file rather than
using an unversioned latest release.

The initially discussed version was:

```yaml
longhorn_version: "1.12.0"
```

Verify that the pinned version exists in the configured Longhorn chart
repository before the first installation.

### Replica progression

Use one replica when only the first Intel node is present:

```yaml
longhorn_replica_count: 1
```

After all three Intel nodes are joined, healthy, and have registered
Longhorn disks, change the default to:

```yaml
longhorn_replica_count: 2
```

Two replicas provide redundancy while reducing the write and rebuild overhead
that three replicas would impose on spinning HDDs.

Existing volumes may require a separate replica-count update after changing
the default.

## Longhorn Ansible files

The Longhorn implementation uses these repository files:

```text
infrastructure/k3s-homelab/playbooks/longhorn-prerequisites.yml
infrastructure/k3s-homelab/playbooks/tasks/longhorn.yml
infrastructure/k3s-homelab/playbooks/templates/longhorn-values.yml.j2
infrastructure/k3s-homelab/playbooks/platform.yml
```

### `longhorn-prerequisites.yml`

This playbook prepares the AMD64 hosts before Longhorn installation.

It must:

- Run with privilege escalation.
- Gather hardware architecture facts.
- Install Longhorn host prerequisites only on `x86_64` hosts.
- Enable and start `iscsid`.

### `tasks/longhorn.yml`

This task file must:

1. Detect eligible AMD64 Kubernetes nodes.
2. Skip Longhorn when no Intel node is present.
3. Label only intended Longhorn nodes.
4. Apply `node.longhorn.io/create-default-disk=true`.
5. Render the Longhorn values template.
6. Install the pinned Longhorn chart.
7. Wait for Longhorn to become ready.
8. Verify that the `longhorn` StorageClass exists.

### `longhorn-values.yml.j2`

The values template must configure:

```yaml
defaultSettings:
  defaultDataPath: /mnt/longhorn
```

It must restrict Longhorn storage components and default disk creation to the
intended Intel nodes.

The `longhorn` StorageClass should not replace the existing default
StorageClass globally. Workloads that need Longhorn should request it
explicitly.

## Platform ordering

Edit:

```text
infrastructure/k3s-homelab/playbooks/platform.yml
```

The required phase ordering is:

```text
K3s cluster
    ↓
MinIO on Raspberry Pi nodes
    ↓
Longhorn on Intel nodes
    ↓
Observability
    ↓
Kubecost on Intel nodes using Longhorn
```

The relevant task order should be:

```yaml
- name: Run MinIO phase
  ansible.builtin.include_tasks: tasks/minio.yml
  when: install_minio | bool

- name: Run Longhorn storage phase
  ansible.builtin.include_tasks: tasks/longhorn.yml
  when: install_longhorn | bool

- name: Run observability phase
  ansible.builtin.include_tasks: tasks/observability.yml
  when: install_observability | bool
```

Kubecost must never be installed before the `longhorn` StorageClass exists.

## Kubecost Ansible behavior

The Kubecost tasks are in:

```text
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
```

The task sequence is:

1. Install Prometheus and Grafana.
2. Query Kubernetes for an eligible AMD64 Kubecost node.
3. Skip Kubecost when no eligible Intel node exists.
4. Render the Kubecost values template when a node exists.
5. Install Kubecost using the rendered values.
6. Wait for the Kubecost workloads to become ready.

The node query requires:

```text
kubernetes.io/arch=amd64
kalaxy3.io/kubecost=true
```

This allows:

```yaml
install_observability: true
install_kubecost: true
```

to remain enabled while the cluster is Pi-only.

In that state, `install_kubecost: true` means:

> Install Kubecost when a compatible and explicitly labeled Intel node exists.

## Kubecost values

The Kubecost values template is:

```text
infrastructure/k3s-homelab/playbooks/templates/kubecost-values.yml.j2
```

All Kubecost workloads are constrained to:

```yaml
nodeSelector:
  kubernetes.io/arch: amd64
  kalaxy3.io/kubecost: "true"
```

The aggregator storage must use Longhorn:

```yaml
aggregator:
  nodeSelector:
    kubernetes.io/arch: amd64
    kalaxy3.io/kubecost: "true"

  persistentConfigsStorage:
    storageClass: longhorn
    storageRequest: 1Gi

  aggregatorDbStorage:
    storageClass: longhorn
    storageRequest: 128Gi
```

The frontend LoadBalancer address remains:

```text
192.168.2.26
```

MinIO federated-storage integration will be configured separately after the
MinIO deployment is finalized.

## Failed Kubecost cleanup

The failed Pi-based Kubecost installation created PVCs using the previous
storage configuration.

Before reinstalling Kubecost with Longhorn, remove the failed release:

```bash
ssh pi@192.168.2.51 \
  'sudo helm \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  uninstall kubecost \
  --namespace kubecost || true'
```

Remove the old namespace and PVCs:

```bash
kubectl delete namespace kubecost --ignore-not-found
```

This is required because an existing PVC's StorageClass cannot be changed from
the old storage class to `longhorn`.

## Required deployment sequence

### Phase 1: Complete the repository changes

Before adding Intel nodes:

1. Finish the Longhorn prerequisite playbook.
2. Finish the Longhorn tasks.
3. Finish the Longhorn values template.
4. Confirm platform ordering.
5. Confirm Kubecost uses `storageClass: longhorn`.
6. Confirm Kubecost requires AMD64 and its explicit node label.
7. Complete the MinIO Pi-only scheduling changes.
8. Run the full Ansible syntax check.
9. Commit the repository changes.

### Phase 2: Prepare the Intel machines

For each Intel machine:

1. Install Ubuntu.
2. Configure its static address.
3. Configure SSH and the Ansible account.
4. Prepare the dedicated 1 TB HDD.
5. Mount the HDD at `/mnt/longhorn`.
6. Add the mount to `/etc/fstab`.
7. Install or allow Ansible to install Longhorn prerequisites.
8. Verify `iscsid`.

### Phase 3: Add the first Intel node

1. Add `amd64-01` to the Ansible inventory.
2. Join it to K3s.
3. Confirm that Kubernetes reports `amd64`.
4. Label it for Longhorn and Kubecost.
5. Install Longhorn with one replica.
6. Verify that `/mnt/longhorn` is registered.
7. Verify that the `longhorn` StorageClass exists.

### Phase 4: Add the remaining Intel nodes

1. Add `amd64-02`.
2. Add `amd64-03`.
3. Confirm both nodes are Ready.
4. Confirm both Longhorn disks are schedulable.
5. Change the default replica count from one to two.
6. Verify replica placement across separate Intel nodes.

### Phase 5: Install Kubecost

Install Kubecost only after:

```bash
kubectl get storageclass longhorn
kubectl get nodes \
  -L kubernetes.io/arch,kalaxy3.io/longhorn,kalaxy3.io/kubecost
kubectl get nodes.longhorn.io \
  --namespace longhorn-system
```

show the expected Longhorn and Kubecost nodes.

## Validation before adding Intel nodes

From:

```text
/Users/dbuddenbaum/dvlp/Kalaxy3/infrastructure/k3s-homelab
```

run:

```bash
ansible-inventory \
  -i inventory/hosts.yml \
  --graph
```

Run the complete syntax check:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/k3s.yml \
  --syntax-check \
  --vault-id kalaxy3@prompt
```

Parse the YAML files:

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
  playbooks/tasks/longhorn.yml \
  playbooks/templates/longhorn-values.yml.j2 \
  playbooks/tasks/observability.yml \
  playbooks/templates/kubecost-values.yml.j2
```

## Validation after Longhorn installation

Check the Longhorn pods:

```bash
kubectl get pods \
  --namespace longhorn-system \
  --output=wide
```

Check the StorageClass:

```bash
kubectl get storageclass longhorn
```

Check Longhorn's node and disk records:

```bash
kubectl get nodes.longhorn.io \
  --namespace longhorn-system
```

Verify labels:

```bash
kubectl get nodes \
  -L kubernetes.io/arch,\
kalaxy3.io/minio,\
kalaxy3.io/longhorn,\
kalaxy3.io/kubecost,\
node.longhorn.io/create-default-disk
```

Expected responsibility split:

```text
arm64-01 through arm64-05
├── kubernetes.io/arch=arm64
├── kalaxy3.io/minio=true
└── no Longhorn disk label

amd64-01 through amd64-03
├── kubernetes.io/arch=amd64
├── kalaxy3.io/longhorn=true
├── kalaxy3.io/kubecost=true
├── node.longhorn.io/create-default-disk=true
└── no MinIO label
```

## Validation after Kubecost installation

Confirm all Kubecost pods run on Intel nodes:

```bash
kubectl get pods \
  --namespace kubecost \
  --output=wide
```

Confirm the aggregator database uses Longhorn:

```bash
kubectl get pvc \
  --namespace kubecost \
  aggregator-db-storage-kubecost-aggregator-0
```

Expected StorageClass:

```text
longhorn
```

Confirm the frontend address:

```bash
kubectl get service \
  kubecost-frontend \
  --namespace kubecost
```

Expected external address:

```text
192.168.2.26
```

## Rebuild summary

For a future cluster rebuild:

1. Build the Pi K3s cluster.
2. Mount the five Pi HDDs at `/mnt/minio`.
3. Deploy MinIO only to the `minio_nodes` inventory group.
4. Build and join the three Intel nodes.
5. Mount each Intel HDD at `/mnt/longhorn`.
6. Install Longhorn prerequisites on the Intel nodes.
7. Label the Intel nodes for Longhorn and Kubecost.
8. Install Longhorn before Kubecost.
9. Use one Longhorn replica with one Intel node.
10. Change to two replicas after all three Intel nodes are healthy.
11. Install Kubecost only after the `longhorn` StorageClass is ready.
12. Store ClickHouse on Longhorn.
13. Configure MinIO separately for federated and backup object storage.
14. Verify that no MinIO workload runs on Intel.
15. Verify that no Kubecost workload runs on ARM.

## References

Official Longhorn documentation:

```text
https://longhorn.io/docs/latest/deploy/install/
https://longhorn.io/docs/latest/concepts/
https://longhorn.io/docs/latest/best-practices/
```

The repository files remain the source of truth for the exact chart versions,
Ansible variables, labels, resource sizes, and Helm values used by Kalaxy3.
