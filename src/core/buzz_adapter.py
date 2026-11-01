# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Buzz Adapter — v0.1 integration between Buzz goals and MekongCoreRuntime.

Receives goal payloads from Buzz, parses them into runtime-compatible dicts,
and sends status updates back. No Buzz hardcoding — protocol-driven.

Outbound updates are delivered through an injectable ``transport`` callable
with the contract ``(url, payload_dict) -> int`` (HTTP status code; ``0``
signals failure). When an ``outbox_store`` (`SQLiteGoalStore`) is wired,
outbound updates are persisted transactionally in ``report_outbox`` with
idempotency deduplication and ``DEAD_LETTER`` transition after ``max_attempts``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from src.mekongcli.core.goal_engine.models import (
    ExecutionTruthStatus,
    ImmutableMandate,
    OutboxEntry,
    TicketRecord,
    new_id,
)
from src.mekongcli.core.goal_engine.store import SQLiteGoalStore

logger = logging.getLogger(__name__)

_CALLBACK_TIMEOUT_S = 5.0

Transport = Any  # callable (url: str, payload: dict) -> int

_NO_TRANSPORT: Any = object()


class BuzzConfigError(ValueError):
    """Required Buzz configuration is missing (fail-loud)."""


def _urllib_transport(url: str, payload: dict[str, Any]) -> int:
    """Default transport: stdlib JSON POST with a short timeout."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_CALLBACK_TIMEOUT_S) as response:
            return int(response.status)
    except Exception as exc:
        logger.warning("Buzz callback POST failed url=%s: %s", url, exc)
        return 0


@dataclass
class BuzzPayload:
    """Parsed representation of a Buzz webhook payload."""

    goal_text: str
    context: dict[str, Any] = field(default_factory=dict)
    callback_url: str | None = None
    mission_id: str | None = None


class BuzzAdapter:
    """Receives goals from Buzz and feeds them into MekongCoreRuntime."""

    @classmethod
    def without_transport(
        cls,
        runtime: Any | None = None,
        outbox_store: SQLiteGoalStore | None = None,
    ) -> "BuzzAdapter":
        """Construct an adapter that refuses delivery (no transport wired)."""
        return cls(runtime=runtime, transport=None, outbox_store=outbox_store)

    def __init__(
        self,
        runtime: Any | None = None,
        transport: Transport | None = _NO_TRANSPORT,
        outbox_store: SQLiteGoalStore | None = None,
    ) -> None:
        self._runtime = runtime
        self._transport = _urllib_transport if transport is _NO_TRANSPORT else transport
        self._outbox_store = outbox_store

    @property
    def runtime(self) -> Any:
        return self._runtime

    @runtime.setter
    def runtime(self, value: Any) -> None:
        self._runtime = value

    @property
    def transport(self) -> Transport:
        return self._transport

    @transport.setter
    def transport(self, value: Transport | None) -> None:
        self._transport = _urllib_transport if value is _NO_TRANSPORT else value

    def receive_goal(self, payload: dict) -> dict:
        """Parse Buzz webhook payload into a Goal dict for runtime.run()."""
        bp = BuzzPayload(
            goal_text=payload.get("goal", payload.get("text", "")),
            context=payload.get("context", {}),
            callback_url=payload.get("callback_url"),
            mission_id=payload.get("mission_id"),
        )
        if not bp.goal_text:
            raise ValueError("Buzz payload missing 'goal' field")
        return {
            "text": bp.goal_text,
            "context": bp.context,
            "mission_id": bp.mission_id,
            "callback_url": bp.callback_url,
        }

    def admit_webhook_event(
        self,
        payload: dict[str, Any],
        *,
        source_id: str | None = None,
    ) -> tuple[TicketRecord, bool]:
        """Admit a Buzz webhook event idempotently on ``(source_id, event_id)``.

        Returns ``(ticket_record, created)`` where ``created`` is ``True`` on
        first admission and ``False`` when the ``(source_id, event_id)`` pair
        was already admitted.
        """
        if self._outbox_store is None:
            raise BuzzConfigError("BuzzAdapter has no outbox_store wired for ticket admission")
        src_id = str(source_id or payload.get("source_id") or "buzz").strip() or "buzz"
        event_id = str(payload.get("event_id") or payload.get("mission_id") or "").strip()
        if not event_id:
            raise ValueError("Buzz webhook payload missing 'event_id' or 'mission_id'")

        raw_ticket_id = str(payload.get("ticket_id") or "").strip()
        ticket_id = raw_ticket_id or (
            "tkt_" + hashlib.sha256(f"{src_id}:{event_id}".encode("utf-8")).hexdigest()[:12]
        )
        goal_id = str(payload.get("goal_id") or payload.get("mission_id") or ticket_id)
        thread_id = str(payload.get("thread_id") or payload.get("session_id") or "default")
        accepted_at = str(payload.get("accepted_at") or "2026-11-02T00:00:00Z")
        caps_raw = payload.get("permitted_capabilities") or ("buzz.mission",)
        bounds_raw = payload.get("resource_boundaries") or (".",)

        mandate = ImmutableMandate(
            ticket_id=ticket_id,
            source_id=src_id,
            event_id=event_id,
            requester=str(payload.get("requester") or "buzz_webhook"),
            authorized_scope=str(payload.get("authorized_scope") or "mission_execution"),
            workspace_id=str(payload.get("workspace_id") or "default"),
            mandate_version=int(payload.get("mandate_version") or 1),
            policy_version=str(payload.get("policy_version") or "v1"),
            accepted_at=accepted_at,
            permitted_capabilities=tuple(str(c) for c in caps_raw),
            resource_boundaries=tuple(str(b) for b in bounds_raw),
            risk_classification=str(payload.get("risk_classification") or "LOW"),
            cost_budget=float(payload.get("cost_budget") or 5.0),
            retry_budget=int(payload.get("retry_budget") or 3),
            verification_requirements=str(payload.get("verification_requirements") or "standard"),
        )
        admitted = self._outbox_store.admit_ticket(
            goal_id=goal_id,
            mandate=mandate,
            thread_id=thread_id,
        )
        created = not bool(admitted.get("deduplicated"))
        persisted_mandate = self._outbox_store.verify_mandate_integrity(admitted["ticket_id"])
        truth_raw = admitted.get("truth_status") or ExecutionTruthStatus.PLANNED.value
        record = TicketRecord(
            ticket_id=admitted["ticket_id"],
            goal_id=admitted["goal_id"],
            mandate=persisted_mandate,
            truth_status=ExecutionTruthStatus(truth_raw),
            thread_id=admitted.get("thread_id"),
            created_at=str(admitted.get("created_at") or ""),
            updated_at=str(admitted.get("updated_at") or ""),
        )
        return record, created

    def send_update(
        self,
        status: str,
        data: dict,
        callback_url: str | None = None,
        *,
        ticket_id: str = "buzz_ticket",
        source_id: str = "buzz",
        thread_id: str = "default",
        idempotency_key: str | None = None,
        max_attempts: int = 3,
    ) -> dict:
        """Build a status update dict destined for the Buzz callback URL.

        When ``self._outbox_store`` is configured, persists the outbound report
        transactionally in ``report_outbox`` and deduplicates by ``idempotency_key``.
        """
        update: dict[str, Any] = {"status": status, "data": data}
        if not callback_url and self._outbox_store is None:
            return update
        if callback_url and self._transport is None:
            raise BuzzConfigError(
                "no transport wired — construct BuzzAdapter(transport=...) or "
                "use BuzzAdapter.without_transport() only if delivery is unwanted"
            )

        if self._outbox_store is not None:
            canonical = json.dumps(update, sort_keys=True, separators=(",", ":"))
            idem_key = idempotency_key or hashlib.sha256(
                f"{ticket_id}:{source_id}:{thread_id}:{canonical}".encode("utf-8")
            ).hexdigest()
            entry = OutboxEntry(
                outbox_id=new_id("outbox"),
                ticket_id=ticket_id,
                source_id=source_id,
                thread_id=thread_id,
                idempotency_key=idem_key,
                payload_json=canonical,
                max_attempts=max_attempts,
            )
            queued = self._outbox_store.enqueue_outbox(entry, callback_url=callback_url)
            if queued.get("deduplicated"):
                return update | {
                    "outbox_id": queued["outbox_id"],
                    "delivery_status": queued["delivery_status"],
                    "deduplicated": True,
                }
            if callback_url:
                delivered = self._outbox_store.process_outbox_delivery(
                    queued["outbox_id"],
                    self._transport,
                )
                return update | {
                    "outbox_id": delivered["outbox_id"],
                    "delivery_status": delivered["delivery_status"],
                    "attempts": delivered["attempts"],
                    "deduplicated": False,
                }
            return update | {
                "outbox_id": queued["outbox_id"],
                "delivery_status": queued["delivery_status"],
                "deduplicated": False,
            }

        if callback_url is None:
            return update
        if self._transport is None:
            raise BuzzConfigError("no transport wired")
        try:
            code = int(self._transport(callback_url, update))
        except Exception as exc:
            logger.warning("Buzz transport raised for %s: %s", callback_url, exc)
            return update
        if 200 <= code < 300:
            logger.info("Buzz callback delivered (%d) to %s", code, callback_url)
        else:
            logger.info("Buzz callback non-2xx (%d) for %s", code, callback_url)
        return update

    def receive_feedback(self, feedback: dict) -> dict:
        """Parse feedback from Buzz for plan adaptation."""
        return feedback


__all__ = ["BuzzAdapter", "BuzzConfigError", "BuzzPayload", "_urllib_transport"]
