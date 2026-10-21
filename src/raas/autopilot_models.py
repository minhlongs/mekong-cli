# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Department templates, Pydantic models, and DB schema for RaaS Autopilot."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

_DB_PATH = Path.home() / ".mekong" / "raas" / "autopilot.db"

_AUTOPILOT_DDL = """
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
"""

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
