#!/usr/bin/env python3
"""Audit evidence-navigation code against Kalaxy3 reuse objectives."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping, Sequence

from workflow.catalog import PrimitiveCatalog
from workflow.model import WorkflowError

POLICY = Path("mkdocs-navigation-policy.json")
TEMPLATE_POLICY = Path("sage-evidence-template-policy.json")
GENERATOR = Path("scripts/docs/generate-mkdocs-navigation.py")
VALIDATOR = Path("scripts/docs/validate-mkdocs-navigation.py")
SUPPORT = Path("scripts/docs/navigation_support.py")
MARKDOWN = Path("scripts/sage/workflow/markdown.py")
RECORDS = Path("scripts/sage/workflow/evidence_records.py")
TEMPLATE_GUARDRAIL = Path("scripts/sage/sage-evidence-template-guardrail.py")
PUBLISHER = Path("scripts/sage/sage-publish.py")
COMPOSITION = Path("scripts/sage/workflows/evidence_navigation.py")
PRIMITIVES = Path("sage-workflow-primitives.json")


class ArchitectureError(WorkflowError):
    """Raised when the implementation violates reuse objectives."""


def parse_args() -> argparse.Namespace:
    """Parse architecture-audit options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def read(repo: Path, relative: Path) -> str:
    """Read one required repository file."""
    path = repo / relative
    if not path.is_file():
        raise ArchitectureError(f"Required architecture file is missing: {relative}")
    return path.read_text(encoding="utf-8")


def imported_modules(text: str) -> set[str]:
    """Return imported module names from one Python source file."""
    tree = ast.parse(text)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def assigned_names(text: str) -> set[str]:
    """Return top-level assigned names from one Python source file."""
    tree = ast.parse(text)
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    result.add(target.id)
    return result


def composition_primitives(text: str) -> tuple[str, ...]:
    """Extract PRIMITIVES_USED from the tracked workflow composition."""
    tree = ast.parse(text)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id == "PRIMITIVES_USED":
            value = ast.literal_eval(node.value)
            return tuple(str(item) for item in value)
    raise ArchitectureError("Tracked composition lacks PRIMITIVES_USED")


def objective(
    identifier: str,
    statement: str,
    passed: bool,
    evidence: Sequence[str],
) -> dict[str, Any]:
    """Build one self-audit objective result."""
    return {
        "objective_id": identifier,
        "statement": statement,
        "status": "pass" if passed else "fail",
        "evidence": list(evidence),
    }


def audit_inputs(repo: Path) -> dict[str, Any]:
    """Load source, policy, registry, and composition audit inputs."""
    composition = read(repo, COMPOSITION)
    used = composition_primitives(composition)
    registry = PrimitiveCatalog.load(repo / PRIMITIVES)
    registry.require(used)
    return {
        "generator": read(repo, GENERATOR),
        "validator": read(repo, VALIDATOR),
        "support": read(repo, SUPPORT),
        "guardrail": read(repo, TEMPLATE_GUARDRAIL),
        "publisher": read(repo, PUBLISHER),
        "composition": composition,
        "navigation_policy": json.loads(read(repo, POLICY)),
        "template_policy": json.loads(read(repo, TEMPLATE_POLICY)),
        "used_primitives": used,
    }


