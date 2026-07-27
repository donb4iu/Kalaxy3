---
evidence_id: SAGE-K3-SECURITY-20260726-001
schema_version: "1.2"
title: Canonical Kalaxy3 Controller Access Baseline and Legacy Intel Administration Retirement
nav_title: Enforce canonical controller access across Kalaxy3
nav_section: security
nav_order: 30
summary: Validates a repository-owned dual-controller SSH and sudo baseline across seven Kalaxy3 nodes and retires the legacy Intel pi administration path.
primary_subject: Kalaxy3 controller access baseline
project: Kalaxy3
record_type: security
status: validated
classification: internal
work_session: Kalaxy3 SAGE enforcement guardrails and canonical controller access
work_started_at: 2026-07-26T19:56:00-05:00
work_completed_at: 2026-07-26T21:21:00-05:00
evidence_collected_at: 2026-07-26T21:21:00-05:00
created_at: 2026-07-26T21:30:00-05:00
updated_at: 2026-07-26T21:44:01-05:00
valid_as_of: 2026-07-26
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
owner: Don Buddenbaum
author: ChatGPT
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donbs-imac and donb-mac-mini
controller_host: donbs-imac and donb-mac-mini
nodes:
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
  - amd64-01
  - amd64-02
node_addresses:
  - arm64-01=192.168.2.51
  - arm64-02=192.168.2.52
  - arm64-03=192.168.2.53
  - arm64-04=192.168.2.54
  - arm64-05=192.168.2.55
  - amd64-01=192.168.2.61
  - amd64-02=192.168.2.62
namespaces:
  - not-applicable
endpoints:
  - origin=github.com/donb4iu/Kalaxy3
  - ssh-arm64-01=192.168.2.51
  - ssh-arm64-02=192.168.2.52
  - ssh-arm64-03=192.168.2.53
  - ssh-arm64-04=192.168.2.54
  - ssh-arm64-05=192.168.2.55
  - ssh-amd64-01=192.168.2.61
  - ssh-amd64-02=192.168.2.62
components:
  - ansible-core=2.18.7
  - ansible.posix=1.6.2
  - Python=3.12.4
  - K3s=v1.36.2+k3s1
  - SSH-host-trust=repository-owned
  - sudo-policy=90-kalaxy3-ansible-admin
repository: donb4iu/Kalaxy3
branch: feature/sage-enforcement-guardrails
implementation_commit: e77cb1620e1f7b1231ebd162d9506d4123520c88
record_path: markdown/security/kalaxy3-controller-access-baseline-sage-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001
confidence: high
tags:
  - sage
  - security
  - ssh
  - sudo
  - controller-access
  - dual-controller
  - ansible
  - idempotency
  - least-privilege
  - legacy-retirement
relationships:
  verifies:
    - Kalaxy3 canonical controller access baseline
    - Dual-controller SSH continuity
    - Noninteractive SSH and sudo on all seven inventory nodes
    - Retirement of the Intel legacy pi administration path
  depends_on:
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/standards/kalaxy3-sage-evidence-publication-process.md
    - markdown/templates/sage-evidence-record-template.md
    - markdown/standards/sage-evidence-metadata-contract-v1.2.json
  supersedes:
    - markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md
  superseded_by:
    - none
  related_to:
    - infrastructure/k3s-homelab/Makefile
    - infrastructure/k3s-homelab/inventory/ssh_known_hosts
    - infrastructure/k3s-homelab/scripts/sage-source-guardrails.py
  conflicts_with:
    - none
  generated_by:
    - infrastructure/k3s-homelab/playbooks/access-baseline.yml
    - infrastructure/k3s-homelab/scripts/ansible-access-preflight.py
    - Manual terminal validation from donbs-imac and donb-mac-mini
    - ChatGPT working-session evidence synthesis
    - scripts/sage/sage-publish.py
  implemented_by:
    - e77cb1620e1f7b1231ebd162d9506d4123520c88
  revalidated_by:
    - none
---
# Canonical Kalaxy3 Controller Access Baseline and Legacy Intel Administration Retirement

## Executive summary

