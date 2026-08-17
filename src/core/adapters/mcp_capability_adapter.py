# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MCP Adapter — wraps MCPServer tools as Capability instances.

Provides the bridge between MCP tools and the CapabilityBus.
Each MCP tool becomes a Capability with:
  - id = "mcp:<tool_name>"
  - source = CapabilitySource.MCP
  - risk_level = MEDIUM (configurable)
  - execute() delegates to MCPServer._handle_<tool_name>()
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.core.capability import Capability, CapabilityBus, CapabilitySource

logger = logging.getLogger(__name__)


class MCPCapabilityAdapter:
    """Adapter that wraps MCPServer tools as Capability instances.

    Usage:
        adapter = MCPCapabilityAdapter()
        adapter.sync_from_mcp()  # discover + register all MCP tools

        # Now available via CapabilityBus:
        caps = adapter.bus.list_capabilities(source=CapabilitySource.MCP)
        result = adapter.bus.execute("mcp:tasks_list", {"status": "todo"})
    """

    def __init__(self, bus: CapabilityBus | None = None) -> None:
        self._bus = bus
        self._mcp_server: Any = None
        self._registered: set[str] = set()

    @property
    def bus(self) -> CapabilityBus | None:
        return self._bus

    @bus.setter
    def bus(self, value: CapabilityBus | None) -> None:
        self._bus = value

    def _get_mcp_server(self) -> Any | None:
        """Lazily import and create MCPServer instance."""
        if self._mcp_server is not None:
            return self._mcp_server

        try:
            from src.core.mcp_server import MCPServer
            self._mcp_server = MCPServer()
            return self._mcp_server
        except Exception as exc:
            logger.warning("MCPCapabilityAdapter: cannot load MCPServer (%s)", exc)
            return None

    def _get_tool_names(self) -> list[str]:
        """Get list of registered MCP tool names."""
        server = self._get_mcp_server()
        if server is None:
            return []
        try:
            # MCPServer builds _tools list during create_app()
            server.create_app()
            return [t.get("name", "") for t in getattr(server, "_tools", []) if t.get("name")]
        except Exception as exc:
            logger.warning("MCPCapabilityAdapter: cannot list tools (%s)", exc)
            return []

    def _build_handler(self, tool_name: str):
        """Build an execute handler for a given MCP tool name.

        Maps tool_name → MCPServer._handle_<tool_name>()
        Falls back to a generic handler if specific method not found.
        """
        server = self._get_mcp_server()
        if server is None:
            return lambda params, ctx=None: {"error": "MCP server unavailable"}

        handler_name = f"_handle_{tool_name}"
        handler = getattr(server, handler_name, None)
        if handler is None:
            # Fallback: try calling via the FastMCP app's tool runner
            return lambda params, ctx=None: {
                "error": f"No handler for MCP tool '{tool_name}'",
                "available": self._get_tool_names(),
            }

        def _exec(params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
            try:
                result = handler(**params)
                return {"ok": True, "result": result, "tool": tool_name}
            except TypeError:
                # If handler expects positional args, try positional
                return {"error": f"Parameter mismatch for {tool_name}"}
            except Exception as exc:
                logger.error("MCP tool %s error: %s", tool_name, exc)
                return {"ok": False, "error": str(exc), "tool": tool_name}

        return _exec

    def sync_from_mcp(self) -> list[Capability]:
        """Discover all MCP tools and register them as Capabilities.

        Returns list of Capability instances created.
        Requires bus to be set before calling.
        """
        if self._bus is None:
            raise RuntimeError("CapabilityBus not set on MCPCapabilityAdapter")

        tool_names = self._get_tool_names()
        capabilities: list[Capability] = []

        for tool_name in tool_names:
            if tool_name in self._registered:
                continue

            server = self._get_mcp_server()
            tool_meta = {}
            if server and hasattr(server, "_tools"):
                for t in server._tools:
                    if t.get("name") == tool_name:
                        tool_meta = t
                        break

            cap = Capability(
                id=f"mcp:{tool_name}",
                name=tool_meta.get("name", tool_name),
                description=tool_meta.get("description", f"MCP tool: {tool_name}"),
                input_schema={},
                risk_level="MEDIUM",
                source=CapabilitySource.MCP,
                cost=0.0,
                tags=["mcp"],
                metadata={"handler": f"_handle_{tool_name}"},
            )
            # Monkey-patch execute to call real handler
            cap.execute = self._build_handler(tool_name)

            self._bus.register(cap)
            self._registered.add(tool_name)
            capabilities.append(cap)

        logger.info("MCPCapabilityAdapter: synced %d capabilities", len(capabilities))
        return capabilities

    def get_capability(self, tool_name: str) -> Capability | None:
        """Get a single MCP capability by tool name."""
        if self._bus is None:
            return None
        return self._bus.get(f"mcp:{tool_name}")


__all__ = ["MCPCapabilityAdapter"]