# Kalaxy3 AMD64 Node and Longhorn Installation Evidence and Rebuild Guide

**Project:** Kalaxy3  
**Completed:** July 19, 2026, America/Chicago  
**Kubernetes timestamps:** July 20, 2026 UTC  
**Target path:** `markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md`  
**Node:** `amd64-01`  
**Node address:** `192.168.2.61`  
**K3s version:** `v1.36.2+k3s1`  
**Longhorn version:** `v1.12.0`

## Purpose

This page records the addition of the first AMD64 node to Kalaxy3, the network
recovery required after the Ubuntu installation, the storage decisions made for
its three physical disks, the Ansible changes that safely prepared the dedicated
Longhorn HDD, the K3s agent join, the Longhorn installation, and the evidence
used to prove that dynamic block storage worked correctly.

The document is intended to be sufficient for rebuilding this part of Kalaxy3
without depending on memory or rediscovering why each disk and node restriction
exists.

## Final validated result

```text
AMD64 node:             amd64-01
Address:                192.168.2.61
Architecture:           x86_64 / Kubernetes amd64
K3s role:               agent
K3s status:             Ready
K3s version:            v1.36.2+k3s1

Operating-system disk:  /dev/nvme0n1, Samsung SSD 990 EVO 1 TB
Root mount:             /
Longhorn disk:          /dev/sda, ST1000VM002-1SD1 1 TB HDD
Longhorn mount:         /mnt/longhorn
Longhorn filesystem:    ext4
Future RAG cache disk:  /dev/nvme1n1, Samsung SSD 990 EVO Plus 4 TB

Longhorn node:          Ready and schedulable
Longhorn disk:          Ready and schedulable
Longhorn StorageClass:  longhorn
Reclaim policy:         Retain
Replica count:          1 while only one AMD64 storage node exists
Functional test:        PVC bound, volume attached, file written and read
Test cleanup:           PVC, PV, and Longhorn volume removed
```

## Architecture after this change

```text
Kalaxy3 K3s cluster
├── arm64-01  192.168.2.51  control-plane, etcd
├── arm64-02  192.168.2.52  control-plane, etcd
├── arm64-03  192.168.2.53  control-plane, etcd
├── arm64-04  192.168.2.54  agent
├── arm64-05  192.168.2.55  agent
└── amd64-01  192.168.2.61  agent
    ├── 1 TB NVMe  -> Ubuntu and K3s root filesystem
    ├── 1 TB HDD   -> /mnt/longhorn
    └── 4 TB NVMe  -> reserved for future local RAG/PDF cache
```

The five Raspberry Pi HDDs remain dedicated to distributed MinIO at
`/mnt/minio`. The AMD64 HDD is dedicated to Longhorn at `/mnt/longhorn`.
MinIO and Longhorn must never be configured to use the same disk or mount path.

## Key design decisions

### AMD64 nodes use normal Ubuntu installation plus Ansible

The Raspberry Pi nodes use the Ubuntu preinstalled image and custom cloud-init
files. The AMD64 nodes do not use that Pi flashing workflow.

The intended AMD64 sequence is:

```text
Install Ubuntu Server normally from ISO
→ establish working network connectivity
→ enable SSH and install the administrator key
→ run Ansible host preparation
→ join the node to K3s
→ install AMD64-only services
```

A hostname left with an installer-generated `new-*` prefix would not prove that
an AMD64 cloud-init file failed, because custom cloud-init was not the selected
AMD64 provisioning mechanism.

### The HDD is the only Longhorn candidate

The host contained three disks:

```text
NAME                        SIZE ROTA TYPE FSTYPE      MOUNTPOINT MODEL
sda                       931.5G    1 disk ext4                  ST1000VM002-1SD1
nvme1n1                     3.6T    0 disk                       Samsung SSD 990 EVO Plus 4TB
├─nvme1n1p1                   1G    0 part vfat
├─nvme1n1p2                   2G    0 part ext4
└─nvme1n1p3                 3.6T    0 part LVM2_member
  └─ubuntu--vg-ubuntu--lv   100G    0 lvm  ext4
nvme0n1                   931.5G    0 disk                       Samsung SSD 990 EVO 1TB
├─nvme0n1p1                   1G    0 part vfat        /boot/efi
└─nvme0n1p2               930.5G    0 part ext4        /
```

