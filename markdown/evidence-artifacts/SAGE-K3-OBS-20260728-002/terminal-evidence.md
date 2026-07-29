# Terminal Evidence — SAGE-K3-OBS-20260728-002

## Scope

This artifact summarizes the operator-supplied terminal transcript for the 2026-07-28 centralized logging activation and deployment session. The complete unabridged transcript is retained as `terminal-transcript.txt`. Repetitive Ansible and Kubernetes output is reduced here, while state transitions, failure messages, exact versions, validation results, and negative evidence are preserved.

## Chronological checkpoint summary

| Local time | Checkpoint | Result |
|---:|---|---|
| 18:51–18:52 | Activation gate change | `deploy_centralized_logging` changed from `false` to `true`; source, deployment, cluster, and SAGE guardrails passed; commit `9c8b0e68aa742dad796d6871df24faf78f4485aa` was pushed; no logging workload was deployed in this checkpoint. |
| 19:06–19:09 | First observability deployment | `kube-prometheus-stack` advanced from revision 10 to 11; Loki 18.5.4 and Fluent Bit Collector 1.0.9 installed; Grafana datasource provisioning failed because `kubernetes.core.k8s` could not import the Python Kubernetes library on `arm64-01`. |
| 19:15–19:16 | Repository correction | The datasource task was changed to the repository-established `k3s kubectl apply` path; server-side dry-run and all guardrails passed; commit `4247387a8062a0a353f5704e40c90b1727881a4a` was pushed. |
| 19:26–19:28 | Resumed observability deployment | Logging releases remained at revision 1; datasource ConfigMap was created; `kube-prometheus-stack` advanced to revision 12 while retaining chart 87.19.0. |
| 19:28–19:39 | Runtime verification | Loki placement, collectors, storage, Grafana datasource health, log queries, all-node stream coverage, startup-pressure clearance, cluster guardrails, and clean Git state passed. |

## Activation checkpoint

```text
52:deploy_centralized_logging: false
...
PASS centralized logging activation checkpoint published
READY FOR CLUSTER DEPLOYMENT
NO LOGGING DEPLOYMENT OCCURRED IN THIS STEP
activation_commit=9c8b0e68aa742dad796d6871df24faf78f4485aa
local=9c8b0e68aa742dad796d6871df24faf78f4485aa
remote=9c8b0e68aa742dad796d6871df24faf78f4485aa
0  0
```

The gate change was isolated, committed, pushed, and verified before cluster deployment.

## Partial deployment and accepted failure

```text
TASK [Install Loki]
changed: [arm64-01]

TASK [Install Fluent Bit Collector]
changed: [arm64-01]

TASK [Provision Grafana Loki datasource]
fatal: [arm64-01]: FAILED! =>
    msg: Failed to import the required Python library (kubernetes) on arm64-01's Python
        /usr/bin/python3.

PLAY RECAP
arm64-01 : ok=26 changed=12 unreachable=0 failed=1 skipped=4
```

Post-failure inspection established that the failure occurred after both logging releases were installed:

```text
fluent-bit-collector  observability  1  deployed  fluent-bit-collector-1.0.9  5.0.9
loki                  observability  1  deployed  loki-18.5.4                  3.7.4
statefulset.apps/loki                  1/1
statefulset PVC storage-loki-0         Bound 40Gi longhorn
daemonset.apps/fluent-bit-collector   7 desired, 7 ready
```

The Grafana datasource ConfigMap was absent. This was a partial deployment, not a rollback or a total deployment failure.

## Repository-owned correction

```text
PASS datasource reconciliation now uses repository-established k3s kubectl
PASS datasource manifest accepted by Kubernetes dry-run
PASS datasource remains absent
PASS 8 installed locked releases; 0 permitted new releases
[wip/centralized-logging-staged-20260726 4247387] Use kubectl for Grafana datasource reconciliation
correction_commit=4247387a8062a0a353f5704e40c90b1727881a4a
local=4247387a8062a0a353f5704e40c90b1727881a4a
remote=4247387a8062a0a353f5704e40c90b1727881a4a
0  0
```

The correction replaced the remote Python-client dependency with:

```yaml
- name: Provision Grafana Loki datasource
  ansible.builtin.command:
    argv:
      - k3s
      - kubectl
      - apply
      - --filename
      - /tmp/grafana-loki-datasource.yml
```

## Successful resumed deployment

```text
TASK [Install Loki]
ok: [arm64-01]

TASK [Install Fluent Bit Collector]
ok: [arm64-01]

TASK [Provision Grafana Loki datasource]
changed: [arm64-01]

PLAY RECAP
arm64-01 : ok=26 changed=2 unreachable=0 failed=0 skipped=13

PASS loki: chart=loki-18.5.4 revision=1 status=deployed
PASS fluent-bit-collector: chart=fluent-bit-collector-1.0.9 revision=1 status=deployed
```

