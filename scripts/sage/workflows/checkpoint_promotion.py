"""Repository-owned checkpoint-to-main promotion composition."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from checkpoint_promotion import applicable_gates, eligibility, self_test as policy_self_test
from request_execution import validate_operator_result
from workflow import (
    AtomicFileWriter,
    AuthorityAssertion,
    AuthorityReconciler,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    GitAuthoritySnapshot,
    GitHubInspector,
    GitInspector,
    JsonlEventLogger,
    OperatorGitProposal,
    PrimitiveCatalog,
    SageDiscovery,
    ValidationCommand,
    ValidationPlan,
    WorkflowError,
)
from workflows.request_planning import derive_component_plan

WORKFLOW_ID = "sage.checkpoint-promotion"
WORKFLOW_VERSION = "1.0.0"
POLICY_PATH = "sage-checkpoint-promotion-policy.json"
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "sage.discovery",
    "git.inspect",
    "github.inspect",
    "authority.reconcile",
    "component.select",
    "capability.gap",
    "validation.plan",
    "operator.git-proposal",
    "evidence.closeout",
    "workflow.composition",
)
SECRET_ENVIRONMENT_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GITHUB_PAT",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "KUBECONFIG",
)


@dataclass
class PromotionContext:
    repo: Path
    request: str
    source_branch: str
    expected_head: str
    target_branch: str
    title: str
    body: str
    state_dir: Path
    catalog: PrimitiveCatalog
    logger: JsonlEventLogger
    runner: CommandRunner
    inspector: GitInspector
    github: GitHubInspector
    writer: AtomicFileWriter
    policy: dict[str, Any]
    discovery: Any = None
    snapshot: GitAuthoritySnapshot | None = None
    frozen_target_head: str | None = None
    remote_source_head: str | None = None
    changed_paths: tuple[str, ...] = ()
    authority_path: Path | None = None
    component_path: Path | None = None
    gap_path: Path | None = None
    eligibility_path: Path | None = None
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    proposal_path: Path | None = None
    state_path: Path | None = None


def stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=4, sort_keys=False) + "\n"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(context: PromotionContext, name: str, value: Mapping[str, Any]) -> Path:
    path = context.state_dir / name
    context.writer.write_text(path, stable_json(value), new_mode=0o600)
    return path


def proposal_id(head: str, boundary: str) -> str:
    token = hashlib.sha256(f"{head}:{boundary}".encode("utf-8")).hexdigest()
    return (
        f"SAGE-GIT-{datetime.now().strftime('%Y%m%d')}-"
        f"{int(token[:8], 16) % 1000:03d}"
    )


def build_context(
    *,
    repo: Path,
    request: str,
    source_branch: str,
    expected_head: str,
    target_branch: str,
    title: str,
    body: str,
) -> PromotionContext:
    resolved = repo.expanduser().resolve()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    state_dir = (
        Path("~/.local/state/kalaxy3/sage-checkpoint-promotion").expanduser()
        / stamp
    )
    state_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(resolved / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        state_dir / "events.jsonl",
        WORKFLOW_ID,
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(resolved, state_dir),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    policy = json.loads((resolved / POLICY_PATH).read_text(encoding="utf-8"))
    github_policy = policy.get("github_repository")
    if not isinstance(github_policy, Mapping):
        raise WorkflowError("checkpoint promotion GitHub repository policy missing")
    github = GitHubInspector(
        str(github_policy.get("owner", "")),
        str(github_policy.get("name", "")),
    )
    return PromotionContext(
        repo=resolved,
        request=request,
        source_branch=source_branch,
        expected_head=expected_head,
        target_branch=target_branch,
        title=title,
        body=body,
        state_dir=state_dir,
        catalog=catalog,
        logger=logger,
        runner=runner,
        inspector=GitInspector(resolved, runner),
        github=github,
        writer=AtomicFileWriter((state_dir,)),
        policy=policy,
    )


def discovery_action(context: PromotionContext) -> None:
    context.discovery = SageDiscovery(context.repo, context.runner).literal(context.request)
    context.runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Retrieve evidence for checkpoint promotion",
            argv=("make", "sage-evidence-retrieve"),
            cwd=context.repo,
            environment={"SAGE_REQUEST": context.request},
            timeout_seconds=600,
        )
    )


def git_authority_action(context: PromotionContext) -> None:
    context.inspector.require_clean()
    context.inspector.require_branch(context.source_branch)
    context.inspector.require_head(context.expected_head)
    local_source = context.inspector.require_upstream_equal()
    remote_source = context.inspector.remote_head("origin", context.source_branch)
    if remote_source != local_source:
        raise WorkflowError(
            "Remote source branch advanced or is stale: "
            f"local={local_source}, remote={remote_source}"
        )

    target_ref = f"origin/{context.target_branch}"
    local_target = context.inspector.head(target_ref)
    remote_target = context.inspector.remote_head("origin", context.target_branch)
    if local_target != remote_target:
        raise WorkflowError(
            "Local target authority is stale versus remote. "
            "Use an explicit operator Git refresh and restart promotion: "
            f"local={local_target}, remote={remote_target}"
        )
    if not context.inspector.is_ancestor(local_target, local_source):
        raise WorkflowError("Source does not descend from frozen target")
    changed = context.inspector.diff_paths(local_target, local_source, three_dot=True)
    if not changed:
        raise WorkflowError("Promotion delta is empty")

    context.snapshot = context.inspector.snapshot()
    context.frozen_target_head = local_target
    context.remote_source_head = remote_source
    context.changed_paths = tuple(sorted(changed))


def authority_action(context: PromotionContext) -> None:
    if (
        context.discovery is None
        or context.snapshot is None
        or context.frozen_target_head is None
        or context.remote_source_head is None
    ):
        raise WorkflowError("Promotion authority prerequisites missing")
    operating = context.repo / "sage-operating-contract-policy.json"
    policy = json.loads(operating.read_text(encoding="utf-8"))
    required = policy["authority_policy"]["required_authority_types"]
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    common = {
        "captured_at": captured_at,
        "freshness": "current",
        "confidence": "high",
        "applicability": "material",
    }
    assertions = (
        AuthorityAssertion(
            "ASSERT-001",
            "operator-intent",
            "operator-request",
            "literal-request",
            subject="checkpoint promotion intent",
            statement=context.request,
            measurement_type="declared",
            evidence_sha256=hashlib.sha256(context.request.encode("utf-8")).hexdigest(),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-002",
            "git",
            "git.inspect",
            f"HEAD:{context.snapshot.head}",
            subject="checkpoint Git authority",
            statement=(
                f"Source {context.source_branch} is synchronized at "
                f"{context.snapshot.head}; target {context.target_branch} is frozen "
                f"at {context.frozen_target_head} and matches the remote read."
            ),
            measurement_type="measured",
            evidence_sha256=hashlib.sha256(
                (
                    context.snapshot.head
                    + context.remote_source_head
                    + context.frozen_target_head
                ).encode("utf-8")
            ).hexdigest(),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-003",
            "github",
            "repository-policy",
            "sage-operating-contract-policy.json#operator_mutation_policy",
            subject="GitHub promotion boundary",
            statement=(
                "GitHub PR creation and merge remain operator-executed proposal "
                "boundaries; github.inspect supplies read-only verification."
            ),
            measurement_type="declared",
            evidence_sha256=sha256_file(operating),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-004",
            "repository-policy",
            "repository",
            POLICY_PATH,
            subject="checkpoint promotion policy",
            statement=(
                "Checkpoint persistence is not promotion; promotion requires every "
                "applicable gate and frozen source/target authority."
            ),
            measurement_type="declared",
            evidence_sha256=sha256_file(context.repo / POLICY_PATH),
            **common,
        ),
        AuthorityAssertion(
            "ASSERT-005",
            "sage",
            "repository",
            "sage-change-authority.json",
            subject="SAGE discovery authority",
            statement="The literal promotion request was classified through SAGE discovery.",
            measurement_type="measured",
            evidence_sha256=hashlib.sha256(
                context.discovery.stdout.encode("utf-8")
            ).hexdigest(),
            **common,
        ),
    )
    receipt = AuthorityReconciler(required).reconcile(
        receipt_id=f"SAGE-AUTH-{datetime.now().strftime('%Y%m%d')}-PROM",
        request=context.request,
        repository=context.snapshot.as_dict(),
        assertions=assertions,
        evidence_references=(
            "action:SAGE-ACTION-20260809-002",
            "action:SAGE-ACTION-20260811-002",
            POLICY_PATH,
        ),
        captured_at=captured_at,
    )
    if receipt.reconciliation["disposition"] != "complete":
        raise WorkflowError(receipt.reconciliation["summary"])
    context.authority_path = write_json(
        context, "authority-reconciliation.json", receipt.to_dict()
    )

    plan = derive_component_plan(
        repo=context.repo,
        catalog=context.catalog,
        request=context.request,
        authority_reference=str(context.authority_path),
        required_primitives=PRIMITIVES_USED,
    )
    if plan.gap_receipt is not None:
        context.gap_path = write_json(context, "capability-gap.json", plan.gap_receipt)
        raise WorkflowError("Registered primitives cannot satisfy checkpoint promotion")
    context.component_path = write_json(
        context, "component-selection.json", plan.selection_manifest
    )
    context.gap_path = write_json(
        context,
        "capability-gap-decision.json",
        {
            "schema_version": "1.0",
            "record_type": "sage-capability-gap-decision",
            "request": context.request,
            "new_primitive_required": False,
            "composition_can_close_gap": True,
            "decision": (
                "Reuse git.inspect, github.inspect, validation.plan, and "
                "operator.git-proposal; no workflow-side Git or GitHub mutation."
            ),
        },
    )


def validation_action(context: PromotionContext) -> None:
    if context.frozen_target_head is None:
        raise WorkflowError("Frozen target missing before validation")
    gates = applicable_gates(context.policy, context.changed_paths)
    commands = tuple(
        ValidationCommand(
            str(gate["label"]),
            tuple(str(item) for item in gate["argv"]),
            3600,
        )
        for gate in gates
    )
    results = ValidationPlan(context.repo, context.runner, commands).run()
    context.validation_results = [
        {
            "gate_id": str(gate["gate_id"]),
            "label": str(gate["label"]),
            "reference": "validation.plan",
            "status": "pass",
            "sha256": result.output_sha256,
        }
        for gate, result in zip(gates, results)
    ]

    context.inspector.require_clean()
    context.inspector.require_branch(context.source_branch)
    context.inspector.require_head(context.expected_head)
    context.inspector.require_upstream_equal()
    remote_source = context.inspector.remote_head("origin", context.source_branch)
    if remote_source != context.expected_head:
        raise WorkflowError("Remote source changed during promotion validation")
    remote_target = context.inspector.remote_head("origin", context.target_branch)
    if remote_target != context.frozen_target_head:
        raise WorkflowError(
            "Target advanced during validation; rerun promotion against new target"
        )


def eligibility_action(context: PromotionContext) -> None:
    if (
        context.snapshot is None
        or context.frozen_target_head is None
        or context.remote_source_head is None
    ):
        raise WorkflowError("Eligibility prerequisites missing")
    value = eligibility(
        policy=context.policy,
        source_branch=context.source_branch,
        source_head=context.snapshot.head,
        upstream_head=str(context.snapshot.upstream_head),
        remote_source_head=context.remote_source_head,
        target_branch=context.target_branch,
        target_head=context.frozen_target_head,
        remote_target_head=context.frozen_target_head,
        changed_paths=context.changed_paths,
        source_descends=True,
        gate_results=context.validation_results,
    )
    context.eligibility_path = write_json(
        context, "promotion-eligibility.json", value
    )


def proposal_validation(context: PromotionContext) -> tuple[dict[str, Any], ...]:
    if context.eligibility_path is None:
        raise WorkflowError("Promotion eligibility receipt missing")
    values = [
        {
            "label": item["label"],
            "reference": str(context.eligibility_path),
            "status": "pass",
            "sha256": item["sha256"],
        }
        for item in context.validation_results
    ]
    values.append(
        {
            "label": "Promotion eligibility",
            "reference": str(context.eligibility_path),
            "status": "pass",
            "sha256": sha256_file(context.eligibility_path),
        }
    )
    return tuple(values)


def create_pr_proposal(context: PromotionContext) -> dict[str, Any]:
    if context.authority_path is None or context.component_path is None:
        raise WorkflowError("Promotion receipts missing")
    proposal = OperatorGitProposal.build(
        proposal_id=proposal_id(context.expected_head, "pull-request-create"),
        controller=WORKFLOW_ID,
        repository=context.inspector.snapshot(),
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="pull-request-create",
        change_scope=context.changed_paths,
        validation=proposal_validation(context),
        command_argv=(
            "gh",
            "pr",
            "create",
            "--base",
            context.target_branch,
            "--head",
            context.source_branch,
            "--title",
            context.title,
            "--body",
            context.body,
        ),
        expected_result=(
            "Create exactly one reviewable PR for the frozen validated checkpoint; "
            "no merge occurs."
        ),
        risk="Creates GitHub review state only.",
        rollback="Close the PR without merging.",
        post_command_verification=(
            "github.inspect verifies exact base/head/source SHA",
            "git.inspect verifies frozen target remains unchanged",
        ),
    )
    context.proposal_path = context.state_dir / "operator-git-proposal-pr-create.json"
    OperatorGitProposal.write(context.proposal_path, proposal, context.writer)
    return proposal


def save_state(context: PromotionContext, proposal: Mapping[str, Any]) -> Path:
    if (
        context.proposal_path is None
        or context.frozen_target_head is None
        or context.eligibility_path is None
    ):
        raise WorkflowError("Proposal state incomplete")
    value = {
        "schema_version": "1.0",
        "record_type": "sage-checkpoint-promotion-state",
        "request": context.request,
        "request_sha256": hashlib.sha256(
            context.request.encode("utf-8")
        ).hexdigest(),
        "source_branch": context.source_branch,
        "source_head": context.expected_head,
        "target_branch": context.target_branch,
        "frozen_target_head": context.frozen_target_head,
        "changed_paths": list(context.changed_paths),
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "promotion_eligibility": str(context.eligibility_path),
        "validation": list(context.validation_results),
        "title": context.title,
        "body": context.body,
        "current_boundary": str(proposal["boundary"]),
        "current_proposal": str(context.proposal_path),
        "pull_request_number": None,
        "merge_commit_sha": None,
        "history": [],
    }
    context.state_path = context.state_dir / "checkpoint-promotion-state.json"
    context.writer.write_text(
        context.state_path, stable_json(value), new_mode=0o600
    )
    return context.state_path


def write_closeout(
    context: PromotionContext,
    status: str,
    details: Mapping[str, Any],
) -> Path:
    return CloseoutWriter(
        destination_directory=context.state_dir,
        primitive_registry=context.repo / "sage-workflow-primitives.json",
        event_log=context.state_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID,
        status=status,
        used_primitives=PRIMITIVES_USED,
        details=dict(details),
    )


def start_promotion(
    *,
    repo: Path,
    request: str,
    source_branch: str,
    expected_head: str,
    target_branch: str,
    title: str,
    body: str,
) -> Mapping[str, Any]:
    context = build_context(
        repo=repo,
        request=request,
        source_branch=source_branch,
        expected_head=expected_head,
        target_branch=target_branch,
        title=title,
        body=body,
    )
    discovery_action(context)
    git_authority_action(context)
    authority_action(context)
    validation_action(context)
    eligibility_action(context)
    proposal = create_pr_proposal(context)
    state = save_state(context, proposal)
    closeout = write_closeout(
        context,
        "operator-review-required",
        {
            "state": str(state),
            "proposal": str(context.proposal_path),
            "promotion_eligibility": str(context.eligibility_path),
            "git_mutation": False,
            "github_mutation": False,
        },
    )
    return {
        "status": "operator-review-required",
        "state": str(state),
        "proposal_path": str(context.proposal_path),
        "promotion_eligibility": str(context.eligibility_path),
        "closeout": str(closeout),
        "event_log": str(context.state_dir / "events.jsonl"),
        "proposal": proposal,
    }


def load_state(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    request = str(value.get("request", ""))
    if (
        value.get("record_type") != "sage-checkpoint-promotion-state"
        or hashlib.sha256(request.encode("utf-8")).hexdigest()
        != value.get("request_sha256")
    ):
        raise WorkflowError("Invalid checkpoint-promotion state")
    return value


def continuation_runtime(repo: Path, state_path: Path):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_dir = (
        Path("~/.local/state/kalaxy3/sage-checkpoint-promotion").expanduser()
        / ("continue-" + stamp)
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    catalog = PrimitiveCatalog.load(repo / "sage-workflow-primitives.json")
    catalog.require(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        run_dir / "events.jsonl",
        WORKFLOW_ID + ".post-operator",
        primitive_versions=catalog.versions_for(PRIMITIVES_USED),
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(repo, run_dir, state_path.parent),
        base_environment={name: "" for name in SECRET_ENVIRONMENT_NAMES},
    )
    policy = json.loads((repo / POLICY_PATH).read_text(encoding="utf-8"))
    github_policy = policy["github_repository"]
    return (
        runner,
        GitInspector(repo, runner),
        GitHubInspector(
            str(github_policy["owner"]),
            str(github_policy["name"]),
        ),
        AtomicFileWriter((run_dir, state_path.parent)),
        run_dir,
    )


def continuation_validation(state: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        {
            "label": item["label"],
            "reference": str(state["promotion_eligibility"]),
            "status": "pass",
            "sha256": item["sha256"],
        }
        for item in state["validation"]
    )


def continue_promotion(
    *,
    repo: Path,
    state_path: Path,
    operator_result_path: Path,
) -> Mapping[str, Any]:
    resolved_repo = repo.expanduser().resolve()
    resolved_state = state_path.expanduser().resolve()
    state = load_state(resolved_state)
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    result = validate_operator_result(
        json.loads(
            operator_result_path.expanduser().resolve().read_text(encoding="utf-8")
        ),
        proposal,
    )
    runner, inspector, github, writer, run_dir = continuation_runtime(
        resolved_repo, resolved_state
    )

    inspector.require_clean()
    inspector.require_branch(str(state["source_branch"]))
    inspector.require_head(str(state["source_head"]))
    inspector.require_upstream_equal()
    remote_source = inspector.remote_head("origin", str(state["source_branch"]))
    if remote_source != state["source_head"]:
        raise WorkflowError("Remote source changed after promotion validation")

    boundary = str(proposal["boundary"])
    next_proposal: dict[str, Any] | None = None
    verification: dict[str, Any]

    if boundary == "pull-request-create":
        pr = github.find_pull_request(
            base_branch=str(state["target_branch"]),
            head_branch=str(state["source_branch"]),
            head_sha=str(state["source_head"]),
        )
        if pr.merged or pr.state != "open" or pr.draft:
            raise WorkflowError("Promotion PR is not an open non-draft PR")
        checked = github.require_pull_request(
            pr.number,
            base_branch=str(state["target_branch"]),
            head_branch=str(state["source_branch"]),
            head_sha=str(state["source_head"]),
            merged=False,
            require_mergeable=True,
        )
        current_target = inspector.remote_head(
            "origin", str(state["target_branch"])
        )
        if current_target != state["frozen_target_head"]:
            raise WorkflowError(
                "Target advanced after validation; rerun checkpoint promotion"
            )
        if checked.base_sha != state["frozen_target_head"]:
            raise WorkflowError("Promotion PR base SHA differs from frozen target")
        state["pull_request_number"] = checked.number
        next_proposal = OperatorGitProposal.build(
            proposal_id=proposal_id(str(state["source_head"]), "pull-request-merge"),
            controller=WORKFLOW_ID,
            repository=inspector.snapshot(),
            authority_receipt=str(state["authority_receipt"]),
            component_manifest=str(state["component_manifest"]),
            boundary="pull-request-merge",
            change_scope=tuple(state["changed_paths"]),
            validation=continuation_validation(state),
            command_argv=("gh", "pr", "merge", str(checked.number), "--merge"),
            expected_result=(
                "Merge exactly the independently verified frozen checkpoint PR."
            ),
            risk="Mutates main through the explicit GitHub operator boundary.",
            rollback=(
                "Do not execute if review is not approved; a merged change requires "
                "a separately governed revert."
            ),
            post_command_verification=(
                "github.inspect verifies merged state and exact source SHA",
                "git.inspect verifies remote main equals the merge commit",
                "an explicit operator fetch refreshes the local graph",
            ),
        )
        next_path = run_dir / "operator-git-proposal-pr-merge.json"
        OperatorGitProposal.write(next_path, next_proposal, writer)
        state["current_boundary"] = "pull-request-merge"
        state["current_proposal"] = str(next_path)
        verification = {
            "status": "pass",
            "boundary": boundary,
            "pull_request": checked.as_dict(),
            "frozen_target_head": current_target,
        }

    elif boundary == "pull-request-merge":
        number = state.get("pull_request_number")
        if not isinstance(number, int):
            raise WorkflowError("Promotion state lacks PR number")
        pr = github.require_pull_request(
            number,
            base_branch=str(state["target_branch"]),
            head_branch=str(state["source_branch"]),
            head_sha=str(state["source_head"]),
            merged=True,
        )
        if pr.merged_at is None or pr.merge_commit_sha is None:
            raise WorkflowError("Merged PR lacks complete merge facts")
        remote_target = inspector.remote_head(
            "origin", str(state["target_branch"])
        )
        if remote_target != pr.merge_commit_sha:
            raise WorkflowError(
                "Remote target does not equal the independently verified merge "
                f"commit: remote={remote_target}, merge={pr.merge_commit_sha}"
            )
        state["merge_commit_sha"] = pr.merge_commit_sha
        next_proposal = OperatorGitProposal.build(
            proposal_id=proposal_id(str(state["source_head"]), "post-merge-fetch"),
            controller=WORKFLOW_ID,
            repository=inspector.snapshot(),
            authority_receipt=str(state["authority_receipt"]),
            component_manifest=str(state["component_manifest"]),
            boundary="other-git-mutation",
            change_scope=tuple(state["changed_paths"]),
            validation=continuation_validation(state),
            command_argv=("git", "fetch", "origin", str(state["target_branch"])),
            expected_result=(
                "Refresh the local remote-tracking target after the verified merge; "
                "no working-tree or branch content changes."
            ),
            risk="Updates local remote-tracking Git references only.",
            rollback="No content rollback; verification fails closed on any mismatch.",
            post_command_verification=(
                "git.inspect verifies origin/main equals the merge commit",
                "git.inspect proves frozen source is an ancestor of origin/main",
            ),
        )
        next_path = run_dir / "operator-git-proposal-post-merge-fetch.json"
        OperatorGitProposal.write(next_path, next_proposal, writer)
        state["current_boundary"] = "other-git-mutation"
        state["current_proposal"] = str(next_path)
        verification = {
            "status": "pass",
            "boundary": boundary,
            "pull_request": pr.as_dict(),
            "remote_target_head": remote_target,
            "next_boundary": "post-merge-fetch",
        }

    elif boundary == "other-git-mutation":
        command = tuple(str(item) for item in proposal["command"]["argv"])
        expected = ("git", "fetch", "origin", str(state["target_branch"]))
        if command != expected:
            raise WorkflowError(
                "Checkpoint promotion permits only the exact post-merge fetch "
                f"at this boundary: expected={expected}, observed={command}"
            )
        merge_commit = state.get("merge_commit_sha")
        if not isinstance(merge_commit, str) or not merge_commit:
            raise WorkflowError("Promotion state lacks verified merge commit")
        local_target = inspector.head(f"origin/{state['target_branch']}")
        remote_target = inspector.remote_head("origin", str(state["target_branch"]))
        if local_target != merge_commit or remote_target != merge_commit:
            raise WorkflowError(
                "Post-merge Git authority mismatch: "
                f"local={local_target}, remote={remote_target}, merge={merge_commit}"
            )
        if not inspector.is_ancestor(str(state["source_head"]), local_target):
            raise WorkflowError(
                "Frozen source head is not contained in refreshed origin/main"
            )
        state["current_boundary"] = "complete"
        state["current_proposal"] = None
        verification = {
            "status": "pass",
            "boundary": "post-merge-fetch",
            "source_head": state["source_head"],
            "origin_main": local_target,
            "remote_main": remote_target,
            "source_contained_in_main": True,
        }

    else:
        raise WorkflowError(f"Unsupported promotion boundary: {boundary}")

    history = list(state["history"])
    history.append(
        {
            "boundary": boundary,
            "proposal": str(proposal_path),
            "operator_output_sha256": result["complete_output_sha256"],
            "verification": verification,
        }
    )
    state["history"] = history
    writer.write_text(resolved_state, stable_json(state), new_mode=0o600)

    verification_path = run_dir / "post-operator-verification.json"
    writer.write_text(
        verification_path, stable_json(verification), new_mode=0o600
    )
    closeout = CloseoutWriter(
        destination_directory=run_dir,
        primitive_registry=resolved_repo / "sage-workflow-primitives.json",
        event_log=run_dir / "events.jsonl",
    ).write(
        workflow_id=WORKFLOW_ID + ".post-operator",
        status="verified",
        used_primitives=PRIMITIVES_USED,
        details={
            "boundary": boundary,
            "verification": str(verification_path),
            "state": str(resolved_state),
        },
    )
    return {
        "status": "complete" if next_proposal is None else "operator-review-required",
        "verified_boundary": boundary,
        "verification": str(verification_path),
        "evidence_closeout": str(closeout),
        "state": str(resolved_state),
        "proposal": next_proposal,
        "proposal_path": state["current_proposal"],
        "event_log": str(run_dir / "events.jsonl"),
    }


def self_test() -> int:
    policy_self_test()
    snapshot = GitAuthoritySnapshot(
        path="/fixture",
        branch="staged/x",
        head="1" * 40,
        upstream_head="1" * 40,
        working_tree_status="clean",
        changed_paths=(),
    )
    validation = (
        {
            "label": "fixture",
            "reference": "fixture:v",
            "status": "pass",
            "sha256": "a" * 64,
        },
    )
    create = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260811-101",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="pull-request-create",
        change_scope=("README.md",),
        validation=validation,
        command_argv=(
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            "staged/x",
            "--title",
            "x",
            "--body",
            "x",
        ),
        expected_result="x",
        risk="x",
        rollback="x",
        post_command_verification=("x",),
        created_at="2026-08-11T18:00:00-05:00",
    )
    merge = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260811-102",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="pull-request-merge",
        change_scope=("README.md",),
        validation=validation,
        command_argv=("gh", "pr", "merge", "42", "--merge"),
        expected_result="x",
        risk="x",
        rollback="x",
        post_command_verification=("x",),
        created_at="2026-08-11T18:00:01-05:00",
    )
    refresh = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260811-103",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="other-git-mutation",
        change_scope=("README.md",),
        validation=validation,
        command_argv=("git", "fetch", "origin", "main"),
        expected_result="x",
        risk="x",
        rollback="x",
        post_command_verification=("x",),
        created_at="2026-08-11T18:00:02-05:00",
    )
    assert create["command"]["executed_by_helper"] is False
    assert merge["command"]["executed_by_helper"] is False
    assert refresh["command"]["executed_by_helper"] is False
    print("PASS PR-create and PR-merge remain explicit operator boundaries")
    print("PASS post-merge Git graph refresh remains an explicit operator boundary")
    print("PASS workflow has no autonomous Git or GitHub mutation")
    print("Kalaxy3 checkpoint promotion workflow self-test: PASS")
    return 0
