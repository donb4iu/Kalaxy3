# SAGE LLM Semantic Adapter SOP

## Governing principle

**LLMs propose meaning. SAGE converts meaning into canonical control records.**

No SAGE LLM role is required to know or reproduce SAGE's internal serialization,
authority, repository, lifecycle, provenance, or receipt formats. A model-facing
contract is a role contract, not a SAGE control-record contract.

## Required boundary

Every SAGE LLM/inference role follows this sequence:

1. SAGE constructs the bounded role context.
2. The role returns only the semantic judgment required for that role.
3. A deterministic SAGE-owned adapter validates the role-level semantic response.
4. The adapter maps the response into the canonical SAGE vocabulary.
5. SAGE injects identity, authority, provenance, lifecycle metadata, and derived
   invariant fields.
6. The existing canonical SAGE validator validates the constructed record.
7. Only deterministic SAGE continuation may act on the validated record.

## Model-owned content

A role may provide only information that actually requires cognition, such as:

- semantic classification or intent;
- concise rationale;
- uncertainty or clarification needs;
- observations relevant to the role.

The role must not be responsible for SAGE schema versions, record types, authority
claims, objective/request/proposal hashes, Git state, lifecycle tokens, receipts,
or fields whose values are deterministic consequences of the semantic choice.

## SAGE-owned conversion

SAGE may translate representation but may not silently repair meaning.

Examples of legitimate deterministic conversion include:

- role-level `bounded-correction` -> internal `implementation-local`;
- deriving `material_change=false` from that mapping;
- injecting `authority=advisory`;
- binding the exact objective identity from SAGE state;
- creating provenance/receipt fields from actual execution evidence.

If a role response is ambiguous, contradictory, or cannot be mapped without
inventing meaning, SAGE must fail closed or enter a genuine clarification boundary.

## Anti-patterns

The following are prohibited:

- teaching an LLM the full SAGE control-record schema merely so it can echo it;
- treating omitted SAGE metadata as a model failure;
- allowing the model to author or elevate its own authority;
- post-inference normalization that changes semantic meaning;
- provider-specific retry loops whose purpose is to coerce SAGE serialization;
- coupling model qualification to knowledge of internal SAGE lifecycle formats.

## Workflow-manager first proof

The workflow-manager role exposes only:

- semantic intent;
- concise rationale;
- optional clarification question;
- non-path-changing observations.

SAGE maps that response into the existing canonical
`sage-llm-workflow-manager-decision`, derives invariant fields, binds exact
objective identity and advisory authority, and then runs the existing canonical
validator unchanged.

## Regression obligation

Every role adapter must prove both directions:

- valid role-level meaning converts to the correct canonical SAGE record without
  model-authored control metadata;
- model attempts to author SAGE control metadata, contradictory meaning, or
  unmappable/ambiguous semantics fail closed before continuation.

This SOP applies to all current and future SAGE LLM/inference roles.
