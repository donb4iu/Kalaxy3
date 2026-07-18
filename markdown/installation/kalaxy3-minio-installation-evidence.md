# Kalaxy3 MinIO Installation Evidence and Rebuild Guide

**Project:** Kalaxy3  
**Validated:** July 17, 2026  
**Target path:** `markdown/installation/kalaxy3-minio-installation-evidence.md`

## Purpose

This page records how distributed MinIO was installed on the five Raspberry Pi
nodes, why it is restricted to those nodes, and how to reproduce and validate
the deployment during a future Kalaxy3 rebuild.

## Final storage architecture

```text
Five Raspberry Pi nodes
└── 5 × 1 TB HDD
    └── /mnt/minio
        └── Distributed MinIO object storage

Future Intel/AMD64 nodes
└── 3 × 1 TB HDD
    └── /mnt/longhorn
        └── Longhorn replicated block storage
```

MinIO and Longhorn must not use the same disks or mount paths.

MinIO will provide S3-compatible object storage for application data, backups,
future Longhorn backups, and future Kubecost federated data. It does not replace
the active Longhorn block volume required by Kubecost ClickHouse.

## MinIO node inventory

**File:**

```text
infrastructure/k3s-homelab/inventory/hosts.yml
```

The existing inventory group contains only the five Pi nodes:

```yaml
minio_nodes:
  hosts:
    arm64-01:
    arm64-02:
    arm64-03:
    arm64-04:
    arm64-05:
```

Inventory validation:

```bash
ansible-inventory   -i inventory/hosts.yml   --graph minio_nodes
```

Observed result:

```text
@minio_nodes:
  |--arm64-01
  |--arm64-02
  |--arm64-03
  |--arm64-04
  |--arm64-05
```

## MinIO variables

**File:**

```text
infrastructure/k3s-homelab/inventory/group_vars/all.yml
```

Relevant values:

```yaml
minio_mount_path: /mnt/minio
minio_storage_class: minio-local
minio_volume_size: 900Gi

install_longhorn: false
install_observability: true
install_kubecost: false
install_minio: true
```

Each nominal 1 TB disk exposes a 900 GiB Kubernetes volume, leaving filesystem
and operational headroom.

The root password is stored as an inline Ansible Vault value:

```yaml
minio_root_password: !vault |
  $ANSIBLE_VAULT;...
```

It is not stored as plaintext.

## Why MinIO is restricted to the Pis

Future Intel nodes are reserved for `/mnt/longhorn`, Longhorn, and Kubecost.

The final deployment uses three scheduling protections:

1. PersistentVolumes are generated only for `groups['minio_nodes']`.
2. MinIO pods require `kubernetes.io/arch: arm64`.
3. MinIO pods require `kalaxy3.io/minio: "true"`.

Required pod anti-affinity also ensures one MinIO pod per physical node.

## Ansible task behavior

**File:**

```text
infrastructure/k3s-homelab/playbooks/tasks/minio.yml
```

The MinIO tasks:

1. Validate the Vault-backed root password.
2. Require at least eight password characters.
3. Require exactly five hosts in `minio_nodes`.
4. Verify all five inventory nodes joined Kubernetes.
5. Label each inventory node `kalaxy3.io/minio=true`.
6. Render `/tmp/minio.yml`.
7. Apply the distributed MinIO resources.

Representative configuration:

```yaml
---
- name: Verify MinIO password was changed
  ansible.builtin.assert:
    that:
      - minio_root_password is defined
      - minio_root_password | length >= 8
      - minio_root_password != 'CHANGE_ME_WITH_ANSIBLE_VAULT'
    fail_msg: >-
      Set minio_root_password in an Ansible Vault encrypted vars file.
  when: install_minio | bool
  no_log: true

- name: Verify MinIO inventory group contains five nodes
  ansible.builtin.assert:
    that:
      - groups['minio_nodes'] is defined
      - groups['minio_nodes'] | length == 5
  when: install_minio | bool

- name: Verify MinIO nodes joined Kubernetes
  ansible.builtin.command:
    argv:
      - k3s
      - kubectl
      - get
      - node
      - "{{ item }}"
      - --output=name
  loop: "{{ groups['minio_nodes'] }}"
  changed_when: false
  when: install_minio | bool

- name: Label MinIO nodes
  ansible.builtin.command:
    argv:
      - k3s
      - kubectl
      - label
      - node
      - "{{ item }}"
      - kalaxy3.io/minio=true
      - --overwrite
  loop: "{{ groups['minio_nodes'] }}"
  when: install_minio | bool

- name: Render MinIO resources
  ansible.builtin.template:
    src: "{{ playbook_dir }}/../manifests/minio.yml.j2"
    dest: /tmp/minio.yml
    mode: "0600"
  when: install_minio | bool
  no_log: true

- name: Install distributed MinIO
  ansible.builtin.command:
    argv:
      - k3s
      - kubectl
      - apply
      - --filename
      - /tmp/minio.yml
  when: install_minio | bool
  no_log: true
```

