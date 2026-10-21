# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - FastAPI Health Endpoint Server."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import threading
import time
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from src.core.event_bus import EventType, get_event_bus

logger = logging.getLogger(__name__)


class ComponentStatus(BaseModel):
    """Status of a single component."""
    status: str  # "healthy", "degraded", "unhealthy"
    message: str | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    """Health endpoint response schema."""
    status: str  # "healthy", "degraded", "unhealthy"
    components: dict[str, ComponentStatus]
    timestamp: str
    version: str
    uptime_seconds: float | None = None


_startup_time: float | None = None
_server_instance: uvicorn.Server | None = None
_component_checks: dict[str, callable] = {}


def register_component_check(name: str, check_fn: callable) -> None:
    """Register a health check function for a component."""
    _component_checks[name] = check_fn
    logger.info(f"Registered health check for component: {name}")


def unregister_component_check(name: str) -> bool:
    """Unregister a component health check."""
    removed = _component_checks.pop(name, None) is not None
    if removed:
        logger.info(f"Unregistered health check for component: {name}")
    return removed


def _check_component(name: str) -> ComponentStatus:
    """Execute health check for a component."""
    check_fn = _component_checks.get(name)
    if not check_fn:
        return ComponentStatus(status="unknown", message=f"No health check registered for '{name}'")
    try:
        return check_fn()
    except Exception as e:
        logger.exception(f"Health check failed for component '{name}': {e}")
        return ComponentStatus(status="unhealthy", message=f"Check failed: {str(e)}")


def _compute_overall_status(components: dict[str, ComponentStatus]) -> str:
    """Compute overall health status from component statuses."""
    statuses = [c.status for c in components.values()]
    if all(s == "healthy" for s in statuses):
        return "healthy"
    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    return "degraded"


def create_health_app() -> FastAPI:
    """Create FastAPI application for health endpoint."""
    app = FastAPI(title="Mekong CLI Health", description="Health endpoint for Mekong CLI system monitoring", version="3.0.0")

    @app.get("/health", response_model=HealthResponse)
    async def get_health() -> HealthResponse:
        components = {name: _check_component(name) for name in _component_checks}
        uptime = (datetime.now(timezone.utc).timestamp() - _startup_time) if _startup_time is not None else None
        return HealthResponse(
            status=_compute_overall_status(components), components=components,
            timestamp=datetime.now(timezone.utc).isoformat(), version="3.0.0", uptime_seconds=uptime,
        )

    @app.get("/ready")
    async def get_readiness() -> dict[str, Any]:
        components = {name: _check_component(name) for name in _component_checks}
        is_ready = all(c.status in ("healthy", "unknown") for c in components.values())
        return {"ready": is_ready, "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.get("/live")
    async def get_liveness() -> dict[str, Any]:
        return {"alive": True, "timestamp": datetime.now(timezone.utc).isoformat()}

    return app


def start_health_server(host: str = "127.0.0.1", port: int = 9192, log_level: str = "warning") -> uvicorn.Server:
    """Start health endpoint server."""
    global _startup_time, _server_instance  # noqa: F824
    app = create_health_app()
    config = uvicorn.Config(app, host=host, port=port, log_level=log_level, access_log=False)
    server = uvicorn.Server(config)

    def run_server() -> None:
        global _startup_time
        _startup_time = datetime.now(timezone.utc).timestamp()
        _server_instance = server  # noqa: F841
        logger.info(f"Health endpoint started at http://{host}:{port}")
        get_event_bus().emit(
            EventType.COLLECTOR_DISCOVERED,
            {"type": "health_endpoint", "host": host, "port": port, "url": f"http://{host}:{port}/health"},
        )
        server.run()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    time.sleep(0.5)
    return server


def stop_health_server() -> None:
    """Stop health endpoint server gracefully."""
    global _server_instance, _startup_time
    if _server_instance is not None:
        logger.info("Stopping health endpoint server...")
        _server_instance.should_exit = True
        _server_instance = None
        _startup_time = None
        logger.info("Health endpoint server stopped")


def get_health_url(host: str = "127.0.0.1", port: int = 9192) -> str:
    """Get health endpoint URL."""
    return f"http://{host}:{port}/health"


__all__ = [
    "HealthResponse", "ComponentStatus", "register_component_check", "unregister_component_check",
    "start_health_server", "stop_health_server", "get_health_url", "create_health_app",
]
