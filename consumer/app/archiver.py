import io
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

_BUCKET = os.getenv("SUPABASE_BUCKET", "streampulse-archive")


class Archiver:
    """
    Buffers events and flushes them to Supabase Storage as Parquet files.
    Partitioned by year/month/day for efficient future querying.
    """

    def __init__(self):
        self._supabase: Optional[object] = None
        self._enabled = False

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")
        if not url or not key:
            print("[Archiver] Supabase not configured; archive uploads disabled")
            return

        try:
            self._supabase = create_client(url, key)
            self._enabled = True
        except Exception as e:
            print(f"[Archiver] Supabase init failed; archive uploads disabled: {e}")

    def flush(self, events: list[dict]):
        if not events or not self._enabled or self._supabase is None:
            return
        try:
            df = pd.DataFrame(events)
            now = datetime.now(timezone.utc)

            # Hive-style partitioning — easy to query later with any SQL engine
            path = (
                f"events/"
                f"year={now.year}/"
                f"month={now.month:02d}/"
                f"day={now.day:02d}/"
                f"{uuid.uuid4()}.parquet"
            )

            buf = io.BytesIO()
            df.to_parquet(buf, engine="pyarrow", index=False, compression="snappy")
            buf.seek(0)

            self._supabase.storage.from_(_BUCKET).upload(
                path=path,
                file=buf.getvalue(),
                file_options={"content-type": "application/octet-stream"},
            )
            print(f"[Archiver] Flushed {len(events)} events → {path}")

        except Exception as e:
            # Archive failure must never crash the consumer
            print(f"[Archiver] WARNING: flush failed (events safe in DB): {e}")
