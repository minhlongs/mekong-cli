# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Reverse engineering MCP client bridge.

Connects to external reverse engineering MCP servers (GhidraMCP, radare2 MCP,
JADX-AI-MCP, Chrome DevTools MCP) via ExternalMcpClient, wrapping tools as
first-class Mekong Capability instances under 3-tier RE Governance.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from src.core.adapters.external_mcp_client import ExternalMcpClient, from_config
from src.core.capability import Capability, CapabilityBus, CapabilitySource

logger = logging.getLogger(__name__)

# Standard recommended MCP servers for Agentic Reverse Engineering
KNOWN_RE_SERVERS: Dict[str, Dict[str, Any]] = {
    "ghidra": {
        "command": "ghidra-mcp",
        "args": [],
        "risk_level": "MEDIUM_RISK",
        "description": "Ghidra Headless Decompilation & Symbol Recovery MCP",
        "tags": ["re", "binary", "ghidra", "decompilation"],
    },
    "radare2": {
        "command": "r2-mcp",
        "args": [],
        "risk_level": "MEDIUM_RISK",
        "description": "radare2 / r2pipe Disassembly & Binary Analysis MCP",
        "tags": ["re", "binary", "r2", "disassembly"],
    },
    "jadx": {
        "command": "jadx-mcp",
        "args": [],
        "risk_level": "MEDIUM_RISK",
        "description": "JADX Android APK / Dex Decompiler MCP",
        "tags": ["re", "apk", "android", "jadx"],
    },
    "chrome-devtools": {
        "command": "npx",
        "args": ["-y", "chrome-devtools-mcp@latest"],
        "risk_level": "MEDIUM_RISK",
        "description": "Chrome DevTools Protocol SaaS / Web App RE MCP",
        "tags": ["re", "web", "devtools", "network"],
    },
}


class ReMcpToolCapability(Capability):
    """Wraps an external MCP tool as a Mekong Capability with RE Governance."""

    def __init__(
        self,
        server_name: str,
        tool_spec: Dict[str, Any],
        client: ExternalMcpClient,
        risk_level: str = "MEDIUM_RISK",
    ) -> None:
        tool_name = tool_spec.get("name", "unknown")
        cap_id = f"re:mcp:{server_name}:{tool_name}"
        super().__init__(
            id=cap_id,
            name=f"[{server_name}] {tool_name}",
            description=tool_spec.get("description", "") or f"MCP tool {tool_name} from {server_name}",
            input_schema=tool_spec.get("inputSchema", {}),
            risk_level=risk_level,
            source=CapabilitySource.MCP,
            tags=["re", "mcp", server_name],
            metadata={"server": server_name, "raw_tool": tool_spec},
        )
        self._tool_name = tool_name
        self._client = client

    def execute(self, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Delegate tool call to underlying ExternalMcpClient."""
        try:
            return self._client.call_tool(self._tool_name, params)
        except Exception as exc:
            logger.error("Failed to execute MCP tool %s: %s", self._tool_name, exc)
            return {"error": str(exc), "tool": self._tool_name}


class ReMcpBridge:
    """Manages connections to RE MCP servers and registers capabilities."""

    def __init__(self, bus: CapabilityBus) -> None:
        self.bus = bus
        self._clients: Dict[str, ExternalMcpClient] = {}

    def connect_server(self, name: str, config: Dict[str, Any], risk_level: str = "MEDIUM_RISK") -> List[str]:
        """Connect to an MCP server from config, list its tools, and register them."""
        client = from_config(config)
        self._clients[name] = client
        registered_ids: List[str] = []

        try:
            tools = client.list_tools()
            for t in tools:
                cap = ReMcpToolCapability(
                    server_name=name,
                    tool_spec=t,
                    client=client,
                    risk_level=risk_level,
                )
                self.bus.register(cap)
                registered_ids.append(cap.id)
            logger.info("Registered %d tools from RE MCP server %s", len(registered_ids), name)
        except Exception as exc:
            logger.warning("Could not list tools for RE MCP server %s: %s", name, exc)

        return registered_ids

    def get_known_servers(self) -> Dict[str, Dict[str, Any]]:
        """Return catalog of standard RE MCP server templates."""
        return dict(KNOWN_RE_SERVERS)

    def close(self) -> None:
        """Close all active MCP client sessions."""
        for client in self._clients.values():
            try:
                client.close()
            except Exception:
                pass
        self._clients.clear()


__all__ = [
    "KNOWN_RE_SERVERS",
    "ReMcpToolCapability",
    "ReMcpBridge",
]