The storage assignments are deliberate:

| Device | Assignment | Reason |
|---|---|---|
| `/dev/nvme0n1` | Ubuntu root and K3s runtime | It already contains `/` and `/boot/efi`; it must be protected from storage automation. |
| `/dev/sda` | `/mnt/longhorn` | It is the dedicated rotational 1 TB HDD and already contains ext4. |
| `/dev/nvme1n1` | Reserved | It is intended for a future high-speed local cache for PDF/RAG processing and currently contains an old LVM layout. |

### The 4 TB NVMe remains untouched

The 4 TB NVMe is not blank. It contains GPT partitions and an LVM physical
volume with a 100 GB logical volume. No Ansible task created, removed, formatted,
or mounted anything on this device during the Longhorn work.

Before using it for RAG caching in the future:

1. Confirm that the existing LVM data is not needed.
2. Record the disk model and serial.
3. Remove the old LVM and partition layout only as a deliberate, separately
   reviewed operation.
4. Create a dedicated filesystem and mount path such as `/mnt/rag-cache`.
5. Expose it as node-local cache storage, not as part of the rotational Longhorn
   disk pool.

The cache should contain rebuildable material such as downloaded PDFs,
extracted text, OCR products, embeddings, indexes, model artifacts, and other
performance-oriented data. Irreplaceable application state should remain on
replicated or backed-up storage.

### One Longhorn replica is correct for the first node

Only `amd64-01` currently provides Longhorn storage. The replica count was
therefore changed from `2` to `1`.

A replica count of two cannot provide two-node resilience when only one eligible
storage node exists and can prevent new volumes from scheduling correctly.
After `amd64-02` joins with its own independent `/mnt/longhorn` disk, increase
the default to two and update existing important volumes to two replicas.

## Network recovery

### Symptom

The add-in network adapter was active in BIOS but appeared inactive after Ubuntu
started. Ubuntu detected two interfaces:

```text
enp4s0  DOWN
enp5s0  DOWN
```

The installed Netplan configuration referenced `enp4s0`, while the connected
physical adapter was `enp5s0`. Manually bringing up `enp5s0` restored carrier.

### Permanent network configuration

The cloud-init-generated Netplan file was removed from the active Netplan
directory, cloud-init network regeneration was disabled, and a single manually
managed file was retained:

```text
/etc/netplan/50-k3s-uplink.yaml
```

Representative configuration:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: false
      addresses:
        - 192.168.2.61/24
      routes:
        - to: default
          via: 192.168.2.1
      nameservers:
        addresses:
          - 192.168.2.1
          - 1.1.1.1
          - 8.8.8.8
      optional: true
```

Cloud-init network regeneration was disabled with:

```text
/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
```

```yaml
network: {config: disabled}
```

### Network validation

After reboot, the static configuration persisted:

```text
enp5s0  UP  192.168.2.61/24
```

The node successfully reached the first K3s server:

```bash
ping -c 3 192.168.2.51
```

## SSH and sudo bootstrap

The Mac mini SSH key was installed with:

```bash
ssh-copy-id dbuddenbaum@192.168.2.61
```

Observed result:

```text
Number of key(s) added: 1
```

Passwordless sudo was then configured for Ansible in:

```text
/etc/sudoers.d/90-k3s-admin
```

```text
dbuddenbaum ALL=(ALL) NOPASSWD:ALL
```

Validation:

```bash
ssh dbuddenbaum@192.168.2.61 \
  'sudo -n true && echo "sudo ready"'
