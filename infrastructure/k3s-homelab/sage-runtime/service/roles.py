"""Invoke replaceable Ollama RACI participants with explicit shared context."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class RoleError(RuntimeError):
    """Indicate a role failed to return a qualified structured contribution."""


def invoke_ollama(endpoint: str, model: str, system: str,
                  envelope: dict[str, Any]) -> dict[str, Any]:
    """Call Ollama's chat endpoint with no inherited conversation history.

    Args:
        endpoint: Administrator-configured Ollama base URL.
        model: Administrator-selected installed model name.
        system: Bounded role instruction.
        envelope: Entirely explicit shared objective and role context.
    """
    request = {
        "model": model, "stream": False, "format": "json",
        "options": {"temperature": 0, "num_ctx": 32768},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(envelope, sort_keys=True)},
        ],
    }
    body = json.dumps(request).encode("utf-8")
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/api/chat", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as response:
            output = json.load(response)
        answer = json.loads(output["message"]["content"])
    except (urllib.error.URLError, KeyError, ValueError) as exc:
        raise RoleError("Ollama did not return a valid JSON contribution") from exc
    if not isinstance(answer, dict):
        raise RoleError("role response must be a JSON object")
    return answer


def validated_engineering(reply: dict[str, Any]) -> dict[str, Any]:
    """Validate bounded engineering advisory fields without granting authority.

    Args:
        reply: Untrusted engineering model response.
    """
    if (not isinstance(reply.get("proposal"), str)
            or not reply["proposal"].strip()
            or not isinstance(reply.get("evidence_paths"), list)):
        raise RoleError("engineering proposal contract incomplete")
    return reply


def classify_referee(reply: dict[str, Any], sources: dict[str, str],
                    criteria: list[str]) -> str:
    """Classify a Referee finding by verifiable source provenance.

    Args:
        reply: Untrusted Referee response.
        sources: Verified source path to SHA-256 mappings.
        criteria: Architect-owned objective acceptance criteria.
    """
    verdict = reply.get("verdict")
    if verdict == "allow":
        return "allow"
    if verdict != "correct" or not isinstance(reply.get("findings"), list):
        raise RoleError("Referee returned an invalid decision")
    for item in reply["findings"]:
        if not isinstance(item, dict):
            continue
        if (sources.get(item.get("source_path")) == item.get("source_sha256")
                and item.get("criterion") in criteria
                and isinstance(item.get("invariant"), str)
                and item["invariant"].strip()):
            return "correction-proposed"
    return "unsupported-objection-recused"


def validate_citations(reply: dict[str, Any], context: dict[str, Any]) -> None:
    """Reject unsupported Engineering citations before Referee invocation.

    Args:
        reply: Untrusted engineering contribution.
        context: Verified shared objective context including retrieved sources.
    """
    expected = {source["path"] for source in context["evidence"]["retrieved_sources"]}
    expected.update(context["source_sha256"])
    citations = reply.get("evidence_paths")
    if not citations or not all(isinstance(path, str) and path in expected
                                for path in citations):
        raise RoleError("engineering cited absent or unverified Git evidence")
