from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.k8s.compute import Pod
from diagrams.k8s.controlplane import APIServer
from diagrams.k8s.group import Namespace
from diagrams.k8s.rbac import Group, RB, Role, SA, User


OUTPUT = Path(__file__).with_name("iam-lab")

graph_attr = {
    "bgcolor": "white",
    "fontname": "Arial",
    "fontsize": "18",
    "pad": "0.3",
    "ranksep": "0.7",
    "nodesep": "0.55",
}

node_attr = {
    "fontname": "Arial",
    "fontsize": "12",
}

edge_attr = {
    "fontname": "Arial",
    "fontsize": "10",
    "color": "#137333",
}

with Diagram(
    "IAM aplicado en Kubernetes",
    filename=str(OUTPUT),
    show=False,
    outformat="png",
    direction="LR",
    graph_attr=graph_attr,
    node_attr=node_attr,
    edge_attr=edge_attr,
):
    ana = User("Ana\ncertificado")
    developers = Group("developers")
    api = APIServer("API Server\nautentica y autoriza")

    ana >> Edge(label="CN=ana\nO=developers") >> developers >> api

    with Cluster("Identidad humana"):
        dev_binding = RB("RoleBinding\ndev")
        dev_role = Role("Role\ndeveloper")
        dev_ns = Namespace("lab-dev")
        prod_binding = RB("RoleBinding\nprod")
        prod_role = Role("Role\nviewer")
        prod_ns = Namespace("lab-prod")

        api >> Edge(label="RBAC") >> dev_binding >> dev_role >> dev_ns
        api >> Edge(label="RBAC") >> prod_binding >> prod_role >> prod_ns

    with Cluster("Identidad de aplicación"):
        reporter_pod = Pod("Pod reporter")
        reporter_sa = SA("ServiceAccount\nreporter")
        app_binding = RB("RoleBinding")
        app_role = Role("Role\npod-reader")
        app_ns = Namespace("lab-apps")

        reporter_pod >> Edge(label="JWT temporal") >> reporter_sa >> api
        api >> app_binding >> app_role >> app_ns
