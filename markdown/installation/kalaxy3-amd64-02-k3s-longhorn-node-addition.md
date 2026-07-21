# Kalaxy3 `amd64-02` K3s and Longhorn Node Addition

## Purpose

This document chronicles the addition of `amd64-02` to the Kalaxy3 cluster as:

- an AMD64 K3s agent;
- a second Longhorn storage node;
- a second replica target for Longhorn volumes; and
- an additional AMD64 node available for workloads that require the AMD64 architecture.

The intent is to preserve both the final configuration and the reasoning behind it so the node and cluster can be rebuilt consistently after a hardware failure, operating-system reinstall, or complete Kalaxy3 recovery.

## Completion date

July 21, 2026

## Final state

| Item | Final value |
|---|---|
| Hostname | `amd64-02` |
| Architecture | `amd64` / `x86_64` |
| Operating system | Ubuntu 24.04.4 LTS |
| Kernel observed during installation | `6.8.0-124-generic` |
| Static IPv4 address | `192.168.2.62/24` |
| Network interface | `enp2s0` |
| Default gateway | `192.168.2.1` |
| K3s role | Agent |
| K3s version | `v1.36.2+k3s1` |
| OS disk | `/dev/sda`, 465.8 GiB Samsung SSD 850 |
| Longhorn disk | `/dev/sdb`, 931.5 GiB rotational disk |
| Longhorn disk model | `ST1000VM002-1ET1` |
| Longhorn filesystem | `ext4` |
| Longhorn mount | `/mnt/longhorn` |
| Longhorn node state | Ready and schedulable |
| Longhorn default replicas | `2` |

At completion, both Longhorn nodes reported healthy:

```text
NAME       READY   ALLOWSCHEDULING   SCHEDULABLE
amd64-01   True    true              True
amd64-02   True    true              True
```

The Longhorn StorageClass and Longhorn default replica settings reported:

```text
StorageClass replicas: 2
Longhorn default: {"v1":"2","v2":"2"}
```

There were no existing Longhorn volume custom resources at the time of verification, so no existing one-replica volumes required conversion.

---

# Why the node was added

Longhorn initially had only one AMD64 storage node, `amd64-01`. That configuration provided persistent storage but no storage-node redundancy. A node outage could make a one-replica volume unavailable.

Adding `amd64-02` provided:

1. a second Longhorn disk and scheduling target;
2. the ability to use two replicas for new volumes;
3. improved availability when one AMD64 storage node is offline;
4. additional AMD64 capacity for architecture-specific applications; and
5. a repeatable process for adding future Intel or AMD nodes.

The Longhorn disk remains separate from the operating-system disk. This reduces the chance that Kubernetes storage activity fills or damages the root filesystem and allows the storage disk to be managed independently.

---

# Starting condition

The Ubuntu ISO had already been installed, and the hostname was already set to:

```text
amd64-02
```

Nothing else had been provisioned.

The host initially received the DHCP address:

```text
192.168.2.116
```

The reserved Kalaxy3 address was:

```text
192.168.2.62
```

Disk discovery showed:

```text
NAME                        SIZE TYPE ROTA FSTYPE      MOUNTPOINTS MODEL
sda                       465.8G disk    0                         Samsung SSD 850
├─sda1                        1G part    0 vfat        /boot/efi
├─sda2                        2G part    0 ext4        /boot
└─sda3                    462.7G part    0 LVM2_member
  └─ubuntu--vg-ubuntu--lv   100G lvm     0 ext4        /
sdb                       931.5G disk    1 ext4                    ST1000VM002-1ET1
```

Important conclusions:

- `/dev/sda` was the operating-system SSD and must never be selected for Longhorn;
- `/dev/sdb` was the single rotational disk in the permitted size range;
- `/dev/sdb` already contained an `ext4` filesystem;
- the Longhorn playbook was designed to preserve a supported existing filesystem and mount it by UUID rather than format it; and
- both NVMe/SSD devices were intentionally excluded by rotational-disk discovery.

---

# Repository files involved

The work affected or introduced the following files:

