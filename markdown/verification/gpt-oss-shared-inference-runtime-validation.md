---
evidence_id: SAGE-K3-INFERENCE-20260919-001
schema_version: "1.2"
title: GPT-OSS Shared Inference Storage Migration, GPU Runtime, and OpenWebUI Validation Evidence
nav_title: Validate GPT-OSS shared inference runtime
nav_section: verification
nav_order: 680
summary: Validates the governed GPT-OSS shared-inference runtime after two fail-closed controller corrections, including Longhorn-to-NFS-SSD model migration, exact model persistence, GPU execution, OpenWebUI health, and retained rollback storage.
primary_subject: GPT-OSS shared inference
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: gpt-oss-shared-inference-runtime-20260919
work_started_at: 2026-09-19T02:52:54-05:00
work_completed_at: 2026-09-19T03:10:16-05:00
evidence_collected_at: 2026-09-19T03:10:16-05:00
created_at: 2026-09-19T03:21:58-05:00
updated_at: 2026-09-19T03:32:45-05:00
valid_as_of: 2026-09-19
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - UTC
owner: Kalaxy3 architecture
author: SAGE evidence generator
operator: Kalaxy3 operator
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: not-captured
execution_host: not-captured
controller_host: not-captured
nodes:
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
  - amd64-01
  - amd64-02
node_addresses:
  - arm64-01=not-captured
  - arm64-02=not-captured
  - arm64-03=not-captured
  - arm64-04=not-captured
  - arm64-05=not-captured
  - amd64-01=not-captured
  - amd64-02=not-captured
namespaces:
  - not-captured
endpoints:
  - openwebui=192.168.2.21
components:
  - ansible-core=2.18.7
  - kubernetes.core=5.1.0
  - helm=3.21.3+g1ad6e68
  - longhorn=1.12.0
  - nfs-subdir-external-provisioner=4.0.18
  - nvidia-device-plugin=0.19.3
  - ollama=version-not-captured
  - openwebui=version-not-captured
  - qwen3=8b-Q4_K_M-digest-500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
repository: donb4iu/Kalaxy3
branch: fix/sage-lifecycle-break-glass-20260907
implementation_commit: 76e012266b9518753c9614ef91daab870e680c69
record_path: markdown/verification/gpt-oss-shared-inference-runtime-validation.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001
confidence: high
tags:
  - sage
  - gpt-oss
  - ollama
  - openwebui
  - gpu
  - nfs-ssd
  - longhorn
  - runtime-validation
  - shared-inference
relationships:
  verifies:
    - SAGE-ACTION-20260813-001
  depends_on:
    - SAGE-GPT-OSS-SHARED-INFERENCE/finalization-evidence.json
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - SAGE-GPT-OSS-SHARED-INFERENCE/runtime-localhost-become-correction.json
    - SAGE-GPT-OSS-SHARED-INFERENCE/runtime-ansible-become-variable-correction.json
  conflicts_with:
    - none
  generated_by:
    - SAGE evidence-generation input bundle
  implemented_by:
    - 76e012266b9518753c9614ef91daab870e680c69
  revalidated_by:
    - none
---

# GPT-OSS Shared Inference Storage Migration, GPU Runtime, and OpenWebUI Validation Evidence

## Executive summary

The approved GPT-OSS shared-inference runtime path is technically validated at repository candidate `76e012266b9518753c9614ef91daab870e680c69`. The session preserved two fail-closed controller corrections, migrated the Ollama model store from retained Longhorn source storage to a distinct NFS-SSD destination, proved exact `qwen3:8b` digest persistence across pod recreation and positive GPU residency during generation, deployed GPU-free OpenWebUI with a healthy external endpoint, and reran the cluster deployment guardrails successfully. Promotion and canonical integration were explicitly not performed by this runtime session.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-INFERENCE-20260919-001 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | GPT-OSS Shared Inference Storage Migration, GPU Runtime, and OpenWebUI Validation Evidence |
| **Navigation title** | Validate GPT-OSS shared inference runtime |
| **Navigation section** | verification |
| **Navigation order** | 680 |
| **Summary** | Validates the governed GPT-OSS shared-inference runtime after two fail-closed controller corrections, including Longhorn-to-NFS-SSD model migration, exact model persistence, GPU execution, OpenWebUI health, and retained rollback storage. |
| **Primary subject** | GPT-OSS shared inference |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | gpt-oss-shared-inference-runtime-20260919 |
| **Started** | 2026-09-19T02:52:54-05:00 |
| **Completed** | 2026-09-19T03:10:16-05:00 |
| **Evidence collected** | 2026-09-19T03:10:16-05:00 |
| **Record created** | 2026-09-19T03:21:58-05:00 |
| **Record updated** | 2026-09-19T03:32:45-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | UTC |
| **Valid as of** | 2026-09-19 |
| **Review due** | event-based |
| **Target record path** | markdown/verification/gpt-oss-shared-inference-runtime-validation.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | fix/sage-lifecycle-break-glass-20260907 |
| **Implementation commit** | 76e012266b9518753c9614ef91daab870e680c69 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | not-captured |
| **Execution host** | not-captured |
| **Controller host** | not-captured |
| **Nodes** | arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02 |
| **Node addresses** | arm64-01=not-captured; arm64-02=not-captured; arm64-03=not-captured; arm64-04=not-captured; arm64-05=not-captured; amd64-01=not-captured; amd64-02=not-captured |
| **Namespaces** | not-captured |
| **Endpoints** | openwebui=192.168.2.21 |
| **Components and versions** | ansible-core=2.18.7; kubernetes.core=5.1.0; helm=3.21.3+g1ad6e68; longhorn=1.12.0; nfs-subdir-external-provisioner=4.0.18; nvidia-device-plugin=0.19.3; ollama=version-not-captured; openwebui=version-not-captured; qwen3=8b-Q4_K_M-digest-500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41 |
| **Owner** | Kalaxy3 architecture |
| **Author** | SAGE evidence generator |
| **Operator** | Kalaxy3 operator |
| **Reviewer** | pending |
| **Confidence** | high |