```

## Repository changes

The completed work was committed and pushed to `main` as commit:

```text
af6857f  Add amd64 Longhorn node and dedicated storage provisioning
```

The local commit was rebased over two generated-documentation commits before a
normal, non-force push.

### Inventory membership

**File:**

```text
infrastructure/k3s-homelab/inventory/hosts.yml
```

`amd64-01` was added as a K3s agent with its own SSH user:

```yaml
k3s_agents:
  hosts:
    arm64-04:
      ansible_host: 192.168.2.54
    arm64-05:
      ansible_host: 192.168.2.55
    amd64-01:
      ansible_host: 192.168.2.61
      ansible_user: dbuddenbaum
```

A dedicated Longhorn inventory group was added:

```yaml
longhorn_nodes:
  hosts:
    amd64-01:
```

This prevents the Longhorn disk preparation play from running on Raspberry Pi
nodes or unrelated AMD64 nodes.

### Host-specific disk safety variables

**File:**

```text
infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
```

```yaml
---
longhorn_disk_expected_model: ST1000VM002-1SD1
longhorn_disk_min_bytes: 800000000000
longhorn_disk_max_bytes: 1200000000000
longhorn_allowed_filesystems:
  - ext4
  - xfs

# Both NVMe devices are intentionally excluded by rotational-disk discovery.
```

The model assertion makes the first node especially conservative. Future nodes
may use different HDD models and should receive their own host-specific value.

### Global Longhorn variables

**File:**

```text
infrastructure/k3s-homelab/inventory/group_vars/all.yml
```

Relevant values after this change:

```yaml
install_longhorn: true
longhorn_version: "1.12.0"
longhorn_data_path: /mnt/longhorn

# Use one replica until amd64-02 joins. Increase this to 2 afterward and
# update existing Longhorn volumes to two replicas.
longhorn_replica_count: 1
```

`install_longhorn` was initially left false while the node and mount were being
validated, then changed to true immediately before the Longhorn platform phase.

### Safe Longhorn disk preparation

**File:**

```text
infrastructure/k3s-homelab/playbooks/longhorn-prerequisites.yml
```

The play now targets only `longhorn_nodes` and performs these operations:

1. Assert that the host architecture is `x86_64`.
2. Install `open-iscsi`, `nfs-common`, `cryptsetup`, and `dmsetup`.
3. Enable `iscsid`.
4. Read the complete block-device inventory with `lsblk --json --bytes`.
5. Select only whole disks that are:
   - rotational;
   - non-removable;
   - between 800 GB and 1.2 TB.
6. Require exactly one candidate.
7. Require the exact expected disk model.
8. Discover and protect the physical root disk.
9. Refuse a disk mounted at a different path.
10. Require an existing ext4 or XFS filesystem and valid UUID.
11. Refuse to format a disk.
12. Create `/mnt/longhorn`.
13. Mount the disk by UUID using `defaults,noatime`.
14. Persist the mount in `/etc/fstab`.
15. Verify the resulting mount.

The architecture assertion was updated to avoid Ansible's deprecated injected
fact variables:

```yaml
- name: Confirm Longhorn nodes use the AMD64 architecture
  ansible.builtin.assert:
    that:
      - ansible_facts["architecture"] == "x86_64"
    fail_msg: >-
      {{ inventory_hostname }} is {{ ansible_facts["architecture"] }}, not x86_64.
```

### Why the playbook refuses to format disks

Automated discovery is useful for selecting the intended disk, but formatting
is destructive. The playbook therefore stops when the selected disk does not
already contain an approved filesystem.

A future rebuild that uses a blank replacement HDD must include a separate,
explicitly reviewed disk-initialization step before this playbook runs. The
normal Longhorn prerequisite play must continue to refuse formatting.

## Longhorn disk preparation evidence

### Check-mode run

Command:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-01 \
  --check \
  --diff \
  --vault-id kalaxy3@prompt
```

Observed selection:

```text
Node: amd64-01
Device: /dev/sda
Model: ST1000VM002-1SD1
Filesystem: ext4
Mount: /mnt/longhorn
```

The check-mode recap was:

```text
amd64-01 : ok=20 changed=4 unreachable=0 failed=0 skipped=1
```

