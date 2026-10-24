#!/usr/bin/env bash
# Workstation-independent Architecture Helper: access via existing Kubernetes context.
set -euo pipefail
QUESTION="${*:-What is the current Architecture Helper objective and outstanding work?}"
PORT="${SAGE_ARCHITECT_PORT:-18880}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kubectl -n sage-runtime port-forward svc/sage-runtime "$PORT:80" >/dev/null 2>&1 &
PID=$!
trap 'kill "$PID" 2>/dev/null || true' EXIT
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if (echo >/dev/tcp/127.0.0.1/"$PORT") >/dev/null 2>&1; then break; fi
  sleep 1
done
TOKEN="$(kubectl -n sage-runtime get secret sage-runtime-api -o jsonpath='{.data.token}' | base64 --decode 2>/dev/null || kubectl -n sage-runtime get secret sage-runtime-api -o jsonpath='{.data.token}' | base64 -D)"
SAGE_API_TOKEN="$TOKEN" SAGE_QUESTION="$QUESTION" SAGE_ARCHITECT_PORT="$PORT" python3 - <<'PY'
"""Ask the cluster-hosted Architecture Helper without exposing the token."""
import json
import os
import urllib.request
import urllib.error
body = json.dumps({'question': os.environ['SAGE_QUESTION']}).encode()
request = urllib.request.Request(
    'http://127.0.0.1:' + os.environ['SAGE_ARCHITECT_PORT'] + '/v1/architecture/ask',
    data=body, headers={'Authorization': 'Bearer ' + os.environ['SAGE_API_TOKEN'],
                        'Content-Type': 'application/json'}, method='POST')
try:
    with urllib.request.urlopen(request, timeout=600) as response:
        answer = json.load(response)
except urllib.error.HTTPError as exc:
    body = exc.read(8192).decode("utf-8", errors="replace")
    try:
        detail = json.loads(body).get("detail", body)
    except ValueError:
        detail = body
    raise SystemExit(f"ARCHITECTURE HELPER HTTP {exc.code}: {detail}") from None
print(json.dumps(answer, indent=2))
PY
