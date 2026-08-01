VENV := .venv
COLLECTIONS := .ansible/collections
TOOLS := .tools
UV := $(TOOLS)/uv
HELM := $(TOOLS)/helm
HELM_WRAPPER := scripts/helm
HELM_VERSION := $(shell cat .helm-version)
SOURCE_GUARDRAILS := python3 scripts/sage-source-guardrails.py
DEPLOYMENT_GUARDRAIL := python3 scripts/sage-deployment-guardrail.py
K3S_GUARDRAIL := python3 scripts/sage-k3s-guardrail.py
HELM_REPOSITORY_GUARDRAIL := python3 scripts/sage-helm-repository-guardrail.py
SAGE_DISCOVERY_GUARDRAIL := python3 ../../scripts/sage/sage-change-discovery-guardrail.py
HELM_LOCK_RECONCILE := $(VENV)/bin/python scripts/helm-lock-reconcile.py
ANSIBLE_ACCESS_PREFLIGHT := $(VENV)/bin/python scripts/ansible-access-preflight.py
UV_VERSION := $(shell cat .uv-version)
PYTHON_VERSION := $(shell cat .python-version)
PYTHON_INSTALL_DIR := $(abspath .python)
UV_CACHE_DIR := $(abspath .uv-cache)
ANSIBLE := $(VENV)/bin/ansible-playbook
PREFLIGHT := $(VENV)/bin/python scripts/controller-preflight.py
VAULT := --ask-vault-pass

.PHONY: install controller-uv controller-helm controller-bootstrap \
        controller-core-preflight controller-helm-preflight \
        cluster-access-preflight controller-preflight \
        sage-discovery-guardrail source-guardrails helm-repository-guardrail \
        k3s-release-guardrail deployment-guardrail \
        helm-lock-reconcile ssh-auth-preflight privilege-preflight \
        ansible-access-preflight bootstrap-guardrails k3s-guardrails \
        cluster-guardrails guardrails \
        recovery-guardrails confirm-uninstall uninstall-syntax \
        helm-release-inventory access-baseline access-baseline-bootstrap bootstrap-ssh-key verify-ssh-host-keys ping \
        phase-0 phase-1 phase-2 phase-3 phase-4 phase-5 \
        phase-6 phase-7 phase-8 survey-clean validate-1 validate-2 validate-3 \
        validate-4 validate-5 validate-6 deploy uninstall syntax

install: controller-bootstrap

controller-uv:
	python3 scripts/install-repository-uv.py

controller-helm:
	python3 scripts/install-repository-helm.py

controller-bootstrap: controller-uv controller-helm
	UV_MANAGED_PYTHON=1 \
	UV_PYTHON_INSTALL_DIR="$(PYTHON_INSTALL_DIR)" \
	UV_CACHE_DIR="$(UV_CACHE_DIR)" \
	$(UV) python install "$(PYTHON_VERSION)"
	rm -rf $(VENV)
	UV_MANAGED_PYTHON=1 \
	UV_PYTHON_INSTALL_DIR="$(PYTHON_INSTALL_DIR)" \
	UV_CACHE_DIR="$(UV_CACHE_DIR)" \
	$(UV) venv --python "$(PYTHON_VERSION)" $(VENV)
	UV_CACHE_DIR="$(UV_CACHE_DIR)" \
	$(UV) pip install --python $(VENV)/bin/python -r requirements.txt
	mkdir -p $(COLLECTIONS)
	$(VENV)/bin/ansible-galaxy collection install \
		--force \
		-p $(COLLECTIONS) \
		-r requirements.yml
	$(PREFLIGHT) --scope core
	$(PREFLIGHT) --scope helm
	$(SAGE_DISCOVERY_GUARDRAIL)
	$(SOURCE_GUARDRAILS)

controller-core-preflight:
	$(PREFLIGHT) --scope core

controller-helm-preflight: controller-helm controller-core-preflight
	$(PREFLIGHT) --scope helm

cluster-access-preflight: controller-helm-preflight
	$(PREFLIGHT) --scope cluster

controller-preflight: controller-core-preflight controller-helm-preflight \
                      cluster-access-preflight

sage-discovery-guardrail:
	$(SAGE_DISCOVERY_GUARDRAIL)

helm-repository-guardrail:
	$(HELM_REPOSITORY_GUARDRAIL)

source-guardrails: sage-discovery-guardrail helm-repository-guardrail
	$(SOURCE_GUARDRAILS)

k3s-release-guardrail:
	$(K3S_GUARDRAIL)

deployment-guardrail:
	$(DEPLOYMENT_GUARDRAIL)

helm-lock-reconcile: cluster-access-preflight deployment-guardrail
	$(HELM_LOCK_RECONCILE) --allow-missing

ssh-auth-preflight: controller-core-preflight
	$(ANSIBLE_ACCESS_PREFLIGHT) --scope ssh

privilege-preflight: controller-core-preflight
	$(ANSIBLE_ACCESS_PREFLIGHT) --scope privilege

ansible-access-preflight: controller-core-preflight
	$(ANSIBLE_ACCESS_PREFLIGHT) --scope all

bootstrap-guardrails: controller-core-preflight source-guardrails \
                      ansible-access-preflight syntax
	@echo "Kalaxy3 SAGE bootstrap guardrails: PASS"

