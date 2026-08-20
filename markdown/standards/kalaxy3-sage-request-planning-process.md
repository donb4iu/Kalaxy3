# Kalaxy3 SAGE request-planning process

## Purpose

SAGE request planning is the repository-owned composition that turns a literal
request plus a checksum-bound **source-only package** into the existing
request-execution proposal interface. It closes SAGE-ACTION-20260808-001 by
removing caller-authored component-selection semantics from normal request
execution.

The planner does not replace implementation expertise. A model or human may
supply proposed repository content, generated paths, validation targets,
evidence references, and an operator commit message. It may not supply
`RequiredCapability`, `ComponentCandidate`, `selection_factors`, component
selection, or capability-gap decisions when this planner applies.

## Authoritative inputs

The planning composition uses:

1. the exact literal request;
2. resolved **repository authority** from Architect-confirmed semantic authority when present, otherwise current SAGE discovery for legacy sources;
3. `sage-workflow-primitives.json`;
4. the mandatory request-execution primitive set published by
   `scripts/sage/workflows/request_execution.py`; and
5. the checksum-bound source-only package.

The source-only package is governed by
`sage-request-planning-source-schema-v1.0.json` for legacy callers, historical semantic-bound v1.1 sources, additive v1.2 for sources that separate semantic applicability from implementation authority, and additive v1.3 for newly confirmed sources that also preserve Architect-confirmed planning obligations. Their manifests deliberately have
no `capabilities`, `candidates`, `selection_factors`, or
`new_primitive_required` fields.

## Semantic authority propagation
When a planning source is generated after Architect semantic confirmation, the source package embeds the exact semantic-understanding and semantic-confirmation artifacts and records their SHA-256 digests. Historical v1.1 sources retain the original combined-context semantic authority contract. New v1.2 sources record both the full Architect-confirmed `applicable_contexts` envelope and the narrower `implementation_contexts` used for source-mutation authority, plus complete context dispositions. That **Architect-confirmed semantic authority** is authoritative for downstream repository-authority resolution.

The planner still performs literal SAGE discovery and evidence retrieval, but raw discovery remains audit evidence rather than a second semantic-authority decision. Request-relevant contexts may remain applicable even when they own no proposed source mutation; they do not thereby gain mutation authority. For v1.2, the planner resolves authority files only from `implementation_contexts` while preserving `applicable_contexts` for evidence, governance, and semantic re-entry checks. If literal discovery produces a context that was not part of the confirmed dispositions, or if path/dependency-derived implementation authority expands beyond the confirmed implementation-context set, planning fails closed and requires a **return to semantic confirmation** rather than broadening scope. A narrowed active mutation set may derive only a subset of the confirmed implementation contexts without invalidating the still-authoritative semantic envelope.

Legacy v1.0 planning sources retain literal-discovery authority behavior. Historical v1.1 and v1.2 semantic sources remain readable under their original contracts and are never rewritten merely to acquire newer fields.

For semantic-bound sources, the active planning-source path set must remain a subset of the Architect-confirmed `implementation_scope`. This permits implementation-local refinement to touch only the files needed for the current candidate while retaining the original confirmed scope as the authority ceiling. Any path outside that ceiling is a semantic scope expansion and fails closed for re-confirmation.

### Planning obligations

v1.3 carries structured **planning obligations** from the confirmed semantic record. The obligation set preserves the accepted action outcome, Definition of Done / acceptance criteria, measurement obligations, authoritative semantic modifications and constraints, feasibility obligations, and explicit Architect planning directives. Each obligation records its provenance rather than flattening those sources into an opaque summary.

Only obligations explicitly classified as `capability` become `RequiredCapability` inputs to `component.select`. Constraint, requirement, validation, measurement, feasibility, outcome, and lifecycle obligations remain first-class planning authority but do not masquerade as deployable components.

A required domain capability with no repository-proven candidate produces a **domain capability gap** through the existing `capability.gap` owner. That gap has `new_primitive_required=false`: it stops planning for governed capability evaluation instead of silently falling back to an engineering-contribution mechanism or pretending that a new SAGE primitive is required.

## Planning behavior