Kalaxy3 controller access was normalized and validated across all seven cluster
nodes. The five ARM64 nodes retain `pi` as their inventory account, while the
two AMD64 nodes retain `dbuddenbaum`; every active inventory account now has
exactly the two repository-approved controller public keys and the same
validated passwordless-sudo policy at
`/etc/sudoers.d/90-kalaxy3-ansible-admin`. The separate Intel `pi`
administration route was retired by removing its SSH authorization, sudo-group
membership, and `90-kalaxy3-pi` policy while retaining the password-locked
account for historical continuity. SSH, privilege escalation, strict
repository-owned host trust, representative independent Mac mini access, and a
full seven-node idempotency pass succeeded. The implementation resolves to
`e77cb1620e1f7b1231ebd162d9506d4123520c88`. This record is `validated`; independent
review remains pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-SECURITY-20260726-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Canonical Kalaxy3 Controller Access Baseline and Legacy Intel Administration Retirement |
| **Navigation title** | Enforce canonical controller access across Kalaxy3 |
| **Navigation section** | security |
| **Navigation order** | 30 |
| **Summary** | Validates a repository-owned dual-controller SSH and sudo baseline across seven Kalaxy3 nodes and retires the legacy Intel pi administration path. |
| **Primary subject** | Kalaxy3 controller access baseline |
| **Record type** | security |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Kalaxy3 SAGE enforcement guardrails and canonical controller access |
| **Started** | 2026-07-26T19:56:00-05:00 |
| **Completed** | 2026-07-26T21:21:00-05:00 |
| **Evidence collected** | 2026-07-26T21:21:00-05:00 |
| **Record created** | 2026-07-26T21:30:00-05:00 |
| **Record updated** | 2026-07-26T21:44:01-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago |
| **Valid as of** | 2026-07-26 |
| **Review due** | event-based |
| **Target record path** | markdown/security/kalaxy3-controller-access-baseline-sage-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/sage-enforcement-guardrails |
| **Implementation commit** | e77cb1620e1f7b1231ebd162d9506d4123520c88 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac and donb-mac-mini |
| **Controller host** | donbs-imac and donb-mac-mini |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62 |
| **Namespaces** | not-applicable |
| **Endpoints** | origin=github.com/donb4iu/Kalaxy3; ssh-arm64-01=192.168.2.51; ssh-arm64-02=192.168.2.52; ssh-arm64-03=192.168.2.53; ssh-arm64-04=192.168.2.54; ssh-arm64-05=192.168.2.55; ssh-amd64-01=192.168.2.61; ssh-amd64-02=192.168.2.62 |
| **Components and versions** | ansible-core=2.18.7; ansible.posix=1.6.2; Python=3.12.4; K3s=v1.36.2+k3s1; SSH-host-trust=repository-owned; sudo-policy=90-kalaxy3-ansible-admin |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author ChatGPT, operator Don Buddenbaum, owner Don Buddenbaum, and reviewer pending. The affected users are the Kalaxy3 operator and future authorized automation controllers. |
| **What** | Replaced inconsistent controller-access paths with one behaviorally uniform baseline: two approved controller keys on every active inventory account, one canonical sudo policy, separate SSH and privilege gates, and retirement of the extra Intel `pi` root-capable route. |
| **When** | Work started 2026-07-26T19:56:00-05:00, completed 2026-07-26T21:21:00-05:00, and evidence was collected through 2026-07-26T21:21:00-05:00. Local and system timestamps use America/Chicago. The result is valid as of 2026-07-26 and is reviewed event-based. |
| **Where** | Environment homelab; system Kalaxy3; cluster kalaxy3; execution host donbs-imac and donb-mac-mini; controller host donbs-imac and donb-mac-mini; nodes arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; node addresses arm64-01=192.168.2.51; arm64-02=192.168.2.52; arm64-03=192.168.2.53; arm64-04=192.168.2.54; arm64-05=192.168.2.55; amd64-01=192.168.2.61; amd64-02=192.168.2.62; namespace not-applicable; endpoints origin=github.com/donb4iu/Kalaxy3; ssh-arm64-01=192.168.2.51; ssh-arm64-02=192.168.2.52; ssh-arm64-03=192.168.2.53; ssh-arm64-04=192.168.2.54; ssh-arm64-05=192.168.2.55; ssh-amd64-01=192.168.2.61; ssh-amd64-02=192.168.2.62; repository donb4iu/Kalaxy3; branch feature/sage-enforcement-guardrails; record markdown/security/kalaxy3-controller-access-baseline-sage-evidence.md. |
| **Why** | The cluster had different active account names by architecture plus an additional Intel `pi` SSH-and-sudo path created by an older playbook. The inconsistency expanded administrative attack surface, made controller access harder to audit, and caused the existing preflight to hide whether SSH or sudo was failing. |
| **How** | Repository-owned public keys, host trust, Ansible playbooks, and preflights were committed in small pushed checkpoints. Read-only audits established the starting state; check-mode failures were corrected; one Intel and one ARM node were applied as canaries; the Mac mini independently verified representative paths; the remaining nodes were updated sequentially; and all seven nodes passed exact key, sudo, legacy-path, SSH, privilege, and idempotency checks. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Active Ansible inventory accounts on all seven Kalaxy3 nodes.
- Repository-approved Mac mini ED25519 and iMac RSA-4096 controller keys.
- Repository-owned strict SSH host trust for all seven nodes.
- Independent SSH-only and privilege-escalation preflights.
- Canonical `90-kalaxy3-ansible-admin` sudo policy with `visudo` validation.
- Removal of superseded `90-k3s-admin` files.
- Retirement of the Intel legacy `pi` SSH, sudo-group, and sudoers path.
- Check-mode behavior, controlled canary rollout, sequential expansion, and
  full idempotency validation.
- Git implementation lineage and evidence-only SAGE publication.

### Out of scope

- Renaming ARM or Intel operating-system accounts.
- Deleting the retained Intel `pi` account or its home directory.
- Rotating either controller key or changing private-key storage.
- Adding a third controller or implementing a certificate authority for SSH.
- Changing K3s, Kubernetes workloads, namespaces, services, or storage.
- Capturing exact OpenSSH and sudo package versions.
- Post-rollout direct Mac mini SSH tests against every node; representative
  ARM and Intel nodes were tested directly.

### Nonclaims

This record does **not** claim:

- that account names are identical across architectures;
- that the retained Intel `pi` account has been deleted;
- that password authentication is globally disabled by this playbook;
- that every future controller is authorized automatically;
- that possession of a public key grants access without the matching private
  key;
- that successful SSH and sudo validation proves unrelated cluster workload
  health;
- that the second controller directly tested every node after rollout.

## Final accepted state

```text
ARM active inventory account:            pi
Intel active inventory account:          dbuddenbaum
Approved active-account key count:       2
Approved key 1:                          Mac mini ED25519 fingerprint
Approved key 2:                          iMac RSA-4096 fingerprint
Repository SSH trust:                    7-node strict known-hosts file
Canonical sudoers file:                  /etc/sudoers.d/90-kalaxy3-ansible-admin
Canonical sudoers owner/mode:             root:root 0440
Canonical sudoers validation:             parsed OK on all seven nodes
Noninteractive SSH:                      PASS on all seven nodes
Noninteractive privilege escalation:     UID 0 on all seven nodes
Superseded 90-k3s-admin:                 absent on all seven nodes
Intel retained pi password:              locked
Intel retained pi sudo group:            absent
Intel retained pi authorized_keys:       absent or empty
Intel 90-kalaxy3-pi:                     absent
Representative Mac mini ARM access:      PASS
Representative Mac mini Intel access:    PASS
Final playbook convergence:              changed=0, unreachable=0, failed=0
Kubernetes workloads changed:            none
```

