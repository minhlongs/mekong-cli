"""Autopilot — the REAL product. Each tenant gets a daemon running THEIR business.

This is WHY someone pays $49/mo:
- Not for API calls (they can self-host free)
- For 22 department heads working 24/7 on THEIR goals
- Configure once → results delivered forever

Architecture:
    POST /raas/autopilot       → customer configures departments + goals + schedule
    GET  /raas/autopilot       → current config
    GET  /raas/autopilot/runs  → execution history

    Background: TenantDaemon picks up configs, executes on schedule,
    delivers results via webhook/email.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.raas.auth import TenantContext, get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/raas", tags=["Autopilot"])

_DB_PATH = Path.home() / ".mekong" / "raas" / "autopilot.db"

# Available departments and their default recurring goals
DEPARTMENT_TEMPLATES = {
    "finance": {
        "name": "Finance",
        "default_goals": [
            {"goal": "Generate weekly P&L summary and cash flow forecast", "schedule": "weekly"},
            {"goal": "Review and categorize this week's expenses", "schedule": "weekly"},
        ],
    },
    "marketing": {
        "name": "Marketing",
        "default_goals": [
            {"goal": "Create 3 social media posts for this week", "schedule": "weekly"},
            {"goal": "SEO audit — find new keyword opportunities", "schedule": "monthly"},
        ],
    },
    "sales": {
        "name": "Sales",
        "default_goals": [
            {"goal": "Generate 10 new lead prospects matching our ICP", "schedule": "weekly"},
            {"goal": "Draft follow-up emails for last week's leads", "schedule": "weekly"},
        ],
    },
    "content": {
        "name": "Content",
        "default_goals": [
            {"goal": "Write one blog post on a trending topic in our industry", "schedule": "weekly"},
            {"goal": "Create email newsletter draft for this week", "schedule": "weekly"},
        ],
    },
    "engineering": {
        "name": "Engineering",
        "default_goals": [
            {"goal": "Code review — scan for security vulnerabilities and tech debt", "schedule": "weekly"},
            {"goal": "Generate sprint retrospective report", "schedule": "biweekly"},
        ],
    },
    "legal": {
        "name": "Legal",
        "default_goals": [
            {"goal": "Review and update Terms of Service for compliance", "schedule": "monthly"},
            {"goal": "GDPR/privacy compliance check", "schedule": "monthly"},
        ],
    },
    "hr": {
        "name": "HR",
        "default_goals": [
            {"goal": "Draft job descriptions for open roles", "schedule": "monthly"},
        ],
    },
    "security": {
        "name": "Security",
        "default_goals": [
            {"goal": "Security scan — check API endpoints, headers, auth flow", "schedule": "weekly"},
        ],
    },
    "ops": {
        "name": "Operations",
        "default_goals": [
            {"goal": "Generate operations health report for all services", "schedule": "daily"},
        ],
    },
    "analyst": {
        "name": "Analyst",
        "default_goals": [
            {"goal": "Competitive analysis — what did competitors ship this week", "schedule": "weekly"},
        ],
    },
    "growth": {
        "name": "Growth",
        "default_goals": [
            {"goal": "Analyze signup funnel — where are users dropping off", "schedule": "weekly"},
            {"goal": "Design one growth experiment to test this week", "schedule": "weekly"},
        ],
    },
}


# ─── Models ──────────────────────────────────────────────────

class AutopilotGoal(BaseModel):
    goal: str = Field(..., description="What the department should do")
    schedule: str = Field("weekly", description="daily|weekly|biweekly|monthly")


class AutopilotConfig(BaseModel):
    departments: dict[str, List[AutopilotGoal]] = Field(
        ..., description="Map of department_id → list of goals with schedules"
    )
    webhook_url: Optional[str] = Field(None, description="URL to POST results to")
    email: Optional[str] = Field(None, description="Email to send results to")
    active: bool = Field(True, description="Enable/disable autopilot")


class AutopilotStatus(BaseModel):
    tenant_id: str
    active: bool
    departments: int
    total_goals: int
    total_runs: int
    last_run: Optional[str]
    config: dict


class AutopilotRun(BaseModel):
    id: str
    department: str
    goal: str
    status: str
    output_preview: str
    created_at: str
    credits_used: int


# ─── Database ────────────────────────────────────────────────

def _init_db():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS autopilot_configs (
            tenant_id TEXT PRIMARY KEY,
            config TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS autopilot_runs (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            department TEXT NOT NULL,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            output TEXT DEFAULT '',
            credits_used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_runs_tenant ON autopilot_runs(tenant_id, created_at);
    """)
    conn.close()


