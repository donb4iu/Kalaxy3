---
evidence_id: SAGE-K3-GOVERNANCE-20260726-001
schema_version: "1.2"
title: Repository-Controlled Kalaxy3 Automation Controller Machine Portability Verification
nav_title: Validate interchangeable Kalaxy3 automation controllers
nav_section: governance
nav_order: 40
summary: Verifies that clean iMac and Mac mini controllers reproduce the same repository-managed Python and Ansible environment despite different system Python versions.
primary_subject: Kalaxy3 automation controller portability
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: Repository-controlled SAGE machine portability
work_started_at: 2026-07-26T13:28:00-05:00
work_completed_at: 2026-07-26T14:51:00-05:00
evidence_collected_at: 2026-07-26T14:51:00-05:00
created_at: 2026-07-26T14:55:00-05:00
updated_at: 2026-07-26T15:10:20-05:00
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
  - donbs-imac
  - donb-mac-mini
node_addresses:
  - donb-mac-mini=192.168.2.8
namespaces:
  - not-applicable
endpoints:
  - origin=github.com/donb4iu/Kalaxy3
  - mac-mini-ssh=192.168.2.8
components:
  - uv=0.11.32
  - Python=3.12.4
  - ansible-core=2.18.7
  - ansible.posix=1.6.2
  - community.general=10.3.0
  - kubernetes.core=5.1.0
  - system-Python-Mac-mini=3.13.5
repository: donb4iu/Kalaxy3
branch: main
implementation_commit: 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
record_path: markdown/operations/kalaxy3-controller-machine-portability-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001
confidence: high
tags:
  - sage
  - governance
  - controller-portability
  - repository-authority
  - automation
  - ansible
  - python
  - uv
  - repeatability
relationships:
  verifies:
    - Kalaxy3 repository authority and automation controller portability
    - Clean controller toolchain recreation
  depends_on:
    - markdown/standards/kalaxy3-sage-evidence-record-standard.md
    - markdown/standards/kalaxy3-sage-evidence-publication-process.md
    - markdown/templates/sage-evidence-record-template.md
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - infrastructure/k3s-homelab/Makefile
    - infrastructure/k3s-homelab/scripts/controller-preflight.py
  conflicts_with:
    - none
  generated_by:
    - ChatGPT working-session evidence synthesis
    - scripts/sage/sage-publish.py
  implemented_by:
    - 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
  revalidated_by:
    - none
---
# Repository-Controlled Kalaxy3 Automation Controller Machine Portability Verification

## Executive summary

