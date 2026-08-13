# Guía de clase paso a paso — IAM, Kubernetes y Google

Duración objetivo: **1 hora 20 minutos**.

Esta guía no es solamente una lista de comandos. En cada bloque indica:

- qué concepto explicar;
- qué decir antes de ejecutar;
- qué comando usar;
- qué parte de la salida observar;
- qué conclusión obtener;
- cómo enlazar con el bloque siguiente.

## Resultado que debe entender el estudiante

Al finalizar, el estudiante debería poder explicar este recorrido con sus palabras:

```text
Identidad → credencial → autenticación → autorización → decisión
```

Y distinguir dos escenarios:

```text
Persona → certificado → Kubernetes → RBAC
Aplicación → Keycloak → Google → token OIDC
```

La frase que ordena toda la clase es:

> Autenticar es comprobar quién sos. Autorizar es decidir qué podés hacer.

---

# Preparación del docente — antes de la clase

No hacer descargas ni configurar Google frente al curso. El tiempo de aula debe usarse para comprender IAM.

Desde `m4-clase1`:

```bash
make preflight
make cluster
make resources
make app
make sso
```

Comprobar:

```bash
kubectl get nodes
kubectl get pods -A
curl -I http://localhost:5100
curl -s http://localhost:8080/realms/formatec/.well-known/openid-configuration | jq .issuer
```

También debe estar configurado el cliente OAuth de Google y el proveedor Google de Keycloak siguiendo [keycloak-google.md](keycloak-google.md).

Para mantener una dificultad intermedia:

- Kubernetes corre en un clúster local `kind` sobre Docker.
- Keycloak y las aplicaciones corren en contenedores Docker locales.
- Solamente el navegador y Keycloak se comunican hacia Internet con Google.
- Ningún servicio del laboratorio se publica en Internet.

---

# 0–7 min — Construir el mapa mental

## Objetivo

Separar identidad, credencial, autenticación y autorización antes de tocar Kubernetes.

## Qué decir

> Cuando alguien intenta acceder a un sistema, el sistema necesita responder cuatro preguntas: quién es, cómo lo demuestra, qué quiere hacer y si está permitido.

Escribir o mostrar:

| Pregunta | Concepto | Ejemplo de la clase |
|---|---|---|
| ¿Quién sos? | identidad | `ana`, grupo `developers` |
| ¿Cómo lo demostrás? | credencial | certificado X.509 |
| ¿Qué querés hacer? | solicitud | `update deployments` |
| ¿Está permitido? | autorización | Role + RoleBinding |

## Primer ejemplo verbal

```text
ana + update + deployments + lab-prod
```

Preguntar al grupo:

> ¿Con saber que es Ana alcanza para permitir la operación?

Respuesta esperada: **no**. Conocer la identidad significa que la autenticación funcionó; todavía falta evaluar permisos.

## Qué mostrar

```bash
kubectl get namespaces
```

Explicar cada ambiente:

- `lab-dev`: los desarrolladores pueden observar y modificar Deployments.
- `lab-prod`: los desarrolladores solamente pueden observar.
- `lab-apps`: aloja una aplicación con identidad propia.

## Transición

> Primero haremos que Kubernetes reconozca a una persona. Después le asignaremos permisos.

---

# 7–17 min — Autenticar una persona con certificado

## Objetivo

Mostrar que Kubernetes recibe usuarios desde un mecanismo externo: no existe un objeto Kubernetes `User` que vayamos a crear.

## Qué explicar antes del comando

Un certificado cliente contiene una identidad firmada por una autoridad confiable. En este laboratorio:

```text
CN=ana          → nombre de usuario
O=developers    → grupo
```

`CN` significa **Common Name**. `O` significa **Organization**; Kubernetes lo interpreta como grupo cuando autentica mediante certificados X.509.

## Qué ejecutar

```bash
make user
```

## Qué hace realmente el comando

Abrir [scripts/create-user.sh](../scripts/create-user.sh) y recorrer sus pasos sin explicar cada opción de OpenSSL:

1. Genera una clave privada para Ana.
2. Crea una solicitud de certificado o CSR.
3. La envía al API Server.
4. Un administrador del laboratorio la aprueba.
5. Kubernetes entrega el certificado firmado.
6. Se crea el contexto `ana@iam-lab` en el kubeconfig.

## Inspeccionar la evidencia

```bash
kubectl get csr ana-iam-lab
kubectl describe csr ana-iam-lab
kubectl --context ana@iam-lab auth whoami
```

Detenerse en:

```text
Username   ana
Groups     [developers system:authenticated]
```

## Qué significa `--context`

`kubectl` puede guardar varias identidades y clústeres. El contexto indica cuál usar para esta solicitud.

```text
sin --context             → identidad administrativa actual
--context ana@iam-lab     → certificado de Ana
```

## Pregunta de control

> ¿El certificado dice que Ana puede modificar producción?

Respuesta: **no**. Solamente permite reconocerla como `ana` y miembro de `developers`.

## Transición

> Ya sabemos quién hace la solicitud. Ahora necesitamos transformar el grupo `developers` en permisos concretos.

---

# 17–32 min — Autorizar mediante Kubernetes RBAC

## Objetivo

Entender los cuatro objetos o elementos del modelo:

```text
Subject → RoleBinding → Role → reglas
```

## Qué mostrar

Abrir [manifests/20-human-rbac.yaml](../manifests/20-human-rbac.yaml).

### Role

Explicar esta regla:

```yaml
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "patch", "update"]
```

Traducción:

> Este Role permite consultar y modificar Deployments dentro del namespace donde fue creado. No permite crearlos ni borrarlos.

Definir los campos:

- `apiGroups`: familia de la API que contiene el recurso.
- `resources`: objetos afectados.
- `verbs`: operaciones permitidas.
- `namespace`: alcance del Role.

### RoleBinding

Mostrar:

```yaml
subjects:
  - kind: Group
    name: developers
roleRef:
  kind: Role
  name: developer
```

Traducción:

> Todos los usuarios autenticados que pertenezcan al grupo `developers` reciben el Role `developer` en `lab-dev`.

Remarcar que el Role define permisos, pero el RoleBinding decide quién los recibe.

## Aplicar la política

```bash
kubectl apply -f manifests/20-human-rbac.yaml
```

Explicar que `apply` declara el estado deseado. Si los objetos ya existen, Kubernetes los actualiza; no necesitamos recrearlos manualmente.

## Preguntar antes de ejecutar

```bash
kubectl --context ana@iam-lab auth can-i list pods -n lab-dev
kubectl --context ana@iam-lab auth can-i update deployments -n lab-dev
kubectl --context ana@iam-lab auth can-i update deployments -n lab-prod
kubectl --context ana@iam-lab auth can-i get secrets -n lab-dev
```

Resultados:

```text
yes
yes
no
no
```

Explicar cada parte de una línea:

```text
kubectl
  --context ana@iam-lab     identidad usada
  auth can-i                consulta al autorizador
  update deployments        verbo y recurso
  -n lab-prod               alcance
```

## Ejecutar una operación real

Permitida:

```bash
kubectl --context ana@iam-lab scale deployment demo --replicas=2 -n lab-dev
```

Denegada intencionalmente:

```bash
kubectl --context ana@iam-lab scale deployment demo --replicas=2 -n lab-prod
```

## Interpretar `Forbidden`

> `Forbidden` no significa “no sé quién sos”. Kubernetes muestra `Forbidden` precisamente porque autenticó a Ana, evaluó sus permisos y no encontró autorización suficiente.

Diferencia conceptual:

```text
401 / no autenticado → no se pudo establecer la identidad
403 / Forbidden      → identidad conocida, acción no autorizada
```

## Regla fundamental de RBAC

Kubernetes RBAC es aditivo:

- las reglas agregan permisos;
- no escribimos reglas `deny`;
- si ninguna regla permite una acción, queda denegada.

