# Terminal Evidence — SAGE-K3-OBS-20260728-001

## Scope

These excerpts were supplied by the operator in the ChatGPT working session or captured in the SAGE generator-input bundle. Repetitive output is reduced, but failure messages, state transitions, final recaps, versions, and negative evidence are retained. No credential or kubeconfig content is included.

## Chronological checkpoint summary

| Sequence | Checkpoint | Result |
|---:|---|---|
| 1 | `133d844` Add repository-owned SAGE change governance | SAGE discovery and evidence orchestration established; full SHA absent from generator bundle. |
| 2 | `abea253b763bbede21226ca559354bcc0ca19650` Lock centralized logging Helm charts | Approved repository sources and exact chart locks added. |
| 3 | `69237e1bffe586a5cdb115b5f56cb8f193d8c404` Complete Loki chart compatibility values | Filesystem placeholder buckets and disabled Canary/test path added. |
| 4 | `8e41f83ac5475cb5ee6ab46b749bd468c8c923e8` Retire obsolete Kubernetes Dashboard source | Obsolete source removed; Headlamp retained. |
| 5 | `82da6e90932ac6dd8caafaf03c7d415e6887d2a2` Validate locked centralized logging charts | Exact locked chart rendering and assertions moved into repository validation. |
| 6 | `a4a11fc03dec92663a7e31924e8b3690d68aec4e` Separate logging placement label reconciliation | Dedicated prerequisite automation corrected, validated, applied, and pushed. |

## Failed path: vaulted YAML parsing

A read-only readiness audit attempted to parse `inventory/group_vars/all/main.yml` with a generic YAML loader. Repository variables included `!vault`, so the extraction path could not reliably resolve the expected node and workload pool. No cluster or repository change occurred. The accepted approach used repository-aware inspection and direct live-state queries instead of weakening or bypassing vault semantics.

## Failed path: declared placement absent live

```text
amd64-01 declared=ai live=<missing>
amd64-02 declared=platform-services live=<missing>
```

Interpretation: inventory intent existed, but the live cluster lacked the labels. Placement could not be claimed until a repository-owned reconciliation path existed.

## Failed path: controller kubeconfig authority

```text
TASK [Reconcile centralized logging workload-pool label]
failed: [localhost] (item=amd64-01)
msg: Could not find or access '/etc/rancher/k3s/k3s.yaml' on the Ansible Controller.
failed: [localhost] (item=amd64-02)
msg: Could not find or access '/etc/rancher/k3s/k3s.yaml' on the Ansible Controller.

PLAY RECAP
localhost : ok=4 changed=0 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
```

No label changed. The dedicated localhost playbook was corrected to use the repository controller kubeconfig.

## Failed path: unavailable Python Kubernetes client

```text
TASK [Reconcile centralized logging workload-pool label]
failed: [localhost] (item=amd64-01)
msg: Failed to import the required Python library (kubernetes) on donbs-imac.local's
     Python /Users/donbuddenbaum/dvlp/Kalaxy3/infrastructure/k3s-homelab/.venv/bin/python.
failed: [localhost] (item=amd64-02)
msg: Failed to import the required Python library (kubernetes) on donbs-imac.local's
     Python /Users/donbuddenbaum/dvlp/Kalaxy3/infrastructure/k3s-homelab/.venv/bin/python.

PLAY RECAP
localhost : ok=4 changed=0 unreachable=0 failed=1 skipped=0 rescued=0 ignored=0
```

No label changed. The accepted task reused repository-owned `kubectl label`, with server-side dry-run for check mode and `--overwrite` for apply.

## Corrected check-mode preview

```text
TASK [Require staged centralized logging]
ok: [localhost]
msg: Centralized logging remains staged and inactive.

TASK [Validate declared workload-pool labels]
ok: [localhost]
msg: Repository workload-pool declarations are valid.

TASK [Preview centralized logging workload-pool label]
ok: [localhost] => (item=amd64-01)
ok: [localhost] => (item=amd64-02)

PLAY RECAP
localhost : ok=5 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0

PASS amd64-01 remains unlabeled after server dry-run
PASS amd64-02 remains unlabeled after server dry-run
```

## Guardrails before amended commit

```text
Kalaxy3 SAGE source guardrails: PASS
Kalaxy3 SAGE deployment guardrail: PASS
PASS locked centralized-logging chart validation
Kalaxy3 repository SAGE guardrails: PASS
```

## Amended placement checkpoint

```text
[wip/centralized-logging-staged-20260726 a4a11fc] Separate logging placement label reconciliation
3 files changed, 133 insertions(+), 20 deletions(-)
create mode 100644 infrastructure/k3s-homelab/playbooks/reconcile-centralized-logging-labels.yml
create mode 100644 infrastructure/k3s-homelab/playbooks/tasks/centralized-logging-node-labels.yml

On branch wip/centralized-logging-staged-20260726
Your branch is ahead of 'origin/wip/centralized-logging-staged-20260726' by 1 commit.
nothing to commit, working tree clean
52:deploy_centralized_logging: false
```

## Bounded label apply

```text
TASK [Reconcile centralized logging workload-pool label]
changed: [localhost] => (item=amd64-01)
changed: [localhost] => (item=amd64-02)

PLAY RECAP
localhost : ok=5 changed=1 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0

amd64-01=ai
amd64-02=platform-services
PASS live workload-pool labels match repository intent
node/amd64-02
PASS amd64-02 is the unique logging target
```

## Idempotency rerun

```text
TASK [Reconcile centralized logging workload-pool label]
ok: [localhost] => (item=amd64-01)
ok: [localhost] => (item=amd64-02)

PLAY RECAP
localhost : ok=5 changed=0 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
PASS label reconciliation is idempotent
```