```text
infrastructure/k3s-homelab/
├── inventory/
│   ├── group_vars/all.yml
│   ├── host_vars/amd64-02.yml
│   └── hosts.yml
├── playbooks/
│   ├── bootstrap-static-network.yml
│   ├── longhorn-prerequisites.yml
│   ├── platform.yml
│   ├── phases/
│   │   ├── phase-00-readiness.yml
│   │   └── phase-08-intel.yml
│   ├── tasks/longhorn.yml
│   └── templates/longhorn-values.yml.j2
└── artifacts/site-survey/amd64-02.yml
```

`phase-08-intel.yml` remains intentionally small:

```yaml
---
- import_playbook: ../prerequisites.yml
- import_playbook: ../k3s.yml
```

It prepares hosts and joins K3s. Longhorn Kubernetes labeling and Helm reconciliation belong to `platform.yml`, not the Intel host-join phase.

---

# Step 1: Add missing static-network automation

## Why this was needed

A repository search showed no existing task that wrote Netplan or changed a DHCP address to a static address. The inventory reserved `192.168.2.62`, but inventory alone does not configure the host network.

The search used was:

```bash
grep -RniE \
  'netplan|static.*ip|ansible_host|addresses:|gateway4|192\.168\.2\.61' \
  playbooks roles inventory
```

No network provisioning role existed. Therefore, `playbooks/bootstrap-static-network.yml` was added to perform the one-time transition from the DHCP address to the reserved static address.

## Bootstrap playbook behavior

The playbook:

- validates the hostname and architecture;
- determines the current default interface from gathered facts;
- checks that the target address is not responding before assigning it;
- writes `/etc/netplan/60-kalaxy3-static.yaml`;
- runs `netplan generate`;
- applies Netplan asynchronously so Ansible can survive the address change; and
- waits for SSH on the new address.

The relevant target values were:

```text
Hostname: amd64-02
Temporary address: 192.168.2.116
Static address: 192.168.2.62
Gateway: 192.168.2.1
Interface discovered: enp2s0
```

## Initial SSH host-key handling

The first Ansible attempt failed because the DHCP address did not yet have an accepted SSH host key:

```text
Host key verification failed.
```

The host key was accepted by connecting manually:

```bash
ssh-keygen -R 192.168.2.116
ssh-keygen -R amd64-02
ssh dbuddenbaum@192.168.2.116
```

The hostname was verified before continuing:

```bash
hostnamectl --static
```

Expected result:

```text
amd64-02
```

An SSH key was then installed so future Ansible runs did not require the SSH password:

```bash
ssh-copy-id dbuddenbaum@192.168.2.116
```

## Run the network bootstrap

From `infrastructure/k3s-homelab`:

```bash
ansible-playbook \
  -i '192.168.2.116,' \
  playbooks/bootstrap-static-network.yml \
  --user dbuddenbaum \
  --ask-become-pass \
  --extra-vars 'kalaxy3_hostname=amd64-02' \
  --extra-vars 'kalaxy3_static_ip=192.168.2.62'
```

The successful run completed eight tasks with no failures and waited successfully for SSH at `192.168.2.62`.

## Verify the new address

```bash
ssh-keygen -R 192.168.2.62

ssh dbuddenbaum@192.168.2.62 '
  hostnamectl --static
  ip -br address
  ip route
  lsblk -e 7 -o NAME,SIZE,TYPE,ROTA,FSTYPE,MOUNTPOINTS,MODEL
'
```

Observed result:

```text
amd64-02
enp2s0 UP 192.168.2.62/24
default via 192.168.2.1 dev enp2s0 proto static
```

Install the SSH key at the final address:

```bash
ssh-copy-id dbuddenbaum@192.168.2.62
```

Verify key-based access:

```bash
ssh -o PasswordAuthentication=no \
  dbuddenbaum@192.168.2.62 \
  'hostnamectl --static'
```

---

# Step 2: Add `amd64-02` to Ansible inventory

`amd64-02` must be in both the K3s agent group and the Longhorn storage group.

The resulting inventory structure is equivalent to:

```yaml
all:
  children:
    k3s_cluster:
      children:
        k3s_agents:
          hosts:
            arm64-04:
              ansible_host: 192.168.2.54
            arm64-05:
              ansible_host: 192.168.2.55
            amd64-01:
              ansible_host: 192.168.2.61
              ansible_user: dbuddenbaum
            amd64-02:
              ansible_host: 192.168.2.62
              ansible_user: dbuddenbaum

    longhorn_nodes:
      hosts:
        amd64-01:
        amd64-02:
```

