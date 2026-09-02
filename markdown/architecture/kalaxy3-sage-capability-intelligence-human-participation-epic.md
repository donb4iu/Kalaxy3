# SAGE Human Participation Adapter — Architect Epic

**Status:** Architect-owned epic; implementation not yet started  
**Product intent:** improve stakeholder participation and tactical attention allocation  
**Execution model:** existing governed SAGE objective-execution methodology remains authoritative  
**Architecture-explorer status:** separate technical due-diligence deliverable, not the first product priority

## Architect objective

Make SAGE materially better at helping human stakeholders participate in complex,
governed objectives.

Given a range of stakeholder concerns and strategic objectives, the experience should
help a human understand:

- what currently deserves attention;
- where human judgment is actually required;
- what SAGE can demonstrate versus what the LLM predicts or hypothesizes;
- what remains unknown, contradicted, or unresolved;
- which tactical investments may advance multiple stakeholder concerns;
- when buying information is more valuable than implementing a presumed solution;
- why an Architect-selected objective is worth pursuing now.

The first product value is **better human participation and decision quality**, not a
pedantic explanation of SAGE internals.

## Coupled operating loops

### Stakeholder / intent loop

Widen the aperture across stakeholder concerns and strategic objectives.

Expose:

- desired outcomes and constraints;
- competing and reinforcing stakeholder concerns;
- evidenced current capability;
- predictions and hypotheses;
- observed gaps;
- unknowns and unresolved areas;
- trade-offs;
- tactical opportunities;
- strategic reach;
- expected benefit;
- confidence;
- effort;
- reversibility;
- dependencies;
- information gain.

The Architect remains authoritative for values, priorities, consequential trade-offs,
and objective selection.

### Objective-execution loop

Once the Architect selects an objective, continue to use the existing governed
development methodology to understand, plan, approve, execute, validate, integrate,
observe, and learn.

The Human Participation Adapter is a client/vector into that lifecycle, not another
workflow engine.

Execution evidence feeds back into the stakeholder / intent loop.

## Epistemic contract

The experience must never upgrade an unsupported statement into a demonstrated fact.

Material conclusions must distinguish at least:

- **demonstrated** — supported by actual evidence;
- **derived** — deterministic projection from authoritative evidence/state;
- **LLM-predicted** — proposed requirement or consequence;
- **hypothesized** — plausible but weakly supported;
- **contradicted** — evidence conflicts with the statement;
- **unknown** — insufficient investigation/evidence;
- **unresolved** — investigation has not distinguished plausible explanations;
- **outside current competence** — no credible current path;
- **known omission / deferred** — intentionally not implemented now.

An LLM proposal is not a SAGE capability.
A capability definition is not proof of successful operation.
A deterministic test is not runtime proof.
One successful episode is not proof of generality.
Unavailable evidence remains unavailable.

## 80/20 product slice

Prove three human-value moments before building a broad SAGE UI.

### 1. What should I care about?

Starting from stakeholder concerns / strategic objectives, show the small number of
material issues currently deserving attention and why.

### 2. Where do you need me?

Show decisions that require human judgment, why SAGE cannot legitimately decide them,
the relevant trade-offs, and what evidence/uncertainty surrounds the decision.

### 3. Where should we spend the next unit of effort?

Compare a small number of tactical opportunities using:

- stakeholder/strategic reach;
- expected benefit;
- evidence strength;
- uncertainty;
- implementation effort;
- reversibility;
- dependencies;
- information gain.

Do not collapse this into an opaque composite priority score.

## Supporting experience

For at least one real objective, allow replay sufficient to show how human decisions
flowed into governed execution and how outcomes changed later understanding.

The initial replay candidate is the recent objective-execution / observed-state
recovery episode because it includes:

- Architect intent and authority;
- LLM reasoning;
- implementation and validation;
- an incorrect workflow assumption;
- independently advanced GitHub state;
- correction without replaying a satisfied mutation;
- human authority boundaries;
- deterministic verification;
- promotion and closeout;
- causal learning.

Replay exists to support stakeholder comprehension and trust, not to make architecture
explanation the primary product.

## Human-comprehension requirement

A knowledgeable stakeholder unfamiliar with Kalaxy3/SAGE should be able to answer:

