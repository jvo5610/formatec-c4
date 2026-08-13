# Extensión conceptual — GitHub Actions y AWS mediante OIDC

Esta extensión conecta el laboratorio local con un caso cloud frecuente. No es una demostración de SSO humano: es **federación de identidad de una carga de trabajo**.

## El problema

Un workflow necesita acceder a AWS. La solución antigua consiste en guardar:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

Son credenciales permanentes que deben almacenarse y rotarse.

## El modelo federado

```text
GitHub Actions
  → obtiene un JWT OIDC temporal
  → AWS valida issuer, audiencia, firma y subject
  → STS permite asumir un rol
  → entrega credenciales temporales
```

## Correspondencia con el laboratorio

| Laboratorio Kubernetes | AWS |
|---|---|
| API Server publica discovery y JWKS | GitHub publica discovery y JWKS |
| JWT identifica al ServiceAccount | JWT identifica repositorio/rama/environment |
| RoleBinding vincula sujeto y Role | Trust policy vincula claims y rol IAM |
| Role limita verbos y recursos | IAM policy limita acciones y recursos |

## Workflow mínimo

```yaml
name: Identidad federada

on:
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  identity:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v5
        with:
          role-to-assume: arn:aws:iam::123456789012:role/formatec-github-oidc
          aws-region: us-east-1

      - run: aws sts get-caller-identity
```

## La condición importante

La trust policy debe limitar qué repositorio y referencia pueden asumir el rol:

```json
{
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub":
      "repo:ORGANIZACION/REPOSITORIO:ref:refs/heads/main"
  }
}
```

Confiar en GitHub sin restringir `sub` sería demasiado amplio.

## Qué debería poder explicar el alumno

> El workflow no guarda una contraseña AWS. Presenta un token temporal firmado por GitHub. AWS verifica ese token y, si sus claims coinciden con la trust policy, entrega credenciales temporales limitadas por un rol.

## Referencias oficiales

- [GitHub: configurar OIDC con AWS](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS: proveedores de identidad OIDC](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
