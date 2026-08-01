---
evidence_id: SAGE-K3-GUARDRAIL-20260731-002
schema_version: "1.2"
title: PR #5 CI Portability Repair and Source-Only Guardrail Validation Evidence
nav_title: Validate PR #5 source-only guardrails
nav_section: governance
nav_order: 420
summary: Documents the three post-publication CI repairs that separated repository authority from runtime prerequisites and made PR #5 source-only guardrails pass without weakening operator-runtime validation.
primary_subject: SAGE CI portability
project: Kalaxy3
record_type: verification
status: validated
classification: internal
work_session: PR #5 CI portability and test-tier repair
work_started_at: not-captured
work_completed_at: 2026-07-31T23:17:00-05:00
evidence_collected_at: 2026-07-31T23:21:49-05:00
created_at: 2026-07-31T23:24:00-05:00
updated_at: 2026-07-31T23:30:09-05:00
valid_as_of: 2026-07-31
review_due: event-based
local_timezone: America/Chicago
system_timestamp_timezones:
  - America/Chicago
  - UTC
owner: Kalaxy3 architecture
author: OpenAI GPT-5.6 Thinking
operator: Don Buddenbaum
reviewer: pending
environment: homelab
system: Kalaxy3
cluster: kalaxy3
execution_host: donbs-imac-and-github-actions
controller_host: donbs-imac
nodes:
  - amd64-01
  - amd64-02
  - arm64-01
  - arm64-02
  - arm64-03
  - arm64-04
  - arm64-05
node_addresses:
  - not-applicable
namespaces:
  - observability
endpoints:
  - github-pr=PR-5
  - loki-api=service/loki-gateway
components:
  - SAGE-schema=1.2
  - SAGE-CI-portability=818fa5860c028ffd721c982861032adf1e9af1e0
  - GitHub-Actions=version-not-captured
  - Python=version-not-captured
  - PyYAML=operator-runtime-only
  - Loki=18.5.4
  - fluent-bit-collector=1.0.9
  - Longhorn=version-not-captured
repository: donb4iu/Kalaxy3
branch: feature/actionable-guardrail-recovery
implementation_commit: 818fa5860c028ffd721c982861032adf1e9af1e0
record_path: markdown/governance/kalaxy3-actionable-guardrail-ci-portability-evidence.md
artifact_root: markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002
confidence: high
tags:
  - sage
  - guardrails
  - continuous-integration
  - source-only
  - runtime-prerequisites
  - yaml
  - centralized-logging
  - evidence
relationships:
  verifies:
    - PR #5 source-only guardrail portability
    - Supplemental validation for SAGE-K3-GUARDRAIL-20260731-001
  depends_on:
    - SAGE-K3-GUARDRAIL-20260731-001
  supersedes:
    - none
  superseded_by:
    - none
  related_to:
    - PR #5 Add actionable SAGE guardrail recovery and runtime validation
    - c50270d740fa3bcca976b6ed20db07cfed545638
  conflicts_with:
    - none
  generated_by:
    - scripts/sage/sage-evidence-orchestrator.py
    - scripts/sage/sage-publish.py
    - GitHub Actions
  implemented_by:
    - 818fa5860c028ffd721c982861032adf1e9af1e0
  revalidated_by:
    - GitHub PR #5 checks at 818fa5860c028ffd721c982861032adf1e9af1e0
---

# PR #5 CI Portability Repair and Source-Only Guardrail Validation Evidence

## Executive summary

PR #5 now passes its repository SAGE and MkDocs checks after three CI-only
failures exposed a common architectural defect: source-only validation had
been coupled to generated operator-runtime prerequisites. Kalaxy3 now treats
repository authority, source-only contracts, and operator-runtime validation as
separate but complementary layers. The final branch at
`818fa5860c028ffd721c982861032adf1e9af1e0` passed source-only tests without `.venv`, PyYAML, site
packages, cluster credentials, or live APIs; retained repository-managed
operator tests and active Loki validation; and produced green GitHub checks with
no base-branch conflict. This supplemental record is validated and linked to
`SAGE-K3-GUARDRAIL-20260731-001`; governance review remains pending.

[TOC]

## Record metadata

| Field | Value |
|---|---|
| **Evidence ID** | SAGE-K3-GUARDRAIL-20260731-002 |
| **Schema version** | 1.2 |
| **Project** | Kalaxy3 |
| **Title** | PR #5 CI Portability Repair and Source-Only Guardrail Validation Evidence |
| **Navigation title** | Validate PR #5 source-only guardrails |
| **Navigation section** | governance |
| **Navigation order** | 420 |
| **Summary** | Documents the three post-publication CI repairs that separated repository authority from runtime prerequisites and made PR #5 source-only guardrails pass without weakening operator-runtime validation. |
| **Primary subject** | SAGE CI portability |
| **Record type** | verification |
| **Status** | validated |
| **Classification** | internal |
| **Work session** | PR #5 CI portability and test-tier repair |
| **Started** | not-captured |
| **Completed** | 2026-07-31T23:17:00-05:00 |
| **Evidence collected** | 2026-07-31T23:21:49-05:00 |
| **Record created** | 2026-07-31T23:24:00-05:00 |
| **Record updated** | 2026-07-31T23:30:09-05:00 |
| **Local timezone** | America/Chicago |
| **System timestamp timezone(s)** | America/Chicago; UTC |
| **Valid as of** | 2026-07-31 |
| **Review due** | event-based |
| **Target record path** | markdown/governance/kalaxy3-actionable-guardrail-ci-portability-evidence.md |
| **Artifact root** | markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002 |
| **Repository** | donb4iu/Kalaxy3 |
| **Branch** | feature/actionable-guardrail-recovery |
| **Implementation commit** | 818fa5860c028ffd721c982861032adf1e9af1e0 |
| **Environment** | homelab |
| **System** | Kalaxy3 |
| **Cluster** | kalaxy3 |
| **Execution host** | donbs-imac-and-github-actions |
| **Controller host** | donbs-imac |
| **Nodes** | amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05 |
| **Node addresses** | not-applicable |
| **Namespaces** | observability |
| **Endpoints** | github-pr=PR-5; loki-api=service/loki-gateway |
| **Components and versions** | SAGE-schema=1.2; SAGE-CI-portability=818fa5860c028ffd721c982861032adf1e9af1e0; GitHub-Actions=version-not-captured; Python=version-not-captured; PyYAML=operator-runtime-only; Loki=18.5.4; fluent-bit-collector=1.0.9; Longhorn=version-not-captured |
| **Owner** | Kalaxy3 architecture |
| **Author** | OpenAI GPT-5.6 Thinking |
| **Operator** | Don Buddenbaum |
| **Reviewer** | pending |
| **Confidence** | high |

