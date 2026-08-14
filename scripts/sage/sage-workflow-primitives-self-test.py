#!/usr/bin/env python3
"""Runtime-path self-tests for reusable SAGE workflow primitives."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    AuthorityAssertion,
    AuthorityReconciler,
    AtomicFileTransaction,
    AtomicFileWriter,
    CapabilityGapRecorder,
    CloseoutWriter,
    ComponentCandidate,
    ComponentSelector,
    CommandRunner,
    CommandSpec,
    GitInspector,
    GitHubInspector,
    GitRepository,
    GitSafetyGuardrail,
    FailureDiagnoser,
    ImprovementActionClient,
    JsonlEventLogger,
    MakefileDocument,
    OperatorGitProposal,
    OutcomeMetrics,
    PrimitiveCatalog,
    RequiredCapability,
    SageDiscovery,
    Step,
    UsageAnalyzer,
    Workflow,
    WorkflowCommandError,
    WorkflowError,
)

from workflows.routine_git_lifecycle import run_controller  # noqa: E402


def fixture_command(
    *args: str,
    cwd: Path,
) -> None:
    subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def registry_fixture(path: Path) -> PrimitiveCatalog:
    path.write_text(
        json.dumps(
            {
                "framework_version": "0.5.0",
                "primitives": [
                    {
                        "primitive_id": "command.run",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "git.repository",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "git.inspect",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "github.inspect",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "sage.discovery",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "sage.action-lifecycle",
                        "version": "1.1.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "makefile.compose",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "workflow.composition",
                        "version": "1.1.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "evidence.closeout",
                        "version": "1.1.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "usage.summary",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "authority.reconcile",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "component.select",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "capability.gap",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "failure.diagnose",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "file.atomic-preserve-mode",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "operator.git-proposal",
                        "version": "1.1.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "git.safety-guardrail",
                        "version": "1.1.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "metrics.outcome",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                ],
            },
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )
    return PrimitiveCatalog.load(path)


def test_runner_and_logging(root: Path) -> None:
    log = root / "events.jsonl"
    logger = JsonlEventLogger(
        log,
        "self-test",
        primitive_versions={"command.run": "1.0.0"},
    )
    runner = CommandRunner(logger, allowed_roots=(root,))

    success = runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Successful runtime test",
            argv=(sys.executable, "-c", "print('ok')"),
            cwd=root,
        )
    )
    if success.stdout.strip() != "ok":
        raise RuntimeError("command success path failed")

    expected = runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Expected return-code runtime test",
            argv=(sys.executable, "-c", "raise SystemExit(3)"),
            cwd=root,
            expected_codes=(3,),
        )
    )
    if expected.returncode != 3:
        raise RuntimeError("expected-code path failed")

    secret = "super-secret-value"
    runner.run(
        CommandSpec(
            primitive_id="command.run",
            label="Secret redaction runtime test",
            argv=(
                sys.executable,
                "-c",
                f"print('token={secret}')",
            ),
            cwd=root,
            sensitive_values=(secret,),
        )
    )

    try:
        runner.run(
            CommandSpec(
                primitive_id="command.run",
                label="Timeout runtime test",
                argv=(
                    sys.executable,
                    "-c",
                    "import time; time.sleep(2)",
                ),
                cwd=root,
                timeout_seconds=0.05,
            )
        )
    except WorkflowCommandError:
        pass
    else:
        raise RuntimeError("timeout path did not fail closed")

    text = log.read_text(encoding="utf-8")
    if secret in text or "token=" in text:
        raise RuntimeError("structured log retained a secret")
    events = [
        json.loads(line)
        for line in text.splitlines()
        if line
    ]
    required = {
        "timestamp",
        "workflow_id",
        "sequence",
        "event",
        "status",
        "primitive_id",
        "primitive_version",
    }
    if not events or any(
        not required.issubset(event)
        for event in events
    ):
        raise RuntimeError("structured event fields are incomplete")
    if any(
        event["primitive_version"] != "1.0.0"
        for event in events
    ):
        raise RuntimeError("primitive versions were not logged")


def prepare_git_repository(root: Path) -> tuple[Path, Path]:
    remote = root / "remote.git"
    work = root / "work"
    fixture_command(
        "git", "init", "--bare", "--initial-branch=main", str(remote), cwd=root
    )
    fixture_command("git", "clone", str(remote), str(work), cwd=root)
    fixture_command(
        "git",
        "config",
        "user.email",
        "sage-self-test@kalaxy3.local",
        cwd=work,
    )
    fixture_command(
        "git",
        "config",
        "user.name",
        "SAGE Self Test",
        cwd=work,
    )
    return remote, work


def write_fake_action_tools(work: Path) -> None:
    scripts = work / "scripts/sage"
    scripts.mkdir(parents=True)

    (scripts / "sage-action-id.py").write_text(
        """import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--registry")
