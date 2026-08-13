#!/usr/bin/env bash
set -euo pipefail

lab_dir=".lab/ana"
csr_name="ana-iam-lab"
cluster_context="kind-iam-lab"

mkdir -p "$lab_dir"
kubectl config use-context "$cluster_context" >/dev/null

if [[ ! -f "$lab_dir/ana.key" ]]; then
  openssl genrsa -out "$lab_dir/ana.key" 2048 >/dev/null 2>&1
fi

openssl req -new \
  -key "$lab_dir/ana.key" \
  -out "$lab_dir/ana.csr" \
  -subj "/CN=ana/O=developers"

csr_request=$(base64 < "$lab_dir/ana.csr" | tr -d '\n')

kubectl delete csr "$csr_name" --ignore-not-found >/dev/null
sed "s|CSR_REQUEST|$csr_request|" manifests/40-ana-csr.yaml | kubectl apply -f - >/dev/null
kubectl certificate approve "$csr_name" >/dev/null

for _ in {1..20}; do
  certificate=$(kubectl get csr "$csr_name" -o jsonpath='{.status.certificate}' 2>/dev/null || true)
  if [[ -n "$certificate" ]]; then
    printf '%s' "$certificate" | base64 --decode > "$lab_dir/ana.crt"
    break
  fi
  sleep 1
done

if [[ ! -s "$lab_dir/ana.crt" ]]; then
  echo "Kubernetes no emitió el certificado de Ana."
  exit 1
fi

cluster_name=$(kubectl config view -o jsonpath="{.contexts[?(@.name=='$cluster_context')].context.cluster}")

kubectl config set-credentials ana \
  --client-certificate="$lab_dir/ana.crt" \
  --client-key="$lab_dir/ana.key" \
  --embed-certs=true >/dev/null

kubectl config set-context ana@iam-lab \
  --cluster="$cluster_name" \
  --user=ana \
  --namespace=lab-dev >/dev/null

echo "Identidad creada. Probando autenticación:"
kubectl --context ana@iam-lab auth whoami
