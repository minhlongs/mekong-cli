"""FastAPI app factory with rate limiting + CORS."""

from __future__ import annotations

import hashlib
import os

import redis
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agent_forest.gateway.deps import get_redis_client, get_settings
from agent_forest.gateway.routes_auth import router as auth_router
from agent_forest.gateway.routes_task import router as task_router
from agent_forest.queue import TASK_QUEUE
from agent_forest.worker.heartbeat import count_alive, last_seen_timestamp


def _rate_key(request: Request) -> str:
    """Rate-limit key: sha256(bearer token) if present, else remote IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1]
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
    return get_remote_address(request)


def _allowed_origins() -> list[str]:
    raw = os.getenv("FOREST_ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["http://localhost:3000"]


def create_app() -> FastAPI:
    settings = get_settings()
    limiter = Limiter(
        key_func=_rate_key,
        default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    )
    app = FastAPI(title="Agent Forest Gateway", version="0.1.0")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    app.include_router(auth_router)
    app.include_router(task_router)

    @app.get("/healthz", tags=["infra"])
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "agent-forest"})

    @app.get("/metrics", tags=["infra"], response_class=PlainTextResponse)
    def metrics(r: redis.Redis = Depends(get_redis_client)) -> str:
        """Prometheus text exposition — queue depth + worker liveness."""
        try:
            depth = int(r.llen(TASK_QUEUE))
        except Exception:
            depth = -1
        try:
            alive = count_alive(r)
            last_seen = last_seen_timestamp(r)
        except Exception:
            alive = -1
            last_seen = 0
        lines = [
            "# HELP agent_forest_queue_depth Current length of Redis task_queue list",
            "# TYPE agent_forest_queue_depth gauge",
            f"agent_forest_queue_depth {depth}",
            "# HELP agent_forest_up Service liveness indicator (1=up)",
            "# TYPE agent_forest_up gauge",
            "agent_forest_up 1",
            "# HELP agent_forest_workers_alive Workers with fresh heartbeat (TTL<60s)",
            "# TYPE agent_forest_workers_alive gauge",
            f"agent_forest_workers_alive {alive}",
            "# HELP agent_forest_worker_last_seen_timestamp Max unix-ts of any live heartbeat",
            "# TYPE agent_forest_worker_last_seen_timestamp gauge",
            f"agent_forest_worker_last_seen_timestamp {last_seen}",
        ]
        return "\n".join(lines) + "\n"

    return app


app = create_app()
