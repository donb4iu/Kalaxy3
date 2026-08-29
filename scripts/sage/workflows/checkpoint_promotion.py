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
WORKFLOW_VERSION = "1.3.0"
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
    reconciliation_required: bool = False
    reconciliation_source_paths: tuple[str, ...] = ()
    reconciliation_target_paths: tuple[str, ...] = ()
    reconciliation_overlap_paths: tuple[str, ...] = ()
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


_URL_UNRESERVED = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def percent_encode(value: str, *, safe: str = "") -> str:
    safe_bytes = {ord(character) for character in safe}
    encoded: list[str] = []
    for byte in value.encode("utf-8"):
        if byte in _URL_UNRESERVED or byte in safe_bytes:
            encoded.append(chr(byte))
        else:
            encoded.append(f"%{byte:02X}")
    return "".join(encoded)


def query_string(values: Mapping[str, str]) -> str:
    return "&".join(
        f"{percent_encode(str(key))}={percent_encode(str(value))}"
        for key, value in values.items()
    )


def github_compare_url(
    github_policy: Mapping[str, Any],
    *,
    base_branch: str,
    head_branch: str,
    title: str,
    body: str,
) -> str:
    owner = str(github_policy.get("owner", "")).strip()
    name = str(github_policy.get("name", "")).strip()
    if not owner or not name:
        raise WorkflowError("GitHub repository policy is incomplete")
    compare = (
        f"https://github.com/{percent_encode(owner)}/{percent_encode(name)}/compare/"
        f"{percent_encode(base_branch, safe='/')}...{percent_encode(head_branch, safe='/')}"
    )
    query = query_string(
        {
            "quick_pull": "1",
            "title": title,
            "body": body,
        }
    )
    return f"{compare}?{query}"


def github_pull_url(
    github_policy: Mapping[str, Any],
    *,
    pull_request_number: int,
) -> str:
    owner = str(github_policy.get("owner", "")).strip()
    name = str(github_policy.get("name", "")).strip()
    if not owner or not name or pull_request_number <= 0:
        raise WorkflowError("GitHub pull-request browser context is incomplete")
    return (
        f"https://github.com/{percent_encode(owner)}/{percent_encode(name)}/pull/"
        f"{pull_request_number}"
    )



def required_github_checks(policy: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    promotion = policy.get("promotion_policy")
    if not isinstance(promotion, Mapping):
        raise WorkflowError("checkpoint promotion policy lacks promotion_policy")
    raw = promotion.get("required_github_checks")
    if not isinstance(raw, list) or not raw:
        raise WorkflowError("checkpoint promotion requires at least one GitHub check")
    result: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping) or set(item) != {"name", "app_slug"}:
            raise WorkflowError(f"required_github_checks[{index}] must contain name and app_slug only")
        name = str(item.get("name", "")).strip()
        app_slug = str(item.get("app_slug", "")).strip()
        if not name or not app_slug:
            raise WorkflowError(f"required_github_checks[{index}] is incomplete")
        key = (name, app_slug)
        if key in seen:
            raise WorkflowError(f"duplicate required GitHub check: {name}/{app_slug}")
        seen.add(key)
        result.append(key)
    return tuple(result)

