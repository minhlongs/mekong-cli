"""Mekong CLI 7 — Minimal MCP stdio client.

JSON-RPC 2.0 over stdio: initialize -> tools/list -> tools/call.
Supports any MCP server executable (e.g. npx -y @some/mcp-server).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Any


class McpError(RuntimeError):
    pass


@dataclass
class McpServer:
    name: str
    command: list[str]
    cwd: str = "."


@dataclass
class McpTool:
    name: str
    description: str = ""
    schema: dict[str, Any] = field(default_factory=dict)
    server: str = ""


class McpClient:
    """Spawn one MCP server per instance; talk JSON-RPC over stdio."""

    def __init__(self, server: McpServer):
        self.server = server
        self._proc: subprocess.Popen | None = None
        self._req_id = 0

    # ── lifecycle ────────────────────────────────────────────

    def _ensure_proc(self) -> subprocess.Popen:
        if self._proc is None or self._proc.poll() is not None:
            self._proc = subprocess.Popen(
                self.server.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.server.cwd,
                text=True,
            )
        return self._proc

    def close(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.stdin.close()  # type: ignore[union-attr]
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
        self._proc = None

    def __enter__(self) -> "McpClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ── JSON-RPC ─────────────────────────────────────────────

    def _request(self, method: str, params: dict[str, Any], timeout: int = 60) -> dict[str, Any]:
        proc = self._ensure_proc()
        self._req_id += 1
        payload = json.dumps({"jsonrpc": "2.0", "id": self._req_id, "method": method, "params": params})
        assert proc.stdin and proc.stdout
        proc.stdin.write(payload + "\n")
        proc.stdin.flush()

        import select

        if not select.select([proc.stdout], [], [], timeout)[0]:
            raise McpError(f"timeout waiting for {method}")

        line = proc.stdout.readline()
        if not line:
            raise McpError(f"server closed stdout on {method}")
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            raise McpError(f"non-JSON reply: {line[:200]}")
        if "error" in msg and msg["error"]:
            raise McpError(f"MCP error {method}: {msg['error']}")
        return msg.get("result", {})

    # ── high-level ───────────────────────────────────────────

    def initialize(self) -> dict[str, Any]:
        result = self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mekong-cli", "version": "7.0.0"},
        })
        # Notifications have no response — write only, don't read.
        proc = self._ensure_proc()
        payload = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        assert proc.stdin
        proc.stdin.write(payload + "\n")
        proc.stdin.flush()
        return result

    def list_tools(self) -> list[McpTool]:
        result = self._request("tools/list", {})
        out: list[McpTool] = []
        for t in result.get("tools", []):
            out.append(
                McpTool(
                    name=str(t.get("name", "")),
                    description=str(t.get("description", "")),
                    schema=t.get("inputSchema", {}) or {},
                    server=self.server.name,
                )
            )
        return out

    def call_tool(self, name: str, args: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
        result = self._request("tools/call", {"name": name, "arguments": args or {}}, timeout=timeout)
        content = result.get("content", [])
        text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        return {
            "tool": name,
            "ok": not result.get("isError", False),
            "output": "\n".join(text_parts)[:3000],
            "structured": result,
        }
