#!/usr/bin/env python3
"""Pilot thin composition for read-only repository validation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SAGE_DIR = ROOT / "scripts" / "sage"
sys.path.insert(0, str(SAGE_DIR))

from workflow import (  # noqa: E402
    CloseoutWriter,
    CommandRunner,
    GitRepository,
    JsonlEventLogger,
    PrimitiveCatalog,
    SageDiscovery,
    Step,
    UsageAnalyzer,
    ValidationCommand,
    ValidationPlan,
    Workflow,
)

WORKFLOW_ID = "sage.repository-validation"
PRIMITIVES_USED = (
    "catalog.registry",
    "logging.events",
    "command.run",
    "git.repository",
    "sage.discovery",
    "validation.plan",
    "evidence.closeout",
    "usage.summary",
    "workflow.composition",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument(
        "--validation",
        action="append",
        default=[],
        help="Make target to execute; may be repeated",
    )
    args = parser.parse_args()

    suffix = datetime.now().strftime("%Y%m%d-%H%M%S")
    state = (
        Path.home()
        / ".local"
        / "state"
        / "kalaxy3"
        / "sage-workflows"
    )
    event_log = state / f"{WORKFLOW_ID}-{suffix}.jsonl"

    catalog = PrimitiveCatalog.load(
        ROOT / "sage-workflow-primitives.json"
    )
    versions = catalog.versions_for(PRIMITIVES_USED)
    logger = JsonlEventLogger(
        event_log,
        WORKFLOW_ID,
        primitive_versions=versions,
    )
    runner = CommandRunner(
        logger,
        allowed_roots=(ROOT,),
    )
    repository = GitRepository(ROOT, runner)
    discovery = SageDiscovery(ROOT, runner)

    targets = args.validation or [
        "sage-workflow-support-self-test",
        "sage-workflow-support-guardrail",
        "sage-workflow-self-test",
        "sage-workflow-guardrail",
        "sage-index-check",
    ]
    validation = ValidationPlan(
        ROOT,
        runner,
        [
            ValidationCommand(
                label=f"Validate Make target {target}",
                argv=("make", target),
                timeout_seconds=1200.0,
            )
            for target in targets
        ],
    )

    results: dict[str, object] = {}
    branch = repository.branch()
    workflow = Workflow(
        workflow_id=WORKFLOW_ID,
        logger=logger,
        catalog=catalog,
        steps=(
            Step(
                "repository-state",
                "git.repository",
                lambda: (
                    repository.require_clean(),
                    repository.require_synced(branch),
                ),
            ),
            Step(
                "sage-discovery",
                "sage.discovery",
                lambda: results.setdefault(
                    "preflight",
                    discovery.literal(args.request),
                ),
            ),
            Step(
                "validation",
                "validation.plan",
                lambda: results.setdefault(
                    "validation",
                    validation.run(),
                ),
            ),
        ),
    )
    workflow.run()

    preflight = results["preflight"]
    closeout = CloseoutWriter(
        destination_directory=Path.home() / "Downloads",
        primitive_registry=ROOT / "sage-workflow-primitives.json",
        event_log=event_log,
    ).write(
        workflow_id=WORKFLOW_ID,
        status="pass",
        used_primitives=PRIMITIVES_USED,
        details={
            "request": args.request,
            "contexts": list(preflight.contexts),
            "authorities": list(preflight.authorities),
            "validation_targets": targets,
            "branch": branch,
            "head": repository.head(),
        },
    )

    summary = UsageAnalyzer.summarize((event_log,))
    print(
        json.dumps(
            {
                "closeout": str(closeout),
                "usage": summary,
            },
            indent=4,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