parser.add_argument("--format")
parser.add_argument("--date")
parser.parse_args()
print("SAGE-ACTION-20260801-002")
""",
        encoding="utf-8",
    )

    (scripts / "sage-improvement-actions.py").write_text(
        """import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--register-file")
parser.add_argument("--action-id")
parser.add_argument("--to-status")
parser.add_argument("--actor")
parser.add_argument("--reason")
parser.add_argument("--evidence-reference", action="append", default=[])
parser.add_argument("--recorded-at")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()

registry = Path("sage-improvement-actions.json")
payload = json.loads(registry.read_text(encoding="utf-8"))
if args.register_file:
    draft = json.loads(
        Path(args.register_file).read_text(encoding="utf-8")
    )
    if args.apply:
        draft["current_status"] = "identified"
        payload["actions"].append(draft)
        registry.write_text(
            json.dumps(payload, indent=4) + "\\n",
            encoding="utf-8",
        )
elif args.action_id and args.to_status:
    matches = [
        item
        for item in payload["actions"]
        if item["action_id"] == args.action_id
    ]
    if len(matches) != 1:
        raise SystemExit(2)
    if args.apply:
        matches[0]["current_status"] = args.to_status
        registry.write_text(
            json.dumps(payload, indent=4) + "\\n",
            encoding="utf-8",
        )
