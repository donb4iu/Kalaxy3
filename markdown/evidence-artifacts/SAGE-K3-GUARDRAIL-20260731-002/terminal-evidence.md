# Terminal evidence — SAGE-K3-GUARDRAIL-20260731-002

This artifact preserves the supplemental terminal evidence captured by the
repository-owned SAGE evidence orchestrator for the PR #5 CI portability
repairs.

- Input bundle: `kalaxy3-pr5-ci-repair-evidence-inputs-20260731-232149.zip`
- Repository: `donb4iu/Kalaxy3`
- Branch: `feature/actionable-guardrail-recovery`
- Implementation commit: `818fa5860c028ffd721c982861032adf1e9af1e0`
- Prior evidence: `SAGE-K3-GUARDRAIL-20260731-001`
- Capture result: repository orchestrator `capture` reported PASS
- Sensitive values: none included; secret-bearing repository files are
  represented only by hashes in the provenance artifact

````text
Kalaxy3 PR #5 supplemental CI-repair evidence chronology
========================================================

Prior evidence:
  Evidence ID: SAGE-K3-GUARDRAIL-20260731-001
  Evidence commit: c50270d740fa3bcca976b6ed20db07cfed545638
  Prior implementation boundary: 4c369193731e9fc7832d8c2a0e1e2718a6210e86

Supplemental implementation commits:
  91785bc Make actionable recovery paths CI-portable
  3fc7e45 Separate source-only and operator runtime self-tests
  818fa58 Separate YAML metadata source and runtime self-tests

CI failure chronology:
1. The actionable-failure catalog required
   infrastructure/k3s-homelab/.venv/bin/ansible-playbook to exist in a
   source-only GitHub checkout. The path is an operator-runtime prerequisite,
   not source-controlled recovery authority.
2. After correcting the catalog, make sage-guardrails still invoked the
   centralized-logging operator-runtime self-test through .venv/bin/python.
   Source-only CI had no generated virtual environment.
3. After separating centralized-logging test tiers, make sage-guardrails
   still invoked the YAML parsing test under system Python. PyYAML was not
   installed because parsing is an operator-runtime capability.

Generic remedies:
- canonical recovery required_paths now contain only portable repository
  authority; generated runtime prerequisites remain in commands and guidance;
- source-only and operator-runtime tests are explicit, complementary tiers;
- source-only tests execute with python3 -S and no site packages;
- optional PyYAML loading is lazy and missing-parser errors are actionable;
- operator tests retain the repository-managed .venv, inventory parsing, and
  live Loki validation.

Accepted final state:
- source-only centralized-logging contract test passes without .venv or PyYAML;
- source-only YAML metadata contract test passes without PyYAML;
- repository-managed operator tests still pass;
- live centralized-logging validation still passes;
- PR #5 GitHub checks passed at
  818fa5860c028ffd721c982861032adf1e9af1e0;
- the green GitHub checks screenshot is supplied separately to the final
  evidence generator.

Remaining constraints:
- source-only tests do not replace operator-runtime or live-cluster tests;
- generated runtime environments remain necessary for parsing inventory and
  validating the active cluster;
- future aggregate guardrail additions must explicitly classify their test
  tier and dependency boundary.

$ git log --oneline --decorate c50270d..HEAD
818fa58 (HEAD -> feature/actionable-guardrail-recovery, origin/feature/actionable-guardrail-recovery) Separate YAML metadata source and runtime self-tests
3fc7e45 Separate source-only and operator runtime self-tests
91785bc Make actionable recovery paths CI-portable
[exit=0]

$ git status --short --branch
## feature/actionable-guardrail-recovery...origin/feature/actionable-guardrail-recovery
[exit=0]

