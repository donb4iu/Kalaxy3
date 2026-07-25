#!/usr/bin/env python3
"""Generate a backward-compatible Kalaxy3 SAGE evidence catalog.

The indexer never rewrites source evidence records. It classifies current SAGE,
legacy SAGE, and pre-SAGE Markdown, applies optional curated registry metadata,
and writes deterministic human- and machine-readable navigation artifacts.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

CURRENT_SCHEMA = "1.2"
CATALOG_SCHEMA = "1.0"
REGISTRY_PATH = "markdown/evidence/legacy-record-registry.json"
GENERATED_MANIFEST = "markdown/evidence/generated-files.json"
GENERATED_ROOT = "markdown/evidence"
ALLOWED_NAV_SECTIONS = {
    "installation",
    "operations",
    "architecture",
    "decisions",
    "finops",
    "governance",
    "security",
    "incidents",
    "experiments",
    "benchmarks",
    "verification",
    "other",
}
DEFAULT_CANDIDATE_ROOTS = [
    "markdown/installation",
    "markdown/operations",
    "markdown/architecture",
    "markdown/decisions",
    "markdown/finops",
    "markdown/security",
    "markdown/incidents",
    "markdown/experiments",
    "markdown/benchmarks",
    "markdown/verification",
]
EXCLUDED_PREFIXES = {
    "markdown/standards",
    "markdown/templates",
    "markdown/evidence-artifacts",
    "markdown/evidence",
}
EVIDENCE_ID_RE = re.compile(r"^SAGE-K3-[A-Z0-9-]+-\d{8}-\d{3}$")
LEGACY_ID_RE = re.compile(r"^LEGACY-K3-[A-F0-9]{10}$")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


class IndexError(RuntimeError):
    pass


def run(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        detail = "\n".join(x for x in [proc.stdout.strip(), proc.stderr.strip()] if x)
        raise IndexError(f"Command failed ({proc.returncode}): {' '.join(args)}\n{detail}")
    return proc


def repo_root(value: str | None) -> Path:
    start = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    proc = run(["git", "rev-parse", "--show-toplevel"], cwd=start)
    return Path(proc.stdout.strip()).resolve()


def safe_repo_path(value: str) -> str:
    p = PurePosixPath(value)
    if p.is_absolute() or not p.parts or any(part in {"", ".", ".."} for part in p.parts):
        raise IndexError(f"Unsafe repository path: {value!r}")
    return p.as_posix()


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "other"


def strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_>#]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_loose_frontmatter(text: str) -> tuple[dict[str, str], dict[str, list[str]], str]:
    if not text.startswith("---\n"):
        return {}, {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, {}, text
    block = text[4:end]
    body = text[end + 5 :]
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        top = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*):(?:\s*(.*))?", line)
        if top:
            current = top.group(1)
            raw = (top.group(2) or "").strip()
            if raw:
                if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
                    raw = raw[1:-1]
                scalars[current] = raw
            else:
                lists.setdefault(current, [])
            continue
        item = re.fullmatch(r"\s{2}-\s+(.+)", line)
        if item and current:
            raw = item.group(1).strip()
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
                raw = raw[1:-1]
            lists.setdefault(current, []).append(raw)
    return scalars, lists, body


def first_heading(body: str) -> str | None:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    return strip_markdown(match.group(1)) if match else None


def section(body: str, heading: str) -> str:
    match = re.search(rf"(?m)^{re.escape(heading)}\s*$", body)
    if not match:
        return ""
    tail = body[match.end() :]
    next_heading = re.search(r"(?m)^##\s+", tail)
    return tail[: next_heading.start()] if next_heading else tail


def first_prose_paragraph(body: str) -> str | None:
    exec_summary = section(body, "## Executive summary")
    candidates = [exec_summary, body]
    for text in candidates:
        for block in re.split(r"\n\s*\n", text):
            cleaned = block.strip()
            if not cleaned:
                continue
            if cleaned.startswith(("#", "|", "```", "---", "[TOC]", "<!--")):
                continue
            cleaned = strip_markdown(cleaned)
            if cleaned:
                return cleaned
    return None


def humanize_filename(path: str) -> str:
    stem = Path(path).stem
    stem = re.sub(r"^\d+[-_]", "", stem)
    words = re.sub(r"[-_]+", " ", stem).strip()
    return " ".join(word.upper() if word.lower() in {"k3s", "gpu", "nfs", "api", "ui", "aws", "sage"} else word for word in words.split())


def concise_nav_title(title: str, path: str) -> str:
    value = title or humanize_filename(path)
    substitutions = [
        (r"(?i)^kalaxy3\s*[:—-]?\s*", ""),
        (r"(?i)\bsage\b", ""),
        (r"(?i)\bevidence record\b", ""),
        (r"(?i)\binstallation evidence\b", "installation"),
        (r"(?i)\bverification evidence\b", "verification"),
        (r"(?i)\bevidence\b", ""),
    ]
    for pattern, replacement in substitutions:
        value = re.sub(pattern, replacement, value)
    value = re.sub(r"\s+", " ", value).strip(" :-—")
    if not value:
        value = humanize_filename(path)
    if len(value) > 80:
        value = value[:77].rstrip() + "..."
    return value


def infer_section(path: str, record_type: str | None = None) -> str:
    if record_type:
        mapping = {
            "installation": "installation",
            "operations": "operations",
            "architecture-decision": "decisions",
            "change": "operations",
            "verification": "verification",
            "incident": "incidents",
            "experiment": "experiments",
            "benchmark": "benchmarks",
            "security": "security",
            "finops": "finops",
        }
        if record_type in mapping:
            return mapping[record_type]
    parts = PurePosixPath(path).parts
    if len(parts) > 1 and parts[1] in ALLOWED_NAV_SECTIONS:
        return parts[1]
    return "other"


def infer_subject(title: str, components: list[str]) -> str:
    if components and components != ["not-applicable"]:
        return components[0].split("=", 1)[0]
    cleaned = re.sub(r"(?i)^kalaxy3\s*[:—-]?\s*", "", title).strip()
    token = re.split(r"[:—-]|\band\b|\bwith\b", cleaned, maxsplit=1, flags=re.I)[0]
    return token.strip() or "Kalaxy3"


def deterministic_legacy_id(path: str) -> str:
    digest = hashlib.sha256(path.encode("utf-8")).hexdigest()[:10].upper()
    return f"LEGACY-K3-{digest}"


def git_dates(repo: Path, path: str) -> tuple[str, str]:
    proc = run(
        ["git", "log", "--follow", "--format=%aI", "--", path],
        cwd=repo,
        check=False,
    )
    values = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not values:
        return "not-captured", "not-captured"
    return values[-1], values[0]


def static_header_value(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^\s*{re.escape(label)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def load_registry(repo: Path) -> dict[str, Any]:
    path = repo / REGISTRY_PATH
    if not path.is_file():
        return {
            "registry_version": "1.0",
            "candidate_roots": DEFAULT_CANDIDATE_ROOTS,
            "exclude_paths": [],
            "records": [],
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IndexError(f"Invalid legacy registry JSON: {exc}") from exc
    if data.get("registry_version") != "1.0":
        raise IndexError("legacy-record-registry.json registry_version must be 1.0")
    for key in ["candidate_roots", "exclude_paths", "records"]:
        if key not in data or not isinstance(data[key], list):
            raise IndexError(f"Legacy registry field {key!r} must be a list")
    return data


def registry_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in registry["records"]:
        if not isinstance(item, dict) or not isinstance(item.get("source_path"), str):
            raise IndexError("Each legacy registry record needs source_path")
        path = safe_repo_path(item["source_path"])
        if path in result:
            raise IndexError(f"Duplicate legacy registry source_path: {path}")
        result[path] = item
    return result


def discover_paths(repo: Path, registry: dict[str, Any]) -> list[str]:
    excluded = {safe_repo_path(x) for x in registry.get("exclude_paths", [])}
    roots = [safe_repo_path(x) for x in registry.get("candidate_roots", DEFAULT_CANDIDATE_ROOTS)]
    found: set[str] = set()

    for root in roots:
        base = repo / root
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            rel = path.relative_to(repo).as_posix()
            if rel not in excluded:
                found.add(rel)

    # Current and older SAGE records can live outside configured roots.
    markdown = repo / "markdown"
    if markdown.exists():
        for path in markdown.rglob("*.md"):
            rel = path.relative_to(repo).as_posix()
            if rel in excluded or any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDED_PREFIXES):
                continue
            try:
                head = path.read_text(encoding="utf-8")[:8192]
            except UnicodeDecodeError:
                continue
            if re.search(r"(?m)^evidence_id:\s*(?:SAGE-K3-|LEGACY-K3-)", head):
                found.add(rel)

    for item in registry.get("records", []):
        if item.get("include", True):
            found.add(safe_repo_path(item["source_path"]))
        else:
            found.discard(safe_repo_path(item["source_path"]))

    return sorted(found)


def normalize_date(value: str) -> str:
    match = DATE_RE.search(value or "")
    return match.group(0) if match else "not-captured"


def build_entry(repo: Path, path: str, override: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    source = repo / path
    if not source.is_file():
        raise IndexError(f"Cataloged evidence path does not exist: {path}")
    text = source.read_text(encoding="utf-8")
    scalars, lists, body = parse_loose_frontmatter(text)
    schema = scalars.get("schema_version", "not-applicable")
    evidence_id = scalars.get("evidence_id")

    if schema == CURRENT_SCHEMA and evidence_id and EVIDENCE_ID_RE.fullmatch(evidence_id):
        record_class = "sage-current"
        metadata_source = "authoritative"
        migration_status = "current"
        required = ["nav_title", "nav_section", "nav_order", "summary", "primary_subject"]
        missing = [key for key in required if not scalars.get(key)]
        if missing:
            raise IndexError(f"Current SAGE record {path} lacks navigation fields: {missing}")
    elif evidence_id and EVIDENCE_ID_RE.fullmatch(evidence_id):
        record_class = "sage-legacy"
        metadata_source = "curated" if override else "inferred"
        migration_status = "recommended"
    else:
        record_class = "legacy-evidence"
        evidence_id = deterministic_legacy_id(path)
        metadata_source = "curated" if override else "inferred"
        migration_status = "not-started"

    override = override or {}
    if override.get("evidence_id"):
        evidence_id = override["evidence_id"]
    if not (EVIDENCE_ID_RE.fullmatch(evidence_id) or LEGACY_ID_RE.fullmatch(evidence_id)):
        raise IndexError(f"Invalid catalog evidence ID for {path}: {evidence_id}")

    title = override.get("title") or scalars.get("title") or first_heading(body) or humanize_filename(path)
    nav_title = override.get("nav_title") or scalars.get("nav_title") or concise_nav_title(title, path)
    nav_section = override.get("nav_section") or scalars.get("nav_section") or infer_section(path, scalars.get("record_type"))
    if nav_section not in ALLOWED_NAV_SECTIONS:
        raise IndexError(f"Invalid nav_section {nav_section!r} for {path}")
    raw_order = override.get("nav_order", scalars.get("nav_order", 500))
    try:
        nav_order = int(raw_order)
    except (TypeError, ValueError) as exc:
        raise IndexError(f"nav_order must be an integer for {path}") from exc
    if not 0 <= nav_order <= 9999:
        raise IndexError(f"nav_order outside 0..9999 for {path}")
    summary = override.get("summary") or scalars.get("summary") or first_prose_paragraph(body) or f"Historical Kalaxy3 record preserved at {path}."
    summary = strip_markdown(summary)
    if len(summary) > 360:
        summary = summary[:357].rstrip() + "..."
    components = lists.get("components", [])
    primary_subject = override.get("primary_subject") or scalars.get("primary_subject") or infer_subject(title, components)
    status = override.get("status") or scalars.get("status") or "historical"
    valid_as_of = override.get("valid_as_of") or scalars.get("valid_as_of")
    completed_at = override.get("completed_at") or scalars.get("work_completed_at") or static_header_value(text, "Completed")
    created_git, modified_git = git_dates(repo, path)
    if not completed_at:
        completed_at = modified_git
    if not valid_as_of:
        valid_as_of = normalize_date(completed_at)
    owner = override.get("owner") or scalars.get("owner") or "not-captured"
    confidence = override.get("confidence") or scalars.get("confidence") or ("medium" if metadata_source == "curated" else "low")
    migration_status = override.get("migration_status", migration_status)
    tags = override.get("tags") or lists.get("tags", [])
    if not isinstance(tags, list):
        raise IndexError(f"tags override must be a list for {path}")

    if record_class != "sage-current":
        warnings.append(f"LEGACY: {path} indexed as {record_class} with {metadata_source} metadata")
    if metadata_source == "inferred":
        warnings.append(f"CURATION: {path} needs registry review")

    return {
        "evidence_id": evidence_id,
        "record_class": record_class,
        "schema_version": schema,
        "title": title,
        "nav_title": nav_title,
        "nav_section": nav_section,
        "nav_order": nav_order,
        "summary": summary,
        "primary_subject": primary_subject,
        "source_path": path,
        "status": status,
        "valid_as_of": valid_as_of,
        "completed_at": completed_at,
        "owner": owner,
        "metadata_source": metadata_source,
        "migration_status": migration_status,
        "confidence": confidence,
        "tags": tags,
    }, warnings


def validate_entries(entries: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    ids: dict[str, str] = {}
    current_titles: dict[tuple[str, str], str] = {}
    for entry in entries:
        evidence_id = entry["evidence_id"]
        if evidence_id in ids:
            raise IndexError(f"Duplicate evidence_id {evidence_id}: {ids[evidence_id]} and {entry['source_path']}")
        ids[evidence_id] = entry["source_path"]
        if len(entry["nav_title"]) > 80:
            raise IndexError(f"nav_title exceeds 80 characters: {entry['source_path']}")
        key = (entry["nav_section"], entry["nav_title"].casefold())
        if entry["record_class"] == "sage-current":
            if key in current_titles:
                raise IndexError(
                    f"Duplicate current nav_title in section {entry['nav_section']}: "
                    f"{current_titles[key]} and {entry['source_path']}"
                )
            current_titles[key] = entry["source_path"]
    return warnings


def md_link(entry: dict[str, Any], from_dir: str = "markdown/evidence") -> str:
    # Catalog files live two levels or more below repo root. Absolute site paths
    # are not portable across Daux and MkDocs, so use repository-relative paths.
    target = PurePosixPath(entry["source_path"])
    base = PurePosixPath(from_dir)
    common = 0
    for left, right in zip(base.parts, target.parts):
        if left != right:
            break
        common += 1
    rel_parts = [".."] * (len(base.parts) - common) + list(target.parts[common:])
    return "/".join(rel_parts)


def table(entries: list[dict[str, Any]], from_dir: str) -> str:
    lines = [
        "| Section | Record | Summary | Class | Status | Valid as of |",
        "|---|---|---|---|---|---|",
    ]
    for entry in entries:
        link = md_link(entry, from_dir)
        summary = entry["summary"].replace("|", "\\|")
        lines.append(
            f"| {entry['nav_section']} | [{entry['nav_title']}]({link}) | {summary} | "
            f"{entry['record_class']} | {entry['status']} | {entry['valid_as_of']} |"
        )
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def generate_outputs(repo: Path, entries: list[dict[str, Any]], warnings: list[str]) -> tuple[dict[str, str], list[str]]:
    generated: dict[str, str] = {}
    current = [e for e in entries if e["record_class"] == "sage-current"]
    legacy = [e for e in entries if e["record_class"] != "sage-current"]
    current_sorted = sorted(current, key=lambda e: (e["nav_section"], e["nav_order"], e["nav_title"].casefold()))
    legacy_sorted = sorted(legacy, key=lambda e: (e["nav_section"], e["nav_title"].casefold()))
    recent = sorted(entries, key=lambda e: (e["valid_as_of"], e["completed_at"]), reverse=True)

    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry["record_class"]] = counts.get(entry["record_class"], 0) + 1

    index = f'''# Kalaxy3 evidence catalog

[TOC]

This catalog is generated by `scripts/sage/sage-index.py`. Source evidence is
never rewritten during reconciliation. Current SAGE records use authoritative
schema 1.2 navigation metadata. Older SAGE and pre-SAGE records remain visible
with curated or inferred metadata and an explicit migration state.

## Catalog summary

| Classification | Count |
|---|---:|
{chr(10).join(f"| {key} | {counts[key]} |" for key in sorted(counts))}
| **Total** | **{len(entries)}** |

## Start here

{table(recent[:12], 'markdown/evidence') if recent else 'No evidence records were discovered.'}

## Browse

- [Current SAGE records](current.md)
- [Historical and legacy evidence](legacy.md)
- [Migration report](migration-report.md)
- [Section indexes](sections/index.md)
- [Subject indexes](subjects/index.md)
- [Status indexes](status/index.md)
- [Machine-readable JSON catalog](catalog.json)
- [CSV catalog](catalog.csv)

## Preservation rule

A newer SAGE schema must not make historical evidence undiscoverable,
unpublished, or invalid merely because it predates the schema. Historical
records remain preserved, classified, indexed, and assigned explicit metadata
provenance. Migration is deliberate, reviewable, and non-destructive.
'''
    generated["markdown/evidence/index.md"] = index

    generated["markdown/evidence/current.md"] = f'''# Current SAGE evidence

[TOC]

These records conform to schema {CURRENT_SCHEMA} and use authoritative
navigation metadata.

{table(current_sorted, 'markdown/evidence') if current_sorted else 'No current SAGE records were discovered.'}
'''
    generated["markdown/evidence/legacy.md"] = f'''# Historical and legacy evidence

[TOC]

These records predate the current SAGE schema or do not yet contain a SAGE
front matter contract. They remain preserved and searchable. Curated metadata
comes from `{REGISTRY_PATH}`; inferred metadata is explicitly identified and
should be reviewed before migration.

{table(legacy_sorted, 'markdown/evidence') if legacy_sorted else 'No legacy records were discovered.'}
'''

    migration_rows = [
        "| Record | Class | Metadata | Migration status | Primary gap |",
        "|---|---|---|---|---|",
    ]
    for entry in legacy_sorted:
        gap = "Curate title, summary, dates, and ownership" if entry["metadata_source"] == "inferred" else "Review and migrate deliberately"
        migration_rows.append(
            f"| [{entry['nav_title']}]({md_link(entry, 'markdown/evidence')}) | "
            f"{entry['record_class']} | {entry['metadata_source']} | "
            f"{entry['migration_status']} | {gap} |"
        )
    warning_lines = "\n".join(f"- {warning}" for warning in sorted(set(warnings))) or "- None"
    generated["markdown/evidence/migration-report.md"] = f'''# SAGE evidence migration report

[TOC]

This report is generated. It does not modify historical records or assert that
inferred metadata was present in the original evidence.

## Legacy migration queue

{chr(10).join(migration_rows) if legacy_sorted else 'No legacy migration candidates.'}

## Reconciliation warnings

{warning_lines}

## Migration rule

A legacy record becomes current SAGE evidence only after its source evidence is
reviewed, missing metadata is explicitly supplied, claims and evidence are
separated, limitations are documented, and the migration is reviewed. The
historical source remains preserved and is linked through supersession
relationships.
'''

    sections = sorted({e["nav_section"] for e in entries})
    generated["markdown/evidence/sections/index.md"] = "# Evidence by section\n\n" + "\n".join(
        f"- [{section.title()}]({slugify(section)}.md)" for section in sections
    ) + "\n"
    for section_name in sections:
        subset = sorted(
            [e for e in entries if e["nav_section"] == section_name],
            key=lambda e: (e["nav_order"], e["nav_title"].casefold()),
        )
        generated[f"markdown/evidence/sections/{slugify(section_name)}.md"] = (
            f"# {section_name.title()} evidence\n\n[TOC]\n\n" + table(subset, "markdown/evidence/sections") + "\n"
        )

    subjects = sorted({e["primary_subject"] for e in entries}, key=str.casefold)
    generated["markdown/evidence/subjects/index.md"] = "# Evidence by subject\n\n" + "\n".join(
        f"- [{subject}]({slugify(subject)}.md)" for subject in subjects
    ) + "\n"
    for subject in subjects:
        subset = sorted(
            [e for e in entries if e["primary_subject"] == subject],
            key=lambda e: (e["nav_section"], e["nav_order"], e["nav_title"].casefold()),
        )
        generated[f"markdown/evidence/subjects/{slugify(subject)}.md"] = (
            f"# Evidence for {subject}\n\n[TOC]\n\n" + table(subset, "markdown/evidence/subjects") + "\n"
        )

    statuses = sorted({e["status"] for e in entries})
    generated["markdown/evidence/status/index.md"] = "# Evidence by status\n\n" + "\n".join(
        f"- [{status}]({slugify(status)}.md)" for status in statuses
    ) + "\n"
    for status in statuses:
        subset = sorted(
            [e for e in entries if e["status"] == status],
            key=lambda e: (e["nav_section"], e["nav_order"], e["nav_title"].casefold()),
        )
        generated[f"markdown/evidence/status/{slugify(status)}.md"] = (
            f"# {status.title()} evidence\n\n[TOC]\n\n" + table(subset, "markdown/evidence/status") + "\n"
        )

    catalog_fingerprint = hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    catalog = {
        "catalog_schema_version": CATALOG_SCHEMA,
        "sage_current_schema": CURRENT_SCHEMA,
        "catalog_fingerprint": catalog_fingerprint,
        "registry_path": REGISTRY_PATH,
        "record_count": len(entries),
        "records": entries,
        "warnings": sorted(set(warnings)),
    }
    generated["markdown/evidence/catalog.json"] = json.dumps(catalog, indent=2, sort_keys=True) + "\n"

    buffer = io.StringIO()
    fields = [
        "evidence_id",
        "record_class",
        "schema_version",
        "nav_section",
        "nav_order",
        "nav_title",
        "primary_subject",
        "summary",
        "status",
        "valid_as_of",
        "completed_at",
        "owner",
        "metadata_source",
        "migration_status",
        "confidence",
        "source_path",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(entries)
    generated["markdown/evidence/catalog.csv"] = buffer.getvalue()

    previous_paths: list[str] = []
    manifest_path = repo / GENERATED_MANIFEST
    if manifest_path.is_file():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous_paths = [safe_repo_path(x) for x in previous.get("generated_paths", [])]
        except (json.JSONDecodeError, IndexError):
            previous_paths = []
    final_paths = sorted([*generated.keys(), GENERATED_MANIFEST])
    stale = sorted(set(previous_paths) - set(final_paths))
    generated[GENERATED_MANIFEST] = json.dumps(
        {
            "generated_files_schema": "1.0",
            "generated_by": "scripts/sage/sage-index.py",
            "generated_paths": final_paths,
            "removed_paths": stale,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    return generated, stale


def reconcile(repo: Path, *, write: bool) -> tuple[list[dict[str, Any]], list[str], list[str], list[str]]:
    registry = load_registry(repo)
    overrides = registry_map(registry)
    paths = discover_paths(repo, registry)
    entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    for path in paths:
        entry, item_warnings = build_entry(repo, path, overrides.get(path))
        entries.append(entry)
        warnings.extend(item_warnings)
    warnings.extend(validate_entries(entries))
    entries = sorted(entries, key=lambda e: (e["nav_section"], e["nav_order"], e["nav_title"].casefold()))
    generated, stale = generate_outputs(repo, entries, warnings)

    changed: list[str] = []
    if write:
        for rel in stale:
            path = repo / rel
            if path.is_file():
                path.unlink()
                changed.append(rel)
        for rel, content in generated.items():
            path = repo / rel
            old = path.read_text(encoding="utf-8") if path.is_file() else None
            if old != content:
                write_text(path, content)
                changed.append(rel)
    else:
        for rel, content in generated.items():
            path = repo / rel
            old = path.read_text(encoding="utf-8") if path.is_file() else None
            if old != content:
                changed.append(rel)
        changed.extend(stale)
    return entries, sorted(set(warnings)), sorted(set(changed)), sorted(set(generated.keys()) | set(stale))


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile Kalaxy3 SAGE and legacy evidence navigation")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["check", "reconcile"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--repo", help="repository path; defaults to current Git repository")
    args = parser.parse_args()
    try:
        repo = repo_root(args.repo)
        entries, warnings, changed, generated_paths = reconcile(repo, write=args.command == "reconcile")
        if args.command == "check" and changed:
            raise IndexError(
                "Generated evidence catalog is stale. Run: "
                "python3 scripts/sage/sage-index.py reconcile\nChanged paths: "
                + ", ".join(changed)
            )
        print(f"SAGE evidence reconciliation: PASS")
        print(f"Records:          {len(entries)}")
        print(f"Generated paths:  {len(generated_paths)}")
        print(f"Changed paths:    {len(changed)}")
        for warning in warnings:
            print(warning, file=sys.stderr)
        return 0
    except (IndexError, OSError, UnicodeError) as exc:
        print(f"SAGE evidence reconciliation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
