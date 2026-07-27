# Current SAGE evidence

[TOC]

These records conform to schema 1.2 and use authoritative
navigation metadata.

| Section | Record | Summary | Class | Status | Valid as of |
|---|---|---|---|---|---|
| benchmarks | [Capture pre-logging Kubecost baseline](../benchmarks/kalaxy3-pre-logging-kubecost-baseline-evidence.md) | Preserves checksum-verified 24-hour and 72-hour Kubecost control measurements before centralized logging changes cluster resource use and cost. | sage-current | validated | 2026-07-25 |
| governance | [Preserve legacy evidence and generate navigation](../operations/kalaxy3-sage-legacy-evidence-navigation-evidence.md) | Adds strict navigation metadata for new SAGE records while preserving and indexing schema 1.0, schema 1.1, and pre-SAGE evidence without rewriting historical source files. | sage-current | validated | 2026-07-25 |
| governance | [Validate interchangeable Kalaxy3 automation controllers](../operations/kalaxy3-controller-machine-portability-evidence.md) | Verifies that clean iMac and Mac mini controllers reproduce the same repository-managed Python and Ansible environment despite different system Python versions. | sage-current | validated | 2026-07-26 |
| governance | [Validate the Kalaxy3 Daux landing page](../governance/kalaxy3-daux-landing-page-sage-evidence.md) | Validates the Kalaxy3 Daux landing-page source, container bootstrap, local render, visual identity, and clean feature-branch preservation without changing branch publication automation. | sage-current | validated | 2026-07-26 |
| governance | [Pause logging work to close the SAGE enforcement gap](../governance/kalaxy3-sage-guardrail-gap-observability-pause-evidence.md) | Documents the machine-local Helm escape path, the missing preventive SAGE controls, and the decision to checkpoint and pause centralized logging until repository and admission guardrails are implemented. | sage-current | validated | 2026-07-26 |
| security | [Enforce canonical controller access across Kalaxy3](../security/kalaxy3-controller-access-baseline-sage-evidence.md) | Validates a repository-owned dual-controller SSH and sudo baseline across seven Kalaxy3 nodes and retires the legacy Intel pi administration path. | sage-current | validated | 2026-07-26 |
