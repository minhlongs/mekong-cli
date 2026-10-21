# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ROI Dashboard — ROIaaS Phase 5."""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from src.analytics.roi_models import (
    AGENT_COSTS,
    DEVELOPER_HOURLY_RATE,
    TIME_ESTIMATES,
    DailyROI,
    ROIMetrics,
)
from src.usage.usage_tracker import UsageTracker, get_tracker


class ROIDashboard:
    """ROI Dashboard for calculating and displaying ROI metrics."""

    def __init__(self, license_key: str, tracker: Optional[UsageTracker] = None) -> None:
        self.license_key = license_key
        self.tracker = tracker or get_tracker()

    def calculate_metrics(self, days: int = 30) -> ROIMetrics:
        report = self.tracker.get_usage_report(self.license_key, days)
        total_minutes_saved = 0
        cmd_saved: Dict[str, int] = {}
        agent_saved: Dict[str, int] = {}
        total_agent_cost = 0.0

        for daily in report.daily_reports:
            for cmd, count in daily.command_breakdown.items():
                est = TIME_ESTIMATES.get(cmd, {"manual": 60, "cli": 5})
                saved = (est["manual"] - est["cli"]) * count
                total_minutes_saved += saved
                cmd_saved[cmd] = cmd_saved.get(cmd, 0) + saved

            for agent, count in daily.agent_breakdown.items():
                est = TIME_ESTIMATES.get(agent, {"manual": 60, "cli": 5})
                saved = (est["manual"] - est["cli"]) * count
                total_minutes_saved += saved
                agent_saved[agent] = agent_saved.get(agent, 0) + saved
                total_agent_cost += AGENT_COSTS.get(agent, 0.05) * count

        hours_saved = total_minutes_saved / 60
        labor_saved = hours_saved * DEVELOPER_HOURLY_RATE
        n_cmd = report.total_commands
        n_agent = report.total_agents
        roi_mult = labor_saved / total_agent_cost if total_agent_cost > 0 else 0

        return ROIMetrics(
            total_minutes_saved=int(total_minutes_saved), total_hours_saved=round(hours_saved, 1),
            labor_cost_saved=round(labor_saved, 2), investment_cost=round(total_agent_cost, 2),
            total_cost_avoided=round(labor_saved, 2), roi_multiplier=round(roi_mult, 1),
            avg_cost_per_command=round(total_agent_cost / n_cmd if n_cmd > 0 else 0, 4),
            avg_cost_per_agent=round(total_agent_cost / n_agent if n_agent > 0 else 0, 4),
            total_commands=n_cmd, total_agents=n_agent, total_pipelines=report.total_pipelines,
            period_days=days, time_saved_by_command=cmd_saved, time_saved_by_agent=agent_saved,
        )

    def get_daily_roi(self, days: int = 30) -> List[DailyROI]:
        report = self.tracker.get_usage_report(self.license_key, days)
        daily_roi: List[DailyROI] = []
        for daily in report.daily_reports:
            minutes = 0
            for cmd, count in daily.command_breakdown.items():
                est = TIME_ESTIMATES.get(cmd, {"manual": 60, "cli": 5})
                minutes += (est["manual"] - est["cli"]) * count
            for agent, count in daily.agent_breakdown.items():
                est = TIME_ESTIMATES.get(agent, {"manual": 60, "cli": 5})
                minutes += (est["manual"] - est["cli"]) * count
            daily_roi.append(DailyROI(
                date=daily.date, minutes_saved=int(minutes),
                cost_saved=round((minutes / 60) * DEVELOPER_HOURLY_RATE, 2),
                commands=daily.total_commands, agents=daily.total_agents,
            ))
        return daily_roi

    def export_json(self, days: int = 30) -> str:
        metrics = self.calculate_metrics(days)
        daily = self.get_daily_roi(days)
        today = datetime.now(timezone.utc)
        return json.dumps({
            "licenseKeyHash": self.tracker._hash_license_key(self.license_key)[:16] + "...",
            "generatedAt": today.isoformat(),
            "period": {"days": days, "startDate": (today - timedelta(days=days)).strftime("%Y-%m-%d"), "endDate": today.strftime("%Y-%m-%d")},
            "summary": metrics.to_dict(),
            "dailyBreakdown": [
                {"date": d.date, "minutesSaved": d.minutes_saved, "costSaved": d.cost_saved, "commands": d.commands, "agents": d.agents}
                for d in daily
            ],
        }, indent=2)

    def generate_ascii_report(self, days: int = 30) -> str:
        m = self.calculate_metrics(days)
        return "\n".join([
            "",
            "╔══════════════════════════════════════════════════════════╗",
            "║              ROI DASHBOARD — ROIaaS Phase 5              ║",
            "╠══════════════════════════════════════════════════════════╣",
            f"║  Period: {days} days{' ' * (46 - len(str(days)))}║",
            f"║  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}{' ' * 37}║",
            "╠══════════════════════════════════════════════════════════╣",
            "║  📊 USAGE SUMMARY                                        ║",
            "╟──────────────────────────────────────────────────────────╢",
            f"║  Total Commands:   {m.total_commands:>6}{' ' * (32 - len(str(m.total_commands)))}║",
            f"║  Total Agents:     {m.total_agents:>6}{' ' * (32 - len(str(m.total_agents)))}║",
            f"║  Total Pipelines:  {m.total_pipelines:>6}{' ' * (32 - len(str(m.total_pipelines)))}║",
            "╠══════════════════════════════════════════════════════════╣",
            "║  ⏱️  TIME SAVINGS                                         ║",
            "╟──────────────────────────────────────────────────────────╢",
            f"║  Minutes Saved:    {m.total_minutes_saved:>6} min{' ' * (26 - len(str(m.total_minutes_saved)))}║",
            f"║  Hours Saved:      {m.total_hours_saved:>6} hrs{' ' * (26 - len(str(m.total_hours_saved)))}║",
            f"║  Labor Cost Saved: ${m.labor_cost_saved:>6}{' ' * (27 - len(str(m.labor_cost_saved)))}║",
            "╠══════════════════════════════════════════════════════════╣",
            "║  💰 ROI METRICS                                          ║",
            "╟──────────────────────────────────────────────────────────╢",
            f"║  Investment Cost:  ${m.investment_cost:>6}{' ' * (27 - len(str(m.investment_cost)))}║",
            f"║  Cost Avoided:     ${m.total_cost_avoided:>6}{' ' * (27 - len(str(m.total_cost_avoided)))}║",
            f"║  ROI Multiplier:   {m.roi_multiplier:>5.1f}x{' ' * (30 - len(f'{m.roi_multiplier:.1f}'))}║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
        ])


def get_dashboard(license_key: str, tracker: Optional[UsageTracker] = None) -> ROIDashboard:
    return ROIDashboard(license_key, tracker)


__all__ = [
    "ROIDashboard",
    "ROIMetrics",
    "DailyROI",
    "TIME_ESTIMATES",
    "AGENT_COSTS",
    "DEVELOPER_HOURLY_RATE",
    "get_dashboard",
]