print(json.dumps({"mode": "apply" if args.apply else "dry-run"}))
""",
        encoding="utf-8",
    )


def test_git_and_lifecycle_runtime(root: Path) -> None:
    _, work = prepare_git_repository(root)
    write_fake_action_tools(work)
    (work / "README.md").write_text("baseline\n", encoding="utf-8")
    (work / "sage-improvement-actions.json").write_text(
        json.dumps(
            {
                "actions": [
                    {
                        "action_id": "SAGE-ACTION-20260801-001",
                        "current_status": "validated",
                    }
                ]
            },
            indent=4,
        )
        + "\n",
        encoding="utf-8",
    )
    fixture_command("git", "add", ".", cwd=work)
    fixture_command("git", "commit", "-m", "baseline", cwd=work)
    fixture_command("git", "push", "-u", "origin", "HEAD", cwd=work)

    logger = JsonlEventLogger(
        root / "git-events.jsonl",
        "git-self-test",
        primitive_versions={
            "git.command": "1.0.0",
            "sage.action-lifecycle": "1.1.0",
        },
    )
    runner = CommandRunner(logger, allowed_roots=(root,))
    repository = GitRepository(work, runner)
    branch = repository.branch()
    repository.require_clean()
    repository.require_synced(branch)

    (work / "README.md").write_text(
        "baseline\nupdated\n",
        encoding="utf-8",
    )
    commit = repository.commit_and_push(
        branch=branch,
        exact_paths={"README.md"},
        message="exercise exact-scope primitive",
        apply=True,
    )
    if len(commit) != 40:
        raise RuntimeError("Git primitive returned an invalid commit")

    client = ImprovementActionClient(repository, runner)
    action_id = client.allocate_id(date_token="20260801")
    if action_id != "SAGE-ACTION-20260801-002":
        raise RuntimeError("canonical action allocation adapter failed")

    draft = root / "action.json"
    draft.write_text(
        json.dumps(
            {
                "action_id": action_id,
                "title": "Fixture action",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registered = client.register(
        draft_path=draft,
        actor="self-test",
        reason="Exercise canonical registration adapter.",
        evidence_references=("fixture:registration",),
        apply=True,
    )
    if registered.get("current_status") != "identified":
        raise RuntimeError("action registration adapter failed")
    repository.commit_and_push(
        branch=branch,
        exact_paths={"sage-improvement-actions.json"},
        message="register fixture action",
        apply=True,
    )

    transitioned = client.transition(
        action_id=action_id,
        to_status="accepted",
        actor="self-test",
        reason="Exercise canonical transition adapter.",
        evidence_references=("fixture:transition",),
        apply=True,
    )
    if transitioned.get("current_status") != "accepted":
        raise RuntimeError("action transition adapter failed")
    repository.commit_and_push(
        branch=branch,
        exact_paths={"sage-improvement-actions.json"},
        message="accept fixture action",
        apply=True,
    )
    repository.require_clean()
    repository.require_synced(branch)



def test_routine_git_lifecycle_controller(root: Path) -> None:
    fixture_root = root / "routine-controller"
    fixture_root.mkdir()
    _, work = prepare_git_repository(fixture_root)
    (work / "README.md").write_text("baseline\n", encoding="utf-8")
    (work / "sage-workflow-primitives.json").write_bytes(
        (ROOT / "sage-workflow-primitives.json").read_bytes()
    )
    fixture_command("git", "add", ".", cwd=work)
    fixture_command("git", "commit", "-m", "baseline", cwd=work)
    fixture_command("git", "push", "-u", "origin", "main", cwd=work)
    base_main = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=work,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    fixture_command("git", "switch", "-c", "feature/routine-controller", cwd=work)
    fixture_command(
        "git",
        "push",
        "-u",
        "origin",
        "feature/routine-controller",
        cwd=work,
    )
    (work / "README.md").write_text("baseline\nroutine\n", encoding="utf-8")

    state_dir = fixture_root / "state"
    state_dir.mkdir()
    state_path = state_dir / "request-execution-state.json"
    proposal_path = state_dir / "operator-git-proposal.json"
    validation = [
        {
            "label": "Fixture validation",
            "reference": "fixture",
            "status": "pass",
            "sha256": None,
        }
    ]
    logger = JsonlEventLogger(
        fixture_root / "proposal-events.jsonl",
        "routine-controller-proposal-self-test",
    )
    runner = CommandRunner(logger, allowed_roots=(fixture_root,))
    snapshot = GitInspector(work, runner).snapshot()
    proposal = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260812-901",
        controller="sage-request-execution",
        repository=snapshot,
        authority_receipt=str(state_dir / "authority.json"),
        component_manifest=str(state_dir / "components.json"),
        boundary="routine-git-lifecycle",
        change_scope=("README.md",),
        validation=validation,
        command_argv=(
            "python3",
            "scripts/sage/sage-routine-git-lifecycle.py",
            "--state",
            str(state_path.resolve()),
            "--proposal",
            str(proposal_path.resolve()),
            "--apply",
        ),
        expected_result="Fixture routine lifecycle succeeds.",
        risk="Fixture mutation only.",
        rollback="Discard fixture.",
        post_command_verification=("git status --porcelain=v1",),
    )
    if proposal["schema_version"] != "1.2":
        raise RuntimeError("routine Git lifecycle did not use operator proposal schema 1.2")
    if proposal["operator_contract"].get("pasted_output_required") is not False:
        raise RuntimeError("routine Git lifecycle still requires pasted operator output")
    if proposal["operator_contract"].get("repository_receipt_required") is not True:
        raise RuntimeError("routine Git lifecycle does not require repository-owned receipt")
    proposal_path.write_text(json.dumps(proposal, indent=4) + "\n", encoding="utf-8")
    state = {
        "record_type": "sage-request-execution-state",
        "current_boundary": "routine-git-lifecycle",
        "current_proposal": str(proposal_path.resolve()),
        "repository_branch": "feature/routine-controller",
        "base_head": base_main,
        "base_main_head": base_main,
        "declared_paths": ["README.md"],
        "operator_plan": {
            "commit_message": "exercise routine controller",
            "push_remote": "origin",
        },
        "validation": validation,
        "authority_receipt": str(state_dir / "authority.json"),
        "component_manifest": str(state_dir / "components.json"),
    }
    state_path.write_text(json.dumps(state, indent=4) + "\n", encoding="utf-8")

    try:
        run_controller(work, state_path, proposal_path, apply=False)
    except WorkflowError:
        pass
    else:
        raise RuntimeError("routine Git lifecycle accepted missing operator approval")

    result = run_controller(work, state_path, proposal_path, apply=True)
    commit = str(result["commit"])
    if commit == base_main or len(commit) != 40:
        raise RuntimeError("routine Git lifecycle returned an invalid commit")
    if result["declared_paths"] != ["README.md"]:
        raise RuntimeError("routine Git lifecycle receipt path scope drifted")
    if not Path(str(result["receipt"])).is_file():
        raise RuntimeError("routine Git lifecycle receipt is missing")
    remote = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", "refs/heads/feature/routine-controller"],
        cwd=work,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split("\t", 1)[0]
    if remote != commit:
        raise RuntimeError("routine Git lifecycle did not publish the exact commit")


def test_least_authority_foundations(root: Path) -> None:
    inspect_root = root / "inspect-fixture"
    inspect_root.mkdir()
    _, work = prepare_git_repository(inspect_root)
    (work / "README.md").write_text("baseline\n", encoding="utf-8")
    fixture_command("git", "add", ".", cwd=work)
    fixture_command("git", "commit", "-m", "baseline", cwd=work)
    fixture_command("git", "push", "-u", "origin", "HEAD", cwd=work)

    logger = JsonlEventLogger(
        root / "least-authority-events.jsonl",
        "least-authority-self-test",
        primitive_versions={
            "git.inspect": "1.2.0",
            "file.atomic-preserve-mode": "1.0.0",
            "operator.git-proposal": "1.3.0",
            "git.safety-guardrail": "1.2.0",
        },
    )
    runner = CommandRunner(logger, allowed_roots=(root,))
    inspector = GitInspector(work, runner)
    clean = inspector.snapshot()
    if clean.working_tree_status != "clean":
        raise RuntimeError("git.inspect clean snapshot failed")
    inspector.require_upstream_equal()
    base_head = inspector.head()
    fixture_command("git", "checkout", "-b", "feature/merge-proof", cwd=work)
    (work / "MERGE_PROOF.md").write_text("source\n", encoding="utf-8")
    fixture_command("git", "add", "MERGE_PROOF.md", cwd=work)
    fixture_command("git", "commit", "-m", "merge proof source", cwd=work)
    source_head = inspector.head()
    fixture_command("git", "checkout", "main", cwd=work)
    fixture_command("git", "merge", "--no-ff", "feature/merge-proof", "-m", "merge proof", cwd=work)
    merge_head = inspector.head()
    if inspector.find_merge_commit(
        base_parent=base_head, merged_parent=source_head, descendant=merge_head
    ) != merge_head:
        raise RuntimeError("git.inspect exact merge topology proof failed")
    (work / "POST_MERGE.md").write_text("automation descendant\n", encoding="utf-8")
    fixture_command("git", "add", "POST_MERGE.md", cwd=work)
    fixture_command("git", "commit", "-m", "post merge automation", cwd=work)
    descendant_head = inspector.head()
    if inspector.find_merge_commit(
        base_parent=base_head, merged_parent=source_head, descendant=descendant_head
    ) != merge_head:
        raise RuntimeError("git.inspect lost merge proof beneath post-merge descendant")
    try:
        inspector.find_merge_commit(
            base_parent=source_head, merged_parent=base_head, descendant=descendant_head
        )
    except Exception:
        pass
    else:
        raise RuntimeError("git.inspect accepted reversed merge parents")
    try:
        inspector.run_read_only(("add", "README.md"))
    except Exception:
        pass
    else:
        raise RuntimeError("git.inspect accepted a mutating subcommand")

    (work / "README.md").write_text("baseline\nchanged\n", encoding="utf-8")
    if inspector.changed_paths() != {"README.md"}:
        raise RuntimeError("git.inspect changed-path scope failed")

    files_root = root / "files"
    files_root.mkdir()
    executable = files_root / "tool.py"
    executable.write_text("print('old')\n", encoding="utf-8")
    executable.chmod(0o755)
    writer = AtomicFileWriter((files_root,))
    writer.write_text(executable, "print('new')\n")
    if executable.stat().st_mode & 0o777 != 0o755:
        raise RuntimeError("atomic writer did not preserve executable mode")
    rollback = files_root / "rollback.txt"
    rollback.write_text("before\n", encoding="utf-8")
    try:
        with AtomicFileTransaction(writer, (rollback,)) as transaction:
            transaction.write_text(rollback, "after\n")
            raise RuntimeError("force rollback")
    except RuntimeError as error:
        if str(error) != "force rollback":
            raise
    if rollback.read_text(encoding="utf-8") != "before\n":
        raise RuntimeError("atomic transaction rollback failed")

    proposal = OperatorGitProposal.build(
        proposal_id="SAGE-GIT-20260801-001",
        controller="self-test",
        repository=clean,
        authority_receipt="fixture:authority",
        component_manifest="fixture:manifest",
        boundary="stage",
        change_scope=("README.md",),
        validation=({
            "label": "fixture validation",
            "status": "pass",
            "reference": "fixture:validation",
            "sha256": None,
        },),
        command_argv=("git", "add", "--", "README.md"),
        expected_result="README.md is staged.",
        risk="Only the declared fixture path is staged.",
        rollback="Run git restore --staged -- README.md.",
        post_command_verification=("git diff --cached --name-only",),
        created_at="2026-08-01T21:55:00-05:00",
    )
    if proposal["command"]["executed_by_helper"] is not False:
        raise RuntimeError("operator proposal execution contract failed")
    if proposal["schema_version"] != "1.0" or proposal["operator_contract"].get("pasted_output_required") is not True:
        raise RuntimeError("legacy/manual command proposal pasted-output compatibility changed")
    if proposal["command"]["command_count"] != 1:
        raise RuntimeError("operator proposal command count failed")

    browser = OperatorGitProposal.build_browser(
        proposal_id="SAGE-GIT-20260801-002",
        controller="self-test",
        repository=clean,
        authority_receipt="fixture:authority",
        component_manifest="fixture:manifest",
        boundary="pull-request-create",
        change_scope=("README.md",),
        validation=({
            "label": "fixture validation",
            "status": "pass",
            "reference": "fixture:validation",
            "sha256": None,
        },),
        browser_action="create-pull-request",
        browser_url=(
            "https://github.com/example/repo/compare/main...staged%2Fx"
            "?quick_pull=1&title=Fixture&body=Fixture"
        ),
        expected_result="Review and create the prepared PR.",
        risk="Fixture GitHub review state.",
        rollback="Close the PR.",
        post_interaction_verification=("github.inspect",),
        created_at="2026-08-01T21:55:01-05:00",
    )
    if browser["schema_version"] != "1.1":
        raise RuntimeError("browser proposal schema version failed")
    if browser["operator_contract"]["execution_mode"] != "browser-review":
        raise RuntimeError("browser proposal execution mode failed")
    if browser["browser"]["provider"] != "github-browser":
        raise RuntimeError("browser proposal provider contract failed")
    if browser["browser"]["opened_by_helper"] is not False:
        raise RuntimeError("browser proposal open contract failed")
    if browser["browser"]["mutation_performed_by_helper"] is not False:
        raise RuntimeError("browser proposal mutation contract failed")
    if "command" in browser:
        raise RuntimeError("browser proposal unexpectedly contains a command")
    try:
        OperatorGitProposal.build(
            proposal_id="SAGE-GIT-20260801-003",
            controller="self-test",
            repository=clean,
            authority_receipt="fixture:authority",
            component_manifest="fixture:manifest",
            boundary="pull-request-create",
            change_scope=("README.md",),
            validation=({
                "label": "fixture validation",
                "status": "pass",
                "reference": "fixture:validation",
                "sha256": None,
            },),
            command_argv=("gh", "pr", "create"),
            expected_result="x",
            risk="x",
            rollback="x",
            post_command_verification=("x",),
            created_at="2026-08-01T21:55:02-05:00",
        )
    except WorkflowError:
        pass
    else:
        raise RuntimeError("operator proposal accepted GitHub CLI PR mutation")
    try:
        OperatorGitProposal.build_browser(
            proposal_id="SAGE-GIT-20260801-004",
            controller="self-test",
            repository=clean,
            authority_receipt="fixture:authority",
            component_manifest="fixture:manifest",
            boundary="pull-request-merge",
            change_scope=("README.md",),
            validation=({
                "label": "fixture validation",
                "status": "pass",
                "reference": "fixture:validation",
                "sha256": None,
            },),
            browser_action="merge-pull-request",
            browser_url="https://example.com/not-github",
            expected_result="x",
            risk="x",
            rollback="x",
            post_interaction_verification=("x",),
            created_at="2026-08-01T21:55:03-05:00",
        )
    except WorkflowError:
        pass
    else:
        raise RuntimeError("operator proposal accepted non-GitHub browser target")

    safe = "from workflow import GitInspector\nPRIMITIVES_USED = ('git.inspect',)\n"
    bad = "import subprocess\nsubprocess.run(['git', 'push', 'origin', 'main'])\n"
    if GitSafetyGuardrail.scan_source(safe, path=root / "safe.py"):
        raise RuntimeError("Git safety guardrail rejected safe source")
    violations = GitSafetyGuardrail.scan_source(bad, path=root / "bad.py")
    if not any(item.code == "GIT-MUTATION" for item in violations):
        raise RuntimeError("Git safety guardrail accepted Git mutation")


def test_github_inspection(root: Path) -> None:
    sha_head = "a" * 40
    sha_base = "b" * 40
    merge_sha = "c" * 40

    def payload(
        *, number: int, merged: bool, merge_commit_sha: str | None = merge_sha
    ) -> dict[str, object]:
        return {
            "number": number,
            "state": "closed" if merged else "open",
            "draft": False,
            "base": {"ref": "main", "sha": sha_base, "repo": {"full_name": "donb4iu/Kalaxy3"}},
            "head": {"ref": "feature/example", "sha": sha_head, "repo": {"full_name": "donb4iu/Kalaxy3"}},
            "merged": merged,
            "merged_at": "2026-08-11T20:00:00Z" if merged else None,
            "merge_commit_sha": merge_commit_sha,
            "mergeable": True,
            "mergeable_state": "clean",
        }

    class FixtureGitHubInspector(GitHubInspector):
        def __init__(self) -> None:
            super().__init__("donb4iu", "Kalaxy3")
            self.details = {17: payload(number=17, merged=False)}
            self.list_items = [{"number": 17, "base": {"ref": "main"}, "head": {"ref": "feature/example", "sha": sha_head}}]

        def _request_json(self, path: str, query=None):
            if path.endswith("/pulls"):
                return list(self.list_items)
            return dict(self.details[int(path.rsplit("/", 1)[1])])

    inspector = FixtureGitHubInspector()
    observed = inspector.find_pull_request(base_branch="main", head_branch="feature/example", head_sha=sha_head)
    if observed.number != 17 or observed.merged is not False:
        raise RuntimeError("github.inspect pre-merge lookup failed")
    inspector.require_pull_request(17, base_branch="main", head_branch="feature/example", head_sha=sha_head, merged=False, require_mergeable=True)
    inspector.details[17] = payload(number=17, merged=True)
    merged = inspector.require_pull_request(17, base_branch="main", head_branch="feature/example", head_sha=sha_head, merged=True)
    if merged.merged_at is None or merged.merge_commit_sha != merge_sha:
        raise RuntimeError("github.inspect post-merge verification failed")
    inspector.details[17] = payload(number=17, merged=True, merge_commit_sha=None)
    merged_without_sha = inspector.require_pull_request(
        17,
        base_branch="main",
        head_branch="feature/example",
        head_sha=sha_head,
        merged=True,
    )
    if merged_without_sha.merged_at is None or merged_without_sha.merge_commit_sha is not None:
        raise RuntimeError("github.inspect rejected or altered nullable merged commit SHA")
    try:
        inspector.require_pull_request(17, base_branch="main", head_branch="feature/example", head_sha="d" * 40)
    except Exception:
        pass
    else:
        raise RuntimeError("github.inspect accepted mismatched head SHA")
    inspector.list_items.append({"number": 18, "base": {"ref": "main"}, "head": {"ref": "feature/example", "sha": sha_head}})
    try:
        inspector.find_pull_request(base_branch="main", head_branch="feature/example", head_sha=sha_head)
    except Exception:
        pass
    else:
        raise RuntimeError("github.inspect accepted ambiguous PR identity")

    for relative in (
        "scripts/sage/workflow/proposal.py",
        "scripts/sage/workflows/checkpoint_promotion.py",
    ):
        production_source = (ROOT / relative).read_text(encoding="utf-8")
        production_violations = GitSafetyGuardrail.scan_source(
            production_source,
            path=ROOT / relative,
        )
        if any(item.code == "GITHUB-DIRECT-API" for item in production_violations):
            raise RuntimeError(
                f"browser proposal path incorrectly acquires direct GitHub API capability: {relative}"
            )

    direct_api = "from urllib.request import urlopen\n" + "urlopen('https://api." + "github.com/repos/example/repo/pulls')\n"
    violations = GitSafetyGuardrail.scan_source(direct_api, path=root / "direct-github-api.py")
    if not any(item.code == "GITHUB-DIRECT-API" for item in violations):
        raise RuntimeError("Git safety guardrail accepted direct GitHub API use")
    trusted = GitSafetyGuardrail.scan_source(direct_api, path=root / "scripts/sage/workflow/github_inspect.py")
    if any(item.code == "GITHUB-DIRECT-API" for item in trusted):
        raise RuntimeError("Git safety guardrail rejected trusted github.inspect transport")


def test_discovery_parser() -> None:
    fixture = """
