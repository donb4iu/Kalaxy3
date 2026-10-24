"""Use LangChain retrieval over a bounded, pinned Git evidence snapshot."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Protocol

from .context import ContextError, read_versioned


class DocumentLike(Protocol):
    """Minimal LangChain document contract used by the compiler."""

    page_content: str
    metadata: dict[str, Any]


class Searcher(Protocol):
    """Allow a real LangChain retriever or isolated test double."""

    def __call__(self, query: str, k: int) -> list[DocumentLike]:
        """Return ranked documents for an objective-related question."""


def allowed_path(path: str) -> bool:
    """Allow only versioned, non-secret repository policy and infrastructure text.

    Args:
        path: Relative Git tree path from a pinned commit.
    """
    rel = Path(path)
    parts = [part.lower() for part in rel.parts]
    blocked = {"secrets", "group_vars", "host_vars", "credentials", ".ssh",
               "private", "vault", "tokens", "keys", "passwords"}
    if any(part in blocked for part in parts):
        return False
    if any(word in rel.name.lower() for word in (
            "secret", "credential", "password", "token", "private", ".vault")):
        return False
    roots = ("infrastructure/k3s-homelab/", "markdown/standards/",
             "markdown/evidence-artifacts/")
    return (path in {"AGENTS.md", "SAGE.md"}
            or path.startswith(roots)) and rel.suffix.lower() in {
                ".md", ".yaml", ".yml", ".json", ".py"}


def versioned_paths(repo: Path, revision: str) -> list[str]:
    """List candidate text paths from the exact committed Git tree.

    Args:
        repo: Disposable repository clone.
        revision: Verified pinned commit.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", revision],
        check=True, capture_output=True, text=True, timeout=45,
    )
    return sorted(path for path in result.stdout.splitlines() if allowed_path(path))


def snapshot(repo: Path, revision: str, limit: int = 800) -> list[dict[str, str]]:
    """Read an auditable evidence corpus without consulting worktree files.

    Args:
        repo: Disposable repository clone.
        revision: Verified pinned commit.
        limit: Hard cap; an oversized corpus must not be silently trimmed.
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


def build_langchain_searcher(records: list[dict[str, str]],
                             endpoint: str, embedding_model: str) -> Searcher:
    """Use official LangChain vector store and Ollama embeddings integration.

    Args:
        records: Verified Git evidence records.
        endpoint: Existing Ollama service URL.
        embedding_model: Installed embedding-capable Ollama model.
    """
    from langchain_core.documents import Document
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_ollama import OllamaEmbeddings

    docs = [Document(page_content=record["content"][:35000],
                     metadata={"path": record["path"], "sha256": record["sha256"]})
            for record in records]
    embeddings = OllamaEmbeddings(model=embedding_model, base_url=endpoint)
    store = InMemoryVectorStore.from_documents(docs, embeddings)
    return lambda query, k: store.similarity_search(query, k=k)


def select_evidence(records: list[dict[str, str]], query: str,
                    search: Searcher, limit: int = 6) -> list[dict[str, str]]:
    """Validate retrieved documents against Git objects before prompt assembly.

    Args:
        records: Committed source objects and SHA-256 digests.
        query: Architect objective and specific question.
        search: Ranker from the official vector store.
        limit: Maximum documents included in role context.
    """
    indexed = {record["path"]: record for record in records}
    results: list[dict[str, str]] = []
    for doc in search(query, limit):
        path = doc.metadata.get("path")
        original = indexed.get(path)
        if not original or doc.metadata.get("sha256") != original["sha256"]:
            raise ContextError("retrieval returned unverified source provenance")
        if doc.page_content != original["content"][:35000]:
            raise ContextError("retrieval returned altered committed content")
        if path not in [item["path"] for item in results]:
            results.append({"path": path, "sha256": original["sha256"],
                            "excerpt": original["content"][:6500]})
    if not results:
        raise ContextError("no source-bound evidence retrieved for this objective")
    return results


def prioritize_records(records: list[dict[str, str]], query: str,
                       limit: int = 28) -> list[dict[str, str]]:
    """Limit embedding work to source-relevant Git documents without losing guards.

    Args:
        records: Immutable committed source snapshots.
        query: Objective and currently assigned work.
        limit: Maximum vectorized documents per task.
    """
    stop = {"about", "from", "with", "this", "that", "what", "which",
            "there", "were", "where", "used", "does", "into", "your",
            "their", "have", "does", "and", "for", "the", "use"}
    terms = {term for term in re.findall(r"[a-z0-9_-]{3,}", query.lower())
             if term not in stop}

    def score(record: dict[str, str]) -> tuple[int, str]:
        """Rank evidence by term overlap, keeping canonical governance visible."""
        path = record["path"].lower()
        content = record["content"].lower()
        base = 3 if path in {"agents.md", "sage.md"} else 0
        weight = sum(5 for term in terms if term in path)
        matches = sum(1 for term in terms if term in content[:35000])
        return (base + weight + matches, path)

    return sorted(records, key=score, reverse=True)[:limit]


def compile_evidence(repo: Path, revision: str, query: str,
                     endpoint: str, model: str) -> dict[str, Any]:
    """Assemble a provenance-bound, disposable semantic projection from Git.

    Args:
        repo: Disposable authoritative Git checkout.
        revision: Exact commit used to restore objective authority.
        query: Objective and task-specific retrieval request.
        endpoint: Ollama endpoint.
        model: Embedding model name, distinct from reasoning model.
    """
    records = snapshot(repo, revision)
    relevant = prioritize_records(records, query)
    searcher = build_langchain_searcher(relevant, endpoint, model)
    selected = select_evidence(relevant, query, searcher)
    manifest = {"revision": revision, "embedding_model": model,
                "corpus_size": len(records), "vectorized_sources": len(relevant),
                "selected_sources": [
                    {"path": r["path"], "sha256": r["sha256"]}
                    for r in selected]}
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return {"manifest": manifest, "manifest_sha256": digest,
            "retrieved_sources": selected}