def validate_browser_operator_result(
    payload: Mapping[str, Any],
    proposal: Mapping[str, Any],
) -> dict[str, Any]:
    browser = proposal.get("browser")
    if proposal.get("schema_version") != "1.1" or not isinstance(browser, Mapping):
        raise WorkflowError("Browser operator result requires proposal schema 1.1")
    if payload.get("schema_version") != "1.0":
        raise WorkflowError("Browser operator result schema_version must be 1.0")
    if payload.get("proposal_id") != proposal.get("proposal_id"):
        raise WorkflowError("Browser operator result proposal_id mismatch")
    if payload.get("browser_sha256") != browser.get("sha256"):
        raise WorkflowError("Browser operator result interaction digest mismatch")
    if payload.get("operator_confirmation_received") is not True:
        raise WorkflowError("Browser operator confirmation is required")
    allowed = {
        "schema_version",
        "proposal_id",
        "browser_sha256",
        "operator_confirmation_received",
    }
    extras = sorted(set(payload) - allowed)
    if extras:
        raise WorkflowError(f"Unexpected browser operator result fields: {extras}")
    digest = hashlib.sha256(stable_json(dict(payload)).encode("utf-8")).hexdigest()
    return {
        "complete_output_sha256": digest,
        "browser_sha256": str(browser["sha256"]),
        "operator_confirmation_received": True,
    }


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

    source_paths = context.inspector.diff_paths(
        local_target, local_source, three_dot=True
    )
    if not source_paths:
        raise WorkflowError("Promotion delta is empty")

    context.snapshot = context.inspector.snapshot()
    context.frozen_target_head = local_target
    context.remote_source_head = remote_source
    context.changed_paths = tuple(sorted(source_paths))

    if context.inspector.is_ancestor(local_target, local_source):
        return

    reconciliation = context.policy.get("source_reconciliation_policy", {})
    if not isinstance(reconciliation, Mapping) or reconciliation.get("enabled") is not True:
        raise WorkflowError("Source does not descend from frozen target")

    target_paths = context.inspector.diff_paths(
        local_source, local_target, three_dot=True
    )
    if not target_paths:
        raise WorkflowError(
            "Source does not descend from frozen target and target has no unique delta"
        )
    overlap = source_paths & target_paths
    context.reconciliation_required = True
    context.reconciliation_source_paths = tuple(sorted(source_paths))
    context.reconciliation_target_paths = tuple(sorted(target_paths))
    context.reconciliation_overlap_paths = tuple(sorted(overlap))
    if overlap:
        raise WorkflowError(
            "Source/target reconciliation requires Architect review because both sides "
            f"changed the same paths: {sorted(overlap)}"
        )


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



def reconciliation_validation(context: PromotionContext) -> tuple[dict[str, Any], ...]:
    if (
        context.frozen_target_head is None
        or context.remote_source_head is None
        or context.authority_path is None
        or context.component_path is None
    ):
        raise WorkflowError("Source reconciliation prerequisites missing")
    facts = {
        "schema_version": "1.0",
        "record_type": "sage-checkpoint-source-reconciliation-facts",
        "request": context.request,
        "source_branch": context.source_branch,
        "source_head": context.expected_head,
        "remote_source_head": context.remote_source_head,
        "target_branch": context.target_branch,
        "frozen_target_head": context.frozen_target_head,
        "source_changed_paths": list(context.reconciliation_source_paths),
        "target_changed_paths": list(context.reconciliation_target_paths),
        "overlapping_changed_paths": list(context.reconciliation_overlap_paths),
        "source_descends_from_target": False,
        "reconciliation_required": True,
    }
    facts_path = write_json(context, "source-reconciliation-facts.json", facts)
    digest = sha256_file(facts_path)
    return (
        {
            "label": "Frozen source and target authority",
            "reference": str(facts_path),
            "status": "pass",
            "sha256": digest,
        },
        {
            "label": "Disjoint source/target changed paths",
            "reference": str(facts_path),
            "status": "pass",
            "sha256": digest,
        },
        {
            "label": "Governed reconciliation component reuse",
            "reference": str(context.component_path),
            "status": "pass",
            "sha256": sha256_file(context.component_path),
        },
    )


