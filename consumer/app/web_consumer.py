import asyncio
import importlib
import os

from fastapi import FastAPI

app = FastAPI(title="StreamPulse Consumer Wrapper", version="1.0.0")
_consumer_task: asyncio.Task | None = None
_startup_error: str | None = None


def _missing_required_env() -> list[str]:
    required = [
        "DATABASE_URL",
        "KAFKA_BOOTSTRAP_SERVERS",
        "KAFKA_TOPIC_EVENTS",
        "KAFKA_TOPIC_DLQ",
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
    ]
    return [k for k in required if not os.getenv(k)]


@app.on_event("startup")
async def on_startup():
    global _consumer_task, _startup_error
    if _consumer_task is None or _consumer_task.done():
        missing = _missing_required_env()
        if missing:
            _startup_error = f"Missing required env vars: {', '.join(missing)}"
            print(f"[Consumer Wrapper] {_startup_error}")
            return

        try:
            run_consumer = importlib.import_module("app.consumer").run
            _consumer_task = asyncio.create_task(run_consumer())
            _startup_error = None
        except Exception as e:
            _startup_error = str(e)
            print(f"[Consumer Wrapper] startup failed: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    global _consumer_task
    if _consumer_task is not None and not _consumer_task.done():
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass


@app.get("/health")
async def health():
    running = _consumer_task is not None and not _consumer_task.done()
    if running:
        return {"status": "ok", "service": "streampulse-consumer"}
    if _startup_error:
        return {
            "status": "error",
            "service": "streampulse-consumer",
            "detail": _startup_error,
        }
    return {"status": "starting", "service": "streampulse-consumer"}
