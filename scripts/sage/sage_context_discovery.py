"""Read-only, revision-pinned Git and optional Neo4j context discovery.

This adapter nominates evidence for independent review. It does not decide
semantic relevance, qualify mappings, claim complete context, or mutate SAGE.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from sage_context_packet import assemble, render_packet

STOP_WORDS = {"about", "after", "and", "are", "for", "from", "into", "must",
              "that", "the", "this", "with", "without", "using", "which"}
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".py", ".yml", ".yaml", ".toml"}
MAX_CANDIDATES = 80


def git(repo: Path, *args: str) -> bytes:
    """Run a read-only Git operation and return stdout.

    Args:
        repo: Existing local Git checkout.
        *args: Git arguments without a shell.
    """
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True).stdout


def exact_revision(repo: Path, revision: str) -> str:
    """Resolve a named revision to an exact commit object.

    Args:
        repo: Existing Git checkout.
        revision: Commit or ref to inspect.
    """
    result = git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    return result.decode("ascii").strip()


def inventory(repo: Path, revision: str) -> dict[str, dict[str, str]]:
    """Enumerate tracked Git blobs at an exact commit without reading bodies.

    Args:
        repo: Git repository.
        revision: Full commit identifier.
    """
    result: dict[str, dict[str, str]] = {}
    for raw in git(repo, "ls-tree", "-rz", "--full-tree", revision).split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split(" ")
        if kind != "blob":
            continue
        name = path.decode("utf-8", errors="strict")
        result[name] = {"path": name, "mode": mode, "git_oid": oid}
    return dict(sorted(result.items()))


def query_terms(objective: str) -> list[str]:
    """Extract transparent lexical discovery cues, never semantic labels.

    Args:
        objective: Exact user-stated objective text.
    """
    terms = set(re.findall(r"[a-z0-9]{4,}", objective.lower())) - STOP_WORDS
    return sorted(terms, key=lambda term: (-len(term), term))[:12]


def git_content_hits(repo: Path, revision: str,
                     terms: Sequence[str]) -> set[str]:
    """Find committed text blobs containing objective terms without exporting text.

    Args:
        repo: Git repository.
        revision: Exact commit revision.
        terms: Bounded literal query terms.
    """
    if not terms:
        return set()
    args = ["git", "-C", str(repo), "grep", "-I", "-i", "-l", "-F"]
    for term in terms:
        args.extend(["-e", term])
    proc = subprocess.run([*args, revision, "--"], capture_output=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError("Git content discovery failed")
    prefix = (revision + ":").encode("ascii")
    return {line[len(prefix):].decode("utf-8") for line in proc.stdout.splitlines()
            if line.startswith(prefix)}


def rank_sources(universe: Mapping[str, Mapping[str, str]],
                 objective: str, hits: set[str]) -> list[str]:
    """Nominate a bounded candidate set independently of any graph result.

    Args:
        universe: Exact Git-tree inventory.
        objective: Architect objective text.
        hits: Paths found by bounded committed-content matching.
    """
    terms = set(query_terms(objective))
    ranked: list[tuple[int, str]] = []
    for path in universe:
        if Path(path).suffix.lower() not in TEXT_EXTENSIONS:
            continue
        path_words = set(re.findall(r"[a-z0-9]{4,}", path.lower()))
        score = 4 * len(terms & path_words) + int(path in hits)
        if score:
            ranked.append((-score, path))
    ranked.sort()
    return [path for _, path in ranked[:MAX_CANDIDATES]]


def verified_blob_sha256(repo: Path, oid: str) -> str:
    """Hash a Git object read directly from the pinned object store.

    Args:
        repo: Git checkout.
        oid: Object identifier from pinned Git tree.
    """
    data = git(repo, "cat-file", "blob", oid)
    return hashlib.sha256(data).hexdigest()


def graph_candidate_paths(result: Mapping[str, Any], revision: str
                          ) -> set[str]:
    """Read candidate paths without treating them as qualified semantic links.

    Args:
        result: Native Issue #50 objective_evidence response.
        revision: Expected graph feature revision.
    """
    projection = result.get("projection_id")
    if not isinstance(projection, str) or not projection.startswith(revision + ":"):
        raise ValueError("Graph projection identity does not match feature revision")
    if result.get("qualification") != "candidate_only":
        raise ValueError("Unexpected graph qualification; refuse authority upgrade")
    return {row["path"] for row in result.get("sources", [])
            if isinstance(row, dict) and isinstance(row.get("path"), str)}


def load_graph_response(path: Path | None) -> dict[str, Any] | None:
    """Load a previously captured native read-only response, when provided.

    Args:
        path: Existing response JSON path or None.
    """
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Graph response must be a JSON object")
    return payload


def build_sources(repo: Path, revision: str,
                  universe: Mapping[str, Mapping[str, str]],
                  candidates: Sequence[str], graph_paths: set[str]
                  ) -> list[dict[str, Any]]:
    """Combine independently retrieved Git candidates with graph suggestions.

    Args:
        repo: Local Git checkout.
        revision: Exact source revision.
        universe: Pinned Git inventory.
        candidates: Independently nominated Git paths.
        graph_paths: Unqualified candidate paths from Issue #50.
    """
    results: list[dict[str, Any]] = []
    for path in sorted(set(candidates) | (graph_paths & universe.keys())):
        source = universe[path]
        lanes = ["independent"] if path in candidates else []
        if path in graph_paths:
            lanes.append("graph")
        results.append({
            "source_id": f"git:{revision}:{path}", "title": path,
            "revision": revision,
            "git_oid": source["git_oid"],
            "claimed_digest": verified_blob_sha256(repo, source["git_oid"]),
            "access": "permitted" if not sensitive_path(path) else "restricted",
            "relevance": "uncertain", "epistemic_state": "not_evaluated",
            "discovery_lanes": lanes, "note": "Lexical discovery candidate; no relevance judgment",
        })
    return results


def sensitive_path(path: str) -> bool:
    """Conservatively classify potentially sensitive path names.

    Args:
        path: Repository-relative source path.
    """
    name = path.lower()
    tokens = set(re.split(r"[^a-z0-9]+", name))
    return bool(tokens & {"secret", "secrets", "credentials", "private", "key"}) or (
        name.endswith((".pem", ".key", ".p12", ".pfx", ".env")))


def graph_discrepancies(graph: Mapping[str, Any] | None,
                        sources: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Compare native graph source identities/digests against Git-read blobs.

    Args:
        graph: Optional candidate read response.
        sources: Independently enumerated and hashed source candidates.
    """
    if graph is None:
        return []
    observed = {row["title"]: row for row in sources}
    problems: list[dict[str, str]] = []
    for candidate in graph.get("sources", []):
        path = candidate.get("path")
        source = observed.get(path)
        if source is None:
            problems.append({"path": str(path), "reason": "not_in_pinned_git"})
            continue
        if candidate.get("git_oid") != source["git_oid"]:
            problems.append({"path": path, "reason": "git_object_mismatch"})
        if candidate.get("content_sha256") != source["claimed_digest"]:
            problems.append({"path": path, "reason": "sha256_mismatch"})
    return sorted(problems, key=lambda row: (row["path"], row["reason"]))


