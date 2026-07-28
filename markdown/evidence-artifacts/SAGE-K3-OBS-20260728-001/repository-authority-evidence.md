# Repository Authority Evidence — SAGE-K3-OBS-20260728-001

## Source bundle

The SAGE generator-input bundle supplied these authoritative files and their checksums. The final evidence package does not modify them; it uses them to bound claims and publication structure.

## SAGE governance authorities

```text
AGENTS.md
SAGE.md
sage-change-authority.json
sage-evidence-policy.json
markdown/standards/kalaxy3-sage-change-discovery-process.md
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/kalaxy3-sage-evidence-orchestration-process.md
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-evidence-orchestrator.py
scripts/sage/sage-index.py
scripts/sage/sage-publish.py
```

## Observability and Helm authorities

```text
infrastructure/k3s-homelab/helm-repositories.json
infrastructure/k3s-homelab/helm-chart-lock.json
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/playbooks/tasks/observability.yml
infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2
infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2
infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml
infrastructure/k3s-homelab/scripts/validate-centralized-logging-yaml.py
infrastructure/k3s-homelab/scripts/sage-source-guardrails.py
infrastructure/k3s-homelab/scripts/sage-deployment-guardrail.py
```

## Approved logging repositories

```text
grafana-community
  URL: https://grafana-community.github.io/helm-charts
  URL SHA-256: 206ac5464a9fcfa3442aa8c4f732e5017d88ffedfbee02e2ff2bed5cb58e67e3

fluent
  URL: https://fluent.github.io/helm-charts/
  URL SHA-256: b16bb56016f47f67656cfbd58474bd8df8db9000c48377b2cef31927f3c33910
```

## Exact logging chart locks

```text
loki
  chart: grafana-community/loki
  version: 18.5.4
  release: loki
  namespace: observability
  enabled_variable: deploy_centralized_logging

fluent_bit_collector
  chart: fluent/fluent-bit-collector
  version: 1.0.9
  release: fluent-bit-collector
  namespace: observability
  enabled_variable: deploy_centralized_logging
```

## Staged configuration authority

```text
deploy_centralized_logging: false
centralized_logging_namespace: observability
centralized_logging_workload_pool: platform-services
centralized_logging_expected_node: amd64-02
loki_storage_class: longhorn
loki_storage_size: 40Gi
loki_retention_period: 168h
```

## Loki compatibility decisions

The authoritative values use monolithic Loki with TSDB schema v13 and filesystem storage. Chart `18.5.4` still validates `bucketNames`, so placeholder names `chunks` and `ruler` are present. Loki Canary is disabled, and the chart test is disabled because it depends on Canary. Longhorn persistence is `40Gi` with retained data policies and Loki placement is AMD64 plus the `platform-services` workload pool.

## Fluent Bit collection decisions

The authoritative values intentionally omit a node selector and use an Exists toleration so the collector DaemonSet covers every Kubernetes node. Output targets `loki-gateway.observability.svc.cluster.local`, persistent buffering uses `/var/lib/fluent-bit`, and Prometheus ServiceMonitor plus dashboards are enabled.

## Repository commit evidence

```text
a4a11fc (HEAD and origin branch) Separate logging placement label reconciliation
82da6e9 Validate locked centralized logging charts
8e41f83 Retire obsolete Kubernetes Dashboard source
69237e1 Complete Loki chart compatibility values
abea253 Lock centralized logging Helm charts
```

The SAGE generator bundle reported no changed, staged, or untracked repository paths at capture time.
