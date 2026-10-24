"""Live source-relevance check against a running Kalaxy3 Architecture Helper."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from .evidence import direct_source


QUESTION = (
    "Using committed Kalaxy3 evidence, explain how Ansible manages GitHub "
    "credentials; cite the actual Ansible sources and distinguish known "
    "implementation from unknown or merely proposed behavior."
)


def probe() -> dict[str, Any]:
    """Fail a live question if its citations don't include real Ansible evidence."""
    request = urllib.request.Request(
        "http://127.0.0.1:8080/v1/architecture/ask",
        data=json.dumps({"question": QUESTION}).encode(),
        headers={"Authorization": "Bearer " + os.environ["SAGE_API_TOKEN"],
                 "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            output = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read(2048).decode("utf-8", errors="replace")
        raise RuntimeError(f"API rejected answer (HTTP {exc.code}): {body}") from exc
    reply = output["answer"]
    paths = reply.get("evidence_paths", [])
    mode = reply.get("answer_mode", "source-bound")
    if mode != "evidence-gap" and not any(
            direct_source({"path": path, "content": "ansible"}, "ansible")
            for path in paths):
        raise RuntimeError("answer contains no cited Ansible implementation source")
    if mode == "evidence-gap":
        if not reply.get("uncertainties") or not any(
                path.startswith(".github/workflows/") for path in paths):
            raise RuntimeError("evidence gap must cite verified GitHub workflow and uncertainty")
        if "do not establish" not in reply.get("answer", "").lower():
            raise RuntimeError("evidence gap must not imply an unsupported relation")
    if not reply.get("supporting_quotes") or not output.get("evidence_manifest_sha256"):
        raise RuntimeError("answer lacks verified Git quote provenance")
    return {"status": "evidence-gap" if mode == "evidence-gap"
            else "direct-source-evidence-present", "git_revision": output["revision"],
            "citation_count": len(paths), "thread_id": output["thread_id"]}


def main() -> None:
    """Report the live functional result without exposing API credentials."""
    print(json.dumps(probe(), indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, ValueError, RuntimeError) as exc:
        sys.exit(f"SAGE ARCHITECTURE HELPER: BLOCKED: {exc}")