Do not add `amd64-02` to `minio_nodes`. MinIO remains assigned to the ARM64 Raspberry Pi nodes.

## Host-specific Longhorn guard

Create `inventory/host_vars/amd64-02.yml`:

```yaml
---
longhorn_disk_expected_model: ST1000VM002-1ET1
longhorn_disk_min_bytes: 800000000000
longhorn_disk_max_bytes: 1200000000000
```

This guard prevents the playbook from silently selecting a different disk model after a rebuild or hardware change.

The disk is not hard-coded as `/dev/sdb`. Linux device names can change. Instead, the playbook discovers the one rotational device within the expected capacity range and then verifies its model.

## Validate inventory

```bash
ansible-inventory \
  -i inventory/hosts.yml \
  --host amd64-02 \
  --yaml

ansible-inventory \
  -i inventory/hosts.yml \
  --graph
```

Expected group memberships:

```text
@k3s_agents
  amd64-02

@longhorn_nodes
  amd64-02
```

Because the inventory inherits `ansible_become: true`, an ad hoc Ansible ping attempts sudo unless become is disabled explicitly:

```bash
ansible \
  -i inventory/hosts.yml \
  amd64-02 \
  -m ping \
  -e ansible_become=false
```

Expected result:

```text
amd64-02 | SUCCESS =>
    changed: false
    ping: pong
```

---

# Step 3: Run host readiness checks

Run:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-00-readiness.yml \
  --limit amd64-02 \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

## Controller-side report bug discovered

All host checks passed, but report generation initially failed on the delegated localhost task:

```text
Duplicate become password prompt encountered waiting for become success.
```

The inventory variable `ansible_become: true` was still affecting the task delegated to the Mac. A task-level `become: false` alone was insufficient because the connection variable had higher precedence.

The controller-side report task was fixed with both settings:

```yaml
    - name: Create host survey report on the Ansible controller
      ansible.builtin.copy:
        dest: >-
          {{ playbook_dir }}/../../artifacts/site-survey/{{ inventory_hostname }}.yml
        mode: "0640"
        content: |
          # Existing survey content
      delegate_to: localhost
      become: false
      vars:
        ansible_become: false
```

Validate the playbook:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-00-readiness.yml \
  --syntax-check
```

Then rerun readiness. The successful result was:

```text
amd64-02 : ok=16 changed=1 unreachable=0 failed=0 skipped=6
```

The report was written to:

```text
artifacts/site-survey/amd64-02.yml
```

## Non-blocking warnings

The readiness playbook emitted Ansible deprecation warnings for top-level injected facts such as:

```yaml
ansible_distribution
ansible_architecture
ansible_memtotal_mb
ansible_default_ipv4
```

These should eventually be converted to forms such as:

```yaml
ansible_facts["distribution"]
ansible_facts["architecture"]
ansible_facts["memtotal_mb"]
ansible_facts["default_ipv4"]
```

The warnings did not block installation.

The playbook also warned that the `command` module no longer honors `executable`. That cleanup is separate from adding the node.

---

# Step 4: Define supported Longhorn filesystems

The first Longhorn prerequisite run stopped safely because this variable was missing:

```text
longhorn_allowed_filesystems is undefined
```

Add the variable in `inventory/group_vars/all.yml` near `longhorn_data_path`:

```yaml
longhorn_data_path: /mnt/longhorn
longhorn_allowed_filesystems:
  - ext4
  - xfs
```

This makes the playbook's filesystem policy explicit and prevents it from accepting an unexpected filesystem.

Validate:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --syntax-check
```

---

# Step 5: Prepare the Longhorn disk

Run the preview first:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-02 \
  --check \
  --diff \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

The playbook safety sequence is important:

1. require AMD64 architecture;
2. install Longhorn host prerequisites;
3. enable `iscsid`;
4. read all block devices;
5. select rotational devices in the configured size range;
6. require exactly one candidate;
7. verify the selected model;
8. determine the physical root disk;
9. prove the candidate is not the root disk;
10. reject a disk mounted at another path;
11. require an existing allowed filesystem and UUID;
12. create `/mnt/longhorn`;
13. mount by UUID; and
14. verify the mount.

The final applied run was:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-02 \
  --diff \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

Successful storage evidence:

```text
Node: amd64-02
Device: /dev/sdb
Model: ST1000VM002-1ET1
Filesystem: ext4
Mount: /mnt/longhorn
```

