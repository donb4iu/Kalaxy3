# Repository guardrail-gap analysis

Evidence ID: SAGE-K3-GOVERNANCE-20260726-002
Analysis date: 2026-07-26
Repository: donb4iu/Kalaxy3
Observed branch for source review: feature/sage-enforcement-guardrails

## Existing SAGE requirement

The current schema 1.2 publication process states that:

- the repository, not a particular workstation, is the publication and
  deployment source of truth;
- the controller must use the repository-created virtual environment, exact
  dependencies, and controller preflight;
- changing controller hosts must not change dependency selection, generated
  configuration, deployment behavior, evidence structure, or the target
  environment;
- machine-local persistent configuration must be reconciled into the
  repository before evidence can claim repeatability.

The evidence template repeats the controller-portability requirements and asks
whether machine-local authoritative state exists.

## Enforcement actually present before the pause

### Repository-controlled controller components

```text
uv                 pinned by .uv-version
Python             pinned by .python-version
ansible-core       pinned in requirements.txt
Ansible collections pinned in requirements.yml
controller checks scripts/controller-preflight.py
```

### Missing Helm enforcement

The inspected Makefile and controller preflight did not:

- install a repository-managed Helm binary;
- pin Helm in a controller-local version file;
- isolate Helm configuration, cache, data, plugins, or registry state;
- reject a Helm binary resolved from PATH;
- inspect or restrict configured Helm repositories;
- scan repository automation for unauthorized bare Helm commands.

## Unsafe execution paths found in the repository

### `playbooks/platform.yml`

Observed behavior:

```text
hosts: k3s_servers[0]
read installed Helm using bare "helm"
download upstream get-helm-3 from the upstream main branch
pipe the installer into bash
install the requested version on the remote control-plane host
add repositories using bare "helm repo add"
update repositories using bare "helm repo update"
```

This creates an additional execution-host dependency beyond the iMac and Mac
mini controller dependency.

### Bare Helm command sites

The source inventory found executable bare Helm use in:

```text
playbooks/tasks/ui.yml
playbooks/tasks/network-storage.yml
playbooks/tasks/longhorn.yml
playbooks/tasks/observability.yml
playbooks/platform.yml
```

Affected services include:

```text
Headlamp
Kubernetes Dashboard
MetalLB
NFS HDD provisioner
NFS SSD provisioner
Longhorn
Prometheus and Grafana
```

### Ansible Helm modules without an enforced binary path

The source inventory found:

```text
kubernetes.core.helm_plugin
kubernetes.core.helm
```

in the observability path. No repository guardrail had yet proved which Helm
binary and Helm state those modules would use.

## Control-gap matrix

| Required control | Policy intent existed | Preventive control existed | Result |
|---|---:|---:|---|
| Repository-managed Helm version | partial | no | gap |
| Isolated Helm state | implicit | no | gap |
| No bare Helm execution | implicit | no | gap |
| Approved repository registry | partial | no | gap |
| Controller-only Helm execution | partial | no | gap |
| Remote execution-host equivalence | stated | no | gap |
| API admission rejection | newly identified need | no | gap |
| Evidence publication gate | yes | yes, but late | detective only |

## Risk

The immediate failure was a harmless chart-pull failure, but the same escape
path could select different chart indexes, plugins, credentials, registry
settings, or Helm behavior on another workstation or control-plane host. A
future command might render or deploy different Kubernetes resources while
appearing to follow repository procedure.

The cost is not limited to money. Potential impact includes:

- unexpected workload placement;
- excessive CPU, memory, storage, or network consumption;
- unsafe stateful workload deployment;
- changes that cannot be reproduced from Git;
- evidence records that claim repeatability despite hidden machine state;
- larger recovery and troubleshooting effort.

## Enforcement classes selected for remediation

The pause decision established four SAGE enforcement classes:

1. **Source guardrail** — persistent configuration, versions, repositories, and
   procedures originate in Git.
2. **Controller guardrail** — only repository-managed tools and isolated state
   execute.
3. **Admission guardrail** — the Kubernetes API rejects unauthorized or
   noncompliant rendered resources.
4. **Evidence gate** — positive and negative guardrail evidence is required
   before implementation acceptance.

The exact implementation and admission policy details remain planned work and
are not claimed as complete by this package.
