import asyncio
import json
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from upstash_redis import Redis

router = APIRouter()

_redis = Redis(
    url=os.getenv("UPSTASH_REDIS_REST_URL"),
    token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
)


def _safe_int(val) -> int:
    try:
        return int(val or 0)
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    try:
        return round(float(val or 0), 2)
    except (ValueError, TypeError):
        return 0.0


@router.websocket("/ws/dashboard")
async def dashboard(websocket: WebSocket):
    """
    Push live metrics every second to any connected dashboard client.
    Connect with:  wscat -c ws://localhost:8002/ws/dashboard
    """
    await websocket.accept()
    print("[WS] Dashboard client connected")

    try:
        while True:
            now = time.time()

            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "totals": {
                    "all_events":  _safe_int(_redis.get("sp:counter:total")),
                    "page_views":  _safe_int(_redis.get("sp:counter:page_view")),
                    "add_to_cart": _safe_int(_redis.get("sp:counter:add_to_cart")),
                    "purchases":   _safe_int(_redis.get("sp:counter:purchase")),
                    "revenue_inr": _safe_float(_redis.get("sp:counter:revenue_inr")),
                },
                "last_60s": {
                    "page_views":  _safe_int(
                        _redis.zcount("sp:window:60s:page_view", now - 60, now)
                    ),
                    "purchases":   _safe_int(
                        _redis.zcount("sp:window:60s:purchase", now - 60, now)
                    ),
                    "add_to_cart": _safe_int(
                        _redis.zcount("sp:window:60s:add_to_cart", now - 60, now)
                    ),
                },
            }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print("[WS] Dashboard client disconnected")
    except Exception as e:
        print(f"[WS] Error: {e}")
