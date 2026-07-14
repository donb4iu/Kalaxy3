# MinIO note

The uploaded notes enable the MicroK8s `minio` addon with:

- one server
- one volume
- `openebs-jiva-csi-default`
- no TLS

That is acceptable for a lab experiment, but it is not the right default for an
8-node cluster with dedicated HDDs per node. This Ansible project therefore:

1. mounts the HDDs consistently under `/mnt/minio` using `/dev/disk/by-id`
2. labels MinIO-capable nodes with `node.kalaxy2/minio=true`
3. leaves MinIO deployment disabled by default

For a later MinIO rollout, use a distributed tenant design and place PVCs only
on the nodes with attached HDDs.
