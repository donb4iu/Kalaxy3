# SAGE Issue #50 — staged Neo4j Community deployment contract

This is a **feature-branch configuration contribution** to the existing Kalaxy3
Ansible-managed Helm platform. It is *not* approval to install a production
Neo4j workload, merge PR #51, or promote a semantic projection.

The official Neo4j Helm chart `neo4j/neo4j` is pinned to `2026.10.1` in the
existing `helm-chart-lock.json` and its vendor repository is added to the
existing `helm-repositories.json`. The normal platform phases, including `all`, do not run this task. The include
is also **hard-disabled with `when: false`**: merely passing extra variables
cannot install Neo4j. Future actual deployment requires an independently
authorized, reviewed change to activate this source-controlled phase. The task
then repeats the explicit phase and authorization-variable guard.

The future installation must satisfy these conditions first:

- Select and qualify adequate AMD64 capacity and Longhorn storage performance.
- Have the existing Vault workflow create the `sage-neo4j-auth` Secret in the
  `sage` namespace. Do not store credentials or literal initial passwords in Git.
- Verify the official chart's required `NEO4J_AUTH` Secret format and lint/render
  the pinned chart with the locked values before any authorized deployment.
- Validate Longhorn PVC size and retention, class RWO, shutdown/recovery and
  observable rebuild of a disposable projection from authoritative SAGE facts.
- Verify secret-scoped credentials and Kubernetes network policies before
  allowing an application-service consumer to connect to the internal endpoint.
- Qualify CPU/memory against live node scheduling, without assuming GPU affinity.
- Confirm how observability will work: **Community Edition does not generate
  Neo4j's native `metrics` mount metrics**, so do not claim Prometheus metrics
  exist merely because Grafana is installed. Use existing logs and permitted
  external monitoring, subject to qualification.

## Approved access and pragmatic resource defaults

The chart's **MetalLB-backed `LoadBalancer` is enabled** as a versioned, staged
configuration, supporting authorized on-premises MacBook, Mac mini and iMac
clients. The Bolt port is available through the LAN service; the HTTPS port is
reserved for an appropriately configured certificate and Browser path. The
plaintext HTTP and backup ports are not exposed. In-cluster SAGE clients use
ClusterIP. Cloudflare Access private TCP for remote MacBook development is a
required later configuration, not a public database listener.

**Do not claim secure access merely because a Helm port is enabled.** Before
actual Kubernetes deployment, validate Bolt TLS and server certificate trust,
Neo4j authentication, allowed network sources, existing protected Traefik UI
routing, the complete Cloudflare private path, and end-to-end browser Bolt
connectivity. Do not provision a public DNS route or unqualified static IP.

The earlier defaults of `20Gi` Longhorn RWO, AMD64 affinity and 1–2 CPU /
3–4 GiB memory are tunable **engineering choices**, not separate Architect
decisions. Validate against actual node workloads and Neo4j heap/pagecache
behavior before deployment and adjust within the existing platform policy.

Production Kubernetes deployment, merge and promotion remain separately
governed. This branch-only contribution does not activate any workload.

## Read-only engineering validation

- `python3 scripts/sage/sage_neo4j_deployment_guardrail.py --repo .`
- `python3 -m unittest discover -s scripts/sage -p 'test_sage_neo4j_deployment.py' -v`
- `python3 -m unittest discover -s scripts/sage -p 'test_sage_neo4j_reconcile.py' -v`
- `python3 scripts/sage/sage-neo4j-reconcile.py --repo . --before HEAD~1 --after HEAD --out /tmp/sage-issue50-reconcile.json`

These test the staging gate and Git evidence-delta accounting only. They do
**not** satisfy DOD-06 independent semantic recall, DOD-08 end-to-end promotion
or DOD-09 break-glass model evolution. PR #51 remains a draft.

References:

- https://neo4j.com/docs/operations-manual/current/kubernetes/helm-charts-setup/
- https://neo4j.com/docs/operations-manual/current/kubernetes/configuration/
- https://neo4j.com/docs/operations-manual/current/kubernetes/persistent-volumes/
