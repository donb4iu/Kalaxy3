# SAGE Project/RACI execution — auditable Definition of Done

**Authority:** Architect-approved execution principle for Project-defined work.
**Applies to:** SAGE-coordinated work and human, LLM, or automated participants
executing a Project-qualified engineering work item. This is a completion
contract, not a substitute for the particular issue's acceptance criteria.

## Operating invariant

**The Project defines the work. RACI defines the participant's authority.
Participants execute within both, subject to SAGE guardrails. Only the
Architect can override the governing Project/RACI contract.**

Participants may choose implementations, innovate, recover mechanical failures,
coordinate, and publish operational status or evidence when their RACI permits.
A proposal to change Architect-owned scope, acceptance criteria, or approval
is not itself an authorized change. If GitHub permissions cannot distinguish
proposal from approval, keep the proposal separate and require a recorded
Architect decision before the contract changes. A routine authorized action
does not require an unnecessary new Architect approval.

Git/GitHub persist source files, hashes, revisions, history, issue contracts,
assignments, PRs, and collaboration events. SAGE persists *semantic* evidence,
causal interpretations, and governing decisions with references to verifiable
Git/GitHub records. Generated catalogs are disposable discovery projections,
not another source of provenance or an independent completion condition.

## Definition of Done — five independent audit questions

Each item requires evidence from authoritative records. An LLM assertion, green
unit tests, or a Project status change alone is insufficient.

- [ ] **Project contract retrieved.** Record the canonical Project/issue URL,
      retrieval evidence, and contract revision/digest actually consumed before
      execution; include governing dependencies and applicable acceptance criteria.
- [ ] **RACI understood and applied.** Record the attributable participant,
      assigned RACI role, authoritative role/authority source, permitted operations,
      reserved decisions, and evidence of the boundary applied to the work.
- [ ] **Independent execution within scope.** Link actions and resulting changes
      to that exact contract and authority. Innovation is permitted within scope;
      scope changes must be proposed, not silently approved. Record deviations.
- [ ] **SAGE guardrail compliance.** Link actual validation and enforcement
      results, including failed/unknown checks, repairs, and explicitly approved
      exceptions. An untested boundary cannot be marked passed.
- [ ] **Durable handoff/reconstruction.** Persist implementation, status, semantic
      evidence, decisions, unresolved obligations, and next action through governed
      Git/GitHub references so a fresh authorized participant can continue
      without earlier chat, memory, machine state, or sequential role history.

**Independent closeout:** A qualified reviewer/auditor must compare each claim
to its cited authoritative evidence and record the verdict. Missing evidence is
**unverified**, a demonstrated violation is **failed**, and an unsupported
`ALLOW` from an LLM is not acceptance. Work remains incomplete until all
applicable issue-specific criteria and the five questions are verified.

**Architect override:** Only an independently attributable Architect decision
may change this contract or its governing Project/RACI requirements. Record its
scope, rationale, affected revision, and resulting obligations in the
Project/Git authority. No SAGE participant, review label, or approval-like
Project status can grant itself this authority. External nondelegable
requirements are not overridden by Project authority.

## Machine-consumable completion evidence

An execution may present a JSON receipt to:

```bash
python3 scripts/sage/sage-project-raci-dod-guardrail.py --receipt path/to/receipt.json
```

Required top-level receipt fields are `project_contract`, `raci`, `execution`,
`guardrails`, `continuation`, `independent_audit`, and `architect_overrides`.
Use evidence references in each field; do not embed credentials or prior chat.
The validator verifies structure and disallows a structurally unsupported
completion claim. **It cannot independently establish that the external
GitHub references or the audit verdict are truthful.** The actual auditor must
read the cited GitHub/Git records. No receipt may grant new authority.

The default repository guardrail checks publication of this contract in the
entry points; it does not claim every open work item has completed its DoD.

## Fresh-participant acceptance scenario

Given a participant without the previous participant's conversation, local
state, or credentials, when assigned an open Project work item, they must be
able to retrieve its live contract, obtain their RACI assignment, execute or
identify a genuine authority blocker, and reconstruct prior progress from
referenced Git/GitHub evidence. An independent auditor must be able to verify
the five questions without consulting an LLM's memory. Conflicting conversation
instructions are not governing authority; an explicit new Architect decision
must be recorded in the authoritative contract before its execution scope
changes.
