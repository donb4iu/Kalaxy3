"""Generic repository-derived experience graph for Human Participation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

ID_KEYS = (
    "objective_id",
    "request_id",
    "action_id",
    "evidence_id",
    "lesson_id",
    "failure_id",
    "review_id",
    "decision_id",
    "capability_id",
    "candidate_id",
    "fact_id",
    "observation_id",
    "session_id",
    "id",
)

TYPE_BY_KEY = {
    "objective_id": "objective",
    "request_id": "request",
    "action_id": "action",
    "evidence_id": "evidence",
    "lesson_id": "lesson",
    "failure_id": "failure",
    "review_id": "review",
    "decision_id": "decision",
    "capability_id": "capability",
    "candidate_id": "candidate",
    "fact_id": "causal_insight",
    "observation_id": "observation",
    "session_id": "session",
    "id": "record",
}

ID_PATTERN = re.compile(
    r"\b(?:SAGE|FAIL|LESSON|ACTION|EVIDENCE|OBS|DECISION|"
    r"OBJECTIVE|REQUEST|CAPABILITY|FACT|REVIEW)-[A-Z0-9][A-Z0-9_.:-]*\b"
)

ROLE_KEYS = (
    "actor",
    "actor_role",
    "role",
    "owner",
    "authority",
    "decision_authority",
    "producer_class",
    "executor",
    "performed_by",
    "proposed_by",
    "approved_by",
)

ROLE_LABELS = {
    "architect": "Architect",
    "llm": "LLM",
    "sage": "SAGE",
    "operator": "Executor / Operator",
    "executor": "Executor / Operator",
    "github": "External system",
    "cluster": "External system",
    "kubernetes": "External system",
    "external": "External system",
}

RELATION_TERMS = (
    ("superseded_by", "superseded_by"),
    ("supersedes", "supersedes"),
    ("invalidated_by", "invalidated_by"),
    ("invalidates", "invalidates"),
    ("contradicted_by", "contradicted_by"),
    ("contradicts", "contradicts"),
    ("stale", "staleness"),
    ("context", "context_limit"),
    ("evidence", "evidence"),
    ("support", "supports"),
    ("contribut", "contributes"),
    ("influenc", "influences"),
    ("inform", "informs"),
    ("reuse", "reuses"),
    ("depend", "depends_on"),
    ("parent", "parent"),
    ("child", "child"),
    ("decision", "decision"),
    ("lesson", "lesson"),
    ("failure", "failure"),
    ("action", "action"),
    ("objective", "objective"),
)

SEMANTIC_RELATIONS = {item[1] for item in RELATION_TERMS}


def load_json(path: Path) -> Any:
    """Load JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def source_paths(repo: Path) -> list[Path]:
    """Return bounded governed JSON sources."""
    paths = sorted(repo.glob("sage-*.json"))
    catalog = repo / "markdown/evidence/catalog.json"
    if catalog.exists():
        paths.append(catalog)
    artifacts = repo / "markdown/evidence-artifacts"
    if artifacts.exists():
        paths.extend(sorted(artifacts.rglob("*.json")))
    return sorted(set(paths))


def identity(record: dict[str, Any], parent_key: str = "") -> tuple[str, str]:
    """Return explicit entity identity."""
    for key in ID_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip(), TYPE_BY_KEY[key]
    if parent_key and ID_PATTERN.fullmatch(parent_key):
        return parent_key, "record"
    return "", ""


def title(record: dict[str, Any], entity_id: str) -> str:
    """Return concise record title without inventing one."""
    for key in (
        "title",
        "name",
        "summary",
        "statement",
        "description",
        "reason",
        "desired_outcome",
    ):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().splitlines()[0][:320]
    return entity_id


