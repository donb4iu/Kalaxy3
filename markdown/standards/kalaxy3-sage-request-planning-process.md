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
2. resolved **repository authority** from current SAGE discovery;
3. `sage-workflow-primitives.json`;
4. the mandatory request-execution primitive set published by
   `scripts/sage/workflows/request_execution.py`; and
5. the checksum-bound source-only package.

The source-only package is governed by
`sage-request-planning-source-schema-v1.0.json`. Its manifest deliberately has
no `capabilities`, `candidates`, `selection_factors`, or
`new_primitive_required` fields.

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

If a mandatory capability cannot be supplied by the registry,
`capability.gap` records the insufficiency and the planner fails closed before
proposal generation. A separately governed and approved capability gap is
required before a new low-level primitive can be implemented.

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
  request-execution parser.