_db_initialized = False


def _ensure_db():
    """Lazy init — only create tables on first actual use."""
    global _db_initialized
    if not _db_initialized:
        _init_db()
        _db_initialized = True


# ─── Endpoints ───────────────────────────────────────────────

@router.get("/autopilot/departments")
def list_departments():
    """List available departments and their default goals."""
    return {
        dept_id: {
            "name": dept["name"],
            "default_goals": dept["default_goals"],
        }
        for dept_id, dept in DEPARTMENT_TEMPLATES.items()
    }


@router.post("/autopilot", response_model=AutopilotStatus)
def configure_autopilot(
    config: AutopilotConfig,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Configure autopilot for this tenant. Departments run on schedule."""
    now = datetime.now(timezone.utc).isoformat()

    # Validate departments
    for dept_id in config.departments:
        if dept_id not in DEPARTMENT_TEMPLATES:
            raise HTTPException(400, f"Unknown department: {dept_id}")

    config_json = config.model_dump_json()

    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            """INSERT INTO autopilot_configs (tenant_id, config, active, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(tenant_id) DO UPDATE SET config=?, active=?, updated_at=?""",
            (tenant.tenant_id, config_json, int(config.active), now, now,
             config_json, int(config.active), now),
        )
        conn.commit()
    finally:
        conn.close()

    total_goals = sum(len(goals) for goals in config.departments.values())

    return AutopilotStatus(
        tenant_id=tenant.tenant_id,
        active=config.active,
        departments=len(config.departments),
        total_goals=total_goals,
        total_runs=0,
        last_run=None,
        config=config.model_dump(),
    )


@router.get("/autopilot", response_model=AutopilotStatus)
def get_autopilot(tenant: TenantContext = Depends(get_tenant_context)):
    """Get current autopilot configuration."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM autopilot_configs WHERE tenant_id = ?",
            (tenant.tenant_id,),
        ).fetchone()

        if not row:
            return AutopilotStatus(
                tenant_id=tenant.tenant_id,
                active=False, departments=0, total_goals=0,
                total_runs=0, last_run=None,
                config={"departments": {}, "active": False},
            )

        config = json.loads(row["config"])
        depts = config.get("departments", {})

        run_count = conn.execute(
            "SELECT COUNT(*) as c FROM autopilot_runs WHERE tenant_id = ?",
            (tenant.tenant_id,),
        ).fetchone()["c"]

        last_run = conn.execute(
            "SELECT created_at FROM autopilot_runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 1",
            (tenant.tenant_id,),
        ).fetchone()

        return AutopilotStatus(
            tenant_id=tenant.tenant_id,
            active=bool(row["active"]),
            departments=len(depts),
            total_goals=sum(len(g) for g in depts.values()),
            total_runs=run_count,
            last_run=last_run["created_at"] if last_run else None,
            config=config,
        )
    finally:
        conn.close()


@router.get("/autopilot/runs", response_model=List[AutopilotRun])
def list_runs(
    limit: int = 20,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List recent autopilot execution runs."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM autopilot_runs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?",
            (tenant.tenant_id, limit),
        ).fetchall()

        return [
            AutopilotRun(
                id=r["id"],
                department=r["department"],
                goal=r["goal"],
                status=r["status"],
                output_preview=(r["output"] or "")[:200],
                created_at=r["created_at"],
                credits_used=r["credits_used"],
            )
            for r in rows
        ]
    finally:
        conn.close()


@router.post("/autopilot/trigger")
def trigger_now(tenant: TenantContext = Depends(get_tenant_context)):
    """Manually trigger one autopilot cycle for this tenant (for testing)."""
    from src.raas.autopilot_executor import execute_tenant_cycle

    result = execute_tenant_cycle(tenant.tenant_id)
    return {"triggered": True, "missions_queued": result}