## Five Ws and How

| Requirement | Answer |
|---|---|
| **Who** | Author OpenAI GPT-5.6 Thinking; operator Don Buddenbaum; owner Kalaxy3 architecture; reviewer pending; affected users are Kalaxy3 operators, maintainers, and PR reviewers. |
| **What** | Three post-publication CI repairs made PR #5 source-only guardrails portable while preserving operator-runtime and live-cluster validation. |
| **When** | Completed 2026-07-31T23:17:00-05:00; evidence collected 2026-07-31T23:21:49-05:00; local timezone America/Chicago; system timestamps America/Chicago; UTC; valid as of 2026-07-31; review due event-based. The exact work start was not captured. |
| **Where** | Environment homelab; cluster kalaxy3; execution host donbs-imac-and-github-actions; controller donbs-imac; nodes amd64-01; amd64-02; arm64-01; arm64-02; arm64-03; arm64-04; arm64-05; addresses not-applicable; namespace observability; endpoints github-pr=PR-5; loki-api=service/loki-gateway; record markdown/governance/kalaxy3-actionable-guardrail-ci-portability-evidence.md. |
| **Why** | GitHub Actions must validate repository contracts from a clean checkout without requiring generated virtual environments, optional parsing dependencies, cluster credentials, or live services, while operator closeout must still prove those runtime paths. |
| **How** | The actionable-failure model now distinguishes source authority from runtime prerequisites; source-only tests run with `python3 -S`; optional PyYAML loading is lazy; operator tests continue through the repository `.venv`; live logging validation and GitHub checks were rerun. |

### Five-W completeness gate

- [x] Who is complete and agrees with metadata.
- [x] What is complete.
- [x] When is complete, uses canonical timestamps, and includes timezone context.
- [x] Where is complete at repository and runtime levels and agrees with metadata.
- [x] Why includes rationale, alternatives, and tradeoffs.
- [x] How is reproducible and verifiable.

## Scope and boundaries

### In scope

- The three CI failures after publication of the initial actionable-guardrail
  evidence record.
- Portable classification of repository authority versus generated runtime
  prerequisites.
- Source-only and operator-runtime test tiers for centralized logging and YAML
  metadata.
- Lazy optional dependency loading and actionable missing-PyYAML behavior.
- Local source-only, operator-runtime, live-cluster, repository guardrail, and
  GitHub PR validation.
- Supplemental lineage to `SAGE-K3-GUARDRAIL-20260731-001`.

### Out of scope

- Rewriting the original evidence record or changing its historical
  implementation boundary.
- Removing `.venv`, PyYAML, kubeconfig, or live cluster access from operator
  validation.
- Proving every future GitHub runner image or every optional dependency.
- Merging PR #5; this record is prepared before merge.
- Classifying the remaining actionable-failure audit candidates.

### Nonclaims

This record does **not** claim that source-only tests replace live validation,
that PyYAML is unnecessary, that all GitHub workflows are portable, or that the
PR has already merged.

## Final accepted state

```text
PR #5 source-only guardrails pass from a clean checkout without generated
operator dependencies, while repository-managed operator tests and live
centralized-logging validation remain required and pass separately.
```

| Item | Accepted result |
|---|---|
| Recovery path authority | `required_paths` contains repository-relative source authority, not `.venv` executables or other generated paths. |
| Centralized-logging CI test | Imports and tests pure validator contracts with `python3 -S`, without PyYAML, cluster credentials, or `.venv`. |
| Centralized-logging operator test | Runs through the repository `.venv` and continues to parse inventory and exercise runtime logic. |
| YAML metadata CI test | Validates types, opaque-value behavior, and actionable missing-PyYAML guidance without parsing YAML. |
| YAML metadata operator test | Parses tagged YAML through the repository `.venv` and keeps `!vault` payloads opaque. |
| Active logging validation | Still passes with seven collectors, Loki and gateway ready, Bound `40Gi` Longhorn storage, and all-node log coverage. |
| GitHub PR #5 | Two checks passed, one documentation-only check skipped, and GitHub reported no conflicts with `main`. |

## Claims and evidence matrix

