"""Live cluster proof of the Architecture Helper's source-grounded API."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Any


def probe() -> dict[str, Any]:
    """Ask an infrastructure question with mandatory evidence and a fresh session."""
    question = ("From committed Kalaxy3 infrastructure evidence, identify the "
                "Ansible credential pattern and distinguish it from a deployed "
                "HashiCorp Vault service. State any uncertainty and cite files.")
    req = urllib.request.Request(
        "http://127.0.0.1:8080/v1/architecture/ask",
        data=json.dumps({"question": question}).encode(),
        headers={"Authorization": "Bearer " + os.environ["SAGE_API_TOKEN"],
                 "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=900) as response:
        output = json.load(response)
    evidence = output["answer"]["evidence_paths"]
    if not output.get("evidence_manifest_sha256") or not evidence:
        raise RuntimeError("architecture response has no pinned Git evidence")
    if output.get("authority") != "read-only architectural proposal; not governed acceptance":
        raise RuntimeError("architect incorrectly claimed execution authority")
    return {"status": "source-bound-answer", "git_revision": output["revision"],
            "citation_count": len(evidence), "thread_id": output["thread_id"]}


def main() -> None:
    """Print source-bound cluster result without leaking credentials."""
    print(json.dumps(probe(), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        sys.exit(f"SAGE ARCHITECTURE HELPER: BLOCKED: {exc}")
