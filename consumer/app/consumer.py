import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone

from confluent_kafka import Consumer, KafkaError, Producer
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from upstash_redis import Redis

from app.archiver import Archiver

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────────────

_db_url = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+asyncpg://"
)
_engine  = create_async_engine(_db_url, pool_size=5, max_overflow=5)
_Session = async_sessionmaker(_engine, expire_on_commit=False)

# ── Redis ─────────────────────────────────────────────────────────────────────

_redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)

# ── Archiver ──────────────────────────────────────────────────────────────────

_archiver   = Archiver()
_buffer: list[dict] = []
FLUSH_EVERY = 100


# ── Kafka config ──────────────────────────────────────────────────────────────

def _requires_kafka_auth(servers: str) -> bool:
    servers_l = servers.lower()
    return (
        "redpanda.com" in servers_l
        or "confluent.cloud" in servers_l
        or "upstash" in servers_l
    )


def _bootstrap_servers() -> str:
    servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").strip()
    servers = (
        servers.replace("SASL_SSL://", "")
        .replace("SSL://", "")
        .replace("PLAINTEXT://", "")
    )

    # Redpanda cloud endpoints are sometimes exposed on both 9092/9093.
    # When only one is provided, try both to avoid listener mismatch issues.
    if _requires_kafka_auth(servers) and "," not in servers:
        if servers.endswith(":9092"):
            base = servers[:-5]
            servers = f"{base}:9092,{base}:9093"
        elif servers.endswith(":9093"):
            base = servers[:-5]
            servers = f"{base}:9093,{base}:9092"

    return servers

def _kafka_auth_conf() -> dict:
    """
    Returns SASL config only when KAFKA_API_KEY is set.
    - Empty key  → local Docker Kafka (no auth needed)
    - Key set    → Redpanda Cloud (SCRAM-SHA-256 + SASL_SSL)
    """
    servers = _bootstrap_servers()
    api_key = os.getenv("KAFKA_API_KEY", "")
    api_secret = os.getenv("KAFKA_API_SECRET", "")

    if not api_key or not api_secret:
        if _requires_kafka_auth(servers):
            raise RuntimeError(
                "KAFKA_API_KEY/KAFKA_API_SECRET are required for cloud Kafka brokers"
            )
        return {}

    return {
        "security.protocol":                    "SASL_SSL",
        "sasl.mechanism":                       "SCRAM-SHA-256",
        "sasl.username":                        api_key,
        "sasl.password":                        api_secret,
        "ssl.endpoint.identification.algorithm": "none",
    }


def _consumer_conf() -> dict:
    conf = {
        "bootstrap.servers":     _bootstrap_servers(),
        "group.id":              "streampulse-analytics-v1",
        "auto.offset.reset":     "earliest",
        "enable.auto.commit":    False,
        "max.poll.interval.ms":  300000,
        "session.timeout.ms":    45000,
        "client.id":             "streampulse-consumer",
    }
    conf.update(_kafka_auth_conf())
    return conf


def _producer_conf() -> dict:
    conf = {
        "bootstrap.servers": _bootstrap_servers(),
        "client.id": "streampulse-dlq-producer",
    }
    conf.update(_kafka_auth_conf())
    return conf


# ── Redis helpers ─────────────────────────────────────────────────────────────

def _update_redis(event: dict):
    etype = event["event_type"]
    now   = time.time()
    try:
        _redis.incr("sp:counter:total")
        _redis.incr(f"sp:counter:{etype}")

        wkey = f"sp:window:60s:{etype}"
        _redis.zadd(wkey, {event["event_id"]: now})
        _redis.zremrangebyscore(wkey, 0, now - 60)
        _redis.expire(wkey, 120)

        if etype == "purchase":
            amount = float(event.get("payload", {}).get("amount", 0))
            _redis.incrbyfloat("sp:counter:revenue_inr", amount)
    except Exception as e:
        print(f"[Redis] WARNING: {e}")


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _save_event(event: dict, db: AsyncSession, offset: int, partition: int):
    await db.execute(
        text("""
            INSERT INTO events
                (event_id, event_type, user_id, payload, kafka_offset, kafka_partition)
            VALUES (:eid, :etype, :uid, :payload, :off, :part)
            ON CONFLICT (event_id) DO NOTHING
        """),
        {
            "eid":     event["event_id"],
            "etype":   event["event_type"],
            "uid":     event["user_id"],
            "payload": json.dumps(event["payload"]),
            "off":     offset,
            "part":    partition,
        },
    )


async def _upsert_aggregate(event: dict, db: AsyncSession):
    bucket_start = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    bucket_end   = bucket_start + timedelta(minutes=1)
    amount = (
        float(event.get("payload", {}).get("amount", 0))
        if event["event_type"] == "purchase" else 0.0
    )
    await db.execute(
        text("""
            INSERT INTO event_aggregates
                (bucket_start, bucket_end, event_type, event_count, total_amount)
            VALUES (:start, :end, :etype, 1, :amount)
            ON CONFLICT (bucket_start, event_type)
            DO UPDATE SET
                event_count  = event_aggregates.event_count + 1,
                total_amount = event_aggregates.total_amount + EXCLUDED.total_amount
        """),
        {"start": bucket_start, "end": bucket_end,
         "etype": event["event_type"], "amount": amount},
    )


# ── Message processor ─────────────────────────────────────────────────────────

async def _process(msg, db: AsyncSession, dlq: Producer):
    global _buffer
    try:
        event   = json.loads(msg.value().decode("utf-8"))
        missing = [k for k in ["event_id", "event_type", "user_id"] if k not in event]
        if missing:
            raise ValueError(f"Missing fields: {missing}")

        await _save_event(event, db, msg.offset(), msg.partition())
        await _upsert_aggregate(event, db)
        _update_redis(event)

        _buffer.append(event)
        if len(_buffer) >= FLUSH_EVERY:
            _archiver.flush(_buffer.copy())
            _buffer.clear()

    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Consumer] Bad message → DLQ: {e}")
        dlq.produce(
            topic=os.getenv("KAFKA_TOPIC_DLQ", "ecommerce-dlq"),
            value=msg.value(),
            headers={"error": str(e).encode()},
        )
        dlq.poll(0)


# ── Main loop ─────────────────────────────────────────────────────────────────

async def run():
    print(f"[Consumer] bootstrap.servers={_bootstrap_servers()}")
    print(f"[Consumer] using_auth={bool(os.getenv('KAFKA_API_KEY', ''))}")
    consumer = Consumer(_consumer_conf())
    dlq      = Producer(_producer_conf())
    consumer.subscribe([os.getenv("KAFKA_TOPIC_EVENTS", "ecommerce-events")])
    print("[Consumer] Started — waiting for messages...")

    async with _Session() as db:
        try:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        print(f"[Consumer] Kafka error: {msg.error()}")
                    continue

                await _process(msg, db, dlq)
                await db.commit()
                consumer.commit(msg)

        except KeyboardInterrupt:
            print("[Consumer] Shutting down...")
        finally:
            if _buffer:
                _archiver.flush(_buffer)
            consumer.close()
            dlq.flush()


if __name__ == "__main__":
    asyncio.run(run())