Kalaxy3 automation-controller portability was validated across `donbs-imac` and
`donb-mac-mini`. Each machine removed all repository-created controller state
and independently rebuilt the same pinned `uv`, Python, Ansible core, and
Ansible collection environment. The Mac mini began with system Python 3.13.5
but correctly installed and used repository-managed Python 3.12.4. Controller
preflight and syntax checks for phases 00 through 06 passed on both machines.
The implementation is preserved by commit
`5edd4e0223408ac6e4e1c63b52aab6ff89c990ec`. This record is `validated`; independent
review remains pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GOVERNANCE-20260726-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | Repository-Controlled Kalaxy3 Automation Controller Machine Portability Verification |
| **Navigation title** | Validate interchangeable Kalaxy3 automation controllers |
| **Navigation section** | governance |
| **Navigation order** | 40 |
| **Summary** | Verifies that clean iMac and Mac mini controllers reproduce the same repository-managed Python and Ansible environment despite different system Python versions. |
| **Primary subject** | Kalaxy3 automation controller portability |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | Repository-controlled SAGE machine portability |
| **Started** | 2026-07-26T13:28:00-05:00 |
| **Completed** | 2026-07-26T14:51:00-05:00 |
| **Evidence collected** | 2026-07-26T14:51:00-05:00 |
| **Record created** | 2026-07-26T14:55:00-05:00 |
| **Record updated** | 2026-07-26T15:10:20-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago |
| **Valid as of** | 2026-07-26 |
| **Review due** | event-based |
| **Target record path** | markdown/operations/kalaxy3-controller-machine-portability-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | main |
| **Implementation commit** | 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac and donb-mac-mini |
| **Controller host** | donbs-imac and donb-mac-mini |
| **Nodes** | donbs-imac; donb-mac-mini |
| **Node addresses** | donb-mac-mini=192.168.2.8 |
| **Namespaces** | not-applicable |
| **Endpoints** | origin=github.com/donb4iu/Kalaxy3; mac-mini-ssh=192.168.2.8 |
| **Components and versions** | uv=0.11.32; Python=3.12.4; ansible-core=2.18.7; ansible.posix=1.6.2; community.general=10.3.0; kubernetes.core=5.1.0; system-Python-Mac-mini=3.13.5 |
| **Owner** | Don Buddenbaum |
| **Author** | ChatGPT |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author ChatGPT, operator Don Buddenbaum, owner Don Buddenbaum, and reviewer pending. The affected user is the Kalaxy3 operator and any future automation controller. |
| **What** | Verified that two independent controller machines recreate the same repository-managed Kalaxy3 automation environment from disposable local state and that the Mac mini does not depend on its system Python version. |
| **When** | Completed 2026-07-26T14:51:00-05:00; evidence collected 2026-07-26T14:51:00-05:00; local timezone America/Chicago; system timestamps America/Chicago; valid as of 2026-07-26; review due event-based. |
| **Where** | Environment homelab; cluster kalaxy3; execution host donbs-imac and donb-mac-mini; controller donbs-imac and donb-mac-mini; nodes donbs-imac and donb-mac-mini; addresses donb-mac-mini=192.168.2.8; namespaces not-applicable; endpoints origin=github.com/donb4iu/Kalaxy3 and mac-mini-ssh=192.168.2.8; record markdown/operations/kalaxy3-controller-machine-portability-evidence.md. |
| **Why** | A workstation-specific Python or Ansible installation would make Kalaxy3 rebuilds and SAGE evidence depend on undocumented machine state. Repository authority requires supported controllers to be interchangeable and to reconstruct exact dependencies without manual workstation customization. |
| **How** | The repository pins `uv`, Python, Ansible core, and collections; the Makefile installs them into ignored repository-local directories; preflight verifies exact versions and managed-Python provenance; both controllers delete local generated state, run the same bootstrap, and run every phase syntax check. Raw evidence is stored under markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- Repository authority for the Kalaxy3 Ansible controller toolchain.
- Clean bootstrap on the x86_64 macOS iMac and Mac mini controllers.
- Exact `uv`, managed Python, ansible-core, and Ansible collection versions.
- Repository-local virtual environment, managed Python, tools, cache, and
  collections.
- macOS checksum compatibility for the versioned `uv` installer.
- Controller preflight and Ansible phase 00 through 06 syntax checks.
- Git implementation lineage and evidence-only SAGE publication.

### Out of scope

- Deployment or modification of Kubernetes cluster resources.
- Validation on Linux controllers, macOS ARM64, CI runners, or Windows.
- Offline bootstrap without internet access.
- Verification of the exact macOS, Git, Make, curl, or compiler versions.
- Cluster runtime behavior beyond playbook syntax.
- Independent reviewer acceptance.

### Nonclaims

This record does **not** claim:

- that every possible controller operating system is supported;
- that the bootstrap is fully offline or immune to upstream supply-chain risk;
- that successful syntax checking proves a cluster deployment will succeed;
- that machine-local credentials, SSH keys, or kubeconfig files are
  interchangeable or should be committed;
- that the commands are no-op idempotent, because the clean test intentionally
  removes and recreates disposable controller state.

## Final accepted state

```text
Source of persistent truth:            donb4iu/Kalaxy3 main
Implementation commit:                 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
Validated controllers:                 donbs-imac, donb-mac-mini
Mac mini system Python:                3.13.5
Repository-managed Python:             3.12.4
Repository-local uv:                   0.11.32
ansible-core:                          2.18.7
ansible.posix:                         1.6.2
community.general:                     10.3.0
kubernetes.core:                       5.1.0
Controller preflight:                  PASS on both controllers
Phase 00 through 06 syntax checks:     PASS on both controllers
Machine-local authoritative config:    none identified
Cluster resources changed:             none
```

