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
    AtomicFileTransaction,
    AtomicFileWriter,
    CloseoutWriter,
    CommandRunner,
    CommandSpec,
    GitInspector,
    GitRepository,
    GitSafetyGuardrail,
    ImprovementActionClient,
    JsonlEventLogger,
    MakefileDocument,
    OperatorGitProposal,
    PrimitiveCatalog,
    SageDiscovery,
    Step,
    UsageAnalyzer,
    Workflow,
    WorkflowCommandError,
)


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
                "framework_version": "0.3.0",
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
                        "primitive_id": "file.atomic-preserve-mode",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "operator.git-proposal",
                        "version": "1.0.0",
                        "maturity": "pilot",
                    },
                    {
                        "primitive_id": "git.safety-guardrail",
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
    fixture_command("git", "init", "--bare", str(remote), cwd=root)
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
            "git.inspect": "1.0.0",
            "file.atomic-preserve-mode": "1.0.0",
            "operator.git-proposal": "1.0.0",
            "git.safety-guardrail": "1.0.0",
        },
    )
    runner = CommandRunner(logger, allowed_roots=(root,))
    inspector = GitInspector(work, runner)
    clean = inspector.snapshot()
    if clean.working_tree_status != "clean":
        raise RuntimeError("git.inspect clean snapshot failed")
    inspector.require_upstream_equal()
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
    if proposal["command"]["command_count"] != 1:
        raise RuntimeError("operator proposal command count failed")

    safe = "from workflow import GitInspector\nPRIMITIVES_USED = ('git.inspect',)\n"
    bad = "import subprocess\nsubprocess.run(['git', 'push', 'origin', 'main'])\n"
    if GitSafetyGuardrail.scan_source(safe, path=root / "safe.py"):
        raise RuntimeError("Git safety guardrail rejected safe source")
    violations = GitSafetyGuardrail.scan_source(bad, path=root / "bad.py")
    if not any(item.code == "GIT-MUTATION" for item in violations):
        raise RuntimeError("Git safety guardrail accepted Git mutation")

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


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-workflow-primitives-self-test-"
    ) as raw:
        root = Path(raw)
        test_runner_and_logging(root)
        test_git_and_lifecycle_runtime(root)
        test_least_authority_foundations(root)
        test_discovery_parser()
        test_makefile_runtime(root)
        test_catalog_composition_closeout_usage(root)

    print("PASS command execution, timeout, redaction, and version logging")
    print("PASS temporary-remote Git and canonical action lifecycle adapters")
    print("PASS least-authority Git inspection, atomic files, operator proposals, and safety")
    print("PASS SAGE discovery parsing")
    print("PASS single-line and multiline Makefile composition")
    print("PASS registered workflow composition and atomic closeout")
    print("PASS primitive usage evidence aggregation")
    print("Kalaxy3 SAGE workflow primitives self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