| Claim ID | Claim | Criticality | Evidence IDs | Result | Confidence |
|---|---|---|---|---|---|
| `CLM-001` | Actionable recovery required paths now contain portable repository authority rather than generated runtime executables. | critical | `EV-001`; `EV-002` | supported | high |
| `CLM-002` | The centralized-logging source-only test runs without `.venv`, PyYAML, site packages, cluster credentials, or live APIs. | critical | `EV-001`; `EV-003` | supported | high |
| `CLM-003` | YAML metadata source-only validation runs without PyYAML while operator-runtime parsing remains separately tested. | critical | `EV-001`; `EV-004` | supported | high |
| `CLM-004` | Repository-managed operator tests and active centralized-logging validation still pass after the CI separation. | critical | `EV-001`; `EV-006` | supported | high |
| `CLM-005` | PR #5 GitHub checks passed at implementation commit `818fa5860c028ffd721c982861032adf1e9af1e0`. | critical | `EV-005`; `EV-001` | supported | high |
| `CLM-006` | The supplemental record is traceable to the prior evidence record, the input bundle, authority hashes, and the three implementation commits. | high | `EV-001`; `EV-007` | supported | high |
| `CLM-007` | Source-only and operator-runtime tests are complementary rather than interchangeable. | high | `EV-003`; `EV-004`; `EV-006` | supported | high |

## Problem and decision rationale

### Problem or opportunity

The initial feature implementation and evidence were valid on the operator
controller, but GitHub Actions revealed three hidden dependency-boundary
violations in succession:

1. a generated `.venv` executable was modeled as a source-controlled recovery
   authority;
2. the aggregate repository guardrail invoked a centralized-logging
   operator-runtime self-test from a source-only checkout;
3. after that separation, the same aggregate invoked YAML parsing without
   installing PyYAML.

Each failure was a new instance of one general problem: the repository had not
made the execution tier of every validation target explicit.

### Decision

Establish explicit source-only and operator-runtime validation tiers and enforce
their boundaries:

- repository recovery authority must be portable source paths;
- generated environments stay in canonical commands and runtime guidance but
  not in source-existence contracts;
- GitHub guardrails use dependency-minimal source-only tests;
- source-only tests run with `python3 -S`;
- PyYAML is imported only when parsing is requested;
- operator-runtime and live-cluster tests remain mandatory for implementation
  and evidence closeout.

### Decision drivers

- GitHub Actions must validate a clean source checkout without hidden
  workstation state.
- Operator validation must continue to use pinned dependencies and real
  cluster access.
- A passing source-only contract must not be mistaken for a live runtime PASS.
- Missing optional dependencies must fail actionably rather than through an
  import traceback.
- Each discovered instance must become a reusable regression for the broader
  class.

### Alternatives considered

| Alternative | Advantages | Disadvantages or risks | Decision |
|---|---|---|---|
| Install the complete homelab `.venv` in GitHub Actions | Makes operator tests available in CI | Requires credentials, cluster access, larger setup, and conflates source and runtime boundaries | rejected |
| Install only PyYAML in GitHub Actions | Fixes the third failure quickly | Leaves hidden optional-dependency coupling and does not address live-runtime assumptions | rejected |
| Remove runtime tests from SAGE validation entirely | Simplifies CI | Weakens operator and evidence closeout assurance | rejected |
| Mark all failing tests as skipped in CI | Makes the PR green | Hides contract defects and eliminates regression coverage | rejected |
| Explicit source-only and operator-runtime tiers | Portable CI plus retained runtime assurance | Adds targets, documentation, and maintenance | accepted |

### Tradeoffs and consequences

- More Make targets and tests exist, but each target now has a clear execution
  contract.
- Source-only tests cannot prove inventory parsing, credentials, connectivity,
  or live service health; those remain operator responsibilities.
- Operator-runtime tests remain slower and machine-dependent because they
  intentionally validate pinned tools and the active cluster.
- Lazy optional imports improve portability but require explicit actionable
  handling when parsing is attempted without the dependency.

## Architecture or change description

```text
                    repository checkout
                           |
              +------------+-------------+
              |                          |
              v                          v
     source-only CI tier          operator-runtime tier
     python3 -S                    repository .venv
     no site packages              pinned PyYAML/Ansible
     no credentials                kubeconfig and credentials
     no live APIs                  live cluster and Loki
              |                          |
              +------------+-------------+
                           |
                    evidence closeout
```

### Before

- Catalog validation required a generated `.venv` executable to exist.
- `make sage-guardrails` depended on operator-only centralized-logging and YAML
  parsing tests.
- Importing the metadata helper eagerly required PyYAML.
- CI failures appeared sequentially because the test tier was implicit.

### After

- `canonical_recovery.required_paths` rejects runtime-only path components.
- The centralized-logging source test imports the real validator with
  `python3 -S` and validates pure contracts and entry points.
- The YAML source test validates type, redaction, and actionable missing-parser
  behavior without importing PyYAML.
- The operator tests use the homelab `.venv`.
- The active runtime validator remains a separate live-cluster target.
- GitHub Actions runs the source-only aggregate and passes.

## Source of truth and implementation lineage

### Repository files

```text
Makefile
sage-actionable-failures.json
sage-change-authority.json
scripts/sage/sage_actionable_failure.py
scripts/sage/sage-actionable-failure-self-test.py
scripts/sage/sage_yaml_metadata.py
scripts/sage/sage-yaml-metadata-source-self-test.py
scripts/sage/sage-yaml-metadata-self-test.py
infrastructure/k3s-homelab/Makefile
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime-source-self-test.py
infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime-self-test.py
markdown/standards/kalaxy3-sage-actionable-failure-contract.md
```

### Implementation commits

```text
91785bc Make actionable recovery paths CI-portable
3fc7e45 Separate source-only and operator runtime self-tests
818fa58 Separate YAML metadata source and runtime self-tests
```

The supplemental publication implementation commit is
`818fa5860c028ffd721c982861032adf1e9af1e0`. The prior record
`SAGE-K3-GUARDRAIL-20260731-001` remains historically correct for implementation
commit `4c369193731e9fc7832d8c2a0e1e2718a6210e86`.

### Versioned dependencies

