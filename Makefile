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
SAGE_OPERATING_CONTRACT_SELF_TEST := $(PYTHON) scripts/sage/sage-operating-contract-self-test.py
SAGE_OPERATING_CONTRACT_GUARDRAIL := $(PYTHON) scripts/sage/sage-operating-contract-guardrail.py

override export REQUEST := $(value REQUEST)

.PHONY: help sage-preflight sage-changed sage-self-test \
        sage-discovery-guardrail sage-index-check \
        sage-improvement-policy-check sage-operating-contract-self-test \
        sage-operating-contract-guardrail sage-operating-contract-check sage-guardrails

help:
	@printf '%s\n' \
	  'Kalaxy3 repository entry points:' \
	  '  SAGE_REQUEST="<request>" make sage-preflight' \
	  '  make sage-changed' \
	  '  make sage-guardrails' \
	  '  make sage-operating-contract-check' \
	  '  make sage-improvement-policy-check' \
	  '  make sage-session-self-test' \
	  '  make sage-feedback-self-test' \
	  '  make sage-candidate-self-test' \
	  '  make sage-learning-self-test' \
	  '  make sage-review-self-test' \
	  '  SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_CONTRIBUTION="<contribution.zip>" make sage-action-bootstrap' \
	  '  SAGE_REQUEST="<request>" SAGE_SOURCE="<source.zip>" make sage-request-plan' \
	  '  SAGE_REQUEST="<request>" SAGE_PROPOSAL="<proposal.zip>" make sage-request-execute' \
	  '  SAGE_STATE="<state.json>" SAGE_OPERATOR_RESULT="<result.json>" make sage-request-continue' \
	  '  SAGE_STATE="<state.json>" SAGE_ROUTINE_RECEIPT="<receipt.json>" make sage-request-continue-routine' \
	  '  SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_TO_STATUS="<status>" SAGE_ACTOR="<actor>" SAGE_REASON="<reason>" SAGE_EVIDENCE_REFERENCE="<ref>" SAGE_COMMIT_MESSAGE="<message>" make sage-improvement-action-transition' \
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

sage-self-test: sage-semantic-bootstrap-self-test sage-index-self-test sage-actionable-failure-self-test sage-actionable-failure-guardrail sage-validator-runtime-self-test centralized-logging-runtime-source-self-test sage-yaml-metadata-source-self-test sage-evidence-retrieval-self-test sage-failure-retrieval-self-test sage-workflow-support-self-test sage-workflow-self-test sage-operating-contract-self-test sage-generated-helper-runtime-self-test sage-request-plan-self-test sage-request-execute-self-test sage-improvement-action-transition-self-test sage-thin-slice-self-test sage-intent-to-outcome-self-test sage-e2e-zero-trust-runtime-self-test
	$(SAGE_PREFLIGHT) --self-test
	$(SAGE_LESSONS) --self-test
	python3 scripts/sage/sage-file-delivery-guardrail.py

sage-discovery-guardrail:
	$(SAGE_DISCOVERY_GUARDRAIL)

sage-index-self-test:
	$(SAGE_INDEX) self-test

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

sage-operating-contract-self-test:
	$(SAGE_OPERATING_CONTRACT_SELF_TEST)

sage-operating-contract-guardrail:
	$(SAGE_OPERATING_CONTRACT_GUARDRAIL)

sage-operating-contract-check: sage-operating-contract-self-test sage-operating-contract-guardrail
	@echo "Kalaxy3 SAGE operating contract: PASS"

sage-guardrails: sage-self-test sage-semantic-bootstrap-guardrail sage-discovery-guardrail sage-operating-contract-guardrail \
                 sage-evidence-self-test sage-evidence-guardrail \
                 sage-active-session-self-test sage-session-close-self-test sage-session-self-test sage-feedback-self-test sage-candidate-self-test sage-learning-self-test sage-review-self-test sage-improvement-policy-check sage-index-check sage-workflow-support-guardrail sage-workflow-guardrail sage-request-planning-guardrail sage-request-execution-guardrail sage-improvement-action-transition-guardrail sage-thin-slice-guardrail sage-checkpoint-promotion-guardrail sage-security-external-access-discovery-guardrail sage-legacy-evidence-projection-guardrail sage-intent-to-outcome-guardrail sage-e2e-zero-trust-guardrail
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
	$(PYTHON) scripts/sage/sage-evidence-template-guardrail.py
	$(PYTHON) scripts/sage/sage-evidence-navigation-architecture-guardrail.py

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
MKDOCS_CONFIG := .mkdocs-work/mkdocs.generated.yml

