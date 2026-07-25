# Operations evidence

[TOC]

| Section | Record | Summary | Class | Status | Valid as of |
|---|---|---|---|---|---|
| operations | [Canonical metadata contract and publisher enforcement](../../operations/kalaxy3-sage-canonical-metadata-contract-evidence.md) | Kalaxy3 SAGE metadata is now defined by a schema 1.1 machine-readable contract, a matching record standard and template, and publisher validation that rejects missing, extra, reordered, renamed, or inconsistent metadata. Every new record must contain an exact YAML field set, an exact human-readable Record metadata table, normalized timestamps, timezones,... | sage-legacy | validated | 2026-07-25 |
| operations | [Repeatable Package Generation and Git Publication Process](../../operations/kalaxy3-sage-evidence-publication-process-evidence.md) | Kalaxy3 now has a repository-owned SAGE evidence publication process that replaces session-specific packaging and Git instructions with a stable contract. Evidence generators must produce one ZIP containing sage-package.json and a canonical payload/; scripts/sage/sage-publish.py validates package integrity, SAGE record structure, claim-to-evidence referen... | sage-legacy | validated | 2026-07-25 |
