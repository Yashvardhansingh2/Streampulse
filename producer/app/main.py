import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.producer import flush_all, make_event, publish

app = FastAPI(title="StreamPulse Producer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulateRequest(BaseModel):
    count: int = 100
    events_per_second: float = 10.0
    event_type: str = None   # None = random mix


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "streampulse-producer", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "streampulse-producer"}


@app.post("/simulate")
async def simulate(body: SimulateRequest):
    """
    Publish events at a controlled rate.
    Example: 200 events at 10/sec takes 20 seconds.
    """
    delay = 1.0 / max(body.events_per_second, 0.1)
    for i in range(body.count):
        publish(make_event(body.event_type))
        await asyncio.sleep(delay)
    flush_all()
    return {
        "published": body.count,
        "rate": body.events_per_second,
        "topic": "ecommerce-events",
    }


@app.post("/simulate/burst")
async def burst(count: int = 500):
    """
    Publish many events as fast as possible — good for stress testing.
    """
    for _ in range(count):
        publish(make_event())
    flush_all()
    return {"published": count, "mode": "burst"}


@app.post("/simulate/scenario/{scenario}")
async def scenario(scenario: str):
    """
    Predefined scenarios:
      - flash_sale  : heavy purchase + add_to_cart burst
      - browse_only : only page_view events
      - mixed       : realistic traffic mix
    """
    scenarios = {
        "flash_sale":  [("purchase", 40), ("add_to_cart", 60)],
        "browse_only": [("page_view", 200)],
        "mixed":       [(None, 150)],
    }
    if scenario not in scenarios:
        return {"error": f"Unknown scenario. Choose: {list(scenarios.keys())}"}

    total = 0
    for etype, count in scenarios[scenario]:
        for _ in range(count):
            publish(make_event(etype))
        total += count
    flush_all()
    return {"published": total, "scenario": scenario}
