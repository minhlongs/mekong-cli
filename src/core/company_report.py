"""Company Report — /company report backend.

Report types: brief, revenue, usage, agents, health.
Reads from .mekong/ data sources and MCUGate SQLite.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from src.core.mcu_gate import MCUGate

logger = logging.getLogger(__name__)

AGENT_ROLES = ("cto", "cmo", "coo", "cfo", "cs", "sales", "editor", "data")
TIER_PRICE = {"starter": 49, "growth": 149, "premium": 499}
MCU_PRICE = 0.049  # avg $/MCU


def generate_report(
    report_type: str = "brief",
    period: str = "week",
    base_dir: str | Path = ".",
    mcu_gate: MCUGate | None = None,
    tenant_id: str = "default",
) -> dict:
    """Generate a business intelligence report.

    Args:
        report_type: brief|revenue|usage|agents|health
        period: week|month|quarter
        base_dir: Project root directory.
        mcu_gate: Optional MCUGate for DB queries.
        tenant_id: Tenant ID for gate queries.

    Returns:
        Report dict with type-specific data.
    """
    generators = {
        "brief": _report_brief,
        "revenue": _report_revenue,
        "usage": _report_usage,
        "agents": _report_agents,
        "health": _report_health,
    }

    gen = generators.get(report_type)
    if not gen:
        raise ValueError(
            f"Unknown report type: {report_type}. "
            f"Valid: {list(generators.keys())}"
        )

    base = Path(base_dir)
    company = _load_company(base)
    memory = _load_memory(base)
    ledger = _load_ledger(base, mcu_gate, tenant_id)

    report = gen(company, memory, ledger, period)
    report["type"] = report_type
    report["period"] = period
    report["generated_at"] = datetime.now(timezone.utc).isoformat()

    # Auto-save
    _save_report(base, report_type, report)

    return report


def _report_brief(company: dict, memory: list, ledger: list, period: str) -> dict:
    """CEO summary — all metrics combined."""
    tasks = _filter_by_period(memory, period)
    success = sum(1 for t in tasks if t.get("status") == "success")
    total = len(tasks)
    total_mcu = sum(t.get("mcu", 0) for t in tasks)

    # Agent breakdown
    agent_tasks = {}
    for role in AGENT_ROLES:
        count = sum(1 for t in tasks if t.get("agent") == role)
        agent_tasks[role] = count

    most_active = max(agent_tasks, key=agent_tasks.get) if agent_tasks else "none"

    return {
        "company_name": company.get("company_name", "Unknown"),
        "tasks_done": total,
        "success_rate": round(success / total * 100, 1) if total else 0,
        "mcu_used": total_mcu,
        "llm_cost": round(total_mcu * MCU_PRICE, 2),
        "most_active_agent": most_active,
        "agent_tasks": agent_tasks,
    }


def _report_revenue(company: dict, memory: list, ledger: list, period: str) -> dict:
    """Revenue breakdown by tier."""
    seed_entries = [e for e in ledger if e.get("type") == "seed"]
    total_mcu_sold = sum(e.get("amount", 0) for e in seed_entries)
    mcu_revenue = round(total_mcu_sold * MCU_PRICE, 2)

    return {
        "company_name": company.get("company_name", "Unknown"),
        "total_mcu_sold": total_mcu_sold,
        "mcu_revenue": mcu_revenue,
        "seed_count": len(seed_entries),
        "tier_prices": TIER_PRICE,
    }


def _report_usage(company: dict, memory: list, ledger: list, period: str) -> dict:
    """Usage by agent and model."""
    tasks = _filter_by_period(memory, period)

    by_agent = {}
    for role in AGENT_ROLES:
        agent_tasks = [t for t in tasks if t.get("agent") == role]
        mcu = sum(t.get("mcu", 0) for t in agent_tasks)
        by_agent[role] = {"tasks": len(agent_tasks), "mcu": mcu, "cost": round(mcu * MCU_PRICE, 2)}

    total_mcu = sum(v["mcu"] for v in by_agent.values())
    total_cost = round(total_mcu * MCU_PRICE, 2)
    mcu_revenue = round(total_mcu * MCU_PRICE, 2)
    margin = round(mcu_revenue - total_cost, 2)

    return {
        "company_name": company.get("company_name", "Unknown"),
        "by_agent": by_agent,
        "total_mcu": total_mcu,
        "total_cost": total_cost,
        "mcu_revenue": mcu_revenue,
        "margin": margin,
    }


def _report_agents(company: dict, memory: list, ledger: list, period: str) -> dict:
    """Agent performance report."""
    tasks = _filter_by_period(memory, period)
    agents = {}

    for role in AGENT_ROLES:
        agent_tasks = [t for t in tasks if t.get("agent") == role]
        total = len(agent_tasks)
        success = sum(1 for t in agent_tasks if t.get("status") == "success")
        mcu = sum(t.get("mcu", 0) for t in agent_tasks)

        agents[role] = {
            "tasks": total,
            "success_rate": round(success / total * 100, 1) if total else 0,
            "avg_mcu": round(mcu / total, 1) if total else 0,
            "total_mcu": mcu,
        }

    # Find alerts (< 90% success)
    alerts = [
        f"{role} success rate {d['success_rate']}% < 90%"
        for role, d in agents.items()
        if d["tasks"] > 0 and d["success_rate"] < 90
    ]

    return {
        "company_name": company.get("company_name", "Unknown"),
        "agents": agents,
        "alerts": alerts,
    }


def _report_health(company: dict, memory: list, ledger: list, period: str) -> dict:
    """System health report."""
    tasks = _filter_by_period(memory, period)
    total = len(tasks)
    errors = sum(1 for t in tasks if t.get("status") == "failed")
    error_rate = round(errors / total * 100, 1) if total else 0

    # MCU gate stats from ledger
    locks = sum(1 for e in ledger if e.get("type") == "lock")
    confirms = sum(1 for e in ledger if e.get("type") == "confirm")
    refunds = sum(1 for e in ledger if e.get("type") == "refund")

    return {
        "company_name": company.get("company_name", "Unknown"),
        "total_tasks": total,
        "errors": errors,
        "error_rate": error_rate,
        "mcu_gate": {
            "locks": locks,
            "confirms": confirms,
            "refunds": refunds,
        },
    }


def _load_company(base: Path) -> dict:
    f = base / ".mekong" / "company.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _load_memory(base: Path) -> list[dict]:
    f = base / ".mekong" / "memory.json"
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _load_ledger(
    base: Path, mcu_gate: MCUGate | None, tenant_id: str
) -> list[dict]:
    if mcu_gate:
        rows = mcu_gate._conn.execute(
            "SELECT id, tenant_id, mission_id, amount, type, status, created_at "
            "FROM mcu_ledger WHERE tenant_id = ? ORDER BY created_at",
            (tenant_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    f = base / ".mekong" / "mcu_ledger.json"
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("entries", [])
    except (json.JSONDecodeError, OSError):
        return []


def _filter_by_period(memory: list[dict], period: str) -> list[dict]:
    """Filter memory entries by period. Simple filter — returns all for now."""
    # In production, filter by timestamp vs period
    # For now, return all entries (period filtering requires datetime parsing)
    return memory


def _save_report(base: Path, report_type: str, report: dict) -> None:
    reports_dir = base / ".mekong" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = reports_dir / f"{date}-{report_type}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