## Navigation contract

- The formal title identifies the runtime validation scope and its storage, GPU, and UI outcomes.
- `nav_title` is a concise human-facing label for the verified shared-inference capability.
- `nav_section: verification` groups this record with technical acceptance evidence.
- `primary_subject: GPT-OSS shared inference` is the subject-index anchor.
- `[TOC]` is present for page-level navigation.

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | **Author:** SAGE evidence generator; **operator:** Kalaxy3 operator; **owner:** Kalaxy3 architecture; **reviewer:** pending; **affected users/teams:** Kalaxy3 shared-inference users and operators. |
| **What** | Validated the bounded GPT-OSS shared-inference runtime: corrected controller-side Ansible privilege behavior, migrated the Ollama model store from Longhorn to NFS-SSD while retaining the source PVC, proved exact `qwen3:8b` persistence and GPU execution, deployed GPU-free OpenWebUI, and confirmed post-runtime cluster guardrails. Promotion remained out of scope. |
| **When** | **Completed:** 2026-09-19T03:10:16-05:00; **evidence collected:** 2026-09-19T03:10:16-05:00; **local timezone:** America/Chicago; **system timestamps:** UTC; **valid as of:** 2026-09-19; **review due:** event-based. Runtime API timestamps in the machine-readable evidence are UTC while session boundaries are recorded in America/Chicago. |
| **Where** | **Environment:** homelab; **cluster:** not-captured; **execution host:** not-captured; **controller:** not-captured; **nodes:** arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; amd64-01; amd64-02; **addresses:** arm64-01=not-captured; arm64-02=not-captured; arm64-03=not-captured; arm64-04=not-captured; arm64-05=not-captured; amd64-01=not-captured; amd64-02=not-captured; **namespaces:** not-captured; **endpoints:** openwebui=192.168.2.21; **record:** markdown/verification/gpt-oss-shared-inference-runtime-validation.md. The workload node directly proven by runtime evidence is `amd64-02`. |
| **Why** | Complete the Architect-approved shared-inference objective without weakening the existing storage, model-identity, GPU, placement, health, or recovery acceptance contract. The source PVC was retained to preserve rollback, and implementation-local controller defects were corrected fail-closed before continuing. |
| **How** | Used repository-governed SAGE request execution and Git persistence for the two controller corrections, then the repository Ansible runtime path to create and bind the NFS-SSD destination, quiesce and copy the model store, redeploy Ollama, recreate its pod, generate with the exact model digest, prove positive VRAM and NVIDIA process participation, deploy OpenWebUI, rerun cluster guardrails, and capture machine-readable and terminal artifacts under `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001`. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at the evidentiary level available in the supplied bundle and agrees with metadata; uncaptured host, cluster-name, namespace, and node-address details are explicitly listed as evidence gaps.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable from repository lineage plus the preserved runtime transcript.

## Scope and boundaries

### In scope

- Repository candidate lineage through `f0cd765487c95a2d7e46d8e352139195536b40b1`, `00c0cdbcdd679d995082d92053182967b7144fcd`, and `76e012266b9518753c9614ef91daab870e680c69`.
- Two fail-closed localhost/controller privilege-escalation corrections and their governed Git persistence.
- Longhorn source retention and NFS-SSD destination migration for the Ollama model store.
- Exact `qwen3:8b` digest persistence across pod recreation.
- Positive VRAM residency and NVIDIA compute-process evidence during generation on `amd64-02`.
- OpenWebUI readiness, GPU-free resource contract, persistent application-state PVC, and HTTP 200 health.
- Post-runtime cluster deployment guardrails and SAGE evidence capture.

### Out of scope

