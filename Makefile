.DEFAULT_GOAL := help

PYTHON ?= python3
SAGE_PREFLIGHT := $(PYTHON) scripts/sage/sage-change-preflight.py
SAGE_LESSONS := $(PYTHON) scripts/sage/sage-lessons.py
SAGE_SESSION_SCORE := $(PYTHON) scripts/sage/sage-session-score.py
SAGE_ACTIVE_SESSION := $(PYTHON) scripts/sage/sage-active-session.py
SAGE_SESSION_CLOSE := $(PYTHON) scripts/sage/sage-session-close.py
SAGE_ACTIVE_SESSION_GUARDRAIL := $(PYTHON) scripts/sage/sage-active-session-guardrail.py
SAGE_FEEDBACK_COMPARE := $(PYTHON) scripts/sage/sage-feedback-compare.py
SAGE_FEEDBACK_GUARDRAIL := $(PYTHON) scripts/sage/sage-feedback-guardrail.py
SAGE_CANDIDATE_LIFECYCLE := $(PYTHON) scripts/sage/sage-candidate-lifecycle.py
SAGE_CANDIDATE_GUARDRAIL := $(PYTHON) scripts/sage/sage-candidate-lifecycle-guardrail.py
SAGE_IMPROVEMENT_ACTIONS := $(PYTHON) scripts/sage/sage-improvement-actions.py
SAGE_BASELINE_EXTRACT := $(PYTHON) scripts/sage/sage-baseline-extract.py
SAGE_LEARNING_GUARDRAIL := $(PYTHON) scripts/sage/sage-learning-guardrail.py
SAGE_POST_SESSION_REVIEW := $(PYTHON) scripts/sage/sage-post-session-review.py
SAGE_POST_SESSION_REVIEW_GUARDRAIL := $(PYTHON) scripts/sage/sage-post-session-review-guardrail.py
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
	  '  make sage-session-self-test' \
	  '  make sage-feedback-self-test' \
	  '  make sage-candidate-self-test' \
	  '  make sage-learning-self-test' \
	  '  make sage-review-self-test' \
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

sage-self-test: sage-actionable-failure-self-test sage-actionable-failure-guardrail sage-validator-runtime-self-test centralized-logging-runtime-source-self-test sage-yaml-metadata-source-self-test
	$(SAGE_PREFLIGHT) --self-test
	$(SAGE_LESSONS) --self-test

sage-discovery-guardrail:
	$(SAGE_DISCOVERY_GUARDRAIL)

sage-index-check:
	$(SAGE_INDEX) check

sage-active-session-self-test:
	$(SAGE_ACTIVE_SESSION) --self-test
	$(SAGE_ACTIVE_SESSION_GUARDRAIL)

sage-session-close-self-test:
	$(SAGE_SESSION_CLOSE) --self-test

sage-session-self-test:
	$(SAGE_SESSION_SCORE) --self-test

sage-feedback-self-test:
	$(SAGE_FEEDBACK_COMPARE) --self-test
	$(SAGE_FEEDBACK_GUARDRAIL)

sage-candidate-self-test:
	$(SAGE_CANDIDATE_LIFECYCLE) --self-test
	$(SAGE_CANDIDATE_GUARDRAIL)

sage-learning-self-test:
	$(SAGE_IMPROVEMENT_ACTIONS) --self-test
	$(SAGE_BASELINE_EXTRACT) --self-test
	$(SAGE_LEARNING_GUARDRAIL)

sage-review-self-test:
	$(SAGE_POST_SESSION_REVIEW) --self-test
	$(SAGE_POST_SESSION_REVIEW_GUARDRAIL)

sage-improvement-policy-check:
	$(SAGE_IMPROVEMENT_GUARDRAIL)

sage-guardrails: sage-self-test sage-discovery-guardrail \
                 sage-evidence-self-test sage-evidence-guardrail \
                 sage-active-session-self-test sage-session-close-self-test sage-session-self-test sage-feedback-self-test sage-candidate-self-test sage-learning-self-test sage-review-self-test sage-improvement-policy-check sage-index-check
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

.PHONY: sage-active-session-self-test

.PHONY: sage-session-self-test

.PHONY: sage-feedback-self-test

.PHONY: sage-candidate-self-test

.PHONY: sage-learning-self-test

.PHONY: sage-review-self-test


# BEGIN KALAXY3 MKDOCS STAGED TARGETS
MKDOCS_VENV := .mkdocs-venv
MKDOCS_PYTHON := $(MKDOCS_VENV)/bin/python
MKDOCS_BIN := $(MKDOCS_VENV)/bin/mkdocs
MKDOCS_READY := $(MKDOCS_VENV)/.kalaxy3-ready
MKDOCS_PUBLICATION_TEST := .mkdocs-work/publication-test/docs