| Item | Accepted result |
|---|---|
| Active access contract | Architecture-specific account names are allowed, but key count, approved identities, host trust, and sudo behavior are uniform. |
| Key authority | The two public-key files under `access/controller-keys` are the approved active-account authorization set. |
| Sudo authority | `90-kalaxy3-ansible-admin` is the only playbook-managed passwordless-sudo policy in this access baseline. |
| Legacy Intel path | The historical `pi` account remains locked but has no controller SSH authorization, sudo-group membership, or dedicated sudoers rule. |
| Preflight semantics | SSH authentication and privilege escalation can fail and be diagnosed independently. |
| Repeatability | A second full playbook execution made zero changes on every node. |
| Git lineage | The implementation resolves to `e77cb1620e1f7b1231ebd162d9506d4123520c88`. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Before this change, both Intel nodes had two parallel root-capable controller paths. | critical | `EV-001`, `EV-002` | supported | high |
| `CLM-002` | Every active inventory account now contains exactly the two approved controller keys. | critical | `EV-006`, `EV-008`, `EV-009`, `EV-010` | supported | high |
| `CLM-003` | Every node now has a valid canonical passwordless-sudo policy and returns UID 0 noninteractively. | critical | `EV-004`, `EV-006`, `EV-008`, `EV-010` | supported | high |
| `CLM-004` | The Intel legacy `pi` SSH and sudo path is retired while the account remains locked. | critical | `EV-006`, `EV-009`, `EV-010` | supported | high |
| `CLM-005` | SSH authentication and privilege escalation are independently testable controls. | high | `EV-004`, `EV-010` | supported | high |
| `CLM-006` | The access playbook is safe to preview in check mode after the documented corrections. | high | `EV-005`, `EV-008` | supported | high |
| `CLM-007` | The approved Mac mini controller can still access representative ARM and Intel nodes after normalization. | critical | `EV-007`, `EV-008` | supported | high |
| `CLM-008` | The final access baseline converges idempotently across all seven nodes. | critical | `EV-006`, `EV-008`, `EV-010` | supported | high |
| `CLM-009` | The implementation is preserved in Git through frequent remote checkpoints. | high | `EV-003`, `EV-011` | supported | high |
| `CLM-010` | No Kubernetes workload or cluster-resource change was required for this security baseline. | normal | `EV-003`, `EV-006`, `EV-008`, `EV-009`, `EV-010` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The live system had architecture-specific active accounts, which was acceptable,
but it also had inconsistent sudoers files and an additional Intel `pi`
administrator created by an earlier provisioning playbook. That retained path
accepted only the Mac mini key and had unrestricted passwordless sudo. The
existing Ansible ping preflight inherited become settings, so it did not
distinguish transport authentication from privilege escalation. Repository
source, live state, and intended controller policy had drifted.

### Decision

Keep the established active inventory accounts (`pi` on ARM and `dbuddenbaum`
on Intel), but enforce one behavioral security contract everywhere:

1. exactly the two approved controller public keys on the active account;
2. repository-owned strict host trust;
3. a single canonical passwordless-sudo policy;
4. independent SSH and privilege preflights;
5. no active controller authorization on the retained Intel `pi` account.

### Decision drivers

- Reduce redundant root-capable access paths.
- Preserve working architecture-specific account names without unnecessary
  operating-system migrations.
- Keep both established controller machines functional.
- Make authorization and host trust reviewable in Git.
- Fail closed before removing an existing sudo path.
- Support clean rebuild and bootstrap cases where passwordless sudo does not
  yet exist.
- Provide deterministic check-mode and idempotency evidence.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Rename every node to one common account | Superficially uniform inventory | High-risk account migration with little security value; changes ownership and rebuild assumptions | rejected |
| Keep both Intel `pi` and `dbuddenbaum` as root-capable paths | Maximum short-term access redundancy | Doubles administrative paths and preserves a one-controller legacy key set | rejected |
| Delete the Intel `pi` account immediately | Removes legacy identity completely | Larger irreversible change; could erase useful history or files before review | deferred |
| Keep existing sudoers filenames per installation | Minimal live change | Continues inconsistent policy names and source drift | rejected |
| Enforce approved keys but leave extra keys | Avoids removing ad hoc access | Prevents deterministic authorization review and retains unknown paths | rejected |
| Enforce both keys exclusively and one canonical sudoers policy | Deterministic, reviewable, dual-controller, and idempotent | Intentional removal of any undeclared ad hoc key | accepted |
| Test SSH and sudo with one inherited-become ping | One command | Cannot identify whether transport or privilege is broken | rejected |
| Split SSH and privilege preflights | Clear diagnosis and independent gates | Two checks instead of one | accepted |

### Tradeoffs and consequences

- `exclusive: true` intentionally removes any undeclared key from active
  inventory accounts.
- The retained Intel `pi` account still exists and should not be mistaken for
  an authorized controller account.
- First-time rebuilds may require a sudo password or console/bootstrap access
  before the canonical policy can be installed.
- Public controller keys are version controlled; matching private keys remain
  machine-local and are not recoverable from Git.
- Direct post-rollout Mac mini testing sampled one ARM and one Intel node rather
  than all seven; the iMac independently verified exact approved fingerprints
  and state on all seven.
- The playbook removes the retained Intel `pi` `authorized_keys` file, so future
  intentional use of that account requires a separately reviewed policy change.

## Architecture or change description

