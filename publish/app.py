import json
import logging
import time
from dapr.clients import DaprClient
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    logging.basicConfig(level=logging.INFO)

    with DaprClient() as client:
        for i in range(1, 10):
            order = {"orderId": i}
            # Publish an event/message using Dapr PubSub
            client.publish_event(
                pubsub_name="orderpubsub",
                topic_name="orders",
                data=json.dumps(order),
                data_content_type="application/json",
            )
            logging.info("Published data: " + json.dumps(order))
            time.sleep(1)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
