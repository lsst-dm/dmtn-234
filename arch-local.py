"""Source for the component diagram for local OpenID Connect authentication."""

import os

from diagrams import Cluster, Diagram, Edge
from diagrams.gcp.compute import KubernetesEngine
from diagrams.gcp.network import LoadBalancing
from diagrams.generic.storage import Storage
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server
from diagrams.onprem.identity import Dex

graph_attr = {
    "label": "",
    "labelloc": "bbc",
    "nodesep": "0.2",
    "pad": "0.2",
    "ranksep": "0.75",
    "splines": "spline",
}

node_attr = {
    "fontsize": "12.0",
}

with Diagram(
    "Restricted access deployment",
    show=False,
    filename="arch-local",
    outformat="png",
    graph_attr=graph_attr,
    node_attr=node_attr,
):
    user = User("End user")
    idp = Server("OpenID Connect\nprovider")
    ldap = Storage("LDAP")

    with Cluster("Kubernetes"):
        ingress = LoadBalancing("Ingress")
        gafaelfawr = KubernetesEngine("Authentication")
        service_a = KubernetesEngine("Service A")
        service_b = KubernetesEngine("Service B")

    user >> idp >> gafaelfawr
    gafaelfawr << ldap
    user >> ingress >> gafaelfawr
    ingress >> service_a
    ingress >> service_b
    service_a >> Edge(label="To service B") >> ingress
