import json
import os
import random
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

PRODUCTS    = [f"PROD_{i:04d}" for i in range(1, 201)]
CATEGORIES  = ["electronics", "clothing", "books", "food", "sports", "home"]
DEVICES     = ["mobile", "desktop", "tablet"]
PAGES       = ["/home", "/product", "/cart", "/checkout", "/search", "/wishlist"]
EVENT_TYPES = [
    "page_view", "add_to_cart", "purchase",
    "search", "wishlist_add", "checkout_start", "remove_from_cart",
]


def _build_conf() -> dict:
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    conf = {
        "bootstrap.servers": servers,
        "acks": "all",
        "retries": 3,
        "retry.backoff.ms": 500,
    }
    api_key = os.getenv("KAFKA_API_KEY", "")
    if api_key:
        # Upstash Kafka uses SCRAM-SHA-256
        # Local Docker Kafka has no auth — api_key will be empty string
        conf.update({
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "SCRAM-SHA-256",
            "sasl.username": api_key,
            "sasl.password": os.getenv("KAFKA_API_SECRET", ""),
        })
    return conf


_producer: Producer = Producer(_build_conf())


def make_event(event_type: str = None) -> dict:
    """Generate a realistic fake e-commerce event."""
    etype = event_type or random.choice(EVENT_TYPES)
    return {
        "event_id":   str(uuid.uuid4()),
        "event_type": etype,
        "user_id":    f"user_{random.randint(1, 500):04d}",
        "session_id": str(uuid.uuid4())[:8],
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "payload": {
            "product_id": random.choice(PRODUCTS),
            "category":   random.choice(CATEGORIES),
            "amount":     round(random.uniform(50.0, 15000.0), 2),
            "currency":   "INR",
            "page":       random.choice(PAGES),
            "device":     random.choice(DEVICES),
        },
    }


def _delivery_report(err, msg):
    if err:
        print(f"[Kafka] Delivery failed: {err}")
    else:
        print(f"[Kafka] OK partition={msg.partition()} offset={msg.offset()}")


def publish(event: dict):
    """Publish one event. Key = user_id so events per user stay ordered."""
    _producer.produce(
        topic=os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce-events"),
        key=event["user_id"].encode(),
        value=json.dumps(event).encode(),
        callback=_delivery_report,
    )
    _producer.poll(0)


def flush_all():
    _producer.flush()
