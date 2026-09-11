"""Fresh SAGE-owned LLM role invocation with an Ollama HTTP reference adapter."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

STATE_ROOT = Path("~/.local/state/kalaxy3/sage-llm-role-invocation").expanduser()
ENDPOINT_ENV = "SAGE_LLM_ROLE_ENDPOINT"
MODEL_ENV = "SAGE_LLM_ROLE_MODEL"


class RoleInvocationError(RuntimeError):
    """Fail-closed role invocation error."""


def stable_json(value: Mapping[str, Any]) -> str:
    """Serialize a mapping deterministically for local execution evidence."""
    return json.dumps(dict(value), indent=2, sort_keys=True) + "\n"


def sha256_json(value: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 identity for a JSON object."""
    raw = json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def normalize_ollama_endpoint(endpoint: str) -> str:
    """Validate one credential-free Ollama base endpoint."""
    parsed = urllib.parse.urlparse(endpoint.strip())
    if parsed.scheme not in {"http", "https"}:
        raise RoleInvocationError("Ollama endpoint must use http or https")
    if not parsed.hostname:
        raise RoleInvocationError("Ollama endpoint requires a hostname")
    if parsed.username or parsed.password:
        raise RoleInvocationError("credentials may not be embedded in Ollama endpoint")
    if parsed.query or parsed.fragment:
        raise RoleInvocationError("Ollama endpoint may not include query or fragment")
    path = parsed.path.rstrip("/")
    if path not in {"", "/api"}:
        raise RoleInvocationError("Ollama endpoint path must be empty or /api")
    netloc = parsed.hostname
    if parsed.port:
        netloc += f":{parsed.port}"
    return urllib.parse.urlunparse((parsed.scheme, netloc, "", "", "", ""))


def resolve_ollama_runtime(
    environment: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    """Resolve the configured role-inference runtime or fail closed.

    Args:
        environment: Optional environment mapping used for deterministic tests.

    Returns:
        The normalized endpoint and configured model.

    Raises:
        RoleInvocationError: If required runtime configuration is absent.
    """
    values = os.environ if environment is None else environment
    endpoint = str(values.get(ENDPOINT_ENV, "")).strip()
    model = str(values.get(MODEL_ENV, "")).strip()
    configured = ((ENDPOINT_ENV, endpoint), (MODEL_ENV, model))
    missing = [name for name, value in configured if not value]
    if missing:
        raise RoleInvocationError(
            "fresh role inference runtime is not configured: " + ", ".join(missing)
        )
    return normalize_ollama_endpoint(endpoint), model


def build_invocation(
    *,
    role: str,
    objective_id: str,
    request: Mapping[str, Any],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Build one explicit fresh role invocation envelope."""
    if not role.strip():
        raise RoleInvocationError("role is required")
    if not objective_id.strip():
        raise RoleInvocationError("objective_id is required")
    return {
        "schema_version": "1.0",
        "record_type": "sage-llm-role-invocation",
        "role": role,
        "objective_id": objective_id,
        "context_policy": {
            "sage_selected_context_only": True,
            "architect_chat_history_included": False,
            "role_chat_history_included": False,
            "predecessor_chat_history_included": False,
            "executor_filesystem_access_required": False,
        },
        "request": dict(request),
        "context": dict(context),
    }


def _request_payload(
    envelope: Mapping[str, Any],
    system_instruction: str,
    model: str,
) -> bytes:
    """Build the provider wire request from one fresh invocation."""
    messages = [
        {"role": "system", "content": system_instruction.strip()},
        {
            "role": "user",
            "content": json.dumps(
                dict(envelope),
                sort_keys=True,
                separators=(",", ":"),
            ),
        },
    ]
    wire = {
        "model": model.strip(),
        "messages": messages,
        "format": "json",
        "stream": False,
    }
    return json.dumps(wire, separators=(",", ":")).encode("utf-8")


def _decode_result(raw: bytes) -> tuple[dict[str, Any], Mapping[str, Any]]:
    """Decode one provider response into a JSON role result."""
    try:
        outer = json.loads(raw.decode("utf-8"))
        content = outer["message"]["content"]
        result = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise RoleInvocationError(
            "Ollama response did not contain a JSON role result"
        ) from error
    if not isinstance(result, dict):
        raise RoleInvocationError("role result must be a JSON object")
    return result, outer


def invoke_ollama_json(
    *,
    envelope: Mapping[str, Any],
    system_instruction: str,
    endpoint: str,
    model: str,
    timeout_seconds: int = 180,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Invoke one fresh role through Ollama /api/chat and return JSON plus receipt."""
    if not system_instruction.strip():
        raise RoleInvocationError("system instruction is required")
    if not model.strip():
        raise RoleInvocationError("Ollama model is required")
    base = normalize_ollama_endpoint(endpoint)
    encoded = _request_payload(envelope, system_instruction, model)
    started_at = datetime.now().astimezone().isoformat(timespec="seconds")
    request = urllib.request.Request(
        base + "/api/chat",
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RoleInvocationError(f"Ollama invocation failed: {error}") from error
    completed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    result, outer = _decode_result(raw)
    receipt = _build_receipt(
        envelope, encoded, raw, result, outer, base, model, started_at, completed_at
    )
    return result, receipt


def _build_receipt(
    envelope: Mapping[str, Any],
    encoded: bytes,
    raw: bytes,
    result: Mapping[str, Any],
    outer: Mapping[str, Any],
    endpoint: str,
    model: str,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    """Build non-conversational provider invocation evidence."""
    return {
        "schema_version": "1.0",
        "record_type": "sage-llm-role-invocation-receipt",
        "role": envelope.get("role"),
        "objective_id": envelope.get("objective_id"),
        "provider": "ollama",
        "transport": "http",
        "endpoint": endpoint,
        "model_requested": model.strip(),
        "model_reported": outer.get("model"),
        "started_at": started_at,
        "completed_at": completed_at,
        "invocation_sha256": sha256_json(envelope),
        "wire_request_sha256": hashlib.sha256(encoded).hexdigest(),
        "provider_response_sha256": hashlib.sha256(raw).hexdigest(),
        "role_result_sha256": sha256_json(result),
        "architect_chat_history_included": False,
        "role_chat_history_included": False,
        "predecessor_chat_history_included": False,
        "executor": {"hostname": socket.gethostname()},
    }


def new_state_dir(prefix: str) -> Path:
    """Create disposable local execution/projection state."""
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    path = STATE_ROOT / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-" + prefix)
    path.mkdir(parents=True, exist_ok=False)
    return path


def persist_json(path: Path, value: Mapping[str, Any]) -> None:
    """Persist one local role artifact with owner-only permissions."""
    path.write_text(stable_json(value), encoding="utf-8")
    path.chmod(0o600)