| Item | Accepted result |
|---|---|
| Repository authority | Persistent dependency versions, bootstrap logic, validation, and procedures are version controlled. |
| Controller independence | Different system Python versions do not select the Kalaxy3 Python runtime. |
| Reproducibility | Both tested controllers recreated the same exact toolchain after deleting generated state. |
| Integrity check | The macOS bootstrap supplied `sha256sum` semantics through `shasum -a 256`; the final install emitted no checksum-skip warning. |
| Git lineage | Full implementation lineage resolves to `5edd4e0223408ac6e4e1c63b52aab6ff89c990ec`. |
| Runtime scope | No Kubernetes resources or persistent workload data changed during this verification. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The earlier bootstrap was still coupled to a matching controller system Python. | high | `EV-001` | supported | high |
| `CLM-002` | The iMac recreated and validated the pinned repository-managed toolchain from clean generated state. | critical | `EV-002`, `EV-004` | supported | high |
| `CLM-003` | The Mac mini recreated the same toolchain while its system Python remained 3.13.5. | critical | `EV-003`, `EV-004` | supported | high |
| `CLM-004` | Both controllers passed preflight and phase 00 through 06 syntax checks with identical pinned dependency versions. | critical | `EV-002`, `EV-003` | supported | high |
| `CLM-005` | The accepted implementation is stored in the authoritative Git repository under a full implementation SHA. | critical | `EV-004` | supported | high |
| `CLM-006` | The final macOS bootstrap performed checksum verification rather than silently skipping it. | high | `EV-002`, `EV-004` | supported | high |
| `CLM-007` | No cluster runtime state was changed by the portability test. | normal | `EV-002`, `EV-003` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The iMac and Mac mini had different system Python environments. The original
bootstrap correctly detected an incompatible Python on the Mac mini but stopped
without creating the required environment. That meant a future operator would
still need undocumented, machine-specific preparation before repository
automation could run.

### Decision

Make the repository provision and verify its own pinned Python and Ansible
controller environment. Treat controller-local environments and caches as
disposable. Treat Git as the sole authoritative source for persistent
dependency versions, bootstrap logic, operational procedures, and evidence.

### Decision drivers

- Rebuildability from a clean checkout.
- Identical behavior across supported controller machines.
- Exact dependency selection rather than PATH-dependent selection.
- No workstation-specific persistent configuration as the sole source.
- Explicit checksum verification on macOS.
- Clear SAGE lineage between implementation and verification evidence.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Manually install Python 3.12.4 on each controller | Familiar and quick for one machine | Creates undocumented workstation state and does not prove future portability | rejected |
| Continue using whichever `python3` appears on PATH | Minimal bootstrap code | Different machines can select incompatible runtimes and packages | rejected |
| Require Homebrew or another global package manager | Centralizes local tools | Couples Kalaxy3 to machine-global package state and package-manager configuration | rejected |
| Pin repository-local `uv` and install managed Python | Exact, rebuildable, isolated, and portable across the tested controllers | Requires an initial internet download and upstream availability | accepted |
| Commit generated environments into Git | Avoids repeated downloads | Large, platform-specific, nonreviewable, and unsafe repository state | rejected |

### Tradeoffs and consequences

- First bootstrap needs internet access and takes longer than reusing an
  existing global environment.
- Generated `.tools`, `.python`, `.uv-cache`, `.venv`, and `.ansible`
  directories consume local disk but remain disposable and ignored.
- The bootstrap depends on a versioned upstream `uv` installer and its checksum
  mechanism.
- `make install` intentionally recreates `.venv`; it proves repeatability, not a
  no-change Ansible-style idempotency recap.
- Local credentials and access material remain machine-local by design, while
  all persistent nonsecret configuration stays in Git.

## Architecture or change description

```text
donb4iu/Kalaxy3 main
  |
  +-- .python-version --------------------------> 3.12.4
  +-- .uv-version ------------------------------> 0.11.32
  +-- requirements.txt -------------------------> ansible-core 2.18.7
  +-- requirements.yml -------------------------> exact collections
  +-- Makefile
  |     |
  |     +-- repository-local uv installer
  |     +-- macOS sha256sum compatibility wrapper
  |     +-- managed Python under .python
  |     +-- virtual environment under .venv
  |     +-- collections under .ansible/collections
  |
  +-- scripts/controller-preflight.py ----------> exact-version checks
        |
        +--> donbs-imac: clean bootstrap and syntax PASS
        +--> donb-mac-mini: clean bootstrap and syntax PASS
```