def policy_objectives(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Evaluate machine-readable navigation and template policy objectives."""
    generator = str(inputs["generator"])
    navigation_policy = inputs["navigation_policy"]
    template_policy = inputs["template_policy"]
    return [
        objective(
            "policy-driven-navigation",
            "Navigation hierarchy is versioned data, not embedded CLI constants.",
            "CURATED_EVIDENCE" not in generator
            and isinstance(navigation_policy.get("evidence"), dict),
            [str(POLICY), str(GENERATOR)],
        ),
        objective(
            "exact-new-template",
            "New evidence packages require the exact current template.",
            template_policy.get("exact_template_required_for_new_packages") is True,
            [str(TEMPLATE_POLICY), str(PUBLISHER)],
        ),
        objective(
            "immutable-history",
            "Legacy and published variants are classified without automatic rewrite.",
            bool(template_policy.get("immutable_record_classes")),
            [str(TEMPLATE_POLICY), str(TEMPLATE_GUARDRAIL)],
        ),
    ]


def shared_authority_objectives(
    inputs: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate shared navigation, evidence, and Markdown authorities."""
    generator = str(inputs["generator"])
    validator = str(inputs["validator"])
    support = str(inputs["support"])
    guardrail = str(inputs["guardrail"])
    publisher = str(inputs["publisher"])
    contract_names = {
        "REQUIRED_FRONTMATTER_ORDER",
        "STATIC_METADATA_ROWS",
        "FIVE_W_ROWS",
        "REQUIRED_TEMPLATE_HEADINGS",
    }
    return [
        objective(
            "shared-navigation-library",
            "Generation and rendered validation share one navigation library.",
            "navigation_support" in imported_modules(generator)
            and "navigation_support" in imported_modules(validator),
            [str(SUPPORT), str(GENERATOR), str(VALIDATOR)],
        ),
        objective(
            "shared-evidence-authorities",
            "Publisher and guardrail consume shared contract authorities.",
            "workflow.evidence_records" in imported_modules(publisher)
            and "workflow.evidence_records" in imported_modules(guardrail)
            and not contract_names.intersection(assigned_names(publisher)),
            [str(RECORDS), str(PUBLISHER), str(TEMPLATE_GUARDRAIL)],
        ),
        objective(
            "shared-markdown-parser",
            "Front matter, headings, and metadata tables use one parser.",
            "workflow.markdown" in imported_modules(support)
            and "workflow.markdown" in imported_modules(guardrail),
            [str(MARKDOWN), str(SUPPORT), str(TEMPLATE_GUARDRAIL)],
        ),
    ]


def shared_navigation_contract_objectives(
    inputs: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Evaluate shared source-path and section-index contracts."""
    validator = str(inputs["validator"])
    support = str(inputs["support"])
    navigation_policy = inputs["navigation_policy"]
    return [
        objective(
            "dual-source-namespace",
            "Shared URL mapping accepts repository and staged source paths.",
            "source_relative_path" in support
            and "markdown/operations/example.md" in validator
            and "operations/example.md" in validator
            and "../operations/example.md" in validator,
            [str(SUPPORT), str(VALIDATOR)],
        ),
        objective(
            "section-index-contract",
            "Evidence landing and children share one rendered-link contract.",
            navigation_policy.get("evidence", {}).get("index_page")
            == "evidence/index.md"
            and "primary_evidence_pages" in support
            and "primary_evidence_pages" in validator
            and "evidence_index_page" in support,
            [str(POLICY), str(SUPPORT), str(VALIDATOR)],
        ),
    ]


def workflow_objectives(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Evaluate composition and mutation-boundary objectives."""
    generator = str(inputs["generator"])
    validator = str(inputs["validator"])
    support = str(inputs["support"])
    guardrail = str(inputs["guardrail"])
    composition = str(inputs["composition"])
    return [
        objective(
            "thin-tracked-composition",
            "Future work is represented by a registered primitive composition.",
            "subprocess" not in imported_modules(composition)
            and bool(inputs["used_primitives"]),
            [str(COMPOSITION), str(PRIMITIVES)],
        ),
        objective(
            "no-domain-git-mutation",
            "Permanent navigation and template code performs no Git mutation.",
            all(
                "subprocess" not in imported_modules(text)
                for text in (generator, validator, support, guardrail, composition)
            ),
            [str(GENERATOR), str(VALIDATOR), str(SUPPORT), str(COMPOSITION)],
        ),
    ]


def objective_results(inputs: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Evaluate all established reuse objectives."""
    return [
        *policy_objectives(inputs),
        *shared_authority_objectives(inputs),
        *shared_navigation_contract_objectives(inputs),
        *workflow_objectives(inputs),
    ]


def audit(repo: Path) -> dict[str, Any]:
    """Audit permanent code against established Kalaxy3 objectives."""
    inputs = audit_inputs(repo)
    results = objective_results(inputs)
    failures = [item for item in results if item["status"] != "pass"]
    if failures:
        identifiers = [item["objective_id"] for item in failures]
        raise ArchitectureError(f"Reuse objectives failed: {identifiers}")
    used = list(inputs["used_primitives"])
    return {
        "schema_version": "1.0",
        "report_type": "evidence-navigation-architecture-self-audit",
        "objectives": results,
        "objective_count": len(results),
        "passed_objectives": len(results),
        "registered_primitives_used": used,
        "status": "pass",
    }


def write_report(path: Path | None, report: Mapping[str, Any]) -> None:
    """Write an optional architecture-audit report."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def self_test(repo: Path) -> int:
    """Exercise inspection helpers and the normal repository audit path."""
    source = (
        "from workflow.evidence_records import PUBLICATION_AUTHORITIES\n"
        "PRIMITIVES_USED = ('git.inspect',)\n"
    )
    if "workflow.evidence_records" not in imported_modules(source):
        raise ArchitectureError("Import inspection")
    if composition_primitives(source) != ("git.inspect",):
        raise ArchitectureError("Composition primitive inspection")
    report = audit(repo)
    if report["status"] != "pass":
        raise ArchitectureError("Normal repository audit path did not pass")
    with TemporaryDirectory() as directory:
        path = Path(directory) / "report.json"
        write_report(path, report)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("passed_objectives") != report["passed_objectives"]:
            raise ArchitectureError("Report writer changed audit results")
    print("PASS architecture import and composition inspection")
    print("PASS normal repository audit path")
    print("PASS machine-readable objective reporting")
    print("Kalaxy3 evidence navigation architecture guardrail self-test: PASS")
    return 0


def main() -> int:
    """Run the architecture self-audit."""
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    if args.self_test:
        return self_test(repo)
    report = audit(repo)
    output = (repo / args.output).resolve() if args.output else None
    write_report(output, report)
    print("Kalaxy3 evidence navigation architecture guardrail: PASS")
    print(f"Reuse objectives passed: {report['passed_objectives']}")
    print(
        "Registered primitives used by composition: "
        f"{len(report['registered_primitives_used'])}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ArchitectureError, WorkflowError, OSError, ValueError, json.JSONDecodeError) as error:
        print(
            f"Kalaxy3 evidence navigation architecture guardrail: FAIL\n{error}",
            file=sys.stderr,
        )
        raise SystemExit(2)
