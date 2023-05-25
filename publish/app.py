import json
import logging
from dapr.clients import DaprClient
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class vCluster(BaseModel):
    name: str
    cluster_type: str


@app.post("/vcluster")
def read_item(cluster: vCluster):
    logging.basicConfig(level=logging.INFO)

    with DaprClient() as client:
        for i in range(1, 2):
            order = {
                "name": cluster.name+"-" + str(i),
                "cluster_type": cluster.cluster_type
            }
            # Publish an event/message using Dapr PubSub
            client.publish_event(
                pubsub_name="orderpubsub",
                topic_name="orders",
                data=json.dumps(order),
                data_content_type="application/json",
            )
            logging.info("Published data: " + json.dumps(order))
        return {"message": "command send for creating vcluster"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