$ make sage-guardrails
python3 scripts/sage/sage-actionable-failure-self-test.py
PASS reusable actionable-failure renderer
PASS original incident regression cases
PASS actionable-failure negative mutation tests
PASS validator bootstrap/runtime failure regression
PASS source-only recovery-path portability regression
Kalaxy3 SAGE actionable failure self-test: PASS
python3 scripts/sage/sage-actionable-failure-guardrail.py
PASS actionable-failure catalog and recovery authority
PASS actionable-failure validator registry
PASS actionable-failure Make entry points
Kalaxy3 SAGE actionable-failure guardrail: PASS
python3 scripts/sage/sage-validator-runner.py --validator-id sage.actionable_failure_self_test --attempted-action 'Validate the SAGE failure framework.' --working-directory . --recovery-command 'python3 scripts/sage/sage-actionable-failure-self-test.py' --authoritative-path scripts/sage/sage-actionable-failure-self-test.py -- python3 scripts/sage/sage-actionable-failure-self-test.py
PASS reusable actionable-failure renderer
PASS original incident regression cases
PASS actionable-failure negative mutation tests
PASS validator bootstrap/runtime failure regression
PASS source-only recovery-path portability regression
Kalaxy3 SAGE actionable failure self-test: PASS
SAGE validator runtime: PASS (sage.actionable_failure_self_test)
/Applications/Xcode.app/Contents/Developer/usr/bin/make -C infrastructure/k3s-homelab centralized-logging-runtime-source-self-test
python3 -S scripts/validate-centralized-logging-runtime-source-self-test.py
PASS runtime validator source-only import without PyYAML
PASS locked-release interpretation
PASS dynamic all-node label selection
PASS live runtime entry-point contract
Kalaxy3 centralized logging source-only self-test: PASS
python3 -S scripts/sage/sage-yaml-metadata-source-self-test.py
PASS plain YAML metadata type contract
PASS opaque tagged-value redaction contract
PASS actionable missing-PyYAML recovery
Kalaxy3 YAML metadata source-only self-test: PASS
python3 scripts/sage/sage-change-preflight.py --self-test
Kalaxy3 SAGE change discovery self-test: PASS
python3 scripts/sage/sage-lessons.py --self-test
Kalaxy3 SAGE lessons discovery self-test: PASS
python3 scripts/sage/sage-change-discovery-guardrail.py
PASS repository-root SAGE discovery entry points
PASS machine-readable change-authority map
PASS authoritative file and directory references
PASS request and changed-path classification tests
PASS literal request transport through root Makefile
PASS authority-map mutation negative tests
Kalaxy3 SAGE discovery guardrail: PASS
python3 scripts/sage/sage-evidence-orchestrator.py self-test
Kalaxy3 SAGE evidence orchestration self-test: PASS
python3 scripts/sage/sage-evidence-orchestration-guardrail.py
PASS canonical evidence request integrity
PASS repository-owned evidence policy and authorities
PASS plain-language evidence request regression tests
PASS original requester language preservation
PASS root Make evidence-generation entry points
PASS evidence policy mutation negative tests
Kalaxy3 SAGE evidence orchestration guardrail: PASS
python3 scripts/sage/sage-active-session.py --self-test
PASS canonical active-session registry contract
PASS duplicate session rejection
PASS label-and-digest-only command storage
PASS unknown measurements remain null
PASS known-failure metrics are preserved
PASS unsafe raw command data is rejected
Kalaxy3 SAGE active-session self-test: PASS
python3 scripts/sage/sage-active-session-guardrail.py
PASS canonical active-session policy references
PASS active-session and event schema contract
PASS valid active-session registry
PASS authority and path classification
PASS local runtime ledger exclusion
PASS duplicate and open-gate mutation negatives
PASS repository-owned recorder self-test
Kalaxy3 SAGE active-session guardrail: PASS
python3 scripts/sage/sage-session-close.py --self-test
PASS completed-session schema contract
PASS final active-session summary token replacement
PASS unavailable prediction actual remains inconclusive
PASS numeric prediction results match inclusive ranges
PASS uncaptured command failures render safely
PASS completed registry uniqueness and field validation
PASS fsync-backed registry serialization
PASS close remains dry-run unless --apply is explicit
Kalaxy3 SAGE session close self-test: PASS
python3 scripts/sage/sage-session-score.py --self-test
PASS raw session metrics preserved
PASS required delivery and learning rates derived
PASS point and inclusive-range prediction scoring
PASS scalar-neutral predictions allow unavailable actuals
PASS zero denominators and zero actuals return null
PASS unavailable raw measurements remain null
PASS confidence-bucket range-hit summaries
PASS session scoring mutation negative tests
Kalaxy3 SAGE session scoring self-test: PASS
python3 scripts/sage/sage-feedback-compare.py --self-test
PASS recurring and one-time cost comparisons
PASS unit-economics and avoidable-rework comparisons
PASS observability direction and window comparisons
PASS provenance and measurement types preserved
PASS zero-baseline percentages remain null
PASS comparison mutation negative tests
Kalaxy3 SAGE feedback comparison self-test: PASS
python3 scripts/sage/sage-feedback-guardrail.py
PASS canonical feedback comparison policy
PASS empty feedback baseline registry
PASS cost and observability comparison schema
PASS matching currency, units, metrics, and directions
PASS provenance and measurement-type preservation
PASS zero-baseline and composite-score policies
PASS feedback policy mutation negative tests
Kalaxy3 SAGE feedback guardrail: PASS
python3 scripts/sage/sage-candidate-lifecycle.py --self-test
PASS canonical candidate lifecycle policy
PASS append-only contiguous transition history
PASS dry-run lifecycle registration
PASS guarded repository-only validation path
PASS closed deployment gate blocks activation
PASS branch, remote, and expected HEAD checks
PASS lifecycle mutation negative tests
Kalaxy3 SAGE candidate lifecycle self-test: PASS
python3 scripts/sage/sage-candidate-lifecycle-guardrail.py
PASS canonical candidate lifecycle policy
PASS candidate and lifecycle status consistency
PASS append-only contiguous lifecycle history
PASS foundational staged implementation
PASS closed deployment gate preserved
PASS activation prerequisites fail closed
PASS repository-only validation bypass is guarded
PASS lifecycle policy mutation negative tests
Kalaxy3 SAGE candidate lifecycle guardrail: PASS
python3 scripts/sage/sage-improvement-actions.py --self-test
PASS canonical improvement-action lifecycle
PASS evidence-backed registration
PASS append-only contiguous action history
PASS dry-run registration and transition planning
PASS explicit apply required for mutation
PASS invalid transitions fail closed
Kalaxy3 SAGE improvement-action self-test: PASS
python3 scripts/sage/sage-baseline-extract.py --self-test
PASS Git numstat baseline parsing
PASS registry-count extraction contract
PASS unavailable session metrics remain null
PASS populated-session aggregation fails closed
PASS baseline check normalization
Kalaxy3 SAGE baseline extraction self-test: PASS
python3 scripts/sage/sage-learning-guardrail.py
PASS canonical improvement-action lifecycle policy
PASS evidence-backed action registry
PASS append-only dry-run action tooling
PASS deterministic repository baseline extraction
PASS unavailable process metrics remain null
PASS prediction and provenance references preserved
PASS composite baseline scoring remains closed
PASS learning-policy mutation negative tests
Kalaxy3 SAGE learning guardrail: PASS
python3 scripts/sage/sage-post-session-review.py --self-test
PASS canonical post-session questions
PASS canonical session linkage
PASS known-failure and lesson-use review
PASS unavailable failure rework remains null
PASS four-plane feedback review
PASS lesson-to-control decision coverage
PASS action drafts validated without mutation
PASS no-action decisions require rationale
PASS post-session review mutation negative tests
Kalaxy3 SAGE post-session review self-test: PASS
python3 scripts/sage/sage-post-session-review-guardrail.py
PASS canonical post-session review policy
PASS canonical post-session review registry
PASS canonical questions and session linkage
PASS known-failure and lesson-use review contract
PASS unavailable failure rework remains nullable
PASS four-plane feedback review contract
PASS lesson-to-control decision coverage
PASS action registration remains a separate mutation
PASS registered actions match review drafts
PASS expected negative Git tests remain quiet
PASS post-session policy mutation negative tests
Kalaxy3 SAGE post-session review guardrail: PASS
python3 scripts/sage/sage-continuous-improvement-guardrail.py
PASS canonical continuous-improvement policy
PASS four-plane feedback contract
PASS immutable versioned prediction policy
PASS candidate and session schema contracts
PASS deterministic session scorecard contract
PASS scalar-neutral prediction closeout contract
PASS unavailable session measurements remain nullable
PASS representative candidate and session records
PASS foundational change candidate registry
PASS discovery prediction v1 remains immutable
PASS machine-readable lesson registry
PASS required seed lessons and preventive controls
PASS multidimensional sizing and confidence policy
PASS cost, observability, and process-metric policy
PASS session rate and prediction scoring policy
PASS live-session measurement semantics
PASS frequent cohesive feature-branch push policy
PASS canonical lesson, valid action, and valid session registries
PASS continuous-improvement mutation negative tests
Kalaxy3 SAGE continuous-improvement guardrail: PASS
python3 scripts/sage/sage-index.py check
CURATION: markdown/installation/k3s-api-ha-kube-vip.md needs registry review
CURATION: markdown/installation/k3s-etcd-baseline-backup-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md needs registry review
CURATION: markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-kubecost-installation-and-verification.md needs registry review
CURATION: markdown/installation/kalaxy3-minio-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-observability-and-kubecost.md needs registry review
CURATION: markdown/installation/kalaxy3-protected-ui-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md needs registry review
CURATION: markdown/installation/longhorn-kubecost-intel-node-preparation.md needs registry review
CURATION: markdown/installation/old/amd64-nocloud-seed-helper.md needs registry review
CURATION: markdown/installation/old/flash.md needs registry review
CURATION: markdown/installation/old/ubuntu-installation-and-node-provisioning-v2.md needs registry review
CURATION: markdown/installation/old/ubuntu-node-provisioning-fixed-amd64.md needs registry review
CURATION: markdown/installation/old/ubuntu-node-provisioning.md needs registry review
CURATION: markdown/installation/ubuntu-node-provisioning-fixed.md needs registry review
CURATION: markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md needs registry review
CURATION: markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md needs registry review
LEGACY: markdown/installation/k3s-api-ha-kube-vip.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/k3s-etcd-baseline-backup-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md indexed as sage-legacy with inferred metadata
LEGACY: markdown/installation/kalaxy3-kubecost-installation-and-verification.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-minio-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-observability-and-kubecost.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-protected-ui-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/longhorn-kubecost-intel-node-preparation.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/amd64-nocloud-seed-helper.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/flash.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-installation-and-node-provisioning-v2.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-node-provisioning-fixed-amd64.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-node-provisioning.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/ubuntu-node-provisioning-fixed.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md indexed as sage-legacy with inferred metadata
LEGACY: markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md indexed as sage-legacy with inferred metadata
SAGE evidence reconciliation: PASS
Records:          34
Generated paths:  48
Changed paths:    0
Kalaxy3 repository SAGE guardrails: PASS
[exit=0]

