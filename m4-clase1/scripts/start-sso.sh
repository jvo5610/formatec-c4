#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build

echo "Esperando a Keycloak..."
for _ in {1..60}; do
  if curl -fsS \
    http://localhost:8080/realms/formatec/.well-known/openid-configuration \
    >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -fsS \
  http://localhost:8080/realms/formatec/.well-known/openid-configuration \
  >/dev/null; then
  echo "Keycloak no quedó disponible. Revisá: docker compose logs keycloak"
  exit 1
fi

for url in http://localhost:5100 http://localhost:5101; do
  for _ in {1..30}; do
    if curl -fsS "$url" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  curl -fsS "$url" >/dev/null
done

echo "Entorno SSO listo:"
echo "  Keycloak: http://localhost:8080  (admin / admin)"
echo "  Portal:   http://localhost:5100"
echo "  Reportes: http://localhost:5101"
echo "  Usuario:  ana / ana123"
