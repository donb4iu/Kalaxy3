# Failure and recovery ledger

| Sequence | Attempted action | Observed result | SAGE interpretation | Accepted recovery |
|---:|---|---|---|---|
| 1 | Run a downloaded one-off validation wrapper | `sage-preflight` failed because `SAGE_REQUEST` was absent | The wrapper duplicated repository orchestration and did not preserve the governed request | Use repository-owned Make targets and provide the literal governed request |
| 2 | Run `make sage-preflight` without `SAGE_REQUEST` | Usage failure, exit 2 | Correct fail-closed behavior | Invoke `SAGE_REQUEST=... make sage-preflight` |
| 3 | Run canonical runtime validation before controller Helm bootstrap | Validator blocked because repository Helm was missing | Runtime bootstrap failure is not a logging validation result | Run `make controller-helm`, preserving the failure receipt |
| 4 | Run `cluster-guardrails` from repository root | No root Make target existed | Wrong SAGE-discovered working directory | Run the target from `infrastructure/k3s-homelab` |
| 5 | Run canonical runtime validation and homelab cluster guardrails | Both passed | Accepted final validation path | Preserve outputs and prepare the evidence package |
