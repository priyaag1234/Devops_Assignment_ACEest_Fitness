#!/bin/bash
# ════════════════════════════════════════════════════
#  deploy.sh – Manual deploy / rollback helper
# ════════════════════════════════════════════════════
set -e

NAMESPACE="aceest"
DEPLOYMENT="aceest-deployment"
IMAGE="$1"          # e.g. youruser/aceest-fitness:3.2.4-42

usage() {
    echo "Usage:"
    echo "  $0 deploy  <image:tag>    # Rolling update"
    echo "  $0 rollback               # Undo last deployment"
    echo "  $0 status                 # Show pod status"
    echo "  $0 logs                   # Tail pod logs"
    exit 1
}

case "$1" in
  deploy)
    if [ -z "$2" ]; then usage; fi
    echo "▶ Deploying $2 to namespace $NAMESPACE ..."
    kubectl set image deployment/$DEPLOYMENT aceest-app="$2" -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=120s
    echo "✅ Deployment successful!"
    ;;
  rollback)
    echo "⏪ Rolling back $DEPLOYMENT in $NAMESPACE ..."
    kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=120s
    echo "✅ Rollback complete!"
    ;;
  status)
    echo "=== Pods ==="
    kubectl get pods -n $NAMESPACE -l app=aceest
    echo ""
    echo "=== Deployment ==="
    kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE
    ;;
  logs)
    POD=$(kubectl get pods -n $NAMESPACE -l app=aceest -o jsonpath="{.items[0].metadata.name}")
    echo "=== Logs from $POD ==="
    kubectl logs -f $POD -n $NAMESPACE
    ;;
  *)
    usage
    ;;
esac
