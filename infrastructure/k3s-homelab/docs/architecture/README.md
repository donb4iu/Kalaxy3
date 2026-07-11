# Kalaxy3 K3s Architecture

## Initial topology

```text
Mac Mini (.8)                 NFS server (.7)
Ansible controller            /export/nfs-hdd
                              /export/nfs-ssd
        |                            |
        +------------ LAN 192.168.2.0/24 ------------+
                                                      |
       +---------------- K3s cluster -----------------+
       |                                               |
       | .51 server + etcd       .54 agent             |
       | .52 server + etcd       .55 agent             |
       | .53 server + etcd                             |
       +-----------------------------------------------+

MetalLB pool: 192.168.2.20-192.168.2.49
Traefik:      192.168.2.20
Headlamp:     192.168.2.22
MinIO API:    192.168.2.23
MinIO UI:     192.168.2.24
```

## Design principles

1. Three server nodes provide an odd embedded-etcd quorum.
2. Two Pi agents host ordinary workloads without expanding etcd unnecessarily.
3. K3s ServiceLB is disabled; MetalLB owns LAN-facing service addresses.
4. Traefik is the only ingress controller initially.
5. Shared persistent volumes use the two NFS storage classes.
6. MinIO uses the five local HDD mounts and does not use NFS.
7. Management applications remain LAN-only until Cloudflare Tunnel and Access are configured.
8. Intel nodes can join later without rebuilding the cluster.

## Workload placement

### Raspberry Pi phase

Suitable workloads include DNS, ingress, metrics, dashboards, lightweight services,
MinIO, and infrastructure controllers.

### Intel phase

Prefer Intel nodes for PostgreSQL, OpenSearch, vector databases, build workloads,
GPU operators, LLM inference, and high-cardinality observability workloads.

## Storage policy

| Storage class | Intended use |
|---|---|
| `nfs-ssd` | Prometheus, Grafana, databases requiring shared persistent storage |
| `nfs-hdd` | backups, archives, logs, large shared datasets |
| `minio-local` | MinIO only |
| `local-path` | disposable data and temporary experiments |

## Failure domains

Embedded etcd tolerates the loss of one of the three server nodes. MinIO tolerance
depends on the final server/drive layout and must be tested before important data is
stored. NFS remains a separate single-server dependency and therefore needs its own
backup and recovery plan.