def compact_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Keep inspectable small raw fields."""
    output: dict[str, Any] = {}
    for key, value in record.items():
        if key in ID_KEYS:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            text = str(value) if value is not None else ""
            if len(text) <= 1200:
                output[key] = value
        elif (
            isinstance(value, list)
            and len(value) <= 16
            and all(isinstance(item, (str, int, float, bool)) for item in value)
        ):
            output[key] = value
    return output


def normalize_role(value: str) -> str:
    """Normalize explicit role string conservatively."""
    lowered = value.strip().lower()
    for needle, label in ROLE_LABELS.items():
        if needle in lowered:
            return label
    return value.strip()


def explicit_roles(record: dict[str, Any]) -> list[dict[str, str]]:
    """Extract only explicit role attribution."""
    output: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key in ROLE_KEYS:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        role = normalize_role(value)
        token = (key, role)
        if token in seen:
            continue
        seen.add(token)
        output.append(
            {
                "role": role,
                "basis": f"explicit field {key}",
                "raw_value": value.strip(),
            }
        )
    return output


def walk_records(
    value: Any,
    source_path: str,
    json_path: str = "$",
    parent_key: str = "",
) -> Iterable[dict[str, Any]]:
    """Yield explicitly identifiable records."""
    if isinstance(value, dict):
        entity_id, entity_type = identity(value, parent_key)
        if entity_id:
            yield {
                "id": entity_id,
                "entity_type": entity_type,
                "title": title(value, entity_id),
                "status": str(
                    value.get(
                        "current_standing",
                        value.get("status", value.get("state", "")),
                    )
                ),
                "source_path": source_path,
                "json_path": json_path,
                "raw_fields": compact_fields(value),
                "role_attribution": explicit_roles(value),
                "_record": value,
            }
        for key, child in value.items():
            yield from walk_records(
                child,
                source_path,
                f"{json_path}.{key}",
                str(key),
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_records(
                child,
                source_path,
                f"{json_path}[{index}]",
                parent_key,
            )


def merge_entities(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Merge duplicate IDs without losing source provenance."""
    entities: dict[str, dict[str, Any]] = {}
    for record in records:
        entity_id = record["id"]
        existing = entities.get(entity_id)
        if existing is None:
            record["source_paths"] = [record.pop("source_path")]
            record["_records"] = [record.pop("_record")]
            entities[entity_id] = record
            continue

        source = record["source_path"]
        if source not in existing["source_paths"]:
            existing["source_paths"].append(source)
        existing["_records"].append(record["_record"])
        if existing["title"] == entity_id and record["title"] != entity_id:
            existing["title"] = record["title"]
        if not existing["status"] and record["status"]:
            existing["status"] = record["status"]
        existing["raw_fields"].update(record["raw_fields"])

        roles = existing["role_attribution"]
        known = {(item["role"], item["basis"]) for item in roles}
        for item in record["role_attribution"]:
            token = (item["role"], item["basis"])
            if token not in known:
                roles.append(item)
                known.add(token)
    return entities


def relation_type(path: str) -> str:
    """Classify only explicit field-path semantics."""
    lowered = path.lower().replace("-", "_")
    for needle, relation in RELATION_TERMS:
        if needle in lowered:
            return relation
    return "references"


def extract_strings(
    value: Any,
    path: str = "$",
) -> Iterable[tuple[str, str]]:
    """Yield string values with their field path."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield from extract_strings(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from extract_strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def relations(
    entities: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build explicit ID-reference relations only."""
    known = set(entities)
    output: dict[tuple[str, str, str], dict[str, Any]] = {}

    for source_id, entity in entities.items():
        for record in entity["_records"]:
            for path, text in extract_strings(record):
                for target_id in sorted(known):
                    if target_id == source_id or target_id not in text:
                        continue
                    relation = relation_type(path)
                    key = (source_id, target_id, relation)
                    output.setdefault(
                        key,
                        {
                            "source": source_id,
                            "target": target_id,
                            "relation": relation,
                            "semantic": relation in SEMANTIC_RELATIONS,
                            "field_path": path,
                        },
                    )
    return list(output.values())


