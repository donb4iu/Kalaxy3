#!/usr/bin/env python3
"""Guard checkpoint persistence versus promotion and least-authority boundaries."""
from __future__ import annotations

import json
from pathlib import Path

from workflow import GitSafetyGuardrail

ROOT = Path(__file__).resolve().parents[2]


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> int:
    policy = json.loads(
        (ROOT / "sage-checkpoint-promotion-policy.json").read_text(encoding="utf-8")
    )
    checkpoint = policy["checkpoint_policy"]
    promotion = policy["promotion_policy"]
    require(checkpoint["persistence_is_promotion"] is False, "checkpoint became promotion")
    require(checkpoint["checkpoint_may_be_incomplete"] is True, "incomplete checkpoint disabled")
    require(checkpoint["checkpoint_may_be_dependency_blocked"] is True, "dependency checkpoint disabled")
    require(checkpoint["remote_synchronization_required"] is True, "remote synchronization disabled")
    require(checkpoint["checkpoint_claims_validation"] is False, "checkpoint claims validation")
    require(checkpoint["checkpoint_claims_promotability"] is False, "checkpoint claims promotability")
    require(promotion["require_all_applicable_gates"] is True, "all-gates requirement disabled")
    require(promotion["fail_if_target_advances_before_merge"] is True, "target-advance guard disabled")
    require(promotion["autonomous_git_or_github_mutation"] is False, "autonomous mutation enabled")
    require(promotion["github_operator_mode"] == "browser-review", "browser-review mode disabled")
    require(promotion["github_cli_required"] is False, "GitHub CLI became required")
    require(promotion["prepared_pr_create_url_required"] is True, "prepared PR-create URL disabled")
    require(promotion["reuse_existing_exact_pr_before_merge"] is True, "existing exact PR reuse disabled")
    require(promotion["prepared_pr_merge_url_required"] is True, "prepared PR-merge URL disabled")
    require(
        promotion["post_interaction_github_verification_required"] is True,
        "post-interaction GitHub verification disabled",
    )
    require(
        promotion["operator_boundaries"]
        == ["pull-request-create", "pull-request-merge", "post-merge-fetch"],
        "promotion operator boundaries changed",
    )
    reconciliation = policy.get("source_reconciliation_policy")
    require(isinstance(reconciliation, dict), "source reconciliation policy missing")
    require(reconciliation.get("enabled") is True, "source reconciliation disabled")
    require(reconciliation.get("require_disjoint_changed_paths") is True, "disjoint-path reconciliation gate disabled")
    require(reconciliation.get("autonomous_git_mutation") is False, "source reconciliation autonomous mutation enabled")
    require(reconciliation.get("require_exact_merge_parent_topology") is True, "source reconciliation exact merge topology disabled")
    require(reconciliation.get("restart_checkpoint_promotion_after_reconciliation") is True, "source reconciliation does not re-enter promotion")
    require(reconciliation.get("source_branch_retirement_in_scope") is False, "source retirement was pulled into the blocker-remediation slice")
    required_checks = promotion.get("required_github_checks")
    require(isinstance(required_checks, list) and len(required_checks) == 3, "required GitHub check policy is incomplete")
    require(
        [item.get("name") for item in required_checks]
        == ["SAGE source governance", "MkDocs Material publication validation", "Portable OCI stage artifact"],
        "required GitHub check names drifted",
    )
    require(all(item.get("app_slug") == "github-actions" for item in required_checks), "required GitHub checks are not bound to github-actions")

    registry = json.loads((ROOT / "sage-workflow-primitives.json").read_text(encoding="utf-8"))
    primitives = {
        item["primitive_id"]: item
        for item in registry["primitives"]
        if isinstance(item, dict) and "primitive_id" in item
    }
    require(primitives["git.inspect"]["version"] == "1.2.0", "git.inspect version mismatch")
    require(primitives["github.inspect"]["version"] == "1.4.0", "github.inspect version mismatch")
    workflow = (ROOT / "scripts/sage/workflows/checkpoint_promotion.py").read_text(encoding="utf-8")
    require("GitRepository" not in workflow, "promotion imported mixed Git mutation authority")
    require(".fetch(" not in workflow, "promotion performs workflow-side Git fetch")
    require("GitHubInspector" in workflow, "promotion does not consume github.inspect")
    require("require_successful_checks(" in workflow, "promotion does not require successful exact-SHA GitHub checks")
    require("required_github_checks(" in workflow, "promotion does not consume required-check policy")
    require(
        "remote_head(" in workflow
        and "is_ancestor(" in workflow
        and "find_merge_commit(" in workflow,
        "Git read authority or exact merge-topology proof incomplete",
    )
    require(
        'boundary="pull-request-create"' in workflow
        and 'boundary="pull-request-merge"' in workflow,
        "operator PR proposals missing",
    )
    require(
        workflow.count("OperatorGitProposal.build_browser(") >= 2,
        "browser-backed PR proposal composition missing",
    )
    require("github_compare_url(" in workflow, "prepared PR-create browser URL missing")
    require("existing_pr_merge_proposal(" in workflow and "required=False" in workflow and "existing_pull_request_reused" in workflow, "existing exact PR re-entry composition missing")
    require("github_pull_url(" in workflow, "prepared PR-merge browser URL missing")
    require("validate_browser_operator_result(" in workflow, "browser confirmation binding missing")
    require('("gh", "pr"' not in workflow, "checkpoint promotion still requires GitHub CLI")
    require(
        "urllib" not in workflow and "http.client" not in workflow,
        "checkpoint promotion browser path must not import HTTP libraries",
    )
    require(
        'boundary="other-git-mutation"' in workflow
        and 'command_argv=("git", "fetch", "origin"' in workflow,
        "explicit post-merge Git refresh proposal missing",
    )
    require(
        '"merge",' in workflow
        and '"--no-edit",' in workflow
        and '"--no-ff",' in workflow
        and "reconciliation_overlap_paths" in workflow
        and "start_source_reconciliation" in workflow,
        "bounded pre-promotion source reconciliation composition missing",
    )
    require(
        'boundary="push"' in workflow
        and 'command_argv=("git", "push", "origin", source_branch)' in workflow,
        "source reconciliation push proposal missing",
    )
    require(
        '"return_to_parent_objective": "checkpoint-promotion"' in workflow
        and "start_promotion(" in workflow,
        "source reconciliation re-entry contract missing",
    )
    require(
        'if boundary == "pull-request-create":' in workflow
        and "Frozen promotion source is not an ancestor of current source branch" in workflow,
        "post-merge synchronized source-descendant recovery contract missing",
    )

    bad_mixed = "from workflow import GitRepository\nPRIMITIVES_USED = ('git.repository',)\n"
    bad_api = "repository.fetch()\n"
    bad_gh = (
        "from workflow import CommandSpec\n"
        "CommandSpec(primitive_id='command.run', label='x', "
        "argv=('gh','pr','merge','1'), cwd=ROOT)\n"
    )
    expected = (
        (bad_mixed, "MIXED-GIT-AUTHORITY"),
        (bad_api, "GIT-MUTATION-API"),
        (bad_gh, "GITHUB-MUTATION"),
    )
    for index, (source, code) in enumerate(expected, start=1):
        violations = GitSafetyGuardrail.scan_source(
            source, path=ROOT / f"checkpoint-promotion-negative-{index}.py"
        )
        require(
            any(item.code == code for item in violations),
            f"canonical safety regression failed to reject {code}",
        )

    request_execution = (
        ROOT / "scripts/sage/workflows/request_execution.py"
    ).read_text(encoding="utf-8")
    require(
        'if boundary not in {"routine-git-lifecycle", "stage", "commit", "push"}:' in request_execution,
        "ordinary request execution lifecycle contract drifted",
    )
    require(
        '"routine-git-lifecycle"' in request_execution
        and "scripts/sage/sage-routine-git-lifecycle.py" in request_execution,
        "ordinary request execution lost the bounded routine Git lifecycle path",
    )

    print("PASS checkpoint persistence remains distinct from promotion")
    print("PASS complete applicable gate and frozen-target requirements")
    print("PASS git.inspect + github.inspect least-authority composition")
    print("PASS exact frozen-source GitHub Actions checks are required before merge proposal")
    print("PASS disjoint-path pre-promotion source reconciliation is operator-executed and re-enters promotion")
    print("PASS PR mutation uses prepared browser-review operator proposals")
    print("PASS exact already-open PR may satisfy the create boundary without duplicate mutation")
    print("PASS post-merge refresh remains an exact operator Git proposal")
    print("PASS nullable GitHub merge SHA falls back to exact post-fetch Git merge topology")
    print("PASS post-merge automation descendants are permitted only after exact merge proof")
    print("PASS synchronized source branch may advance after merge while frozen source remains authoritative")
    print("PASS prior mixed-authority and GitHub-mutation classes fail closed")
    print("PASS ordinary request execution adds bounded routine Git lifecycle without checkpoint authority")
    print("Kalaxy3 SAGE checkpoint promotion guardrail: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError, SyntaxError) as error:
        print("Kalaxy3 SAGE checkpoint promotion guardrail: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
