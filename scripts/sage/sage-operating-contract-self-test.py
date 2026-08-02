#!/usr/bin/env python3
"""Runtime and fail-closed tests for operating-contract composition."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAGE_DIR = ROOT / "scripts" / "sage"
COMPOSITION = SAGE_DIR / "workflows" / "operating_contract.py"
sys.path.insert(0, str(SAGE_DIR))

from workflow import JsonlEventLogger, PrimitiveCatalog  # noqa: E402


def load_composition():
    specification = importlib.util.spec_from_file_location(
        "sage_operating_contract_composition",
        COMPOSITION,
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"Unable to load composition: {COMPOSITION}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def action_map(sequence, observed, *, fail_at=None):
    result = {}
    for step_id, _ in sequence:
        def action(step=step_id):
            observed.append(step)
            if step == fail_at:
                raise RuntimeError(f"expected fixture failure at {step}")
            return {"step": step, "status": "pass"}
        result[step_id] = action
    return result


def event_records(path: Path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def main() -> int:
    composition = load_composition()
    catalog = PrimitiveCatalog.load(ROOT / "sage-workflow-primitives.json")
    catalog.require(composition.PRIMITIVES_USED)

    with tempfile.TemporaryDirectory(
        prefix="kalaxy3-operating-contract-self-test-"
    ) as raw:
        root = Path(raw)
        event_log = root / "events.jsonl"
        logger = JsonlEventLogger(
            event_log,
            "sage.operating-contract.fixture",
            primitive_versions=catalog.versions_for(
                composition.PRIMITIVES_USED
            ),
        )

        observed = []
        pre = composition.build_pre_mutation_workflow(
            workflow_id="sage.operating-contract.fixture.pre",
            logger=logger,
            catalog=catalog,
            actions=action_map(
                composition.PRE_MUTATION_SEQUENCE,
                observed,
            ),
        )
        pre.run()
        expected_pre = [
            step_id
            for step_id, _ in composition.PRE_MUTATION_SEQUENCE
        ]
        if observed != expected_pre:
            raise RuntimeError(
                f"Pre-mutation sequence mismatch: {observed}"
            )

        observed_post = []
        post = composition.build_post_operator_workflow(
            workflow_id="sage.operating-contract.fixture.post",
            logger=logger,
            catalog=catalog,
            actions=action_map(
                composition.POST_OPERATOR_SEQUENCE,
                observed_post,
            ),
        )
        post.run()
        expected_post = [
            step_id
            for step_id, _ in composition.POST_OPERATOR_SEQUENCE
        ]
        if observed_post != expected_post:
            raise RuntimeError(
                f"Post-operator sequence mismatch: {observed_post}"
            )

        failure_log = root / "failure-events.jsonl"
        failure_logger = JsonlEventLogger(
            failure_log,
            "sage.operating-contract.fixture.failure",
            primitive_versions=catalog.versions_for(
                composition.PRIMITIVES_USED
            ),
        )
        failed_observed = []
        failed = composition.build_pre_mutation_workflow(
            workflow_id="sage.operating-contract.fixture.failure",
            logger=failure_logger,
            catalog=catalog,
            actions=action_map(
                composition.PRE_MUTATION_SEQUENCE,
                failed_observed,
                fail_at="implement-declared-repository-scope",
            ),
        )
        try:
            failed.run()
        except RuntimeError as error:
            if "expected fixture failure" not in str(error):
                raise
        else:
            raise RuntimeError("Failure fixture unexpectedly passed")

        stop_index = expected_pre.index(
            "implement-declared-repository-scope"
        ) + 1
        if failed_observed != expected_pre[:stop_index]:
            raise RuntimeError(
                "Composition did not stop at the first failed primitive"
            )

        records = event_records(event_log)
        failures = event_records(failure_log)
        if not any(
            item.get("event") == "workflow-finish"
            and item.get("status") == "pass"
            for item in records
        ):
            raise RuntimeError("Successful composition closeout event missing")
        if not any(
            item.get("event") == "workflow-finish"
            and item.get("status") == "fail"
            for item in failures
        ):
            raise RuntimeError("Failed composition closeout event missing")

    print("PASS exact pre-mutation operating-contract sequence")
    print("PASS operator boundary separates post-command verification")
    print("PASS composition stops on the first failed primitive")
    print("PASS structured pass and fail runtime events")
    print("Kalaxy3 SAGE operating-contract self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
