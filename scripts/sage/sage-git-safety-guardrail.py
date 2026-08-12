#!/usr/bin/env python3
"""CLI guardrail for downloaded helper Git and credential safety."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import GitSafetyGuardrail  # noqa: E402


def self_test() -> int:
    safe = """from workflow import GitInspector\nPRIMITIVES_USED = (\"git.inspect\",)\n"""
    bad_git = """import subprocess\nsubprocess.run([\"git\", \"add\", \".\"])\n"""
    bad_gh = """from workflow import CommandSpec\nCommandSpec(primitive_id=\"command.run\", label=\"x\", argv=(\"gh\", \"pr\", \"create\"), cwd=ROOT)\n"""
    bad_api = (
        "from urllib.request import urlopen\n"
        + "urlopen('https://api."
        + "github.com/repos/example/repo/pulls')\n"
    )
    bad_secret = """import os\ntoken = os.environ.get(\"GH_TOKEN\")\n"""
    bad_deploy = """from workflow import CommandSpec\nCommandSpec(primitive_id=\"command.run\", label=\"x\", argv=(\"kubectl\", \"apply\", \"-f\", \"x\"), cwd=ROOT)\n"""
    trusted_controller = (
        "from workflow import GitRepository\n"
        "repository = GitRepository(ROOT, RUNNER)\n"
        "repository.commit_and_push(branch='feature/x', exact_paths=('x',), message='x', apply=True)\n"
    )
    trusted_forbidden = (
        "from workflow import GitRepository\n"
        "repository = GitRepository(ROOT, RUNNER)\n"
        "repository.create_branch('feature/x', apply=True)\n"
    )

    if GitSafetyGuardrail.scan_source(safe, path=Path("safe.py")):
        raise RuntimeError("safe helper was rejected")
    for label, source, code in (
        ("git", bad_git, "GIT-MUTATION"),
        ("github", bad_gh, "GITHUB-MUTATION"),
        ("github-api", bad_api, "GITHUB-DIRECT-API"),
        ("credential", bad_secret, "CREDENTIAL-INHERITANCE"),
        ("deployment", bad_deploy, "DEPLOYMENT-MUTATION"),
    ):
        observed = GitSafetyGuardrail.scan_source(source, path=Path(f"bad-{label}.py"))
        if not any(item.code == code for item in observed):
            raise RuntimeError(f"{label} negative test did not fail closed")

    trusted_path = Path("scripts/sage/workflows/routine_git_lifecycle.py")
    if GitSafetyGuardrail.scan_source(trusted_controller, path=trusted_path):
        raise RuntimeError("trusted routine Git controller commit-and-push path was rejected")
    misplaced = GitSafetyGuardrail.scan_source(
        trusted_controller,
        path=Path("scripts/sage/workflows/not-trusted.py"),
    )
    if not any(item.code == "MIXED-GIT-AUTHORITY" for item in misplaced):
        raise RuntimeError("trusted routine Git allowance escaped its exact path")
    forbidden = GitSafetyGuardrail.scan_source(trusted_forbidden, path=trusted_path)
    if not any(item.code == "GIT-MUTATION-API" for item in forbidden):
        raise RuntimeError("trusted routine Git controller accepted branch creation")

    with tempfile.TemporaryDirectory(prefix="sage-git-safety-fixture-") as raw:
        root = Path(raw)
        fixture = root / "fixture.py"
        fixture.write_text(bad_git, encoding="utf-8")
        if GitSafetyGuardrail.scan_paths(
            (fixture,),
            allow_fixture_mutation=True,
            fixture_root=root,
        ):
            raise RuntimeError("isolated temporary fixture mutation was rejected")
        outside = Path("fixture.py")
        if not GitSafetyGuardrail.scan_source(
            bad_git,
            path=outside,
            allow_fixture_mutation=True,
            fixture_root=root,
        ):
            raise RuntimeError("fixture allowance escaped its temporary root")

    print("PASS read-only helper path")
    print("PASS Git mutation, GitHub mutation, and direct GitHub API rejection")
    print("PASS credential inheritance rejection")
    print("PASS deployment mutation rejection")
    print("PASS isolated temporary-repository fixture allowance")
    print("PASS exact-path routine Git controller allowance for commit-and-push only")
    print("Kalaxy3 Git safety guardrail self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    paths = tuple(args.paths)
    if not paths:
        paths = tuple(sorted((ROOT / "scripts/sage/workflows").glob("*.py")))
    violations = GitSafetyGuardrail.scan_paths(paths)
    if violations:
        print("Kalaxy3 Git safety guardrail: FAIL CLOSED")
        for violation in violations:
            print(f"  - {violation.render()}")
        return 1
    print(f"PASS Git safety scan for {len(paths)} path(s)")
    print("Kalaxy3 Git safety guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
