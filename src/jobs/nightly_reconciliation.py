# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

#!/usr/bin/env python3
"""Mekong CLI - Nightly Reconciliation Cron Job."""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.billing.reconciliation import (  # noqa: E402
    AuditResult,
    ReconciliationConfig,
    get_reconciliation_service,
)
from src.core.auth_tenant import derive_tenant_id  # noqa: E402
from src.core.event_bus import EventType, get_event_bus  # noqa: E402
from src.db.repository import LicenseRepository, get_repository  # noqa: E402
from src.jobs.nightly_reconciliation_models import (  # noqa: E402
    ReconciliationReport,
    StripeDiscrepancy,
)
from src.jobs.nightly_reconciliation_service import (  # noqa: E402
    NightlyReconciliationService,
)
from src.jobs.nightly_reconciliation_stripe import (  # noqa: E402
    StripeReconciliationAdapter,
)

console = Console()
logger = logging.getLogger(__name__)


async def main_async(dry_run: bool = False, audit_date: Optional[str] = None) -> None:
    """Main async entry point."""
    if audit_date:
        try:
            audit_dt = date.fromisoformat(audit_date)
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD[/red]")
            raise SystemExit(1)
    else:
        audit_dt = None

    service = NightlyReconciliationService()
    report = await service.run_full_reconciliation(
        audit_date=audit_dt,
        dry_run=dry_run,
    )

    if report.critical_count > 0:
        console.print(f"\n[bold red]⚠ {report.critical_count} critical discrepancies require attention[/bold red]")
        raise SystemExit(1)


def main() -> None:
    """Main entry point for cron job."""
    import argparse

    parser = argparse.ArgumentParser(description="Nightly billing reconciliation")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without saving results",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Audit date (YYYY-MM-DD, default: yesterday)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        asyncio.run(main_async(dry_run=args.dry_run, audit_date=args.date))
    except KeyboardInterrupt:
        console.print("\n[yellow]Reconciliation cancelled[/yellow]")
        raise SystemExit(0)
    except SystemExit as e:
        raise e
    except Exception as e:
        console.print(f"[bold red]✗ Reconciliation failed: {e}[/bold red]")
        logger.exception("Reconciliation failed")
        raise SystemExit(1)


__all__ = [
    "StripeReconciliationAdapter",
    "StripeDiscrepancy",
    "ReconciliationReport",
    "NightlyReconciliationService",
    "main_async",
    "main",
    "console",
    "Table",
    "AuditResult",
    "ReconciliationConfig",
    "get_reconciliation_service",
    "derive_tenant_id",
    "EventType",
    "get_event_bus",
    "LicenseRepository",
    "get_repository",
]

if __name__ == "__main__":
    main()
