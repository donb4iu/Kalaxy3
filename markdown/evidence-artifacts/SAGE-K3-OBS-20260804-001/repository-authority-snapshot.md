# Repository authority snapshot

This artifact records the repository-controlled configuration used to interpret
centralized-logging runtime evidence at commit `cf6eee9976919be1ed5a9d283e8a609d740eee04`.

## Authoritative configuration

- `deploy_centralized_logging: true`
- `centralized_logging_namespace: observability`
- `centralized_logging_workload_pool: platform-services`
- `centralized_logging_expected_node: amd64-02`
- `loki_storage_class: longhorn`
- `loki_storage_size: 40Gi`
- `loki_retention_period: 168h`
- Loki deployment mode: monolithic with one `singleBinary` replica.
- Loki persistence: enabled, `40Gi`, Longhorn, retain on deletion and scale-down.
- Fluent Bit Collector: DaemonSet semantics with an `Exists` toleration and
  delivery to `loki-gateway.observability.svc.cluster.local:80`.
- Grafana Loki data source: proxy access through the in-cluster Loki gateway.

## Locked versions

- `fluent-bit-collector`: chart `fluent/fluent-bit-collector`, version `1.0.9`
- `loki`: chart `grafana-community/loki`, version `18.5.4`
- `longhorn`: chart `longhorn/longhorn`, version `1.12.0`

## Authority file checksums

| Repository path | SHA-256 |
|---|---|
| `infrastructure/k3s-homelab/inventory/group_vars/all/main.yml` | `1716598d6ecd27d319eefa3f01dc7742b148943d23791f64057815e0f7e6b0fe` |
| `infrastructure/k3s-homelab/helm-chart-lock.json` | `b91eaaf4e73edf1d9e9fe2865ae53464e1c0e106dff805c7a637391af96cf46c` |
| `infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2` | `cf51e8fb0319b50a65a302d0b59b15fa41c0f444cd951bf3aeabcc15e3da55a5` |
| `infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2` | `dd08b1027c18fdc9d32da6547c788d6c473265f28f2446befd63df4eb5ed56a2` |
| `infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2` | `662c6be98a5f2f6d3f1a11b48525a8c8c11c301fb62eef78c5cc8a09fbcb964f` |
| `infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py` | `a94dbd3b38e95aca03428d964564f2629f049dedda8bdb896bf66b33ec954b48` |

## Boundaries

This snapshot proves what the supplied repository bundle declared. It does not
replace the live runtime validation or independently prove historical deployment
steps that occurred before the captured session.
