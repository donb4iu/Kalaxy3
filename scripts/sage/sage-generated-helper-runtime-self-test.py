#!/usr/bin/env python3
"""Exact-CLI positive and negative tests for generated-helper delivery."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    CommandRunner,
    CommandSpec,
    JsonlEventLogger,
    WorkflowCommandError,
)


@dataclass(frozen=True)
class CaseResult:
    """Observed outcome for one exact-CLI fixture."""

    returncode: int
    receipt: Path
    stdout: str
    stderr: str


def file_sha256(path: Path) -> str:
    """Return the SHA-256 digest of one file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_runtime(root: Path, status: str) -> Path:
    """Build a disposable exact production-CLI repository fixture."""

    target = root / "repository"
    (target / "scripts/sage/workflows").mkdir(parents=True)
    shutil.copytree(SAGE_DIR / "workflow", target / "scripts/sage/workflow")
    shutil.copy2(
        SAGE_DIR / "workflows/generated_helper_delivery.py",
        target / "scripts/sage/workflows/generated_helper_delivery.py",
    )
    shutil.copy2(
        SAGE_DIR / "sage-python-static-guardrail.py",
        target / "scripts/sage/sage-python-static-guardrail.py",
    )
    shutil.copy2(ROOT / "sage-workflow-primitives.json", target)
    payload = json.loads((ROOT / "sage-improvement-actions.json").read_text())
    action = next(
        item for item in payload["actions"]
        if item.get("action_id") == "SAGE-ACTION-20260730-001"
    )
    action["current_status"] = status
    (target / "sage-improvement-actions.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def positive_helper() -> str:
    """Return a helper with distinct self-test and operator paths."""

    return '''#!/usr/bin/env python3
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.self_test:
        print("helper-self-test=pass")
        return 0
    if args.package is None or args.package.read_text() != "package-ok\\n":
        return 7
    print("helper-operator-path=pass")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''


def manifest_payload(
    helper: Path,
    fixture: Path,
    companion: Path,
) -> dict[str, object]:
    """Build one valid delivery manifest."""

    return {
        "schema_version": "1.0",
        "helper_sha256": file_sha256(helper),
        "runtime_fixture": str(fixture),
        "companion_artifacts": [
            {"path": str(companion), "sha256": file_sha256(companion)}
        ],
        "self_test_argv": ["{python}", "{helper}", "--self-test"],
        "operator_argv": [
            "{python}", "{helper}", "--package", str(companion)
        ],
    }


def build_case(root: Path, helper_source: str) -> tuple[Path, Path, Path, Path]:
    """Create helper, manifest, fixture, and companion artifacts."""

    artifacts = root / "artifacts"
    fixture = root / "fixture"
    artifacts.mkdir(parents=True)
    fixture.mkdir(parents=True)
    (fixture / ".sage-generated-helper-fixture.json").write_text(
        '{"disposable": true}\n', encoding="utf-8"
    )
    helper = artifacts / "helper.py"
    helper.write_text(helper_source, encoding="utf-8")
    helper.chmod(0o755)
    companion = artifacts / "package.zip"
    companion.write_text("package-ok\n", encoding="utf-8")
    manifest = artifacts / "delivery.json"
    manifest.write_text(
        json.dumps(manifest_payload(helper, fixture, companion), indent=2) + "\n",
        encoding="utf-8",
    )
    return helper, manifest, companion, fixture


def exact_cli(
    repository: Path,
    helper: Path,
    manifest: Path,
    receipt: Path,
    expected_codes: tuple[int, ...],
) -> CaseResult:
    """Run the copied production CLI through the repository command primitive."""

    log = receipt.parent / "self-test-runner.events.jsonl"
    logger = JsonlEventLogger(log, "sage.generated-helper.self-test")
    runner = CommandRunner(logger, allowed_roots=(repository, receipt.parent))
    spec = CommandSpec(
        primitive_id="command.run",
        label="Exercise exact generated-helper delivery CLI",
        argv=(
            sys.executable,
            "scripts/sage/workflows/generated_helper_delivery.py",
            "--helper", str(helper),
            "--manifest", str(manifest),
            "--receipt", str(receipt),
        ),
        cwd=repository,
        expected_codes=expected_codes,
    )
    result = runner.run(spec)
    return CaseResult(result.returncode, receipt, result.stdout, result.stderr)


def run_failure_case(
    name: str,
    mutate: Callable[[Path, Path, Path, Path], None],
) -> None:
    """Require one exact-CLI failure to leave no receipt."""

    with tempfile.TemporaryDirectory(prefix=f"sage-helper-{name}-") as raw:
        root = Path(raw)
        repository = copy_runtime(root, "validated")
        helper, manifest, companion, fixture = build_case(
            root, positive_helper()
        )
        mutate(helper, manifest, companion, fixture)
        receipt = root / "receipt.json"
        result = exact_cli(repository, helper, manifest, receipt, (2,))
        if result.returncode != 2 or receipt.exists():
            raise RuntimeError(f"{name}: failure did not fail closed")


def mutate_digest(helper: Path, manifest: Path, *_: Path) -> None:
    """Break the helper digest after manifest creation."""

    helper.write_text(helper.read_text() + "\n# changed\n", encoding="utf-8")


def mutate_missing_companion(_: Path, __: Path, companion: Path, ___: Path) -> None:
    """Remove the declared companion artifact."""

    companion.unlink()


def mutate_companion_digest(_: Path, manifest: Path, companion: Path, __: Path) -> None:
    """Change a companion without refreshing its declared digest."""

    companion.write_text("changed\n", encoding="utf-8")


def mutate_omitted_companion(_: Path, manifest: Path, __: Path, ___: Path) -> None:
    """Omit the required companion from the operator path."""

    payload = json.loads(manifest.read_text())
    payload["operator_argv"] = ["{python}", "{helper}"]
    manifest.write_text(json.dumps(payload, indent=2) + "\n")


def mutate_unimported_hashlib(helper: Path, manifest: Path, *_: Path) -> None:
    """Inject the original missing-import recurrence."""

    helper.write_text("def main():\n    return hashlib.sha256(b'x').hexdigest()\n")
    refresh_helper_digest(helper, manifest)


def mutate_undefined_authority(helper: Path, manifest: Path, *_: Path) -> None:
    """Inject the unresolved AUTHORITY_DIGESTS recurrence."""

    helper.write_text("def main():\n    return AUTHORITY_DIGESTS['x']\n")
    refresh_helper_digest(helper, manifest)


def mutate_invalid_late_path(helper: Path, manifest: Path, *_: Path) -> None:
    """Create a defined name that fails only on the operator path."""

    helper.write_text('''#!/usr/bin/env python3
import argparse
AUTHORITY_DIGESTS = None
parser = argparse.ArgumentParser()
parser.add_argument("--self-test", action="store_true")
parser.add_argument("--package")
args = parser.parse_args()
if args.self_test:
    raise SystemExit(0)
print(AUTHORITY_DIGESTS["missing"])
''')
    refresh_helper_digest(helper, manifest)


def mutate_unsafe_helper(helper: Path, manifest: Path, *_: Path) -> None:
    """Inject prohibited Git mutation machinery."""

    helper.write_text(
        "import subprocess\nsubprocess.run(['git','push','origin','main'])\n"
    )
    refresh_helper_digest(helper, manifest)


def refresh_helper_digest(helper: Path, manifest: Path) -> None:
    """Refresh only the helper digest after a source mutation."""

    payload = json.loads(manifest.read_text())
    payload["helper_sha256"] = file_sha256(helper)
    manifest.write_text(json.dumps(payload, indent=2) + "\n")


def accepted_gate_test() -> None:
    """Require the staged accepted action to block real delivery."""

    with tempfile.TemporaryDirectory(prefix="sage-helper-accepted-") as raw:
        root = Path(raw)
        repository = copy_runtime(root, "accepted")
        helper, manifest, _, _ = build_case(root, positive_helper())
        receipt = root / "receipt.json"
        result = exact_cli(repository, helper, manifest, receipt, (2,))
        if result.returncode != 2 or receipt.exists():
            raise RuntimeError("accepted action did not block real delivery")


def positive_test() -> None:
    """Require the exact validated-state CLI and receipt semantics to pass."""

    with tempfile.TemporaryDirectory(prefix="sage-helper-positive-") as raw:
        root = Path(raw)
        repository = copy_runtime(root, "validated")
        helper, manifest, companion, _ = build_case(root, positive_helper())
        receipt = root / "receipt.json"
        result = exact_cli(repository, helper, manifest, receipt, (0,))
        payload = json.loads(receipt.read_text())
        if result.returncode != 0 or payload.get("status") != "pass":
            raise RuntimeError("positive exact-CLI fixture failed")
        if payload.get("helper", {}).get("sha256") != file_sha256(helper):
            raise RuntimeError("positive receipt helper digest mismatch")
        observed = payload.get("companion_artifacts", [{}])[0].get("sha256")
        if observed != file_sha256(companion):
            raise RuntimeError("positive receipt companion digest mismatch")
        if len(payload.get("validation", [])) != 4:
            raise RuntimeError("positive receipt validation count mismatch")



def symlink_alias_test() -> None:
    """Require canonical path aliases to identify the same companion."""

    with tempfile.TemporaryDirectory(prefix="sage-helper-symlink-") as raw:
        root = Path(raw)
        real_root = root / "real"
        real_root.mkdir()
        alias_root = root / "alias"
        alias_root.symlink_to(real_root, target_is_directory=True)
        repository = copy_runtime(real_root, "validated")
        helper, manifest, companion, _ = build_case(alias_root, positive_helper())
        receipt = root / "receipt.json"
        result = exact_cli(repository, helper, manifest, receipt, (0,))
        payload = json.loads(receipt.read_text())
        if result.returncode != 0 or payload.get("status") != "pass":
            raise RuntimeError("canonical companion path alias failed")
        observed = payload.get("companion_artifacts", [{}])[0].get("sha256")
        if observed != file_sha256(companion):
            raise RuntimeError("canonical companion alias digest mismatch")

def stale_receipt_test() -> None:
    """Require stale receipt evidence to fail closed without replacement."""

    with tempfile.TemporaryDirectory(prefix="sage-helper-stale-") as raw:
        root = Path(raw)
        repository = copy_runtime(root, "validated")
        helper, manifest, _, _ = build_case(root, positive_helper())
        receipt = root / "receipt.json"
        receipt.write_text("stale\n")
        result = exact_cli(repository, helper, manifest, receipt, (2,))
        if result.returncode != 2 or receipt.read_text() != "stale\n":
            raise RuntimeError("stale receipt was not preserved fail-closed")


def main() -> int:
    """Execute exact-CLI positive, lifecycle, and regression fixtures."""

    positive_test()
    symlink_alias_test()
    accepted_gate_test()
    stale_receipt_test()
    cases = (
        ("helper-digest", mutate_digest),
        ("missing-companion", mutate_missing_companion),
        ("companion-digest", mutate_companion_digest),
        ("omitted-companion", mutate_omitted_companion),
        ("unimported-hashlib", mutate_unimported_hashlib),
        ("undefined-authority", mutate_undefined_authority),
        ("invalid-late-path", mutate_invalid_late_path),
        ("unsafe-helper", mutate_unsafe_helper),
    )
    for name, mutation in cases:
        run_failure_case(name, mutation)
    print("PASS exact validated-state helper delivery CLI")
    print("PASS canonical companion path aliases")
    print("PASS accepted lifecycle delivery gate")
    print("PASS helper and companion handoff failures")
    print("PASS hashlib and AUTHORITY_DIGESTS regressions")
    print("PASS defined late-path runtime failure")
    print("PASS unsafe helper and stale receipt failures")
    print("PASS failed paths leave no partial receipt")
    print("Kalaxy3 generated-helper runtime self-test: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, WorkflowCommandError) as error:
        print("Kalaxy3 generated-helper runtime self-test: FAIL CLOSED")
        print(f"  - {error}")
        raise SystemExit(2)
