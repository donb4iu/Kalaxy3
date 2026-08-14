#!/usr/bin/env python3
"""Create a governed planning source from an accepted action and engineering contribution."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

SAGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SAGE_DIR))

from request_execution import ProposalError
from semantic_understanding import load_engineering_contribution
from workflow import WorkflowError
from workflows.semantic_bootstrap import begin_bootstrap, continue_bootstrap


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="sage-semantic-bootstrap-") as raw:
        root = Path(raw)
        package = root / "contribution.zip"
        manifest = {
            "schema_version": "1.0",
            "contribution_id": "TEST-001",
            "contributor": {"participant_class": "llm", "identity": "self-test"},
            "summary": "Add one test file",
            "rationale": "Exercise repository-owned contribution parsing.",
            "assumptions": [],
            "alternatives": ["No change"],
            "files": [{"path": "fixture.txt", "mode": "0644"}],
        }
        with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("engineering-contribution.json", json.dumps(manifest))
            archive.writestr("payload/fixture.txt", b"fixture\n")
        contribution = load_engineering_contribution(package)
        if contribution.paths != ("fixture.txt",):
            raise RuntimeError("engineering contribution path mismatch")
        bad = root / "bad.zip"
        manifest["files"] = [{"path": "sage-source.json", "mode": "0644"}]
        with zipfile.ZipFile(bad, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("engineering-contribution.json", json.dumps(manifest))
            archive.writestr("payload/sage-source.json", b"{}")
        try:
            load_engineering_contribution(bad)
        except ProposalError:
            pass
        else:
            raise RuntimeError("external sage-source.json contribution was accepted")
    print("PASS engineering contribution without caller-authored SAGE hashes")
    print("PASS external sage-source.json authorship fails closed")
    print("Kalaxy3 SAGE semantic bootstrap self-test: PASS")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action-id")
    parser.add_argument("--request")
    parser.add_argument("--contribution", type=Path)
    parser.add_argument("--continue-state", type=Path)
    parser.add_argument("--confirm-understanding-sha256")
    parser.add_argument("--actor")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    continuing = args.continue_state is not None
    starting = any((args.action_id, args.request, args.contribution))
    if continuing and starting:
        raise WorkflowError("start and continue arguments are mutually exclusive")
    if continuing:
        if not args.confirm_understanding_sha256 or not args.actor:
            raise WorkflowError("--confirm-understanding-sha256 and --actor are required with --continue-state")
        result = continue_bootstrap(args.repo, args.continue_state, args.confirm_understanding_sha256, args.actor, args.output)
        print("Kalaxy3 SAGE semantic bootstrap: PASS")
        print("Architect semantic confirmation: PASS")
        print("Feasibility: sufficient for planning-source generation; runtime outcome remains validation-dependent")
        print(f"Planning source: {result['source']}")
        print("Next operator command:")
        print(f"  {result['next_command']['display']}")
        return 0
    if not args.action_id or not args.request or args.contribution is None:
        raise WorkflowError("--action-id, --request, and --contribution are required")
    result = begin_bootstrap(args.repo, args.action_id, args.request, args.contribution)
    print("Kalaxy3 SAGE semantic bootstrap: ARCHITECT CONFIRMATION REQUIRED")
    print(f"Interpretation: {result['semantic_understanding']}")
    print(f"State: {result['state']}")
    print("Next Architect boundary:")
    print(f"  {result['confirmation_command']['display']}")
    print("Confirm only if the interpretation matches intended meaning and implementation scope.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, TypeError, ProposalError, WorkflowError, RuntimeError, zipfile.BadZipFile, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE semantic bootstrap: FAIL CLOSED", file=sys.stderr)
        print(f"  - {error}", file=sys.stderr)
        raise SystemExit(2)
