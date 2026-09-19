# Repository evidence

- Branch: `fix/sage-lifecycle-break-glass-20260907`
- HEAD: `d8b402c74ad26966e9128f26927fec7e97809ea2`
- HEAD subject: Add SAGE evidence for cognition-plane architecture direction

## Git status

```text
 M Makefile
 M infrastructure/k3s-homelab/helm-chart-lock.json
 M infrastructure/k3s-homelab/helm-repositories.json
 M infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
 M infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
 M infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
 M infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py
?? infrastructure/k3s-homelab/nvidia-platforms.json
?? infrastructure/k3s-homelab/playbooks/gpu.yml
?? infrastructure/k3s-homelab/playbooks/tasks/nvidia-device-plugin.yml
?? infrastructure/k3s-homelab/playbooks/tasks/nvidia-gpu-host.yml
?? infrastructure/k3s-homelab/playbooks/tasks/nvidia-gpu-qualification.yml
?? scripts/sage/sage-intent-front-door.py
```

## Changed paths

```text
Makefile
infrastructure/k3s-homelab/helm-chart-lock.json
infrastructure/k3s-homelab/helm-repositories.json
infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
infrastructure/k3s-homelab/nvidia-platforms.json
infrastructure/k3s-homelab/playbooks/gpu.yml
infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
infrastructure/k3s-homelab/playbooks/tasks/nvidia-device-plugin.yml
infrastructure/k3s-homelab/playbooks/tasks/nvidia-gpu-host.yml
infrastructure/k3s-homelab/playbooks/tasks/nvidia-gpu-qualification.yml
infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py
scripts/sage/sage-intent-front-door.py
```

## Unstaged diff stat

```text
 Makefile                                                          | 4 ++++
 infrastructure/k3s-homelab/helm-chart-lock.json                   | 7 +++++++
 infrastructure/k3s-homelab/helm-repositories.json                 | 5 +++++
 infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml       | 4 ++++
 infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml       | 8 ++++++--
 infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml    | 1 +
 .../k3s-homelab/scripts/sage-helm-repository-guardrail.py         | 1 +
 7 files changed, 28 insertions(+), 2 deletions(-)
```

## Unstaged diff

