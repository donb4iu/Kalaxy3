# Deployment Order

1. Phase 0: non-modifying site survey and architecture review.
2. Phase 1: host prerequisites only.
3. Phase 2: K3s servers and agents.
4. Phase 3: MetalLB, Traefik service configuration, and NFS provisioners.
5. Phase 4: Headlamp; Dashboard remains optional.
6. Phase 5: Prometheus, Grafana, Alertmanager, and Kubecost.
7. Phase 6: MinIO after every local HDD mount is verified.
8. Phase 7: DNS, TLS, RBAC review, backup jobs, and Cloudflare Access design.
9. Phase 8: add Intel workers and introduce workload placement rules.

Commit phase notes after each successful validation. Never run `make deploy` until
every individual phase has been executed and validated successfully.
