"""Mekong CLI - Gateway API Server.

FastAPI server exposing Mekong CLI orchestration to AgencyOS.
REST API + SSE streaming for real-time mission execution.

Usage:
    uvicorn src.gateway:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os as _os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.gateway_mission_routes import router as mission_router, MISSION_STORE
from src.api.gateway_webhook_mcu_routes import router as webhook_mcu_router
from src.raas.missions_api_router import router as raas_router
from src.raas.revenue_router import router as revenue_router
from src.raas.checkout_router import router as checkout_router
from src.raas.tenant_use_case_router import router as tenant_router
from src.raas.reports_router import router as reports_router
from src.raas.autopilot import router as autopilot_router
from src.core.request_logger import RequestLoggerMiddleware
from src.core.mcu_billing import MCUBilling

logger = logging.getLogger(__name__)

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
    description="Unified API contract for AgencyOS → Mekong CLI integration",
    version="3.3.0",
    docs_url="/api-docs",
    redoc_url="/api-redoc",
)

# Mount routers — gateway endpoints
app.include_router(mission_router)
app.include_router(webhook_mcu_router)

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
        "http://localhost:3000,http://localhost:8080,https://mekongmind.pages.dev,https://mekongmind.com,https://www.mekongmind.com,https://api.cashclaw.cc",
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

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "3.3.0",
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
