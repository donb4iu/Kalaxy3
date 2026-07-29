.DEFAULT_GOAL := help

PYTHON ?= python3
SAGE_PREFLIGHT := $(PYTHON) scripts/sage/sage-change-preflight.py
SAGE_LESSONS := $(PYTHON) scripts/sage/sage-lessons.py
SAGE_DISCOVERY_GUARDRAIL := \
	$(PYTHON) scripts/sage/sage-change-discovery-guardrail.py
SAGE_INDEX := $(PYTHON) scripts/sage/sage-index.py
SAGE_EVIDENCE_ORCHESTRATOR := $(PYTHON) scripts/sage/sage-evidence-orchestrator.py
SAGE_EVIDENCE_GUARDRAIL := $(PYTHON) scripts/sage/sage-evidence-orchestration-guardrail.py
SAGE_IMPROVEMENT_GUARDRAIL := $(PYTHON) scripts/sage/sage-continuous-improvement-guardrail.py

override export REQUEST := $(value REQUEST)

.PHONY: help sage-preflight sage-changed sage-self-test \
        sage-discovery-guardrail sage-index-check \
        sage-improvement-policy-check sage-guardrails

help:
	@printf '%s\n' \
	  'Kalaxy3 repository entry points:' \
	  '  SAGE_REQUEST="<request>" make sage-preflight' \
	  '  make sage-changed' \
	  '  make sage-guardrails' \
	  '  make sage-improvement-policy-check' \
	  '  SAGE_REQUEST="<request>" make sage-evidence-prepare' \
	  '  SAGE_PACKAGE="<package.zip>" make sage-evidence-check'

sage-preflight:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" make sage-preflight'; \
	  exit 2; \
	}
	$(SAGE_PREFLIGHT) --request "$$SAGE_REQUEST"
	$(SAGE_LESSONS) --request "$$SAGE_REQUEST"

sage-changed:
	$(SAGE_PREFLIGHT) --changed
	$(SAGE_LESSONS) --changed

sage-self-test:
	$(SAGE_PREFLIGHT) --self-test
	$(SAGE_LESSONS) --self-test

sage-discovery-guardrail:
	$(SAGE_DISCOVERY_GUARDRAIL)

sage-index-check:
	$(SAGE_INDEX) check

sage-improvement-policy-check:
	$(SAGE_IMPROVEMENT_GUARDRAIL)

sage-guardrails: sage-self-test sage-discovery-guardrail \
                 sage-evidence-self-test sage-evidence-guardrail \
                 sage-improvement-policy-check sage-index-check
	@echo "Kalaxy3 repository SAGE guardrails: PASS"

.PHONY: sage-evidence-brief sage-evidence-prepare \
        sage-evidence-check sage-evidence-self-test \
        sage-evidence-guardrail

sage-evidence-brief:
	$(SAGE_EVIDENCE_ORCHESTRATOR) brief

sage-evidence-prepare:
	$(SAGE_EVIDENCE_ORCHESTRATOR) capture

sage-evidence-check:
	$(SAGE_EVIDENCE_ORCHESTRATOR) check

sage-evidence-self-test:
	$(SAGE_EVIDENCE_ORCHESTRATOR) self-test

sage-evidence-guardrail:
	$(SAGE_EVIDENCE_GUARDRAIL)