```text
donb4iu/Kalaxy3 feature/sage-enforcement-guardrails
  |
  +-- inventory/ssh_known_hosts
  |     +--> strict host identity for 7 nodes
  |
  +-- access/controller-keys/
  |     +--> donb-mac-mini-ed25519.pub
  |     +--> donbs-imac-rsa.pub
  |
  +-- scripts/ansible-access-preflight.py
  |     +--> --scope ssh       (become=false)
  |     +--> --scope privilege (become=true, UID 0)
  |     +--> --scope all
  |
  +-- playbooks/access-baseline.yml
        |
        +--> all active inventory accounts
        |     +--> exclusive approved two-key set
        |     +--> 90-kalaxy3-ansible-admin
        |     +--> sudo -n verification
        |     +--> remove 90-k3s-admin
        |
        +--> longhorn_nodes / Intel only
              +--> retain locked pi account
              +--> remove pi from sudo group
              +--> remove pi authorized_keys
              +--> remove 90-kalaxy3-pi
              +--> assert retired state
```

### Before

```text
ARM:
  active pi account
  two controller keys
  preexisting passwordless sudo through noncanonical host setup

Intel:
  active dbuddenbaum account
  two controller keys
  90-k3s-admin
  plus retained pi account
  Mac mini key only
  sudo group and 90-kalaxy3-pi
```

### After

```text
ARM:
  active pi account
  exact two approved controller keys
  canonical 90-kalaxy3-ansible-admin

Intel:
  active dbuddenbaum account
  exact two approved controller keys
  canonical 90-kalaxy3-ansible-admin
  retained pi locked with no SSH authorization, sudo group, or sudoers rule
```

## Source of truth and implementation lineage

### Repository files

```text
.gitignore
infrastructure/k3s-homelab/Makefile
infrastructure/k3s-homelab/ansible.cfg
infrastructure/k3s-homelab/access/controller-keys/donb-mac-mini-ed25519.pub
infrastructure/k3s-homelab/access/controller-keys/donbs-imac-rsa.pub
infrastructure/k3s-homelab/inventory/group_vars/all/main.yml
infrastructure/k3s-homelab/inventory/ssh_known_hosts
infrastructure/k3s-homelab/playbooks/access-baseline.yml
infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
infrastructure/k3s-homelab/scripts/ansible-access-preflight.py
infrastructure/k3s-homelab/scripts/bootstrap-ssh-key.py
infrastructure/k3s-homelab/scripts/controller-preflight.py
infrastructure/k3s-homelab/scripts/sage-source-guardrails.py
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-publish.py
scripts/sage/sage-index.py
```

Retired active implementation source:

```text
infrastructure/k3s-homelab/playbooks/intel-admin-access.yml
```

### Implementation commit

```text
e77cb1620e1f7b1231ebd162d9506d4123520c88
Fix access baseline check-mode validation
```

The full implementation SHA includes the preceding guardrail, approved-key,
preflight-split, and access-baseline commits through Git ancestry.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| Python | 3.12.4 | repository-managed controller runtime |
| ansible-core | 2.18.7 | repository requirements |
| ansible.posix | 1.6.2 | repository-managed Ansible collection |
| K3s | v1.36.2+k3s1 | observed installed version and repository release guardrail |
| OpenSSH server/client | not-captured | evidence gap; functional behavior directly tested |
| sudo | not-captured | evidence gap; policy parsing and UID 0 behavior directly tested |

### Configuration excerpt

```yaml
- name: Install the complete approved controller key set
  ansible.posix.authorized_key:
    user: "{{ ansible_user }}"
    state: present
    key: "{{ kalaxy3_controller_public_keys }}"
    exclusive: true
    manage_dir: true

- name: Install the canonical Ansible sudo policy
  ansible.builtin.copy:
    dest: /etc/sudoers.d/90-kalaxy3-ansible-admin
    content: "{{ ansible_user }} ALL=(ALL:ALL) NOPASSWD: ALL\n"
    owner: root
    group: root
    mode: "0440"
    validate: /usr/sbin/visudo -cf %s

- name: Verify noninteractive sudo through the canonical policy
  ansible.builtin.command:
    argv: [sudo, -n, id, -u]
  become: false
  changed_when: false

- name: Remove the legacy Intel pi passwordless-sudo policy
  ansible.builtin.file:
    path: /etc/sudoers.d/90-kalaxy3-pi
    state: absent
```

No public-key bodies are reproduced in this record. The authoritative public
keys are the repository files named above.

## Prerequisites and assumptions

### Proven prerequisites

- The iMac and Mac mini approved private keys existed locally and matched the
  repository public-key fingerprints.
- All seven node host keys were represented in
  `inventory/ssh_known_hosts`.
- Before rollout, the active inventory accounts accepted noninteractive SSH and
  privilege escalation.
- The repository-managed controller toolchain passed exact version checks.
- Both approved controller key files were committed and pushed before the live
  access change.
- The existing Intel `pi` account was password locked before its legacy SSH and
  sudo paths were removed.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The two repository public keys remain controlled by Don Buddenbaum and correspond to protected private keys. | Unauthorized private-key possession would permit administrative access. | Rotate the affected key immediately and rerun the baseline and all-node validation. |
| `ASM-002` | Local or physical console recovery remains available if both controller keys become unusable. | Simultaneous key loss could lock out remote administration. | Document and periodically test host-console recovery separately. |
| `ASM-003` | No service depends on SSH login as the retained Intel `pi` account. | Removing its authorization could break undocumented automation. | Revalidate after any discovery of scripts or services naming Intel `pi`. |
| `ASM-004` | Repository host-key records remain authentic after intentional node rebuilds. | A stale record fails closed; an improperly replaced record could trust the wrong host. | Review host replacement evidence and update trust through the repository process. |

No material assumption was used in place of the direct acceptance tests. The
remaining assumptions describe credential custody and recovery dependencies.

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab

make bootstrap-guardrails
make k3s-release-guardrail
make controller-helm-preflight
make deployment-guardrail
make helm-lock-reconcile
make ansible-access-preflight
```

Read-only baseline collection established active accounts, key fingerprints,
sudo rules, host trust, and the live Intel legacy path before implementation.

### Execution

Repository checkpoints were committed and pushed after each logical change:

```text
guardrail framework
approved controller public keys
split SSH and privilege preflights
canonical access-baseline playbook
check-mode validation corrections
```

The rollout sequence was:

```bash
# Read-only Intel preview
ansible-playbook playbooks/access-baseline.yml   --limit amd64-01 --check --diff

