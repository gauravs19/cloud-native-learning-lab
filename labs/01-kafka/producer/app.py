import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from confluent_kafka import Producer

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
TOPIC = os.getenv("KAFKA_TOPIC", "events")

producer = Producer({"bootstrap.servers": BOOTSTRAP})
app = FastAPI(title="Kafka Learning Producer")


class Event(BaseModel):
    key: str          # partition key, e.g. a userId / orderId
    message: str


def _delivery(err, msg):
    if err:
        print(f"DELIVERY FAILED: {err}")
    else:
        print(f"delivered key={msg.key()} -> partition {msg.partition()} offset {msg.offset()}")


@app.post("/publish")
def publish(event: Event):
    payload = json.dumps({"message": event.message})
    # KEY DECIDES THE PARTITION: Kafka hashes the key -> same key = same partition
    producer.produce(TOPIC, key=event.key, value=payload, callback=_delivery)
    producer.flush()
    return {"status": "sent", "key": event.key}


@app.post("/publish-bulk")
def publish_bulk(count: int = 30):
    """Send `count` events across keys user-0..user-9 to watch partition spread."""
    for i in range(count):
        key = f"user-{i % 10}"
        producer.produce(TOPIC, key=key, value=json.dumps({"n": i}), callback=_delivery)
    producer.flush()
    return {"status": "sent", "count": count}


@app.get("/health")
def health():
    return {"ok": True}
