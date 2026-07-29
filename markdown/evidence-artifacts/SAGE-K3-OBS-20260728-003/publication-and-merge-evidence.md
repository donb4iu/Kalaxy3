# Publication and Main-Merge Evidence — SAGE-K3-OBS-20260728-003

## Repository publisher validation

Operator-supplied output:

```text
SAGE package validation: PASS
Evidence ID: SAGE-K3-OBS-20260728-002
Record:      markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md
```

## Repository publisher result

```text
Publication completed with a clean working tree.
Evidence ID:           SAGE-K3-OBS-20260728-002
Implementation commit: 4247387a8062a0a353f5704e40c90b1727881a4a
Evidence commit:       81cdb0b9c25491e15be6cc7de8897de3ecbd05b5
Record:                markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md
Checksum:              markdown/operations/kalaxy3-centralized-logging-deployment-evidence.md.sha256
Published to:          origin/wip/centralized-logging-staged-20260726
```

## Main integration result

The final operator output records:

```text
[main d5878d8] Merge centralized logging observability deployment
merge_commit=d5878d8d7ad3dc2f90822bbf162fe2b2fc63d075
first_parent=761c87974548db37d4a52bbd78d4d7ac2ff321cc
second_parent=81cdb0b9c25491e15be6cc7de8897de3ecbd05b5
PASS merge commit contains the completed feature branch
...
local_main=d5878d8d7ad3dc2f90822bbf162fe2b2fc63d075
remote_main=d5878d8d7ad3dc2f90822bbf162fe2b2fc63d075
0  0
...
nothing to commit, working tree clean
PASS centralized logging deployment merged into main
PASS readiness and deployment SAGE evidence merged into main
PASS main published and synchronized
```

## Guardrail results retained by the merge transcript

- Repository SAGE guardrails: PASS.
- SAGE evidence reconciliation: PASS with zero generated-path changes.
- Homelab source and deployment guardrails: PASS.
- All seven inventory hosts passed noninteractive SSH and privilege-escalation checks.
- All platform-phase playbook syntax checks passed.
- Eight installed Helm releases matched exact locks; zero new releases were permitted.
- Both observability evidence-record checksums passed.
- `deploy_centralized_logging: true` remained active.

## Source transcript

The operator-provided merge transcript had SHA-256 `0705a89c9baa175c92359deb0f6a62f99da4c014df483739a0ed176d159c343e`. The transcript was used as audit evidence but is not duplicated in full because the canonical source record already preserves the deployment terminal evidence and this artifact preserves the decisive publication and merge observations.
