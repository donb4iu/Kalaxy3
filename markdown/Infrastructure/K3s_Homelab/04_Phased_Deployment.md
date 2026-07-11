# Phased deployment and refinement workflow

Do not run `make deploy` for the first installation. Complete each phase, run
its validation target, record observations, and adjust variables before moving
forward.

## Phase 0 — Readiness and architecture baseline

**Purpose:** Prove that the Mac, nodes, disks, NFS server, addressing, and SSH
configuration are ready without changing the cluster.

```bash
make install
make phase-0
```

**Gate:**

- All five nodes answer Ansible ping.
- Nodes have unique hostnames and expected IP addresses.
- `/mnt/minio` is a real mount on every Pi, not a directory on the boot SSD.
- Both NFS exports mount successfully from every node.
- `192.168.2.20-49` is excluded from DHCP.

Record decisions in `markdown/Infrastructure/K3s_Homelab/Phase_Notes.md` before proceeding.

## Phase 1 — Operating-system prerequisites

**Purpose:** Install host packages, kernel settings, time synchronization, and
K3s prerequisites. This phase does not install Kubernetes.

```bash
make phase-1
make validate-1
```

**Gate:** All hosts are reachable after reboot, swap/cgroup requirements are
correct, NFS client access works, and `/mnt/minio` remains mounted.

## Phase 2 — K3s core cluster

**Purpose:** Create three K3s servers using embedded etcd and join two agents.
Traefik remains bundled, while ServiceLB is disabled for later MetalLB use.

```bash
make phase-2
make validate-2
```

**Gate:**

- Exactly five nodes are `Ready`.
- `.51-.53` are control-plane/etcd nodes.
- `.54-.55` are workers.
- CoreDNS and metrics-server are healthy.
- Kubeconfig works from the Mac.

Take the first etcd snapshot before adding platform services.

## Phase 3 — Networking and persistent storage

**Purpose:** Install MetalLB, assign Traefik `192.168.2.20`, and create the
`nfs-hdd` and `nfs-ssd` StorageClasses.

```bash
make phase-3
make validate-3
```

**Gate:**

- Traefik owns `192.168.2.20`.
- A test LoadBalancer receives an address from the MetalLB pool.
- Test PVCs for both NFS classes bind and survive pod recreation.
- No MetalLB address conflicts appear on the LAN.

## Phase 4 — Administrative UI

**Purpose:** Install Headlamp first. Kubernetes Dashboard remains optional.
Neither service is exposed to the public Internet.

```bash
make phase-4
make validate-4
```

**Gate:** Headlamp is reachable from the LAN and authentication/RBAC behavior
is understood. Enable Dashboard only when its additional value is clear.

## Phase 5 — Metrics and cost observability

**Purpose:** Install Prometheus, Grafana, Alertmanager, node-exporter,
kube-state-metrics, and Kubecost. Loki and tracing remain disabled.

```bash
make phase-5
make validate-5
```

**Gate:**

- All five nodes appear in Grafana/Prometheus.
- Persistent volumes use `nfs-ssd`.
- CPU, memory, and disk pressure remain acceptable for 24-48 hours.
- Alertmanager and Kubecost are healthy.

Do not add Loki or Tempo until this baseline is stable and Intel capacity is
available or measurements show adequate headroom.

## Phase 6 — Distributed MinIO

**Purpose:** Deploy MinIO across the five dedicated one-terabyte HDD mounts.

```bash
make phase-6
make validate-6
```

**Gate:**

- Every MinIO pod is pinned to the intended node.
- Every volume resolves to `/mnt/minio` on the HDD.
- MinIO reports all drives online.
- Upload, download, and node-restart tests succeed.
- A separate backup target is identified; erasure coding is not a backup.

## Phase 7 — Security, DNS, and Cloudflare design

**Purpose:** Establish internal DNS names, TLS, RBAC boundaries, secret
handling, backup policy, and Cloudflare Tunnel/Access design.

This phase intentionally does not open router ports. Complete the design and
then add Cloudflare credentials using encrypted variables or an external secret
manager.

```bash
make phase-7
```

**Gate:** Internal names resolve locally; public services require Cloudflare
Access MFA; no management service is directly port-forwarded.

## Phase 8 — Intel node expansion

Add `.61-.63` to `k3s_agents`, initially as workers:

```bash
make phase-8
make validate-2
```

Label/taint Intel and GPU nodes before moving AI, databases, logging, tracing,
or other heavy workloads. Do not add all Intel systems as extra etcd members.

## Refinement rule

At every gate, update `group_vars/all.yml`, inventory, Helm values, and
`markdown/Infrastructure/K3s_Homelab/Phase_Notes.md`. Commit the working state before proceeding:

```bash
git add .
git commit -m "Complete phase N"
```

Rollback should return to the most recent completed phase rather than trying to
repair multiple unvalidated subsystems at once.
