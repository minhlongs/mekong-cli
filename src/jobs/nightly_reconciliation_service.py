# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Nightly Reconciliation Service Implementation."""

from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.billing.reconciliation import (
    AuditResult,
    ReconciliationConfig,
    get_reconciliation_service,
)
from src.core.auth_tenant import derive_tenant_id
from src.core.event_bus import get_event_bus
from src.db.repository import LicenseRepository, get_repository
from src.jobs.nightly_reconciliation_models import (
    NightlyReconciliationReportMixin,
    ReconciliationReport,
    StripeDiscrepancy,
)
from src.jobs.nightly_reconciliation_stripe import StripeReconciliationAdapter

logger = logging.getLogger(__name__)


class NightlyReconciliationService(NightlyReconciliationReportMixin):
    """Nightly reconciliation service with Stripe integration."""

    def __init__(
        self,
        repository: Optional[LicenseRepository] = None,
        stripe_adapter: Optional[StripeReconciliationAdapter] = None,
    ) -> None:
        self._repo = repository or get_repository()
        self._stripe = stripe_adapter or StripeReconciliationAdapter()
        self._event_bus = get_event_bus()
        self._config = ReconciliationConfig()

    async def run_full_reconciliation(
        self,
        audit_date: Optional[date] = None,
        dry_run: bool = False,
    ) -> ReconciliationReport:
        """Run full reconciliation with Stripe comparison."""
        start_time = time.time()
        audit_dt = audit_date or (date.today() - timedelta(days=1))

        c = self._get_console()
        c.print(f"\n[bold cyan]🔍 Nightly Reconciliation[/bold cyan]\nAudit Date: [cyan]{audit_dt}[/cyan]\nDry Run: [yellow]{dry_run}[/yellow]\n")

        licenses = await self._get_active_licenses()
        c.print(f"Found [cyan]{len(licenses)}[/cyan] active licenses\n")

        reconciled_count, stripe_reconciled_count = 0, 0
        discrepancies: List[StripeDiscrepancy] = []
        local_only_discrepancies: List[AuditResult] = []
        warnings: List[str] = []

        for info in licenses:
            l_key, key_id, email = info["license_key"], info["key_id"], info.get("email", "")
            tenant = derive_tenant_id(l_key)
            try:
                l_res = await self._reconcile_local(l_key, key_id, audit_dt)
                if l_res.status != "matched":
                    local_only_discrepancies.append(l_res)
                    warnings.append(f"{tenant}: Local variance ${l_res.variance} ({l_res.variance_percent:.2f}%)")
                else:
                    reconciled_count += 1

                if email:
                    s_res = await self._reconcile_with_stripe(l_key, key_id, email, audit_dt, audit_dt + timedelta(days=1), l_res.actual_amount)
                    if s_res:
                        discrepancies.append(s_res)
                        warnings.append(f"{tenant}: Stripe variance ${s_res.variance} ({s_res.variance_percent:.2f}%)")
                    else:
                        stripe_reconciled_count += 1
                else:
                    warnings.append(f"{tenant}: No email for Stripe lookup")
            except Exception as e:
                logger.error("Reconciliation failed for %s: %s", tenant, e)
                warnings.append(f"{tenant}: Error - {str(e)}")

        total_variance = sum((d.variance for d in discrepancies), Decimal(0))
        critical_count = sum(1 for d in discrepancies if d.variance_percent > 10)
        report = ReconciliationReport(
            run_date=audit_dt, total_licenses=len(licenses), reconciled_count=reconciled_count,
            stripe_reconciled_count=stripe_reconciled_count, discrepancies=discrepancies,
            local_only_discrepancies=local_only_discrepancies, total_variance=total_variance,
            critical_count=critical_count, warnings=warnings, duration_seconds=time.time() - start_time,
        )
        self._print_report(report)
        if not dry_run:
            await self._save_report(report)
        if report.critical_count > 0 or report.total_variance > Decimal("100"):
            await self._trigger_alerts(report)
        return report

    async def _reconcile_local(self, license_key: str, key_id: str, audit_date: date) -> AuditResult:
        service = get_reconciliation_service()
        results = await service.run_daily_reconciliation(audit_date=audit_date)
        res = next((r for r in results if r.license_key == license_key), None)
        return res or AuditResult(
            audit_id=f"local_{license_key}_{audit_date}", license_key=license_key,
            key_id=key_id, audit_date=audit_date, expected_amount=Decimal(0),
            actual_amount=Decimal(0), variance=Decimal(0), variance_percent=0, status="matched",
        )

    async def _reconcile_with_stripe(
        self, license_key: str, key_id: str, email: str = "",
        start: Optional[date] = None, end: Optional[date] = None, local_amount: Decimal = Decimal(0),
        customer_email: Optional[str] = None, period_start: Optional[date] = None, period_end: Optional[date] = None,
    ) -> Optional[StripeDiscrepancy]:
        effective_email = customer_email or email
        effective_start = period_start or start or date.today()
        effective_end = period_end or end or date.today()
        invoices = await self._stripe.get_invoices_for_period(effective_email, effective_start, effective_end)
        if not invoices:
            return None
        stripe_amount = Decimal(0)
        items = []
        for inv in invoices:
            stripe_amount += Decimal(str(inv["amount_due"]))
            items.extend(inv["line_items"])
        variance = local_amount - stripe_amount
        v_pct = float(abs(variance) / stripe_amount * 100) if stripe_amount > 0 else (100.0 if local_amount > 0 else 0.0)
        if abs(variance) < Decimal("0.50") and v_pct < 1:
            return None
        return StripeDiscrepancy(
            license_key=license_key, key_id=key_id, period_start=effective_start, period_end=effective_end,
            local_amount=local_amount, stripe_amount=stripe_amount, variance=variance,
            variance_percent=v_pct, local_line_items=[], stripe_line_items=items,
            status="open" if v_pct > 5 else "investigating", notes=f"Variance detected: {v_pct:.2f}%",
        )

    async def _get_active_licenses(self) -> List[Dict[str, Any]]:
        return []
