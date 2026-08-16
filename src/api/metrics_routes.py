# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Prometheus /metrics endpoint — manual text format, no prometheus_client dep.

Exposes key gateway metrics in Prometheus exposition format (text/plain 0.0.4).
Optionally protected by METRICS_AUTH_TOKEN env var (bearer token).
"""
from __future__ import annotations

import os
import time

from fastapi import APIRouter, Request, Response

router = APIRouter()

_METRICS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


def _prom_line(name: str, labels: dict[str, str] | None, value: float, help_text: str, metric_type: str) -> str:
    """Build a single Prometheus metric block (HELP + TYPE + value line)."""
    label_str = ""
    if labels:
        label_str = "{" + ",".join(f'{k}="{v}"' for k, v in labels.items()) + "}"
    return f"# HELP {name} {help_text}\n# TYPE {name} {metric_type}\n{name}{label_str} {value}\n"


def _build_metrics_text(start_time: float) -> str:
    """Collect metrics from live subsystems and return Prometheus text format."""
    from src.gateway import mcu_billing, _APP_START_TIME
    from src.core.pev_metrics_collector import get_pev_metrics

    lines: list[str] = []

    # mekong_mcu_tenant_count
    try:
        tenant_count = float(mcu_billing.tenant_count)
    except Exception:
        tenant_count = 0.0
    lines.append(_prom_line(
        "mekong_mcu_tenant_count", None, tenant_count,
        "Number of billing tenants", "gauge",
    ))

    # mekong_gateway_uptime_seconds
    uptime = round(time.monotonic() - _APP_START_TIME, 2)
    lines.append(_prom_line(
        "mekong_gateway_uptime_seconds", None, uptime,
        "Seconds since gateway process started", "gauge",
    ))

    # PEV metrics
    try:
        pev = get_pev_metrics()
        gm = pev.get_global_metrics()

        successful = float(gm.get("total_successful", 0))
        failed = float(gm.get("total_failed", 0))
        # pipelines_total by status (counters)
        lines.append(_prom_line(
            "mekong_pev_pipelines_total", {"status": "success"}, successful,
            "Total PEV pipelines by status", "counter",
        ))
        lines.append(_prom_line(
            "mekong_pev_pipelines_total", {"status": "failed"}, failed,
            "Total PEV pipelines by status", "counter",
        ))

        lines.append(_prom_line(
            "mekong_pev_success_rate", None, float(gm.get("overall_success_rate", 0.0)),
            "PEV pipeline success rate (0-1)", "gauge",
        ))
        lines.append(_prom_line(
            "mekong_pev_avg_duration_ms", None, float(gm.get("avg_duration_ms", 0.0)),
            "Average PEV pipeline duration in milliseconds", "gauge",
        ))
    except Exception:
        pass  # PEV metrics unavailable — omit rather than crash

    return "".join(lines)


@router.get("/metrics")
async def prometheus_metrics(request: Request) -> Response:
    """Prometheus metrics endpoint. Optionally gated by bearer token."""
    auth_token = os.getenv("METRICS_AUTH_TOKEN")
    if auth_token:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer ") or auth_header[7:] != auth_token:
            return Response(
                content='{"error": "unauthorized"}',
                status_code=401,
                media_type="application/json",
            )

    body = _build_metrics_text(time.monotonic())
    return Response(content=body, media_type=_METRICS_CONTENT_TYPE)