| Component/tool | Version | Source |
|---|---:|---|
| SAGE record schema | 1.2 | metadata contract |
| GitHub Actions | version not captured | PR #5 checks screenshot |
| Python | version not captured | source-only and operator command output |
| PyYAML | version not captured; operator-runtime only | lazy import contract and `.venv` parsing test |
| Loki Helm chart | 18.5.4 | live runtime validation |
| Fluent Bit Collector chart | 1.0.9 | live runtime validation |
| Longhorn | version not captured | Bound storage observation |

### Controller portability and repository authority

| Item | Evidence |
|---|---|
| Repository-controlled dependencies | Make targets, source tests, actionable-failure catalog, standards, and validators |
| Controller bootstrap | repository homelab `.venv` for operator-runtime tests |
| Controller preflight | source-only tests pass with `python3 -S`; operator and live tests pass separately |
| Controller host | donbs-imac |
| Execution host | donbs-imac-and-github-actions |
| Machine-local authoritative state | none claimed; `.venv`, credentials, and kubeconfig are runtime prerequisites rather than repository authority |

- [x] Another supported controller can validate source contracts from a clean checkout.
- [x] No generated `.venv` path is modeled as source-controlled authority.
- [x] Operator-only dependencies remain explicit and separately validated.
- [x] The final implementation commit and green CI result are recorded.

### Configuration excerpt

```make
sage-self-test: centralized-logging-runtime-source-self-test                 sage-yaml-metadata-source-self-test

centralized-logging-runtime-self-test:
        .venv/bin/python scripts/validate-centralized-logging-runtime-self-test.py

sage-yaml-metadata-self-test:
        infrastructure/k3s-homelab/.venv/bin/python           scripts/sage/sage-yaml-metadata-self-test.py
```

The excerpt is conceptual; exact formatting remains authoritative in the
repository Makefiles.

## Prerequisites and assumptions

### Proven prerequisites

- `EV-002`: repository authority files exist in a source-only fixture without
  `.venv`.
- `EV-003`: the centralized-logging validator imports and its pure contracts
  pass under `python3 -S`.
- `EV-004`: metadata types and missing-PyYAML behavior pass under `python3 -S`.
- `EV-006`: the repository `.venv` and live cluster remain available on
  `donbs-imac`.
- `EV-005`: GitHub Actions executed the PR source-only guardrails successfully.

### Assumptions

| Assumption ID | Assumption | Risk if false | Validation plan |
|---|---|---|---|
| `ASM-001` | The screenshot corresponds to PR #5 at `818fa5860c028ffd721c982861032adf1e9af1e0` as reported by the operator. | CI lineage could be misattributed. | Retain screenshot, full SHA, and branch history; confirm in PR before merge. |
| `ASM-002` | Future source-only tests continue to avoid optional site packages and live access. | CI portability could regress. | Run with `python3 -S` and keep explicit tier documentation. |
| `ASM-003` | Operator controllers recreate the repository `.venv` before runtime testing. | Operator tests could fail before target validation. | Use repository bootstrap and actionable prerequisite guidance. |

## Implementation procedure

### Preparation

```bash
cd ~/dvlp/Kalaxy3
git switch feature/actionable-guardrail-recovery
git status
git fetch origin
```

### Execution

```bash
# Commit 91785bc
# Classify required_paths as repository authority and add a source-only fixture.

# Commit 3fc7e45
# Add centralized-logging source-only tests and preserve .venv operator tests.

# Commit 818fa58
# Add YAML metadata source-only tests, lazy PyYAML loading, and preserve parsing tests.
```

### Expected change

- `make sage-guardrails` runs only source-only tests that a clean GitHub checkout
  can satisfy.
- Operator targets continue to use the repository `.venv`.
- Live runtime validation remains unchanged.
- GitHub PR checks pass without adding broad runtime dependencies to the
  workflow.

### Observed change

```text
Kalaxy3 centralized logging source-only self-test: PASS
Kalaxy3 YAML metadata source-only self-test: PASS
Kalaxy3 centralized logging runtime self-test: PASS
Kalaxy3 centralized logging runtime validation: PASS
Kalaxy3 repository SAGE guardrails: PASS
GitHub PR #5: All checks have passed
```

### Failed or superseded paths

| Attempt | Failure | Why it failed | Generic correction |
|---|---|---|---|
| Require `.venv/bin/ansible-playbook` in `required_paths` | CI checkout had no generated `.venv` | Runtime prerequisite was misclassified as repository authority | Reject runtime-only path components from source authority |
| Run centralized-logging runtime self-test inside `sage-self-test` | `.venv/bin/python` did not exist in GitHub Actions | Operator-runtime test was included in source-only aggregate | Add source-only test target and keep runtime target separate |
| Call stale `select_coverage_label` in new source test | Actual API is `select_node_label(candidates, values, nodes)` | Test was written against remembered rather than inspected API | Inspect and enforce the real function signature |
| Run YAML parsing test under system Python | PyYAML was absent | Parsing dependency belonged to operator tier | Add source-only metadata contract test and lazy import |
| Install ad hoc dependencies in CI | not attempted | Would mask tier coupling rather than fix it | Preserve dependency-minimal source-only contract |

## Evidence items

### `EV-001` — Supplemental commit lineage and terminal validation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-001`; `CLM-002`; `CLM-003`; `CLM-004`; `CLM-005`; `CLM-006` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | donbs-imac |
| Target | feature branch and validation targets |
| Tool and version | Git=version-not-captured; Make=version-not-captured; Python=version-not-captured |
| Expected result | Three CI repairs are committed and all local validation tiers pass |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
git log --oneline c50270d..HEAD
make sage-guardrails
make centralized-logging-runtime-source-self-test
make sage-yaml-metadata-source-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

**Observed result**

