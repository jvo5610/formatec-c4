import os
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, render_template_string, session, url_for


APP_NAME = os.environ.get("APP_NAME", "Portal")
CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "portal")
CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "portal-lab-secret")
KEYCLOAK_PUBLIC_URL = os.environ.get(
    "KEYCLOAK_PUBLIC_URL", "http://localhost:8080"
)
KEYCLOAK_INTERNAL_URL = os.environ.get(
    "KEYCLOAK_INTERNAL_URL", KEYCLOAK_PUBLIC_URL
)
REALM = os.environ.get("KEYCLOAK_REALM", "formatec")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "solo-para-el-laboratorio")
app.config["SESSION_COOKIE_NAME"] = f"formatec_{CLIENT_ID}_session"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

oauth = OAuth(app)
keycloak = oauth.register(
    name="keycloak",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_url=(
        f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}/protocol/openid-connect/auth"
    ),
    access_token_url=(
        f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token"
    ),
    userinfo_endpoint=(
        f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
    ),
    jwks_uri=(
        f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"
    ),
    server_metadata={
        "issuer": f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}",
        "authorization_endpoint": (
            f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}/protocol/openid-connect/auth"
        ),
        "token_endpoint": (
            f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token"
        ),
        "userinfo_endpoint": (
            f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/userinfo"
        ),
        "jwks_uri": (
            f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"
        ),
    },
    client_kwargs={"scope": "openid profile email"},
)

PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ app_name }} · Formatec</title>
  <style>
    :root { color-scheme: light; font-family: Inter, system-ui, sans-serif; }
    body { margin: 0; background: #f5faf5; color: #0b1f3a; }
    main { max-width: 850px; margin: 48px auto; padding: 36px; background: white;
           border: 1px solid #b8dcb8; border-radius: 22px; box-shadow: 0 14px 45px #0b5d1e18; }
    h1, h2 { color: #08711a; }
    .tag { color: #08711a; font-weight: 700; }
    a.button { display: inline-block; padding: 12px 18px; border-radius: 10px;
               background: #08711a; color: white; text-decoration: none; font-weight: 700; }
    .profile { display: grid; grid-template-columns: 110px 1fr; gap: 24px; align-items: center; }
    img, .avatar { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; }
    .avatar { display: grid; place-items: center; background: #d9efd9; color: #08711a;
              font-size: 34px; font-weight: 800; }
    table { border-collapse: collapse; width: 100%; margin: 24px 0; }
    th, td { padding: 10px; border-bottom: 1px solid #dce8dc; text-align: left; }
    th { width: 180px; color: #08711a; }
    code { overflow-wrap: anywhere; }
    .note { background: #eef8ee; padding: 14px; border-left: 4px solid #08711a; }
    .provider { display: inline-block; margin: 8px 0 18px; padding: 7px 12px;
                border: 1px solid #87bf8a; border-radius: 999px; background: #eef8ee;
                color: #08711a; font-weight: 800; }
  </style>
</head>
<body><main>
  <p class="tag">Cliente OIDC: {{ client_id }}</p>
  <h1>{{ app_name }}</h1>
  {% if not user %}
    <p>Esta aplicación confía solamente en Keycloak. Desde allí podés usar una cuenta local
       o elegir Google sin entregar la contraseña a la aplicación.</p>
    <a class="button" href="{{ url_for('login') }}">Iniciar sesión con Keycloak</a>
  {% else %}
    <section class="profile">
      {% if user.get('picture') %}
        <img src="{{ user.get('picture') }}" alt="Foto del perfil">
      {% else %}
        <div class="avatar">{{ (user.get('given_name') or user.get('preferred_username') or '?')[0] }}</div>
      {% endif %}
      <div>
        <h2>{{ user.get('name') or user.get('preferred_username') }}</h2>
        <p>{{ user.get('email', 'Sin correo disponible') }}</p>
        <span class="provider">Origen: {{ user.get('identity_provider', 'cuenta local de Keycloak') }}</span>
      </div>
    </section>
    <table>
      {% for claim in claims %}
      <tr><th>{{ claim }}</th><td><code>{{ user.get(claim, '—') }}</code></td></tr>
      {% endfor %}
    </table>
    <p class="note"><strong>La app recibió identidad de Keycloak.</strong> Si el origen dice
      <code>google</code>, Google autenticó al usuario, pero el token consumido por esta app
      fue emitido y firmado por Keycloak.</p>
    <a class="button" href="{{ url_for('logout') }}">Cerrar sesión central</a>
  {% endif %}
</main></body></html>
"""


@app.get("/")
def home():
    return render_template_string(
        PAGE,
        app_name=APP_NAME,
        client_id=CLIENT_ID,
        user=session.get("user"),
        claims=[
            "identity_provider",
            "sub",
            "preferred_username",
            "given_name",
            "family_name",
            "email",
            "email_verified",
            "picture",
            "iss",
        ],
    )


@app.get("/login")
def login():
    return keycloak.authorize_redirect(url_for("callback", _external=True))


@app.get("/callback")
def callback():
    token = keycloak.authorize_access_token()
    user = dict(keycloak.userinfo(token=token))
    # Authlib valida el ID token y deja sus claims en `userinfo`. Allí aparecen
    # datos del emisor como `iss`, que el endpoint UserInfo no siempre repite.
    id_token_claims = dict(token.get("userinfo") or {})
    user.update(id_token_claims)
    session["user"] = user
    session["id_token"] = token.get("id_token")
    return redirect(url_for("home"))


@app.get("/logout")
def logout():
    session.clear()
    params = {"post_logout_redirect_uri": url_for("home", _external=True)}
    # En este laboratorio el client_id alcanza para validar la redirección.
    # Evita acoplar la demo a diferencias de validación de id_token_hint.
    params["client_id"] = CLIENT_ID
    return redirect(
        f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}/protocol/openid-connect/logout?"
        + urlencode(params)
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