The run completed:

```text
amd64-02 : ok=21 changed=4 unreachable=0 failed=0
```

The playbook did not format the disk. It preserved the existing `ext4` filesystem and mounted it by UUID.

## Verify the mount directly

```bash
ansible \
  -i inventory/hosts.yml \
  amd64-02 \
  --become \
  --ask-become-pass \
  -m shell \
  -a '
    set -eu
    findmnt /mnt/longhorn
    lsblk -e 7 -o NAME,SIZE,TYPE,ROTA,FSTYPE,UUID,MOUNTPOINTS,MODEL
    grep -F "/mnt/longhorn" /etc/fstab
    systemctl is-enabled iscsid
    systemctl is-active iscsid
  '
```

---

# Step 6: Join `amd64-02` to K3s

Run the existing Intel phase without limiting it:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-08-intel.yml \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

Do not normally use `--limit amd64-02` for this phase because the K3s playbook reads the cluster join token from a server node and may require other plays to execute.

The phase:

- prepared all K3s nodes idempotently;
- reran Longhorn disk prerequisites for the configured Longhorn nodes;
- read the K3s join token from `arm64-01`;
- wrote the K3s agent configuration on `amd64-02`;
- installed and joined the K3s agent;
- restarted the agent; and
- waited for the agent service.

`amd64-02` completed successfully:

```text
amd64-02 : ok=34 changed=8 unreachable=0 failed=0
```

## Unrelated MinIO failure during the phase

The complete phase also validated MinIO mounts on the ARM64 nodes. `arm64-04` failed because `/mnt/minio` was not mounted:

```text
/mnt/minio is not a mounted filesystem on arm64-04.
Mount the 1-TB HDD there by UUID first; this playbook deliberately will not format disks.
```

This failure was unrelated to `amd64-02`. Ansible continued executing later plays for the other hosts, and `amd64-02` joined successfully.

This outstanding issue should be repaired separately before relying on a fully clean run of `phase-08-intel.yml`:

```bash
ansible \
  -i inventory/hosts.yml \
  arm64-04 \
  --become \
  --ask-become-pass \
  -m shell \
  -a '
    lsblk -e 7 -o NAME,SIZE,FSTYPE,UUID,MOUNTPOINTS,MODEL
    findmnt /mnt/minio || true
    grep -F "/mnt/minio" /etc/fstab || true
  '
```

## Verify the K3s node

```bash
kubectl get nodes -o wide
kubectl get node amd64-02 -o wide
```

Observed result:

```text
amd64-02 Ready <none> v1.36.2+k3s1 192.168.2.62 amd64
```

---

# Step 7: Enable the new node in Longhorn

Immediately after joining K3s, the node did not yet have the Longhorn labels:

```text
NAME       STATUS   ARCH    LONGHORN   CREATE-DEFAULT-DISK
amd64-02   Ready    amd64
```

This was expected from the current orchestration. `phase-08-intel.yml` joins the node, while `playbooks/tasks/longhorn.yml` is included by `playbooks/platform.yml`.

The labels were initially applied manually to activate the node immediately:

```bash
kubectl label node amd64-02 \
  kalaxy3.io/longhorn=true \
  node.longhorn.io/create-default-disk=true \
  --overwrite
```

The platform automation also adds:

```text
kalaxy3.io/kubecost=true
```

After labeling, verify:

```bash
kubectl get node amd64-02 \
  -L kubernetes.io/arch,kalaxy3.io/longhorn,node.longhorn.io/create-default-disk
```

Expected:

```text
amd64-02 Ready amd64 true true
```

Longhorn then started the node-local components:

```text
engine-image-...          1/1 Running amd64-02
instance-manager-...      1/1 Running amd64-02
longhorn-csi-plugin-...    3/3 Running amd64-02
longhorn-manager-...       2/2 Running amd64-02
```

## Current label automation behavior

`playbooks/tasks/longhorn.yml` currently discovers and labels every Kubernetes node with:

```text
kubernetes.io/arch=amd64
```

That is valid for the current Kalaxy3 topology because both AMD64 nodes are intended Longhorn nodes. However, a future AMD64 compute-only node would also receive Longhorn and Kubecost labels.

A future hardening change should label only inventory members of `longhorn_nodes` rather than every AMD64 node.