The logging Helm releases remained at revision 1 during reconciliation. The broader observability phase advanced the unchanged locked `kube-prometheus-stack` release to revision 12.

## Placement and collector coverage

```text
loki-0                          2/2 Running amd64-02
loki-gateway-5c75989494-97v27   2/2 Running amd64-02
PASS all Loki pods are ready on amd64-02

expected:
node/amd64-01
node/amd64-02
node/arm64-01
node/arm64-02
node/arm64-03
node/arm64-04
node/arm64-05

collectors:
node/amd64-01
node/amd64-02
node/arm64-01
node/arm64-02
node/arm64-03
node/arm64-04
node/arm64-05

PASS one ready Fluent Bit Collector runs on every node
```

## Storage validation

```text
phase=Bound
storage_class=longhorn
requested=40Gi
state=attached
robustness=healthy
replicas=2
PASS Loki Longhorn volume is attached, healthy, and replicated twice
```

The observed volume was `pvc-75885121-8c1b-4024-aaf2-6d341244ea6d`.

## Grafana datasource validation

```text
configmap/grafana-datasource-loki
name=Loki
uid=loki
type=loki
url=http://loki-gateway.observability.svc.cluster.local
PASS Grafana loaded the Loki datasource
{"message":"Data source successfully connected.","status":"OK"}
status=ok
message=Data source successfully connected.
PASS Grafana reached Loki successfully
```

Credentials were decoded into a temporary mode-0600 file, used only for local API verification, never displayed, and removed by cleanup.

## Log-ingestion validation

```text
PASS Loki readiness endpoint
stream_count=6
labels={"cluster":"kalaxy3", ... "node":"amd64-02", ...}
labels={"cluster":"kalaxy3", ... "node":"arm64-02", ...}
labels={"cluster":"kalaxy3", ... "node":"arm64-05", ...}
PASS recent Kalaxy3 logs are queryable

expected=['amd64-01', 'amd64-02', 'arm64-01', 'arm64-02', 'arm64-03', 'arm64-04', 'arm64-05']
observed=['amd64-01', 'amd64-02', 'arm64-01', 'arm64-02', 'arm64-03', 'arm64-04', 'arm64-05']
PASS Loki contains recent streams from all seven nodes
```

## Startup backlog pressure

The first collector logs contained retryable `429` responses at the default observed limit and non-retryable rejection of historical entries outside Loki's acceptable ingestion window:

```text
HTTP status=429
ingestion rate limit exceeded for user fake (limit: 4194304 bytes/sec)

HTTP status=400 Not retrying.
entry ... has timestamp too old
entry ... ignored, reason: entry too far behind
```

Successful retries and accepted current streams were also present. Final validation examined every collector for the preceding five minutes:

```text
recent_rate_limit_errors=0
recent_old_timestamp_errors=0
PASS no rate-limit or old-timestamp errors occurred in the last five minutes
```

This proves the observed startup burst cleared; it does not prove that future restart backlogs will always clear without tuning.

## Operator verification-helper failures

These failures occurred in ad hoc validation wrappers, not in repository deployment logic:

1. A shell-quoted Python revision helper converted a dictionary key expression and raised `NameError: name 'name' is not defined`. The observability playbook did not run in that attempt.
2. A Python heredoc consumed standard input that was intended to carry Secret JSON, causing `JSONDecodeError`. The repository deployment had already succeeded through datasource creation; only the verification helper failed.
3. Another shell-quoted Python helper raised `KeyError: 'loki-18.5.4'`. It was read-only and made no cluster change.
4. Bash indirect expansion was pasted into zsh and produced `zsh: event not found: PID_NAME` during parsing. Nothing ran.
5. The final validation explicitly invoked Bash and used file-backed JSON to avoid standard-input and shell-quoting ambiguity.

These paths are retained because they distinguish tool-wrapper mistakes from implementation defects and explain the final verification method.

## Final guardrail and repository result

```text
PASS 8 installed locked releases; 0 permitted new releases
Kalaxy3 Helm lock reconciliation: PASS
Kalaxy3 SAGE cluster deployment guardrails: PASS
52:deploy_centralized_logging: true
nothing to commit, working tree clean

PASS Loki 18.5.4 deployed and healthy
PASS Fluent Bit Collector 1.0.9 runs on all seven nodes
PASS Grafana loaded and reached the Loki datasource
PASS Longhorn storage is healthy and replicated
PASS recent logs from all seven nodes are queryable
PASS initial ingestion pressure cleared
CENTRALIZED LOGGING OBSERVABILITY DEPLOYMENT COMPLETE
```