The apparent changes represented what Ansible would create or mount; check mode
did not modify the node.

### Real run

The same playbook was run without `--check`.

Observed result:

```text
amd64-01 : ok=21 changed=4 unreachable=0 failed=0 skipped=0
```

The mount verification passed and the play reported:

```text
Node: amd64-01
Device: /dev/sda
Model: ST1000VM002-1SD1
Filesystem: ext4
Mount: /mnt/longhorn
```

### Idempotency evidence

A later check-mode run reported no changes:

```text
amd64-01 : ok=20 changed=0 unreachable=0 failed=0 skipped=1
```

This established that the package state, iSCSI service, disk selection,
filesystem validation, mount directory, UUID-based fstab entry, and active mount
were all stable.

## K3s join evidence

The AMD64 node was joined using the existing Intel phase:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-08-intel.yml \
  --vault-id kalaxy3@prompt
```

The phase:

- reran common K3s prerequisites idempotently across all six nodes;
- validated all five Pi MinIO mounts without involving `amd64-01`;
- reran the dedicated Longhorn disk preparation on `amd64-01`;
- read the existing cluster token from `arm64-01`;
- wrote the K3s agent configuration on `amd64-01`;
- installed and started `k3s-agent`;
- exported the kubeconfig back to the Mac.

Relevant observed tasks:

```text
TASK [Create K3s configuration directory]
changed: [amd64-01]

TASK [Write K3s agent configuration]
changed: [amd64-01]

TASK [Install and join K3s agent]
changed: [amd64-01]

RUNNING HANDLER [Restart K3s agent]
changed: [amd64-01]

TASK [Wait for K3s agent service]
ok: [amd64-01]
```

Final recap:

```text
amd64-01 : ok=34 changed=7 unreachable=0 failed=0 skipped=0
```

Kubernetes validation showed:

```text
NAME       STATUS   ROLES                VERSION        ARCH
amd64-01   Ready    <none>               v1.36.2+k3s1   amd64
arm64-01   Ready    control-plane,etcd   v1.36.2+k3s1   arm64
arm64-02   Ready    control-plane,etcd   v1.36.2+k3s1   arm64
arm64-03   Ready    control-plane,etcd   v1.36.2+k3s1   arm64
arm64-04   Ready    <none>               v1.36.2+k3s1   arm64
arm64-05   Ready    <none>               v1.36.2+k3s1   arm64
```

## Longhorn installation

### Initial skipped run

The first Longhorn-only platform command skipped the phase because
`install_longhorn` was still false:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars platform_phase=longhorn \
  --vault-id kalaxy3@prompt
```

This was correct feature-flag behavior rather than an installation failure.

### Enabled installation

After setting:

```yaml
install_longhorn: true
longhorn_replica_count: 1
```

The same normal command was run without an override:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars platform_phase=longhorn \
  --vault-id kalaxy3@prompt
```

Successful tasks included:

```text
TASK [Run Longhorn storage phase]
included: playbooks/tasks/longhorn.yml for arm64-01

TASK [Find AMD64 Kubernetes nodes]
ok: [arm64-01]

TASK [Label AMD64 nodes for Longhorn and Kubecost]
changed: [arm64-01]

TASK [Write Longhorn Helm values]
changed: [arm64-01]

TASK [Install Longhorn]
changed: [arm64-01]