---

# Step 8: Increase the default replica count to two

With two healthy Longhorn storage nodes, update `inventory/group_vars/all.yml`:

```yaml
# Use two replicas across the AMD64 Longhorn storage nodes.
# Existing volumes must be updated separately.
longhorn_replica_count: 2
```

This changes the default for new Longhorn volumes. It does not automatically alter existing volumes.

At the time of this work, no Longhorn volumes existed, so no migration was required.

---

# Step 9: Reconcile Longhorn through the platform playbook

`playbooks/tasks/longhorn.yml` is included from `playbooks/platform.yml`.

The Longhorn platform block should remain between the UI and observability phases and should explicitly support a Longhorn-only phase:

```yaml
    - name: Run Longhorn storage phase
      ansible.builtin.include_tasks:
        file: tasks/longhorn.yml
        apply:
          tags:
            - longhorn
      when:
        - install_longhorn | bool
        - selected_platform_phase in ['all', 'longhorn']
      tags:
        - longhorn
```

The `apply` section is important if `--tags longhorn` is used because tags on a dynamic `include_tasks` statement are not automatically inherited by all included tasks.

Validate after editing:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --syntax-check
```

Run the Longhorn-only platform reconciliation:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags longhorn \
  --extra-vars 'platform_phase=longhorn' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

Before the explicit phase condition was added, this also worked because the Longhorn include ran whenever `install_longhorn` was true while all other phase conditions skipped for `platform_phase=longhorn`:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --extra-vars 'platform_phase=longhorn' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

The successful reconciliation:

- found the AMD64 Kubernetes nodes;
- applied the Longhorn, Kubecost, and create-default-disk labels;
- regenerated `/tmp/longhorn-values.yml`;
- ran `helm upgrade --install` for Longhorn; and
- verified the Longhorn StorageClass.

Observed recap:

```text
arm64-01 : ok=12 changed=3 unreachable=0 failed=0 skipped=6
```

---

# Step 10: Final verification

## Verify K3s

```bash
kubectl get nodes -o wide
```

Expected nodes include:

```text
amd64-01 Ready 192.168.2.61 amd64
amd64-02 Ready 192.168.2.62 amd64
```

## Verify Kubernetes labels

```bash
kubectl get node amd64-02 \
  -L kubernetes.io/arch,kalaxy3.io/longhorn,kalaxy3.io/kubecost,node.longhorn.io/create-default-disk
```

## Verify Longhorn node state

```bash
kubectl get nodes.longhorn.io \
  -n longhorn-system
```

Expected:

```text
NAME       READY   ALLOWSCHEDULING   SCHEDULABLE
amd64-01   True    true              True
amd64-02   True    true              True
```

## Verify Longhorn pods on both nodes

```bash
kubectl get pods \
  -n longhorn-system \
  -o wide
```

At minimum, each Longhorn storage node should have:

- `longhorn-manager`;
- `longhorn-csi-plugin`;
- an engine image pod; and
- an instance manager.

## Verify the registered disk path

```bash
kubectl get nodes.longhorn.io amd64-02 \
  -n longhorn-system \
  -o jsonpath='
Node: {.metadata.name}
Ready: {.status.conditions[?(@.type=="Ready")].status}
Schedulable: {.status.conditions[?(@.type=="Schedulable")].status}
{range .spec.disks[*]}
Disk path: {.path}
Allow scheduling: {.allowScheduling}
{end}
'
echo
```

Expected:

```text
Node: amd64-02
Ready: True
Schedulable: True
Disk path: /mnt/longhorn
Allow scheduling: true
```

## Verify replica defaults

```bash
kubectl get storageclass longhorn \
  -o jsonpath='StorageClass replicas: {.parameters.numberOfReplicas}{"\n"}'

kubectl get settings.longhorn.io default-replica-count \
  -n longhorn-system \
  -o jsonpath='Longhorn default: {.value}{"\n"}'
```

Expected:

```text
StorageClass replicas: 2
Longhorn default: {"v1":"2","v2":"2"}
```

## Verify existing Longhorn volumes

```bash
kubectl get volumes.longhorn.io \
  -n longhorn-system
