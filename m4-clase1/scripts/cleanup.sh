#!/usr/bin/env bash
set -euo pipefail

kubectl config delete-context ana@iam-lab >/dev/null 2>&1 || true
kubectl config delete-user ana >/dev/null 2>&1 || true

if command -v kind >/dev/null 2>&1 && kind get clusters 2>/dev/null | grep -Fxq iam-lab; then
  kind delete cluster --name iam-lab
else
  echo "El cluster iam-lab no existe."
fi

if [[ -d .lab ]]; then
  mv .lab ".lab.cleaned.$(date +%s)"
  echo "Las credenciales locales se movieron a un directorio .lab.cleaned.* ignorado por Git."
fi