```text
818fa58 Separate YAML metadata source and runtime self-tests
3fc7e45 Separate source-only and operator runtime self-tests
91785bc Make actionable recovery paths CI-portable
All listed validation targets returned PASS.
```

**Interpretation**

The transcript proves the final branch state and local validation outcome. The
separate GitHub screenshot proves the hosted PR result.

### `EV-002` — Repository authority and runtime-prerequisite classification

| Field | Value |
|---|---|
| Classification | `repository-evidence` |
| Supports or contradicts | `CLM-001` |
| Collected by | repository SAGE evidence orchestrator |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | repository snapshot |
| Target | actionable-failure catalog and parser |
| Tool and version | SAGE-actionable-failure=818fa5860c028ffd721c982861032adf1e9af1e0 |
| Expected result | Source authority excludes generated runtime directories |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/evidence-input-provenance.json` |

**Command, query, source, or observation**

```text
canonical_recovery.required_paths:
  - infrastructure/k3s-homelab/inventory/hosts.yml
  - infrastructure/k3s-homelab/playbooks/validate-centralized-logging.yml

canonical command:
  .venv/bin/ansible-playbook ...
```

**Observed result**

The repository model rejects absolute paths, path traversal, `.venv`, `.tools`,
`.helm`, and cache directories from `required_paths`. The runtime command still
uses the repository-managed `.venv`.

**Interpretation**

The repair preserves canonical operator guidance while allowing a source-only
checkout to validate recovery authority.

### `EV-003` — Centralized-logging source-only and operator test tiers

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-002`; `CLM-007` |
| Collected by | repository automation |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | donbs-imac source-only fixture and operator runtime |
| Target | centralized-logging runtime validator contracts |
| Tool and version | Python=version-not-captured |
| Expected result | Source-only import and pure contracts pass without optional dependencies; operator test remains separate |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 -S scripts/validate-centralized-logging-runtime-source-self-test.py
.venv/bin/python scripts/validate-centralized-logging-runtime-self-test.py
```

**Observed result**

```text
PASS runtime validator source-only import without PyYAML
PASS locked-release interpretation
PASS dynamic all-node label selection
PASS live runtime entry-point contract
Kalaxy3 centralized logging source-only self-test: PASS
Kalaxy3 centralized logging runtime self-test: PASS
```

**Interpretation**

The source test proves import and pure contracts, not live health. The operator
test retains dependency and inventory behavior.

### `EV-004` — YAML metadata source-only and parsing test tiers

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-003`; `CLM-007` |
| Collected by | repository automation |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | donbs-imac source-only and operator runtimes |
| Target | YAML metadata contract and tagged parsing |
| Tool and version | PyYAML=version-not-captured |
| Expected result | Pure contract passes without PyYAML; parsing and opaque tags pass in `.venv` |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
python3 -S scripts/sage/sage-yaml-metadata-source-self-test.py
infrastructure/k3s-homelab/.venv/bin/python   scripts/sage/sage-yaml-metadata-self-test.py
```

**Observed result**

```text
PASS plain YAML metadata type contract
PASS opaque tagged-value redaction contract
PASS actionable missing-PyYAML recovery
Kalaxy3 YAML metadata source-only self-test: PASS
PASS vault and unknown tags remain opaque
Kalaxy3 SAGE YAML metadata self-test: PASS
```

**Interpretation**

Lazy loading removes an import-time dependency from source-only validation
without weakening operator parsing coverage.

### `EV-005` — GitHub PR #5 green checks

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-005` |
| Collected by | Don Buddenbaum |
| Collected at | 2026-07-31T23:17:00-05:00 |
| Execution source | GitHub Actions PR interface |
| Target | PR #5 at `818fa5860c028ffd721c982861032adf1e9af1e0` |
| Tool and version | GitHub Actions=version-not-captured |
| Expected result | Repository SAGE and MkDocs checks pass with no base conflict |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/github-pr5-checks-passed.png` |

**Command, query, source, or observation**

```text
GitHub PR #5 checks panel
```

**Observed result**

```text
All checks have passed
1 skipped, 2 successful checks
No conflicts with base branch
```

**Interpretation**

The screenshot provides the hosted CI result. The skipped `doc` check is
expected because the PR-specific MkDocs validation and SAGE validation passed.

### `EV-006` — Retained operator-runtime and live logging validation

| Field | Value |
|---|---|
| Classification | `direct-observation` |
| Supports or contradicts | `CLM-004`; `CLM-007` |
| Collected by | Don Buddenbaum and repository automation |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | donbs-imac |
| Target | active Kalaxy3 centralized logging |
| Tool and version | Loki=18.5.4; fluent-bit-collector=1.0.9 |
| Expected result | Source-only separation does not weaken live validation |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/terminal-evidence.md` |

**Command, query, source, or observation**

```bash
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

**Observed result**

```text
collectors: 7
loki: 1
gateway: 1
storage: Bound 40Gi longhorn
recent_query_results: 1
covered_nodes: amd64-01, amd64-02, arm64-01 through arm64-05
```

**Interpretation**

The operator tier still proves live service health. This result is bounded to
the collection time and does not prove long-term retention or performance.

### `EV-007` — Input provenance, prior evidence, and authority hashes

| Field | Value |
|---|---|
| Classification | `generated-artifact` |
| Supports or contradicts | `CLM-006` |
| Collected by | repository SAGE evidence orchestrator |
| Collected at | 2026-07-31T23:21:49-05:00 |
| Execution source | donbs-imac and evidence generator |
| Target | supplemental input bundle and prior evidence lineage |
| Tool and version | sage-evidence-orchestrator=1.2-contract |
| Expected result | Original request, repository HEAD, prior record, terminal transcript, screenshot, and authority hashes are traceable |
| Actual result | pass |
| Confidence | high |
| Sensitive data | none |
| Artifact | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/evidence-input-provenance.json` |