def create_source_reconciliation_proposal(
    context: PromotionContext,
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    if (
        context.snapshot is None
        or context.frozen_target_head is None
        or context.authority_path is None
        or context.component_path is None
    ):
        raise WorkflowError("Source reconciliation receipts missing")
    if context.reconciliation_overlap_paths:
        raise WorkflowError("Source reconciliation path overlap is not eligible")
    validation = reconciliation_validation(context)
    scope = tuple(
        sorted(
            set(context.reconciliation_target_paths)
            | {f"refs/heads/{context.source_branch}"}
        )
    )
    proposal = OperatorGitProposal.build(
        proposal_id=proposal_id(context.expected_head, "source-reconciliation-merge"),
        controller=WORKFLOW_ID,
        repository=context.snapshot,
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="other-git-mutation",
        change_scope=scope,
        validation=validation,
        command_argv=(
            "git",
            "merge",
            "--no-edit",
            "--no-ff",
            context.frozen_target_head,
        ),
        expected_result=(
            "Create exactly one local merge commit on the synchronized source branch "
            "whose first parent is the frozen source and whose second parent is the "
            "exact frozen target; no push or promotion occurs."
        ),
        risk=(
            "Mutates only the local source branch. Reconciliation is offered only after "
            "git.inspect proves the source-side and target-side changed-path sets are "
            "disjoint; any unexpected merge conflict or topology mismatch fails closed."
        ),
        rollback=(
            "Do not execute the proposal. After execution, any rollback requires a "
            "separately governed recovery boundary; no reset or rebase is authorized."
        ),
        post_command_verification=(
            "git.inspect verifies the working tree is clean",
            "git.inspect verifies the exact ordered merge-parent topology",
            "git.inspect verifies the remote source still equals the frozen pre-merge source",
        ),
    )
    context.proposal_path = (
        context.state_dir / "operator-git-proposal-source-reconciliation-merge.json"
    )
    OperatorGitProposal.write(context.proposal_path, proposal, context.writer)
    return proposal, validation


def save_source_reconciliation_state(
    context: PromotionContext,
    proposal: Mapping[str, Any],
    validation: tuple[dict[str, Any], ...],
) -> Path:
    if (
        context.proposal_path is None
        or context.frozen_target_head is None
        or context.authority_path is None
        or context.component_path is None
    ):
        raise WorkflowError("Source reconciliation state prerequisites missing")
    value = {
        "schema_version": "1.0",
        "record_type": "sage-checkpoint-promotion-state",
        "mode": "source-reconciliation",
        "request": context.request,
        "request_sha256": hashlib.sha256(
            context.request.encode("utf-8")
        ).hexdigest(),
        "source_branch": context.source_branch,
        "source_head": context.expected_head,
        "target_branch": context.target_branch,
        "frozen_target_head": context.frozen_target_head,
        "changed_paths": list(context.changed_paths),
        "source_changed_paths": list(context.reconciliation_source_paths),
        "target_changed_paths": list(context.reconciliation_target_paths),
        "overlapping_changed_paths": [],
        "authority_receipt": str(context.authority_path),
        "component_manifest": str(context.component_path),
        "reconciliation_validation": [dict(item) for item in validation],
        "title": context.title,
        "body": context.body,
        "current_boundary": str(proposal["boundary"]),
        "current_proposal": str(context.proposal_path),
        "reconciliation_phase": "merge-frozen-target-into-source",
        "reconciled_head": None,
        "history": [],
    }
    context.state_path = context.state_dir / "checkpoint-promotion-state.json"
    context.writer.write_text(
        context.state_path, stable_json(value), new_mode=0o600
    )
    return context.state_path


def start_source_reconciliation(context: PromotionContext) -> Mapping[str, Any]:
    proposal, validation = create_source_reconciliation_proposal(context)
    state = save_source_reconciliation_state(context, proposal, validation)
    closeout = write_closeout(
        context,
        "operator-review-required",
        {
            "state": str(state),
            "proposal": str(context.proposal_path),
            "source_reconciliation": True,
            "frozen_source": context.expected_head,
            "frozen_target": context.frozen_target_head,
            "source_changed_paths": list(context.reconciliation_source_paths),
            "target_changed_paths": list(context.reconciliation_target_paths),
            "overlapping_changed_paths": [],
            "git_mutation": False,
            "github_mutation": False,
        },
    )
    return {
        "status": "operator-review-required",
        "state": str(state),
        "proposal_path": str(context.proposal_path),
        "closeout": str(closeout),
        "event_log": str(context.state_dir / "events.jsonl"),
        "source_reconciliation": True,
        "proposal": proposal,
    }


def source_reconciliation_continuation_validation(
    state: Mapping[str, Any],
) -> tuple[dict[str, Any], ...]:
    values = state.get("reconciliation_validation")
    if not isinstance(values, list) or not values:
        raise WorkflowError("Source reconciliation validation evidence missing")
    return tuple(dict(item) for item in values)



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
    github_policy = context.policy["github_repository"]
    proposal = OperatorGitProposal.build_browser(
        proposal_id=proposal_id(context.expected_head, "pull-request-create"),
        controller=WORKFLOW_ID,
        repository=context.inspector.snapshot(),
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="pull-request-create",
        change_scope=context.changed_paths,
        validation=proposal_validation(context),
        browser_action="create-pull-request",
        browser_url=github_compare_url(
            github_policy,
            base_branch=context.target_branch,
            head_branch=context.source_branch,
            title=context.title,
            body=context.body,
        ),
        expected_result=(
            "Review the fully prepared GitHub pull-request form and click Create pull "
            "request; no merge occurs."
        ),
        risk="Creates GitHub review state only after explicit operator approval.",
        rollback="Close the PR without merging.",
        post_interaction_verification=(
            "github.inspect verifies exact base/head/source SHA",
            "git.inspect verifies frozen target remains unchanged",
        ),
    )
    context.proposal_path = context.state_dir / "operator-git-proposal-pr-create.json"
    OperatorGitProposal.write(context.proposal_path, proposal, context.writer)
    return proposal


def existing_pr_merge_proposal(context: PromotionContext) -> tuple[dict[str, Any], Any, tuple[Any, ...], str] | None:
    if context.authority_path is None or context.component_path is None or context.frozen_target_head is None:
        raise WorkflowError("Promotion receipts missing before existing-PR lookup")
    pr = context.github.find_pull_request(
        base_branch=context.target_branch,
        head_branch=context.source_branch,
        head_sha=context.expected_head,
        required=False,
    )
    if pr is None:
        return None
    if pr.merged or pr.state != "open" or pr.draft:
        raise WorkflowError("Existing promotion PR is not an open non-draft PR")
    checked = context.github.require_pull_request(
        pr.number,
        base_branch=context.target_branch,
        head_branch=context.source_branch,
        head_sha=context.expected_head,
        merged=False,
        require_mergeable=True,
    )
    check_runs = context.github.require_successful_checks(
        head_sha=context.expected_head,
        required=required_github_checks(context.policy),
    )
    current_target = context.inspector.remote_head("origin", context.target_branch)
    if current_target != context.frozen_target_head:
        raise WorkflowError("Target advanced after validation; rerun checkpoint promotion")
    if checked.base_sha != context.frozen_target_head:
        raise WorkflowError("Existing promotion PR base SHA differs from frozen target")
    github_policy = context.policy["github_repository"]
    proposal = OperatorGitProposal.build_browser(
        proposal_id=proposal_id(context.expected_head, "pull-request-merge"),
        controller=WORKFLOW_ID,
        repository=context.inspector.snapshot(),
        authority_receipt=str(context.authority_path),
        component_manifest=str(context.component_path),
        boundary="pull-request-merge",
        change_scope=context.changed_paths,
        validation=proposal_validation(context),
        browser_action="merge-pull-request",
        browser_url=github_pull_url(github_policy, pull_request_number=checked.number),
        expected_result=(
            "Review the independently verified existing pull request, select Create a merge "
            "commit if GitHub presents multiple merge methods, and click the final merge confirmation."
        ),
        risk="Mutates main only after explicit operator approval in GitHub.",
        rollback="Do not approve if review is not complete; a merged change requires a separately governed revert.",
        post_interaction_verification=(
            "github.inspect verifies merged state and exact source SHA",
            "git.inspect verifies remote main equals the merge commit",
            "an explicit operator fetch refreshes the local graph",
        ),
    )
    context.proposal_path = context.state_dir / "operator-git-proposal-pr-merge.json"
    OperatorGitProposal.write(context.proposal_path, proposal, context.writer)
    return proposal, checked, check_runs, current_target


def save_state(
    context: PromotionContext,
    proposal: Mapping[str, Any],
    *,
    pull_request_number: int | None = None,
    required_github_checks: tuple[Mapping[str, Any], ...] = (),
    existing_pull_request_reused: bool = False,
) -> Path:
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
        "pull_request_number": pull_request_number,
        "required_github_checks": [dict(item) for item in required_github_checks],
        "existing_pull_request_reused": existing_pull_request_reused,
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
    if context.reconciliation_required:
        return start_source_reconciliation(context)
    validation_action(context)
    eligibility_action(context)
    existing = existing_pr_merge_proposal(context)
    if existing is None:
        proposal = create_pr_proposal(context)
        state = save_state(context, proposal)
        existing_pr_reused = False
    else:
        proposal, checked, check_runs, current_target = existing
        state = save_state(
            context,
            proposal,
            pull_request_number=checked.number,
            required_github_checks=tuple(item.as_dict() for item in check_runs),
            existing_pull_request_reused=True,
        )
        existing_pr_reused = True
    closeout = write_closeout(
        context,
        "operator-review-required",
        {
            "state": str(state),
            "proposal": str(context.proposal_path),
            "promotion_eligibility": str(context.eligibility_path),
            "git_mutation": False,
            "github_mutation": False,
            "existing_pull_request_reused": existing_pr_reused,
        },
    )
    return {
        "status": "operator-review-required",
        "state": str(state),
        "proposal_path": str(context.proposal_path),
        "promotion_eligibility": str(context.eligibility_path),
        "closeout": str(closeout),
        "event_log": str(context.state_dir / "events.jsonl"),
        "existing_pull_request_reused": existing_pr_reused,
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



def continue_source_reconciliation(
    *,
    repo: Path,
    state_path: Path,
    operator_result_path: Path,
) -> Mapping[str, Any]:
    resolved_repo = repo.expanduser().resolve()
    resolved_state = state_path.expanduser().resolve()
    state = load_state(resolved_state)
    if state.get("mode") != "source-reconciliation":
        raise WorkflowError("Checkpoint state is not a source-reconciliation state")
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    operator_payload = json.loads(
        operator_result_path.expanduser().resolve().read_text(encoding="utf-8")
    )
    result = validate_operator_result(operator_payload, proposal)
    runner, inspector, _github, writer, run_dir = continuation_runtime(
        resolved_repo, resolved_state
    )

    inspector.require_clean()
    source_branch = str(state["source_branch"])
    inspector.require_branch(source_branch)
    current_source = inspector.head()
    remote_source = inspector.remote_head("origin", source_branch)
    frozen_source = str(state["source_head"])
    frozen_target = str(state["frozen_target_head"])
    phase = str(state.get("reconciliation_phase", ""))
    validation = source_reconciliation_continuation_validation(state)

    next_proposal: dict[str, Any] | None = None
    verification: dict[str, Any]

    if phase == "merge-frozen-target-into-source":
        if str(proposal.get("boundary")) != "other-git-mutation":
            raise WorkflowError("Source reconciliation merge boundary is invalid")
        expected_command = (
            "git",
            "merge",
            "--no-edit",
            "--no-ff",
            frozen_target,
        )
        command = tuple(str(item) for item in proposal["command"]["argv"])
        if command != expected_command:
            raise WorkflowError(
                "Source reconciliation permits only the exact frozen-target merge: "
                f"expected={expected_command}, observed={command}"
            )
        upstream_before_push = inspector.head("@{upstream}")
        if upstream_before_push != frozen_source or remote_source != frozen_source:
            raise WorkflowError(
                "Remote source changed before reconciliation push: "
                f"frozen={frozen_source}, upstream={upstream_before_push}, "
                f"remote={remote_source}"
            )
        if current_source == frozen_source:
            raise WorkflowError("Source reconciliation merge produced no new commit")
        if not inspector.is_ancestor(frozen_source, current_source):
            raise WorkflowError("Frozen source is not an ancestor of reconciled source")
        if not inspector.is_ancestor(frozen_target, current_source):
            raise WorkflowError("Frozen target is not an ancestor of reconciled source")
        merge_commit = inspector.find_merge_commit(
            base_parent=frozen_source,
            merged_parent=frozen_target,
            descendant=current_source,
        )
        if merge_commit != current_source:
            raise WorkflowError(
                "Source reconciliation head is not the exact merge commit: "
                f"head={current_source}, merge={merge_commit}"
            )

        next_proposal = OperatorGitProposal.build(
            proposal_id=proposal_id(current_source, "source-reconciliation-push"),
            controller=WORKFLOW_ID,
            repository=inspector.snapshot(),
            authority_receipt=str(state["authority_receipt"]),
            component_manifest=str(state["component_manifest"]),
            boundary="push",
            change_scope=(f"refs/heads/{source_branch}",),
            validation=validation,
            command_argv=("git", "push", "origin", source_branch),
            expected_result=(
                "Publish exactly the verified reconciliation merge commit to the "
                "existing source branch; no PR or main-branch mutation occurs."
            ),
            risk=(
                "Mutates only the declared remote source branch. Promotion remains "
                "blocked until checkpoint promotion restarts and reruns every "
                "applicable validation gate against current main."
            ),
            rollback=(
                "Do not execute the proposal; after execution, any remote rollback "
                "requires a separately governed boundary."
            ),
            post_command_verification=(
                "git.inspect verifies local source equals its upstream and live remote source",
                "git.inspect verifies frozen source and frozen target remain ancestors",
                "checkpoint promotion restarts against current target authority",
            ),
        )
        next_path = run_dir / "operator-git-proposal-source-reconciliation-push.json"
        OperatorGitProposal.write(next_path, next_proposal, writer)
        state["reconciled_head"] = current_source
        state["reconciliation_phase"] = "push-reconciled-source"
        state["current_boundary"] = "push"
        state["current_proposal"] = str(next_path)
        verification = {
            "status": "pass",
            "boundary": "source-reconciliation-merge",
            "frozen_source": frozen_source,
            "frozen_target": frozen_target,
            "reconciled_head": current_source,
            "exact_merge_parent_topology": True,
            "next_boundary": "push-reconciled-source",
        }

    elif phase == "push-reconciled-source":
        if str(proposal.get("boundary")) != "push":
            raise WorkflowError("Source reconciliation push boundary is invalid")
        expected_command = ("git", "push", "origin", source_branch)
        command = tuple(str(item) for item in proposal["command"]["argv"])
        if command != expected_command:
            raise WorkflowError(
                "Source reconciliation permits only the exact source push: "
                f"expected={expected_command}, observed={command}"
            )
        reconciled_head = str(state.get("reconciled_head") or "")
        if current_source != reconciled_head:
            raise WorkflowError(
                "Reconciled source HEAD changed before push verification: "
                f"expected={reconciled_head}, observed={current_source}"
            )
        upstream = inspector.require_upstream_equal()
        remote_source = inspector.remote_head("origin", source_branch)
        if upstream != current_source or remote_source != current_source:
            raise WorkflowError(
                "Reconciled source is not synchronized after push: "
                f"head={current_source}, upstream={upstream}, remote={remote_source}"
            )
        if not inspector.is_ancestor(frozen_source, current_source):
            raise WorkflowError("Frozen source ancestry was lost after reconciliation")
        if not inspector.is_ancestor(frozen_target, current_source):
            raise WorkflowError("Frozen target ancestry was lost after reconciliation")
        merge_commit = inspector.find_merge_commit(
            base_parent=frozen_source,
            merged_parent=frozen_target,
            descendant=current_source,
        )
        if merge_commit != current_source:
            raise WorkflowError(
                "Reconciled source no longer resolves to the exact merge commit"
            )

        state["reconciliation_phase"] = "complete"
        state["current_boundary"] = "complete"
        state["current_proposal"] = None
        verification = {
            "status": "pass",
            "boundary": "source-reconciliation-push",
            "frozen_source": frozen_source,
            "frozen_target": frozen_target,
            "reconciled_head": current_source,
            "remote_source": remote_source,
            "source_synchronized": True,
            "return_to_parent_objective": "checkpoint-promotion",
        }
    else:
        raise WorkflowError(f"Unsupported source reconciliation phase: {phase}")

    history = list(state["history"])
    history.append(
        {
            "boundary": str(proposal["boundary"]),
            "phase": phase,
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
        workflow_id=WORKFLOW_ID + ".source-reconciliation.post-operator",
        status="verified",
        used_primitives=PRIMITIVES_USED,
        details={
            "verification": str(verification_path),
            "state": str(resolved_state),
        },
    )

    if next_proposal is not None:
        return {
            "status": "operator-review-required",
            "verified_boundary": "source-reconciliation-merge",
            "verification": str(verification_path),
            "evidence_closeout": str(closeout),
            "state": str(resolved_state),
            "proposal": next_proposal,
            "proposal_path": state["current_proposal"],
            "event_log": str(run_dir / "events.jsonl"),
            "source_reconciliation": True,
        }

    restarted = dict(
        start_promotion(
            repo=resolved_repo,
            request=str(state["request"]),
            source_branch=source_branch,
            expected_head=current_source,
            target_branch=str(state["target_branch"]),
            title=str(state["title"]),
            body=str(state["body"]),
        )
    )
    restarted["source_reconciliation_completed"] = True
    restarted["source_reconciliation_state"] = str(resolved_state)
    restarted["source_reconciliation_verification"] = str(verification_path)
    restarted["reconciled_head"] = current_source
    return restarted



def continue_promotion(
    *,
    repo: Path,
    state_path: Path,
    operator_result_path: Path,
) -> Mapping[str, Any]:
    resolved_repo = repo.expanduser().resolve()
    resolved_state = state_path.expanduser().resolve()
    state = load_state(resolved_state)
    if state.get("mode") == "source-reconciliation":
        return continue_source_reconciliation(
            repo=resolved_repo,
            state_path=resolved_state,
            operator_result_path=operator_result_path,
        )
    proposal_path = Path(str(state["current_proposal"])).expanduser().resolve()
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    operator_payload = json.loads(
        operator_result_path.expanduser().resolve().read_text(encoding="utf-8")
    )
    if proposal.get("schema_version") == "1.1" and "browser" in proposal:
        result = validate_browser_operator_result(operator_payload, proposal)
    else:
        result = validate_operator_result(operator_payload, proposal)
    runner, inspector, github, writer, run_dir = continuation_runtime(
        resolved_repo, resolved_state
    )

    boundary = str(proposal["boundary"])
    inspector.require_clean()
    inspector.require_branch(str(state["source_branch"]))
    current_source = inspector.head()
    inspector.require_upstream_equal()
    remote_source = inspector.remote_head("origin", str(state["source_branch"]))
    if remote_source != current_source:
        raise WorkflowError(
            "Current source branch is not synchronized: "
            f"local={current_source}, remote={remote_source}"
        )
    frozen_source = str(state["source_head"])
    if boundary == "pull-request-create":
        if current_source != frozen_source:
            raise WorkflowError("Remote source changed before pull-request verification")
    elif not inspector.is_ancestor(frozen_source, current_source):
        raise WorkflowError(
            "Frozen promotion source is not an ancestor of current source branch"
        )

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
        policy = json.loads((resolved_repo / POLICY_PATH).read_text(encoding="utf-8"))
        check_runs = github.require_successful_checks(
            head_sha=str(state["source_head"]),
            required=required_github_checks(policy),
        )
        state["required_github_checks"] = [item.as_dict() for item in check_runs]
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
        github_policy = json.loads(
            (resolved_repo / POLICY_PATH).read_text(encoding="utf-8")
        )["github_repository"]
        next_proposal = OperatorGitProposal.build_browser(
            proposal_id=proposal_id(str(state["source_head"]), "pull-request-merge"),
            controller=WORKFLOW_ID,
            repository=inspector.snapshot(),
            authority_receipt=str(state["authority_receipt"]),
            component_manifest=str(state["component_manifest"]),
            boundary="pull-request-merge",
            change_scope=tuple(state["changed_paths"]),
            validation=continuation_validation(state),
            browser_action="merge-pull-request",
            browser_url=github_pull_url(
                github_policy,
                pull_request_number=checked.number,
            ),
            expected_result=(
                "Review the independently verified pull request, select Create a merge "
                "commit if GitHub presents multiple merge methods, and click the final "
                "merge confirmation."
            ),
            risk="Mutates main only after explicit operator approval in GitHub.",
            rollback=(
                "Do not approve if review is not complete; a merged change requires "
                "a separately governed revert."
            ),
            post_interaction_verification=(
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
            "required_github_checks": [item.as_dict() for item in check_runs],
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
        if pr.merged_at is None:
            raise WorkflowError("Merged PR lacks merged_at")
        if pr.base_sha != state["frozen_target_head"]:
            raise WorkflowError("Merged PR base SHA differs from frozen target")
        remote_target = inspector.remote_head(
            "origin", str(state["target_branch"])
        )
        if remote_target == state["frozen_target_head"]:
            raise WorkflowError(
                "Remote target has not advanced after the independently verified merge"
            )
        state["github_merge_commit_sha"] = pr.merge_commit_sha
        state["post_merge_remote_head"] = remote_target
        state["merge_commit_sha"] = None
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
                "git.inspect verifies refreshed origin/main equals live remote main",
                "git.inspect finds one exact merge commit whose first parent is the frozen target and second parent is the frozen source",
                "git.inspect permits only descendant post-merge automation commits after that exact merge",
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
        local_target = inspector.head(f"origin/{state['target_branch']}")
        remote_target = inspector.remote_head("origin", str(state["target_branch"]))
        if local_target != remote_target:
            raise WorkflowError(
                "Post-merge local/remote target authority mismatch: "
                f"local={local_target}, remote={remote_target}"
            )
        frozen_target = str(state["frozen_target_head"])
        source_head = str(state["source_head"])
        if not inspector.is_ancestor(frozen_target, local_target):
            raise WorkflowError(
                "Frozen target is not contained in refreshed origin/main"
            )
        if not inspector.is_ancestor(source_head, local_target):
            raise WorkflowError(
                "Frozen source head is not contained in refreshed origin/main"
            )
        merge_commit = inspector.find_merge_commit(
            base_parent=frozen_target,
            merged_parent=source_head,
            descendant=local_target,
        )
        github_merge_commit = state.get("github_merge_commit_sha")
        if github_merge_commit is not None and github_merge_commit != merge_commit:
            raise WorkflowError(
                "GitHub merge commit differs from exact Git topology proof: "
                f"github={github_merge_commit}, git={merge_commit}"
            )
        if not inspector.is_ancestor(merge_commit, local_target):
            raise WorkflowError(
                "Verified merge commit is not contained in refreshed origin/main"
            )
        state["merge_commit_sha"] = merge_commit
        state["current_boundary"] = "complete"
        state["current_proposal"] = None
        verification = {
            "status": "pass",
            "boundary": "post-merge-fetch",
            "source_head": state["source_head"],
            "origin_main": local_target,
            "remote_main": remote_target,
            "source_contained_in_main": True,
            "frozen_target_contained_in_main": True,
            "merge_commit_sha": merge_commit,
            "post_merge_descendants_permitted": local_target != merge_commit,
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
    create_url = github_compare_url(
        {"owner": "example", "name": "repo"},
        base_branch="main",
        head_branch="staged/x",
        title="x",
        body="body x",
    )
    create = OperatorGitProposal.build_browser(
        proposal_id="SAGE-GIT-20260811-101",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="pull-request-create",
        change_scope=("README.md",),
        validation=validation,
        browser_action="create-pull-request",
        browser_url=create_url,
        expected_result="x",
        risk="x",
        rollback="x",
        post_interaction_verification=("x",),
        created_at="2026-08-11T18:00:00-05:00",
    )
    merge = OperatorGitProposal.build_browser(
        proposal_id="SAGE-GIT-20260811-102",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="pull-request-merge",
        change_scope=("README.md",),
        validation=validation,
        browser_action="merge-pull-request",
        browser_url=github_pull_url(
            {"owner": "example", "name": "repo"},
            pull_request_number=42,
        ),
        expected_result="x",
        risk="x",
        rollback="x",
        post_interaction_verification=("x",),
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
    reconcile = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260811-104",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="other-git-mutation",
        change_scope=("docs/sitemap.xml", "refs/heads/staged/x"),
        validation=validation,
        command_argv=("git", "merge", "--no-edit", "--no-ff", "0" * 40),
        expected_result="x",
        risk="x",
        rollback="x",
        post_command_verification=("x",),
        created_at="2026-08-11T18:00:03-05:00",
    )
    reconcile_push = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260811-105",
        controller="self-test",
        repository=snapshot,
        authority_receipt="fixture:a",
        component_manifest="fixture:c",
        boundary="push",
        change_scope=("refs/heads/staged/x",),
        validation=validation,
        command_argv=("git", "push", "origin", "staged/x"),
        expected_result="x",
        risk="x",
        rollback="x",
        post_command_verification=("x",),
        created_at="2026-08-11T18:00:04-05:00",
    )
    assert create["browser"]["opened_by_helper"] is False
    assert merge["browser"]["mutation_performed_by_helper"] is False
    assert refresh["command"]["executed_by_helper"] is False
    assert reconcile["command"]["executed_by_helper"] is False
    assert reconcile_push["command"]["executed_by_helper"] is False
    assert reconcile["command"]["argv"][:4] == ["git", "merge", "--no-edit", "--no-ff"]
    assert reconcile_push["command"]["argv"] == ["git", "push", "origin", "staged/x"]
    assert "quick_pull=1" in create["browser"]["url"]
    assert create["operator_contract"]["execution_mode"] == "browser-review"
    assert merge["operator_contract"]["pasted_output_required"] is False
    print("PASS PR-create and PR-merge use browser-backed operator approval")
    print("PASS pre-promotion source reconciliation uses explicit merge and push proposals")
    print("PASS post-merge Git graph refresh remains an explicit operator boundary")
    print("PASS workflow has no autonomous Git or GitHub mutation")
    print("Kalaxy3 checkpoint promotion workflow self-test: PASS")
    return 0