- Promotion, merge to canonical integration, or any claim that the validated feature branch is already the canonical repository state.
- Performance, concurrency, throughput, latency, endurance, or capacity benchmarking beyond the observed runtime acceptance path.
- Destructive removal of the original Longhorn source PVC.
- Governance acceptance by a named reviewer; this record is `validated`, not `accepted`.

### Nonclaims

This record does **not** claim that runtime validation itself performed promotion, canonical integration, model benchmarking, production certification, or deletion of rollback storage.

## Final accepted state

```text
Repository candidate: 76e012266b9518753c9614ef91daab870e680c69
Ollama pod: ollama-0 on amd64-02, 1 ready replica
Model: qwen3:8b
Exact digest: 500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41
GPU evidence: positive size_vram plus NVIDIA compute-process evidence
Active Ollama PVC: ollama-models-ollama-0-nfs on nfs-ssd
Retained rollback PVC: ollama-models-ollama-0 on longhorn
OpenWebUI: 1 ready replica, GPU-free, HTTP 200 at 192.168.2.21
Promotion: not yet performed
```

| Item | Accepted result |
|---|---|
| Controller execution boundary | Repository-proven `ansible_become: false` variable override prevents inherited inventory privilege escalation on localhost controller plays. |
| Model-store migration | Copy completed from quiesced Longhorn source to Bound NFS-SSD destination; source remained retained. |
| Ollama persistence | Exact model digest remained present after pod recreation. |
| GPU execution | Generation succeeded with positive VRAM residency and NVIDIA compute-process evidence. |
| OpenWebUI | Deployment reached 1 ready replica, requested no GPU, state PVC was Bound, and `/health` returned HTTP 200. |
| Regression gate | Post-runtime cluster deployment guardrails passed. |
| Promotion | Explicitly not performed. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | The validated candidate source is commit `76e012266b9518753c9614ef91daab870e680c69`, synchronized on the feature branch with a clean repository snapshot before evidence capture. | critical | `EV-001`; `EV-002` | supported | high |
| `CLM-002` | Both controller privilege defects failed closed and were corrected without weakening the approved runtime acceptance surface. | high | `EV-002`; `EV-004` | supported | high |
| `CLM-003` | The Ollama model store migrated to Bound `nfs-ssd` claim `ollama-models-ollama-0-nfs` while the original Bound Longhorn claim `ollama-models-ollama-0` remained retained. | critical | `EV-002`; `EV-003` | supported | high |
| `CLM-004` | Exact `qwen3:8b` digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` persisted across Ollama pod recreation. | critical | `EV-002`; `EV-003` | supported | high |
| `CLM-005` | An actual generation loaded that exact model into GPU VRAM and produced NVIDIA compute-process evidence on `amd64-02`. | critical | `EV-002`; `EV-003` | supported | high |
| `CLM-006` | OpenWebUI reached one ready replica, requested no GPU, had a Bound state PVC, and returned HTTP 200 on its external health endpoint. | high | `EV-002`; `EV-003` | supported | high |
| `CLM-007` | Post-runtime cluster deployment guardrails passed after Ollama migration and OpenWebUI deployment. | high | `EV-002` | supported | high |
| `CLM-008` | Runtime success does not constitute promotion or canonical integration. | high | `EV-003`; `EV-004` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The shared-inference objective required converting a repository-qualified candidate into a live capability while preserving exact model identity, GPU execution, rollback storage, and a separate promotion boundary. The first two runtime continuations exposed controller-side Ansible privilege semantics before the workload mutation path could complete.

### Decision

Treat both localhost privilege findings as implementation-local corrections inside the already-approved objective, preserve fail-closed behavior, persist each correction through governed repository execution, and resume the same runtime path only after deterministic validation. The second correction used the repository-proven `ansible_become: false` play-variable override to defeat the higher-precedence inventory connection variable.

### Decision drivers

- Preserve the Architect-approved runtime objective and acceptance criteria.
- Avoid weakening exact model-digest and GPU-residency proof.
- Retain the Longhorn source PVC as a rollback boundary.
- Reuse repository prior art for Ansible connection-variable precedence rather than inventing a parallel workaround.
- Keep runtime validation distinct from promotion/canonical integration.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Prompt for or require controller sudo | Could bypass the immediate failure. | Gives local Kubernetes controller operations unnecessary privilege and conflicts with repository prior art. | rejected |
| Keep only play-level `become: false` | Minimal source change. | Demonstrated ineffective because inventory `ansible_become` has higher precedence. | rejected |
| Add play-variable `ansible_become: false` | Matches repository prior art and keeps controller Kubernetes operations unprivileged. | Requires a second bounded source correction and commit. | accepted |
| Abandon NFS-SSD migration and keep Longhorn active | Avoids migration time. | Fails the approved storage objective and shared-inference final-state contract. | rejected |
| Delete the old Longhorn source after copy | Frees storage immediately. | Removes the approved rollback source and increases cutover risk. | rejected |

### Tradeoffs and consequences

- The final path adds two small corrective commits before runtime validation, but preserves a clear causal lineage.
- The source Longhorn PVC consumes storage after cutover by design so rollback remains available.
- The model-store copy took a prolonged but bounded wait, favoring safety and exact copying over a faster live-copy shortcut.
- OpenWebUI retains its own Longhorn-backed application-state PVC; only the Ollama model store was migrated to NFS-SSD in this scope.

## Architecture or change description

```text
Before
  Longhorn PVC ollama-models-ollama-0
          |
          v
      Ollama pod on amd64-02 + NVIDIA GPU

