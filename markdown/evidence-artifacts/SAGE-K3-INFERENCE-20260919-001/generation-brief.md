# Kalaxy3 SAGE evidence-generation brief

## Original requester language

```text
Original Architect disposition: "approve".

Approved objective: execute the GPT-OSS shared-inference runtime path for SAGE-ACTION-20260813-001. The first runtime attempt failed closed before cluster mutation because localhost-only Ansible controller tasks attempted sudo. SAGE persisted an implementation-local play-level become=false correction, but the next runtime continuation failed identically because the inventory-level ansible_become connection variable has higher precedence than the play keyword. Repository prior art already documented this exact behavior and the required ansible_become=false play-variable override. SAGE therefore applied and persisted that bounded second correction without changing storage/model/GPU/placement/health/recovery semantics, proved the read-only controller path without sudo, and continued the same approved runtime path. Generate governed SAGE evidence preserving both fail-closed corrections and the successful runtime observations. Do not claim promotion or canonical integration from runtime evidence alone.
```

The original request is authoritative context and must not be rewritten into a weaker requirement.

## Automatically applied canonical request

# Canonical SAGE working-session evidence request

Use this exact request after a Kalaxy3 working session:

> Generate the SAGE evidence package for the most recent Kalaxy3 working
> session using the repository SAGE evidence-record standard, canonical
> metadata contract, evidence-record template, evidence-publication process,
> and evidence-navigation compatibility rules. Use schema 1.2. Populate every
> canonical front-matter field in exact order, including formal title,
> navigation title, navigation section, navigation order, summary, and primary
> subject. Generate the exact Record metadata table from front matter, include
> an explicit `[TOC]`, and keep the Five Ws consistent with canonical metadata.
> Include all available terminal and repository evidence, final state, failed
> attempts, rationale, limitations, gaps, rollback, rebuild, idempotency,
> security review, and revalidation. Preserve historical evidence through the
> existing catalog and legacy registry rather than rewriting or excluding it.
> Produce one valid ZIP with `sage-package.json` and `payload/`. Return the
> package and only the standard check and publication commands. Do not invent
> another metadata format, navigation format, or Git workflow.

Expected response:

1. one ZIP package;
2. one validation command:

   ```bash
   python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
   ```

3. one publication command:

   ```bash
   python3 scripts/sage/sage-publish.py publish \
     ~/Downloads/<package>.zip \
     --push
   ```

The generator must not provide an ad hoc static header, manual catalog edit,
`unzip`, `git add`, `git commit`, `pull`, or `push` workflow. Canonical metadata,
legacy preservation, navigation reconciliation, and Git publication belong to
the repository contracts and publisher.

## Inferred SAGE contexts

- `repository-governance`
- `evidence`
- `storage`

## Discovered authoritative files