For every primitive required by the current request-execution composition, the
planner derives a required capability from the operating contract and an
eligible candidate from the live **workflow-primitives** registry.

Candidate factors are repository-derived:

- direct applicability comes from the mandatory request-execution contract;
- authority compatibility is bounded by successful current SAGE discovery;
- least-authority fit comes from using the exact registered primitive required
  by the operating contract;
- interface verification requires the registered module, symbol, and source;
- runtime-test coverage comes from the primitive registry;
- version and maturity come only from the primitive registry.

`component.select` remains the selection authority. The planner does not use an
opaque composite score.

If a mandatory workflow capability cannot be supplied by the registry,
`capability.gap` records the primitive insufficiency and the planner fails closed before
proposal generation. A separately governed and approved primitive gap is
required before a new low-level primitive can be implemented.

If an Architect-confirmed domain capability cannot be proven by an existing registered candidate, the same `capability.gap` ownership records a domain capability gap and fails closed without authorizing a new primitive. This distinction is required for capabilities such as reusable secrets management: the planner must surface the unresolved domain decision instead of accepting a controller-local token file merely because it appeared in the original contribution.

When more than one Architect-confirmed domain capability is unresolved, planning evaluates the complete domain-capability set in the same pass. It writes one versioned receipt per unresolved capability plus a checksum-bound `sage-domain-capability-gap-set` index (the domain capability gap set) and then fails closed once. The planner may not stop after the first domain gap when the remaining required capability set is already known. This permits the Architect and candidate-iteration lifecycle to govern one coherent class-level remediation instead of repeating discovery, confirmation, and mutation for structurally equivalent gaps.


A review-required domain-capability gap set is an **actionable domain capability review** boundary, not an opaque planner error. When the planner already knows the exact gap-set path, required capabilities, decision authority, staged-candidate provenance, approval composition, or retry boundary, it MUST surface those facts through the shared actionable-failure contract. The planner MUST NOT require the invoker to reconstruct deterministic arguments that SAGE already possesses.

Architect-owned decision content remains different from deterministic recovery knowledge. In particular, SAGE may identify the exact approval command and all checksum-bound arguments, but it MUST NOT invent an approval/rejection decision or rationale. The actionable response explicitly names any such human-owned input as unresolved. If the confirmed planning source exposes the staged engineering-contribution package and digest, request planning verifies that package before presenting it as the approval candidate. If that provenance cannot be verified, the failure says so and does not pretend that a complete approval command is available.

For implementation-local or planning re-entry that reuses already-confirmed semantic authority, the embedded semantic-understanding and semantic-confirmation artifacts remain immutable. The reused planning source separately binds the effective current engineering contribution with exactly one `implementation-local-contribution-package:<absolute-package-path>` and one `implementation-local-contribution-sha256:<digest>` evidence reference. Request planning verifies the package checksum and requires its source-file path/mode/digest set to match the current planning-source payloads before surfacing that package as the staged approval candidate. Missing, ambiguous, checksum-mismatched, or payload-substituted implementation-local provenance fails closed; SAGE must not fall back to the older semantic contribution merely because semantic authority is reused.

The planner preserves a local `sage-actionable-failure-observation` for this boundary, including whether the cause was known, whether candidate provenance was available, whether recovery guidance was prepared, whether Architect action was required, the retry boundary, and the required capability set. These observations are workflow-friction evidence for interpretation burden, avoidable rework, and recovery effectiveness.

### Governed domain-capability remediation and bootstrap deadlock

A domain capability gap is a planning stop, not a dead end. SAGE must not create the **bootstrap deadlock** in which implementing a capability first requires that same capability to already be implemented. The original `review-required` gap receipts remain immutable evidence. The Architect may approve the complete domain capability gap set through the repository-owned approval composition, which creates checksum-bound approved copies and preserves the original receipt paths and digests as evidence. Approval is bound to the exact staged engineering-contribution digest and the semantic-understanding/confirmation digests from the planning run that produced the gap set. Approval authorizes evaluation of that staged implementation candidate; it does not prove that candidate works.