Approved migration
  quiesce Ollama -> copy source read-only -> NFS-SSD destination
                                         -> retain Longhorn source

After
  NFS-SSD PVC ollama-models-ollama-0-nfs
          |
          v
      Ollama pod on amd64-02 + NVIDIA GPU
          ^
          |
      OpenWebUI service/UI
      external health: 192.168.2.21

Rollback source retained: Longhorn PVC ollama-models-ollama-0
```

### Before

Ollama was running from the Bound Longhorn source PVC with the expected `qwen3:8b` digest. The NFS-SSD destination and OpenWebUI workload were absent at the pre-mutation boundary described by the supplied generation brief and transcript lineage.

### After

Ollama ran as one ready replica on `amd64-02` using `ollama-models-ollama-0-nfs` on `nfs-ssd`; the original Longhorn source remained Bound. The exact model digest survived pod recreation, generation produced positive GPU-residency evidence, and OpenWebUI became healthy without requesting a GPU.

## Source of truth and implementation lineage

### Repository files

```text
infrastructure/k3s-homelab/manifests/ollama.yml.j2
infrastructure/k3s-homelab/manifests/openwebui.yml.j2
infrastructure/k3s-homelab/ollama-platforms.json
infrastructure/k3s-homelab/playbooks/gpu.yml
infrastructure/k3s-homelab/playbooks/migrate-ollama-models.yml
infrastructure/k3s-homelab/playbooks/ollama.yml
infrastructure/k3s-homelab/playbooks/openwebui.yml
infrastructure/k3s-homelab/playbooks/tasks/nvidia-gpu-host.yml
infrastructure/k3s-homelab/playbooks/validate-ollama.yml
markdown/evidence-artifacts/SAGE-GPT-OSS-SHARED-INFERENCE/finalization-evidence.json
markdown/evidence-artifacts/SAGE-GPT-OSS-SHARED-INFERENCE/runtime-localhost-become-correction.json
markdown/evidence-artifacts/SAGE-GPT-OSS-SHARED-INFERENCE/runtime-ansible-become-variable-correction.json
```

### Implementation commit

```text
76e012266b9518753c9614ef91daab870e680c69
Expected pre-publication repository candidate: 76e012266b9518753c9614ef91daab870e680c69
Subject: Correct GPT-OSS Ansible become variable precedence
```

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| ansible-core | 2.18.7 | controller preflight terminal evidence |
| kubernetes.core | 5.1.0 | controller preflight terminal evidence |
| Helm | 3.21.3+g1ad6e68 | repository Helm preflight terminal evidence |
| Longhorn | 1.12.0 | Helm lock reconciliation terminal evidence |
| NFS subdir external provisioner | 4.0.18 | Helm lock reconciliation terminal evidence |
| NVIDIA device plugin | 0.19.3 | Helm lock reconciliation terminal evidence |
| Ollama server | version-not-captured | explicit evidence gap |
| OpenWebUI | version-not-captured | explicit evidence gap |
| qwen3 model | 8B Q4_K_M, exact digest recorded | runtime API evidence |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Repository preflight and lock reconciliation passed; authoritative package files are checksum-bound in the SAGE input bundle. |
| Controller bootstrap | Repository-managed virtual environment, uv, Helm binary, collections, and kubeconfig were exercised by the terminal transcript. |
| Controller preflight | `controller-preflight.py --scope core`, `--scope helm`, and `--scope cluster` passed. |
| Controller host | `not-captured`; architecture type `darwin-arm64` is observed, but hostname is not present in the supplied bundle. |
| Execution host | `not-captured`; localhost controller execution and cluster node `amd64-02` are evidenced separately. |
| Machine-local authoritative state | none claimed; machine-local runtime paths are treated as capture locations, while repository commit and package artifacts preserve the evidence. |

- [x] Another supported controller can recreate the repository-managed toolchain from a clean checkout, subject to access credentials and cluster reachability.
- [x] No workstation is claimed to contain the only authoritative deployment configuration.
- [x] Manual runtime corrections in this session were reconciled into repository-owned automation before continuation.
- [x] Controller tool versions exercised by the runtime path are recorded in `components`; the controller hostname itself is an explicit evidence gap.

### Configuration excerpt

```yaml
# Effective localhost privilege boundary demonstrated by the accepted correction
hosts: localhost
become: false
connection: local
vars:
  ansible_become: false
