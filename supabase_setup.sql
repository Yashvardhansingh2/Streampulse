-- ============================================================
-- StreamPulse — Supabase SQL Setup
-- Run this entire file in: Supabase → SQL Editor → New Query
-- Create a SECOND Supabase project called "streampulse"
-- ============================================================

-- Raw events (every message from Kafka lands here)
CREATE TABLE IF NOT EXISTS events (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id         TEXT        UNIQUE NOT NULL,
    event_type       TEXT        NOT NULL,
    user_id          TEXT        NOT NULL,
    payload          JSONB,
    kafka_offset     BIGINT,
    kafka_partition  INTEGER,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS events_type_time_idx
    ON events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS events_user_time_idx
    ON events (user_id, created_at DESC);

-- 1-minute aggregates (upserted by the consumer in real time)
CREATE TABLE IF NOT EXISTS event_aggregates (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    bucket_start TIMESTAMPTZ NOT NULL,
    bucket_end   TIMESTAMPTZ NOT NULL,
    event_type   TEXT        NOT NULL,
    event_count  INTEGER     DEFAULT 0,
    total_amount NUMERIC     DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (bucket_start, event_type)
);

CREATE INDEX IF NOT EXISTS agg_bucket_idx
    ON event_aggregates (bucket_start DESC);

-- Dead letter queue (malformed messages the consumer rejected)
CREATE TABLE IF NOT EXISTS dead_letter_events (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_message  TEXT,
    error_reason TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
