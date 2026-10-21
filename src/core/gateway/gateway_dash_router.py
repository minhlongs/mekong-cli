# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dashboard and diagnostic endpoints for Mekong Gateway."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.core.gateway.gateway_helpers import scan_projects
from src.core.gateway.models import PresetAction, ProjectInfo
from src.core.gateway.rate_limiter import get_telemetry_hub
from src.core.gateway.streaming import get_mission_streaming_broker
from src.core.gateway_config import GatewayConfig, load_config

dash_router = APIRouter()

GATEWAY_CONFIG: GatewayConfig = load_config()
PRESET_ACTIONS: list[dict[str, str]] = GATEWAY_CONFIG.presets
VERSION = "1.0.0"


@dash_router.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    from src.core.gateway_dashboard import DASHBOARD_HTML as dash_html
    presets_json = json.dumps(PRESET_ACTIONS)
    html = dash_html.replace("__PRESETS_JSON__", presets_json).replace("__VERSION__", f"v{VERSION}")
    return HTMLResponse(content=html)


@dash_router.get("/presets")
def list_presets() -> list[PresetAction]:
    return [PresetAction(**p) for p in PRESET_ACTIONS]


@dash_router.get("/projects")
def list_projects() -> list[ProjectInfo]:
    return scan_projects()


@dash_router.get("/health")
def health_check() -> dict[str, Any]:
    hub_health = get_telemetry_hub().get_health()
    broker_stats = get_mission_streaming_broker().get_stats()
    return {
        **hub_health,
        "status": "ok",
        "health": hub_health.get("status", "healthy"),
        "engine": "Plan-Execute-Verify",
        "version": VERSION,
        "broker": broker_stats,
        "active_streams": broker_stats.get("active_missions", hub_health.get("active_streams", 0)),
        "active_subscribers": broker_stats.get("active_subscribers", hub_health.get("active_subscribers", 0)),
        "active_ws_connections": broker_stats.get("active_ws_connections", 0),
    }


@dash_router.get("/api/v1/gateway/metrics")
def get_gateway_metrics() -> dict[str, Any]:
    metrics = get_telemetry_hub().get_metrics()
    broker_stats = get_mission_streaming_broker().get_stats()
    metrics["active_ws_connections"] = broker_stats.get("active_ws_connections", 0)
    metrics["total_events_emitted"] = broker_stats.get("total_events_emitted", 0)
    metrics["broker"] = broker_stats
    return metrics


__all__ = [
    "GATEWAY_CONFIG",
    "PRESET_ACTIONS",
    "VERSION",
    "dash_router",
    "dashboard",
    "get_gateway_metrics",
    "health_check",
    "list_presets",
    "list_projects",
]