.PHONY: docs-mkdocs-bootstrap docs-mkdocs-prepare docs-mkdocs-config
.PHONY: docs-mkdocs-build
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

docs-mkdocs-config: docs-mkdocs-bootstrap docs-mkdocs-prepare
	$(MKDOCS_PYTHON) scripts/docs/generate-mkdocs-navigation.py

docs-mkdocs-build: docs-mkdocs-config
	$(MKDOCS_BIN) build --config-file $(MKDOCS_CONFIG) --clean

docs-mkdocs-build-strict: docs-mkdocs-config
	$(MKDOCS_BIN) build --config-file $(MKDOCS_CONFIG) --clean --strict

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

# Deterministic SAGE evidence retrieval
SAGE_EVIDENCE_RETRIEVAL ?= python3 scripts/sage/sage-evidence-retrieval.py
SAGE_EVIDENCE_RETRIEVAL_SELF_TEST ?= python3 scripts/sage/sage-evidence-retrieval-self-test.py

sage-evidence-retrieve:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" make sage-evidence-retrieve'; \
	  exit 2; \
	}
	$(SAGE_EVIDENCE_RETRIEVAL) retrieve --request "$$SAGE_REQUEST"

sage-evidence-retrieval-self-test:
	$(SAGE_EVIDENCE_RETRIEVAL_SELF_TEST)

# Failure-triggered SAGE retrieval
SAGE_FAILURE_RETRIEVAL ?= python3 scripts/sage/sage-failure-retrieval-gate.py

sage-failure-retrieval:
	@test -n "$${SAGE_FAILURE:-}" || { \
	  echo 'Usage: SAGE_FAILURE="<failure>" make sage-failure-retrieval'; \
	  exit 2; \
	}
	$(SAGE_FAILURE_RETRIEVAL) --failure "$$SAGE_FAILURE"

sage-failure-retrieval-self-test:
	python3 -S scripts/sage/sage-failure-retrieval-gate.py --self-test

.PHONY: sage-failure-retrieval sage-failure-retrieval-self-test

.PHONY: sage-capability-intelligence-render \
	sage-capability-intelligence-check \
	sage-capability-intelligence-self-test \
	sage-capability-intelligence-guardrail

sage-capability-intelligence-render:
	python3 scripts/sage/sage-capability-intelligence.py render
	python3 scripts/sage/sage-capability-intelligence.py metrics

sage-capability-intelligence-check:
	python3 scripts/sage/sage-capability-intelligence.py check
	python3 scripts/sage/sage-capability-intelligence.py render --check
	python3 scripts/sage/sage-capability-intelligence.py metrics --check

sage-capability-intelligence-self-test:
	python3 scripts/sage/sage-capability-intelligence.py self-test

sage-capability-intelligence-guardrail:
	python3 scripts/sage/sage-capability-intelligence-guardrail.py
.PHONY: sage-thin-slice-render sage-thin-slice-check \
	sage-thin-slice-self-test sage-thin-slice-guardrail

sage-thin-slice-render:
	python3 scripts/sage/sage-thin-slice.py render
	python3 scripts/sage/sage-thin-slice.py metrics

sage-thin-slice-check:
	python3 scripts/sage/sage-thin-slice.py check
	python3 scripts/sage/sage-thin-slice.py render --check
	python3 scripts/sage/sage-thin-slice.py metrics --check

sage-thin-slice-self-test:
	python3 scripts/sage/sage-thin-slice.py self-test

sage-thin-slice-guardrail:
	python3 scripts/sage/sage-thin-slice-guardrail.py
.PHONY: sage-file-delivery-guardrail

sage-file-delivery-guardrail:
	python3 scripts/sage/sage-file-delivery-guardrail.py

.PHONY: sage-workflow-support-self-test sage-workflow-support-guardrail

sage-workflow-support-self-test:
	$(PYTHON) scripts/sage/sage-action-id.py --self-test
	$(PYTHON) scripts/sage/sage-python-static-guardrail.py --self-test

sage-workflow-support-guardrail:
	$(PYTHON) scripts/sage/sage-workflow-support-guardrail.py

.PHONY: sage-workflow-self-test sage-workflow-guardrail sage-workflow-usage

