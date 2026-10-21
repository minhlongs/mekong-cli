# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Configuration dataclasses and exceptions for external MCP client adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class StdioConfig:
    """Configuration for a stdio-transport MCP server."""

    command: str
    args: List[str] = field(default_factory=list)
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    timeout: float = 30.0


@dataclass(frozen=True)
class HttpConfig:
    """Configuration for a Streamable-HTTP MCP server."""

    url: str
    headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    sse_read_timeout: float = 60.0


class ExternalMcpError(RuntimeError):
    """Base error for external MCP client failures."""


class ExternalMcpTimeout(ExternalMcpError):
    """Server did not respond within the configured timeout."""


class ExternalMcpTransportError(ExternalMcpError):
    """Transport-level failure (subprocess crash, HTTP error, etc.)."""


def load_stdio():
    """Load stdio transport + ClientSession; raise a loud error if missing."""
    try:
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore[import-untyped]
        from mcp import ClientSession  # type: ignore[import-untyped]

        return stdio_client, StdioServerParameters, ClientSession
    except ImportError as exc:
        raise ExternalMcpError(
            "mcp SDK is required for stdio transport. Install it: pip install mcp"
        ) from exc


def load_http():
    """Load Streamable-HTTP transport + ClientSession; raise if missing."""
    try:
        from mcp.client.streamable_http import streamablehttp_client  # type: ignore[import-untyped]
        from mcp import ClientSession  # type: ignore[import-untyped]

        return streamablehttp_client, ClientSession
    except ImportError as exc:
        raise ExternalMcpError(
            "mcp SDK is required for http transport. Install it: pip install mcp"
        ) from exc


__all__ = [
    "StdioConfig",
    "HttpConfig",
    "ExternalMcpError",
    "ExternalMcpTimeout",
    "ExternalMcpTransportError",
    "load_stdio",
    "load_http",
]
