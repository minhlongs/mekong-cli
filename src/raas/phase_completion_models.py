# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and summary table rendering for Phase Completion Detector."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class PhaseStatus(str, Enum):
    """Status of each ROIaaS phase."""

    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class PhaseInfo:
    """Information about a phase's status."""

    name: str
    status: PhaseStatus
    description: str
    last_checked: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


def build_initial_phases() -> Dict[str, PhaseInfo]:
    """Initialize all six ROIaaS phase definitions."""
    return {
        "phase_1_license_gate": PhaseInfo(
            name="Phase 1: RAAS_LICENSE_KEY Gate",
            status=PhaseStatus.NOT_STARTED,
            description="License validation and premium feature gating",
        ),
        "phase_2_license_ui": PhaseInfo(
            name="Phase 2: License Management UI",
            status=PhaseStatus.NOT_STARTED,
            description="Admin dashboard for license management",
        ),
        "phase_3_payment_webhook": PhaseInfo(
            name="Phase 3: Stripe/Polar Webhook",
            status=PhaseStatus.NOT_STARTED,
            description="Payment processing and webhook integration",
        ),
        "phase_4_usage_metering": PhaseInfo(
            name="Phase 4: Usage Metering",
            status=PhaseStatus.NOT_STARTED,
            description="Real-time usage tracking and credit metering",
        ),
        "phase_5_analytics_dashboard": PhaseInfo(
            name="Phase 5: Analytics Dashboard",
            status=PhaseStatus.NOT_STARTED,
            description="Business intelligence and usage analytics",
        ),
        "phase_6_terminal_validation": PhaseInfo(
            name="Phase 6: Terminal Validation",
            status=PhaseStatus.NOT_STARTED,
            description="End-to-end integration validation + Completion Certificate",
        ),
    }


def render_phase_summary_table(console: Any, phases: List[PhaseInfo]) -> None:
    """Display summary table of all phases on the given Rich console."""
    from rich.table import Table

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Phase", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    status_icons = {
        PhaseStatus.OPERATIONAL: "✓",
        PhaseStatus.DEGRADED: "⚠",
        PhaseStatus.FAILED: "✗",
        PhaseStatus.INITIALIZING: "⟳",
        PhaseStatus.NOT_STARTED: "○",
    }
    status_colors = {
        PhaseStatus.OPERATIONAL: "green",
        PhaseStatus.DEGRADED: "yellow",
        PhaseStatus.FAILED: "red",
        PhaseStatus.INITIALIZING: "blue",
        PhaseStatus.NOT_STARTED: "dim",
    }

    for phase in phases:
        icon = status_icons[phase.status]
        color = status_colors[phase.status]
        details = phase.errors[0] if phase.errors else "OK"
        table.add_row(
            phase.name,
            f"[{color}]{icon} {phase.status.value.upper()}[/{color}]",
            f"[dim]{details}[/dim]",
        )

    console.print(table)
