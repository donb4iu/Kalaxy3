# Kalaxy3 SAGE Human Participation Workbench Process

## Purpose

The Human Participation Workbench is a stakeholder-first read-only adapter over
persisted SAGE experience and intent projections.

Its first proof answers three questions:

1. What can SAGE help me with?
2. Given this objective, what matters?
3. Where is my judgment valuable?

The product hierarchy is stakeholder objective and value first, then
experience-backed guidance, uncertainty, new possibilities, human decisions,
and evidence drill-down.

## Read-only boundary

The initial workbench does not initiate objectives, approve work, mutate
workflows, invoke runtime infrastructure, call external APIs, or alter evidence.

Its generated state must declare `interaction_mode: read_only`.

The browser assets are static and must not contain network calls, forms, or
mutation controls. The workbench can therefore be reviewed independently of a
cluster or runtime LLM invocation path.

## Epistemic presentation

The workbench visibly distinguishes:

- **Evidence** — persisted source material;
- **SAGE-derived** — deterministic projections or validation;
- **LLM-derived** — semantic interpretation grounded in cited evidence;
- **LLM-proposed** — new possibilities that may extend beyond experience;
- **Architect** — authority for objectives, trade-offs, transfer, and action.

The UI must not collapse these classes into a single confidence or priority
score.

## Evidence drill-down

Every LLM-derived experience theme and intent-applicability judgment presented
to the user must retain its cited evidence.

The UI may summarize that evidence for usability but cannot replace or promote
the underlying evidence identity.

## Unknowns

Unknown or executor-unavailable experience remains visible. The UI must not fill
missing current runtime evidence by inference from historical experience.

## Static publication path

The proof is implemented as dependency-free HTML, CSS, JavaScript, and generated
read-only state under the existing MkDocs/static publication surface.

This is intentionally an 80/20 product slice. A later live workbench may add a
runtime LLM interaction path or objective initiation only after those authority
and evidence boundaries are separately proven.

## Generic experience intelligence

The workbench must not depend on a curated list of showcase episodes.

A repository-derived experience graph supplies raw browsable entities and
explicit identifier relationships for all discovered governed records within
the bounded machine-readable source set.

Optional human narration is augmentation only. If no narration exists, the raw
governed entity remains fully inspectable.

### Role interaction

The Architect defines intent/end state, constraints and consequential choices;
the LLM may innovate beyond prior SAGE experience; SAGE reconciles proposals
against evidence, experience, authority, guardrails and executable capability;
executors/external systems perform work; later learning records consequences.

The browser may display role interaction only from explicit provenance.
Missing attribution remains unknown.

LLM innovation is displayed separately from prior experience and Architect
intent so the product does not collapse innovation into current SAGE
capabilities.

### Bidirectional navigation

Every discovered relationship is navigable in both directions.

Semantic relationships are kept distinct from generic identifier references. A
generic reference cannot be presented as evidence of causal contribution.

### Current standing

Age alone cannot make evidence stale.

Standing changes only when explicit status or relationships record
supersession, contradiction, invalidation, staleness or context limitation.

### Historical effort and repeat cost

Linked failures, lessons, evidence and actions may be displayed as historical
path signals.

These counts are never future-cost estimates.

Any statement that a future comparable path should be easier, safer or faster
is interpretive/predictive until a later comparable episode demonstrates the
effect.

### Optional narration

Narration metadata may explain what an entity means, what it enables, why it
matters, historical effort context, reusable value created, expected repeat
effect and limits.

The expected repeat effect must retain an interpretive or proposed epistemic
status rather than being rendered as demonstrated evidence.

### Projection-source and relationship safety

The experience graph must not consume its own generated Human Participation
output or unrelated policy/configuration files as accumulated experience.
Relationship semantics come from explicit leaf-field contracts. Ordinary
`contexts` membership means applicability, not evidence staleness. When a
specific governed identity and generic `id` refer to the same record, the
specific identity wins.
