# Keycloak como broker de identidad de Google

Esta extensión permite iniciar sesión en las aplicaciones del laboratorio mediante Google y mostrar información básica del perfil: nombre, apellido, correo y foto.

## Qué estamos construyendo

```text
Portal / Reportes
       │ confían en
       ▼
    Keycloak
       │ delega autenticación
       ▼
     Google
```

Las aplicaciones siguen teniendo un solo proveedor confiable: Keycloak. Google es un proveedor externo que Keycloak utiliza como identity broker.

## 1. Crear el cliente en Google Cloud

En Google Cloud Console:

1. Crear o seleccionar un proyecto de laboratorio.
2. Configurar la pantalla de consentimiento OAuth.
3. Si la aplicación está en modo prueba, agregar las cuentas que participarán como usuarios de prueba.
4. Crear credenciales de tipo **OAuth Client ID → Web application**.
5. Agregar esta URI de redirección autorizada:

```text
http://localhost:8080/realms/formatec/broker/google/endpoint
```

Guardar el Client ID y Client Secret fuera del repositorio.

## 2. Configurar Google en Keycloak

1. Abrir <http://localhost:8080/admin/>.
2. Ingresar como `admin` / `admin`.
3. Seleccionar el realm `formatec`.
4. Entrar en **Identity providers**.
5. Elegir **Google**.
6. Pegar Client ID y Client Secret.
7. Confirmar que los scopes incluyan:

```text
openid profile email
```

8. Guardar.

No habilitar `Store tokens` para esta demostración: la aplicación solo necesita la identidad normalizada que entrega Keycloak.

## 3. Propagar la foto

Nombre, apellido y correo normalmente se importan al perfil federado. Para hacer explícita la foto:

### Mapper del proveedor Google

Dentro del proveedor Google, crear un mapper:

```text
Name: picture from Google
Mapper type: Attribute Importer
Claim: picture
User Attribute Name: picture
```

### Mapper del client scope `profile`

En **Client scopes → profile → Mappers**, crear:

```text
Name: picture
Mapper type: User Attribute
User Attribute: picture
Token Claim Name: picture
Claim JSON Type: String
Add to ID token: On
Add to access token: On
Add to userinfo: On
```

Esto produce una cadena clara:

```text
claim picture de Google
  → atributo picture del usuario Keycloak
  → claim picture entregado a la aplicación
```

## 4. Probar

1. Cerrar la sesión central desde cualquiera de las aplicaciones.
2. Abrir <http://localhost:5100>.
3. Elegir iniciar sesión.
4. En la pantalla de Keycloak elegir Google.
5. Otorgar consentimiento para `profile` y `email`.
6. Verificar nombre, apellido, correo y foto en el Portal.
7. Abrir <http://localhost:5101> y confirmar el SSO.

## Qué datos pedimos y cuáles no

| Scope | Datos necesarios para la demo |
|---|---|
| `openid` | identificador de identidad (`sub`) |
| `profile` | nombre, apellido y foto disponibles |
| `email` | correo y estado de verificación |

No solicitamos acceso a:

- contactos;
- Google Drive;
- calendario;
- archivos;
- contraseña de Google.

## Preguntas para el grupo

1. ¿Quién autenticó realmente al usuario?
2. ¿Quién emitió el token que consume nuestra aplicación?
3. ¿Por qué `sub` es mejor identificador que el correo?
4. ¿Mostrar la foto significa que la app puede leer Google Drive?
5. ¿Qué ocurriría si una aplicación pidiera scopes adicionales?

## Referencias oficiales

- [Keycloak: integración de proveedores de identidad](https://www.keycloak.org/docs/latest/server_admin/#_identity_broker)
- [Google: OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)
- [Google: claims del endpoint UserInfo](https://developers.google.com/identity/openid-connect/reference#obtainuserinfo)
