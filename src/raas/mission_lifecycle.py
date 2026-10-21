# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mission lifecycle orchestrator: submit → queue → execute → verify → deliver → bill.

Coordinates MissionStore, CreditStore, and WebhookDispatcher to execute the
full RaaS mission pipeline. Credits are reserved BEFORE execution per global
RaaS standard (idempotent billing).
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from src.raas.credits import MISSION_COSTS, CreditStore
from src.raas.mission_lifecycle_helpers import (
    _LOW_CREDIT_THRESHOLD,
    InsufficientCreditsError,
    MissionWebhookMixin,
    _auto_detect_complexity,
)
from src.raas.mission_models import (
    CreateMissionRequest,
    MissionComplexity,  # noqa: F401
    MissionRecord,
    MissionStatus,
)
from src.raas.mission_store import MissionStore
from src.raas.webhook_events import (  # noqa: F401
    credits_depleted_event,
    credits_low_event,
    mission_completed_event,
    mission_created_event,
    mission_failed_event,
)

logger = logging.getLogger(__name__)


class MissionLifecycle(MissionWebhookMixin):
    """Orchestrates mission state transitions with credit reservation."""

    def __init__(
        self,
        mission_store: MissionStore,
        credit_store: CreditStore,
        dispatcher=None,
        webhook_url_fn: Optional[Callable[[str], Optional[str]]] = None,
        credit_limit_fn: Optional[Callable[[str], int]] = None,
    ) -> None:
        self._missions = mission_store
        self._credits = credit_store
        self._dispatcher = dispatcher
        self._webhook_url_fn = webhook_url_fn
        self._credit_limit_fn = credit_limit_fn or (lambda _: 200)

    def submit(
        self,
        tenant_id: str,
        request: CreateMissionRequest,
    ) -> MissionRecord:
        """Reserve credits and create a queued mission."""
        complexity = request.complexity or _auto_detect_complexity(request.goal)
        cost = MISSION_COSTS.get(complexity.value, 1)

        balance = self._credits.get_balance(tenant_id)
        if balance < cost:
            self._emit_depleted(tenant_id, balance)
            raise InsufficientCreditsError(
                f"Insufficient credits: need {cost}, have {balance}. "
                "Upgrade at https://mekongmind.com/pricing"
            )

        ok = self._credits.deduct(
            tenant_id=tenant_id,
            amount=cost,
            reason="reserve:submit",
        )
        if not ok:
            raise InsufficientCreditsError(
                f"Concurrent deduction failed: balance {balance} < {cost}"
            )

        record = self._missions.create(
            tenant_id=tenant_id,
            goal=request.goal,
            complexity=complexity,
            credits_cost=cost,
        )

        self._emit_created(record)
        self._maybe_emit_low(tenant_id)
        return record

    def start(self, mission_id: str, tenant_id: str) -> Optional[MissionRecord]:
        """Transition mission to RUNNING."""
        record = self._missions.get(mission_id, tenant_id)
        if record is None:
            return None
        if record.status != MissionStatus.queued:
            return record
        self._missions.update_status(mission_id, MissionStatus.running)
        return self._missions.get(mission_id, tenant_id)

    def complete(
        self,
        mission_id: str,
        tenant_id: str,
        duration_seconds: float = 0.0,
    ) -> Optional[MissionRecord]:
        """Mark mission completed and emit webhook."""
        record = self._missions.get(mission_id, tenant_id)
        if record is None:
            return None
        self._missions.update_status(mission_id, MissionStatus.completed)
        updated = self._missions.get(mission_id, tenant_id)
        if updated:
            self._emit_completed(updated, duration_seconds)
        return updated

    def fail(
        self,
        mission_id: str,
        tenant_id: str,
        reason: str,
        refund: bool = False,
    ) -> Optional[MissionRecord]:
        """Mark mission failed, optionally refund credits, emit webhook."""
        record = self._missions.get(mission_id, tenant_id)
        if record is None:
            return None
        self._missions.update_status(
            mission_id, MissionStatus.failed, error_msg=reason
        )
        if refund and record.credits_cost > 0:
            self._credits.add(
                tenant_id=tenant_id,
                amount=record.credits_cost,
                reason=f"refund:mission:{mission_id}",
            )
        updated = self._missions.get(mission_id, tenant_id)
        if updated:
            self._emit_failed(updated, reason)
        return updated


__all__ = [
    "_LOW_CREDIT_THRESHOLD",
    "InsufficientCreditsError",
    "MissionLifecycle",
    "_auto_detect_complexity",
]