### Before

The bootstrap used the controller's `python3`. The Mac mini exposed the
remaining coupling by reporting Python 3.13.5 and refusing to create the
repository-required Python 3.12.4 environment.

### After

The same repository command installs `uv 0.11.32`, provisions managed Python
3.12.4, creates the virtual environment, installs exact Ansible dependencies,
and validates provenance and versions on both tested controllers.

## Source of truth and implementation lineage

### Repository files

```text
.gitignore
infrastructure/k3s-homelab/.python-version
infrastructure/k3s-homelab/.uv-version
infrastructure/k3s-homelab/Makefile
infrastructure/k3s-homelab/ansible.cfg
infrastructure/k3s-homelab/requirements.txt
infrastructure/k3s-homelab/requirements.yml
infrastructure/k3s-homelab/scripts/controller-preflight.py
markdown/standards/kalaxy3-sage-evidence-record-standard.md
markdown/standards/sage-evidence-metadata-contract-v1.2.json
markdown/standards/kalaxy3-sage-evidence-publication-process.md
markdown/templates/sage-evidence-record-template.md
scripts/sage/sage-publish.py
scripts/sage/sage-index.py
```

### Implementation commit

```text
5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
Provision repository-managed Python controllers
```

### Versioned dependencies

| Component/tool | Version | Repository source |
|---|---:|---|
| `uv` | `0.11.32` | `infrastructure/k3s-homelab/.uv-version` |
| Python | `3.12.4` | `infrastructure/k3s-homelab/.python-version` |
| ansible-core | `2.18.7` | `infrastructure/k3s-homelab/requirements.txt` |
| ansible.posix | `1.6.2` | `infrastructure/k3s-homelab/requirements.yml` |
| community.general | `10.3.0` | `infrastructure/k3s-homelab/requirements.yml` |
| kubernetes.core | `5.1.0` | `infrastructure/k3s-homelab/requirements.yml` |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | `.python-version`, `.uv-version`, `requirements.txt`, and `requirements.yml` |
| Controller bootstrap | `make install` |
| Controller preflight | `make controller-preflight` returned PASS on both machines |
| Controller hosts | `donbs-imac`, `donb-mac-mini` |
| Execution hosts | `donbs-imac`, `donb-mac-mini` |
| Machine-local authoritative state | None identified; generated environments and caches are disposable |

- [x] Another supported controller recreated the toolchain from clean generated state.
- [x] No workstation contains the only authoritative deployment configuration.
- [x] Manual controller fixes were reconciled into repository-owned automation.
- [x] Controller and execution-host dependency versions are recorded in `components`.

### Configuration excerpt

```makefile
UV_VERSION := $(shell cat .uv-version)
PYTHON_VERSION := $(shell cat .python-version)
PYTHON_INSTALL_DIR := $(abspath .python)
UV_CACHE_DIR := $(abspath .uv-cache)

controller-bootstrap: controller-uv
	UV_MANAGED_PYTHON=1 \
	UV_PYTHON_INSTALL_DIR="$(PYTHON_INSTALL_DIR)" \
	UV_CACHE_DIR="$(UV_CACHE_DIR)" \
	$(UV) python install "$(PYTHON_VERSION)"
```

## Prerequisites and assumptions

### Proven prerequisites

- Git access to `origin=github.com/donb4iu/Kalaxy3` was demonstrated by pull
  and push output in `EV-002`, `EV-003`, and `EV-004`.
- The tested controllers had `curl`, `sh`, `make`, Git, and macOS `shasum`
  available because the clean bootstrap completed.
- The Mac mini was reachable through `mac-mini-ssh=192.168.2.8`.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The pinned upstream `uv` installer remains available. | A first clean bootstrap cannot download `uv`. | Revalidate on every pinned-version change; later add an approved mirror or cached artifact if offline recovery is required. |
| `ASM-002` | The installer checksum verification remains valid for the selected release. | A corrupt or substituted download might not be detected. | Preserve the no-skip negative check and revalidate after installer changes. |
| `ASM-003` | x86_64 macOS remains a supported controller platform. | Future OS or architecture changes may break package or Python installation. | Run the same clean portability test on every new controller platform. |

