"""FastAPI app factory with rate limiting + CORS."""

from __future__ import annotations

import hashlib
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from agent_forest.gateway.deps import get_settings
from agent_forest.gateway.routes_auth import router as auth_router
from agent_forest.gateway.routes_task import router as task_router


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

    return app


app = create_app()