$ make centralized-logging-runtime-source-self-test
/Applications/Xcode.app/Contents/Developer/usr/bin/make -C infrastructure/k3s-homelab centralized-logging-runtime-source-self-test
python3 -S scripts/validate-centralized-logging-runtime-source-self-test.py
PASS runtime validator source-only import without PyYAML
PASS locked-release interpretation
PASS dynamic all-node label selection
PASS live runtime entry-point contract
Kalaxy3 centralized logging source-only self-test: PASS
[exit=0]

$ make sage-yaml-metadata-source-self-test
python3 -S scripts/sage/sage-yaml-metadata-source-self-test.py
PASS plain YAML metadata type contract
PASS opaque tagged-value redaction contract
PASS actionable missing-PyYAML recovery
Kalaxy3 YAML metadata source-only self-test: PASS
[exit=0]

$ make centralized-logging-runtime-self-test
.venv/bin/python scripts/validate-centralized-logging-runtime-self-test.py
PASS vault-tolerant inventory metadata
Kalaxy3 centralized logging runtime self-test: PASS
[exit=0]

$ make centralized-logging-runtime-validate
python3 ../../scripts/sage/sage-validator-runner.py --validator-id centralized_logging.runtime --attempted-action 'Validate active centralized logging.' --working-directory infrastructure/k3s-homelab --recovery-command 'make centralized-logging-runtime-validate' --authoritative-path infrastructure/k3s-homelab/inventory/group_vars/all/main.yml --authoritative-path infrastructure/k3s-homelab/helm-chart-lock.json --authoritative-path infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py --integrity-requirement 'Preserve activation state, chart locks, storage, and logs.' -- .venv/bin/python scripts/validate-centralized-logging-runtime.py
Kalaxy3 centralized logging runtime validation: PASS
{
  "datasource_configmaps": 2,
  "helm_releases": {
    "fluent-bit-collector": "1.0.9",
    "loki": "18.5.4"
  },
  "kubectl": "/usr/local/bin/kubectl",
  "loki_data": {
    "covered_nodes": [
      "amd64-01",
      "amd64-02",
      "arm64-01",
      "arm64-02",
      "arm64-03",
      "arm64-04",
      "arm64-05"
    ],
    "node_label": "node",
    "recent_query_results": 1
  },
  "storage": {
    "phase": "Bound",
    "requested": "40Gi",
    "storage_class": "longhorn"
  },
  "workloads": {
    "collectors": 7,
    "gateway": 1,
    "loki": 1
  }
}
SAGE validator runtime: PASS (centralized_logging.runtime)
[exit=0]

