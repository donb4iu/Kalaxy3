# Repository Authority Evidence — SAGE-K3-OBS-20260728-002

## Repository boundary

| Field | Value |
|---|---|
| Repository | `donb4iu/Kalaxy3` |
| Branch | `wip/centralized-logging-staged-20260726` |
| HEAD | `4247387a8062a0a353f5704e40c90b1727881a4a` |
| HEAD subject | `Use kubectl for Grafana datasource reconciliation` |
| Working-tree state | clean |
| Activation commit | `9c8b0e68aa742dad796d6871df24faf78f4485aa` |
| Correction and implementation commit | `4247387a8062a0a353f5704e40c90b1727881a4a` |

## Recent implementation lineage

```text
4247387 Use kubectl for Grafana datasource reconciliation
9c8b0e6 Activate centralized logging deployment
9e6a2bb Add SAGE evidence for staged observability readiness
a4a11fc Separate logging placement label reconciliation
82da6e9 Validate locked centralized logging charts
```

## Repository-controlled final state

`inventory/group_vars/all/main.yml` declares:

```yaml
install_observability: true
deploy_centralized_logging: true
install_kubecost: false
centralized_logging_namespace: observability
centralized_logging_workload_pool: platform-services
centralized_logging_expected_node: amd64-02
loki_storage_class: longhorn
loki_storage_size: 40Gi
loki_retention_period: 168h
```

`playbooks/tasks/observability.yml` uses exact chart-lock versions for Loki and Fluent Bit Collector, validates the unique `amd64-02` placement target, and provisions the Grafana datasource with the repository-established `k3s kubectl apply` path.

## Relevant authority inventory

| Repository authority | SHA-256 captured by generator bundle |
|---|---|
| `markdown/standards/kalaxy3-sage-evidence-record-standard.md` | `b0aa762265fb4f58ef26bd3b1edafdcee57a4ded77579efa8a48177569da8771` |
| `markdown/standards/sage-evidence-metadata-contract-v1.2.json` | `81e45630d852f1c67ab3e6b95b506e942ceae6f11f08cfd2831e0f366db0726d` |
| `markdown/templates/sage-evidence-record-template.md` | `3671b5ed8eb93adc5e735c9a7ce3a399674dd0cb46658f73b3336b66e3490a1b` |
| `markdown/standards/kalaxy3-sage-evidence-publication-process.md` | `1cfa7b6d8c34d956cc343c8c55b6f6de35f77c7cc81983e23b3e0f4a8ebf6878` |
| `scripts/sage/sage-publish.py` | `a156ef52619db0f34c3f09e9d98fa081fb428e1380807ad33741a540aedcb270` |
| `scripts/sage/sage-index.py` | `c9a0dbea22597301216217b8c69e59af2578581eaeb4d3f51463756158b920b2` |
| `sage-change-authority.json` | `2c8a1823cdb81742755d5bdea66f9fa7da1d52a465508efb5e9f436de73a8325` |
| `sage-evidence-policy.json` | `9a35840b6d939dc6f63ce1951f455c94f7843a9f6fbef2249d038ba7e989809f` |
| `AGENTS.md` | `645b3b92975a0f81c83d8f97f65630ec4f744bd12d7e222f6176d18e290d9300` |
| `SAGE.md` | `547569b3d695a3ed464d4923719d54e5856f4b1a60dde5ae6d7a2845d8ec1be9` |
| `infrastructure/k3s-homelab/helm-repositories.json` | `e3ccc3ca562ed5b5219c104b0d17b6e46610ae077a44ddbd31dafda0b8a7e763` |
| `infrastructure/k3s-homelab/helm-chart-lock.json` | `b91eaaf4e73edf1d9e9fe2865ae53464e1c0e106dff805c7a637391af96cf46c` |
| `infrastructure/k3s-homelab/playbooks/platform.yml` | `5dc889b5c865439764891fe302442f8889fcf04f42b1d78d3eb268a4bb1e097f` |
| `infrastructure/k3s-homelab/scripts/sage-source-guardrails.py` | `3724f7edfc1e51bd15c185b960c64a0190167944d963e3853a2c42b214994063` |
| `infrastructure/k3s-homelab/scripts/sage-deployment-guardrail.py` | `57b5a23a72eae4f1e77f44ae3611c1bde7609c3abfe0e44e4f8d6b62f7027cc0` |
| `infrastructure/k3s-homelab/playbooks/tasks/observability.yml` | `3c1fae337c9cb9abe6c8b8e07dff8b1b06b4e26338b3e686836dd0ca1084d613` |
| `infrastructure/k3s-homelab/inventory/group_vars/all/main.yml` | `b3b1c574102ad8358975cb18c1fb9ca24f2f20f372684d33cd48b65c23adacc2` |
| `infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2` | `cf51e8fb0319b50a65a302d0b59b15fa41c0f444cd951bf3aeabcc15e3da55a5` |
| `infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2` | `dd08b1027c18fdc9d32da6547c788d6c473265f28f2446befd63df4eb5ed56a2` |
| `infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2` | `662c6be98a5f2f6d3f1a11b48525a8c8c11c301fb62eef78c5cc8a09fbcb964f` |
| `infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml` | `a46789d6ec005cdf559cf5458cf410371ee586704043e6f05eeacc7a30feaf4c` |
| `infrastructure/k3s-homelab/scripts/validate-centralized-logging-yaml.py` | `251cfc3de8ce1e25cd84f9786580c56e2624707eaeab5614f35c7d8be64a61ef` |

## Exact chart locks

| Release | Repository | Chart | Locked version | Runtime revision after deployment |
|---|---|---|---:|---:|
| Loki | `grafana-community` | `loki` | 18.5.4 | 1 |
| Fluent Bit Collector | `fluent` | `fluent-bit-collector` | 1.0.9 | 1 |
| Prometheus and Grafana | `prometheus-community` | `kube-prometheus-stack` | 87.19.0 | 12 |

## Authority interpretation

The repository stores the deployment gate, approved Helm repositories, exact chart locks, placement rules, values, datasource manifest, and reconciliation procedure. The operator workstation supplied kubeconfig, SSH, vault access, and disposable local port-forwards, but it did not contain the only authoritative deployment definition.