On planning re-entry, an **approved domain capability gap** may select a checksum-bound **staged implementation candidate** only when all of the following are true: the exact capability was Architect-approved in the gap set; the effective engineering-contribution digest and semantic authority in the current planning source exactly match the approval binding; the current governed workflow capability baseline already classifies that capability as a known gap or partial capability; the proposed checksum-bound baseline moves that exact capability to `implemented`; and every mapped implementation path is either present in the approved source package or already exists in the repository. Candidate substitution, semantic-authority substitution, stale approval reuse, or capability-set mismatch fails closed. The selected candidate remains `staged-implementation` until request execution and the complete applicable validation gate succeed. This is implementation authority, not retrospective capability proof.

For later requests, an `implemented` entry in the governed workflow capability baseline becomes a repository-proven domain candidate only when all mapped implementation paths exist. That allows normal planning to consume a capability after it has actually been implemented and validated instead of rediscovering the same gap forever. External callers still may not author capability or candidate semantics.

The optional approved-gap-set input is therefore an explicit Architect authority input to planning, never an LLM or tool self-approval mechanism. Missing, stale, candidate-substituted, semantic-authority-substituted, mismatched, partially approved, or checksum-invalid gap evidence fails closed.

## Published interface

Successful planning emits the unchanged
`sage-request-execution-proposal-schema-v1.0.json` package consumed by
`sage-request-execute.py`. Request execution therefore consumes a stable
planning result instead of caller-authored capabilities and candidates.

Normal usage is:

```console
SAGE_REQUEST="<literal request>" SAGE_SOURCE="<source.zip>" make sage-request-plan
SAGE_REQUEST="<same literal request>" SAGE_PROPOSAL="<planned proposal.zip>" make sage-request-execute
```

The planner records resolved authority, component selection, event logs, and a
local closeout under the SAGE local-state directory.

## Mutation and authority boundary

Planning performs **no Git mutation**, **no GitHub mutation**, and **no
deployment mutation**. It also does not change repository content. The existing
request executor remains responsible for checksum-bound repository-content
application, validation, safety analysis, and the deterministic operator
stage → commit → push lifecycle.

External callers and tracked downloaded helpers are prohibited from
reconstructing request-planning capability derivation, candidate eligibility,
selection factors, component selection, or capability-gap semantics after the
repository planner is available.

## Required regressions

The planner self-test must prove:

- a semantic-vocabulary replay request resolves the existing
  request-execution primitive capabilities without external candidate
  semantics;
- a deliberately unsupported required capability creates an explicit
  `capability.gap` receipt and blocks proposal generation; and
- a source-only package becomes a proposal accepted by the existing
  request-execution parser;
- request-relevant contexts with no proposed source mutation remain visible in the semantic applicability envelope without leaking unrelated mutation authority;
- implementation contexts remain a subset of the full semantic applicability envelope;
- historical v1.1 semantic planning sources remain readable without rewrite; and
- a genuinely new post-confirmation context fails closed and returns to semantic confirmation instead of silently expanding authority;
- Architect-confirmed planning obligations survive into v1.3 planning authority; and
- the reusable-secrets regression creates a domain capability gap with `new_primitive_required=false`, preserving Ansible as the established deployment/control model and preventing a controller-local token plus rendered Kubernetes Secret from satisfying the obligation by default;
- two unresolved Architect-confirmed domain capabilities are reported together in one planning pass rather than truncating the gap set to the first capability;
- review-required domain-gap evidence remains immutable while Architect approval produces separately checksum-bound approved copies;
- an approved known gap can select only the exact contribution- and semantic-authority-bound staged implementation candidate without claiming pre-validation success or requiring the capability it is intended to create; and
- a domain capability already marked `implemented` with existing mapped repository paths is rediscovered as a repository-proven candidate on later planning runs.

## Repository-owned source construction

`scripts/sage/request_planning.py` publishes `write_source_package` so trusted repository compositions can derive `sage-source.json`, payload hashes, and archive scope internally. Human, LLM, and external callers are not required to author that SAGE-internal manifest. The accepted-action semantic-bootstrap composition is the first consumer; it preserves the existing `sage-request-plan` proposal interface rather than duplicating component selection or capability-gap semantics.
