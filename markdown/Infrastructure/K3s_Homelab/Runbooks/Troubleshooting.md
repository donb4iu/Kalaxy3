# Troubleshooting Guide

## Ansible cannot reach every node

Test `ping`, TCP port 22, direct SSH, route selection, and the Mac network adapter.
Do not change playbooks until ordinary SSH works.

## A server fails to join

Verify time synchronization, hostname uniqueness, token consistency, TCP 6443, and
etcd peer connectivity. Do not repeatedly initialize a second cluster.

## MetalLB address remains pending

Confirm its address pool exists, the address is outside DHCP, speaker pods run on the
nodes, and layer-2 traffic is not filtered by the switch or router.

## A PVC remains pending

Check the requested StorageClass, NFS export reachability, provisioner logs, directory
permissions, and whether the NFS server permits the node subnet.

## MinIO writes to the boot SSD

Stop immediately. Verify `/mnt/minio` is mounted on every MinIO node. The deployment
must not proceed when the mount check fails.
