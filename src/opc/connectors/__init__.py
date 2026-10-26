"""OPC Connectors — pluggable external and offline adapters."""
from __future__ import annotations

from src.opc.connectors.base import ConnectorProtocol, ConnectorResult
from src.opc.connectors.mock import MockConnector

__all__ = ["ConnectorProtocol", "ConnectorResult", "MockConnector"]
