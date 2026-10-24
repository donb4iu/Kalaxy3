#!/bin/bash
# Deploy the existing SAGE runtime to K3s without Docker or Mac-side images.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
for app in kubectl python3; do
  command -v "$app" >/dev/null || { echo "BLOCKED: $app is unavailable"; exit 2; }
done
python3 "$ROOT/verify_bundle.py" "$ROOT"
python3 "$ROOT/prepare_ollama.py"
kubectl cluster-info >/dev/null
kubectl get nodes -o json | python3 -c 'import json,sys; a=json.load(sys.stdin).get("items",[]); assert a and any("k3s" in n.get("status",{}).get("nodeInfo",{}).get("kubeletVersion","") for n in a), "BLOCKED: context is not recognized as K3s"'
echo "K3S CONTEXT: $(kubectl config current-context)"
kubectl get storageclass longhorn >/dev/null || { echo 'BLOCKED: Longhorn storage class absent'; exit 2; }
kubectl apply -f "$ROOT/k8s/namespace.yaml"
for resource in configmaps deployments services persistentvolumeclaims networkpolicies; do
  [[ "$(kubectl auth can-i create "$resource" -n sage-runtime)" == yes ]] || {
    echo "BLOCKED: cannot create $resource in sage-runtime"; exit 2;
  }
done
if ! kubectl -n sage-runtime get secret sage-runtime-api >/dev/null 2>&1; then
  echo 'CREATE: dedicated Kubernetes-native SAGE API credential (no HashiCorp Vault assumption)'
  python3 -c 'import secrets,sys; sys.stdout.write(secrets.token_urlsafe(48))' \
    | kubectl -n sage-runtime create secret generic sage-runtime-api \
        --from-file=token=/dev/stdin >/dev/null
fi
[[ -n "$(kubectl -n sage-runtime get secret sage-runtime-api -o jsonpath='{.data.token}')" ]] || {
  echo 'BLOCKED: sage-runtime-api exists but has no token key'; exit 2;
}
WORK="$(mktemp -d "${TMPDIR:-/tmp}/sage-k3s-deploy.XXXXXXXX")"
trap 'rm -rf "$WORK"' EXIT
SAGE_MANIFEST_OUT="$WORK/runtime.yaml" SAGE_METADATA_OUT="$WORK/metadata.json" python3 "$ROOT/render.py"
CM_NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["SOURCE_CONFIGMAP"])' "$WORK/metadata.json")"
CM_HASH="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["SOURCE_DIGEST"])' "$WORK/metadata.json")"
kubectl -n sage-runtime create configmap "$CM_NAME" \
  --from-file="requirements.txt=$ROOT/requirements.txt" \
  --from-file="__init__.py=$ROOT/service/__init__.py" \
  --from-file="context.py=$ROOT/service/context.py" \
  --from-file="evidence.py=$ROOT/service/evidence.py" \
  --from-file="main.py=$ROOT/service/main.py" \
  --from-file="handoff.py=$ROOT/service/handoff.py" \
  --from-file="architect.py=$ROOT/service/architect.py" \
  --from-file="probe.py=$ROOT/service/probe.py" \
  --from-file="roles.py=$ROOT/service/roles.py" \
  --from-file="selfcheck.py=$ROOT/service/selfcheck.py" \
  --from-file="workflow.py=$ROOT/service/workflow.py" \
  --dry-run=client -o json | CM_HASH="$CM_HASH" python3 -c 'import json,os,sys; x=json.load(sys.stdin); x["immutable"]=True; x.setdefault("metadata",{}).setdefault("annotations",{})["sage.kalaxy3/source-sha256"]=os.environ["CM_HASH"]; print(json.dumps(x))' \
  | kubectl apply -f -
kubectl apply -f "$WORK/runtime.yaml"
echo 'VERIFY: Kubernetes rollout'
if ! kubectl -n sage-runtime rollout status deployment/sage-runtime --timeout=300s; then
  kubectl -n sage-runtime get pods -l app.kubernetes.io/name=sage-runtime -o wide || true
  kubectl -n sage-runtime get events --sort-by=.metadata.creationTimestamp | tail -n 30 || true
  echo 'BLOCKED: runtime rollout failed; no source success claimed'
  exit 2
fi
echo 'VERIFY: live Git context, Ollama, and LangGraph'
kubectl -n sage-runtime exec deployment/sage-runtime -c runtime -- python3 -m service.selfcheck
echo 'VERIFY: full Architecture Helper API with actual Git/vector retrieval and Ollama'
kubectl -n sage-runtime exec deployment/sage-runtime -c runtime -- python3 -m service.probe
kubectl -n sage-runtime get deployment/sage-runtime pvc/sage-workflow-checkpoints svc/sage-runtime
cat <<'TXT'
SAGE CLUSTER RUNTIME: DEPLOYED AND CHECKED; PROPOSAL HANDOFF IS AVAILABLE.
Governed Git mutation and end-to-end Architecture Helper completion remain separate proof boundaries.
Access from an authorized workstation:
  kubectl -n sage-runtime port-forward svc/sage-runtime 8080:80
  http://localhost:8080/healthz
TXT