## Kubernetes manifest design

**File:**

```text
infrastructure/k3s-homelab/manifests/minio.yml.j2
```

### StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: {{ minio_storage_class }}
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain
```

This is static local storage. Ansible generates the PersistentVolumes, and the
underlying data remains retained if claims are removed.

### Per-node local PersistentVolumes

```jinja
{% for host in groups['minio_nodes'] %}
apiVersion: v1
kind: PersistentVolume
metadata:
  name: minio-{{ host }}
spec:
  capacity:
    storage: {{ minio_volume_size }}
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: {{ minio_storage_class }}
  local:
    path: {{ minio_mount_path }}
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - {{ host }}
---
{% endfor %}
```

Each PV is permanently associated with one Pi hostname and `/mnt/minio`.

### StatefulSet placement

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
  namespace: minio
spec:
  serviceName: minio-headless
  replicas: 5
  podManagementPolicy: Parallel
  selector:
    matchLabels:
      app: minio
  template:
    metadata:
      labels:
        app: minio
    spec:
      nodeSelector:
        kubernetes.io/arch: arm64
        kalaxy3.io/minio: "true"
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: minio
              topologyKey: kubernetes.io/hostname
```

This means a MinIO pod must:

- Run on ARM64.
- Run on a node carrying the explicit MinIO label.
- Use a local PV tied to that node.
- Run on a different node from every other MinIO replica.

### Distributed server configuration

```yaml
args:
  - server
  - http://minio-{0...4}.minio-headless.minio.svc.cluster.local/data
  - --console-address
  - :9001
```

Each of the five pods contributes one `/data` volume to the same distributed
MinIO cluster.

## Installation command

The MinIO-only phase was applied with:

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/platform.yml   --vault-id kalaxy3@prompt   --extra-vars platform_phase=minio
```

Successful task evidence:

```text
TASK [Verify MinIO password was changed]
ok: [arm64-01]

TASK [Verify MinIO inventory group contains five nodes]
ok: [arm64-01]
msg: All assertions passed

TASK [Verify MinIO nodes joined Kubernetes]
ok: [arm64-01] => (item=arm64-01)
ok: [arm64-01] => (item=arm64-02)
ok: [arm64-01] => (item=arm64-03)
ok: [arm64-01] => (item=arm64-04)
ok: [arm64-01] => (item=arm64-05)

TASK [Label MinIO nodes]
ok: [arm64-01] => (item=arm64-01)
ok: [arm64-01] => (item=arm64-02)
ok: [arm64-01] => (item=arm64-03)
ok: [arm64-01] => (item=arm64-04)
ok: [arm64-01] => (item=arm64-05)

TASK [Render MinIO resources]
changed: [arm64-01]

