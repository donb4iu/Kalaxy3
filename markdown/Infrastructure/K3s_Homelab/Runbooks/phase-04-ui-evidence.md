# Kalaxy3 Phase 04 UI Evidence

**Evidence date:** July 13, 2026  
**Cluster:** `kalaxy3`  
**Phase:** Phase 04 — Cluster user interface  
**Application:** Headlamp  
**Kubeconfig:** `kubeconfig-kalaxy3.yaml`

## Validation Commands

```bash
export KUBECONFIG="$PWD/kubeconfig-kalaxy3.yaml"

kubectl get pods -A | grep -i headlamp
kubectl get svc -A | grep -i headlamp
```

## Headlamp Pod Status

```text
headlamp   headlamp-9f5b76c67-c27rw   1/1   Running   0   42s
```

The Headlamp pod reported:

- Namespace: `headlamp`
- Pod: `headlamp-9f5b76c67-c27rw`
- Ready containers: `1/1`
- Status: `Running`
- Restarts: `0`

This confirms that the Headlamp workload started successfully and is
operational.

## Headlamp Service Status

```text
headlamp   headlamp   LoadBalancer   10.43.167.2   192.168.2.22   80:31210/TCP   42s
```

The Headlamp service reported:

| Field | Value |
|---|---|
| Namespace | `headlamp` |
| Service | `headlamp` |
| Type | `LoadBalancer` |
| Cluster IP | `10.43.167.2` |
| External IP | `192.168.2.22` |
| Service port | `80` |
| NodePort | `31210` |

MetalLB assigned the configured external address:

```text
192.168.2.22
```

## Access URL

Headlamp is available on the local network at:

```text
http://192.168.2.22
```

Optional HTTP validation:

```bash
curl -I http://192.168.2.22
```

## Phase 04 Result

Phase 04 completed successfully with the following results:

- Headlamp was installed in the `headlamp` namespace.
- The Headlamp pod reached the `Running` state.
- The pod reported `1/1` containers ready.
- No pod restarts were reported.
- A Kubernetes `LoadBalancer` service was created.
- MetalLB assigned the external IP address `192.168.2.22`.
- Headlamp is reachable over HTTP on port `80`.

## Recommended Additional Validation

```bash
kubectl get deployment -n headlamp
kubectl describe pod -n headlamp -l app.kubernetes.io/name=headlamp
kubectl describe svc -n headlamp headlamp
kubectl get endpoints -n headlamp headlamp
```

## Conclusion

The Kalaxy3 cluster administration UI is operational. Headlamp is running
successfully and is exposed on the local network through MetalLB at
`192.168.2.22`.

The cluster is ready for the next deployment phase: observability and cost
monitoring.