TASK [Verify the Longhorn StorageClass]
ok: [arm64-01]
```

Final recap:

```text
arm64-01 : ok=12 changed=3 unreachable=0 failed=0 skipped=5
```

Although Helm was executed from `arm64-01`, the generated Longhorn values and
node labels restricted Longhorn workloads and default disk creation to the
eligible AMD64 node.

## Longhorn placement and health evidence

### Pod placement

All Longhorn pods were running on `amd64-01`:

```text
csi-attacher-*             1/1  Running  amd64-01
csi-provisioner-*          1/1  Running  amd64-01
csi-resizer-*              1/1  Running  amd64-01
csi-snapshotter-*          1/1  Running  amd64-01
engine-image-*             1/1  Running  amd64-01
instance-manager-*         1/1  Running  amd64-01
longhorn-csi-plugin-*      3/3  Running  amd64-01
longhorn-driver-deployer-* 1/1  Running  amd64-01
longhorn-manager-*         2/2  Running  amd64-01
longhorn-ui-*              1/1  Running  amd64-01
```

No Longhorn pod was scheduled on an ARM64 node.

### Kubernetes node labels

```text
NAME       STATUS   ARCH    CREATE-DEFAULT-DISK   LONGHORN
amd64-01   Ready    amd64   true                  true
arm64-01   Ready    arm64
arm64-02   Ready    arm64
arm64-03   Ready    arm64
arm64-04   Ready    arm64
arm64-05   Ready    arm64
```

### Longhorn node state

```text
NAME       READY   ALLOWSCHEDULING   SCHEDULABLE
amd64-01   True    true              True
```

The Longhorn node object registered one filesystem disk:

```text
Path:                 /mnt/longhorn
Allow scheduling:     true
Disk type:            filesystem
Storage maximum:      983351140352 bytes
Storage available:    983249715200 bytes at validation
Storage scheduled:    0 bytes before the functional test
```

The disk conditions were:

```text
Ready:        True
Schedulable:  True
```

### StorageClasses

The cluster contained:

```text
NAME                   PROVISIONER                                             RECLAIMPOLICY   VOLUMEBINDINGMODE
local-path (default)   rancher.io/local-path                                   Delete          WaitForFirstConsumer
longhorn               driver.longhorn.io                                      Retain          Immediate
longhorn-static        driver.longhorn.io                                      Delete          Immediate
minio-local            kubernetes.io/no-provisioner                            Retain          WaitForFirstConsumer
nfs-hdd                cluster.local/nfs-hdd-nfs-subdir-external-provisioner   Retain          Immediate
nfs-ssd                cluster.local/nfs-ssd-nfs-subdir-external-provisioner   Retain          Immediate
```

`local-path` intentionally remained the cluster default. Workloads that need
Longhorn must request `storageClassName: longhorn` explicitly unless a future
architecture decision changes the default.

## Functional volume test

### Create the test claim

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: longhorn-test
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 1Gi
EOF
```

The claim initially appeared `Pending` when checked at age zero, then bound
normally:

```text
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
longhorn-test   Bound    pvc-9ae54f0e-9849-414a-9369-4d277f4447ed   1Gi        RWO            longhorn
```

Before a pod used it, the Longhorn volume correctly appeared detached:

```text
STATE      ROBUSTNESS   NODE
detached   unknown
```

### Create a pod and write data

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: longhorn-test
  namespace: default
spec:
  nodeSelector:
    kubernetes.io/hostname: amd64-01
  containers:
    - name: test
      image: busybox:1.36
      command:
        - sh
        - -c
        - |
          echo "Longhorn test $(date)" > /data/test.txt
          cat /data/test.txt
          sleep 3600
      volumeMounts:
        - name: storage
          mountPath: /data
  volumes:
    - name: storage
      persistentVolumeClaim:
        claimName: longhorn-test
EOF
```

The pod became ready:

```text
NAME            READY   STATUS    RESTARTS
longhorn-test   1/1     Running   0
```

The log and direct file read both returned:

```text
Longhorn test Mon Jul 20 02:38:04 UTC 2026
```

### Attached-volume evidence

While the pod was running:

```text
NAME                                       STATE      ROBUSTNESS   SIZE         NODE
pvc-9ae54f0e-9849-414a-9369-4d277f4447ed   attached   healthy      1073741824   amd64-01
```

Longhorn created one running replica on the intended disk:

```text
NAME                                                  STATE     NODE       DISK
pvc-9ae54f0e-9849-414a-9369-4d277f4447ed-r-2133cd4d   running   amd64-01   35f9c7ca-fc4e-427f-8e56-213f26c1d821
```

The instance manager and engine image were both the expected Longhorn v1.12.0
components.

### Test cleanup

The test pod and PVC were deleted. Because the `longhorn` StorageClass uses the
`Retain` reclaim policy, the PV became `Released` and the detached Longhorn
volume remained until explicitly removed.

Cleanup commands:

```bash
TEST_VOLUME="pvc-9ae54f0e-9849-414a-9369-4d277f4447ed"

