#!/usr/bin/env bash
set -euo pipefail

missing=0
for command_name in docker kind kubectl openssl jq python3 curl; do
  if command -v "$command_name" >/dev/null 2>&1; then
    printf '✓ %s\n' "$command_name"
  else
    printf '✗ falta %s\n' "$command_name"
    missing=1
  fi
done

if ! docker info >/dev/null 2>&1; then
  echo "✗ Docker está instalado pero el daemon no responde"
  missing=1
else
  echo "✓ Docker responde"
fi

if [[ "$missing" -ne 0 ]]; then
  echo "Revisá los requisitos del README antes de continuar."
  exit 1
fi

echo "Entorno listo."
