# SAGE Human Participation Introspection-Contract Audit

**Purpose:** determine what SAGE can truthfully project before UI work.

## Interpretation

`structured_explicit` means a scanned JSON authority/schema has an explicit matching field. `documented_context` means the concept appears in audited material but this audit does not prove a queryable structured representation. `absent_in_scanned_authority` means neither was found. Context is not promoted to capability.

## Coverage matrix

| Concept | Current support |
|---|---|
| stakeholder_concerns | documented_context |
| strategic_objectives | structured_explicit |
| participant_authority | structured_explicit |
| participant_contribution | documented_context |
| current_target_capability | structured_explicit |
| evidence_provenance | structured_explicit |
| prediction_hypothesis | structured_explicit |
| uncertainty_unknown | structured_explicit |
| contradiction_conflict | structured_explicit |
| known_omission_deferral | structured_explicit |
| tactical_opportunity | structured_explicit |
| effort_reversibility | structured_explicit |
| strategic_reach_leverage | documented_context |
| information_gain | documented_context |
| objective_episode_replay | structured_explicit |
| evidence_availability | documented_context |

## Support details

### stakeholder_concerns

**Observed status:** `documented_context`
- `sage-change-authority.json:860: "wider participation",`
- `sage-improvement-actions.json:880: "Human participant roles include stakeholder/sponsor/product owner, architect/engineer, operator, and reviewer/approver; the same human may `
- `sage-improvement-actions.json:884: "The LLM is a first-class contributor of external/world knowledge, state-of-practice patterns, alternatives, critique, risk identification, `
- `sage-improvement-actions.json:894: "Beyond mandatory gates, SAGE preserves a provenance-backed multidimensional outcome vector against human-owned intent, requirements, constr`

### strategic_objectives

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::policy.mission`
- `sage-thin-slice.json::measures[0].target`
- `sage-thin-slice.json::measures[1].target`
- `sage-thin-slice.json::measures[2].target`

### participant_authority

**Observed status:** `structured_explicit`
- `markdown/evidence/catalog.json::records[0].owner`
- `markdown/evidence/catalog.json::records[10].owner`
- `markdown/evidence/catalog.json::records[11].owner`
- `markdown/evidence/catalog.json::records[12].owner`

### participant_contribution

**Observed status:** `documented_context`
- `sage-thin-slice.json:50: "sage_contribution": "Preserve the literal objective and connect it to repository, observability, storage, validation, and evidence authorit`
- `sage-thin-slice.json:51: "human_contribution": "The operator defined the desired outcome and retained authority over activation and Git boundaries.",`
- `sage-thin-slice.json:61: "sage_contribution": "Expose the authority gap instead of treating successful deployment as sufficient evidence.",`
- `sage-thin-slice.json:62: "human_contribution": "The operator accepted the pause and required repository-owned guardrails before proceeding.",`

### current_target_capability

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::picture.capabilities`
- `sage-thin-slice.json::measures[0].target`
- `sage-thin-slice.json::measures[1].target`
- `sage-thin-slice.json::measures[2].target`

### evidence_provenance

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::picture.capabilities[0].assertions[0].evidence_refs`
- `sage-capability-intelligence.json::picture.capabilities[0].assertions[1].evidence_refs`
- `sage-capability-intelligence.json::picture.capabilities[0].current_dimensions.cost-efficiency.evidence_refs`
- `sage-capability-intelligence.json::picture.capabilities[0].current_dimensions.evidence-confidence.evidence_refs`

### prediction_hypothesis

**Observed status:** `structured_explicit`
- `markdown/standards/sage-thin-slice-schema-v1.0.json::properties.alternatives`
- `sage-capability-intelligence.json::decision_cycle.branches[0].prediction`
- `sage-capability-intelligence.json::decision_cycle.branches[1].prediction`
- `sage-capability-intelligence.json::decision_cycle.branches[2].prediction`

### uncertainty_unknown

**Observed status:** `structured_explicit`
- `markdown/evidence/catalog.json::records[0].confidence`
- `markdown/evidence/catalog.json::records[10].confidence`
- `markdown/evidence/catalog.json::records[11].confidence`
- `markdown/evidence/catalog.json::records[12].confidence`

### contradiction_conflict

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::picture.conflicts`

### known_omission_deferral

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::federation.authorities[0].limitations`
- `sage-capability-intelligence.json::federation.authorities[10].limitations`
- `sage-capability-intelligence.json::federation.authorities[11].limitations`
- `sage-capability-intelligence.json::federation.authorities[1].limitations`

### tactical_opportunity

**Observed status:** `structured_explicit`
- `sage-continuous-improvement-policy.json::registries.improvement_actions`

### effort_reversibility

**Observed status:** `structured_explicit`
- `sage-capability-intelligence.json::decision_cycle.branches[0].prediction.effort`
- `sage-capability-intelligence.json::decision_cycle.branches[0].prediction.reversibility`
- `sage-capability-intelligence.json::decision_cycle.branches[1].prediction.effort`
- `sage-capability-intelligence.json::decision_cycle.branches[1].prediction.reversibility`

