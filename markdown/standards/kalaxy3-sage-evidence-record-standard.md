---
title: Kalaxy3 SAGE Evidence Record Standard
project: Kalaxy3
record_type: governance-standard
schema_version: "1.0"
status: proposed
created_at: 2026-07-24T23:45:00-05:00
valid_as_of: 2026-07-24
owner: Kalaxy3 architecture
intended_path: markdown/standards/kalaxy3-sage-evidence-record-standard.md
companion_template: markdown/templates/sage-evidence-record-template.md
---

# Kalaxy3 SAGE Evidence Record Standard

## SAGE meaning

**SAGE** stands for **Systems Architecture & Governance through Evidence**.

SAGE is the Kalaxy3 evidence-driven engineering methodology. It treats
architecture decisions, implementation records, observed verification, known
limitations, rebuild instructions, and operational outcomes as linked evidence
rather than as isolated narrative documents.

The goal is to create durable engineering memory that can be used by humans,
automation, and future AI services without trusting recollection or unsupported
summaries.

A SAGE record should make it possible to answer:

- What claim or system state is being asserted?
- What direct evidence supports it?
- Who performed, owns, and reviewed the work?
- When and where was the evidence collected?
- Why was this design selected?
- How can the result be reproduced, verified, repaired, or superseded?
- Which earlier and later records are related?
- How strong, current, and complete is the evidence?

## Evaluation of the current Kalaxy3 evidence records

### Overall assessment

The current Kalaxy3 installation records are technically strong. They preserve
important details that are commonly lost:

- design rationale and rejected alternatives;
- exact repository paths and configuration fragments;
- installation and reconciliation commands;
- observed terminal output;
- functional verification;
- security and credential-handling restrictions;
- rebuild and troubleshooting procedures;
- idempotency evidence in several records;
- known limitations and future work.

They already function as useful rebuild guides and institutional memory.

The weakness is consistency, not substance. Each record organizes evidence
differently, and several governance facts are implicit rather than
machine-readable. That limits cross-record search, automated freshness checks,
claim-to-proof traceability, and future Capability Lineage Graph ingestion.

### Strong patterns to preserve

1. **Purpose and rationale**

   Existing records usually explain both what was installed and why the design
   was selected. This is essential SAGE content and must remain mandatory.

2. **Final validated state**

   The strongest records summarize the accepted result before presenting the
   implementation history. This lets a reader distinguish the final design
   from failed attempts.

3. **Commands paired with observed results**

   The records generally distinguish commands from the output actually seen.
   SAGE should formalize this into evidence items rather than lose it in prose.

4. **Rebuild and troubleshooting guidance**

   The records are written to make Kalaxy3 reproducible rather than merely to
   chronicle work. This remains a core requirement.

5. **Security boundaries**

   Protected-UI and administrative-access records explicitly identify material
   that must not enter Git, including secrets, password hashes, and private
   keys. Every SAGE record must include a data-handling review, even when the
   answer is “no sensitive material involved.”

6. **Idempotency and functional verification**

   Several records prove that automation converges and that the deployed
   service performs its intended function. Both are stronger than installation
   success alone and should be independent acceptance criteria.

### Gaps the standard must correct

1. **No consistent evidence identity**

   Records do not consistently have an immutable evidence ID, schema version,
   record type, lifecycle status, or evidence owner.

2. **The five Ws are present but scattered**

   What, when, where, and why are often discoverable, but who performed,
   reviewed, or owns the result is usually absent. The five Ws must be explicit
   and complete near the beginning of every record.

3. **Claims are not formally connected to proof**

   A command and output may be present, but the specific claim that the output
   proves is not always identified. SAGE requires claim IDs and an evidence
   matrix.

4. **Planned, inferred, and observed information can be mixed**

   Future work, intended design, inferred meaning, and directly observed state
   sometimes appear in the same narrative. Every material statement must be
   distinguishable as direct evidence, generated evidence, derived conclusion,
   assumption, or planned work.

5. **Freshness and supersession are not governed**

   Records rarely say when they must be revalidated or which later record
   supersedes them. This is already material in Kalaxy3: older records refer to
   paths, flags, node counts, replica counts, or Kubecost behavior that later
   work changed.

6. **Repository lineage is inconsistent**

   Some records include a commit ID, while others provide only filenames or a
   proposed commit. Every accepted record should identify the implementation
   commit or explicitly state that it is not yet committed.

7. **Acceptance criteria are often implicit**

   Checklists are helpful, but a formal expected-versus-observed pass/fail table
   is easier to review and automate.

