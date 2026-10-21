# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Gateway API Server.

FastAPI server exposing Mekong CLI orchestration to AgencyOS.
REST API + SSE streaming for real-time mission execution.

Usage:
    uvicorn src.gateway:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os as _os
import time as _time

# ruff: noqa: E402
# sys.path must be modified before these engine/src imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.gateway_mission_routes import router as mission_router
from src.api.gateway_webhook_mcu_routes import router as webhook_mcu_router
from src.api.coupon_router import router as coupon_router
from src.api.auth_routes import router as auth_router, vn_auth_router
from src.auth.routes import router as auth_ui_router
from src.raas.missions_api_router import router as raas_router
from src.raas.revenue_router import router as revenue_router
from src.raas.checkout_router import router as checkout_router
from src.raas.nowpayments_router import router as nowpayments_router
from src.raas.tenant_use_case_router import router as tenant_router
from src.raas.reports_router import router as reports_router
from src.raas.autopilot import router as autopilot_router
from src.raas.marketplace_router import router as marketplace_router
from src.api.vn_pricing_routes import router as vn_pricing_router
from src.api.vn_pilot_routes import router as vn_pilot_router
from src.api.vn_payments_routes import router as vn_payments_router
from src.api.org_routes import org_router
from src.api.billing_routes import router as billing_router
from src.api.metrics_routes import router as metrics_router
from src.api.opencore_status_routes import router as opencore_status_router
from src.api.quota_status_endpoints import quota_router
from src.api.tier_config_routes import router as tier_config_router
from src.middleware.csrf_middleware import CSRFMiddleware
from src.middleware.rate_limit_gateway_middleware import RateLimitGatewayMiddleware
from src.middleware.pilot_credit_gate import PilotCreditGateMiddleware
# Ensure engine/ layer is importable regardless of uvicorn cwd
import sys as _sys
_ENGINE_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "engine")
if _ENGINE_DIR not in _sys.path:
    _sys.path.insert(0, _ENGINE_DIR)

from engine.license.license_gate_middleware import EngineLicenseGateMiddleware
from src.core.request_logger import RequestLoggerMiddleware
from src.core.mcu_billing import MCUBilling
from src.core.billing_adapter import BillingAdapter
from src.core.logging_config import configure_logging
from src.core.sentry_init import init_sentry
from src.core.telemetry_init import init_telemetry

configure_logging()
init_sentry()
init_telemetry()

logger = logging.getLogger(__name__)
_APP_START_TIME: float = _time.monotonic()

mcu_billing = MCUBilling()
billing_adapter = BillingAdapter(mcu_billing)

_is_production = _os.getenv("MEKONG_ENV", "development") == "production"

app = FastAPI(
    title="Mekong CLI Gateway API",
    description="Unified API for MekongMind — the one-person company platform",
    version="3.3.0",
    docs_url=None if _is_production else "/api-docs",
    redoc_url=None if _is_production else "/api-redoc",
)

# Mount routers — gateway & RaaS endpoints
for _r in (
    mission_router, webhook_mcu_router, coupon_router, auth_router,
    vn_auth_router, auth_ui_router, raas_router, revenue_router,
    checkout_router, nowpayments_router, tenant_router, reports_router,
    vn_pricing_router, vn_pilot_router, vn_payments_router, org_router,
    billing_router, autopilot_router, marketplace_router, metrics_router,
    quota_router, tier_config_router, opencore_status_router,
):
    app.include_router(_r)

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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Idempotency-Key", "X-CSRF-Token"],
)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitGatewayMiddleware)
app.add_middleware(PilotCreditGateMiddleware)
app.add_middleware(EngineLicenseGateMiddleware)

_APP_VERSION = "3.3.0"


from src.gateway_health import build_health_response, check_database, component_status, memory_usage_mb

# Backward compatibility aliases
_memory_usage_mb = memory_usage_mb
_check_database = check_database
_component_status = lambda: component_status(billing_adapter)  # noqa: E731


@app.get("/healthz")
async def healthz() -> dict:
    """Lightweight liveness probe (no I/O) for load balancers / Fly.io checks."""
    return {"status": "ok", "version": _APP_VERSION}


@app.get("/health")
async def health_check() -> dict:
    """Enhanced health check with uptime, memory, version, and component status."""
    return await build_health_response(_APP_VERSION, _APP_START_TIME, billing_adapter)


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
