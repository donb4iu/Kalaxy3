"""Git-grounded Architecture Helper with independently checked source quotes."""

from __future__ import annotations

import re
from typing import Any, Callable, TypedDict

from .evidence import direct_source, focus_domain, query_terms
from .roles import RoleError


class ArchitectState(TypedDict, total=False):
    """Disposable execution projection bound to immutable Git context."""

    question: str
    revision: str
    evidence: dict[str, Any]
    answer: dict[str, Any]


def validate_architect_answer(reply: dict[str, Any], evidence: dict[str, Any],
                              question: str, *, internal_gap: bool = False) -> None:
    """Reject invented citations and policy citations substituted for source facts.

    Args:
        reply: Untrusted Ollama structured answer.
        evidence: Verified retrieved Git source manifest and excerpts.
        question: Architect question for matching direct implementation evidence.
    """
    sources = {r["path"]: r for r in evidence["retrieved_sources"]}
    paths = reply.get("evidence_paths")
    quotes = reply.get("supporting_quotes")
    if (not isinstance(reply.get("answer"), str) or not reply["answer"].strip()
            or not isinstance(reply.get("uncertainties"), list)
            or not isinstance(paths, list) or not paths
            or not all(isinstance(p, str) and p in sources for p in paths)
            or not isinstance(quotes, list) or not quotes):
        raise RoleError("architecture answer lacks verified citations and source quotes")
    quoted_paths: set[str] = set()
    for entry in quotes:
        if not isinstance(entry, dict):
            raise RoleError("architecture quote must include Git path and source text")
        path, quote = entry.get("path"), entry.get("quote")
        if (not isinstance(path, str) or path not in paths
                or not isinstance(quote, str) or not 12 <= len(quote) <= 400
                or quote not in sources[path]["excerpt"]):
            raise RoleError("source quote is absent from the pinned Git excerpt")
        quoted_paths.add(path)
    if not set(paths).issubset(quoted_paths):
        raise RoleError("every cited source requires an exact verified quote")
    domain = focus_domain(question)
    gap = internal_gap and reply.get("answer_mode") == "evidence-gap"
    if domain and not gap and not any(
            direct_source(sources[p], domain) for p in quoted_paths):
        raise RoleError(f"{domain} question cites no direct implementation evidence")
    q = question.lower()
    if domain == "ansible" and "github" in q and any(
            word in q for word in ("credential", "secret", "token", "vault")):
        supported = any(
            direct_source(sources[e["path"]], domain)
            and "github" in e["quote"].lower()
            and any(w in e["quote"].lower() for w in (
                "credential", "secret", "token", "vault"))
            and ("vault" not in reply["answer"].lower()
                 or "vault" in e["quote"].lower())
            for e in quotes
        )
        if not supported and not (
                internal_gap and reply.get("answer_mode") == "evidence-gap"):
            raise RoleError("Ansible GitHub credential claim has no direct source quote")


def quote_line(record: dict[str, Any], terms: tuple[str, ...]) -> str | None:
    """Find one exact source line supporting a documented fact.

    Args:
        record: Git-verified excerpt and path.
        terms: Case-insensitive content match terms.
    """
    for line in record["excerpt"].splitlines():
        candidate = line.strip()
        if (12 <= len(candidate) <= 400
                and any(term in candidate.lower() for term in terms)
                and candidate in record["excerpt"]):
            return candidate
    return None


def extractive_fallback(evidence: dict[str, Any], question: str) -> dict[str, Any]:
    """Return verified cross-source findings without inventing their relationship.

    Args:
        evidence: Immutable, quoted Git excerpts.
        question: Architect question requiring Ansible/GitHub evidence.
    """
    if focus_domain(question) != "ansible" or "github" not in question.lower():
        raise RoleError("model answer lacked source-grounded citations")
    records = evidence["retrieved_sources"]
    ansible = [r for r in records if direct_source(r, "ansible")]
    if not ansible:
        raise RoleError("no direct Ansible source in pinned Git")
    workflows = [r for r in records if r["path"].startswith(".github/workflows/")]
    linked = [r for r in ansible if "github" in r["excerpt"].lower()
              and any(x in r["excerpt"].lower()
                      for x in ("vault", "credential", "secret", "token"))]
    quotes: list[dict[str, str]] = []
    for record in linked[:1]:
        text = quote_line(record, ("github",))
        if text and any(x in text.lower() for x in (
                "vault", "credential", "secret", "token")):
            quotes.append({"path": record["path"], "quote": text})
    if quotes:
        answer = "The pinned Ansible source contains this GitHub reference: " + quotes[0]["quote"]
        mode = "verbatim-evidence-fallback"
    else:
        work = next(((r, quote_line(r, ("api_token_github", "github_token")))
                     for r in workflows if quote_line(r, ("api_token_github", "github_token"))), None)
        source = next(((r, quote_line(r, ("ansible", "hosts:", "tasks:", "- name:")))
                       for r in ansible if quote_line(r, ("ansible", "hosts:", "tasks:", "- name:"))), None)
        for pair in (work, source):
            if pair:
                quotes.append({"path": pair[0]["path"], "quote": pair[1]})
        if not work:
            raise RoleError("no verified GitHub credential source in pinned Git")
        if not quotes:
            raise RoleError("no quotable Git evidence about the requested systems")
        answer = (
            "The pinned sources do not establish that Ansible Vault stores or supplies "
            "GitHub credentials. Available quotations identify only the separate "
            "configuration shown below; no relationship is inferred: "
            + " | ".join(q["quote"] for q in quotes))
        mode = "evidence-gap"
    return {"answer": answer, "evidence_paths": [q["path"] for q in quotes],
            "supporting_quotes": quotes,
            "uncertainties": ["The Git evidence may not capture private Ansible Vault usage."],
            "answer_mode": mode}


