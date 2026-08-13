#!/usr/bin/env bash
set -euo pipefail

context="ana@iam-lab"
failures=0

assert_can() {
  local expected="$1"
  local verb="$2"
  local resource="$3"
  local namespace="$4"
  local actual

  actual=$(kubectl --context "$context" auth can-i "$verb" "$resource" -n "$namespace" 2>/dev/null || true)
  if [[ "$actual" == "$expected" ]]; then
    printf '✓ %-3s  %-6s %-12s en %s\n' "$actual" "$verb" "$resource" "$namespace"
  else
    printf '✗ esperado=%s actual=%s para %s %s en %s\n' \
      "$expected" "$actual" "$verb" "$resource" "$namespace"
    failures=$((failures + 1))
  fi
}

echo "Identidad observada por Kubernetes:"
kubectl --context "$context" auth whoami
echo
echo "Matriz de autorización:"

assert_can yes list pods lab-dev
assert_can yes update deployments.apps lab-dev
assert_can yes list pods lab-prod
assert_can no update deployments.apps lab-prod
assert_can no get secrets lab-dev
assert_can no get secrets lab-prod

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

echo
echo "Todas las decisiones coinciden con la política esperada."
