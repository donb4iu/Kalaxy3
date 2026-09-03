# Human Participation / Experience Intelligence — Next Iteration

## Product conclusion

The Human Participation Workbench should not require a newcomer to understand
SAGE before they can understand what SAGE has helped accomplish or why its
accumulated experience matters.

The next iteration therefore treats the repository as an inspectable network of
governed experience rather than as a set of hand-curated showcase episodes.

All discoverable governed objectives and episodes are browsable in a raw form.
Optional LLM-generated narration may sit above that raw form to translate SAGE
vocabulary into plain language, but narration never becomes canonical episode
identity or evidence.

## Architect intent and role separation

The Architect defines the intended future state, value, constraints,
priorities, trade-offs and consequential approvals.

The Architect is **not** assumed to dictate implementation.

A core product value is that the LLM can widen the solution space by proposing
architecture, alternatives, experiments, critiques and innovations that do not
need to exist in SAGE's current experience or vocabulary.

SAGE then reconciles those proposals against:

- accumulated governed experience;
- current evidence and uncertainty;
- authority boundaries;
- guardrails and safety requirements;
- currently executable capabilities;
- known debt and deferred obligations.

Executors and external systems perform governed work and emit observable
results. Later evidence and causal learning can strengthen, weaken, narrow,
contradict or supersede prior judgments.

## Five peer entry points

The workbench home surface uses peer-level entry points rather than one long
ordered page:

1. **Objectives & experiences — what SAGE has helped accomplish and learn**
2. **Capabilities — what SAGE can help with**
3. **Current objective — what matters now**
4. **Human judgment — where decisions shaped outcomes**
5. **Role interaction — how intent, innovation, governance and execution came together**

These are navigation choices, not a prescribed reading order.

## Role interaction view

Where provenance supports it, each episode should expose:

**Architect intent**
→ **relevant experience surfaced**
→ **LLM innovation / alternatives / critique**
→ **Architect decisions**
→ **SAGE reconciliation and guardrails**
→ **execution / external-system action**
→ **evidence and outcome**
→ **remediation, debt and learning**
→ **expected next-time advantage**

The interaction view is provenance-driven. Missing role attribution is shown as
unknown rather than inferred.

LLM proposals remain visibly distinct from:

- Architect intent;
- SAGE-derived projections;
- demonstrated evidence.

This preserves the value of the LLM as an innovative participant rather than
reducing it to a translator of existing SAGE state.

## Curiosity navigation

Important entities support both questions:

- **Where did this come from?**
- **What did this contribute to?**

The browser exposes explicit upstream and downstream relationships between
objectives, evidence, decisions, lessons, failures, actions, capabilities,
causal insights and other governed records.

Generic textual references are distinguishable from semantically meaningful
relationships. A reference alone must not be mislabeled as causal contribution.

## Optional human narration

Every objective or entity remains inspectable without narration.

Optional narration can add:

- what the item means in plain English;
- what it enables;
- why someone should care;
- concrete accomplishment/context;
- strengths and weaknesses;
- 80/20 trade-offs;
- reusable value created;
- what may transfer to another objective;
- what is expected to be different next time.

Narration is explicitly interpretive. It cannot promote an LLM judgment into
demonstrated evidence.

## Evidence value and contribution history

Evidence should answer not only **what supports this?** but also
**what has this supported?**

The UI should make visible, where repository relationships support it:

- decisions informed;
- objectives or episodes that consumed the evidence;
- causal insights strengthened or weakened;
- controls or actions motivated;
- later episodes that reused it;
- later evidence that superseded, narrowed or contradicted it.

This makes the multiplier effect of producing reusable evidence inspectable.

## Causal learning remains revisitable

Partially supported or incomplete causal insights remain visible as work in
progress. Failing to satisfy stronger acceptance or maturity criteria does not
erase a legitimate provenanced causal contribution.

The browser should show current standing, contribution history, strengthening,
weakening, contradiction and supersession when those relationships are
available.

## Staleness is contextual, not age

Age alone does not make evidence stale.

Current standing is derived only from explicit status or relationships such as
supersession, contradiction, invalidation or recorded staleness/context limits.

Evidence can remain historically valid while being unsafe as proof of current
state.

## Human judgment and downstream consequences

Architect authority does not imply Architect infallibility.

Consequential decisions should be traceable to:

- evidence and uncertainty available at decision time;
- alternatives considered where preserved;
- expected implications;
- observed downstream implications;
- technical, functional, nonfunctional and process debt;
- later evidence that strengthened or weakened the original judgment;
- whether the same choice would still be preferred today.

The UI must distinguish decision quality given then-available evidence from the
eventual outcome.

## Historical effort versus future expected effort

A difficult first path must not be presented as the expected cost of repeating
that path.

The workbench separates:

1. **Observed discovery/remediation effort** — historical failures, corrections,
   interventions and new capability construction.
2. **Reusable value created** — controls, lessons, primitives, evidence
   patterns, causal insights and automation that survive the episode.
3. **Expected repeat effect** — an explicitly predicted/LLM-derived statement
   about what should be easier, safer or faster next time.
4. **Later demonstrated repeat effect** — only when a comparable future episode
   supplies evidence.

Historical path effort remains useful for extrapolating genuinely new
complexity, but already-remediated discovery cost should not simply be copied
into future estimates.

## Learning ingestion / experience bootstrapping

SAGE can benefit from externally sourced learning without treating it as local
truth.

Imported lessons should remain provenanced priors that may later be
strengthened, narrowed, weakened, contradicted or superseded by local evidence.

Kalaxy2 Zero Trust and prior Git-agent experience are examples of the behavior
this future lifecycle should make explicit and inspectable.

## 80/20 boundary for this iteration

This iteration proves:

- generic repository-derived entity/episode browsing;
- peer-level navigation;
- bidirectional explicit relationships;
- raw governed views for all discovered entities;
- optional narration metadata;
- role-interaction visibility from explicit provenance;
- LLM innovation as a distinct contribution class;
- explicit current standing;
- contribution/reuse visibility where relationships exist;
- scalable search/filtering;
- separation of historical effort from future-repeat interpretation.

It does **not** introduce:

- a live graph database;
- GraphRAG or another retrieval engine;
- runtime LLM invocation;
- automated evidence ingestion;
- workflow or approval mutation;
- inferred causal links unsupported by repository relationships;
- inferred role attribution unsupported by repository provenance;
- opaque aggregate maturity or value scores.
