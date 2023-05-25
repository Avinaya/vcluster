from flask import Flask, request, jsonify
from kubernetes import client, config
from fastapi import HTTPException
import json
import logging
import os
import yaml

app = Flask(__name__)

app_port = os.getenv("APP_PORT", "6001")

logging.basicConfig(level=logging.INFO)

config.load_kube_config()

api_client = client.CoreV1Api()
api_client_apps = client.AppsV1Api()
api_client_custom = client.CustomObjectsApi()


def create_namespace(namespace):
    try:
        api_client.create_namespace(
            client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
        )
        print(f"Namespace '{namespace}' created successfully")
    except client.rest.ApiException as e:
        if e.status == 409:
            print(f"Namespace '{namespace}' already exists")
        else:
            raise e


# Register Dapr pub/sub subscriptions
@app.route("/dapr/subscribe", methods=["GET"])
def subscribe():
    subscriptions = [
        {"pubsubname": "orderpubsub", "topic": "orders", "route": "orders"}
    ]
    print("Dapr pub/sub is subscribed to: " + json.dumps(subscriptions))
    return jsonify(subscriptions)


# Dapr subscription in /dapr/subscribe sets up this route
@app.route("/orders", methods=["POST"])
def orders_subscriber():

    logging.info("Published data: " + json.dumps(request.json["data"]))
    namespace = request.json["data"]["name"] + "-vcluster"
    name = request.json["data"]["name"]
    types = request.json["data"]["cluster_type"]

    if not types:
        with open("../files/vcluster.yaml") as f:
            vcluster = f.read().format(namespace=namespace, name=name)
    elif types == "basic":
        with open("../files/basic.yaml") as f:
            vcluster = f.read().format(namespace=namespace, name=name)
        with open("../files/basic_quota.yaml") as f:
            quota = f.read().format(namespace=namespace, name=name)
        print(vcluster)
    elif types == "platinum":
        with open("../files/platinum.yaml") as f:
            vcluster = f.read().format(namespace=namespace, name=name)
        with open("../files/platinum_quota.yaml") as f:
            quota = f.read().format(namespace=namespace, name=name)

    try:

        # Load the YAML file into a Python dictionary
        with open("../files/cluster.yaml") as f:
            custom_resource = f.read().format(namespace=namespace, name=name)

        create_namespace(namespace)

        # Create the custom resource in the cluster
        api_client_custom.create_namespaced_custom_object(
            group="cluster.x-k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="clusters",
            body=yaml.safe_load(custom_resource),
        )

        # Create the custom resource in the cluster
        api_client_custom.create_namespaced_custom_object(
            group="infrastructure.cluster.x-k8s.io",
            version="v1alpha1",
            namespace=namespace,
            plural="vclusters",
            body=yaml.safe_load(vcluster),
        )
        if not types:
            quota = None
        elif types in ("basic", "platinum"):
            api_client.create_namespaced_resource_quota(
                namespace=namespace, body=yaml.safe_load(quota)
            )
        nodes = api_client.list_node().items
        node_count = len(nodes)

        return {
            "message": "vcluster created successfully",
            "name": name,
            "nodecount": node_count,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.run(port=app_port)