These assumptions do not contradict the tested two-machine result.

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
git pull --ff-only origin main
cd infrastructure/k3s-homelab
rm -rf .venv .ansible .tools .python .uv-cache
```

### Execution

```bash
make install &&
make controller-preflight &&
make syntax
```

### Expected change

The repository should install local `uv 0.11.32`, install managed Python
3.12.4, create `.venv`, install exact Ansible dependencies and repository-local
collections, pass controller preflight, and pass syntax checks for phases 00
through 06 without requiring a global Python 3.12.4 installation.

### Observed change

`EV-002` and `EV-003` show the expected result on the iMac and Mac mini. The
Mac mini's global Python remained 3.13.5 while the repository-managed runtime
was 3.12.4.

### Failed or superseded paths

- The pre-portability bootstrap stopped when system Python did not exactly match
  3.12.4 (`EV-001`).
- The first preflight parser treated `uv --version` build metadata as part of
  the semantic version and was corrected to select the version token.
- The initial macOS installer run skipped checksum verification because
  `sha256sum` was absent. The accepted implementation supplies compatible
  `sha256sum` behavior using `shasum -a 256`.
- Intermediate Makefile-edit commands produced malformed formatting and were
  repaired and revalidated before commit. Those failed forms were never
  committed as the accepted implementation.

## Evidence items

### `EV-001` — Initial Mac mini system-Python coupling failure

| Field | Value |
|---|---|
| Classification | `negative-evidence` |
| Supports or contradicts | `CLM-001` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T14:24:00-05:00 |
| Execution source | donb-mac-mini |
| Target | Kalaxy3 controller bootstrap |
| Tool and version | system-Python=3.13.5; Make=version-not-captured |
| Expected result | A clean controller can create the required environment |
| Actual result | fail |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 --version
make install
make controller-preflight
make syntax
```

**Observed result**

```text
Python 3.13.5
Python 3.13.5 found; repository requires 3.12.4
make: *** [controller-bootstrap] Error 1
```

**Interpretation**

The negative result proves that the earlier bootstrap validated the mismatch
but did not yet remove workstation preparation as a prerequisite.