def generic_evidence_fallback(evidence: dict[str, Any], question: str) -> dict[str, Any]:
    """Report only verified source excerpts when a broad answer is unsupported.

    Args:
        evidence: Exact cited excerpts from an authorized Git checkpoint.
        question: The Architect's original question.
    """
    terms = query_terms(question)
    selections: list[dict[str, str]] = []
    for record in evidence["retrieved_sources"]:
        quote = quote_line(record, tuple(sorted(terms, key=len, reverse=True)))
        if quote is not None:
            selections.append({"path": record["path"], "quote": quote})
        if len(selections) == 4:
            break
    if not selections:
        raise RoleError("no quotable relevant Git evidence for the architecture request")
    answer = (
        "I cannot verify a complete implementation plan from the currently "
        "retrieved evidence. These are exact, independently verifiable Git "
        "excerpts, not claims that implementation is complete: "
        + " | ".join(f"{item['path']}: {item['quote']}" for item in selections)
    )
    return {
        "answer": answer,
        "evidence_paths": [item["path"] for item in selections],
        "supporting_quotes": selections,
        "uncertainties": [
            "An end-to-end deployment recipe and acceptance evidence are unverified.",
            "Additional directly relevant repository evidence may be needed.",
        ],
        "answer_mode": "evidence-gap",
    }


def build_architect_graph(
    invoke: Callable[[str, str, dict[str, Any]], dict[str, Any]],
) -> Any:
    """Build the existing LangGraph Architect node with independent evidence checks.

    Args:
        invoke: Stateless Ollama role adapter receiving pinned task context.
    """
    from langgraph.graph import END, START, StateGraph

    def architect(state: ArchitectState) -> dict[str, Any]:
        """Answer from verified sources or fail rather than invent infrastructure."""
        evidence = state["evidence"]
        if (not evidence.get("retrieved_sources")
                or evidence["manifest"]["revision"] != state["revision"]):
            raise RoleError("architect context provenance is missing")
        system = (
            "You are the Kalaxy3 Architecture Helper. Answer only what the supplied "
            "committed Git evidence demonstrates. Return JSON with keys: answer "
            "(string), evidence_paths (list of Git paths), supporting_quotes "
            "(list of {path, quote} using VERBATIM 12-400 character excerpts), "
            "uncertainties (list). Every cited path needs a literal source quote. "
            "For Ansible questions cite actual Ansible configuration, playbooks or "
            "infrastructure runbooks, not general SAGE policy. If Git evidence "
            "does not establish credential handling, explicitly say it is unknown; "
            "never infer it from general governance text. Never claim execution."
        )
        reply = invoke(system, state["question"], evidence)
        try:
            validate_architect_answer(reply, evidence, state["question"])
        except RoleError as diagnostic:
            q = state["question"].lower()
            if focus_domain(q) == "ansible" and "github" in q:
                reply = extractive_fallback(evidence, state["question"])
            else:
                correction = (
                    f"Previous answer failed verification: {diagnostic}. "
                    "Retry with the SAME Git excerpts and no new claims. "
                    "Every cited path needs an exact 12-400 character quote "
                    "copied from its retrieved excerpt. Mark unsupported "
                    "requirements explicitly as uncertain."
                )
                retry = invoke(system + " " + correction, state["question"], evidence)
                try:
                    validate_architect_answer(retry, evidence, state["question"])
                    reply = retry
                except RoleError:
                    reply = generic_evidence_fallback(evidence, state["question"])
            validate_architect_answer(
                reply, evidence, state["question"],
                internal_gap=reply.get("answer_mode") == "evidence-gap")
        return {"answer": reply}

    graph = StateGraph(ArchitectState)
    graph.add_node("architect", architect)
    graph.add_edge(START, "architect")
    graph.add_edge("architect", END)
    return graph


def make_ollama_adapter(endpoint: str, model: str) -> Callable[..., dict[str, Any]]:
    """Create stateless Ollama invocation with verified task-specific Git context.

    Args:
        endpoint: Existing deployed Ollama Service.
        model: Configured reasoning model name.
    """
    from .roles import invoke_ollama

    def call(system: str, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        """Supply the immutable evidence manifest to a fresh model request."""
        return invoke_ollama(endpoint, model, system, {
            "question": question, "manifest": evidence["manifest"],
            "retrieved_sources": evidence["retrieved_sources"],
        })

    return call