# Real Intel canary and second run
ansible-playbook playbooks/access-baseline.yml   --limit amd64-01 --diff

# Read-only ARM preview
ansible-playbook playbooks/access-baseline.yml   --limit arm64-01 --check --diff

# Real ARM canary and second run
ansible-playbook playbooks/access-baseline.yml   --limit arm64-01 --diff

# Remaining nodes, serialized
ansible-playbook playbooks/access-baseline.yml   --limit 'arm64-02:arm64-03:arm64-04:arm64-05:amd64-02'   --forks 1 --diff

# Final all-node convergence
ansible-playbook playbooks/access-baseline.yml --forks 1
```

Mac mini direct SSH checks were performed after the Intel and ARM canaries with:

```text
IdentitiesOnly=yes
BatchMode=yes
StrictHostKeyChecking=yes
UserKnownHostsFile=inventory/ssh_known_hosts
```

### Expected change

- Active accounts retain their architecture-specific names.
- Active accounts converge to exactly the two approved keys.
- The canonical sudoers file is installed and validated before old files are
  removed.
- Intel `pi` remains locked but loses controller SSH and unrestricted sudo.
- SSH and privilege tests pass independently.
- A second identical playbook run produces zero changes.

### Observed change

All expected changes occurred. The canary and remaining-node runs had no failed
or unreachable hosts. Representative Mac mini direct checks passed. The final
seven-node run reported zero changes and zero failures.

## Evidence items

### `EV-001` — Active-account and controller baseline

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001`, `CLM-002`, `CLM-003` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26 before 20:05 America/Chicago |
| Execution source | `donbs-imac`, then `donb-mac-mini` |
| Target | All seven inventory nodes |
| Tool and version | ansible-core 2.18.7; OpenSSH version not captured |
| Expected result | Establish the real active accounts, key fingerprints, sudo behavior, and strict trust behavior before mutation |
| Actual result | pass; active accounts had both keys and sudo; stale Mac mini trust failed closed until authoritative trust was used |
| Confidence | high |
| Sensitive data | Public-key bodies omitted; fingerprints retained |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; external checksums artifact |

### `EV-002` — Intel parallel-root-path audit

| Field | Value |
|---|---|
| Classification | `direct-observation` and `repository-evidence` |
| Supports or contradicts | `CLM-001`, `CLM-004` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T20:05:03-05:00 |
| Execution source | `donbs-imac` |
| Target | `amd64-01`, `amd64-02`, and legacy playbook source |
| Tool and version | ansible-core 2.18.7; `getent`, `passwd`, `ssh-keygen`, `sudo`, `visudo` versions not captured |
| Expected result | Determine whether legacy `pi` access remained live |
| Actual result | pass; both Intel nodes had active `pi` key and passwordless-sudo paths in addition to `dbuddenbaum` |
| Confidence | high |
| Sensitive data | Public-key bodies omitted; fingerprints retained |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; `acccd691...` external artifact |

### `EV-003` — Guardrail and Git checkpoint validation

| Field | Value |
|---|---|
| Classification | `repository-evidence` and `direct-observation` |
| Supports or contradicts | `CLM-009`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T20:07:00-05:00 through 2026-07-26T21:01:00-05:00 |
| Execution source | `donbs-imac` |
| Target | Feature branch and repository guardrails |
| Tool and version | Git version not captured; Python 3.12.4; ansible-core 2.18.7; Helm v3.21.3 |
| Expected result | Store recoverable source checkpoints and prove source/dependency gates before live access changes |
| Actual result | pass; five logical commits were pushed and required gates passed |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/implementation-commit-summary.txt`; `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md` |

### `EV-004` — Split SSH and privilege gates

| Field | Value |
|---|---|
| Classification | `repository-evidence` and `direct-observation` |
| Supports or contradicts | `CLM-003`, `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T20:25:00-05:00 through 2026-07-26T20:29:00-05:00 |
| Execution source | `donbs-imac` |
| Target | All seven inventory nodes |
| Tool and version | Python 3.12.4; ansible-core 2.18.7 |
| Expected result | SSH-only scope passes without become; privilege scope proves UID 0; combined scope requires both |
| Actual result | pass on all seven; bootstrap and recovery gates also passed |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md` |

### `EV-005` — Negative check-mode evidence and corrections

| Field | Value |
|---|---|
| Classification | `negative-evidence`, `repository-evidence`, and `direct-observation` |
| Supports or contradicts | `CLM-006`, `CLM-009` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T20:40:00-05:00 through 2026-07-26T21:00:00-05:00 |
| Execution source | `donbs-imac` |
| Target | Access-baseline source and `amd64-01` check mode |
| Tool and version | Python 3.12.4; ansible-core 2.18.7 |
| Expected result | Preview completes without node mutation |
| Actual result | initial failures exposed missing-file assumption, skipped read-only command, simulated-removal assertion, and status-parser defects; corrected preview passed with failed=0 |
| Confidence | high |
| Sensitive data | Public-key bodies omitted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md` |

### `EV-006` — Intel canary and idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004`, `CLM-008`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T21:02:53-05:00 through 2026-07-26T21:05:08-05:00 |
| Execution source | `donbs-imac` |
| Target | `amd64-01` |
| Tool and version | ansible-core 2.18.7; system utilities versions not captured |
| Expected result | Normalize active account, validate new sudo before removing old policy, retire legacy `pi`, and converge on second run |
| Actual result | pass; first run changed=6, second run changed=0, failed=0 |
| Confidence | high |
| Sensitive data | Public-key bodies omitted; fingerprints retained |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; external canary and postvalidation checksums |

