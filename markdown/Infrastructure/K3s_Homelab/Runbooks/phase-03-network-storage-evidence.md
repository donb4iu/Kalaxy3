# Kalaxy3 Phase 03 Network and Storage Evidence

**Evidence date:** July 13, 2026  
**Cluster:** `kalaxy3`  
**Phase:** Phase 03 — Network and storage  
**Kubeconfig:** `kubeconfig-kalaxy3.yaml`

## Validation Commands

```bash
export KUBECONFIG="$PWD/kubeconfig-kalaxy3.yaml"

kubectl get pods -n metallb-system
kubectl get svc -n kube-system traefik
kubectl get storageclass
```

## MetalLB Pod Status

```text
NAME                                             READY   STATUS    RESTARTS   AGE
metallb-controller-bc9cbb54b-vk7xs               1/1     Running   0          117s
metallb-frr-k8s-7k9hg                            5/5     Running   0          117s
metallb-frr-k8s-8rjmm                            5/5     Running   0          117s
metallb-frr-k8s-nttwr                            5/5     Running   0          117s
metallb-frr-k8s-qfhds                            5/5     Running   0          117s
metallb-frr-k8s-ssvg9                            5/5     Running   0          117s
metallb-frr-k8s-statuscleaner-75b695f48d-xkrmt   1/1     Running   0          117s
metallb-speaker-28brk                            1/1     Running   0          117s
metallb-speaker-42cwv                            1/1     Running   0          117s
metallb-speaker-cwnvf                            1/1     Running   0          117s
metallb-speaker-vmlhf                            1/1     Running   0          117s
metallb-speaker-zthcp                            1/1     Running   0          117s
```

All MetalLB controller, FRR, status-cleaner, and speaker pods reported
`Running`.

The five MetalLB speaker pods correspond to the five K3s nodes. Each speaker
is available to advertise assigned load-balancer addresses on the local
network.

## Traefik LoadBalancer Service

```text
NAME      TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                      AGE
traefik   LoadBalancer   10.43.227.120   192.168.2.20   80:32476/TCP,443:30462/TCP   112m
```

MetalLB assigned the configured external address:

```text
192.168.2.20
```

This confirms that the Traefik service is no longer in the `<pending>` state
and is reachable through the local network load-balancer address.

| Service | Type | Cluster IP | External IP | Ports |
|---|---|---:|---:|---|
| `traefik` | `LoadBalancer` | `10.43.227.120` | `192.168.2.20` | `80`, `443` |

## Storage Classes

```text
NAME                   PROVISIONER                                             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path                                   Delete          WaitForFirstConsumer   false                  113m
nfs-hdd                cluster.local/nfs-hdd-nfs-subdir-external-provisioner   Retain          Immediate              true                   46s
nfs-ssd                cluster.local/nfs-ssd-nfs-subdir-external-provisioner   Retain          Immediate              true                   35s
```

Three storage classes are available.

| Storage class | Backing storage | Reclaim policy | Binding mode | Expansion |
|---|---|---|---|---|
| `local-path` | Node-local K3s storage | `Delete` | `WaitForFirstConsumer` | No |
| `nfs-hdd` | NFS HDD export | `Retain` | `Immediate` | Yes |
| `nfs-ssd` | NFS SSD export | `Retain` | `Immediate` | Yes |

The NFS-backed storage classes use a `Retain` reclaim policy. Deleting a
PersistentVolumeClaim therefore does not automatically remove the underlying
PersistentVolume data.

## Phase 03 Result

Phase 03 completed successfully with the following results:

- MetalLB is installed and operational.
- MetalLB speakers are running on all five K3s nodes.
- FRR components are running on all five nodes.
- Traefik received the external IP address `192.168.2.20`.
- The default K3s `local-path` storage class remains available.
- The `nfs-hdd` storage class is available for HDD-backed persistent storage.
- The `nfs-ssd` storage class is available for SSD-backed persistent storage.
- Both NFS storage classes allow volume expansion.
- Both NFS storage classes use the `Retain` reclaim policy.

## Recommended Additional Validation

```bash
kubectl get ipaddresspools.metallb.io -A
kubectl get l2advertisements.metallb.io -A
kubectl describe svc -n kube-system traefik
kubectl get pods -A | grep nfs
```

A simple PersistentVolumeClaim test can be used to confirm dynamic
provisioning for each NFS storage class before application workloads are
deployed.

## Conclusion

The Kalaxy3 cluster network and shared-storage foundation is operational.
MetalLB is successfully advertising Traefik at `192.168.2.20`, and both HDD-
and SSD-backed NFS storage classes are ready for application workloads.

The cluster is ready for the next deployment phase: user interfaces and
cluster administration tools.
