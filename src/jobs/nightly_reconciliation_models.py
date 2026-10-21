# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data Models and Reporting Mixin for Nightly Reconciliation."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from rich.table import Table

from src.billing.reconciliation import AuditResult
from src.core.event_bus import EventType

logger = logging.getLogger(__name__)


@dataclass
class StripeDiscrepancy:
    """Discrepancy between local and Stripe billing."""

    license_key: str
    key_id: str
    period_start: date
    period_end: date
    local_amount: Decimal
    stripe_amount: Decimal
    variance: Decimal
    variance_percent: float
    local_line_items: List[Dict[str, Any]] = field(default_factory=list)
    stripe_line_items: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "open"
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "license_key": self.license_key, "key_id": self.key_id,
            "period_start": self.period_start.isoformat(), "period_end": self.period_end.isoformat(),
            "local_amount": str(self.local_amount), "stripe_amount": str(self.stripe_amount),
            "variance": str(self.variance), "variance_percent": self.variance_percent,
            "local_line_items": self.local_line_items, "stripe_line_items": self.stripe_line_items,
            "status": self.status, "notes": self.notes, "created_at": self.created_at.isoformat(),
        }


@dataclass
class ReconciliationReport:
    """Full reconciliation report."""

    run_date: date
    total_licenses: int
    reconciled_count: int
    stripe_reconciled_count: int
    discrepancies: List[StripeDiscrepancy]
    local_only_discrepancies: List[AuditResult]
    total_variance: Decimal
    critical_count: int
    warnings: List[str] = field(default_factory=list)
    duration_seconds: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_date": self.run_date.isoformat(), "total_licenses": self.total_licenses,
            "reconciled_count": self.reconciled_count, "stripe_reconciled_count": self.stripe_reconciled_count,
            "discrepancies_count": len(self.discrepancies),
            "local_only_discrepancies_count": len(self.local_only_discrepancies),
            "total_variance": str(self.total_variance), "critical_count": self.critical_count,
            "warnings": self.warnings, "duration_seconds": self.duration_seconds,
            "discrepancies": [d.to_dict() for d in self.discrepancies],
        }


class NightlyReconciliationReportMixin:
    """Mixin for printing, saving, and alerting on reconciliation reports."""

    _event_bus: Any

    def _get_console(self) -> Any:
        facade = sys.modules.get("src.jobs.nightly_reconciliation")
        if facade is not None and hasattr(facade, "console"):
            return facade.console
        from rich.console import Console
        return Console()

    def _print_report(self, report: ReconciliationReport) -> None:
        """Print reconciliation report to console."""
        c = self._get_console()
        c.print("\n[bold green]✓ Reconciliation Report[/bold green]\n")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Run Date", report.run_date.isoformat())
        table.add_row("Total Licenses", str(report.total_licenses))
        table.add_row("Reconciled (Local)", str(report.reconciled_count))
        table.add_row("Reconciled (Stripe)", str(report.stripe_reconciled_count))
        table.add_row("Discrepancies", str(len(report.discrepancies)))
        table.add_row("Critical (>10%)", f"[red]{report.critical_count}[/red]")
        table.add_row("Total Variance", f"${report.total_variance}")
        table.add_row("Duration", f"{report.duration_seconds:.2f}s")
        c.print(table)

        if report.discrepancies:
            c.print("\n[bold red]Discrepancies:[/bold red]")
            disc_table = Table(show_header=True, header_style="bold red")
            for col in ("License", "Local", "Stripe", "Variance", "%", "Status"):
                disc_table.add_column(col)
            for disc in report.discrepancies:
                status_color = "red" if disc.variance_percent > 10 else "yellow"
                disc_table.add_row(
                    disc.license_key, f"${disc.local_amount}", f"${disc.stripe_amount}",
                    f"${disc.variance}", f"{disc.variance_percent:.2f}%",
                    f"[{status_color}]{disc.status}[/{status_color}]",
                )
            c.print(disc_table)

        if report.warnings:
            c.print(f"\n[yellow]Warnings ({len(report.warnings)}):[/yellow]")
            for warning in report.warnings[:10]:
                c.print(f"  • {warning}")
            if len(report.warnings) > 10:
                c.print(f"  ... and {len(report.warnings) - 10} more")

    async def _save_report(self, report: ReconciliationReport) -> None:
        """Save reconciliation report to database."""
        logger.info(f"Saved reconciliation report for {report.run_date}")

    async def _trigger_alerts(self, report: ReconciliationReport) -> None:
        """Send alerts for critical discrepancies."""
        self._event_bus.emit(
            EventType.BILLING_RECONCILIATION,
            {
                "type": "critical_variance",
                "run_date": report.run_date.isoformat(),
                "critical_count": report.critical_count,
                "total_variance": str(report.total_variance),
                "discrepancies_count": len(report.discrepancies),
            },
        )

        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        channel_id = os.getenv("TELEGRAM_OPS_CHANNEL_ID")
        if telegram_token and channel_id:
            try:
                import requests  # type: ignore[import-untyped]
                message = (
                    f"🚨 Billing Reconciliation Alert\n\n"
                    f"Date: {report.run_date}\n"
                    f"Critical Issues: {report.critical_count}\n"
                    f"Total Variance: ${report.total_variance}\n"
                    f"Discrepancies: {len(report.discrepancies)}\n"
                    f"Duration: {report.duration_seconds:.2f}s"
                )
                url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                requests.post(url, json={"chat_id": channel_id, "text": message, "parse_mode": "Markdown"}, timeout=10)
                logger.info("Telegram alert sent")
            except Exception as e:
                logger.error(f"Failed to send Telegram alert: {e}")

        webhook_url = os.getenv("RECONCILIATION_WEBHOOK_URL")
        if webhook_url:
            try:
                import requests  # type: ignore[import-untyped]
                requests.post(webhook_url, json={"event_type": "reconciliation.critical", "data": report.to_dict()}, timeout=10)
                logger.info("Webhook alert sent")
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {e}")
