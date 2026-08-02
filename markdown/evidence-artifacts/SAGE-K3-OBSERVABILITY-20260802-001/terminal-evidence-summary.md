# Grafana operations dashboard and alerting evidence summary

## Evidence boundary

- Branch: `feature/grafana-operations-dashboard`
- Final captured HEAD: `6250100ebf015e5243854a32d2a1741d73ed4484`
- Grafana implementation completion commit: `55916a36afdee3fd8187f2269995f44e7ba532c2`
- Captured source inputs: 14
- Expanded authority files: 132
- Input bundle SHA-256: `1ac7f891b41c39aa967c92f4e2b01562beb89ae259406c351e91bae5d94aa15d`

## Implementation checkpoints

| Checkpoint | Commit | Observed result |
|---|---|---|
| Telemetry scrape staging | `fecb97540127ac3abee4100ef7f8dcf74286d769` | Three repository-owned ServiceMonitors staged with the deployment gate closed. |
| Dashboard definition staging | `4dc80e59ea2c0829a809abe60c3bdea61f56613a` | Twenty-panel dashboard definition validated and pushed. |
| Dashboard activation | `fa5a752e1bf25c249b09cd0579399b3924b69fc5` | Three ServiceMonitors and the dashboard ConfigMap persisted; live acceptance followed verifier repair. |
| Alert-rule staging | `ab36c484e32c28936f282287c707b0e4087cbaba` | Two Prometheus alert rules staged with the alert gate closed. |
| Alert-rule activation | `55916a36afdee3fd8187f2269995f44e7ba532c2` | PrometheusRule persisted; both rules loaded healthy and inactive. |
| SAGE capture repair | `6250100ebf015e5243854a32d2a1741d73ed4484` | Authority directories now expand to tracked files before capture. |

## Final live observations

- Dashboard UID `kalaxy3-operations` was provisioned in namespace `observability`.
- The dashboard contained 20 data panels.
- Two Kubecost and two Longhorn Prometheus targets reported `up`.
- Seven Longhorn and Kubecost panel queries returned live results.
- `FluentBitCoverageDegraded` loaded with `health=ok` and `state=inactive`.
- `LonghornStorageUtilizationHigh` loaded with `health=ok` and `state=inactive`.
- Both direct alert expressions returned zero active results during acceptance.

## Failure chronology and corrective lessons

1. A dashboard activation invocation omitted the parent `observability` tag. The correction used both parent and child tags.
2. The dashboard verifier confused the ServiceMonitor object namespace with its target namespace. The correction validated objects in `observability` and `namespaceSelector.matchNames` separately.
3. A discovery helper placed `kubectl -A` after the resource. The corrected command used supported all-namespace ordering.
4. The render target assumed the dashboard gate was closed after activation. The corrected validation path supplied render-only gate overrides.
5. YAML folded scalar syntax inserted a space into an Ansible source path. The correction used contiguous quoted paths and a regression test.
6. Kubernetes rejected `kalaxy3.io/component` as a Prometheus alert-rule label. The correction kept Kubernetes-qualified labels only in object metadata and used Prometheus-compatible rule labels.
7. Git porcelain output lost its leading status column through `.strip()`, and rollback state was captured too late. The correction used NUL-delimited byte parsing and captured rollback state before mutation.
8. SAGE authority discovery permitted directories, but capture required files. The repository orchestrator now expands authority directories through tracked files.
9. The first authority-repair helper repeated the Git-leading-space defect. The corrected helper reused the NUL-delimited parser, demonstrating that Git status parsing must be centralized as a repository primitive.

## Remaining gaps

- The live dashboard definition still contains staged or pending wording for Longhorn and Kubecost rows and a `staged` tag/label. The data is live, but the semantic presentation was not cleaned up in the captured implementation.
- Dedicated dashboard panels showing the two Prometheus alert states were planned but are not evidenced as implemented.
- No human screenshot or browser-based visual acceptance artifact was supplied.
- No notification routing or Alertmanager delivery test was performed; this record validates rule loading and evaluation only.
- Evidence-use effectiveness is not causally proven. Repository guardrails and prior lessons were used, but this session does not quantify whether evidence retrieval reduced rework or elapsed time.

## Source inventory

The permanent artifact directory includes the full canonical input ZIP, its capture receipt, the canonical brief, repository evidence, session context, bundle manifest, and all fourteen source evidence files.