- `AGENTS.md`
- `SAGE.md`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-authority-reconcile.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-capability-gap.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-component-select.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-failure-diagnose.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-decision-primitives.json`
- `markdown/standards/kalaxy3-sage-actionable-failure-contract.md`
- `markdown/standards/kalaxy3-sage-change-discovery-process.md`
- `markdown/standards/kalaxy3-sage-operating-contract.md`
- `markdown/standards/sage-authority-reconciliation-schema-v1.0.json`
- `markdown/standards/sage-failure-diagnosis-schema-v1.0.json`
- `markdown/standards/sage-operator-git-proposal-schema-v1.0.json`
- `markdown/standards/sage-operator-git-proposal-schema-v1.1.json`
- `markdown/standards/sage-operator-git-proposal-schema-v1.2.json`
- `sage-actionable-failure-registry.json`
- `sage-actionable-failures.json`
- `sage-change-authority.json`
- `sage-operating-contract-policy.json`
- `scripts/sage/sage-actionable-failure-audit.py`
- `scripts/sage/sage-actionable-failure-guardrail.py`
- `scripts/sage/sage-actionable-failure-self-test.py`
- `scripts/sage/sage-decision-primitives-guardrail.py`
- `scripts/sage/sage-file-delivery-guardrail.py`
- `scripts/sage/sage-git-safety-guardrail.py`
- `scripts/sage/sage-validator-runner.py`
- `scripts/sage/sage-yaml-metadata-self-test.py`
- `scripts/sage/sage-yaml-metadata-source-self-test.py`
- `scripts/sage/sage_actionable_failure.py`
- `scripts/sage/sage_yaml_metadata.py`
- `scripts/sage/workflow/authority.py`
- `scripts/sage/workflow/diagnosis.py`
- `scripts/sage/workflow/gaps.py`
- `scripts/sage/workflow/safety.py`
- `scripts/sage/workflow/selection.py`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/capability-gap-outcome-metrics.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-outcome-metrics.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/outcome-metrics-baseline.json`
- `scripts/sage/sage-outcome-metrics-guardrail.py`
- `scripts/sage/workflow/metrics.py`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/component-selection-root-enforcement.json`
- `markdown/evidence-artifacts/SAGE-K3-OPERATING-CONTRACT-20260801-001/root-enforcement-readiness.json`
- `scripts/sage/sage-operating-contract-guardrail.py`
- `scripts/sage/sage-operating-contract-self-test.py`
- `scripts/sage/workflows/operating_contract.py`
- `scripts/sage/workflow/markdown.py`
- `scripts/sage/workflow/evidence_records.py`
- `scripts/sage/workflows/evidence_navigation.py`
- `scripts/sage/sage-evidence-navigation-architecture-guardrail.py`
- `scripts/sage/workflows/generated_helper_delivery.py`
- `scripts/sage/sage-generated-helper-runtime-self-test.py`
- `markdown/standards/kalaxy3-sage-generated-helper-runtime-validation-process.md`
- `markdown/standards/sage-generated-helper-delivery-manifest-schema-v1.0.json`
- `scripts/sage/request_execution.py`
- `scripts/sage/workflows/request_execution.py`
- `scripts/sage/sage-request-execute.py`
- `scripts/sage/sage-request-execution-guardrail.py`
- `scripts/sage/sage-change-preflight.py`
- `markdown/standards/kalaxy3-sage-request-execution-process.md`
- `markdown/standards/sage-request-execution-proposal-schema-v1.0.json`
- `scripts/sage/request_planning.py`
- `scripts/sage/workflows/request_planning.py`
- `scripts/sage/sage-request-plan.py`
- `scripts/sage/sage-request-planning-guardrail.py`
- `scripts/sage/sage-domain-capability-gap-approve.py`
- `markdown/standards/kalaxy3-sage-request-planning-process.md`
- `markdown/standards/sage-request-planning-source-schema-v1.0.json`
- `markdown/standards/sage-request-planning-source-schema-v1.1.json`
- `markdown/standards/sage-request-planning-source-schema-v1.2.json`
- `scripts/sage/workflows/improvement_action_transition.py`
- `scripts/sage/sage-improvement-action-transition.py`
- `scripts/sage/sage-improvement-action-amendment.py`
- `scripts/sage/sage-improvement-action-transition-guardrail.py`
- `scripts/sage/workflows/routine_git_lifecycle.py`
- `scripts/sage/sage-routine-git-lifecycle.py`
- `scripts/sage/semantic_understanding.py`
- `scripts/sage/workflows/semantic_bootstrap.py`
- `scripts/sage/sage-action-bootstrap.py`
- `scripts/sage/sage-semantic-bootstrap-guardrail.py`
- `markdown/standards/kalaxy3-sage-semantic-bootstrap-process.md`
- `markdown/standards/sage-engineering-contribution-schema-v1.0.json`
- `markdown/standards/sage-semantic-understanding-schema-v1.0.json`
- `sage-recovery-policy.json`
- `markdown/standards/kalaxy3-sage-recovery-process.md`
- `markdown/standards/sage-recovery-next-boundary-schema-v1.0.json`
- `markdown/standards/sage-recovery-consumption-schema-v1.0.json`
- `scripts/sage/workflow/recovery.py`
- `scripts/sage/workflows/intent_to_outcome.py`
- `markdown/standards/kalaxy3-sage-evidence-record-standard.md`
- `markdown/standards/kalaxy3-sage-evidence-publication-process.md`
- `markdown/standards/sage-evidence-metadata-contract-v1.2.json`
- `markdown/templates/sage-evidence-record-template.md`
- `scripts/sage/sage-index.py`
- `scripts/sage/sage-publish.py`
- `sage-evidence-policy.json`
- `scripts/sage/sage-evidence-orchestrator.py`
- `markdown/standards/kalaxy3-sage-evidence-orchestration-process.md`
- `sage-evidence-template-policy.json`
- `scripts/sage/sage-evidence-template-guardrail.py`
- `sage-legacy-evidence-sources.json`
- `scripts/sage/legacy_evidence_projection.py`
- `scripts/sage/sage-legacy-evidence-project.py`
- `scripts/sage/sage-legacy-evidence-projection-guardrail.py`
- `markdown/standards/sage-legacy-evidence-projection-schema-v1.0.json`
- `markdown/standards/kalaxy3-sage-legacy-evidence-projection-process.md`
- `infrastructure/k3s-homelab/playbooks/tasks/longhorn.yml`
- `infrastructure/k3s-homelab/playbooks/tasks/network-storage.yml`
- `infrastructure/k3s-homelab/inventory/group_vars/all/main.yml`

## Baseline checks discovered

- `make sage-discovery-guardrail`
- `make sage-index-check`
- `make sage-evidence-guardrail`
- `make cluster-guardrails`

## Required validation discovered

- `make sage-self-test`
- `make sage-discovery-guardrail`
- `make sage-index-check`
- `make sage-operating-contract-check`
- `python3 scripts/sage/sage-evidence-navigation-architecture-guardrail.py`
- `make sage-evidence-self-test`
- `make sage-evidence-guardrail`
- `python3 scripts/sage/sage-evidence-template-guardrail.py`
- `make cluster-guardrails`

## Minimum evidence quality contract

1. Preserve the original requester language verbatim.
2. Apply the canonical generation request automatically.
3. Use package and record schema 1.2.
4. Populate every canonical metadata field in exact order.
5. Mirror front matter in the canonical Record metadata table.
6. Include an explicit TOC and every mandatory section in order.
7. Keep Five Ws and How consistent with canonical metadata.
8. Create atomic claims and trace each claim to evidence IDs.
9. Separate expected results, observations, and derived conclusions.
10. Preserve failed paths separately from the accepted final state.
11. Document rationale, alternatives, tradeoffs, and consequences.
12. Document security, rollback, rebuild, operations, and revalidation.
13. Identify limitations, assumptions, evidence gaps, and confidence.
14. Store artifacts under the permanent evidence ID and hash each file.
15. Produce one package that passes the repository publisher check.
16. Return only the package and standard check and publish commands.

## Repository working-session boundary

- Branch: `fix/sage-lifecycle-break-glass-20260907`
- HEAD: `76e012266b9518753c9614ef91daab870e680c69`
- Changed path count: 0
- Supplied terminal evidence files: 2

## Generator output contract

Generate one schema 1.2 SAGE evidence package ZIP.
The package must pass:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
```

Return only the package and these standard commands:

```bash
python3 scripts/sage/sage-publish.py check ~/Downloads/<package>.zip
python3 scripts/sage/sage-publish.py publish ~/Downloads/<package>.zip --push
```

Do not invent a separate metadata, navigation, validation, Git, or publication workflow.

## Explicit evidence gaps

- Supplied terminal evidence is included in this bundle.
