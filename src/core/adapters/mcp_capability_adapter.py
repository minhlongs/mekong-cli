# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MCP Adapter — wraps MekongMcpServer tools as Capability instances on CapabilityBus."""

from __future__ import annotations

import logging
from typing import Any, Dict

from src.core.capability import Capability, CapabilityBus, CapabilitySource
from src.core.mcp_server import MekongMcpServer

logger = logging.getLogger(__name__)
_TOOL_PREFIX = "cc_"


class MCPCapabilityAdapter:
    """Adapter that wraps MekongMcpServer tools as Capability instances."""

    def __init__(self, bus: CapabilityBus | None = None, mcp_server: Any | None = None) -> None:
        self._bus = bus
        self._mcp_server: Any = mcp_server
        self._registered: set[str] = set()

    @property
    def bus(self) -> CapabilityBus | None:
        return self._bus

    @bus.setter
    def bus(self, value: CapabilityBus | None) -> None:
        self._bus = value

    def _get_mcp_server(self) -> Any:
        """Lazily create the real MekongMcpServer instance."""
        if self._mcp_server is not None:
            return self._mcp_server
        self._mcp_server = MekongMcpServer()
        return self._mcp_server

    def _get_tool_names(self) -> list[str]:
        """Get list of registered MCP tool names."""
        server = self._get_mcp_server()
        try:
            server.create_app()
            return [t.get("name", "") for t in getattr(server, "_tools", []) if t.get("name")]
        except Exception as exc:
            logger.warning("MCPCapabilityAdapter: cannot list tools (%s)", exc)
            return []

    @staticmethod
    def _handler_base(tool_name: str) -> str:
        """Strip the ``cc_`` prefix to get the handler method base name."""
        return tool_name[len(_TOOL_PREFIX):] if tool_name.startswith(_TOOL_PREFIX) else tool_name

    def _build_handler(self, tool_name: str):
        """Build an execute handler for a given MCP tool name.

        Maps tool_name -> MekongMcpServer._handle_<base>() where ``base`` is
        the tool name with the ``cc_`` prefix stripped. Falls back to a generic
        handler if the specific method is not found.
        """
        server = self._get_mcp_server()
        base = self._handler_base(tool_name)
        handler_name = f"_handle_{base}"
        handler = getattr(server, handler_name, None)
        if handler is None:
            # Fallback: no matching handler on the server for this tool.
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
            if hasattr(server, "_tools"):
                for t in server._tools:
                    if t.get("name") == tool_name:
                        tool_meta = t
                        break

            base = self._handler_base(tool_name)
            cap = Capability(
                id=f"mcp:{tool_name}",
                name=tool_meta.get("name", tool_name),
                description=tool_meta.get("description", f"MCP tool: {tool_name}"),
                input_schema={},
                risk_level="MEDIUM",
                source=CapabilitySource.MCP,
                cost=0.0,
                tags=["mcp"],
                metadata={"handler": f"_handle_{base}"},
            )
            # Monkey-patch execute to call real handler.
            # setattr (not direct assignment) so pyright does not flag
            # reassigning the dataclass method "execute".
            setattr(cap, "execute", self._build_handler(tool_name))

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