$ make sage-index-check
python3 scripts/sage/sage-index.py check
CURATION: markdown/installation/k3s-api-ha-kube-vip.md needs registry review
CURATION: markdown/installation/k3s-etcd-baseline-backup-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md needs registry review
CURATION: markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-kubecost-installation-and-verification.md needs registry review
CURATION: markdown/installation/kalaxy3-minio-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-observability-and-kubecost.md needs registry review
CURATION: markdown/installation/kalaxy3-protected-ui-installation-evidence.md needs registry review
CURATION: markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md needs registry review
CURATION: markdown/installation/longhorn-kubecost-intel-node-preparation.md needs registry review
CURATION: markdown/installation/old/amd64-nocloud-seed-helper.md needs registry review
CURATION: markdown/installation/old/flash.md needs registry review
CURATION: markdown/installation/old/ubuntu-installation-and-node-provisioning-v2.md needs registry review
CURATION: markdown/installation/old/ubuntu-node-provisioning-fixed-amd64.md needs registry review
CURATION: markdown/installation/old/ubuntu-node-provisioning.md needs registry review
CURATION: markdown/installation/ubuntu-node-provisioning-fixed.md needs registry review
CURATION: markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md needs registry review
CURATION: markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md needs registry review
LEGACY: markdown/installation/k3s-api-ha-kube-vip.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/k3s-etcd-baseline-backup-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-amd64-02-k3s-longhorn-node-addition.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-amd64-node-and-longhorn-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-intel-pi-admin-access-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-kubecost-calibration-sage-evidence.md indexed as sage-legacy with inferred metadata
LEGACY: markdown/installation/kalaxy3-kubecost-installation-and-verification.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-minio-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-observability-and-kubecost.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-protected-ui-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/kalaxy3-traefik-dashboard-installation-evidence.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/longhorn-kubecost-intel-node-preparation.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/amd64-nocloud-seed-helper.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/flash.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-installation-and-node-provisioning-v2.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-node-provisioning-fixed-amd64.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/old/ubuntu-node-provisioning.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/installation/ubuntu-node-provisioning-fixed.md indexed as legacy-evidence with inferred metadata
LEGACY: markdown/operations/kalaxy3-sage-canonical-metadata-contract-evidence.md indexed as sage-legacy with inferred metadata
LEGACY: markdown/operations/kalaxy3-sage-evidence-publication-process-evidence.md indexed as sage-legacy with inferred metadata
SAGE evidence reconciliation: PASS
Records:          34
Generated paths:  48
Changed paths:    0
[exit=0]

$ make sage-evidence-guardrail
python3 scripts/sage/sage-evidence-orchestration-guardrail.py
PASS canonical evidence request integrity
PASS repository-owned evidence policy and authorities
PASS plain-language evidence request regression tests
PASS original requester language preservation
PASS root Make evidence-generation entry points
PASS evidence policy mutation negative tests
Kalaxy3 SAGE evidence orchestration guardrail: PASS
[exit=0]
````