## Exact locked-chart rendering

```text
PASS repository virtual environment /Users/donbuddenbaum/dvlp/Kalaxy3/infrastructure/k3s-homelab/.venv
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS kubernetes.core 5.1.0
PASS Helm v3.21.3+g1ad6e68 (darwin-amd64)
PASS Helm kubeconfig /Users/donbuddenbaum/dvlp/Kalaxy3/infrastructure/k3s-homelab/kubeconfig-kalaxy3.yaml
PASS kubeconfig current context default

PASS YAML: loki-values.yml
PASS YAML: fluent-bit-values.yml
PASS YAML: grafana-loki-datasource.yml
PASS placement: Loki=platform-services; Fluent Bit=all nodes
PASS locked chart render: grafana-community/loki version=18.5.4 release=loki namespace=observability
PASS locked chart render: fluent/fluent-bit-collector version=1.0.9 release=fluent-bit-collector namespace=observability
PASS Loki manifests: amd64/platform-services, Longhorn=40Gi, filesystem storage, no test hook
PASS Fluent Bit manifests: one all-node DaemonSet in observability
PASS locked centralized-logging chart validation
```

## Target and storage readiness

```text
architecture=amd64
workload_pool=platform-services
ready=True
PASS intended Loki node is ready and correctly labeled

NAME       PROVISIONER          RECLAIM   BINDING
longhorn   driver.longhorn.io   Retain    Immediate

longhorn_ready=True
longhorn_schedulable=True
PASS Longhorn target node is ready and schedulable
```

## Pre-dry-run negative evidence

```text
PASS Loki and Fluent Bit Helm releases are absent
PASS centralized logging resources are absent
```

## Server-side dry-run: Loki

```text
serviceaccount/loki-gateway created (server dry run)
serviceaccount/loki-memcached created (server dry run)
serviceaccount/loki created (server dry run)
configmap/loki created (server dry run)
configmap/loki-gateway created (server dry run)
configmap/loki-runtime created (server dry run)
clusterrole.rbac.authorization.k8s.io/loki-clusterrole created (server dry run)
clusterrolebinding.rbac.authorization.k8s.io/loki-clusterrolebinding created (server dry run)
service/loki-gateway-exporter created (server dry run)
service/loki-gateway created (server dry run)
service/loki created (server dry run)
service/loki-headless created (server dry run)
service/loki-memberlist created (server dry run)
deployment.apps/loki-gateway created (server dry run)
statefulset.apps/loki created (server dry run)
PASS Loki manifests accepted by Kubernetes dry-run
```

## Server-side dry-run: Fluent Bit and Grafana

```text
serviceaccount/fluent-bit-collector created (server dry run)
configmap/fluent-bit-collector-config created (server dry run)
configmap/fluent-bit-collector-dashboard created (server dry run)
configmap/fluent-bit-collector-scripts created (server dry run)
clusterrole.rbac.authorization.k8s.io/fluent-bit-collector created (server dry run)
clusterrolebinding.rbac.authorization.k8s.io/fluent-bit-collector created (server dry run)
daemonset.apps/fluent-bit-collector created (server dry run)
podmonitor.monitoring.coreos.com/fluent-bit-collector created (server dry run)
PASS Fluent Bit manifests accepted by Kubernetes dry-run

configmap/grafana-datasource-loki created (server dry run)
PASS Grafana datasource accepted by Kubernetes dry-run
PASS server-side dry-run persisted no logging resources
```

## Final cluster guardrails

```text
PASS noninteractive SSH authentication for 7 inventory hosts
PASS noninteractive Ansible privilege escalation for 7 inventory hosts
Kalaxy3 SAGE bootstrap guardrails: PASS
PASS 6 enabled Helm releases have exact chart pins
SKIP fluent_bit_collector: release is not enabled
SKIP loki: release is not enabled
PASS 6 installed locked releases; 0 permitted new releases
Kalaxy3 Helm lock reconciliation: PASS
Kalaxy3 SAGE cluster deployment guardrails: PASS
```

## Final gate and repository result

```text
52:deploy_centralized_logging: false

On branch wip/centralized-logging-staged-20260726
Your branch is ahead of 'origin/wip/centralized-logging-staged-20260726' by 1 commit.
nothing to commit, working tree clean

PASS centralized logging placement prerequisites
PASS centralized logging activation readiness
NO LOGGING DEPLOYMENT OCCURRED
```

## Push checkpoint

```text
To github.com:donb4iu/Kalaxy3.git
82da6e9..a4a11fc  wip/centralized-logging-staged-20260726 -> wip/centralized-logging-staged-20260726

local=a4a11fc03dec92663a7e31924e8b3690d68aec4e
remote=a4a11fc03dec92663a7e31924e8b3690d68aec4e
PASS local and remote checkpoints match
0  0
PASS Loki and Fluent Bit releases remain absent
52:deploy_centralized_logging: false
nothing to commit, working tree clean
PASS staged centralized logging checkpoint published
NO LOGGING DEPLOYMENT OCCURRED
```

## SAGE generator input capture

```text
Kalaxy3 SAGE evidence-generation inputs: PASS
Bundle: /private/tmp/kalaxy3-sage-evidence-inputs.zip
Next gate: generate one package from this bundle, then run
  SAGE_PACKAGE=<package.zip> make sage-evidence-check
```

Copied input bundle verification:

```text
size_bytes=98378
sha256=8f43c71b4047990fe8963486f1fc5775aeea969c12872cfe0395ba4932213bd3
entries=37
PASS captured SAGE generator-input package
```
