# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Core billing calculation engine for API usage metering."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Dict, List, Optional

from src.core.auth_tenant import derive_tenant_id
from src.core.usage_metering import UsageEvent
from src.db.repository import LicenseRepository, get_repository
from src.raas.billing_engine_models import (
    VALID_PLANS,
    BillingResult,
    LineItem,
    RateCard,
)
from src.raas.billing_engine_resolver import RateCardResolver

logger = logging.getLogger(__name__)


class BillingEngine:
    """Core billing calculation engine aggregating usage events against rate cards."""

    def __init__(
        self,
        repository: Optional[LicenseRepository] = None,
        rate_resolver: Optional[RateCardResolver] = None,
    ) -> None:
        self._repo = repository or get_repository()
        self._rate_resolver = rate_resolver or RateCardResolver(self._repo)

    async def calculate_charges(
        self,
        license_key: str,
        usage_events: List[UsageEvent],
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> BillingResult:
        """Calculate charges for a list of usage events."""
        if not usage_events:
            now = datetime.now(timezone.utc)
            return BillingResult(
                license_key=license_key, key_id="",
                period_start=period_start or now, period_end=period_end or now,
            )

        key_id = usage_events[0].metadata.get("key_id", "")
        aggregated = self._aggregate_events(usage_events)
        line_items: List[LineItem] = []
        total = Decimal(0)
        included_used: Dict[str, Decimal] = {}

        for (event_type, model_name), events in aggregated.items():
            rate_card = await self._rate_resolver.resolve(
                license_key=license_key, event_type=event_type, model_name=model_name
            )
            if not rate_card:
                logger.warning(f"No rate card for {event_type}/{model_name}, skipping")
                continue

            total_qty = sum(Decimal(str(e.value)) for e in events)
            cache_key = f"{rate_card.plan_tier}:{event_type}:{model_name or '*'}"
            used_so_far = included_used.get(cache_key, Decimal(0))
            remaining_inc = rate_card.included_quantity - used_so_far

            charge, overage = rate_card.calculate_charge(total_qty, remaining_inc)
            included_used[cache_key] = used_so_far + min(total_qty, remaining_inc)

            line_items.append(
                LineItem(
                    event_type=event_type, model_name=model_name, quantity=total_qty,
                    unit=rate_card.unit, unit_price=rate_card.unit_price,
                    subtotal=charge, final_amount=charge,
                    metadata={
                        "event_count": len(events),
                        "overage_quantity": str(overage),
                        "included_used": str(included_used[cache_key]),
                    },
                )
            )
            total += charge

        return BillingResult(
            license_key=license_key, key_id=key_id,
            period_start=period_start or min(e.timestamp for e in usage_events),
            period_end=period_end or max(e.timestamp for e in usage_events),
            line_items=line_items, total=total,
        )

    def _aggregate_events(
        self, events: List[UsageEvent]
    ) -> Dict[tuple[str, Optional[str]], List[UsageEvent]]:
        aggregated: Dict[tuple[str, Optional[str]], List[UsageEvent]] = {}
        for event in events:
            aggregated.setdefault((event.event_type, event.metadata.get("model")), []).append(event)
        return aggregated

    async def calculate_period_charges(
        self, license_key: str, period_start: datetime, period_end: datetime
    ) -> BillingResult:
        """Calculate charges for a billing period from database."""
        events = await self._repo.get_usage_events(
            license_key=license_key, start_date=period_start, end_date=period_end
        )
        if not events:
            return BillingResult(
                license_key=license_key, key_id="", period_start=period_start, period_end=period_end
            )

        usage_events = [
            UsageEvent(
                event_type=e["event_type"], category=e.get("category", "usage"),
                metric=e["metric"], value=e["value"],
                timestamp=e["timestamp"].timestamp() if isinstance(e["timestamp"], datetime) else e["timestamp"],
                metadata=e.get("metadata", {}),
            )
            for e in events
        ]
        return await self.calculate_charges(
            license_key=license_key, usage_events=usage_events,
            period_start=period_start, period_end=period_end,
        )


_engine: Optional[BillingEngine] = None
_resolver: Optional[RateCardResolver] = None


def get_engine() -> BillingEngine:
    global _engine
    if _engine is None:
        _engine = BillingEngine()
    return _engine


def get_rate_resolver() -> RateCardResolver:
    global _resolver
    if _resolver is None:
        _resolver = RateCardResolver()
    return _resolver


def reset_engine() -> None:
    global _engine, _resolver
    _engine = None
    _resolver = None


__all__ = [
    "RateCard", "LineItem", "BillingResult", "RateCardResolver", "BillingEngine",
    "VALID_PLANS", "derive_tenant_id", "get_engine", "get_rate_resolver", "reset_engine",
]
