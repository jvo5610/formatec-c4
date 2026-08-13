from pathlib import Path

from diagrams import Diagram, Edge
from diagrams.onprem.auth import Oauth2Proxy
from diagrams.onprem.client import Client, Users
from diagrams.onprem.compute import Server


OUTPUT = Path(__file__).with_name("sso-google")

with Diagram(
    "SSO e identidad federada",
    filename=str(OUTPUT),
    show=False,
    outformat="png",
    direction="LR",
    graph_attr={
        "bgcolor": "white",
        "fontname": "Arial",
        "fontsize": "18",
        "pad": "0.3",
        "ranksep": "0.7",
        "nodesep": "0.55",
    },
    node_attr={"fontname": "Arial", "fontsize": "12"},
    edge_attr={"fontname": "Arial", "fontsize": "10", "color": "#137333"},
):
    user = Users("Usuario")
    portal = Client("Portal")
    reports = Client("Reportes")
    keycloak = Oauth2Proxy("Keycloak\nOIDC + SSO")
    google = Server("Google\nIdP externo")

    user >> Edge(label="abre") >> portal
    user >> Edge(label="abre") >> reports
    portal >> Edge(label="OIDC") >> keycloak
    reports >> Edge(label="misma sesión") >> keycloak
    keycloak >> Edge(label="identity brokering") >> google
    google >> Edge(label="perfil") >> keycloak
