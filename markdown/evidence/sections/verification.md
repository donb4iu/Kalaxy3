# Verification evidence

[TOC]

| Section | Record | Summary | Class | Status | Valid as of |
|---|---|---|---|---|---|
| verification | [Centralized logging availability SLO activation](../../verification/kalaxy3-centralized-logging-availability-slo-evidence.md) | Verifies live Fluent Bit and Loki availability SLO recording rules, inactive alert state, lifecycle-safe activation, and guarded evidence-capture recovery. | sage-current | validated | 2026-08-02 |
| verification | [Validate active centralized logging](../../verification/kalaxy3-centralized-logging-runtime-validation-evidence.md) | Validates Loki and Fluent Bit across all seven Kalaxy3 nodes, preserves failed operator paths, and records the repository-governed recovery and cluster guardrails. | sage-current | validated | 2026-08-04 |
| verification | [Audit centralized logging SAGE evidence quality](../../verification/kalaxy3-centralized-logging-sage-evidence-quality-audit.md) | Independently audits SAGE-K3-OBS-20260728-002 against the Kalaxy3 schema 1.2 quality contract and confirms it meets the generic SAGE prompt baseline while providing stronger specificity and traceability. | sage-current | validated | 2026-07-28 |
| verification | [Validate GPT-OSS shared inference runtime](../../verification/gpt-oss-shared-inference-runtime-validation.md) | Validates the governed GPT-OSS shared-inference runtime after two fail-closed controller corrections, including Longhorn-to-NFS-SSD model migration, exact model persistence, GPU execution, OpenWebUI health, and retained rollback storage. | sage-current | validated | 2026-09-19 |
