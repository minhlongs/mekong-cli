# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autopilot Executor — runs tenant missions on schedule."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Optional
import uuid

import requests

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / ".mekong" / "raas" / "autopilot.db"
GATEWAY_URL = "http://localhost:8000"
SCHEDULE_INTERVALS = {"daily": 86400, "weekly": 604800, "biweekly": 1209600, "monthly": 2592000}


def _get_tenant_api_key(tenant_id: str) -> Optional[str]:
    """Look up tenant API key from tenants.db (daemon uses master key)."""
    tenants_db = Path.home() / ".mekong" / "raas" / "tenants.db"
    if not tenants_db.exists():
        return None
    conn = sqlite3.connect(str(tenants_db))
    conn.row_factory = sqlite3.Row
    try:
        return None
    finally:
        conn.close()


def _get_daemon_key() -> str:
    """Get or create daemon API key."""
    key_file = Path.home() / ".mekong" / "daemon-api-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    try:
        r = requests.post(
            f"{GATEWAY_URL}/v1/onboard",
            json={"name": "Autopilot Daemon", "email": "autopilot@mekong.local"},
            timeout=10,
        )
        if r.status_code == 200:
            key = r.json()["api_key"]
            key_file.write_text(key)
            return key
    except Exception as e:
        logger.error("Failed to get daemon key: %s", e)
    return ""


def _is_due(schedule: str, last_run_ts: float, now: float) -> bool:
    """Check if a goal is due based on schedule and last run."""
    return (now - last_run_ts) >= SCHEDULE_INTERVALS.get(schedule, SCHEDULE_INTERVALS["weekly"])


def _get_last_run_time(tenant_id: str, department: str, goal: str) -> float:
    """Get timestamp of last run for this specific goal."""
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        row = conn.execute(
            "SELECT created_at FROM autopilot_runs WHERE tenant_id = ? AND department = ? "
            "AND goal = ? ORDER BY created_at DESC LIMIT 1",
            (tenant_id, department, goal),
        ).fetchone()
        return datetime.fromisoformat(row[0]).timestamp() if row else 0
    finally:
        conn.close()


def _record_run(tenant_id: str, dept: str, goal: str, status: str, output: str = "", credits: int = 0) -> None:
    """Record an autopilot run."""
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "INSERT INTO autopilot_runs (id, tenant_id, department, goal, status, output, credits_used, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), tenant_id, dept, goal, status, output, credits, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _submit_mission(goal: str, api_key: str) -> tuple[str, str]:
    """Submit mission via gateway API. Returns (status, output)."""
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.post(f"{GATEWAY_URL}/raas/missions", json={"goal": goal}, headers=headers, timeout=10)
        if r.status_code == 402:
            return "no_credits", ""
        if r.status_code != 202:
            return "error", f"HTTP {r.status_code}"

        mission_id = r.json()["id"]
        for _ in range(18):
            time.sleep(10)
            sr = requests.get(f"{GATEWAY_URL}/raas/missions/{mission_id}", headers=headers, timeout=10)
            if sr.status_code == 200:
                data = sr.json()
                if data["status"] == "completed":
                    return "completed", data.get("output", "")
                if data["status"] == "failed":
                    return "failed", data.get("error_message", "")
        return "timeout", ""
    except Exception as e:
        return "error", str(e)


def _deliver_results(config: dict, dept: str, goal: str, output: str) -> None:
    """Deliver results via webhook or email if configured."""
    webhook_url = config.get("webhook_url")
    if webhook_url:
        try:
            payload = {"type": "autopilot.result", "department": dept, "goal": goal, "output": output, "timestamp": datetime.now(timezone.utc).isoformat()}
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception as e:
            logger.warning("Webhook delivery failed: %s", e)


def execute_tenant_cycle(tenant_id: str) -> int:
    """Execute one autopilot cycle for a specific tenant. Returns missions queued."""
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT config, active FROM autopilot_configs WHERE tenant_id = ? AND active = 1", (tenant_id,)).fetchone()
        if not row:
            return 0
    finally:
        conn.close()

    config = json.loads(row["config"])
    now = datetime.now(timezone.utc).timestamp()
    api_key = _get_daemon_key()
    if not api_key:
        logger.error("No daemon API key — cannot execute autopilot")
        return 0

    missions_run = 0
    for dept_id, goals in config.get("departments", {}).items():
        for goal_item in goals:
            goal_text = goal_item.get("goal", "") if isinstance(goal_item, dict) else str(goal_item)
            schedule = goal_item.get("schedule", "weekly") if isinstance(goal_item, dict) else "weekly"
            if not _is_due(schedule, _get_last_run_time(tenant_id, dept_id, goal_text), now):
                continue

            logger.info("Autopilot [%s/%s]: %s", tenant_id[:8], dept_id, goal_text[:50])
            status, output = _submit_mission(goal_text, api_key)
            _record_run(tenant_id, dept_id, goal_text, status, output, credits=1 if status == "completed" else 0)
            if output and status == "completed":
                _deliver_results(config, dept_id, goal_text, output)
            missions_run += 1

    return missions_run


def execute_all_tenants() -> dict:
    """Execute autopilot for ALL active tenants. Called by daemon loop."""
    if not _DB_PATH.exists():
        return {"tenants": 0, "missions": 0}
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        rows = conn.execute("SELECT tenant_id FROM autopilot_configs WHERE active = 1").fetchall()
    finally:
        conn.close()
    return {"tenants": len(rows), "missions": sum(execute_tenant_cycle(row[0]) for row in rows)}
