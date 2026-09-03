"""Semantic experience synthesis contract for Human Participation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sage_evidence_retrieval import load_json, retrieve, validate_result

POLICY = Path("sage-evidence-retrieval-policy.json")
ALLOWED_RELATIONSHIPS = {
    "directly_relevant",
    "analogous",
    "weak_or_uncertain",
    "contradictory",
    "no_useful_support",
}
ALLOWED_EPISTEMIC = {"llm_derived", "llm_proposed"}


def canonical_json(value: Any) -> str:
    """Return stable JSON serialization."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_json(value: Any) -> str:
    """Hash stable JSON."""
    return hashlib.sha256(
        canonical_json(value).encode("utf-8")
    ).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def compact_result(
    result: dict[str, Any],
    origins: set[str],
) -> dict[str, Any]:
    """Keep evidence needed for semantic reasoning and traceability."""
    return {
        "evidence_ref": result["identifier"],
        "source_type": result["source_type"],
        "title": result["title"],
        "status": result.get("status", ""),
        "source_path": result["source_path"],
        "record_path": result.get("record_path", ""),
        "confidence": result.get("confidence", {}),
        "recency": result.get("recency", {}),
        "applicable_facts": result.get("applicable_facts", []),
        "origins": sorted(origins),
    }


def projection_results(
    payload: dict[str, Any],
    origin: str,
) -> list[tuple[dict[str, Any], str]]:
    """Collect canonical results already surfaced by a projection."""
    output: list[tuple[dict[str, Any], str]] = []
    areas = payload.get("areas", payload.get("relevant_experience", []))
    for area in areas:
        for key in ("experience_candidates", "reviewed_weak_candidates"):
            for wrapper in area.get(key, []):
                result = wrapper.get("canonical_result")
                if isinstance(result, dict):
                    output.append((result, origin))
    return output


def open_retrieval(repo: Path) -> dict[str, Any]:
    """Create one broad bounded canonical experience snapshot."""
    request = (
        "Retrieve a broad bounded snapshot of accumulated Kalaxy3 SAGE "
        "engineering experience across objectives, outcomes, evidence, "
        "lessons, failures, recovery, delivery, artifact integrity, runtime, "
        "security, observability, operations, architecture, governance, "
        "human participation, corrections, causal learning, and improvement "
        "actions. This is an experience-corpus input for LLM synthesis, not "
        "an applicability or competence query."
    )
    payload = retrieve(
        repo=repo,
        policy_path=repo / POLICY,
        request=request,
        limit=40,
    )
    validate_result(
        payload,
        load_json(repo / POLICY),
        require_final=False,
    )
    return payload


def build_corpus(
    repo: Path,
    inventory_path: Path,
    intent_path: Path,
) -> dict[str, Any]:
    """Build a bounded deduplicated evidence corpus for LLM synthesis."""
    inventory = load_object(inventory_path)
    intent = load_object(intent_path)
    broad = open_retrieval(repo)

    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    origins: dict[tuple[str, str, str], set[str]] = {}

    inputs = [
        *((item, "experience_inventory_projection")
          for item, _ in projection_results(
              inventory, "experience_inventory_projection"
          )),
        *((item, "intent_projection")
          for item, _ in projection_results(intent, "intent_projection")),
        *((item, "open_canonical_retrieval")
          for item in broad["results"]),
    ]

    for result, origin in inputs:
        key = (
            str(result["source_type"]),
            str(result["identifier"]),
            str(result["source_path"]),
        )
        merged[key] = result
        origins.setdefault(key, set()).add(origin)

    records = [
        compact_result(merged[key], origins[key])
        for key in sorted(merged)
    ]
    return {
        "schema_version": "1.0",
        "corpus_scope": "bounded_governed_experience_snapshot",
        "completeness_claim": "not_exhaustive",
        "semantic_use": (
            "LLM may derive themes and hypotheses; SAGE validates citations "
            "and epistemic boundaries but does not validate semantic truth."
        ),
        "open_retrieval": {
            "request": broad["request"],
            "algorithm_version": broad["algorithm_version"],
            "policy_sha256": broad["policy_sha256"],
            "retrieval_basis_sha256": broad["retrieval_basis_sha256"],
            "result_count": len(broad["results"]),
        },
        "records": records,
        "corpus_sha256": sha256_json(records),
    }