```text
diff --git a/Makefile b/Makefile
index 535bd21..a3390bc 100644
--- a/Makefile
+++ b/Makefile
@@ -731,3 +731,7 @@ sage-architecture-approval-self-test:
 
 sage-architecture-approval-guardrail:
 	$(PYTHON) scripts/sage/sage-architecture-approval-guardrail.py
+
+.PHONY: sage-intent-submit
+sage-intent-submit:
+	@python3 scripts/sage/sage-intent-front-door.py --request "$${SAGE_REQUEST:?SAGE_REQUEST is required}"
diff --git a/infrastructure/k3s-homelab/helm-chart-lock.json b/infrastructure/k3s-homelab/helm-chart-lock.json
index 6a8b960..b07816e 100644
--- a/infrastructure/k3s-homelab/helm-chart-lock.json
+++ b/infrastructure/k3s-homelab/helm-chart-lock.json
@@ -62,6 +62,13 @@
             "namespace": "storage",
             "release": "nfs-ssd",
             "version": "4.0.18"
+        },
+        "nvidia_device_plugin": {
+            "chart": "nvdp/nvidia-device-plugin",
+            "enabled_variable": "always",
+            "namespace": "nvidia-device-plugin",
+            "release": "nvidia-device-plugin",
+            "version": "0.19.3"
         }
     },
     "schema_version": "1.0"
diff --git a/infrastructure/k3s-homelab/helm-repositories.json b/infrastructure/k3s-homelab/helm-repositories.json
index 13ee2da..c8b6ff3 100644
--- a/infrastructure/k3s-homelab/helm-repositories.json
+++ b/infrastructure/k3s-homelab/helm-repositories.json
@@ -39,6 +39,11 @@
             "name": "longhorn",
             "url": "https://charts.longhorn.io",
             "url_sha256": "fb7e9a4773fc0b78c82a6905fc62e1a675b271aa1d6ed461a42068c3bcb93860"
+        },
+        {
+            "name": "nvdp",
+            "url": "https://nvidia.github.io/k8s-device-plugin",
+            "url_sha256": "8844777aa1ff4085f0d287677d69c57b7ff7d662f44e811758719d887dd86903"
         }
     ],
     "schema_version": "1.0"
diff --git a/infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml b/infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
index 80cde64..436223e 100644
--- a/infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
+++ b/infrastructure/k3s-homelab/inventory/host_vars/amd64-01.yml
@@ -32,6 +32,10 @@ kalaxy3_cost:
     useful_life_months: 60
     average_incremental_watts: 0.00
 
+kalaxy3_nvidia_pci_device_id: "10de:2204"
+kalaxy3_nvidia_subsystem_id: "3842:3982"
+kalaxy3_nvidia_expected_name_contains: "NVIDIA GeForce RTX 3090"
+
 kalaxy3_node_labels:
   kalaxy3.io/hardware-class: intel-i5-11600-128gb
   kalaxy3.io/cost-profile: amd64-high-memory
diff --git a/infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml b/infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
index 582d805..7885b15 100644
--- a/infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
+++ b/infrastructure/k3s-homelab/inventory/host_vars/amd64-02.yml
@@ -19,7 +19,7 @@ kalaxy3_cost:
     enabled: true
     kubernetes_schedulable: false
     vendor: nvidia
-    model: rtx-3060-ti
+    model: rtx-3060-lhr
     memory_gib: 8
     count: 1
     purchase_price_usd: 500.00
@@ -27,6 +27,10 @@ kalaxy3_cost:
     useful_life_months: 60
     average_incremental_watts: 0.00
 
+kalaxy3_nvidia_pci_device_id: "10de:2504"
+kalaxy3_nvidia_subsystem_id: "1462:397d"
+kalaxy3_nvidia_expected_name_contains: "NVIDIA GeForce RTX 3060"
+
 kalaxy3_node_labels:
   kalaxy3.io/hardware-class: intel-i5-11600-64gb
   kalaxy3.io/cost-profile: amd64-standard
@@ -36,5 +40,5 @@ kalaxy3_node_labels:
   kalaxy3.io/storage-role: longhorn
   kalaxy3.io/gpu-capable: "true"
   kalaxy3.io/gpu-vendor: nvidia
-  kalaxy3.io/gpu-model: rtx-3060-ti
+  kalaxy3.io/gpu-model: rtx-3060-lhr
   kalaxy3.io/gpu-memory-gib: "8"
diff --git a/infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml b/infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
index 20a1e2a..916b49c 100644
--- a/infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
+++ b/infrastructure/k3s-homelab/playbooks/phases/phase-08-intel.yml
@@ -1,3 +1,4 @@
 ---
 - import_playbook: ../prerequisites.yml
 - import_playbook: ../k3s.yml
+- import_playbook: ../gpu.yml
diff --git a/infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py b/infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py
index a6335f5..6775d87 100755
--- a/infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py
+++ b/infrastructure/k3s-homelab/scripts/sage-helm-repository-guardrail.py
@@ -24,6 +24,7 @@ TRUSTED_REPOSITORIES: Final = {
     "headlamp": "https://kubernetes-sigs.github.io/headlamp/",
     "longhorn": "https://charts.longhorn.io",
     "metallb": "https://metallb.github.io/metallb",
+    "nvdp": "https://nvidia.github.io/k8s-device-plugin",
     "nfs": (
         "https://kubernetes-sigs.github.io/"
         "nfs-subdir-external-provisioner"
```

## Staged diff stat

```text
(none)
```

## Staged diff

```text
(none)
```

## Recent commits

```text
d8b402c (HEAD -> fix/sage-lifecycle-break-glass-20260907, origin/fix/sage-lifecycle-break-glass-20260907) Add SAGE evidence for cognition-plane architecture direction
1048f1c Complete the bounded missing published-interface slice of SAGE-ACTION-20260813-001 so a persistent Architect-facing LLM
016cc29 Repair SAGE lifecycle authority composition
b381ddf (origin/feature/sage-action-20260907-001-path-neutral-causal-identity, feature/sage-action-20260907-001-path-neutral-causal-identity) record SAGE objective DoD bounding evidence
0a637f5 checkpoint SAGE LLM role-agent shared-context architecture
```
