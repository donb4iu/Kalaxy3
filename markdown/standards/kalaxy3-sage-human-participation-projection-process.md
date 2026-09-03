# Kalaxy3 SAGE Human Participation Projection Process

## Purpose

Provide a read-only adapter that converts existing governed SAGE state into a
stakeholder-facing decision surface without creating new workflow authority.

The first slice answers exactly three questions:

1. **What should I care about?**
2. **Where do you need me?**
3. **Where should we spend the next unit of effort?**

## Authority and epistemic rules

The projection is not an authority source. It must preserve links to the source
state from which each material item was projected.

A projection must not:

- convert contextual support into demonstrated capability;
- convert an LLM proposal into established SAGE state;
- hide unknown, unavailable, contradicted, or unresolved evidence;
- infer runtime proof from deterministic validation;
- infer general maturity from one successful episode;
- replace Architect authority with a scalar priority/ranking score.

The Architect retains responsibility for stakeholder values, consequential
trade-offs, and objective selection.

## 80/20 proof

The first proof projects the completed human-participation introspection audit.

It intentionally does not implement:

- a browser UI;
- objective mutation;
- approval controls;
- workflow execution;
- runtime mutation;
- a graph database;
- a generalized portfolio optimizer.

The purpose is to determine whether the existing SAGE model can support a
truthful and useful human-participation experience before those investments.

## Advancement criterion

Advance to a UI slice only when:

- all three stakeholder questions have useful answers;
- material items expose epistemic status and source provenance;
- context-only concepts remain visibly context-only;
- unavailable evidence remains unavailable;
- human decision boundaries remain Architect-owned;
- no opaque aggregate priority score is required to make the projection useful.

If the projection remains technically correct but incomprehensible to a
knowledgeable stakeholder, treat that as failure of the read model rather than
as a presentation-only defect.

## Experience-informed help does not bound innovation

The Human Participation Adapter must not treat absence of prior SAGE experience as
a reason that SAGE cannot help.

Two entry modes are supported conceptually:

1. **Experience inventory** — "What are you prepared to help with?"
2. **Intent-relative analysis** — "Given this intent, what relevant experience
   exists and what new possibilities should be considered?"

Repository evidence retrieval establishes evidence candidates only. A retrieval
match does not by itself establish competence, transferability, or applicability.

When relevant experience exists, SAGE preserves and presents it. When experience
is partial, analogous, or absent, the LLM may still propose novel requirements,
architectures, experiments, or solution paths from broader knowledge. Those
proposals remain explicitly `llm_proposed` until evidence or Architect authority
changes their status.

The operating contract is:

**experience informs -> LLM innovates -> SAGE reconciles/proves what it can ->
Architect decides**

SAGE's evidenced experience envelope improves its priors; it is not a hard
solution-space boundary.

## Canonical experience retrieval and seed contract

Human-participation experience profiles must provide a complete canonical
retrieval request. Projection-local keyword `terms` are not a substitute for
the repository-owned evidence-retrieval path.

Each profile declares whether it is being used for:

- `experience_inventory` — evidence that SAGE has accumulated relevant
  experience in a bounded area; or
- `intent_transfer` — evidence that may transfer to the current stakeholder
  intent and therefore remains subject to revalidation.

Relationship metadata such as `direct`, `analogous`, `weakly_related`, and
`contradictory` wraps canonical retrieval results. It must not be inserted into
the canonical result object or change its immutable retrieval basis.

A recovery that restores an older checkpoint must migrate the complete input
contract atomically. Adding only new fields while leaving obsolete query fields
is an invalid partial migration and must fail before retrieval.

## Semantic experience synthesis

Canonical retrieval and semantic judgment have different responsibilities.

SAGE first supplies a bounded governed experience corpus. The corpus may combine
a broad canonical retrieval snapshot with canonical evidence already surfaced
by intent-relative or experience-inventory projections. The corpus must declare
that it is bounded and must not claim exhaustiveness.

An LLM may then:

- derive human-meaningful experience themes from that corpus;
- judge whether retrieved experience is directly relevant, analogous, weak or
  uncertain, contradictory, or provides no useful support for a current intent;
- explain the judgment and identify assumptions, unknowns, and implications;
- propose innovations that are not supported by prior experience.

Every material LLM-derived experience or applicability claim must cite governed
evidence actually present in the bounded corpus. Intent applicability citations
must also have been retrieved for that intent area.

SAGE validates citation resolution, evidence identity, allowed epistemic status,
and authority boundaries. SAGE does **not** claim that deterministic validation
makes an LLM semantic judgment true. LLM-derived themes and applicability
judgments remain `llm_derived`; novel alternatives remain `llm_proposed`.

Absence of direct experience is not a refusal condition. The LLM may innovate
beyond SAGE's experience, and the Architect decides whether a historical lesson,
analogy, experiment, or novel proposal becomes part of the objective path.