```

At installation time, the result was:

```text
No resources found in longhorn-system namespace.
```

---

# Complete rebuild order

Use this sequence after reinstalling Ubuntu on `amd64-02`.

## 1. Confirm physical layout

```bash
hostnamectl --static
uname -m
ip -br address
ip route
lsblk -e 7 -o NAME,SIZE,TYPE,ROTA,FSTYPE,MOUNTPOINTS,MODEL
```

Required assumptions:

- hostname is `amd64-02`;
- architecture is `x86_64`;
- OS disk is not the rotational 1-TB disk;
- exactly one rotational disk is between 800 GB and 1.2 TB;
- disk model is `ST1000VM002-1ET1`, unless the hardware was intentionally replaced; and
- the Longhorn disk contains `ext4` or XFS.

## 2. Accept the temporary SSH host key and install the controller key

```bash
ssh-keygen -R <temporary-dhcp-address>
ssh dbuddenbaum@<temporary-dhcp-address>
ssh-copy-id dbuddenbaum@<temporary-dhcp-address>
```

## 3. Apply the static address

```bash
ansible-playbook \
  -i '<temporary-dhcp-address>,' \
  playbooks/bootstrap-static-network.yml \
  --user dbuddenbaum \
  --ask-become-pass \
  --extra-vars 'kalaxy3_hostname=amd64-02' \
  --extra-vars 'kalaxy3_static_ip=192.168.2.62'
```

## 4. Install the SSH key at the final address

```bash
ssh-keygen -R 192.168.2.62
ssh-copy-id dbuddenbaum@192.168.2.62
```

## 5. Verify inventory and host variables

```bash
ansible-inventory -i inventory/hosts.yml --host amd64-02 --yaml
ansible-inventory -i inventory/hosts.yml --graph
```

## 6. Run readiness

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-00-readiness.yml \
  --limit amd64-02 \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

## 7. Preview and apply Longhorn host prerequisites

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-02 \
  --check \
  --diff \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

Verify that only the expected rotational disk is selected, then apply:

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/longhorn-prerequisites.yml \
  --limit amd64-02 \
  --diff \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

## 8. Join K3s

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/phases/phase-08-intel.yml \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

## 9. Reconcile Longhorn

```bash
ansible-playbook \
  -i inventory/hosts.yml \
  playbooks/platform.yml \
  --tags longhorn \
  --extra-vars 'platform_phase=longhorn' \
  --ask-become-pass \
  --vault-id kalaxy3@prompt
```

## 10. Run final verification

```bash
kubectl get nodes -o wide
kubectl get nodes.longhorn.io -n longhorn-system
kubectl get pods -n longhorn-system -o wide
kubectl get storageclass longhorn -o yaml
kubectl get settings.longhorn.io default-replica-count -n longhorn-system -o yaml
```

---

# Failure modes encountered and their resolution

## SSH host-key verification failed

**Cause:** The freshly installed host at its DHCP address was not yet trusted by the Mac.

**Resolution:** Remove stale entries and connect manually once before running Ansible.

```bash
ssh-keygen -R 192.168.2.116
ssh dbuddenbaum@192.168.2.116
```

## Ansible password login rejected while host checking was enabled

**Cause:** Ansible would not use password authentication until the host key was present in `known_hosts`.

**Resolution:** Accept the SSH host key manually, then use `ssh-copy-id`.

## Ad hoc Ansible ping requested a sudo password

**Cause:** `ansible_become: true` was inherited from inventory.

**Resolution:** Disable become for nonprivileged connectivity tests.

```bash
ansible -i inventory/hosts.yml amd64-02 -m ping -e ansible_become=false
```

## Readiness report tried to sudo on localhost

**Cause:** A delegated task inherited the inventory connection variable `ansible_become: true`.

**Resolution:** Set both the task keyword and variable override:

```yaml
delegate_to: localhost
become: false
vars:
  ansible_become: false
```

## Incorrect sudo password

**Cause:** The become prompt received a password different from the `amd64-02` account password.

**Resolution:** Verify directly:

```bash
ssh dbuddenbaum@192.168.2.62
sudo -k
sudo whoami
```

Use that same password at Ansible's `BECOME password` prompt. The Vault password is separate.

## `longhorn_allowed_filesystems` was undefined

**Cause:** The prerequisite playbook referenced a policy variable that had not been defined.

**Resolution:** Add:

```yaml
longhorn_allowed_filesystems:
  - ext4
  - xfs