.PHONY: docs-mkdocs-bootstrap docs-mkdocs-prepare docs-mkdocs-build
.PHONY: docs-mkdocs-build-strict docs-mkdocs-validate docs-mkdocs-stage
.PHONY: docs-mkdocs-publication-test docs-mkdocs-publication-check
.PHONY: docs-mkdocs-generate

$(MKDOCS_READY): requirements-docs.txt requirements-docs.lock.txt
	python3 -m venv $(MKDOCS_VENV)
	$(MKDOCS_PYTHON) -m pip install -r requirements-docs.lock.txt
	@touch $(MKDOCS_READY)

docs-mkdocs-bootstrap: $(MKDOCS_READY)

docs-mkdocs-prepare:
	python3 scripts/docs/prepare-mkdocs-source.py

docs-mkdocs-build: docs-mkdocs-bootstrap docs-mkdocs-prepare
	$(MKDOCS_BIN) build --config-file mkdocs.yml --clean

docs-mkdocs-build-strict: docs-mkdocs-bootstrap docs-mkdocs-prepare
	$(MKDOCS_BIN) build --config-file mkdocs.yml --clean --strict

docs-mkdocs-validate:
	python3 scripts/docs/validate-mkdocs-build.py
	python3 scripts/docs/validate-mkdocs-navigation.py

docs-mkdocs-stage: docs-mkdocs-build-strict docs-mkdocs-validate
	@echo "Kalaxy3 staged MkDocs build: PASS"

docs-mkdocs-publication-test: docs-mkdocs-stage
	rm -rf $(MKDOCS_PUBLICATION_TEST)
	python3 scripts/docs/promote-mkdocs-site.py \
		--destination $(MKDOCS_PUBLICATION_TEST)
	python3 scripts/docs/validate-mkdocs-publication.py \
		--destination $(MKDOCS_PUBLICATION_TEST)
	@echo "Kalaxy3 staged MkDocs publication test: PASS"

docs-mkdocs-publication-check:
	python3 scripts/docs/validate-mkdocs-publication.py \
		--destination docs

docs-mkdocs-generate: docs-mkdocs-stage
	python3 scripts/docs/promote-mkdocs-site.py \
		--destination docs
	python3 scripts/docs/validate-mkdocs-publication.py \
		--destination docs
	@echo "Kalaxy3 MkDocs generated documentation: PASS"
# END KALAXY3 MKDOCS STAGED TARGETS
.PHONY: sage-session-close-self-test

.PHONY: sage-actionable-failure-self-test
sage-actionable-failure-self-test:
	python3 scripts/sage/sage-actionable-failure-self-test.py

.PHONY: sage-actionable-failure-guardrail
sage-actionable-failure-guardrail:
	python3 scripts/sage/sage-actionable-failure-guardrail.py

.PHONY: sage-actionable-failure-audit
sage-actionable-failure-audit:
	python3 scripts/sage/sage-actionable-failure-audit.py

.PHONY: sage-validator-runtime-self-test
sage-validator-runtime-self-test:
	python3 scripts/sage/sage-validator-runner.py --validator-id sage.actionable_failure_self_test --attempted-action 'Validate the SAGE failure framework.' --working-directory . --recovery-command 'python3 scripts/sage/sage-actionable-failure-self-test.py' --authoritative-path scripts/sage/sage-actionable-failure-self-test.py -- python3 scripts/sage/sage-actionable-failure-self-test.py

.PHONY: centralized-logging-runtime-self-test
centralized-logging-runtime-self-test:
	$(MAKE) -C infrastructure/k3s-homelab centralized-logging-runtime-self-test

.PHONY: centralized-logging-runtime-validate
centralized-logging-runtime-validate:
	$(MAKE) -C infrastructure/k3s-homelab centralized-logging-runtime-validate

.PHONY: sage-yaml-metadata-self-test
sage-yaml-metadata-self-test:
	infrastructure/k3s-homelab/.venv/bin/python scripts/sage/sage-yaml-metadata-self-test.py

.PHONY: centralized-logging-runtime-source-self-test
centralized-logging-runtime-source-self-test:
	$(MAKE) -C infrastructure/k3s-homelab centralized-logging-runtime-source-self-test

.PHONY: sage-yaml-metadata-source-self-test
sage-yaml-metadata-source-self-test:
	python3 -S scripts/sage/sage-yaml-metadata-source-self-test.py