def build_input(repo: Path, feature: str, main: str,
                objective_id: str, objective: str, role: str,
                graph: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assemble transparent independent/graph observations with scope limitations.

    Args:
        repo: Repository containing both revisions.
        feature: Exact source feature commit.
        main: Exact promoted main commit.
        objective_id: Objective/issue identifier.
        objective: Objective text.
        role: Isolated agent role.
        graph: Optional captured read-only Issue #50 result.
    """
    universe = inventory(repo, feature)
    hits = git_content_hits(repo, feature, query_terms(objective))
    candidates = rank_sources(universe, objective, hits)
    graph_paths = graph_candidate_paths(graph, feature) if graph else set()
    sources = build_sources(repo, feature, universe, candidates, graph_paths)
    scope = {"git_tree": "searched", "git_text": "searched",
             "neo4j_candidate": "searched" if graph else "not_searched",
             "github_project": "not_searched", "external_systems": "not_searched"}
    request = {"objective_id": objective_id, "objective": objective,
               "role": role, "feature_revision": feature,
               "main_revision": main, "as_of": f"git:{feature}",
               "sources": sources, "search_scope": scope}
    counts = {"git_source_universe": len(universe),
              "git_independent_candidates": len(candidates),
              "git_content_match_paths": len(hits),
              "graph_candidate_paths_returned": len(graph_paths),
              "graph_paths_not_in_feature_tree": sorted(graph_paths - universe.keys()),
              "independent_candidates_not_in_graph_result": sorted(set(candidates) - graph_paths),
              "graph_candidate_page_incomplete": bool(graph and graph.get("next_offset") is not None),
              "graph_git_identity_disagreements": graph_discrepancies(graph, sources),
              "selected_sources_bounded": len(candidates) >= MAX_CANDIDATES}
    return request, counts


def write_outputs(out: Path, request: Mapping[str, Any],
                  counts: Mapping[str, Any], repo: Path,
                  feature: str, main: str) -> None:
    """Write local review artifacts; never write inside the source repository.

    Args:
        out: Output directory outside source checkout.
        request: Context packet inputs.
        counts: Search coverage observations.
        repo: Source Git checkout.
        feature: Exact feature commit.
        main: Exact main commit.
    """
    if out.resolve().is_relative_to(repo.resolve()):
        raise ValueError("Refusing evidence outputs inside the source Git checkout")
    manifest = assemble(request)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, Any] = {"context-input.json": request,
                             "context-manifest.json": manifest,
                             "discovery-coverage.json": counts}
    for name, payload in files.items():
        (out / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (out / "context-packet.md").write_text(render_packet(manifest), encoding="utf-8")
    (out / "git-feature-revision.txt").write_text(feature + "\n")
    (out / "git-main-revision.txt").write_text(main + "\n")


def parser() -> argparse.ArgumentParser:
    """Create the read-only first-slice CLI argument parser."""
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo", type=Path, required=True)
    result.add_argument("--feature", required=True)
    result.add_argument("--main", required=True)
    result.add_argument("--objective-id", required=True)
    result.add_argument("--objective", required=True)
    result.add_argument("--role", default="engineering_review")
    result.add_argument("--graph-response", type=Path)
    result.add_argument("--out", type=Path, required=True)
    return result


def main() -> int:
    """Run independent pinned Git discovery with optional candidate comparison."""
    args = parser().parse_args()
    feature = exact_revision(args.repo, args.feature)
    main_revision = exact_revision(args.repo, args.main)
    graph = load_graph_response(args.graph_response)
    request, counts = build_input(args.repo, feature, main_revision,
                                  args.objective_id, args.objective,
                                  args.role, graph)
    write_outputs(args.out, request, counts, args.repo, feature, main_revision)
    print("SOURCE_INVENTORY=" + str(counts["git_source_universe"]))
    print("CANDIDATES=" + str(counts["git_independent_candidates"]))
    print("GRAPH_RESPONSE=" + ("SUPPLIED_CANDIDATE_ONLY" if graph else "NOT_SUPPLIED"))
    print("COMPLETE_CONTEXT_CLAIM=NOT_MADE")
    print("OUTPUT=" + str(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
