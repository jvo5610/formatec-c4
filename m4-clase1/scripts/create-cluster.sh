#!/usr/bin/env bash
set -euo pipefail

cluster_name="iam-lab"

if kind get clusters 2>/dev/null | grep -Fxq "$cluster_name"; then
  echo "El cluster $cluster_name ya existe."
else
  kind create cluster --config kind-config.yaml --wait 120s
fi

kubectl config use-context "kind-$cluster_name" >/dev/null
kubectl get nodes