8. **Evidence capture context is incomplete**

   Commands should identify execution host, target cluster or node, namespace,
   local timezone, relevant system timestamp timezone, tool version, and exit
   status when material.

9. **Record completion is not always reflected in status**

   A record may contain unchecked requirements such as missing second-run
   idempotency evidence while still reading like a final record. Lifecycle
   status must make incompleteness visible.

10. **Large records mix distinct concerns**

    A record may contain architecture decisions, installation history,
    troubleshooting, raw logs, and future plans in one long stream. The new
    standard keeps these sections but gives them a predictable order and allows
    large raw evidence to move into appendices or linked artifacts.

## Mandatory five-W and one-H requirements

Every SAGE evidence record must explicitly answer all five Ws. **How** is also
mandatory because evidence without reproducible execution and validation is
not sufficient for Kalaxy3.

| Requirement | Required content |
|---|---|
| **Who** | Author or evidence collector, implementation operator, accountable owner, reviewer or approver, and affected teams or users when relevant. |
| **What** | The change, incident, decision, capability, claim, final state, and boundaries of what is and is not covered. |
| **When** | Implementation time, evidence-collection time, timezone, system timestamp timezone when different, valid-as-of date, and revalidation trigger or review date. |
| **Where** | Project, environment, cluster, nodes, namespaces, endpoints, repository paths, branches, and execution host. |
| **Why** | Problem or opportunity, decision drivers, alternatives considered, tradeoffs, risks, and expected value. |
| **How** | Implementation sequence, source changes, commands, observed results, acceptance tests, rollback, rebuild, and troubleshooting. |

A record that cannot answer one of the five Ws must identify the missing fact as
an evidence gap. It must not silently omit it.

## Evidence classifications

Every evidence item should use one of these classifications:

| Classification | Meaning |
|---|---|
| `direct-observation` | Output observed from the target system, tool, API, hardware, or user-visible behavior. |
| `generated-artifact` | A rendered manifest, report, package, checksum, test result, or other deterministic output. |
| `repository-evidence` | Version-controlled source, configuration, commit, diff, tag, or pull request. |
| `derived-conclusion` | A conclusion calculated or reasoned from identified evidence. |
| `external-authority` | Vendor documentation, standards, specifications, or authoritative external sources. |
| `assumption` | A fact believed for the purpose of the work but not yet proven. |
| `planned` | Intended future state that has not yet been implemented or validated. |
| `negative-evidence` | A failed test, absent resource, rejected response, or other observation showing that a condition did not hold. |

Direct observations and repository evidence should support all critical claims.
Derived conclusions must identify their supporting evidence IDs. Assumptions and
planned statements cannot be used to mark an acceptance criterion as passed.

## Confidence levels

| Confidence | Use |
|---|---|
| `high` | Direct, repeatable evidence from the correct target with clear provenance and no material contradiction. |
| `medium` | Credible evidence exists but measurement precision, coverage, or repeatability is limited. |
| `low` | Evidence is indirect, incomplete, provisional, or substantially assumption-based. |
| `unknown` | Confidence has not been assessed. This is allowed only in draft records. |

## Record lifecycle

Use exactly one status:

| Status | Meaning |
|---|---|
| `draft` | Record is being assembled; required facts or evidence may be missing. |
| `implemented` | Change exists, but full acceptance evidence or review is incomplete. |
| `validated` | Acceptance criteria passed and evidence is recorded. |
| `accepted` | Validated and reviewed as the current Kalaxy3 source of truth. |
| `superseded` | A newer record replaces some or all of this record. |
| `retired` | The capability or configuration no longer exists. |
| `rejected` | The attempted design was evaluated and intentionally not accepted. |

A record with an unchecked mandatory acceptance criterion cannot be `validated`
or `accepted`.

## Required evidence lineage

Every record must define relationships where applicable:

- `verifies`: decision, capability, requirement, or claim proved by this record;
- `depends_on`: records or system states required for this result;
- `supersedes`: earlier records or claims replaced by this result;
- `superseded_by`: later accepted record replacing this one;
- `related_to`: relevant but nondependent records;
- `conflicts_with`: evidence that materially contradicts this record;
- `generated_by`: automation, workflow, or tool that produced the record;
- `implemented_by`: Git commit, pull request, playbook, manifest, or change set;
- `revalidated_by`: later evidence showing the record still holds.

Use repository-relative paths and stable evidence IDs rather than only prose
references.

## Mandatory record sections

Every accepted SAGE evidence record must contain these sections, in this order:

