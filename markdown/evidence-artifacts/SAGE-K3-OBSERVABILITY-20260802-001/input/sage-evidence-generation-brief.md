# Kalaxy3 SAGE evidence-generation brief

## Original requester language

```text
Generate a SAGE-compliant evidence package for the completed Kalaxy3 Grafana operations dashboard, telemetry scrape coverage, and actionable alerting work on feature/grafana-operations-dashboard. Include all available terminal evidence and JSON receipts; explain what was done, why it was done, and how it was validated; preserve the complete failure chronology and corrective lessons; identify the five implementation commits and live acceptance outcomes; document rollback, rebuild, remaining validation gaps, evidence-use metrics, recurrence indicators, and reusable workflow improvements; and prepare the package for SAGE publication and pull-request closeout.
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
- `evidence-orchestration`
- `continuous-improvement`
- `helm-platform`
- `observability`
- `workflow-primitives`

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
- `markdown/standards/kalaxy3-sage-evidence-record-standard.md`
- `markdown/standards/kalaxy3-sage-evidence-publication-process.md`
- `markdown/standards/sage-evidence-metadata-contract-v1.2.json`
- `markdown/templates/sage-evidence-record-template.md`
- `scripts/sage/sage-index.py`
- `scripts/sage/sage-publish.py`
- `sage-evidence-policy.json`
- `scripts/sage/sage-evidence-orchestrator.py`
- `markdown/standards/kalaxy3-sage-evidence-orchestration-process.md`
- `scripts/sage/sage-evidence-orchestration-guardrail.py`
- `markdown/standards/kalaxy3-sage-continuous-improvement-process.md`
- `markdown/standards/sage-active-session-schema-v1.0.json`
- `markdown/standards/sage-change-candidate-lifecycle-schema-v1.0.json`
- `markdown/standards/sage-change-candidate-schema-v1.0.json`
- `markdown/standards/sage-continuous-improvement-baseline-schema-v1.0.json`
- `markdown/standards/sage-feedback-comparison-schema-v1.0.json`
- `markdown/standards/sage-improvement-action-schema-v1.0.json`
- `markdown/standards/sage-outcome-metrics-schema-v1.0.json`
- `markdown/standards/sage-post-session-review-schema-v1.0.json`
- `markdown/standards/sage-session-improvement-schema-v1.0.json`
- `markdown/standards/sage-session-scorecard-schema-v1.0.json`
- `sage-active-session-registry.json`
- `sage-change-candidate-lifecycle-registry.json`
- `sage-change-candidate-registry.json`
- `sage-continuous-improvement-baseline-registry.json`
- `sage-continuous-improvement-policy.json`
- `sage-feedback-baseline-registry.json`
- `sage-improvement-actions.json`
- `sage-lessons.json`
- `sage-post-session-review-registry.json`
- `sage-session-improvement-registry.json`
- `scripts/sage/sage-active-session-guardrail.py`
- `scripts/sage/sage-active-session.py`
- `scripts/sage/sage-baseline-extract.py`
- `scripts/sage/sage-candidate-lifecycle-guardrail.py`
- `scripts/sage/sage-candidate-lifecycle.py`
- `scripts/sage/sage-continuous-improvement-guardrail.py`
- `scripts/sage/sage-feedback-compare.py`
- `scripts/sage/sage-feedback-guardrail.py`
- `scripts/sage/sage-improvement-actions.py`
- `scripts/sage/sage-learning-guardrail.py`
- `scripts/sage/sage-lessons.py`
- `scripts/sage/sage-post-session-review-guardrail.py`
- `scripts/sage/sage-post-session-review.py`
- `scripts/sage/sage-session-score.py`
- `infrastructure/k3s-homelab/helm-repositories.json`
- `infrastructure/k3s-homelab/helm-chart-lock.json`
- `infrastructure/k3s-homelab/playbooks/platform.yml`
- `infrastructure/k3s-homelab/scripts/sage-source-guardrails.py`
- `infrastructure/k3s-homelab/scripts/sage-deployment-guardrail.py`
- `infrastructure/k3s-homelab/playbooks/tasks/observability.yml`
- `infrastructure/k3s-homelab/inventory/group_vars/all/main.yml`
- `markdown/standards/kalaxy3-sage-workflow-primitives-process.md`
- `markdown/standards/kalaxy3-sage-workflow-support-process.md`
- `markdown/standards/sage-capability-gap-receipt-schema-v1.0.json`
- `markdown/standards/sage-component-selection-manifest-schema-v1.0.json`
- `markdown/standards/sage-workflow-primitives-schema-v1.0.json`
- `sage-workflow-primitives.json`
- `scripts/sage/sage-action-id.py`
- `scripts/sage/sage-python-static-guardrail.py`
- `scripts/sage/sage-workflow-primitives-guardrail.py`
- `scripts/sage/sage-workflow-primitives-self-test.py`
- `scripts/sage/sage-workflow-support-guardrail.py`
- `scripts/sage/sage-workflow-usage.py`
- `scripts/sage/sage_identifiers.py`
- `scripts/sage/workflow/`
- `scripts/sage/workflow/files.py`
- `scripts/sage/workflow/git_inspect.py`
- `scripts/sage/workflow/proposal.py`
- `scripts/sage/workflows/`

## Baseline checks discovered

- `make sage-discovery-guardrail`
- `make sage-index-check`
- `make sage-evidence-guardrail`
- `make sage-active-session-self-test`
- `make sage-review-self-test`
- `make sage-learning-self-test`
- `make sage-candidate-self-test`
- `make sage-feedback-self-test`
- `make sage-session-self-test`
- `make sage-improvement-policy-check`
- `make helm-repository-guardrail`
- `make source-guardrails`
- `make deployment-guardrail`
- `make sage-workflow-support-self-test`
- `make sage-workflow-support-guardrail`
- `make sage-workflow-self-test`
- `make sage-workflow-guardrail`
- `make sage-operating-contract-check`

## Required validation discovered

- `make sage-self-test`
- `make sage-discovery-guardrail`
- `make sage-index-check`
- `make sage-operating-contract-check`
- `make sage-evidence-self-test`
- `make sage-evidence-guardrail`
- `make sage-active-session-self-test`
- `make sage-review-self-test`
- `make sage-learning-self-test`
- `make sage-candidate-self-test`
- `make sage-feedback-self-test`
- `make sage-session-self-test`
- `make sage-improvement-policy-check`
- `make sage-guardrails`
- `make source-guardrails`
- `make deployment-guardrail`
- `make cluster-guardrails`
- `make sage-workflow-self-test`
- `make sage-workflow-guardrail`
- `make sage-workflow-support-self-test`
- `make sage-workflow-support-guardrail`
- `make sage-workflow-usage`

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

- Branch: `feature/grafana-operations-dashboard`
- HEAD: `6250100ebf015e5243854a32d2a1741d73ed4484`
- Changed path count: 0
- Supplied terminal evidence files: 14

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
