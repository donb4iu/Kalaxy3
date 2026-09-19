#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

ROLE_ID = "sage.intent-bootstrap-role"
BLOCKER_BOUNDARY = "workflow-manager-runtime-qualification"
BLOCKER_CLASS = "fresh-role-inference-runtime"


def stable_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def state_dir():
    default = Path.home() / ".local/state/kalaxy3/sage-intent-front-door"
    root = Path(os.environ.get("SAGE_INTENT_FRONT_DOOR_STATE_ROOT", str(default)))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    path = root / stamp
    path.mkdir(parents=True, exist_ok=False)
    os.chmod(path, 0o700)
    return path


def run_preflight(req):
    proc = subprocess.run(
        [sys.executable, "scripts/sage/sage-change-preflight.py", "--request", req],
        capture_output=True,
        text=True,
    )
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def runtime_config():
    return (
        os.environ.get("SAGE_LLM_ROLE_ENDPOINT", "").strip(),
        os.environ.get("SAGE_LLM_ROLE_MODEL", "").strip(),
    )


def normalize_chat_url(endpoint):
    value = endpoint.rstrip("/")
    return value if value.endswith("/api/chat") else value + "/api/chat"


def invoke_ollama(endpoint, model, envelope):
    system = (
        "You are a fresh disposable SAGE intent-bootstrap role. "
        "You have no Architect chat history, no prior-role chat history, and no predecessor chat history. "
        "Treat the supplied SAGE envelope as your complete context. "
        "You are advisory only: do not mutate anything and do not choose caller-facing SAGE mechanics. "
        "Return one JSON object only with keys decision, summary, assumptions, alternatives, recommended_path, "
        "material_decision_required, questions, confidence. "
        "decision must be one of plan, clarify, bootstrap-contribution."
    )
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(envelope, sort_keys=True)},
        ],
        "options": {"temperature": 0},
    }
    req = urllib_request.Request(
        normalize_chat_url(endpoint),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
    except (URLError, HTTPError, TimeoutError) as exc:
        raise RuntimeError(f"fresh-role runtime invocation failed: {exc}") from exc

    outer = json.loads(raw)
    content = outer.get("message", {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("fresh-role runtime returned no message content")

    try:
        decision = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("fresh-role runtime returned non-JSON advisory content") from exc

    allowed = {"plan", "clarify", "bootstrap-contribution"}
    if not isinstance(decision, dict) or decision.get("decision") not in allowed:
        raise RuntimeError("fresh-role advisory decision is outside the published bootstrap vocabulary")

    return decision


def main():
    parser = argparse.ArgumentParser(description="Published Architect -> SAGE raw-intent front door")
    parser.add_argument("--request", default=os.environ.get("SAGE_REQUEST", ""))
    args = parser.parse_args()
    literal = args.request.strip()
    if not literal:
        raise SystemExit("SAGE_REQUEST or --request is required")

    out = state_dir()
    request_sha = sha256_text(literal)

    status_lines = git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    repo = {
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "working_tree": status_lines,
    }

    preflight = run_preflight(literal)
    write_json(out / "preflight.json", preflight)

    envelope = {
        "schema_version": "1.0",
        "role_id": ROLE_ID,
        "literal_request": literal,
        "request_sha256": request_sha,
        "repository": repo,
        "context_policy": {
            "architect_chat_inherited": False,
            "prior_role_chat_inherited": False,
            "predecessor_chat_inherited": False,
            "source": "sage-created-envelope-only",
        },
        "authority": {
            "llm": "advisory-only",
            "sage": "facts-state-allowed-actions-and-execution",
        },
        "preflight": {
            "returncode": preflight["returncode"],
            "stdout_sha256": sha256_text(preflight["stdout"]),
            "stderr_sha256": sha256_text(preflight["stderr"]),
        },
    }
    context_sha = sha256_text(stable_json(envelope))
    envelope["context_sha256"] = context_sha
    write_json(out / "fresh-role-envelope.json", envelope)

    endpoint, model = runtime_config()
    if not endpoint or not model:
        result = {
            "schema_version": "1.0",
            "record_type": "sage-architect-request-front-door-result",
            "status": "blocked",
            "request_sha256": request_sha,
            "fresh_role": {
                "role_id": ROLE_ID,
                "invoked": False,
                "context_sha256": context_sha,
                "provider_endpoint_configured": bool(endpoint),
                "model_configured": bool(model),
            },
            "blocker": {
                "boundary": BLOCKER_BOUNDARY,
                "class": BLOCKER_CLASS,
                "mutation_performed": False,
                "reason": "SAGE-owned fresh-role inference runtime is not configured; persistent caller fallback is forbidden.",
            },
            "architect_attention_required": False,
            "next_functional_requirement": (
                "Qualify the shared Kalaxy-hosted inference runtime, then resubmit the same literal request."
            ),
            "receipt": str(out / "front-door-result.json"),
        }
        write_json(out / "front-door-result.json", result)
        print("Kalaxy3 SAGE raw-intent front door: GOVERNED BLOCKER")
        print(f"request_sha256={request_sha}")
        print(f"fresh_role.role_id={ROLE_ID}")
        print("fresh_role.invoked=false")
        print(f"fresh_role.context_sha256={context_sha}")
        print(f"blocker.boundary={BLOCKER_BOUNDARY}")
        print(f"blocker.class={BLOCKER_CLASS}")
        print(f"receipt={out / 'front-door-result.json'}")
        return 0

    receipt = {
        "schema_version": "1.0",
        "role_id": ROLE_ID,
        "request_sha256": request_sha,
        "context_sha256": context_sha,
        "endpoint": endpoint,
        "model": model,
    }

    try:
        advisory = invoke_ollama(endpoint, model, envelope)
    except Exception as exc:
        write_json(out / "invocation-receipt.json", receipt | {"status": "failed", "error": str(exc)})
        result = {
            "schema_version": "1.0",
            "record_type": "sage-architect-request-front-door-result",
            "status": "blocked",
            "request_sha256": request_sha,
            "fresh_role": {
                "role_id": ROLE_ID,
                "invoked": True,
                "context_sha256": context_sha,
                "model": model,
            },
            "blocker": {
                "boundary": BLOCKER_BOUNDARY,
                "class": BLOCKER_CLASS,
                "mutation_performed": False,
                "reason": str(exc),
            },
            "architect_attention_required": False,
            "receipt": str(out / "front-door-result.json"),
        }
        write_json(out / "front-door-result.json", result)
        print("Kalaxy3 SAGE raw-intent front door: GOVERNED BLOCKER")
        print(f"fresh_role.role_id={ROLE_ID}")
        print("fresh_role.invoked=true")
        print(f"fresh_role.context_sha256={context_sha}")
        print(f"blocker.boundary={BLOCKER_BOUNDARY}")
        print(f"receipt={out / 'front-door-result.json'}")
        return 0

    write_json(out / "advisory-decision.json", advisory)
    write_json(out / "invocation-receipt.json", receipt | {"status": "pass", "decision": advisory.get("decision")})
    result = {
        "schema_version": "1.0",
        "record_type": "sage-architect-request-front-door-result",
        "status": "fresh-role-advisory-ready",
        "request_sha256": request_sha,
        "fresh_role": {
            "role_id": ROLE_ID,
            "invoked": True,
            "context_sha256": context_sha,
            "model": model,
            "decision": advisory.get("decision"),
        },
        "advisory_decision": str(out / "advisory-decision.json"),
        "invocation_receipt": str(out / "invocation-receipt.json"),
        "mutation_performed": False,
        "next_boundary": (
            "SAGE deterministic consumption of the advisory result; caller must not select an internal re-entry boundary."
        ),
    }
    write_json(out / "front-door-result.json", result)

    print("Kalaxy3 SAGE raw-intent front door: FRESH ROLE COMPLETE")
    print(f"request_sha256={request_sha}")
    print(f"fresh_role.role_id={ROLE_ID}")
    print("fresh_role.invoked=true")
    print(f"fresh_role.context_sha256={context_sha}")
    print(f"fresh_role.model={model}")
    print(f"fresh_role.decision={advisory.get('decision')}")
    print(f"invocation_receipt={out / 'invocation-receipt.json'}")
    print(f"advisory_decision={out / 'advisory-decision.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