1. Machine-readable front matter.
2. Title and one-paragraph executive summary.
3. Five Ws and How.
4. Scope and boundaries.
5. Final accepted state.
6. Claims and evidence matrix.
7. Problem and decision rationale.
8. Alternatives and tradeoffs.
9. Architecture or change description.
10. Source-of-truth files and implementation lineage.
11. Prerequisites and assumptions.
12. Implementation procedure.
13. Verification and acceptance criteria.
14. Idempotency or repeatability evidence.
15. Security, privacy, and secret-handling review.
16. Reliability, recovery, rollback, and rebuild procedure.
17. Operational considerations and observability.
18. Known limitations, evidence gaps, and risks.
19. Freshness, revalidation, and supersession rules.
20. Final checklist and reviewer acceptance.
21. Appendices or linked raw artifacts.

A section may state “not applicable,” but it must not disappear silently.

## Evidence item minimum fields

Each material evidence item must identify:

- evidence ID;
- classification;
- claim supported or contradicted;
- command, query, file, API, test, or observation;
- execution source and target;
- collection timestamp and timezone;
- observed result;
- expected result when testing;
- pass, fail, partial, or informational status;
- confidence;
- redactions or omitted sensitive material;
- artifact path or checksum when evidence is stored separately.

## Acceptance rules

A SAGE record is acceptable only when:

- all five Ws and How are answered;
- every critical claim has at least one evidence item;
- direct system evidence and repository evidence agree;
- expected and observed results are distinguished;
- failed attempts are separated from the accepted final state;
- idempotency or repeatability is tested when automation is involved;
- rollback or rebuild consequences are documented;
- credentials and sensitive material are excluded or redacted;
- limitations and assumptions are explicit;
- the implementation commit is recorded or marked pending;
- the record has an owner and reviewer;
- freshness and supersession rules are defined.

## Recommended evidence-record identifier

Use this format:

```text
SAGE-K3-<DOMAIN>-<YYYYMMDD>-<NNN>
```

Examples:

```text
SAGE-K3-STORAGE-20260724-001
SAGE-K3-FINOPS-20260724-001
SAGE-K3-NETWORK-20260724-001
```

The ID is permanent. Renaming a Markdown file does not change the evidence ID.

## Recommended repository organization

```text
markdown/
├── standards/
│   └── kalaxy3-sage-evidence-record-standard.md
├── templates/
│   └── sage-evidence-record-template.md
├── installation/
├── operations/
├── architecture/
├── decisions/
└── evidence-artifacts/
    └── <evidence-id>/
```

The Markdown record should contain concise, reviewable evidence. Very large raw
logs, generated YAML, screenshots, benchmark output, or archives should be
stored under `markdown/evidence-artifacts/<evidence-id>/` or another durable
artifact store and referenced by path and checksum.

Do not commit secrets, private keys, authentication hashes, unredacted Secret
manifests, tokens, credentials, or sensitive personal information.

## Migration guidance for existing records

Existing records do not need immediate full rewrites. Apply SAGE incrementally:

1. Add front matter with an evidence ID, status, owner, valid-as-of date, and
   lineage.
2. Add a Five Ws and How table.
3. Add a concise claims-and-evidence matrix referencing existing sections.
4. Add implementation commit and source-of-truth paths.
5. Add revalidation triggers and supersession links.
6. Change incomplete records to `draft` or `implemented` rather than presenting
   them as final.
7. Mark stale records `superseded` and link to the accepted replacement instead
   of deleting historical evidence.

## SAGE quality score

A lightweight review score may be used for existing and new records:

| Category | Points |
|---|---:|
| Five Ws and How complete | 15 |
| Final claim and scope clear | 10 |
| Claim-to-evidence traceability | 15 |
| Direct observed evidence | 10 |
| Repository and commit lineage | 10 |
| Reproducible implementation and rebuild | 10 |
| Acceptance and functional tests | 10 |
| Idempotency or repeatability | 5 |
| Security and data handling | 5 |
| Risks, limitations, and assumptions | 5 |
| Freshness and supersession | 5 |
| **Total** | **100** |

Suggested interpretation:

- `90–100`: accepted SAGE-grade record;
- `75–89`: validated but requires governance completion;
- `60–74`: useful implementation record with material evidence gaps;
- below `60`: narrative or working notes, not an accepted evidence record.

## Adoption decision

All new Kalaxy3 evidence records should begin from
`markdown/templates/sage-evidence-record-template.md`.

Existing records remain valuable historical evidence. They should be upgraded
when they are next modified, revalidated, or superseded rather than rewritten
all at once.
