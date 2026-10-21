# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autopilot — tenant daemon API routes for department goals and schedules."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import sqlite3
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.autopilot_models import (
    _AUTOPILOT_DDL,
    _DB_PATH,
    DEPARTMENT_TEMPLATES,
    AutopilotConfig,
    AutopilotGoal,
    AutopilotRun,
    AutopilotStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/raas", tags=["Autopilot"])
_db_initialized = False


def _init_db() -> None:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.executescript(_AUTOPILOT_DDL)
    conn.close()


def _ensure_db() -> None:
    global _db_initialized
    if not _db_initialized:
        _init_db()
        _db_initialized = True


@router.get("/autopilot/departments")
def list_departments() -> dict:
    return {
        dept_id: {"name": dept["name"], "default_goals": dept["default_goals"]}
        for dept_id, dept in DEPARTMENT_TEMPLATES.items()
    }


@router.post("/autopilot", response_model=AutopilotStatus)
def configure_autopilot(
    config: AutopilotConfig,
    tenant: TenantContext = Depends(get_tenant_context),
) -> AutopilotStatus:
    now = datetime.now(timezone.utc).isoformat()
    for dept_id in config.departments:
        if dept_id not in DEPARTMENT_TEMPLATES:
            raise HTTPException(400, f"Unknown department: {dept_id}")

    config_json = config.model_dump_json()
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "INSERT INTO autopilot_configs (tenant_id, config, active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(tenant_id) DO UPDATE SET config=?, active=?, updated_at=?",
            (tenant.tenant_id, config_json, int(config.active), now, now, config_json, int(config.active), now),
        )
        conn.commit()
    finally:
        conn.close()

    return AutopilotStatus(
        tenant_id=tenant.tenant_id, active=config.active,
        departments=len(config.departments),
        total_goals=sum(len(goals) for goals in config.departments.values()),
        total_runs=0, last_run=None, config=config.model_dump(),
    )


@router.get("/autopilot", response_model=AutopilotStatus)
def get_autopilot(
    tenant: TenantContext = Depends(get_tenant_context),
) -> AutopilotStatus:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM autopilot_configs WHERE tenant_id = ?", (tenant.tenant_id,)
        ).fetchone()
        if not row:
            return AutopilotStatus(
                tenant_id=tenant.tenant_id, active=False, departments=0,
                total_goals=0, total_runs=0, last_run=None,
                config={"departments": {}, "active": False},
            )

        config = json.loads(row["config"])
        depts = config.get("departments", {})
        run_count = conn.execute(
            "SELECT COUNT(*) as c FROM autopilot_runs WHERE tenant_id = ?", (tenant.tenant_id,)
        ).fetchone()["c"]
        last_run = conn.execute(
            "SELECT created_at FROM autopilot_runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 1",
            (tenant.tenant_id,),
        ).fetchone()

        return AutopilotStatus(
            tenant_id=tenant.tenant_id, active=bool(row["active"]),
            departments=len(depts), total_goals=sum(len(g) for g in depts.values()),
            total_runs=run_count, last_run=last_run["created_at"] if last_run else None,
            config=config,
        )
    finally:
        conn.close()


@router.get("/autopilot/runs", response_model=List[AutopilotRun])
def list_runs(
    limit: int = 20,
    tenant: TenantContext = Depends(get_tenant_context),
) -> List[AutopilotRun]:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM autopilot_runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
            (tenant.tenant_id, limit),
        ).fetchall()
        return [
            AutopilotRun(
                id=r["id"], department=r["department"], goal=r["goal"], status=r["status"],
                output_preview=(r["output"] or "")[:200], created_at=r["created_at"],
                credits_used=r["credits_used"],
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/autopilot/trigger")
def trigger_now(tenant: TenantContext = Depends(get_tenant_context)) -> dict:
    from src.raas.autopilot_executor import execute_tenant_cycle

    return {"triggered": True, "missions_queued": execute_tenant_cycle(tenant.tenant_id)}


__all__ = [
    "AutopilotConfig", "AutopilotGoal", "AutopilotRun", "AutopilotStatus",
    "DEPARTMENT_TEMPLATES", "_DB_PATH", "_ensure_db", "_init_db",
    "configure_autopilot", "get_autopilot", "list_departments",
    "list_runs", "router", "trigger_now",
]