### `EV-002` — Clean iMac bootstrap validation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`, `CLM-004`, `CLM-006`, `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T14:46:00-05:00 |
| Execution source | donbs-imac |
| Target | Repository-managed controller environment |
| Tool and version | uv=0.11.32; Python=3.12.4; ansible-core=2.18.7 |
| Expected result | Clean bootstrap, preflight PASS, and phase 00 through 06 syntax PASS |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
rm -rf .venv .ansible .tools .python .uv-cache
make install &&
make controller-preflight &&
make syntax
```

**Observed result**

```text
PASS uv 0.11.32
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS ansible.posix 1.6.2
PASS community.general 10.3.0
PASS kubernetes.core 5.1.0
Kalaxy3 controller preflight: PASS
phase-00 through phase-06 syntax checks: PASS
checksum-skip warning: absent
```

**Interpretation**

The iMac recreated the complete accepted controller environment without relying
on previously generated repository-local state.

### `EV-003` — Clean Mac mini cross-machine reproduction

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003`, `CLM-004`, `CLM-007` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-26T14:51:00-05:00 |
| Execution source | donb-mac-mini |
| Target | Repository-managed controller environment |
| Tool and version | system-Python=3.13.5; uv=0.11.32; managed-Python=3.12.4; ansible-core=2.18.7 |
| Expected result | Reproduce the same managed environment despite a different system Python |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 --version
rm -rf .venv .ansible .tools .python .uv-cache
make install &&
make controller-preflight &&
make syntax
```

**Observed result**

```text
System Python: Python 3.13.5
Installed Python 3.12.4
PASS uv 0.11.32
PASS Python 3.12.4
PASS ansible-core 2.18.7
PASS ansible.posix 1.6.2
PASS community.general 10.3.0
PASS kubernetes.core 5.1.0
Kalaxy3 controller preflight: PASS
phase-00 through phase-06 syntax checks: PASS
```

**Interpretation**

This is the direct portability proof: two controllers with different
machine-level conditions selected the same repository-controlled runtime and
dependency set.

### `EV-004` — Authoritative implementation commit

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-002`, `CLM-003`, `CLM-005`, `CLM-006` |
| Collected by | ChatGPT |
| Collected at | 2026-07-26T14:55:00-05:00 |
| Execution source | donb4iu/Kalaxy3 Git history |
| Target | Implementation commit and declared source files |
| Tool and version | Git=version-not-captured |
| Expected result | Full implementation SHA with the accepted repository changes |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/implementation-commit-summary.txt` |

**Command, query, source, or observation**

```bash
git show --stat --oneline 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
```

**Observed result**

```text
5edd4e0223408ac6e4e1c63b52aab6ff89c990ec Provision repository-managed Python controllers
4 files changed, 81 insertions(+), 11 deletions(-)
```

**Interpretation**

The commit records the accepted bootstrap, preflight, version pin, ignored
generated-state paths, and macOS checksum compatibility. It does not by itself
prove runtime success; `EV-002` and `EV-003` provide that direct evidence.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | A clean iMac controller recreates the exact toolchain | `EV-002` | pinned versions and all checks PASS | observed exactly | pass |
| `AC-002` | A clean Mac mini controller recreates the same toolchain with system Python 3.13.5 | `EV-003` | managed Python 3.12.4 and all checks PASS | observed exactly | pass |
| `AC-003` | Dependency versions agree on both controllers | `EV-002`, `EV-003` | exact matching versions | all six pinned components agree | pass |
| `AC-004` | Every phase 00 through 06 playbook parses | `EV-002`, `EV-003` | seven syntax checks PASS | seven syntax checks PASS on both | pass |
| `AC-005` | macOS checksum verification is not skipped | `EV-002`, `EV-004` | no checksum-skip warning | warning absent in final clean run | pass |
| `AC-006` | Implementation has full Git lineage | `EV-004` | full SHA and declared files | full SHA resolved at publication | pass |
| `AC-007` | Test does not modify cluster state | `EV-002`, `EV-003` | controller-local and Git operations only | no deployment playbook executed | pass |

### Functional verification

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
make controller-preflight &&
make syntax
```

Observed:

```text
Kalaxy3 controller preflight: PASS
phase-00 through phase-06 syntax checks: PASS
```

### Negative verification

```bash
rm -rf .tools .python .uv-cache .venv .ansible
make install 2>&1 | grep -F 'skipping sha256 checksum verification'
```

Observed:

```text
No matching checksum-skip warning in the accepted clean iMac bootstrap.
```

## Idempotency and repeatability

### First accepted run

The iMac deleted every generated controller directory and recreated the pinned
environment successfully (`EV-002`).

### Independent clean reproduction

The Mac mini performed the same deletion and bootstrap independently while its
system Python was 3.13.5, then produced the same version and syntax results
(`EV-003`).

### Interpretation

Cross-machine clean repeatability is proven for the two tested x86_64 macOS
controllers. `make install` intentionally recreates `.venv`, so this record
does not claim a `changed=0` no-op rerun. The required steady state is the
validated dependency set and executable behavior, not preservation of generated
files.

## Security, privacy, and evidence handling

### Security controls

- The versioned installer is fetched over TLS.
- The bootstrap ensures checksum verification is available on macOS through a
  repository-local `sha256sum` compatibility wrapper.
- Repository-generated executables, Python, caches, virtual environments, and
  collections are ignored rather than committed.
- Credentials, private keys, kubeconfig material, tokens, and secret values
  remain outside this evidence package.
- The publisher performs its own secret-pattern scan before publication.

### Sensitive material excluded

- SSH private keys and public-key contents.
- Kubeconfig and Ansible Vault content.
- Authentication tokens, passwords, and environment secrets.
- Full user home-directory listings and unrelated shell history.
- The obsolete, unrelated Kubecost research PDF.

### Redactions and omissions