### `EV-007` — Independent Mac mini Intel check

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T21:07:30-05:00 |
| Execution source | `donb-mac-mini` |
| Target | `dbuddenbaum@amd64-01` |
| Tool and version | OpenSSH version not captured |
| Expected result | Strict direct SSH with the approved ED25519 key and noninteractive sudo succeeds |
| Actual result | pass; remote user `dbuddenbaum`, sudo UID 0 |
| Confidence | high |
| Sensitive data | Private key not captured |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; `2311a70...` external artifact |

### `EV-008` — ARM preview, canary, independent check, and idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-006`, `CLM-007`, `CLM-008`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T21:08:48-05:00 through 2026-07-26T21:13:50-05:00 |
| Execution source | `donbs-imac` and `donb-mac-mini` |
| Target | `arm64-01` |
| Tool and version | ansible-core 2.18.7; OpenSSH version not captured |
| Expected result | Keep active `pi`, install exact approved keys and canonical sudo, skip Intel retirement, converge, and remain accessible from Mac mini |
| Actual result | pass; preview failed=0, canary failed=0, second run changed=0, Mac mini sudo UID 0 |
| Confidence | high |
| Sensitive data | Private keys not captured; public-key bodies omitted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; four external artifact checksums |

### `EV-009` — Serialized remaining-node rollout

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T21:15:12-05:00 |
| Execution source | `donbs-imac` |
| Target | `arm64-02` through `arm64-05`, `amd64-02` |
| Tool and version | ansible-core 2.18.7 |
| Expected result | Four ARM accounts normalize; second Intel node also retires legacy `pi`; no failed or unreachable hosts |
| Actual result | pass; ARM changed=2 each, Intel changed=6, all failed=0 and unreachable=0 |
| Confidence | high |
| Sensitive data | Public-key bodies omitted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; `076c78d...` external artifact |

### `EV-010` — Final seven-node validation and idempotency

| Field | Value |
|---|---|
| Classification | `direct-observation` and `generated-artifact` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-004`, `CLM-005`, `CLM-008`, `CLM-010` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T21:18:17-05:00 through 2026-07-26T21:21:00-05:00 |
| Execution source | `donbs-imac` |
| Target | All seven Kalaxy3 nodes |
| Tool and version | Python 3.12.4; ansible-core 2.18.7; ansible.posix 1.6.2 |
| Expected result | SSH and privilege pass; exact two fingerprints and canonical sudo exist; legacy Intel route absent; second playbook run changed=0 |
| Actual result | pass on every node; changed=0, unreachable=0, failed=0 |
| Confidence | high |
| Sensitive data | Public-key bodies omitted; fingerprints retained |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md`; `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/validation-summary.json`; `46814bb...` external artifact |

### `EV-011` — Source and artifact integrity inventory

| Field | Value |
|---|---|
| Classification | `generated-artifact` and `repository-evidence` |
| Supports or contradicts | `CLM-009` |
| Collected by | Don Buddenbaum and ChatGPT |
| Collected at | 2026-07-26 working session and package generation |
| Execution source | `donbs-imac` and evidence generator |
| Target | Repository source, external evidence files, and package artifacts |
| Tool and version | SHA-256; tool versions vary or not captured |
| Expected result | Preserve implementation lineage and deterministic evidence hashes without storing secrets |
| Actual result | pass |
| Confidence | high |
| Sensitive data | no private keys or credentials; public-key bodies intentionally omitted |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/external-artifact-checksums.sha256`; `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/implementation-commit-summary.txt` |

## Verification and acceptance criteria

| Criterion | Expected result | Observed result | Evidence | Status |
|---|---|---|---|---|
| Repository host trust | Seven declared hosts and strict checking | Seven-host trust passed; stale Mac mini trust failed closed before correction | `EV-001`, `EV-003` | pass |
| Approved active keys | Exactly two approved fingerprints per active account | Two exact fingerprints on all seven nodes | `EV-006`, `EV-008`, `EV-010` | pass |
| Canonical sudoers | root-owned mode 0440, parses, returns UID 0 | Passed on all seven nodes | `EV-006`, `EV-008`, `EV-010` | pass |
| Superseded sudoers | `90-k3s-admin` absent | Absent on all seven nodes | `EV-006`, `EV-008`, `EV-010` | pass |
| Intel legacy sudo | `90-kalaxy3-pi` and sudo group absent | Absent on both Intel nodes | `EV-006`, `EV-009`, `EV-010` | pass |
| Intel legacy SSH | retained `pi` has no nonempty `authorized_keys` | Absent or empty on both Intel nodes | `EV-006`, `EV-009`, `EV-010` | pass |
| Intel account safety | retained `pi` password remains locked | Locked on both Intel nodes | `EV-006`, `EV-010` | pass |
| SSH-only gate | all seven return Ansible pong without become | PASS | `EV-004`, `EV-010` | pass |
| Privilege gate | all seven return UID 0 noninteractively | PASS | `EV-004`, `EV-010` | pass |
| Mac mini continuity | representative ARM and Intel direct checks pass | PASS on `arm64-01` and `amd64-01` | `EV-007`, `EV-008` | pass |
| Check-mode safety | previews complete without failure or mutation | PASS after documented corrections | `EV-005`, `EV-008` | pass |
| Idempotency | second complete run changes nothing | All seven changed=0, failed=0 | `EV-010` | pass |
| Workload isolation | no K3s workload deployment or restart required | No cluster-resource command in access playbook | `EV-003`, `EV-010` | pass |
| Implementation lineage | full committed SHA is resolvable | `e77cb1620e1f7b1231ebd162d9506d4123520c88` | `EV-003`, `EV-011` | pass |

Acceptance result: all technical criteria passed. The record remains
`validated`, rather than `accepted`, pending independent reviewer approval.

## Idempotency and repeatability

### Test performed

After both canaries and the complete remaining-node rollout, the same
`playbooks/access-baseline.yml` playbook was run across all seven nodes with
`--forks 1`.

### Observed result

```text
amd64-01: changed=0 unreachable=0 failed=0
amd64-02: changed=0 unreachable=0 failed=0
arm64-01: changed=0 unreachable=0 failed=0
arm64-02: changed=0 unreachable=0 failed=0
arm64-03: changed=0 unreachable=0 failed=0
arm64-04: changed=0 unreachable=0 failed=0
arm64-05: changed=0 unreachable=0 failed=0
```

The check-mode preview is also repeatable because the two read-only discovery
commands explicitly execute during check mode, while the real post-removal
assertion is skipped only when changes are simulated.

### Interpretation

The automation converges deterministically for the evidenced seven-node
inventory. Key comments and order are normalized because the complete approved
set is supplied to a single `authorized_key` invocation with `exclusive: true`.

## Security, privacy, and evidence handling

### Security controls

- Active account authorization is exactly the repository-approved two-key set.
- Strict host checking uses the repository-owned seven-node trust file.
- SSH and sudo are tested independently and fail closed.
- Canonical sudoers content is validated with `visudo` before installation.
- The new sudo policy is proven before the old active-account policy is
  removed.
- The Intel legacy root-capable path is retired.
- The retained Intel `pi` password remains locked.
- Playbook application was serialized during the broad rollout.
- Git checkpoints were pushed before live changes and after source corrections.

### Credential and secret handling

- Only public keys are version controlled.
- No private key was copied, displayed, or packaged.
- Public-key bodies are intentionally omitted from terminal artifacts; stable
  fingerprints prove identity.
- No password, password hash, token, kubeconfig content, bearer credential,
  Ansible Vault plaintext, or Kubernetes Secret is present.
- Local Downloads artifacts are referenced by checksum rather than embedded
  when the original files were not available to the package generator.

### Residual risks

- Compromise of either approved private key grants the access authorized by its
  corresponding public key.
- Passwordless unrestricted sudo is powerful; this baseline reduces duplicate
  paths but does not implement command-scoped sudo.
- The repository trust file must be updated through a reviewed process after a
  legitimate host rebuild.
- Physical or console recovery is outside this record.
- A future change to `ansible_user` must update both key and sudo policy
  evidence.

## Reliability, recovery, rollback, and rebuild

### Reliability

The final state is declarative, repository owned, and idempotent. Failure of one
controller does not remove the other approved controller key. Host-key mismatch
fails before authentication. Sudo is verified before superseded active-account
sudoers files are removed.

### Recovery from lost active-account authorization

Use physical console, another still-approved controller, or another explicitly
authorized break-glass path to restore the two repository public keys to the
active inventory account. Then run:

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
make access-baseline
make ansible-access-preflight
```

