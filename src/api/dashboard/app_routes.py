# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Public analytics, export, health, filter, and telemetry routes for Dashboard App."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from starlette.requests import Request

from src.api.dashboard.app_models import AuthConfig, _facade, dashboard_service, logger

routes_router = APIRouter()


def _svc() -> Any:
    return getattr(_facade(), "dashboard_service", dashboard_service)


@routes_router.get("/api/metrics/api-calls")
async def get_api_calls(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    granularity: Literal["day", "week", "month"] = "day",
):
    """Get API call volume for date range."""
    try:
        svc = _svc()
        daily_usage = await svc._queries.get_daily_usage(start_date, end_date)
        return {"success": True, "data": svc._format_chart_data(daily_usage, granularity)}
    except Exception as e:
        logger.error(f"API calls error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/metrics/licenses")
async def get_licenses(
    date: str = Query(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    """Get active licenses."""
    try:
        return {"success": True, "data": await _svc()._queries.get_active_licenses()}
    except Exception as e:
        logger.error(f"Licenses error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/endpoints")
async def get_endpoints(limit: int = Query(default=10, ge=1, le=50)):
    """Get top endpoints by call volume."""
    try:
        return {"success": True, "data": await _svc()._queries.get_top_endpoints(limit=limit)}
    except Exception as e:
        logger.error(f"Endpoints error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/export")
async def export_data(
    request: Request,
    format: Literal["csv", "json"] = "json",
    start: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    license_key: Optional[str] = Query(None),
    days: int = Query(default=30, ge=1, le=365),
):
    """Export data to CSV or JSON."""
    try:
        if not start or not end:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        else:
            start_date, end_date = start, end

        date_range = (start_date, end_date)
        svc = _svc()
        if format == "csv":
            return PlainTextResponse(await svc.export_to_csv(date_range, license_key), media_type="text/csv")
        return PlainTextResponse(await svc.export_to_json(date_range, license_key), media_type="application/json")
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/health")
async def health_check():
    """Health check endpoint with auth config status."""
    config = getattr(_facade(), "AuthConfig", AuthConfig)()
    return {"status": "healthy", "auth": config.get_config_summary()}


@routes_router.get("/api/filters/licenses")
async def get_license_filters():
    """Get list of license keys for filter dropdown."""
    try:
        licenses = await _svc()._queries.get_active_licenses()
        result, seen = [], set()
        for lic in licenses:
            key = lic.get("license_key", "")
            if key and key not in seen:
                result.append({
                    "key_id": lic.get("key_id", ""),
                    "license_key": key[:20] + "..." if len(key) > 20 else key,
                    "tier": lic.get("tier", "unknown"),
                    "email": lic.get("email", ""),
                })
                seen.add(key)
        return {"success": True, "data": result[:100]}
    except Exception as e:
        logger.error(f"License filters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/telemetry/events")
async def get_telemetry_events(
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get telemetry events with optional filters."""
    try:
        from src.db.queries.analytics_queries import TelemetryQueries

        events = await TelemetryQueries().get_telemetry_events(
            event_type=event_type, start_date=start_date, end_date=end_date, limit=limit
        )
        return {
            "success": True, "data": events,
            "metadata": {
                "total_count": len(events),
                "filters": {"event_type": event_type, "start_date": start_date, "end_date": end_date},
            },
        }
    except Exception as e:
        logger.error(f"Telemetry events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/telemetry/cli-versions")
async def get_cli_versions():
    """Get CLI version distribution from telemetry data."""
    try:
        from src.db.queries.analytics_queries import TelemetryQueries

        return {"success": True, "data": await TelemetryQueries().get_cli_version_distribution()}
    except Exception as e:
        logger.error(f"CLI versions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@routes_router.get("/api/telemetry/sessions")
async def get_session_stats(range_days: int = Query(default=30, ge=1)):
    """Get session statistics from telemetry data."""
    try:
        from src.db.queries.analytics_queries import TelemetryQueries

        return {"success": True, "data": await TelemetryQueries().get_session_statistics(range_days)}
    except Exception as e:
        logger.error(f"Session stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

