SHELL := /bin/bash

.PHONY: help preflight cluster resources user test-human app jwks sso sso-stop diagram clean

help:
	@echo "make preflight    Comprueba las herramientas"
	@echo "make cluster      Crea el cluster kind"
	@echo "make resources    Crea namespaces, demos y RBAC humano"
	@echo "make user         Crea certificado y contexto de Ana"
	@echo "make test-human   Ejecuta pruebas permitidas/denegadas"
	@echo "make app          Despliega y prueba el ServiceAccount"
	@echo "make jwks         Muestra token, discovery y JWKS"
	@echo "make sso          Levanta Keycloak y la demo OIDC (Reportes es opcional)"
	@echo "make sso-stop     Detiene Keycloak y las apps OIDC"
	@echo "make diagram      Regenera el diagrama (opcional)"
	@echo "make clean        Elimina el cluster y archivos temporales"

preflight:
	@./scripts/preflight.sh

cluster:
	@./scripts/create-cluster.sh

resources:
	@kubectl apply -f manifests/10-workloads.yaml
	@kubectl apply -f manifests/20-human-rbac.yaml
	@kubectl rollout status deployment/demo -n lab-dev --timeout=120s
	@kubectl rollout status deployment/demo -n lab-prod --timeout=120s

user:
	@./scripts/create-user.sh

test-human:
	@./scripts/test-human-rbac.sh

app:
	@kubectl apply -f manifests/30-app-rbac.yaml
	@kubectl rollout status deployment/reporter -n lab-apps --timeout=120s
	@for attempt in {1..20}; do \
	  output="$$(kubectl logs -n lab-apps deployment/reporter 2>/dev/null || true)"; \
	  if grep -q '\[PERMITIDO\]' <<< "$$output"; then printf '%s\n' "$$output"; exit 0; fi; \
	  sleep 1; \
	done; \
	echo "La aplicación no produjo el resultado esperado."; \
	kubectl logs -n lab-apps deployment/reporter; \
	exit 1

jwks:
	@TOKEN="$$(kubectl create token reporter -n lab-apps --duration=15m)"; \
	./scripts/inspect-token.sh "$$TOKEN"; \
	echo; echo "--- Discovery ---"; \
	kubectl get --raw /.well-known/openid-configuration | jq '{issuer,jwks_uri,id_token_signing_alg_values_supported}'; \
	echo; echo "--- kids publicados en JWKS ---"; \
	kubectl get --raw /openid/v1/jwks | jq -r '.keys[].kid'

sso:
	@./scripts/start-sso.sh

sso-stop:
	@./scripts/stop-sso.sh

diagram:
	@python3 docs/diagrams/iam_lab.py
	@python3 docs/diagrams/sso_google.py

clean:
	@./scripts/stop-sso.sh
	@./scripts/cleanup.sh
