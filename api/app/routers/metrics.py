import os

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

router = APIRouter()

_db_url = os.getenv("DATABASE_URL", "").replace(
    "postgresql://", "postgresql+asyncpg://"
)
_engine  = create_async_engine(_db_url, pool_size=3)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def _db() -> AsyncSession:
    async with _Session() as s:
        yield s


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "service": "streampulse-api"}


@router.get("/metrics/aggregates")
async def aggregates():
    """Return per-event-type totals for the last hour."""
    async with _Session() as db:
        rows = await db.execute(text("""
            SELECT
                event_type,
                SUM(event_count)  AS total_events,
                SUM(total_amount) AS total_revenue_inr
            FROM event_aggregates
            WHERE bucket_start > NOW() - INTERVAL '1 hour'
            GROUP BY event_type
            ORDER BY total_events DESC
        """))
        return {"last_hour": [dict(r._mapping) for r in rows.fetchall()]}


@router.get("/metrics/recent")
async def recent_events():
    """Return the 20 most recent raw events."""
    async with _Session() as db:
        rows = await db.execute(text("""
            SELECT event_type, user_id, payload, created_at
            FROM events
            ORDER BY created_at DESC
            LIMIT 20
        """))
        return {"events": [dict(r._mapping) for r in rows.fetchall()]}


@router.get("/metrics/topusers")
async def top_users():
    """Return the 10 users with most events today."""
    async with _Session() as db:
        rows = await db.execute(text("""
            SELECT user_id, COUNT(*) AS event_count
            FROM events
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY user_id
            ORDER BY event_count DESC
            LIMIT 10
        """))
        return {"top_users": [dict(r._mapping) for r in rows.fetchall()]}


@router.get("/metrics/revenue")
async def revenue():
    """Return total purchase revenue by hour for the last 24 hours."""
    async with _Session() as db:
        rows = await db.execute(text("""
            SELECT
                date_trunc('hour', bucket_start) AS hour,
                SUM(total_amount) AS revenue_inr
            FROM event_aggregates
            WHERE event_type = 'purchase'
              AND bucket_start > NOW() - INTERVAL '24 hours'
            GROUP BY hour
            ORDER BY hour DESC
        """))
        return {"hourly_revenue": [dict(r._mapping) for r in rows.fetchall()]}
