# Kalaxy3 generated-helper runtime-validation process

## Purpose

This process prevents an exact generated helper from being delivered when its
source parses but its actual runtime path contains an unresolved name, missing
import, invalid late-bound value, unsafe mutation capability, or incomplete
companion artifact handoff.

## Repository-owned composition

`scripts/sage/workflows/generated_helper_delivery.py` is the tracked validation
composition. It reuses the registered command, validation-plan, undefined-global,
helper-safety, structured-logging, atomic-file, catalog, and workflow-composition
controls. It does not create a new low-level primitive and it does not execute
Git, GitHub, credential, ref, cluster, or deployment mutation.

A delivery manifest conforming to
`markdown/standards/sage-generated-helper-delivery-manifest-schema-v1.0.json`
identifies:

- the exact helper SHA-256;
- an explicitly disposable runtime fixture outside the live repository;
- every required companion artifact path and SHA-256;
- the declared `--self-test` argv;
- the exact non-self-test operator path argv.

The composition fails closed unless the self-test and operator commands invoke
the exact helper, the operator path consumes every declared companion artifact,
and all helper and companion digests match before execution.

## Validation sequence

The repository-owned workflow performs:

1. current `SAGE-ACTION-20260730-001` lifecycle verification;
2. manifest, fixture, helper, companion artifact, and digest verification;
3. Git, GitHub, credential, and deployment safety analysis;
4. isolated `py_compile` of the exact helper;
5. repository-owned undefined-global analysis;
6. the declared helper self-test, which must emit non-empty runtime execution evidence;
7. the exact non-self-test operator path, which must emit non-empty runtime execution evidence;
8. atomic machine-readable receipt creation after all checks pass.

Syntax compilation, source-token checks, or self-test-only execution are not
runtime validation.

## Required regressions

The exact production CLI self-test must prove that delivery rejects:

- an unimported `hashlib` reference;
- an undefined `AUTHORITY_DIGESTS` reference;
- a defined-but-invalid late runtime value;
- a silent zero-exit declared self-test;
- a silent zero-exit exact operator path;
- a missing companion artifact;
- a companion artifact digest mismatch;
- an operator path that omits a required companion artifact;
- a helper digest mismatch;
- Git, GitHub, credential, or deployment mutation capability;
- a stale pre-existing receipt.

Every failed path must leave no partial new receipt. A validated positive path
must record helper, manifest, companion, event-log, command-output, and final
receipt digests.

## Lifecycle and measurement

The implementation may be staged while `SAGE-ACTION-20260730-001` is
`accepted`. Real helper delivery remains blocked until that action reaches
`validated`, `measured`, or `closed` through the canonical lifecycle tool.

The action is not measured or closed until the recurrence rate is evaluated
across the next five generated-helper deliveries. Each delivery records the
runtime result and digests in its associated SAGE session or evidence package.
