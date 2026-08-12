#!/usr/bin/env python3
"""Validate and render the Kalaxy3 SAGE end-to-end thin slice."""

from __future__ import annotations

import argparse
import copy
import html
import importlib.util
import json
import posixpath
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
MODEL = "sage-thin-slice.json"
VIEW = "markdown/architecture/kalaxy3-sage-thin-slice.md"
METRICS = "markdown/architecture/kalaxy3-sage-thin-slice-metrics.json"
CATALOG = "markdown/evidence/catalog.json"
NAVIGATION_SUPPORT = "scripts/docs/navigation_support.py"


def load(root: Path) -> dict[str, Any]:
    return json.loads((root / MODEL).read_text(encoding="utf-8"))


def _require_fields(value: Mapping[str, Any], fields: tuple[str, ...], label: str) -> list[str]:
    return [f"{label} missing {field}" for field in fields if field not in value]


def _validate_selected(value: Mapping[str, Any]) -> list[str]:
    failures = _require_fields(
        value,
        ("capability_id", "selection_authority_id", "selection_rationale", "evidence_refs"),
        "selected_case",
    )
    if value.get("selection_authority_id") != "operator-intent":
        failures.append("selected case must preserve operator decision authority")
    if not value.get("evidence_refs"):
        failures.append("selected case requires evidence")
    return failures