When passwordless sudo has not yet been established on a rebuilt node, use the
repository bootstrap target and provide the existing host sudo password:

```bash
make access-baseline-bootstrap
```

Private keys must be restored from their secure controller backup; they cannot
be reconstructed from the repository public keys.

### Rollback

A normal rollback should restore access to the declared active inventory
account, not reactivate the retired Intel `pi` administration route. From local
console or a valid controller:

1. restore the approved active-account public keys;
2. reinstall `90-kalaxy3-ansible-admin` with owner `root:root`, mode `0440`;
3. validate it using `visudo -cf`;
4. prove `sudo -n id -u` returns `0`;
5. rerun `playbooks/access-baseline.yml`.

Reactivating Intel `pi` SSH or passwordless sudo is a new security decision and
requires a reviewed source change and superseding evidence.

### Rebuild sequence

```text
1. Rebuild the host and retain the intended inventory account.
2. Verify the host identity and update repository SSH trust after review.
3. Bootstrap one approved controller key when first access requires it.
4. Run repository controller bootstrap and core preflight.
5. Run access-baseline-bootstrap when a sudo password is still required.
6. Run make access-baseline.
7. Run make ssh-auth-preflight and make privilege-preflight.
8. Verify exact key fingerprints and canonical sudoers state.
9. On Intel, verify retained pi is locked and has no SSH or sudo path.
10. Run the access playbook again and require changed=0.
```

No Kubernetes workload restore is required for this access-only change.

## Operational considerations and observability

- Run `make ansible-access-preflight` before deployment and recovery workflows.
- Use `make ssh-auth-preflight` to isolate transport or key failures.
- Use `make privilege-preflight` to isolate sudo-policy failures.
- Run `make access-baseline` after approved key rotation, inventory account
  changes, or node replacement.
- Review `inventory/ssh_known_hosts` whenever a node host key changes.
- Treat an unexpected nonzero key count, unknown fingerprint, extra sudoers
  file, or Intel `pi` authorization as a security drift event.
- Preserve command output and SHA-256 checksums under the evidence ID artifact
  root during revalidation.
- This baseline does not install continuous SSH or sudo telemetry. Detection is
  preflight- and audit-driven.

## Known limitations, evidence gaps, and risks

| Gap or risk | Effect | Owner | Trigger or resolution |
|---|---|---|---|
| OpenSSH and sudo package versions were not captured | Behavior is proven, but exact package lineage is incomplete | Don Buddenbaum | Capture versions at next access revalidation |
| Post-rollout Mac mini direct access sampled one ARM and one Intel node | Second-controller direct coverage is representative rather than exhaustive | Don Buddenbaum | Run strict direct checks against all seven after key rotation or reviewer request |
| No physical-console recovery test was performed | Remote lockout recovery remains procedural | Don Buddenbaum | Test during a planned maintenance window |
| Passwordless sudo remains unrestricted | A valid controller key can obtain full root | Don Buddenbaum | Evaluate command-scoped sudo only with an operational impact study |
| Intel `pi` account remains present | Identity exists though controller authorization is absent | Don Buddenbaum | Delete only after filesystem and service dependency review |
| No automated key-expiration or certificate authority | Key lifecycle is manual | Don Buddenbaum | Reassess when a third controller or multiple operators are added |
| External raw artifacts remain in Downloads until publication | Loss before publication would remove original raw files, though checksums and material excerpts are preserved here | Don Buddenbaum | Publish package and retain repository artifacts |