**Command, query, source, or observation**

```text
Input bundle SHA-256: cacbdf374351d1ed6e974c6ab60b82bf4af3a74adfe4ba300b7aadc9ed3d7b8e
GitHub checks screenshot SHA-256: 58b9d85f1343644c7a8d1d5675f45943d5dbec191a70e5677f56d61403214d6e
Prior evidence ID: SAGE-K3-GUARDRAIL-20260731-001
Prior evidence commit: c50270d740fa3bcca976b6ed20db07cfed545638
```

**Observed result**

The input bundle contains the schema, template, publisher, indexer, current
source snapshots, repository context, and terminal evidence. The provenance
artifact also binds the separately supplied GitHub screenshot to its digest.

**Interpretation**

This evidence record supplements rather than rewrites the prior record. The
publisher remains authoritative for final timestamp replacement, checksum,
catalog reconciliation, evidence commit, and push.

## Verification and acceptance criteria

| Criterion ID | Requirement | Test or evidence | Expected | Observed | Result |
|---|---|---|---|---|---|
| `AC-001` | Recovery authority is source-portable | `EV-002` | no generated runtime path in `required_paths` | observed | pass |
| `AC-002` | Centralized-logging source contract runs without optional runtime dependencies | `EV-003` | `python3 -S` PASS | observed | pass |
| `AC-003` | YAML metadata source contract runs without PyYAML | `EV-004` | type, redaction, and actionable missing-parser tests pass | observed | pass |
| `AC-004` | Operator centralized-logging tests remain valid | `EV-003`; `EV-006` | `.venv` self-test and live validator pass | observed | pass |
| `AC-005` | Operator YAML parsing remains valid | `EV-004` | tagged parsing and opaque-value tests pass | observed | pass |
| `AC-006` | Repository aggregate guardrails pass | `EV-001` | `make sage-guardrails` PASS | observed | pass |
| `AC-007` | Hosted PR checks pass | `EV-005` | two successful checks and no base conflict | observed | pass |
| `AC-008` | Supplemental lineage is traceable | `EV-007` | prior evidence, three commits, bundle, screenshot, and hashes recorded | present | pass |

### Functional verification

```bash
make sage-guardrails
make centralized-logging-runtime-source-self-test
make sage-yaml-metadata-source-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

Observed:

```text
Kalaxy3 repository SAGE guardrails: PASS
Kalaxy3 centralized logging source-only self-test: PASS
Kalaxy3 YAML metadata source-only self-test: PASS
Kalaxy3 centralized logging runtime self-test: PASS
Kalaxy3 centralized logging runtime validation: PASS
```

### Negative verification

- The source-only logging test fails if the validator eagerly imports PyYAML.
- The YAML source-only test requires an actionable error when parsing is
  requested without PyYAML.
- The actionable-failure parser rejects `.venv`, `.tools`, `.helm`, absolute
  paths, and traversal from repository `required_paths`.
- The source-only node-label regression rejects incomplete node coverage and
  enforces the real `select_node_label(candidates, values, nodes)` signature.

## Idempotency and repeatability

### First accepted run

The fixes were committed in three cohesive checkpoints because each GitHub
failure exposed the next hidden runtime dependency. Failed helper and CI paths
stopped before merge and preserved evidence.

### Steady-state rerun

Local source-only, operator-runtime, live-cluster, SAGE index, and evidence
guardrails passed at `818fa5860c028ffd721c982861032adf1e9af1e0`. GitHub then reran the PR workflow
and reported all checks passed.

### Interpretation

Source-only tests are deterministic for a given checkout and system Python.
Operator-runtime and live tests are repeatable but depend on the repository
`.venv`, credentials, connectivity, and current cluster state. The two tiers
must continue to be run for their separate claims.

## Security, privacy, and evidence handling

### Security controls

- Source-only CI does not require kubeconfig, Vault access, cluster
  credentials, or secret decryption.
- PyYAML is loaded only when parsing is requested.
- Opaque tagged values remain redacted and reject boolean coercion.
- The operator `.venv` remains the approved dependency boundary.
- The GitHub screenshot contains repository and check status only.
- The publisher scans text artifacts for high-confidence secret patterns.

### Sensitive material excluded

- No Vault ciphertext, credentials, tokens, passwords, keys, kubeconfig
  contents, or Kubernetes Secret values are included.
- Source authority files are represented by hashes in provenance rather than
  copied into permanent artifacts.
- The input ZIP is referenced by digest and not embedded.

### Redactions and omissions

- GitHub runner image and action versions were not captured.
- Python, PyYAML, Git, and Make versions were not captured in this
  supplemental session.
- Node addresses are not required for the portability claims.

### Residual security risk

A future source-only test could accidentally import a dependency that reads
credentials or contacts live services. Running with `python3 -S`, reviewing
imports, and maintaining explicit tier contracts reduces but does not eliminate
that risk.

## Reliability, recovery, rollback, and rebuild

### Failure modes

| Failure mode | Detection | Impact | Recovery |
|---|---|---|---|
| Generated path added to repository authority | actionable-failure self-test or CI guardrail | source-only catalog validation fails | move the path to runtime guidance and keep source authority portable |
| Operator test added to source-only aggregate | GitHub `No such file or directory` for `.venv` | PR guardrail fails before target validation | add a source-only contract test and retain operator target separately |
| Optional parser imported eagerly | source-only `ModuleNotFoundError` | CI cannot import validator modules | lazy-load dependency and fail actionably only when feature is invoked |
| Source test uses stale API | attribute or signature regression | false test failure | inspect the repository implementation and enforce its actual signature |
| Source-only test passes but runtime is broken | operator or live target fails | false confidence if tiers are conflated | require both tiers before evidence closeout |
| GitHub checks regress | PR status turns red | merge blocked | inspect first failure, classify tier, add generic regression, rerun |

### Rollback

For the unmerged feature branch:

```bash
git switch feature/actionable-guardrail-recovery
git revert 818fa5860c028ffd721c982861032adf1e9af1e0
git revert 3fc7e45e6ba641e18c77345f7bda7680ef42e59d
git revert 91785bceb2f473eb8623e14c4d2e490e89f5bb80
```

Because `818fa58` depends on the target separation introduced by `3fc7e45`,
revert in reverse order. Reverts must be reviewed and must not be used to
bypass red CI.

### Rebuild procedure

1. Clone `donb4iu/Kalaxy3` and check out `818fa5860c028ffd721c982861032adf1e9af1e0` or a merged
   descendant.
2. Run `make sage-guardrails` in a clean source checkout.
3. Confirm source-only tests use `python3 -S` and do not require `.venv`.
4. Recreate the repository-managed homelab `.venv`.
5. Run `make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test`.
6. Run `make sage-yaml-metadata-self-test`.
7. With cluster access, run
   `make -C infrastructure/k3s-homelab centralized-logging-runtime-validate`.
8. Confirm GitHub PR checks pass before merge.
9. Run `python3 scripts/sage/sage-index.py check`.

### Data durability and backup impact

These changes affect validation code, dependency boundaries, and documentation.
They do not alter Loki data, PVCs, retention, reclaim policy, or backups. The
live validator observes Bound Longhorn storage but does not test restore.

## Operational considerations and observability

### Health signals

- GitHub PR check status and commit SHA.
- `make sage-guardrails`.
- Source-only centralized-logging and YAML metadata test results.
- Operator `.venv` self-test results.
- Active centralized-logging runtime output.
- Evidence index and orchestration guardrails.

### Routine verification

```bash
cd ~/dvlp/Kalaxy3
make sage-guardrails
make centralized-logging-runtime-source-self-test
make sage-yaml-metadata-source-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
make sage-yaml-metadata-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