def _validate_alternatives(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    identifiers = [item.get("case_id") for item in items]
    if len(identifiers) != len(set(identifiers)):
        failures.append("alternative case IDs must be unique")
    dispositions = {item.get("disposition") for item in items}
    if "rejected" not in dispositions:
        failures.append("at least one rejected alternative is required")
    if "do-nothing" not in identifiers:
        failures.append("do-nothing alternative is required")
    for item in items:
        failures.extend(_require_fields(item, ("case_id", "title", "disposition", "rationale"), "alternative"))
    return failures


def _validate_trace(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    expected = list(range(1, len(items) + 1))
    if [item.get("sequence") for item in items] != expected:
        failures.append("end-to-end trace sequence must be contiguous")
    for item in items:
        failures.extend(_require_fields(
            item,
            ("sequence", "stage_id", "title", "source_statement", "sage_contribution", "human_contribution", "evidence_refs"),
            "trace stage",
        ))
        if not item.get("evidence_refs"):
            failures.append(f"{item.get('stage_id')}: source-backed stage requires evidence")
        if not item.get("human_contribution"):
            failures.append(f"{item.get('stage_id')}: human contribution is required")
    return failures


def _validate_measures(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    identifiers = [item.get("measure_id") for item in items]
    if len(identifiers) != len(set(identifiers)):
        failures.append("measure IDs must be unique")
    for item in items:
        failures.extend(_require_fields(
            item,
            ("measure_id", "description", "target", "actual", "unit", "status", "measurement_type", "evidence_refs"),
            "measure",
        ))
        unavailable = item.get("measurement_type") == "unavailable"
        if unavailable and item.get("actual") is not None:
            failures.append(f"{item.get('measure_id')}: unavailable actual must be null")
        if not unavailable and not item.get("evidence_refs"):
            failures.append(f"{item.get('measure_id')}: measured outcome requires evidence")
        if item.get("status") == "not-measured" and not unavailable:
            failures.append(f"{item.get('measure_id')}: not-measured must be unavailable")
    return failures


def _validate_participation(items: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    required = {"reader", "operator", "domain-expert", "engineer", "reviewer"}
    observed = {item.get("participant") for item in items}
    if not required <= observed:
        failures.append(f"participation paths missing {sorted(required - observed)}")
    for item in items:
        failures.extend(_require_fields(item, ("participant", "entry_action", "authority"), "participation path"))
    return failures


def validate(value: Mapping[str, Any]) -> list[str]:
    failures = _require_fields(
        value,
        ("schema_version", "thin_slice_id", "title", "status", "audience", "introduction", "case_question", "selected_case", "alternatives", "end_to_end_trace", "measures", "participation_paths", "future_capability"),
        "thin slice",
    )
    if value.get("schema_version") != "1.0":
        failures.append("schema_version must be 1.0")
    if value.get("thin_slice_id") != "kalaxy3.centralized-logging":
        failures.append("unexpected thin_slice_id")
    failures.extend(_validate_selected(value.get("selected_case", {})))
    failures.extend(_validate_alternatives(value.get("alternatives", [])))
    failures.extend(_validate_trace(value.get("end_to_end_trace", [])))
    failures.extend(_validate_measures(value.get("measures", [])))
    failures.extend(_validate_participation(value.get("participation_paths", [])))
    return failures


def metrics(value: Mapping[str, Any]) -> dict[str, Any]:
    measures = value["measures"]
    return {
        "schema_version": "1.0",
        "snapshot_type": "sage-thin-slice",
        "thin_slice_id": value["thin_slice_id"],
        "status": value["status"],
        "trace_stage_count": len(value["end_to_end_trace"]),
        "alternative_count": len(value["alternatives"]),
        "participation_path_count": len(value["participation_paths"]),
        "measures_met": sum(item["status"] == "met" for item in measures),
        "measures_not_measured": sum(item["status"] == "not-measured" for item in measures),
        "measures": measures,
        "maturity_claim": None,
    }


def _load_navigation_support(root: Path) -> Any:
    """Load the repository-owned MkDocs navigation contract."""
    path = root / NAVIGATION_SUPPORT
    if not path.is_file():
        raise ValueError(f"navigation support missing: {path}")
    spec = importlib.util.spec_from_file_location(
        "kalaxy3_thin_slice_navigation_support",
        path,
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load navigation support: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, "source_url", None)):
        raise ValueError("navigation support must expose source_url")
    return module


def _catalog_by_id(root: Path) -> dict[str, Mapping[str, Any]]:
    """Return canonical evidence catalog records by evidence ID."""
    path = root / CATALOG
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    if not isinstance(records, list):
        raise ValueError("evidence catalog records must be a list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            continue
        if evidence_id in indexed:
            raise ValueError(f"duplicate evidence ID in catalog: {evidence_id}")
        indexed[evidence_id] = record
    return indexed


def _published_relative_url(source_path: str, navigation: Any) -> str:
    """Resolve one repository Markdown path to a URL relative to this page."""
    current = str(navigation.source_url(VIEW)).strip("/")
    target = str(navigation.source_url(source_path)).strip("/")
    if not current or not target:
        raise ValueError(
            f"navigation source_url returned empty path: {source_path}"
        )
    relative = posixpath.relpath(target, start=current)
    if not relative.endswith("/"):
        relative += "/"
    return relative


def _record_link(
    evidence_ref: str,
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> tuple[str, str, str] | None:
    """Resolve one evidence reference to label, URL, and canonical ID."""
    record = catalog.get(evidence_ref)
    if record is None:
        return None
    source_path = record.get("source_path")
    if not isinstance(source_path, str) or not source_path:
        raise ValueError(f"{evidence_ref}: catalog source_path missing")
    label = record.get("nav_title") or record.get("title") or evidence_ref
    return str(label), _published_relative_url(source_path, navigation), evidence_ref


def _evidence_html(
    evidence_refs: list[str],
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> str:
    """Render compact friendly evidence links for visual cards."""
    links: list[str] = []
    unresolved: list[str] = []
    for ref in evidence_refs:
        resolved = _record_link(ref, catalog, navigation)
        if resolved is None:
            unresolved.append(f"<code>{_escape(ref)}</code>")
            continue
        label, url, evidence_id = resolved
        links.append(
            '<a class="sage-evidence-link" '
            f'href="{_escape(url)}" '
            f'title="{_escape(evidence_id)}">'
            f'{_escape(label)}</a>'
        )
    values = links + unresolved
    if not values:
        return ""
    return (
        '<div class="sage-links"><strong>Evidence:</strong> '
        + " · ".join(values)
        + "</div>"
    )


def _source_relative_markdown_url(
    source_path: str,
    navigation: Any,
) -> str:
    """Resolve one canonical source to a Markdown-relative .md link."""
    current = navigation.source_relative_path(VIEW)
    target = navigation.source_relative_path(source_path)
    return posixpath.relpath(
        target.as_posix(),
        start=current.parent.as_posix(),
    )


def _evidence_markdown(
    evidence_refs: list[str],
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> str:
    """Render MkDocs-valid source links while preserving evidence IDs."""
    values: list[str] = []
    for ref in evidence_refs:
        record = catalog.get(ref)
        if record is None:
            values.append(f"`{ref}`")
            continue
        source_path = record.get("source_path")
        if not isinstance(source_path, str) or not source_path:
            raise ValueError(f"{ref}: catalog source_path missing")
        label = record.get("nav_title") or record.get("title") or ref
        url = _source_relative_markdown_url(source_path, navigation)
        values.append(f"[{label}]({url}) (`{ref}`)")
    return ", ".join(values)


def _repository_doc_url(
    root: Path,
    source_path: str,
    navigation: Any,
) -> str:
    """Require and resolve one canonical repository documentation page."""
    path = root / source_path
    if not path.is_file():
        raise ValueError(f"documentation provenance source missing: {source_path}")
    return _published_relative_url(source_path, navigation)


def _render_alternatives(value: Mapping[str, Any]) -> list[str]:
    lines = ["## Alternatives considered", "", "| Case | Disposition | Rationale |", "|---|---|---|"]
    for item in value["alternatives"]:
        lines.append(f"| `{item['case_id']}` | {item['disposition']} | {item['rationale']} |")
    return lines


def _render_trace(
    value: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> list[str]:
    lines = ["## End-to-end trace", ""]
    for item in value["end_to_end_trace"]:
        lines.extend([
            f"### {item['sequence']}. {item['title']}", "",
            f"**What happened:** {item['source_statement']}", "",
            f"**SAGE contribution:** {item['sage_contribution']}", "",
            f"**Human contribution:** {item['human_contribution']}", "",
            "**Evidence:** "
            + _evidence_markdown(item["evidence_refs"], catalog, navigation),
            "",
        ])
    return lines


def _render_measures(
    value: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> list[str]:
    lines = [
        "## Measured outcomes and open measurements",
        "",
        "| Measure | Target | Actual | Status | Evidence |",
        "|---|---:|---:|---|---|",
    ]
    for item in value["measures"]:
        actual = "unknown" if item["actual"] is None else str(item["actual"])
        refs = (
            _evidence_markdown(item["evidence_refs"], catalog, navigation)
            or "not yet available"
        )
        lines.append(
            f"| `{item['measure_id']}` | {item['target']} {item['unit']} | "
            f"{actual} | {item['status']} | {refs} |"
        )
    return lines


def _render_participation(value: Mapping[str, Any]) -> list[str]:
    lines = ["## How to participate", ""]
    for item in value["participation_paths"]:
        lines.extend([
            f"### {item['participant']}", "",
            item["entry_action"], "",
            f"**Authority boundary:** {item['authority']}", "",
        ])
    return lines


def _escape(value: object) -> str:
    """Escape deterministic model text for generated HTML."""
    return html.escape(str(value), quote=True)


def _visual_measure_value(item: Mapping[str, Any]) -> str:
    """Render one compact measure value."""
    actual = item.get("actual")
    if actual is None:
        return "Not measured"
    if isinstance(actual, bool):
        return "Yes" if actual else "No"
    unit = str(item.get("unit", "")).strip()
    return f"{actual} {unit}".strip()


def _render_visual_summary(
    value: Mapping[str, Any],
    catalog: Mapping[str, Mapping[str, Any]],
    navigation: Any,
) -> list[str]:
    """Render the newcomer-first decision-space visualization."""
    selected = value["selected_case"]
    measures = value["measures"]
    met = [item for item in measures if item.get("status") == "met"]
    unknown = [item for item in measures if item.get("status") == "not-measured"]
    trace = value["end_to_end_trace"]

    lines = [
        "<style>",
        ".sage-visual{margin:1.2rem 0 2rem 0}",
        ".sage-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:.8rem;margin:.8rem 0 1.2rem 0}",
        ".sage-card{border:1px solid var(--md-default-fg-color--lightest,#ddd);border-radius:10px;padding:1rem;background:var(--md-default-bg-color,#fff)}",
        ".sage-card h3{margin:.1rem 0 .45rem 0;font-size:1rem}",
        ".sage-kicker{font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;opacity:.7}",
        ".sage-big{font-size:1.55rem;font-weight:700;line-height:1.15;margin:.25rem 0}",
        ".sage-flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.6rem;margin:1rem 0 1.4rem 0}",
        ".sage-step{border-left:4px solid var(--md-primary-fg-color,#555);padding:.7rem .8rem;background:var(--md-code-bg-color,#f5f5f5);border-radius:6px}",
        ".sage-step strong{display:block;margin-bottom:.25rem}",
        ".sage-status{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:.08rem .5rem;font-size:.72rem;font-weight:700}",
        ".sage-muted{opacity:.72}",
        ".sage-role{font-size:.9rem;line-height:1.35}",
        ".sage-links{margin-top:.65rem;padding-top:.55rem;border-top:1px solid var(--md-default-fg-color--lightest,#ddd);font-size:.78rem;line-height:1.4}",
        ".sage-evidence-link{text-decoration:none;font-weight:600}",
        ".sage-provenance{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:.55rem;margin:.8rem 0 1.4rem 0}",
        ".sage-provenance .sage-step{min-height:7rem}",
        "</style>",
        '<div class="sage-visual">',
        '<div class="sage-grid">',
        '<div class="sage-card">',
        '<div class="sage-kicker">Architect&#x27;s Objective</div>',
        f'<div class="sage-big">{_escape(value["end_to_end_trace"][0]["source_statement"])}</div>',
        '<div class="sage-role"><strong>Decision authority:</strong> Operator</div>',
        '</div>',
        '<div class="sage-card">',
        '<div class="sage-kicker">SAGE contribution</div>',
        '<div class="sage-big">Govern the decision path</div>',
        '<div class="sage-role">Connect intent, authority, alternatives, evidence, failures, validation, and outcomes without taking authority away from people or source systems.</div>',
        '</div>',
        '<div class="sage-card">',
        '<div class="sage-kicker">Validated outcome</div>',
        f'<div class="sage-big">{len(met)} measured outcomes met</div>',
        f'<div class="sage-role">{len(unknown)} important learning measures remain explicitly open.</div>',
        '</div>',
        '</div>',
        '<div class="sage-card">',
        '<div class="sage-kicker">Core case evidence</div>',
        _evidence_html(selected["evidence_refs"], catalog, navigation),
        '</div>',
        '<h2>Decision path at a glance</h2>',
        '<div class="sage-flow">',
    ]
    for item in trace:
        lines.extend([
            '<div class="sage-step">',
            f'<span class="sage-kicker">Stage {item["sequence"]}</span>',
            f'<strong>{_escape(item["title"])}</strong>',
            f'<span class="sage-muted">{_escape(item["source_statement"])}</span>',
            _evidence_html(item["evidence_refs"], catalog, navigation),
            '</div>',
        ])
    lines.extend([
        '</div>',
        '<h2>Decision space</h2>',
        '<div class="sage-grid">',
    ])
    disposition_labels = {
        "retained-foundation": "Retained foundation",
        "deferred": "Deferred",
        "rejected": "Rejected",
    }
    for item in value["alternatives"]:
        disposition = str(item["disposition"])
        lines.extend([
            '<div class="sage-card">',
            f'<span class="sage-status">{_escape(disposition_labels.get(disposition, disposition))}</span>',
            f'<h3>{_escape(item["title"])}</h3>',
            f'<div class="sage-role">{_escape(item["rationale"])}</div>',
            '</div>',
        ])
    lines.extend([
        '</div>',
        '<h2>Outcome scorecard</h2>',
        '<div class="sage-grid">',
    ])
    for item in measures:
        label = "Met" if item["status"] == "met" else "Open"
        lines.extend([
            '<div class="sage-card">',
            f'<span class="sage-status">{_escape(label)}</span>',
            f'<div class="sage-kicker">{_escape(item["measure_id"])}</div>',
            f'<div class="sage-big">{_escape(_visual_measure_value(item))}</div>',
            f'<div class="sage-role">{_escape(item["description"])}</div>',
            _evidence_html(item["evidence_refs"], catalog, navigation),
            '</div>',
        ])
    lines.extend([
        '</div>',
        '<h2>Who contributes what?</h2>',
        '<div class="sage-grid">',
    ])
    for item in value["participation_paths"]:
        lines.extend([
            '<div class="sage-card">',
            f'<div class="sage-kicker">{_escape(item["participant"])}</div>',
            f'<h3>{_escape(item["entry_action"])}</h3>',
            f'<div class="sage-role"><strong>Authority:</strong> {_escape(item["authority"])}</div>',
            '</div>',
        ])
    lines.extend([
        '</div>',
        '</div>',
    ])
    return lines


def _render_documentation_provenance(
    root: Path,
    navigation: Any,
) -> list[str]:
    """Show how repository-owned SAGE machinery produced this documentation."""
    steps = (
        (
            "1 · Intent",
            "Preserve the architect's literal objective and determine applicable authority.",
            "markdown/standards/kalaxy3-sage-change-discovery-process.md",
            "Change discovery process",
        ),
        (
            "2 · Retrieval",
            "Retrieve prior evidence and lessons before proposing or correcting work.",
            "markdown/standards/kalaxy3-sage-evidence-retrieval-process.md",
            "Evidence retrieval process",
        ),
        (
            "3 · Composition",
            "Compose the centralized-logging case from governed SAGE state rather than hand-maintaining the story.",
            "markdown/standards/kalaxy3-sage-thin-slice-process.md",
            "Thin-slice process",
        ),
        (
            "4 · Visualization",
            "Generate this visual projection from the canonical thin-slice model and evidence catalog.",
            "markdown/standards/kalaxy3-sage-thin-slice-process.md",
            "Thin-slice rendering contract",
        ),
        (
            "5 · Validation",
            "Fail closed when source, authority, evidence, measured outcomes, or rendered-artifact contracts are violated.",
            "markdown/standards/kalaxy3-sage-thin-slice-process.md",
            "Thin-slice validation contract",
        ),
        (
            "6 · Publication",
            "Build and validate the page through the repository-owned MkDocs publication and navigation path.",
            "markdown/standards/kalaxy3-mkdocs-evidence-navigation-process.md",
            "MkDocs evidence navigation",
        ),
        (
            "7 · Reuse",
            "Keep evidence navigable and retrievable so later SAGE decisions can apply prior experience.",
            "markdown/standards/kalaxy3-sage-evidence-retrieval-process.md",
            "Evidence reuse contract",
        ),
    )
    lines = [
        "<h2>How SAGE helped produce this view</h2>",
        "<p>This page is itself a small SAGE case: the documentation is a governed projection of repository state, evidence, and validated publication machinery rather than a separately maintained narrative.</p>",
        '<div class="sage-provenance">',
    ]
    for kicker, statement, source_path, link_label in steps:
        url = _repository_doc_url(root, source_path, navigation)
        lines.extend([
            '<div class="sage-step">',
            f'<span class="sage-kicker">{_escape(kicker)}</span>',
            f'<strong>{_escape(statement)}</strong>',
            f'<a class="sage-evidence-link" href="{_escape(url)}">{_escape(link_label)}</a>',
            '</div>',
        ])
    lines.extend([
        "</div>",
        "<p><strong>Why this matters:</strong> the reader can follow the same chain SAGE used: objective → authority → retrieved experience → composition → validation → publication → reusable evidence.</p>",
    ])
    return lines


def render(value: Mapping[str, Any], root: Path = ROOT) -> str:
    selected = value["selected_case"]
    catalog = _catalog_by_id(root)
    navigation = _load_navigation_support(root)
    lines = [
        "# Kalaxy3 SAGE End-to-End Thin Slice", "",
        f"**Case:** {value['title']}", "",
        "## What SAGE is", "", value["introduction"], "",
        "## The question", "", value["case_question"], "",
    ]
    lines.extend(_render_visual_summary(value, catalog, navigation))
    lines.extend(_render_documentation_provenance(root, navigation))
    lines.extend([
        "",
        "## Why this case", "", selected["selection_rationale"], "",
        "Decision authority: **Operator**", "",
        "Core evidence: "
        + _evidence_markdown(selected["evidence_refs"], catalog, navigation),
        "",
        "## Detailed evidence trace", "",
        "The visual summary above is intentionally newcomer-first. The sections below preserve the deterministic review trace used to verify every stage, alternative, outcome, and authority boundary.", "",
    ])
    lines.extend(_render_alternatives(value))
    lines.extend([""] + _render_trace(value, catalog, navigation))
    lines.extend(_render_measures(value, catalog, navigation))
    lines.extend([""] + _render_participation(value))
    lines.extend(["## Reusable future capability", ""])
    lines.extend(f"- {item}" for item in value["future_capability"])
    lines.extend([
        "",
        "SAGE remains a federated decision partner. Repository, operator, runtime, and domain authorities retain their scoped authority.",
        "",
    ])
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> bool:
    normalized = content.rstrip() + "\n"
    if check:
        return path.is_file() and path.read_text(encoding="utf-8") == normalized
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(normalized, encoding="utf-8")
    return True


def self_test(
    value: Mapping[str, Any],
    root: Path = ROOT,
) -> list[str]:
    failures = validate(value)
    cases: list[tuple[dict[str, Any], str]] = []
    no_human = copy.deepcopy(value)
    no_human["end_to_end_trace"][0]["human_contribution"] = ""
    cases.append((no_human, "human contribution"))
    no_baseline = copy.deepcopy(value)
    no_baseline["alternatives"] = [
        item
        for item in no_baseline["alternatives"]
        if item["case_id"] != "do-nothing"
    ]
    cases.append((no_baseline, "do-nothing alternative"))
    fabricated = copy.deepcopy(value)
    fabricated["measures"][-1]["actual"] = 0
    cases.append((fabricated, "unavailable actual must be null"))
    no_evidence = copy.deepcopy(value)
    no_evidence["end_to_end_trace"][0]["evidence_refs"] = []
    cases.append((no_evidence, "requires evidence"))
    wrong_authority = copy.deepcopy(value)
    wrong_authority["selected_case"]["selection_authority_id"] = "sage-inference"
    cases.append((wrong_authority, "operator decision authority"))
    for candidate, expected in cases:
        observed = validate(candidate)
        if not any(expected in item for item in observed):
            failures.append(f"negative test missing {expected}: {observed}")

    try:
        catalog = _catalog_by_id(root)
        navigation = _load_navigation_support(root)
        selected_refs = value["selected_case"]["evidence_refs"]
        resolved_selected = [
            _record_link(ref, catalog, navigation)
            for ref in selected_refs
        ]
        if not all(resolved_selected):
            unresolved = [
                ref
                for ref, resolved in zip(selected_refs, resolved_selected)
                if resolved is None
            ]
            failures.append(
                f"selected-case evidence lacks catalog navigation: {unresolved}"
            )

        rendered = render(value, root)
        if "\\n" in rendered:
            failures.append(
                "rendered thin slice contains literal backslash-n sequences"
            )
        if rendered.count("\n") < 20:
            failures.append(
                "rendered thin slice must contain real line structure"
            )
        if "Architect&#x27;s Objective" not in rendered:
            failures.append(
                "rendered thin slice must expose Architect's Objective"
            )
        if "Human intent & authority" in rendered:
            failures.append(
                "rendered thin slice must not expose superseded human-objective label"
            )
        if ">operator-intent<" in rendered or "`operator-intent`" in rendered:
            failures.append(
                "rendered thin slice must not expose internal operator-intent identifier"
            )
        required_visual_markers = (
            "Decision path at a glance",
            "Decision space",
            "Outcome scorecard",
            "Who contributes what?",
            "How SAGE helped produce this view",
            "Detailed evidence trace",
        )
        for marker in required_visual_markers:
            if marker not in rendered:
                failures.append(
                    f"rendered thin slice missing visual marker: {marker}"
                )
        if rendered.count('class="sage-evidence-link"') < len(selected_refs):
            failures.append(
                "rendered thin slice lacks expected navigable evidence links"
            )
        for ref in selected_refs:
            record = catalog.get(ref)
            if record is None:
                continue
            source_path = record.get("source_path")
            if not isinstance(source_path, str) or not source_path:
                failures.append(
                    f"{ref}: selected evidence source_path missing"
                )
                continue
            expected_link = _source_relative_markdown_url(
                source_path,
                navigation,
            )
            if not expected_link.endswith(".md"):
                failures.append(
                    f"{ref}: Markdown evidence link must retain .md source suffix"
                )
            if f"]({expected_link})" not in rendered:
                failures.append(
                    f"{ref}: rendered Markdown source link missing: {expected_link}"
                )
        for required_path in (
            "markdown/standards/kalaxy3-sage-change-discovery-process.md",
            "markdown/standards/kalaxy3-sage-evidence-retrieval-process.md",
            "markdown/standards/kalaxy3-sage-thin-slice-process.md",
            "markdown/standards/kalaxy3-mkdocs-evidence-navigation-process.md",
        ):
            _repository_doc_url(root, required_path, navigation)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        failures.append(f"navigable provenance validation failed: {error}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("check", "render", "metrics", "self-test"))
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = load(args.repo)
    failures = validate(value)
    if failures:
        print("SAGE thin slice: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    if args.command == "check":
        print("SAGE thin-slice model: PASS")
        return 0
    if args.command == "render":
        if not write_or_check(args.repo / VIEW, render(value, args.repo), args.check):
            print("Rendered thin-slice view differs")
            return 1
        print("SAGE thin-slice render: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    if args.command == "metrics":
        content = json.dumps(metrics(value), indent=2, ensure_ascii=False)
        if not write_or_check(args.repo / METRICS, content, args.check):
            print("Thin-slice metrics snapshot differs")
            return 1
        print("SAGE thin-slice metrics: " + ("CURRENT" if args.check else "WRITTEN"))
        return 0
    failures = self_test(value, args.repo)
    if failures:
        print("SAGE thin-slice self-test: FAIL CLOSED")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS selected real case and alternatives")
    print("PASS source, SAGE, and human-contribution separation")
    print("PASS measured outcomes and explicit unknowns")
    print("PASS participation and reusable-capability paths")
    print("PASS authority, evidence, and do-nothing negative tests")
    print("SAGE thin-slice self-test: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
