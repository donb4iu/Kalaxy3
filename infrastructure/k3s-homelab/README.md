# Kalaxy3 K3s homelab — phased deployment

This repository builds the five-Pi K3s cluster in independent, testable phases.
For the first installation, **do not run `make deploy`**. Start with
`docs/PHASED-DEPLOYMENT.md`, run one phase, validate it, record observations in
`docs/phase-notes.md`, and refine the configuration before proceeding.

```bash
make install
make phase-0
```

The initial topology remains three Pi K3s servers (`.51-.53`) and two Pi agents
(`.54-.55`). Intel nodes `.61-.63` can be added later as agents without
rebuilding the cluster.

## Address plan

| Purpose | Address |
|---|---:|
| K3s API bootstrap endpoint | `192.168.2.51:6443` |
| Traefik | `192.168.2.20` |
| Kubernetes Dashboard | `192.168.2.21` |
| Headlamp | `192.168.2.22` |
| MinIO API | `192.168.2.23:9000` |
| MinIO Console | `192.168.2.24:9001` |
| Grafana | `192.168.2.25` |
| MetalLB pool | `192.168.2.20-49` |

Reserve the entire MetalLB range in the router so DHCP never assigns it.

## Before running

1. Confirm SSH key authentication works from the Mac to all five nodes.
2. Confirm `/mnt/minio` is a mounted, dedicated HDD on every Pi:

   ```bash
   findmnt /mnt/minio
   df -h /mnt/minio
   ```

3. Ensure the NFS exports are reachable from every node.
4. Edit `inventory/hosts.yml` if the SSH user or hostnames differ.
5. Encrypt the MinIO password rather than storing it in plain text:

   ```bash
   cp group_vars/all.yml group_vars/all.vault.yml
   ansible-vault encrypt group_vars/all.vault.yml
   ```

   A cleaner approach is to leave ordinary settings in `all.yml`, put only
   `minio_root_password` in `group_vars/all/vault.yml`, and encrypt that file.

## Install

```bash
make install
make ping
make deploy
export KUBECONFIG="$PWD/kubeconfig-kalaxy3.yaml"
kubectl get nodes -o wide
kubectl get pods -A
kubectl get svc -A
```

Run only the cluster or platform phase with `make cluster` or `make platform`.

## Dashboard access

Dashboard is available internally at `https://192.168.2.21`. Create a short-
lived login token only when needed:

```bash
kubectl -n kubernetes-dashboard create token admin-user --duration=1h
```

Do not publish Dashboard directly through router port forwarding. Put a
Cloudflare Tunnel in front of the internal service and require Cloudflare
Access MFA. Headlamp at `http://192.168.2.22` is installed as the preferred UI.

## Internal DNS

Create local DNS records pointing to Traefik (`192.168.2.20`) for ordinary
Ingress applications. Services exposed by their own LoadBalancer address can
also have direct records. Recommended records:

```text
k8s.home.donb4iu.com       192.168.2.22
minio.home.donb4iu.com     192.168.2.24
grafana.home.donb4iu.com   192.168.2.25
```

## Adding Intel nodes

Add `.61-.63` under `k3s_agents`, then run:

```bash
make cluster
```

Keep the server count at three. If the Intel nodes are intended to replace the
Pi control plane, migrate one server at a time and retain an odd server count;
do not simply add all three as additional servers.

## Storage policy

- `nfs-ssd`: databases, Prometheus, Grafana, and latency-sensitive PVCs.
- `nfs-hdd`: large, slower, shared data.
- `minio-local`: only the five directly attached MinIO HDDs.
- K3s `local-path`: avoid for important state because it is node-local and is
  not a backup.

MinIO data is distributed across the five local drives, but erasure coding is
not a backup. Back up irreplaceable buckets outside this cluster.
