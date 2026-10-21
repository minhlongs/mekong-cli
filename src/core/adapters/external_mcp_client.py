# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""External MCP client adapter — consume tools from third-party MCP servers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .external_mcp_connection import ExternalMcpConnectionManager
from .external_mcp_types import (
    ExternalMcpError,
    ExternalMcpTimeout,
    ExternalMcpTransportError,
    HttpConfig,
    StdioConfig,
)

logger = logging.getLogger(__name__)


class ExternalMcpClient:
    """Synchronous facade over the async mcp SDK client."""

    def __init__(self) -> None:
        self._config: Any = None
        self._transport: str = ""
        self._conn: Optional[ExternalMcpConnectionManager] = None
        self._closed: bool = False
        self._session: Any = None
        self._portal: Any = None
        self._portal_cm: Any = None

    @classmethod
    def stdio(
        cls,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: float = 30.0,
    ) -> "ExternalMcpClient":
        client = cls()
        client._config = StdioConfig(command=command, args=args or [], env=env, cwd=cwd, timeout=timeout)
        client._transport = "stdio"
        client._conn = ExternalMcpConnectionManager("stdio", client._config)
        return client

    @classmethod
    def http(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        sse_read_timeout: float = 60.0,
    ) -> "ExternalMcpClient":
        client = cls()
        client._config = HttpConfig(url=url, headers=headers, timeout=timeout, sse_read_timeout=sse_read_timeout)
        client._transport = "http"
        client._conn = ExternalMcpConnectionManager("http", client._config)
        return client

    def _ensure_connected(self) -> Any:
        if self._closed:
            raise ExternalMcpError("client is closed")
        if self._session is not None:
            return self._session
        if self._conn is None:
            self._conn = ExternalMcpConnectionManager(self._transport, self._config)
        return self._conn.ensure_connected()

    @property
    def _active_portal(self) -> Any:
        if self._portal is not None:
            return self._portal
        if self._conn is not None:
            return self._conn.portal
        return None

    def list_tools(self) -> List[Dict[str, Any]]:
        session = self._ensure_connected()
        portal = self._active_portal
        try:
            tool_result = portal.call(session.list_tools)
        except Exception as exc:
            raise ExternalMcpError(f"list_tools failed: {exc}") from exc

        tools: List[Dict[str, Any]] = []
        for t in getattr(tool_result, "tools", []):
            tools.append(
                {
                    "name": t.name,
                    "description": getattr(t, "description", "") or "",
                    "inputSchema": getattr(t, "inputSchema", {}) or {},
                }
            )
        return tools

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = self._ensure_connected()
        portal = self._active_portal
        try:
            result = portal.call(session.call_tool, name, arguments or {})
        except Exception as exc:
            raise ExternalMcpError(f"call_tool({name!r}) failed: {exc}") from exc

        content_parts: List[str] = []
        for part in getattr(result, "content", []):
            text = getattr(part, "text", None)
            content_parts.append(text if text is not None else str(part))

        return {
            "content": content_parts,
            "is_error": bool(getattr(result, "isError", False) or getattr(result, "is_error", False)),
            "text": "\n".join(content_parts),
        }

    def close(self) -> None:
        if self._closed:
            return
        if self._conn is not None:
            self._conn.close()
        if self._portal_cm is not None:
            try:
                self._portal_cm.__exit__(None, None, None)
            except Exception:
                pass
            self._portal_cm = None
            self._portal = None
        self._closed = True

    def __enter__(self) -> "ExternalMcpClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<ExternalMcpClient transport={self._transport} closed={self._closed}>"


def from_config(config: Dict[str, Any]) -> ExternalMcpClient:
    """Build an ExternalMcpClient from a JSON config dict."""
    if "command" in config:
        return ExternalMcpClient.stdio(
            command=config["command"], args=config.get("args"),
            env=config.get("env"), cwd=config.get("cwd"),
            timeout=float(config.get("timeout", 30.0)),
        )
    if "url" in config:
        return ExternalMcpClient.http(
            url=config["url"], headers=config.get("headers"),
            timeout=float(config.get("timeout", 30.0)),
            sse_read_timeout=float(config.get("sse_read_timeout", 60.0)),
        )
    raise ExternalMcpError(
        f"MCP config must contain either 'command' (stdio) or 'url' (http); got keys: {sorted(config)}"
    )


def parse_mcp_servers(config: Dict[str, Any]) -> Dict[str, ExternalMcpClient]:
    """Parse the mcpServers block from a Claude-Desktop-style config."""
    servers = config.get("mcpServers") or config.get("servers") or {}
    result: Dict[str, ExternalMcpClient] = {}
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        try:
            result[name] = from_config(spec)
        except ExternalMcpError as exc:
            logger.warning("skipping MCP server %r: %s", name, exc)
    return result


__all__ = [
    "ExternalMcpClient", "StdioConfig", "HttpConfig", "ExternalMcpError",
    "ExternalMcpTimeout", "ExternalMcpTransportError", "from_config", "parse_mcp_servers",
]