1. What outcomes/concerns are being optimized?
2. What currently deserves my attention?
3. Where does SAGE need human judgment, and why?
4. What is known versus predicted, hypothesized, unknown, or unresolved?
5. What evidence supports the important conclusions?
6. What tactical choices exist and which stakeholder concerns do they affect?
7. Why might an experiment/information-gathering step be preferable to implementation?
8. What objective was selected, by whom, and why?
9. What changed after execution and learning?

If the slice is technically complete but those questions remain opaque, the slice fails.

## First prerequisite: introspection-contract audit

Do not begin UI implementation first.

Determine whether current authoritative SAGE information can project:

**stakeholder concern -> strategic objective -> evidenced capability ->
prediction/gap/unknown -> tactical opportunity -> Architect decision ->
objective episode -> outcome/learning**

without inventing a second authority model.

Audit existing:

- capability intelligence;
- mission / target / current state;
- participant authority;
- causal evidence;
- objective episodes;
- capability gaps;
- deferred limitations;
- outcome metrics;
- evidence retrieval;
- path critique and learning.

Identify only the minimum missing first-class concepts required for the 80/20 slice.

The audit must explicitly test whether the model is understandable to a human, not
merely structurally complete.

## Initial technology hypothesis — not yet an implementation decision

If the audit supports it, the likely 80/20 implementation is:

- Python 3.12 typed introspection/query library;
- narrow FastAPI + Pydantic read surface;
- React + TypeScript + Vite client;
- simple cards/tables/timelines/decision surfaces;
- no graph database initially;
- no new canonical UI-owned state;
- repository/runtime authorities remain authoritative;
- rebuildable provenance-bound projections/caches only;
- read-only/replay first;
- no UI-driven mutation/approval/execution initially;
- no cluster-hosting prerequisite.

Technology may change if the introspection audit finds a materially better fit.

## Explicitly deferred

- making the UI a new workflow engine;
- replacing the existing development methodology;
- generalized portfolio optimization;
- arbitrary-domain ontology;
- broad architecture explorer;
- investor technical due-diligence architecture browser;
- UI-driven approvals/mutation;
- cluster hosting;
- generalized graph database;
- live event streaming unless proven necessary;
- solving every SAGE omission before delivering stakeholder value.

## Separate due-diligence deliverable

A rigorous SAGE architecture explorer remains valuable for technical diligence:

- participant roles and authority;
- lifecycle semantics;
- guardrails;
- evidence model;
- maturity;
- failure/recovery behavior;
- architectural strengths/weaknesses;
- intentional non-goals.

It is not the first product slice unless evidence shows that architectural opacity is
itself blocking stakeholder participation.

The product sequence is:

**stakeholder value -> inspectable reasoning/evidence -> technical due diligence**

rather than architecture explanation first.

## Success criteria for the epic's first slice

The 80/20 slice succeeds when one unfamiliar stakeholder can use it to:

- identify material stakeholder concerns around a real objective;
- identify at least one consequential human decision and understand why it is human;
- distinguish demonstrated facts from LLM predictions and unresolved uncertainty;
- compare two or three tactical investments without an invented opaque score;
- identify when information gathering has higher expected value than implementation;
- trace material claims to supporting evidence or explicit absence of evidence;
- understand how one real objective's execution changed SAGE's later capability
  intelligence;
- do all of this without requiring an LLM to reconstruct raw SAGE artifacts for them.

## Sizing hypothesis

- introspection-contract audit: **S**, roughly 0.5–1.5 focused days;
- first useful human-participation slice: **M/L**, roughly 4–7 focused engineering days;
- likely elapsed governed-development time: roughly one to two calendar weeks.

These are planning estimates, not commitments.

## Resume rule

When this epic is resumed:

1. Start from this Architect objective, not from a preferred UI implementation.
2. Run the introspection-contract audit first.
3. Do not create a new authority or lifecycle model merely for presentation.
4. Treat stakeholder comprehension and decision usefulness as acceptance requirements.
5. Fail visibly on unsupported capability/maturity claims.
6. Keep architecture due diligence separate unless it materially advances stakeholder
   participation.
7. Let evidence determine whether the workbench eventually becomes the primary human
   SAGE experience.
