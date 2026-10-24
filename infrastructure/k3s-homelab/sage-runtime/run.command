#!/usr/bin/env bash
# Direct Architect-authorized repair: retain SAGE source, publish runtime, deploy to K3s.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${SAGE_KALAXY_REPO:-$HOME/Downloads/sage-functional-integration-clean-20261022}"
DEST="$REPO/infrastructure/k3s-homelab/sage-runtime"
BRANCH=feature/sage-functional-delegation-continuation-20261022
BASE=755cc194150e4420d116ffc5efbe85cdb57299df
for tool in python3 git kubectl; do
  command -v "$tool" >/dev/null || { echo "BLOCKED: missing $tool"; exit 2; }
done
python3 "$ROOT/verify_bundle.py" "$ROOT"
[[ -d "$REPO/.git" ]] || { echo 'BLOCKED: feature repository not found'; exit 2; }
[[ "$(git -C "$REPO" branch --show-current)" == "$BRANCH" ]] || {
  echo 'BLOCKED: not on the qualified feature branch'; exit 2;
}
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$BASE" || -d "$DEST" ]] || {
  echo 'BLOCKED: unknown repository revision'; exit 2;
}
[[ -z "$(git -C "$REPO" diff --cached --name-only)" ]] || {
  echo 'BLOCKED: unrelated staged Git changes'; exit 2;
}
PYTHONPATH="$ROOT" python3 -m unittest discover -s "$ROOT/tests" -v
python3 -m compileall -q "$ROOT/service"
if [[ ! -d "$DEST" ]]; then
  mkdir -p "$DEST"
  cp -R "$ROOT/service" "$ROOT/tests" "$ROOT/k8s" "$DEST/"
  find "$DEST" -type d -name __pycache__ -prune -exec rm -rf {} +
  cp "$ROOT"/{requirements.txt,render.py,deploy.command,prepare_ollama.py,verify_bundle.py,bundle-sha256.json,README.md,ARCHITECT-CHECKPOINT.md,ask.command,run.command} "$DEST/"
fi
# Never overwrite an existing, potentially diverged runtime implementation.
python3 - "$ROOT" "$DEST" <<'PY'
"""Assert that the checked-out deployment source matches the sealed candidate."""
import hashlib
import json
import sys
from pathlib import Path
source, target = map(Path, sys.argv[1:])
for relative, expected in json.loads((source / 'bundle-sha256.json').read_text()).items():
    path = target / relative
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        sys.exit(f'BLOCKED: conflicting runtime source: {relative}')
print('KALAXY3 RUNTIME INTEGRATION: verified')
PY
(
  cd "$REPO"
  git add -- infrastructure/k3s-homelab/sage-runtime
  git diff --cached --check
  if ! git diff --cached --quiet; then
    git commit -m 'Integrate cluster-hosted LangGraph Architecture Helper runtime'
    git push origin "$BRANCH"
  fi
)
bash "$DEST/deploy.command"
echo 'DEPLOYED: read-only Architecture Helper plus governed request-execution boundary.'
echo 'USAGE: bash ~/Downloads/sage-architecture-helper-repair/ask.command "your question"'
echo 'Objective completion must still be demonstrated by an accepted SAGE execution receipt.'
