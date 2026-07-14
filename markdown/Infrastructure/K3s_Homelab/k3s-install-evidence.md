# Kalaxy3 K3s Installation Evidence

**Installation date:** July 13, 2026  
**Cluster:** `kalaxy3`  
**Platform:** Five Raspberry Pi 4B nodes running Ubuntu 24.04.4 LTS  
**K3s version:** `v1.36.2+k3s1`  
**Container runtime:** `containerd://2.3.2-k3s2`

## Installation Result

The Ansible deployment completed successfully across all five Raspberry Pi
nodes. The resulting K3s cluster contains:

- Three control-plane and embedded-etcd nodes
- Two K3s agent nodes
- A healthy Kubernetes API
- A healthy embedded etcd datastore
- Running CoreDNS, metrics-server, local-path provisioner, and Traefik
- A generated kubeconfig for remote administration from the Mac mini

## Validation Commands

```bash
export KUBECONFIG="$PWD/kubeconfig-kalaxy3.yaml"

kubectl get nodes -o wide
kubectl get pods -A
kubectl get storageclass
kubectl get svc -A
kubectl get --raw='/readyz?verbose'
```

## Node Status

```text
NAME       STATUS   ROLES                AGE   VERSION        INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION             CONTAINER-RUNTIME
arm64-01   Ready    control-plane,etcd   18m   v1.36.2+k3s1   192.168.2.51   <none>        Ubuntu 24.04.4 LTS   6.8.0-1047-raspi (arm64)   containerd://2.3.2-k3s2
arm64-02   Ready    control-plane,etcd   17m   v1.36.2+k3s1   192.168.2.52   <none>        Ubuntu 24.04.4 LTS   6.8.0-1047-raspi (arm64)   containerd://2.3.2-k3s2
arm64-03   Ready    control-plane,etcd   15m   v1.36.2+k3s1   192.168.2.53   <none>        Ubuntu 24.04.4 LTS   6.8.0-1047-raspi (arm64)   containerd://2.3.2-k3s2
arm64-04   Ready    <none>               14m   v1.36.2+k3s1   192.168.2.54   <none>        Ubuntu 24.04.4 LTS   6.8.0-1047-raspi (arm64)   containerd://2.3.2-k3s2
arm64-05   Ready    <none>               14m   v1.36.2+k3s1   192.168.2.55   <none>        Ubuntu 24.04.4 LTS   6.8.0-1047-raspi (arm64)   containerd://2.3.2-k3s2
```

All five nodes reported `Ready`.

| Node | Address | K3s role |
|---|---:|---|
| `arm64-01` | `192.168.2.51` | Control plane and etcd |
| `arm64-02` | `192.168.2.52` | Control plane and etcd |
| `arm64-03` | `192.168.2.53` | Control plane and etcd |
| `arm64-04` | `192.168.2.54` | Agent |
| `arm64-05` | `192.168.2.55` | Agent |

## Kubernetes System Pods

```text
NAMESPACE     NAME                                      READY   STATUS      RESTARTS      AGE
kube-system   coredns-5f5694d56b-94grj                  1/1     Running     0             18m
kube-system   helm-install-traefik-9crp8                0/1     Completed   2 (17m ago)   18m
kube-system   helm-install-traefik-crd-bcqtp            0/1     Completed   0             18m
kube-system   local-path-provisioner-58d557dc48-4k9bb   1/1     Running     0             18m
kube-system   metrics-server-7c86f97b8d-ctzq2           1/1     Running     0             18m
kube-system   traefik-6cd8c7cd89-9js75                  1/1     Running     0             17m
```

The two `helm-install-traefik` pods are completed installation jobs. The
long-running CoreDNS, local-path provisioner, metrics-server, and Traefik
pods are all running.

## Storage Class

```text
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  18m
```

The initial K3s `local-path` storage class is installed and marked as the
default storage class. NFS-backed and MinIO-specific storage classes are not
included in this initial installation evidence.

## Kubernetes Services

```text
NAMESPACE     NAME             TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
default       kubernetes       ClusterIP      10.43.0.1       <none>        443/TCP                      18m
kube-system   kube-dns         ClusterIP      10.43.0.10      <none>        53/UDP,53/TCP,9153/TCP       18m
kube-system   metrics-server   ClusterIP      10.43.179.159   <none>        443/TCP                      18m
kube-system   traefik          LoadBalancer   10.43.227.120   <pending>     80:32476/TCP,443:30462/TCP   17m
```

Traefik is running, but its external address is still `<pending>`. This is
expected at this stage because MetalLB has not yet assigned a LAN address to
the `LoadBalancer` service.

## Kubernetes API Readiness

```text
[+]ping ok
[+]log ok
[+]etcd ok
[+]etcd-readiness ok
[+]informer-sync ok
[+]poststarthook/start-apiserver-admission-initializer ok
[+]poststarthook/generic-apiserver-start-informers ok
[+]poststarthook/priority-and-fairness-config-consumer ok
[+]poststarthook/priority-and-fairness-filter ok
[+]poststarthook/storage-object-count-tracker-hook ok
[+]poststarthook/start-apiextensions-informers ok
[+]poststarthook/start-apiextensions-controllers ok
[+]poststarthook/crd-informer-synced ok
[+]poststarthook/start-system-namespaces-controller ok
[+]poststarthook/peer-endpoint-reconciler-controller ok
[+]poststarthook/start-cluster-authentication-info-controller ok
[+]poststarthook/start-kube-apiserver-identity-lease-controller ok
[+]poststarthook/start-kube-apiserver-identity-lease-garbage-collector ok
[+]poststarthook/storage-readiness ok
[+]poststarthook/start-legacy-token-tracking-controller ok
[+]poststarthook/start-service-ip-repair-controllers ok
[+]poststarthook/rbac/bootstrap-roles ok
[+]poststarthook/scheduling/bootstrap-system-priority-classes ok
[+]poststarthook/priority-and-fairness-config-producer ok
[+]poststarthook/bootstrap-controller ok
[+]poststarthook/start-kubernetes-service-cidr-controller ok
[+]poststarthook/aggregator-reload-proxy-client-cert ok
[+]poststarthook/start-kube-aggregator-informers ok
[+]poststarthook/apiservice-status-local-available-controller ok
[+]poststarthook/apiservice-status-remote-available-controller ok
[+]poststarthook/apiservice-registration-controller ok
[+]poststarthook/apiservice-discovery-controller ok
[+]poststarthook/kube-apiserver-autoregistration ok
[+]autoregister-completion ok
[+]poststarthook/apiservice-openapi-controller ok
[+]poststarthook/apiservice-openapiv3-controller ok
[+]shutdown ok
readyz check passed
```

The readiness endpoint confirms that the Kubernetes API server and embedded
etcd datastore passed all reported readiness checks.

## Conclusion

The initial Kalaxy3 K3s installation completed successfully. At the time this
evidence was captured:

- All five nodes were connected and `Ready`.
- The three-server embedded-etcd control plane was operational.
- Both agent nodes were joined to the cluster.
- Core Kubernetes services were running.
- The Kubernetes API readiness check passed.
- Traefik was installed and waiting for MetalLB to provide an external IP.
- The default local-path storage class was available.

The cluster is ready for the next deployment phase: MetalLB, network
configuration, NFS-backed storage classes, dashboards, observability, and
MinIO.
