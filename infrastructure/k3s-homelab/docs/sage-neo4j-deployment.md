# SAGE Issue #50 — staged Neo4j Community deployment contract

This is the **feature-branch production-configuration deployment** for the
existing Kalaxy3 Ansible-managed Helm platform. Explicit selection runs the
actual cluster chart; PR #51 merge and model promotion remain separate.

The official Neo4j Helm chart `neo4j/neo4j` is pinned to `2026.10.1` in the
existing `helm-chart-lock.json` and its vendor repository is added to the
existing `helm-repositories.json`. The normal platform phases, including `all`, do not run this task. The include
is explicitly selected only with `platform_phase=sage_neo4j` and
`sage_neo4j_deploy_authorized=true`; ordinary `all` deployments never
include it. The task repeats the phase and authorization-variable guard.

The cluster deployment requires these existing operational conditions:

- Select and qualify adequate AMD64 capacity and Longhorn storage performance.
- Initialize the `sage` namespace and `sage-neo4j-auth` Kubernetes Secret
  using the operator bootstrap. Never store passwords or key material in Git.
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
external application-client activation, validate Bolt TLS and server certificate trust,
Neo4j authentication, allowed network sources, existing protected Traefik UI
routing, the complete Cloudflare private path, and end-to-end browser Bolt
connectivity. Do not provision a public DNS route or unqualified static IP.

The earlier defaults of `20Gi` Longhorn RWO, AMD64 affinity and 1–2 CPU /
3–4 GiB memory are tunable **engineering choices**, not separate Architect
decisions. Validate against actual node workloads and Neo4j heap/pagecache
behavior before deployment and adjust within the existing platform policy.

This feature branch supports explicit test deployment through the real
platform phase. Main-branch merge and projection promotion are separate.

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

## Explicit Issue #50 K3s validation (feature deployment)

The `sage_neo4j` phase runs only when both `platform_phase=sage_neo4j`
and `sage_neo4j_deploy_authorized=true` are supplied. It is excluded from
`platform_phase=all`. The actual pinned `neo4j/neo4j` Helm chart, Longhorn PVC,
and MetalLB LoadBalancer are the installation under test.

Before running the phase, the `sage` namespace must contain
Kubernetes `sage-neo4j-auth` (`NEO4J_AUTH=neo4j/<password>`),
`sage-neo4j-bolt-tls` and `sage-neo4j-https-tls`. Each TLS Secret must contain
`private.key` and `public.crt`. The first-run operator creates these
Kubernetes Secrets when missing; existing Secrets are preserved. The generated
certificate is self-signed for LAN bootstrap, with DNS subject-alternative names.
Trust-chain and DNS provisioning for additional consumers remain separate from
this in-cluster and pinned-certificate operational validation. The deployment values require TLS for Bolt and
configure HTTPS. These Secret names are infrastructure references, never
credentials stored in Git.

Use the Issue #50 feature deployment driver on the controller to render the
pinned chart, run the real Ansible phase, inspect the StatefulSet, release,
LoadBalancer and Longhorn PVC, then port-forward the same workload to the
existing Git-derived Neo4j CLI. An encrypted loopback port-forward uses
`bolt+ssc` solely for in-cluster graph build/readback. It is not proof of
external client certificate trust; validate LAN TLS and browser access
independently before labeling external access operational.

Do not merge or declare deployed unless the operator's K3s receipt confirms
actual cluster observations. No semantic-usefulness score is an installation
gate.