### Capacity, performance, cost, and sustainability

- **Capacity:** no runtime capacity change was introduced.
- **Performance:** source-only CI should be faster than provisioning the full
  operator environment, but duration was not measured.
- **Cost:** no new persistent service or paid dependency was added.
- **Sustainability:** source-only checks avoid unnecessary environment
  provisioning and live cluster access; power and runner savings were not
  measured.

## Known limitations, evidence gaps, and risks

| ID | Type | Description | Impact | Owner | Due or trigger |
|---|---|---|---|---|---|
| `GAP-001` | evidence-gap | `work_started_at` is `not-captured`. | Session duration cannot be calculated. | Kalaxy3 architecture | next evidence session |
| `GAP-002` | evidence-gap | GitHub runner image, action versions, Python, PyYAML, Git, and Make versions were not captured. | Exact tool reproduction is incomplete. | Kalaxy3 architecture | next workflow or test-tier edit |
| `GAP-003` | limitation | The GitHub screenshot is visual evidence and does not include the run URL or machine-readable workflow result. | Hosted CI lineage relies on PR number, branch SHA, and operator-provided screenshot. | Kalaxy3 architecture | future GitHub API evidence integration |
| `GAP-004` | limitation | Source-only tests validate imports and pure contracts, not inventory parsing, credentials, network access, or live services. | A source PASS cannot establish runtime health. | Kalaxy3 architecture | every implementation closeout |
| `GAP-005` | risk | Future aggregate Make targets may accidentally reintroduce operator-only dependencies. | CI portability could regress. | Kalaxy3 architecture | any aggregate guardrail change |
| `GAP-006` | technical-debt | Remaining actionable-failure candidates still require classification. | Other validators may retain implicit dependency tiers. | Kalaxy3 architecture | prioritized migration work |
| `GAP-007` | governance | Reviewer is pending and PR #5 is not yet merged. | Record is validated, not accepted. | Kalaxy3 architecture | PR review and merge |

## Troubleshooting

### GitHub reports a missing `.venv` executable

**Meaning**

A source-only aggregate invoked an operator-runtime target or modeled a
generated path as repository authority.

**Checks**

```bash
grep -n "\.venv" Makefile sage-actionable-failures.json
make sage-guardrails
```

**Recovery**

Keep `.venv` in operator commands and guidance, remove it from source
`required_paths`, and add or invoke a source-only contract test.

### Source-only test reports missing PyYAML

**Meaning**

Parsing was attempted in the source-only tier or an optional dependency was
imported eagerly.

**Checks**

```bash
python3 -S scripts/sage/sage-yaml-metadata-source-self-test.py
grep -n "import yaml" scripts/sage/sage_yaml_metadata.py
```

**Recovery**

Keep import lazy, validate pure contracts without parsing, and run the parsing
test through the repository `.venv`.

### Centralized-logging source test reports a missing helper

**Meaning**

The test may use a stale remembered API.

**Checks**

```bash
grep -n "^def select_"   infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py
```

**Recovery**

Inspect the actual function name and signature, update the source-only
regression, then rerun both test tiers.

### Source-only tests pass but live validation fails

**Meaning**

Repository contracts are portable, but operator dependencies, access, or the
target system are not healthy.

**Checks**

```bash
make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
make -C infrastructure/k3s-homelab centralized-logging-runtime-validate
```

**Recovery**

Treat the operator or live failure separately; do not weaken the source-only
test or report target health from a source-contract PASS.

## Freshness, revalidation, and supersession

### Revalidate when