- Long dependency-download logs and Git fast-forward file lists were trimmed.
- User home paths are abbreviated in the terminal artifact where they add no
  evidentiary value.
- No material pass, failure, version, host, timestamp, or commit result was
  omitted.

### Residual security risk

- Initial bootstrap trusts the pinned upstream release location, TLS, and the
  installer's checksum metadata. Offline recovery or a repository-controlled
  mirror has not been implemented.
- Repository-local installed binaries remain executable supply-chain inputs and
  must be recreated after a pin or trust-policy change.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Upstream `uv` release unavailable | `controller-uv` download fails | A clean controller cannot bootstrap | Restore connectivity, use an approved mirror, or temporarily retain a previously verified local tool directory |
| Checksum command unavailable | Bootstrap reports neither `sha256sum` nor `shasum` | Installer does not proceed | Install a trusted checksum utility or add a reviewed platform-specific compatibility path |
| Wrong managed Python selected | Preflight reports Python mismatch or non-repository base prefix | Automation cannot be trusted as portable | Remove generated directories and rerun `make install` |
| Dependency drift | Preflight reports ansible-core or collection mismatch | Different controllers may behave differently | Restore repository pins and rebuild generated state |
| Upstream package no longer builds | `uv pip install` fails | New clean controller cannot complete | Revalidate pins, update them in a controlled implementation commit, and supersede this evidence |
| Implementation regression | One controller fails clean bootstrap or syntax | Portability claim no longer holds | Revert or repair the implementation, then publish new evidence |

### Rollback

```bash
cd ~/dvlp/Kalaxy3
git revert 5edd4e0223408ac6e4e1c63b52aab6ff89c990ec
cd infrastructure/k3s-homelab
rm -rf .venv .ansible .tools .python .uv-cache
```

Rollback restores the earlier system-Python-dependent behavior and therefore
also invalidates the portability claim.

### Rebuild procedure

1. Clone or fast-forward `donb4iu/Kalaxy3` branch `main`.
2. Enter `infrastructure/k3s-homelab`.
3. Remove `.venv`, `.ansible`, `.tools`, `.python`, and `.uv-cache`.
4. Run `make install`.
5. Run `make controller-preflight`.
6. Run `make syntax`.
7. Confirm the exact versions and phase 00 through 06 PASS results recorded
   above.

### Data durability and backup impact

No Kubernetes workload data, persistent volume, database, cluster secret, or
etcd state was modified. The generated controller directories are disposable
and require no backup. The Git repository and published SAGE evidence are the
durable records.

## Operational considerations and observability

### Health signals