sage-workflow-self-test:
	$(PYTHON) scripts/sage/sage-workflow-primitives-self-test.py

sage-workflow-guardrail:
	$(PYTHON) scripts/sage/sage-workflow-primitives-guardrail.py

sage-workflow-usage:
	$(PYTHON) scripts/sage/sage-workflow-usage.py

.PHONY: sage-generated-helper-runtime-self-test

sage-generated-helper-runtime-self-test:
	python3 scripts/sage/sage-generated-helper-runtime-self-test.py


.PHONY: sage-improvement-action-transition sage-improvement-action-amendment sage-improvement-action-transition-self-test sage-improvement-action-transition-guardrail

sage-improvement-action-transition:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_TO_STATUS="<status>" SAGE_ACTOR="<actor>" SAGE_REASON="<reason>" SAGE_EVIDENCE_REFERENCE="<ref>" SAGE_COMMIT_MESSAGE="<message>" make sage-improvement-action-transition'; \
	  exit 2; \
	}
	@test -n "$${SAGE_ACTION_ID:-}" || { echo 'SAGE_ACTION_ID is required'; exit 2; }
	@test -n "$${SAGE_TO_STATUS:-}" || { echo 'SAGE_TO_STATUS is required'; exit 2; }
	@test -n "$${SAGE_ACTOR:-}" || { echo 'SAGE_ACTOR is required'; exit 2; }
	@test -n "$${SAGE_REASON:-}" || { echo 'SAGE_REASON is required'; exit 2; }
	@test -n "$${SAGE_EVIDENCE_REFERENCE:-}" || { echo 'SAGE_EVIDENCE_REFERENCE is required'; exit 2; }
	@test -n "$${SAGE_COMMIT_MESSAGE:-}" || { echo 'SAGE_COMMIT_MESSAGE is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-improvement-action-transition.py \
	  --request "$$SAGE_REQUEST" \
	  --action-id "$$SAGE_ACTION_ID" \
	  --to-status "$$SAGE_TO_STATUS" \
	  --actor "$$SAGE_ACTOR" \
	  --reason "$$SAGE_REASON" \
	  --evidence-reference "$$SAGE_EVIDENCE_REFERENCE" \
	  --commit-message "$$SAGE_COMMIT_MESSAGE" \
	  --push-remote "$${SAGE_PUSH_REMOTE:-origin}"

sage-improvement-action-amendment:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_AMEND_FILE="<replacement.json>" SAGE_EXPECTED_CONTRACT_SHA256="<sha256>" SAGE_ACTOR="<actor>" SAGE_REASON="<reason>" SAGE_EVIDENCE_REFERENCE="<ref>" SAGE_COMMIT_MESSAGE="<message>" make sage-improvement-action-amendment'; \
	  exit 2; \
	}
	@test -n "$${SAGE_AMEND_FILE:-}" || { echo 'SAGE_AMEND_FILE is required'; exit 2; }
	@test -n "$${SAGE_EXPECTED_CONTRACT_SHA256:-}" || { echo 'SAGE_EXPECTED_CONTRACT_SHA256 is required'; exit 2; }
	@test -n "$${SAGE_ACTOR:-}" || { echo 'SAGE_ACTOR is required'; exit 2; }
	@test -n "$${SAGE_REASON:-}" || { echo 'SAGE_REASON is required'; exit 2; }
	@test -n "$${SAGE_EVIDENCE_REFERENCE:-}" || { echo 'SAGE_EVIDENCE_REFERENCE is required'; exit 2; }
	@test -n "$${SAGE_COMMIT_MESSAGE:-}" || { echo 'SAGE_COMMIT_MESSAGE is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-improvement-action-amendment.py \
	  --request "$$SAGE_REQUEST" \
	  --amend-file "$$SAGE_AMEND_FILE" \
	  --expected-contract-sha256 "$$SAGE_EXPECTED_CONTRACT_SHA256" \
	  --actor "$$SAGE_ACTOR" \
	  --reason "$$SAGE_REASON" \
	  --evidence-reference "$$SAGE_EVIDENCE_REFERENCE" \
	  --commit-message "$$SAGE_COMMIT_MESSAGE" \
	  --push-remote "$${SAGE_PUSH_REMOTE:-origin}"

sage-improvement-action-transition-self-test:
	$(PYTHON) scripts/sage/sage-improvement-action-transition.py --self-test

sage-improvement-action-transition-guardrail:
	$(PYTHON) scripts/sage/sage-improvement-action-transition-guardrail.py

.PHONY: sage-action-bootstrap sage-action-bootstrap-continue sage-semantic-bootstrap-self-test sage-semantic-bootstrap-guardrail

sage-action-bootstrap:
	@test -n "$${SAGE_REQUEST:-}" || { echo 'Usage: SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_CONTRIBUTION="<contribution.zip>" make sage-action-bootstrap'; exit 2; }
	@test -n "$${SAGE_ACTION_ID:-}" || { echo 'Usage: SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_CONTRIBUTION="<contribution.zip>" make sage-action-bootstrap'; exit 2; }
	@test -n "$${SAGE_CONTRIBUTION:-}" || { echo 'Usage: SAGE_REQUEST="<request>" SAGE_ACTION_ID="<id>" SAGE_CONTRIBUTION="<contribution.zip>" make sage-action-bootstrap'; exit 2; }
	$(PYTHON) scripts/sage/sage-action-bootstrap.py --request "$$SAGE_REQUEST" --action-id "$$SAGE_ACTION_ID" --contribution "$$SAGE_CONTRIBUTION"

sage-action-bootstrap-continue:
	@test -n "$${SAGE_STATE:-}" || { echo 'Usage: SAGE_STATE="<state.json>" SAGE_CONFIRMATION="<sha256>" SAGE_ACTOR=architect make sage-action-bootstrap-continue'; exit 2; }
	@test -n "$${SAGE_CONFIRMATION:-}" || { echo 'Usage: SAGE_STATE="<state.json>" SAGE_CONFIRMATION="<sha256>" SAGE_ACTOR=architect make sage-action-bootstrap-continue'; exit 2; }
	@test -n "$${SAGE_ACTOR:-}" || { echo 'Usage: SAGE_STATE="<state.json>" SAGE_CONFIRMATION="<sha256>" SAGE_ACTOR=architect make sage-action-bootstrap-continue'; exit 2; }
	$(PYTHON) scripts/sage/sage-action-bootstrap.py --continue-state "$$SAGE_STATE" --confirm-understanding-sha256 "$$SAGE_CONFIRMATION" --actor "$$SAGE_ACTOR"

sage-semantic-bootstrap-self-test:
	$(PYTHON) scripts/sage/sage-action-bootstrap.py --self-test

sage-semantic-bootstrap-guardrail:
	$(PYTHON) scripts/sage/sage-semantic-bootstrap-guardrail.py

.PHONY: sage-request-plan sage-request-plan-self-test sage-request-planning-guardrail sage-request-execute sage-request-continue sage-request-continue-routine sage-request-execute-self-test sage-request-execution-guardrail

sage-request-plan:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_SOURCE="<source.zip>" make sage-request-plan'; \
	  exit 2; \
	}
	@test -n "$${SAGE_SOURCE:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_SOURCE="<source.zip>" make sage-request-plan'; \
	  exit 2; \
	}
	$(PYTHON) scripts/sage/sage-request-plan.py --request "$$SAGE_REQUEST" --source "$$SAGE_SOURCE"

sage-request-plan-self-test:
	$(PYTHON) scripts/sage/sage-request-plan.py --self-test

sage-request-planning-guardrail:
	$(PYTHON) scripts/sage/sage-request-planning-guardrail.py

sage-request-execute:
	@test -n "$${SAGE_REQUEST:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_PROPOSAL="<proposal.zip>" make sage-request-execute'; \
	  exit 2; \
	}
	@test -n "$${SAGE_PROPOSAL:-}" || { \
	  echo 'Usage: SAGE_REQUEST="<request>" SAGE_PROPOSAL="<proposal.zip>" make sage-request-execute'; \
	  exit 2; \
	}
	$(PYTHON) scripts/sage/sage-request-execute.py --request "$$SAGE_REQUEST" --proposal "$$SAGE_PROPOSAL"

sage-request-continue:
	@test -n "$${SAGE_STATE:-}" || { \
	  echo 'Usage: SAGE_STATE="<state.json>" SAGE_OPERATOR_RESULT="<result.json>" make sage-request-continue'; \
	  exit 2; \
	}
	@test -n "$${SAGE_OPERATOR_RESULT:-}" || { \
	  echo 'Usage: SAGE_STATE="<state.json>" SAGE_OPERATOR_RESULT="<result.json>" make sage-request-continue'; \
	  exit 2; \
	}
	$(PYTHON) scripts/sage/sage-request-execute.py --continue-state "$$SAGE_STATE" --operator-result "$$SAGE_OPERATOR_RESULT"


sage-request-continue-routine:
	@test -n "$${SAGE_STATE:-}" || { \
	  echo 'Usage: SAGE_STATE="<state.json>" SAGE_ROUTINE_RECEIPT="<receipt.json>" make sage-request-continue-routine'; \
	  exit 2; \
	}
	@test -n "$${SAGE_ROUTINE_RECEIPT:-}" || { \
	  echo 'Usage: SAGE_STATE="<state.json>" SAGE_ROUTINE_RECEIPT="<receipt.json>" make sage-request-continue-routine'; \
	  exit 2; \
	}
	$(PYTHON) scripts/sage/sage-request-execute.py --continue-state "$$SAGE_STATE" --routine-receipt "$$SAGE_ROUTINE_RECEIPT"

sage-request-execute-self-test:
	$(PYTHON) scripts/sage/sage-request-execute.py --self-test

sage-request-execution-guardrail:
	$(PYTHON) scripts/sage/sage-request-execution-guardrail.py

.PHONY: sage-checkpoint-promotion-self-test sage-checkpoint-promotion-guardrail
.PHONY: sage-checkpoint-promote sage-checkpoint-promotion-continue

sage-checkpoint-promotion-self-test:
	$(PYTHON) scripts/sage/sage-checkpoint-promote.py --self-test

sage-checkpoint-promotion-guardrail: sage-checkpoint-promotion-self-test
	$(PYTHON) scripts/sage/sage-checkpoint-promotion-guardrail.py

sage-checkpoint-promote:
	@test -n "$$SAGE_REQUEST" || (echo 'SAGE_REQUEST is required' >&2; exit 2)
	@test -n "$$SAGE_SOURCE_BRANCH" || (echo 'SAGE_SOURCE_BRANCH is required' >&2; exit 2)
	@test -n "$$SAGE_EXPECTED_HEAD" || (echo 'SAGE_EXPECTED_HEAD is required' >&2; exit 2)
	@test -n "$$SAGE_PR_TITLE" || (echo 'SAGE_PR_TITLE is required' >&2; exit 2)
	@test -n "$$SAGE_PR_BODY" || (echo 'SAGE_PR_BODY is required' >&2; exit 2)
	$(PYTHON) scripts/sage/sage-checkpoint-promote.py --request "$$SAGE_REQUEST" --source-branch "$$SAGE_SOURCE_BRANCH" --expected-head "$$SAGE_EXPECTED_HEAD" --target-branch main --title "$$SAGE_PR_TITLE" --body "$$SAGE_PR_BODY" --repo "$(CURDIR)"

sage-checkpoint-promotion-continue:
	@test -n "$$SAGE_STATE" || (echo 'SAGE_STATE is required' >&2; exit 2)
	@test -n "$$SAGE_OPERATOR_RESULT" || (echo 'SAGE_OPERATOR_RESULT is required' >&2; exit 2)
	$(PYTHON) scripts/sage/sage-checkpoint-promote.py --continue-state "$$SAGE_STATE" --operator-result "$$SAGE_OPERATOR_RESULT" --repo "$(CURDIR)"

# SAGE security/external-access and legacy-evidence bootstrap guardrails
.PHONY: sage-security-external-access-discovery-guardrail \
        sage-legacy-evidence-projection-guardrail

sage-security-external-access-discovery-guardrail:
	$(PYTHON) scripts/sage/sage-security-external-access-discovery-guardrail.py

sage-legacy-evidence-projection-guardrail:
	$(PYTHON) scripts/sage/sage-legacy-evidence-projection-guardrail.py

# SAGE intent-to-outcome and zero-trust E2E viability slice
SAGE_E2E_INFRA_DIR := infrastructure/k3s-homelab

.PHONY: sage-intent-to-outcome sage-intent-to-outcome-confirm \
        sage-intent-to-outcome-adopt-request sage-intent-to-outcome-adopt-iteration \
        sage-intent-to-outcome-iterate sage-intent-to-outcome-continue \
        sage-intent-to-outcome-continue-routine sage-intent-to-outcome-record-runtime \
        sage-intent-to-outcome-promote sage-intent-to-outcome-continue-promotion \
        sage-intent-to-outcome-self-test sage-intent-to-outcome-guardrail \
        sage-e2e-zero-trust-guardrail sage-e2e-zero-trust-deploy \
        sage-e2e-zero-trust-runtime-validate sage-e2e-zero-trust-runtime-receipt \
        sage-e2e-zero-trust-runtime-self-test

sage-intent-to-outcome:
	@test -n "$${SAGE_REQUEST:-}" || { echo 'SAGE_REQUEST is required'; exit 2; }
	@test -n "$${SAGE_ACTION_ID:-}" || { echo 'SAGE_ACTION_ID is required'; exit 2; }
	@test -n "$${SAGE_CONTRIBUTION:-}" || { echo 'SAGE_CONTRIBUTION is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py start --request "$$SAGE_REQUEST" --action-id "$$SAGE_ACTION_ID" --contribution "$$SAGE_CONTRIBUTION"

sage-intent-to-outcome-confirm:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_CONFIRMATION:-}" || { echo 'SAGE_CONFIRMATION is required'; exit 2; }
	@test -n "$${SAGE_DISPOSITIONS:-}" || { echo 'SAGE_DISPOSITIONS is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py confirm --state "$$SAGE_INTENT_STATE" --confirmation "$$SAGE_CONFIRMATION" --dispositions "$$SAGE_DISPOSITIONS" --actor architect

sage-intent-to-outcome-adopt-request:
	@test -n "$${SAGE_REQUEST:-}" || { echo 'SAGE_REQUEST is required'; exit 2; }
	@test -n "$${SAGE_REQUEST_STATE:-}" || { echo 'SAGE_REQUEST_STATE is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py adopt-request --request "$$SAGE_REQUEST" --request-state "$$SAGE_REQUEST_STATE"

sage-intent-to-outcome-adopt-iteration:
	@test -n "$${SAGE_REQUEST:-}" || { echo 'SAGE_REQUEST is required'; exit 2; }
	@test -n "$${SAGE_REQUEST_STATE:-}" || { echo 'SAGE_REQUEST_STATE is required'; exit 2; }
	@test -n "$${SAGE_ACTION_ID:-}" || { echo 'SAGE_ACTION_ID is required'; exit 2; }
	@test -n "$${SAGE_CANDIDATE_HEAD:-}" || { echo 'SAGE_CANDIDATE_HEAD is required'; exit 2; }
	@test -n "$${SAGE_UNRESOLVED_FINDING:-}" || { echo 'SAGE_UNRESOLVED_FINDING is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py adopt-iteration --request "$$SAGE_REQUEST" --request-state "$$SAGE_REQUEST_STATE" --action-id "$$SAGE_ACTION_ID" --candidate-head "$$SAGE_CANDIDATE_HEAD" --unresolved-finding "$$SAGE_UNRESOLVED_FINDING"

sage-intent-to-outcome-iterate:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_CONTRIBUTION:-}" || { echo 'SAGE_CONTRIBUTION is required'; exit 2; }
	@test -n "$${SAGE_ITERATION_TRIGGER:-}" || { echo 'SAGE_ITERATION_TRIGGER is required'; exit 2; }
	@test -n "$${SAGE_REENTRY_BOUNDARY:-}" || { echo 'SAGE_REENTRY_BOUNDARY is required'; exit 2; }
	@test -n "$${SAGE_PARENT_CHECKPOINT:-}" || { echo 'SAGE_PARENT_CHECKPOINT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py iterate --state "$$SAGE_INTENT_STATE" --contribution "$$SAGE_CONTRIBUTION" --trigger "$$SAGE_ITERATION_TRIGGER" --reentry-boundary "$$SAGE_REENTRY_BOUNDARY" --parent-checkpoint "$$SAGE_PARENT_CHECKPOINT"

sage-intent-to-outcome-continue:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_OPERATOR_RESULT:-}" || { echo 'SAGE_OPERATOR_RESULT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py continue-request --state "$$SAGE_INTENT_STATE" --operator-result "$$SAGE_OPERATOR_RESULT"

sage-intent-to-outcome-continue-routine:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_ROUTINE_RECEIPT:-}" || { echo 'SAGE_ROUTINE_RECEIPT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py continue-request --state "$$SAGE_INTENT_STATE" --routine-receipt "$$SAGE_ROUTINE_RECEIPT"

sage-intent-to-outcome-record-runtime:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_RUNTIME_RECEIPT:-}" || { echo 'SAGE_RUNTIME_RECEIPT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py record-runtime --state "$$SAGE_INTENT_STATE" --runtime-receipt "$$SAGE_RUNTIME_RECEIPT"

sage-intent-to-outcome-promote:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_EXPECTED_HEAD:-}" || { echo 'SAGE_EXPECTED_HEAD is required'; exit 2; }
	@test -n "$${SAGE_PR_TITLE:-}" || { echo 'SAGE_PR_TITLE is required'; exit 2; }
	@test -n "$${SAGE_PR_BODY:-}" || { echo 'SAGE_PR_BODY is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py promote --state "$$SAGE_INTENT_STATE" --expected-head "$$SAGE_EXPECTED_HEAD" --title "$$SAGE_PR_TITLE" --body "$$SAGE_PR_BODY"

sage-intent-to-outcome-continue-promotion:
	@test -n "$${SAGE_INTENT_STATE:-}" || { echo 'SAGE_INTENT_STATE is required'; exit 2; }
	@test -n "$${SAGE_OPERATOR_RESULT:-}" || { echo 'SAGE_OPERATOR_RESULT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py continue-promotion --state "$$SAGE_INTENT_STATE" --operator-result "$$SAGE_OPERATOR_RESULT"

sage-intent-to-outcome-self-test:
	$(PYTHON) scripts/sage/sage-intent-to-outcome.py --self-test

sage-intent-to-outcome-guardrail:
	$(PYTHON) scripts/sage/sage-intent-to-outcome-guardrail.py

sage-e2e-zero-trust-guardrail:
	$(PYTHON) scripts/sage/sage-e2e-zero-trust-guardrail.py
	$(MAKE) -C $(SAGE_E2E_INFRA_DIR) source-guardrails
	$(MAKE) -C $(SAGE_E2E_INFRA_DIR) deployment-guardrail
	$(MAKE) -C $(SAGE_E2E_INFRA_DIR) cluster-guardrails
	cd $(SAGE_E2E_INFRA_DIR) && .venv/bin/ansible-playbook cloudflare/deploy-sage-e2e.yml --syntax-check
	cd $(SAGE_E2E_INFRA_DIR) && .venv/bin/ansible-playbook cloudflare/validate-sage-e2e.yml --syntax-check

sage-e2e-zero-trust-deploy:
	@test -n "$${SAGE_EXTERNAL_HOSTNAME:-}" || { echo 'SAGE_EXTERNAL_HOSTNAME is required'; exit 2; }
	@test -n "$${KALAXY3_ANSIBLE_SECRETS_FILE:-}" || { echo 'KALAXY3_ANSIBLE_SECRETS_FILE is required'; exit 2; }
	cd $(SAGE_E2E_INFRA_DIR) && .venv/bin/ansible-playbook cloudflare/deploy-sage-e2e.yml --extra-vars "sage_external_hostname=$$SAGE_EXTERNAL_HOSTNAME kalaxy3_secrets_file=$$KALAXY3_ANSIBLE_SECRETS_FILE"

sage-e2e-zero-trust-runtime-validate:
	@test -n "$${SAGE_EXTERNAL_HOSTNAME:-}" || { echo 'SAGE_EXTERNAL_HOSTNAME is required'; exit 2; }
	cd $(SAGE_E2E_INFRA_DIR) && .venv/bin/ansible-playbook cloudflare/validate-sage-e2e.yml --extra-vars "sage_external_hostname=$$SAGE_EXTERNAL_HOSTNAME"

sage-e2e-zero-trust-runtime-receipt:
	@test -n "$${SAGE_EXTERNAL_HOSTNAME:-}" || { echo 'SAGE_EXTERNAL_HOSTNAME is required'; exit 2; }
	@test -n "$${SAGE_AUTOMATED_RUNTIME_RECEIPT:-}" || { echo 'SAGE_AUTOMATED_RUNTIME_RECEIPT is required'; exit 2; }
	$(PYTHON) scripts/sage/sage-e2e-zero-trust-runtime-receipt.py --automated "$$SAGE_AUTOMATED_RUNTIME_RECEIPT" --hostname "$$SAGE_EXTERNAL_HOSTNAME" --authorized-mfa-verified --privileged-routes-reviewed --actor architect

sage-e2e-zero-trust-runtime-self-test:
	$(PYTHON) scripts/sage/sage-e2e-zero-trust-runtime-receipt.py --self-test
