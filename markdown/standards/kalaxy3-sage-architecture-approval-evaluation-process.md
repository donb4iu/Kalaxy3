# SAGE LLM architecture-approval evaluation

## Purpose

Before a material architecture or objective-path decision reaches Architect
approval, the LLM receives the governed decision surface and independently
evaluates architectural fitness. The purpose is to exercise the breadth of the
LLM's potential influence before commitment, not merely to verify a design that
has already been selected.

The control model is:

**Architect intent -> SAGE experience/evidence/context -> independent LLM
architecture evaluation -> SAGE reconciliation -> Architect approval ->
delegated implementation -> outcome evidence and learning.**

SAGE should provide relevant accumulated experience and evidence when available; absence of relevant experience is represented as unknown rather than silently narrowing the solution space.

The LLM is advisory. It cannot approve architecture, expand authority, mutate
the repository, or authorize migration. The Architect remains the approval
authority.

## Framework-guided, not framework-bound

WAR and CAF provide useful aperture. WAR covers operational excellence,
security, reliability, performance efficiency, cost optimization, and
sustainability. CAF covers business, people, governance, platform, security,
and operations.

They are **seeds**, not an exhaustive checklist. The LLM may introduce other
fit-for-purpose lenses when material: human factors, usability, quality
attributes, threat modeling, architecture/technology alternatives, delivery and
recovery, economics, organizational learning, or concerns not yet represented
in SAGE.

Checklist completion is not evidence of architectural fitness. An opaque
aggregate architecture score is prohibited.

## Independent breadth

The evaluator must be free to challenge the proposed representation, component,
platform, engine, ownership boundary, operating model, delivery model, or even
whether the decision surface is solving the right problem. Current SAGE
capabilities and vocabulary do not bound the solution space.

The evaluator explicitly records lenses considered, alternatives or materially
different approaches, material findings with epistemic status, unknowns and
areas it could not competently evaluate, and how the evaluation could influence
the Architect's decision.

SAGE validates provenance, binding, authority, and record shape. It does not
claim the LLM's semantic judgment is true merely because the record validates.

## Delegate implementation; evaluate effects

The evaluation should identify implementation constraints only when they are
material to architectural fitness. It should not micromanage implementation
mechanics that can be delegated within the approved outcome and risk envelope.

The value of the evaluation is assessed later by effects such as risks exposed,
alternatives widened, assumptions challenged, information gained, avoidable
debt, confidence legitimately changed, and evidence from subsequent outcomes.
The evaluation is not rewarded for touching every framework category.

## First enforced consumer

The objective-execution material-path approval is the first enforced consumer.
Its existing planning critic remains useful as a specialized path/ownership
critique, but Architect approval now also requires the broader reusable
architecture-evaluation payload. The exact evaluation is content-bound into the
approval evidence.

Routine implementation-local corrections inside an already approved objective,
authority, scope, constraint, risk, and outcome envelope do not reopen
architecture approval. A true replan or other material architecture decision
does.
