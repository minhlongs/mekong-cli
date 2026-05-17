"""Mekong CLI - Gateway API Server.

FastAPI server exposing Mekong CLI orchestration to AgencyOS.
REST API + SSE streaming for real-time mission execution.

Usage:
    uvicorn src.gateway:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os as _os
import sys
import time as _time
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.gateway_mission_routes import router as mission_router
from src.api.gateway_webhook_mcu_routes import router as webhook_mcu_router
from src.api.coupon_router import router as coupon_router
from src.api.polar_webhook import router as polar_webhook_router
from src.api.auth_routes import router as auth_router
from src.raas.missions_api_router import router as raas_router
from src.raas.revenue_router import router as revenue_router
from src.raas.checkout_router import router as checkout_router
from src.raas.tenant_use_case_router import router as tenant_router
from src.raas.reports_router import router as reports_router
from src.raas.autopilot import router as autopilot_router
from src.core.request_logger import RequestLoggerMiddleware
from src.core.mcu_billing import MCUBilling
from src.core.logging_config import configure_logging
from src.core.sentry_init import init_sentry
from src.core.telemetry_init import init_telemetry

configure_logging()
init_sentry()
init_telemetry()

logger = logging.getLogger(__name__)

# Capture process start time for uptime reporting
_APP_START_TIME: float = _time.monotonic()

# =============================================================================
# BILLING SINGLETON
# =============================================================================
# Global MCUBilling instance for credit management
mcu_billing = MCUBilling()

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Mekong CLI Gateway API",
    description="Unified API for MekongMind — the one-person company platform",
    version="3.3.0",
    docs_url="/api-docs",
    redoc_url="/api-redoc",
)

# Mount routers — gateway endpoints
app.include_router(mission_router)
app.include_router(webhook_mcu_router)
app.include_router(coupon_router)
app.include_router(polar_webhook_router)
app.include_router(auth_router)

# Mount routers — RaaS endpoints
app.include_router(raas_router)
app.include_router(revenue_router)
app.include_router(checkout_router)
app.include_router(tenant_router)
app.include_router(reports_router)
app.include_router(autopilot_router)

# CORS for AgencyOS frontend
_ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in _os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080,https://mekongmind.com,https://www.mekongmind.com,https://api.cashclaw.cc,https://ide.mekongmind.com",
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH CHECK
# =============================================================================

_APP_VERSION = "3.3.0"


def _memory_usage_mb() -> float | None:
    """Return RSS memory in MB, or None if psutil unavailable."""
    try:
        import psutil
        proc = psutil.Process()
        return round(proc.memory_info().rss / 1024 / 1024, 2)
    except Exception:
        return None


def _component_status() -> dict[str, dict]:
    """Check key component availability without external I/O."""
    components: dict[str, dict] = {}

    # Billing
    try:
        _ = mcu_billing  # singleton already constructed
        components["billing"] = {"status": "healthy"}
    except Exception as exc:
        components["billing"] = {"status": "unhealthy", "error": str(exc)}

    # Auth (check module importability)
    try:
        from src.core.auth_jwt import decode_jwt  # noqa: F401
        components["auth"] = {"status": "healthy"}
    except Exception as exc:
        components["auth"] = {"status": "unhealthy", "error": str(exc)}

    # Sentry
    sentry_dsn = _os.getenv("SENTRY_DSN")
    components["sentry"] = {
        "status": "healthy" if sentry_dsn else "disabled",
        "configured": bool(sentry_dsn),
    }

    # OpenTelemetry
    otel_endpoint = _os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    components["otel"] = {
        "status": "healthy" if otel_endpoint else "disabled",
        "configured": bool(otel_endpoint),
    }

    return components


@app.get("/healthz")
async def healthz() -> dict:
    """Lightweight liveness probe (no I/O) for load balancers / Fly.io checks."""
    return {"status": "ok", "version": _APP_VERSION}


@app.get("/health")
async def health_check() -> dict:
    """Enhanced health check with uptime, memory, version, and component status."""
    uptime_seconds = round(_time.monotonic() - _APP_START_TIME, 2)
    components = _component_status()

    # Overall status: unhealthy if any required component is unhealthy
    required = {"billing", "auth"}
    overall = "healthy"
    for name, info in components.items():
        if name in required and info.get("status") == "unhealthy":
            overall = "unhealthy"
            break

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": _APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "python_version": sys.version.split()[0],
        "memory_mb": _memory_usage_mb(),
        "components": components,
    }


app.add_middleware(RequestLoggerMiddleware)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.gateway:app",
        host="0.0.0.0",
        port=int(_os.environ.get("GATEWAY_PORT", "8000")),
        reload=True,
    )
