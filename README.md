# StreamPulse

Real-time e-commerce event analytics pipeline built with Kafka, FastAPI, PostgreSQL, Redis-style counters, and a live WebSocket dashboard.

StreamPulse simulates shopping traffic, processes events with consumer groups, stores raw + aggregated metrics, and exposes query APIs for dashboards.

## Why This Project

Most analytics demos are either batch-oriented or too minimal. StreamPulse focuses on practical streaming concepts:

- event production at configurable rates
- Kafka topic ingestion with consumer groups
- per-minute aggregate upserts for fast analytics queries
- near real-time counters for dashboard-style UX
- dead-letter handling for malformed events

## Architecture

```mermaid
flowchart LR
    A[Producer API\nFastAPI] -->|ecommerce-events| B[(Kafka)]
    B --> C[Consumer x2\nWorker Group]
    C --> D[(PostgreSQL\nraw events + aggregates)]
    C --> E[(Upstash Redis\nrealtime counters)]
    C --> F[(Supabase Storage\nParquet archive optional)]
    G[API Service\nFastAPI] --> D
    G --> E
    H[WebSocket Client\nDashboard] --> G
```

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- Confluent Kafka client
- PostgreSQL + SQLAlchemy (asyncpg)
- Upstash Redis client
- Supabase Python client
- Docker Compose (local orchestration)

## Project Layout

```text
streampulse/
  api/        # Query API + WebSocket dashboard endpoint
  consumer/   # Kafka consumer, DB writer, Redis updater, archiver
  producer/   # Event simulation API and Kafka producer
  docker-compose.yml
  supabase_setup.sql
```

## Ports

- `8001` Producer API
- `8002` Metrics/API + WebSocket
- `8090` Kafka UI
- `9092` Kafka external listener
- `5433` PostgreSQL
- `6380` Redis container

## Quick Start (Local)

### 1) Prerequisites

- Docker Desktop running
- Git

### 2) Configure Environment

Create or edit `.env` in repo root:

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_API_KEY=
KAFKA_API_SECRET=
KAFKA_TOPIC_EVENTS=ecommerce-events
KAFKA_TOPIC_DLQ=ecommerce-dlq

DATABASE_URL=postgresql://postgres:your_password@db.yourref.supabase.co:5432/postgres
SUPABASE_URL=https://yourref.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
SUPABASE_BUCKET=streampulse-archive

UPSTASH_REDIS_REST_URL=https://your-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token
```

Notes:
- Local Kafka works without `KAFKA_API_KEY` and `KAFKA_API_SECRET`.
- If Supabase credentials are missing/invalid, archive uploads are disabled safely.
- DB writes still use the local Postgres from Docker Compose.

### 3) Start Services

```bash
docker compose up --build -d
```

### 4) Initialize Database Schema

Run once per fresh volume:

```bash
docker compose exec -T postgres psql -U admin -d streampulse -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
docker compose exec -T postgres psql -U admin -d streampulse < supabase_setup.sql
```

### 5) Verify Health

```bash
curl http://localhost:8001/health
curl http://localhost:8002/api/v1/health
```

## Input / Output Test Flow

### Send Input Events

```bash
curl -X POST http://localhost:8001/simulate \
  -H "Content-Type: application/json" \
  -d '{"count": 50, "events_per_second": 10}'
```

### Read Output Metrics

```bash
curl http://localhost:8002/api/v1/metrics/aggregates
curl http://localhost:8002/api/v1/metrics/recent
curl http://localhost:8002/api/v1/metrics/topusers
curl http://localhost:8002/api/v1/metrics/revenue
```

### Live Dashboard Stream

```bash
wscat -c ws://localhost:8002/ws/dashboard
```

## Useful Producer Scenarios

```bash
# Burst load
curl -X POST "http://localhost:8001/simulate/burst?count=500"

# Flash sale
curl -X POST http://localhost:8001/simulate/scenario/flash_sale

# Purchase-only run
curl -X POST http://localhost:8001/simulate \
  -H "Content-Type: application/json" \
  -d '{"count": 25, "events_per_second": 5, "event_type": "purchase"}'
```

## Kafka UI

Open:

```bash
open http://localhost:8090
```

Expected topics:

- `ecommerce-events`
- `ecommerce-dlq`

## Common Commands

```bash
# Service status
docker compose ps

# Tail logs
docker compose logs -f

# Tail specific services
docker compose logs -f producer consumer api

# Rebuild one service
docker compose up --build api

# Stop and keep data
docker compose down

# Stop and delete volumes (requires schema init again)
docker compose down -v
```

## Troubleshooting

### Kafka fails with listener port error

If you see `Each listener must have a different port`, ensure compose uses distinct internal/external listeners:

- internal: `kafka:29092`
- external host: `localhost:9092`

### API returns 500 for metrics tables

If tables like `event_aggregates` are missing, run schema init commands again:

```bash
docker compose exec -T postgres psql -U admin -d streampulse < supabase_setup.sql
```

### No aggregate data after simulate

Check consumer logs and topic flow:

```bash
docker compose logs --tail=200 consumer kafka
```

### WebSocket connects but values are zero

Redis-backed live counters require valid Upstash env values. DB metrics endpoints can still work without it.

## Deployment Notes (Render)

Deploy as three services:

- `producer` as Web Service
- `consumer` as Background Worker
- `api` as Web Service

Set environment variables per service scope carefully.
For hosted WebSocket clients, use `wss://` URL scheme.

## Security Notes

- Never commit `.env`
- Use service role keys only in trusted backend services
- Rotate leaked tokens immediately

## License

Use your preferred license (MIT/Apache-2.0 recommended) before public production use.
