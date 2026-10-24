"""Check installed Ollama models; optionally pull only the embedding model."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Any


def request_json(endpoint: str, path: str, body: dict[str, Any] | None = None
                 ) -> dict[str, Any]:
    """Call one Ollama API endpoint.

    Args:
        endpoint: Existing cluster Ollama origin.
        path: Ollama API path.
        body: Optional JSON payload.
    """
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(
        endpoint.rstrip("/") + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=900 if body else 30) as response:
        return json.loads(response.read())


def main() -> None:
    """Verify model availability and bootstrap one expressly selected embedding model."""
    endpoint = os.environ.get("SAGE_OLLAMA_URL", "http://192.168.2.27:11434")
    embed = os.environ.get("SAGE_OLLAMA_EMBED_MODEL", "nomic-embed-text")
    inference = os.environ.get("SAGE_OLLAMA_MODEL", "qwen3:8b")
    installed = {record["name"] for record in request_json(endpoint, "/api/tags")["models"]}
    if not ({inference, inference + ":latest"} & installed):
        raise RuntimeError(f"BLOCKED: existing reasoning model {inference} unavailable")
    if not ({embed, embed + ":latest"} & installed):
        if os.environ.get("SAGE_BOOTSTRAP_EMBEDDINGS", "1") != "1":
            raise RuntimeError(f"BLOCKED: embedding model {embed} unavailable")
        print(f"PROVISION: embedding model {embed} into existing Ollama")
        result = request_json(endpoint, "/api/pull", {"name": embed, "stream": False})
        if result.get("status") != "success":
            raise RuntimeError(f"BLOCKED: embedding pull failed: {result.get('status')}")
    print(f"OLLAMA MODELS: PASS ({inference}; {embed})")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        sys.exit(str(exc))
