# Backup and Recovery Strategy

## Embedded etcd

Create scheduled K3s etcd snapshots and copy them away from the server node to the
NFS HDD export or another backup target. Test restoration on an isolated node before
relying on the procedure.

## Kubernetes objects

Store all declarative manifests and Helm values in Git. Back up cluster-scoped and
application-specific secrets using an encrypted mechanism; never commit plaintext
secret material.

## NFS persistent volumes

Back up both NFS exports independently of Kubernetes. Snapshots on the same physical
server are not sufficient by themselves.

## MinIO

Erasure coding is availability protection, not a backup. Replicate important buckets
to storage outside the five-node MinIO deployment.

## Recovery order

1. Restore network addressing and DNS.
2. Restore a healthy three-node K3s control plane from a tested etcd snapshot.
3. Reinstall platform controllers from Git.
4. Restore NFS-backed application data.
5. Restore or reconnect MinIO data according to the MinIO recovery procedure.
6. Validate ingress, monitoring, and applications.
