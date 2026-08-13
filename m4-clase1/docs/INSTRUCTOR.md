# Guía docente

La guía narrativa completa para dictar los 80 minutos está en [GUIA-DE-CLASE.md](GUIA-DE-CLASE.md). Este archivo queda como referencia rápida de preparación, ideas centrales y fallos esperados.

## Objetivo de aprendizaje

Al finalizar, el estudiante debe poder explicar que Kubernetes primero autentica una identidad y luego RBAC evalúa si una combinación de sujeto, verbo, recurso y alcance está permitida.

## Preparación previa

Ejecutar antes de la clase:

```bash
make preflight
make cluster
make resources
make sso
```

Esto descarga las imágenes y evita consumir tiempo de clase por la red.

Si se mostrará el login con Google, completar además la configuración de [keycloak-google.md](keycloak-google.md) y probarla con la cuenta que se usará en vivo. El Client ID y Client Secret de Google no se guardan en Git.

## Hilo conductor

Usar siempre la misma solicitud:

```text
¿Puede esta identidad ejecutar este verbo sobre este recurso en este namespace?
```

### Bloque 1 — Ana

- Certificado: autenticación.
- `CN=ana`: nombre de usuario.
- `O=developers`: pertenencia al grupo.
- Role: conjunto de permisos.
- RoleBinding: unión entre sujeto y Role.

### Bloque 2 — Diferencia entre ambientes

No explicar `lab-prod` como una denegación explícita. Kubernetes RBAC agrega permisos. En producción solo se otorga lectura; por ausencia de permiso, modificar queda denegado.

### Bloque 3 — Aplicación

La aplicación no “hereda” la identidad del docente ni del usuario que desplegó el Pod. El ServiceAccount es su identidad en tiempo de ejecución.

### Bloque 4 — JWT y JWKS

No profundizar en RSA. Alcanzan cuatro ideas:

1. el token contiene afirmaciones (`claims`);
2. el emisor lo firma con una clave privada;
3. publica la clave pública en JWKS;
4. el receptor verifica firma, issuer, audiencia y vencimiento.

### Bloque 5 — Federación con Google

La demostración principal usa un solo Portal. Primero hacer un login local de control; después cerrar sesión y elegir Google. La app confía en Keycloak; Keycloak delega la autenticación en Google y luego emite el token que consume el Portal.

Mostrar cinco evidencias: pantalla de Google, `identity_provider=google`, usuario federado en Keycloak, `iss` de Keycloak y correspondencia del `kid` con su JWKS. Si queda tiempo, usar Reportes para mostrar SSO.

Configurar el OAuth Client y los mappers antes de la clase. No emplear tiempo de aula creando el proyecto de Google Cloud.

### Bloque 6 — Cloud

GitHub Actions → AWS repite el mismo patrón para una carga de trabajo externa. No presentarlo como SSO humano.

## Fallos esperados

- `Forbidden` en producción: resultado correcto.
- `Forbidden` al leer Secrets: resultado correcto.
- Si `auth whoami` muestra al administrador, verificar que se usó `--context ana@iam-lab`.
- Si el CSR no emite certificado, revisar `kubectl describe csr ana-iam-lab`.
- Si el Pod tarda, revisar `kubectl get pods -n lab-apps` y la descarga de `python:3.12-alpine`.

## Pregunta desafío

Pedir que agreguen `configmaps` al Role de `reporter` sin tocar Secrets. Luego deben probar ambos resultados con `kubectl auth can-i`.
