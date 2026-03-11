"""Mission lifecycle orchestrator: submit → queue → execute → verify → deliver → bill.

Coordinates MissionStore, CreditStore, and WebhookDispatcher to execute the
full RaaS mission pipeline. Credits are reserved BEFORE execution per global
RaaS standard (idempotent billing).
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from src.raas.credits import CreditStore, MISSION_COSTS
from src.raas.mission_models import (
    CreateMissionRequest,
    MissionComplexity,
    MissionRecord,
    MissionStatus,
)
from src.raas.mission_store import MissionStore
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


class MissionLifecycle:
    """Orchestrates mission state transitions with credit reservation.

    Credit deduction happens BEFORE mission creation so tenants cannot
    over-submit when balance is insufficient.

    Args:
        mission_store: Persistence for mission records.
        credit_store: Persistence for tenant balances.
        dispatcher: Optional WebhookDispatcher instance.
        webhook_url_fn: Callable(tenant_id) -> Optional[str] for URL lookup.
        credit_limit_fn: Callable(tenant_id) -> int for plan limit lookup.
    """

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(
        self,
        tenant_id: str,
        request: CreateMissionRequest,
    ) -> MissionRecord:
        """Reserve credits and create a queued mission.

        Args:
            tenant_id: Owning tenant.
            request: Validated mission creation payload.

        Returns:
            Newly created MissionRecord in QUEUED state.

        Raises:
            InsufficientCreditsError: Balance too low for the complexity tier.
        """
        complexity = request.complexity or _auto_detect_complexity(request.goal)
        cost = MISSION_COSTS.get(complexity.value, 1)

        balance = self._credits.get_balance(tenant_id)
        if balance < cost:
            self._emit_depleted(tenant_id, balance)
            raise InsufficientCreditsError(
                f"Insufficient credits: need {cost}, have {balance}. "
                "Upgrade at https://polar.sh/mekong"
            )

        # Debit BEFORE creating the record — prevents double-spend on retry
        ok = self._credits.deduct(
            tenant_id=tenant_id,
            amount=cost,
            reason=f"reserve:submit",
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
        """Transition mission to RUNNING.

        Returns the refreshed record, or None if not found/wrong tenant.
        """
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
        """Mark mission failed, optionally refund credits, emit webhook.

        Args:
            mission_id: Mission that failed.
            tenant_id: Owner for scoped lookup.
            reason: Human-readable failure description.
            refund: If True, restore debited credits to tenant balance.
        """
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

    # ------------------------------------------------------------------
    # Webhook emission helpers
    # ------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _auto_detect_complexity(goal: str) -> MissionComplexity:
    length = len(goal)
    if length < 50:
        return MissionComplexity.simple
    if length < 150:
        return MissionComplexity.standard
    return MissionComplexity.complex