TASK [Install distributed MinIO]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=11 changed=2 unreachable=0 failed=0 skipped=4
```

## Rollout evidence

Command:

```bash
kubectl rollout status   statefulset/minio   --namespace minio   --timeout=20m
```

Observed result:

```text
Waiting for 5 pods to be ready...
Waiting for 4 pods to be ready...
Waiting for 3 pods to be ready...
Waiting for 2 pods to be ready...
Waiting for 1 pods to be ready...
partitioned roll out complete: 5 new pods have been updated...
```

## Pod placement evidence

```text
NAME      READY   STATUS    RESTARTS   IP           NODE
minio-0   1/1     Running   0          10.42.2.18   arm64-03
minio-1   1/1     Running   0          10.42.5.7    arm64-05
minio-2   1/1     Running   0          10.42.3.7    arm64-04
minio-3   1/1     Running   0          10.42.1.8    arm64-02
minio-4   1/1     Running   0          10.42.0.9    arm64-01
```

All five pods were healthy and every Pi hosted exactly one replica.

## PVC evidence

```text
NAME           STATUS   VOLUME           CAPACITY   STORAGECLASS
data-minio-0   Bound    minio-arm64-03   900Gi      minio-local
data-minio-1   Bound    minio-arm64-05   900Gi      minio-local
data-minio-2   Bound    minio-arm64-04   900Gi      minio-local
data-minio-3   Bound    minio-arm64-02   900Gi      minio-local
data-minio-4   Bound    minio-arm64-01   900Gi      minio-local
```

Final pod-to-storage mapping:

```text
minio-0 → arm64-03 → minio-arm64-03 → /mnt/minio
minio-1 → arm64-05 → minio-arm64-05 → /mnt/minio
minio-2 → arm64-04 → minio-arm64-04 → /mnt/minio
minio-3 → arm64-02 → minio-arm64-02 → /mnt/minio
minio-4 → arm64-01 → minio-arm64-01 → /mnt/minio
```

StatefulSet ordinal numbers are not expected to match Pi node numbers.

## Service evidence

```text
NAME             TYPE           EXTERNAL-IP    PORTS
minio-api        LoadBalancer   192.168.2.23   9000
minio-console    LoadBalancer   192.168.2.24   9001
minio-headless   ClusterIP      none           9000,9001
```

Endpoints:

```text
MinIO API:      http://192.168.2.23:9000
MinIO console:  http://192.168.2.24:9001
```

## Endpoint health evidence

API check:

```bash
curl -fsS   http://192.168.2.23:9000/minio/health/live   && echo "MinIO API healthy"
```

Observed:

```text
MinIO API healthy
```

Console check:

```bash
curl -I http://192.168.2.24:9001
```

Observed:

```text
HTTP/1.1 200 OK
Server: MinIO Console
Content-Type: text/html
```

## Overall cluster health evidence

Command:

```bash
kubectl get pods -A   --field-selector=status.phase!=Running,status.phase!=Succeeded
```

Observed:

```text
No resources found
```

## Rebuild procedure

### 1. Prepare each Pi disk

On every Pi:

```bash
findmnt /mnt/minio
df -h /mnt/minio
lsblk -f
```

Confirm `/mnt/minio` is the dedicated 1 TB HDD and that the mount exists in
`/etc/fstab`.

### 2. Build the five-node K3s cluster

```bash
kubectl get nodes -o wide
```

All five Pi nodes must report `Ready`.

### 3. Validate inventory

```bash
ansible-inventory   -i inventory/hosts.yml   --graph minio_nodes
```

The group must contain exactly `arm64-01` through `arm64-05`.

### 4. Validate configuration

```bash
git diff --check
```

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/platform.yml   --syntax-check   --vault-id kalaxy3@prompt
```

Confirm the manifest includes:

```yaml
nodeSelector:
  kubernetes.io/arch: arm64
  kalaxy3.io/minio: "true"
```

Confirm the PV loop uses:

```jinja
{% for host in groups['minio_nodes'] %}
```

### 5. Apply MinIO

```bash
ansible-playbook   -i inventory/hosts.yml   playbooks/platform.yml   --vault-id kalaxy3@prompt   --extra-vars platform_phase=minio
```

### 6. Wait for readiness

```bash
kubectl rollout status   statefulset/minio   --namespace minio   --timeout=20m
```

### 7. Verify placement and storage

```bash
kubectl get pods -n minio -o wide
kubectl get pvc -n minio -o wide
kubectl get pv
```

Requirements:

- Five running pods
- One pod per Pi
- Five bound PVCs
- Local PV path `/mnt/minio`
- No Intel node hosting MinIO

### 8. Verify services

```bash
kubectl get svc -n minio -o wide
```

Expected addresses:

```text
API:      192.168.2.23:9000
Console:  192.168.2.24:9001
```

### 9. Verify endpoint health

```bash
curl -fsS   http://192.168.2.23:9000/minio/health/live   && echo "MinIO API healthy"

curl -I http://192.168.2.24:9001
```

### 10. Verify cluster health

```bash
kubectl get pods -A   --field-selector=status.phase!=Running,status.phase!=Succeeded
```

Expected:

```text
No resources found
```

## Troubleshooting notes

### Password assertion failure

The password is an inline `!vault` value in:

```text
inventory/group_vars/all.yml
```

The current assertion requires at least eight characters.

### Duplicate YAML marker

`playbooks/tasks/minio.yml` must begin with exactly one marker:

```yaml
---
- name: Verify MinIO password was changed
```

### Invalid node selector field

The correct Kubernetes field is:

```yaml
nodeSelector:
```

Do not use the earlier typo:

```yaml
nodelSelectors:
```

### Pending pod

Check:

```bash
kubectl describe pod -n minio POD_NAME
kubectl get pvc -n minio
kubectl get pv
kubectl get nodes -L kubernetes.io/arch,kalaxy3.io/minio
```

Common causes include a missing label, missing `/mnt/minio` mount, retained
PV/PVC state, hostname mismatch, or insufficient eligible nodes for required
anti-affinity.

## Final validated state

```text
K3s nodes:            5 Ready Raspberry Pi nodes
MinIO replicas:       5
MinIO placement:      one replica per Pi
MinIO PVCs:           5 Bound
Volume size:          900 GiB per node
Mount path:           /mnt/minio
StorageClass:         minio-local
API address:          192.168.2.23:9000
Console address:      192.168.2.24:9001
API health:           passed
Console response:     HTTP 200
Unhealthy pods:       none
Longhorn:             disabled until Intel nodes
Kubecost:             disabled until Intel and Longhorn
```
