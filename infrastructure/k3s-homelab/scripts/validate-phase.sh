#!/usr/bin/env bash
set -euo pipefail

phase="${1:-}"
export KUBECONFIG="${KUBECONFIG:-$PWD/kubeconfig-kalaxy3.yaml}"

case "$phase" in
  1)
    .venv/bin/ansible all -m ping
    .venv/bin/ansible rpi_nodes -b -m shell \
      -a 'findmnt /mnt/minio && df -h /mnt/minio'
    ;;
  2)
    kubectl get nodes -o wide
    kubectl get pods -n kube-system -o wide
    kubectl wait --for=condition=Ready nodes --all --timeout=5m
    ;;
  3)
    kubectl get ipaddresspools,l2advertisements -n metallb-system
    kubectl get svc -n kube-system traefik -o wide
    kubectl get storageclass
    ;;
  4)
    kubectl get pods,svc -n headlamp
    kubectl get pods,svc -n kubernetes-dashboard 2>/dev/null || true
    ;;
  5)
    kubectl get pods,pvc -n observability
    kubectl get pods,pvc -n kubecost
    ;;
  6)
    kubectl get pods,pv,pvc,svc -n minio -o wide
    ;;
  *)
    echo "Usage: $0 {1|2|3|4|5|6}" >&2
    exit 2
    ;;
esac
