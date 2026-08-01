# Terminal evidence — SAGE-K3-GUARDRAIL-20260731-001

This artifact preserves the terminal evidence captured by the repository-owned
SAGE evidence orchestrator for the actionable guardrail recovery session.

- Input bundle: `kalaxy3-actionable-guardrail-evidence-inputs-20260731-221335.zip`
- Repository: `donb4iu/Kalaxy3`
- Branch: `feature/actionable-guardrail-recovery`
- Implementation commit: `4c369193731e9fc7832d8c2a0e1e2718a6210e86`
- Capture result: repository orchestrator `capture` reported PASS
- Sensitive values: none included; encrypted YAML payloads were not captured

```text
Kalaxy3 actionable-guardrail recovery evidence chronology
========================================================

Branch:
  feature/actionable-guardrail-recovery

Commits:
  78b839d Define actionable SAGE failure contract
  3aeac1e Add reusable SAGE actionable failure framework
  054f625 Migrate centralized logging failures to shared recovery
  4c36919 Add vault-tolerant active logging runtime validation

Observed failures retained as regression evidence:
1. Global/Homebrew Ansible was invalid because repository validation requires
   the pinned .venv interpreter and dependencies.
2. The staged render validator was invoked after centralized logging was
   activated; changing the lifecycle gate to satisfy it was prohibited.
3. Dynamic dataclass import failed because the module was not placed in
   sys.modules before exec_module.
4. A generated helper silently exited after truncation because it never
   defined or invoked main().
5. yaml.safe_load failed on an unrelated !vault value when only a plain
   feature gate was needed.
6. A repair helper assumed one exact source anchor instead of inspecting the
   actual ROOT layout.
7. Evidence closeout incorrectly assumed a generate subcommand; the actual
   repository contract is brief, capture, check, and self-test.

Generic protections:
- reusable actionable-failure contract, renderer, catalog, and guardrail;
- validator runtime wrapper with dependency-free emergency reporting;
- real runtime and terminal-output tests;
- helper entry-point and startup-marker tests;
- opaque-tag YAML metadata loading without decrypting or exposing secrets;
- staged-versus-active lifecycle routing;
- validator-candidate coverage audit;
- repository interface discovery instead of invented commands.

Validated active centralized logging:
- fluent-bit-collector 1.0.9;
- Loki 18.5.4;
- seven ready collectors;
- Loki 1/1 and gateway 1/1;
- Bound 40Gi Longhorn storage;
- Grafana datasource configuration;
- recent queryable Loki data;
- coverage for amd64-01, amd64-02, and arm64-01 through arm64-05.

Remaining scope:
- classify unregistered validator candidates by operational risk;
- separate active validators from historical, generated, bootstrap-only,
  and false-positive candidates;
- migrate coherent families in separate validated checkpoints.

$ git log --oneline --decorate 78b839d^..HEAD
4c36919 (HEAD -> feature/actionable-guardrail-recovery, origin/feature/actionable-guardrail-recovery) Add vault-tolerant active logging runtime validation
054f625 Migrate centralized logging failures to shared recovery
3aeac1e Add reusable SAGE actionable failure framework
78b839d Define actionable SAGE failure contract
[exit=0]

$ git status --short --branch
## feature/actionable-guardrail-recovery...origin/feature/actionable-guardrail-recovery
[exit=0]

$ python3 scripts/sage/sage-actionable-failure-audit.py --summary
Kalaxy3 actionable-failure coverage audit
candidate_count: 74
registered_count: 2
migrated_count: 2
planned_count: 0
unregistered_count: 72
Unregistered validator candidates:
  - Makefile
  - cloud-init-setup/k3-node-provisioning/ansible/configure-amd64-nodes.yml
  - cloud-init-setup/k3-node-provisioning/ansible/files/prepare-minio-disk.sh
  - cloud-init-setup/k3-node-provisioning/setup/cloud-config-arm64-01.yml
  - cloud-init-setup/k3-node-provisioning/setup/cloud-config-arm64-02.yml
  - cloud-init-setup/k3-node-provisioning/setup/cloud-config-arm64-03.yml
  - cloud-init-setup/k3-node-provisioning/setup/cloud-config-arm64-04.yml
  - cloud-init-setup/k3-node-provisioning/setup/cloud-config-arm64-05.yml
  - cloud-init-setup/nodes/ansible-microk8s/microk8s-ansible/roles/storage/tasks/main.yml
  - cloud-init-setup/nodes/arm64-01.yml
  - cloud-init-setup/nodes/arm64-02.yml
  - cloud-init-setup/nodes/arm64-03.yml
  - cloud-init-setup/nodes/arm64-04.yml
  - cloud-init-setup/nodes/arm64-05.yml
  - cloud-init-setup/nodes/new-amd64-01.yml
  - cloud-init-setup/nodes/new-amd64-02.yml
  - cloud-init-setup/nodes/new-amd64-03.yml
  - docs/evidence-artifacts/SAGE-K3-GOVERNANCE-20260726-003/validate-daux-landing-page.sh
  - infrastructure/k3s-homelab/Makefile
  - infrastructure/k3s-homelab/playbooks/access-baseline.yml
  - infrastructure/k3s-homelab/playbooks/bootstrap-static-network.yml
  - infrastructure/k3s-homelab/playbooks/longhorn-prerequisites.yml
  - infrastructure/k3s-homelab/playbooks/phases/phase-00-readiness.yml
  - infrastructure/k3s-homelab/playbooks/platform.yml
  - infrastructure/k3s-homelab/playbooks/prerequisites.yml
  - infrastructure/k3s-homelab/playbooks/reconcile-centralized-logging-labels.yml
  - infrastructure/k3s-homelab/playbooks/tasks/install-k3s.yml
  - infrastructure/k3s-homelab/playbooks/tasks/kubecost-calibration.yml
  - infrastructure/k3s-homelab/playbooks/tasks/minio.yml
  - infrastructure/k3s-homelab/playbooks/tasks/observability.yml
  - ... 42 more
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

$ make sage-self-test
python3 scripts/sage/sage-actionable-failure-self-test.py
PASS reusable actionable-failure renderer
PASS original incident regression cases
PASS actionable-failure negative mutation tests
PASS validator bootstrap/runtime failure regression
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
Kalaxy3 SAGE actionable failure self-test: PASS
SAGE validator runtime: PASS (sage.actionable_failure_self_test)
/Applications/Xcode.app/Contents/Developer/usr/bin/make -C infrastructure/k3s-homelab centralized-logging-runtime-self-test
.venv/bin/python scripts/validate-centralized-logging-runtime-self-test.py
PASS vault-tolerant inventory metadata
Kalaxy3 centralized logging runtime self-test: PASS
python3 scripts/sage/sage-yaml-metadata-self-test.py
PASS ordinary YAML metadata
PASS vault and unknown tags remain opaque
PASS opaque values reject boolean coercion
Kalaxy3 SAGE YAML metadata self-test: PASS
python3 scripts/sage/sage-change-preflight.py --self-test
Kalaxy3 SAGE change discovery self-test: PASS
python3 scripts/sage/sage-lessons.py --self-test
Kalaxy3 SAGE lessons discovery self-test: PASS
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
Records:          33
Generated paths:  47
Changed paths:    0
[exit=0]

$ make sage-evidence-self-test
python3 scripts/sage/sage-evidence-orchestrator.py self-test
Kalaxy3 SAGE evidence orchestration self-test: PASS
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
```
