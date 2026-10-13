#!/usr/bin/env python3
"""Independent fresh Referee checkpoint; no execution authority."""
from __future__ import annotations

import os
from typing import Any


class RefereeError(RuntimeError):
    """Referee did not independently qualify the delegation."""


def assess(request: str, advisory: dict[str, Any], endpoint: str, model: str, assignment: dict[str, Any] | None = None) -> dict[str, Any]:
    """Ask an independent fresh role to check intent fidelity and architecture."""
    from llm_role_invocation import invoke_ollama_json

    envelope = {
        "functional_request": request,
        "bounded_assignment": assignment or {"deliverable": request},
        "proposed_delegation": advisory,
        "source": "persistent-manager-functional-request",
        "role": "independent-referee",
    }
    instruction = (
        "You are an independent fresh SAGE Referee, with no preceding dialogue. "
        "Judge whether the proposed delegation actually addresses the bounded assignment deliverable, "
        "rather than quietly substituting documentation, clarification, or another task. "
        "A harmless but off-target response is a fidelity failure, not an approval. "
        "Judge whether the proposed delegation preserves the functional request "
        "without changing SAGE architecture, self-granting authority, bypassing "
        "roles, requiring an LLM to manufacture evidence, or claiming execution "
        "proof without receipts. Return JSON only with verdict (allow or reject), "
        "findings (array of strings), and rationale (string). You may not "
        "authorize mutation or redefine SAGE roles."
    )
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "verdict": {"type": "string", "enum": ["allow", "reject"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": ["verdict", "findings", "rationale"],
    }
    endpoint = os.environ.get("SAGE_REFEREE_ROLE_ENDPOINT", endpoint).strip() or endpoint
    model = os.environ.get("SAGE_REFEREE_ROLE_MODEL", model).strip() or model
    decision, provider_receipt = invoke_ollama_json(
        envelope=envelope, system_instruction=instruction,
        endpoint=endpoint, model=model, response_format=schema,
        think="low", num_ctx=32768, num_predict=4096, temperature=0,
    )
    if not isinstance(decision, dict) or decision.get("verdict") not in ("allow", "reject"):
        raise RefereeError("independent Referee did not supply a valid verdict")
    if not isinstance(decision.get("findings"), list) or not isinstance(decision.get("rationale"), str):
        raise RefereeError("independent Referee response is incomplete")
    return {"decision": decision, "provider_receipt": provider_receipt,
            "role_runtime": {"role": "independent-referee", "model": model}}
