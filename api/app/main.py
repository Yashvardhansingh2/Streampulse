from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import metrics, ws

app = FastAPI(title="StreamPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics.router, prefix="/api/v1")
app.include_router(ws.router)


@app.get("/")
def root():
    return {
        "service": "streampulse-api",
        "status": "running",
        "endpoints": {
            "health":      "/api/v1/health",
            "aggregates":  "/api/v1/metrics/aggregates",
            "recent":      "/api/v1/metrics/recent",
            "top_users":   "/api/v1/metrics/topusers",
            "revenue":     "/api/v1/metrics/revenue",
            "websocket":   "ws://localhost:8002/ws/dashboard",
        },
    }
