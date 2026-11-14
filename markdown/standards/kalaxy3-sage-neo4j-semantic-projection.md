# Issue #50 — Neo4j semantic query projection (engineering candidate)

This is a bounded **candidate implementation**, not an approved semantic ontology, an autonomous planner, or a new SAGE authority store. The authoritative engineering work contract is [Kalaxy3 Issue #50](https://github.com/donb4iu/Kalaxy3/issues/50). Architect approval for implementation does not authorize production deployment, promotion to `main`, or changes to Architect-owned scope.

## Contracts and data boundaries

- `scripts/sage/sage_neo4j_inventory.py`: read-only pinned Git-tree inventory; identifies **every** tracked Git object and SHA-256 digests of its committed bytes. Reads only metadata into Neo4j, never source bodies, credentials or evidence text. Unreadable/binary sources remain counted. Rebuild uses exact commit revision.
- `sage-semantic-concepts.json`: existing SAGE concept vocabulary; concepts with no evidence remain independent nodes. Path aliases produce **unverified candidates**, not accepted semantic facts.
- `scripts/sage/sage_neo4j_lifecycle.py`: exact source count and reverse-relationship checks, scoped evidence-presence state, bounded model revision repair and externally verified activation policy interface.
- `scripts/sage/sage_neo4j_projection.py`: version-scoped Neo4j graph projection with readback and unique keys. Does not implement `activate`, `publish`, `promote`, merge or production deployment. `SageProjection` remains `candidate`.
- `scripts/sage/sage-neo4j-projection.py`: explicit local-only Neo4j integration CLI. Never accepts remote Bolt servers in this first slice.

**Source authority** remains governed Git and externally authoritative systems. A Neo4j graph is a disposable query view. The Git parent and evidence source revision are included in the projection identity. Even a successful matching query is not evidence-maturity adjudication.

## Execution (isolated engineering branch)

```bash
python3 -m unittest discover -s scripts/sage -p test_sage_neo4j.py -v
```

For isolated local Neo4j integration testing, install the pinned official `neo4j` driver from `requirements-sage-neo4j.txt` in a separate venv. Supply local `SAGE_NEO4J_PASSWORD` and a loopback Bolt endpoint:

```bash
python3 scripts/sage/sage-neo4j-projection.py \
  --repo . --out /tmp/sage-issue50-neo4j-evidence \
  --require-integration --concept storage
```

No live source content is copied into Neo4j. Query output only includes source paths and candidate status. Access to the local projection still requires a protected endpoint and source-level authorization before shared deployment.

## Acceptance ledger — NOT 9/9

| DoD | Status in this contribution | Remaining work before objective acceptance |
|---|---|---|
| 01 — Lossless inventory | Partial: full committed Git-tree identity and per-blob hashes | Reconcile historical 79 anchors, external evidence, independent full-coverage enumerator and current source universe |
| 02 — Semantic breadth | Partial: existing concept vocabulary and untrusted path candidates | Full corpus concept accounting, cross-cutting obligation applicability and independently reconciled mappings |
| 03 — Graph fidelity | Partial: version-scoped concept and evidence nodes, related edges | Historical solution/obligation/condition graph fidelity and cross-revision lineage |
| 04 — Evidence presence | Partial: distinguish candidate from qualified absence | Complete scoped qualification and zero-evidence assertions against independent benchmarks |
| 05 — Semantic matching | Partial: path alias candidates, exact graph readback | Contextual/paraphrase semantic matching and complete accepted bidirectional links |
| 06 — Recall benchmarks | Not complete | Independent concept/obligation corpus and negative precision/recall evaluation |
| 07 — Rebuild | Partial: exact version identity and post-write count checks | Full graph-digest equivalence, robust failed-build isolation and reconstruction comparison |
| 08 — Development/promotion synchronization | Partial: version-scoped candidate avoids active pointer | Integrate with native SAGE promotion, replay source add/change/delete and drift recovery |
| 09 — Break-glass evolution | Partial: bounded repair validation with approved changed paths | Governed end-to-end patch, RACI tests, promotion and post-activation readback |

The graph being created is only a **candidate**. No code here is allowed to declare objective success, activate a promoted graph, or bypass existing SAGE approval. The feature branch / draft PR is an engineering contribution subject to independent review and subsequent completion of remaining DoD.

## Deferred work and explicit risks

A feature-complete ontology, stand-alone vector database, Neo4j HA, and production K3s deployment remain deferred. This slice does **not** establish semantic recall from free-form human paraphrases, and Neo4j Community cannot independently enforce per-evidence read authorization for a multi-tenant shared endpoint. Therefore the first test endpoint is bound to loopback and should not publish raw evidence. Evidence classification and access controls must be qualified before any shared deployment.

Python dependencies for this slice (copyable `requirements.txt`):

```text
neo4j==6.4.1
```


<!-- SAGE-ISSUE50-SEMANTIC-INTENT-20261111 -->

## Architectural continuity: objective-scoped semantic evidence retrieval

**Status:** Clarification of the already-approved Issue #50 intent. This is not a new
objective, subsystem, acceptance gate, authority grant, or deployment authorization.

### Institutional knowledge and temporal intent

SAGE's governed evidence corpus preserves complete, detailed, functional engineering
knowledge independently of any LLM, conversation, or engineering team. It includes
objectives and requirements, implementations and lifecycle state, alternatives
considered or deferred, their original decision rationale, assumptions, estimates,
measurements, corrections, outcomes, and source/authority provenance.

Preserve the historical conditions and intent of decisions, including what was known
at the time. Subsequent developments add linked evidence; they do not silently
rewrite earlier decisions. This parallels the established RFP architecture's use of
successive source-document iterations navigated through a semantic question corpus.

### Data model, semantic retrieval, and reasoning are distinct

- The governed evidence corpus is the durable source of SAGE institutional knowledge.
- The rebuildable Neo4j projection represents evidence identities, concepts, typed
  relationships, applicability, provenance, and temporal/causal connections.
- Semantic matching maps an Architect-owned objective to candidate concept anchors.
- Relationship-aware retrieval assembles an objective-specific evidence subgraph,
  rather than traversing or sending the entire corpus on every objective.
- Architect and collaborating LLMs interpret, correlate, critique, compare, infer,
  and decide using retrieved evidence within established role/authority boundaries.

Neo4j is a query projection, not canonical authority or a reasoning engine. The
semantic retrieval mechanism may improve as models and technology evolve without
changing the enduring evidence or granting the projection decision authority.

### Objective-related evidence and guardrails

An in-scope Kalaxy3 implementation objective should retrieve existing capabilities,
prior art, alternatives, unresolved questions, operational measurements, and the
applicable governed implementation baseline. This includes observability, net
operational cost, security, lifecycle, and recovery obligations via documented
applicability relationships, including scoped always-applicable baseline links.

Guardrails are implementation requirements/features to fulfill, not semantic
inhibitors. Retrieval is an evidence helper, never a new approval, failure, or scope
gate. Existing deterministic governance enforcement and Architect authority remain
unchanged at their established boundaries.

Established, candidate, and not-yet-evaluated relationships remain distinguishable.
Lack of an existing semantic mapping is not evidence that the source is irrelevant or
that an implementation is missing. Broader source discovery must remain available
when the mapped graph does not cover the objective. Source identity, Git lineage,
main-versus-feature state, supporting/contradictory evidence, uncertainty, and
historical context accompany retrieved findings.

### Cross-episode learning without functional fixedness

Retrieve deferred/rejected alternatives and quantitative observations across
objective episodes, including completion time, engineering effort, intervention and
correction cycles, operational cost, reliability, resource use, and reuse.
Subsequent work may change the circumstances behind an earlier decision and create a
small option worth examining under the current objective.

The purpose is to prevent repeatedly selecting the familiar solution merely because
the team lacks accumulated context. SAGE does not judge, score, or rank which option
must be chosen. The Architect and LLM collaborators reason over attributable
supporting and opposing evidence. Their qualified new findings can become governed
causal evidence for future retrieval.

### Multi-team, multi-role evidence assembly

Existing evidence-analysis, integration, path/architecture criticism, implementation
criticism, optimization, and auditor/referee perspectives may contribute multiple
retrieval or evidence-organization steps. They do not become extra approval gates.
Multiple engineering teams must have consistent access to the same institutional
knowledge without depending on persistent-LLM memory or manual reconstruction.

### Retrieval efficiency and measurement

Optimize the objective-specific subgraph for relevant evidence coverage, temporal
and causal completeness, provenance, and usable context with limited noise, duplicate
material, tokens, execution time, and inference/operational cost. Retrieval quality
and its effect on objective completion and rework can be measured across episodes.
Quantitative scores may be contextual guidance, not hidden policies for excluding
findings or promoting an alternative. Grouping, summaries, pagination, and
progressive expansion preserve access to full underlying evidence.

### Issue #50 qualification and scope

Use the existing approved Issue #50 Definition of Done and test scenarios. Distinguish
what the current code and evidence demonstrate from what remains unqualified.
Isolated concept-to-source classification is a diagnostic, not a substitute for
objective-centered retrieval and reproducible historical context.

This clarification does not authorize a new recommendation engine, independent
reasoning system, permanent facts store, threshold policy, modification of main,
production Neo4j activation, or deployment. Continue bounded engineering and
qualification through the existing feature-branch governance lifecycle.


## Objective-scoped candidate retrieval — bounded implementation slice

The local-only `sage-neo4j-projection.py` integration interface supports
`--objective "Monitor Longhorn observability" --page-size 30 --offset 0`.
It uses existing projection-scoped aliases and visible token overlap as
explicitly provisional candidate entry points,
expands at most one `RELATED_CONCEPT` hop, and returns associated
`CANDIDATE_CONCEPT` sources and literal document links with Git identity,
content digests, and unchanged mapping status. It does **not** claim
paraphrase coverage, semantic qualification, or evidence maturity.

`--seed-concept storage` optionally accepts a concept nominated by a
collaborating LLM; this remains `caller_proposed_candidate`, never authority.
`--browse-inventory --unmapped-only` exposes paginated source records
regardless of semantic matching, so an absent candidate edge cannot become
an assertion that evidence is absent. The page limit affects transport only,
not the available evidence universe.

This slice reuses the candidate graph without model migration or activation.
Globally applicable guardrail relationships, causal/historical alternatives,
complete objective-level recall, and qualified operational proof remain
subject to the existing Issue #50 acceptance ledger. No new gates, scores,
or ontology authority are introduced.

## Evidence-attested context pointers — bounded continuation

**Status:** Candidate-only Issue #50 implementation. This extends the published
objective-scoped retrieval path; it does not qualify a semantic relationship,
change SAGE authority, activate Neo4j, or close the acceptance ledger.

The pinned Git inventory now emits two additional rebuildable projection views:

- `root_governance_sources`: actual root `AGENTS.md` / `SAGE.md` entries, if
  present in the pinned Git tree, with content digests and source revision.
  A `ROOT_GOVERNANCE_POINTER` graph edge makes them accessible for Kalaxy3
  implementation-context retrieval even when the objective has no alias match.
  This is a *repository-instruction source pointer*, not a determination that
  every statement in those files applies to an arbitrary objective.
- `source_sections`: literal Markdown headings for decision, alternatives,
  context, rationale, assumptions, requirements, operational context, and
  outcomes, with section hash and line span. All headings from repository-root
  instruction documents are indexed as source-structure pointers. The graph
  uses version-scoped `SageEvidenceSection` nodes and `SECTION_OF` links.
  These point back to original source text; they do not copy the source bodies,
  or infer accepted/rejected decisions, causes, correctness, or obligation scope.

The `objective_evidence()` response includes provenance-bearing root source
pointers, section metadata, independent section pagination (`section_offset`,
`section_limit`, `next_section_offset`), and attested sections for one-hop
literal source references. A missing semantic match or missing root pointer
continues to mean `not_evaluated`, not qualified absence. Both concept-source
pages and section pages are navigation, not semantic thresholds. The complete
inventory remains accessible separately.

Projection fingerprints now include an `attested_context_v1` schema marker to
prevent reusing an older graph identity for a changed projection representation.
The pinned source SHA-256 hashes already bind the deterministic section
metadata and root-source existence to an exact Git revision. The new writer
verifies context-node and governance-pointer counts in addition to original
source/concept/reference counts. These safeguards do not constitute full graph
rebuild-equivalence qualification under DoD 07.

**Still unresolved:** source-qualified applicability of individual obligations,
semantic interpretation of historical acceptance/rejection and decision rationale,
complete temporal/causal relationships, cross-revision continuity, independent
objective-level recall, authoritative promotion, and deployment. No root source
pointer is an enforcement mechanism or a substitute for governed discovery.

## Source-attested typed relationship claims — bounded continuation

**Status:** Candidate-only Issue #50 implementation. This is an evidence-navigation
capability, not new policy authority or a historical-decision adjudicator.

The optional, Git-committed `sage-neo4j-relationship-claims.json` registry (version
1) declares a bounded set of attributable relationship *claims*. Each row names
an ID, closed relation kind, source subject, optional source object, explicit
scope, evidence source path, starting line and exact one-to-five-line quote.
The reader obtains both the registry and the quoted evidence **from the same
pinned Git revision**, not the working tree. It rejects missing sources,
duplicate IDs, invalid scope/type and misquoted evidence before graph writing.
The projection records SHA-256 evidence and quote digests, line pointers and
source relationships; it never stores the raw quote or upgrades the claim to an
approved decision. A source's literal text and a curator's typed interpretation
remain distinguishable.

The closed relation vocabulary is `applicable_to`, `decision_about`,
`alternative_considered`, `alternative_rejected`, `supersedes`, `depends_on`,
`supports` and `contradicts`. Source-to-source relations require both endpoints
to exist in the same committed source inventory. `applicable_to` requires the
specific `kalaxy3_implementation` scope and an actual root source but **does
not** grant a claim authority over another project or all operational contexts.
The initial registry includes one attributable discovery obligation already
expressed literally in `AGENTS.md`. Additional historical assertions require
separately sourced and governed declarations rather than guessed headings.

Neo4j represents these as version-scoped `SageRelationClaim` nodes linked by
`CLAIM_SUBJECT`, `CLAIM_OBJECT` (when present) and `CLAIM_EVIDENCE` edges to
version-scoped Git sources. Their `kind` is the **registered claim type** and
their `semantic_qualification` remains `not_evaluated`. Candidate graph count
verification includes these claims. The projection fingerprint now uses
`attested_relationship_claims_v1` to prevent reuse of the earlier graph schema
identity; committed registry bytes also participate in the Git source hash.

`objective_evidence()` now returns `relationship_claims`, their total and
independent `claim_offset`, `claim_limit` and `next_claim_offset`. A globally
registered implementation claim remains discoverable even when no concept name
matches an objective. Non-global relation claims are retrieved only for source
pointers on the bounded candidate/one-hop context page. Independent pagination
is transport-only, not a filter asserting that other evidence does not exist.
The full source inventory remains accessible and evidence presence remains
`not_evaluated` throughout.

**Still unresolved:** semantic assessment and qualification of claims, broader
obligation population, temporal/causal decision interpretation, cross-episode
precision/recall, full DoD graph equivalence and production activation. No
ordinary claim may override deterministic SAGE enforcement, Architect approval,
or the separate deployment and Git promotion boundaries.

## Objective-level recall: bounded independent measurement candidate

**Status:** Read-only Issue #50 candidate measurement, not objective acceptance or
semantic authority. The source–concept pair benchmark above does not measure
whether a real objective retrieves the relevant source and typed-claim evidence.

`scripts/sage/sage_neo4j_objective_measure.py` provides separate per-objective
and micro-averaged **labeled-only** precision/recall for source pointers and
source-attested relationship claims. It pages through all bounded source,
section and claim results of the existing `objective_evidence()` read interface,
and preserves distinct lexical candidate and contextual source counts. Missing
or uncertain labels are not treated as negative judgments; unjudged retrieved
identities are counted separately. It rejects duplicate annotations, unknown
source/claim identifiers and source/graph revision mismatches. Its output states
`measurement_only`, `semantic_qualification=not_evaluated`, and
`architect_acceptance=not_evaluated`.

The **external** annotation JSON uses `sage-neo4j-objective-labels-v1` with
`projection_id`, `revision`, `fingerprint`, `annotator`, `annotation_reference`,
and a nonempty `cases` list. Each case has `id`, the literal `objective`,
`source_judgments` and `claim_judgments`. Each judgment identifies a real
`path` or `claim_id`, `verdict` (`relevant`, `irrelevant`, `uncertain`) and a
nonempty `basis`. The source and claim universe must already exist in the exact
candidate graph. A deliberately unfilled judgment list means *not evaluated*.

The local-only, read-only CLI uses the existing pinned Neo4j client requirement
(`neo4j==6.4.1`) and the existing environment secret
`SAGE_NEO4J_PASSWORD`. An independent reviewer must supply the label document;
the script does **not** produce its own ground truth.

```bash
python3 scripts/sage/sage-neo4j-objective-measure.py \
  --projection-id "<existing-candidate-id>" \
  --labels /private/path/to/independent-objective-labels.json \
  --out /private/path/to/issue50-objective-metrics.json
```

This requires an already running **loopback** Neo4j candidate graph. The CLI
rejects non-loopback Bolt URIs, uses a Neo4j read session, and creates an
operator-private receipt without overwriting an existing one. It does not
create, rebuild, activate or deploy the graph. Scores are limited to the named
objectives and expressly judged identifiers; a missing independent label set,
full-population review, live graph or external authority determination leaves
DoD 06 and obligation qualification **open**, not passed.
