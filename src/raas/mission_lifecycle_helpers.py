# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Webhook emission and complexity helpers for MissionLifecycle."""
from __future__ import annotations

import logging
from typing import Optional

from src.raas.mission_models import MissionComplexity, MissionRecord
from src.raas.webhook_events import (
    credits_depleted_event,
    credits_low_event,
    mission_completed_event,
    mission_created_event,
    mission_failed_event,
)

logger = logging.getLogger(__name__)

_LOW_CREDIT_THRESHOLD = 0.10  # emit credits.low when <=10% of limit remains


class InsufficientCreditsError(Exception):
    """Raised when tenant balance is too low to reserve credits."""


def _auto_detect_complexity(goal: str) -> MissionComplexity:
    length = len(goal)
    if length < 50:
        return MissionComplexity.simple
    if length < 150:
        return MissionComplexity.standard
    return MissionComplexity.complex


class MissionWebhookMixin:
    """Webhook delivery helper mixin for MissionLifecycle."""

    def _url(self, tenant_id: str) -> Optional[str]:
        if self._dispatcher is None or self._webhook_url_fn is None:
            return None
        return self._webhook_url_fn(tenant_id)

    def _deliver(self, event, tenant_id: str) -> None:
        url = self._url(tenant_id)
        if not url:
            return
        try:
            self._dispatcher.deliver(event, url)
        except Exception as exc:
            logger.warning("Webhook delivery failed (%s): %s", event.event_type, exc)

    def _emit_created(self, record: MissionRecord) -> None:
        self._deliver(
            mission_created_event(
                tenant_id=record.tenant_id,
                mission_id=record.id,
                goal=record.goal,
                complexity=record.complexity.value,
                credits_cost=record.credits_cost,
            ),
            record.tenant_id,
        )

    def _emit_completed(self, record: MissionRecord, duration: float) -> None:
        self._deliver(
            mission_completed_event(
                tenant_id=record.tenant_id,
                mission_id=record.id,
                credits_billed=record.credits_cost,
                duration_seconds=duration,
            ),
            record.tenant_id,
        )

    def _emit_failed(self, record: MissionRecord, reason: str) -> None:
        self._deliver(
            mission_failed_event(
                tenant_id=record.tenant_id,
                mission_id=record.id,
                reason=reason,
            ),
            record.tenant_id,
        )

    def _emit_depleted(self, tenant_id: str, balance: int) -> None:
        self._deliver(
            credits_depleted_event(tenant_id, balance, "unknown"),
            tenant_id,
        )

    def _maybe_emit_low(self, tenant_id: str) -> None:
        limit = self._credit_limit_fn(tenant_id)
        balance = self._credits.get_balance(tenant_id)
        if limit > 0 and balance <= int(limit * _LOW_CREDIT_THRESHOLD):
            self._deliver(
                credits_low_event(tenant_id, balance, limit),
                tenant_id,
            )