Ejecutar la matriz completa:

```bash
make test-human
```

## Transición

> Ya resolvimos la identidad de una persona. Pero una aplicación que corre todo el día no debería usar el certificado personal de Ana.

---

# 32–45 min — Identidad de aplicaciones con ServiceAccount

## Objetivo

Mostrar que una carga de trabajo necesita identidad propia y permisos mínimos.

## Qué explicar

Un `ServiceAccount` no representa a una persona. Representa a un proceso que corre dentro del clúster.

```text
Persona       → certificado → usuario ana
Aplicación    → JWT montado → ServiceAccount reporter
```

La identidad completa será:

```text
system:serviceaccount:lab-apps:reporter
```

Se compone de:

- prefijo `system:serviceaccount`;
- namespace `lab-apps`;
- nombre `reporter`.

## Recorrer el manifiesto

Abrir [manifests/30-app-rbac.yaml](../manifests/30-app-rbac.yaml) y señalar:

1. `ServiceAccount reporter`: identidad.
2. `Role pod-reader`: puede leer Pods.
3. `RoleBinding reporter-pod-reader`: conecta identidad y permisos.
4. `serviceAccountName: reporter`: hace que el Pod utilice esa identidad.
5. El cliente Python: llama a la API de Kubernetes desde el Pod.

## Qué hace el cliente Python

Dentro del contenedor, Kubernetes monta automáticamente:

```text
/var/run/secrets/kubernetes.io/serviceaccount/token
/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
/var/run/secrets/kubernetes.io/serviceaccount/namespace
```

La aplicación:

1. lee el token;
2. llama al API Server usando `Authorization: Bearer ...`;
3. intenta listar Pods;
4. intenta listar Secrets.

## Ejecutar

```bash
make app
kubectl logs -n lab-apps deployment/reporter
```

Salida esperada:

```text
Identidad: system:serviceaccount:lab-apps:reporter
[PERMITIDO] list pods: HTTP 200
[DENEGADO]  list secrets: HTTP 403
```

## Interpretación

- HTTP `200`: el token es válido y RBAC permite listar Pods.
- HTTP `403`: el mismo token es válido, pero RBAC no permite leer Secrets.

Preguntar:

> ¿La aplicación está rota porque no puede leer Secrets?

Respuesta: **no**. Ése es el resultado seguro. La aplicación puede cumplir su función sin acceder a información sensible.

## Idea de menor privilegio

> Una identidad debe tener exactamente los permisos necesarios para su tarea y nada más.

## Transición

> Sabemos que el Pod presenta un token. Ahora vamos a abrirlo y entender cómo otro sistema puede verificarlo.

---

# 45–55 min — JWT, discovery y JWKS

## Objetivo

Comprender un token firmado sin convertir la clase en criptografía.

## Crear un token temporal

```bash
TOKEN=$(kubectl create token reporter -n lab-apps --duration=15m)
./scripts/inspect-token.sh "$TOKEN"
```

Explicar que un JWT tiene tres partes separadas por puntos:

```text
header.payload.signature
```

- Header: algoritmo y clave utilizada.
- Payload: claims o afirmaciones.
- Signature: permite detectar modificaciones y verificar al emisor.

## Claims que deben observar

| Claim | Pregunta que responde |
|---|---|
| `iss` | ¿Quién emitió el token? |
| `sub` | ¿Qué identidad representa? |
| `aud` | ¿Para quién fue creado? |
| `exp` | ¿Cuándo deja de ser válido? |
| `kid` | ¿Qué clave pública permite verificar la firma? |

## Discovery

```bash
kubectl get --raw /.well-known/openid-configuration | jq
```

Qué explicar:

> El discovery document es un documento de metadatos. Permite que un cliente descubra el issuer, el endpoint de claves y otras capacidades sin inventar direcciones.

## JWKS

```bash
kubectl get --raw /openid/v1/jwks | jq
```

JWKS significa **JSON Web Key Set**. Publica claves públicas; no contiene la clave privada del emisor.

