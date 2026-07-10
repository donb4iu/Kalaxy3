# MicroK8s 8-node Ansible build

This project turns the uploaded MicroK8s notes into an Ansible-driven build for
an 8-node mixed-architecture cluster.

## What was corrected from the notes

- Replaced fragile `/dev/sdb` usage with per-node `/dev/disk/by-id/...` paths.
- Avoided making the Kubernetes Dashboard a default-on feature.
- Kept `hostpath-storage` disabled by default because it is node-local.
- Left the MicroK8s `minio` addon disabled by default because the notes create a
  single-server, single-volume tenant, which is not resilient.
- Replaced namespace default scheduling ideas with node labels and taints as the
  primary mechanism. The `PodNodeSelector` approach in the notes depends on API
  server admission customization and older namespace annotation patterns.
- Recommended a 3-control-plane + 5-worker topology for HA.

## Recommended topology

- Control plane: 3 nodes
- Workers: 5 nodes
- GPU nodes: label and taint the two amd64 GPU-capable workers
- HDDs: mounted on all nodes at `/mnt/minio` for future MinIO usage

## Prerequisites

- Ubuntu on all 8 nodes
- Passwordless sudo for `ansible_user`
- SSH reachability from the Ansible control host
- Correct `data_disk_by_id` values filled in for each node
- `ansible-galaxy collection install community.general ansible.posix`

## Usage

```bash
cd microk8s-ansible
ansible-galaxy collection install community.general ansible.posix
ansible-playbook playbooks/site.yml
```

The kubeconfig is written locally to `./artifacts/kubeconfig`.

## Notes on addons

Default enabled:

- dns
- ingress
- metallb
- metrics-server

Optional via `group_vars/all.yml`:

- dashboard
- observability
- openebs
- hostpath-storage
- gpu

## Files

- `inventory/hosts.yml`: node inventory and per-host disk identifiers
- `group_vars/all.yml`: cluster-wide settings
- `playbooks/site.yml`: full orchestration entry point
- `roles/common`: OS bootstrap
- `roles/storage`: HDD mount preparation
- `roles/microk8s`: install, cluster formation, labels, taints, addons
