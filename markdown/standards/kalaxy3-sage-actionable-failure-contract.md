# Kalaxy3 SAGE actionable failure contract

## Purpose

A SAGE-controlled failure MUST guide an operator who knows only the action
they attempted. Guardrails MUST NOT depend on remembered conversations,
undocumented lifecycle state, prior branch history, or assumed repository
expertise.

## Required response sections

Every actionable failure MUST provide these labeled sections:

1. `SAGE ACTION BLOCKED`
2. `Attempted action`
3. `Detected state`
4. `Why this is invalid`
5. `Likely intended outcome`
6. `Confirm the correct approach`
7. `Allowed actions`
8. `Prohibited actions`
9. `Canonical recovery`
10. `SAGE integrity requirements`
11. `Repository gap`

The likely intention MUST be labeled as an inference. The detected state
MUST come from repository or runtime evidence.

## Recovery behavior

The failure MUST provide an exact repository-owned command or Make target.
It MUST also name the authoritative repository paths that explain the
current lifecycle and recovery process.

When SAGE cannot determine a canonical recovery path, it MUST:

- state the uncertainty explicitly;
- provide the repository-owned discovery command that resolves it;
- identify the missing capability as a systemic repository gap;
- preserve failed-path evidence for evaluation;
- prohibit substitution of undocumented or ad hoc commands.

## Integrity behavior

Recovery guidance MUST preserve:

- repository-owned tooling and pinned dependencies;
- authoritative configuration and lifecycle gates;
- required discovery, source, deployment, cluster, and evidence guardrails;
- failed and successful terminal evidence;
- generated-index and publication lineage;
- rollback authority;
- frequent cohesive validated commits and immediate pushes.

A guardrail MUST NOT recommend bypassing assertions, weakening validation,
changing a lifecycle gate only to satisfy a validator, using unmanaged
tooling, or editing generated evidence directly.

## Reusable implementation

The repository-wide implementation consists of:

- `scripts/sage/sage_actionable_failure.py` for strict rendering;
- `sage-actionable-failures.json` for contextual recovery knowledge;
- `sage-actionable-failure-registry.json` for migration coverage;
- `scripts/sage/sage-actionable-failure-guardrail.py` for authority checks;
- `scripts/sage/sage-actionable-failure-audit.py` for uncovered validators.

An observed incident is a required regression case, but the primary design
target is the broader validator-failure class. New recovery commands must be
verified against existing repository paths or Make targets. Uncovered
validators remain visible in the audit until migrated or explicitly exempted.

## Validator bootstrap and runtime failures

A validator can fail before it evaluates the target system. Import errors,
missing runtime names, dependency mismatches, invalid interpreters, working
directory errors, and uncaught internal exceptions are a separate failure
class.

Such a failure MUST NOT be reported as a target-system validation result.
SAGE must preserve the traceback, identify that validation did not complete,
explain how to verify the approved validator environment, provide the
canonical repair command, and require an exercised runtime regression test.

`py_compile` is a syntax check only. Validator changes require execution of
their real import, reporting, and terminal-output paths.

## Encrypted and tagged configuration metadata

Validators that need non-secret configuration metadata MUST NOT require
decryption of unrelated secrets. Repository YAML can contain `!vault` or
other application-specific tags while also containing ordinary lifecycle,
placement, or feature-gate values.

Such validators must use the repository-owned opaque-tag metadata loader.
Unknown tagged values are represented only by their tag, cannot be coerced
to booleans, and must not expose their payload in output. Validators must
still require ordinary values to have their expected concrete types.

A generic `yaml.safe_load` failure on an unrelated encrypted value is a
validator-runtime defect, not evidence that the target system is invalid.
The real repository file and a synthetic tagged document must both be
covered by exercised regression tests.

## Repository authority and runtime prerequisites

`canonical_recovery.required_paths` identifies repository-relative source
authority needed to understand and execute recovery. These paths must remain
valid in a source-only checkout such as continuous integration.

Generated or environment-provisioned paths, including `.venv`, `.tools`,
`.helm`, and cache directories, are runtime prerequisites rather than
repository authority. They may appear in the canonical command and
explanatory recovery text, but MUST NOT be required to exist merely to
validate the catalog.

Guardrails must validate source authority independently from operator-runtime
provisioning. A source-only CI regression with no generated virtual
environment is required whenever this boundary changes.
