#!/usr/bin/env python3
"""Render a plain-language, read-only projection of SAGE PR work evidence."""

from __future__ import annotations

import argparse
import html
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "sage-pr-work-thread-v1"


class ProjectionError(ValueError):
    """Indicate an invalid or unsupported work-thread record."""


def text(value: Any) -> str:
    """Escape one value for safe inclusion in HTML.

    Args:
        value: Untrusted field from an evidence record.
    """
    return html.escape(str(value), quote=True)


def required_string(data: Mapping[str, Any], key: str) -> str:
    """Read a nonempty text field without coercing structured objects.

    Args:
        data: Parsed source record.
        key: Required field name.
    """
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProjectionError(f"Missing or invalid {key}")
    return value.strip()


def text_items(value: Any, limit: int = 20) -> list[str]:
    """Validate a bounded list of readable descriptions.

    Args:
        value: Untrusted list value.
        limit: Maximum number of entries.
    """
    if not isinstance(value, list) or len(value) > limit:
        raise ProjectionError("Expected a bounded list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ProjectionError("List entries must be nonempty text")
    return [item.strip() for item in value]


def validate_thread(value: Any) -> dict[str, Any]:
    """Validate the 80/20 dashboard contract without asserting authority.

    Args:
        value: Parsed JSON work-thread candidate.
    """
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ProjectionError("Unsupported work-thread schema")
    objective = value.get("objective")
    if not isinstance(objective, dict):
        raise ProjectionError("Missing objective")
    for key in ("id", "title", "intent"):
        required_string(objective, key)
    milestone = value.get("milestone")
    if not isinstance(milestone, dict):
        raise ProjectionError("Missing milestone")
    for key in ("id", "title", "proposal"):
        required_string(milestone, key)
    work = value.get("work", {})
    if not isinstance(work, dict):
        raise ProjectionError("Invalid work state")
    for key in ("done", "doing", "next", "blocked"):
        text_items(work.get(key, []))
    for key in ("inquiries", "iterations", "raci", "learnings", "concepts"):
        entries = value.get(key, [])
        if not isinstance(entries, list) or len(entries) > 30:
            raise ProjectionError(f"Invalid or unbounded {key}")
        if any(not isinstance(item, dict) for item in entries):
            raise ProjectionError(f"Invalid entry in {key}")
    return value


def inquiry_summary(record: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve inquiry occurrence and recorded outputs without claiming coverage.

    Args:
        record: One untrusted prior-art inquiry observation.
    """
    return {
        "question": required_string(record, "question"),
        "recorded_results": text_items(record.get("results", [])),
        "unresolved": text_items(record.get("gaps", [])),
        "receipt_sha256": record.get("receipt_sha256"),
        "record_authenticity": "not_verified_by_projection",
    }


def project(thread: Mapping[str, Any],
            verified_inquiry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Convert raw work-thread content into a non-authorizing dashboard model.

    Args:
        thread: Schema-validated PR work-thread description.
        verified_inquiry: Optional independently verified provenance result.
    """
    return {
        "schema": "sage-architecture-work-projection-v1",
        "source_schema": SCHEMA,
        "objective": thread["objective"],
        "milestone": thread["milestone"],
        "work": thread.get("work", {}),
        "inquiries": [dict(inquiry_summary(item), record_authenticity=(
            "signature_valid_against_supplied_key" if verified_inquiry else
            "not_verified_by_projection")) for item in thread.get("inquiries", [])],
        "inquiry_attestation": dict(verified_inquiry or {}),
        "iterations": thread.get("iterations", []),
        "raci": thread.get("raci", []),
        "learnings": thread.get("learnings", []),
        "concepts": thread.get("concepts", []),
        "authority": "untrusted_projection_not_an_approval_or_a_signed_receipt",
        "gate": ("inquiry_record_attested_not_approved" if verified_inquiry else
                 "not_qualified; independent signed evidence verification required"),
    }


def pills(items: Sequence[str], empty: str = "None recorded") -> str:
    """Render a compact accessible list of plain-language facts.

    Args:
        items: Text items, not trusted HTML.
        empty: Placeholder for absent content.
    """
    if not items:
        return f"<p class='muted'>{text(empty)}</p>"
    return "<ul>" + "".join(f"<li>{text(item)}</li>" for item in items) + "</ul>"


def card(title: str, content: str, subtitle: str = "") -> str:
    """Wrap trusted, internally generated HTML in a dashboard card.

    Args:
        title: Plain-text heading.
        content: Already-escaped internal HTML fragment.
        subtitle: Optional plain-text description.
    """
    hint = f"<p class='muted'>{text(subtitle)}</p>" if subtitle else ""
    return f"<section class='card'><h2>{text(title)}</h2>{hint}{content}</section>"


def inquiry_cards(inquiries: Sequence[Mapping[str, Any]]) -> str:
    """Describe recorded queries, returned prior art, and unresolved questions.

    Args:
        inquiries: Untrusted observations, explicitly not verified here.
    """
    if not inquiries:
        return card("What did we look up?", "<p>No inquiry record supplied.</p>",
                    "Absence of evidence is not evidence that no prior art exists")
    output = ""
    for item in inquiries:
        content = f"<h3>{text(item['question'])}</h3>"
        content += "<strong>Returned</strong>" + pills(item["recorded_results"], "No results recorded")
        content += "<strong>Still uncertain</strong>" + pills(item["unresolved"])
        authenticity = item.get("record_authenticity", "not_verified_by_projection")
        content += f"<p class='muted'>Evidence status: {text(authenticity)}</p>"
        output += content
    return card("What did we look up?", output,
                "A recorded search is not a guarantee of complete or correct retrieval")


def timeline_card(iterations: Sequence[Mapping[str, Any]]) -> str:
    """Render the Architect/RFP iteration history as normal language.

    Args:
        iterations: Bounded sequence of proposed or observed revisions.
    """
    if not iterations:
        return card("What changed after discussion?", pills([]))
    output = "<ol class='timeline'>"
    for item in iterations:
        who = text(item.get("actor", "Unattributed"))
        question = text(item.get("question", "No question recorded"))
        change = text(item.get("change", "No change recorded"))
        output += f"<li><strong>{who}</strong><p>{question}</p><p>→ {change}</p></li>"
    return card("What changed after discussion?", output + "</ol>")


def raci_card(items: Sequence[Mapping[str, Any]]) -> str:
    """Render role progress without interpreting invocation as qualification.

    Args:
        items: Existing RACI role descriptions and reported dispositions.
    """
    if not items:
        return card("Who has reviewed it?", pills([]), "No qualified RACI evidence supplied")
    output = "<ul>"
    for item in items:
        role = text(item.get("role", "Unknown role"))
        state = text(item.get("state", "Not evidenced"))
        output += f"<li><strong>{role}:</strong> {state} (reported, not authenticated)</li>"
    return card("Who has reviewed it?", output + "</ul>")


def concept_card(items: Sequence[Mapping[str, Any]]) -> str:
    """Show knowledge-model relationships in language fit for an Architect.

    Args:
        items: Candidate concept relationships and their source descriptions.
    """
    if not items:
        return card("Where does this fit?", pills([]),
                    "No concept-to-milestone relationships supplied")
    output = "<ul>"
    for item in items:
        title = text(item.get("name", "Unknown capability"))
        state = text(item.get("state", "Unknown"))
        evidence = text(item.get("evidence", "No source cited"))
        output += f"<li><strong>{title}</strong>: {state}<p class='muted'>{evidence}</p></li>"
    return card("Where does this fit?", output + "</ul>",
                "Candidate relationships; the semantic collection remains authoritative")


def html_page(projection: Mapping[str, Any]) -> str:
    """Produce a standalone accessible snapshot for architecture dashboard ingestion.

    Args:
        projection: Structured, non-authorizing dashboard projection.
    """
    objective = projection["objective"]
    milestone = projection["milestone"]
    work = projection["work"]
    status = card("Where are we?", "<strong>Completed (reported)</strong>" + pills(work.get("done", []))
                  + "<strong>In progress</strong>" + pills(work.get("doing", []))
                  + "<strong>Next</strong>" + pills(work.get("next", []))
                  + "<strong>Blocked</strong>" + pills(work.get("blocked", [])))
    reason = card("Why this work?", f"<p>{text(objective['intent'])}</p><p><strong>Approach:</strong> "
                  f"{text(milestone['proposal'])}</p>")
    learning = pills([str(x.get("summary", "Unspecified learning"))
                      for x in projection["learnings"]])
    sections = (reason + status + inquiry_cards(projection["inquiries"])
                + timeline_card(projection["iterations"])
                + raci_card(projection["raci"])
                + concept_card(projection["concepts"])
                + card("What did we learn?", learning,
                       "Include successful reuse, new scenarios, and SPRs from failed retrieval"))
    header = f"<p class='eyebrow'>KALAXY3 • WORK IN PROGRESS</p><h1>{text(objective['title'])}</h1>"
    header += f"<p class='lead'>Milestone {text(milestone['id'])}: {text(milestone['title'])}</p>"
    attested = projection.get("inquiry_attestation", {})
    banner = ("<div class='notice'><strong>Signature valid against supplied key.</strong> "
              "Independent authority requires that CI pin that key to trusted main. "
              "This does not certify retrieval completeness, relevance, or approval.</div>") if attested else WARNING
    return HTML_TOP + header + banner + f"<main class='grid'>{sections}</main>" + HTML_BOTTOM


HTML_TOP = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SAGE | Architecture work in progress</title><style>
:root{color-scheme:light;font-family:system-ui,-apple-system,sans-serif;color:#182b38;background:#f4f7fa}
body{margin:auto;max-width:1180px;padding:34px 24px}h1{font-size:2rem;margin:0 0 8px}
h2{font-size:1.12rem;margin:0 0 12px}h3{font-size:1rem}p{line-height:1.5}
.eyebrow{font-size:.78rem;letter-spacing:.12em;font-weight:700;color:#395d74}
.lead{font-size:1.08rem;margin:4px 0 20px}.muted{color:#526475;font-size:.9rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:16px}
.card{background:#fff;border:1px solid #d6e1ea;padding:20px 22px;border-radius:12px}
.card ul,.timeline{padding-left:19px;line-height:1.5}.card li{margin:7px 0}
.notice{border-left:4px solid #b56c17;padding:10px 15px;background:#fff9ed;margin:24px 0}
</style></head><body>"""
WARNING = """<div class="notice"><strong>Evidence status:</strong> This is a readable
projection of supplied records, not a verified approval. A SHA-256 alone cannot certify
that semantic retrieval occurred. Independent signature and scope verification are
required before PR qualification.</div>"""
HTML_BOTTOM = "</body></html>"


def load_verified_inquiry(args: argparse.Namespace,
                          thread: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    """Validate an independent receipt and return its exact inquiry records.

    Args:
        args: Command-line paths for receipt, signature, key, and proposal.
        thread: Milestone whose proposal the signed receipt must describe.
    """
    paths = [args.receipt, args.signature, args.trusted_key, args.proposal,
             args.collection_revision]
    if not any(paths):
        return None
    if not all(paths):
        raise ProjectionError("All signed-inquiry verification inputs are required")
    location = Path(__file__).resolve().parents[2] / "ci/sage_semantic_inquiry_gate.py"
    spec = importlib.util.spec_from_file_location("inquiry_gate", location)
    if spec is None or spec.loader is None:
        raise ProjectionError("Independent inquiry verifier is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    evidence = module.verify_inquiry(args.receipt, args.signature, args.trusted_key,
                                     thread["objective"]["id"], thread["milestone"]["id"],
                                     args.proposal, args.collection_revision)
    signed = json.loads(args.receipt.read_text(encoding="utf-8"))
    inquiries = [{"question": item["question"], "results": item["returned"],
                  "gaps": [], "receipt_sha256": evidence["sha256"]}
                 for item in signed["inquiries"]]
    return evidence, inquiries


def main() -> None:
    """Render the work view; optionally verify inquiry provenance in-process."""
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--thread", type=Path, required=True)
    cli.add_argument("--json", type=Path, required=True)
    cli.add_argument("--html", type=Path, required=True)
    for name in ("receipt", "signature", "trusted-key", "proposal"):
        cli.add_argument(f"--{name}", type=Path)
    cli.add_argument("--collection-revision")
    args = cli.parse_args()
    thread = validate_thread(json.loads(args.thread.read_text(encoding="utf-8")))
    verified = load_verified_inquiry(args, thread)
    if verified:
        attestation, inquiries = verified
        thread = {**thread, "inquiries": inquiries}
    else:
        attestation = None
    projected = project(thread, attestation)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.html.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(projected, indent=2) + "\n", encoding="utf-8")
    args.html.write_text(html_page(projected), encoding="utf-8")
    print("STATUS=READ_ONLY_WORK_PROJECTION_WRITTEN")
    print("PR_ADMISSION=NOT_GRANTED; INQUIRY_SIGNATURE=" +
          ("VALIDATED_AGAINST_SUPPLIED_KEY" if verified else "NOT_VERIFIED"))


if __name__ == "__main__":
    main()
