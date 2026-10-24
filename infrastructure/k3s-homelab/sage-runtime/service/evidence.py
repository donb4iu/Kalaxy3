"""Retrieve task-specific, provenance-verified evidence from a pinned Git tree."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Protocol

from .context import ContextError, read_versioned


class DocumentLike(Protocol):
    """Minimum LangChain document interface."""

    page_content: str
    metadata: dict[str, Any]


class Searcher(Protocol):
    """Callable semantic search interface."""

    def __call__(self, query: str, k: int) -> list[DocumentLike]:
        """Return ranked Git-backed documents."""


def allowed_path(path: str) -> bool:
    """Allow source documentation while excluding secrets and encrypted values.

    Args:
        path: Git-tree-relative source path.
    """
    rel = Path(path)
    parts = [part.lower() for part in rel.parts]
    excluded = {"secrets", "group_vars", "host_vars", "credentials", ".ssh",
                "private", "tokens", "keys", "passwords"}
    if any(part in excluded for part in parts):
        return False
    if any(word in rel.name.lower() for word in (
            "secret", "credential", "password", "token", "private", ".vault")):
        return False
    roots = ("infrastructure/k3s-homelab/", "markdown/standards/",
             "markdown/evidence-artifacts/", "markdown/infrastructure/k3s_homelab/",
             ".github/workflows/")
    return (path in {"AGENTS.md", "SAGE.md"}
            or path.lower().startswith(roots)) and rel.suffix.lower() in {
                ".md", ".yaml", ".yml", ".json", ".py", ".cfg"}


def versioned_paths(repo: Path, revision: str) -> list[str]:
    """List eligible immutable Git objects.

    Args:
        repo: Disposable repository checkout.
        revision: Exact pinned commit.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", revision],
        check=True, capture_output=True, text=True, timeout=45)
    return sorted(path for path in proc.stdout.splitlines() if allowed_path(path))


def snapshot(repo: Path, revision: str, limit: int = 800) -> list[dict[str, str]]:
    """Read the committed evidence corpus, never the mutable worktree.

    Args:
        repo: Disposable repository checkout.
        revision: Exact pinned commit.
        limit: Maximum number of eligible files before failing closed.
    """
    paths = versioned_paths(repo, revision)
    if len(paths) > limit:
        raise ContextError(f"evidence corpus exceeds limit: {len(paths)} > {limit}")
    records: list[dict[str, str]] = []
    for path in paths:
        data = read_versioned(repo, revision, path)
        if len(data) > 35000 or b"\x00" in data or data.startswith(b"$ANSIBLE_VAULT;"):
            continue
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        records.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(),
                        "content": content})
    if not records:
        raise ContextError("no qualifying versioned evidence for context retrieval")
    return records


def focus_domain(query: str) -> str | None:
    """Identify source domains requiring direct operational evidence.

    Args:
        query: Architect question or delegated task description.
    """
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    for domain in ("ansible", "longhorn", "minio", "traefik", "ollama"):
        if domain in tokens:
            return domain
    return None


def direct_source(record: dict[str, str], domain: str) -> bool:
    """Identify implementation evidence rather than governance-only commentary.

    Args:
        record: Pinned Git source record.
        domain: Explicitly mentioned technical subsystem.
    """
    path = record["path"].lower()
    if domain == "ansible":
        if path.endswith("/ansible.cfg") or "/playbooks/" in path:
            return True
        if path.startswith("markdown/infrastructure/k3s_homelab/"):
            return "ansible" in record.get("content", record.get("excerpt", "")).lower()
        return path.startswith("infrastructure/k3s-homelab/") and (
            "ansible" in path or "/inventory/" in path)
    return (domain in path and path.startswith("infrastructure/"))


def query_terms(query: str) -> set[str]:
    """Extract topic-bearing search words, including credential synonyms.

    Args:
        query: Architectural question or role objective.
    """
    stop = {"about", "from", "with", "this", "that", "what", "which", "there",
            "were", "where", "used", "does", "into", "your", "their", "have",
            "and", "for", "the", "use", "using", "explain", "cite", "files",
            "relevant", "committed", "kalaxy3", "evidence", "deployed", "proposed"}
    terms = {word for word in re.findall(r"[a-z0-9_-]{3,}", query.lower())
             if word not in stop}
    if terms & {"credential", "credentials", "secret", "secrets", "token", "tokens"}:
        terms.update({"vault", "secret", "token", "credential"})
    if "ansible" in terms:
        terms.update({"playbook", "ansible.cfg"})
    return terms


def source_score(record: dict[str, str], query: str) -> int:
    """Score relevance deterministically before approximate vector search.

    Args:
        record: Pinned Git source record.
        query: Current task, rather than a general SAGE governance summary.
    """
    terms = query_terms(query)
    path, content = record["path"].lower(), record["content"].lower()
    weight = sum(12 for term in terms if term in path)
    weight += sum(2 for term in terms if term in content)
    domain = focus_domain(query)
    if domain and direct_source(record, domain):
        weight += 35
    return weight