```

## Prerequisites and assumptions

### Proven prerequisites

- Repository branch and candidate commit were synchronized before runtime continuation (`EV-001`, `EV-002`).
- Controller core, Helm, and cluster preflights passed (`EV-002`).
- All seven inventory hosts passed noninteractive SSH and privilege-escalation preflight (`EV-002`).
- The target GPU node `amd64-02`, NVIDIA RuntimeClass, final storage class, and MetalLB address pool passed runtime prechecks (`EV-002`).
- The exact expected model digest existed before the migration continuation and after migration/restart (`EV-002`, `EV-003`).

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | Retained Longhorn source data remains usable as the rollback source until intentionally retired. | Rollback could require re-copy or model re-pull. | Revalidate source PVC binding and recovery procedure before destructive retirement. |
| `ASM-002` | External OpenWebUI address `192.168.2.21` remains assigned by the configured LAN load-balancer policy. | UI endpoint can change or become unreachable. | Revalidate Service ingress and `/health` after network or MetalLB changes. |
| `ASM-003` | Exact image/application versions for Ollama and OpenWebUI remain governed by repository source even though their runtime version strings were not captured into this evidence bundle. | A later reader cannot independently identify those application versions from this record alone. | Capture explicit application/image version identities at the next runtime revalidation or promotion evidence boundary. |

The assumptions do not contradict the observed technical acceptance results, but `ASM-003` remains a traceability gap for application-version reporting.

## Implementation procedure

### Preparation

```bash
# Repository-governed preparation performed by SAGE and captured in EV-002
make cluster-guardrails
# Read-only pre-mutation checks verified source storage, exact model identity,
# target node GPU availability, and absence of the destination/UI workloads.
```

### Execution

```bash
# Functional sequence captured in the terminal artifact
# 1. Persist localhost privilege corrections through SAGE request execution.
# 2. Run playbooks/ollama.yml to create/bind NFS-SSD destination, quiesce,
#    copy, render/apply Ollama, and wait ready.
# 3. Run playbooks/validate-ollama.yml with exact qwen3:8b digest.
# 4. Run playbooks/openwebui.yml and wait for ready/external health.
# 5. Run make cluster-guardrails again.
```

### Expected change

- Ollama model data becomes active on a distinct NFS-SSD PVC.
- Original Longhorn model PVC remains present for recovery.
- Exact selected model persists after pod recreation and participates in GPU-backed generation.
- OpenWebUI becomes healthy and consumes no GPU resource.
- No promotion claim is earned solely by runtime success.

### Observed change

The copy completed after bounded polling, the destination PVC became the active Ollama claim, the source Longhorn PVC remained Bound, the exact model digest persisted after pod recreation, GPU evidence passed, OpenWebUI reached one ready replica and HTTP 200, and post-runtime cluster guardrails passed.

## Evidence items

### `EV-001` — Repository snapshot before evidence generation

- **Type:** repository evidence.
- **Collector:** SAGE evidence orchestrator.
- **Time:** 2026-09-19T03:10:16-05:00.
- **Source:** `repository-evidence.md` from the supplied SAGE generation bundle.
- **Target:** `donb4iu/Kalaxy3` branch `fix/sage-lifecycle-break-glass-20260907`.
- **Tool/version:** Git identity captured by repository evidence; exact Git version not captured.
- **Expected:** clean candidate at the final correction commit.
- **Actual:** HEAD `76e012266b9518753c9614ef91daab870e680c69`, matching remote feature branch, with no changed paths in the captured repository snapshot.
- **Confidence:** high.
- **Sensitivity:** internal repository metadata only.
- **Artifact:** `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/repository-evidence.md`, SHA-256 `b82e05b946d57f9ef4a5b7ce486c91400671cbe18c82433829f02839854194e7`.

### `EV-002` — Governed correction and runtime terminal transcript

- **Type:** direct terminal evidence.
- **Collector:** Kalaxy3 operator through the repository-controlled helper and Ansible/SAGE tooling.
- **Time:** session window ending 2026-09-19T03:10:16-05:00.
- **Source:** controller terminal output preserved by the approved runtime helper.
- **Target:** Kalaxy3 repository and homelab runtime.
- **Tool/version:** ansible-core 2.18.7, kubernetes.core 5.1.0, Helm 3.21.3+g1ad6e68; additional versions appear in the transcript.
- **Expected:** persist the bounded `ansible_become` precedence correction, complete storage migration, exact model/GPU validation, OpenWebUI deployment, and post-runtime guardrails without weakening acceptance.
- **Actual:** correction request execution and routine Git lifecycle passed; runtime migration, digest persistence, GPU participation, OpenWebUI health, and post-runtime guardrails passed.
- **Confidence:** high.
- **Sensitivity:** internal operational evidence; no secrets are intentionally included.
- **Artifact:** `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/correction-and-runtime-terminal-evidence.txt`, SHA-256 `23af6b0939c1f4dbd41709c0a69c0aa3738aff25961e18635c52acbae3e273a7`.

### `EV-003` — Machine-readable runtime evidence

- **Type:** generated runtime observation.
- **Collector:** approved runtime helper using Kubernetes and Ollama/OpenWebUI APIs.
- **Time:** 2026-09-19T03:10:16-05:00 collection boundary; embedded runtime fields include UTC timestamps.
- **Source:** post-runtime machine-readable evidence JSON.
- **Target:** Ollama, model storage, GPU runtime, and OpenWebUI.
- **Tool/version:** repository-managed Python/Kubernetes client path; exact Python runtime version 3.12.4 is captured in `EV-002`.
- **Expected:** exact digest, positive GPU residency, active NFS-SSD destination, retained Longhorn source, healthy GPU-free OpenWebUI, and no promotion claim.
- **Actual:** all listed conditions recorded with `status: pass` and `runtime_success_claimed: true`; `promotion_status` is `not-yet-performed`.
- **Confidence:** high.
- **Sensitivity:** internal runtime metadata and LAN endpoint only.
- **Artifact:** `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/runtime-evidence.json`, SHA-256 `4f267d3f7f00122f03675868104b414fdd42736a7e9a8d73cae8ff251d2c60cd`.

### `EV-004` — Original Architect request and canonical generation brief

- **Type:** authority and generation-context evidence.
- **Collector:** SAGE evidence orchestrator.
- **Time:** 2026-09-19T03:10:16-05:00.
- **Source:** canonical generation brief in the supplied input bundle.
- **Target:** evidence scope, nonclaims, failed-path lineage, and package contract.
- **Tool/version:** SAGE evidence orchestrator version identified by the authority snapshot hash.
- **Expected:** preserve the original Architect disposition and both fail-closed corrections; do not claim promotion or canonical integration from runtime success.
- **Actual:** original requester language is preserved verbatim in Appendix A and the nonclaim is enforced throughout this record.
- **Confidence:** high.
- **Sensitivity:** internal governance context.
- **Artifact:** `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/generation-brief.md`, SHA-256 `545c3fb8a1f01d0dbd863006bdf32d5c1d0fa598cc755d8e4ddaf46850fe2ffe`.

### `EV-005` — Input-bundle provenance manifest and identity

- **Type:** generated provenance evidence.
- **Collector:** this evidence generator from the exact uploaded SAGE input ZIP.
- **Time:** 2026-09-19T03:21:58-05:00.
- **Source:** SAGE input bundle manifest plus independently computed bundle SHA-256.
- **Target:** reproducibility of this evidence-generation context.
- **Tool/version:** Python standard library SHA-256/ZIP processing.
- **Expected:** every supplied authority and terminal artifact remains content-addressed.
- **Actual:** package preserves the bundle manifest and source bundle SHA-256 `98f4a6043de204512b0af56d81ebc06132ea93352722274e68e9e62aa5d6dd04`.
- **Confidence:** high.
- **Sensitivity:** repository paths and checksums only.
- **Artifacts:** `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/input-bundle-manifest.json`, SHA-256 `64023ccf329d71e03c500e4205b01612bad98334fa6ef5bb6a4e428be55f9651`; `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/source-input-bundle.sha256.txt`, SHA-256 `d208e131293369c121563d3bd6ba4183fb7bcf666e65541aadaf3938cafa8ac0`.

## Verification and acceptance criteria

| Criterion | Expected result | Observation | Evidence | Result |
|---|---|---|---|---|
| Controller privilege boundary | Local Kubernetes controller tasks do not invoke sudo. | `ansible_become: false` play-variable correction was persisted and the runtime controller prechecks passed. | `EV-002` | pass |
| Destination storage | Distinct NFS-SSD PVC becomes Bound and active for Ollama. | `ollama-models-ollama-0-nfs` is Bound, storage class `nfs-ssd`, and active for Ollama. | `EV-002`, `EV-003` | pass |
| Rollback storage | Original source PVC remains intact. | `ollama-models-ollama-0` remains Bound on Longhorn and is marked retained. | `EV-003` | pass |
| Exact model persistence | Expected digest exists before and after pod recreation. | Digest `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` remained exact after restart. | `EV-002`, `EV-003` | pass |
| GPU inference | Actual generation uses GPU. | Positive `size_vram`, Ollama GPU processor participation, and NVIDIA compute-process evidence passed. | `EV-002`, `EV-003` | pass |
| OpenWebUI | One ready replica, no GPU request, Bound state PVC, HTTP 200 health. | All four conditions were observed; external host `192.168.2.21`. | `EV-002`, `EV-003` | pass |
| Regression | Cluster guardrails still pass after runtime mutation. | Post-runtime cluster deployment guardrails passed. | `EV-002` | pass |
| Promotion separation | Runtime success does not imply promotion. | Machine-readable evidence says `promotion_status: not-yet-performed`. | `EV-003`, `EV-004` | pass |

Technical criteria passed; governance reviewer acceptance remains a separate lifecycle step, so this record is `validated` rather than `accepted`.

## Idempotency and repeatability

- The final Ollama playbook re-reads current workload state and determines whether model-store migration remains required before copying.
- The accepted source uses a distinct destination PVC and waits for binding/readiness instead of assuming immediate convergence.
- The model acceptance path recreates the pod without deleting persistent storage and rechecks the exact digest afterward.
- The original Longhorn PVC remains a recovery source rather than being deleted as part of the successful path.
- Re-running the full evidence publisher is deterministic over this package, but runtime re-execution should first reconcile the existing destination PVC and deployed OpenWebUI rather than assume the original pre-mutation state.

## Security, privacy, and evidence handling

- Controller-side Kubernetes operations were deliberately kept unprivileged; the accepted correction prevents inherited inventory `ansible_become` from invoking sudo for localhost API work.
- No credentials or secret values are intentionally recorded in the generated evidence package.
- The package includes internal LAN addressing (`192.168.2.21`) because it is material runtime evidence and the record classification is `internal`.
- The evidence package preserves checksums for every payload file and relies on the repository publisher for final token replacement, checksum creation, catalog reconciliation, and Git publication.
- Vault or other secret-source details were not required to establish the runtime claims in this session.

## Reliability, recovery, rollback, and rebuild

### Recovery

The model-store migration quiesced Ollama before the copy. The approved design retained the original Longhorn source PVC and failed closed on controller errors before crossing mutation boundaries. The successful path copied into a distinct destination and only then activated the NFS-SSD-backed workload.

### Rollback

If the NFS-SSD-backed Ollama workload becomes unusable before source retirement, the retained Longhorn PVC is the preserved recovery source. Rollback should use repository-owned workload definitions and rebind/redeploy against the retained source rather than deleting or mutating evidence to make state appear successful.

### Rebuild

A supported controller should begin from the repository candidate lineage, recreate the repository-managed Python/Ansible/Helm environment, pass controller and cluster preflights, and then use the repository playbooks. The exact model digest in this record is the acceptance identity for this runtime episode.

### Failure preservation

The session intentionally preserves the two privilege-escalation failures as causal evidence rather than hiding them behind the successful final run. The first play-level `become: false` correction was insufficient; repository prior art established that an `ansible_become: false` variable override was required because inventory connection-variable precedence is stronger.

## Operational considerations and observability

- **Ollama readiness:** one ready replica on `amd64-02` was observed after migration.
- **Model identity:** `/api/tags` and `/api/ps` evidence is represented in `runtime-evidence.json`; the exact digest is the primary identity.
- **GPU operation:** positive VRAM accounting and NVIDIA compute-process evidence should be rechecked after GPU runtime, driver, model, or workload changes.
- **Storage:** both NFS-SSD destination binding and retained Longhorn source binding are material operational signals until rollback storage is intentionally retired.
- **OpenWebUI:** deployment readiness and HTTP `/health` at its current LoadBalancer endpoint are the observed UI signals.
- **Regression:** `make cluster-guardrails` passed after deployment and remains the broad platform regression gate captured by this session.
- **Copy duration:** the migration required extended polling before success; future larger model stores should treat copy duration as an observable operational cost rather than an immediate failure signal.

## Known limitations, evidence gaps, and risks

- `not-captured`: the exact cluster name is not present in the supplied evidence-generation bundle.
- `not-captured`: controller and execution-host hostnames are not present; only `darwin-arm64` controller architecture is directly observed in the transcript.
- `not-captured`: Kubernetes namespace names are not emitted into the supplied post-runtime machine-readable artifact.
- Node IP addresses are not captured; the node identities are captured, and metadata records their addresses as `node-name=not-captured`.
- Ollama and OpenWebUI application/image version strings are not captured in the supplied bundle, although the repository candidate governs their deployment source.
- Runtime acceptance is a point-in-time observation valid as of 2026-09-19; it does not establish long-duration reliability, load capacity, concurrency, latency, throughput, or recovery-time objectives.
- The evidence bundle does not itself prove promotion, merge to `main`, or canonical integration; those are explicitly separate and currently unearned.
- OpenWebUI state remains on a Bound Longhorn PVC in the observed state; this session's NFS-SSD migration applied to the Ollama model store, not the UI state store.

## Troubleshooting

| Symptom | Meaning supported by this session | Governed response |
|---|---|---|
| Localhost Kubernetes task asks for sudo | Inventory `ansible_become` is overriding the controller privilege boundary. | Preserve the failure, verify the repository `ansible_become: false` play-variable override, rerun read-only controller prechecks, and only then continue. |
| NFS destination does not bind | Storage migration cannot safely proceed. | Fail closed; inspect the configured NFS-SSD StorageClass/provisioner and retain the Longhorn source. |
| Copy pod does not complete | Model data has not earned cutover. | Keep Ollama quiesced only within the bounded migration/recovery policy; inspect copy-pod state and do not delete the source PVC. |
| Exact digest missing after restart | Persistence or model identity is unproven. | Fail acceptance and restore/reconcile from retained source or repository-governed model acquisition. |
| `size_vram` is zero or NVIDIA process evidence absent | GPU-backed inference is unproven. | Fail runtime acceptance; inspect placement, RuntimeClass, device plugin, and container GPU visibility. |
| OpenWebUI health fails | UI capability is not validated even if Ollama is healthy. | Inspect Deployment/Service/PVC health and Ollama service connectivity without changing the model acceptance claim. |

## Freshness, revalidation, and supersession

Revalidate this record when any of the following occurs:

- the shared-inference candidate is promoted or merged to a different canonical commit;
- the Ollama or OpenWebUI image/version changes;
- the selected model or digest changes;
- the GPU node, runtime, device plugin, or driver stack changes;
- the NFS-SSD StorageClass, provisioner, destination PVC, or retained source PVC changes;
- MetalLB/service addressing changes;
- the original Longhorn rollback source is intentionally retired;
- a failure indicates that exact digest persistence, GPU participation, OpenWebUI health, or storage placement no longer holds.

A promotion or canonical-integration record should link this evidence rather than rewrite it.

## Final completion checklist and reviewer acceptance

- [x] Original requester language is preserved verbatim in the package.
- [x] Canonical schema 1.2 metadata is populated in exact order.
- [x] Record metadata table mirrors front matter.
- [x] Five Ws and How are complete and consistent with metadata.
- [x] Claims are atomic and trace to concrete evidence items.
- [x] Both fail-closed correction paths are preserved separately from the successful final runtime state.
- [x] Exact model digest, persistence, GPU participation, storage state, OpenWebUI health, and post-runtime guardrails are evidenced.
- [x] Limitations, explicit `not-captured` values, assumptions, rollback, rebuild, operations, troubleshooting, and revalidation are documented.
- [x] Promotion and canonical integration remain explicit nonclaims.
- [x] Every package artifact is declared and checksum-bound in `sage-package.json`.

Reviewer acceptance: `pending`. Technical status: `validated`.

## Git review and publication

This is an `evidence-only` package. It does not contain implementation mutations. The repository publisher must resolve `76e012266b9518753c9614ef91daab870e680c69` against the declared feature branch, inject `2026-09-19T03:32:45-05:00`, create the record checksum and publication manifest, reconcile generated evidence indexes, create the evidence commit, and push only through the standard publisher workflow.

Standard validation command:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/sage-k3-inference-20260919-001-gpt-oss-shared-inference-runtime-evidence.zip
```

