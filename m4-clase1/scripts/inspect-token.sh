#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 1 ]]; then
  echo "Uso: $0 <jwt>"
  exit 1
fi

token="$1"

decode_segment() {
  local segment="$1"
  local padding=$(( (4 - ${#segment} % 4) % 4 ))
  segment="${segment//-/+}"
  segment="${segment//_/\/}"
  segment+=$(printf '=%.0s' $(seq 1 "$padding") 2>/dev/null || true)
  printf '%s' "$segment" | base64 --decode 2>/dev/null
}

IFS='.' read -r header payload _signature <<< "$token"

echo "--- Header: cómo fue firmado ---"
decode_segment "$header" | jq
echo
echo "--- Payload: qué afirma el emisor ---"
decode_segment "$payload" | jq '{iss,sub,aud,iat,exp,"kubernetes.io":."kubernetes.io"}'
