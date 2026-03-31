import asyncio

from fastapi import FastAPI

from app.consumer import run as run_consumer

app = FastAPI(title="StreamPulse Consumer Wrapper", version="1.0.0")
_consumer_task: asyncio.Task | None = None


@app.on_event("startup")
async def on_startup():
    global _consumer_task
    if _consumer_task is None or _consumer_task.done():
        _consumer_task = asyncio.create_task(run_consumer())


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
    return {"status": "ok" if running else "starting", "service": "streampulse-consumer"}
