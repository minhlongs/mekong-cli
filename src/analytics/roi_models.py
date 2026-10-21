# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ROI Dashboard Metrics and Cost Constants — ROIaaS Phase 5."""

from dataclasses import dataclass, field
from typing import Any, Dict

TIME_ESTIMATES: Dict[str, Dict[str, int]] = {
    "cook": {"manual": 120, "cli": 5},
    "plan": {"manual": 60, "cli": 2},
    "fix": {"manual": 90, "cli": 10},
    "code": {"manual": 180, "cli": 15},
    "test": {"manual": 60, "cli": 5},
    "review": {"manual": 45, "cli": 3},
    "deploy": {"manual": 30, "cli": 2},
    "debug": {"manual": 120, "cli": 15},
    "planner": {"manual": 90, "cli": 3},
    "researcher": {"manual": 180, "cli": 5},
    "fullstack-developer": {"manual": 240, "cli": 10},
    "tester": {"manual": 60, "cli": 3},
    "code-reviewer": {"manual": 90, "cli": 5},
    "debugger": {"manual": 120, "cli": 10},
    "docs-manager": {"manual": 60, "cli": 3},
    "project-manager": {"manual": 45, "cli": 2},
}

AGENT_COSTS: Dict[str, float] = {
    "planner": 0.05,
    "researcher": 0.08,
    "fullstack-developer": 0.15,
    "tester": 0.04,
    "code-reviewer": 0.06,
    "debugger": 0.10,
    "docs-manager": 0.04,
    "project-manager": 0.03,
    "scout": 0.02,
    "explorer": 0.03,
}

DEVELOPER_HOURLY_RATE = 75


@dataclass
class ROIMetrics:
    """ROI metrics dataclass."""

    total_minutes_saved: int = 0
    total_hours_saved: float = 0.0
    labor_cost_saved: float = 0.0
    investment_cost: float = 0.0
    total_cost_avoided: float = 0.0
    roi_multiplier: float = 0.0
    avg_cost_per_command: float = 0.0
    avg_cost_per_agent: float = 0.0
    total_commands: int = 0
    total_agents: int = 0
    total_pipelines: int = 0
    period_days: int = 30
    time_saved_by_command: Dict[str, int] = field(default_factory=dict)
    time_saved_by_agent: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "totalMinutesSaved": self.total_minutes_saved,
            "totalHoursSaved": round(self.total_hours_saved, 1),
            "laborCostSaved": round(self.labor_cost_saved, 2),
            "investmentCost": round(self.investment_cost, 2),
            "totalCostAvoided": round(self.total_cost_avoided, 2),
            "roiMultiplier": round(self.roi_multiplier, 1),
            "avgCostPerCommand": round(self.avg_cost_per_command, 4),
            "avgCostPerAgent": round(self.avg_cost_per_agent, 4),
            "totalCommands": self.total_commands,
            "totalAgents": self.total_agents,
            "totalPipelines": self.total_pipelines,
            "periodDays": self.period_days,
            "timeSavedByCommand": self.time_saved_by_command,
            "timeSavedByAgent": self.time_saved_by_agent,
        }


@dataclass
class DailyROI:
    """Daily ROI metrics."""

    date: str
    minutes_saved: int = 0
    cost_saved: float = 0.0
    commands: int = 0
    agents: int = 0