- any SAGE aggregate guardrail target changes;
- `.venv`, optional dependencies, or runtime paths appear in source authority;
- centralized-logging validator imports or pure helper APIs change;
- YAML metadata loading or tagged-value behavior changes;
- the GitHub Actions workflow or runner environment changes;
- operator Python, PyYAML, Ansible, kubeconfig, or cluster access changes;
- the active logging deployment or cluster topology changes;
- the prior actionable-guardrail evidence is superseded;
- PR #5 is rebased, amended, or merged at a different implementation SHA.

### Scheduled review

```text
event-based: review on test-tier, workflow, runtime-dependency, validator, or PR lineage change
```

### Supersession rule

This supplemental record depends on, but does not supersede,
`SAGE-K3-GUARDRAIL-20260731-001`. A future accepted record may supersede both
only if it preserves their implementation boundaries and failure chronology.

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
- [x] Supplemental implementation commit is recorded.
- [x] Prior evidence relationship is explicit.

### Evidence

- [x] Every critical claim has supporting evidence.
- [x] Expected and observed results are separated.
- [x] Source-only, operator-runtime, live, and hosted CI results are distinct.
- [x] Direct observations identify source, target, time, and tool version or an explicit gap.
- [x] Failed CI and stale-API paths are separated from final state.
- [x] Input bundle, terminal transcript, screenshot, and authority hashes are traceable.
- [x] Every `not-captured` metadata value has an evidence gap.
- [x] Idempotency and repeatability are bounded.

### Safety and operations

- [x] Secrets and credentials are excluded.
- [x] Source-only CI requires no privileged runtime access.
- [x] Operator and live validation remain documented.
- [x] Rollback and rebuild procedures are documented.
- [x] Known limitations and gaps have owners or triggers.
- [x] Revalidation criteria are defined.

### Review acceptance

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Owner | Kalaxy3 architecture | conditional | 2026-07-31 | Implementation and PR checks passed; merge remains pending. |
| Reviewer | pending | pending | pending | Review supplemental evidence and PR #5 before merge. |

## Git review and publication

Use only the repository publication process:

```bash
cd ~/dvlp/Kalaxy3

python3 scripts/sage/sage-publish.py check \
  ~/Downloads/kalaxy3-pr5-ci-portability-evidence-SAGE-K3-GUARDRAIL-20260731-002.zip

python3 scripts/sage/sage-publish.py publish \
  ~/Downloads/kalaxy3-pr5-ci-portability-evidence-SAGE-K3-GUARDRAIL-20260731-002.zip \
  --push
```

The package uses evidence-only publication and binds lineage to
`818fa5860c028ffd721c982861032adf1e9af1e0`. Publishing creates a supplemental evidence commit,
record checksum, publication manifest, and reconciled indexes. The PR checks
must rerun after publication before merge.

## Appendices and raw artifacts

### Artifact inventory

| Artifact | Path or URI | SHA-256 | Contains sensitive data | Retention |
|---|---|---|---|---|
| Terminal evidence | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/terminal-evidence.md` | `48b4e5e770f87659a9df126bdd1f98293d63b4bee38d75aa5113cbef48fa6454` | no | permanent with evidence ID |
| Evidence input provenance | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/evidence-input-provenance.json` | `385956ecb099b04a71d1148c070a6aa470389b43653b9f611eb9b42491d05352` | no | permanent with evidence ID |
| GitHub PR #5 checks screenshot | `markdown/evidence-artifacts/SAGE-K3-GUARDRAIL-20260731-002/github-pr5-checks-passed.png` | `58b9d85f1343644c7a8d1d5675f45943d5dbec191a70e5677f56d61403214d6e` | no | permanent with evidence ID |
| Input bundle | `kalaxy3-pr5-ci-repair-evidence-inputs-20260731-232149.zip` | `cacbdf374351d1ed6e974c6ab60b82bf4af3a74adfe4ba300b7aadc9ed3d7b8e` | not embedded; may contain source snapshots | retain outside repository until publication review completes |

### Original requester language

```text
Generate a supplemental schema 1.2 SAGE evidence record for the post-publication CI repairs on PR #5, Add actionable SAGE guardrail recovery and runtime validation. Link the record to prior evidence SAGE-K3-GUARDRAIL-20260731-001 and prior evidence commit c50270d. Cover implementation commits 91785bc, 3fc7e45, and 818fa58. Explain the three source-only CI failures and their broader classes: a generated .venv executable incorrectly modeled as repository authority; an operator-runtime centralized-logging self-test incorrectly included in source-only GitHub guardrails; and a YAML parsing self-test requiring PyYAML incorrectly included in the same source-only aggregate. Document the generic remedies: repository-authority versus runtime-prerequisite classification, source-only versus operator-runtime test tiers, lazy optional dependency loading, source-only tests using python3 -S, and retention of the repository-managed .venv and live cluster tests for operator and evidence closeout. Preserve failed paths, accepted final state, rationale, limitations, rollback, rebuild, and revalidation. Record that PR #5 GitHub checks passed at HEAD 818fa5860c028ffd721c982861032adf1e9af1e0; the green GitHub screenshot is supplied separately to the final evidence generator. Use the repository-owned SAGE standard, metadata contract, template, orchestrator, publisher, and indexer.
```

### Prior evidence relationship

```text
Prior evidence ID: SAGE-K3-GUARDRAIL-20260731-001
Prior evidence commit: c50270d740fa3bcca976b6ed20db07cfed545638
Prior implementation commit: 4c369193731e9fc7832d8c2a0e1e2718a6210e86
Supplemental implementation commit: 818fa5860c028ffd721c982861032adf1e9af1e0
```

### Publication-package generation note

The repository orchestrator produced a generation input bundle. This schema
1.2 publication ZIP adds `sage-package.json`, the supplemental record, terminal
evidence, provenance, and the GitHub checks screenshot under `payload/`.