Kalaxy3 SAGE change discovery: PASS
Inferred SAGE contexts:
  - repository-governance
  - workflow-primitives

[workflow-primitives]
  Authoritative files:
  - sage-workflow-primitives.json
  - scripts/sage/workflow/runner.py

Implementation policy:
"""
    result = SageDiscovery.parse("fixture", fixture)
    if result.contexts != (
        "repository-governance",
        "workflow-primitives",
    ):
        raise RuntimeError("discovery context parser failed")
    if result.authorities != (
        "sage-workflow-primitives.json",
        "scripts/sage/workflow/runner.py",
    ):
        raise RuntimeError("discovery authority parser failed")


def test_makefile_runtime(root: Path) -> None:
    source = """PYTHON ?= python3

sage-self-test: alpha
	@echo self

sage-guardrails: sage-self-test \
                 alpha beta \
                 gamma
	@echo guardrails

alpha:
	@echo alpha

beta:
	@echo beta

gamma:
	@echo gamma
"""
    document = MakefileDocument.parse(source)
    document.add_dependency(
        "sage-self-test",
        "sage-workflow-self-test",
    )
    document.add_dependency(
        "sage-guardrails",
        "sage-workflow-guardrail",
    )
    document.append_block(
        """sage-workflow-self-test:
	@echo workflow-self-test

