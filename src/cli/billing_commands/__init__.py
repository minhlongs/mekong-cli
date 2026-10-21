# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Billing Commands

CLI interface for API usage billing operations:
- simulate: Simulate usage and billing calculation
- submit-usage: Submit real usage for billing
- reconcile: Trigger reconciliation audit
- emit-event: Emit billing events to webhook
"""

from __future__ import annotations

from src.billing.engine import BillingResult, get_engine
from src.billing.event_emitter import get_emitter
from src.billing.idempotency import get_idempotency_manager
from src.billing.reconciliation import get_reconciliation_service
from src.cli.billing_commands.helpers import (
    app,
    billing_main,
    console,
    logger,
    print_billing_result,
    print_error,
    print_success,
)
from src.cli.billing_commands.reconcile_events import (
    emit_billing_event,
    trigger_reconciliation,
)
from src.cli.billing_commands.simulate_submit import (
    simulate_billing,
    submit_usage,
)
from src.cli.billing_commands.status_sync_tiers import (
    billing_status,
    billing_sync,
    billing_sync_status,
    billing_tiers,
)
from src.core.event_bus import EventType, get_event_bus
from src.raas.billing_sync import BillingSyncService, SyncConfig, get_service


def main() -> None:
    """Main entry point for billing CLI."""
    app()


__all__ = [
    "BillingResult",
    "BillingSyncService",
    "EventType",
    "SyncConfig",
    "app",
    "billing_main",
    "billing_status",
    "billing_sync",
    "billing_sync_status",
    "billing_tiers",
    "console",
    "emit_billing_event",
    "get_emitter",
    "get_engine",
    "get_event_bus",
    "get_idempotency_manager",
    "get_reconciliation_service",
    "get_service",
    "logger",
    "main",
    "print_billing_result",
    "print_error",
    "print_success",
    "simulate_billing",
    "submit_usage",
    "trigger_reconciliation",
]