Comparar:

```bash
./scripts/inspect-token.sh "$TOKEN" | grep kid
kubectl get --raw /openid/v1/jwks | jq -r '.keys[].kid'
```

Conclusión:

> El `kid` del JWT indica qué clave del JWKS debe usar el receptor para comprobar la firma.

No afirmar que decodificar equivale a validar:

```text
decodificar → leer contenido
validar     → comprobar firma, issuer, audience y vencimiento
```

## Transición

> Kubernetes hizo esto para una carga de trabajo. Ahora veremos el mismo modelo con una persona que inicia sesión en una aplicación cloud.

---

# 55–75 min — Aplicación, Keycloak y Google

## Objetivo

Mostrar federación real: la aplicación confía en Keycloak y Keycloak delega el login en Google.

## Dibujar el flujo antes de abrir el navegador

```text
1. Usuario abre Portal
2. Portal redirige a Keycloak
3. Usuario elige Google
4. Google autentica al usuario
5. Google devuelve la identidad a Keycloak
6. Keycloak importa o vincula al usuario
7. Keycloak emite su propio token
8. Portal valida y consume el token de Keycloak
```

## Definir los participantes

| Participante | Responsabilidad |
|---|---|
| Portal Flask | aplicación o cliente OIDC |
| Keycloak | proveedor confiable para el Portal e identity broker |
| Google | proveedor externo que autentica la cuenta |
| Usuario | elige proveedor y presta consentimiento |

## Aclarar OAuth y OIDC

Explicación breve:

- OAuth 2.0 delega acceso mediante tokens.
- OpenID Connect agrega una capa de identidad sobre OAuth 2.0.
- El scope `openid` indica que queremos autenticación OIDC.
- `profile` y `email` solicitan datos básicos del perfil.

Para esta demostración no pedimos Drive, contactos ni calendario.

## Paso 1 — Mostrar el Portal sin sesión

Abrir <http://localhost:5100>.

Qué decir:

> El Portal no tiene formulario de contraseña ni una integración directa con Google. Su único proveedor configurado es Keycloak.

Seleccionar **Iniciar sesión con Keycloak**.

## Paso 2 — Mostrar las dos posibilidades de Keycloak

En la pantalla de Keycloak señalar:

- usuario y contraseña local;
- botón Google.

Explicar:

> Keycloak puede autenticar desde su propia base o actuar como intermediario hacia otro proveedor. En esta clase elegiremos Google.

## Paso 3 — Elegir Google

Seleccionar **Google** y luego la cuenta de prueba.

Antes de continuar, detenerse en la pantalla de consentimiento:

- nombre e imagen de perfil;
- dirección de correo;
- ausencia de Drive, contactos o calendario.

Qué decir:

> La contraseña se introduce en el dominio de Google. Ni el Portal ni Keycloak reciben esa contraseña.

Continuar.

## Paso 4 — Inspeccionar el resultado en el Portal

El Portal debe mostrar:

```text
name                 Jose Videla Olmos
email                jvidelaolmos@gmail.com
identity_provider    google
iss                  http://localhost:8080/realms/formatec
```

Interpretar las dos evidencias principales:

- `identity_provider=google`: Google fue el proveedor externo usado para autenticar.
- `iss=.../realms/formatec`: el token que consume el Portal fue emitido por Keycloak.

Ésta es la diferencia central:

```text
Google comprueba la cuenta
Keycloak emite la identidad que confía la aplicación
```

## Paso 5 — Mostrar el usuario federado

Abrir la consola de administración de Keycloak:

```text
http://localhost:8080/admin/
```

Entrar al realm `formatec` → **Users** → usuario de Google.

Mostrar la identidad federada vinculada.

Qué explicar:

> En el primer login, Keycloak crea o vincula una representación local del usuario. Eso permite que nuestras aplicaciones trabajen con una identidad consistente aunque el login haya ocurrido en Google.

## Paso 6 — Volver a discovery y JWKS

