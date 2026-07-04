import os
import json
import time
import threading
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


def _stream(rate: int, seconds: int, key_count: int):
    """Background worker: produce `rate` events/sec for `seconds`, across key_count keys."""
    n = 0
    for _ in range(seconds):
        start = time.monotonic()
        for _ in range(rate):
            key = f"user-{n % key_count}"
            producer.produce(TOPIC, key=key, value=json.dumps({"n": n}))
            n += 1
        producer.poll(0)              # serve delivery callbacks without blocking
        elapsed = time.monotonic() - start
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)  # pace to ~rate/sec
    producer.flush()
    print(f"stream done: produced {n} events")


@app.post("/stream")
def stream(rate: int = 20, seconds: int = 30, key_count: int = 10):
    """Produce a steady STREAM: `rate` events/sec for `seconds` seconds (runs in the background).

    Tune the load vs the consumer (which handles ~5 msg/sec per partition):
      - rate below total consumer throughput  -> no lag
      - rate above it                          -> lag builds (watch Kafka UI), drain by scaling consumers
    """
    total = rate * seconds
    threading.Thread(target=_stream, args=(rate, seconds, key_count), daemon=True).start()
    return {"status": "streaming", "rate": rate, "seconds": seconds, "keys": key_count, "total": total}


@app.get("/health")
def health():
    return {"ok": True}