No evidence gap contradicts the validated technical claims.

## Troubleshooting

### SSH-only preflight fails

Run:

```bash
make ssh-auth-preflight
```

Check:

- the active `ansible_user`;
- the matching local private key;
- `IdentitiesOnly` and noninteractive SSH behavior;
- repository host-key trust;
- the two expected fingerprints in active-account `authorized_keys`;
- file ownership and mode.

Do not weaken strict host checking to bypass a mismatch. Verify the host
identity and update the repository trust file through review.

### Privilege preflight fails

Run:

```bash
make privilege-preflight
```

On the target, inspect and validate:

```text
/etc/sudoers.d/90-kalaxy3-ansible-admin
owner root
group root
mode 0440
visudo -cf PASS
```

For a first-time rebuild without passwordless sudo, use
`make access-baseline-bootstrap`.

### Check mode reports an undefined legacy account fact

Confirm the read-only `getent passwd pi` and `id -nG pi` tasks use:

```yaml
check_mode: false
changed_when: false
```

These commands must observe real state during a preview.

### Check mode fails the post-removal assertion

The final assertion must contain:

```yaml
when: not ansible_check_mode
```

Check mode simulates file removal but a following `stat` still sees the real
file.

### Intel `pi` remains SSH-accessible

Confirm:

```text
/home/pi/.ssh/authorized_keys is absent or empty
/etc/sudoers.d/90-kalaxy3-pi is absent
pi is not a member of sudo
passwd -S pi reports L
```

Then rerun `playbooks/access-baseline.yml` against the affected Intel node.

### An approved controller loses access after key rotation

Update the repository public-key file, review its fingerprint, commit it, and
run the access baseline while another approved controller or console session is
still available. Never rotate both controller keys simultaneously without a
tested recovery path.

## Freshness, revalidation, and supersession

### Revalidate when

- either approved controller key changes;
- an active inventory account changes;
- a node is rebuilt or replaced;
- an SSH host key changes;
- `access-baseline.yml`, `ansible-access-preflight.py`, `ansible.cfg`, or
  inventory SSH settings change;
- a new controller or operator is added;
- a new sudo policy is introduced;
- the retained Intel `pi` account is deleted or reauthorized;
- an access preflight fails;
- any node contains an unexpected key or sudoers file;
- a conflicting or superseding security record is accepted.

### Scheduled review

```text
Event-based, plus an annual controller-key and sudo-policy review.
```

### Supersession rule

When replaced, set this record to `superseded`, populate `superseded_by`,
preserve all artifacts and checksums, and identify whether the approved key set,
account mapping, sudo policy, and Intel legacy-path conclusions remain valid.

## Final completion checklist and reviewer acceptance

### Governance

- [x] Evidence ID is unique and permanent.
- [x] Schema version is 1.2.
- [x] Front matter follows the exact metadata contract and order.
- [x] Record metadata exactly mirrors front matter.
- [x] Status accurately reflects completeness.
- [x] Owner, author, operator, and reviewer are identified.
- [x] Five Ws and How agree with canonical metadata.
- [x] Scope and nonclaims are explicit.
- [x] Implementation commit is recorded or validly not-applicable.
- [x] Relationships and supersession fields are complete.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Direct observations identify source, target, time, and tool version.
- [x] Derived conclusions reference evidence IDs.
- [x] Assumptions and planned work are marked.
- [x] Failed attempts are separated from final state.
- [x] Idempotency or repeatability is proven or not-applicable.
- [x] Every not-captured value has an evidence gap.

### Safety and operations

- [x] Secrets and sensitive data are excluded or redacted.
- [x] Security limitations and residual risks are recorded.
- [x] Rollback, rebuild, and data-durability impacts are documented.
- [x] Operational health checks are documented.
- [x] Known limitations and gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Don Buddenbaum | accept | 2026-07-26 | Technical result accepted as the current seven-node controller-access baseline. |
| Reviewer | pending | pending | pending | Independent review is required before status may become accepted. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check   ~/Downloads/kalaxy3-controller-access-baseline-sage-package.zip

python3 scripts/sage/sage-publish.py publish   ~/Downloads/kalaxy3-controller-access-baseline-sage-package.zip   --push
```

Do not invent a session-specific unzip, stage, commit, rebase, or push sequence.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Working-session terminal evidence | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/terminal-evidence.md` | `ae3d7db510163838bd24c9c6ce2c31bbb1ca17ed896d9c3a997be3a2ab52b848` | public-key bodies redacted; no secrets | retain with evidence record |
| External artifact checksum inventory | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/external-artifact-checksums.sha256` | `f77ecba02e45e026742aa4c903eb99be7ab4e0ea4d53d065f2a7e0dea30fc865` | no | retain with evidence record |
| Implementation commit summary | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/implementation-commit-summary.txt` | `e333a405fa52f2bf6b48d6141bc5be4569a7251cd998616da8414bcabcc869cb` | no | retain with evidence record |
| Machine-readable validation summary | `markdown/evidence-artifacts/SAGE-K3-SECURITY-20260726-001/validation-summary.json` | `9cc529624942393c7c1f808e7120849828b5dfa1ae2ece40517bda40bd73a434` | no | retain with evidence record |

### Additional notes

The package is evidence-only because the implementation was already committed
and pushed before package generation. The publisher will resolve
`e77cb1620e1f7b1231ebd162d9506d4123520c88` to
`e77cb1620e1f7b1231ebd162d9506d4123520c88` and `2026-07-26T21:44:01-05:00` to the publication
timestamp. The publisher, not this package, creates the final record checksum,
publication manifest, and generated evidence indexes.
