# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dashboard FastAPI App — ROIaaS Phase 5 REST API for analytics dashboard."""

from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

app = FastAPI(
    title="Mekong Dashboard API", version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc"
)


def run_dashboard(port: int = 8080, open_browser: bool = True, host: str = "0.0.0.0") -> None:
    """Run dashboard server."""
    from src.api.dashboard.app_models import run_dashboard as _run

    _run(port=port, open_browser=open_browser, host=host)


from src.api.dashboard.app_models import (  # noqa: E402, F401
    AuthConfig, BASE_DIR, DashboardService, Permission, STATIC_DIR,
    SessionMiddleware, _ALLOWED_ORIGINS, auth_router, dashboard_service, logger, templates,
)
from src.api.dashboard.app_routes import (  # noqa: E402, F401
    export_data, get_api_calls, get_cli_versions, get_endpoints, get_license_filters,
    get_licenses, get_session_stats, get_telemetry_events, health_check, routes_router,
)
from src.auth.rbac import get_current_user, require_permission  # noqa: E402

app.add_middleware(SessionMiddleware)
app.add_middleware(
    CORSMiddleware, allow_origins=_ALLOWED_ORIGINS, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(auth_router)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Serve dashboard HTML."""
    authenticated = getattr(request.state, "authenticated", False)
    user = get_current_user(request)
    if not (BASE_DIR / "templates" / "dashboard.html").exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "authenticated": authenticated, "user": user}
    )


@app.get("/api/metrics")
@require_permission(Permission.VIEW_DASHBOARD)
async def get_metrics(
    request: Request,
    range_days: int = Query(default=30, ge=1, le=365),
    granularity: Literal["day", "week", "month"] = "day",
    license_key: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
    """Get all dashboard metrics (requires authentication)."""
    try:
        metrics = await dashboard_service.get_metrics(
            range_days=range_days, license_key=license_key, start_date=start_date, end_date=end_date
        )
        return {
            "success": True,
            "data": {
                "api_calls": metrics.api_calls, "active_licenses": metrics.active_licenses,
                "top_endpoints": metrics.top_endpoints, "revenue": metrics.revenue,
                "tier_distribution": metrics.tier_distribution, "last_updated": metrics.last_updated,
                "license_health": metrics.license_health, "renewal_prompts": metrics.renewal_prompts,
                "rate_limit_events": metrics.rate_limit_events,
            },
        }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/license-health")
@require_permission(Permission.VIEW_DASHBOARD)
async def get_license_health(request: Request):
    """Get license health overview with status counts."""
    try:
        metrics = await dashboard_service.get_metrics(range_days=30)
        return {"success": True, "data": metrics.license_health}
    except Exception as e:
        logger.error(f"License health error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/renewal-prompts")
@require_permission(Permission.VIEW_DASHBOARD)
async def get_renewal_prompts(request: Request, days: int = Query(default=7, ge=1, le=30)):
    """Get expired/expiring licenses needing renewal attention."""
    try:
        metrics = await dashboard_service.get_metrics(range_days=30)
        prompts = [
            p for p in metrics.renewal_prompts if abs(p.get("days_since_or_until_expiry", 0)) <= days
        ][:20]
        return {
            "success": True, "data": prompts,
            "metadata": {"window_days": days, "total_count": len(prompts)},
        }
    except Exception as e:
        logger.error(f"Renewal prompts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rate-limit-events")
@require_permission(Permission.VIEW_DASHBOARD)
async def get_rate_limit_events(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
):
    """Get recent rate limit events with optional filters."""
    try:
        events = await dashboard_service._rate_limit_emitter.get_recent_events(
            tenant_id=tenant_id, event_type=event_type, limit=limit
        )
        return {
            "success": True, "data": events,
            "metadata": {
                "total_count": len(events),
                "filters": {"event_type": event_type, "tenant_id": tenant_id},
            },
        }
    except Exception as e:
        logger.error(f"Rate limit events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(routes_router)