k3s-guardrails: bootstrap-guardrails k3s-release-guardrail
	@echo "Kalaxy3 SAGE K3s guardrails: PASS"

cluster-guardrails: bootstrap-guardrails controller-helm-preflight \
                    cluster-access-preflight deployment-guardrail \
                    helm-lock-reconcile
	@echo "Kalaxy3 SAGE cluster deployment guardrails: PASS"

guardrails: cluster-guardrails

recovery-guardrails: controller-core-preflight source-guardrails \
                     ansible-access-preflight uninstall-syntax
	@echo "Kalaxy3 SAGE recovery guardrails: PASS"

uninstall-syntax:
	$(ANSIBLE) playbooks/uninstall.yml --syntax-check

confirm-uninstall:
	@test "$(CONFIRM_UNINSTALL)" = "kalaxy3" || { \
		echo "Refusing uninstall. Re-run with CONFIRM_UNINSTALL=kalaxy3"; \
		exit 1; \
	}

helm-release-inventory: cluster-access-preflight source-guardrails
	$(HELM_WRAPPER) list --all-namespaces --output json

access-baseline: controller-core-preflight ssh-auth-preflight
	$(ANSIBLE) playbooks/access-baseline.yml

access-baseline-bootstrap: controller-core-preflight
	$(ANSIBLE) playbooks/access-baseline.yml --ask-become-pass

bootstrap-ssh-key: controller-core-preflight
	@test -n "$(HOST)" || { \
		echo "Usage: make bootstrap-ssh-key HOST=<inventory-host>"; \
		exit 1; \
	}
	$(VENV)/bin/python scripts/bootstrap-ssh-key.py --host "$(HOST)"

verify-ssh-host-keys: controller-core-preflight
	$(VENV)/bin/python scripts/verify-ssh-host-keys.py

ping: ansible-access-preflight
	$(VENV)/bin/ansible all -m ping

phase-0: bootstrap-guardrails
	$(ANSIBLE) playbooks/phases/phase-00-readiness.yml

survey-clean:
	rm -f artifacts/site-survey/*.yml artifacts/site-survey/*.json

phase-1: bootstrap-guardrails
	$(ANSIBLE) playbooks/phases/phase-01-prerequisites.yml

phase-2: k3s-guardrails
	$(ANSIBLE) playbooks/phases/phase-02-k3s.yml

phase-3: cluster-guardrails
	$(ANSIBLE) playbooks/phases/phase-03-network-storage.yml

phase-4: cluster-guardrails
	$(ANSIBLE) playbooks/phases/phase-04-ui.yml

phase-5: cluster-guardrails
	$(ANSIBLE) playbooks/phases/phase-05-observability.yml

phase-6: cluster-guardrails
	$(ANSIBLE) playbooks/phases/phase-06-minio.yml $(VAULT)

phase-7:
	@echo "Complete markdown/Infrastructure/K3s_Homelab/Phase_Notes.md security, DNS, TLS, backup, and Cloudflare decisions."
	@echo "Do not expose management services with router port forwarding."

phase-8: cluster-guardrails
	$(ANSIBLE) playbooks/phases/phase-08-intel.yml

validate-1:
	./scripts/validate-phase.sh 1

validate-2:
	./scripts/validate-phase.sh 2

validate-3:
	./scripts/validate-phase.sh 3

validate-4:
	./scripts/validate-phase.sh 4

validate-5:
	./scripts/validate-phase.sh 5

validate-6:
	./scripts/validate-phase.sh 6

syntax:
	$(ANSIBLE) playbooks/phases/phase-00-readiness.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-01-prerequisites.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-02-k3s.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-03-network-storage.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-04-ui.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-05-observability.yml --syntax-check
	$(ANSIBLE) playbooks/phases/phase-06-minio.yml --syntax-check

# Convenience target only after every phase has been tested independently.
deploy: cluster-guardrails
	$(ANSIBLE) playbooks/site.yml $(VAULT)

uninstall: recovery-guardrails confirm-uninstall
	$(ANSIBLE) playbooks/uninstall.yml

.PHONY: centralized-logging-render
centralized-logging-render: controller-preflight
	.venv/bin/ansible-playbook \
		playbooks/validate-centralized-logging.yml

.PHONY: centralized-logging-runtime-self-test
centralized-logging-runtime-self-test:
	.venv/bin/python scripts/validate-centralized-logging-runtime-self-test.py

.PHONY: centralized-logging-runtime-validate
centralized-logging-runtime-validate:
	python3 ../../scripts/sage/sage-validator-runner.py --validator-id centralized_logging.runtime --attempted-action 'Validate active centralized logging.' --working-directory infrastructure/k3s-homelab --recovery-command 'make centralized-logging-runtime-validate' --authoritative-path infrastructure/k3s-homelab/inventory/group_vars/all/main.yml --authoritative-path infrastructure/k3s-homelab/helm-chart-lock.json --authoritative-path infrastructure/k3s-homelab/scripts/validate-centralized-logging-runtime.py --integrity-requirement 'Preserve activation state, chart locks, storage, and logs.' -- .venv/bin/python scripts/validate-centralized-logging-runtime.py

.PHONY: centralized-logging-runtime-source-self-test
centralized-logging-runtime-source-self-test:
	python3 -S scripts/validate-centralized-logging-runtime-source-self-test.py