kubectl delete pv "${TEST_VOLUME}"

kubectl delete volumes.longhorn.io \
  -n longhorn-system \
  "${TEST_VOLUME}"
```

Final result:

```text
No resources found in longhorn-system namespace.
```

This final message referred to Longhorn volume resources, not the Longhorn
installation itself. The Longhorn pods, node object, disk, CRDs, and
StorageClasses remained installed.

## Test interpretation

The successful test proved all of the following:

- The Longhorn CSI provisioner created a 1 GiB volume.
- Kubernetes bound the claim to a Longhorn PV.
- Longhorn attached the volume to `amd64-01`.
- A replica was created on the registered `/mnt/longhorn` disk.
- The pod mounted the volume.
- The container wrote a file.
- The container read the same file.
- The volume reported `healthy` while attached.
- The volume detached when the consuming pod was removed.
- Retain-policy cleanup behavior was understood and handled deliberately.

The test did not complete a pod-delete-and-recreate persistence check because
the PVC was deleted before the pod was recreated. The successful write/read,
attachment, healthy replica, and clean detach were sufficient to validate the
installation. A later workload deployment will provide ongoing persistence
evidence.

## Known warnings and outstanding hardening

The Longhorn node reported two non-blocking conditions during validation.
Longhorn remained ready and schedulable, and the functional volume test passed.

### `multipathd` warning

Observed condition:

```text
Multipathd: False
Reason: MultipathdIsRunning
Message: multipathd is running with a known issue that affects Longhorn.
```

This node uses local disks and does not currently need multipath SAN support.
The intended remediation is to stop, disable, and mask `multipathd.service` and
`multipathd.socket`, then persist that behavior in Ansible.

Do not mark this remediation complete until the commands have actually been run
and the Longhorn condition has been rechecked.

### `dm_crypt` warning

Observed condition:

```text
KernelModulesLoaded: False
Reason: KernelModulesNotLoaded
Message: Kernel modules [dm_crypt] are not loaded
```

Unencrypted test volumes worked. Loading and persisting `dm_crypt` is still
recommended so the node passes all Longhorn prerequisite checks and can support
encrypted Longhorn volumes later.

Recommended Ansible tasks after validation:

```yaml
- name: Load the dm_crypt kernel module
  ansible.builtin.command:
    argv:
      - modprobe
      - dm_crypt
  changed_when: false

- name: Load dm_crypt after reboot
  ansible.builtin.copy:
    dest: /etc/modules-load.d/longhorn.conf
    owner: root
    group: root
    mode: "0644"
    content: |
      dm_crypt

- name: Disable multipathd services
  ansible.builtin.systemd_service:
    name: "{{ item }}"
    enabled: false
    state: stopped
    masked: true
  loop:
    - multipathd.service
    - multipathd.socket
```

## Rebuild procedure

### 1. Install Ubuntu Server on the AMD64 node

Install Ubuntu Server 24.04 LTS from the normal ISO. Create the
`dbuddenbaum` administrator account and enable OpenSSH Server.

Do not use the Raspberry Pi image-flashing workflow for AMD64 nodes.

### 2. Identify the active NIC

From the console:

```bash
ip -br link
lspci -nnk | sed -n '/Ethernet controller/,+5p'
sudo netplan get
```

Bring candidate interfaces up and check carrier when necessary:

```bash
sudo ip link set enp4s0 up
sudo ip link set enp5s0 up
```

Use the interface that reports carrier. On the validated `amd64-01` build, that
interface was `enp5s0`.

### 3. Create the permanent Netplan file

Retain one manually managed file:

```text
/etc/netplan/50-k3s-uplink.yaml
```

Assign:

```text
Address:  192.168.2.61/24
Gateway:  192.168.2.1
DNS:      192.168.2.1, 1.1.1.1, 8.8.8.8
```

Disable cloud-init network regeneration, apply Netplan, reboot, and verify the
address survives.

### 4. Bootstrap SSH access

```bash
ssh-copy-id dbuddenbaum@192.168.2.61
```

Create the passwordless sudo file and validate it with `visudo`.

### 5. Confirm disk identity before Ansible

```bash
ssh dbuddenbaum@192.168.2.61 \
  'sudo lsblk -o NAME,SIZE,ROTA,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL'