- `make controller-preflight` returns zero and prints each exact dependency.
- `make syntax` returns zero and lists phases 00 through 06.
- `.tools/uv --version` reports 0.11.32.
- `.venv/bin/python` reports 3.12.4 with a base prefix under `.python`.
- `ansible-config dump --only-changed` shows repository-local collection paths.
- `git status --short` identifies accidental persistent local changes.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3/infrastructure/k3s-homelab
make controller-preflight &&
make syntax
```

For a new controller or after a source-of-truth change, perform the complete
clean rebuild procedure instead of relying only on existing generated state.

### Capacity, performance, cost, and sustainability

- **Capacity:** Adds local copies of `uv`, Python, packages, collections, and
  cache data on each controller.
- **Performance:** First bootstrap requires downloads and package preparation;
  subsequent nonclean operations can reuse cached data.
- **Cost:** No paid service or cluster-resource cost was introduced; normal
  network and storage use applies.
- **Sustainability/power:** Negligible operational power impact; repeated clean
  rebuilds consume transient compute and network resources.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | Linux, macOS ARM64, CI, and other future controllers were not tested. | Portability beyond the two x86_64 macOS controllers remains unproven. | Don Buddenbaum | Before declaring another platform supported |
| `GAP-002` | evidence-gap | Exact macOS, Git, Make, curl, compiler, and shell versions were not preserved. | Root-cause precision may be lower for a future platform regression. | Don Buddenbaum | On the next controller portability revalidation |
| `RISK-001` | risk | A first clean bootstrap requires upstream network availability. | Offline rebuild is not presently guaranteed. | Don Buddenbaum | When offline disaster recovery becomes a requirement |
| `RISK-002` | risk | Upstream installer and package availability can change despite version pins. | A future clean bootstrap can fail even when Git is unchanged. | Don Buddenbaum | On any upstream failure or pin update |
| `DEBT-001` | technical-debt | The portability test is operator-run rather than a CI matrix. | Regressions are found during manual revalidation instead of automatically. | Don Buddenbaum | When Kalaxy3 CI is introduced |
| `LIMIT-001` | limitation | Syntax checks do not execute Kubernetes changes. | This record verifies controller reproducibility, not runtime deployment behavior. | Don Buddenbaum | Revalidate deployment separately |

## Troubleshooting

### System Python mismatch appears again

**Meaning**

A legacy bootstrap path is being used, or the repository-managed Python
installation did not complete.

**Checks**

```bash
git log -1 --oneline
grep -nE 'UV_VERSION|PYTHON_VERSION|controller-bootstrap' Makefile
.venv/bin/python scripts/controller-preflight.py
```

**Recovery**

```bash
git pull --ff-only origin main
rm -rf .venv .ansible .tools .python .uv-cache
make install
```

### `uv mismatch` includes build metadata

**Meaning**

The preflight version parser may be comparing the complete `uv --version`
output instead of its semantic-version token.

**Checks**

```bash
.tools/uv --version
grep -nA18 '^def validate_uv' scripts/controller-preflight.py
```

**Recovery**

Restore `scripts/controller-preflight.py` from the authoritative branch and
rerun the clean rebuild.

### Checksum verification is skipped

**Meaning**

The installer did not find `sha256sum`, and the macOS compatibility wrapper was
not created or not placed first in the installer PATH.

**Checks**

```bash
sed -n '/^controller-uv:/,/^controller-bootstrap:/p' Makefile
ls -l .tools/sha256sum
```

**Recovery**

Restore the committed Makefile, remove `.tools`, and rerun `make install`.

### Collections resolve outside the repository

**Meaning**

The controller is scanning machine-global collection paths.

**Checks**

```bash
.venv/bin/ansible-config dump --only-changed |
grep -E 'COLLECTIONS_PATH|COLLECTIONS_SCAN_SYS_PATH'
```

**Recovery**

Restore `ansible.cfg`, delete `.ansible` and `.venv`, and rerun the bootstrap.

## Freshness, revalidation, and supersession

### Revalidate when

- `.python-version`, `.uv-version`, `requirements.txt`, or `requirements.yml`
  changes;
- the Makefile, preflight script, or `ansible.cfg` changes;
- a new controller OS or CPU architecture is introduced;
- macOS removes or changes `shasum`;
- the `uv` installer or download/checksum behavior changes;
- a clean bootstrap or any phase syntax check fails;
- the repository publication process or metadata contract changes;
- a conflicting portability record is validated.

### Scheduled review

```text
Event-based, with an annual controller rebuild test if no triggering change
occurs sooner.
```

### Supersession rule

When a newer portability implementation or broader controller matrix is
validated, set this record to `superseded`, populate `superseded_by`, retain the
evidence ID and artifacts, and state whether the original two-controller claims
remain valid.

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
| Owner | Don Buddenbaum | accept | 2026-07-26 | Technical result accepted as the current two-controller baseline. |
| Reviewer | pending | pending | pending | Independent review is required before status may become accepted. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-controller-machine-portability-sage-package.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-controller-machine-portability-sage-package.zip \
  --push
```

Do not invent a session-specific unzip, stage, commit, rebase, or push sequence.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Working-session terminal evidence | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/terminal-evidence.md` | `3de17314b9fa9134349e1c1fbfd09d610b3d38a18355bbfaa2eef80992e2a144` | no | retain with evidence record |
| Implementation commit summary | `markdown/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-001/implementation-commit-summary.txt` | `716ecba4b8ac7de0bc4544f507cf641939428bb7c6d317b7fa5899bcdde45353` | no | retain with evidence record |

### Additional notes

The obsolete, untracked Kubecost-on-AWS research PDF was intentionally removed
from the Mac mini checkout because the operator stated that later Kalaxy3
iterations had superseded its analysis. Its removal did not create a Git change
and is not part of the implementation commit.
