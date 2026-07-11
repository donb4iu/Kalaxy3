VENV := .venv
ANSIBLE := $(VENV)/bin/ansible-playbook
VAULT := --ask-vault-pass

.PHONY: install ping phase-0 phase-1 phase-2 phase-3 phase-4 phase-5 \
        phase-6 phase-7 phase-8 validate-1 validate-2 validate-3 \
        validate-4 validate-5 validate-6 deploy uninstall syntax

install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/ansible-galaxy collection install -r requirements.yml

ping:
	$(VENV)/bin/ansible all -m ping

phase-0:
	$(ANSIBLE) playbooks/phases/phase-00-readiness.yml

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
	@echo "Complete docs/phase-notes.md security, DNS, TLS, backup, and Cloudflare decisions."
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
