# Kalaxy3 SAGE Workflow-Support Process

## Purpose

Workflow automation must reuse canonical repository behavior rather than
reimplementing identifiers, Git handling, lifecycle transitions, discovery,
validation, logging, or evidence generation in each helper.

## Canonical identifier allocation

SAGE improvement-action identifiers are allocated only by the canonical
allocator in `scripts/sage/sage_identifiers.py` through the read-only
`scripts/sage/sage-action-id.py` interface.

Allocation uses exact set membership and first-free sequencing. It does not
use regular-expression parsing. Collision, gap, malformed-record, date, and
namespace-exhaustion cases are runtime tested.

Tracked workflows and wrappers must not define local functions named
`next_action_id`, `allocate_action_id`, or `allocate_scoped_id`.

## Static runtime-name validation

Python workflow code must pass the repository-owned undefined global
guardrail before delivery. Syntax compilation alone is insufficient because
it does not resolve runtime global names.

The guardrail uses Python's symbol-table model and rejects unresolved global
references such as an undefined `FAILURE_EVIDENCE`.

## Exact-path validation

A change is not validated by checking that a source token exists. Validation
must exercise the exact runtime path up to a controlled mutation boundary.

For action registration this means:

1. allocate through the canonical allocator;
2. construct and validate the draft;
3. dry-run the canonical registration command;
4. apply only from a clean tree;
5. validate and commit the exact registry mutation.

## Makefile integration

Aggregate Make targets are extended through prerequisites, not by inserting
recipe lines into a prerequisite declaration that may continue across lines.
The complete candidate Makefile MUST be written to a temporary file and
parsed with GNU Make dry-run commands before it replaces the repository file.

## Primitive-first correction

When a root cause belongs to a reusable primitive, the correction updates the
primitive and adds a regression test. A wrapper-only root-cause patch is
prohibited.

Primitive evolution records failure evidence and validates the corrected
runtime branch before another production mutation.
