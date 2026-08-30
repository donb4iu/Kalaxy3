# SAGE Workflow Capability Completeness Audit

## Purpose

SAGE must not discover predictable workflow-engine and delivery lifecycle capabilities one collision at a time. This process turns the recurring pattern into a class-level capability-intelligence control.

The comparison surface is intentionally implementation-neutral. GitHub Actions, Jenkins, Argo Workflows, and Tekton are used as representative discovery sources for mature workflow capability families. Their features are not SAGE authority and do not become requirements merely because another product implements them.

## Capability families

The governed baseline covers SCM lifecycle, workflow state, triggers/events, orchestration, artifacts/promotion, environment authority, execution portability, evidence/observability/recovery, and reusable composition.

Every capability receives exactly one disposition:

- `implemented`
- `partial`
- `required-gap`
- `deferred-gap`
- `intentionally-prohibited`
- `not-applicable`

There is no silent `unclassified` state.

## Class-level remediation

When one observed defect demonstrates that a capability family is structurally incomplete, SAGE audits the complete family before proposing another isolated patch. Structurally equivalent gaps are grouped into the same governed remediation scope when they share authority, lifecycle semantics, or an implementation root cause.

This does not authorize indiscriminate feature parity. SAGE records gaps that are not required now as deferred or not applicable and preserves the Architect's authority over priority and Definition of Done.

## Bootstrap deadlock

The capability-intelligence policy already identifies both of these as blocking conditions:

- a bootstrap requires the capability it is intended to create;
- required live state exists only through undocumented manual mutation.

Branch bootstrap is the regression case for that rule. The permanent branch-lifecycle composition therefore reuses `git.inspect` and `operator.git-proposal`, emits one operator command per boundary, freezes exact repository authority, verifies each operator result, and contains no direct Git mutation implementation. Its post-promotion closeout mode additionally proves the promoted source is contained in stable authoritative `main`, permits only fast-forward local-main reconciliation, governs exact remote and local source-ref retirement, and records a milestone-level SAGE repository-lineage receipt while leaving detailed chronology to Git.

Historical branch transitions are not rewritten and retrospective receipts are not fabricated. Where evidence is later reconciled, it must distinguish governed-and-evidenced, independently-verifiable-but-previously-unrecorded, and unsupported history.

## Validation

`make sage-capability-intelligence-workflow-audit` validates the completeness matrix. Root SAGE guardrails also exercise the branch-lifecycle self-test and guardrail so future changes cannot silently remove the governed bootstrap path.

The audit is expected to evolve as SAGE learns which workflow capabilities are materially required. Changes remain Architect-governed and evidence-backed.