```bash
curl -s http://localhost:8080/realms/formatec/.well-known/openid-configuration \
  | jq '{issuer,authorization_endpoint,token_endpoint,userinfo_endpoint,jwks_uri}'

curl -s http://localhost:8080/realms/formatec/protocol/openid-connect/certs \
  | jq '.keys[] | {kid, kty, alg}'
```

Conectar con el bloque anterior:

> Igual que con el ServiceAccount, la aplicación descubre al emisor y obtiene sus claves públicas. La diferencia es que ahora el sujeto es una persona y Keycloak es el issuer.

## Extensión opcional — SSO

Si quedan dos o tres minutos, abrir <http://localhost:5101> y seleccionar login.

Keycloak reutiliza la sesión existente. No es necesario autenticarse nuevamente con Google.

Definición:

> SSO permite que varias aplicaciones confíen en una sesión central de autenticación.

No confundir:

- federación: Keycloak confía en una identidad externa de Google;
- SSO: dos aplicaciones reutilizan una sesión de Keycloak.

## Transición

> Ya vimos personas y aplicaciones, credenciales largas y tokens temporales, y permisos humanos y de workloads. Cerremos uniendo el modelo.

---

# 75–80 min — Cierre y comprobación

## Reconstruir el modelo completo

| Caso | Identidad | Credencial | Autentica | Autoriza |
|---|---|---|---|---|
| Ana en Kubernetes | `ana`, grupo `developers` | certificado X.509 | API Server | Kubernetes RBAC |
| Pod reporter | ServiceAccount `reporter` | JWT temporal | API Server | Kubernetes RBAC |
| Usuario del Portal | usuario federado | flujo OIDC | Google + Keycloak | la aplicación o sus roles |

## Preguntas de comprobación

1. ¿Por qué el certificado de Ana no contiene sus permisos?
2. ¿Qué diferencia existe entre Role y RoleBinding?
3. ¿Por qué un `403 Forbidden` demuestra que la identidad pudo autenticarse?
4. ¿Por qué el Pod usa ServiceAccount y no la identidad del docente?
5. ¿Qué relación existe entre `kid` y JWKS?
6. ¿Quién autenticó la cuenta de Google?
7. ¿Quién emitió el token consumido por el Portal?
8. ¿Qué diferencia existe entre federación y SSO?

## Respuestas esperadas

1. La credencial prueba identidad; RBAC define permisos por separado.
2. Role contiene reglas; RoleBinding las asigna a sujetos.
3. El sistema conoce al sujeto, pero no encontró una regla que permita la acción.
4. Cada workload debe tener identidad propia y permisos mínimos.
5. `kid` selecciona la clave pública con la que se verifica la firma.
6. Google comprobó la cuenta.
7. Keycloak emitió el token confiado por el Portal.
8. Federación conecta dominios/proveedores de identidad; SSO reutiliza una sesión entre aplicaciones.

## Frase final

> IAM no es solamente crear usuarios. Es establecer identidades verificables y controlar, con el menor privilegio posible, qué puede hacer cada persona o aplicación.

---

# Si algo falla durante la demostración

## Ana aparece como administradora

Verificar que el comando incluya:

```bash
--context ana@iam-lab
```

## Una operación devuelve `Forbidden`

Primero revisar si era una denegación intencional. Usar:

```bash
kubectl --context ana@iam-lab auth can-i VERBO RECURSO -n NAMESPACE
```

## El reporter no muestra logs

```bash
kubectl get pods -n lab-apps
kubectl describe pod -n lab-apps -l app=reporter
kubectl logs -n lab-apps deployment/reporter
```

## No aparece el botón Google

Confirmar el proveedor en:

```text
Keycloak → realm formatec → Identity providers → Google
```

## Google informa redirect URI inválida

La URI registrada debe coincidir exactamente:

```text
http://localhost:8080/realms/formatec/broker/google/endpoint
```

## El Portal no abre

```bash
docker compose ps
docker compose logs portal
docker compose logs keycloak
```

