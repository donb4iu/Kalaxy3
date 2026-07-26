# Terminal evidence: SAGE guardrail gap and observability pause

Evidence ID: SAGE-K3-GOVERNANCE-20260726-002
Collection date: 2026-07-26
Local timezone: America/Chicago
Operator: Don Buddenbaum
Controller: donbs-imac

This artifact preserves the material terminal observations that caused the
centralized-logging session to stop. Download progress and unrelated output
were trimmed. No credentials, private keys, kubeconfig content, or secret
values are included.

## EV-001 — Machine-local Helm entered the validation path

Approximate local time: 2026-07-26T15:56:00-05:00

Command:

```bash
helm version --short

helm pull \
  oci://ghcr.io/grafana-community/helm-charts/loki \
  --version 18.5.4 \
  --destination "$render_dir"

helm pull \
  oci://ghcr.io/fluent/helm-charts/fluent-bit-collector \
  --version 1.0.9 \
  --destination "$render_dir"
```

Observed material output:

```text
v3.15.4+gfa9efb0
Error: failed to authorize: failed to fetch oauth token:
unexpected status from GET request to https://ghcr.io/token?...:
403 Forbidden
Error: failed to authorize: failed to fetch oauth token:
unexpected status from GET request to https://ghcr.io/token?...:
403 Forbidden
```

Interpretation:

The command selected the iMac's global Helm 3.15.4 from PATH rather than a
repository-managed Helm binary. The pull failures exposed the tool-selection
problem before any chart installation occurred.

## EV-002 — Machine-local Helm repository state influenced the session

Approximate local time: 2026-07-26T15:57:00-05:00 through
2026-07-26T16:01:00-05:00

Commands:

```bash
helm repo add \
  grafana-community \
  https://grafana-community.github.io/helm-charts

helm repo add \
  fluent \
  https://fluent.github.io/helm-charts

helm repo update
```

Observed material output:

```text
"grafana-community" has been added to your repositories
"fluent" has been added to your repositories
Unable to get an update from the "kalaxy2-charts" chart repository
(http://127.0.0.1:8081/): connection refused
Unable to get an update from the "my-local-repo" chart repository
(http://127.0.0.1:8081/): connection refused
Unable to get an update from the "kubernetes-dashboard" chart repository:
404 Not Found
Successfully got an update from the "fluent" chart repository
Successfully got an update from the "grafana-community" chart repository
```

Interpretation:

The repository update consulted unrelated, stale repositories from the iMac's
personal Helm configuration. This proved that chart validation was no longer
independent of the selected workstation.

## EV-003 — Observability work was checkpointed and pushed

Local time: 2026-07-26T16:01:00-05:00 through
2026-07-26T16:16:00-05:00

Commands:

```bash
git switch -c wip/centralized-logging-staged-20260726

git add \
  infrastructure/k3s-homelab/Makefile \
  infrastructure/k3s-homelab/inventory/group_vars/all/main.yml \
  infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml \
  infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml \
  infrastructure/k3s-homelab/playbooks/tasks/observability.yml \
  infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml \
  infrastructure/k3s-homelab/playbooks/templates/fluent-bit-collector-values.yml.j2 \
  infrastructure/k3s-homelab/playbooks/templates/grafana-loki-datasource.yml.j2 \
  infrastructure/k3s-homelab/playbooks/templates/loki-values.yml.j2 \
  infrastructure/k3s-homelab/scripts/validate-centralized-logging-yaml.py

git commit -m "WIP: checkpoint staged centralized logging"

git push -u origin \
  wip/centralized-logging-staged-20260726
```

Observed material output:

```text
Switched to a new branch 'wip/centralized-logging-staged-20260726'
[wip/centralized-logging-staged-20260726 84e381c]
WIP: checkpoint staged centralized logging
10 files changed, 641 insertions(+)
To github.com:donb4iu/Kalaxy3.git
 * [new branch] wip/centralized-logging-staged-20260726
branch 'wip/centralized-logging-staged-20260726' set up to track
'origin/wip/centralized-logging-staged-20260726'
```

Interpretation:

The unfinished observability work was preserved remotely without merging it
into main or presenting it as an accepted implementation.

## EV-004 — Guardrail work was isolated on a clean branch

Local time: 2026-07-26T16:16:00-05:00 through
2026-07-26T16:17:00-05:00

Commands:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/sage-enforcement-guardrails
git status
```

Observed material output:

```text
Switched to branch 'main'
Your branch is up to date with 'origin/main'.
Already up to date.
Switched to a new branch 'feature/sage-enforcement-guardrails'
On branch feature/sage-enforcement-guardrails
nothing to commit, working tree clean
```

Interpretation:

Guardrail remediation was separated from the paused WIP and began from a clean
main-based branch.

## EV-005 — No deployment command was executed after the gap surfaced

The captured commands used local rendering, local Helm version/repository/pull
operations, Git branching, source inspection, and SAGE analysis. The captured
session contains no `helm install`, `helm upgrade`, `kubectl apply`,
`kubectl create`, or Ansible phase-deployment command after the gap was
identified.

This proves only the captured command path. It does not substitute for a fresh
cluster-state query, which remains part of future implementation evidence.
