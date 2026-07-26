VENV := .venv
COLLECTIONS := .ansible/collections
TOOLS := .tools
UV := $(TOOLS)/uv
UV_VERSION := $(shell cat .uv-version)
PYTHON_VERSION := $(shell cat .python-version)
PYTHON_INSTALL_DIR := $(abspath .python)
UV_CACHE_DIR := $(abspath .uv-cache)
ANSIBLE := $(VENV)/bin/ansible-playbook
PREFLIGHT := $(VENV)/bin/python scripts/controller-preflight.py
VAULT := --ask-vault-pass

.PHONY: install controller-uv controller-bootstrap \
        controller-preflight ping \
        phase-0 phase-1 phase-2 phase-3 phase-4 phase-5 \
        phase-6 phase-7 phase-8 survey-clean validate-1 validate-2 validate-3 \
        validate-4 validate-5 validate-6 deploy uninstall syntax

install: controller-bootstrap

controller-uv:
	@mkdir -p $(TOOLS)
	@if ! command -v sha256sum >/dev/null 2>&1; then \
		command -v shasum >/dev/null 2>&1 || { \
			echo "Neither sha256sum nor shasum is available"; \
			exit 1; \
		}; \
		printf '%s\n' '#!/bin/sh' \
		  'exec shasum -a 256 "$$@"' \
		  > "$(TOOLS)/sha256sum"; \
		chmod 755 "$(TOOLS)/sha256sum"; \
	fi
	@if [ ! -x "$(UV)" ] || \
	   [ "$$($(UV) --version 2>/dev/null | awk '{print $$2}')" != "$(UV_VERSION)" ]; then \
		rm -f "$(UV)"; \
		curl --proto '=https' --tlsv1.2 -LsSf \
		  "https://releases.astral.sh/github/uv/releases/download/$(UV_VERSION)/uv-installer.sh" | \
		  env PATH="$(abspath $(TOOLS)):$$PATH" \
		  UV_UNMANAGED_INSTALL="$(abspath $(TOOLS))" sh; \
	fi
	@test -x "$(UV)"
	@test "$$($(UV) --version | awk '{print $$2}')" = "$(UV_VERSION)"
controller-bootstrap: controller-uv
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
	$(PREFLIGHT)

controller-preflight:
	$(PREFLIGHT)

ping:
	$(VENV)/bin/ansible all -m ping

phase-0:
	$(ANSIBLE) playbooks/phases/phase-00-readiness.yml

survey-clean:
	rm -f artifacts/site-survey/*.yml artifacts/site-survey/*.json

phase-1:
	$(ANSIBLE) playbooks/phases/phase-01-prerequisites.yml

phase-2:
	$(ANSIBLE) playbooks/phases/phase-02-k3s.yml

phase-3:
	$(ANSIBLE) playbooks/phases/phase-03-network-storage.yml

phase-4:
	$(ANSIBLE) playbooks/phases/phase-04-ui.yml

phase-5:
	$(ANSIBLE) playbooks/phases/phase-05-observability.yml

phase-6:
	$(ANSIBLE) playbooks/phases/phase-06-minio.yml $(VAULT)

phase-7:
	@echo "Complete markdown/Infrastructure/K3s_Homelab/Phase_Notes.md security, DNS, TLS, backup, and Cloudflare decisions."
	@echo "Do not expose management services with router port forwarding."

phase-8:
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
deploy:
	$(ANSIBLE) playbooks/site.yml $(VAULT)

uninstall:
	$(ANSIBLE) playbooks/uninstall.yml