def current_standing(
    entity: dict[str, Any],
    outgoing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> dict[str, str]:
    """Derive standing only from explicit status or relations."""
    status = entity.get("status", "").strip()
    lowered = status.lower()
    if "supersed" in lowered:
        return {"state": "superseded", "basis": "explicit status"}
    if "contradict" in lowered:
        return {"state": "contradicted", "basis": "explicit status"}
    if "invalid" in lowered:
        return {"state": "invalidated", "basis": "explicit status"}
    if "stale" in lowered:
        return {"state": "potentially_stale", "basis": "explicit status"}

    outgoing_types = {item["relation"] for item in outgoing}
    incoming_types = {item["relation"] for item in incoming}
    if "superseded_by" in outgoing_types or "supersedes" in incoming_types:
        return {"state": "superseded", "basis": "explicit relationship"}
    if (
        "contradicted_by" in outgoing_types
        or "contradicts" in incoming_types
    ):
        return {"state": "contradicted", "basis": "explicit relationship"}
    if (
        "invalidated_by" in outgoing_types
        or "invalidates" in incoming_types
    ):
        return {"state": "invalidated", "basis": "explicit relationship"}
    if "staleness" in outgoing_types or "staleness" in incoming_types:
        return {"state": "potentially_stale", "basis": "explicit relationship"}
    if "context_limit" in outgoing_types or "context_limit" in incoming_types:
        return {"state": "context_limited", "basis": "explicit relationship"}

    return {
        "state": "no_explicit_supersession_recorded",
        "basis": "no supersession/contradiction/staleness relationship found",
    }


def relationship_indexes(
    entities: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    """Attach bidirectional relationships and current standing."""
    outgoing: dict[str, list[dict[str, Any]]] = {key: [] for key in entities}
    incoming: dict[str, list[dict[str, Any]]] = {key: [] for key in entities}
    for edge in edges:
        outgoing[edge["source"]].append(edge)
        incoming[edge["target"]].append(edge)

    for entity_id, entity in entities.items():
        entity["outgoing"] = sorted(
            outgoing[entity_id],
            key=lambda item: (item["relation"], item["target"]),
        )
        entity["incoming"] = sorted(
            incoming[entity_id],
            key=lambda item: (item["relation"], item["source"]),
        )
        entity["current_standing"] = current_standing(
            entity,
            entity["outgoing"],
            entity["incoming"],
        )


def classify_episode(entity: dict[str, Any]) -> bool:
    """Classify objective/episode-like records without curated names."""
    return entity["entity_type"] in {
        "objective",
        "request",
        "action",
        "review",
        "session",
    }


def path_signals(
    entity: dict[str, Any],
    entities: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """Count linked entity classes as historical structural signals."""
    ids = {
        edge["source"] for edge in entity["incoming"]
    } | {
        edge["target"] for edge in entity["outgoing"]
    }
    counts: dict[str, int] = {}
    for entity_id in ids:
        related = entities.get(entity_id)
        if not related:
            continue
        kind = related["entity_type"]
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items()))


def role_interaction(
    entity: dict[str, Any],
    entities: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project explicit role participation around one episode."""
    ids = [entity["id"]]
    ids.extend(edge["source"] for edge in entity["incoming"])
    ids.extend(edge["target"] for edge in entity["outgoing"])
    output: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for entity_id in ids:
        related = entities.get(entity_id)
        if not related:
            continue
        for role in related.get("role_attribution", []):
            token = (entity_id, role["role"])
            if token in seen:
                continue
            seen.add(token)
            output.append(
                {
                    "role": role["role"],
                    "entity_id": entity_id,
                    "entity_type": related["entity_type"],
                    "title": related["title"],
                    "basis": role["basis"],
                }
            )
    return output


def build_graph(repo: Path) -> dict[str, Any]:
    """Build generic static experience graph."""
    records = []
    scanned = []
    for path in source_paths(repo):
        rel = str(path.relative_to(repo))
        scanned.append(rel)
        try:
            value = load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        records.extend(walk_records(value, rel))

    entities = merge_entities(records)
    edges = relations(entities)
    relationship_indexes(entities, edges)

    public_entities = []
    for entity in entities.values():
        entity["path_signals"] = path_signals(entity, entities)
        entity["is_episode"] = classify_episode(entity)
        if entity["is_episode"]:
            entity["role_interaction"] = role_interaction(entity, entities)
        else:
            entity["role_interaction"] = []
        entity.pop("_records", None)
        entity["source_paths"] = sorted(entity["source_paths"])
        public_entities.append(entity)

    return {
        "schema_version": "1.0",
        "projection_type": "generic_repository_experience_graph",
        "interaction_mode": "read_only",
        "role_rule": (
            "Role interaction uses explicit provenance only. Missing role "
            "attribution remains unknown rather than inferred."
        ),
        "relationship_semantics": {
            "semantic_relations": sorted(SEMANTIC_RELATIONS),
            "references": (
                "Generic explicit identifier reference; not a causal claim."
            ),
        },
        "standing_rule": (
            "Age alone never creates staleness. Standing requires explicit "
            "status or supersession/contradiction/invalidation/staleness "
            "relationship."
        ),
        "future_cost_rule": (
            "Historical path signals describe observed structure only and "
            "must not be presented as expected future repeat cost."
        ),
        "sources_scanned": scanned,
        "entities": sorted(
            public_entities,
            key=lambda item: (
                item["entity_type"],
                item["title"].lower(),
                item["id"],
            ),
        ),
        "relationships": sorted(
            edges,
            key=lambda item: (
                item["source"],
                item["relation"],
                item["target"],
            ),
        ),
    }