Standard publication command:

```bash
python3 scripts/sage/sage-publish.py publish ~/Downloads/sage-k3-inference-20260919-001-gpt-oss-shared-inference-runtime-evidence.zip --push
```

## Appendices and raw artifacts

### Appendix A — Original requester language

```text
Original Architect disposition: "approve".

Approved objective: execute the GPT-OSS shared-inference runtime path for SAGE-ACTION-20260813-001. The first runtime attempt failed closed before cluster mutation because localhost-only Ansible controller tasks attempted sudo. SAGE persisted an implementation-local play-level become=false correction, but the next runtime continuation failed identically because the inventory-level ansible_become connection variable has higher precedence than the play keyword. Repository prior art already documented this exact behavior and the required ansible_become=false play-variable override. SAGE therefore applied and persisted that bounded second correction without changing storage/model/GPU/placement/health/recovery semantics, proved the read-only controller path without sudo, and continued the same approved runtime path. Generate governed SAGE evidence preserving both fail-closed corrections and the successful runtime observations. Do not claim promotion or canonical integration from runtime evidence alone.
```

### Appendix B — Artifact inventory

| Artifact | SHA-256 |
|---|---|
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/correction-and-runtime-terminal-evidence.txt` | `23af6b0939c1f4dbd41709c0a69c0aa3738aff25961e18635c52acbae3e273a7` |
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/runtime-evidence.json` | `4f267d3f7f00122f03675868104b414fdd42736a7e9a8d73cae8ff251d2c60cd` |
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/repository-evidence.md` | `b82e05b946d57f9ef4a5b7ce486c91400671cbe18c82433829f02839854194e7` |
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/generation-brief.md` | `545c3fb8a1f01d0dbd863006bdf32d5c1d0fa598cc755d8e4ddaf46850fe2ffe` |
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/input-bundle-manifest.json` | `64023ccf329d71e03c500e4205b01612bad98334fa6ef5bb6a4e428be55f9651` |
| `markdown/evidence-artifacts/SAGE-K3-INFERENCE-20260919-001/source-input-bundle.sha256.txt` | `d208e131293369c121563d3bd6ba4183fb7bcf666e65541aadaf3938cafa8ac0` |

### Appendix C — Source bundle identity

```text
98f4a6043de204512b0af56d81ebc06132ea93352722274e68e9e62aa5d6dd04  sage-gpt-oss-shared-inference-runtime-evidence-inputs-20260919-025254-corrected.zip
```