### strategic_reach_leverage

**Observed status:** `documented_context`
- `sage-improvement-actions.json:894: "Beyond mandatory gates, SAGE preserves a provenance-backed multidimensional outcome vector against human-owned intent, requirements, constr`
- `sage-improvement-actions.json:911: "Measure effectiveness, efficiency, correctness/quality, reliability, time to validated outcome, human effort, cost, rework, recurrence, aut`
- `sage-improvement-actions.json:1016: "Beyond mandatory gates, SAGE preserves a provenance-backed multidimensional outcome vector against human-owned intent, requirements, constr`
- `sage-improvement-actions.json:1033: "Measure effectiveness, efficiency, correctness/quality, reliability, time to validated outcome, human effort, cost, rework, recurrence, aut`

### information_gain

**Observed status:** `documented_context`
- `markdown/architecture/kalaxy3-sage-capability-intelligence-human-participation-epic.md:49: - information gain.`
- `markdown/architecture/kalaxy3-sage-capability-intelligence-human-participation-epic.md:112: - information gain.`

### objective_episode_replay

**Observed status:** `structured_explicit`
- `sage-improvement-actions.json::actions[0].history`
- `sage-improvement-actions.json::actions[10].history`
- `sage-improvement-actions.json::actions[11].history`
- `sage-improvement-actions.json::actions[12].history`

### evidence_availability

**Observed status:** `documented_context`
- `sage-improvement-actions.json:908: "Track workflow/decision observability coverage separately from infrastructure/application observability and measure missing instrumentation`
- `sage-improvement-actions.json:1030: "Track workflow/decision observability coverage separately from infrastructure/application observability and measure missing instrumentation`
- `markdown/architecture/kalaxy3-sage-capability-intelligence-human-participation-epic.md:85: Unavailable evidence remains unavailable.`

## Preliminary disposition

This is source coverage, not an Architect priority decision.

- **Candidate reuse:** strategic_objectives, participant_authority, current_target_capability, evidence_provenance, prediction_hypothesis, uncertainty_unknown, contradiction_conflict, known_omission_deferral, tactical_opportunity, effort_reversibility, objective_episode_replay
- **Needs normalization/query projection:** stakeholder_concerns, participant_contribution, strategic_reach_leverage, information_gain, evidence_availability
- **Candidate first-class gaps:** none

## Epic provenance/catalog test

Current catalog projection(s) mentioning the Architect epic:

```json
{"completed_at": "not-captured", "confidence": "low", "evidence_id": "LEGACY-K3-D2AEC96351", "metadata_source": "inferred", "migration_status": "not-started", "nav_order": 500, "nav_section": "architecture", "nav_title": "Human Participation Adapter \u2014 Architect Epic", "owner": "not-captured", "primary_subject": "SAGE Human Participation Adapter", "record_class": "legacy-evidence", "schema_version": "not-applicable", "source_path": "markdown/architecture/kalaxy3-sage-capability-intelligence-human-participation-epic.md", "status": "historical", "summary": "Status: Architect-owned epic; implementation not yet started Product intent: improve stakeholder participation and tactical attention allocation Execution model: existing governed SAGE objective-execution methodology remains authoritative Architecture-explorer status: separate technical due-diligence deliverable, not the first product priority", "tags": [], "title": "SAGE Human Participation Adapter \u2014 Architect Epic", "valid_as_of": "not-captured"}
```

## Runtime evidence availability

Local state exposes 3 state families.

No `objective-episode*.json` records were found locally.

## Proposed minimum read contract

**Status: proposal, not current capability.**

```json
{
  "query_context": [
    "perspective",
    "stakeholder_concerns",
    "strategic_objectives"
  ],
  "attention_items": [
    "claim_refs",
    "why_now",
    "affected_concerns",
    "uncertainty"
  ],
  "human_decisions": [
    "decision",
    "authority",
    "tradeoffs",
    "evidence_refs"
  ],
  "tactical_opportunities": [
    "expected_benefit",
    "strategic_reach",
    "evidence_strength",
    "uncertainty",
    "effort",
    "reversibility",
    "dependencies",
    "information_gain"
  ],
  "claims": [
    "epistemic_status",
    "source_type",
    "source_ref",
    "confidence",
    "availability"
  ],
  "episodes": [
    "participants",
    "authority_transitions",
    "actual_path",
    "outcomes",
    "learning"
  ]
}
```

The contract must preserve source/evidence identity and cannot allow LLM interpretation to upgrade epistemic status.

## Architect review / stop condition

Before UI implementation decide:

1. Which structured concepts can be reused unchanged?
2. Which contextual concepts can be derived deterministically?
3. Which concepts need minimal first-class representation?
4. Is provenance/type distinction strong enough for human comprehension?
5. Which real episode has sufficient available evidence for first replay?
6. Does the original M/L 80/20 implementation estimate still hold?

Do not repair every discovered SAGE deficiency as part of this audit.
