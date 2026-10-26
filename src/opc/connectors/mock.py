"""Deterministic offline mock connector for testing and local verification."""
from __future__ import annotations

from typing import Any

from src.opc.connectors.base import ConnectorResult
from src.opc.models import ActionPayload


class MockConnector:
    """Offline connector recording dispatched payloads without network or billing."""

    def __init__(self, connector_id: str = "mock_followup_draft", simulate_uncertain: bool = False) -> None:
        self.connector_id = connector_id
        self.simulate_uncertain = simulate_uncertain
        self.dispatched: dict[str, dict[str, Any]] = {}

    def dispatch(self, idempotency_key: str, payload: ActionPayload) -> ConnectorResult:
        """Record action in memory idempotently."""
        if idempotency_key in self.dispatched:
            return ConnectorResult(
                success=True,
                connector_id=self.connector_id,
                status="completed",
                response_data={"deduplicated": True, "record": self.dispatched[idempotency_key]},
            )

        if self.simulate_uncertain:
            return ConnectorResult(
                success=False,
                connector_id=self.connector_id,
                status="uncertain_reconciliation_required",
                response_data={},
                error_message="Simulated network timeout after request transmission; reconciliation required.",
            )

        record = {
            "idempotency_key": idempotency_key,
            "recipient": payload.recipient,
            "capability": payload.capability,
            "content": payload.content,
            "budget": f"{payload.budget_amount} {payload.budget_currency}",
        }
        self.dispatched[idempotency_key] = record
        return ConnectorResult(
            success=True,
            connector_id=self.connector_id,
            status="completed",
            response_data={"deduplicated": False, "record": record},
        )