def prioritize_records(records: list[dict[str, str]], query: str,
                       limit: int = 28) -> list[dict[str, str]]:
    """Select relevant Git files before embedding, including direct source files.

    Args:
        records: Full pinned source index.
        query: Current task-specific question.
        limit: Maximum number of complete documents embedded.
    """
    ranked = sorted(records, key=lambda r: (-source_score(r, query), r["path"]))
    if focus_domain(query) == "ansible" and "github" in query.lower():
        workflows = [r for r in ranked if r["path"].startswith(".github/workflows/")
                     and "secrets." in r["content"].lower()
                     and "github" in r["content"].lower()]
        preferred = workflows[:2] + [r for r in ranked if r not in workflows[:2]]
        return preferred[:limit]
    return ranked[:limit]


def build_langchain_searcher(records: list[dict[str, str]],
                             endpoint: str, embedding_model: str) -> Searcher:
    """Use LangChain's official in-memory vector store and Ollama embeddings.

    Args:
        records: Verified Git evidence records.
        endpoint: Existing Kubernetes Ollama Service endpoint.
        embedding_model: Installed Ollama embedding model.
    """
    from langchain_core.documents import Document
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_ollama import OllamaEmbeddings

    docs = [Document(page_content=record["content"],
                     metadata={"path": record["path"], "sha256": record["sha256"]})
            for record in records]
    embeddings = OllamaEmbeddings(model=embedding_model, base_url=endpoint)
    store = InMemoryVectorStore.from_documents(docs, embeddings)
    return lambda query, k: store.similarity_search(query, k=k)


def evidence_excerpt(content: str, query: str, width: int = 6500) -> str:
    """Return an exact substring near the best task-specific evidence passage.

    Args:
        content: Verified Git object text.
        query: Architect question, used only for choosing the quoted passage.
        width: Maximum excerpt length.
    """
    if len(content) <= width:
        return content
    terms = query_terms(query)
    lower = content.lower()
    places = range(0, len(content), 800)
    ranked = [(sum(lower[pos:pos + width].count(term) for term in terms), pos)
              for pos in places]
    best = max(ranked, key=lambda pair: (pair[0], -pair[1]))[1]
    return content[best:best + width]


def select_evidence(records: list[dict[str, str]], query: str,
                    search: Searcher, limit: int = 6) -> list[dict[str, str]]:
    """Validate semantic hits and include direct implementation evidence.

    Args:
        records: Verified Git source records.
        query: Current question.
        search: LangChain search callable or isolated test double.
        limit: Maximum evidence sources returned.
    """
    indexed = {record["path"]: record for record in records}
    selected: list[str] = []
    domain = focus_domain(query)
    if domain:
        direct = [r for r in records if direct_source(r, domain)]
        if not direct:
            raise ContextError(f"missing direct {domain} implementation evidence in Git")
        credentials = {"token", "secret", "credential", "vault"}
        if domain == "ansible" and "github" in query.lower():
            relevant = [r for r in direct if "github" in r["content"].lower()
                        and any(w in r["content"].lower() for w in credentials)]
            selected.extend(r["path"] for r in relevant[:2])
        if domain == "ansible" and "github" in query.lower():
            workflows = [r for r in records if r["path"].startswith(
                ".github/workflows/") and "secrets." in r["content"].lower()
                and "github" in r["content"].lower()]
            selected.extend(r["path"] for r in workflows[:2])
        selected.extend(r["path"] for r in direct[:2])
    for doc in search(query, limit + 4):
        path = doc.metadata.get("path")
        source = indexed.get(path)
        if not source or doc.metadata.get("sha256") != source["sha256"]:
            raise ContextError("retrieval returned unverified source provenance")
        if doc.page_content != source["content"]:
            raise ContextError("retrieval returned altered committed content")
        if path not in selected:
            selected.append(path)
    if not selected:
        raise ContextError("no source-bound evidence retrieved for this objective")
    return [{"path": path, "sha256": indexed[path]["sha256"],
             "excerpt": evidence_excerpt(indexed[path]["content"], query)}
            for path in selected[:limit]]


def compile_evidence(repo: Path, revision: str, query: str,
                     endpoint: str, model: str) -> dict[str, Any]:
    """Compile a mandatory context from pinned Git sources plus vector search.

    Args:
        repo: Disposable repository clone.
        revision: Exact governing Git revision.
        query: Objective and task-specific question.
        endpoint: Configured Ollama service.
        model: Embedding model name.
    """
    records = snapshot(repo, revision)
    candidates = prioritize_records(records, query)
    selected = select_evidence(candidates, query,
                               build_langchain_searcher(candidates, endpoint, model))
    manifest = {"revision": revision, "embedding_model": model,
                "corpus_size": len(records), "vectorized_sources": len(candidates),
                "selected_sources": [{"path": r["path"], "sha256": r["sha256"]}
                                     for r in selected]}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return {"manifest": manifest, "manifest_sha256": digest,
            "retrieved_sources": selected}