def evidence_index(
    corpus: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Index corpus evidence by stable evidence reference."""
    index: dict[str, list[dict[str, Any]]] = {}
    for record in corpus["records"]:
        index.setdefault(record["evidence_ref"], []).append(record)
    return index


def intent_area_refs(intent: dict[str, Any]) -> dict[str, set[str]]:
    """Map current intent areas to their canonical evidence identifiers."""
    mapping: dict[str, set[str]] = {}
    for area in intent.get("relevant_experience", []):
        refs: set[str] = set()
        for key in ("experience_candidates", "reviewed_weak_candidates"):
            for wrapper in area.get(key, []):
                result = wrapper.get("canonical_result", {})
                if result.get("identifier"):
                    refs.add(str(result["identifier"]))
        mapping[str(area["area"])] = refs
    return mapping


def validate_refs(
    refs: list[str],
    known: set[str],
    label: str,
) -> list[str]:
    """Validate that LLM citations resolve to governed evidence."""
    errors: list[str] = []
    if not refs:
        errors.append(f"{label} must cite at least one evidence_ref")
    unknown = sorted(set(refs) - known)
    if unknown:
        errors.append(
            f"{label} cites unknown evidence: {', '.join(unknown)}"
        )
    return errors


def validate_theme(
    theme: dict[str, Any],
    known: set[str],
    index: int,
) -> list[str]:
    """Validate one LLM-derived experience theme."""
    label = f"experience_themes[{index}]"
    errors = validate_refs(
        list(theme.get("evidence_refs", [])),
        known,
        label,
    )
    if theme.get("epistemic_status") != "llm_derived":
        errors.append(f"{label} must remain llm_derived")
    if not theme.get("why_this_theme"):
        errors.append(f"{label} lacks why_this_theme")
    if "priority_score" in theme or "overall_score" in theme:
        errors.append(f"{label} contains opaque aggregate score")
    return errors


def validate_assessment(
    item: dict[str, Any],
    known: set[str],
    area_refs: dict[str, set[str]],
    index: int,
) -> list[str]:
    """Validate one LLM semantic applicability assessment."""
    label = f"intent_applicability[{index}]"
    refs = list(item.get("evidence_refs", []))
    errors = validate_refs(refs, known, label)
    area = str(item.get("intent_area", ""))
    if area not in area_refs:
        errors.append(f"{label} references unknown intent area {area!r}")
    elif not set(refs).issubset(area_refs[area]):
        errors.append(
            f"{label} cites evidence not retrieved for intent area {area}"
        )
    if item.get("epistemic_status") != "llm_derived":
        errors.append(f"{label} must remain llm_derived")
    if item.get("semantic_relationship") not in ALLOWED_RELATIONSHIPS:
        errors.append(f"{label} has invalid semantic relationship")
    if item.get("transfer_decision") != "requires_architect_judgment":
        errors.append(f"{label} must leave transfer to Architect judgment")
    if not item.get("why"):
        errors.append(f"{label} lacks semantic explanation")
    if "assumptions" not in item or "unknowns" not in item:
        errors.append(f"{label} must expose assumptions and unknowns")
    return errors


def validate_innovation(
    item: dict[str, Any],
    index: int,
) -> list[str]:
    """Validate innovation remains possible without experience support."""
    label = f"innovation_beyond_experience[{index}]"
    errors: list[str] = []
    if item.get("epistemic_status") != "llm_proposed":
        errors.append(f"{label} must remain llm_proposed")
    if item.get("decision_authority") != "Architect":
        errors.append(f"{label} decision authority must be Architect")
    if not item.get("proposal") or not item.get("why"):
        errors.append(f"{label} lacks proposal or rationale")
    return errors


def validate_proposal(
    proposal: dict[str, Any],
    corpus: dict[str, Any],
    intent: dict[str, Any],
) -> list[str]:
    """Validate LLM semantic synthesis against governed evidence."""
    errors: list[str] = []
    known = set(evidence_index(corpus))
    area_refs = intent_area_refs(intent)

    if proposal.get("producer_class") != "llm":
        errors.append("proposal producer_class must be llm")
    if proposal.get("corpus_sha256") != corpus.get("corpus_sha256"):
        errors.append("proposal corpus_sha256 does not match corpus")
    if proposal.get("semantic_claim_status") != "llm_derived_not_fact":
        errors.append("semantic_claim_status must remain llm_derived_not_fact")

    themes = proposal.get("experience_themes", [])
    if not themes:
        errors.append("proposal must contain experience_themes")
    for index, theme in enumerate(themes):
        errors.extend(validate_theme(theme, known, index))

    assessments = proposal.get("intent_applicability", [])
    if not assessments:
        errors.append("proposal must contain intent_applicability")
    for index, item in enumerate(assessments):
        errors.extend(
            validate_assessment(item, known, area_refs, index)
        )

    innovations = proposal.get("innovation_beyond_experience", [])
    if not innovations:
        errors.append("proposal must preserve innovation beyond experience")
    for index, item in enumerate(innovations):
        errors.extend(validate_innovation(item, index))

    if proposal.get("architect_authority") != (
        "Architect decides objectives, trade-offs, and whether to transfer "
        "experience into action."
    ):
        errors.append("Architect authority statement missing or changed")

    return errors


def resolved_evidence(
    refs: list[str],
    index: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Resolve cited evidence into compact trace records."""
    output: list[dict[str, Any]] = []
    for ref in refs:
        records = index.get(ref, [])
        output.extend(records)
    return output


def build_synthesis(
    proposal: dict[str, Any],
    corpus: dict[str, Any],
    intent: dict[str, Any],
) -> dict[str, Any]:
    """Build validated stakeholder-facing semantic projection."""
    errors = validate_proposal(proposal, corpus, intent)
    if errors:
        raise ValueError("\n".join(errors))

    index = evidence_index(corpus)
    themes = []
    for theme in proposal["experience_themes"]:
        projected = dict(theme)
        projected["evidence"] = resolved_evidence(
            list(theme["evidence_refs"]),
            index,
        )
        themes.append(projected)

    applicability = []
    for item in proposal["intent_applicability"]:
        projected = dict(item)
        projected["evidence"] = resolved_evidence(
            list(item["evidence_refs"]),
            index,
        )
        applicability.append(projected)

    return {
        "schema_version": "1.0",
        "projection_type": "semantic_experience_and_intent_synthesis",
        "corpus_scope": corpus["corpus_scope"],
        "corpus_completeness": corpus["completeness_claim"],
        "corpus_sha256": corpus["corpus_sha256"],
        "validation": {
            "evidence_citations_resolved": True,
            "semantic_truth_validated_by_sage": False,
            "epistemic_boundaries_validated": True,
        },
        "architect_intent": intent["architect_intent"],
        "experience_themes": themes,
        "intent_applicability": applicability,
        "innovation_beyond_experience": proposal[
            "innovation_beyond_experience"
        ],
        "architect_authority": proposal["architect_authority"],
    }
