# SAGE objective-to-PR inquiry evidence and architecture dashboard

**Classification:** Clarification of existing SAGE architecture, not a new governance workstream.
**Existing anchors:** PR granularity advisory, objective-first planning, prior-art presumption, RFP-style Architect iteration, semantic collection, SPR, Narrator, Observatory, Reviewer/Referee, independent Auditor, Path Critic, and governed PR lifecycle.
**Source baseline reviewed:** Kalaxy3 `main` capture `47124f339cb3a1c163fce7456ecf859eb069d41e` and current-workflow archive provided November 22, 2026.

## Decision and 80/20 requirement

The PR-granularity admission check must establish **that a prior-art inquiry actually occurred and exactly what the semantic collection returned**, not whether the first retrieval was complete or relevant. Imperfect retrieval is a normal, reviewable input to the Architect's iterative reasoning, **not** automatically a failed inquiry.

A model-generated SHA or a model's claim to have queried the collection is not evidence of retrieval. A separately controlled retrieval recorder must attest to the canonical query/response record, collection revision, proposal scope, and identity. A trusted-base check verifies that signature and binding. Until that recorder and key admission exist, the hard gate must fail closed when required; the presentation layer must mark missing/unverified records, rather than silently accepting them.

A check cannot prevent someone from opening a GitHub PR manually. It can refuse PR promotion, and the SAGE-controlled PR creation path can require the attested milestone proposal before submission. The independent Architect break-glass route remains separate and accountable.

## One ordinary workflow, multiple consumers

1. **Candidate milestone:** Persistent LLM describes the work, acceptance criteria, and its best 80/20 path. It asks the semantic collection for relevant prior art.
2. **Evidence capture:** Trusted recorder returns an attested query, bounded search scope, returned refs/results (including zero results), collection revision and exact proposal digest. It does *not* assert that retrieval was correct or exhaustive.
3. **Architect iteration:** The Architect can accept or question the proposal (e.g. “We already build multi-arch images via Actions; check again”). Earlier versions and the inquiry evidence remain linked, not overwritten. A revised proposal and new inquiry receive new digests.
4. **Governed execution:** Existing SAGE RACI consumes the **same evidence thread**, with independent Narrator, Observatory, Reviewer/Referee, Auditor and Path Critic assessments; implementation corrections remain part of the original milestone.
5. **Learning:** Wrong/out-of-scope retrieval becomes an SPR candidate and causal evidence for semantic enrichment. Successful reuse and entirely new scenarios are also recorded and can enrich the semantic collection.
6. **Promotion:** A trusted-base PR check verifies evidence *authenticity and scope*, the established auditor check qualifies the substantive review, and the Architect's exceptional bypass is available through the existing break-glass boundary.

## Architecture dashboard: translate, do not make the Architect speak SAGE

The dashboard's in-progress objective view should answer in plain English:

| Human question | Source/projection | Honest unknown state |
|---|---|---|
| What are we trying to do? | Objective and milestone proposal | No approved milestone linked |
| What did we look up? | Attested semantic inquiry, refs and results | Not recorded / unverified |
| What changed after discussion? | RFP/Architect iteration history | No feedback yet |
| What's done / underway / next / blocked? | Evidence-bound objective state and narrated work | Reported only; not qualified |
| Who has actually reviewed it? | RACI observations and independently qualified receipts | Role invocation is not approval |
| What did we learn? | SPRs, corrections and successful prior-art reuse | Not yet reconciled into semantic collection |
| How much remains? | Acceptance-criterion coverage against the authorized milestone | Unknown until objectively measured |

The dashboard is a **read-only projection**, not a decision authority. Do not invent completion percentages when DoD coverage is not measurable. Present original evidence identifiers in drill-down views when authoritative data is available. The semantic collection's revision is not a freshness guarantee. Do not convert “no results recorded” into “no prior art exists.”

## Implementation boundary in this contribution

- `scripts/ci/sage_semantic_inquiry_gate.py`: standalone, testable verifier for canonical RSA/SHA-256 attested inquiries, bound to objective, milestone, proposed approach, and semantic collection revision. It certifies signature and scope **only**, never relevance, coverage, or approval. **No attester key or signer runtime is installed by this package.**
- `scripts/sage/architecture_helper/pr_work_projection.py`: non-authorizing JSON and standalone HTML projections suitable for a dashboard to consume. It can optionally invoke the signed-inquiry validator, replace claimed retrieval results with the signed response, and label signature status. The HTML example intentionally shows unverified source claims and all outstanding work.
- `examples/pr62-work-thread.json`: a transparent, bounded example based on operator output; **not a signed RACI record**, and not proof that SAGE's semantic retrieval was run for PR #62.
- Tests: signed receipt verification, tamper rejection, proposal revision rejection, absence of fabricated authority, human-readable iteration visibility.

### Before turning on a mandatory rule

Reconcile the actual current `scripts/ci/pr_granularity_advisory.py`, the semantic adapter's live response contract, and the architecture dashboard's ingestion interface. The provided capture contains the trusted-base workflow but not these implementation sources. Bind the independent retrieval controller to the real semantic collection, preserve sign-only custody outside the persistent LLM, and verify a live signed query/response record from a real milestone. Then add the qualified status check to the existing GitHub ruleset; don't prematurely block all PRs with an unprovisioned checker.

Do **not** replace the PR-granularity advisory, add a new planning workflow, grant the persistent LLM signing keys, declare RACI completion from role invocations, or enable enforcement based on these offline tests.
