# Kalaxy3 SAGE fresh-role implementation readiness

## Purpose

Fresh/disposable LLM roles are bounded SAGE engineering cognition, not an
authority source. A generated plan, procedure, or code proposal is not evidence
that implementation is understood or ready.

SAGE therefore preserves these distinctions:

- model knowledge or engineering inference is not evidence;
- a proposal is not authority;
- plausibility is not implementation readiness;
- successful generation is not successful engineering;
- assumptions and hypotheses are not facts;
- an unknown is not permission to guess.

## Governed dispositions

Every planning advisory that may lead to implementation carries exactly one
implementation-readiness disposition:

1. `implementation-ready`
   - the role supplies a concrete bounded recipe;
   - validation/proof is explicit;
   - repository/evidence grounding is identified;
   - no blocking unknown or material Architect-owned decision remains.

2. `knowledge-evidence-capability-gap`
   - the objective is understood but faithful implementation is not;
   - the missing knowledge/evidence/capability is explicit;
   - the gap-closing input or capability is explicit;
   - no implementation contribution may be generated.

3. `material-decision-required`
   - multiple credible paths or a material architecture/technology/value/scope/
     authority/trust/cost/risk choice remains;
   - alternatives are preserved for Architect disposition;
   - the fresh role does not select the material choice.

4. `unsupported`
   - the available context cannot support a bounded implementation path;
   - the role stops and records what would be required to make the problem
     tractable.

Only `implementation-ready` may cross the first-candidate generation boundary.

## Epistemic structure

A readiness advisory keeps supplied evidence/repository grounding separate from
model inference, assumptions, dependencies, blocking unknowns, limitations,
validation, and stop conditions. SAGE deterministically validates this shape and
derives the lifecycle status/next boundary from the validated disposition.
The LLM does not self-assert those mechanical lifecycle semantics.

A repository grounding claim must name a real repository file. If a digest is
supplied it must match current repository bytes. Syntactically valid output that
claims nonexistent grounding is rejected.

## Bootstrap provenance

The Action-002 implementation that first installs this capability is a bounded
bootstrap exception: the persistent Architect-facing GPT-5.6 Sol model performs
the implementation-engineer role because the normal first-candidate mechanism
does not yet exist. Its contribution remains advisory engineering work and is
not represented as fresh-isolated provenance. After the capability is accepted,
normal role isolation/qualification applies again.
