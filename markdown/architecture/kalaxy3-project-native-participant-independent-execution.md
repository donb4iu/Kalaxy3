# ADR: Project-native, participant-independent work execution

- **Status:** Architect-approved principle; candidate repository implementation pending independent review
- **Governing objective:** [Kalaxy3 #43](https://github.com/donb4iu/Kalaxy3/issues/43)
- **Implementation work:** [Kalaxy3 #44](https://github.com/donb4iu/Kalaxy3/issues/44)
- **Qualification:** [Kalaxy3 #45](https://github.com/donb4iu/Kalaxy3/issues/45)
- **End-to-end proof:** [Kalaxy3 #46](https://github.com/donb4iu/Kalaxy3/issues/46)
- **Decision owner:** Architect
- **Admitted source reference:** `697b54ddcc2d0110a7edb154875e19d7b33db527`

## Context

Kalaxy3 work is executed by interchangeable participants: an internal engineer, an
external engineering provider, an LLM participant, or SAGE-coordinated roles.
Participants may pick up nonconsecutive issues, lose their execution environment,
or replace a prior participant. No issue may require a persistent LLM conversation
or another participant's undocumented local state to be understandable and completable.

## Decision

GitHub Issues and GitHub Project #15 are the authoritative work-management and
communication surfaces. The issue body defines the durable engineering contract;
native assignment, issue relationships, Project fields, comments, linked pull
requests, and reviews carry responsibility, progress, questions, and evidence.
Governed Git and associated engineering records establish source and qualification
evidence. An issue's status is read from GitHub, not asserted by LLM-authored text.

A work item must specify its outcome, scope and exclusions, inputs, constraints,
explicit dependencies, applicable authority, deliverables, acceptance criteria,
and Definition of Done. Participants must verify current authoritative evidence,
not assume prior issues were completed or previous execution context is available.

The Architect retains independent authority over objectives and material decisions.
Engineering participants retain their independently conferred responsibilities.
SAGE may discover, coordinate, execute *its own delegated actions*, preserve
provenance, recover context, and report evidence and uncertainty. SAGE's checks
may bound what SAGE autonomously does; they do not grant SAGE authority over
independently authorized participants or GitHub's native state.

Completion is established by acceptance evidence and applicable qualification,
not merely by status movement. Deployment requires separate operational authority.
An approved deviation must identify its approver, scope, reason, remaining risk,
and substitute evidence; it does not imply unperformed work occurred.

## Credential and access-control boundary (AC15)

Engineering roles may read GitHub work definitions through appropriately scoped
read-only capabilities. The LLM must not receive general-purpose credentials
that permit editing Architect-owned intent, qualification records, or protected
repository state. This restriction must be enforced by GitHub permission scopes,
separate identities, and/or a separately isolated adapter that holds credentials
outside the executing LLM's accessible environment. A source-level allowlist
for GraphQL queries is **not** a credential boundary when the LLM can invoke
an alternative tool with the same credential.

Any engineering write must be constrained to explicitly permitted operations
using independently enforced permissions, attributable identity, and auditable
provenance. In particular, issue comments or a new Project status do not amend
Architect-approved intent. Proposed objective changes require the Architect's
independent decision; SAGE records that decision without approving it.

Qualification must include an inventory of every credential and reachable
mutation path, actual negative permission tests (not merely mocked validators),
separation of engineering-write from review/approval, and a successful authorized
engineering-write test. Until then, AC15 is **unverified**, and general-purpose
GitHub write credentials must not be exposed to an executing LLM.

## Work contract and evidence rules

1. **Task definition:** The issue body states a participant-neutral result and
   objectively verifiable acceptance criteria.
2. **Dynamic execution state:** Use native Project fields, assignees, relationships,
   comments, PRs, and review records. Do not maintain a parallel SAGE status system.
3. **Source identity:** Associate implementation and review evidence with the
   issue/repository identity and exact Git revision.
4. **Dependencies:** Discover blocking relationships and their acceptance evidence.
   Issue numbers or creation dates never imply execution order.
5. **Resumption:** A fresh participant reconstructs the next action from GitHub and
   governed Git without this or any other LLM conversation.
6. **Honest uncertainty:** Missing or inaccessible authoritative evidence is
   reported as unknown/blocked for SAGE automation, not as success.
7. **Independent authority:** The Architect may act directly; SAGE records the
   action and provenance, not a second authorization.

## Implementation and enforcement

- Adopt a reusable participant-neutral GitHub issue form under
  `.github/ISSUE_TEMPLATE/`.
- Integrate deterministic contract and source/evidence checks into existing SAGE
  execution paths rather than inventing a parallel lifecycle.
- Validate real Project read-back separately from mocked tests, and verify source
  revision, assignment when required, status freshness, and authority provenance.
- Preserve supported non-Project pathways without falsely labeling them
  Project-qualified.
- Make failures observable and actionable; do not silently promote unsupported
  evidence into a verified result.

## Verification

- A fresh LLM participant can discover #44 from Project #15, retrieve its contract,
  report verified dependencies, and recover an interrupted assignment without
  previous LLM context.
- Nonsequential issue selection and missing/stale Project evidence produce correct
  results in automated positive and negative tests.
- Implementation, independent Referee/Reviewer findings, PRs, and promotion
  evidence are attributable to the source revision and originating issue.
- Independent human-team usability remains a design requirement. Live execution
  by a human/outsourced team may be deferred until such a team is available, with
  its deferral and reconsideration trigger recorded on #44. Such validation may
  not be represented as passed before it occurs.

## Consequences

This enables outsourcing and LLM replacement without rewriting assignments,
and reduces reliance on conversation memory. It requires disciplined issue
contracts and GitHub-visible handoffs. A Project item placed In Progress without
an executing assignee or implementation evidence documents selection, not proof
that a Responsible has started work.

## Adoption note

Confirm the repository's existing ADR naming/location conventions before merging;
this path and filename are provisional. The approved principle and the adoption
of this particular file are different events.

## Source-snapshot integration assessment (candidate)

The source ZIP received for issue #44 contains fixed read-only Project queries,
read-only pull-request inspection, and a GitHub Actions Projects visibility probe.
These demonstrate code-level intent and mock-test coverage, not actual GitHub
permission isolation or a live read-back of the private Project. The enhanced
Projects inspector exposes body, assignees, and observed status, while expressly
reporting Architect authority, issue activity, and dependencies as unverified or
not retrieved. These remain outstanding integration obligations.
