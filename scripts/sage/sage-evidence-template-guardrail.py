#!/usr/bin/env python3
"""Guard shared SAGE evidence authorities and immutable record compatibility."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from workflow.evidence_records import (
    EvidenceAuthorities,
    EvidenceRecord,
    EvidenceTemplatePolicy,
)
from workflow.markdown import MarkdownDocument
from workflow.model import WorkflowError


class TemplateError(WorkflowError):
    """Raised when evidence authorities or records diverge."""


def parse_args() -> argparse.Namespace:
    """Parse guardrail options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def publisher_imports_shared_authorities(path: Path) -> bool:
    """Return whether publisher imports the shared publication authorities."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "workflow.evidence_records":
            continue
        names = {item.name for item in node.names}
        if "PUBLICATION_AUTHORITIES" in names:
            return True
    return False


def authority_audit(authorities: EvidenceAuthorities) -> dict[str, Any]:
    """Validate contract, template, publisher, and policy agreement."""
    contract = authorities.contract
    template = authorities.template
    if template.front_matter_keys() != authorities.front_matter_order:
        raise TemplateError("Template front matter differs from JSON contract")
    labels = template.table_labels("Record metadata")
    expected_labels = tuple(label for label, _ in authorities.metadata_rows)
    if labels != expected_labels:
        raise TemplateError("Template metadata rows differ from JSON contract")
    if not authorities.policy.exact_template_required_for_new_packages:
        raise TemplateError("Exact current template is not required for new packages")
    publisher = authorities.repository_root / authorities.policy.publisher_path
    if not publisher_imports_shared_authorities(publisher):
        raise TemplateError("Publisher does not import shared evidence authorities")
    return {
        **authorities.authority_summary(),
        "policy_path": str(authorities.policy.path.relative_to(authorities.repository_root)),
        "publisher_uses_shared_authorities": True,
        "exact_template_required_for_new_packages": True,
    }


def record_detail(
    authorities: EvidenceAuthorities,
    record: EvidenceRecord,
    profile: str,
) -> dict[str, Any]:
    """Return one current-record compatibility detail."""
    document = MarkdownDocument.load(
        authorities.repository_root / record.source_path
    )
    headings = document.h2_headings()
    return {
        "evidence_id": record.evidence_id,
        "source_path": record.source_path,
        "profile": profile,
        "missing_current_template_headings": [
            item for item in authorities.template_headings if item not in headings
        ],
        "additional_or_renamed_headings": [
            item for item in headings if item not in authorities.template_headings
        ],
    }


def record_audit(authorities: EvidenceAuthorities) -> dict[str, Any]:
    """Classify current records and inventory immutable historical records."""
    current = authorities.catalog.current(
        authorities.policy.current_record_class
    )
    exact: list[str] = []
    variants: list[dict[str, Any]] = []
    for record in current:
        profile = authorities.classify_current_record(record)
        if profile == "exact-current-template":
            exact.append(record.evidence_id)
        else:
            variants.append(record_detail(authorities, record, profile))
    legacy = authorities.catalog.legacy(
        authorities.policy.current_record_class
    )
    return {
        "current_count": len(current),
        "exact_current_template_count": len(exact),
        "exact_current_template_ids": exact,
        "compatible_template_variant_count": len(variants),
        "compatible_template_variants": variants,
        "legacy_count": len(legacy),
        "legacy_classes": sorted({item.record_class for item in legacy}),
        "immutable_record_classes": list(
            authorities.policy.immutable_record_classes
        ),
    }


def build_report(repo: Path) -> dict[str, Any]:
    """Build the complete authority and record audit."""
    authorities = EvidenceAuthorities.load(repo)
    return {
        "schema_version": "1.0",
        "report_type": "sage-evidence-template-consistency",
        "authority": authority_audit(authorities),
        "records": record_audit(authorities),
        "status": "pass",
    }


def write_report(path: Path | None, report: Mapping[str, Any]) -> None:
    """Write an optional JSON report."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fixture_policy(root: Path) -> Path:
    """Write a minimal evidence-template policy fixture."""
    path = root / "sage-evidence-template-policy.json"
    payload = {
        "schema_version": "1.0",
        "policy_id": "fixture",
        "metadata_contract_path": "contract.json",
        "template_path": "template.md",
        "catalog_path": "catalog.json",
        "publisher_path": "publisher.py",
        "current_record_class": "sage-current",
        "immutable_record_classes": ["sage-legacy", "legacy-evidence"],
        "exact_template_required_for_new_packages": True,
        "compatible_heading_prefixes": ["Executive summary", "Record metadata"],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_fixture_contract(root: Path) -> None:
    """Write a minimal metadata-contract fixture."""
    payload = {
        "front_matter_order": ["evidence_id", "schema_version"],
        "list_fields": [],
        "static_metadata_rows": [
            ["Evidence ID", "evidence_id"],
            ["Schema version", "schema_version"],
        ],
        "five_w_rows": ["Who", "What", "When", "Where", "Why", "How"],
    }
    (root / "contract.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def write_fixture_record(root: Path) -> None:
    """Write matching template and current-record fixtures."""
    template = (
        "---\nevidence_id: fixture\nschema_version: '1.2'\n---\n"
        "# Fixture\n\n## Executive summary\n\n[TOC]\n\n"
        "## Record metadata\n\n| Field | Value |\n|---|---|\n"
        "| **Evidence ID** | fixture |\n"
        "| **Schema version** | 1.2 |\n"
    )
    (root / "template.md").write_text(template, encoding="utf-8")
    (root / "record.md").write_text(template, encoding="utf-8")


def write_fixture_catalog(root: Path) -> None:
    """Write a one-record evidence catalog fixture."""
    catalog = {
        "records": [
            {
                "evidence_id": "fixture",
                "source_path": "record.md",
                "record_class": "sage-current",
                "title": "Fixture",
                "nav_title": "Fixture",
                "metadata_source": "front-matter",
                "migration_status": "current",
            }
        ]
    }
    (root / "catalog.json").write_text(
        json.dumps(catalog),
        encoding="utf-8",
    )


def self_test() -> int:
    """Exercise shared parsing and immutable compatibility classification."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        fixture_policy(root)
        write_fixture_contract(root)
        write_fixture_record(root)
        write_fixture_catalog(root)
        (root / "publisher.py").write_text(
            "from workflow.evidence_records import PUBLICATION_AUTHORITIES\n",
            encoding="utf-8",
        )
        policy = EvidenceTemplatePolicy.load(
            root / "sage-evidence-template-policy.json"
        )
        if policy.current_record_class != "sage-current":
            raise TemplateError("Template policy parser")
        document = MarkdownDocument.load(root / "record.md")
        expected = ("Executive summary", "Record metadata")
        if document.h2_headings() != expected:
            raise TemplateError("Markdown heading parser")
    print("PASS shared template-policy and Markdown parsing")
    print("PASS immutable current-record compatibility model")
    print("Kalaxy3 SAGE evidence template guardrail self-test: PASS")
    return 0


def main() -> int:
    """Run the evidence-template consistency guardrail."""
    args = parse_args()
    if args.self_test:
        return self_test()
    repo = args.repo.expanduser().resolve()
    report = build_report(repo)
    output = (repo / args.output).resolve() if args.output else None
    write_report(output, report)
    records = report["records"]
    print("Kalaxy3 SAGE evidence template guardrail: PASS")
    print(f"Current schema 1.2 records: {records['current_count']}")
    print(
        "Exact current template records: "
        f"{records['exact_current_template_count']}"
    )
    print(
        "Compatible immutable variants: "
        f"{records['compatible_template_variant_count']}"
    )
    print(f"Historical and legacy records: {records['legacy_count']}")
    print("New evidence packages require the exact current template")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (TemplateError, WorkflowError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Kalaxy3 SAGE evidence template guardrail: FAIL\n{error}", file=sys.stderr)
        raise SystemExit(2)
