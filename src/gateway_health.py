# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Health check probe utilities for Gateway API Server."""

from __future__ import annotations

import os as _os
import sys
import time as _time
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def memory_usage_mb() -> Optional[float]:
    """Return RSS memory in MB, or None if psutil unavailable."""
    try:
        import psutil
        proc = psutil.Process()
        return round(proc.memory_info().rss / 1024 / 1024, 2)
    except ImportError:
        return None


async def check_database() -> Dict[str, Any]:
    """Probe PostgreSQL connectivity via asyncpg pool."""
    db_url = _os.getenv("DATABASE_URL")
    if not db_url:
        return {"status": "disabled", "configured": False}
    try:
        from src.db.database import get_database
        db = get_database()
        if db._pool is None:
            return {"status": "not_connected", "configured": True}
        async with db._pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "configured": True}
    except Exception as exc:
        return {"status": "unhealthy", "configured": True, "error": str(exc)}


def component_status(billing_adapter: Any) -> Dict[str, Dict[str, Any]]:
    """Check key component availability without external I/O."""
    components: Dict[str, Dict[str, Any]] = {}

    try:
        _ = billing_adapter
        components["billing"] = {"status": "healthy"}
    except Exception as exc:
        components["billing"] = {"status": "unhealthy", "error": str(exc)}

    try:
        from src.core.auth_jwt import decode_jwt  # noqa: F401
        components["auth"] = {"status": "healthy"}
    except Exception as exc:
        components["auth"] = {"status": "unhealthy", "error": str(exc)}

    sentry_dsn = _os.getenv("SENTRY_DSN")
    components["sentry"] = {
        "status": "healthy" if sentry_dsn else "disabled",
        "configured": bool(sentry_dsn),
    }

    otel_endpoint = _os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    components["otel"] = {
        "status": "healthy" if otel_endpoint else "disabled",
        "configured": bool(otel_endpoint),
    }

    return components


async def build_health_response(
    app_version: str, start_time: float, billing_adapter: Any
) -> Dict[str, Any]:
    """Build enhanced health check payload."""
    uptime_seconds = round(_time.monotonic() - start_time, 2)
    components = component_status(billing_adapter)
    components["database"] = await check_database()

    required = {"billing", "auth", "database"}
    overall = "healthy"
    for name, info in components.items():
        if name in required and info.get("status") == "unhealthy":
            overall = "unhealthy"
            break

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": app_version,
        "uptime_seconds": uptime_seconds,
        "python_version": sys.version.split()[0],
        "memory_mb": memory_usage_mb(),
        "components": components,
    }
