# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate card resolution for RaaS Billing Engine."""

from __future__ import annotations

from decimal import Decimal
import logging
from typing import Dict, Optional

from src.core.auth_tenant import derive_tenant_id
from src.db.repository import LicenseRepository, get_repository
from src.raas.billing_engine_models import VALID_PLANS, RateCard

logger = logging.getLogger(__name__)


class RateCardResolver:
    """Resolve rate cards for license key and event type."""

    def __init__(self, repository: Optional[LicenseRepository] = None) -> None:
        self._repo = repository or get_repository()
        self._cache: Dict[str, RateCard] = {}

    async def resolve(
        self,
        license_key: str,
        event_type: str,
        model_name: Optional[str] = None,
    ) -> Optional[RateCard]:
        """Resolve rate card for license key and event type."""
        license_info = await self._repo.get_license_by_key(license_key)
        if not license_info:
            logger.warning("License not found: %s", derive_tenant_id(license_key))
            return None

        plan_tier = license_info.get("tier", "free")

        if plan_tier not in VALID_PLANS:
            logger.error(
                "Invalid plan tier %s for license %s",
                plan_tier,
                derive_tenant_id(license_key),
            )
            raise ValueError(
                f"Invalid plan tier {plan_tier!r} for license {license_key}. "
                f"Valid: {sorted(VALID_PLANS)}"
            )

        cache_key = f"{plan_tier}:{event_type}:{model_name or '*'}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        rate_card_data = await self._repo.get_rate_card(
            plan_tier=plan_tier,
            event_type=event_type,
            model_name=model_name,
        )

        if not rate_card_data:
            rate_card_data = await self._repo.get_rate_card(
                plan_tier=plan_tier,
                event_type=event_type,
                model_name=None,
            )

        if not rate_card_data:
            logger.warning(f"No rate card found for {cache_key}")
            return None

        rate_card = RateCard(
            plan_tier=rate_card_data["plan_tier"],
            event_type=rate_card_data["event_type"],
            model_name=rate_card_data.get("model_name"),
            unit=rate_card_data["unit"],
            unit_price=Decimal(str(rate_card_data["unit_price"])),
            included_quantity=Decimal(str(rate_card_data.get("included_quantity", 0))),
            overage_rate=(
                Decimal(str(rate_card_data["overage_rate"]))
                if rate_card_data.get("overage_rate")
                else None
            ),
            overage_threshold=(
                Decimal(str(rate_card_data["overage_threshold"]))
                if rate_card_data.get("overage_threshold")
                else None
            ),
            metadata=rate_card_data.get("metadata", {}),
        )

        self._cache[cache_key] = rate_card
        return rate_card

    def clear_cache(self) -> None:
        """Clear rate card cache."""
        self._cache.clear()