sage-workflow-guardrail:
	@echo workflow-guardrail
"""
    )
    rendered = document.render()
    if "sage-workflow-self-test" not in document.dependencies(
        "sage-self-test"
    ):
        raise RuntimeError("single-line Make dependency composition failed")
    if "sage-workflow-guardrail" not in document.dependencies(
        "sage-guardrails"
    ):
        raise RuntimeError("multiline Make dependency composition failed")

    makefile = root / "Makefile"
    makefile.write_text(rendered, encoding="utf-8")
    for target in (
        "sage-workflow-self-test",
        "sage-self-test",
        "sage-guardrails",
    ):
        fixture_command(
            "make",
            "--no-print-directory",
            "-f",
            str(makefile),
            "-n",
            target,
            cwd=root,
        )


def test_catalog_composition_closeout_usage(root: Path) -> None:
    registry = root / "registry.json"
    catalog = registry_fixture(registry)
    identifiers = (
        "workflow.composition",
        "makefile.compose",
        "evidence.closeout",
        "usage.summary",
    )
    versions = catalog.versions_for(identifiers)
    log = root / "composition-events.jsonl"
    logger = JsonlEventLogger(
        log,
        "composition-self-test",
        primitive_versions=versions,
    )
    observed: list[str] = []
    workflow = Workflow(
        workflow_id="composition-self-test",
        logger=logger,
        catalog=catalog,
        steps=(
            Step(
                "first",
                "makefile.compose",
                lambda: observed.append("first"),
            ),
            Step(
                "second",
                "makefile.compose",
                lambda: observed.append("second"),
            ),
        ),
    )
    workflow.run()
    if observed != ["first", "second"]:
        raise RuntimeError("workflow step ordering failed")

    closeout = CloseoutWriter(
        destination_directory=root / "closeout",
        primitive_registry=registry,
        event_log=log,
    ).write(
        workflow_id="composition-self-test",
        status="pass",
        used_primitives=identifiers,
        details={"runtime_path": "exercised"},
    )
    payload = json.loads(closeout.read_text(encoding="utf-8"))
    if payload["primitive_versions"] != versions:
        raise RuntimeError("closeout primitive provenance failed")

    summary = UsageAnalyzer.summarize((log,))
    if summary["workflow_count"] != 1:
        raise RuntimeError("usage workflow count failed")
    if not summary["successful_events_by_primitive_version"]:
        raise RuntimeError("usage primitive summary is empty")



def test_decision_and_diagnosis_primitives() -> None:
    repository = {"path": ".", "branch": "main", "head": "a" * 40, "upstream_head": "a" * 40, "working_tree_clean": True}
    assertions = (
        AuthorityAssertion("AUTH-001", "git", "repository", "HEAD", "2026-08-01T22:00:00-05:00", "current", "git.head", "a" * 40, "measured", "high", "material", None),
        AuthorityAssertion("AUTH-002", "repository-policy", "repository", "policy", "2026-08-01T22:00:00-05:00", "current", "policy.state", "staged", "declared", "high", "material", None),
    )
    receipt = AuthorityReconciler(("git", "repository-policy")).reconcile(receipt_id="SAGE-AUTH-20260801-997", request="fixture", repository=repository, assertions=assertions, evidence_references=("fixture",), captured_at="2026-08-01T22:00:00-05:00")
    if receipt.mutation_gate["status"] != "review-ready":
        raise RuntimeError("complete authority was not review-ready")
    conflict = AuthorityReconciler(("git",)).reconcile(receipt_id="SAGE-AUTH-20260801-996", request="fixture", repository=repository, assertions=(assertions[0], AuthorityAssertion("AUTH-003", "git", "repository", "other", "2026-08-01T22:00:00-05:00", "current", "git.head", "b" * 40, "measured", "high", "material", None)), evidence_references=("fixture",), captured_at="2026-08-01T22:00:00-05:00")
    if conflict.mutation_gate["status"] != "blocked":
        raise RuntimeError("material authority conflict did not block mutation")

    selector = ComponentSelector()
    capability = RequiredCapability("CAP-997", "fixture")
    selected = ComponentCandidate("CANDIDATE-997", ("CAP-997",), "good", "1.0.0", "good.py", "pilot", {"applicability":"direct","authority_compatibility":"compatible","mutation_scope_fit":"least-authority","published_interface_verified":True,"successful_production_executions":None,"failed_production_executions":None,"open_recurrence":"no","runtime_test_coverage":"positive-and-negative"}, ("fixture",), "least authority")
    rejected = ComponentCandidate("CANDIDATE-996", ("CAP-997",), "bad", "1.0.0", "bad.py", "pilot", {"applicability":"partial","authority_compatibility":"compatible","mutation_scope_fit":"broader-than-required","published_interface_verified":True,"successful_production_executions":10,"failed_production_executions":0,"open_recurrence":"no","runtime_test_coverage":"positive-and-negative"}, ("fixture",), "broader")
    manifest = selector.build_manifest(manifest_id="SAGE-COMP-20260801-997", request="fixture", authority_receipt="fixture", capabilities=(capability,), candidates=(rejected, selected), approval={"status":"approved","reviewed_by":"operator","reviewed_at":"2026-08-01T22:00:00-05:00","rationale":"fixture"}, created_at="2026-08-01T22:00:00-05:00")
    selector.require_complete(manifest)
    if manifest["selections"][0]["component_id"] != "good" or manifest["candidates"][0]["disposition"] != "rejected":
        raise RuntimeError("component selection or rejected-alternative retention failed")

    gap = CapabilityGapRecorder.create(gap_id="SAGE-GAP-20260801-997", request="fixture", authority_receipt="fixture", component_manifest="fixture", required_capability="fixture", candidates_considered=({"component_id":"old","version":"1.0.0","source_path":"old.py","insufficiency":"missing","composition_can_close_gap":False},), missing_interface_or_behavior="missing", why_configuration_is_insufficient="cannot configure", why_composition_is_insufficient="cannot compose", proposed_primitive={"primitive_id":"new.fixture","responsibility":"fixture","side_effects":"none","idempotency":"deterministic","logging":"caller","failure_mode":"closed","runtime_tests":["positive","negative"],"initial_maturity":"pilot"}, approval={"status":"approved","reviewed_by":"operator","reviewed_at":"2026-08-01T22:00:00-05:00","rationale":"fixture"}, evidence_references=("fixture",), created_at="2026-08-01T22:00:00-05:00")
    CapabilityGapRecorder.assert_implementation_allowed(gap)

    diagnosis = FailureDiagnoser.diagnose(diagnosis_id="SAGE-DIAG-20260801-997", failure_id="FAIL-997", attempted_action="fixture", what_failed="fixture", direct_evidence=({"source":"fixture","captured_at":"2026-08-01T22:00:00-05:00","observation":"failed","artifact":"fixture","sha256":None},), actual_path={"component_id":"bad","component_version":"1.0.0","source_path":"bad.py","description":"bad"}, expected_path={"component_id":"good","component_version":"1.0.0","source_path":"good.py","description":"good"}, why_actual_path_differed="selection bypass", ownership="composition", mutation_effect={"mutation_opportunity":True,"mutation_performed":False,"detected_pre_mutation":True,"mutation_scope":"none"}, lesson_use={"retrieval_performed":True,"applicable_lesson_ids":[],"surfaced_lesson_ids":[],"used_lesson_ids":[],"nonuse_reason":None}, previous_failure_references=(), avoidable_rework_minutes=None, correction={"disposition":"update-composition","reusable_correction":"use selected component","target_control_type":"guardrail","primitive_version_bump_required":False,"regression_test_required":True,"action_reference":None,"no_action_rationale":None}, evidence_references=("fixture",), recorded_at="2026-08-01T22:00:00-05:00")
    if diagnosis["divergence"]["selection_failure"] is not True:
        raise RuntimeError("failure diagnosis did not record path divergence")


def test_outcome_metrics() -> None:
    from workflow.metrics import RAW_FIELDS
    raw = {field: None for field in RAW_FIELDS}
    raw.update({"workflows_completed":4,"first_pass_completions":3,"semantic_validations":2,"semantic_false_passes":0,"commands_executed":8,"manual_corrections":2,"operator_interventions":1,"authority_checks":4,"authority_failures":0,"components_selected":4,"components_reused":3,"known_failures_encountered":2,"known_failures_recurred":1,"mutation_opportunities":2,"failures_detected_pre_mutation":2})
    report = OutcomeMetrics.build_report(report_id="SAGE-METRICS-20260801-997", captured_at="2026-08-01T22:40:00-05:00", period={"started_at":"2026-08-01T22:00:00-05:00","completed_at":"2026-08-01T22:40:00-05:00"}, workflow_class="fixture", raw_metrics=raw, provenance=({"source_type":"runtime","reference":"fixture","measurement_type":"measured","captured_at":"2026-08-01T22:40:00-05:00"},), limitations=("fixture",))
    if report["derived_metrics"]["first_pass_completion_rate"] != 0.75 or report["derived_metrics"]["component_reuse_ratio"] != 0.75:
        raise RuntimeError("outcome metric derivation failed")
    baseline = {**report, "report_id":"SAGE-METRICS-20260801-996", "derived_metrics":{**report["derived_metrics"], "first_pass_completion_rate":0.5}}
    if OutcomeMetrics.trend(metric="first_pass_completion_rate", current_report=report, baseline_report=baseline, direction="higher-is-better", comparability_basis="same fixture class")["result"] != "improved":
        raise RuntimeError("outcome trend comparison failed")
    try:
        OutcomeMetrics.derive({**raw,"first_pass_completions":5})
    except ValueError:
        pass
    else:
        raise RuntimeError("invalid outcome subset was accepted")
    try:
        OutcomeMetrics.trend(metric="first_pass_completion_rate", current_report=report, baseline_report={**baseline,"workflow_class":"other"}, direction="higher-is-better", comparability_basis="invalid")
    except ValueError:
        pass
    else:
        raise RuntimeError("incomparable outcome trend was accepted")

def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-workflow-primitives-self-test-"
    ) as raw:
        root = Path(raw)
        test_runner_and_logging(root)
        test_git_and_lifecycle_runtime(root)
        test_routine_git_lifecycle_controller(root)
        test_least_authority_foundations(root)
        test_github_inspection(root)
        test_decision_and_diagnosis_primitives()
        test_outcome_metrics()
        test_discovery_parser()
        test_makefile_runtime(root)
        test_catalog_composition_closeout_usage(root)

    print("PASS command execution, timeout, redaction, and version logging")
    print("PASS temporary-remote Git and canonical action lifecycle adapters")
    print("PASS operator-approved bounded routine Git lifecycle controller")
    print("PASS least-authority Git and GitHub inspection, atomic files, operator proposals, and safety")
    print("PASS authority reconciliation, component selection, capability gaps, and failure diagnosis")
    print("PASS semantic outcome metrics, null preservation, and comparable trends")
    print("PASS SAGE discovery parsing")
    print("PASS single-line and multiline Makefile composition")
    print("PASS registered workflow composition and atomic closeout")
    print("PASS primitive usage evidence aggregation")
    print("Kalaxy3 SAGE workflow primitives self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
