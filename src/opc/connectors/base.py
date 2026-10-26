"""Base connector protocol for OPC external side-effects."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from src.opc.models import ActionPayload


@dataclass(frozen=True)
class ConnectorResult:
    """Result returned by a connector after dispatching an action."""

    success: bool
    connector_id: str
    status: str  # "completed", "failed", "uncertain_reconciliation_required"
    response_data: dict[str, Any]
    error_message: str | None = None


class ConnectorProtocol(Protocol):
    """Protocol implemented by all OPC connectors."""

    connector_id: str

    def dispatch(self, idempotency_key: str, payload: ActionPayload) -> ConnectorResult:
        """Execute the external action idempotently."""
        ...
