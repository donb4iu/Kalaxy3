#!/usr/bin/env python3
"""Fail closed when the SAGE thin-slice model, generated views, or evidence boundary drift."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/sage/sage-thin-slice.py"
LEGACY_REGISTRY = "markdown/evidence/legacy-record-registry.json"
EVIDENCE_CATALOG = "markdown/evidence/catalog.json"
GENERATED_VIEW = "markdown/architecture/kalaxy3-sage-thin-slice.md"


def load_cli() -> object:
    spec = importlib.util.spec_from_file_location("sage_thin_slice", CLI)
    if spec is None or spec.loader is None:
        raise RuntimeError("thin-slice module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evidence_boundary_failures(
    registry: Mapping[str, Any],
    catalog: Mapping[str, Any],
    generated_view: str = GENERATED_VIEW,
) -> list[str]:
    failures: list[str] = []

    exclude_paths = registry.get("exclude_paths")
    if not isinstance(exclude_paths, list):
        failures.append("legacy evidence exclude_paths must be a list")
    else:
        count = sum(path == generated_view for path in exclude_paths)
        if count != 1:
            failures.append(
                "thin-slice generated view must occur exactly once in "
                f"legacy evidence exclude_paths; found {count}"
            )

    records = catalog.get("records")
    if not isinstance(records, list):
        failures.append("evidence catalog records must be a list")
    else:
        contaminants = [
            str(record.get("evidence_id", "unknown"))
            for record in records
            if isinstance(record, Mapping)
            and record.get("source_path") == generated_view
        ]
        if contaminants:
            failures.append(
                "thin-slice generated view appears in evidence catalog: "
                + ", ".join(contaminants)
            )

    return failures


def evidence_boundary_self_test() -> list[str]:
    failures: list[str] = []
    clean_registry = {"exclude_paths": [GENERATED_VIEW]}
    clean_catalog = {"records": []}

    if evidence_boundary_failures(clean_registry, clean_catalog):
        failures.append("positive evidence-boundary fixture failed")

    missing = evidence_boundary_failures({"exclude_paths": []}, clean_catalog)
    if not any("exactly once" in failure and "found 0" in failure for failure in missing):
        failures.append(f"missing-exclusion negative test did not fail closed: {missing}")

    duplicate = evidence_boundary_failures(
        {"exclude_paths": [GENERATED_VIEW, GENERATED_VIEW]},
        clean_catalog,
    )
    if not any("exactly once" in failure and "found 2" in failure for failure in duplicate):
        failures.append(f"duplicate-exclusion negative test did not fail closed: {duplicate}")

    contaminated = evidence_boundary_failures(
        clean_registry,
        {
            "records": [
                {
                    "evidence_id": "LEGACY-K3-TEST",
                    "source_path": GENERATED_VIEW,
                }
            ]
        },
    )
    if not any(
        "appears in evidence catalog" in failure and "LEGACY-K3-TEST" in failure
        for failure in contaminated
    ):
        failures.append(f"catalog-contamination negative test did not fail closed: {contaminated}")

    return failures


def main() -> int:
    try:
        module = load_cli()
        value = module.load(ROOT)
        failures = module.validate(value)
        if failures:
            raise RuntimeError("; ".join(failures))
        view = module.render(value).rstrip() + "\n"
        metrics = json.dumps(module.metrics(value), indent=2, ensure_ascii=False).rstrip() + "\n"
        if (ROOT / module.VIEW).read_text(encoding="utf-8") != view:
            raise RuntimeError("rendered thin-slice view differs")
        if (ROOT / module.METRICS).read_text(encoding="utf-8") != metrics:
            raise RuntimeError("thin-slice metrics snapshot differs")
        self_failures = module.self_test(value)
        if self_failures:
            raise RuntimeError("; ".join(self_failures))

        boundary_self_failures = evidence_boundary_self_test()
        if boundary_self_failures:
            raise RuntimeError("; ".join(boundary_self_failures))

        registry = json.loads((ROOT / LEGACY_REGISTRY).read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / EVIDENCE_CATALOG).read_text(encoding="utf-8"))
        boundary_failures = evidence_boundary_failures(registry, catalog)
        if boundary_failures:
            raise RuntimeError("; ".join(boundary_failures))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print("Kalaxy3 SAGE thin-slice guardrail: FAIL CLOSED")
        print(f"  - {error}")
        return 1
    print("PASS coherent public introduction and selected real case")
    print("PASS source, SAGE, and human authority separation")
    print("PASS end-to-end trace, evidence, measures, and unknowns")
    print("PASS wider participation and reusable future capability")
    print("PASS thin-slice generated-view legacy exclusion")
    print("PASS generated thin-slice view absent from evidence catalog")
    print("Kalaxy3 SAGE thin-slice guardrail: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
