# Pause decision: centralized logging and SAGE guardrail remediation

Evidence ID: SAGE-K3-GOVERNANCE-20260726-002
Decision date: 2026-07-26
Decision owner: Don Buddenbaum

## Decision

Pause centralized-logging implementation and deployment until the SAGE
enforcement gap is repaired, independently validated, and evidenced.

## Immediate actions completed

- Stopped chart-pull and observability deployment work.
- Preserved the unfinished logging implementation on
  `wip/centralized-logging-staged-20260726`.
- Pushed checkpoint commit `84e381c` to the remote repository.
- Returned to an up-to-date main branch.
- Created clean branch `feature/sage-enforcement-guardrails`.
- Inventoried current Helm call sites and controller checks.
- Requested this evidence-only SAGE package before remediation begins.

## Why a pause was chosen

Continuing observability would have normalized a workflow that violated the
repository-authority principle just validated during the controller-portability
session. Fixing the chart reference alone would have addressed the immediate
403 response but left the root cause intact: arbitrary Helm binary selection
and machine-local state.

The work was paused because:

- repository repeatability is a prerequisite, not a post-deployment
  documentation task;
- hidden Helm state can produce costly or unsafe deployment differences;
- later evidence review is too late to be the only control;
- API admission should independently reject dangerous rendered resources when
  an earlier controller gate is bypassed;
- the unfinished work could be preserved safely without forcing a premature
  merge.

## Resume conditions

Centralized logging must remain paused until evidence demonstrates:

1. repository-managed, checksum-verified Helm installation;
2. repository-isolated Helm configuration, cache, data, registry, and plugins;
3. controller preflight validation of exact Helm version and location;
4. source-policy rejection of unauthorized bare Helm execution;
5. repository-declared and validated chart repositories;
6. explicit Ansible Helm binary selection;
7. removal or control of the remote control-plane Helm bootstrap path;
8. staged Kubernetes admission policies with positive and negative tests;
9. enforcement promotion from warning/audit to deny where approved;
10. clean reproduction from the iMac and Mac mini;
11. a SAGE evidence package for the guardrail implementation.

## Nondecision

This pause does not select the final Loki or Fluent Bit chart source or version.
The WIP branch contains provisional logging work and known unresolved chart
transport/version assumptions. It is a preservation branch, not an accepted
implementation branch.

## Recovery

When guardrail work is accepted, resume from the WIP branch by reviewing and
rebasing or selectively integrating its changes under the new controlled Helm
and admission workflow. If the WIP proves obsolete, retain the branch for
history and rebuild centralized logging from main under the new controls.