```

Requirements for this node:

```text
/dev/nvme0n1 -> root filesystem
/dev/sda     -> ST1000VM002-1SD1, ext4, Longhorn candidate
/dev/nvme1n1 -> reserved; no automated changes
```

Stop if the device model, size, filesystem, or root-disk mapping differs.
Update the host variables only after physically confirming the replacement
hardware.

### 6. Validate inventory

```bash
ansible-inventory \
  -i inventory/hosts.yml \
  --graph \
  --vault-id kalaxy3@prompt
```

`amd64-01` must appear in both:

```text
k3s_agents
longhorn_nodes
```

### 7. Dry-run Longhorn preparation

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-01 \
  --check \
  --diff \
  --vault-id kalaxy3@prompt
```

The selected device must be `/dev/sda`. Stop immediately if either NVMe appears
as the candidate.

### 8. Mount the Longhorn HDD

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-01 \
  --diff \
  --vault-id kalaxy3@prompt
```

Validate:

```bash
ssh dbuddenbaum@192.168.2.61 '
  findmnt /mnt/longhorn
  df -h /mnt/longhorn
  grep -F /mnt/longhorn /etc/fstab
  lsblk -o NAME,SIZE,ROTA,FSTYPE,MOUNTPOINTS,MODEL
'
```

Reboot once and confirm `/mnt/longhorn` mounts automatically.

### 9. Join K3s

Run the complete Intel phase rather than limiting the full K3s join play to one
host. The play needs access to the existing server group and cluster token.

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-08-intel.yml \
  --vault-id kalaxy3@prompt
```

Validate:

```bash
kubectl get nodes -o wide
kubectl get node amd64-01 \
  -L kubernetes.io/arch,kalaxy3.io/longhorn,kalaxy3.io/kubecost
```

### 10. Enable and install Longhorn

Use:

```yaml
install_longhorn: true
longhorn_replica_count: 1
```

Then run:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars platform_phase=longhorn \
  --vault-id kalaxy3@prompt
```

### 11. Validate Longhorn

```bash
kubectl get pods -n longhorn-system -o wide
kubectl get storageclass
kubectl get nodes \
  -L kubernetes.io/arch,node.longhorn.io/create-default-disk,kalaxy3.io/longhorn
kubectl get nodes.longhorn.io -n longhorn-system
kubectl get nodes.longhorn.io amd64-01 -n longhorn-system -o yaml
```

Required conditions:

```text
amd64-01 Kubernetes node: Ready
Longhorn node Ready: True
Longhorn node Schedulable: True
/mnt/longhorn disk Ready: True
/mnt/longhorn disk Schedulable: True
ARM64 Longhorn storage nodes: none
```

### 12. Run a functional PVC test

Create an explicitly Longhorn-backed PVC and a pod that writes and reads a file.
Confirm the volume becomes `attached` and `healthy`, and confirm one replica is
running on `amd64-01`.

When deleting a test PVC, remember that the StorageClass uses `Retain`. Remove
the released PV and Longhorn volume explicitly when the test data is no longer
needed.

## Operational checks

### Node and mount

```bash
kubectl get node amd64-01 -o wide

ssh dbuddenbaum@192.168.2.61 '
  systemctl is-active k3s-agent
  systemctl is-active iscsid
  findmnt /mnt/longhorn
  df -h /mnt/longhorn