```

## `arm64-04` MinIO mount validation failed

**Cause:** `/mnt/minio` was not a mounted filesystem on `arm64-04`.

**Impact:** The failure was unrelated to `amd64-02`; later plays still joined the AMD64 node.

**Resolution:** Repair the ARM64 disk mount separately and rerun the appropriate prerequisite phase.

## Longhorn pods did not initially appear on `amd64-02`

**Cause:** The K3s join phase does not run the platform Longhorn tasks.

**Resolution:** Apply labels immediately if necessary, then run the Longhorn platform reconciliation.

---

# Security and operational notes

- Never place K3s join tokens, Ansible Vault passwords, MinIO passwords, or plaintext secrets in this document.
- Avoid posting full `ansible-inventory --host` output publicly because it may contain encrypted Vault blocks and sensitive infrastructure details.
- Keep `/dev/sda` protected as the operating-system disk.
- Do not replace model validation with an unconditional `/dev/sdb` assignment; device names can change after hardware or firmware changes.
- Longhorn two-replica storage tolerates one replica loss, but it is not a backup. Maintain independent backups or snapshots outside the two Longhorn nodes.
- If both Longhorn nodes share a single power source, network switch, or failure domain, two replicas do not protect against that shared failure.

---

# Follow-up work

## Required

1. Repair `/mnt/minio` on `arm64-04` so the complete prerequisite phase runs cleanly.
2. Commit the new and modified Ansible files and this installation record.
3. Capture a final `git diff --check` and clean `git status` after committing.

## Recommended hardening

1. Change `tasks/longhorn.yml` to label only `groups['longhorn_nodes']` instead of every AMD64 Kubernetes node.
2. Convert deprecated top-level Ansible facts to `ansible_facts[...]` syntax.
3. Remove the obsolete `executable` parameter from the `command` task in readiness checks.
4. Add an automated test that verifies delegated localhost tasks do not inherit remote `ansible_become` settings.
5. Add a post-K3s phase or explicit orchestration note that always follows a new K3s node join with `platform_phase=longhorn`.
6. Test a two-replica PVC after the first real Longhorn workload is deployed.

---

# Suggested Git review and commit

From the Kalaxy3 repository root:

```bash
git status
git diff --check
git diff
```

Review at least:

```text
infrastructure/k3s-homelab/inventory/hosts.yml
infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
infrastructure/k3s-homelab/inventory/group_vars/all.yml
infrastructure/k3s-homelab/playbooks/bootstrap-static-network.yml
infrastructure/k3s-homelab/playbooks/phases/phase-00-readiness.yml
infrastructure/k3s-homelab/playbooks/platform.yml
markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md
```

Suggested commit:

```bash
git add \
  infrastructure/k3s-homelab/inventory/hosts.yml \
  infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml \
  infrastructure/k3s-homelab/inventory/group_vars/all.yml \
  infrastructure/k3s-homelab/playbooks/bootstrap-static-network.yml \
  infrastructure/k3s-homelab/playbooks/phases/phase-00-readiness.yml \
  infrastructure/k3s-homelab/playbooks/platform.yml \
  markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md

git commit -m \
  "Add amd64-02 K3s agent and second Longhorn storage node"

git pull --rebase origin main
git push origin main
git status
```

Only add paths that exist and were intentionally changed.

---

# Completion checklist

- [x] Hostname is `amd64-02`.
- [x] Static address is `192.168.2.62`.
- [x] SSH key authentication works.
- [x] Ansible inventory includes `amd64-02` under `k3s_agents`.
- [x] Ansible inventory includes `amd64-02` under `longhorn_nodes`.
- [x] Host-specific Longhorn model guard is present.
- [x] Readiness checks pass.
- [x] Controller-side survey report is generated without sudo on localhost.
- [x] Longhorn prerequisites are installed.
- [x] `/dev/sdb` is mounted by UUID at `/mnt/longhorn`.
- [x] K3s agent is installed and Ready.
- [x] Longhorn labels are present.
- [x] Longhorn node-local pods are Running.
- [x] `amd64-02` is Ready and schedulable in Longhorn.
- [x] Default Longhorn replica count is `2`.
- [x] Longhorn StorageClass replica count is `2`.
- [ ] `arm64-04` MinIO mount failure is repaired.
- [ ] Repository changes are reviewed, committed, and pushed.