'
```

### Longhorn health

```bash
kubectl get pods -n longhorn-system -o wide
kubectl get nodes.longhorn.io -n longhorn-system
kubectl get volumes.longhorn.io -n longhorn-system
kubectl get replicas.longhorn.io -n longhorn-system -o wide
```

### Conditions requiring attention

```bash
kubectl get nodes.longhorn.io amd64-01 \
  -n longhorn-system \
  -o jsonpath='{range .status.conditions[*]}{.type}: {.status} {.reason}{"\n"}{end}'
```

## Expansion procedure for `amd64-02`

When the second AMD64 node is available:

1. Give it `192.168.2.62`.
2. Add it to `k3s_agents` and `longhorn_nodes`.
3. Add host-specific disk model and safety limits.
4. Prepare and validate its independent `/mnt/longhorn` HDD.
5. Join it to K3s.
6. Rerun the Longhorn platform phase.
7. Verify both Longhorn nodes and both disks are schedulable.
8. Change `longhorn_replica_count` from `1` to `2`.
9. Update existing important Longhorn volumes to two replicas.
10. Test replica placement across both physical hosts.

Two replicas on two separate nodes provide node-level redundancy. Two replicas
on the same physical node do not.

## Kubecost next step

The original Kubecost ClickHouse workload failed on ARM64 with an illegal
instruction. `amd64-01` and Longhorn now provide the required architecture and
persistent block storage foundation.

Before reinstalling Kubecost:

1. Confirm all Kubecost workloads require both:

   ```yaml
   nodeSelector:
     kubernetes.io/arch: amd64
     kalaxy3.io/kubecost: "true"
   ```

2. Change Kubecost stateful storage from the earlier NFS or local-path values to
   the `longhorn` StorageClass where appropriate.
3. Remove or deliberately handle the old released Kubecost NFS PVs.
4. Keep the Longhorn replica count at one until `amd64-02` joins.
5. Reinstall Kubecost and capture separate deployment evidence.

## Final rebuild checklist

```text
[ ] Ubuntu Server installed normally on AMD64 hardware
[ ] Correct NIC identified by carrier
[ ] /etc/netplan/50-k3s-uplink.yaml is the only active intended Netplan file
[ ] Static address 192.168.2.61 survives reboot
[ ] SSH key authentication works
[ ] Passwordless sudo works for Ansible
[ ] /dev/nvme0n1 confirmed as root disk
[ ] /dev/sda confirmed as the dedicated 1 TB rotational HDD
[ ] /dev/nvme1n1 preserved for future RAG cache
[ ] amd64-01 is in k3s_agents and longhorn_nodes
[ ] Host disk-model safety variable matches the physical HDD
[ ] Longhorn preparation dry run selects only /dev/sda
[ ] /dev/sda is mounted by UUID at /mnt/longhorn
[ ] Mount survives reboot
[ ] amd64-01 joins K3s as Ready amd64 agent
[ ] Longhorn labels exist only on intended AMD64 nodes
[ ] Longhorn pods are Running
[ ] Longhorn node and disk are Ready and schedulable
[ ] StorageClass longhorn exists with replica count 1
[ ] Test PVC binds
[ ] Test pod attaches the volume and writes/reads data
[ ] Test volume reports healthy
[ ] Retained test resources are removed deliberately
[ ] multipathd warning reviewed and remediated
[ ] dm_crypt module loaded and persisted
[ ] Changes committed and pushed
```

## Final status

**PASS — first AMD64 Longhorn storage node installed and functionally validated.**

As of July 19, 2026:

- `amd64-01` is a Ready K3s agent.
- The operating-system NVMe is protected.
- The 4 TB future RAG-cache NVMe is untouched.
- The dedicated 1 TB HDD is persistently mounted at `/mnt/longhorn`.
- Longhorn 1.12.0 is installed on the AMD64 node.
- The Longhorn node and disk are ready and schedulable.
- Dynamic PVC provisioning succeeded.
- Volume attachment and replica creation succeeded.
- Container-level write and read verification succeeded.
- Test resources were cleaned up.
- The repository changes were committed and pushed.
